"""AUD-01 / AUD-02 diagnostic: does the data provide a NON-ARBITRARY partition
of the coast into tide-dominated and surge-competitive sectors?

Any absolute floor on a driver (`Hs >= 1.5 m`, `surge >= 20 cm`) is arbitrary
unless anchored in a criterion, which is the objection recorded in AUD-02 §7.4.
This script tests whether a floor has to be chosen at all, by asking whether
the dimensionless ratio

    surge(q99 anomaly) / spring-neap modulation of daily high water

— computed per point by `audit_AUD_01_surge_vs_tide_magnitude.py` — separates
the 808 coastal points into distinct populations on its own.

It reports:

1. the distribution of the ratio and the largest internal gap in its sorted
   log10 values, compared with the typical gap (a gap many times the typical
   one indicates a real antimode rather than a chosen cut);
2. a coarse histogram in log space, so the bimodality can be seen rather than
   asserted;
3. the geographic coherence of the resulting partition, and where the spatial
   transition occurs;
4. whether the same partition also removes the physically empty wave
   thresholds of AUD-02, which would indicate the two issues share a
   population of points rather than being independent;
5. the cost of the partition, in grid points and in compound events excluded.

Read-only diagnostic. Does not modify the production pipeline or any published
output, and does not itself apply any partition.

Usage:
    python -m src.exploratory.audit_AUD_01_validity_domain_partition

Output:
    outputs/audit/AUD-01_validity_domain_partition/partition_summary.json
    outputs/audit/AUD-01_validity_domain_partition/ratio_histogram.csv
    outputs/audit/AUD-01_validity_domain_partition/points_with_partition.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RATIO_CSV = (
    ROOT / "outputs" / "audit" / "AUD-01_surge_vs_tide_magnitude" / "surge_vs_tide_by_point.csv"
)
METRICS_CSV = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_validity_domain_partition"

#: Fraction of the sorted distribution trimmed at each end before looking for
#: the largest gap, so an isolated outlier cannot masquerade as an antimode.
EDGE_TRIM = 0.05


def largest_internal_gap(values: np.ndarray) -> tuple[float, float, float, float]:
    """Return (lower, upper, gap, median_gap) of the largest interior gap."""
    ordered = np.sort(values)
    gaps = np.diff(ordered)
    lo = int(EDGE_TRIM * gaps.size)
    hi = int((1 - EDGE_TRIM) * gaps.size)
    k = lo + int(np.argmax(gaps[lo:hi]))
    return float(ordered[k]), float(ordered[k + 1]), float(gaps[k]), float(np.median(gaps))


def main() -> None:
    for path in (RATIO_CSV, METRICS_CSV):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run audit_AUD_01_surge_vs_tide_magnitude first."
            )

    ratio_df = pd.read_csv(RATIO_CSV)
    metrics = pd.read_csv(METRICS_CSV)

    key = lambda df: list(  # noqa: E731
        zip(df["grid_lat"].round(4), df["grid_lon"].round(4))
    )
    ratio_df["_key"] = key(ratio_df)
    metrics["_key"] = key(metrics)
    df = ratio_df.merge(
        metrics[["_key", "thr_hs_abs", "thr_ssh_total_abs", "compound_count_total"]],
        on="_key",
        how="inner",
    ).drop(columns="_key")

    ratio = df["surge_q99_over_swing"].dropna()

    # Antimode search in log space: the ratio spans two orders of magnitude, so
    # a multiplicative scale is the natural one for judging separation.
    lo_v, hi_v, gap, median_gap = largest_internal_gap(np.log10(ratio.values))
    cut = float(10 ** ((lo_v + hi_v) / 2))
    gap_ratio = gap / median_gap if median_gap > 0 else float("inf")

    counts, edges = np.histogram(np.log10(ratio.values), bins=18)
    hist = pd.DataFrame(
        {
            "log10_lower": edges[:-1],
            "log10_upper": edges[1:],
            "ratio_lower": 10 ** edges[:-1],
            "ratio_upper": 10 ** edges[1:],
            "n_points": counts,
        }
    )

    df["domain"] = np.where(
        df["surge_q99_over_swing"] >= cut, "surge_competitive", "tide_dominated"
    )
    keep = df[df["domain"] == "surge_competitive"]
    drop = df[df["domain"] == "tide_dominated"]

    aud02 = {}
    for t in (1.0, 1.5, 2.0):
        total = int((df["thr_hs_abs"] < t).sum())
        remaining = int((keep["thr_hs_abs"] < t).sum())
        aud02[f"thr_hs_below_{t}m"] = {
            "total_points": total,
            "remaining_in_valid_domain": remaining,
            "pct_removed": (100.0 * (1 - remaining / total)) if total else None,
        }

    total_events = float(df["compound_count_total"].sum())
    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_validity_domain_partition",
        "source_ratio": str(RATIO_CSV.relative_to(ROOT)),
        "n_points": int(len(df)),
        "antimode_search": {
            "method": (
                "largest interior gap in the sorted log10 ratio, edges trimmed "
                f"{EDGE_TRIM:.0%} each side"
            ),
            "gap_between_ratios": [float(10**lo_v), float(10**hi_v)],
            "derived_cut": cut,
            "gap_dex": gap,
            "median_gap_dex": median_gap,
            "gap_over_median": gap_ratio,
            "note": (
                "gap_over_median >> 1 indicates the cut sits in a genuine "
                "antimode rather than being imposed"
            ),
        },
        "partition": {
            "surge_competitive": {
                "n_points": int(len(keep)),
                "lat_min": float(keep["grid_lat"].min()),
                "lat_max": float(keep["grid_lat"].max()),
                "thr_hs_min_m": float(keep["thr_hs_abs"].min()),
                "thr_hs_p05_m": float(keep["thr_hs_abs"].quantile(0.05)),
                "thr_hs_median_m": float(keep["thr_hs_abs"].median()),
            },
            "tide_dominated": {
                "n_points": int(len(drop)),
                "lat_min": float(drop["grid_lat"].min()),
                "lat_max": float(drop["grid_lat"].max()),
                "thr_hs_min_m": float(drop["thr_hs_abs"].min()),
                "thr_hs_p05_m": float(drop["thr_hs_abs"].quantile(0.05)),
                "thr_hs_median_m": float(drop["thr_hs_abs"].median()),
            },
            "geographic_coherence": {
                "tide_dominated_points_south_of_20S": int((drop["grid_lat"] < -20).sum()),
                "surge_competitive_points_north_of_20S": int((keep["grid_lat"] > -20).sum()),
                "note": (
                    "near-perfect split at about 20-21 S, but derived from the "
                    "physical ratio rather than imposed as a latitude cut"
                ),
            },
        },
        "aud02_overlap": aud02,
        "cost_of_partition": {
            "pct_points_excluded": 100.0 * len(drop) / len(df),
            "pct_compound_events_excluded": 100.0 * float(drop["compound_count_total"].sum())
            / total_events,
        },
        "caveats": [
            "The ratio depends on GLORYS12 surge, which may be underestimated on "
            "the wide shallow Amazon shelf; the partition is conditional on the "
            "model and cannot be verified without tide gauges (AUD-18).",
            "Bimodality may be partly amplified by uneven grid-point sampling "
            "along a convoluted coastline, though the sharp spatial transition "
            "near 21-22 S has a physical basis in shelf geometry.",
            "The partition does not fully resolve AUD-02: some low wave "
            "thresholds survive inside the retained domain.",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "points_with_partition.csv", index=False)
    hist.to_csv(OUT_DIR / "ratio_histogram.csv", index=False)
    with (OUT_DIR / "partition_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
