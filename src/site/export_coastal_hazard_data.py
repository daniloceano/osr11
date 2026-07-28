"""Export the coastal Hazard Index layers consumed by the results website.

The Hazard Index and its three components are calculated once on the 808-point
native ocean grid by ``src/04_risk_integration/hazard_index.py``. They are then
projected onto the Natural Earth 10-m coastline by
``src/04_risk_integration/coastal_projection.py`` — the same module that backs
``outputs/article_figures/coastal_hazard_index_components.png`` — so the website
map, the article figure, and the municipal risk layer all originate from a
single implementation. Nothing is renormalized here.

Outputs:

    site/public/data/coastal_hazard_segments.geojson
    site/public/data/coastal_hazard_metadata.json
    site/public/data/coastal_basemap.geojson

Usage:
    python -m src.site.export_coastal_hazard_data
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
from shapely.geometry import box, mapping

from src.risk_integration.coastal_projection import (
    COASTAL_MAP_EXTENT,
    attach_nearest_municipality,
    dissolve_by_source,
    project_values_to_coastline,
    read_coastal_inputs,
)
from src.risk_integration.hazard_index import (
    NATIVE_GRID_SOURCE,
    derive_native_hazard_index,
    numeric_stats,
)
from src.risk_integration.palettes import (
    component_colors,
    palette_catalog,
    risk_colors,
)


ROOT = Path(__file__).resolve().parents[2]
SITE_DATA_DIR = ROOT / "site" / "public" / "data"
METRICS_SOURCE = SITE_DATA_DIR / "hazard_characterization_grid_metrics.json"
OUTPUT_GEOJSON = SITE_DATA_DIR / "coastal_hazard_segments.geojson"
OUTPUT_METADATA = SITE_DATA_DIR / "coastal_hazard_metadata.json"
OUTPUT_BASEMAP = SITE_DATA_DIR / "coastal_basemap.geojson"

COORDINATE_DECIMALS = 4
VALUE_DECIMALS = 4

# Land, country, and state context drawn behind the coastal hazard layer. The
# window is slightly wider than the displayed extent so no edge is clipped.
BASEMAP_EXTENT = (-60.0, -30.0, -37.0, 8.0)
BASEMAP_SIMPLIFY_DEGREES = 0.01

LAYER_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "compound_count_annual_mean",
        "label": "Compound-event frequency",
        "short_label": "Frequency",
        "unit": "events yr⁻¹",
        "unit_plain": "events per year",
        "value_kind": "catalog",
        "decimals": 1,
        "boundaries": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        "palette": "component",
        "description": (
            "Mean annual number of compound wave/sea-level events at the "
            "nearest native ocean grid point, straight from the Step 3.2 "
            "catalog."
        ),
    },
    {
        "key": "mean_overlap_duration",
        "label": "Mean overlap duration",
        "short_label": "Duration",
        "unit": "days",
        "unit_plain": "days",
        "value_kind": "catalog",
        "decimals": 2,
        "boundaries": [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6],
        "palette": "component",
        "description": (
            "Mean number of calendar days during which the wave and the "
            "sea-level episodes of a compound event overlap, straight from "
            "the Step 3.2 catalog."
        ),
    },
    {
        "key": "mean_compound_intensity_norm",
        "label": "Mean compound intensity",
        "short_label": "Intensity",
        "unit": "dimensionless",
        "unit_plain": "dimensionless",
        "value_kind": "catalog",
        "decimals": 3,
        "boundaries": [0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55],
        "palette": "component",
        "description": (
            "Event-level compound intensity stored in the catalog: how far "
            "each driver rose above its own local q90 detection threshold, "
            "rescaled by the domain-wide Q05/Q95 of those excesses and "
            "averaged with equal weights. Subtracting the local baseline "
            "keeps the astronomical tide out of the severity score. It is "
            "already a dimensionless compound intensity, so the map shows it "
            "unchanged — no extra Min-Max scaling is applied for display."
        ),
    },
    {
        "key": "Hazard_Index",
        "label": "Hazard Index",
        "short_label": "Hazard Index",
        "unit": "0–1",
        "unit_plain": "0-1 index",
        "value_kind": "index",
        "decimals": 3,
        "boundaries": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
        "palette": "hazard",
        "description": (
            "Final composite Hazard Index: the three components are Min-Max "
            "normalized over the 808 native grid points, averaged with equal "
            "weights of 1/3, and the mean is Min-Max normalized again to "
            "span 0-1."
        ),
    },
)

DETAIL_FIELDS = (
    "Hazard_Frequency",
    "Hazard_Duration",
    "Hazard_Intensity",
    "Hazard_Index_raw",
)


def _round_geometry(geojson: dict[str, Any]) -> dict[str, Any]:
    """Round coordinates and property values to keep the payload small."""

    def round_coordinates(coordinates: Any) -> Any:
        if isinstance(coordinates, (list, tuple)):
            if coordinates and isinstance(coordinates[0], (int, float)):
                return [round(float(value), COORDINATE_DECIMALS) for value in coordinates]
            return [round_coordinates(item) for item in coordinates]
        return coordinates

    for feature in geojson["features"]:
        feature["geometry"]["coordinates"] = round_coordinates(
            feature["geometry"]["coordinates"]
        )
        properties = feature["properties"]
        for key, value in list(properties.items()):
            if isinstance(value, float):
                if not math.isfinite(value):
                    properties[key] = None
                else:
                    properties[key] = round(value, VALUE_DECIMALS)
    return geojson


def _attach_metric_index(
    segments: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Link each segment to its grid point in the Step 3 metric catalog.

    The 87 characterization metrics stay in their own file; the coastal layer
    only carries the array position of the source grid point, so the per-metric
    explorer can be drawn on the same coastline without duplicating the
    catalog.
    """
    if not METRICS_SOURCE.exists():
        raise FileNotFoundError(
            "The coastal metric explorer requires the Step 3.8 export: "
            f"{METRICS_SOURCE}"
        )
    catalog = json.loads(METRICS_SOURCE.read_text(encoding="utf-8"))
    lookup = {
        (round(float(point["lat"]), 4), round(float(point["lon"]), 4)): index
        for index, point in enumerate(catalog["grid_points"])
    }
    positions = [
        lookup.get(
            (
                round(float(latitude), 4),
                round(float(longitude), 4),
            )
        )
        for latitude, longitude in zip(
            segments["source_latitude"],
            segments["source_longitude"],
        )
    ]
    unmatched = sum(1 for position in positions if position is None)
    if unmatched:
        raise ValueError(
            f"{unmatched} coastal segments could not be matched to a grid "
            f"point in {METRICS_SOURCE.name}"
        )

    linked = segments.copy()
    linked["metrics_index"] = [int(position) for position in positions]
    metadata = {
        "metrics_file": str(METRICS_SOURCE.relative_to(ROOT)),
        "field": "metrics_index",
        "method": (
            "Array position of the source native grid point inside "
            "grid_points of the Step 3.8 metric catalog, matched on "
            "latitude/longitude rounded to 4 decimals"
        ),
        "purpose": (
            "lets the per-grid-point explorer draw any of the Step 3 metrics "
            "on the same coastline without duplicating the catalog"
        ),
        "catalog_grid_points": int(len(catalog["grid_points"])),
        "linked_features": int(len(linked)),
        "distinct_grid_points": int(linked["metrics_index"].nunique()),
    }
    return linked, metadata


