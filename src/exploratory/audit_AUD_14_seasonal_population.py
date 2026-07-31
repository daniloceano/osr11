"""AUD-14 diagnostic: does the seasonal-population blind spot attenuate or aggravate?

The exposure term counts residents *de jure* on 2022-07-31. The floating summer
population of the resort municipalities is invisible, and the bias is
directional: it understates exactly the SC/PR/SP/RJ sector that carries the
highest physical hazard.

Two questions can be answered from data already in the repository, without
inventing a seasonal estimate:

1. **Does the hazard season coincide with the tourist season?** If compound
   events concentrate in austral autumn and winter, when the resort towns are
   empty, the effective annual bias is smaller than the summer peak suggests.
   Answered from the Step 3.4 seasonality product, regenerated on 2026-07-31.
2. **Which municipalities look like they hold occasional-use dwellings?** The
   ratio of residents to occupied households within 10 km is the immediate
   proxy: an anomalously low ratio marks a housing stock larger than its
   resident population. This is a *flag*, not an estimate — it is reported
   without being converted into people.

The occasional-use-dwelling count itself is deliberately NOT estimated here.
The IBGE statistical grid carries only TOTAL and TOTAL_DOM; the occasional-use
variable would require a separate SIDRA acquisition with its own provenance
record, and any occupancy factor applied to it would be an unverifiable
assumption in a layer that is currently sound.

Usage:
    python -m src.exploratory.audit_AUD_14_seasonal_population

Output:
    outputs/audit/AUD-14_seasonal_population/hazard_seasonality_by_region.csv
    outputs/audit/AUD-14_seasonal_population/occasional_use_proxy.csv
    outputs/audit/AUD-14_seasonal_population/diagnosis_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SEASONALITY = (
    ROOT / "outputs" / "storm_catalog" / "seasonality" / "seasonality_summary.csv"
)
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-14_seasonal_population"

#: Austral summer, when the floating population of the resort towns peaks.
SUMMER = "DJF"

#: Latitude bands. The resort-municipality problem is concentrated in the two
#: southern ones.
BANDS = (
    ("N/NE (north of 12 S)", -12.0, 6.5),
    ("ES/BA-S", -21.0, -12.0),
    ("SP/RJ", -25.0, -21.0),
    ("SC/PR", -29.0, -25.0),
    ("RS", -35.5, -29.0),
)

#: Municipalities named in the issue record as the ones the bias bites hardest.
NAMED_RESORTS = (
    "Balneário Camboriú",
    "Bombinhas",
    "Guarujá",
    "Ubatuba",
    "Cabo Frio",
)


def _band_of(lat: float) -> str:
    for name, low, high in BANDS:
        if low <= lat < high:
            return name
    return "out of band"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Hazard seasonality ────────────────────────────────────────────────
    seasons = pd.read_csv(SEASONALITY)
    seasons["band"] = seasons["grid_lat"].map(_band_of)
    season_cols = [
        c for c in seasons.columns if c.startswith("compound_season_")
    ]
    grouped = seasons.groupby("band")[season_cols].sum()
    totals = grouped.sum(axis=1)
    shares = grouped.div(totals.where(totals > 0), axis=0)
    shares["n_points"] = seasons.groupby("band").size()
    shares["compound_events"] = totals
    shares = shares.reset_index()
    shares.to_csv(OUT_DIR / "hazard_seasonality_by_region.csv", index=False)

    summer_col = f"compound_season_{SUMMER}"
    summer_share = {
        row["band"]: (
            None
            if not np.isfinite(row[summer_col])
            else round(float(row[summer_col]), 4)
        )
        for _, row in shares.iterrows()
    }

    # ── 2. Occasional-use proxy ──────────────────────────────────────────────
    exposure = pd.read_csv(EXPOSURE_CSV)
    payload = json.loads(GEOJSON.read_text())
    municipal = pd.DataFrame([f["properties"] for f in payload["features"]])

    # Merge on the IBGE code, never on the name: "Santa Rita" exists in both
    # MA and PB in this set, and a name join would duplicate both rows.
    frame = exposure[
        ["municipality_code", "municipality_name", "state", "pop_10km", "dom_10km"]
    ].copy()
    frame["municipality_code"] = frame["municipality_code"].astype(str)
    frame = frame[frame["dom_10km"] > 0].copy()
    frame["residents_per_household_10km"] = (
        frame["pop_10km"] / frame["dom_10km"]
    )
    national = float(frame["pop_10km"].sum() / frame["dom_10km"].sum())
    frame["ratio_minus_national"] = (
        frame["residents_per_household_10km"] - national
    )
    municipal["municipality_code"] = municipal["municipality_code"].astype(str)
    frame = frame.merge(
        municipal[["municipality_code", "Risk_Hazard"]],
        on="municipality_code",
        how="left",
    )
    assert len(frame) == len(exposure[exposure["dom_10km"] > 0]), "merge duplicated rows"
    frame["risk_rank"] = frame["Risk_Hazard"].rank(ascending=False, method="min")
    frame = frame.sort_values("residents_per_household_10km")
    frame.to_csv(OUT_DIR / "occasional_use_proxy.csv", index=False)

    lowest = frame.head(20)[
        [
            "municipality_name",
            "state",
            "pop_10km",
            "dom_10km",
            "residents_per_household_10km",
            "risk_rank",
        ]
    ]
    named = frame[frame["municipality_name"].isin(NAMED_RESORTS)][
        [
            "municipality_name",
            "state",
            "pop_10km",
            "dom_10km",
            "residents_per_household_10km",
            "risk_rank",
        ]
    ]

    summary = {
        "generated_by": "src.exploratory.audit_AUD_14_seasonal_population",
        "sources": {
            "seasonality": str(SEASONALITY.relative_to(ROOT)),
            "exposure": str(EXPOSURE_CSV.relative_to(ROOT)),
            "municipal_product": str(GEOJSON.relative_to(ROOT)),
        },
        "hazard_seasonality": {
            "note": (
                "Share of accepted compound events falling in each austral "
                "season, by latitude band, from the Step 3.4 product "
                "regenerated on 2026-07-31."
            ),
            "summer_DJF_share_by_band": summer_share,
            "by_band": shares.round(4).to_dict(orient="records"),
        },
        "occasional_use_proxy": {
            "note": (
                "Residents per occupied household within 10 km. A low value "
                "flags a housing stock larger than the resident population, "
                "which is what a high share of occasional-use dwellings looks "
                "like. It is a flag, not an estimate of people."
            ),
            "national_ratio_over_the_set": round(national, 4),
            "verdict": (
                "The proxy does not work, and the reason is definitional. IBGE "
                "counts *occupied* households, so dwellings of occasional use "
                "are already excluded from the denominator as well as from the "
                "numerator. The ratio therefore measures household size, not "
                "the size of the housing stock relative to the resident "
                "population, and it cannot detect second homes. The named "
                "resort municipalities confirm this: they sit at 2.41-2.89 "
                "residents per household against a set-wide 2.71, i.e. astride "
                "the average rather than below it, with only Balneario Camboriu "
                "clearly low. Diagnostic 2 of the issue record is recorded here "
                "as attempted and rejected; the occasional-use variable itself "
                "would have to come from a new SIDRA acquisition."
            ),
            "twenty_lowest": lowest.round(3).to_dict(orient="records"),
            "named_resort_municipalities": named.round(3).to_dict(orient="records"),
        },
        "not_estimated": {
            "occasional_use_dwelling_count": (
                "Not obtained. The IBGE Grade Estatística 2022 carries TOTAL "
                "and TOTAL_DOM only; the occasional-use category exists at "
                "census-tract level in SIDRA and would require a separate "
                "acquisition with its own provenance record. No occupancy "
                "factor is applied, because any such factor would be an "
                "unverifiable assumption imposed on a layer that is currently "
                "sound, and inflating the resort municipalities would 'fix' "
                "the known validation failures by parameter adjustment rather "
                "than by correcting a mechanism."
            )
        },
    }
    (OUT_DIR / "diagnosis_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
