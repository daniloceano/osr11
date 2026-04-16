"""
I/O helpers for Step 3 — Storm Catalog Generation.

Handles loading inputs (thresholds, unified dataset, municipality reference,
coastal grid points) and saving outputs (JSON catalogs, CSV summaries,
run metadata).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from src.exploratory_data_analysis.coastal import find_coastal_points

from ..config import analysis_config as cfg

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# INPUT LOADING
# ══════════════════════════════════════════════════════════════════════════════


def load_optimal_thresholds(path: Path | None = None) -> dict[str, float]:
    """Load the PU-optimal threshold pair from Step 2e output.

    Returns
    -------
    dict with keys ``thr_hs_pct`` and ``thr_ssh_pct`` (float, e.g. 0.90).
    """
    path = path or cfg.OPTIMAL_PAIR_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"Step 2e optimal pair file not found: {path}\n"
            "Run Step 2e first or verify the path in config/analysis_config.py."
        )
    df = pd.read_csv(path)
    required_cols = {"thr_hs_pct", "thr_ssh_pct"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing columns in {path.name}: {missing}. "
            f"Found: {list(df.columns)}"
        )
    if len(df) != 1:
        raise ValueError(
            f"Expected 1 row in {path.name}, found {len(df)}."
        )
    row = df.iloc[0]
    thr_hs = float(row["thr_hs_pct"])
    thr_ssh = float(row["thr_ssh_pct"])

    if not (0.5 <= thr_hs <= 1.0):
        raise ValueError(f"thr_hs_pct={thr_hs} outside valid range [0.5, 1.0]")
    if not (0.5 <= thr_ssh <= 1.0):
        raise ValueError(f"thr_ssh_pct={thr_ssh} outside valid range [0.5, 1.0]")

    log.info(
        "Loaded thresholds from %s: thr_hs_pct=%.4f, thr_ssh_pct=%.4f",
        path.name, thr_hs, thr_ssh,
    )
    return {"thr_hs_pct": thr_hs, "thr_ssh_pct": thr_ssh}


def load_unified_dataset(path: Path | None = None) -> xr.Dataset:
    """Load the unified metocean NetCDF dataset.

    Validates presence of required variables (VHM0, zos) and expected
    dimensions (time, latitude, longitude).
    """
    path = path or cfg.UNIFIED_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"Unified dataset not found: {path}\n"
            f"Current RUN_MODE={cfg.RUN_MODE!r}. "
            "Set RUN_MODE='test' for SC fixture or produce the full-domain "
            "dataset first."
        )
    ds = xr.open_dataset(path, chunks=None)  # load eagerly for daily data

    # Validate variables
    for var in (cfg.HS_VAR, cfg.SSH_VAR):
        if var not in ds.data_vars:
            raise ValueError(
                f"Required variable '{var}' not found in {path.name}. "
                f"Available: {list(ds.data_vars)}"
            )

    # Validate dimensions
    for dim in ("time", "latitude", "longitude"):
        if dim not in ds.dims:
            raise ValueError(
                f"Required dimension '{dim}' not found in {path.name}. "
                f"Available: {list(ds.dims)}"
            )

    log.info(
        "Loaded unified dataset: %s | %d time steps | lat [%.2f, %.2f] | "
        "lon [%.2f, %.2f]",
        path.name,
        ds.dims["time"],
        float(ds.latitude.min()), float(ds.latitude.max()),
        float(ds.longitude.min()), float(ds.longitude.max()),
    )
    return ds


def load_municipality_grid_ref(
    path: Path | None = None,
) -> pd.DataFrame:
    """Load the municipality–grid reference CSV (SC domain, optional QA).

    Returns DataFrame with columns including grid_lat, grid_lon, municipality.
    """
    path = path or cfg.MUNICIPALITY_GRID_REF
    if not path.exists():
        log.warning("Municipality grid ref not found: %s (optional)", path)
        return pd.DataFrame()
    df = pd.read_csv(path)
    log.info(
        "Loaded municipality grid ref: %d municipalities from %s",
        len(df), path.name,
    )
    return df


def identify_coastal_grid_points(
    ds: xr.Dataset,
    max_dist_km: float | None = None,
    min_valid_frac: float | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Identify valid coastal ocean grid points from the unified dataset.

    Uses the Natural Earth 10m coastline + KDTree approach from Step 2a
    (``coastal.find_coastal_points``).

    Returns
    -------
    DataFrame with columns: grid_lat, grid_lon, hs_valid_frac, ssh_valid_frac,
    dist_to_coast_km.  One row per valid coastal grid point.
    """
    max_dist_km = max_dist_km or cfg.COASTAL_MAX_DIST_KM
    min_valid_frac = min_valid_frac or cfg.MIN_VALID_FRAC

    lat = ds.latitude.values
    lon = ds.longitude.values

    # Temporal mean of Hs to identify valid ocean cells
    hs_mean = ds[cfg.HS_VAR].mean(dim="time").values
    ssh_mean = ds[cfg.SSH_VAR].mean(dim="time").values

    # Use Hs mean to define valid ocean mask (non-NaN)
    # Both variables should have similar coverage, but Hs is the primary
    coastal_mask, dist_to_coast = find_coastal_points(
        lat, lon, hs_mean, cfg.COASTLINE_SHP, max_dist_km=max_dist_km,
    )

    # Collect coastal grid points with valid data fractions
    n_time = ds.dims["time"]
    hs_data = ds[cfg.HS_VAR].values  # (time, lat, lon)
    ssh_data = ds[cfg.SSH_VAR].values

    rows: list[dict] = []
    skipped_nan: list[dict] = []

    coast_idx = np.argwhere(coastal_mask)
    for i_lat, i_lon in coast_idx:
        glat = float(lat[i_lat])
        glon = float(lon[i_lon])
        d_coast = float(dist_to_coast[i_lat, i_lon])

        hs_valid = float(np.count_nonzero(np.isfinite(hs_data[:, i_lat, i_lon])) / n_time)
        ssh_valid = float(np.count_nonzero(np.isfinite(ssh_data[:, i_lat, i_lon])) / n_time)

        record = {
            "grid_lat": glat,
            "grid_lon": glon,
            "hs_valid_frac": round(hs_valid, 4),
            "ssh_valid_frac": round(ssh_valid, 4),
            "dist_to_coast_km": round(d_coast, 2),
        }

        if hs_valid < min_valid_frac or ssh_valid < min_valid_frac:
            record["skip_reason"] = (
                f"hs_valid_frac={hs_valid:.3f}" if hs_valid < min_valid_frac
                else f"ssh_valid_frac={ssh_valid:.3f}"
            )
            skipped_nan.append(record)
        else:
            rows.append(record)

    if skipped_nan:
        log.warning(
            "%d coastal grid points skipped (valid_frac < %.2f): %s",
            len(skipped_nan), min_valid_frac,
            [(r["grid_lat"], r["grid_lon"], r.get("skip_reason")) for r in skipped_nan],
        )

    df = pd.DataFrame(rows)
    log.info(
        "Coastal grid points: %d valid (of %d within %.0f km of coast, %d skipped)",
        len(df), len(coast_idx), max_dist_km, len(skipped_nan),
    )

    return df, skipped_nan


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT SERIALIZATION
# ══════════════════════════════════════════════════════════════════════════════


