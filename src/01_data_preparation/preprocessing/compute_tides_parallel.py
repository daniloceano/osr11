"""
Parallel FES2022 tide computation for preprocessing.

Computes daily-maximum FES2022 tides and SSH_total for all coastal grid
points in the unified metocean dataset. Designed for production runs on
multi-core servers (tested with up to 110 cores).

This module reuses the FES2022 evaluation logic from Step 2c
(``src.tidal_sensitivity.tides``) and wraps it in a multiprocessing
pool for embarrassingly parallel execution across grid points.

Scientific definition (canonical, inherited from Step 2c):
    tide_daily_max(d) = max(FES2022(d 00:00), FES2022(d 01:00), ..., FES2022(d 23:00))
    SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)

Architecture:
    - Each worker computes the full 1993–2025 tidal time series at one
      grid point (~12,000 hourly evaluations × 33 years).
    - Workers are independent (no shared state beyond the tide model files).
    - Results are collected in the main process and assembled into an
      xarray DataArray.
    - Failed grid points are logged and produce NaN in the output.
    - The function returns partial results even if some workers fail.

Caching / resumability:
    - If a tide cache file exists on disk, it is loaded instead of
      recomputing. This allows restarting after partial failures.
    - The cache is a single NetCDF file with tide_daily_max as a
      3D DataArray (time × latitude × longitude), mostly NaN for
      non-coastal points.
"""
from __future__ import annotations

import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# WORKER FUNCTION (runs in a separate process)
# ══════════════════════════════════════════════════════════════════════════════


