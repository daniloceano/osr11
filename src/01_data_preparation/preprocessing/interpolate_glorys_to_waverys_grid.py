"""
Interpolate GLORYS sea level (zos) to the WAVERYS spatial grid and build a
unified metocean dataset for compound-event analysis.

Why this step exists
--------------------
GLORYS12 (~1/12°, daily) and WAVERYS (~0.2°, 3-hourly) come on different spatial
grids.  Before any joint analysis they must share a common grid.  WAVERYS is
chosen as the target because it is the coarser product: interpolating the finer
GLORYS onto the coarser WAVERYS grid avoids spurious spatial detail and is
computationally inexpensive.

Temporal alignment
------------------
GLORYS is daily.  WAVERYS is 3-hourly and is resampled to daily (mean or max,
configurable) before merging.  Only days present in **both** datasets are kept
(temporal intersection).

Spatial interpolation
---------------------
Uses ``xarray.DataArray.interp`` with the WAVERYS lat/lon coordinates as
targets.  The GLORYS domain fully contains the WAVERYS grid, so no extrapolation
is needed.  Boundary behaviour is therefore safe with ``fill_value=None``
(scipy linear).

Usage
-----
python -m src.preprocessing.interpolate_glorys_to_waverys_grid \
    --config config/preprocessing/glorys_to_waverys_test.yaml
"""

from __future__ import annotations

import argparse
import glob
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(path: str | Path) -> dict:
    """Load and return the YAML configuration file."""
    with open(path) as fh:
        cfg = yaml.safe_load(fh)
    log.info("Config loaded from %s", path)
    return cfg


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def _resolve_input_files(path_spec: str | Path) -> list[Path]:
    """Resolve a path specification to a sorted list of NetCDF files.

    Supports three forms:
    - A single .nc file:  "/data/raw/glorys_brazil_full.nc"
    - A glob pattern:     "/data/raw/glorys/glorys_zos_????.nc"
                          "/data/raw/glorys/glorys_zos_*.nc"
    - A directory:        "/data/raw/glorys/"  (auto-discovers *.nc files)

    Duplicated downloads (files with '_(1)' suffix) are automatically excluded.
    """
    p = Path(path_spec)

    if p.is_dir():
        files = sorted(p.glob("*.nc"))
    elif "*" in str(p) or "?" in str(p):
        files = sorted(Path(f) for f in glob.glob(str(p)))
    elif p.is_file():
        return [p]
    else:
        raise FileNotFoundError(
            f"Input path not found: {path_spec!r}.  "
            f"Expected a file, directory, or glob pattern."
        )

    # Exclude duplicate downloads from CMEMS (e.g. *_(1).nc, *_(2).nc)
    files = [f for f in files if "_(" not in f.name]

    if not files:
        raise FileNotFoundError(
            f"No NetCDF files found matching: {path_spec!r}"
        )

    return files


def _open_dataset(path_spec: str | Path, label: str) -> xr.Dataset:
    """Open one or many NetCDF files as a single xarray Dataset.

    For multiple files, uses ``xr.open_mfdataset`` with ``combine='by_coords'``
    which handles concatenation along the time dimension automatically.
    """
    files = _resolve_input_files(path_spec)

    if len(files) == 1:
        log.info("Loading %s from single file: %s", label, files[0])
        return xr.open_dataset(files[0])
    else:
        log.info(
            "Loading %s from %d files: %s … %s",
            label, len(files), files[0].name, files[-1].name,
        )
        ds = xr.open_mfdataset(
            [str(f) for f in files],
            combine="by_coords",
            data_vars="minimal",
            coords="minimal",
            compat="override",
        )
        log.info("  Concatenated %s: %s", label, dict(ds.sizes))
        return ds


def load_glorys(path: str | Path, var: str) -> xr.Dataset:
    """Open GLORYS file(s) and keep only *var* (sea-level variable).

    Supports single file, glob pattern, or directory of monthly NetCDFs.
    """
    log.info("Loading GLORYS from %s  [var=%s]", path, var)
    ds = _open_dataset(path, label="GLORYS")
    _check_variable(ds, var, label="GLORYS")
    return ds[[var]]


def load_waverys(path: str | Path, var_hs: str, var_dir: str) -> xr.Dataset:
    """Open WAVERYS file(s) and keep *var_hs* and *var_dir*.

    Supports single file, glob pattern, or directory of monthly NetCDFs.
    """
    log.info("Loading WAVERYS from %s  [vars=%s, %s]", path, var_hs, var_dir)
    ds = _open_dataset(path, label="WAVERYS")
    _check_variable(ds, var_hs, label="WAVERYS")
    _check_variable(ds, var_dir, label="WAVERYS")
    return ds[[var_hs, var_dir]]


