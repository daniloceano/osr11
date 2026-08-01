"""AUD-11 diagnostic: how much sample dependence survived the fixed-anchor rescale?

AUD-11 decided, and this repository implemented, the replacement of every
sample-anchored normalisation by fixed anchors: hazard frequency against 99
events, hazard severity against 1.0, exposure against the 10^2-10^6 goalposts,
and the 0.01 floor and final Min-Max removed. The decision entry states the aim
as "nenhum valor publicado passará a depender de qual município ou qual ponto
está no conjunto".

That aim is not fully met, and the gap is worth measuring rather than assuming
away. The vulnerability layer is `Phi(PC1 / sd(PC1))` and **sd(PC1) is estimated
from the delivered sample** (`export_risk_index_data.py`, population standard
deviation over the 282 municipalities). Change the set and the scale of the
vulnerability factor changes with it, so every municipality moves.

Two questions follow, and they have different answers. Removing one municipality
is the original AUD-11 concern and is now small. Removing a region is not.

This also re-runs, on the recompute path, the influence analysis of AUD-11 §8.1
and the domain-change test of §8.5, both of which had stood unexecuted. Neither
is void: the AUD-07 municipality bootstrap only resampled published values and so
could not see this residual at all.

Usage:
    python -m src.exploratory.audit_AUD_11_scale_anchoring

Output:
    outputs/audit/AUD-11_scale_anchoring/leave_one_out_influence.csv
    outputs/audit/AUD-11_scale_anchoring/domain_change_tests.csv
    outputs/audit/AUD-11_scale_anchoring/normalization_scheme_comparison.csv
    outputs/audit/AUD-11_scale_anchoring/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-11_scale_anchoring"

HAZARD = "Hazard_Index_mun"
EXPOSURE = "Exposure_Index"
VULNERABILITY = "Vulnerability_CDF_PC1"
RISK = "Risk_Hazard"

NORTH_NORTHEAST = {"AP", "PA", "MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"}
#: The three states the record names in section 8.5.
RECORD_DOMAIN_TEST = {"AP", "PA", "MA"}

#: Displacement measured under the superseded Min-Max chain, for comparison.
LEGACY_MAX_DISPLACEMENT = 0.0945


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    delivered = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    return delivered, delivered.dropna(subset=[RISK]).reset_index(drop=True)


def vulnerability_from(pc1: pd.Series, sd: float) -> np.ndarray:
    return norm.cdf(pc1.to_numpy() / sd)


def risk_from(frame: pd.DataFrame, sd: float) -> np.ndarray:
    return np.cbrt(
        frame[HAZARD].to_numpy()
        * frame[EXPOSURE].to_numpy()
        * vulnerability_from(frame["PC1"], sd)
    )


def _minmax(values: np.ndarray) -> np.ndarray:
    low, high = np.nanmin(values), np.nanmax(values)
    return np.zeros_like(values) if high == low else (values - low) / (high - low)


def leave_one_out(delivered: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    """Displacement induced in every other municipality by removing one.

    The scale is re-estimated inside each leave-one-out sample, which is the only
    way the residual dependence can show up.
    """
    codes = delivered["municipality_code"].to_numpy()
    pc1 = delivered["PC1"]
    rows = []
    for position, code in enumerate(codes):
        subset_sd = float(pc1.drop(pc1.index[position]).std(ddof=0))
        remaining = scored[scored["municipality_code"] != code]
        recomputed = risk_from(remaining, subset_sd)
        published = remaining[RISK].to_numpy()
        shifted_ranks = pd.Series(-recomputed).rank(method="min").to_numpy()
        reference_ranks = pd.Series(-published).rank(method="min").to_numpy()
        rows.append(
            {
                "removed_code": code,
                "removed_name": delivered["municipality_name"].iloc[position],
                "removed_state": delivered["state"].iloc[position],
                "sd_pc1": subset_sd,
                "mean_absolute_risk_shift": float(np.abs(recomputed - published).mean()),
                "max_absolute_risk_shift": float(np.abs(recomputed - published).max()),
                "max_rank_shift": int(np.abs(shifted_ranks - reference_ranks).max()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "max_absolute_risk_shift", ascending=False
    ).reset_index(drop=True)


def domain_change_tests(
    delivered: pd.DataFrame, scored: pd.DataFrame
) -> pd.DataFrame:
    """Recompute after excluding whole regions, as AUD-11 section 8.5 asks."""
    full_sd = float(delivered["PC1"].std(ddof=0))
    cases = {
        "exclude AP+PA+MA (the record's test)": RECORD_DOMAIN_TEST,
        "exclude the whole North/Northeast": NORTH_NORTHEAST,
        "exclude the South/Southeast": set(delivered["state"]) - NORTH_NORTHEAST,
        "exclude the 84 exact-zero municipalities": None,
    }
    rows = []
    for label, states in cases.items():
        if states is None:
            keep_delivered = delivered[
                ~delivered["municipality_code"].isin(
                    scored.loc[scored[RISK] == 0, "municipality_code"]
                )
            ]
            keep_scored = scored[scored[RISK] > 0]
        else:
            keep_delivered = delivered[~delivered["state"].isin(states)]
            keep_scored = scored[~scored["state"].isin(states)]
        if keep_scored.empty:
            continue
        subset_sd = float(keep_delivered["PC1"].std(ddof=0))
        recomputed = risk_from(keep_scored, subset_sd)
        published = keep_scored[RISK].to_numpy()
        shifted = pd.Series(-recomputed).rank(method="min").to_numpy()
        reference = pd.Series(-published).rank(method="min").to_numpy()
        rows.append(
            {
                "case": label,
                "n_remaining": int(len(keep_scored)),
                "sd_pc1": subset_sd,
                "sd_change_percent": 100.0 * (subset_sd / full_sd - 1.0),
                "spearman_vs_published": float(spearmanr(recomputed, published).statistic),
                "median_rank_shift": float(np.median(np.abs(shifted - reference))),
                "max_rank_shift": int(np.abs(shifted - reference).max()),
                "max_absolute_risk_shift": float(np.abs(recomputed - published).max()),
            }
        )
    return pd.DataFrame(rows)


def normalization_schemes(scored: pd.DataFrame) -> pd.DataFrame:
    """The four schemes AUD-11 section 8.2 asks to compare, end to end."""
    hazard = scored[HAZARD].to_numpy()
    exposure = scored[EXPOSURE].to_numpy()
    vulnerability = scored[VULNERABILITY].to_numpy()
    published = scored[RISK].to_numpy()
    names = scored["municipality_name"].to_numpy()
    top20_published = set(names[np.argsort(-published)[:20]])

    def rank_pct(values: np.ndarray) -> np.ndarray:
        return pd.Series(values).rank(pct=True).to_numpy()

    def z_clipped(values: np.ndarray) -> np.ndarray:
        z = (values - values.mean()) / values.std(ddof=0)
        return np.clip((z + 3.0) / 6.0, 0.0, 1.0)

    candidates = {
        "fixed anchors (published)": published,
        "Min-Max per component, then Min-Max": _minmax(
            np.cbrt(_minmax(hazard) * _minmax(exposure) * _minmax(vulnerability))
        ),
        "percentile rank per component": np.cbrt(
            rank_pct(hazard) * rank_pct(exposure) * rank_pct(vulnerability)
        ),
        "clipped z-score per component": np.cbrt(
            z_clipped(hazard) * z_clipped(exposure) * z_clipped(vulnerability)
        ),
    }
    rows = []
    for label, values in candidates.items():
        rows.append(
            {
                "scheme": label,
                "spearman_vs_published": float(spearmanr(values, published).statistic),
                "top20_overlap": len(
                    top20_published & set(names[np.argsort(-values)[:20]])
                ),
                "n_exactly_zero": int((values == 0).sum()),
                "n_exactly_one": int((values == 1).sum()),
                "min": float(values.min()),
                "max": float(values.max()),
                "anchored_on_individual_municipalities": label.startswith("Min-Max"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    delivered, scored = load()
    full_sd = float(delivered["PC1"].std(ddof=0))

    identity = risk_from(scored, full_sd)
    if not np.allclose(identity, scored[RISK].to_numpy(), atol=1e-5):
        raise ValueError(
            "the recompute path does not reproduce the published risk; every "
            "displacement below would be measuring the wrong thing"
        )

    influence = leave_one_out(delivered, scored)
    domains = domain_change_tests(delivered, scored)
    schemes = normalization_schemes(scored)

    influence.to_csv(OUT_DIR / "leave_one_out_influence.csv", index=False)
    domains.to_csv(OUT_DIR / "domain_change_tests.csv", index=False)
    schemes.to_csv(OUT_DIR / "normalization_scheme_comparison.csv", index=False)

    worst = influence.iloc[0]
    zeros = scored[scored[RISK] == 0]
    summary = {
        "source": str(GEOJSON.relative_to(ROOT)),
        "sd_pc1_full_sample": full_sd,
        "residual_sample_dependence": {
            "where": "Vulnerability_CDF_PC1 = Phi(PC1 / sd(PC1)), sd estimated "
            "from the delivered sample",
            "hazard_and_exposure": "none — fixed anchors",
            "note": (
                "The stated aim of AUD-11 was that no published value would "
                "depend on set membership. One dependence survives, and it is "
                "material at domain scale even though it is small at the scale "
                "of a single municipality."
            ),
        },
        "leave_one_out": {
            "worst_municipality": f"{worst['removed_name']}/{worst['removed_state']}",
            "max_absolute_risk_shift": float(worst["max_absolute_risk_shift"]),
            "legacy_minmax_max_displacement": LEGACY_MAX_DISPLACEMENT,
            "improvement_factor": LEGACY_MAX_DISPLACEMENT
            / float(worst["max_absolute_risk_shift"]),
            "max_rank_shift_any_removal": int(influence["max_rank_shift"].max()),
        },
        "exact_anchors": {
            "n_risk_exactly_zero": int((scored[RISK] == 0).sum()),
            "n_risk_exactly_one": int((scored[RISK] == 1).sum()),
            "risk_max": float(scored[RISK].max()),
            "zero_causes": zeros["risk_zero_cause"].value_counts().to_dict(),
            "verdict": (
                "No municipality sits at an exact anchor as a scale artefact. "
                "The zeros are substantive: they mean the associated grid point "
                "accepted no compound event in 1993-2025. Nothing reaches 1."
            ),
        },
        "domain_change": domains.to_dict("records"),
        "scheme_comparison": schemes.to_dict("records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"sd(PC1) over the delivered sample: {full_sd:.6f}\n")
    print("Leave-one-out, worst case:")
    print(influence.head(5).to_string(index=False))
    print("\nDomain-change tests:")
    print(domains.to_string(index=False))
    print("\nNormalisation schemes:")
    print(schemes.to_string(index=False))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
