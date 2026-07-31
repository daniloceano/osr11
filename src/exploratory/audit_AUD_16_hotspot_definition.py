"""AUD-16 diagnostic: is there anything in the risk distribution that a
"hotspot" could mean?

The record asks whether discrete hotspots exist, how sensitive any cut is, and
whether spatial autocorrelation offers a statistically grounded definition. Three
things changed since it was written and each moves the question.

First, the risk index no longer spans 0-1 by Min-Max: AUD-11 replaced sample
anchoring with fixed goalposts, so class limits now keep their meaning across
regenerations. The record's objection that equal intervals over a Min-Max scale
give a false impression of absolute meaning no longer applies; the scale is the
same one next time.

Second, 84 municipalities sit at exactly zero. The record's premise -- "unimodal,
no natural break anywhere" -- is false against the current product: a point mass
at zero is a natural break, and it is the only unambiguous one. The question
becomes whether the 196 positive values hold any further structure.

Third, AUD-07 produced rank confidence intervals from a bootstrap over the record
period, which makes the record's diagnostic 4 -- define a hotspot by the interval,
not by the point estimate -- executable for the first time.

Unimodality is tested by Silverman's critical-bandwidth bootstrap rather than
Hartigan's dip, and natural breaks by one-dimensional Fisher-Jenks via k-means,
because diptest, jenkspy and libpysal are not available in this environment and a
paper repository is not the place to add dependencies for three numbers.

Usage:
    python -m src.exploratory.audit_AUD_16_hotspot_definition

Output:
    outputs/audit/AUD-16_hotspot_definition/distribution_structure.json
    outputs/audit/AUD-16_hotspot_definition/jenks_classes.csv
    outputs/audit/AUD-16_hotspot_definition/cut_sensitivity.csv
    outputs/audit/AUD-16_hotspot_definition/class_scheme_comparison.csv
    outputs/audit/AUD-16_hotspot_definition/interval_based_hotspots.csv
    outputs/audit/AUD-16_hotspot_definition/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
RANK_CI = (
    ROOT / "outputs" / "audit" / "AUD-07_aggregation_sensitivity"
    / "rank_confidence_intervals.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-16_hotspot_definition"

RISK = "Risk_Hazard"
#: Equal-interval scheme currently published, after the AUD-11 rescale.
PUBLISHED_BOUNDARIES = [0.0, 0.000001, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

SILVERMAN_DRAWS = 500
SEED = 16
GRID_POINTS = 2048


def load() -> gpd.GeoDataFrame:
    frame = gpd.read_file(GEOJSON)
    return frame[frame[RISK].notna()].reset_index(drop=True)


def _count_modes(sample: np.ndarray, bandwidth: float) -> int:
    kde = gaussian_kde(sample, bw_method=bandwidth / sample.std(ddof=1))
    grid = np.linspace(sample.min(), sample.max(), GRID_POINTS)
    density = kde(grid)
    return int(np.sum((density[1:-1] > density[:-2]) & (density[1:-1] > density[2:])))


def _critical_bandwidth(sample: np.ndarray, modes: int = 1) -> float:
    """Smallest bandwidth whose Gaussian KDE has at most `modes` modes."""
    low, high = 1e-4, float(sample.std(ddof=1) * 3)
    for _ in range(60):
        mid = (low + high) / 2
        if _count_modes(sample, mid) > modes:
            low = mid
        else:
            high = mid
    return high


def silverman_unimodality(sample: np.ndarray) -> dict[str, float]:
    """Silverman (1981) critical-bandwidth bootstrap test of unimodality.

    H0: the density has one mode. Small p rejects unimodality.
    """
    rng = np.random.default_rng(SEED)
    h_crit = _critical_bandwidth(sample, modes=1)
    n = sample.size
    scale = 1.0 / np.sqrt(1.0 + h_crit**2 / sample.var(ddof=1))
    mean = sample.mean()
    exceed = 0
    for _ in range(SILVERMAN_DRAWS):
        base = rng.choice(sample, size=n, replace=True)
        smoothed = mean + scale * (base - mean + h_crit * rng.standard_normal(n))
        if _count_modes(smoothed, h_crit) > 1:
            exceed += 1
    return {
        "n": int(n),
        "critical_bandwidth": float(h_crit),
        "draws": SILVERMAN_DRAWS,
        "p_value": float(exceed / SILVERMAN_DRAWS),
        "reject_unimodality_at_5pct": bool(exceed / SILVERMAN_DRAWS < 0.05),
    }


def jenks_classes(values: np.ndarray, max_classes: int = 8) -> pd.DataFrame:
    """Fisher-Jenks natural breaks via one-dimensional k-means, with GVF.

    In one dimension k-means converges to the Fisher optimum given enough
    restarts, which is why no dedicated Jenks dependency is needed here.
    """
    total_deviation = float(((values - values.mean()) ** 2).sum())
    rows = []
    for k in range(2, max_classes + 1):
        model = KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(
            values.reshape(-1, 1)
        )
        labels = model.labels_
        within = sum(
            float(((values[labels == c] - values[labels == c].mean()) ** 2).sum())
            for c in range(k)
        )
        edges = sorted(
            float(values[labels == c].max()) for c in range(k)
        )
        rows.append(
            {
                "n_classes": k,
                "gvf": (total_deviation - within) / total_deviation,
                "upper_bounds": ";".join(f"{edge:.4f}" for edge in edges),
            }
        )
    return pd.DataFrame(rows)


def cut_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Which municipalities a hotspot cut selects, by rule."""
    ordered = frame.sort_values(RISK, ascending=False).reset_index(drop=True)
    names = ordered["municipality_name"].to_numpy()
    positive = ordered[ordered[RISK] > 0]
    rows = []
    for size in (5, 10, 15, 20, 30, 50):
        rows.append(
            {
                "rule": f"top-{size}",
                "n_selected": size,
                "threshold_value": float(ordered[RISK].iloc[size - 1]),
                "members": ";".join(names[:size]),
            }
        )
    for percentile in (90, 95, 99):
        cut = float(np.percentile(frame[RISK], percentile))
        selected = ordered[ordered[RISK] > cut]
        rows.append(
            {
                "rule": f"p{percentile} of all 280",
                "n_selected": int(len(selected)),
                "threshold_value": cut,
                "members": ";".join(selected["municipality_name"]),
            }
        )
    for percentile in (90, 95, 99):
        cut = float(np.percentile(positive[RISK], percentile))
        selected = ordered[ordered[RISK] > cut]
        rows.append(
            {
                "rule": f"p{percentile} of the 196 positive",
                "n_selected": int(len(selected)),
                "threshold_value": cut,
                "members": ";".join(selected["municipality_name"]),
            }
        )
    return pd.DataFrame(rows)