def build_coastal_basemap() -> dict[str, Any]:
    """Clip Natural Earth land, country, and state context to the map window."""
    from cartopy.io import shapereader

    window = box(
        BASEMAP_EXTENT[0],
        BASEMAP_EXTENT[2],
        BASEMAP_EXTENT[1],
        BASEMAP_EXTENT[3],
    )
    sources = (
        ("land", "physical", "land", None),
        ("country", "cultural", "admin_0_boundary_lines_land", None),
        ("state", "cultural", "admin_1_states_provinces_lines", "Brazil"),
    )
    features: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for layer, category, name, country_filter in sources:
        path = shapereader.natural_earth(
            resolution="10m",
            category=category,
            name=name,
        )
        reader = shapereader.Reader(path)
        geometries = []
        for record in reader.records():
            if (
                country_filter is not None
                and record.attributes.get("ADM0_NAME") != country_filter
            ):
                continue
            geometry = record.geometry
            if geometry is None or geometry.is_empty:
                continue
            if not geometry.intersects(window):
                continue
            clipped = geometry.intersection(window)
            if clipped.is_empty:
                continue
            simplified = clipped.simplify(
                BASEMAP_SIMPLIFY_DEGREES,
                preserve_topology=True,
            )
            if simplified.is_empty:
                continue
            geometries.append(simplified)
        counts[layer] = len(geometries)
        for geometry in geometries:
            features.append(
                {
                    "type": "Feature",
                    "properties": {"layer": layer},
                    "geometry": mapping(geometry),
                }
            )

    basemap = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_by": "src.site.export_coastal_hazard_data",
            "source": "Natural Earth 10 m",
            "layers": {
                "land": "physical/ne_10m_land (light-gray continent)",
                "country": "cultural/ne_10m_admin_0_boundary_lines_land",
                "state": (
                    "cultural/ne_10m_admin_1_states_provinces_lines, "
                    "Brazil only"
                ),
            },
            "extent": list(BASEMAP_EXTENT),
            "simplify_tolerance_degrees": BASEMAP_SIMPLIFY_DEGREES,
            "feature_counts": counts,
        },
        "features": features,
    }
    return _round_geometry(basemap)


