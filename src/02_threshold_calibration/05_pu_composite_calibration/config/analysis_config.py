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

Combined positive-event framework:
    Step 2e uses BOTH reported-event databases as its positive set P:

    1. Expanded documentary database (primary):
       ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv
       - 56 documented ressaca events (1998–2020, 14 municipalities)
       - Curated from news archives, academic theses, technical reports
       - Traceable source citations (URL + title) for each event
       - Explicit marine-forcing evidence (not generic flood reports)
       See ressaca_sc_eventos_sc_1998_2020_repository_methodology.md

    2. Legacy Leal et al. (2024) database:
       reported_events_Karine_sc.csv
       - 91 unique (municipality, date) rows from 72 disasters (1998–2020,
         22 municipalities)
       - Original Civil Defense / insurance damage database

    Combined positive set (via load_combined_events()):
       - 147 unique (municipality, date) pairs (0 exact overlaps)
       - 27 unique municipalities (union of 14 expanded + 22 legacy cities)
       - 2 near-matches (±3 days at Florianópolis, retained as separate events)
       - P for scoring = evaluable events with valid grid associations (~143);
         4 expanded cities (Biguaçu, Imbituba, Joinville, Laguna) are
         structural misses (no grid point in municipality_grid_ref.csv)

Relationship to Step 2d:
    Step 2d (CSI Grid Scan) was a diagnostic step that revealed the limitations
    of classical verification metrics under incomplete reporting (FAR=0.984).
    Step 2e does NOT use the thresholds from Step 2d. Instead, it performs
    an independent threshold sweep using the PU composite score, which is
    designed to handle under-reported impact databases.

Scored detector (recalibrated 2026-07-30):
    Step 2e now scores EXACTLY the production detector. It used to score a
    detector built on SSH_total = zos + tide, a variable the production method
    abandoned on 2026-07-29 (MHWS) and does not read at all under the HAT gate
    adopted on 2026-07-30. Calibrating on a variable the detector never reads
    is a scientific inconsistency; see AUD-01 §14.

        wave  : Hs  >= q_hs  local
        level : zos >= q_zos local            (tide-free; NOT SSH_total)
        gate  : max(SWL) > HAT over the overlap days, with
                SWL = (zos - local mean of zos) + tide_daily_max
                HAT = max(tide_daily_max) over 1993-2025, per grid point

    Everything else is unchanged: matching window, episode audit (E_i, I_i,
    C_i, q_i), composite score, weights, alphas, B_target, sensitivity.

Temporal and spatial conventions:
    Inherited from Steps 2c–2d:
        - VHM0 (Hₛ) = daily maximum from 3-hourly WAVERYS
        - zos = GLORYS12 daily snapshot at 00:00 UTC
        - tide_daily_max = daily maximum of hourly FES2022
        - Directional matching window: [D-2, D-1, D, D+1 00Z]
        - Local percentile thresholds computed from full metocean record

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

# ── Explicit percentile grid (2026-07-30) ────────────────────────────────────
# The grid used to be generated from PCT_START/PCT_STOP/PCT_STEP, which produced
# 9 levels (q50…q90) and 81 pairs. It is now an EXPLICIT LIST because 0.99 does
# not fall on the regular 0.05 step, and AUD-02 §4 recorded that the selected
# optimum sat on the q90 edge of the grid — "um sinal de que o ótimo pode estar
# fora dela". Extending to q95 and q99 tests that directly.
#
#     11 levels × 11 levels = 121 pairs
#
# PCT_START / PCT_STOP / PCT_STEP are DELIBERATELY RETAINED below. They are no
# longer the source of the Step 2e grid, but they remain in CFG so that any
# consumer that reads them (Step 2d shares the same key names in its own
# analysis_config and is diagnostic only) keeps working unchanged. Edit
# PCT_LEVELS to change the Step 2e sweep; editing the three scalars alone has
# no effect on Step 2e.
PCT_LEVELS: list[float] = [
    0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99,
]

PCT_START = 0.50    # retained for compatibility; NOT the Step 2e grid source
PCT_STOP = 0.90     # retained for compatibility; NOT the Step 2e grid source
PCT_STEP = 0.05     # retained for compatibility; NOT the Step 2e grid source

# Episode clustering — maximum gap between compound days within same episode
EPISODE_MAX_GAP_DAYS = 1

# ══════════════════════════════════════════════════════════════════════════════
# COMPOSITE SCORE WEIGHTS (configurable)
# ══════════════════════════════════════════════════════════════════════════════

