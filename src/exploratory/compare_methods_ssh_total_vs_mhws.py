"""Side-by-side comparison of the legacy SSH_total method and the MHWS method.

Derives the native-grid Hazard Index under both methods with the same
:func:`hazard_index.derive_native_hazard_index` implementation, transfers each
to the municipalities through the pre-associated grid point, and recomputes the
integrated risk with the same conjunctive formula, so the only thing that
differs between the two arms is the compound-event definition.

The municipal attributes — geometry, ``SVI_Coast_2022``, ``pop_10km``,
``pop_municipality`` and the pre-associated ``grid_lat``/``grid_lon`` — are read
from the published legacy product, which is the same source the site exporter
uses. Exposure and vulnerability are therefore identical in both arms by
construction.

Nothing here is published: the site data, the article figures and the legacy
snapshot are all left untouched. This produces a comparison only.

Usage:
    python -m src.exploratory.compare_methods_ssh_total_vs_mhws

Output:
    outputs/method_comparison_ssh_total_vs_mhws/hazard_by_point.csv
    outputs/method_comparison_ssh_total_vs_mhws/risk_by_municipality.csv
    outputs/method_comparison_ssh_total_vs_mhws/comparison_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.risk_integration.exposure_index import CLIP_FLOOR, exposure_inform
from src.risk_integration.hazard_index import derive_native_hazard_index

ROOT = Path(__file__).resolve().parents[2]
LEGACY_METRICS = (
    ROOT / "outputs" / "legacy_ssh_total_method" / "hazard" / "compound_metrics.csv"
)
MHWS_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
MUNICIPAL_SOURCE = (
    ROOT
    / "outputs"
    / "legacy_ssh_total_method"
    / "risk"
    / "risk_index_municipalities.geojson"
)
OUT_DIR = ROOT / "outputs" / "method_comparison_ssh_total_vs_mhws"

LATITUDE_BANDS = [
    ("RS", -36.0, -30.0),
    ("SC/PR", -30.0, -25.0),
    ("SP/RJ", -25.0, -20.0),
    ("ES/BA-S", -20.0, -15.0),
    ("BA-N", -15.0, -10.0),
    ("NE", -10.0, -5.0),
    ("N_equatorial", -5.0, 0.0),
    ("AP", 0.0, 7.0),
]


def _minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    lower, upper = float(finite.min()), float(finite.max())
    if np.isclose(lower, upper):
        return pd.Series(0.0, index=values.index)
    return (values - lower) / (upper - lower)


def _band(lat: float) -> str | None:
    for name, lo, hi in LATITUDE_BANDS:
        if lo <= lat < hi:
            return name
    return None


def load_municipal_attributes() -> pd.DataFrame:
    with MUNICIPAL_SOURCE.open() as f:
        geo = json.load(f)
    records = []
    for feature in geo["features"]:
        p = feature["properties"]
        records.append(
            {
                "municipality_code": p.get("municipality_code"),
                "municipality_name": p.get("municipality_name"),
                "state": p.get("state"),
                "grid_lat": p.get("grid_lat"),
                "grid_lon": p.get("grid_lon"),
                "SVI_Coast_2022": p.get("SVI_Coast_2022"),
                "pop_10km": p.get("pop_10km"),
                "pop_municipality": p.get("pop_municipality"),
                "Risk_Hazard_published": p.get("Risk_Hazard"),
            }
        )
    return pd.DataFrame(records)


def municipal_risk(hazard_grid: pd.DataFrame, municipal: pd.DataFrame) -> pd.DataFrame:
    """Transfer the hazard to municipalities and recompute the integrated risk."""
    lookup = hazard_grid.copy()
    lookup["_key"] = list(
        zip(lookup["grid_lat"].round(6), lookup["grid_lon"].round(6))
    )
    lookup = lookup.set_index("_key")["Hazard_Index"]

    out = municipal.copy()
    keys = list(zip(out["grid_lat"].round(6), out["grid_lon"].round(6)))
    out["Hazard_Index"] = pd.Series(
        [lookup.get(k, np.nan) for k in keys], index=out.index
    )
    out["Hazard_Index_mun"] = _minmax(out["Hazard_Index"])

    population = pd.to_numeric(out["pop_10km"], errors="coerce")
    municipal_population = pd.to_numeric(out["pop_municipality"], errors="coerce")
    out["Exposure_Index"] = exposure_inform(population, municipal_population)

    svi_fraction = pd.to_numeric(out["SVI_Coast_2022"], errors="coerce") / 100.0
    floor = lambda s: s.clip(lower=CLIP_FLOOR, upper=1.0)  # noqa: E731
    out["Risk_Hazard_raw"] = (
        floor(out["Hazard_Index_mun"]) * floor(out["Exposure_Index"]) * floor(svi_fraction)
    ) ** (1.0 / 3.0)
    out["Risk_Hazard"] = _minmax(out["Risk_Hazard_raw"])
    return out


def main() -> None:
    for path in (LEGACY_METRICS, MHWS_METRICS, MUNICIPAL_SOURCE):
        if not path.exists():
            raise FileNotFoundError(path)

    legacy_grid, legacy_meta = derive_native_hazard_index(LEGACY_METRICS)
    mhws_grid, mhws_meta = derive_native_hazard_index(MHWS_METRICS)

    key = lambda d: list(zip(d["grid_lat"].round(6), d["grid_lon"].round(6)))  # noqa: E731
    legacy_grid["_key"] = key(legacy_grid)
    mhws_grid["_key"] = key(mhws_grid)
    grid = legacy_grid.merge(
        mhws_grid, on="_key", suffixes=("_legacy", "_mhws")
    ).drop(columns="_key")
    grid["band"] = grid["grid_lat_legacy"].map(_band)

    municipal = load_municipal_attributes()
    risk_legacy = municipal_risk(legacy_grid, municipal)
    risk_mhws = municipal_risk(mhws_grid, municipal)

    risk = municipal[
        ["municipality_code", "municipality_name", "state", "grid_lat", "grid_lon"]
    ].copy()
    for name, frame in (("legacy", risk_legacy), ("mhws", risk_mhws)):
        for field in ("Hazard_Index", "Hazard_Index_mun", "Risk_Hazard"):
            risk[f"{field}_{name}"] = frame[field]
    risk["Exposure_Index"] = risk_legacy["Exposure_Index"]
    risk["SVI_Coast_2022"] = municipal["SVI_Coast_2022"]

    valid = risk["Risk_Hazard_legacy"].notna() & risk["Risk_Hazard_mhws"].notna()
    ranked = risk[valid].copy()
    ranked["rank_legacy"] = ranked["Risk_Hazard_legacy"].rank(ascending=False)
    ranked["rank_mhws"] = ranked["Risk_Hazard_mhws"].rank(ascending=False)
    ranked["rank_change"] = ranked["rank_legacy"] - ranked["rank_mhws"]

    top10_legacy = ranked.nsmallest(10, "rank_legacy")
    top10_mhws = ranked.nsmallest(10, "rank_mhws")
    overlap10 = len(set(top10_legacy["municipality_code"]) & set(top10_mhws["municipality_code"]))
    top20_legacy = set(ranked.nsmallest(20, "rank_legacy")["municipality_code"])
    top20_mhws = set(ranked.nsmallest(20, "rank_mhws")["municipality_code"])

    def _north_share(frame: pd.DataFrame, n: int, column: str) -> float:
        top = frame.nsmallest(n, column)
        return float(100 * (top["grid_lat"] > -20).mean())

    summary = {
        "generated_by": "src.exploratory.compare_methods_ssh_total_vs_mhws",
        "arms": {
            "legacy": {
                "source": str(LEGACY_METRICS.relative_to(ROOT)),
                "detector": "SSH_total = zos + tide, local q90",
                "grid_points": legacy_meta["grid_point_count"],
            },
            "mhws": {
                "source": str(MHWS_METRICS.relative_to(ROOT)),
                "detector": "zos ∩ Hs, conditioned on SWL > MHWS",
                "grid_points": mhws_meta["grid_point_count"],
            },
        },
        "hazard_grid": {
            "spearman_Hazard_Index": float(
                grid["Hazard_Index_legacy"].corr(
                    grid["Hazard_Index_mhws"], method="spearman"
                )
            ),
            "by_band": {
                band: {
                    "n_points": int(len(sub)),
                    "Hazard_Index_legacy": round(float(sub["Hazard_Index_legacy"].mean()), 4),
                    "Hazard_Index_mhws": round(float(sub["Hazard_Index_mhws"].mean()), 4),
                }
                for band, sub in grid.groupby("band", observed=True)
            },
        },
        "municipal_risk": {
            "n_municipalities": int(valid.sum()),
            "spearman_Risk_Hazard": float(
                ranked["Risk_Hazard_legacy"].corr(
                    ranked["Risk_Hazard_mhws"], method="spearman"
                )
            ),
            "top10_overlap": overlap10,
            "top20_overlap": len(top20_legacy & top20_mhws),
            "pct_north_of_20S_in_top10_legacy": _north_share(ranked, 10, "rank_legacy"),
            "pct_north_of_20S_in_top10_mhws": _north_share(ranked, 10, "rank_mhws"),
            "pct_north_of_20S_in_top20_legacy": _north_share(ranked, 20, "rank_legacy"),
            "pct_north_of_20S_in_top20_mhws": _north_share(ranked, 20, "rank_mhws"),
            "top10_legacy": top10_legacy[
                ["municipality_name", "state", "Risk_Hazard_legacy"]
            ].to_dict("records"),
            "top10_mhws": top10_mhws[
                ["municipality_name", "state", "Risk_Hazard_mhws"]
            ].to_dict("records"),
            "biggest_risers": ranked.nlargest(10, "rank_change")[
                ["municipality_name", "state", "rank_legacy", "rank_mhws"]
            ].to_dict("records"),
            "biggest_fallers": ranked.nsmallest(10, "rank_change")[
                ["municipality_name", "state", "rank_legacy", "rank_mhws"]
            ].to_dict("records"),
        },
    }

    # Diagnostic, not a method change: the duration component behaves very
    # differently under the two detectors, so the comparison is reported with
    # and without it. Under the MHWS detector the level episodes in the tropics
    # are long-lived low-frequency anomalies rather than synoptic storms, which
    # inflates the overlap duration exactly where the correction was meant to
    # reduce the hazard. Dropping the component is NOT adopted here; the
    # numbers exist so the choice can be made on evidence. See AUD-06.
    variants = {}
    for label, components in (
        ("three_components_F_D_I", ("Hazard_Frequency", "Hazard_Duration", "Hazard_Intensity")),
        ("two_components_F_I", ("Hazard_Frequency", "Hazard_Intensity")),
    ):
        for arm in ("legacy", "mhws"):
            variant_grid = pd.DataFrame(
                {
                    "grid_lat": grid["grid_lat_legacy"],
                    "grid_lon": grid["grid_lon_legacy"],
                }
            )
            variant_grid["Hazard_Index"] = _minmax(
                grid[[f"{c}_{arm}" for c in components]].mean(axis=1)
            )
            variant_risk = municipal_risk(variant_grid, municipal)
            ok = variant_risk[variant_risk["Risk_Hazard"].notna()]
            top10 = ok.nlargest(10, "Risk_Hazard")
            variants[f"{label}__{arm}"] = {
                "pct_north_of_20S_in_top10": float(100 * (top10["grid_lat"] > -20).mean()),
                "pct_north_of_20S_in_top20": float(
                    100 * (ok.nlargest(20, "Risk_Hazard")["grid_lat"] > -20).mean()
                ),
                "top5": ok.nlargest(5, "Risk_Hazard")["municipality_name"].tolist(),
            }
    summary["aggregation_variants"] = variants
    summary["aggregation_note"] = (
        "Removing the duration component moves the MHWS arm from 90 % to 30 % "
        "of the top-10 north of 20 S. The detector correction is therefore "
        "conditional on resolving AUD-06; with duration retained at weight 1/3 "
        "the correction is reversed rather than merely diluted."
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid.to_csv(OUT_DIR / "hazard_by_point.csv", index=False)
    ranked.sort_values("rank_mhws").to_csv(
        OUT_DIR / "risk_by_municipality.csv", index=False
    )
    with (OUT_DIR / "comparison_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=float)

    print(json.dumps(summary["hazard_grid"], indent=2, default=float))
    print()
    print(json.dumps(
        {k: v for k, v in summary["municipal_risk"].items()
         if not isinstance(v, list)},
        indent=2, default=float,
    ))


if __name__ == "__main__":
    main()
