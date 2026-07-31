"""AUD-15 diagnostic: recount the sample coverage of the current product.

The coverage figures in the issue record -- 282 municipalities delivered, 280
with a hazard association, four with a degenerate exposure count -- were taken
before the Step 3 catalogue was regenerated on the q70/q99 detector with the HAT
gate. Two of those numbers can move under the new method even though no
municipality was added or removed: a municipality keeps its association but its
point may now accept no compound event at all, which is a different kind of
absence and was not previously possible to report.

This recounts every category from the current files and names every case, so
that the manuscript, the README and the site can state the absences by name
rather than leaving them in a metadata JSON.

Usage:
    python -m src.exploratory.audit_AUD_15_sample_coverage

Output:
    outputs/audit/AUD-15_sample_coverage/coverage_by_municipality.csv
    outputs/audit/AUD-15_sample_coverage/absent_and_degenerate_cases.csv
    outputs/audit/AUD-15_sample_coverage/coverage_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
METADATA = ROOT / "site" / "public" / "data" / "risk_index_metadata.json"
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
ASSOCIATION = (
    ROOT / "data" / "external" / "municipal_grid_association"
    / "municipal_grid_association.csv"
)
HAT_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-15_sample_coverage"

#: Population within 10 km below which the exposure count is treated as
#: degenerate: the municipality is in the set but the metric cannot discriminate.
DEGENERATE_POP_10KM = 1000
#: Floor applied to every component before the geometric mean.
CLIP_FLOOR = 0.01


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = json.loads(GEOJSON.read_text())
    frame = pd.DataFrame([f["properties"] for f in payload["features"]])
    metadata = json.loads(METADATA.read_text())
    metrics = pd.read_csv(HAT_METRICS)

    frame["risk_rank"] = frame["Risk_Hazard"].rank(ascending=False, method="min")

    # Grid-point activity behind each association: a municipality can hold a
    # valid association to a point that accepted no compound event at all.
    metrics["key"] = list(
        zip(metrics["grid_lat"].round(2) + 0.0, metrics["grid_lon"].round(2) + 0.0)
    )
    activity = metrics.set_index("key")[
        ["compound_count_total", "mean_integrated_severity", "n_candidate_events",
         "n_rejected_by_hat", "thr_hs_abs", "hat_m"]
    ]
    frame["key"] = list(
        zip(
            pd.to_numeric(frame["grid_lat"], errors="coerce").round(2) + 0.0,
            pd.to_numeric(frame["grid_lon"], errors="coerce").round(2) + 0.0,
        )
    )
    joined = frame.join(activity, on="key", rsuffix="_pt")

    joined["has_association"] = joined["grid_lat"].notna() & joined["grid_lon"].notna()
    joined["has_hazard_value"] = joined["Hazard_Index_mun"].notna()
    joined["has_risk_value"] = joined["Risk_Hazard"].notna()
    joined["has_svi"] = joined["SVI_Coast_2022"].notna()
    joined["point_accepted_zero_events"] = (
        joined["has_association"] & (joined["compound_count_total"].fillna(-1) == 0)
    )
    joined["degenerate_exposure"] = joined["pop_10km"] < DEGENERATE_POP_10KM
    joined["exposure_at_floor"] = (
        joined["Exposure_Index"].round(6) <= CLIP_FLOOR + 1e-9
    )

    def _reason(row: pd.Series) -> str:
        if not row["has_association"]:
            return "no grid-point association in the delivered/archived file"
        if not row["has_hazard_value"]:
            return "association present but no hazard value transferred"
        return ""

    joined["absence_reason"] = joined.apply(_reason, axis=1)

    export_columns = [
        "municipality_code",
        "municipality_name",
        "state",
        "grid_lat",
        "grid_lon",
        "has_association",
        "has_svi",
        "has_hazard_value",
        "has_risk_value",
        "absence_reason",
        "compound_count_total",
        "mean_integrated_severity",
        "n_candidate_events",
        "n_rejected_by_hat",
        "point_accepted_zero_events",
        "pop_municipality",
        "pop_10km",
        "degenerate_exposure",
        "Exposure_Index",
        "exposure_at_floor",
        "SVI_Coast_2022",
        "Hazard_Index_mun",
        "Risk_Hazard",
        "risk_rank",
    ]
    joined[export_columns].sort_values(
        ["has_risk_value", "risk_rank"], na_position="first"
    ).to_csv(OUT_DIR / "coverage_by_municipality.csv", index=False)

    cases = joined[
        (~joined["has_risk_value"])
        | joined["degenerate_exposure"]
        | joined["point_accepted_zero_events"]
    ][export_columns].copy()

    def _category(row: pd.Series) -> str:
        parts = []
        if not row["has_risk_value"]:
            parts.append("absent from the risk map")
        if row["point_accepted_zero_events"]:
            parts.append("hazard point accepted zero compound events")
        if row["degenerate_exposure"]:
            parts.append(f"pop_10km < {DEGENERATE_POP_10KM}")
        return "; ".join(parts)

    cases["category"] = cases.apply(_category, axis=1)
    cases.sort_values(["category", "municipality_name"]).to_csv(
        OUT_DIR / "absent_and_degenerate_cases.csv", index=False
    )

    absent = joined[~joined["has_risk_value"]]
    zero_event = joined[joined["point_accepted_zero_events"]]
    degenerate = joined[joined["degenerate_exposure"]]

    # Sensitivity: does dropping the degenerate-exposure municipalities move the
    # published ranking? They anchor no normalisation if their removal leaves
    # rho at 1.
    retained = joined[
        joined["has_risk_value"] & ~joined["degenerate_exposure"]
    ].copy()
    h = retained["Hazard_Index_mun"].clip(lower=CLIP_FLOOR)
    e = retained["Exposure_Index"].clip(lower=CLIP_FLOOR)
    v = (retained["SVI_Coast_2022"] / 100.0).clip(lower=CLIP_FLOOR)
    raw = np.cbrt(h * e * v)
    rescaled = (raw - raw.min()) / (raw.max() - raw.min())
    rho_after_exclusion = float(
        spearmanr(rescaled, retained["Risk_Hazard"])[0]
    )
    max_shift = float(
        np.max(
            np.abs(
                rescaled.rank(ascending=False, method="min")
                - retained["Risk_Hazard"].rank(ascending=False, method="min")
            )
        )
    )

    summary = {
        "generated_by": "src.exploratory.audit_AUD_15_sample_coverage",
        "sources": {
            "municipal_product": str(GEOJSON.relative_to(ROOT)),
            "metadata": str(METADATA.relative_to(ROOT)),
            "hazard_metrics": str(HAT_METRICS.relative_to(ROOT)),
            "association_archive": str(ASSOCIATION.relative_to(ROOT)),
        },
        "counts": {
            "municipalities_delivered": int(len(joined)),
            "with_svi": int(joined["has_svi"].sum()),
            "with_grid_association": int(joined["has_association"].sum()),
            "with_hazard_value": int(joined["has_hazard_value"].sum()),
            "with_risk_value": int(joined["has_risk_value"].sum()),
            "absent_from_risk_map": int(len(absent)),
            "association_to_a_point_with_zero_accepted_events": int(len(zero_event)),
            "degenerate_exposure_pop10km_below_1000": int(len(degenerate)),
            "exposure_at_the_0.01_floor": int(joined["exposure_at_floor"].sum()),
        },
        "absent_municipalities": [
            {
                "municipality_name": row["municipality_name"],
                "state": row["state"],
                "reason": row["absence_reason"],
                "svi": None
                if pd.isna(row["SVI_Coast_2022"])
                else round(float(row["SVI_Coast_2022"]), 3),
                "pop_10km": None
                if pd.isna(row["pop_10km"])
                else int(row["pop_10km"]),
            }
            for _, row in absent.iterrows()
        ],
        "zero_event_point_municipalities": [
            {
                "municipality_name": row["municipality_name"],
                "state": row["state"],
                "grid_lat": float(row["grid_lat"]),
                "grid_lon": float(row["grid_lon"]),
                "n_candidate_events": int(row["n_candidate_events"]),
                "n_rejected_by_hat": int(row["n_rejected_by_hat"]),
                "Hazard_Index_mun": float(row["Hazard_Index_mun"]),
                "risk_rank": int(row["risk_rank"]),
            }
            for _, row in zero_event.sort_values("municipality_name").iterrows()
        ],
        "degenerate_exposure_municipalities": [
            {
                "municipality_name": row["municipality_name"],
                "state": row["state"],
                "pop_municipality": int(row["pop_municipality"]),
                "pop_10km": int(row["pop_10km"]),
                "Exposure_Index": round(float(row["Exposure_Index"]), 4),
                "risk_rank": None
                if pd.isna(row["risk_rank"])
                else int(row["risk_rank"]),
            }
            for _, row in degenerate.sort_values("pop_10km").iterrows()
        ],
        "exclusion_sensitivity": {
            "test": (
                "recompute the risk over the municipalities that remain after "
                "dropping those with pop_10km below 1000"
            ),
            "municipalities_retained": int(len(retained)),
            "spearman_rho_vs_published": rho_after_exclusion,
            "max_absolute_rank_shift": max_shift,
        },
        "metadata_agreement": {
            "metadata_municipality_feature_count": metadata["hazard_transfer"][
                "municipality_feature_count"
            ],
            "metadata_matched_hazard_count": metadata["hazard_transfer"][
                "matched_hazard_count"
            ],
            "metadata_missing_municipalities": [
                m["municipality_name"]
                for m in metadata["hazard_transfer"]["missing_municipalities"]
            ],
            "agrees_with_recount": bool(
                metadata["hazard_transfer"]["matched_hazard_count"]
                == int(joined["has_hazard_value"].sum())
                and metadata["hazard_transfer"]["municipality_feature_count"]
                == len(joined)
            ),
        },
    }
    (OUT_DIR / "coverage_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
