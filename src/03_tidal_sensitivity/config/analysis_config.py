"""
Configuration for the tidal sensitivity analysis (OSR11 — Step 2b).

This analysis extends the preliminary compound event occurrence analysis
(src/02_preliminary_compound) by adding FES2022 astronomical tide to the
GLORYS12 SSH signal, forming a total sea level:

    SSH_total = SSH (zos, GLORYS12/WAVERYS grid) + tide (FES2022)

Both the SSH-only analysis and the SSH_total analysis are run so that results
can be compared directly.

Domain: Full Santa Catarina coast — same 5 sectors and 91 events as Step 2.
"""
from __future__ import annotations

from pathlib import Path

# Project root: config/ -> 03_tidal_sensitivity/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[3]

CFG: dict = {
    # ── Inputs (inherited from 02_preliminary_compound) ──────────────────────
    "unified_file": ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc",
    "events_file":  ROOT / "data/reported events/reported_events_Karine_sc.csv",

    # ── Tide model settings ───────────────────────────────────────────────────
    # Directory containing eo-tides compatible model files.
    # eo-tides expects the subdirectory to match its internal naming convention.
    "tide_models_dir": ROOT / "data/tide_models_clipped_brasil",
    "tide_model": "FES2022",          # eo-tides model identifier
    "tide_var_name": "tide",          # name for tidal column in outputs
    "ssh_total_var": "zos_total",     # name for SSH + tide combined variable

    # ── Output paths ─────────────────────────────────────────────────────────
    "output_root":      ROOT / "outputs/tidal_sensitivity",
    "fig_dir":          ROOT / "outputs/tidal_sensitivity/figures",
    "fig_events_dir":   ROOT / "outputs/tidal_sensitivity/figures/events",
    "fig_summary_dir":  ROOT / "outputs/tidal_sensitivity/figures/summary",
    "fig_comparison_dir": ROOT / "outputs/tidal_sensitivity/figures/comparison",
    "tab_dir":          ROOT / "outputs/tidal_sensitivity/tables",
    "log_dir":          ROOT / "outputs/tidal_sensitivity/logs",

    # ── Variable names (as in the NetCDF file) ────────────────────────────────
    "hs_var":  "VHM0",   # significant wave height (m)
    "ssh_var": "zos",    # sea surface height above geoid (m)

    # ── Analysis parameters (same as 02_preliminary_compound) ─────────────────
    "target_sector": None,             # all SC sectors
    "event_half_window_days": 3,       # ±3 days → 7-day window
    "threshold_quantile": 0.90,        # q90 first-pass threshold
    "pot_min_separation_days": 1,

    # ── Tidal computation ─────────────────────────────────────────────────────
    # Frequency of tidal signal to estimate from FES2022.
    # "D" matches the daily resolution of the unified dataset.
    # eo-tides will compute tides at midnight UTC of each day.
    "tide_freq": "D",
}
