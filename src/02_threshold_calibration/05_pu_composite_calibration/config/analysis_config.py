"""
Configuration for Step 2e — PU Composite Calibration.

Part of STEP 2 — Threshold Calibration (umbrella step).
Location: src/02_threshold_calibration/05_pu_composite_calibration/

This sub-step calibrates compound event detection thresholds using a
positive-unlabeled (PU) composite score that treats unmatched detected
episodes as unlabeled rather than as automatically false alarms.

Methodology reference:
    osr11_option_c_methodology.md — "Proposed composite score for threshold
    calibration under impact under-reporting"

Reported events database:
    This step uses the expanded documentary coastal-impact database
    (ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv), which was
    curated from news archives, academic theses/dissertations, and technical
    reports. See ressaca_sc_eventos_sc_1998_2020_repository_methodology.md
    for the full documentary search and curation protocol.

    The expanded database provides:
        - 56 documented ressaca events (1998–2020)
        - Municipality-level resolution with coastal sector attribution
        - Traceable source citations (URL + title) for each event
        - Explicit marine-forcing evidence (not generic flood reports)

Relationship to Step 2d:
    Step 2d (CSI Grid Scan) was a diagnostic step that revealed the limitations
    of classical verification metrics under incomplete reporting (FAR=0.984).
    Step 2e does NOT use the thresholds from Step 2d. Instead, it performs
    an independent threshold sweep using the PU composite score, which is
    designed to handle under-reported impact databases.

Temporal and spatial conventions:
    Inherited from Steps 2c–2d:
        - SSH_total = zos(00:00 UTC) + tide(daily max)
        - VHM0 (Hₛ) = daily maximum from 3-hourly WAVERYS
        - Directional matching window: [D-2, D-1, D, D+1 00Z]
        - Local percentile thresholds computed from validated period

Weight interpretation (default values from methodology document):
    - w1, w2, w3: Composite score component weights (sum to 1.0)
        w1 = 0.60 — positive recall (primary objective)
        w2 = 0.20 — annual burden penalty
        w3 = 0.20 — soft unmatched penalty

    - alpha_E, alpha_I, alpha_C: Confidence weight components (sum to 1.0)
        alpha_E = 0.60 — external evidence (Civil Defense, news)
        alpha_I = 0.30 — physical intensity (percentile exceedance)
        alpha_C = 0.10 — context coherence (season, neighbors, exposure)
"""
from __future__ import annotations

from pathlib import Path

# Project root: config/ -> 05_pu_composite_calibration/ -> 02_threshold_calibration/ -> src/ -> root
ROOT = Path(__file__).resolve().parents[4]

# ══════════════════════════════════════════════════════════════════════════════
# INPUT PATHS
# ══════════════════════════════════════════════════════════════════════════════

# Unified metocean dataset (produced by Step 1)
UNIFIED_FILE = ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc"

# ── Reported events database (expanded documentary archive) ──────────────────
# Primary: Expanded database from documentary search (news, theses, reports)
# See: ressaca_sc_eventos_sc_1998_2020_repository_methodology.md
EVENTS_FILE = ROOT / "data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
EVENTS_METHODOLOGY = ROOT / "data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md"

# Legacy: Original Leal et al. (2024) Civil Defense database (91 events)
# Retained for comparison but NOT used as primary input for Step 2e.
EVENTS_FILE_LEGACY = ROOT / "data/reported events/reported_events_Karine_sc.csv"

# ── Municipality–grid reference (produced by preprocessing) ──────────────────
MUNICIPALITY_GRID_REF = ROOT / "outputs/preprocessing/municipality_grid_ref.csv"

# ── Step 2d outputs (diagnostic reference only) ──────────────────────────────
# These are used for comparison with CSI-based results, NOT as threshold inputs.
# Step 2e performs its own independent threshold sweep.
CSI_METRICS_FILE = ROOT / "outputs/threshold_calibration/tables/tab_TC4_metrics_full.csv"
OPTIMAL_PAIR_FILE = ROOT / "outputs/threshold_calibration/tables/tab_TC4_optimal_pair.csv"

# ── Tide model settings (same as Steps 2c–2d) ────────────────────────────────
TIDE_MODELS_DIR = ROOT / "data/tide_models_clipped_brasil"
TIDE_MODEL = "FES2022"

# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT PATHS
# ══════════════════════════════════════════════════════════════════════════════

OUTPUT_ROOT = ROOT / "outputs/threshold_calibration"
FIG_DIR = OUTPUT_ROOT / "figures"
FIG_SUMMARY_DIR = OUTPUT_ROOT / "figures/summary"
TAB_DIR = OUTPUT_ROOT / "tables"
LOG_DIR = OUTPUT_ROOT / "logs"

# Audit database (manual input — external evidence flags)
# This CSV should be created/updated by the researcher during the audit process.
AUDIT_DATABASE = ROOT / "data/audit/unmatched_episode_audit.csv"

