"""AUD-09 diagnostic: directionality and validity of ``SVI_Coast_2022``.

The index is PC1 of ten z-scored IBGE/SIDRA 2022 indicators, with the sign of
the component flipped globally when its mean correlation with the inputs is
negative, then Min--Max rescaled to 0--100. Two indicators correlate negatively
with the published index, which the baseline review flagged as possible
inverted directionality.

This separates four things that the single word "inverted" conflates:

1. an indicator **encoded** in the wrong direction, i.e. the column measures
   the opposite of what its name says. That would be an implementation error
   and would require recomputing the index;
2. a **legitimate negative PC1 loading**: the indicator is encoded correctly
   and the dominant axis of the data simply places it on the low pole;
3. an arbitrary flip of the **global** sign of the component;
4. the difference between an index of material deprivation and an index of
   coastal susceptibility -- a naming and interpretation question, not an
   arithmetic one.

Nothing is corrected here. The script reproduces the published index from the
delivered indicators, publishes the loadings, and measures what would change
under each alternative, so that the decision rests on numbers.

Usage:
    python -m src.exploratory.audit_AUD_09_svi_directionality

Output:
    outputs/audit/AUD-09_svi_directionality/indicator_directionality.csv
    outputs/audit/AUD-09_svi_directionality/pc_loadings.csv
    outputs/audit/AUD-09_svi_directionality/alternative_indices.csv
    outputs/audit/AUD-09_svi_directionality/largest_rank_changes.csv
    outputs/audit/AUD-09_svi_directionality/diagnosis_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-09_svi_directionality"

#: The ten indicators, in the order used by the external build script
#: ``src/04_risk_integration/external_svi/build_svi_coast_2022.py``.
INDICATORS = (
    "pop_house",
    "pop_rent",
    "pop_poverty",
    "pop_agevul",
    "pop_nonwhite",
    "pop_illiterate",
    "pop_nowater",
    "pop_nosewage",
    "pop_nogarbage",
    "pop_nopaving",
)

#: What each column actually contains, read off the SIDRA queries in the build
#: script, and the direction the conceptual framework assigns to it. ``+1``
#: means "higher value = more vulnerable".
INDICATOR_SPEC: dict[str, dict[str, object]] = {
    "pop_house": {
        "meaning": "mean residents per occupied household (crowding)",
        "sidra": "t/9605 v/93 (population) / t/9930 v/381 c63/95826 (households)",
        "encoding": "pop_total / dom_total, then Min-Max rescaled to 0-1 over the 282",
        "expected_sign": +1,
        "expected_rationale": "crowding raises exposure per dwelling and lowers coping capacity",
    },
    "pop_rent": {
        "meaning": "proportion of households NOT owned by a resident",
        "sidra": "t/9930 v/381 c63/all",
        "encoding": "1 - (owned by a resident / total)",
        "expected_sign": +1,
        "expected_rationale": "tenure insecurity impedes recovery and rebuilding",
    },
    "pop_poverty": {
        "meaning": "proportion of households up to 1/2 minimum wage per capita",
        "sidra": "t/10296 v/13604 c386/all",
        "encoding": "(up to 1/4 + 1/4 to 1/2 MW) / total",
        "expected_sign": +1,
        "expected_rationale": "material deprivation is the canonical vulnerability axis",
    },
    "pop_agevul": {
        "meaning": "proportion in vulnerable age groups (0-9 and 60+)",
        "sidra": "t/9514 v/93 c287 age-class list",
        "encoding": "sum(vulnerable classes) / total",
        "expected_sign": +1,
        "expected_rationale": "children and the elderly evacuate less easily",
    },
    "pop_nonwhite": {
        "meaning": "proportion not self-declared white",
        "sidra": "t/9605 v/93 c86/2776,95251",
        "encoding": "1 - (white / total)",
        "expected_sign": +1,
        "expected_rationale": "racial inequality proxies historical disadvantage in Brazil",
    },
    "pop_illiterate": {
        "meaning": "illiteracy rate (15+)",
        "sidra": "t/9543 v/2513 (literacy rate, %)",
        "encoding": "1 - literacy_rate/100",
        "expected_sign": +1,
        "expected_rationale": "literacy conditions access to warnings and to aid",
    },
    "pop_nowater": {
        "meaning": "proportion of households without a general water network",
        "sidra": "t/6909 v/382 c301/all",
        "encoding": "1 - (general network / total)",
        "expected_sign": +1,
        "expected_rationale": "sanitation deficit compounds flood impact",
    },
    "pop_nosewage": {
        "meaning": "proportion of households without adequate sewage",
        "sidra": "t/9397 v/382 c11558 sewage-type list",
        "encoding": "1 - (general network or septic-to-network / total)",
        "expected_sign": +1,
        "expected_rationale": "sanitation deficit compounds flood impact",
    },
    "pop_nogarbage": {
        "meaning": "proportion of households without waste collection",
        "sidra": "t/9541 v/382 c67/all",
        "encoding": "1 - (collected / total)",
        "expected_sign": +1,
        "expected_rationale": "uncollected waste blocks drainage and worsens flooding",
    },
    "pop_nopaving": {
        "meaning": "proportion of households on unpaved streets",
        "sidra": "t/6591 v/allxp c14/200,72246,72247",
        "encoding": "(no paved street) / total",
        "expected_sign": +1,
        "expected_rationale": "unpaved streets mark infrastructure deficit",
    },
}

#: Anchor test for a reversed column. Every indicator except ``pop_house`` is a
#: proportion, so the failure mode to exclude is that ``x`` was published where
#: ``1 - x`` was intended. That cannot be detected from a correlation, because a
#: reversal flips the sign of exactly the quantity under suspicion. It is
#: detected by reading the value at two municipalities whose real-world standing
#: is not in dispute, and asking whether the published number is the one the
#: definition predicts.
#:
#: ``Balneário Camboriú`` is the least deprived municipality of the set and
#: ``Chaves/PA`` the most. ``expected_high_at`` names the anchor at which the
#: correctly encoded indicator must take the larger value.
ANCHOR_LOW_DEPRIVATION = "Balneário Camboriú"
ANCHOR_HIGH_DEPRIVATION = "Chaves"

ANCHOR_EXPECTATION: dict[str, dict[str, str]] = {
    "pop_house": {
        "expected_high_at": "high",
        "why": "crowding rises with deprivation and falls with income",
    },
    "pop_rent": {
        "expected_high_at": "low",
        "why": (
            "non-ownership is an urban-affluence trait in Brazil: rental and "
            "second-home stock concentrate in the wealthy resort towns, while "
            "self-built owner occupancy dominates the poor rural coast. A value "
            "near 0.9 at Chaves would instead mean 90 % of Amazon-estuary "
            "households do not own their home, which is not the case, and would "
            "be the signature of a reversed column"
        ),
    },
    "pop_poverty": {
        "expected_high_at": "high",
        "why": "definitional",
    },
    "pop_agevul": {
        "expected_high_at": "neither",
        "why": (
            "the indicator sums two age tails that move in opposite directions "
            "with income: the 0-9 share falls with development while the 60+ "
            "share rises. Their sum is therefore nearly flat across the "
            "deprivation gradient, and no anchor ordering is predicted. The "
            "reversal test is the level instead: 0-9 plus 60+ is about 0.25-0.40 "
            "in Brazil, so a reversed column would sit near 0.60-0.75"
        ),
    },
    "pop_nonwhite": {"expected_high_at": "high", "why": "racial inequality gradient"},
    "pop_illiterate": {"expected_high_at": "high", "why": "definitional"},
    "pop_nowater": {"expected_high_at": "high", "why": "service-coverage gradient"},
    "pop_nosewage": {"expected_high_at": "high", "why": "service-coverage gradient"},
    "pop_nogarbage": {"expected_high_at": "high", "why": "service-coverage gradient"},
    "pop_nopaving": {"expected_high_at": "high", "why": "service-coverage gradient"},
}

#: Level envelope, used only for ``pop_agevul``, where no anchor ordering is
#: predicted and the reversal signature is the level of the series itself.
AGEVUL_LEVEL_ENVELOPE = (0.15, 0.55)


def _load() -> pd.DataFrame:
    payload = json.loads(GEOJSON.read_text())
    rows = [feature["properties"] for feature in payload["features"]]
    return pd.DataFrame(rows)


def _pca_index(frame: pd.DataFrame, columns: list[str]) -> dict[str, object]:
    """Reproduce the external pipeline: z-score, PC1, global sign, Min-Max."""
    matrix = frame[columns].to_numpy(dtype=float)
    scaled = StandardScaler().fit_transform(matrix)
    pca = PCA()
    scores = pca.fit_transform(scaled)
    pc1 = scores[:, 0]
    loadings = pca.components_[0]
    mean_corr = float(
        np.mean([np.corrcoef(pc1, matrix[:, j])[0, 1] for j in range(len(columns))])
    )
    flipped = mean_corr < 0
    if flipped:
        pc1 = -pc1
        loadings = -loadings
    lo, hi = float(pc1.min()), float(pc1.max())
    index = 100.0 * (pc1 - lo) / (hi - lo)
    return {
        "pc1": pc1,
        "index": index,
        "loadings": loadings,
        "loadings_pc2": pca.components_[1] * (-1.0 if flipped else 1.0),
        "explained": pca.explained_variance_ratio_,
        "mean_corr_before_flip": mean_corr,
        "sign_flipped": bool(flipped),
    }


def _rank(values: np.ndarray) -> np.ndarray:
    return pd.Series(values).rank(ascending=False, method="min").to_numpy()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _load()
    columns = list(INDICATORS)
    published = frame["SVI_Coast_2022"].to_numpy(dtype=float)

    # ── 1. Reproduce the published index ─────────────────────────────────────
    current = _pca_index(frame, columns)
    reproduction = {
        "pearson_r": float(pearsonr(current["index"], published)[0]),
        "max_abs_difference": float(np.max(np.abs(current["index"] - published))),
        "spearman_rho": float(spearmanr(current["index"], published)[0]),
        "explained_variance_pc1": float(current["explained"][0]),
        "explained_variance_pc2": float(current["explained"][1]),
        "mean_correlation_before_global_flip": current["mean_corr_before_flip"],
        "global_sign_was_flipped": current["sign_flipped"],
    }

    # ── 2. Directionality table, with the reversal test at named anchors ─────
    by_name = frame.set_index("municipality_name")
    rows = []
    for j, name in enumerate(columns):
        values = frame[name].to_numpy(dtype=float)
        spec = INDICATOR_SPEC[name]
        expectation = ANCHOR_EXPECTATION[name]
        r_index = float(pearsonr(values, published)[0])
        rho_index = float(spearmanr(values, published)[0])
        r_poverty = float(pearsonr(values, frame["pop_poverty"].to_numpy(float))[0])
        loading = float(current["loadings"][j])
        low_anchor = float(by_name.loc[ANCHOR_LOW_DEPRIVATION, name])
        high_anchor = float(by_name.loc[ANCHOR_HIGH_DEPRIVATION, name])

        expected_high_at = expectation["expected_high_at"]
        if expected_high_at == "high":
            reversal_passes = high_anchor > low_anchor
        elif expected_high_at == "low":
            reversal_passes = low_anchor > high_anchor
        else:  # neither: judge the level of the series instead
            lo, hi = AGEVUL_LEVEL_ENVELOPE
            reversal_passes = bool(values.min() >= lo and values.max() <= hi)

        if not reversal_passes:
            verdict = "REVERSAL TEST FAILS - column may be encoded backwards"
        elif loading >= 0:
            verdict = "encoding confirmed; positive PC1 loading"
        else:
            verdict = (
                "encoding confirmed; negative PC1 loading is empirical, "
                "not an encoding error"
            )
        rows.append(
            {
                "indicator": name,
                "meaning": spec["meaning"],
                "sidra_source": spec["sidra"],
                "encoding": spec["encoding"],
                "expected_sign": spec["expected_sign"],
                "expected_rationale": spec["expected_rationale"],
                "observed_min": float(values.min()),
                "observed_median": float(np.median(values)),
                "observed_max": float(values.max()),
                "argmin_municipality": str(
                    frame["municipality_name"].iloc[int(np.argmin(values))]
                ),
                "argmax_municipality": str(
                    frame["municipality_name"].iloc[int(np.argmax(values))]
                ),
                f"value_at_{ANCHOR_LOW_DEPRIVATION}": low_anchor,
                f"value_at_{ANCHOR_HIGH_DEPRIVATION}": high_anchor,
                "expected_high_at": expected_high_at,
                "reversal_test_rationale": expectation["why"],
                "reversal_test_passes": bool(reversal_passes),
                "pc1_loading": loading,
                "implemented_sign": int(np.sign(loading)),
                "r_with_svi": r_index,
                "rho_with_svi": rho_index,
                "r_with_poverty": r_poverty,
                "verdict": verdict,
            }
        )
    directionality = pd.DataFrame(rows)
    directionality.to_csv(OUT_DIR / "indicator_directionality.csv", index=False)

    loadings_frame = pd.DataFrame(
        {
            "indicator": columns,
            "pc1_loading": current["loadings"],
            "pc2_loading": current["loadings_pc2"],
        }
    )
    loadings_frame.to_csv(OUT_DIR / "pc_loadings.csv", index=False)

    # ── 3. Alternatives ──────────────────────────────────────────────────────
    matrix = frame[columns].to_numpy(dtype=float)
    z = StandardScaler().fit_transform(matrix)

    # (a) additive index with conceptual directionality imposed on every input
    additive_raw = z.mean(axis=1)
    additive = 100.0 * (additive_raw - additive_raw.min()) / (
        additive_raw.max() - additive_raw.min()
    )

    # (b) PCA restricted to the eight indicators with positive loadings
    eight = [c for c in columns if c not in ("pop_rent", "pop_agevul")]
    eight_result = _pca_index(frame, eight)

    # (c) PCA with the two negative-loading indicators sign-forced before PCA
    forced = frame[columns].copy()
    for name in ("pop_rent", "pop_agevul"):
        forced[name] = -forced[name]
    forced_result = _pca_index(forced, columns)

    # (d) percentile-rank rescaling of the published PC1, which removes the
    #     exact 0 / exact 100 Min-Max anchors
    ranks = pd.Series(current["pc1"]).rank(pct=True).to_numpy()
    percentile_index = 100.0 * ranks

    alternatives = pd.DataFrame(
        {
            "municipality_code": frame["municipality_code"],
            "municipality_name": frame["municipality_name"],
            "state": frame["state"],
            "svi_published": published,
            "svi_reproduced": current["index"],
            "svi_additive_imposed": additive,
            "svi_pca_eight": eight_result["index"],
            "svi_pca_sign_forced": forced_result["index"],
            "svi_percentile_rank": percentile_index,
        }
    )
    alternatives.to_csv(OUT_DIR / "alternative_indices.csv", index=False)

    def _compare(name: str, values: np.ndarray) -> dict[str, float]:
        rank_published = _rank(published)
        rank_alt = _rank(values)
        shift = np.abs(rank_published - rank_alt)
        top10_published = set(alternatives["municipality_code"][np.argsort(-published)[:10]])
        top10_alt = set(alternatives["municipality_code"][np.argsort(-values)[:10]])
        return {
            "variant": name,
            "pearson_r_with_published": float(pearsonr(values, published)[0]),
            "spearman_rho_with_published": float(spearmanr(values, published)[0]),
            "median_absolute_rank_shift": float(np.median(shift)),
            "max_absolute_rank_shift": float(shift.max()),
            "top10_overlap_with_published": int(len(top10_published & top10_alt)),
        }

    comparisons = [
        _compare("additive_imposed_direction", additive),
        _compare("pca_eight_indicators", eight_result["index"]),
        _compare("pca_sign_forced_inputs", forced_result["index"]),
        _compare("percentile_rank_rescale", percentile_index),
    ]

    # ── 4. Effect of each alternative on the published risk ──────────────────
    hazard = frame["Hazard_Index_mun"].to_numpy(dtype=float)
    exposure = frame["Exposure_Index"].to_numpy(dtype=float)
    risk_published = frame["Risk_Hazard"].to_numpy(dtype=float)
    valid = np.isfinite(hazard) & np.isfinite(exposure) & np.isfinite(risk_published)

    def _risk_from(svi: np.ndarray) -> np.ndarray:
        floor = 0.01
        h = np.clip(hazard, floor, None)
        e = np.clip(exposure, floor, None)
        v = np.clip(svi / 100.0, floor, None)
        raw = np.cbrt(h * e * v)
        lo = np.nanmin(raw[valid])
        hi = np.nanmax(raw[valid])
        return (raw - lo) / (hi - lo)

    risk_rows = []
    for name, svi in (
        ("published", published),
        ("additive_imposed_direction", additive),
        ("pca_eight_indicators", eight_result["index"]),
        ("pca_sign_forced_inputs", forced_result["index"]),
        ("percentile_rank_rescale", percentile_index),
    ):
        risk = _risk_from(svi)
        rho = float(spearmanr(risk[valid], risk_published[valid])[0])
        rank_pub = _rank(np.where(valid, risk_published, np.nan))
        rank_alt = _rank(np.where(valid, risk, np.nan))
        shift = np.abs(rank_pub - rank_alt)[valid]
        order_pub = np.argsort(-np.where(valid, risk_published, -np.inf))[:10]
        order_alt = np.argsort(-np.where(valid, risk, -np.inf))[:10]
        risk_rows.append(
            {
                "svi_variant": name,
                "spearman_rho_risk_vs_published": rho,
                "median_absolute_rank_shift": float(np.median(shift)),
                "max_absolute_rank_shift": float(shift.max()),
                "risk_top10_overlap": int(
                    len(
                        set(frame["municipality_code"].iloc[order_pub])
                        & set(frame["municipality_code"].iloc[order_alt])
                    )
                ),
            }
        )

    # ── 5. Municipalities whose SVI rank moves most under imposed direction ──
    rank_pub = _rank(published)
    rank_add = _rank(additive)
    movers = pd.DataFrame(
        {
            "municipality_name": frame["municipality_name"],
            "state": frame["state"],
            "svi_published": published,
            "svi_additive_imposed": additive,
            "rank_published": rank_pub,
            "rank_additive": rank_add,
            "rank_shift": rank_add - rank_pub,
            "pop_rent": frame["pop_rent"],
            "pop_agevul": frame["pop_agevul"],
            "pop_poverty": frame["pop_poverty"],
        }
    )
    movers = movers.reindex(
        movers["rank_shift"].abs().sort_values(ascending=False).index
    ).head(25)
    movers.to_csv(OUT_DIR / "largest_rank_changes.csv", index=False)

    # ── 6. Redundancy and scale artefacts ────────────────────────────────────
    corr = frame[columns].corr()
    off_diagonal = corr.to_numpy()[~np.eye(len(columns), dtype=bool)]
    sanitation = ["pop_nowater", "pop_nosewage", "pop_nogarbage", "pop_nopaving"]
    sanitation_corr = frame[sanitation].corr().to_numpy()
    sanitation_off = sanitation_corr[~np.eye(len(sanitation), dtype=bool)]

    exact_anchors = {
        "n_exactly_zero": int(np.sum(np.isclose(published, 0.0))),
        "n_exactly_hundred": int(np.sum(np.isclose(published, 100.0))),
        "zero_municipality": frame["municipality_name"][
            np.isclose(published, 0.0)
        ].tolist(),
        "hundred_municipality": frame["municipality_name"][
            np.isclose(published, 100.0)
        ].tolist(),
    }

    summary = {
        "generated_by": "src.exploratory.audit_AUD_09_svi_directionality",
        "source": str(GEOJSON.relative_to(ROOT)),
        "municipality_count": int(len(frame)),
        "reproduction_of_published_index": reproduction,
        "indicator_verdicts": {
            row["indicator"]: row["verdict"] for row in rows
        },
        "n_indicators_failing_reversal_test": int(
            (~directionality["reversal_test_passes"]).sum()
        ),
        "indicators_failing_reversal_test": directionality.loc[
            ~directionality["reversal_test_passes"], "indicator"
        ].tolist(),
        "n_indicators_with_negative_pc1_loading": int(
            (directionality["pc1_loading"] < 0).sum()
        ),
        "negative_loading_indicators": directionality.loc[
            directionality["pc1_loading"] < 0, "indicator"
        ].tolist(),
        "alternative_index_comparisons": comparisons,
        "risk_effect_of_alternatives": risk_rows,
        "redundancy": {
            "mean_abs_offdiagonal_correlation_all_ten": float(
                np.mean(np.abs(off_diagonal))
            ),
            "mean_abs_offdiagonal_correlation_sanitation_block": float(
                np.mean(np.abs(sanitation_off))
            ),
        },
        "scale_artefacts": exact_anchors,
        "correlation_svi_with_poverty": float(
            pearsonr(published, frame["pop_poverty"].to_numpy(float))[0]
        ),
        "correlation_svi_with_log_population": float(
            spearmanr(
                published, np.log10(frame["pop_municipality"].to_numpy(float))
            )[0]
        ),
    }
    (OUT_DIR / "diagnosis_summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