def _check_variable(ds: xr.Dataset, var: str, label: str) -> None:
    """Raise a clear error if *var* is not in *ds*."""
    if var not in ds:
        available = list(ds.data_vars)
        raise KeyError(
            f"{label}: variable '{var}' not found.  "
            f"Available: {available}"
        )


# ---------------------------------------------------------------------------
# Temporal alignment
# ---------------------------------------------------------------------------

def resample_waverys_daily(ds: xr.Dataset, method: str) -> xr.Dataset:
    """Resample WAVERYS from 3-hourly to daily.

    Uses a numpy/pandas groupby approach instead of ``xarray.resample``
    for performance: loading 93 k timestamps via xarray GroupBy is extremely
    slow (~20 min), whereas the numpy path completes in ~10 s.

    Parameters
    ----------
    method:
        'mean' — daily mean (suited for climatology).
        'max'  — daily maximum (suited for extremes / compound events).

    Notes
    -----
    When ``method='max'``, the same aggregation is applied to all WAVERYS
    variables, including VMDR (mean wave direction).  Taking the maximum of
    a directional variable is not physically meaningful; however, VMDR is not
    used by any downstream analysis step (Step 3b only uses VHM0).  The choice
    to aggregate VMDR with the same method avoids per-variable branching in
    the preprocessing pipeline and has no practical effect on results.
    """
    if method not in ("mean", "max"):
        raise ValueError(f"resample_method must be 'mean' or 'max', got '{method}'")

    log.info("Loading WAVERYS into memory …")
    ds = ds.load()

    log.info("Resampling WAVERYS to daily (%s) …", method)

    dates = pd.DatetimeIndex(ds.time.values).normalize()  # floor to day
    daily_idx = pd.DatetimeIndex(sorted(set(dates)))

    agg = np.mean if method == "mean" else np.max

    data_vars: dict[str, xr.DataArray] = {}
    for var in ds.data_vars:
        raw = ds[var].values  # shape: (time, lat, lon)
        daily_data = np.stack(
            [agg(raw[dates == d], axis=0) for d in daily_idx],
            axis=0,
        ).astype(np.float32)
        data_vars[var] = xr.DataArray(
            daily_data,
            dims=("time", "latitude", "longitude"),
            attrs=ds[var].attrs,
        )

    ds_daily = xr.Dataset(
        data_vars,
        coords={
            "time": daily_idx,
            "latitude": ds.latitude,
            "longitude": ds.longitude,
        },
        attrs=ds.attrs,
    )

    log.info("  WAVERYS daily shape: %s", dict(ds_daily.sizes))
    return ds_daily


def temporal_intersection(
    ds_glorys: xr.Dataset,
    ds_waverys: xr.Dataset,
) -> tuple[xr.Dataset, xr.Dataset]:
    """Keep only time steps present in both datasets (inner join on time)."""
    t_g = set(ds_glorys.time.values.astype("datetime64[D]"))
    t_w = set(ds_waverys.time.values.astype("datetime64[D]"))
    common = sorted(t_g & t_w)

    if not common:
        raise ValueError("No common time steps found between GLORYS and WAVERYS.")

    log.info(
        "Temporal intersection: %d days  [%s → %s]",
        len(common),
        str(common[0])[:10],
        str(common[-1])[:10],
    )

    ds_g = ds_glorys.sel(time=ds_glorys.time.dt.floor("D").isin(common))
    ds_w = ds_waverys.sel(time=ds_waverys.time.dt.floor("D").isin(common))
    return ds_g, ds_w


# ---------------------------------------------------------------------------
# Spatial interpolation
# ---------------------------------------------------------------------------

def interpolate_glorys_to_waverys_grid(
    ds_glorys: xr.Dataset,
    ds_waverys: xr.Dataset,
    method: str,
) -> xr.Dataset:
    """Interpolate GLORYS onto the WAVERYS lat/lon grid.

    Uses ``xarray.Dataset.interp``.  Both datasets must share coordinate names
    'latitude' and 'longitude'.
    """
    log.info(
        "Interpolating GLORYS (%s) → WAVERYS grid (%s) using method='%s' …",
        _grid_str(ds_glorys),
        _grid_str(ds_waverys),
        method,
    )

    target_lat = ds_waverys.latitude
    target_lon = ds_waverys.longitude

    # Verify GLORYS domain contains WAVERYS grid (no extrapolation needed)
    _check_coverage(ds_glorys, target_lat, target_lon)

    ds_interp = ds_glorys.interp(
        latitude=target_lat,
        longitude=target_lon,
        method=method,
        kwargs={"fill_value": None},  # allow slight extrapolation at exact edges
    )

    log.info("  Interpolated GLORYS grid: %s", dict(ds_interp.sizes))
    return ds_interp