# ══════════════════════════════════════════════════════════════════════════════
# VARIABLE NAMES (as in the unified NetCDF file)
# ══════════════════════════════════════════════════════════════════════════════

HS_VAR = "VHM0"         # significant wave height (m)
SSH_VAR = "zos"         # sea surface height above geoid (m)
TIDE_VAR = "tide"       # FES2022 astronomical tide (m)
SSH_TOTAL_VAR = "zos_total"  # zos + tide

# ══════════════════════════════════════════════════════════════════════════════
# DIRECTIONAL MATCHING WINDOW (same as Step 2d)
# ══════════════════════════════════════════════════════════════════════════════

# Offsets (in days) relative to the reported event date D.
# The window is asymmetric and causal: [D-2, D-1, D, D+1 00Z].
MATCH_WINDOW_OFFSETS = [-2, -1, 0, 1]

# ══════════════════════════════════════════════════════════════════════════════
# THRESHOLD SWEEP CONFIGURATION (same as Step 2d by default)
# ══════════════════════════════════════════════════════════════════════════════

PCT_START = 0.50    # first percentile to test (inclusive)
PCT_STOP = 0.90     # last percentile to test (inclusive)
PCT_STEP = 0.05     # step size — 0.05 = 5 percentile points

# Episode clustering — maximum gap between compound days within same episode
EPISODE_MAX_GAP_DAYS = 1

# ══════════════════════════════════════════════════════════════════════════════
# COMPOSITE SCORE WEIGHTS (configurable)
# ══════════════════════════════════════════════════════════════════════════════

# Component weights for the composite score: Score(θ) = w1·R_pos - w2·B - w3·F_soft/P
# These should sum to 1.0 for interpretability.
W1_RECALL = 0.60        # weight for positive recall R_pos(θ)
W2_BURDEN = 0.20        # weight for annual burden B(θ)
W3_SOFT_PENALTY = 0.20  # weight for soft unmatched penalty F_soft(θ)/P

# ══════════════════════════════════════════════════════════════════════════════
# CONFIDENCE WEIGHT PARAMETERS (q_i components)
# ══════════════════════════════════════════════════════════════════════════════

# Confidence weight: q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)
# These should sum to 1.0.
ALPHA_E = 0.60  # external evidence weight (binary: Civil Defense, news sources)
ALPHA_I = 0.30  # physical intensity weight (continuous: percentile exceedance)
ALPHA_C = 0.10  # context coherence weight (0–1: season + neighbors + exposure)

# ══════════════════════════════════════════════════════════════════════════════
# ANNUAL BURDEN PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# Per-municipality annual burden target.
#
# The effective B_target is computed at run time as:
#     B_target_effective = B_TARGET_PER_MUNICIPALITY × n_municipalities
#
# where n_municipalities is the number of unique municipalities with valid grid
# associations in the event records (determined from the expanded events database).
#
# SCIENTIFIC RATIONALE:
#   One event per month per municipality (~12/year) is a climatologically
#   plausible upper bound for compound coastal events on the SC coast. It
#   implies that, for every municipality being monitored, the detector should
#   not flag more than ~12 compound episodes per year on average. Scaling by
#   n_municipalities ensures the total domain budget grows proportionally with
#   spatial coverage, avoiding penalising analyses with more municipalities.
#
# Example: 14 municipalities → B_target_effective = 12 × 14 = 168 ep/yr
B_TARGET_PER_MUNICIPALITY = 12.0  # episodes per year per municipality

# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT COHERENCE PARAMETERS (C_i components)
# ══════════════════════════════════════════════════════════════════════════════

# Active season months for storm-wave coastal impacts in SC (climatological)
# Used for C_i^season indicator.
ACTIVE_SEASON_MONTHS = [4, 5, 6, 7, 8, 9, 10]  # April–October (autumn–winter–early spring)

# Exposed municipalities — northern-sector Santa Catarina coastal municipalities.
# Used for C_i^exposure indicator: C_i^exposure = 1 for episodes at these municipalities.
#
# SCIENTIFIC RATIONALE (Step 2e authoritative decision):
#   The northern sector (Itapoá, São Francisco do Sul, Araquari, Balneário Barra do Sul,
#   Barra Velha) is treated as high-exposure because:
#     1. These municipalities are in the northernmost part of the Santa Catarina coast,
#        exposed to a distinct wave climate influenced by NE swell and tropical systems.
#     2. Grid coverage for GLORYS12/WAVERYS in this sector is partially degraded (higher
#        NaN fractions due to shallow bathymetry and complex coastline geometry), making
#        real events more likely to appear as unmatched detections even when they occurred.
#     3. Treating these municipalities as exposure-vulnerable increases the soft plausibility
#        of unmatched episodes there, partially compensating for the model coverage gap.
#
#   NOTE: This list uses municipality names (strings) matching the keys in
#   src/02_threshold_calibration/02_preliminary_compound/events.py::_SOUTH_SC_COORDS.
#   IBGE codes are not used because municipality names are the primary join key in all
#   event records throughout this project.
EXPOSED_MUNICIPALITIES: list[str] = [
    "Itapoá",
    "São Francisco do Sul",
    "Araquari",
    "Balneário Barra do Sul",
    "Barra Velha",
]

