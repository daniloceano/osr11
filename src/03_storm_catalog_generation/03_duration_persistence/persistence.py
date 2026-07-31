"""
Duration and persistence metrics for Step 3 — Hazard Characterization.

Computes per-grid-point persistence statistics for Hₛ storms, tide-free zos storms,
and compound events. Metrics include storm counts, duration statistics,
integrated intensity, and interevent waiting times.

For Hₛ and tide-free zos (per grid point):
    - storm_count_total
    - storm_count_annual_mean
    - mean_duration_days
    - p95_duration_days
    - max_duration_days
    - mean_integrated_intensity
    - mean_interevent_time_days

For compound events (per grid point):
    - compound_count_total
    - compound_count_annual_mean
    - mean_overlap_duration
    - p95_overlap_duration
    - max_overlap_duration
    - mean_time_between_compound_events_days
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    build_grid_index,
    safe_percentile,
    save_json,
    save_csv,
    HS_CATALOG,
    LEVEL_CATALOG,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "duration_persistence"


def compute_univariate_persistence(
    storms: list[dict],
    n_years: float,
) -> dict[str, float | int | None]:
    """Compute persistence metrics for a single variable at one grid point."""
    n = len(storms)
    if n == 0:
        return {
            "storm_count_total": 0,
            "storm_count_annual_mean": 0.0,
            "mean_duration_days": None,
            "p95_duration_days": None,
            "max_duration_days": None,
            "mean_integrated_intensity": None,
            "mean_interevent_time_days": None,
        }

    durations = [s["duration_days"] for s in storms]
    intensities = [s.get("integrated_intensity", 0) for s in storms]

    # Interevent time (days between end of storm i and start of storm i+1)
    interevent_times = []
    sorted_storms = sorted(storms, key=lambda s: s["date_start"])
    for i in range(len(sorted_storms) - 1):
        end_i = date.fromisoformat(sorted_storms[i]["date_end"])
        start_next = date.fromisoformat(sorted_storms[i + 1]["date_start"])
        gap = (start_next - end_i).days
        if gap > 0:
            interevent_times.append(gap)

    return {
        "storm_count_total": n,
        "storm_count_annual_mean": round(n / n_years, 2) if n_years > 0 else None,
        "mean_duration_days": round(float(np.mean(durations)), 2),
        "p95_duration_days": round(float(np.percentile(durations, 95)), 2),
        "max_duration_days": int(np.max(durations)),
        "mean_integrated_intensity": round(float(np.mean(intensities)), 4),
        "mean_interevent_time_days": (
            round(float(np.mean(interevent_times)), 2)
            if interevent_times else None
        ),
    }


def compute_compound_persistence(
    compound_events: list[dict],
    n_years: float,
) -> dict[str, float | int | None]:
    """Compute persistence metrics for compound events at one grid point."""
    n = len(compound_events)
    if n == 0:
        return {
            "compound_count_total": 0,
            "compound_count_annual_mean": 0.0,
            "mean_overlap_duration": None,
            "p95_overlap_duration": None,
            "max_overlap_duration": None,
            "mean_time_between_compound_events_days": None,
        }

    overlaps = [e["overlap_duration_days"] for e in compound_events]

    # Interevent time for compound events
    interevent = []
    sorted_events = sorted(compound_events, key=lambda e: e["date_start"])
    for i in range(len(sorted_events) - 1):
        end_i = date.fromisoformat(sorted_events[i]["date_end"])
        start_next = date.fromisoformat(sorted_events[i + 1]["date_start"])
        gap = (start_next - end_i).days
        if gap > 0:
            interevent.append(gap)

    return {
        "compound_count_total": n,
        "compound_count_annual_mean": round(n / n_years, 2) if n_years > 0 else None,
        "mean_overlap_duration": round(float(np.mean(overlaps)), 2),
        "p95_overlap_duration": round(float(np.percentile(overlaps, 95)), 2),
        "max_overlap_duration": int(np.max(overlaps)),
        "mean_time_between_compound_events_days": (
            round(float(np.mean(interevent)), 2)
            if interevent else None
        ),
    }


def run_duration_persistence(
    compound_catalog_path: Path | None = None,
) -> dict:
    """Run duration/persistence analysis over all grid points.

    Reads Hₛ and SSH_total catalogs plus compound catalog.
    Returns dict with grid_results and domain summary.
    """
    import json

    hs_catalog = load_catalog(HS_CATALOG)
    level_catalog = load_catalog(LEVEL_CATALOG)
    run_meta = load_run_metadata()
    n_years = get_period_years(run_meta)

    # Load compound catalog if available
    compound_path = compound_catalog_path or (
        ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
    )
    compound_catalog = {}
    if compound_path.exists():
        with open(compound_path) as f:
            compound_data = json.load(f)
        for gp in compound_data:
            key = (round(gp["grid_lat"], 4), round(gp["grid_lon"], 4))
            compound_catalog[key] = gp.get("compound_events", [])

    level_index = build_grid_index(level_catalog)

    grid_results = []
    for hs_gp in hs_catalog:
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]
        key = (round(lat, 4), round(lon, 4))

        level_gp = level_index.get(key)
        hs_storms = hs_gp.get("storms", [])
        level_storms = level_gp.get("storms", []) if level_gp else []
        compound_events = compound_catalog.get(key, [])

        hs_metrics = compute_univariate_persistence(hs_storms, n_years)
        level_metrics = compute_univariate_persistence(level_storms, n_years)
        compound_metrics = compute_compound_persistence(compound_events, n_years)

        grid_results.append({
            "grid_lat": round(lat, 4),
            "grid_lon": round(lon, 4),
            "municipality": hs_gp.get("municipality"),
            # Hs persistence
            **{f"hs_{k}": v for k, v in hs_metrics.items()},
            # SSH_total persistence
            **{f"zos_{k}": v for k, v in level_metrics.items()},
            # Compound persistence
            **compound_metrics,
        })

    log.info("Duration/persistence computed for %d grid points", len(grid_results))

    return {"grid_results": grid_results, "n_years": n_years}


def save_duration_results(results: dict, output_dir: Path | None = None):
    """Save duration/persistence results."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results["grid_results"])
    save_csv(df, out / "duration_persistence_metrics.csv")
    save_json(results["grid_results"], out / "duration_persistence_metrics.json")
    log.info("Duration/persistence results saved to %s", out)