def _check_coverage(
    ds_src: xr.Dataset,
    target_lat: xr.DataArray,
    target_lon: xr.DataArray,
) -> None:
    """Warn if target grid points fall outside the source domain."""
    lat_ok = (
        float(target_lat.min()) >= float(ds_src.latitude.min()) - 0.01
        and float(target_lat.max()) <= float(ds_src.latitude.max()) + 0.01
    )
    lon_ok = (
        float(target_lon.min()) >= float(ds_src.longitude.min()) - 0.01
        and float(target_lon.max()) <= float(ds_src.longitude.max()) + 0.01
    )
    if not (lat_ok and lon_ok):
        log.warning(
            "Target grid may extend beyond source domain — extrapolation will occur.  "
            "Source lat [%.3f, %.3f], lon [%.3f, %.3f] | "
            "Target lat [%.3f, %.3f], lon [%.3f, %.3f]",
            float(ds_src.latitude.min()), float(ds_src.latitude.max()),
            float(ds_src.longitude.min()), float(ds_src.longitude.max()),
            float(target_lat.min()), float(target_lat.max()),
            float(target_lon.min()), float(target_lon.max()),
        )


def _grid_str(ds: xr.Dataset) -> str:
    """Return compact grid description string."""
    return (
        f"lat=[{float(ds.latitude.min()):.2f},{float(ds.latitude.max()):.2f}]"
        f" lon=[{float(ds.longitude.min()):.2f},{float(ds.longitude.max()):.2f}]"
        f" n={ds.sizes.get('latitude')}×{ds.sizes.get('longitude')}"
    )


# ---------------------------------------------------------------------------
# Build unified dataset
# ---------------------------------------------------------------------------

