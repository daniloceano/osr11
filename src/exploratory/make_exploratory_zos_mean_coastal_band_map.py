"""Generate one exploratory map of temporal-mean GLORYS ``zos`` near the coast.

Only raw dynamic sea level (``zos``) is analyzed; tides and ``SSH_total`` are
explicitly excluded. The plotted field is restricted to valid ocean cells no
more than 200 km from the Natural Earth 10m coastline. Main rivers from Natural
Earth are drawn over gray land, with the rios Apodi and Paraguaçu supplied by
the Brazilian National Water and Sanitation Agency (ANA).

Run from the repository root:

    python src/exploratory/make_exploratory_zos_mean_coastal_band_map.py
"""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
# Optional river-label and legend imports; uncomment with the blocks in the
# plotting function to restore those annotations.
# from matplotlib.lines import Line2D
# import matplotlib.patheffects as path_effects
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import shape
import xarray as xr

from src.exploratory.longterm_mean_zos_map import coord_name, sort_lat_lon
from src.figures_article.make_article_calibration_heatmaps import (
    QUALITY_COLORS_WORSE_TO_BETTER,
)

DEFAULT_INPUT = ROOT / "data/unified/metocean_brazil_unified_waverys_grid.nc"
DEFAULT_APODI_RIVER = ROOT / "data/external/ana_bho/rio_apodi.geojson"
DEFAULT_PARAGUACU_RIVER = ROOT / "data/external/ana_bho/rio_paraguacu.geojson"
DEFAULT_OUTPUT_DIR = ROOT / "outputs/exploratory_zos_mean_coastal_band_map"
DEFAULT_ARTICLE_OUTPUT_DIR = ROOT / "outputs/article_figures"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"
COASTAL_DISTANCE_KM = 200.0
COAST_DENSIFY_STEP_DEG = 0.02
COAST_SEARCH_BUFFER_DEG = 5.0
EARTH_RADIUS_KM = 6371.0088
COLORBAR_MAX_M = 0.3
COLORBAR_BINS = 6
MAXIMUM_RIVER_SCALERANK = 6
FORCED_NATURAL_EARTH_RIVERS = {"Mearim"}
RIVER_LABELS = {
    "Amazonas": (-52.15, -2.65),
    "Mearim": (-45.15, -3.85),
    "Apodi–Mossoró": (-38.05, -5.85),
    "Paraguaçu": (-40.15, -12.95),
}


def parse_args(*, article_supplement: bool = False) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Map temporal-mean raw GLORYS zos over ocean cells within a "
            "specified distance from the coastline."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument(
        "--coastal-distance-km",
        type=float,
        default=COASTAL_DISTANCE_KM,
    )
    parser.add_argument("--apodi-river", type=Path, default=DEFAULT_APODI_RIVER)
    parser.add_argument(
        "--paraguacu-river",
        type=Path,
        default=DEFAULT_PARAGUACU_RIVER,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            DEFAULT_ARTICLE_OUTPUT_DIR
            if article_supplement
            else DEFAULT_OUTPUT_DIR
        ),
    )
    parser.add_argument("--coastline", type=Path, default=DEFAULT_COASTLINE)
    parser.add_argument("--dpi", type=int, default=300 if article_supplement else 150)
    return parser.parse_args()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def field_boundaries(field: xr.DataArray) -> np.ndarray:
    finite = field.values[np.isfinite(field.values)]
    if finite.size == 0:
        raise ValueError(f"{field.name!r} contains no finite coastal cells")
    return np.linspace(0.0, COLORBAR_MAX_M, COLORBAR_BINS + 1)


def palette_for_bins(
    number_of_bins: int,
    *,
    reserve_over_color: bool = False,
) -> tuple[str, ...]:
    last_index = len(QUALITY_COLORS_WORSE_TO_BETTER) - (
        2 if reserve_over_color else 1
    )
    indices = np.rint(
        np.linspace(0, last_index, number_of_bins)
    ).astype(int)
    return tuple(QUALITY_COLORS_WORSE_TO_BETTER[index] for index in indices)


def densify_line_coordinates(
    coordinates: np.ndarray,
    maximum_step_degrees: float,
) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for start, end in zip(coordinates[:-1], coordinates[1:]):
        steps = max(
            1,
            int(np.ceil(np.max(np.abs(end - start)) / maximum_step_degrees)),
        )
        fractions = np.arange(steps, dtype=float)[:, None] / steps
        pieces.append(start + fractions * (end - start))
    pieces.append(coordinates[-1:])
    return np.vstack(pieces)