# ══════════════════════════════════════════════════════════════════════════════
# SENSITIVITY ANALYSIS CONFIGURATIONS
# ══════════════════════════════════════════════════════════════════════════════

# Alternative weight triplets for sensitivity experiments (methodology section 2.X.9)
SENSITIVITY_WEIGHTS = [
    {"w1": 0.70, "w2": 0.15, "w3": 0.15, "label": "high_recall"},
    {"w1": 0.50, "w2": 0.25, "w3": 0.25, "label": "balanced"},
    {"w1": 0.60, "w2": 0.20, "w3": 0.20, "label": "default"},
]

# Alternative confidence weight triplets
SENSITIVITY_ALPHA = [
    {"alpha_E": 0.70, "alpha_I": 0.20, "alpha_C": 0.10, "label": "evidence_heavy"},
    {"alpha_E": 0.50, "alpha_I": 0.40, "alpha_C": 0.10, "label": "intensity_moderate"},
    {"alpha_E": 0.60, "alpha_I": 0.30, "alpha_C": 0.10, "label": "default"},
]

# Alternative per-municipality B_target values (episodes/year/municipality).
# Effective domain budget = value × n_municipalities at run time.
SENSITIVITY_B_TARGET = [6.0, 12.0, 18.0, 24.0]

# ══════════════════════════════════════════════════════════════════════════════
# CONSOLIDATED CONFIGURATION DICTIONARY
# ══════════════════════════════════════════════════════════════════════════════

CFG: dict = {
    # ── Inputs ────────────────────────────────────────────────────────────────
    "unified_file": UNIFIED_FILE,
    "events_file": EVENTS_FILE,                     # expanded documentary database
    "events_methodology": EVENTS_METHODOLOGY,       # methodology documentation
    "events_file_legacy": EVENTS_FILE_LEGACY,       # legacy Leal et al. (for comparison)
    "municipality_grid_ref": MUNICIPALITY_GRID_REF,
    "audit_database": AUDIT_DATABASE,

    # Step 2d outputs (diagnostic comparison only — NOT used for threshold selection)
    "csi_metrics_file": CSI_METRICS_FILE,
    "optimal_pair_file": OPTIMAL_PAIR_FILE,

    # Tide model
    "tide_models_dir": TIDE_MODELS_DIR,
    "tide_model": TIDE_MODEL,
    "tide_var_name": TIDE_VAR,
    "ssh_total_var": SSH_TOTAL_VAR,

    # ── Outputs ───────────────────────────────────────────────────────────────
    "output_root": OUTPUT_ROOT,
    "fig_dir": FIG_DIR,
    "fig_summary_dir": FIG_SUMMARY_DIR,
    "tab_dir": TAB_DIR,
    "log_dir": LOG_DIR,

    # ── Variables ─────────────────────────────────────────────────────────────
    "hs_var": HS_VAR,
    "ssh_var": SSH_VAR,

    # ── Matching window ───────────────────────────────────────────────────────
    "match_window_offsets": MATCH_WINDOW_OFFSETS,

    # ── Threshold sweep (Step 2e performs its own independent sweep) ──────────
    "pct_start": PCT_START,
    "pct_stop": PCT_STOP,
    "pct_step": PCT_STEP,
    "episode_max_gap_days": EPISODE_MAX_GAP_DAYS,

    # ── Composite score weights ───────────────────────────────────────────────
    "w1_recall": W1_RECALL,
    "w2_burden": W2_BURDEN,
    "w3_soft_penalty": W3_SOFT_PENALTY,

    # ── Confidence weight parameters ──────────────────────────────────────────
    "alpha_E": ALPHA_E,
    "alpha_I": ALPHA_I,
    "alpha_C": ALPHA_C,

    # ── Annual burden (per municipality; effective = value × n_municipalities) ──
    "b_target_per_municipality": B_TARGET_PER_MUNICIPALITY,

    # ── Context coherence ─────────────────────────────────────────────────────
    "active_season_months": ACTIVE_SEASON_MONTHS,
    "exposed_municipalities": EXPOSED_MUNICIPALITIES,   # list[str] of northern-sector municipality names

    # ── Sensitivity analysis ──────────────────────────────────────────────────
    "sensitivity_weights": SENSITIVITY_WEIGHTS,
    "sensitivity_alpha": SENSITIVITY_ALPHA,
    "sensitivity_b_target": SENSITIVITY_B_TARGET,
}