def build_unified_dataset(
    ds_glorys_interp: xr.Dataset,
    ds_waverys_daily: xr.Dataset,
    var_zos: str,
    var_hs: str,
    var_dir: str,
    interp_method: str,
    resample_method: str,
) -> xr.Dataset:
    """Merge interpolated GLORYS and resampled WAVERYS into one dataset."""
    log.info("Merging variables into unified dataset …")

    # Align time coordinates (floor to day to ensure exact match)
    ds_g = ds_glorys_interp.assign_coords(
        time=ds_glorys_interp.time.dt.floor("D")
    )
    ds_w = ds_waverys_daily.assign_coords(
        time=ds_waverys_daily.time.dt.floor("D")
    )

    ds_unified = xr.merge([ds_w[[var_hs, var_dir]], ds_g[[var_zos]]])

    # Cast to float32 (safe: all source vars are float32)
    for var in [var_zos, var_hs, var_dir]:
        if ds_unified[var].dtype != np.float32:
            ds_unified[var] = ds_unified[var].astype(np.float32)

    # Global attributes
    _hs_desc = (
        "daily maximum from 3-hourly WAVERYS"
        if resample_method == "max"
        else "daily mean from 3-hourly WAVERYS"
    )
    _zos_desc = "daily snapshot at 00:00 UTC from GLORYS12 (daily product; sub-daily SSH not available)"

    ds_unified.attrs = {
        "title": "Unified metocean dataset — WAVERYS spatial grid",
        "description": (
            "GLORYS12 sea surface height (zos) interpolated to the WAVERYS grid. "
            "WAVERYS wave variables resampled to daily resolution. "
            "Intended for compound coastal-event analysis."
        ),
        "glorys_source": "CMEMS GLOBAL_MULTIYEAR_PHY_001_030 (GLORYS12)",
        "waverys_source": "CMEMS GLOBAL_MULTIYEAR_WAV_001_032 (WAVERYS/MFWAM)",
        "spatial_grid": "WAVERYS (~0.2° resolution)",
        "interpolation_method": interp_method,
        "temporal_resample_method": f"WAVERYS resampled to daily ({resample_method})",
        "temporal_strategy": "Temporal intersection of GLORYS (daily) and WAVERYS (daily after resample)",
        "VHM0_temporal_convention": _hs_desc,
        "zos_temporal_convention": _zos_desc,
        "zos_limitation": (
            "GLORYS12 is a daily ocean reanalysis with one snapshot per day at 00:00 UTC. "
            "Daily-maximum SSH cannot be derived from this product. "
            "Sub-daily SSH data would require a different source (e.g., hourly CMEMS NRT product)."
        ),
        "Conventions": "CF-1.6",
    }

    log.info("  Unified dataset variables: %s", list(ds_unified.data_vars))
    log.info("  Unified dataset sizes: %s", dict(ds_unified.sizes))
    return ds_unified


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_dataset(ds: xr.Dataset, path: str | Path) -> None:
    """Save dataset to NetCDF with lossless compression."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    encoding = {
        var: {"zlib": True, "complevel": 4}
        for var in ds.data_vars
    }

    log.info("Saving unified dataset to %s …", path)
    ds.to_netcdf(path, encoding=encoding)
    log.info("  Saved: %.1f MB", path.stat().st_size / 1e6)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(
    cfg: dict,
    ds: xr.Dataset,
    var_zos: str,
    var_hs: str,
    var_dir: str,
) -> None:
    """Print a compact summary of the processing run."""
    time_start = str(ds.time.values[0])[:10]
    time_end = str(ds.time.values[-1])[:10]
    n_days = ds.sizes["time"]
    lat_res = float(np.diff(ds.latitude.values).mean())
    lon_res = float(np.diff(ds.longitude.values).mean())

    print()
    print("=" * 60)
    print("  UNIFIED METOCEAN DATASET — SUMMARY")
    print("=" * 60)
    print(f"  Input GLORYS   : {cfg['input']['glorys']}")
    print(f"  Input WAVERYS  : {cfg['input']['waverys']}")
    print(f"  Output file    : {cfg['output']['file']}")
    print()
    print(f"  Variables")
    print(f"    {var_zos:12s}  sea surface height (from GLORYS, interpolated)")
    print(f"    {var_hs:12s}  significant wave height (from WAVERYS, daily {cfg['temporal']['resample_method']})")
    print(f"    {var_dir:12s}  mean wave direction (from WAVERYS, daily {cfg['temporal']['resample_method']})")
    print()
    print(f"  Interpolation method  : {cfg['interpolation']['method']}")
    print(f"  Temporal resample     : WAVERYS 3-hourly → daily ({cfg['temporal']['resample_method']})")
    print(f"  Temporal strategy     : intersection (inner join on daily timestamps)")
    print()
    print(f"  Final temporal range  : {time_start} → {time_end}  ({n_days} days)")
    print(f"  Final grid (WAVERYS)  : {ds.sizes['latitude']} lat × {ds.sizes['longitude']} lon")
    print(f"  Grid spacing          : Δlat ≈ {lat_res:.3f}°  Δlon ≈ {lon_res:.3f}°")
    print(f"  Lat range             : {float(ds.latitude.min()):.2f}° → {float(ds.latitude.max()):.2f}°")
    print(f"  Lon range             : {float(ds.longitude.min()):.2f}° → {float(ds.longitude.max()):.2f}°")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(config_path: str | Path) -> None:
    """Run the full interpolation pipeline.

    If the config includes a ``tides`` section with ``enabled: true``,
    FES2022 daily-max tides and SSH_total are computed and added to the
    unified dataset. This is the recommended production workflow — it
    eliminates the tide computation bottleneck from Step 3.
    """
    cfg = load_config(config_path)

    var_zos = cfg["variables"]["glorys_sea_level"]
    var_hs = cfg["variables"]["waverys_wave_height"]
    var_dir = cfg["variables"]["waverys_wave_direction"]
    interp_method = cfg["interpolation"]["method"]
    resample_method = cfg["temporal"]["resample_method"]

    # 1. Load
    ds_glorys = load_glorys(cfg["input"]["glorys"], var_zos)
    ds_waverys = load_waverys(cfg["input"]["waverys"], var_hs, var_dir)

    # 2. Temporal alignment
    ds_waverys_daily = resample_waverys_daily(ds_waverys, resample_method)
    ds_glorys, ds_waverys_daily = temporal_intersection(ds_glorys, ds_waverys_daily)

    # 3. Spatial interpolation (GLORYS → WAVERYS grid)
    ds_glorys_interp = interpolate_glorys_to_waverys_grid(
        ds_glorys, ds_waverys_daily, interp_method
    )

    # 4. Build unified dataset
    ds_unified = build_unified_dataset(
        ds_glorys_interp,
        ds_waverys_daily,
        var_zos=var_zos,
        var_hs=var_hs,
        var_dir=var_dir,
        interp_method=interp_method,
        resample_method=resample_method,
    )

    # 5. Optional: compute FES2022 tides and SSH_total
    tides_cfg = cfg.get("tides", {})
    if tides_cfg.get("enabled", False):
        ds_unified = _add_tides_and_ssh_total(ds_unified, tides_cfg, var_zos, var_hs)

    save_dataset(ds_unified, cfg["output"]["file"])
    print_summary(cfg, ds_unified, var_zos, var_hs, var_dir)


def _add_tides_and_ssh_total(
    ds: xr.Dataset,
    tides_cfg: dict,
    var_zos: str,
    var_hs: str,
) -> xr.Dataset:
    """Compute FES2022 tides and SSH_total, adding them to the dataset.

    This is the production-mode preprocessing step that pre-computes
    tides so Step 3 can consume SSH_total directly from the NetCDF.
    """
    from .compute_tides_parallel import (
        compute_ssh_total,
        compute_tides_parallel,
        identify_coastal_points_for_tides,
    )
    from datetime import datetime, timezone

    log.info("=" * 60)
    log.info("TIDE COMPUTATION — adding tide_daily_max and SSH_total")
    log.info("=" * 60)

    tide_model = tides_cfg.get("model", "FES2022")
    tide_model_dir = tides_cfg.get("model_dir", "data/tide_models_clipped_brasil")
    coastline_shp = tides_cfg.get("coastline_shp", "data/ne_10m_coastline/ne_10m_coastline.shp")
    max_dist_km = tides_cfg.get("coastal_max_dist_km", 50.0)

    par_cfg = tides_cfg.get("parallel", {})
    max_workers = par_cfg.get("max_workers", 4)

    out_vars = tides_cfg.get("output_vars", {})
    tide_var_name = out_vars.get("tide_daily_max", "tide_daily_max")
    ssh_total_var_name = out_vars.get("ssh_total", "SSH_total")

    # Cache path — adjacent to output file
    output_dir = Path(ds.encoding.get("source", "")).parent if ds.encoding.get("source") else Path(".")
    cache_path = Path("data/cache/tide_daily_max_cache.nc")

    # Identify coastal grid points
    coastal_points = identify_coastal_points_for_tides(
        ds, coastline_shp, max_dist_km=max_dist_km, hs_var=var_hs,
    )

    # Compute tides in parallel
    tide_da = compute_tides_parallel(
        ds=ds,
        coastal_points=coastal_points,
        tide_model=tide_model,
        tide_model_dir=tide_model_dir,
        max_workers=max_workers,
        cache_path=cache_path,
    )

    # Compute SSH_total
    ssh_total_da = compute_ssh_total(ds, tide_da, zos_var=var_zos)

    # Add to dataset
    ds[tide_var_name] = tide_da
    ds[ssh_total_var_name] = ssh_total_da.astype(np.float32)

    # Update global attributes
    ds.attrs["tide_computation"] = (
        f"{tide_model} daily-max tides pre-computed at "
        f"{len(coastal_points)} coastal grid points"
    )
    ds.attrs["SSH_total_definition"] = (
        f"SSH_total = {var_zos}(00:00 UTC) + tide_daily_max"
    )
    ds.attrs["tide_precomputed"] = "true"
    ds.attrs["tide_model"] = tide_model
    ds.attrs["tide_computation_date"] = datetime.now(timezone.utc).isoformat()

    log.info(
        "Added %s and %s to unified dataset (%d coastal points)",
        tide_var_name, ssh_total_var_name, len(coastal_points),
    )
    return ds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interpolate GLORYS to WAVERYS grid and build unified metocean dataset."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML configuration file (e.g. config/preprocessing/glorys_to_waverys_test.yaml)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Override max_workers for parallel tide computation (production mode).",
    )
    args = parser.parse_args()

    # Allow CLI to override tide workers
    if args.workers:
        _cfg = load_config(args.config)
        if "tides" in _cfg:
            _cfg.setdefault("tides", {}).setdefault("parallel", {})["max_workers"] = args.workers
            # Re-save won't work with YAML roundtrip, so we patch at runtime:
            import functools
            _original_load = load_config
            load_config = functools.wraps(_original_load)(lambda p: _cfg)

    try:
        main(args.config)
    except Exception as exc:
        log.error("Pipeline failed: %s", exc)
        sys.exit(1)