def lon_lat_to_unit_sphere(
    longitude: np.ndarray,
    latitude: np.ndarray,
) -> np.ndarray:
    longitude_radians = np.deg2rad(longitude)
    latitude_radians = np.deg2rad(latitude)
    cos_latitude = np.cos(latitude_radians)
    return np.column_stack(
        (
            cos_latitude * np.cos(longitude_radians),
            cos_latitude * np.sin(longitude_radians),
            np.sin(latitude_radians),
        )
    )


def distance_to_coast(
    field: xr.DataArray,
    coastline: Path,
) -> xr.DataArray:
    latitude_name = coord_name(field, ("latitude", "lat", "y"))
    longitude_name = coord_name(field, ("longitude", "lon", "x"))
    latitude = field[latitude_name].values
    longitude = field[longitude_name].values
    west = float(np.nanmin(longitude)) - COAST_SEARCH_BUFFER_DEG
    east = float(np.nanmax(longitude)) + COAST_SEARCH_BUFFER_DEG
    south = float(np.nanmin(latitude)) - COAST_SEARCH_BUFFER_DEG
    north = float(np.nanmax(latitude)) + COAST_SEARCH_BUFFER_DEG

    coastline_samples: list[np.ndarray] = []
    for geometry in shapereader.Reader(str(coastline)).geometries():
        minx, miny, maxx, maxy = geometry.bounds
        if maxx < west or minx > east or maxy < south or miny > north:
            continue
        coordinates = np.asarray(geometry.coords, dtype=float)[:, :2]
        samples = densify_line_coordinates(
            coordinates,
            COAST_DENSIFY_STEP_DEG,
        )
        inside_search_area = (
            (samples[:, 0] >= west)
            & (samples[:, 0] <= east)
            & (samples[:, 1] >= south)
            & (samples[:, 1] <= north)
        )
        coastline_samples.append(samples[inside_search_area])

    if not coastline_samples:
        raise ValueError("No coastline vertices intersect the zos domain")
    sampled_coastline = np.vstack(coastline_samples)
    sampled_coastline = sampled_coastline[
        np.all(np.isfinite(sampled_coastline), axis=1)
    ]
    if sampled_coastline.size == 0:
        raise ValueError("No finite coastline vertices available for distance calculation")

    coastline_tree = cKDTree(
        lon_lat_to_unit_sphere(
            sampled_coastline[:, 0],
            sampled_coastline[:, 1],
        )
    )
    grid_longitude, grid_latitude = np.meshgrid(longitude, latitude)
    chord_distance, _ = coastline_tree.query(
        lon_lat_to_unit_sphere(grid_longitude.ravel(), grid_latitude.ravel()),
        k=1,
    )
    central_angle = 2.0 * np.arcsin(np.clip(chord_distance / 2.0, 0.0, 1.0))
    distance_km = (EARTH_RADIUS_KM * central_angle).reshape(grid_latitude.shape)
    result = xr.DataArray(
        distance_km.astype("float32"),
        coords={
            latitude_name: field[latitude_name],
            longitude_name: field[longitude_name],
        },
        dims=(latitude_name, longitude_name),
        name="distance_to_coast_km",
    )
    result.attrs.update(
        {
            "long_name": "Approximate great-circle distance to coastline",
            "units": "km",
            "coastline_source": relative(coastline),
            "method": (
                "nearest Natural Earth 10m coastline point after densifying "
                f"segments to <= {COAST_DENSIFY_STEP_DEG} degree spacing; "
                "nearest neighbor evaluated on a unit sphere"
            ),
            "earth_radius_km": EARTH_RADIUS_KM,
            "coastline_sample_count": int(sampled_coastline.shape[0]),
        }
    )
    return result


def natural_earth_layers() -> tuple[Path, Path, Path, Path]:
    land = Path(
        shapereader.natural_earth(
            resolution="10m",
            category="physical",
            name="land",
        )
    )
    rivers = Path(
        shapereader.natural_earth(
            resolution="10m",
            category="physical",
            name="rivers_lake_centerlines",
        )
    )
    country_boundaries = Path(
        shapereader.natural_earth(
            resolution="10m",
            category="cultural",
            name="admin_0_boundary_lines_land",
        )
    )
    state_boundaries = Path(
        shapereader.natural_earth(
            resolution="10m",
            category="cultural",
            name="admin_1_states_provinces_lines",
        )
    )
    return land, rivers, country_boundaries, state_boundaries


