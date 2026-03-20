"""
Part E — Municipality–grid association.

For each municipality in the events database:
1. Fetches its centroid coordinates from the IBGE Localidades + Malhas APIs.
2. Identifies "coastal" grid cells in each model grid (WAVERYS, GLORYS) using
   the Natural Earth 10 m coastline — cells must be non-NaN AND within
   *max_coastal_dist_km* of the actual coastline.
3. Finds the nearest coastal grid cell in each model to the municipality
   centroid, using a KDTree in approximate-km coordinates.
4. Flags municipalities with separate ``in_wave_domain`` and ``in_gl_domain``
   booleans, reflecting that WAVERYS and GLORYS may have different coastal
   coverage (GLORYS uses a finer ocean mask, leading to some coastal cells
   being land-masked in GLORYS but valid in WAVERYS).

The ``in_test_domain`` column (legacy alias for ``in_wave_domain``) is kept
for backward compatibility with downstream modules.

IBGE coordinate strategy
-------------------------
Centroid of the outer polygon ring from IBGE Malhas v2 API.
Composite municipality names (e.g. "Içara/Balneário Rincão") are matched
by trying each part after splitting on "/" or "|".
"""
from __future__ import annotations

import gzip
import json
import logging
import sys
import unicodedata
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# Allow running this module directly (python municipalities.py)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.coastal import find_coastal_points, nearest_coastal_point
from src.explore_test_data_south_sc.config.analysis_config import CFG

log = logging.getLogger(__name__)


# ── Public analysis function ──────────────────────────────────────────────────

def run_municipality_grid_association(
    df_events: pd.DataFrame,
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
) -> pd.DataFrame:
    """Part E: fetch IBGE coordinates and associate municipalities to coastal grid points.

    Returns
    -------
    pd.DataFrame
        One row per municipality with coordinates, nearest coastal grid points,
        and ``in_wave_domain`` / ``in_gl_domain`` / ``in_test_domain`` flags.
    """
    log.info("== Part E: Municipality–grid association (NE coastline approach) ==")

    municipalities = sorted(df_events["municipality"].dropna().unique().tolist())
    log.info("Unique municipalities in database: %d", len(municipalities))

    muni_coords = fetch_ibge_coords(municipalities)

    # Pre-compute coastal masks for both grids (computed once, reused per municipality)
    log.info("  Computing WAVERYS coastal mask...")
    wave_mean     = ds_wave[CFG["wave_var"]].mean(dim="time").values
    wave_coastal, _ = find_coastal_points(
        ds_wave.latitude.values, ds_wave.longitude.values,
        wave_mean,
        shp_path    = CFG["ne_coastline_shp"],
        max_dist_km = CFG["max_coastal_dist_km"],
    )

    log.info("  Computing GLORYS coastal mask...")
    gl_mean       = ds_gl[CFG["ssl_var"]].mean(dim="time").values
    gl_coastal, _ = find_coastal_points(
        ds_gl.latitude.values, ds_gl.longitude.values,
        gl_mean,
        shp_path    = CFG["ne_coastline_shp"],
        max_dist_km = CFG["max_coastal_dist_km"],
    )

    grid_table = build_grid_table(
        muni_coords,
        ds_wave.latitude.values, ds_wave.longitude.values, wave_coastal,
        ds_gl.latitude.values,   ds_gl.longitude.values,   gl_coastal,
    )

    sector_map = df_events.groupby("municipality")["coastal_sector"].first()
    grid_table["coastal_sector"] = grid_table["municipality"].map(sector_map)

    cols = [
        "municipality", "coastal_sector", "muni_lat", "muni_lon",
        "in_wave_domain", "in_gl_domain", "in_test_domain",
        "wave_grid_lat", "wave_grid_lon", "wave_dist_km",
        "gl_grid_lat", "gl_grid_lon", "gl_dist_km",
    ]
    grid_table = grid_table[[c for c in cols if c in grid_table.columns]]

    out = CFG["tab_dir"] / "tab_municipality_grid_association.csv"
    grid_table.to_csv(out, index=False)
    log.info("  -> tab_municipality_grid_association.csv")

    n_wave = int(grid_table["in_wave_domain"].sum())
    n_gl   = int(grid_table["in_gl_domain"].sum())
    n_tot  = len(grid_table)
    log.info(
        "  %d/%d municipalities have WAVERYS coastal point | "
        "%d/%d have GLORYS coastal point",
        n_wave, n_tot, n_gl, n_tot,
    )

    outside_wave = grid_table.loc[~grid_table["in_wave_domain"], "municipality"].tolist()
    outside_gl   = grid_table.loc[~grid_table["in_gl_domain"],   "municipality"].tolist()
    if outside_wave:
        log.info("  No WAVERYS coastal point: %s", outside_wave)
    if outside_gl:
        log.info("  No GLORYS coastal point:  %s", outside_gl)

    return grid_table


