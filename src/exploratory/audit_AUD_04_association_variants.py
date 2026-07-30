"""AUD-04 diagnostic: compare candidate rules for transferring hazard to municipalities.

The delivered association assigns one ocean grid point per municipality by a
rule produced outside the repository, which does not reproduce (see
``audit_AUD_04_association_diagnosis``). This implements the candidate
replacements listed in AUD-04 Sec. 8 and compares them on the same hazard field,
so the choice can be made on evidence.

Candidates, all computed from versioned inputs and fully reproducible::

    delivered   the external association currently in use, for reference
    nearest     nearest grid point to the municipal polygon
    maxcount    highest compound-event count within a radius
    idw         inverse-distance-weighted mean of the points within a radius
    exposed     highest local wave threshold within a radius, i.e. the most
                wave-exposed point
    coastline   mean over the coastal segments nearest to the municipality,
                reusing the same coastline projection the figures and the site
                already use

``nearest``, ``maxcount`` and ``exposed`` select a single point; ``idw`` and
``coastline`` average several, which smooths the field and interacts with the
municipal renormalisation (AUD-11) — reported rather than assumed away.

Adopts nothing. Changing the association changes every municipal hazard value
at once, so the decision is left to the user.

Usage:
    python -m src.exploratory.audit_AUD_04_association_variants

Output:
    outputs/audit/AUD-04_association_variants/variants_by_municipality.csv
    outputs/audit/AUD-04_association_variants/variants_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from src.risk_integration.coastal_projection import (
    COASTAL_PROJECTION_CRS,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.hazard_index import derive_native_hazard_index

ROOT = Path(__file__).resolve().parents[2]
MUNICIPAL_SHAPEFILE = ROOT / "outputs" / "risk_index" / "risk_index.shp"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-04_association_variants"

#: Radius for the neighbourhood rules, in metres.
RADIUS_M = 30_000.0
#: Power of the inverse-distance weighting.
IDW_POWER = 2.0
#: Floor on distance so a point inside the polygon does not produce a zero divisor.
IDW_MIN_DISTANCE_M = 1_000.0

VARIANTS = ("delivered", "nearest", "maxcount", "idw", "exposed", "coastline")


def _resolve(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _minmax(values: pd.Series) -> pd.Series:
    finite = values[np.isfinite(values)]
    if finite.empty or np.isclose(finite.min(), finite.max()):
        return pd.Series(np.nan, index=values.index)
    return (values - finite.min()) / (finite.max() - finite.min())


def main() -> None:
    if not MUNICIPAL_SHAPEFILE.exists():
        raise FileNotFoundError(MUNICIPAL_SHAPEFILE)

    grid, _ = derive_native_hazard_index()
    points = gpd.GeoDataFrame(
        grid.copy(),
        geometry=gpd.points_from_xy(grid["grid_lon"], grid["grid_lat"]),
        crs="EPSG:4326",
    ).to_crs(COASTAL_PROJECTION_CRS)

    municipalities = gpd.read_file(MUNICIPAL_SHAPEFILE)
    columns = list(municipalities.columns)
    code_col = _resolve(columns, ("CD_MUN",))
    name_col = _resolve(columns, ("NM_MUN", "municipali"))
    state_col = _resolve(columns, ("SIGLA_UF", "uf"))
    lat_col = _resolve(columns, ("grid_lat",))
    lon_col = _resolve(columns, ("grid_lon",))
    municipalities = municipalities.to_crs(COASTAL_PROJECTION_CRS)

    grid_key = {
        (round(la, 4), round(lo, 4)): i
        for i, (la, lo) in enumerate(zip(grid["grid_lat"], grid["grid_lon"]))
    }
    hazard = grid["Hazard_Index"].to_numpy(dtype=float)

    # Coastline variant: project the hazard onto 5 km coastal segments and take,
    # for each municipality, the mean over the segments nearest to it. This is
    # the same geometry the article figures and the website already use.
    print("Projecting hazard onto the coastline ...")
    coastal_municipalities, coastline = read_coastal_inputs()
    segments, _ = project_values_to_coastline(
        grid, ["Hazard_Index"],
        municipalities=coastal_municipalities, coastline=coastline,
    )
    segments = segments.to_crs(COASTAL_PROJECTION_CRS)
    segment_points = gpd.GeoDataFrame(
        {"Hazard_Index": segments["Hazard_Index"].to_numpy(dtype=float)},
        geometry=segments.geometry.centroid,
        crs=COASTAL_PROJECTION_CRS,
    )
    municipal_index = gpd.GeoDataFrame(
        {"_mun": np.arange(len(municipalities))},
        geometry=municipalities.geometry,
        crs=COASTAL_PROJECTION_CRS,
    )
    joined = gpd.sjoin_nearest(segment_points, municipal_index, how="left")
    coastline_mean = joined.groupby("_mun")["Hazard_Index"].mean()
    coastline_count = joined.groupby("_mun")["Hazard_Index"].size()
    print("Coastline projection complete.")

    rows = []
    for position, (_, feature) in enumerate(municipalities.iterrows()):
        record = {
            "municipality_code": feature[code_col],
            "municipality_name": feature[name_col],
            "state": feature[state_col] if state_col else None,
        }
        geometry = feature.geometry
        if geometry is None or geometry.is_empty:
            rows.append(record)
            continue

        assigned_index = grid_key.get(
            (round(feature[lat_col], 4), round(feature[lon_col], 4))
        )
        if assigned_index is not None:
            record["delivered"] = hazard[assigned_index]

        distances = points.geometry.distance(geometry).to_numpy(dtype=float)
        nearest_index = int(distances.argmin())
        record["nearest"] = hazard[nearest_index]
        record["distance_nearest_km"] = distances[nearest_index] / 1000.0
        if assigned_index is not None:
            record["distance_delivered_km"] = distances[assigned_index] / 1000.0

        within = np.flatnonzero(distances <= RADIUS_M)
        # A municipality with no point inside the radius falls back to the
        # nearest point, so that no unit is left without a value; flagged.
        record["n_points_in_radius"] = int(within.size)
        if within.size == 0:
            within = np.array([nearest_index])
            record["radius_fallback"] = True
        else:
            record["radius_fallback"] = False

        counts = grid["compound_count_total"].to_numpy(dtype=float)[within]
        record["maxcount"] = hazard[within[int(np.argmax(counts))]]

        thresholds = grid["thr_hs_abs"].to_numpy(dtype=float)[within]
        record["exposed"] = hazard[within[int(np.argmax(thresholds))]]

        weights = 1.0 / np.maximum(distances[within], IDW_MIN_DISTANCE_M) ** IDW_POWER
        record["idw"] = float(np.average(hazard[within], weights=weights))

        record["coastline"] = float(coastline_mean.get(position, np.nan))
        record["n_coastal_segments"] = int(coastline_count.get(position, 0))
        rows.append(record)

    table = pd.DataFrame(rows)
    valid = table[table["delivered"].notna()].copy()

    # Municipal renormalisation, as the risk product applies it.
    for variant in VARIANTS:
        valid[f"{variant}_mun"] = _minmax(valid[variant])
        valid[f"{variant}_rank"] = valid[variant].rank(ascending=False)

    reference = valid["delivered"]
    comparison = {}
    for variant in VARIANTS:
        if variant == "delivered":
            continue
        series = valid[variant]
        both = reference.notna() & series.notna()
        top20_ref = set(valid.nsmallest(20, "delivered_rank")["municipality_code"])
        top20_var = set(valid.nsmallest(20, f"{variant}_rank")["municipality_code"])
        comparison[variant] = {
            "spearman_vs_delivered": float(
                reference[both].corr(series[both], method="spearman")
            ),
            "mean_abs_difference": float((series[both] - reference[both]).abs().mean()),
            "max_abs_difference": float((series[both] - reference[both]).abs().max()),
            "top20_overlap_with_delivered": len(top20_ref & top20_var),
            "std_of_field": float(series.std()),
        }

    testcases = [
        "Itajaí", "Navegantes", "Balneário Camboriú", "Itapema", "Caraguatatuba",
        "Magé", "Duque de Caxias", "Guapimirim", "São Gonçalo",
        "Paraty", "Angra dos Reis", "Vigia", "Colares", "Paracuru",
    ]
    testcase_rows = valid[valid["municipality_name"].isin(testcases)][
        ["municipality_name", "state", *VARIANTS, "distance_delivered_km",
         "distance_nearest_km", "n_points_in_radius"]
    ].round(3)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_04_association_variants",
        "radius_km": RADIUS_M / 1000.0,
        "idw_power": IDW_POWER,
        "n_municipalities": int(len(valid)),
        "note": (
            "Hazard field is the revised two-component index (AUD-01/AUD-06). "
            "Values are the native-grid Hazard_Index before municipal "
            "renormalisation."
        ),
        "comparison_vs_delivered": comparison,
        "field_dispersion": {
            variant: {
                "std": float(valid[variant].std()),
                "iqr": float(
                    valid[variant].quantile(0.75) - valid[variant].quantile(0.25)
                ),
            }
            for variant in VARIANTS
        },
        "radius_fallbacks": int(valid["radius_fallback"].sum()),
        "municipalities_with_no_coastal_segment": int((valid["n_coastal_segments"] == 0).sum()),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    valid.to_csv(OUT_DIR / "variants_by_municipality.csv", index=False)
    testcase_rows.to_csv(OUT_DIR / "variants_testcases.csv", index=False)
    with (OUT_DIR / "variants_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=float)

    pd.set_option("display.width", 220)
    print(json.dumps(summary["comparison_vs_delivered"], indent=2, default=float))
    print()
    print("Dispersão do campo (desvio-padrão do Hazard_Index municipal):")
    for variant in VARIANTS:
        print(f"  {variant:<12}{summary['field_dispersion'][variant]['std']:.4f}")
    print()
    print("Casos-teste:")
    print(testcase_rows.to_string(index=False))


if __name__ == "__main__":
    main()
