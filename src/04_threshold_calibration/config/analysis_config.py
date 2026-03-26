"""
Configuration for the threshold calibration analysis (OSR11 — Step 4).

This analysis performs a systematic CSI grid scan over pairs of Hₛ and SSH_total
percentile thresholds, using a causal/antecedent matching window to evaluate
threshold performance against the 91-event SC coastal disaster database.

The SSH_total variable (zos + FES2022 tide) is used, consistent with the
decision consolidated in the Tidal Sensitivity Analysis (Step 3 / Step 2b).

Causal window
-------------
An observed event reported on date D is considered captured if the compound
condition (Hs >= thr_hs AND SSH_total >= thr_ssh_total) holds at any of:
    D-2, D-1, D, D+1 00Z (operational tolerance)

D+1 00Z is included because the dataset uses daily snapshots at 00:00 UTC.
An event reported on civil day D may have its peak in the late hours of D,
which appears at 00Z of D+1 in the daily snapshot series.

Threshold grid
--------------
Both Hₛ and SSH_total thresholds are swept from q50 to q90 in steps of 0.05.
Thresholds are computed locally at each municipality's grid point using the
full climatological series (1993–2025).

Domain: Full Santa Catarina coast — same 5 sectors and 91 events as Steps 2–3.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path

# Project root: config/ -> 04_threshold_calibration/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[3]

CFG: dict = {
    # ── Inputs (inherited from 02_preliminary_compound and 03_tidal_sensitivity) ─
    "unified_file": ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc",
    "events_file":  ROOT / "data/reported events/reported_events_Karine_sc.csv",

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

    # ── Threshold grid ────────────────────────────────────────────────────────
    # Both Hₛ and SSH_total are swept over this set of percentiles.
    # q50–q90 in 0.05 steps → 9 levels each → 81 threshold pairs total.
    "hs_percentiles":        list(np.arange(0.50, 0.95, 0.05).round(2)),
    "ssh_total_percentiles": list(np.arange(0.50, 0.95, 0.05).round(2)),

    # ── Causal matching window ────────────────────────────────────────────────
    # Offsets (in days) relative to the reported event date D.
    # [D-2, D-1, D, D+1] — D+1 included as operational tolerance for 00Z snapshots.
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
