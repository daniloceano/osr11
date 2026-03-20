"""
Central configuration for the southern Santa Catarina test data exploratory analysis.

Adjust file paths and analysis parameters here; no other module needs
to be edited to change dataset locations or key thresholds.
"""
from __future__ import annotations

from pathlib import Path

# Project root: config/ -> explore_test_data_south_sc/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[3]

CFG: dict = {
    # ── Input data paths ──────────────────────────────────────────────────────
    "wave_file":   ROOT / "data/test/waverys_sc_sul_test.nc",
    "glorys_file": ROOT / "data/test/glorys_sc_sul_test.nc",
    "events_file": ROOT / "data/reported events/reported_events_Karine_sc.csv",

    # ── Output paths ──────────────────────────────────────────────────────────
    "output_root": ROOT / "outputs/south_sc_test_data_exploratory",
    "fig_dir":     ROOT / "outputs/south_sc_test_data_exploratory/figures",
    "tab_dir":     ROOT / "outputs/south_sc_test_data_exploratory/tables",
    "log_dir":     ROOT / "outputs/south_sc_test_data_exploratory/logs",
    "meta_dir":    ROOT / "outputs/south_sc_test_data_exploratory/metadata",

    # ── Variable names (as in the NetCDF files) ───────────────────────────────
    "wave_var":    "VHM0",   # significant wave height (m)
    "dir_var":     "VMDR",   # mean wave direction (°)
    "ssl_var":     "zos",    # sea surface height above geoid (m)

    # ── Coastal point selection ────────────────────────────────────────────────
    # Path to the Natural Earth 10 m coastline shapefile (.shp)
    "ne_coastline_shp":        ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp",
    # Maximum distance (km) from the coastline to qualify a grid cell as "coastal".
    # At 1/12° resolution (~9.25 km/cell) this corresponds to ~5 grid cells.
    "max_coastal_dist_km":     50.0,

    # ── Analysis parameters ───────────────────────────────────────────────────
    # Lag window (days) to consider two peaks temporally coincident
    "coincidence_window_days": 3,
    # Days around a peak event for time series zoom panels
    "timeseries_window_days":  15,
    # Quantile thresholds for compound co-occurrence quick-look [EDA only]
    # NOT a final compound-event definition for the study.
    "compound_hs_quantile":    0.90,
    "compound_zos_quantile":   0.90,
    # Restrict to South sector municipalities to match the test domain extent
    "target_sector":           "South",
}