# Component weights for the composite score: Score(θ) = w1·R_pos - w2·B - w3·F_soft/P
# These should sum to 1.0 for interpretability.
#
# REWEIGHTED 2026-07-30, together with the two-sided burden below.
#
# Under the previous triplet (0.60 / 0.20 / 0.20) the third term dominated the
# score without bound: F_soft/P reached 29.4 at q50/q50 against a maximum
# possible recall contribution of 0.60. Extending the sweep grid past q90 made
# the consequence visible — Spearman(Score, accepted episodes) = -0.999, i.e.
# the score was a monotone preference for detecting nothing, and its optimum
# was the emptiest pair in the grid. See
# outputs/audit/AUD-01_step2e_score_surface/.
#
# The burden now carries the dominant weight because it is the only term
# anchored on an external observation (the reported event rate). The soft
# penalty is retained, at reduced weight, as a tiebreaker on the plausibility
# of unmatched detections rather than as the objective.
W1_RECALL = 0.30        # weight for positive recall R_pos(θ)
W2_BURDEN = 0.60        # weight for burden deviation B(θ)
W3_SOFT_PENALTY = 0.10  # weight for soft unmatched penalty F_soft(θ)

#: Superseded triplet, kept for the record and reproducible via SENSITIVITY_WEIGHTS.
LEGACY_WEIGHTS = {"w1": 0.60, "w2": 0.20, "w3": 0.20}

# ══════════════════════════════════════════════════════════════════════════════
# CONFIDENCE WEIGHT PARAMETERS (q_i components)
# ══════════════════════════════════════════════════════════════════════════════

# Confidence weight: q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)
# These should sum to 1.0.
#
# REWEIGHTED 2026-07-30 — away from external evidence, towards physical
# intensity and context coherence.
#
# Measured on the recalibrated sweep: E_i = 1 in 154 of 436 352 unmatched
# episodes, i.e. 0.04 %. With α_E = 0.60 the confidence weight was therefore
# capped at 0.40 for 99.96 % of episodes BY CONSTRUCTION, so every unmatched
# detection carried a penalty of at least 0.60 regardless of how physically
# plausible it was. That is not a measurement of implausibility; it is a
# measurement of the sparseness of the documentary record.
#
# The whole premise of the PU framework is that the reported record is
# incomplete (AUD-18: no independent validation base exists). Weighting the
# absence of a documentary match at 0.60 contradicts that premise: it treats a
# probable false negative of the Civil Defense register as strong evidence
# against the detection. The weight is moved to the two terms that do not
# depend on the register — the physical intensity of the episode and its
# contextual coherence (season, spatial concurrence, exposure).
ALPHA_E = 0.20  # external evidence (binary; sparse and known to under-report)
ALPHA_I = 0.50  # physical intensity (continuous: percentile exceedance)
ALPHA_C = 0.30  # context coherence (0–1: season + neighbours + exposure)

#: Superseded triplet, kept for the record and reproducible via SENSITIVITY_ALPHA.
LEGACY_ALPHA = {"alpha_E": 0.60, "alpha_I": 0.30, "alpha_C": 0.10}

# ══════════════════════════════════════════════════════════════════════════════
# ANNUAL BURDEN PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# Per-municipality annual detection rate that the detector should reproduce.
#
# CHANGED 2026-07-30 from a one-sided ceiling to a TWO-SIDED ANCHOR.
#
# The former term was
#     B = min(1, (H + U) / (Y × B_target_effective))     with B_target = 12/yr
# which penalises only over-detection and is minimised at ZERO detections. It
# therefore pushed in the same direction as the soft penalty, and raising its
# weight made the "detect nothing" pull stronger, not weaker: sweeping w2 from
# 0.20 to 0.69 left the optimum pinned at the emptiest pair of the grid.
#
# The term is now a deviation from an expected rate, in both directions:
#     rate(θ) = (H + U) / (Y × n_municipalities)
#     B       = min(1, |log10( rate(θ) / BURDEN_TARGET_PER_MUNICIPALITY )|)
#
# A detector that flags far fewer episodes than expected is now penalised as
# much as one that floods, which is what gives the score an interior optimum.
# The log ratio makes the penalty symmetric in relative terms — detecting half
# the expected rate costs the same as detecting twice — and the cap at 1 keeps
# the term in [0, 1] like the other two, so that w1+w2+w3 = 1 is meaningful.
#
# ANCHORING THE RATE — what the observed record does and does not fix:
#   Leal et al. (2024, Nat Hazards 120, 11465-11482) record 72 distinct declared
#   coastal disasters in Santa Catarina over 1998-2023, i.e. 2.77 declared
#   events per year for the whole SC coast. Combined with the expanded
#   documentary archive, the Step 2e positive set holds 147 (municipality, date)
#   pairs over 22.4 validated years across 27 municipalities:
#
#       reported rate = 147 / (22.4 × 27) = 0.243 detections/municipality/year
#
#   That is a LOWER BOUND, not an expectation. Under-reporting is the premise
#   of the whole PU framework, and AUD-18 records that no independent
#   validation base exists against which to measure it. Choosing the anchor
#   therefore means choosing an assumed under-reporting factor, which is a
#   declared assumption and is treated as such: SENSITIVITY_B_TARGET spans
#   0.5 to 6.0/municipality/year, i.e. roughly 2x to 25x the reported rate.
#
#   The default of 2.0 assumes the true rate of compound coastal episodes is
#   about 8x the declared rate — one episode per municipality every six months.
#   The superseded 12.0/yr was never an expectation; the configuration
#   described it as "a climatologically plausible UPPER BOUND", which is 49x
#   the reported rate and unusable as the centre of a two-sided penalty.
BURDEN_TARGET_PER_MUNICIPALITY = 2.0  # expected detections/year/municipality

