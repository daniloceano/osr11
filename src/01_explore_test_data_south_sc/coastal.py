"""
Coastal grid point selection using the Natural Earth 10 m coastline.

This module replaces the heuristic of using "minimum longitude" as a coastal
proxy.  Instead, every grid point is evaluated against the actual NE coastline:

1. Load all NE coastline vertices from the local shapefile.
2. Build a KDTree in approximate-km coordinates.
3. For a model grid (lat × lon), return a boolean mask of cells that are:
   - non-NaN in the temporal mean (i.e. valid ocean cells), AND
   - within *max_dist_km* kilometres of the nearest coastline vertex.
4. Given a reference location (e.g. a municipality centroid), find the nearest
   coastal grid point in O(log N) time.

Scientific rationale
--------------------
Grid cells identified as "coastal" by this procedure are guaranteed to:
- Carry real ocean model data (non-NaN mean).
- Lie within a physically meaningful distance of the land–sea boundary.

This is preferable to a minimum-longitude proxy, which can select offshore
cells for domains where the coast is not strictly meridional, or can
accidentally pick sub-domain grid cells far from any coastline.

Dependencies
------------
Uses ``cartopy.io.shapereader`` (already a project dependency via cartopy)
which wraps pyshp and returns shapely geometries.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from scipy.spatial import KDTree

log = logging.getLogger(__name__)


# ── Coastline loading ─────────────────────────────────────────────────────────

def load_coastline_vertices(shp_path: Path) -> np.ndarray:
    """Load all vertex coordinates from a Natural Earth shapefile.

    Parameters
    ----------
    shp_path:
        Path to the ``.shp`` file (e.g. ``ne_10m_coastline.shp``).

    Returns
    -------
    np.ndarray of shape (N, 2) with columns [lat, lon] (degrees).
    """
    import cartopy.io.shapereader as shpreader

    reader = shpreader.Reader(str(shp_path))
    all_pts: list[np.ndarray] = []

    for geom in reader.geometries():
        if geom.geom_type == "MultiLineString":
            for part in geom.geoms:
                pts = np.array(part.coords)      # [[lon, lat], ...]
                all_pts.append(pts[:, ::-1])     # -> [[lat, lon], ...]
        elif geom.geom_type == "LineString":
            pts = np.array(geom.coords)          # [[lon, lat], ...]
            all_pts.append(pts[:, ::-1])

    if not all_pts:
        raise ValueError(f"No valid LineString geometries found in {shp_path}")

    vertices = np.vstack(all_pts)
    log.debug("NE coastline: %d vertices loaded from %s", len(vertices), shp_path.name)
    return vertices                              # shape (N, 2): [lat, lon]


# ── Primary public function ───────────────────────────────────────────────────

def find_coastal_points(
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    data_mean: np.ndarray,
    shp_path: Path,
    max_dist_km: float = 50.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Identify valid ocean grid cells within *max_dist_km* of the coastline.

    Parameters
    ----------
    lat_grid, lon_grid:
        1-D coordinate arrays (degrees).
    data_mean:
        2-D array of shape (n_lat, n_lon) — temporal mean used to mark valid
        (non-NaN) ocean cells.  Cells with NaN mean are treated as land.
    shp_path:
        Path to the NE 10 m coastline ``.shp`` file.
    max_dist_km:
        Maximum distance (km) from the coastline for a cell to qualify as
        "coastal".  Default: 50 km (~5 grid cells at 1/12° resolution).

    Returns
    -------
    coastal_mask : np.ndarray of shape (n_lat, n_lon), dtype=bool
        True where the cell is both valid (non-NaN) and within *max_dist_km*
        of the coastline.
    dist_to_coast : np.ndarray of shape (n_lat, n_lon), dtype=float
        Distance to the nearest coastline vertex in km.  NaN for land cells
        (NaN in *data_mean*).
    """
    valid_mask = ~np.isnan(data_mean)           # (n_lat, n_lon) bool

    # ── Build coastline KDTree in approximate km ──────────────────────────
    coast_ll  = load_coastline_vertices(shp_path)  # (N, 2) [lat, lon]
    lat_ref   = float(np.mean(lat_grid))
    cos_lat   = np.cos(np.radians(lat_ref))

    def _to_km(lat_lon: np.ndarray) -> np.ndarray:
        return np.column_stack([
            lat_lon[:, 0] * 111.0,
            lat_lon[:, 1] * 111.0 * cos_lat,
        ])

    coast_km = _to_km(coast_ll)
    tree     = KDTree(coast_km)

    # ── Query distances for all valid grid cells ──────────────────────────
    lats, lons    = np.meshgrid(lat_grid, lon_grid, indexing="ij")
    valid_idx     = np.argwhere(valid_mask)                 # (M, 2)
    valid_pts_ll  = np.column_stack([
        lats[valid_mask], lons[valid_mask],
    ])                                                       # (M, 2)
    valid_pts_km  = _to_km(valid_pts_ll)

    dists_valid, _ = tree.query(valid_pts_km)                # (M,)

    # ── Assemble output arrays ────────────────────────────────────────────
    dist_to_coast   = np.full(data_mean.shape, np.nan)
    coastal_mask    = np.zeros(data_mean.shape, dtype=bool)

    for (i, j), d in zip(valid_idx, dists_valid):
        dist_to_coast[i, j] = d
        if d <= max_dist_km:
            coastal_mask[i, j] = True

    n_coastal = int(coastal_mask.sum())
    log.info(
        "Coastal mask: %d valid ocean cells | %d within %.0f km of coastline",
        int(valid_mask.sum()), n_coastal, max_dist_km,
    )
    if n_coastal == 0:
        log.warning(
            "No coastal grid cells found within %.0f km — check domain extent "
            "and coastline file path.", max_dist_km,
        )

    return coastal_mask, dist_to_coast


# ── Nearest coastal point ─────────────────────────────────────────────────────

def nearest_coastal_point(
    lat_ref: float,
    lon_ref: float,
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    coastal_mask: np.ndarray,
) -> dict | None:
    """Find the nearest coastal grid point to a reference location.

    Parameters
    ----------
    lat_ref, lon_ref:
        Reference coordinates (e.g. municipality centroid), in degrees.
    lat_grid, lon_grid:
        1-D coordinate arrays (degrees).
    coastal_mask:
        Boolean mask of shape (n_lat, n_lon) from :func:`find_coastal_points`.

    Returns
    -------
    dict with keys ``grid_lat``, ``grid_lon``, ``lat_idx``, ``lon_idx``,
    ``dist_km``; or ``None`` if *coastal_mask* contains no True values.
    """
    coast_idx = np.argwhere(coastal_mask)       # (M, 2)
    if len(coast_idx) == 0:
        return None

    lats, lons = np.meshgrid(lat_grid, lon_grid, indexing="ij")
    coast_lats = lats[coastal_mask]
    coast_lons = lons[coastal_mask]

    cos_lat  = np.cos(np.radians(lat_ref))
    dlat_km  = (coast_lats - lat_ref) * 111.0
    dlon_km  = (coast_lons - lon_ref) * 111.0 * cos_lat
    dists    = np.sqrt(dlat_km**2 + dlon_km**2)

    best     = int(np.argmin(dists))
    i_lat, i_lon = coast_idx[best]

    return {
        "grid_lat": float(lat_grid[i_lat]),
        "grid_lon": float(lon_grid[i_lon]),
        "lat_idx":  int(i_lat),
        "lon_idx":  int(i_lon),
        "dist_km":  float(dists[best]),
    }
