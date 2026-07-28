r"""Generate only the Santa Catarina calibration-location map.

Suggested LaTeX figure block (requires ``\usepackage{graphicx}``)
-----------------------------------------------------------------
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\linewidth]{outputs/article_figures/santa_catarina_study_area_and_grid_points.png}
    \caption{Santa Catarina coastal study area and municipality--grid
    association used in the threshold-calibration analysis. Colored polygons
    identify the study municipalities grouped into five coastal sectors
    (North, Central-north, Central, Central-south, and South). Open circles
    indicate the nearest ocean grid points, and gray lines connect each
    municipality to its assigned grid point. Gray shading denotes land and the
    light-blue background denotes the ocean. Numbered municipalities are:
    1, Itapoá; 2, São Francisco do Sul; 3, Araquari; 4, Balneário Barra do Sul;
    5, Barra Velha; 6, Balneário Piçarras; 7, Penha; 8, Navegantes; 9, Itajaí;
    10, Balneário Camboriú; 11, Itapema; 12, Bombinhas; 13, Porto Belo;
    14, Tijucas; 15, Biguaçu; 16, Florianópolis; 17, Palhoça; 18, Garopaba;
    19, Imbituba; 20, Laguna; 21, Içara; 22, Balneário Rincão; 23, Araranguá;
    24, Balneário Arroio do Silva; 25, Balneário Gaivota; and 26, Passo de
    Torres. The inset locates Santa Catarina within South America.}
    \label{fig:calibration-study-area-grid}
\end{figure}
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import Point, Polygon, box
from shapely.ops import polygonize, unary_union

from config.plot_config import SECTOR_COLORS, apply_publication_style
from src.figures_article.calibration_common import COASTLINE_SHP, SECTOR_ORDER, load_map_data
from src.figures_article.figure_io import _save_figure, validate_article_figure_outputs

MAP_EXTENT = (-50.25, -47.95, -29.45, -25.75)
GEOMETRY_CRS = "EPSG:31982"
COAST_MATCH_TOLERANCE_METRES = 2_000
LAND_COLOR = "#D8D8D4"
OCEAN_COLOR = "#EAF3F8"
MUNICIPALITY_MAP_IDS = {
    "Itapoá": 1,
    "São Francisco do Sul": 2,
    "Araquari": 3,
    "Balneário Barra do Sul": 4,
    "Barra Velha": 5,
    "Balneário Piçarras": 6,
    "Penha": 7,
    "Navegantes": 8,
    "Itajaí": 9,
    "Balneário Camboriú": 10,
    "Itapema": 11,
    "Bombinhas": 12,
    "Porto Belo": 13,
    "Tijucas": 14,
    "Biguaçu": 15,
    "Florianópolis": 16,
    "Palhoça": 17,
    "Garopaba": 18,
    "Imbituba": 19,
    "Laguna": 20,
    "Içara": 21,
    "Balneário Rincão": 22,
    "Araranguá": 23,
    "Balneário Arroio do Silva": 24,
    "Balneário Gaivota": 25,
    "Passo de Torres": 26,
}


def _coastline_from_municipal_geometry(
    brazil_municipalities: gpd.GeoDataFrame,
) -> gpd.GeoSeries:
    """Return maritime edges that coincide exactly with the municipal polygons.

    Natural Earth is used only to classify which parts of the SC polygon edge
    are coastal. The returned linework itself comes from the municipal geometry,
    preventing mismatched generalisations from crossing filled polygons.
    """
    sc = brazil_municipalities[brazil_municipalities["state"] == "SC"]
    sc_projected = sc.to_crs(GEOMETRY_CRS).geometry.union_all()
    reference = gpd.read_file(COASTLINE_SHP, bbox=MAP_EXTENT).to_crs(GEOMETRY_CRS)
    coastal_zone = reference.geometry.union_all().buffer(COAST_MATCH_TOLERANCE_METRES)
    aligned = sc_projected.boundary.intersection(coastal_zone)
    return gpd.GeoSeries([aligned], crs=GEOMETRY_CRS).to_crs("EPSG:4326")


def _shared_state_boundaries(
    brazil_municipalities: gpd.GeoDataFrame,
) -> gpd.GeoSeries:
    """Extract SC's shared PR/RS borders without outlining the coastal strip."""
    projected = brazil_municipalities.to_crs(GEOMETRY_CRS)
    sc_boundary = projected[projected["state"] == "SC"].geometry.union_all().boundary
    borders = []
    for neighbour in ("PR", "RS"):
        neighbour_union = projected[projected["state"] == neighbour].geometry.union_all()
        borders.append(sc_boundary.intersection(neighbour_union.buffer(20)))
    return gpd.GeoSeries(borders, crs=GEOMETRY_CRS).to_crs("EPSG:4326")


def _regional_land_geometry(
    brazil_municipalities: gpd.GeoDataFrame,
    aligned_coastline: gpd.GeoSeries,
) -> gpd.GeoSeries:
    """Build a local land mask and replace its coastal edge with municipal data."""
    domain = box(MAP_EXTENT[0], MAP_EXTENT[2], MAP_EXTENT[1], MAP_EXTENT[3])
    reference = gpd.read_file(COASTLINE_SHP, bbox=MAP_EXTENT).to_crs("EPSG:4326")
    open_lines = [geometry.intersection(domain) for geometry in reference.geometry if not geometry.is_ring]
    cells = list(polygonize(unary_union(open_lines + [domain.boundary])))
    land_seed = Point(MAP_EXTENT[0] + 0.01, (MAP_EXTENT[2] + MAP_EXTENT[3]) / 2)
    mainland = next(cell for cell in cells if cell.covers(land_seed))
    islands = [Polygon(geometry.coords) for geometry in reference.geometry if geometry.is_ring]
    base_land = gpd.GeoSeries([unary_union([mainland, *islands])], crs="EPSG:4326").to_crs(GEOMETRY_CRS).iloc[0]

    sc_land = (
        brazil_municipalities[brazil_municipalities["state"] == "SC"]
        .to_crs(GEOMETRY_CRS).geometry.union_all()
    )
    coast_zone = aligned_coastline.to_crs(GEOMETRY_CRS).union_all().buffer(3_000)
    corrected_land = base_land.difference(coast_zone).union(sc_land.intersection(coast_zone))
    return gpd.GeoSeries([corrected_land], crs=GEOMETRY_CRS).to_crs("EPSG:4326")


