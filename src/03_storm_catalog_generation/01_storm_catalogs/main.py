"""
Step 3 — Storm Catalog Generation: CLI orchestrator.

Applies PU-optimal thresholds (from Step 2e) to the full 1993–2025 metocean
record to produce independent storm catalogs for Hs and SSH_total at each
coastal grid point.

Usage
-----
    cd <project_root>
    python -m src.03_storm_catalog_generation.01_storm_catalogs.main [--all | --phase PHASE]

Phases
------
    load-validate    Load inputs, identify coastal grid points
    tides            Compute FES2022 daily-max tides and SSH_total
    catalog          Build storm catalogs (thresholds + exceedance + clustering)
    figures          Generate QA figures
    all              Run the full pipeline (default)

See RUN.md for quick-start instructions.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from ..config import analysis_config as cfg

log = logging.getLogger("step3")


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE PHASES
# ══════════════════════════════════════════════════════════════════════════════


def phase_load_validate() -> dict[str, Any]:
    """Phase 1: Load inputs, identify coastal grid points.

    Returns a context dict passed to subsequent phases.
    """
    from . import io as sio

    log.info("=" * 70)
    log.info("PHASE 1 — Load and validate inputs")
    log.info("=" * 70)
    log.info("Run mode: %s", cfg.RUN_MODE)

    # 1. Load thresholds
    thresholds = sio.load_optimal_thresholds()

    # 2. Load unified dataset
    ds = sio.load_unified_dataset()

    # 3. Identify coastal grid points
    coastal_df, skipped = sio.identify_coastal_grid_points(ds)
    if coastal_df.empty:
        log.error("No valid coastal grid points found. Aborting.")
        sys.exit(1)

    # 4. Load municipality reference (optional, for QA labeling)
    muni_df = sio.load_municipality_grid_ref()

    # Build municipality lookup: (grid_lat, grid_lon) → municipality name
    muni_lookup: dict[tuple[float, float], str] = {}
    if not muni_df.empty and "grid_lat" in muni_df.columns:
        for _, row in muni_df.iterrows():
            key = (round(float(row["grid_lat"]), 2), round(float(row["grid_lon"]), 2))
            muni_lookup[key] = row.get("municipality", "")

    log.info(
        "Summary: %d coastal grid points, thresholds hs=q%.0f ssh=q%.0f, "
        "municipality labels for %d points",
        len(coastal_df),
        thresholds["thr_hs_pct"] * 100,
        thresholds["thr_ssh_pct"] * 100,
        len(muni_lookup),
    )

    return {
        "thresholds": thresholds,
        "ds": ds,
        "coastal_df": coastal_df,
        "skipped": skipped,
        "muni_lookup": muni_lookup,
    }


def phase_tides(ctx: dict[str, Any]) -> dict[str, Any]:
    """Phase 2: Resolve SSH_total for all coastal grid points.

    Three modes (controlled by ``cfg.TIDE_MODE``):

    **auto** (default):
        Detect what's in the dataset:
        - If SSH_total exists → use directly (precomputed)
        - Elif tide_daily_max + zos → reconstruct SSH_total
        - Else → compute FES2022 at runtime (legacy)

    **precomputed**:
        Require SSH_total in dataset. Fail if absent.

    **runtime**:
        Always compute FES2022 at runtime (legacy, slow).

    Adds ``ssh_total_cache`` to context: dict mapping (lat, lon) → pd.Series.
    Also sets ``ctx["tide_mode_used"]`` for run metadata.
    """
    log.info("=" * 70)
    log.info("PHASE 2 — Resolve SSH_total (TIDE_MODE=%s)", cfg.TIDE_MODE)
    log.info("=" * 70)

    ds = ctx["ds"]
    coastal_df = ctx["coastal_df"]

    grid_points = list(
        zip(coastal_df["grid_lat"].values, coastal_df["grid_lon"].values)
    )

    # ── Detect available pre-computed variables ───────────────────────────
    has_ssh_total = cfg.SSH_TOTAL_VAR in ds.data_vars
    has_tide_daily_max = cfg.TIDE_DAILY_MAX_VAR in ds.data_vars
    has_zos = cfg.SSH_VAR in ds.data_vars

    log.info(
        "Dataset variables: SSH_total=%s, tide_daily_max=%s, zos=%s",
        has_ssh_total, has_tide_daily_max, has_zos,
    )

    # ── Determine which mode to use ──────────────────────────────────────
    tide_mode = cfg.TIDE_MODE

    if tide_mode == "precomputed":
        if not has_ssh_total:
            log.error(
                "TIDE_MODE='precomputed' but '%s' not found in dataset. "
                "Run preprocessing with tides enabled, or set TIDE_MODE='auto'.",
                cfg.SSH_TOTAL_VAR,
            )
            sys.exit(1)
        mode_used = "precomputed_ssh_total"

    elif tide_mode == "runtime":
        mode_used = "runtime_fes2022"

    elif tide_mode == "auto":
        if has_ssh_total:
            mode_used = "precomputed_ssh_total"
        elif has_tide_daily_max and has_zos:
            mode_used = "reconstructed_from_tide_daily_max"
        else:
            mode_used = "runtime_fes2022"

    else:
        raise ValueError(f"Unknown TIDE_MODE: {tide_mode!r}")

    log.info("SSH_total resolution mode: %s", mode_used)
    ctx["tide_mode_used"] = mode_used

    # ── Execute the chosen mode ──────────────────────────────────────────

    if mode_used == "precomputed_ssh_total":
        ctx = _tides_from_precomputed_ssh_total(ctx, ds, grid_points)

    elif mode_used == "reconstructed_from_tide_daily_max":
        ctx = _tides_from_precomputed_tide(ctx, ds, grid_points)

    elif mode_used == "runtime_fes2022":
        ctx = _tides_from_runtime(ctx, ds, grid_points)

    return ctx


def _tides_from_precomputed_ssh_total(
    ctx: dict[str, Any],
    ds: xr.Dataset,
    grid_points: list[tuple[float, float]],
) -> dict[str, Any]:
    """Extract SSH_total directly from the dataset (fastest production path)."""
    log.info("Using pre-computed SSH_total from unified dataset")

    ssh_total_cache: dict[tuple[float, float], pd.Series] = {}
    failed: list[tuple[float, float]] = []

    for lat, lon in grid_points:
        series = _extract_point_series(ds, cfg.SSH_TOTAL_VAR, lat, lon)
        if series is not None:
            ssh_total_cache[(lat, lon)] = series
        else:
            failed.append((lat, lon))

    ctx["ssh_total_cache"] = ssh_total_cache
    ctx["tide_cache"] = {}
    ctx["tide_failed"] = failed

    log.info(
        "SSH_total loaded for %d/%d grid points (%d failed)",
        len(ssh_total_cache), len(grid_points), len(failed),
    )
    return ctx


def _tides_from_precomputed_tide(
    ctx: dict[str, Any],
    ds: xr.Dataset,
    grid_points: list[tuple[float, float]],
) -> dict[str, Any]:
    """Reconstruct SSH_total from pre-computed tide_daily_max + zos."""
    log.info("Reconstructing SSH_total from tide_daily_max + zos")

    ssh_total_cache: dict[tuple[float, float], pd.Series] = {}
    failed: list[tuple[float, float]] = []

    for lat, lon in grid_points:
        zos = _extract_point_series(ds, cfg.SSH_VAR, lat, lon)
        tide = _extract_point_series(ds, cfg.TIDE_DAILY_MAX_VAR, lat, lon)
        if zos is not None and tide is not None:
            ssh_total = zos + tide
            ssh_total.name = cfg.SSH_TOTAL_VAR
            ssh_total_cache[(lat, lon)] = ssh_total
        else:
            failed.append((lat, lon))

    ctx["ssh_total_cache"] = ssh_total_cache
    ctx["tide_cache"] = {}
    ctx["tide_failed"] = failed

    log.info(
        "SSH_total reconstructed for %d/%d grid points (%d failed)",
        len(ssh_total_cache), len(grid_points), len(failed),
    )
    return ctx


def _tides_from_runtime(
    ctx: dict[str, Any],
    ds: xr.Dataset,
    grid_points: list[tuple[float, float]],
) -> dict[str, Any]:
    """Compute FES2022 tides at runtime (legacy mode, slow)."""
    from .tides import build_tide_cache, compute_ssh_total

    time_index = pd.DatetimeIndex(ds.time.values)

    log.info(
        "Computing FES2022 daily-max tides at runtime for %d grid points "
        "(legacy mode — consider preprocessing with tides for large domains)...",
        len(grid_points),
    )
    t0 = time.time()
    tide_cache = build_tide_cache(grid_points, time_index)
    elapsed = time.time() - t0
    log.info("Tide computation completed in %.1f s", elapsed)

    ssh_total_cache: dict[tuple[float, float], pd.Series] = {}
    tide_failed: list[tuple[float, float]] = []

    for lat, lon in grid_points:
        key = (lat, lon)
        if key not in tide_cache:
            tide_failed.append(key)
            continue

        ssh_series = _extract_point_series(ds, cfg.SSH_VAR, lat, lon)
        if ssh_series is None:
            tide_failed.append(key)
            continue

        ssh_total = compute_ssh_total(ssh_series, tide_cache[key])
        ssh_total_cache[key] = ssh_total

    if tide_failed:
        log.warning("%d grid points without SSH_total: %s", len(tide_failed), tide_failed)

    ctx["ssh_total_cache"] = ssh_total_cache
    ctx["tide_cache"] = tide_cache
    ctx["tide_failed"] = tide_failed

    log.info(
        "SSH_total computed for %d/%d grid points",
        len(ssh_total_cache), len(grid_points),
    )
    return ctx


def phase_catalog(ctx: dict[str, Any]) -> dict[str, Any]:
    """Phase 3: Build storm catalogs for Hs and SSH_total independently.

    Supports parallel processing via ``--workers N``. When N > 1, grid points
    are processed in parallel using a ProcessPoolExecutor.

    Adds ``catalog_hs`` and ``catalog_ssh`` to context.
    """
    from .segmentation import build_storm_catalog_for_point
    from . import io as sio

    log.info("=" * 70)
    log.info("PHASE 3 — Build storm catalogs")
    log.info("=" * 70)

    ds = ctx["ds"]
    coastal_df = ctx["coastal_df"]
    ssh_total_cache = ctx["ssh_total_cache"]
    thresholds = ctx["thresholds"]
    muni_lookup = ctx["muni_lookup"]
    n_workers = ctx.get("n_workers", 1)

    thr_hs_pct = thresholds["thr_hs_pct"]
    thr_ssh_pct = thresholds["thr_ssh_pct"]

    n_points = len(coastal_df)

    # ── Pre-extract all time series (vectorized, before parallel) ─────────
    log.info("Extracting time series for %d grid points …", n_points)
    point_data: list[dict] = []
    for _, row in coastal_df.iterrows():
        lat = float(row["grid_lat"])
        lon = float(row["grid_lon"])
        key = (lat, lon)
        muni = muni_lookup.get((round(lat, 2), round(lon, 2)))

        hs_series = _extract_point_series(ds, cfg.HS_VAR, lat, lon)
        ssh_series = ssh_total_cache.get(key)

        point_data.append({
            "lat": lat,
            "lon": lon,
            "muni": muni,
            "hs_series": hs_series,
            "ssh_series": ssh_series,
            "hs_valid_frac": float(row["hs_valid_frac"]),
            "ssh_valid_frac": float(row["ssh_valid_frac"]),
            "dist_to_coast_km": float(row["dist_to_coast_km"]),
        })

    # ── Process grid points (sequential or parallel) ──────────────────────
    if n_workers > 1:
        log.info("Parallel catalog generation: %d workers, %d grid points", n_workers, n_points)
        results = _catalog_parallel(point_data, thr_hs_pct, thr_ssh_pct, n_workers)
    else:
        log.info("Sequential catalog generation: %d grid points", n_points)
        results = _catalog_sequential(point_data, thr_hs_pct, thr_ssh_pct)

    # ── Unpack results ────────────────────────────────────────────────────
    catalog_hs = [r["entry_hs"] for r in results]
    catalog_ssh = [r["entry_ssh"] for r in results]
    grid_meta = [r["meta"] for r in results]

    # ── Aggregate stats ───────────────────────────────────────────────────
    total_hs = sum(len(e.get("storms", [])) for e in catalog_hs)
    total_ssh = sum(len(e.get("storms", [])) for e in catalog_ssh)
    log.info(
        "Catalog complete: %d Hs storms, %d SSH_total storms across %d grid points",
        total_hs, total_ssh, n_points,
    )

    # ── Save outputs ──────────────────────────────────────────────────────
    sio.make_output_dirs()

    sio.save_catalog_json(catalog_hs, cfg.CATALOG_DIR / "catalog_hs_storms.json")
    sio.save_catalog_json(catalog_ssh, cfg.CATALOG_DIR / "catalog_ssh_total_storms.json")
    sio.save_catalog_csv(catalog_hs, cfg.TAB_DIR / "tab_SC3_hs_storms_summary.csv")
    sio.save_catalog_csv(catalog_ssh, cfg.TAB_DIR / "tab_SC3_ssh_total_storms_summary.csv")
    sio.save_grid_metadata_csv(grid_meta, cfg.TAB_DIR / "tab_SC3_catalog_metadata.csv")

    # ── Run metadata ──────────────────────────────────────────────────────
    ds = ctx["ds"]
    run_meta = {
        "run_date": datetime.now(timezone.utc).isoformat(),
        "run_mode": cfg.RUN_MODE,
        "dataset": str(cfg.UNIFIED_FILE),
        "period_full_series": [
            str(ds.time.values[0])[:10],
            str(ds.time.values[-1])[:10],
        ],
        "period_threshold_computation": "full_record",
        "thr_hs_pct": thr_hs_pct,
        "thr_ssh_pct": thr_ssh_pct,
        "episode_max_gap_days": cfg.EPISODE_MAX_GAP_DAYS,
        "coastal_max_dist_km": cfg.COASTAL_MAX_DIST_KM,
        "min_valid_frac": cfg.MIN_VALID_FRAC,
        "tide_model": cfg.TIDE_MODEL,
        "tide_mode_configured": cfg.TIDE_MODE,
        "tide_mode_used": ctx.get("tide_mode_used", "unknown"),
        "ssh_total_precomputed": ctx.get("tide_mode_used", "").startswith("precomputed"),
        "n_grid_points": n_points,
        "n_grid_points_skipped": len(ctx.get("skipped", [])),
        "n_catalog_workers": n_workers,
        "n_hs_storms_total": total_hs,
        "n_ssh_total_storms_total": total_ssh,
    }
    sio.save_run_metadata(run_meta, cfg.LOG_DIR / "run_metadata.json")

    ctx["catalog_hs"] = catalog_hs
    ctx["catalog_ssh"] = catalog_ssh
    ctx["grid_meta"] = grid_meta
    ctx["run_meta"] = run_meta
    return ctx


# ── Catalog helpers (sequential / parallel) ───────────────────────────────


def _process_single_point(
    pd_data: dict,
    thr_hs_pct: float,
    thr_ssh_pct: float,
) -> dict:
    """Process one grid point: build Hs and SSH_total catalog entries.

    This function is self-contained (no xarray, no global state) so it can be
    shipped to a worker process via ProcessPoolExecutor.
    """
    from .segmentation import build_storm_catalog_for_point

    lat = pd_data["lat"]
    lon = pd_data["lon"]
    muni = pd_data["muni"]

    # ── Hs catalog ────────────────────────────────────────────────────────
    hs_series = pd_data["hs_series"]
    if hs_series is not None:
        entry_hs = build_storm_catalog_for_point(
            grid_lat=lat, grid_lon=lon, series=hs_series,
            threshold_pct=thr_hs_pct, var_prefix="hs", municipality=muni,
        )
    else:
        entry_hs = {
            "grid_lat": lat, "grid_lon": lon, "municipality": muni,
            "thr_hs_pct": thr_hs_pct, "thr_hs_abs": None,
            "storms": [], "_skip_reason": "no_hs_data",
        }

    # ── SSH_total catalog ─────────────────────────────────────────────────
    ssh_series = pd_data["ssh_series"]
    if ssh_series is not None:
        entry_ssh = build_storm_catalog_for_point(
            grid_lat=lat, grid_lon=lon, series=ssh_series,
            threshold_pct=thr_ssh_pct, var_prefix="ssh_total", municipality=muni,
        )
    else:
        entry_ssh = {
            "grid_lat": lat, "grid_lon": lon, "municipality": muni,
            "thr_ssh_total_pct": thr_ssh_pct, "thr_ssh_total_abs": None,
            "storms": [], "_skip_reason": "no_ssh_total",
        }

    # ── Per-grid-point metadata ───────────────────────────────────────────
    n_hs = len(entry_hs.get("storms", []))
    n_ssh = len(entry_ssh.get("storms", []))
    meta = {
        "grid_lat": lat, "grid_lon": lon, "municipality": muni,
        "hs_valid_frac": pd_data["hs_valid_frac"],
        "ssh_valid_frac": pd_data["ssh_valid_frac"],
        "dist_to_coast_km": pd_data["dist_to_coast_km"],
        "thr_hs_pct": thr_hs_pct,
        "thr_hs_abs": entry_hs.get("thr_hs_abs"),
        "thr_ssh_total_pct": thr_ssh_pct,
        "thr_ssh_total_abs": entry_ssh.get("thr_ssh_total_abs"),
        "n_hs_storms": n_hs, "n_ssh_total_storms": n_ssh,
        "skip_reason_hs": entry_hs.get("_skip_reason"),
        "skip_reason_ssh": entry_ssh.get("_skip_reason"),
    }

    return {"entry_hs": entry_hs, "entry_ssh": entry_ssh, "meta": meta}


def _catalog_sequential(
    point_data: list[dict], thr_hs_pct: float, thr_ssh_pct: float,
) -> list[dict]:
    """Process all grid points sequentially."""
    results = []
    n = len(point_data)
    for i, pd_item in enumerate(point_data):
        if (i + 1) % max(1, n // 10) == 0 or i == 0:
            log.info("  Processing grid point %d/%d", i + 1, n)
        results.append(_process_single_point(pd_item, thr_hs_pct, thr_ssh_pct))
    return results


def _catalog_parallel(
    point_data: list[dict],
    thr_hs_pct: float,
    thr_ssh_pct: float,
    n_workers: int,
) -> list[dict]:
    """Process grid points in parallel using ProcessPoolExecutor.

    Each worker receives pre-extracted pd.Series data (no xarray transfer).
    Order is preserved via executor.map().
    """
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing as mp
    from functools import partial

    ctx_spawn = mp.get_context("spawn")

    worker_fn = partial(
        _process_single_point,
        thr_hs_pct=thr_hs_pct,
        thr_ssh_pct=thr_ssh_pct,
    )

    n = len(point_data)
    log.info("Spawning %d workers for %d grid points …", n_workers, n)

    with ProcessPoolExecutor(
        max_workers=n_workers,
        mp_context=ctx_spawn,
    ) as executor:
        results = list(executor.map(worker_fn, point_data, chunksize=max(1, n // (n_workers * 4))))

    log.info("Parallel catalog generation complete: %d grid points processed", len(results))
    return results


def phase_figures(ctx: dict[str, Any]) -> dict[str, Any]:
    """Phase 4: Generate diagnostic QA figures."""
    from . import figures as fig_mod

    log.info("=" * 70)
    log.info("PHASE 4 — QA figures")
    log.info("=" * 70)

    catalog_hs = ctx["catalog_hs"]
    catalog_ssh = ctx["catalog_ssh"]

    fig_mod.plot_annual_counts(
        catalog_hs, catalog_ssh,
        cfg.FIG_DIR / "fig_SC3_annual_storm_counts.png",
    )
    fig_mod.plot_duration_distribution(
        catalog_hs, catalog_ssh,
        cfg.FIG_DIR / "fig_SC3_duration_distribution.png",
    )
    fig_mod.plot_seasonal_climatology(
        catalog_hs, catalog_ssh,
        cfg.FIG_DIR / "fig_SC3_seasonal_climatology.png",
    )

    return ctx


# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════


def _extract_point_series(
    ds, var: str, lat: float, lon: float,
) -> pd.Series | None:
    """Extract a 1-D time series for a variable at the nearest grid point.

    Uses xarray's nearest-neighbor selection.
    Returns None if the result is all-NaN.
    """
    try:
        da = ds[var].sel(latitude=lat, longitude=lon, method="nearest")
        series = da.to_series()
        series.index = pd.DatetimeIndex(series.index)
        series.name = var
        if series.isna().all():
            log.warning("All-NaN %s at (%.4f, %.4f)", var, lat, lon)
            return None
        return series
    except Exception as exc:
        log.error("Failed to extract %s at (%.4f, %.4f): %s", var, lat, lon, exc)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY PRINTING
# ══════════════════════════════════════════════════════════════════════════════


def print_summary(ctx: dict[str, Any]) -> None:
    """Print a human-readable summary of the run."""
    meta = ctx.get("run_meta", {})
    print("\n" + "=" * 70)
    print("STEP 3 — Storm Catalog Generation: Run Summary")
    print("=" * 70)
    print(f"  Run mode:           {meta.get('run_mode', '?')}")
    print(f"  Dataset:            {Path(meta.get('dataset', '?')).name}")
    print(f"  Period:             {meta.get('period_full_series', ['?', '?'])}")
    print(f"  Thresholds:         Hs=q{meta.get('thr_hs_pct', 0)*100:.0f}, "
          f"SSH_total=q{meta.get('thr_ssh_pct', 0)*100:.0f}")
    print(f"  Episode gap:        {meta.get('episode_max_gap_days', '?')} day(s)")
    print(f"  Coastal grid pts:   {meta.get('n_grid_points', '?')} "
          f"({meta.get('n_grid_points_skipped', 0)} skipped)")
    print(f"  Hs storms:          {meta.get('n_hs_storms_total', '?')}")
    print(f"  SSH_total storms:   {meta.get('n_ssh_total_storms_total', '?')}")
    print(f"  Tide mode:          {meta.get('tide_mode_used', '?')}")
    print(f"  Tide model:         {meta.get('tide_model', '?')}")
    print(f"  Output dir:         {cfg.OUTPUT_ROOT}")
    print("=" * 70 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Step 3 — Storm Catalog Generation",
    )
    parser.add_argument(
        "--phase",
        choices=["load-validate", "tides", "catalog", "figures", "all"],
        default="all",
        help="Pipeline phase to run (default: all).",
    )
    parser.add_argument(
        "--mode",
        choices=["test", "production"],
        default=None,
        help="Override RUN_MODE from config.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING"],
        default="INFO",
    )
    parser.add_argument(
        "--tide-mode",
        choices=["auto", "precomputed", "runtime"],
        default=None,
        help="Override TIDE_MODE from config. "
        "'auto' detects pre-computed fields; 'precomputed' requires SSH_total; "
        "'runtime' forces on-the-fly FES2022 computation (slow).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for catalog generation (default: 1 = sequential). "
        "Recommended: 4-16 for local, up to 50-100 for large servers.",
    )
    args = parser.parse_args(argv)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Override run mode if requested
    if args.mode:
        cfg.RUN_MODE = args.mode
        cfg.UNIFIED_FILE = (
            cfg.UNIFIED_FILE_TEST if args.mode == "test"
            else cfg.UNIFIED_FILE_PRODUCTION
        )

    # Override tide mode if requested
    if args.tide_mode:
        cfg.TIDE_MODE = args.tide_mode

    t_start = time.time()
    phase = args.phase
    n_workers = args.workers

    log.info("Step 3 — Storm Catalog Generation")
    log.info("Run mode: %s | Phase: %s | Tide mode: %s | Workers: %d",
             cfg.RUN_MODE, phase, cfg.TIDE_MODE, n_workers)

    ctx: dict[str, Any] = {"n_workers": n_workers}

    if phase in ("load-validate", "all"):
        ctx.update(phase_load_validate())

    if phase in ("tides", "all"):
        if "ds" not in ctx:
            ctx.update(phase_load_validate())
        ctx = phase_tides(ctx)

    if phase in ("catalog", "all"):
        if "ssh_total_cache" not in ctx:
            if "ds" not in ctx:
                ctx.update(phase_load_validate())
            ctx = phase_tides(ctx)
        ctx = phase_catalog(ctx)

    if phase in ("figures", "all"):
        if "catalog_hs" not in ctx:
            log.error("Catalogs not available. Run --phase catalog first.")
            sys.exit(1)
        ctx = phase_figures(ctx)

    if "run_meta" in ctx:
        print_summary(ctx)

    elapsed = time.time() - t_start
    log.info("Step 3 completed in %.1f s", elapsed)


if __name__ == "__main__":
    main()
