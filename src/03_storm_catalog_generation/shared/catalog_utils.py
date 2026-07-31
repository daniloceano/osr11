"""
Shared catalog I/O utilities for Step 3 submodules.

Provides common functions for loading storm catalogs, extracting metadata,
and computing derived quantities used by multiple submodules.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# ── Default paths (relative to project root) ─────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
CATALOG_DIR = ROOT / "outputs" / "storm_catalog"
HS_CATALOG = CATALOG_DIR / "catalog_hs_storms.json"
#: Level storm catalogue. Segmented on tide-free ``zos`` since 2026-07-31;
#: the superseded SSH_total catalogue is at
#: ``outputs/legacy_ssh_total_method/step3_full_ssh_total_q90/``.
LEVEL_CATALOG = CATALOG_DIR / "catalog_zos_storms.json"
#: Field-name prefix of the level catalogue, mirroring the Step 3 config.
LEVEL_PREFIX = "zos"
METADATA_FILE = CATALOG_DIR / "logs" / "run_metadata.json"


def load_catalog(path: Path) -> list[dict]:
    """Load a storm catalog JSON (list of grid-point dicts)."""
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {path}")
    with open(path) as f:
        return json.load(f)


def load_run_metadata(path: Path | None = None) -> dict:
    """Load run metadata from Step 3."""
    path = path or METADATA_FILE
    if not path.exists():
        raise FileNotFoundError(f"Run metadata not found: {path}")
    with open(path) as f:
        return json.load(f)


def get_period_years(run_meta: dict) -> float:
    """Compute the number of years covered by the catalog."""
    d0 = date.fromisoformat(run_meta["period_full_series"][0])
    d1 = date.fromisoformat(run_meta["period_full_series"][1])
    return (d1 - d0).days / 365.25


def storm_days(storm: dict) -> set[str]:
    """Return set of calendar-day strings (YYYY-MM-DD) covered by a storm."""
    ts = storm.get("time_series", {})
    dates = ts.get("dates", [])
    if dates:
        return set(dates)
    from datetime import timedelta
    start = date.fromisoformat(storm["date_start"])
    end = date.fromisoformat(storm["date_end"])
    return {
        (start + timedelta(days=d)).isoformat()
        for d in range((end - start).days + 1)
    }


def storm_date_range(storm: dict) -> tuple[date, date]:
    """Return (start_date, end_date) as date objects."""
    return (
        date.fromisoformat(storm["date_start"]),
        date.fromisoformat(storm["date_end"]),
    )


def flatten_catalog(catalog: list[dict], var_prefix: str = "") -> pd.DataFrame:
    """Flatten a catalog JSON into a DataFrame with one row per storm."""
    rows = []
    for entry in catalog:
        lat = entry["grid_lat"]
        lon = entry["grid_lon"]
        muni = entry.get("municipality")
        for storm in entry.get("storms", []):
            rows.append({
                "grid_lat": lat,
                "grid_lon": lon,
                "municipality": muni,
                "event_id": storm.get("event_id"),
                "date_start": storm["date_start"],
                "date_end": storm["date_end"],
                "duration_days": storm["duration_days"],
                "peak_value": storm["peak_value"],
                "peak_date": storm.get("peak_date"),
                "integrated_intensity": storm.get("integrated_intensity"),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date_start"] = pd.to_datetime(df["date_start"])
        df["date_end"] = pd.to_datetime(df["date_end"])
        df["year"] = df["date_start"].dt.year
        df["month"] = df["date_start"].dt.month
    return df


def build_grid_index(catalog: list[dict]) -> dict[tuple[float, float], dict]:
    """Build a lookup dict: (lat, lon) -> grid-point catalog entry."""
    idx = {}
    for gp in catalog:
        key = (round(gp["grid_lat"], 4), round(gp["grid_lon"], 4))
        idx[key] = gp
    return idx


def safe_percentile(values: list | np.ndarray, q: float) -> float | None:
    """Compute percentile, returning None if empty."""
    if len(values) == 0:
        return None
    return float(np.percentile(values, q))


def save_json(data: Any, path: Path) -> None:
    """Save data as JSON with compact formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    log.info("Saved: %s (%.1f KB)", path, path.stat().st_size / 1024)


def save_csv(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    log.info("Saved: %s (%d rows)", path, len(df))
