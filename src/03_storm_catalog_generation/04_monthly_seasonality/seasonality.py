"""
Monthly seasonality analysis for Step 3 — Hazard Characterization.

Computes monthly climatological statistics for Hₛ storms, SSH_total storms,
and compound events. No circular statistics in this phase (advanced/future).

Per grid point:
    - Monthly event count climatology (12 months)
    - Monthly relative share (fraction of total events per month)
    - Month of peak occurrence
    - Optional seasonal aggregation (DJF/MAM/JJA/SON)

References:
    - Standard monthly climatology following meteorological convention.
"""
from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    flatten_catalog,
    build_grid_index,
    save_json,
    save_csv,
    HS_CATALOG,
    SSH_CATALOG,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "seasonality"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Season mapping: month → season name
SEASON_MAP = {
    12: "DJF", 1: "DJF", 2: "DJF",
    3: "MAM", 4: "MAM", 5: "MAM",
    6: "JJA", 7: "JJA", 8: "JJA",
    9: "SON", 10: "SON", 11: "SON",
}


def _monthly_counts(storms: list[dict]) -> dict[int, int]:
    """Count storms by starting month (1-indexed)."""
    counter: Counter = Counter()
    for s in storms:
        try:
            month = int(s["date_start"].split("-")[1]) if isinstance(s["date_start"], str) else s["date_start"].month
        except (ValueError, IndexError, AttributeError):
            continue
        counter[month] += 1
    return dict(counter)


def _monthly_climatology(monthly_counts: dict[int, int]) -> dict:
    """Build monthly climatology dict from count mapping."""
    counts = [monthly_counts.get(m, 0) for m in range(1, 13)]
    total = sum(counts)

    if total == 0:
        return {
            "monthly_counts": counts,
            "monthly_share": [0.0] * 12,
            "peak_month": None,
            "peak_month_name": None,
            "seasonal_counts": {"DJF": 0, "MAM": 0, "JJA": 0, "SON": 0},
        }

    shares = [round(c / total, 4) if total > 0 else 0.0 for c in counts]
    peak_idx = int(np.argmax(counts))
    peak_month = peak_idx + 1

    # Seasonal aggregation
    seasonal = {"DJF": 0, "MAM": 0, "JJA": 0, "SON": 0}
    for m, c in enumerate(counts, 1):
        seasonal[SEASON_MAP[m]] += c

    return {
        "monthly_counts": counts,
        "monthly_share": shares,
        "peak_month": peak_month,
        "peak_month_name": MONTH_NAMES[peak_idx],
        "seasonal_counts": seasonal,
    }


def compute_point_seasonality(
    hs_storms: list[dict],
    ssh_storms: list[dict],
    compound_events: list[dict],
) -> dict:
    """Compute seasonality for all three event types at one grid point."""
    hs_monthly = _monthly_counts(hs_storms)
    ssh_monthly = _monthly_counts(ssh_storms)
    compound_monthly = _monthly_counts(compound_events)

    return {
        "hs": _monthly_climatology(hs_monthly),
        "ssh_total": _monthly_climatology(ssh_monthly),
        "compound": _monthly_climatology(compound_monthly),
    }


def run_seasonality(
    compound_catalog_path: Path | None = None,
) -> dict:
    """Run seasonality analysis over all grid points."""
    import json

    hs_catalog = load_catalog(HS_CATALOG)
    ssh_catalog = load_catalog(SSH_CATALOG)

    # Load compound catalog
    compound_path = compound_catalog_path or (
        ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
    )
    compound_catalog = {}
    if compound_path.exists():
        with open(compound_path) as f:
            compound_data = json.load(f)
        for gp in compound_data:
            key = (round(gp["grid_lat"], 5), round(gp["grid_lon"], 5))
            compound_catalog[key] = gp.get("compound_events", [])

    ssh_index = build_grid_index(ssh_catalog)

    grid_results = []
    for hs_gp in hs_catalog:
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]
        key = (round(lat, 5), round(lon, 5))

        ssh_gp = ssh_index.get(key)
        hs_storms = hs_gp.get("storms", [])
        ssh_storms = ssh_gp.get("storms", []) if ssh_gp else []
        compound_events = compound_catalog.get(key, [])

        seasonality = compute_point_seasonality(hs_storms, ssh_storms, compound_events)

        grid_results.append({
            "grid_lat": round(lat, 4),
            "grid_lon": round(lon, 4),
            "municipality": hs_gp.get("municipality"),
            # Hs seasonality
            "hs_monthly_counts": seasonality["hs"]["monthly_counts"],
            "hs_monthly_share": seasonality["hs"]["monthly_share"],
            "hs_peak_month": seasonality["hs"]["peak_month"],
            "hs_peak_month_name": seasonality["hs"]["peak_month_name"],
            "hs_seasonal_counts": seasonality["hs"]["seasonal_counts"],
            # SSH_total seasonality
            "ssh_total_monthly_counts": seasonality["ssh_total"]["monthly_counts"],
            "ssh_total_monthly_share": seasonality["ssh_total"]["monthly_share"],
            "ssh_total_peak_month": seasonality["ssh_total"]["peak_month"],
            "ssh_total_peak_month_name": seasonality["ssh_total"]["peak_month_name"],
            "ssh_total_seasonal_counts": seasonality["ssh_total"]["seasonal_counts"],
            # Compound seasonality
            "compound_monthly_counts": seasonality["compound"]["monthly_counts"],
            "compound_monthly_share": seasonality["compound"]["monthly_share"],
            "compound_peak_month": seasonality["compound"]["peak_month"],
            "compound_peak_month_name": seasonality["compound"]["peak_month_name"],
            "compound_seasonal_counts": seasonality["compound"]["seasonal_counts"],
        })

    log.info("Seasonality computed for %d grid points", len(grid_results))
    return {"grid_results": grid_results}


def save_seasonality_results(results: dict, output_dir: Path | None = None):
    """Save seasonality results."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    save_json(results["grid_results"], out / "seasonality_metrics.json")

    # Also export a flat CSV with summary metrics (no arrays)
    rows = []
    for gr in results["grid_results"]:
        rows.append({
            "grid_lat": gr["grid_lat"],
            "grid_lon": gr["grid_lon"],
            "municipality": gr.get("municipality"),
            "hs_peak_month": gr["hs_peak_month"],
            "hs_peak_month_name": gr["hs_peak_month_name"],
            "ssh_total_peak_month": gr["ssh_total_peak_month"],
            "ssh_total_peak_month_name": gr["ssh_total_peak_month_name"],
            "compound_peak_month": gr["compound_peak_month"],
            "compound_peak_month_name": gr["compound_peak_month_name"],
            # Seasonal counts as separate columns
            **{f"hs_season_{s}": gr["hs_seasonal_counts"][s] for s in ["DJF", "MAM", "JJA", "SON"]},
            **{f"ssh_total_season_{s}": gr["ssh_total_seasonal_counts"][s] for s in ["DJF", "MAM", "JJA", "SON"]},
            **{f"compound_season_{s}": gr["compound_seasonal_counts"][s] for s in ["DJF", "MAM", "JJA", "SON"]},
        })
    df = pd.DataFrame(rows)
    save_csv(df, out / "seasonality_summary.csv")
    log.info("Seasonality results saved to %s", out)