def _compute_tide_for_point(
    lat: float,
    lon: float,
    time_start: str,
    time_end: str,
    tide_model: str,
    tide_model_dir: str,
) -> dict[str, Any]:
    """Compute FES2022 daily-max tide at a single grid point.

    This function runs in a child process. It imports eo_tides lazily
    and performs the full hourly→daily-max reduction.

    Parameters
    ----------
    lat, lon : float
        Grid point coordinates.
    time_start, time_end : str
        ISO date strings delimiting the time range.
    tide_model : str
        Tide model name (e.g. "FES2022").
    tide_model_dir : str
        Path to the tide model directory.

    Returns
    -------
    dict with keys: lat, lon, status, values (list of floats or None),
    dates (list of ISO date strings).
    """
    try:
        from eo_tides.model import model_tides

        # Build hourly time index for the full period
        daily_index = pd.date_range(time_start, time_end, freq="D")
        hourly_start = pd.Timestamp(time_start)
        hourly_end = pd.Timestamp(time_end) + pd.Timedelta("23h")
        hourly_index = pd.date_range(hourly_start, hourly_end, freq="h")

        # Evaluate FES2022 at hourly resolution
        result = model_tides(
            x=float(lon),
            y=float(lat),
            model=[tide_model],
            time=hourly_index,
            directory=tide_model_dir,
        )
        tide_hourly = result["tide_height"].droplevel(["x", "y"])

        # Resample to daily maximum
        tide_daily_max = tide_hourly.resample("D").max()
        tide_daily_max.index = tide_daily_max.index.normalize()

        # Reindex to exact daily dates
        tide_out = tide_daily_max.reindex(daily_index)

        return {
            "lat": lat,
            "lon": lon,
            "status": "ok",
            "values": tide_out.values.tolist(),
            "dates": [d.isoformat()[:10] for d in daily_index],
        }
    except Exception as exc:
        return {
            "lat": lat,
            "lon": lon,
            "status": "failed",
            "error": str(exc),
            "values": None,
            "dates": None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# COASTAL GRID IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════


def identify_coastal_points_for_tides(
    ds: xr.Dataset,
    coastline_shp: str | Path,
    max_dist_km: float = 50.0,
    hs_var: str = "VHM0",
) -> list[tuple[float, float]]:
    """Identify ocean grid points within max_dist_km of the coastline.

    Uses the same Natural Earth coastline + KDTree logic as Step 2a.

    Returns
    -------
    list of (lat, lon) tuples for coastal grid points.
    """
    from src.exploratory_data_analysis.coastal import find_coastal_points

    lat = ds.latitude.values
    lon = ds.longitude.values
    data_mean = ds[hs_var].mean(dim="time").values

    coastal_mask, _ = find_coastal_points(
        lat, lon, data_mean, Path(coastline_shp), max_dist_km=max_dist_km,
    )

    points = []
    coast_idx = np.argwhere(coastal_mask)
    for i_lat, i_lon in coast_idx:
        points.append((float(lat[i_lat]), float(lon[i_lon])))

    log.info(
        "Identified %d coastal grid points for tide computation "
        "(within %.0f km of coastline)",
        len(points), max_dist_km,
    )
    return points


# ══════════════════════════════════════════════════════════════════════════════
# PARALLEL ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════


def compute_tides_parallel(
    ds: xr.Dataset,
    coastal_points: list[tuple[float, float]],
    tide_model: str = "FES2022",
    tide_model_dir: str = "data/tide_models_clipped_brasil",
    max_workers: int = 4,
    cache_path: Path | None = None,
) -> xr.DataArray:
    """Compute FES2022 daily-max tides for all coastal grid points in parallel.

    Parameters
    ----------
    ds : xr.Dataset
        Unified dataset (used only for coordinate grids and time range).
    coastal_points : list of (lat, lon)
        Grid points for which to compute tides.
    tide_model : str
        Tide model name.
    tide_model_dir : str
        Path to tide model files.
    max_workers : int
        Number of parallel processes.
    cache_path : Path or None
        If set, save/load the tide cache as a NetCDF file for resumability.

    Returns
    -------
    xr.DataArray
        ``tide_daily_max`` with dims (time, latitude, longitude).
        Non-coastal points are NaN.
    """
    time_index = pd.DatetimeIndex(ds.time.values)
    time_start = str(time_index[0])[:10]
    time_end = str(time_index[-1])[:10]
    n_days = len(time_index)

    lat_vals = ds.latitude.values
    lon_vals = ds.longitude.values

    # ── Check cache ───────────────────────────────────────────────────────
    if cache_path and cache_path.exists():
        log.info("Loading tide cache from %s", cache_path)
        da_cache = xr.open_dataarray(cache_path)
        # Check which points still need computation
        already_done = set()
        for pt_lat, pt_lon in coastal_points:
            i_lat = int(np.argmin(np.abs(lat_vals - pt_lat)))
            i_lon = int(np.argmin(np.abs(lon_vals - pt_lon)))
            if not np.all(np.isnan(da_cache.values[:, i_lat, i_lon])):
                already_done.add((pt_lat, pt_lon))
        remaining = [p for p in coastal_points if p not in already_done]
        log.info(
            "Cache has %d/%d points. %d remaining.",
            len(already_done), len(coastal_points), len(remaining),
        )
        if not remaining:
            return da_cache
    else:
        remaining = list(coastal_points)
        da_cache = None

    # ── Initialize output array ───────────────────────────────────────────
    if da_cache is not None:
        tide_data = da_cache.values.copy()
    else:
        tide_data = np.full(
            (n_days, len(lat_vals), len(lon_vals)),
            np.nan,
            dtype=np.float32,
        )

    # ── Submit parallel tasks ─────────────────────────────────────────────
    n_pts = len(remaining)
    log.info(
        "Computing FES2022 daily-max tides: %d grid points × %d days "
        "(%d workers, %s backend)",
        n_pts, n_days, max_workers, "multiprocessing",
    )

    completed = 0
    failed = 0

    # Use spawn context for clean process isolation
    ctx = mp.get_context("spawn")

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as pool:
        futures = {}
        for pt_lat, pt_lon in remaining:
            fut = pool.submit(
                _compute_tide_for_point,
                lat=pt_lat,
                lon=pt_lon,
                time_start=time_start,
                time_end=time_end,
                tide_model=tide_model,
                tide_model_dir=tide_model_dir,
            )
            futures[fut] = (pt_lat, pt_lon)

        for fut in as_completed(futures):
            pt_lat, pt_lon = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:
                log.error("Worker crashed for (%.4f, %.4f): %s", pt_lat, pt_lon, exc)
                failed += 1
                continue

            completed += 1
            if completed % max(1, n_pts // 20) == 0:
                log.info(
                    "  Progress: %d/%d completed (%d failed)",
                    completed, n_pts, failed,
                )

            if result["status"] == "ok":
                i_lat = int(np.argmin(np.abs(lat_vals - pt_lat)))
                i_lon = int(np.argmin(np.abs(lon_vals - pt_lon)))
                tide_data[:, i_lat, i_lon] = np.array(
                    result["values"], dtype=np.float32
                )
            else:
                log.warning(
                    "Tide failed at (%.4f, %.4f): %s",
                    pt_lat, pt_lon, result.get("error", "unknown"),
                )
                failed += 1

    log.info(
        "Tide computation complete: %d/%d ok, %d failed",
        completed - failed, n_pts, failed,
    )

    # ── Build DataArray ───────────────────────────────────────────────────
    da = xr.DataArray(
        tide_data,
        dims=("time", "latitude", "longitude"),
        coords={
            "time": time_index,
            "latitude": lat_vals,
            "longitude": lon_vals,
        },
        name="tide_daily_max",
        attrs={
            "long_name": "FES2022 daily-maximum astronomical tide height",
            "units": "m",
            "tide_model": tide_model,
            "computation_method": (
                "FES2022 evaluated at hourly resolution (00:00-23:00 UTC); "
                "daily maximum retained per calendar day"
            ),
            "note": "NaN for non-coastal / non-ocean grid points",
        },
    )

    # ── Save cache ────────────────────────────────────────────────────────
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        encoding = {"tide_daily_max": {"zlib": True, "complevel": 4}}
        da.to_netcdf(cache_path, encoding=encoding)
        log.info("Tide cache saved to %s", cache_path)

    return da


# ══════════════════════════════════════════════════════════════════════════════
# SSH_TOTAL COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════


def compute_ssh_total(
    ds: xr.Dataset,
    tide_da: xr.DataArray,
    zos_var: str = "zos",
) -> xr.DataArray:
    """Compute SSH_total = zos + tide_daily_max.

    Parameters
    ----------
    ds : xr.Dataset
        Unified dataset containing ``zos``.
    tide_da : xr.DataArray
        Daily-max tide heights (time × latitude × longitude).
    zos_var : str
        Name of the sea surface height variable.

    Returns
    -------
    xr.DataArray
        SSH_total with same dims as input.
    """
    log.info("Computing SSH_total = %s + tide_daily_max", zos_var)

    zos = ds[zos_var]
    ssh_total = zos + tide_da

    ssh_total.name = "SSH_total"
    ssh_total.attrs = {
        "long_name": "Total sea surface height (ocean + astronomical tide)",
        "units": "m",
        "definition": f"SSH_total = {zos_var}(00:00 UTC) + tide_daily_max",
        "zos_source": "GLORYS12 daily reanalysis (00:00 UTC snapshot)",
        "tide_source": "FES2022 daily maximum (hourly evaluation, daily max retained)",
        "limitation": (
            "zos is a 00:00 UTC snapshot; tide_daily_max is the daily maximum "
            "which may occur at a different time. SSH_total therefore combines "
            "two non-simultaneous quantities — an accepted approximation "
            "inherent to GLORYS12's daily-only output."
        ),
    }

    n_valid = int((~np.isnan(ssh_total.values)).sum())
    n_total = int(ssh_total.size)
    log.info(
        "SSH_total computed: %d/%d valid values (%.1f%%)",
        n_valid, n_total, 100.0 * n_valid / max(n_total, 1),
    )

    return ssh_total
