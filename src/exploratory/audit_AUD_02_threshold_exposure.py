"""AUD-02 supplementary product: what the local wave threshold means, by sector
and by state, and how much of the published ranking rests on low thresholds.

AUD-02 closes as a recognised limitation: the PU calibration demonstrably does
not determine the wave axis (the six best pairs lie within 1 % of the score and
span q50-q80), and an absolute floor would have to be anchored outside the
pipeline -- in a setup/runup formulation that needs beach-face slope, the
physical layer that AUD-10 already recorded as absent. Filtering sheltered
points is equally unavailable: coastline orientation shelters points that lie in
no bay at all, so "real shelter" and "doubtful cell" cannot be separated by any
rule this repository can state.

What a recognised limitation does require is that the reader can see what the
threshold means where they live, and that the exposure of the published result
is declared rather than left to be discovered. This script produces both.

Note on sectors: the latitude bands of AUD-02 section 3 come from a partition
that is not documented anywhere in the repository and could not be reproduced --
only the two northern sectors match. The bands below are therefore stated
explicitly and are not claimed to reproduce that table.

Usage:
    python -m src.exploratory.audit_AUD_02_threshold_exposure

Output:
    outputs/audit/AUD-02_threshold_exposure/thresholds_by_latitude_band.csv
    outputs/audit/AUD-02_threshold_exposure/thresholds_by_state.csv
    outputs/audit/AUD-02_threshold_exposure/municipal_threshold_exposure.csv
    outputs/audit/AUD-02_threshold_exposure/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
HAT_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-02_threshold_exposure"

#: Explicit latitude cuts. Descriptive only; nothing downstream depends on them.
BAND_CUTS = [-35.0, -29.0, -25.3, -21.0, -18.0, -12.0, -5.0, 0.0, 7.0]
BAND_LABELS = [
    "RS (-35..-29)",
    "SC/PR (-29..-25.3)",
    "SP/RJ (-25.3..-21)",
    "ES/BA-S (-21..-18)",
    "BA-N (-18..-12)",
    "NE (-12..-5)",
    "N equatorial (-5..0)",
    "AP (0..7)",
]

#: The two marks AUD-02 section 3 counts points against.
FLOORS_M = (1.0, 1.5, 2.0)

#: Coordinates are stored at different precision in the two sources; rounding to
#: three decimals is exact for a 0.2 deg grid and makes the join total.
JOIN_PRECISION = 3


def load_points() -> pd.DataFrame:
    points = pd.read_csv(HAT_METRICS)
    points["band"] = pd.cut(
        points["grid_lat"], BAND_CUTS, labels=BAND_LABELS, ordered=False
    )
    return points


def load_municipalities() -> pd.DataFrame:
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    return frame.dropna(subset=["Risk_Hazard"]).reset_index(drop=True)


def join_municipalities_to_points(
    municipalities: pd.DataFrame, points: pd.DataFrame
) -> pd.DataFrame:
    left = municipalities.copy()
    right = points.copy()
    for frame in (left, right):
        frame["_lat"] = frame["grid_lat"].round(JOIN_PRECISION)
        frame["_lon"] = frame["grid_lon"].round(JOIN_PRECISION)
    merged = left.merge(
        right[["_lat", "_lon", "thr_hs_abs", "hat_m", "compound_count_total"]],
        on=["_lat", "_lon"],
        how="left",
    )
    unmatched = int(merged["thr_hs_abs"].isna().sum())
    if unmatched:
        raise ValueError(
            f"{unmatched} municipalities failed to join to a grid point; the "
            "coordinate join is not total and every count below would be wrong"
        )
    merged = merged.sort_values("Risk_Hazard", ascending=False).reset_index(drop=True)
    merged["rank"] = merged.index + 1
    return merged.drop(columns=["_lat", "_lon"])


def _threshold_stats(group: pd.DataFrame) -> pd.Series:
    values = group["thr_hs_abs"]
    stats = {
        "n_points": int(values.size),
        "min": float(values.min()),
        "q25": float(values.quantile(0.25)),
        "median": float(values.median()),
        "q75": float(values.quantile(0.75)),
        "max": float(values.max()),
    }
    for floor in FLOORS_M:
        stats[f"n_below_{floor:g}m"] = int((values < floor).sum())
    return pd.Series(stats)


def thresholds_by_band(points: pd.DataFrame) -> pd.DataFrame:
    table = (
        points.groupby("band", observed=True)
        .apply(_threshold_stats, include_groups=False)
        .reset_index()
    )
    return table


def thresholds_by_state(municipal: pd.DataFrame) -> pd.DataFrame:
    """Threshold summary over the points that actually feed published municipalities.

    A point serving several municipalities is counted once per municipality: the
    question this answers is what threshold underlies a published value, not how
    the grid is distributed.
    """
    table = (
        municipal.groupby("state", observed=True)
        .apply(_threshold_stats, include_groups=False)
        .reset_index()
        .rename(columns={"n_points": "n_municipalities"})
    )
    return table.sort_values("median").reset_index(drop=True)


def ranking_exposure(municipal: pd.DataFrame) -> dict[str, object]:
    """How much of the published ranking rests on low wave thresholds."""
    positive = municipal[municipal["Risk_Hazard"] > 0]
    out: dict[str, object] = {}
    for floor in FLOORS_M:
        below = municipal["thr_hs_abs"] < floor
        below_positive = positive["thr_hs_abs"] < floor
        out[f"below_{floor:g}m"] = {
            "municipalities_published": int(below.sum()),
            "municipalities_with_positive_risk": int(below_positive.sum()),
            "in_top10": int((positive.loc[below_positive, "rank"] <= 10).sum()),
            "in_top20": int((positive.loc[below_positive, "rank"] <= 20).sum()),
            "in_top50": int((positive.loc[below_positive, "rank"] <= 50).sum()),
        }
    top20 = municipal[municipal["rank"] <= 20]
    out["top20_threshold"] = {
        "min": float(top20["thr_hs_abs"].min()),
        "median": float(top20["thr_hs_abs"].median()),
        "max": float(top20["thr_hs_abs"].max()),
    }
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    points = load_points()
    municipal = join_municipalities_to_points(load_municipalities(), points)

    band_table = thresholds_by_band(points)
    state_table = thresholds_by_state(municipal)
    columns = [
        "rank", "municipality_name", "state", "grid_lat", "grid_lon",
        "thr_hs_abs", "hat_m", "compound_count_total", "Hazard_Index_mun",
        "Risk_Hazard",
    ]

    band_table.to_csv(OUT_DIR / "thresholds_by_latitude_band.csv", index=False)
    state_table.to_csv(OUT_DIR / "thresholds_by_state.csv", index=False)
    municipal[columns].to_csv(
        OUT_DIR / "municipal_threshold_exposure.csv", index=False
    )

    all_points = points["thr_hs_abs"]
    low = points[points["thr_hs_abs"] < 1.5]
    summary = {
        "sources": {
            "points": str(HAT_METRICS.relative_to(ROOT)),
            "municipalities": str(GEOJSON.relative_to(ROOT)),
        },
        "grid_points": int(all_points.size),
        "threshold_min_m": float(all_points.min()),
        "threshold_median_m": float(all_points.median()),
        "points_below_floor": {
            f"{floor:g}m": int((all_points < floor).sum()) for floor in FLOORS_M
        },
        "low_threshold_points_still_active": {
            "definition": "grid points with thr_hs_abs < 1.5 m",
            "n_points": int(len(low)),
            "n_without_accepted_event": int((low["compound_count_total"] == 0).sum()),
            "accepted_events": int(low["compound_count_total"].sum()),
            "share_of_all_accepted_events": float(
                low["compound_count_total"].sum() / points["compound_count_total"].sum()
            ),
        },
        "ranking_exposure": ranking_exposure(municipal),
        "note": (
            "The HAT gate did not empty the low-threshold points: they still "
            "carry a sixth of all accepted compound events, and the "
            "municipalities they feed are no longer the northern ones -- those "
            "are at zero hazard regardless -- but the top of the published "
            "ranking itself."
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(band_table.to_string(index=False))
    print()
    print(state_table.to_string(index=False))
    print("\nRanking exposure:")
    print(json.dumps(summary["ranking_exposure"], indent=2))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
