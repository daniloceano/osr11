"""Export the municipal population-exposure layer for the results website.

Joins ``outputs/exposure/municipal_exposure.csv`` to the municipal geometry
already published for the risk layer and writes:

    site/public/data/exposure_municipalities.geojson
    site/public/data/exposure_metadata.json

The site publishes the adopted exposure term and its auditable components:

* ``E_inform`` — the adopted fixed-goalpost index, applied to ``pop_eff``;
* ``E_inform_absolute`` and ``E_inform_relative`` — its two components;
* ``pop_eff`` and the four cumulative bands — the source quantities.

The two halves of ``E_inform`` travel with it as ``E_inform_absolute`` and
``E_inform_relative`` so the pair can be inspected separately.

The former Min--Max, log-Min--Max and rank candidates remain in feature
properties for audit comparisons, but are not offered as current map layers.

Raw counts travel with the normalised values so a reader hovering a
municipality sees the population behind the number, in every distance band.

Usage:
    python -m src.site.export_exposure_data
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd

from src.risk_integration.coastal_projection import COASTAL_MAP_EXTENT
from src.risk_integration.exposure_index import (
    EFFECTIVE_POPULATION_WEIGHTS,
    GOALPOST_MAX_INHABITANTS,
    GOALPOST_MIN_INHABITANTS,
    all_variants,
    effective_population,
    variant_components,
)
from src.risk_integration.palettes import component_colors, risk_colors


ROOT = Path(__file__).resolve().parents[2]
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
EXPOSURE_METADATA = ROOT / "outputs" / "exposure" / "municipal_exposure_metadata.json"
RISK_GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"

SITE_DATA_DIR = ROOT / "site" / "public" / "data"
OUTPUT_GEOJSON = SITE_DATA_DIR / "exposure_municipalities.geojson"
OUTPUT_METADATA = SITE_DATA_DIR / "exposure_metadata.json"

OUTPUT_CRS = "EPSG:4326"
EXPOSURE_FIELD = "pop_eff"
NORMALIZED_BOUNDARIES = [round(value, 3) for value in np.linspace(0.0, 1.0, 9)]
#: Class limits for the coastal share, in per cent. Deliberately not uniform:
#: the median municipality has 90 % of its people inside the band and a quarter
#: has more than 99.8 %, so equal-width classes would collapse the top.
SHARE_BOUNDARIES = [0.0, 25.0, 50.0, 65.0, 80.0, 90.0, 95.0, 99.0, 100.0]


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return round(value, 6) if math.isfinite(value) else None
    return value


def _numeric_stats(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce").dropna().astype(float)
    if values.empty:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {
        "count": int(values.count()),
        "min": round(float(values.min()), 6),
        "max": round(float(values.max()), 6),
        "mean": round(float(values.mean()), 6),
        "median": round(float(values.median()), 6),
    }


def _count_boundaries(series: pd.Series) -> list[float]:
    """Class limits for a raw population count, on a log-spaced ladder.

    Equal-width classes on a count this skewed would put every municipality in
    the first class, which is exactly the failure the page is about.
    """
    values = pd.to_numeric(series, errors="coerce").dropna()
    upper = float(values.max())
    ladder = [0, 1_000, 5_000, 20_000, 50_000, 150_000, 400_000, 1_000_000]
    while ladder[-1] < upper:
        ladder.append(ladder[-1] * 3)
    return [float(value) for value in ladder]


def build_exposure_layer() -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    for path in (EXPOSURE_CSV, RISK_GEOJSON):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is required. Run src.risk_integration.municipal_exposure "
                "and src.site.export_risk_index_data first; there is no fallback."
            )

    municipalities = gpd.read_file(RISK_GEOJSON)
    exposure = pd.read_csv(EXPOSURE_CSV, dtype={"municipality_code": str})
    municipalities["municipality_code"] = municipalities["municipality_code"].astype(str)

    count_fields = [
        column
        for column in exposure.columns
        if column.startswith(("pop_", "dom_"))
    ]
    merged = municipalities[
        ["municipality_code", "municipality_name", "state", "state_name", "geometry"]
    ].merge(
        exposure[["municipality_code", *count_fields]],
        on="municipality_code",
        how="left",
        validate="one_to_one",
    )
    merged[EXPOSURE_FIELD] = effective_population(merged)
    missing = int(merged[EXPOSURE_FIELD].isna().sum())
    if missing:
        raise ValueError(
            f"{missing} municipalities have no exposure value; the exposure table "
            "and the municipal layer do not describe the same set"
        )

    population = pd.to_numeric(merged[EXPOSURE_FIELD], errors="coerce")
    municipal_population = pd.to_numeric(merged["pop_municipality"], errors="coerce")
    derived = {
        **all_variants(population, municipal_population),
        **variant_components(population, municipal_population),
    }
    for name, values in derived.items():
        merged[name] = values
    merged["share_pop_eff"] = (
        population / municipal_population.replace(0, np.nan) * 100.0
    ).fillna(0.0).clip(0.0, 100.0)

    # The coastal share in its readable unit. ``E_inform_relative`` is the same
    # quantity as a fraction, which is what the formula consumes; these are for
    # reading and mapping.
    share_fields: list[str] = []
    for band in ("1km", "2km", "5km", "10km"):
        for prefix, total in (("pop", "pop_municipality"), ("dom", "dom_municipality")):
            source, denominator = f"{prefix}_{band}", total
            if source not in merged or denominator not in merged:
                continue
            field = f"share_{prefix}_{band}"
            merged[field] = (
                pd.to_numeric(merged[source], errors="coerce")
                / pd.to_numeric(merged[denominator], errors="coerce").replace(0, np.nan)
                * 100.0
            ).fillna(0.0).clip(0.0, 100.0)
            share_fields.append(field)

    export = gpd.GeoDataFrame(geometry=merged.geometry, crs=OUTPUT_CRS)
    for column in (
        "municipality_code",
        "municipality_name",
        "state",
        "state_name",
        *count_fields,
        *share_fields,
        *derived,
        "pop_eff",
        "share_pop_eff",
    ):
        export[column] = merged[column].map(_to_jsonable)

    layers: list[dict[str, Any]] = [
        {
            "key": "E_inform",
            "label": "Exposure — adopted effective-population criterion",
            "short_label": "Exposure Index",
            "unit": "0–1",
            "stage": "index",
            "group": "Adopted exposure criterion",
            "actual_field": (
                "derived:geomean(goalposts(log10(pop_eff), 1e2, 1e6), "
                "pop_eff/pop_municipality)"
            ),
            "decimals": 3,
            "boundaries": NORMALIZED_BOUNDARIES,
            "colors": risk_colors(8),
            "palette": "risk",
            "palette_source": "green-to-red palette shared with the hazard and risk layers",
            "description": (
                "The effective/weighted population on a log scale between fixed goalposts of "
                f"{GOALPOST_MIN_INHABITANTS:,.0f} and {GOALPOST_MAX_INHABITANTS:,.0f} "
                "inhabitants, combined by geometric mean with the share of the "
                "municipal population inside the band. Following INFORM: the "
                "absolute count favours the metropolitan municipalities and the "
                "share favours the small fully-coastal ones, so the indicator is "
                "computed both ways and the pair aggregated. Fixed goalposts make "
                "the scale independent of which municipalities are in the set — "
                "0.5 always denotes 10,000 inhabitants — at the cost of saturating "
                "the six municipalities outside them."
            ),
            "stats": _numeric_stats(export["E_inform"]),
        },
        {
            "key": "E_inform_absolute",
            "label": "INFORM half — absolute count between goalposts",
            "short_label": "E abs (goalposts)",
            "unit": "0–1",
            "stage": "component",
            "group": "Components of the adopted criterion",
            "actual_field": "derived:goalposts(log10(pop_eff), 1e2, 1e6)",
            "decimals": 3,
            "boundaries": NORMALIZED_BOUNDARIES,
            "colors": risk_colors(8),
            "palette": "risk",
            "palette_source": "green-to-red palette shared with the hazard and risk layers",
            "description": (
                "How many people, on a log scale fixed between "
                f"{GOALPOST_MIN_INHABITANTS:,.0f} and {GOALPOST_MAX_INHABITANTS:,.0f} "
                "inhabitants. 0.5 always denotes 10,000 people, whichever "
                "municipalities are in the set. On its own it favours the "
                "metropolitan municipalities."
            ),
            "stats": _numeric_stats(export["E_inform_absolute"]),
        },
        {
            "key": "share_pop_eff",
            "label": "Exposure half — effective population as municipal share",
            "short_label": "Effective share",
            "unit": "%",
            "stage": "component",
            "group": "Components of the adopted criterion",
            "actual_field": "derived:100*pop_eff/pop_municipality",
            "decimals": 1,
            "boundaries": SHARE_BOUNDARIES,
            "colors": component_colors(len(SHARE_BOUNDARIES) - 1),
            "palette": "component",
            "palette_source": "magma ramp shared with the hazard components",
            "description": (
                "How coastal the municipality is, rather than how many people it "
                "holds: a hamlet entirely on the shore and a city entirely on the "
                "shore both reach 100 %. On its own it is not exposure, which is "
                "why it is paired with the absolute half. Class limits are not "
                "uniform — the median municipality is at 90 % and a quarter above "
                "99.8 %, so even classes would collapse the top of the scale."
            ),
            "stats": _numeric_stats(export["share_pop_eff"]),
        },
        {
            "key": "E_log10",
            "label": "Exposure — Min–Max of log₁₀(population+1)",
            "short_label": "E (log₁₀)",
            "unit": "0–1",
            "stage": "normalized",
            "group": "Candidate normalisations",
            "actual_field": "derived:minmax(log10(pop_eff+1))",
            "decimals": 3,
            "boundaries": NORMALIZED_BOUNDARIES,
            "colors": risk_colors(8),
            "palette": "risk",
            "palette_source": "green-to-red palette shared with the hazard and risk layers",
            "description": (
                "Exposure read as an order of magnitude. The logarithm repairs the "
                "shape of the count before the rescaling, so every municipality "
                "occupies the scale — but it compresses real differences: Rio de "
                "Janeiro ends about 1.5 times the median municipality rather than "
                "188 times."
            ),
            "stats": _numeric_stats(export["E_log10"]),
        },
        {
            "key": "E_rank",
            "label": "Exposure — percentile rank of the population",
            "short_label": "E (rank)",
            "unit": "0–1",
            "stage": "normalized",
            "group": "Candidate normalisations",
            "actual_field": "derived:rank(pop_eff, pct=True)",
            "decimals": 3,
            "boundaries": NORMALIZED_BOUNDARIES,
            "colors": risk_colors(8),
            "palette": "risk",
            "palette_source": "green-to-red palette shared with the hazard and risk layers",
            "description": (
                "Exposure read as a position along the Brazilian coast. Uniform by "
                "construction, so it discriminates everywhere — and it is the only "
                "candidate under which the exposure term actually drives the "
                "integrated risk. It discards magnitude entirely."
            ),
            "stats": _numeric_stats(export["E_rank"]),
        },
        {
            "key": EXPOSURE_FIELD,
            "label": "Effective population from cumulative distance bands",
            "short_label": "Effective population",
            "unit": "weighted inhabitants",
            "stage": "raw",
            "group": "Raw counts",
            "actual_field": EXPOSURE_FIELD,
            "decimals": 0,
            "boundaries": _count_boundaries(export[EXPOSURE_FIELD]),
            "colors": component_colors(len(_count_boundaries(export[EXPOSURE_FIELD])) - 1),
            "palette": "component",
            "palette_source": "magma ramp shared with the hazard components",
            "description": (
                "Weighted exposure proxy, not a literal inhabitant count: 0.4×pop_1km + "
                "0.3×pop_2km + 0.2×pop_5km + 0.1×pop_10km. Source counts come from "
                "the IBGE Grade Estatistica 2022 (200 m urban "
                "/ 1 km rural cells), attributed by cell centroid. Class limits are "
                "log-spaced: equal-width classes would place almost every "
                "municipality in the first one."
            ),
            "stats": _numeric_stats(export[EXPOSURE_FIELD]),
        },
        {
            "key": "dom_10km",
            "label": "Occupied households within 10 km of the coastline",
            "short_label": "Households ≤10 km",
            "unit": "households",
            "stage": "raw",
            "group": "Raw counts",
            "actual_field": "dom_10km",
            "decimals": 0,
            "boundaries": _count_boundaries(export["dom_10km"]),
            "colors": component_colors(len(_count_boundaries(export["dom_10km"])) - 1),
            "palette": "component",
            "palette_source": "magma ramp shared with the hazard components",
            "description": (
                "Occupied households, private and collective. A proxy for the "
                "residential asset stock; it excludes the seasonal-use dwellings "
                "that are numerous on this coast."
            ),
            "stats": _numeric_stats(export["dom_10km"]),
        },
    ]

    population_band_layers = []
    for band in ("1km", "2km", "5km", "10km"):
        field = f"pop_{band}"
        population_band_layers.append(
            {
                "key": field,
                "label": f"Resident population within {band.replace('km', ' km')} of the coastline",
                "short_label": f"Population ≤{band}",
                "unit": "inhabitants",
                "stage": "raw",
                "group": "Cumulative population bands",
                "actual_field": field,
                "decimals": 0,
                "boundaries": _count_boundaries(export[field]),
                "colors": component_colors(len(_count_boundaries(export[field])) - 1),
                "palette": "component",
                "palette_source": "magma ramp shared with the hazard components",
                "description": (
                    f"Literal resident count in the cumulative ≤{band} band. "
                    "The bands overlap by construction and are combined with "
                    "weights 0.4/0.3/0.2/0.1 to obtain pop_eff."
                ),
                "stats": _numeric_stats(export[field]),
            }
        )
    layers.extend(population_band_layers)
    layers = [
        layer for layer in layers if layer["key"] not in {"E_log10", "E_rank"}
    ]

    upstream: dict[str, Any] = {}
    if EXPOSURE_METADATA.exists():
        with open(EXPOSURE_METADATA, encoding="utf-8") as handle:
            upstream = json.load(handle)

    metadata = {
        "generated_by": "src.site.export_exposure_data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "municipal_population_exposure",
        "source_path": str(EXPOSURE_CSV.relative_to(ROOT)),
        "geometry_source": str(RISK_GEOJSON.relative_to(ROOT)),
        "source_crs": OUTPUT_CRS,
        "output_crs": OUTPUT_CRS,
        "feature_count": int(len(export)),
        "source_feature_count": int(len(export)),
        "map_extent": list(COASTAL_MAP_EXTENT),
        "basemap": "site/public/data/coastal_basemap.geojson",
        "exposure_field": EXPOSURE_FIELD,
        "effective_population": {
            "formula": "0.4*pop_1km + 0.3*pop_2km + 0.2*pop_5km + 0.1*pop_10km",
            "cumulative_band_weights": EFFECTIVE_POPULATION_WEIGHTS,
            "equivalent_ring_weights": {"0-1km": 1.0, "1-2km": 0.6, "2-5km": 0.3, "5-10km": 0.1},
            "interpretation": "effective/weighted population, not a literal count of inhabitants",
        },
        "distance_bands_km": upstream.get("distance_bands_km"),
        "attribution": upstream.get("attribution"),
        "interpretation": upstream.get("interpretation"),
        "grid_provenance": upstream.get("grid_provenance"),
        "available_layers": layers,
        "audit_fields": {
            "note": (
                "Present in the GeoJSON properties but not offered as a map layer."
            ),
            "fields": ["E_linear", "E_log10", "E_rank"],
        },
        "totals": {
            field: int(pd.to_numeric(export[field]).sum()) for field in count_fields
        },
        "numeric_stats": {
            field: _numeric_stats(export[field])
            for field in (*count_fields, *share_fields, *derived, "pop_eff", "share_pop_eff")
        },
        "decision_pending": (
            "The adopted criterion uses pop_eff from all four cumulative bands. "
            "Alternative log/rank/linear layers remain comparison diagnostics only."
        ),
        "caveat": (
            "Proximity, not modelled inundation: no water level is propagated over "
            "land anywhere in this workflow. Resident (de jure) population on "
            "2022-07-31; the seasonal population of the resort municipalities is "
            "not represented."
        ),
    }
    return export, metadata


def main() -> None:
    export, metadata = build_exposure_layer()
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    export.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")

    print(f"Saved: {OUTPUT_GEOJSON} ({OUTPUT_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Saved: {OUTPUT_METADATA} ({OUTPUT_METADATA.stat().st_size / 1024:.1f} KB)")
    print("Layers:")
    for layer in metadata["available_layers"]:
        print(f"  {layer['key']:10s} <- {layer['actual_field']} ({layer['stats']['count']} values)")


if __name__ == "__main__":
    main()
