"""AUD-08 diagnostic: what the effective-population decision fixed, and what it
did not.

AUD-08 recorded two defects in the exposure term. The first was **saturation**:
under a single 10 km band, 92 of 282 municipalities had a coastal-to-municipal
population ratio above 0.99 and 59 sat exactly at the ceiling, so the relative
half barely discriminated. The second was **MAUP**: dividing the coastal
population by the whole municipal population measures how coastal a municipality
is, which is a property of the administrative outline rather than of risk, and it
penalises large municipalities with a small coastal sector -- Campos dos
Goytacazes/RJ and Linhares/ES being the named cases.

The effective-population decision of 2026-07-31 replaced the single band with a
distance-weighted mean of the cumulative 1, 2, 5 and 10 km bands. The record was
never re-measured against it, and the two defects fared very differently.

A note on the MAUP criterion. The record asks for a comparison against a finer
spatial support, naming the census sector. That misplaces the problem: the
population is already counted on the IBGE statistical grid at 200 m in urban and
1 km in rural areas, which is **finer** than a census sector. The support of the
population count is not the issue. The issue is the **reporting unit and the
denominator**: the index is published per municipality and the relative term
divides by the entire municipal population. That is what is measured here.

Usage:
    python -m src.exploratory.audit_AUD_08_exposure_support

Output:
    outputs/audit/AUD-08_exposure_support/saturation_by_band.csv
    outputs/audit/AUD-08_exposure_support/band_ladder.csv
    outputs/audit/AUD-08_exposure_support/denominator_penalty.csv
    outputs/audit/AUD-08_exposure_support/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-08_exposure_support"

HAZARD = "Hazard_Index_mun"
VULNERABILITY = "Vulnerability_CDF_PC1"
RISK = "Risk_Hazard"

BANDS = ["pop_1km", "pop_2km", "pop_5km", "pop_10km", "pop_eff"]
#: Fixed absolute goalposts, 10^2 to 10^6 inhabitants.
GOALPOST_LOG_MIN, GOALPOST_LOG_MAX = 2.0, 6.0
#: The two municipalities the record names as the MAUP case study.
NAMED_CASES = ["Campos dos Goytacazes", "Linhares"]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    delivered = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    scored = delivered.dropna(subset=[RISK]).sort_values(
        RISK, ascending=False
    ).reset_index(drop=True)
    scored["rank_published"] = scored.index + 1
    return delivered, scored


def exposure_from(population: pd.Series, municipal: pd.Series) -> pd.DataFrame:
    """The published exposure recipe, applied to an arbitrary population count."""
    with np.errstate(divide="ignore"):
        absolute = np.clip(
            (np.log10(population.where(population > 0)) - GOALPOST_LOG_MIN)
            / (GOALPOST_LOG_MAX - GOALPOST_LOG_MIN),
            0.0,
            1.0,
        ).fillna(0.0)
    relative = (population / municipal).clip(0.0, 1.0)
    return pd.DataFrame(
        {"absolute": absolute, "relative": relative, "index": np.sqrt(absolute * relative)}
    )


def saturation_by_band(delivered: pd.DataFrame) -> pd.DataFrame:
    """How often the relative term reaches its ceiling, band by band."""
    rows = []
    for band in BANDS:
        ratio = (delivered[band] / delivered["pop_municipality"]).clip(0, 1)
        rows.append(
            {
                "band": band,
                "median_ratio": float(ratio.median()),
                "n_above_0.99": int((ratio > 0.99).sum()),
                "n_at_ceiling": int((ratio >= 1.0).sum()),
                "n_zero_population": int((delivered[band] == 0).sum()),
                "share_at_ceiling": float((ratio >= 1.0).mean()),
            }
        )
    return pd.DataFrame(rows)


def residual_discrimination(delivered: pd.DataFrame) -> dict[str, float]:
    """Do the municipalities that used to saturate now separate?

    Diagnostic 4 of the record asked whether the absolute half rescued the
    saturated group. Under the effective population the question changes: the
    group no longer saturates at all, so what matters is whether it spreads.
    """
    ratio_10km = (delivered["pop_10km"] / delivered["pop_municipality"]).clip(0, 1)
    formerly_saturated = ratio_10km >= 1.0
    ratio_eff = (delivered["pop_eff"] / delivered["pop_municipality"]).clip(0, 1)
    group = ratio_eff[formerly_saturated]
    return {
        "n_formerly_at_ceiling_under_pop_10km": int(formerly_saturated.sum()),
        "their_ratio_under_pop_eff_min": float(group.min()),
        "their_ratio_under_pop_eff_median": float(group.median()),
        "their_ratio_under_pop_eff_max": float(group.max()),
        "their_ratio_under_pop_eff_iqr": float(
            group.quantile(0.75) - group.quantile(0.25)
        ),
        "n_of_them_still_at_ceiling": int((group >= 1.0).sum()),
    }


def band_ladder(scored: pd.DataFrame) -> pd.DataFrame:
    """Effect of each band choice on the published municipal ranking."""
    published = scored[RISK].to_numpy()
    names = scored["municipality_name"].to_numpy()
    top20 = set(names[np.argsort(-published)[:20]])
    rows = []
    for band in BANDS:
        exposure = exposure_from(scored[band], scored["pop_municipality"])
        risk = np.cbrt(
            scored[HAZARD].to_numpy()
            * exposure["index"].to_numpy()
            * scored[VULNERABILITY].to_numpy()
        )
        shifted = pd.Series(-risk).rank(method="min").to_numpy()
        rows.append(
            {
                "band": band,
                "n_exposure_zero": int((exposure["index"] == 0).sum()),
                "spearman_vs_published": float(spearmanr(risk, published).statistic),
                "median_rank_shift": float(
                    np.median(np.abs(shifted - scored["rank_published"].to_numpy()))
                ),
                "top20_overlap": len(top20 & set(names[np.argsort(-risk)[:20]])),
            }
        )
    return pd.DataFrame(rows)


def denominator_penalty(scored: pd.DataFrame) -> pd.DataFrame:
    """Which municipalities the municipal denominator penalises most.

    The counterfactual drops the relative half entirely, keeping the absolute
    half, and reports the rank each municipality would gain.

    Municipalities whose hazard is zero are excluded. Their risk is zero under
    both variants, so they tie in a single block and any rank movement they show
    is an artefact of where that tied block starts, not a penalty being lifted.
    """
    without_relative = np.cbrt(
        scored[HAZARD].to_numpy()
        * scored["Exposure_absolute"].to_numpy()
        * scored[VULNERABILITY].to_numpy()
    )
    alternative_rank = pd.Series(-without_relative).rank(method="min").astype(int)
    frame = pd.DataFrame(
        {
            "rank_published": scored["rank_published"],
            "rank_without_relative_term": alternative_rank,
            "municipality_name": scored["municipality_name"],
            "state": scored["state"],
            "pop_municipality": scored["pop_municipality"],
            "pop_eff": scored["pop_eff"],
            "Exposure_absolute": scored["Exposure_absolute"],
            "Exposure_relative": scored["Exposure_relative"],
            "Exposure_Index": scored["Exposure_Index"],
            "Risk_Hazard": scored[RISK],
        }
    )
    frame["positions_gained"] = (
        frame["rank_published"] - frame["rank_without_relative_term"]
    )
    frame = frame[scored[RISK].to_numpy() > 0]
    return frame.sort_values("positions_gained", ascending=False).reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    delivered, scored = load()

    saturation = saturation_by_band(delivered)
    ladder = band_ladder(scored)
    penalty = denominator_penalty(scored)

    saturation.to_csv(OUT_DIR / "saturation_by_band.csv", index=False)
    ladder.to_csv(OUT_DIR / "band_ladder.csv", index=False)
    penalty.to_csv(OUT_DIR / "denominator_penalty.csv", index=False)

    without_relative = np.cbrt(
        scored[HAZARD] * scored["Exposure_absolute"] * scored[VULNERABILITY]
    )
    names = scored["municipality_name"].to_numpy()
    top20 = set(names[np.argsort(-scored[RISK].to_numpy())[:20]])

    summary = {
        "source": str(GEOJSON.relative_to(ROOT)),
        "saturation": {
            "verdict": (
                "Dissolved by the effective-population decision. Under pop_10km "
                "the relative term hit its ceiling in 59 of 282 municipalities "
                "and exceeded 0.99 in 92; under pop_eff neither happens once."
            ),
            "by_band": saturation.to_dict("records"),
            "residual_discrimination": residual_discrimination(delivered),
        },
        "maup": {
            "note": (
                "The record asks to compare against a census-sector support. The "
                "population is already counted on the IBGE statistical grid at "
                "200 m urban / 1 km rural, which is finer than a census sector, "
                "so the support of the count is not where the MAUP lives. It "
                "lives in the reporting unit and in the municipal denominator."
            ),
            "median_share_of_municipal_population_in_pop_eff": float(
                (delivered["pop_eff"] / delivered["pop_municipality"]).median()
            ),
            "counterfactual_without_relative_term": {
                "spearman_vs_published": float(
                    spearmanr(without_relative, scored[RISK]).statistic
                ),
                "top20_overlap": len(
                    top20 & set(names[np.argsort(-without_relative.to_numpy())[:20]])
                ),
            },
            "named_cases": penalty[
                penalty["municipality_name"].isin(NAMED_CASES)
            ].to_dict("records"),
            "ten_most_penalised": penalty.head(10)[
                ["municipality_name", "state", "rank_published",
                 "rank_without_relative_term", "positions_gained",
                 "Exposure_relative"]
            ].to_dict("records"),
        },
        "band_ladder": ladder.to_dict("records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print("Saturation of the relative term, by band:")
    print(saturation.to_string(index=False))
    print("\nBand ladder against the published ranking:")
    print(ladder.to_string(index=False))
    print("\nMost penalised by the municipal denominator:")
    print(
        penalty.head(10)[
            ["rank_published", "rank_without_relative_term", "positions_gained",
             "municipality_name", "state", "Exposure_relative"]
        ].to_string(index=False)
    )
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
