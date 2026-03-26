"""
Configuration for the threshold calibration analysis (OSR11 — Step 4).

This analysis performs a systematic CSI grid scan over pairs of Hₛ and SSH_total
percentile thresholds, using a causal/antecedent matching window to evaluate
threshold performance against the 91-event SC coastal disaster database.

The SSH_total variable (zos + FES2022 tide) is used, consistent with the
decision consolidated in the Tidal Sensitivity Analysis (Step 3 / Step 2b).

Temporal convention
-------------------
The unified GLORYS12/WAVERYS dataset contains daily values with timestamps at
00:00 UTC. FES2022 tides are evaluated at 00:00 UTC each day (instantaneous
snapshot at midnight), consistent with the dataset time convention.

    SSH_total(t) = zos(t, 00:00 UTC) + tide(t, 00:00 UTC)

The D+1 00Z operational tolerance in the matching window accounts for events
whose peak forcing occurred late on civil day D (e.g., 18:00 UTC), which would
appear at 00Z of D+1 in the daily snapshot series.

Threshold sweep
---------------
To change the sweep, modify pct_start, pct_stop, and pct_step below.
The derived hs_percentiles and ssh_total_percentiles lists are computed
automatically from those three values.

    Current setting: q50 to q90 in 5% steps → 9 levels → 81 pairs total.

To test finer resolution (e.g., every 2%):   pct_step = 0.02
To extend the range to q95:                  pct_stop = 0.95
To restrict to q70–q90 only:                 pct_start = 0.70

Domain: Full Santa Catarina coast — same 5 sectors and 91 events as Steps 2–3.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path

# Project root: config/ -> 04_threshold_calibration/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[3]

# ── Threshold sweep parameters ────────────────────────────────────────────────
# Adjust these three values to change the sweep range and resolution.
# Both Hₛ and SSH_total use the same sweep (same grid for each variable).
_PCT_START: float = 0.50   # first percentile to test (inclusive)
_PCT_STOP:  float = 0.90   # last percentile to test (inclusive)
_PCT_STEP:  float = 0.05   # step size — 0.05 = 5 percentile points

_percentile_levels = list(
    np.round(np.arange(_PCT_START, _PCT_STOP + _PCT_STEP / 2, _PCT_STEP), 2)
)

CFG: dict = {
    # ── Inputs (inherited from 02_preliminary_compound and 03_tidal_sensitivity) ─
    "unified_file": ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc",
    "events_file":  ROOT / "data/reported events/reported_events_Karine_sc.csv",

    # ── Municipality–grid reference (produced by src/preprocessing/municipality_grid_ref.py) ──
    # If this file exists it is loaded as the primary source for municipality→grid matching,
    # replacing the single-time-step validity check in build_event_records.
    "municipality_grid_ref": ROOT / "outputs/preprocessing/municipality_grid_ref.csv",

    # ── Tide model settings (same as 03_tidal_sensitivity) ───────────────────
    "tide_models_dir": ROOT / "data/tide_models_clipped_brasil",
    "tide_model": "FES2022",
    "tide_var_name": "tide",
    "ssh_total_var": "zos_total",

    # ── Output paths ──────────────────────────────────────────────────────────
    "output_root":       ROOT / "outputs/threshold_calibration",
    "fig_dir":           ROOT / "outputs/threshold_calibration/figures",
    "fig_events_dir":    ROOT / "outputs/threshold_calibration/figures/events",
    "fig_summary_dir":   ROOT / "outputs/threshold_calibration/figures/summary",
    "tab_dir":           ROOT / "outputs/threshold_calibration/tables",
    "log_dir":           ROOT / "outputs/threshold_calibration/logs",

    # ── Variable names (as in the NetCDF file) ────────────────────────────────
    "hs_var":  "VHM0",   # significant wave height (m)
    "ssh_var": "zos",    # sea surface height above geoid (m)

    # ── Analysis parameters (same as Steps 2–3) ───────────────────────────────
    "target_sector": None,              # all SC sectors
    "event_half_window_days": 3,        # retained for EventRecord compatibility

    # ── Threshold sweep configuration ─────────────────────────────────────────
    # Read-only mirrors of the module-level constants above.
    # To change the sweep: edit _PCT_START, _PCT_STOP, _PCT_STEP at the top.
    "pct_start": _PCT_START,
    "pct_stop":  _PCT_STOP,
    "pct_step":  _PCT_STEP,

    # Derived percentile lists (one per variable; same grid for Hₛ and SSH_total).
    "hs_percentiles":        _percentile_levels,
    "ssh_total_percentiles": _percentile_levels,

    # ── Causal matching window ────────────────────────────────────────────────
    # Offsets (in days) relative to the reported event date D.
    # [D-2, D-1, D, D+1] — D+1 included as operational tolerance for 00:00 UTC snapshots.
    "match_window_offsets": [-2, -1, 0, 1],

    # ── Episode clustering for false alarms ───────────────────────────────────
    # Maximum gap (in days) between compound days that are still merged into
    # the same episode. Set to 1 so that two consecutive compound days with a
    # single gap day are considered one episode.
    "episode_max_gap_days": 1,

    # ── Optimal pair selection hierarchy ─────────────────────────────────────
    # 1. Maximum CSI
    # 2. Minimum FAR (tiebreaker)
    # 3. Most restrictive pair (highest percentile sum, second tiebreaker)
}