# ── Grid-table builder ────────────────────────────────────────────────────────

def build_grid_table(
    muni_coords: pd.DataFrame,
    lat_wave: np.ndarray, lon_wave: np.ndarray, wave_coastal: np.ndarray,
    lat_gl: np.ndarray,   lon_gl: np.ndarray,   gl_coastal: np.ndarray,
) -> pd.DataFrame:
    """Associate each municipality to its nearest coastal WAVERYS and GLORYS points.

    Uses the precomputed coastal masks (non-NaN AND within max_coastal_dist_km
    of the NE coastline) rather than a simple bounding-box check.

    Parameters
    ----------
    muni_coords:
        Output of :func:`fetch_ibge_coords`.
    lat_wave, lon_wave, wave_coastal:
        WAVERYS 1-D coordinate arrays and boolean coastal mask.
    lat_gl, lon_gl, gl_coastal:
        GLORYS 1-D coordinate arrays and boolean coastal mask.

    Returns
    -------
    pd.DataFrame with one row per municipality.
    """
    rows = []
    for _, row in muni_coords.iterrows():
        lat, lon = row["lat"], row["lon"]
        r: dict = {
            "municipality": row["municipality"],
            "muni_lat":     lat,
            "muni_lon":     lon,
        }

        if np.isnan(lat) or np.isnan(lon):
            r.update({
                "in_wave_domain": False, "in_gl_domain": False, "in_test_domain": False,
                "wave_grid_lat": np.nan, "wave_grid_lon": np.nan, "wave_dist_km": np.nan,
                "gl_grid_lat":   np.nan, "gl_grid_lon":   np.nan, "gl_dist_km":   np.nan,
            })
            rows.append(r)
            continue

        # WAVERYS nearest coastal point
        wp = nearest_coastal_point(lat, lon, lat_wave, lon_wave, wave_coastal)
        if wp is not None:
            r.update({
                "in_wave_domain":  True,
                "wave_grid_lat":   wp["grid_lat"],
                "wave_grid_lon":   wp["grid_lon"],
                "wave_dist_km":    wp["dist_km"],
            })
        else:
            r.update({
                "in_wave_domain":  False,
                "wave_grid_lat":   np.nan,
                "wave_grid_lon":   np.nan,
                "wave_dist_km":    np.nan,
            })

        # GLORYS nearest coastal point
        gp = nearest_coastal_point(lat, lon, lat_gl, lon_gl, gl_coastal)
        if gp is not None:
            r.update({
                "in_gl_domain": True,
                "gl_grid_lat":  gp["grid_lat"],
                "gl_grid_lon":  gp["grid_lon"],
                "gl_dist_km":   gp["dist_km"],
            })
        else:
            r.update({
                "in_gl_domain": False,
                "gl_grid_lat":  np.nan,
                "gl_grid_lon":  np.nan,
                "gl_dist_km":   np.nan,
            })

        # Legacy alias: in_test_domain = in_wave_domain
        r["in_test_domain"] = r["in_wave_domain"]
        rows.append(r)

    return pd.DataFrame(rows)


# ── IBGE coordinate retrieval ─────────────────────────────────────────────────

