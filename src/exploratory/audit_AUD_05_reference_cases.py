"""AUD-05 acceptance suite: confront the published product with a reference case
list fixed in advance.

AUD-05 is the terminal question of this audit. It has no correction of its own:
it closes when the product can explain every reference case by an identified
mechanism, or declare the divergence.

The record's section 10 warns that adjusting the method until the known cases
appear at the top is result selection, and that removing inconvenient cases after
seeing them fail is the worst possible outcome. Seven audit sessions have since
looked at where individual municipalities land, so the list in
``docs/scientific_audit/reference_cases.csv`` was built **only** from sources
that predate every method change -- the immutable baseline review of 2026-07-29
and the external literature identified while closing AUD-02 -- and was committed
before this script was run.

Two design points follow from the record itself. First, hazard and integrated
risk carry **separate expectations**: the baseline review found the hazard top-10
physically sound while the integrated index failed, so collapsing them would hide
the very distinction the suite exists to make. Second, several cases carry the
expectation ``ambiguous`` or ``low`` **by design** -- a wealthy municipality with
real erosion is expected to score low on an index whose vulnerability layer
measures material deprivation, and recording that as a pass or a failure would
both be wrong. Those cases are reported, not scored.

Usage:
    python -m src.exploratory.audit_AUD_05_reference_cases

Output:
    outputs/audit/AUD-05_reference_cases/case_report.csv
    outputs/audit/AUD-05_reference_cases/divergences.csv
    outputs/audit/AUD-05_reference_cases/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
CASES = ROOT / "docs" / "scientific_audit" / "reference_cases.csv"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-05_reference_cases"

RISK = "Risk_Hazard"
HAZARD = "Hazard_Index_mun"
METRIC_CRS = 5880

#: A "high" expectation is met at or above this percentile of the scored sample,
#: a "low" one at or below its complement. Declared here rather than chosen after
#: seeing the results.
HIGH_PERCENTILE = 0.66
LOW_PERCENTILE = 0.34


def load() -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    delivered = gpd.read_file(GEOJSON)
    delivered["municipality_code"] = delivered["municipality_code"].astype(str)
    scored = delivered[delivered[RISK].notna()].copy()
    scored["risk_rank"] = scored[RISK].rank(ascending=False, method="min").astype(int)
    scored["risk_pct"] = scored[RISK].rank(pct=True)
    scored["hazard_rank"] = scored[HAZARD].rank(ascending=False, method="min").astype(int)
    scored["hazard_pct"] = scored[HAZARD].rank(pct=True)
    cases = pd.read_csv(CASES, dtype={"ibge_code": str})
    return delivered, scored, cases


def distance_to_assigned_point(delivered: gpd.GeoDataFrame) -> pd.Series:
    """Kilometres from the municipal polygon to the ocean grid point it uses."""
    metric = delivered.to_crs(METRIC_CRS)
    points = gpd.GeoSeries(
        gpd.points_from_xy(delivered["grid_lon"], delivered["grid_lat"]),
        crs=4326,
    ).to_crs(METRIC_CRS)
    return pd.Series(metric.geometry.distance(points).to_numpy() / 1e3, index=delivered.index)


def verdict(expectation: str, percentile: float | None) -> str:
    """Confront one expectation with one observed percentile."""
    if expectation == "absent":
        return "meets" if percentile is None else "diverges"
    if percentile is None:
        return "diverges (no value, but one was expected)"
    if expectation == "high":
        return "meets" if percentile >= HIGH_PERCENTILE else "diverges"
    if expectation == "low":
        return "meets" if percentile <= LOW_PERCENTILE else "diverges"
    return "not scored (expectation is ambiguous by design)"


def build_report(
    delivered: gpd.GeoDataFrame, scored: pd.DataFrame, cases: pd.DataFrame
) -> pd.DataFrame:
    delivered = delivered.assign(distance_km=distance_to_assigned_point(delivered))
    joined = cases.merge(
        delivered[
            ["municipality_code", "distance_km", "grid_lat", "grid_lon",
             "Hazard_Frequency", "Hazard_Severity", "Exposure_absolute",
             "Exposure_relative", "Exposure_Index", "Vulnerability_CDF_PC1",
             "pop_municipality", "pop_eff", "coverage_status", "risk_zero_cause"]
        ],
        left_on="ibge_code",
        right_on="municipality_code",
        how="left",
    ).merge(
        scored[["municipality_code", HAZARD, "hazard_rank", "hazard_pct",
                RISK, "risk_rank", "risk_pct"]],
        left_on="ibge_code",
        right_on="municipality_code",
        how="left",
        suffixes=("", "_scored"),
    )
    if joined["distance_km"].isna().any():
        missing = joined.loc[joined["distance_km"].isna(), "municipality"].tolist()
        raise ValueError(f"reference cases absent from the delivered set: {missing}")

    joined["verdict_hazard"] = [
        verdict(exp, pct if pd.notna(pct) else None)
        for exp, pct in zip(joined["expectation_hazard"], joined["hazard_pct"])
    ]
    joined["verdict_risk"] = [
        verdict(exp, pct if pd.notna(pct) else None)
        for exp, pct in zip(joined["expectation_risk"], joined["risk_pct"])
    ]
    columns = [
        "municipality", "state", "role", "expectation_hazard", "verdict_hazard",
        "hazard_rank", HAZARD, "expectation_risk", "verdict_risk", "risk_rank",
        RISK, "Hazard_Frequency", "Hazard_Severity", "Exposure_absolute",
        "Exposure_relative", "Exposure_Index", "Vulnerability_CDF_PC1",
        "pop_municipality", "pop_eff", "distance_km", "coverage_status",
        "risk_zero_cause", "evidence", "rationale",
    ]
    return joined[columns].sort_values(["role", "state", "municipality"]).reset_index(
        drop=True
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    delivered, scored, cases = load()
    report = build_report(delivered, scored, cases)
    diverging = report[
        report["verdict_hazard"].str.startswith("diverges")
        | report["verdict_risk"].str.startswith("diverges")
    ]

    report.to_csv(OUT_DIR / "case_report.csv", index=False)
    diverging.to_csv(OUT_DIR / "divergences.csv", index=False)

    def tally(column: str) -> dict[str, int]:
        return report[column].value_counts().to_dict()

    summary = {
        "sources": {
            "product": str(GEOJSON.relative_to(ROOT)),
            "reference_cases": str(CASES.relative_to(ROOT)),
        },
        "list_provenance": (
            "Built only from the immutable baseline review of 2026-07-29 and the "
            "external literature identified while closing AUD-02, and committed "
            "before this script was first run."
        ),
        "thresholds": {
            "high_expectation_met_at_or_above_percentile": HIGH_PERCENTILE,
            "low_expectation_met_at_or_below_percentile": LOW_PERCENTILE,
        },
        "n_cases": int(len(report)),
        "by_role": report["role"].value_counts().to_dict(),
        "hazard_verdicts": tally("verdict_hazard"),
        "risk_verdicts": tally("verdict_risk"),
        "n_diverging_on_either": int(len(diverging)),
        "diverging": diverging[
            ["municipality", "state", "role", "expectation_hazard",
             "verdict_hazard", "hazard_rank", "expectation_risk", "verdict_risk",
             "risk_rank"]
        ].to_dict("records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    pd.set_option("display.width", 200)
    print(
        report[
            ["municipality", "state", "role", "expectation_hazard", "verdict_hazard",
             "hazard_rank", "expectation_risk", "verdict_risk", "risk_rank"]
        ].to_string(index=False)
    )
    print("\nHazard verdicts:", json.dumps(summary["hazard_verdicts"], ensure_ascii=False))
    print("Risk verdicts:  ", json.dumps(summary["risk_verdicts"], ensure_ascii=False))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
