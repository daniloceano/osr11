"""Re-evaluate the three falsifiable criteria of AUD-01 §14 on the final catalogue.

The §14 decision entry of 2026-07-30 fixed three consequences to judge the
adoption of the HAT gate by:

    (a) rho(|lat|, Hazard_Severity) clearly positive, with Amapá no longer
        tied with SC/PR;
    (b) the S->N gradient of the hazard index preserved or reinforced;
    (c) the municipal ranking stable in the South and Southeast.

Those were first measured on the comparison arm, which used the SUPERSEDED
q90/q90 threshold pair. The Step 2e recalibration changed the pair, and the
pair changes the whole catalogue, so the criteria have to be judged again on
the definitive product. This script reports BOTH sets of numbers side by side:

    MHWS              the superseded method
    HAT q90/q90       the published comparison arm
    HAT q70/q99       the definitive catalogue

Exposure, vulnerability and the grid-to-municipality association are read from
the published municipal product and are identical across all three arms by
construction, so every difference reported here comes from the detector and
the threshold pair alone.

Usage:
    conda run -n osr11 python -m src.exploratory.audit_AUD_01_final_criteria

Outputs:
    outputs/audit/AUD-01_final_criteria/criteria_summary.json
    outputs/audit/AUD-01_final_criteria/hazard_by_point.csv
    outputs/audit/AUD-01_final_criteria/risk_by_municipality.csv
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.exploratory.compare_methods_ssh_total_vs_mhws import (
    LATITUDE_BANDS,
    _band,
    load_municipal_attributes,
    municipal_risk,
)
from src.risk_integration.hazard_index import derive_native_hazard_index

ARMS = {
    "mhws": ROOT / "outputs" / "legacy_mhws_method" / "hazard" / "compound_metrics_mhws.csv",
    "hat_q90": ROOT / "outputs" / "hat_method" / "compound_metrics_hat.csv",
    "hat_final": ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv",
}
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_final_criteria"
N_POINTS = 808


def _prepare(source: Path, destination: Path) -> pd.DataFrame:
    """Apply the agreed zero-event policy before the index is derived.

    Absence of an accepted event means frequency 0 and integrated severity 0,
    never a missing value, so that every arm normalises over the same 808
    points instead of over whatever survives a dropna().
    """
    frame = pd.read_csv(source)
    for field in ("compound_count_total", "mean_integrated_severity"):
        frame[field] = pd.to_numeric(frame[field], errors="coerce").fillna(0.0)
    if len(frame) != N_POINTS:
        raise AssertionError(f"{source} has {len(frame)} points, expected {N_POINTS}")
    frame.to_csv(destination, index=False)
    return frame


def _rho(a: pd.Series, b: pd.Series) -> float | None:
    value = a.corr(b, method="spearman")
    return None if not np.isfinite(value) else round(float(value), 6)


def main() -> None:
    for path in ARMS.values():
        if not path.exists():
            raise FileNotFoundError(path)

    grids: dict[str, pd.DataFrame] = {}
    raw: dict[str, pd.DataFrame] = {}
    with tempfile.TemporaryDirectory(prefix="osr11_final_criteria_") as temporary:
        temporary_path = Path(temporary)
        for arm, source in ARMS.items():
            raw[arm] = _prepare(source, temporary_path / f"{arm}.csv")
            grid, metadata = derive_native_hazard_index(temporary_path / f"{arm}.csv")
            if metadata["grid_point_count"] != N_POINTS:
                raise AssertionError(
                    f"{arm}: normalisation population is "
                    f"{metadata['grid_point_count']}, expected {N_POINTS}"
                )
            grids[arm] = grid

    municipal = load_municipal_attributes()
    risks = {arm: municipal_risk(grid, municipal) for arm, grid in grids.items()}

    risk = municipal[
        ["municipality_code", "municipality_name", "state", "grid_lat", "grid_lon"]
    ].copy()
    for arm, frame in risks.items():
        risk[f"Risk_Hazard_{arm}"] = frame["Risk_Hazard"]
        risk[f"Hazard_Index_{arm}"] = frame["Hazard_Index"]
    for arm, frame in raw.items():
        lookup = dict(
            zip(
                zip(frame["grid_lat"].round(6), frame["grid_lon"].round(6)),
                frame["compound_count_total"],
            )
        )
        keys = list(zip(risk["grid_lat"].round(6), risk["grid_lon"].round(6)))
        risk[f"compound_count_{arm}"] = [lookup.get(k, np.nan) for k in keys]

    valid = risk[[f"Risk_Hazard_{arm}" for arm in ARMS]].notna().all(axis=1)
    ranked = risk.loc[valid].copy()
    for arm in ARMS:
        ranked[f"rank_{arm}"] = ranked[f"Risk_Hazard_{arm}"].rank(
            ascending=False, method="min"
        )

    # Criterion (c) is about the South and Southeast, the sector of highest
    # physical confidence, so it is measured there and not only domain-wide.
    south_southeast = ranked["grid_lat"] < -20.0

    def _top10(arm: str) -> pd.DataFrame:
        return ranked.nsmallest(10, f"rank_{arm}")

    summary: dict = {
        "generated_by": "src.exploratory.audit_AUD_01_final_criteria",
        "arms": {arm: str(path.relative_to(ROOT)) for arm, path in ARMS.items()},
        "note": (
            "The §14 criteria were fixed before execution and first measured on "
            "the q90/q90 comparison arm. The Step 2e recalibration changed the "
            "threshold pair, which changes the whole catalogue, so both sets of "
            "numbers are reported."
        ),
        "coverage": {
            arm: {
                "domain_events": int(frame["compound_count_total"].sum()),
                "grid_points_zero_events": int(
                    (frame["compound_count_total"] == 0).sum()
                ),
                "municipalities_zero_events": int(
                    (ranked[f"compound_count_{arm}"] == 0).sum()
                ),
            }
            for arm, frame in raw.items()
        },
        "criterion_a_severity_latitude": {
            arm: {
                "spearman_abs_latitude": _rho(
                    grid["grid_lat"].abs(), grid["Hazard_Severity"]
                ),
                "mean_severity_by_band": {
                    band: round(
                        float(
                            grid.loc[
                                grid["grid_lat"].map(_band) == band, "Hazard_Severity"
                            ].mean()
                        ),
                        6,
                    )
                    for band, _, _ in LATITUDE_BANDS
                },
            }
            for arm, grid in grids.items()
        },
        "criterion_b_index_gradient": {
            arm: {
                "spearman_abs_latitude": _rho(
                    grid["grid_lat"].abs(), grid["Hazard_Index"]
                ),
                "mean_index_by_band": {
                    band: round(
                        float(
                            grid.loc[
                                grid["grid_lat"].map(_band) == band, "Hazard_Index"
                            ].mean()
                        ),
                        6,
                    )
                    for band, _, _ in LATITUDE_BANDS
                },
            }
            for arm, grid in grids.items()
        },
        "criterion_c_municipal_stability": {
            "n_municipalities": int(len(ranked)),
            "n_municipalities_south_southeast": int(south_southeast.sum()),
            "vs_mhws": {
                arm: {
                    "spearman_risk_domain": _rho(
                        ranked["Risk_Hazard_mhws"], ranked[f"Risk_Hazard_{arm}"]
                    ),
                    "spearman_risk_south_southeast": _rho(
                        ranked.loc[south_southeast, "Risk_Hazard_mhws"],
                        ranked.loc[south_southeast, f"Risk_Hazard_{arm}"],
                    ),
                    "top10_overlap_count": len(
                        set(_top10("mhws")["municipality_code"])
                        & set(_top10(arm)["municipality_code"])
                    ),
                    "pct_top10_north_of_20S": round(
                        float(100 * (_top10(arm)["grid_lat"] > -20.0).mean()), 1
                    ),
                    "median_abs_rank_change_south_southeast": round(
                        float(
                            (
                                ranked.loc[south_southeast, "rank_mhws"]
                                - ranked.loc[south_southeast, f"rank_{arm}"]
                            ).abs().median()
                        ),
                        1,
                    ),
                }
                for arm in ("hat_q90", "hat_final")
            },
            "tracked_municipalities": {
                name: {
                    f"rank_{arm}": int(row[f"rank_{arm}"]) for arm in ARMS
                }
                for name, row in (
                    (r["municipality_name"], r)
                    for _, r in ranked[
                        ranked["municipality_name"].isin(
                            ["Itajaí", "Bombinhas", "Presidente Kennedy", "Navegantes",
                             "São José do Norte", "São Sebastião", "Bertioga"]
                        )
                    ].iterrows()
                )
            },
            "top10_final": [
                {
                    "municipality_name": row["municipality_name"],
                    "state": row["state"],
                    "rank": int(row["rank_hat_final"]),
                    "Risk_Hazard": round(float(row["Risk_Hazard_hat_final"]), 6),
                }
                for _, row in _top10("hat_final").sort_values("rank_hat_final").iterrows()
            ],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    merged = grids["mhws"][["grid_lat", "grid_lon"]].copy()
    for arm, grid in grids.items():
        for field in ("Hazard_Frequency", "Hazard_Severity", "Hazard_Index"):
            merged[f"{field}_{arm}"] = grid[field].to_numpy()
    merged.to_csv(OUT_DIR / "hazard_by_point.csv", index=False)
    ranked.sort_values("rank_hat_final").to_csv(
        OUT_DIR / "risk_by_municipality.csv", index=False
    )
    (OUT_DIR / "criteria_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