def main_river_geometries(
    rivers_path: Path,
    extent: list[float],
) -> tuple[list[object], list[str]]:
    west, east, south, north = extent
    geometries: list[object] = []
    names: set[str] = set()
    for record in shapereader.Reader(str(rivers_path)).records():
        attributes = record.attributes
        scalerank = attributes.get("scalerank")
        feature_class = str(attributes.get("featurecla", ""))
        name = str(attributes.get("name", "")).strip()
        is_forced = name in FORCED_NATURAL_EARTH_RIVERS
        if (
            scalerank is None
            or (
                int(scalerank) > MAXIMUM_RIVER_SCALERANK
                and not is_forced
            )
        ):
            continue
        if feature_class not in {"River", "Lake Centerline"}:
            continue
        minx, miny, maxx, maxy = record.geometry.bounds
        if maxx < west or minx > east or maxy < south or miny > north:
            continue
        geometries.append(record.geometry)
        if name:
            names.add(name)
    return geometries, sorted(names)


def selected_river_geometries(
    river_path: Path,
    extent: list[float],
) -> tuple[list[object], list[str]]:
    west, east, south, north = extent
    document = json.loads(river_path.read_text(encoding="utf-8"))
    geometries: list[object] = []
    names: set[str] = set()
    for feature in document.get("features", []):
        geometry_mapping = feature.get("geometry")
        if not geometry_mapping:
            continue
        geometry = shape(geometry_mapping)
        minx, miny, maxx, maxy = geometry.bounds
        if maxx < west or minx > east or maxy < south or miny > north:
            continue
        geometries.append(geometry)
        name = str(feature.get("properties", {}).get("NORIOCOMP", "")).strip()
        if name:
            names.add(name)
    return geometries, sorted(names)