def make_output_dirs() -> None:
    """Create all output directories."""
    for d in (cfg.OUTPUT_ROOT, cfg.CATALOG_DIR, cfg.TAB_DIR, cfg.FIG_DIR, cfg.LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)
    log.debug("Output directories created under %s", cfg.OUTPUT_ROOT)


def save_catalog_json(
    catalog: list[dict[str, Any]],
    path: Path,
) -> None:
    """Serialize a storm catalog to JSON.

    Parameters
    ----------
    catalog : list of per-grid-point dicts (see README §4.1 for schema).
    path : output file path.
    """

    class _Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, pd.Timestamp):
                return obj.isoformat()[:10]
            return super().default(obj)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(catalog, f, indent=2, cls=_Encoder, ensure_ascii=False)
    size_mb = path.stat().st_size / (1024 * 1024)
    log.info("Saved catalog JSON: %s (%.2f MB, %d grid points)", path.name, size_mb, len(catalog))


def save_catalog_csv(
    catalog: list[dict[str, Any]],
    path: Path,
) -> None:
    """Flatten a storm catalog to a CSV summary table (one row per event)."""
    rows: list[dict] = []
    for entry in catalog:
        glat = entry["grid_lat"]
        glon = entry["grid_lon"]
        muni = entry.get("municipality")
        for storm in entry.get("storms", []):
            row = {
                "grid_lat": glat,
                "grid_lon": glon,
                "municipality": muni,
                "event_id": storm["event_id"],
                "date_start": storm["date_start"],
                "date_end": storm["date_end"],
                "duration_days": storm["duration_days"],
                "peak_value": storm["peak_value"],
                "peak_date": storm["peak_date"],
                "integrated_intensity": storm["integrated_intensity"],
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved catalog CSV: %s (%d storm events)", path.name, len(df))


def save_grid_metadata_csv(
    grid_meta: list[dict[str, Any]],
    path: Path,
) -> None:
    """Save per-grid-point metadata/QA table."""
    df = pd.DataFrame(grid_meta)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved grid metadata CSV: %s (%d grid points)", path.name, len(df))


def save_run_metadata(meta: dict[str, Any], path: Path) -> None:
    """Save run metadata to JSON."""

    class _Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, Path):
                return str(obj)
            return super().default(obj)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(meta, f, indent=2, cls=_Encoder, ensure_ascii=False)
    log.info("Saved run metadata: %s", path.name)
