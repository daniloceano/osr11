"""
Data loading for the threshold calibration analysis.

Loads the unified daily metocean dataset (VHM0 + zos on the WAVERYS spatial grid)
and the Leal et al. (2024) reported-events CSV.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import xarray as xr

from src.preliminary_compound.config.analysis_config import CFG

log = logging.getLogger(__name__)


def load_unified_dataset() -> xr.Dataset:
    """Load the unified daily metocean dataset and validate key variables."""
    path = CFG["unified_file"]
    if not path.exists():
        raise FileNotFoundError(
            f"Unified dataset not found: {path}\n"
            "Run src/preprocessing/interpolate_glorys_to_waverys_grid.py first."
        )
    ds = xr.open_dataset(path)
    required = {CFG["hs_var"], CFG["ssh_var"]}
    _check_vars(ds, required, path)
    log.info(
        "Unified dataset: %d days | %d lat | %d lon | %s to %s",
        ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"],
        str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10],
    )
    return ds


def load_reported_events() -> pd.DataFrame:
    """Load and clean the reported events CSV (Leal et al. 2024).

    Applies the same cleaning steps as the exploratory analysis:
    column renaming, date parsing, numeric coercion, missing-value handling,
    and filtering to the target coastal sector.
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
        "Wdir (m/s)":                       "wdir_deg",
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

    df = df.dropna(subset=["disaster_id", "municipality", "date"]).reset_index(drop=True)

    target_sector = CFG["target_sector"]
    n_before = len(df)
    if target_sector is not None:
        df = df[df["coastal_sector"] == target_sector].copy().reset_index(drop=True)
        log.info(
            "Events filtered to %s sector: %d -> %d records (%d removed)",
            target_sector, n_before, len(df), n_before - len(df),
        )
    else:
        df = df.copy().reset_index(drop=True)
        log.info(
            "Events: all SC sectors retained (%d records across %d sectors)",
            len(df), df["coastal_sector"].nunique(),
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
