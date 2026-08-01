"""AUD-09 diagnostic: where the exact Min-Max anchors survive, and what the
vulnerability-scale alternatives cost under the current pipeline.

Two criteria of AUD-09 stood unverified. One was explicitly deferred to AUD-11:
whether any municipality still receives an exact scale anchor. The other asked
for a comparison against alternative vulnerability scales, and it was answered --
but under the pipeline that existed on 2026-07-31 before the fixed-anchor
rescale, with a 0.01 floor and a final Min-Max that no longer exist. The numbers
the record carries (percentile rank at rho = 0.958 on the final risk, maximum
displacement 108 positions) therefore describe a product that is gone.

This re-measures the alternatives against the published product and separates two
things the record conflates: the scale that **enters the risk**, which is
`Phi(PC1/sd(PC1))` and has no exact anchors, and the scale that is **published as
a layer**, `SVI_Coast_2022`, which is still the original 0-100 Min-Max and still
puts one municipality at exactly 0 and another at exactly 100. Keeping it was a
deliberate traceability choice, not an oversight, but it does surface in article
products and needs declaring.

Usage:
    python -m src.exploratory.audit_AUD_09_scale_alternatives

Output:
    outputs/audit/AUD-09_scale_alternatives/vulnerability_scale_alternatives.csv
    outputs/audit/AUD-09_scale_alternatives/exact_anchor_audit.json
    outputs/audit/AUD-09_scale_alternatives/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
SVI_TABLE = (
    ROOT / "outputs" / "article_figures" / "tables" / "top10_municipalities_by_svi.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-09_scale_alternatives"

HAZARD = "Hazard_Index_mun"
EXPOSURE = "Exposure_Index"
VULNERABILITY = "Vulnerability_CDF_PC1"
RISK = "Risk_Hazard"

#: The ten SIDRA indicators, all coded so that higher means more deprived.
INDICATORS = [
    "pop_poverty", "pop_illiterate", "pop_house", "pop_nogarbage", "pop_nonwhite",
    "pop_nosewage", "pop_nowater", "pop_nopaving", "pop_agevul", "pop_rent",
]


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    delivered = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    return delivered, delivered.dropna(subset=[RISK]).reset_index(drop=True)


def _minmax(values: np.ndarray) -> np.ndarray:
    low, high = values.min(), values.max()
    return (values - low) / (high - low)


def vulnerability_alternatives(delivered: pd.DataFrame) -> dict[str, np.ndarray]:
    """Candidate scales for the vulnerability factor, over the 282 delivered."""
    pc1 = delivered["PC1"].to_numpy()
    standardized = np.column_stack(
        [
            (delivered[name].to_numpy() - delivered[name].to_numpy().mean())
            / delivered[name].to_numpy().std(ddof=0)
            for name in INDICATORS
        ]
    )
    additive = standardized.mean(axis=1)
    return {
        "Phi(PC1/sd) — published": norm.cdf(pc1 / pc1.std(ddof=0)),
        "Min-Max of PC1 (the original SVI/100)": _minmax(pc1),
        "percentile rank of PC1": pd.Series(pc1).rank(pct=True).to_numpy(),
        "additive z-score, direction imposed": norm.cdf(
            additive / additive.std(ddof=0)
        ),
    }


def compare_on_risk(
    delivered: pd.DataFrame, scored: pd.DataFrame, alternatives: dict
) -> pd.DataFrame:
    """Effect of each vulnerability scale on the published municipal ranking.

    Each candidate is computed over the 282 delivered municipalities and then
    aligned by IBGE code onto the 280 that carry a risk value.
    """
    published = scored[RISK].to_numpy()
    names = scored["municipality_name"].to_numpy()
    top20_published = set(names[np.argsort(-published)[:20]])
    codes = scored["municipality_code"]
    rows = []
    for label, values in alternatives.items():
        subset = (
            pd.Series(values, index=delivered["municipality_code"])
            .reindex(codes)
            .to_numpy()
        )
        if np.isnan(subset).any():
            raise ValueError(f"alignment by municipality_code failed for {label!r}")
        risk = np.cbrt(
            scored[HAZARD].to_numpy() * scored[EXPOSURE].to_numpy() * subset
        )
        shifted = pd.Series(-risk).rank(method="min").to_numpy()
        reference = pd.Series(-published).rank(method="min").to_numpy()
        rows.append(
            {
                "scale": label,
                "spearman_with_published_vulnerability": float(
                    spearmanr(subset, scored[VULNERABILITY]).statistic
                ),
                "spearman_on_risk": float(spearmanr(risk, published).statistic),
                "top20_overlap": len(
                    top20_published & set(names[np.argsort(-risk)[:20]])
                ),
                "max_rank_shift": int(np.abs(shifted - reference).max()),
                "n_exactly_zero": int((subset == 0).sum()),
                "n_exactly_one": int((subset == 1).sum()),
                "min": float(subset.min()),
                "max": float(subset.max()),
            }
        )
    return pd.DataFrame(rows)


def exact_anchor_audit(delivered: pd.DataFrame) -> dict:
    """Where an exact 0 or 100 still reaches a published product."""
    at_zero = delivered.loc[delivered["SVI_Coast_2022"] == 0]
    at_hundred = delivered.loc[delivered["SVI_Coast_2022"] == 100]
    table_head = pd.read_csv(SVI_TABLE).head(1).to_dict("records")
    return {
        "vulnerability_entering_the_risk": {
            "field": VULNERABILITY,
            "formula": "Phi(PC1 / sd(PC1, ddof=0))",
            "min": float(delivered[VULNERABILITY].min()),
            "max": float(delivered[VULNERABILITY].max()),
            "n_exactly_zero": int((delivered[VULNERABILITY] == 0).sum()),
            "n_exactly_one": int((delivered[VULNERABILITY] == 1).sum()),
            "verdict": "No exact anchor. The criterion is met on the risk path.",
        },
        "svi_published_as_a_layer": {
            "field": "SVI_Coast_2022",
            "formula": "Min-Max of PC1, 0-100 (original, preserved for traceability)",
            "min": float(delivered["SVI_Coast_2022"].min()),
            "max": float(delivered["SVI_Coast_2022"].max()),
            "at_exactly_zero": at_zero[["municipality_name", "state"]].to_dict("records"),
            "at_exactly_hundred": at_hundred[["municipality_name", "state"]].to_dict(
                "records"
            ),
            "surfaces_in": {
                "article_table_first_row": table_head,
                "note": (
                    "The article SVI table prints 100.000 for the top municipality "
                    "and the map layer spans 0-100, so the Min-Max artefact is "
                    "visible to a reader even though it no longer reaches the risk."
                ),
            },
            "verdict": (
                "Exact anchors persist here by deliberate choice: the delivered "
                "SVI was preserved unchanged for traceability and provenance. It "
                "must be declared, not silently carried."
            ),
        },
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    delivered, scored = load()
    alternatives = vulnerability_alternatives(delivered)
    comparison = compare_on_risk(delivered, scored, alternatives)
    anchors = exact_anchor_audit(delivered)

    comparison.to_csv(
        OUT_DIR / "vulnerability_scale_alternatives.csv", index=False
    )
    with (OUT_DIR / "exact_anchor_audit.json").open("w", encoding="utf-8") as handle:
        json.dump(anchors, handle, indent=2, ensure_ascii=False)

    summary = {
        "source": str(GEOJSON.relative_to(ROOT)),
        "note": (
            "The record's alternative-scale numbers (percentile rank at rho = "
            "0.958 on risk, maximum displacement 108) were measured under the "
            "superseded pipeline, with a 0.01 floor and a final Min-Max. They are "
            "re-measured here against the published product."
        ),
        "alternatives": comparison.to_dict("records"),
        "exact_anchors": anchors,
        "lima_et_al_2024_comparison": {
            "status": "not performed, and not planned",
            "reason": (
                "The reference SVI-Coast is built on the 2010 census and is not "
                "held in this repository; obtaining it requires the supplementary "
                "material of the published article. The researcher decided on "
                "2026-07-31 not to pursue external material."
            ),
        },
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(comparison.to_string(index=False))
    print("\nExact-anchor audit:")
    print(json.dumps(anchors, indent=2, ensure_ascii=False)[:1200])
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
