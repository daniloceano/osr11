"""
Utility helpers for Step 2e — PU Composite Calibration.

Provides data loading, output directory management, and logging helpers.
All functions are self-contained and do not depend on other Step 2e modules.

Loading the expanded events database
-------------------------------------
The expanded events CSV (`ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`)
uses a different schema than the legacy Leal et al. database. The column "city"
maps to "municipality" throughout this codebase. Synthetic integer disaster_ids
(1, 2, …, N) are assigned so that build_event_records() from the preliminary_compound
module can be called without modification.

Loading the legacy events database
------------------------------------
The legacy CSV is loaded with minimal cleaning for use as a corroborating evidence
source in the E_i calculation (audit.py). Only disaster_id, municipality, date, and
coastal_sector are required from the legacy database.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

log = logging.getLogger(__name__)


# ── Output directory management ──────────────────────────────────────────────

def make_output_dirs(cfg: dict) -> None:
    """Create all Step 2e output directories if they don't exist.

    Parameters
    ----------
    cfg : dict
        Configuration dictionary from analysis_config.CFG.
    """
    dirs = [
        cfg["output_root"],
        cfg["fig_dir"],
        cfg["fig_summary_dir"],
        cfg["tab_dir"],
        cfg["log_dir"],
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    log.debug("Output directories ready: %s", cfg["output_root"])


# ── Threshold grid ────────────────────────────────────────────────────────────

def build_percentile_levels(start: float, stop: float, step: float) -> list[float]:
    """Generate a list of percentile levels from start to stop (inclusive).

    Parameters
    ----------
    start, stop : float
        First and last percentile (e.g., 0.50 and 0.90).
    step : float
        Step size (e.g., 0.05 for 5 percentile-point increments).

    Returns
    -------
    list of float, each rounded to 10 decimal places to avoid float drift.
    """
    levels = np.arange(start, stop + step * 0.5, step)
    return [round(float(v), 10) for v in levels]


# ── Data loading: expanded events (Step 2e primary) ──────────────────────────

def load_expanded_events(path: Path) -> pd.DataFrame:
    """Load the expanded documentary coastal-impact database.

    Source file: ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv
    Schema: city, date, coastal_sector, source_title, source_url, notes

    Returns a DataFrame with columns:
        disaster_id   – synthetic int (row index + 1, for compatibility with
                        build_event_records() which reads int(row["disaster_id"]))
        municipality  – string, renamed from "city"
        date          – pd.Timestamp
        coastal_sector
        source_title
        source_url
        notes

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist.
    ValueError
        If required columns are absent or no valid rows remain after cleaning.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Expanded events database not found: {path}\n"
            "Expected: data/reported events/"
            "ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
        )

    df = pd.read_csv(path)

    # Rename "city" → "municipality" for consistency with the rest of the codebase
    if "city" in df.columns:
        df = df.rename(columns={"city": "municipality"})
    elif "municipality" not in df.columns:
        raise ValueError(
            f"Expanded events CSV must have a 'city' or 'municipality' column. "
            f"Found columns: {list(df.columns)}"
        )

    # Require date
    if "date" not in df.columns:
        raise ValueError(
            f"Expanded events CSV must have a 'date' column. "
            f"Found columns: {list(df.columns)}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["municipality", "date"]).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            "Expanded events database is empty after removing rows with missing "
            "municipality or date."
        )

    # Assign synthetic disaster_id (row index + 1, 1-based)
    df.insert(0, "disaster_id", range(1, len(df) + 1))

    # Optional columns — fill with empty string if absent
    for col in ["coastal_sector", "source_title", "source_url", "notes"]:
        if col not in df.columns:
            df[col] = ""

    log.info(
        "Expanded events loaded: %d records | %d municipalities | %s to %s",
        len(df),
        df["municipality"].nunique(),
        df["date"].min().date(),
        df["date"].max().date(),
    )
    return df


# ── Data loading: legacy events (used as E_i evidence source) ────────────────

def load_legacy_events(path: Path) -> pd.DataFrame:
    """Load the legacy Leal et al. (2024) Civil Defense database.

    Used exclusively as a corroborating evidence source for E_i in audit.py.
    Only returns disaster_id, municipality, date, and coastal_sector.

    The legacy CSV uses English column headers with spaces. This loader performs
    minimal cleaning (column rename, date parse, string strip).

    Parameters
    ----------
    path : Path
        Path to reported_events_Karine_sc.csv.

    Returns
    -------
    DataFrame with columns [disaster_id, municipality, date, coastal_sector].
    """
    path = Path(path)
    if not path.exists():
        log.warning(
            "Legacy events file not found: %s — E_i will be 0 for all episodes "
            "(no legacy corroboration available).",
            path,
        )
        return pd.DataFrame(columns=["disaster_id", "municipality", "date", "coastal_sector"])

    df = pd.read_csv(path)

    rename = {
        "Disaster ID":                      "disaster_id",
        "Dates of occurrence (mm/dd/yyyy)": "date",
        "Municipalities":                   "municipality",
        "Coastal Sectors":                  "coastal_sector",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    for col in ["municipality", "coastal_sector"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["disaster_id", "municipality", "date"]).reset_index(drop=True)

    # Keep only needed columns
    keep = ["disaster_id", "municipality", "date", "coastal_sector"]
    df = df[[c for c in keep if c in df.columns]]

    log.info(
        "Legacy events loaded: %d rows | %d unique disaster IDs | %d municipalities",
        len(df),
        df["disaster_id"].nunique() if "disaster_id" in df.columns else 0,
        df["municipality"].nunique(),
    )
    return df


# ── Data loading: unified metocean dataset ────────────────────────────────────

def load_unified_dataset(path: Path) -> xr.Dataset:
    """Load the unified daily metocean dataset and validate key variables.

    Parameters
    ----------
    path : Path
        Path to metocean_sc_full_unified_waverys_grid.nc.

    Returns
    -------
    xr.Dataset with at least VHM0 and zos variables.

    Raises
    ------
    FileNotFoundError, ValueError
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Unified metocean dataset not found: {path}\n"
            "Run src/01_data_preparation/preprocessing first."
        )

    ds = xr.open_dataset(path)

    required = {"VHM0", "zos"}
    missing = required - set(ds.data_vars)
    if missing:
        raise ValueError(
            f"Unified dataset is missing required variable(s): {missing}. "
            f"Available: {list(ds.data_vars)}"
        )

    log.info(
        "Unified dataset: %d days | %d lat × %d lon | %s to %s",
        ds.sizes["time"],
        ds.sizes.get("latitude", ds.sizes.get("lat", "?")),
        ds.sizes.get("longitude", ds.sizes.get("lon", "?")),
        str(ds.time.values[0])[:10],
        str(ds.time.values[-1])[:10],
    )
    return ds


# ── Logging ───────────────────────────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a human-readable formatter.

    Safe to call multiple times; only adds a handler if none is present.
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.setLevel(level)
    root.addHandler(handler)