def plot_mean_coastal_band_map(
    coastal_mean: xr.DataArray,
    ocean_distance_to_coast: xr.DataArray,
    *,
    coastal_distance_km: float,
    boundaries: np.ndarray,
    coastline: Path,
    apodi_river: Path,
    paraguacu_river: Path,
    period: str,
    output: Path,
    dpi: int,
    show_title: bool = True,
    show_administrative_boundaries: bool = False,
    grid_label_size: float = 8,
    colorbar_label_size: float = 10,
    colorbar_tick_size: float = 8,
) -> list[str]:
    lat_name = coord_name(coastal_mean, ("latitude", "lat", "y"))
    lon_name = coord_name(coastal_mean, ("longitude", "lon", "x"))
    latitude = coastal_mean[lat_name].values
    longitude = coastal_mean[lon_name].values
    crs = ccrs.PlateCarree()

    colors = palette_for_bins(
        len(boundaries) - 1,
        reserve_over_color=True,
    )
    cmap = ListedColormap(colors, name="article_calibration_quality_palette")
    cmap.set_over(QUALITY_COLORS_WORSE_TO_BETTER[-1])
    norm = BoundaryNorm(boundaries, cmap.N, clip=False)

    lon_span = float(np.nanmax(longitude) - np.nanmin(longitude))
    lat_span = float(np.nanmax(latitude) - np.nanmin(latitude))
    extent = [
        float(np.nanmin(longitude)) - max(0.2, 0.02 * lon_span),
        float(-34.0) + max(0.2, 0.02 * lon_span),
        float(np.nanmin(latitude)) - max(0.2, 0.02 * lat_span),
        float(np.nanmax(latitude)) + max(0.2, 0.02 * lat_span),
    ]
    (
        land_path,
        rivers_path,
        country_boundaries_path,
        state_boundaries_path,
    ) = natural_earth_layers()
    land_geometries = list(shapereader.Reader(str(land_path)).geometries())
    country_boundary_geometries = list(
        shapereader.Reader(str(country_boundaries_path)).geometries()
    )
    state_boundary_geometries = list(
        shapereader.Reader(str(state_boundaries_path)).geometries()
    )
    river_geometries, river_names = main_river_geometries(rivers_path, extent)
    apodi_geometries, apodi_names = selected_river_geometries(
        apodi_river,
        extent,
    )
    paraguacu_geometries, paraguacu_names = selected_river_geometries(
        paraguacu_river,
        extent,
    )
    coastline_geometries = list(shapereader.Reader(str(coastline)).geometries())

    fig = plt.figure(figsize=(7.4, 9.4))
    axis = plt.axes(projection=crs)
    axis.set_facecolor("#e8f1f5")
    mesh = axis.pcolormesh(
        longitude,
        latitude,
        coastal_mean.values,
        transform=crs,
        shading="auto",
        cmap=cmap,
        norm=norm,
        zorder=1,
    )
    axis.add_geometries(
        land_geometries,
        crs=crs,
        facecolor="0.86",
        edgecolor="none",
        zorder=2,
    )
    if show_administrative_boundaries:
        axis.add_geometries(
            state_boundary_geometries,
            crs=crs,
            facecolor="none",
            edgecolor="0.58",
            linewidth=0.30,
            alpha=0.9,
            zorder=2.2,
        )
        axis.add_geometries(
            country_boundary_geometries,
            crs=crs,
            facecolor="none",
            edgecolor="0.32",
            linewidth=0.8,
            alpha=0.95,
            zorder=2.3,
        )
    axis.add_geometries(
        river_geometries,
        crs=crs,
        facecolor="none",
        edgecolor="#2f78a3",
        linewidth=1,
        alpha=0.9,
        zorder=3,
    )
    axis.add_geometries(
        apodi_geometries + paraguacu_geometries,
        crs=crs,
        facecolor="none",
        edgecolor="#2f78a3",
        linewidth=1,
        alpha=0.95,
        zorder=3.1,
    )
    axis.add_geometries(
        coastline_geometries,
        crs=crs,
        facecolor="none",
        edgecolor="0.12",
        linewidth=0.45,
        zorder=4,
    )
    axis.contour(
        longitude,
        latitude,
        ocean_distance_to_coast.values,
        levels=[coastal_distance_km],
        colors=["#1f5673"],
        linewidths=0.55,
        linestyles="--",
        transform=crs,
        zorder=4,
    )
    axis.set_extent(extent, crs=crs)

    grid = axis.gridlines(
        draw_labels=True,
        linewidth=0.25,
        color="0.35",
        alpha=0.45,
        linestyle="--",
    )
    grid.top_labels = False
    grid.right_labels = False
    grid.xlabel_style = {"size": grid_label_size}
    grid.ylabel_style = {"size": grid_label_size}

    if show_title:
        axis.set_title(
            "Temporal mean dynamic sea level (GLORYS zos)\n"
            f"within {coastal_distance_km:.0f} km of the coastline | {period}",
            fontsize=11,
            fontweight="bold",
            pad=9,
        )
    # Optional river names. Uncomment this block and the path_effects import
    # near the top of the file to restore the labels.
    # for river_name, (label_lon, label_lat) in RIVER_LABELS.items():
    #     label = axis.text(
    #         label_lon,
    #         label_lat,
    #         river_name,
    #         transform=crs,
    #         fontsize=7,
    #         fontstyle="italic",
    #         color="#1f638d",
    #         ha="center",
    #         va="center",
    #         zorder=5,
    #     )
    #     label.set_path_effects(
    #         [path_effects.withStroke(linewidth=2.0, foreground="white")]
    #     )

    # Optional map legend. Uncomment this block and the Line2D import near the
    # top of the file to restore it.
    # legend_handles = [
    #     Line2D(
    #         [0],
    #         [0],
    #         color="#2f78a3",
    #         linewidth=1.1,
    #         label="Main rivers (Natural Earth + ANA BHO)",
    #     ),
    #     Line2D(
    #         [0],
    #         [0],
    #         color="#1f5673",
    #         linewidth=0.9,
    #         linestyle="--",
    #         label=f"{coastal_distance_km:.0f} km from coastline",
    #     ),
    # ]
    # axis.legend(
    #     handles=legend_handles,
    #     loc="lower left",
    #     fontsize=7.5,
    #     frameon=True,
    #     framealpha=0.92,
    #     borderpad=0.45,
    # )

    colorbar = fig.colorbar(
        mesh,
        ax=axis,
        orientation="vertical",
        ticks=boundaries,
        boundaries=boundaries,
        spacing="uniform",
        drawedges=True,
        extend="max",
        extendfrac="auto",
        pad=0.025,
        shrink=0.86,
    )
    colorbar.set_label("Mean zos (m)", fontsize=colorbar_label_size)
    colorbar.ax.tick_params(labelsize=colorbar_tick_size)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return sorted(set(river_names) | set(apodi_names) | set(paraguacu_names))