def generate_calibration_map() -> list[str]:
    apply_publication_style()
    municipalities, grid, brazil_municipalities = load_map_data()
    projection = ccrs.PlateCarree()
    fig = plt.figure(figsize=(7.2, 8.4))
    ax = fig.add_axes([0.08, 0.06, 0.84, 0.86], projection=projection)
    ax.set_extent(MAP_EXTENT, crs=projection)
    ax.set_facecolor(OCEAN_COLOR)
    coastline = _coastline_from_municipal_geometry(brazil_municipalities)
    regional_land = _regional_land_geometry(brazil_municipalities, coastline)
    ax.add_geometries(regional_land, crs=projection, facecolor=LAND_COLOR,
                      edgecolor="none", zorder=0)

    ax.add_geometries(brazil_municipalities.geometry, crs=projection, facecolor=LAND_COLOR,
                      edgecolor="#B8B8B2", linewidth=0.25, zorder=1)
    for sector in SECTOR_ORDER:
        subset = municipalities[municipalities["sector"] == sector]
        if not subset.empty:
            ax.add_geometries(subset.geometry, crs=projection, facecolor=SECTOR_COLORS[sector],
                              edgecolor="white", linewidth=0.65, alpha=0.88, zorder=3)
    # Both line layers are derived from the same municipal polygons as the fills.
    # This guarantees exact spatial coincidence at publication resolution.
    state_boundaries = _shared_state_boundaries(brazil_municipalities)
    ax.add_geometries(state_boundaries, crs=projection, facecolor="none",
                      edgecolor="#73777A", linewidth=1.0, zorder=3.4)
    ax.add_geometries(coastline, crs=projection, facecolor="none",
                      edgecolor="#22272B", linewidth=0.9, zorder=3.5)

    unique_points = grid.drop_duplicates(["grid_lat", "grid_lon"])
    for _, row in grid.iterrows():
        ax.plot([row["muni_lon"], row["grid_lon"]], [row["muni_lat"], row["grid_lat"]],
                transform=projection, color="#505050", linewidth=0.45, alpha=0.42, zorder=4)
    ax.scatter(unique_points["grid_lon"], unique_points["grid_lat"], transform=projection,
               s=24, marker="o", facecolor="white", edgecolor="black", linewidth=0.75, zorder=6)
    label_data = municipalities.copy()
    label_data["map_id"] = label_data["municipality_name"].map(MUNICIPALITY_MAP_IDS)
    missing_ids = label_data.loc[label_data["map_id"].isna(), "municipality_name"].tolist()
    if missing_ids:
        raise ValueError(f"Missing map identifiers for municipalities: {missing_ids}")
    label_data["label_point"] = (
        label_data.to_crs(GEOMETRY_CRS).geometry.representative_point().to_crs("EPSG:4326")
    )
    for row in label_data.itertuples():
        label = ax.text(row.label_point.x, row.label_point.y, str(int(row.map_id)),
                        transform=projection, fontsize=6.5, fontweight="bold",
                        ha="center", va="center", color="#111111", zorder=7)
        label.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground="white")])
    gl = ax.gridlines(draw_labels=True, linewidth=0.35, color="#777777", alpha=0.5,
                      linestyle="--", x_inline=False, y_inline=False)
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 8}

    inset_crs = ccrs.Orthographic(central_longitude=-52, central_latitude=-28)
    inset = fig.add_axes([0.105, 0.70, 0.22, 0.19], projection=inset_crs)
    inset.set_global()
    inset.set_facecolor("#DCECF4")
    inset.add_feature(cfeature.LAND.with_scale("110m"), facecolor="#C8C8C8",
                      edgecolor="#555555", linewidth=0.35, zorder=1)
    inset.add_feature(cfeature.BORDERS.with_scale("110m"), edgecolor="#666666", linewidth=0.35, zorder=2)
    sc_boundary = brazil_municipalities[brazil_municipalities["state"] == "SC"].dissolve()
    inset.add_geometries(sc_boundary.geometry, crs=projection, facecolor="none",
                         edgecolor="#D7191C", linewidth=2.6, zorder=4)

    sector_handles = [Patch(facecolor=SECTOR_COLORS[s], edgecolor="none", label=s) for s in SECTOR_ORDER]
    symbol_handles = [
        Line2D([], [], marker="o", linestyle="none", markerfacecolor="white",
               markeredgecolor="black", markersize=5, label="Ocean grid point"),
        Line2D([], [], color="#505050", linewidth=0.7, label="Municipality–grid link"),
    ]
    ax.legend(handles=sector_handles + symbol_handles, loc="upper left",
              bbox_to_anchor=(0.015, 0.68), ncol=1, fontsize=10.0,
              frameon=True, framealpha=0.92, borderpad=0.55,
              labelspacing=0.35, handlelength=1.5)
    return _save_figure(fig, "santa_catarina_study_area_and_grid_points")


def main() -> None:
    for path in generate_calibration_map():
        print(path)
    validate_article_figure_outputs()


if __name__ == "__main__":
    main()
