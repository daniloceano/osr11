"""Canonical projection of native-grid values onto the Brazilian coastline.

The Hazard Index and its components are calculated on the 808-point native
ocean grid (see :mod:`src.risk_integration.hazard_index`). This module is the
single implementation that *displays* those grid values along the coast: it
clips the Natural Earth 10-m coastline to the coastal-municipality band, splits
the linework into short segments in a metric projection, and assigns to each
segment the values of its nearest native ocean point.

The operation is purely cartographic — no index is recalculated or
renormalized here. The same function backs the article figure
``outputs/article_figures/coastal_hazard_index_components.png``, the
exploratory comparison, and the website coastal-hazard layer, so all three
share one geospatial definition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import GeometryCollection, LineString, MultiLineString

from src.risk_integration.hazard_index import numeric_stats


ROOT = Path(__file__).resolve().parents[2]
MUNICIPALITY_SOURCE = (
    ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
)
COASTLINE_SOURCE = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"

OUTPUT_CRS = "EPSG:4326"
COASTAL_PROJECTION_CRS = "EPSG:5880"
COASTLINE_CLIP_EXTENT = (-56.0, -27.0, -36.5, 7.0)
COASTAL_MAP_EXTENT = (-56.0, -32.0, -35.5, 6.5)
COASTLINE_MUNICIPAL_BUFFER_M = 30_000.0
COASTLINE_SEGMENT_MAX_LENGTH_M = 5_000.0


def read_coastal_inputs(
    municipality_source: Path = MUNICIPALITY_SOURCE,
    coastline_source: Path = COASTLINE_SOURCE,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Load the coastal-municipality polygons and the Natural Earth coastline."""
    for path in (municipality_source, coastline_source):
        if not path.exists():
            raise FileNotFoundError(path)

    layers: list[gpd.GeoDataFrame] = []
    for path in (municipality_source, coastline_source):
        layer = gpd.read_file(path)
        if layer.crs is None:
            layer = layer.set_crs(OUTPUT_CRS)
        elif str(layer.crs).upper() != OUTPUT_CRS:
            layer = layer.to_crs(OUTPUT_CRS)
        layers.append(layer)
    municipalities, coastline = layers
    if municipalities.empty:
        raise ValueError(f"{municipality_source} contains no features")
    if coastline.empty:
        raise ValueError(f"{coastline_source} contains no features")
    return municipalities, coastline


def line_parts(geometry: object) -> list[LineString]:
    """Flatten any line-like geometry into a list of simple LineStrings."""
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, (MultiLineString, GeometryCollection)):
        parts: list[LineString] = []
        for part in geometry.geoms:
            parts.extend(line_parts(part))
        return parts
    return []


def _clip_coastline(
    municipalities: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame,
) -> list[LineString]:
    municipalities_projected = municipalities.to_crs(COASTAL_PROJECTION_CRS)
    coastline_subset = coastline.cx[
        COASTLINE_CLIP_EXTENT[0]:COASTLINE_CLIP_EXTENT[1],
        COASTLINE_CLIP_EXTENT[2]:COASTLINE_CLIP_EXTENT[3],
    ]
    coastline_projected = coastline_subset.to_crs(COASTAL_PROJECTION_CRS)
    municipal_buffer = municipalities_projected.geometry.union_all().buffer(
        COASTLINE_MUNICIPAL_BUFFER_M
    )
    clipped: list[LineString] = []
    for geometry in coastline_projected.geometry:
        clipped.extend(line_parts(geometry.intersection(municipal_buffer)))
    if not clipped:
        raise RuntimeError(
            "No Natural Earth coastline intersects the coastal municipalities"
        )
    return clipped


def _split_lines(
    clipped_lines: Sequence[LineString],
) -> tuple[list[LineString], np.ndarray, np.ndarray, np.ndarray]:
    geometries: list[LineString] = []
    midpoints: list[np.ndarray] = []
    line_ids: list[int] = []
    orders: list[int] = []
    for line_id, line in enumerate(clipped_lines):
        coordinates = np.asarray(line.coords, dtype=float)
        order = 0
        for start, end in zip(coordinates[:-1], coordinates[1:]):
            length = float(np.linalg.norm(end - start))
            number_of_segments = max(
                1,
                int(np.ceil(length / COASTLINE_SEGMENT_MAX_LENGTH_M)),
            )
            points = start + (end - start) * np.linspace(
                0.0,
                1.0,
                number_of_segments + 1,
            )[:, None]
            for segment_start, segment_end in zip(points[:-1], points[1:]):
                geometries.append(LineString([segment_start, segment_end]))
                midpoints.append((segment_start + segment_end) / 2.0)
                line_ids.append(line_id)
                orders.append(order)
                order += 1
    return (
        geometries,
        np.asarray(midpoints, dtype=float),
        np.asarray(line_ids, dtype=int),
        np.asarray(orders, dtype=int),
    )


