"""
Central configuration for the preliminary compound event occurrence analysis.

Uses the unified metocean dataset (WAVERYS grid, daily resolution) as input.
Adjust file paths and parameters here; no other module needs to be edited
to change dataset locations or key thresholds.

Domain: Full Santa Catarina coast — all five sectors of the Leal et al. (2024)
database (North, Central-north, Central, Central-south, South).
"""
from __future__ import annotations

from pathlib import Path

# Project root: config/ -> 02_preliminary_compound/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[3]

CFG: dict = {
    # ── Input data paths ──────────────────────────────────────────────────────
    # Unified daily dataset: VHM0, VMDR, zos all on the WAVERYS spatial grid.
    # Full SC domain: lat −29.4° to −26.0°, covers all Leal et al. (2024) sectors.
    "unified_file": ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc",
    "events_file":  ROOT / "data/reported events/reported_events_Karine_sc.csv",

    # ── Output paths ──────────────────────────────────────────────────────────
    "output_root":      ROOT / "outputs/preliminary_compound",
    "fig_dir":          ROOT / "outputs/preliminary_compound/figures",
    "fig_events_dir":   ROOT / "outputs/preliminary_compound/figures/events",
    "fig_summary_dir":  ROOT / "outputs/preliminary_compound/figures/summary",
    "tab_dir":          ROOT / "outputs/preliminary_compound/tables",
    "log_dir":          ROOT / "outputs/preliminary_compound/logs",

    # ── Variable names (as in the NetCDF file) ────────────────────────────────
    "hs_var":  "VHM0",   # significant wave height (m)
    "ssh_var": "zos",    # sea surface height above geoid (m)

    # ── Analysis parameters ───────────────────────────────────────────────────
    # Sector filter for reported events. Set to None to include all SC sectors.
    # Previously "South" (restricted to south SC test domain).
    "target_sector": None,

    # Half-window on each side of the event date (total window = 2*half + 1 days)
    "event_half_window_days": 3,   # 3 before + event day + 3 after = 7 days

    # Quantile for preliminary first-pass threshold (q90)
    "threshold_quantile": 0.90,    # q90 of the full climatological series

    # Minimum separation for MagicA POT declustering (days)
    "pot_min_separation_days": 1,

    # Number of top events to show in the summary ranking figure
    "n_top_events_summary": 10,
}
