"""AUD-07 diagnostic: how stable is the municipal ranking, and to what.

AUD-07 asks for three things: a versioned aggregation-sensitivity table, an
all-against-all agreement matrix between variants, and a bootstrap confidence
interval for the rank of each municipality. The first two transfer directly. The
third does not, and the reason matters.

The bootstrap the record specifies resamples municipalities with replacement and
"recomputes all normalisations within each resample". That design existed because
every published value depended on the sample: Min-Max anchored the hazard on its
own extremes and the risk on its own extremes, so removing or duplicating a
municipality moved everyone else (AUD-11 measured up to 0.094). Since AUD-11
replaced sample anchoring with fixed goalposts, a municipality's risk no longer
depends on which other municipalities are present, and resampling them perturbs
nothing. The design would report near-zero rank uncertainty and that would be an
artefact of the design, not evidence of robustness. This script demonstrates that
degeneracy rather than assuming it, and then measures the uncertainty that does
exist.

That uncertainty is in the hazard: 33 years of record estimate an event rate and
a mean severity, and both carry sampling error. The bootstrap here resamples the
33 years with replacement, recounts accepted compound events per grid point from
the event-level catalogue, recomputes the severity mean over the resampled years,
and propagates to the municipal risk with exposure and vulnerability held fixed.

Usage:
    python -m src.exploratory.audit_AUD_07_aggregation_sensitivity

Output:
    outputs/audit/AUD-07_aggregation_sensitivity/variant_agreement_matrix.csv
    outputs/audit/AUD-07_aggregation_sensitivity/variant_topn_stability.csv
    outputs/audit/AUD-07_aggregation_sensitivity/hazard_weight_sensitivity.csv
    outputs/audit/AUD-07_aggregation_sensitivity/rank_confidence_intervals.csv
    outputs/audit/AUD-07_aggregation_sensitivity/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
CATALOG = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-07_aggregation_sensitivity"

#: Fixed anchors adopted in AUD-11. 99 events over 33 years is 3 events/year.
FREQUENCY_GOALPOST = 99.0
SEVERITY_GOALPOST = 1.0

YEARS = list(range(1993, 2026))
DRAWS = 1000
SEED = 7
CI_LEVEL = 90.0

JOIN_PRECISION = 3


def load_municipalities() -> pd.DataFrame:
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    frame = frame.dropna(subset=["Risk_Hazard"]).reset_index(drop=True)
    frame["_lat"] = frame["grid_lat"].round(JOIN_PRECISION)
    frame["_lon"] = frame["grid_lon"].round(JOIN_PRECISION)
    return frame


def load_event_year_tables() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Per grid point and calendar year: event count and summed integrated severity."""
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    year_index = {year: position for position, year in enumerate(YEARS)}
    counts = np.zeros((len(catalog), len(YEARS)))
    severity_sums = np.zeros((len(catalog), len(YEARS)))
    points = []
    for row, point in enumerate(catalog):
        points.append(
            {
                "_lat": round(point["grid_lat"], JOIN_PRECISION),
                "_lon": round(point["grid_lon"], JOIN_PRECISION),
            }
        )
        for event in point["compound_events"]:
            column = year_index[int(event["date_start"][:4])]
            counts[row, column] += 1.0
            severity_sums[row, column] += float(event["integrated_severity"])
    return pd.DataFrame(points), counts, severity_sums


def hazard_from_counts(counts: np.ndarray, severity_sums: np.ndarray) -> np.ndarray:
    """Published hazard definition, applied to arbitrary count/severity totals."""
    total = counts.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_severity = np.where(total > 0, severity_sums.sum(axis=1) / total, 0.0)
    frequency = np.minimum(total / FREQUENCY_GOALPOST, 1.0)
    severity = np.minimum(mean_severity / SEVERITY_GOALPOST, 1.0)
    return (frequency + severity) / 2.0


def risk_from_hazard(
    hazard: np.ndarray, exposure: np.ndarray, vulnerability: np.ndarray
) -> np.ndarray:
    return np.cbrt(hazard * exposure * vulnerability)


def variant_table(frame: pd.DataFrame) -> dict[str, pd.Series]:
    """Aggregation variants a reviewer could reasonably propose."""
    hazard = frame["Hazard_Index_mun"]
    exposure = frame["Exposure_Index"]
    vulnerability = frame["Vulnerability_CDF_PC1"]
    return {
        "published (geometric H,E,V)": np.cbrt(hazard * exposure * vulnerability),
        "arithmetic mean H,E,V": (hazard + exposure + vulnerability) / 3.0,
        "hazard = frequency only": np.cbrt(
            frame["Hazard_Frequency"] * exposure * vulnerability
        ),
        "hazard = severity only": np.cbrt(
            frame["Hazard_Severity"] * exposure * vulnerability
        ),
        "components by percentile rank": np.cbrt(
            hazard.rank(pct=True) * exposure.rank(pct=True)
            * vulnerability.rank(pct=True)
        ),
        "drop hazard (E x V)": np.sqrt(exposure * vulnerability),
        "drop exposure (H x V)": np.sqrt(hazard * vulnerability),
        "drop vulnerability (H x E)": np.sqrt(hazard * exposure),
        "hazard alone": hazard,
    }


