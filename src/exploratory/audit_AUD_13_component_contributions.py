"""AUD-13 diagnostic: how the three risk layers actually contribute, measured
against the current product.

Every number in AUD-13 sections 3.1-3.7 was taken on 2026-07-29, before the HAT
gate (AUD-01/AUD-06), the removal of the Min-Max chain and the 0.01 floor
(AUD-11), and the effective-population exposure (AUD-08). All of them describe a
product that no longer exists, and two of the diagnostics the record asks for
cannot be run as written: the variance decomposition of log(Risk_Hazard_raw) is
undefined for the 84 municipalities that now sit at exact zero.

This script re-measures the behaviour of the index on the published product and
adds the one thing the record never had to explain: the mechanism that produces
the hazard field. The HAT gate is monotonic in latitude -- the bar to clear grows
fivefold from Rio Grande do Sul to Amapa for reasons unrelated to storms -- and
that gradient, crossed with the north-south development gradient, is what drives
the hazard-vulnerability anticorrelation.

Log-based quantities are reported on the 196 municipalities with Risk_Hazard > 0
and labelled as such. Restricting the sample is a choice, not the diagnostic the
record asked for, and the outputs say so explicitly.

Usage:
    python -m src.exploratory.audit_AUD_13_component_contributions

Output:
    outputs/audit/AUD-13_component_contributions/component_behaviour.csv
    outputs/audit/AUD-13_component_contributions/rank_correlations.csv
    outputs/audit/AUD-13_component_contributions/aggregation_contrafactuals.csv
    outputs/audit/AUD-13_component_contributions/hazard_gate_latitude_gradient.csv
    outputs/audit/AUD-13_component_contributions/municipality_contributions.csv
    outputs/audit/AUD-13_component_contributions/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
HAT_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-13_component_contributions"

HAZARD = "Hazard_Index_mun"
EXPOSURE = "Exposure_Index"
VULNERABILITY = "Vulnerability_CDF_PC1"
RISK = "Risk_Hazard"
COMPONENTS = {"hazard": HAZARD, "exposure": EXPOSURE, "vulnerability": VULNERABILITY}

# Latitude bands used to expose the HAT gradient. Chosen to separate the
# extratropical sector, the SE bight, the eastern coast, the NE and the
# macrotidal north; they are descriptive, nothing downstream depends on them.
LATITUDE_BANDS = [-35.0, -28.0, -23.0, -15.0, -8.0, -2.0, 7.0]

NORTH_NORTHEAST = {
    "AP", "PA", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA",
}

SHUFFLE_DRAWS = 2000
SHUFFLE_SEED = 13


def load_municipalities() -> pd.DataFrame:
    """Municipalities carrying a risk value, from the published GeoJSON."""
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    return frame.dropna(subset=[RISK]).reset_index(drop=True)


def component_behaviour(nonzero: pd.DataFrame) -> pd.DataFrame:
    """Marginal distribution and log dispersion of each component.

    Restricted to municipalities with positive risk: sd(log) is undefined where a
    component is exactly zero.
    """
    rows = []
    for name, field in COMPONENTS.items():
        values = nonzero[field]
        rows.append(
            {
                "component": name,
                "field": field,
                "n": int(values.size),
                "min": float(values.min()),
                "p10": float(values.quantile(0.10)),
                "median": float(values.median()),
                "p90": float(values.quantile(0.90)),
                "max": float(values.max()),
                "sd_log": float(np.log(values).std(ddof=0)),
                "cv": float(values.std(ddof=0) / values.mean()),
            }
        )
    return pd.DataFrame(rows)


def variance_decomposition(nonzero: pd.DataFrame) -> dict[str, float]:
    """Covariance share of each component in var(log risk), summing to one.

    Shares may be negative: a component anticorrelated with the aggregate reduces
    the dispersion of the index instead of adding to it.
    """
    logs = {name: np.log(nonzero[field]) for name, field in COMPONENTS.items()}
    log_risk = sum(logs.values()) / 3.0
    total = float(np.var(log_risk, ddof=0))
    shares = {
        name: float(np.cov(series / 3.0, log_risk, ddof=0)[0, 1] / total)
        for name, series in logs.items()
    }
    shares["_total_var_log_risk"] = total
    return shares


def rank_correlations(frame: pd.DataFrame, label: str) -> pd.DataFrame:
    """Pairwise Spearman correlations among the components and the risk."""
    fields = {**COMPONENTS, "risk": RISK}
    rows = []
    names = list(fields)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            rows.append(
                {
                    "sample": label,
                    "pair": f"{left}~{right}",
                    "spearman": float(
                        spearmanr(frame[fields[left]], frame[fields[right]]).statistic
                    ),
                }
            )
    return pd.DataFrame(rows)


def partial_rank_correlations(nonzero: pd.DataFrame) -> dict[str, float]:
    """Partial Spearman of risk against each component, controlling the other two."""
    fields = [HAZARD, EXPOSURE, VULNERABILITY, RISK]
    precision = np.linalg.inv(np.corrcoef(nonzero[fields].rank().T.values))
    out = {}
    for index, name in enumerate(COMPONENTS):
        out[name] = float(
            -precision[index, 3] / np.sqrt(precision[index, index] * precision[3, 3])
        )
    return out


def _top_overlap(frame: pd.DataFrame, candidate: pd.Series, size: int) -> int:
    reference = set(frame.nlargest(size, RISK)["municipality_name"])
    ranked = set(
        frame.assign(_candidate=candidate).nlargest(size, "_candidate")[
            "municipality_name"
        ]
    )
    return len(reference & ranked)


def aggregation_contrafactuals(frame: pd.DataFrame, nonzero: pd.DataFrame) -> pd.DataFrame:
    """Alternative aggregations, against the published ranking.

    Reported on the full sample and on the positive-risk subset: the 84 exact
    zeros tie in the published ranking, and a variant that separates them scores
    against a block of tied ranks, which flatters or penalises it artificially.
    """
    def variants(data: pd.DataFrame) -> dict[str, pd.Series]:
        hazard, exposure, vulnerability = (
            data[HAZARD], data[EXPOSURE], data[VULNERABILITY],
        )
        return {
            "published (geometric H,E,V)": (hazard * exposure * vulnerability) ** (1 / 3),
            "arithmetic mean H,E,V": (hazard + exposure + vulnerability) / 3.0,
            "hazard = frequency only": (
                data["Hazard_Frequency"] * exposure * vulnerability
            ) ** (1 / 3),
            "hazard = severity only": (
                data["Hazard_Severity"] * exposure * vulnerability
            ) ** (1 / 3),
            "drop hazard (E x V)": (exposure * vulnerability) ** 0.5,
            "drop exposure (H x V)": (hazard * vulnerability) ** 0.5,
            "drop vulnerability (H x E)": (hazard * exposure) ** 0.5,
            "hazard alone": hazard,
            "exposure alone": exposure,
            "vulnerability alone": vulnerability,
        }

    rows = []
    for label, data in (("all_280", frame), ("positive_risk_196", nonzero)):
        for name, candidate in variants(data).items():
            rows.append(
                {
                    "sample": label,
                    "variant": name,
                    "spearman_vs_published": float(
                        spearmanr(candidate, data[RISK]).statistic
                    ),
                    "top10_overlap": _top_overlap(data, candidate, 10),
                    "top20_overlap": _top_overlap(data, candidate, 20),
                }
            )
    return pd.DataFrame(rows)


def cancellation_effect(nonzero: pd.DataFrame) -> dict[str, float]:
    """Variance compression caused by anticorrelation between component pairs.

    Each pair is broken by permuting one member, keeping both marginals intact.
    A ratio below one means the observed anticorrelation compresses the index.
    """
    rng = np.random.default_rng(SHUFFLE_SEED)
    logs = {name: np.log(nonzero[field]).to_numpy() for name, field in COMPONENTS.items()}
    observed = float(np.var(sum(logs.values()) / 3.0, ddof=0))

    out = {"observed_var_log_risk": observed}
    for broken in ("exposure", "vulnerability"):
        draws = np.empty(SHUFFLE_DRAWS)
        for draw in range(SHUFFLE_DRAWS):
            shuffled = dict(logs)
            shuffled[broken] = rng.permutation(logs[broken])
            draws[draw] = np.var(sum(shuffled.values()) / 3.0, ddof=0)
        independent = float(draws.mean())
        out[f"independent_var_breaking_{broken}"] = independent
        out[f"compression_ratio_breaking_{broken}"] = observed / independent
    return out


def hazard_gate_gradient() -> pd.DataFrame:
    """HAT, wave threshold and accepted-event counts by latitude band.

    This is the mechanism behind the hazard field, and it is the piece AUD-13
    never had: the gate is monotonic in latitude for tidal reasons, independent
    of the storm climate.
    """
    metrics = pd.read_csv(HAT_METRICS)
    metrics["band"] = pd.cut(metrics["grid_lat"], LATITUDE_BANDS)
    grouped = metrics.groupby("band", observed=True)
    table = grouped.agg(
        grid_points=("grid_lat", "size"),
        hat_m_mean=("hat_m", "mean"),
        thr_hs_abs_mean=("thr_hs_abs", "mean"),
        points_without_accepted_event=(
            "compound_count_total", lambda values: int((values == 0).sum())
        ),
        accepted_events_mean=("compound_count_total", "mean"),
        candidates_rejected_by_hat=("n_rejected_by_hat", "sum"),
    ).reset_index()
    table["band"] = table["band"].astype(str)
    return table


def municipality_contributions(nonzero: pd.DataFrame) -> pd.DataFrame:
    """Per-municipality contribution of each component to log risk.

    Expressed as departures from the median of each component, in units of that
    component's log standard deviation, so that a row reads "this municipality
    ranks where it does because V is 1.2 sd above and H 0.4 sd below".
    """
    frame = nonzero[["municipality_name", "state", RISK]].copy()
    for name, field in COMPONENTS.items():
        logs = np.log(nonzero[field])
        frame[f"{name}_z_log"] = (logs - logs.median()) / logs.std(ddof=0)
    frame["rank"] = frame[RISK].rank(ascending=False, method="min").astype(int)
    return frame.sort_values("rank").reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frame = load_municipalities()
    nonzero = frame[frame[RISK] > 0].reset_index(drop=True)

    behaviour = component_behaviour(nonzero)
    correlations = pd.concat(
        [rank_correlations(frame, "all_280"), rank_correlations(nonzero, "positive_risk_196")],
        ignore_index=True,
    )
    contrafactuals = aggregation_contrafactuals(frame, nonzero)
    gate = hazard_gate_gradient()
    contributions = municipality_contributions(nonzero)

    behaviour.to_csv(OUT_DIR / "component_behaviour.csv", index=False)
    correlations.to_csv(OUT_DIR / "rank_correlations.csv", index=False)
    contrafactuals.to_csv(OUT_DIR / "aggregation_contrafactuals.csv", index=False)
    gate.to_csv(OUT_DIR / "hazard_gate_latitude_gradient.csv", index=False)
    contributions.to_csv(OUT_DIR / "municipality_contributions.csv", index=False)

    top50 = frame.nlargest(50, RISK)
    regional = {
        f"top{size}_north_northeast": int(
            frame.nlargest(size, RISK)["state"].isin(NORTH_NORTHEAST).sum()
        )
        for size in (10, 20, 50)
    }

    summary = {
        "source": str(GEOJSON.relative_to(ROOT)),
        "municipalities_with_risk": int(len(frame)),
        "municipalities_with_positive_risk": int(len(nonzero)),
        "municipalities_at_exact_zero": int((frame[RISK] == 0).sum()),
        "risk_range": [float(frame[RISK].min()), float(frame[RISK].max())],
        "log_quantities_restricted_to": "Risk_Hazard > 0 (196 municipalities)",
        "variance_decomposition_log_risk": variance_decomposition(nonzero),
        "partial_rank_correlation_risk_vs": partial_rank_correlations(nonzero),
        "cancellation": cancellation_effect(nonzero),
        "regional_composition": regional,
        "top50_north_northeast_share": float(
            top50["state"].isin(NORTH_NORTHEAST).mean()
        ),
        "note": (
            "The variance decomposition of log(Risk_Hazard) that AUD-13 section 8 "
            "asks for is undefined on the full sample: 84 municipalities sit at "
            "exact zero. It is reported on the positive-risk subset and must be "
            "read as such."
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Municipalities with risk: {len(frame)} ({len(nonzero)} positive)")
    print("\nVariance share of log(risk):")
    for name in COMPONENTS:
        print(f"  {name:<15} {100 * summary['variance_decomposition_log_risk'][name]:6.1f} %")
    print("\nPartial rank correlation of risk against:")
    for name, value in summary["partial_rank_correlation_risk_vs"].items():
        print(f"  {name:<15} {value:+.3f}")
    print("\nHazard gate by latitude band:")
    print(gate.to_string(index=False))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