def project_values_to_coastline(
    native_grid: pd.DataFrame,
    value_fields: Iterable[str],
    *,
    municipalities: gpd.GeoDataFrame | None = None,
    coastline: gpd.GeoDataFrame | None = None,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Assign native ocean-grid values to short Natural Earth coast segments.

    Parameters
    ----------
    native_grid:
        Table with ``grid_lat``/``grid_lon`` and the fields to transfer. It is
        consumed as-is: no value is recalculated, rescaled, or renormalized.
    value_fields:
        Names of the columns carried onto each coastal segment.
    municipalities, coastline:
        Optional preloaded layers; :func:`read_coastal_inputs` is used when
        omitted.

    Returns
    -------
    (segments, metadata)
        ``segments`` is an EPSG:4326 GeoDataFrame of coastal LineStrings with
        the transferred values plus the provenance of the source grid point.
    """
    fields = list(dict.fromkeys(value_fields))
    required = ["grid_lon", "grid_lat", *fields]
    missing = sorted(set(required).difference(native_grid.columns))
    if missing:
        raise ValueError(
            "The native grid lacks required field(s): " + ", ".join(missing)
        )

    source_points = (
        native_grid[required].dropna().reset_index(drop=True)
    )
    if source_points.empty:
        raise RuntimeError("No native ocean grid points are available")

    if municipalities is None or coastline is None:
        loaded_municipalities, loaded_coastline = read_coastal_inputs()
        municipalities = (
            loaded_municipalities if municipalities is None else municipalities
        )
        coastline = loaded_coastline if coastline is None else coastline

    clipped_lines = _clip_coastline(municipalities, coastline)
    geometries, midpoints, line_ids, orders = _split_lines(clipped_lines)

    ocean_points = gpd.GeoDataFrame(
        source_points,
        geometry=gpd.points_from_xy(
            source_points["grid_lon"],
            source_points["grid_lat"],
        ),
        crs=OUTPUT_CRS,
    ).to_crs(COASTAL_PROJECTION_CRS)
    point_coordinates = np.asarray(
        [(point.x, point.y) for point in ocean_points.geometry],
        dtype=float,
    )
    nearest_distance_m, nearest_position = cKDTree(point_coordinates).query(
        midpoints,
        k=1,
    )
    source_rows = source_points.iloc[nearest_position].reset_index(drop=True)

    attributes: dict[str, Any] = {
        "coastline_id": line_ids,
        "segment_order": orders,
        "source_grid_index": nearest_position.astype(int),
        "source_longitude": source_rows["grid_lon"].to_numpy(dtype=float),
        "source_latitude": source_rows["grid_lat"].to_numpy(dtype=float),
        "nearest_grid_distance_km": nearest_distance_m / 1_000.0,
    }
    for field in fields:
        attributes[field] = source_rows[field].to_numpy(dtype=float)
    segments = gpd.GeoDataFrame(
        attributes,
        geometry=geometries,
        crs=COASTAL_PROJECTION_CRS,
    ).to_crs(OUTPUT_CRS)

    metadata = {
        "implementation": "src/04_risk_integration/coastal_projection.py",
        "method": (
            "Natural Earth 10m coastline clipped to a 30-km buffer around "
            "the coastal-municipality union; linework split into segments no "
            "longer than 5 km in EPSG:5880; each segment assigned the values "
            "at its nearest native ocean grid point by projected midpoint "
            "distance"
        ),
        "recalculates_index": False,
        "coastline_source": _relative(COASTLINE_SOURCE),
        "municipality_source": _relative(MUNICIPALITY_SOURCE),
        "projected_crs": COASTAL_PROJECTION_CRS,
        "output_crs": OUTPUT_CRS,
        "municipal_buffer_m": COASTLINE_MUNICIPAL_BUFFER_M,
        "maximum_segment_length_m": COASTLINE_SEGMENT_MAX_LENGTH_M,
        "clipped_line_count": len(clipped_lines),
        "segment_count": int(len(segments)),
        "native_grid_point_count": int(len(source_points)),
        "native_grid_points_used": int(len(np.unique(nearest_position))),
        "transferred_fields": fields,
        "nearest_distance_km": {
            "minimum": round(float(np.min(nearest_distance_m) / 1_000.0), 6),
            "median": round(float(np.median(nearest_distance_m) / 1_000.0), 6),
            "mean": round(float(np.mean(nearest_distance_m) / 1_000.0), 6),
            "p90": round(
                float(np.quantile(nearest_distance_m, 0.90) / 1_000.0),
                6,
            ),
            "p99": round(
                float(np.quantile(nearest_distance_m, 0.99) / 1_000.0),
                6,
            ),
            "maximum": round(float(np.max(nearest_distance_m) / 1_000.0), 6),
        },
        "assigned_value_statistics": {
            field: numeric_stats(segments[field]) for field in fields
        },
    }
    return segments, metadata


def attach_nearest_municipality(
    segments: gpd.GeoDataFrame,
    municipalities: gpd.GeoDataFrame | None = None,
    *,
    name_field: str = "municipality_name",
    state_field: str = "state",
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Label each coastal segment with its nearest coastal municipality.

    The label identifies the municipality that the segment would feed in the
    risk integration. It is attached for interpretation only and takes no part
    in the Hazard Index calculation.
    """
    if municipalities is None:
        municipalities, _ = read_coastal_inputs()
    missing = [
        field
        for field in (name_field, state_field)
        if field not in municipalities.columns
    ]
    if missing:
        raise ValueError(
            "The municipality layer lacks required field(s): "
            + ", ".join(missing)
        )

    segments_projected = segments.to_crs(COASTAL_PROJECTION_CRS)
    municipalities_projected = municipalities.to_crs(COASTAL_PROJECTION_CRS)
    joined = gpd.sjoin_nearest(
        gpd.GeoDataFrame(
            geometry=segments_projected.geometry.centroid,
            crs=COASTAL_PROJECTION_CRS,
        ),
        municipalities_projected[[name_field, state_field, "geometry"]],
        how="left",
        distance_col="_municipality_distance_m",
    )
    # sjoin_nearest can return ties; keep the first match per segment.
    joined = joined[~joined.index.duplicated(keep="first")].reindex(
        segments_projected.index
    )

    labelled = segments.copy()
    labelled["municipality_name"] = joined[name_field].to_numpy()
    labelled["municipality_state"] = joined[state_field].to_numpy()
    distances_km = (
        joined["_municipality_distance_m"].to_numpy(dtype=float) / 1_000.0
    )
    labelled["municipality_distance_km"] = distances_km

    finite = distances_km[np.isfinite(distances_km)]
    metadata = {
        "method": (
            "Nearest coastal municipality polygon to the segment centroid, "
            "measured in EPSG:5880"
        ),
        "purpose": (
            "interpretation and hand-off to the municipal risk integration; "
            "it does not take part in the Hazard Index calculation"
        ),
        "municipality_source": _relative(MUNICIPALITY_SOURCE),
        "labelled_segment_count": int(np.isfinite(distances_km).sum()),
        "distinct_municipalities": int(
            labelled["municipality_name"].nunique(dropna=True)
        ),
        "distance_km": {
            "minimum": round(float(finite.min()), 6) if finite.size else None,
            "median": round(float(np.median(finite)), 6) if finite.size else None,
            "maximum": round(float(finite.max()), 6) if finite.size else None,
        },
    }
    return labelled, metadata


def dissolve_by_source(
    segments: gpd.GeoDataFrame,
    extra_group_fields: Sequence[str] = (),
) -> gpd.GeoDataFrame:
    """Merge consecutive coastal segments that share one source grid point.

    Values and geometry are preserved exactly; only the number of features is
    reduced, which keeps the browser payload small without changing what is
    drawn. Requires the ``coastline_id``/``segment_order`` bookkeeping produced
    by :func:`project_values_to_coastline`. ``extra_group_fields`` adds further
    columns to the run key, so a run never spans two different values of them
    (used to keep municipality labels exact).
    """
    required = {"coastline_id", "segment_order", "source_grid_index"}
    missing = sorted(required.difference(segments.columns))
    if missing:
        raise ValueError(
            "Cannot dissolve coastal segments; missing field(s): "
            + ", ".join(missing)
        )

    group_fields = ["coastline_id", "source_grid_index", *extra_group_fields]
    ordered = segments.sort_values(
        ["coastline_id", "segment_order"]
    ).reset_index(drop=True)
    keys = ordered[group_fields].astype(str).to_numpy()
    breaks = np.ones(len(ordered), dtype=bool)
    if len(ordered) > 1:
        breaks[1:] = np.any(keys[1:] != keys[:-1], axis=1)
    run_ids = np.cumsum(breaks) - 1

    records: list[dict[str, Any]] = []
    geometries: list[LineString] = []
    attribute_columns = [
        column
        for column in ordered.columns
        if column not in {"geometry", "segment_order"}
    ]
    for run_id in range(int(run_ids.max()) + 1):
        member_positions = np.flatnonzero(run_ids == run_id)
        coordinates: list[tuple[float, float]] = []
        for position in member_positions:
            geometry = ordered.geometry.iloc[position]
            points = list(geometry.coords)
            if coordinates and coordinates[-1] == points[0]:
                coordinates.extend(points[1:])
            else:
                coordinates.extend(points)
        first = ordered.iloc[member_positions[0]]
        record = {column: first[column] for column in attribute_columns}
        record["segment_count"] = int(len(member_positions))
        record["nearest_grid_distance_km"] = float(
            ordered["nearest_grid_distance_km"]
            .iloc[member_positions]
            .mean()
        )
        records.append(record)
        geometries.append(LineString(coordinates))

    return gpd.GeoDataFrame(
        pd.DataFrame(records),
        geometry=geometries,
        crs=segments.crs,
    )


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