def agreement_matrix(variants: dict[str, pd.Series]) -> pd.DataFrame:
    names = list(variants)
    matrix = pd.DataFrame(index=names, columns=names, dtype=float)
    for left in names:
        for right in names:
            matrix.loc[left, right] = spearmanr(
                variants[left], variants[right]
            ).statistic
    return matrix.round(4)


def topn_stability(
    variants: dict[str, pd.Series], names: pd.Series, sizes=(5, 10, 20, 50)
) -> pd.DataFrame:
    reference = variants["published (geometric H,E,V)"]
    rows = []
    for label, values in variants.items():
        row = {"variant": label}
        for size in sizes:
            top_reference = set(names[np.argsort(-np.asarray(reference))[:size]])
            top_variant = set(names[np.argsort(-np.asarray(values))[:size]])
            row[f"top{size}"] = len(top_reference & top_variant)
        rows.append(row)
    return pd.DataFrame(rows)


def hazard_weight_sensitivity(frame: pd.DataFrame) -> pd.DataFrame:
    """Sweep the frequency/severity split of the two-component hazard.

    The record asks for a simplex over three hazard components. The hazard has
    carried two since AUD-01/AUD-06 removed duration, so the simplex is a line.
    """
    published = frame["Risk_Hazard"].to_numpy()
    names = frame["municipality_name"].to_numpy()
    top10_published = set(names[np.argsort(-published)[:10]])
    rows = []
    for weight in np.round(np.arange(0.0, 1.01, 0.1), 2):
        hazard = (
            weight * frame["Hazard_Frequency"] + (1 - weight) * frame["Hazard_Severity"]
        ).to_numpy()
        risk = risk_from_hazard(
            hazard,
            frame["Exposure_Index"].to_numpy(),
            frame["Vulnerability_CDF_PC1"].to_numpy(),
        )
        top10 = set(names[np.argsort(-risk)[:10]])
        rows.append(
            {
                "w_frequency": weight,
                "w_severity": round(1 - weight, 2),
                "spearman_vs_published": float(spearmanr(risk, published).statistic),
                "top10_overlap": len(top10_published & top10),
            }
        )
    return pd.DataFrame(rows)


def municipality_bootstrap_is_degenerate(frame: pd.DataFrame) -> dict[str, float]:
    """Show that resampling municipalities no longer perturbs any published value.

    Only sd(PC1) is estimated from the sample, and the CDF is monotone in it, so
    the vulnerability ranks -- and therefore the risk ranks -- are invariant.
    """
    rng = np.random.default_rng(SEED)
    published = frame["Risk_Hazard"].to_numpy()
    reference_ranks = pd.Series(published).rank(ascending=False, method="min")
    shifts = []
    for _ in range(200):
        keep = rng.choice(len(frame), size=len(frame), replace=True)
        subset = frame.iloc[np.unique(keep)]
        ranks = subset["Risk_Hazard"].rank(ascending=False, method="min")
        # Compare only the relative order among the municipalities retained.
        reference = reference_ranks.iloc[np.unique(keep)].rank(method="min")
        shifts.append(float((ranks.rank(method="min") - reference).abs().max()))
    return {
        "draws": 200,
        "max_relative_rank_shift_observed": float(np.max(shifts)),
        "mean_relative_rank_shift": float(np.mean(shifts)),
        "interpretation": (
            "Risk values are independent of sample membership under fixed "
            "goalposts, so the municipality bootstrap the record specifies "
            "measures nothing. Any residual shift is re-indexing, not value "
            "perturbation."
        ),
    }