def fetch_ibge_coords(names: list[str]) -> pd.DataFrame:
    """Fetch municipality centroid coordinates from the IBGE APIs.

    Uses IBGE Localidades v1 for IBGE codes and IBGE Malhas v2 for polygon
    geometry. Coordinate is the centroid of the outer polygon ring.

    Parameters
    ----------
    names: list of municipality names (as they appear in the events database).

    Returns
    -------
    pd.DataFrame with columns: municipality, ibge_code, lat, lon, coord_source.
    """
    log.info("Fetching SC municipality list from IBGE API...")
    raw = _ibge_get(
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados/SC/municipios"
    )
    if raw is None:
        log.warning("IBGE API unavailable — municipality coordinates will be NaN.")
        return pd.DataFrame({
            "municipality": names, "ibge_code": pd.NA,
            "lat": np.nan, "lon": np.nan, "coord_source": "ibge_unavailable",
        })

    ibge_lookup = {_norm(m["nome"]): m for m in raw}
    records = []

    for raw_name in names:
        parts   = [p.strip() for p in raw_name.replace("/", "|").split("|")]
        matched = next(
            (ibge_lookup[_norm(p)] for p in parts if _norm(p) in ibge_lookup), None
        )
        if matched is None:
            log.warning("  Not found in IBGE list: %r", raw_name)
            records.append({
                "municipality": raw_name, "ibge_code": pd.NA,
                "lat": np.nan, "lon": np.nan, "coord_source": "not_found",
            })
            continue

        code = matched["id"]
        geo  = _ibge_get(
            f"https://servicodados.ibge.gov.br/api/v2/malhas/{code}"
            f"?resolucao=2&formato=application/vnd.geo+json"
        )
        if geo is None:
            records.append({
                "municipality": raw_name, "ibge_code": code,
                "lat": np.nan, "lon": np.nan, "coord_source": "api_error",
            })
            continue

        try:
            geom = geo["features"][0]["geometry"]
            if geom["type"] == "Polygon":
                lat, lon = _polygon_centroid(geom["coordinates"])
            elif geom["type"] == "MultiPolygon":
                largest = max(geom["coordinates"], key=lambda p: len(p[0]))
                lat, lon = _polygon_centroid(largest)
            else:
                raise ValueError(f"Unexpected geometry type: {geom['type']}")

            records.append({
                "municipality":  raw_name,
                "ibge_code":     code,
                "lat":           lat,
                "lon":           lon,
                "coord_source":  f"IBGE malhas v2 — code {code} — outer polygon centroid",
            })
            log.info("  %s -> IBGE %s -> (%.3fS, %.3fW)", raw_name, code, lat, lon)

        except Exception as exc:
            log.warning("  Failed to parse IBGE geometry for %r: %s", raw_name, exc)
            records.append({
                "municipality": raw_name, "ibge_code": code,
                "lat": np.nan, "lon": np.nan, "coord_source": "parse_error",
            })

    return pd.DataFrame(records)


# ── IBGE API internals ────────────────────────────────────────────────────────

def _norm(name: str) -> str:
    """Normalize accents and case for fuzzy name matching."""
    return (
        unicodedata.normalize("NFD", name)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def _ibge_get(url: str, timeout: int = 15) -> object | None:
    """GET request to IBGE API; returns None on any failure.

    Handles gzip-encoded responses automatically — the IBGE API may return
    Content-Encoding: gzip regardless of the Accept-Encoding header sent.
    """
    try:
        req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return json.loads(gzip.decompress(raw))
    except Exception as exc:
        log.warning("IBGE API request failed (%s): %s", url[:70], exc)
        return None


def _polygon_centroid(rings: list) -> tuple[float, float]:
    """Centroid from mean coordinates of a GeoJSON polygon exterior ring."""
    coords = np.array(rings[0])  # [[lon, lat], ...]
    return float(coords[:, 1].mean()), float(coords[:, 0].mean())  # lat, lon


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    from src.explore_test_data_south_sc.utils import make_output_dirs
    from src.explore_test_data_south_sc.io import (
        load_glorys_data, load_reported_events, load_wave_data,
    )

    make_output_dirs()

    _ds_wave   = load_wave_data()
    _ds_gl     = load_glorys_data()
    _df_events = load_reported_events()

    run_municipality_grid_association(_df_events, _ds_wave, _ds_gl)
