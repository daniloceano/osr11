"""
Data loading for the south SC exploratory analysis.

Loads WAVERYS (wave height), GLORYS12 (sea surface height), and the Leal et al.
(2024) reported-events CSV with basic validation and informational logging.

TEST DATA SCOPE
---------------
The events dataset is filtered to **South sector municipalities only**
to match the spatial coverage of the test NetCDF files (approx. −29.4 to −27.6°S).
This is the intended behaviour for this exploratory phase and is logged explicitly.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import xarray as xr

from src.explore_test_data_south_sc.config.analysis_config import CFG

log = logging.getLogger(__name__)


def load_wave_data() -> xr.Dataset:
    """Load WAVERYS test dataset and validate that VHM0 is present."""
    path = CFG["wave_file"]
    if not path.exists():
        raise FileNotFoundError(f"WAVERYS file not found: {path}")
    ds = xr.open_dataset(path)
    _check_vars(ds, {CFG["wave_var"]}, path)
    log.info(
        "WAVERYS: %d time steps | %d lat | %d lon | %s to %s",
        ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"],
        str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10],
    )
    return ds


def load_glorys_data() -> xr.Dataset:
    """Load GLORYS12 test dataset and validate that zos is present."""
    path = CFG["glorys_file"]
    if not path.exists():
        raise FileNotFoundError(f"GLORYS file not found: {path}")
    ds = xr.open_dataset(path)
    _check_vars(ds, {CFG["ssl_var"]}, path)
    log.info(
        "GLORYS:  %d time steps | %d lat | %d lon | %s to %s",
        ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"],
        str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10],
    )
    return ds


def load_reported_events() -> pd.DataFrame:
    """Load and clean the reported events CSV (Leal et al. 2024).

    Steps
    -----
    1. Rename columns to snake_case.
    2. Strip whitespace and normalise text fields.
    3. Parse dates; replace ``*`` (original missing-data marker) with NaN.
    4. Convert numeric columns.
    5. Drop rows without event ID or municipality.
    6. Filter to ``CFG["target_sector"]`` (South sector) to match test domain.

    Returns
    -------
    pd.DataFrame
        Cleaned and filtered events table.
    """
    path = CFG["events_file"]
    if not path.exists():
        raise FileNotFoundError(f"Events file not found: {path}")

    df = pd.read_csv(path)

    rename = {
        "Disaster ID":                      "disaster_id",
        "Dates of occurrence (mm/dd/yyyy)": "date",
        "Months":                           "month",
        "Municipalities":                   "municipality",
        "Coastal Sectors":                  "coastal_sector",
        "EM or SPC":                        "disaster_type",
        "hgt":                              "hgt_m",
        "Wspd (m/s)":                       "wspd_ms",
        "Wdir (m/s)":                       "wdir_deg",   # label says m/s but values are degrees
        "Hs (m)":                           "hs_m",
        "Hsdir (°)":                        "hsdir_deg",
        "HsPp (s)":                         "hspp_s",
        "WP":                               "weather_pattern",
        "Number of Human Damage":           "n_human_damage",
        "Material Damage (BRL)":            "material_damage_brl",
        "Environmental Damage (BRL)":       "env_damage_brl",
        "Public Economic Losses (BRL)":     "public_losses_brl",
        "Private Economic Losses (BRL)":    "private_losses_brl",
    }
    df = df.rename(columns=rename)

    for col in ["municipality", "coastal_sector", "disaster_type", "month"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.replace("*", pd.NA)

    num_cols = [
        "hgt_m", "wspd_ms", "wdir_deg", "hs_m", "hsdir_deg", "hspp_s",
        "n_human_damage", "material_damage_brl", "env_damage_brl",
        "public_losses_brl", "private_losses_brl",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["disaster_id", "municipality"]).reset_index(drop=True)

    target_sector = CFG["target_sector"]
    n_before = len(df)
    df = df[df["coastal_sector"] == target_sector].copy().reset_index(drop=True)
    log.info(
        "Filtered to %s sector: %d -> %d events (%d removed)",
        target_sector, n_before, len(df), n_before - len(df),
    )
    log.info(
        "Reported events: %d records | %d municipalities | %s to %s",
        len(df), df["municipality"].nunique(),
        df["date"].min().date(), df["date"].max().date(),
    )
    return df


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_vars(ds: xr.Dataset, required: set, path: Path) -> None:
    missing = required - set(ds.data_vars)
    if missing:
        raise ValueError(
            f"Variable(s) {missing} not found in {path.name}. "
            f"Available: {list(ds.data_vars)}"
        )