def year_bootstrap(
    frame: pd.DataFrame, points: pd.DataFrame, counts: np.ndarray, severity: np.ndarray
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Resample the 33 years of record; propagate to municipal rank."""
    lookup = {(row._lat, row._lon): index for index, row in points.iterrows()}
    point_rows = np.array(
        [lookup[(lat, lon)] for lat, lon in zip(frame["_lat"], frame["_lon"])]
    )
    exposure = frame["Exposure_Index"].to_numpy()
    vulnerability = frame["Vulnerability_CDF_PC1"].to_numpy()

    identity = hazard_from_counts(counts, severity)[point_rows]
    identity_risk = risk_from_hazard(identity, exposure, vulnerability)
    if not np.allclose(identity_risk, frame["Risk_Hazard"].to_numpy(), atol=1e-3):
        raise ValueError(
            "the identity draw does not reproduce the published risk; the "
            "bootstrap would be measuring a different quantity"
        )

    rng = np.random.default_rng(SEED)
    ranks = np.empty((DRAWS, len(frame)))
    zero_counts = np.zeros(len(frame))
    for draw in range(DRAWS):
        multiplicity = np.bincount(
            rng.integers(0, len(YEARS), size=len(YEARS)), minlength=len(YEARS)
        ).astype(float)
        drawn_counts = counts * multiplicity
        drawn_severity = severity * multiplicity
        hazard = hazard_from_counts(drawn_counts, drawn_severity)[point_rows]
        risk = risk_from_hazard(hazard, exposure, vulnerability)
        zero_counts += risk == 0
        ranks[draw] = pd.Series(-risk).rank(method="min").to_numpy()

    low = (100 - CI_LEVEL) / 2
    table = pd.DataFrame(
        {
            "municipality_name": frame["municipality_name"],
            "state": frame["state"],
            "Risk_Hazard": frame["Risk_Hazard"],
            "rank_published": frame["Risk_Hazard"]
            .rank(ascending=False, method="min")
            .astype(int),
            "rank_median": np.median(ranks, axis=0),
            "rank_ci_low": np.percentile(ranks, low, axis=0),
            "rank_ci_high": np.percentile(ranks, 100 - low, axis=0),
            "share_of_draws_at_zero_risk": zero_counts / DRAWS,
        }
    ).sort_values("rank_published").reset_index(drop=True)
    table["ci_width"] = table["rank_ci_high"] - table["rank_ci_low"]

    top20 = table[table["rank_published"] <= 20]
    stats = {
        "draws": DRAWS,
        "ci_level_percent": CI_LEVEL,
        "median_ci_width_all": float(table["ci_width"].median()),
        "median_ci_width_top20": float(top20["ci_width"].median()),
        "max_ci_high_within_top10": float(
            table[table["rank_published"] <= 10]["rank_ci_high"].max()
        ),
        "n_municipalities_whose_ci_covers_rank_10": int(
            ((table["rank_ci_low"] <= 10) & (table["rank_ci_high"] >= 10)).sum()
        ),
        "n_always_zero": int((table["share_of_draws_at_zero_risk"] == 1.0).sum()),
        "n_sometimes_zero": int(
            table["share_of_draws_at_zero_risk"].between(1e-9, 1 - 1e-9).sum()
        ),
    }
    return table, stats


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_municipalities()
    points, counts, severity = load_event_year_tables()

    variants = variant_table(frame)
    names = frame["municipality_name"].to_numpy()

    matrix = agreement_matrix(variants)
    stability = topn_stability(variants, names)
    weights = hazard_weight_sensitivity(frame)
    intervals, bootstrap_stats = year_bootstrap(frame, points, counts, severity)

    matrix.to_csv(OUT_DIR / "variant_agreement_matrix.csv")
    stability.to_csv(OUT_DIR / "variant_topn_stability.csv", index=False)
    weights.to_csv(OUT_DIR / "hazard_weight_sensitivity.csv", index=False)
    intervals.to_csv(OUT_DIR / "rank_confidence_intervals.csv", index=False)

    summary = {
        "sources": {
            "municipalities": str(GEOJSON.relative_to(ROOT)),
            "event_catalogue": str(CATALOG.relative_to(ROOT)),
        },
        "municipalities": int(len(frame)),
        "years": [YEARS[0], YEARS[-1]],
        "municipality_bootstrap": municipality_bootstrap_is_degenerate(frame),
        "year_bootstrap": bootstrap_stats,
        "variant_spearman_vs_published": {
            label: float(
                spearmanr(values, variants["published (geometric H,E,V)"]).statistic
            )
            for label, values in variants.items()
        },
        "note": (
            "The bootstrap over municipalities specified in AUD-07 section 8.2 "
            "lost its rationale when AUD-11 removed sample anchoring. The "
            "uncertainty that remains is in the hazard estimate, and is "
            "measured here by resampling the 33 years of record."
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print("Spearman of each variant against the published ranking:")
    for label, value in summary["variant_spearman_vs_published"].items():
        print(f"  {label:<32} {value:+.3f}")
    print("\nHazard weight sweep:")
    print(weights.to_string(index=False))
    print("\nYear bootstrap:")
    print(json.dumps(bootstrap_stats, indent=2))
    print("\nTop-20 rank intervals:")
    print(
        intervals.head(20)[
            ["rank_published", "municipality_name", "state", "rank_ci_low",
             "rank_median", "rank_ci_high"]
        ].to_string(index=False)
    )
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
