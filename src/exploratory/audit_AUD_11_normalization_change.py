"""Create the auditable before/after comparison for AUD-08/09/11/15."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[2]
BEFORE = ROOT / "outputs/audit/AUD-11_normalization_change/risk_index_before.geojson"
AFTER = ROOT / "site/public/data/risk_index_municipalities.geojson"
OUT = ROOT / "outputs/audit/AUD-11_normalization_change"


def _rank(frame: pd.DataFrame, field: str) -> pd.Series:
    return frame[field].rank(ascending=False, method="min")


def main() -> None:
    before = gpd.read_file(BEFORE).drop(columns="geometry")
    after = gpd.read_file(AFTER).drop(columns="geometry")
    keys = ["municipality_code", "municipality_name", "state"]
    merged = before.merge(after, on=keys, suffixes=("_before", "_after"))
    for suffix in ("before", "after"):
        merged[f"rank_{suffix}"] = _rank(merged, f"Risk_Hazard_{suffix}")
    merged["rank_change"] = merged["rank_after"] - merged["rank_before"]
    merged["absolute_rank_change"] = merged["rank_change"].abs()
    comparable = merged.dropna(subset=["Risk_Hazard_before", "Risk_Hazard_after"])
    old_top10 = set(comparable.nlargest(10, "Risk_Hazard_before").municipality_code)
    new_top10 = set(comparable.nlargest(10, "Risk_Hazard_after").municipality_code)

    def after_field(name: str) -> str:
        return f"{name}_after" if f"{name}_after" in merged else name

    old_eff = (
        0.5 * merged[after_field("pop_1km")]
        + 0.3 * merged[after_field("pop_5km")]
        + 0.2 * merged[after_field("pop_10km")]
    )
    new_eff = merged[after_field("pop_eff")]
    exposure_comparison = {
        "pearson": float(pearsonr(old_eff, new_eff).statistic),
        "spearman": float(spearmanr(old_eff, new_eff).statistic),
        "top10_overlap": int(len(set(old_eff.nlargest(10).index) & set(new_eff.nlargest(10).index))),
        "maximum_rank_displacement": int((old_eff.rank(ascending=False) - new_eff.rank(ascending=False)).abs().max()),
        "old_formula": "0.5*pop_1km+0.3*pop_5km+0.2*pop_10km (comparison only)",
        "new_formula": "0.4*pop_1km+0.3*pop_2km+0.2*pop_5km+0.1*pop_10km",
    }
    zero_rows = merged.loc[
        merged["Risk_Hazard_after"].eq(0),
        keys + ["Hazard_Index_mun_after", "Exposure_Index_after", after_field("risk_zero_cause")],
    ].copy()
    summary = {
        "municipalities_delivered": int(len(after)),
        "municipalities_with_risk": int(after.Risk_Hazard.notna().sum()),
        "spearman_risk_before_after": float(spearmanr(comparable.Risk_Hazard_before, comparable.Risk_Hazard_after).statistic),
        "median_absolute_rank_change": float(comparable.absolute_rank_change.median()),
        "maximum_absolute_rank_change": int(comparable.absolute_rank_change.max()),
        "top10_overlap": int(len(old_top10 & new_top10)),
        "top10_before": comparable.nlargest(10, "Risk_Hazard_before")[keys + ["Risk_Hazard_before"]].to_dict("records"),
        "top10_after": comparable.nlargest(10, "Risk_Hazard_after")[keys + ["Risk_Hazard_after"]].to_dict("records"),
        "risk_range_before": [float(comparable.Risk_Hazard_before.min()), float(comparable.Risk_Hazard_before.max())],
        "risk_range_after": [float(comparable.Risk_Hazard_after.min()), float(comparable.Risk_Hazard_after.max())],
        "exact_zero_count_after": int(len(zero_rows)),
        "zero_cause_counts": zero_rows[after_field("risk_zero_cause")].value_counts().to_dict(),
        "coverage_status_counts": after.coverage_status.value_counts().to_dict(),
        "exposure_formula_comparison": exposure_comparison,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    comparable.sort_values("absolute_rank_change", ascending=False).head(20).to_csv(
        OUT / "largest_rank_changes.csv", index=False
    )
    zero_rows.to_csv(OUT / "exact_zero_municipalities.csv", index=False)
    pd.DataFrame({
        **{key: merged[key] for key in keys},
        "pop_eff_old_comparison": old_eff,
        "pop_eff_new": new_eff,
    }).to_csv(OUT / "exposure_formula_comparison.csv", index=False)
    (OUT / "comparison_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