def interval_based_hotspots(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """AUD-16 diagnostic 4: define a hotspot by the rank interval, not the point.

    A municipality qualifies at level N when its 90 % interval stays inside the
    first N positions, i.e. it never leaves the band across the resampled record.
    """
    intervals = pd.read_csv(RANK_CI)
    merged = frame.merge(
        intervals[["municipality_name", "state", "rank_published", "rank_ci_low",
                   "rank_ci_high", "share_of_draws_at_zero_risk"]],
        on=["municipality_name", "state"],
        how="left",
    )
    counts = {}
    for size in (10, 20, 30, 50):
        robust = merged["rank_ci_high"] <= size
        counts[f"robustly_within_top{size}"] = int(robust.sum())
        counts[f"published_top{size}_that_are_robust"] = int(
            (robust & (merged["rank_published"] <= size)).sum()
        )
    table = (
        merged.sort_values("rank_published")
        .loc[
            :,
            ["rank_published", "municipality_name", "state", RISK, "rank_ci_low",
             "rank_ci_high", "share_of_draws_at_zero_risk"],
        ]
        .head(60)
        .reset_index(drop=True)
    )
    table["robust_top10"] = table["rank_ci_high"] <= 10
    table["robust_top20"] = table["rank_ci_high"] <= 20
    return table, counts


def class_scheme_comparison(values: np.ndarray, jenks: pd.DataFrame) -> pd.DataFrame:
    """Class counts under equal intervals, quantiles and natural breaks."""
    rows = []
    published = pd.cut(
        values, bins=PUBLISHED_BOUNDARIES, include_lowest=True, right=True
    )
    for interval, count in published.value_counts().sort_index().items():
        rows.append(
            {"scheme": "published equal intervals", "class": str(interval),
             "n": int(count)}
        )
    quantile_edges = [0.0] + list(np.percentile(values[values > 0], [20, 40, 60, 80, 100]))
    quantile_classes = pd.cut(values, bins=quantile_edges, include_lowest=True)
    for interval, count in quantile_classes.value_counts().sort_index().items():
        rows.append(
            {"scheme": "quantiles of positive values", "class": str(interval),
             "n": int(count)}
        )
    best = jenks.iloc[(jenks["gvf"] - 0.9).abs().argsort().iloc[0]]
    edges = [0.0] + [float(x) for x in best["upper_bounds"].split(";")]
    jenks_classes_cut = pd.cut(values, bins=sorted(set(edges)), include_lowest=True)
    for interval, count in jenks_classes_cut.value_counts().sort_index().items():
        rows.append(
            {"scheme": f"Fisher-Jenks k={int(best['n_classes'])}",
             "class": str(interval), "n": int(count)}
        )
    return pd.DataFrame(rows)


def spatial_autocorrelation_feasibility(frame: gpd.GeoDataFrame) -> dict:
    """Global Moran's I, and how much of it pseudo-replication can explain.

    Municipalities sharing a grid point carry an identical hazard by construction
    (AUD-04). Where such pairs are also spatial neighbours, any measured spatial
    autocorrelation is partly an artefact of the association, not a property of
    the risk field -- which is what decides whether Getis-Ord Gi* is usable here.
    """
    geometry = frame.geometry
    joined = gpd.sjoin(
        gpd.GeoDataFrame(geometry=geometry).reset_index(),
        gpd.GeoDataFrame(geometry=geometry).reset_index(),
        predicate="intersects",
    )
    pairs = joined[joined["index_left"] != joined["index_right"]]
    left = pairs["index_left"].to_numpy()
    right = pairs["index_right"].to_numpy()

    point_key = (
        frame["grid_lat"].round(3).astype(str) + "_" + frame["grid_lon"].round(3).astype(str)
    ).to_numpy()
    same_point = point_key[left] == point_key[right]

    values = frame[RISK].to_numpy()
    deviation = values - values.mean()
    weight_sum = float(len(left))
    numerator = float((deviation[left] * deviation[right]).sum())
    morans_i = (len(values) / weight_sum) * numerator / float((deviation**2).sum())

    return {
        "n_municipalities": int(len(frame)),
        "n_distinct_grid_points": int(pd.unique(point_key).size),
        "max_municipalities_per_point": int(pd.Series(point_key).value_counts().max()),
        "n_contiguity_pairs": int(len(left)),
        "share_of_neighbour_pairs_sharing_a_grid_point": float(same_point.mean()),
        "global_morans_I_risk": float(morans_i),
        "interpretation": (
            "Neighbour pairs that share a grid point have identical hazard by "
            "construction, so Gi* would measure the association geometry as much "
            "as the risk field."
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frame = load()
    values = frame[RISK].to_numpy()
    positive = values[values > 0]

    structure = {
        "n_municipalities": int(values.size),
        "n_exact_zero": int((values == 0).sum()),
        "n_positive": int(positive.size),
        "risk_range": [float(values.min()), float(values.max())],
        "zero_inflation_note": (
            "The point mass at zero is the one unambiguous natural break in the "
            "distribution. It is a category, not the lowest class of a gradient: "
            "no accepted compound event in 1993-2025."
        ),
        "silverman_unimodality_positive_values": silverman_unimodality(positive),
        "silverman_unimodality_all_values": silverman_unimodality(values),
    }

    jenks = jenks_classes(positive)
    cuts = cut_sensitivity(frame)
    schemes = class_scheme_comparison(values, jenks)
    intervals, interval_counts = interval_based_hotspots(frame)
    spatial = spatial_autocorrelation_feasibility(frame)

    with (OUT_DIR / "distribution_structure.json").open("w", encoding="utf-8") as handle:
        json.dump(structure, handle, indent=2, ensure_ascii=False)
    jenks.to_csv(OUT_DIR / "jenks_classes.csv", index=False)
    cuts.to_csv(OUT_DIR / "cut_sensitivity.csv", index=False)
    schemes.to_csv(OUT_DIR / "class_scheme_comparison.csv", index=False)
    intervals.to_csv(OUT_DIR / "interval_based_hotspots.csv", index=False)

    summary = {
        "source": str(GEOJSON.relative_to(ROOT)),
        "distribution": structure,
        "jenks_gvf": {int(r.n_classes): round(r.gvf, 4) for r in jenks.itertuples()},
        "interval_based_hotspot_counts": interval_counts,
        "spatial_autocorrelation": spatial,
        "note": (
            "Class limits are now stable across regenerations because AUD-11 "
            "replaced sample anchoring with fixed goalposts; the record's "
            "objection to equal intervals over a Min-Max scale no longer applies."
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(json.dumps(structure["silverman_unimodality_positive_values"], indent=2))
    print("\nFisher-Jenks GVF by class count:")
    print(jenks.to_string(index=False))
    print("\nInterval-based hotspot counts:")
    print(json.dumps(interval_counts, indent=2))
    print("\nSpatial autocorrelation feasibility:")
    print(json.dumps(spatial, indent=2))
    print("\nCut sensitivity:")
    print(cuts[["rule", "n_selected", "threshold_value"]].to_string(index=False))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