def field_statistics(field: xr.DataArray) -> dict[str, float | int]:
    finite = field.values[np.isfinite(field.values)]
    return {
        "finite_cells": int(finite.size),
        "minimum": float(finite.min()),
        "mean": float(finite.mean()),
        "maximum": float(finite.max()),
    }


def main(*, article_supplement: bool = False) -> None:
    args = parse_args(article_supplement=article_supplement)
    for path in (
        args.input,
        args.coastline,
        args.apodi_river,
        args.paraguacu_river,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    if args.coastal_distance_km <= 0:
        raise ValueError("--coastal-distance-km must be positive")

    figure_dir = args.output_dir if article_supplement else args.output_dir / "figures"
    data_dir = args.output_dir / "data"
    metadata_dir = args.output_dir / "metadata"
    for directory in (figure_dir, data_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    with xr.open_dataset(args.input) as dataset:
        if "zos" not in dataset:
            raise ValueError(
                f"'zos' not found. Available variables: {list(dataset.data_vars)}"
            )
        zos = sort_lat_lon(dataset["zos"])
        time_name = coord_name(zos, ("time",))
        period_start = str(zos[time_name].values[0])[:10]
        period_end = str(zos[time_name].values[-1])[:10]
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Mean of empty slice",
                category=RuntimeWarning,
            )
            mean_zos = zos.mean(time_name, skipna=True).astype("float32").load()
        source_units = zos.attrs.get("units", "m")

    distance = distance_to_coast(mean_zos, args.coastline).load()
    ocean_distance = distance.where(np.isfinite(mean_zos))
    distance_tag = f"{args.coastal_distance_km:.0f}km"
    coastal_mask = (ocean_distance <= args.coastal_distance_km).rename(
        f"within_{distance_tag}_coast_mask"
    )
    coastal_mean = mean_zos.where(coastal_mask).rename(
        "zos_temporal_mean_coastal_band"
    )
    period = f"{period_start} to {period_end}"
    coastal_mean.attrs.update(
        {
            "long_name": (
                "Temporal mean GLORYS zos within "
                f"{args.coastal_distance_km:.0f} km of the coastline"
            ),
            "units": source_units,
            "source_variable": "zos",
            "excluded_variables": "tide_daily_max, SSH_total",
            "source_file": relative(args.input),
            "period": period,
            "coastal_distance_mask": (
                f"distance_to_coast_km <= {args.coastal_distance_km:g}"
            ),
        }
    )
    ocean_distance = ocean_distance.rename("ocean_distance_to_coast_km")
    ocean_distance.attrs.update(distance.attrs)
    ocean_distance.attrs["long_name"] = (
        "Approximate great-circle distance from valid ocean cells to coastline"
    )
    coastal_mask.attrs.update(
        {
            "long_name": (
                "Valid ocean cells within "
                f"{args.coastal_distance_km:.0f} km of the coastline"
            ),
            "coastline_source": relative(args.coastline),
        }
    )

    boundaries = field_boundaries(coastal_mean)
    if article_supplement:
        figure_path = (
            figure_dir
            / f"supplementary_temporal_mean_zos_within_{distance_tag}_coast.png"
        )
        metadata_path = (
            metadata_dir / "supplementary_zos_mean_coastal_band_metadata.json"
        )
    else:
        run_date = date.today().strftime("%Y%m%d")
        figure_path = (
            figure_dir
            / f"explore_zos_mean_within_{distance_tag}_coast_{run_date}.png"
        )
        metadata_path = (
            metadata_dir / "explore_zos_mean_coastal_band_metadata.json"
        )
    data_path = data_dir / f"zos_temporal_mean_within_{distance_tag}_coast.nc"

    xr.Dataset(
        {
            coastal_mean.name: coastal_mean,
            ocean_distance.name: ocean_distance,
            coastal_mask.name: coastal_mask.astype("int8"),
        }
    ).to_netcdf(data_path)
    river_names = plot_mean_coastal_band_map(
        coastal_mean,
        ocean_distance,
        coastal_distance_km=args.coastal_distance_km,
        boundaries=boundaries,
        coastline=args.coastline,
        apodi_river=args.apodi_river,
        paraguacu_river=args.paraguacu_river,
        period=period,
        output=figure_path,
        dpi=args.dpi,
        show_title=not article_supplement,
        show_administrative_boundaries=article_supplement,
        grid_label_size=10 if article_supplement else 8,
        colorbar_label_size=11 if article_supplement else 10,
        colorbar_tick_size=10 if article_supplement else 8,
    )

    metadata = {
        "figure_role": "supplementary" if article_supplement else "exploratory",
        "input": relative(args.input),
        "source_variable": "zos",
        "excluded_variables": ["tide_daily_max", "SSH_total"],
        "period": {"start": period_start, "end": period_end},
        "units": source_units,
        "coastal_distance_mask": {
            "coastline": relative(args.coastline),
            "coastline_dataset": "Natural Earth 10m coastline",
            "criterion": (
                f"distance_to_coast_km <= {args.coastal_distance_km:g}"
            ),
            "method": distance.attrs["method"],
            "earth_radius_km": EARTH_RADIUS_KM,
            "coastline_densification_step_degrees": COAST_DENSIFY_STEP_DEG,
            "coastline_sample_count": distance.attrs["coastline_sample_count"],
        },
        "statistics": {
            "temporal_mean_in_coastal_band": field_statistics(coastal_mean),
        },
        "colorbar": {
            "type": "discrete",
            "number_of_bins": int(len(boundaries) - 1),
            "boundaries_m": boundaries.tolist(),
            "palette": list(
                palette_for_bins(
                    len(boundaries) - 1,
                    reserve_over_color=True,
                )
            ),
            "extend": "max",
            "extend_threshold_m": COLORBAR_MAX_M,
            "over_color": QUALITY_COLORS_WORSE_TO_BETTER[-1],
            "palette_source": "article calibration heatmaps (R_pos/B/F_soft)",
        },
        "rivers": {
            "sources": [
                {
                    "dataset": "Natural Earth 10m rivers_lake_centerlines",
                    "maximum_scalerank": MAXIMUM_RIVER_SCALERANK,
                    "forced_names": sorted(FORCED_NATURAL_EARTH_RIVERS),
                },
                {
                    "dataset": "ANA Base Hidrográfica Ottocodificada",
                    "input": relative(args.apodi_river),
                    "service": (
                        "dados_abertos/Hidrografia/MapServer/0 (SNIRH/ANA)"
                    ),
                    "query": "NORIOCOMP = 'Rio Apodi'",
                },
                {
                    "dataset": "ANA Base Hidrográfica Ottocodificada",
                    "input": relative(args.paraguacu_river),
                    "service": (
                        "dados_abertos/Hidrografia/MapServer/0 (SNIRH/ANA)"
                    ),
                    "query": "NORIOCOMP = 'Rio Paraguaçu'",
                },
            ],
            "labels_drawn": [],
            "configured_labels": sorted(RIVER_LABELS),
            "legend_drawn": False,
            "names_intersecting_map": river_names,
        },
        "administrative_boundaries": {
            "drawn": article_supplement,
            "countries": {
                "dataset": "Natural Earth 10m admin_0_boundary_lines_land",
                "line_color": "0.32",
                "line_width_pt": 0.55,
            },
            "states_and_provinces": {
                "dataset": "Natural Earth 10m admin_1_states_provinces_lines",
                "line_color": "0.58",
                "line_width_pt": 0.30,
            },
        },
        "plot_style": {
            "dpi": args.dpi,
            "title_drawn": not article_supplement,
            "grid_label_size_pt": 10 if article_supplement else 8,
            "colorbar_label_size_pt": 11 if article_supplement else 10,
            "colorbar_tick_size_pt": 10 if article_supplement else 8,
        },
        "outputs": {"figure": relative(figure_path), "fields": relative(data_path)},
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(figure_path)
    print(data_path)
    print(metadata_path)

    if article_supplement:
        from src.figures_article.make_article_risk_figures import (
            validate_article_figure_outputs,
        )

        validate_article_figure_outputs()


if __name__ == "__main__":
    main()