#: Superseded one-sided ceiling, kept so the old behaviour stays reproducible.
LEGACY_B_TARGET_PER_MUNICIPALITY = 12.0

#: "two_sided" = |log10(rate/target)| capped at 1 (current);
#: "ceiling"   = min(1, rate/target), the superseded one-sided form.
BURDEN_MODE = "two_sided"

# Retained under its former name because scoring.py, sensitivity.py and the
# saved decomposition tables all key on it.
B_TARGET_PER_MUNICIPALITY = BURDEN_TARGET_PER_MUNICIPALITY

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
    {"w1": 0.40, "w2": 0.50, "w3": 0.10, "label": "recall_leaning"},
    {"w1": 0.20, "w2": 0.70, "w3": 0.10, "label": "rate_anchored"},
    {"w1": 0.30, "w2": 0.55, "w3": 0.15, "label": "penalty_leaning"},
    {"w1": 0.30, "w2": 0.60, "w3": 0.10, "label": "default"},
    # The superseded triplet, so its behaviour stays reproducible and auditable.
    {"w1": 0.60, "w2": 0.20, "w3": 0.20, "label": "legacy_2026_07_29"},
]

# Alternative confidence weight triplets
SENSITIVITY_ALPHA = [
    {"alpha_E": 0.30, "alpha_I": 0.45, "alpha_C": 0.25, "label": "evidence_leaning"},
    {"alpha_E": 0.10, "alpha_I": 0.55, "alpha_C": 0.35, "label": "evidence_minimal"},
    {"alpha_E": 0.20, "alpha_I": 0.45, "alpha_C": 0.35, "label": "context_leaning"},
    {"alpha_E": 0.20, "alpha_I": 0.50, "alpha_C": 0.30, "label": "default"},
    # The superseded triplet, which capped q_i at 0.40 for 99.96 % of episodes.
    {"alpha_E": 0.60, "alpha_I": 0.30, "alpha_C": 0.10, "label": "legacy_2026_07_29"},
]

# Alternative expected detection rates (detections/year/municipality), spanning
# roughly 2x to 25x the reported rate of 0.243 that Leal et al. (2024) plus the
# expanded documentary archive establish as a lower bound.
SENSITIVITY_B_TARGET = [0.5, 1.0, 2.0, 3.0, 6.0]

# Alternative episode gap tolerance values (in days).
# Maximum gap between compound days that are merged into the same episode.
# Tests how episode clustering granularity affects the PU score.
SENSITIVITY_GAP_DAYS = [0, 1, 2, 3]

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
    # pct_levels is the authoritative grid; the three scalars are legacy keys.
    "pct_levels": PCT_LEVELS,
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

    # ── Burden anchor (per municipality; two-sided deviation from this rate) ──
    "b_target_per_municipality": B_TARGET_PER_MUNICIPALITY,
    "burden_mode": BURDEN_MODE,

    # ── Context coherence ─────────────────────────────────────────────────────
    "active_season_months": ACTIVE_SEASON_MONTHS,
    "exposed_municipalities": EXPOSED_MUNICIPALITIES,   # list[str] of northern-sector municipality names

    # ── Sensitivity analysis ──────────────────────────────────────────────────
    "sensitivity_weights": SENSITIVITY_WEIGHTS,
    "sensitivity_alpha": SENSITIVITY_ALPHA,
    "sensitivity_b_target": SENSITIVITY_B_TARGET,
    "sensitivity_gap_days": SENSITIVITY_GAP_DAYS,
}
