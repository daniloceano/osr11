"""
Step 3 — Storm Catalog Generation: CLI orchestrator.

Applies PU-optimal thresholds (from Step 2e) to the full 1993–2025 metocean
record to produce independent storm catalogs for Hs and tide-free sea level
(zos) at each coastal grid point.

The level catalogue was segmented on SSH_total until 2026-07-31. Audit AUD-01
retired that: a percentile of zos + tide selects on tidal phase rather than on
storm forcing. The tide re-enters as the HAT gate applied in Step 3.2, not as
part of the level threshold. See ``config/analysis_config.py``.

Usage
-----
    cd <project_root>
    python -m src.03_storm_catalog_generation.01_storm_catalogs.main [--all | --phase PHASE]

Phases
------
    load-validate    Load inputs, identify coastal grid points
    tides            Load the tide-free level series and the daily-max tide
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
        "Summary: %d coastal grid points, thresholds hs=q%.0f %s=q%.0f, "
        "municipality labels for %d points",
        len(coastal_df),
        thresholds["thr_hs_pct"] * 100,
        cfg.LEVEL_PREFIX,
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
    """Phase 2: Resolve the level and tide series for all coastal grid points.

    Since 2026-07-31 the segmented level variable is tide-free ``zos``, so this
    phase no longer builds SSH_total. It loads two things:

    * ``level_cache`` — the zos series that Phase 3 segments into episodes;
    * ``tide_cache``  — the daily-maximum FES2022 tide, which Step 3.2 needs in
      order to form SWL and apply the HAT gate. It is loaded here because this
      is where the dataset is open, not because the level threshold uses it.

    ``cfg.TIDE_MODE`` now governs only how the tide is obtained:

    **auto** (default)
        Use ``tide_daily_max`` from the unified dataset if present; otherwise
        compute FES2022 at runtime.
    **precomputed**
        Require ``tide_daily_max`` in the dataset. Fail if absent.
    **runtime**
        Always compute FES2022 at runtime (slow; small domains only).

    Historical behaviour, superseded: this phase used to resolve SSH_total =
    zos + tide and hand that to the segmentation. AUD-01 established that a
    percentile of that sum selects on tidal phase rather than on storm forcing.
    """
    log.info("=" * 70)
    log.info(
        "PHASE 2 — Resolve level (%s) and tide (TIDE_MODE=%s)",
        cfg.LEVEL_VAR, cfg.TIDE_MODE,
    )
    log.info("=" * 70)

    ds = ctx["ds"]
    coastal_df = ctx["coastal_df"]

    grid_points = list(
        zip(coastal_df["grid_lat"].values, coastal_df["grid_lon"].values)
    )

    has_level = cfg.LEVEL_VAR in ds.data_vars
    has_tide_daily_max = cfg.TIDE_DAILY_MAX_VAR in ds.data_vars
    log.info(
        "Dataset variables: %s=%s, %s=%s",
        cfg.LEVEL_VAR, has_level, cfg.TIDE_DAILY_MAX_VAR, has_tide_daily_max,
    )

    if not has_level:
        log.error(
            "Level variable %r not found in the unified dataset. The level "
            "catalogue is segmented on the tide-free field; there is no "
            "fallback that would preserve the method.",
            cfg.LEVEL_VAR,
        )
        sys.exit(1)

    # ── Level series (tide-free) ──────────────────────────────────────────
    level_cache: dict[tuple[float, float], pd.Series] = {}
    level_failed: list[tuple[float, float]] = []
    for lat, lon in grid_points:
        series = _extract_point_series(ds, cfg.LEVEL_VAR, lat, lon)
        if series is not None:
            level_cache[(lat, lon)] = series
        else:
            level_failed.append((lat, lon))
    log.info(
        "Level series loaded for %d/%d grid points (%d failed)",
        len(level_cache), len(grid_points), len(level_failed),
    )

    # ── Daily-maximum astronomical tide (for the Step 3.2 HAT gate) ───────
    tide_mode = cfg.TIDE_MODE
    if tide_mode == "precomputed" and not has_tide_daily_max:
        log.error(
            "TIDE_MODE='precomputed' but %r is absent. Run preprocessing with "
            "tides enabled, or set TIDE_MODE='auto'.",
            cfg.TIDE_DAILY_MAX_VAR,
        )
        sys.exit(1)

    if tide_mode == "runtime" or not has_tide_daily_max:
        mode_used = "runtime_fes2022"
    else:
        mode_used = "precomputed_tide_daily_max"

    tide_cache: dict[tuple[float, float], pd.Series] = {}
    tide_failed: list[tuple[float, float]] = []

    if mode_used == "precomputed_tide_daily_max":
        for lat, lon in grid_points:
            series = _extract_point_series(ds, cfg.TIDE_DAILY_MAX_VAR, lat, lon)
            if series is not None:
                tide_cache[(lat, lon)] = series
            else:
                tide_failed.append((lat, lon))
    else:
        from .tides import build_tide_cache

        time_index = pd.DatetimeIndex(ds.time.values)
        log.info(
            "Computing FES2022 daily-max tides at runtime for %d grid points …",
            len(grid_points),
        )
        t0 = time.time()
        tide_cache = build_tide_cache(grid_points, time_index)
        log.info("Tide computation completed in %.1f s", time.time() - t0)
        tide_failed = [key for key in grid_points if key not in tide_cache]

    if tide_failed:
        log.warning("%d grid points without a tide series", len(tide_failed))

    log.info("Tide resolution mode: %s", mode_used)
    log.info(
        "Tide loaded for %d/%d grid points", len(tide_cache), len(grid_points)
    )

    ctx["level_cache"] = level_cache
    ctx["tide_cache"] = tide_cache
    ctx["level_failed"] = level_failed
    ctx["tide_failed"] = tide_failed
    ctx["tide_mode_used"] = mode_used
    return ctx


def phase_catalog(ctx: dict[str, Any]) -> dict[str, Any]:
    """Phase 3: Build storm catalogs for Hs and tide-free zos independently.

    Supports parallel processing via ``--workers N``. When N > 1, grid points
    are processed in parallel using a ProcessPoolExecutor.

    Adds ``catalog_hs`` and ``catalog_level`` to context.
    """
    from .segmentation import build_storm_catalog_for_point
    from . import io as sio

    log.info("=" * 70)
    log.info("PHASE 3 — Build storm catalogs")
    log.info("=" * 70)

    ds = ctx["ds"]
    coastal_df = ctx["coastal_df"]
    level_cache = ctx["level_cache"]
    tide_cache = ctx["tide_cache"]
    thresholds = ctx["thresholds"]
    muni_lookup = ctx["muni_lookup"]
    n_workers = ctx.get("n_workers", 1)

    thr_hs_pct = thresholds["thr_hs_pct"]
    # The Step 2e table still names the level column thr_ssh_pct. Its meaning
    # changed with the detector: it is now a percentile of tide-free zos.
    thr_level_pct = thresholds["thr_ssh_pct"]

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
        level_series = level_cache.get(key)

        point_data.append({
            "lat": lat,
            "lon": lon,
            "muni": muni,
            "hs_series": hs_series,
            "level_series": level_series,
            "hs_valid_frac": float(row["hs_valid_frac"]),
            "level_valid_frac": float(row["ssh_valid_frac"]),
            "dist_to_coast_km": float(row["dist_to_coast_km"]),
        })

    # ── Process grid points (sequential or parallel) ──────────────────────
    if n_workers > 1:
        log.info("Parallel catalog generation: %d workers, %d grid points", n_workers, n_points)
        results = _catalog_parallel(point_data, thr_hs_pct, thr_level_pct, n_workers)
    else:
        log.info("Sequential catalog generation: %d grid points", n_points)
        results = _catalog_sequential(point_data, thr_hs_pct, thr_level_pct)

    # ── Unpack results ────────────────────────────────────────────────────
    catalog_hs = [r["entry_hs"] for r in results]
    catalog_level = [r["entry_level"] for r in results]
    grid_meta = [r["meta"] for r in results]

    # ── Aggregate stats ───────────────────────────────────────────────────
    total_hs = sum(len(e.get("storms", [])) for e in catalog_hs)
    total_level = sum(len(e.get("storms", [])) for e in catalog_level)
    log.info(
        "Catalog complete: %d Hs storms, %d %s storms across %d grid points",
        total_hs, total_level, cfg.LEVEL_PREFIX, n_points,
    )

    # ── Save outputs ──────────────────────────────────────────────────────
    sio.make_output_dirs()

    sio.save_catalog_json(catalog_hs, cfg.CATALOG_DIR / "catalog_hs_storms.json")
    sio.save_catalog_json(catalog_level, cfg.CATALOG_DIR / cfg.LEVEL_CATALOG_NAME)
    sio.save_catalog_csv(catalog_hs, cfg.TAB_DIR / "tab_SC3_hs_storms_summary.csv")
    sio.save_catalog_csv(
        catalog_level,
        cfg.TAB_DIR / f"tab_SC3_{cfg.LEVEL_PREFIX}_storms_summary.csv",
    )
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
        "thr_level_pct": thr_level_pct,
        "level_var": cfg.LEVEL_VAR,
        "level_prefix": cfg.LEVEL_PREFIX,
        "level_is_tide_free": True,
        "episode_max_gap_days": cfg.EPISODE_MAX_GAP_DAYS,
        "coastal_max_dist_km": cfg.COASTAL_MAX_DIST_KM,
        "min_valid_frac": cfg.MIN_VALID_FRAC,
        "tide_model": cfg.TIDE_MODEL,
        "tide_mode_configured": cfg.TIDE_MODE,
        "tide_mode_used": ctx.get("tide_mode_used", "unknown"),
        "tide_precomputed": ctx.get("tide_mode_used", "").startswith("precomputed"),
        "n_grid_points": n_points,
        "n_grid_points_skipped": len(ctx.get("skipped", [])),
        "n_catalog_workers": n_workers,
        "n_hs_storms_total": total_hs,
        f"n_{cfg.LEVEL_PREFIX}_storms_total": total_level,
    }
    sio.save_run_metadata(run_meta, cfg.LOG_DIR / "run_metadata.json")

    ctx["catalog_hs"] = catalog_hs
    ctx["catalog_level"] = catalog_level
    ctx["grid_meta"] = grid_meta
    ctx["run_meta"] = run_meta
    return ctx


# ── Catalog helpers (sequential / parallel) ───────────────────────────────


def _process_single_point(
    pd_data: dict,
    thr_hs_pct: float,
    thr_level_pct: float,
) -> dict:
    """Process one grid point: build the Hs and tide-free level catalog entries.

    This function is self-contained (no xarray, no global state) so it can be
    shipped to a worker process via ProcessPoolExecutor.

    The level entry is segmented on ``cfg.LEVEL_VAR`` (zos) and its fields carry
    the ``cfg.LEVEL_PREFIX`` prefix, so the schema names the quantity that was
    actually thresholded.
    """
    from .segmentation import build_storm_catalog_for_point

    lat = pd_data["lat"]
    lon = pd_data["lon"]
    muni = pd_data["muni"]
    prefix = cfg.LEVEL_PREFIX

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

    # ── Level catalog (tide-free) ─────────────────────────────────────────
    level_series = pd_data["level_series"]
    if level_series is not None:
        entry_level = build_storm_catalog_for_point(
            grid_lat=lat, grid_lon=lon, series=level_series,
            threshold_pct=thr_level_pct, var_prefix=prefix, municipality=muni,
        )
    else:
        entry_level = {
            "grid_lat": lat, "grid_lon": lon, "municipality": muni,
            f"thr_{prefix}_pct": thr_level_pct, f"thr_{prefix}_abs": None,
            "storms": [], "_skip_reason": "no_level_data",
        }

    # ── Per-grid-point metadata ───────────────────────────────────────────
    n_hs = len(entry_hs.get("storms", []))
    n_level = len(entry_level.get("storms", []))
    meta = {
        "grid_lat": lat, "grid_lon": lon, "municipality": muni,
        "hs_valid_frac": pd_data["hs_valid_frac"],
        f"{prefix}_valid_frac": pd_data["level_valid_frac"],
        "dist_to_coast_km": pd_data["dist_to_coast_km"],
        "thr_hs_pct": thr_hs_pct,
        "thr_hs_abs": entry_hs.get("thr_hs_abs"),
        f"thr_{prefix}_pct": thr_level_pct,
        f"thr_{prefix}_abs": entry_level.get(f"thr_{prefix}_abs"),
        "n_hs_storms": n_hs, f"n_{prefix}_storms": n_level,
        "skip_reason_hs": entry_hs.get("_skip_reason"),
        "skip_reason_level": entry_level.get("_skip_reason"),
    }

    return {"entry_hs": entry_hs, "entry_level": entry_level, "meta": meta}


def _catalog_sequential(
    point_data: list[dict], thr_hs_pct: float, thr_level_pct: float,
) -> list[dict]:
    """Process all grid points sequentially."""
    results = []
    n = len(point_data)
    for i, pd_item in enumerate(point_data):
        if (i + 1) % max(1, n // 10) == 0 or i == 0:
            log.info("  Processing grid point %d/%d", i + 1, n)
        results.append(_process_single_point(pd_item, thr_hs_pct, thr_level_pct))
    return results


def _catalog_parallel(
    point_data: list[dict],
    thr_hs_pct: float,
    thr_level_pct: float,
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
        thr_level_pct=thr_level_pct,
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
    catalog_level = ctx["catalog_level"]

    fig_mod.plot_annual_counts(
        catalog_hs, catalog_level,
        cfg.FIG_DIR / "fig_SC3_annual_storm_counts.png",
    )
    fig_mod.plot_duration_distribution(
        catalog_hs, catalog_level,
        cfg.FIG_DIR / "fig_SC3_duration_distribution.png",
    )
    fig_mod.plot_seasonal_climatology(
        catalog_hs, catalog_level,
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
          f"{meta.get('level_var', 'level')} (tide-free)="
          f"q{meta.get('thr_level_pct', 0)*100:.0f}")
    print(f"  Episode gap:        {meta.get('episode_max_gap_days', '?')} day(s)")
    print(f"  Coastal grid pts:   {meta.get('n_grid_points', '?')} "
          f"({meta.get('n_grid_points_skipped', 0)} skipped)")
    print(f"  Hs storms:          {meta.get('n_hs_storms_total', '?')}")
    _level_prefix = meta.get("level_prefix", "zos")
    print(f"  {_level_prefix} storms:         "
          f"{meta.get(f'n_{_level_prefix}_storms_total', '?')}")
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
        if "level_cache" not in ctx:
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