def build_coastal_hazard_data() -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Project the native-grid Hazard Index onto the coastline for the site."""
    native_grid, native_metadata = derive_native_hazard_index()
    municipalities, coastline = read_coastal_inputs()

    layer_fields = [spec["key"] for spec in LAYER_SPECS]
    segments, assignment_metadata = project_values_to_coastline(
        native_grid,
        (*layer_fields, *DETAIL_FIELDS),
        municipalities=municipalities,
        coastline=coastline,
    )
    segments, municipality_metadata = attach_nearest_municipality(
        segments,
        municipalities,
    )
    dissolved = dissolve_by_source(segments, ("municipality_name",))
    dissolved = dissolved.drop(columns=["coastline_id"], errors="ignore")
    dissolved, metrics_link_metadata = _attach_metric_index(dissolved)

    metadata: dict[str, Any] = {
        "generated_by": "src.site.export_coastal_hazard_data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": "1993-2025",
        "source_file": str(NATIVE_GRID_SOURCE.relative_to(ROOT)),
        "native_hazard_index": native_metadata,
        "native_grid_point_count": assignment_metadata["native_grid_point_count"],
        "native_grid_points_used": assignment_metadata["native_grid_points_used"],
        "coastal_projection": {
            **assignment_metadata,
            "feature_count": int(len(dissolved)),
            "feature_note": (
                "Consecutive 5-km segments sharing the same nearest native "
                "grid point are merged into one polyline for transport. "
                "Geometry and values are unchanged; only the feature count "
                "is reduced."
            ),
        },
        "nearest_municipality": municipality_metadata,
        "metric_catalog_link": metrics_link_metadata,
        "palettes": palette_catalog(),
        "map_extent": list(COASTAL_MAP_EXTENT),
        "coordinate_decimals": COORDINATE_DECIMALS,
        "value_decimals": VALUE_DECIMALS,
        "layers": [
            {
                "key": spec["key"],
                "label": spec["label"],
                "short_label": spec["short_label"],
                "unit": spec["unit"],
                "unit_plain": spec["unit_plain"],
                "value_kind": spec["value_kind"],
                "decimals": spec["decimals"],
                "boundaries": spec["boundaries"],
                "colors": (
                    component_colors(len(spec["boundaries"]) - 1)
                    if spec["palette"] == "component"
                    else risk_colors(len(spec["boundaries"]) - 1)
                ),
                "palette": spec["palette"],
                "palette_source": (
                    "matplotlib magma sampled from 0.95 to 0.12, as in "
                    "outputs/article_figures/coastal_hazard_index_components.png"
                    if spec["palette"] == "component"
                    else "green-to-red palette shared with the Risk Index"
                ),
                "display_values": (
                    "native-grid catalog values, without the methodological "
                    "Min-Max scaling used to build the index"
                    if spec["value_kind"] == "catalog"
                    else "final Hazard Index after both Min-Max steps"
                ),
                "description": spec["description"],
                "statistics": numeric_stats(dissolved[spec["key"]]),
            }
            for spec in LAYER_SPECS
        ],
        "detail_fields": {
            field: numeric_stats(dissolved[field]) for field in DETAIL_FIELDS
        },
        "normalization_note": (
            "The Min-Max normalization of the three components happens only "
            "inside the index construction on the native grid. The frequency, "
            "duration, and intensity layers of this map show the catalog "
            "values themselves."
        ),
        "outputs": {
            "geojson": str(OUTPUT_GEOJSON.relative_to(ROOT)),
            "metadata": str(OUTPUT_METADATA.relative_to(ROOT)),
            "basemap": str(OUTPUT_BASEMAP.relative_to(ROOT)),
        },
    }
    return dissolved, metadata


def save_coastal_hazard_data(
    segments: gpd.GeoDataFrame,
    metadata: dict[str, Any],
) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    geojson = _round_geometry(json.loads(segments.to_json()))
    geojson.pop("bbox", None)
    for feature in geojson["features"]:
        feature.pop("id", None)
    OUTPUT_GEOJSON.write_text(
        json.dumps(geojson, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    OUTPUT_METADATA.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Saved: {OUTPUT_GEOJSON} "
        f"({OUTPUT_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)"
    )
    print(
        f"Saved: {OUTPUT_METADATA} "
        f"({OUTPUT_METADATA.stat().st_size / 1024:.1f} KB)"
    )


def main() -> None:
    segments, metadata = build_coastal_hazard_data()
    save_coastal_hazard_data(segments, metadata)
    basemap = build_coastal_basemap()
    OUTPUT_BASEMAP.write_text(
        json.dumps(basemap, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Saved: {OUTPUT_BASEMAP} "
        f"({OUTPUT_BASEMAP.stat().st_size / 1024 / 1024:.2f} MB) "
        f"{basemap['metadata']['feature_counts']}"
    )
    print(
        f"Native grid points: {metadata['native_grid_point_count']} "
        f"(used: {metadata['native_grid_points_used']})"
    )
    print(
        f"Coastal segments: {metadata['coastal_projection']['segment_count']} "
        f"-> {metadata['coastal_projection']['feature_count']} polylines"
    )
    for layer in metadata["layers"]:
        stats = layer["statistics"]
        print(
            f"  {layer['key']} ({layer['unit_plain']}): "
            f"min={stats['min']} max={stats['max']}"
        )
    distances = metadata["coastal_projection"]["nearest_distance_km"]
    print(
        "Nearest native point distance (km): "
        f"median={distances['median']} p99={distances['p99']} "
        f"max={distances['maximum']}"
    )
    assert np.isfinite(
        [layer["statistics"]["max"] for layer in metadata["layers"]]
    ).all()


if __name__ == "__main__":
    main()
