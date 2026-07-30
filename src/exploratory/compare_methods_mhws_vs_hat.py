"""Compare the published MHWS arm with the experimental HAT arm.

Both arms are passed through ``derive_native_hazard_index``.  Before that call,
the same explicit zero-event policy is applied to both sources: frequency and
integrated severity are zero where no event was accepted.  Temporary prepared
CSVs keep the canonical index function literally unchanged.

Exposure, vulnerability, and grid-to-municipality associations come from the
published municipal product and are identical between arms.  Duration and
peak intensity are normalized and reported only as retired diagnostics.

Usage:
    conda run -n osr11 python -m src.exploratory.compare_methods_mhws_vs_hat

Outputs:
    outputs/method_comparison_mhws_vs_hat/hazard_by_point.csv
    outputs/method_comparison_mhws_vs_hat/risk_by_municipality.csv
    outputs/method_comparison_mhws_vs_hat/comparison_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

import numpy as np
import pandas as pd

from src.exploratory.compare_methods_ssh_total_vs_mhws import (
    LATITUDE_BANDS,
    _band,
    _minmax,
    load_municipal_attributes,
    municipal_risk,
)
from src.risk_integration.hazard_index import derive_native_hazard_index

ROOT = Path(__file__).resolve().parents[2]
MHWS_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
MHWS_SUMMARY = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_summary_mhws.json"
)
HAT_DIR = ROOT / "outputs" / "hat_method"
HAT_METRICS = HAT_DIR / "compound_metrics_hat.csv"
HAT_SUMMARY = HAT_DIR / "compound_summary_hat.json"
OUT_DIR = ROOT / "outputs" / "method_comparison_mhws_vs_hat"

COMPONENTS = (
    "Hazard_Frequency",
    "Hazard_Severity",
    "Hazard_Index",
    "Hazard_Duration",
    "Hazard_Peak_Intensity",
)


def _prepare(source: Path, destination: Path) -> pd.DataFrame:
    frame = pd.read_csv(source)
    for field in ("compound_count_total", "mean_integrated_severity"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce").fillna(0.0)
    if len(frame) != 808:
        raise AssertionError(f"{source} has {len(frame)} points, expected 808")
    frame.to_csv(destination, index=False)
    return frame


def _add_diagnostics(grid: pd.DataFrame) -> pd.DataFrame:
    grid = grid.copy()
    grid["Hazard_Duration"] = _minmax(
        pd.to_numeric(grid["mean_overlap_duration"], errors="coerce").fillna(0.0)
    )
    grid["Hazard_Peak_Intensity"] = _minmax(
        pd.to_numeric(
            grid["mean_compound_intensity_norm"], errors="coerce"
        ).fillna(0.0)
    )
    return grid


def _rho(a: pd.Series, b: pd.Series) -> float | None:
    value = a.corr(b, method="spearman")
    return None if not np.isfinite(value) else round(float(value), 6)


def _records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    return frame[columns].to_dict("records")


def main() -> None:
    for path in (MHWS_METRICS, MHWS_SUMMARY, HAT_METRICS, HAT_SUMMARY):
        if not path.exists():
            raise FileNotFoundError(path)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="osr11_mhws_hat_") as temporary:
        temporary_path = Path(temporary)
        mhws_raw = _prepare(MHWS_METRICS, temporary_path / "mhws.csv")
        hat_raw = _prepare(HAT_METRICS, temporary_path / "hat.csv")
        mhws, mhws_metadata = derive_native_hazard_index(
            temporary_path / "mhws.csv"
        )
        hat, hat_metadata = derive_native_hazard_index(temporary_path / "hat.csv")

    if len(mhws) != 808 or len(hat) != 808:
        raise AssertionError(
            f"Unequal normalization populations: MHWS={len(mhws)}, HAT={len(hat)}"
        )
    mhws = _add_diagnostics(mhws)
    hat = _add_diagnostics(hat)

    key = lambda frame: list(  # noqa: E731
        zip(frame["grid_lat"].round(6), frame["grid_lon"].round(6))
    )
    mhws["_key"] = key(mhws)
    hat["_key"] = key(hat)
    grid = mhws.merge(hat, on="_key", suffixes=("_mhws", "_hat")).drop(
        columns="_key"
    )
    grid["latitude_band"] = grid["grid_lat_mhws"].map(_band)

    municipal = load_municipal_attributes()
    risk_mhws = municipal_risk(mhws, municipal)
    risk_hat = municipal_risk(hat, municipal)
    risk = municipal[
        ["municipality_code", "municipality_name", "state", "grid_lat", "grid_lon"]
    ].copy()
    for arm, frame in (("mhws", risk_mhws), ("hat", risk_hat)):
        risk[f"Hazard_Index_{arm}"] = frame["Hazard_Index"]
        risk[f"Hazard_Index_mun_{arm}"] = frame["Hazard_Index_mun"]
        risk[f"Risk_Hazard_{arm}"] = frame["Risk_Hazard"]
    risk["Exposure_Index"] = risk_mhws["Exposure_Index"]
    risk["SVI_Coast_2022"] = municipal["SVI_Coast_2022"]

    count_lookup_mhws = dict(
        zip(key(mhws), mhws["compound_count_total"].fillna(0))
    )
    count_lookup_hat = dict(zip(key(hat), hat["compound_count_total"].fillna(0)))
    municipal_keys = list(
        zip(risk["grid_lat"].round(6), risk["grid_lon"].round(6))
    )
    risk["compound_count_total_mhws"] = [
        count_lookup_mhws.get(item, np.nan) for item in municipal_keys
    ]
    risk["compound_count_total_hat"] = [
        count_lookup_hat.get(item, np.nan) for item in municipal_keys
    ]

    valid = risk["Risk_Hazard_mhws"].notna() & risk["Risk_Hazard_hat"].notna()
    ranked = risk.loc[valid].copy()
    ranked["rank_mhws"] = ranked["Risk_Hazard_mhws"].rank(
        ascending=False, method="min"
    )
    ranked["rank_hat"] = ranked["Risk_Hazard_hat"].rank(
        ascending=False, method="min"
    )
    ranked["rank_change_hat_minus_mhws"] = (
        ranked["rank_mhws"] - ranked["rank_hat"]
    )
    top_mhws = ranked.nsmallest(10, "rank_mhws")
    top_hat = ranked.nsmallest(10, "rank_hat")
    overlap = set(top_mhws["municipality_code"]) & set(
        top_hat["municipality_code"]
    )

    component_summary: dict[str, Any] = {}
    for component in COMPONENTS:
        mhws_field = f"{component}_mhws"
        hat_field = f"{component}_hat"
        component_summary[component] = {
            "spearman_between_arms": _rho(grid[mhws_field], grid[hat_field]),
            "spearman_abs_latitude_mhws": _rho(
                grid["grid_lat_mhws"].abs(), grid[mhws_field]
            ),
            "spearman_abs_latitude_hat": _rho(
                grid["grid_lat_hat"].abs(), grid[hat_field]
            ),
            "by_latitude_band": {
                band: {
                    "n_points": int(len(subset)),
                    "mean_mhws": round(float(subset[mhws_field].mean()), 6),
                    "mean_hat": round(float(subset[hat_field].mean()), 6),
                }
                for band, subset in grid.groupby(
                    "latitude_band", observed=True
                )
            },
        }

    mhws_summary = json.loads(MHWS_SUMMARY.read_text())
    hat_summary = json.loads(HAT_SUMMARY.read_text())
    summary = {
        "generated_by": "src.exploratory.compare_methods_mhws_vs_hat",
        "status": "comparison only; HAT is not adopted",
        "normalization": {
            "policy": (
                "Both arms contain the same 808 grid points. At a point with no "
                "accepted event, frequency=0 and integrated severity=0 before "
                "calling derive_native_hazard_index."
            ),
            "mhws_grid_points": mhws_metadata["grid_point_count"],
            "hat_grid_points": hat_metadata["grid_point_count"],
            "implementation": "src/04_risk_integration/hazard_index.py",
            "reference_percentiles_mhws": mhws_summary.get(
                "rescaling_reference_percentiles"
            ),
            "reference_percentiles_hat": hat_summary[
                "rescaling_reference_percentiles"
            ],
        },
        "coverage": {
            "grid_points_zero_events_mhws": int(
                (mhws_raw["compound_count_total"] == 0).sum()
            ),
            "grid_points_zero_events_hat": int(
                (hat_raw["compound_count_total"] == 0).sum()
            ),
            "municipalities_zero_events_mhws": int(
                (ranked["compound_count_total_mhws"] == 0).sum()
            ),
            "municipalities_zero_events_hat": int(
                (ranked["compound_count_total_hat"] == 0).sum()
            ),
        },
        "components": component_summary,
        "within_arm_component_correlation": {
            "spearman_frequency_severity_mhws": _rho(
                grid["Hazard_Frequency_mhws"], grid["Hazard_Severity_mhws"]
            ),
            "spearman_frequency_severity_hat": _rho(
                grid["Hazard_Frequency_hat"], grid["Hazard_Severity_hat"]
            ),
        },
        "municipal_risk": {
            "n_municipalities": int(len(ranked)),
            "spearman_between_arms": _rho(
                ranked["Risk_Hazard_mhws"], ranked["Risk_Hazard_hat"]
            ),
            "top10_overlap_count": len(overlap),
            "top10_overlap_municipalities": sorted(
                ranked.loc[
                    ranked["municipality_code"].isin(overlap),
                    "municipality_name",
                ].tolist()
            ),
            "pct_top10_north_of_20S_mhws": round(
                float(100 * (top_mhws["grid_lat"] > -20.0).mean()), 1
            ),
            "pct_top10_north_of_20S_hat": round(
                float(100 * (top_hat["grid_lat"] > -20.0).mean()), 1
            ),
            "top10_mhws": _records(
                top_mhws,
                ["municipality_name", "state", "rank_mhws", "Risk_Hazard_mhws"],
            ),
            "top10_hat": _records(
                top_hat,
                ["municipality_name", "state", "rank_hat", "Risk_Hazard_hat"],
            ),
            "largest_rises_under_hat": _records(
                ranked.nlargest(15, "rank_change_hat_minus_mhws"),
                [
                    "municipality_name",
                    "state",
                    "rank_mhws",
                    "rank_hat",
                    "rank_change_hat_minus_mhws",
                ],
            ),
            "largest_falls_under_hat": _records(
                ranked.nsmallest(15, "rank_change_hat_minus_mhws"),
                [
                    "municipality_name",
                    "state",
                    "rank_mhws",
                    "rank_hat",
                    "rank_change_hat_minus_mhws",
                ],
            ),
        },
        "latitude_bands": [
            {"name": name, "lower": lower, "upper": upper}
            for name, lower, upper in LATITUDE_BANDS
        ],
    }
    grid.to_csv(OUT_DIR / "hazard_by_point.csv", index=False)
    ranked.sort_values("rank_hat").to_csv(
        OUT_DIR / "risk_by_municipality.csv", index=False
    )
    (OUT_DIR / "comparison_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
