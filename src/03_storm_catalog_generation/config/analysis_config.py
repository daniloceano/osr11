"""
Configuration for Step 3 — Hazard Characterization of Extreme and Compound
Coastal Events.

Part of the OSR11 pipeline.
Location: src/03_storm_catalog_generation/

This step applies the PU-optimal thresholds from Step 2e to the full metocean
record (1993–2025) and produces independent storm catalogs for Hs and tide-free
sea level (zos) at each coastal grid point, then runs the full hazard
characterization suite: compound detection, duration/persistence, seasonality,
trends (Mann–Kendall + Sen slope), univariate EVA (POT–GPD), and dependence
analysis (τ, ρ, χ, χ̄).

Threshold source:
    The sole authoritative threshold pair is from Step 2e (PU Composite
    Calibration): outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv
    Step 2d (CSI Grid Scan) thresholds are NOT used.

Level variable (changed 2026-07-31 by AUD-01):
    The level catalogue is segmented on raw ``zos`` — tide-free — and NOT on
    SSH_total. The audit established that a percentile of zos + tide is set by
    tidal phase rather than by storm forcing: north of 20 S the tide carries
    96-98 % of the variance of SSH_total, so a local q90 of SSH_total is in
    practice the spring-tide envelope, and exceedances recur fortnightly by
    construction with no storm involved.

    The astronomical tide re-enters the method as a *gate*, not as part of the
    detection threshold. A compound event is accepted only where the still-water
    level reaches the local Highest Astronomical Tide:

        HAT    = max(tide_daily_max) over 1993-2025, per grid point
        SWL(d) = (zos(d) - mean(zos)) + tide_daily_max(d)
        gate   : max(SWL) over the shared days > HAT

    zos is de-meaned because it is referenced to the geoid while HAT is a height
    above local mean sea level; the two are only comparable after removing the
    local offset.

    The superseded definition, retained here for the record:
        SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)

Threshold computation period:
    Local percentile thresholds are computed from the FULL metocean record
    (1993–2025), consistent with the corrected Step 2e implementation.
    The validated period (1998–2020) restricts only the event-matching scan in
    Step 2e, not the climatological percentile computation.

Episode clustering:
    EPISODE_MAX_GAP_DAYS = 1 inherited from Step 2e.
    Two exceedance days belong to the same episode if separated by at most
    1 non-exceedance day.

Spatial scope:
    Coastal grid points are identified from the unified metocean dataset using
    the Natural Earth 10m coastline (same approach as Step 2a). The pipeline
    supports both the SC test fixture and a full-domain production run.
"""
from __future__ import annotations

from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# PROJECT ROOT
# ══════════════════════════════════════════════════════════════════════════════

# config/ → 03_storm_catalog_generation/ → src/ → root
ROOT = Path(__file__).resolve().parents[3]

# ══════════════════════════════════════════════════════════════════════════════
# RUN MODE
# ══════════════════════════════════════════════════════════════════════════════

# "test"  → SC fixture: data/test/metocean_sc_full_unified_waverys_grid.nc
# "production" → full  domain: data/unified/metocean_brazil_unified_waverys_grid.nc
#                (must be produced by rerunning Step 1 on the full-domain raw data)
RUN_MODE = "test"

# ══════════════════════════════════════════════════════════════════════════════
# INPUT PATHS
# ══════════════════════════════════════════════════════════════════════════════

# ── Unified metocean datasets ─────────────────────────────────────────────────
# Test fixture (SC coast, committed to repo)
UNIFIED_FILE_TEST = ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc"

# Production (full Brazilian coast — must be generated before full-domain run)
UNIFIED_FILE_PRODUCTION = ROOT / "data/unified/metocean_brazil_unified_waverys_grid.nc"

# Resolved at runtime based on RUN_MODE
UNIFIED_FILE = UNIFIED_FILE_TEST if RUN_MODE == "test" else UNIFIED_FILE_PRODUCTION

# ── Step 2e optimal threshold pair ────────────────────────────────────────────
OPTIMAL_PAIR_FILE = ROOT / "outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv"

# ── Municipality–grid reference (SC, for QA and backward compatibility) ───────
MUNICIPALITY_GRID_REF = ROOT / "outputs/preprocessing/municipality_grid_ref.csv"

# ── Tide model settings (same as Steps 2c–2e) ────────────────────────────────
TIDE_MODELS_DIR = ROOT / "data/tide_models_clipped_brasil"
TIDE_MODEL = "FES2022"

# ── Coastline shapefile (for coastal grid selection) ──────────────────────────
COASTLINE_SHP = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT PATHS
# ══════════════════════════════════════════════════════════════════════════════

OUTPUT_ROOT = ROOT / "outputs/storm_catalog"
CATALOG_DIR = OUTPUT_ROOT
TAB_DIR = OUTPUT_ROOT / "tables"
FIG_DIR = OUTPUT_ROOT / "figures"
LOG_DIR = OUTPUT_ROOT / "logs"

# ── Hazard characterization submodule outputs ─────────────────────────────────
COMPOUND_DIR = OUTPUT_ROOT / "compound"
DURATION_DIR = OUTPUT_ROOT / "duration_persistence"
SEASONALITY_DIR = OUTPUT_ROOT / "seasonality"
TRENDS_DIR = OUTPUT_ROOT / "trends"
EVA_DIR = OUTPUT_ROOT / "eva"
DEPENDENCE_DIR = OUTPUT_ROOT / "dependence"

# ══════════════════════════════════════════════════════════════════════════════
# VARIABLE NAMES (as in the unified NetCDF file)
# ══════════════════════════════════════════════════════════════════════════════

HS_VAR = "VHM0"           # significant wave height (m), daily max
SSH_VAR = "zos"            # sea surface height above geoid (m), 00:00 UTC
SSH_TOTAL_VAR = "SSH_total"  # superseded level variable; no longer segmented
TIDE_DAILY_MAX_VAR = "tide_daily_max"  # pre-computed FES2022 daily-max tide

# ══════════════════════════════════════════════════════════════════════════════
# LEVEL VARIABLE FOR THE STORM CATALOGUE
# ══════════════════════════════════════════════════════════════════════════════

#: Dataset variable segmented into level storm episodes. Since 2026-07-31 this
#: is tide-free ``zos``; see the module docstring for why SSH_total was retired.
LEVEL_VAR = SSH_VAR

#: Field-name prefix for the level catalogue (``thr_zos_pct``, ``peak_zos``, …).
#: The prefix is part of the published schema, so it says what the quantity
#: actually is — the site has twice shipped figures labelled SSH_total over
#: tide-free data, and a prefix that lies is how that happens.
LEVEL_PREFIX = "zos"

#: Filename of the level catalogue written by Step 3.1.
LEVEL_CATALOG_NAME = f"catalog_{LEVEL_PREFIX}_storms.json"

# ══════════════════════════════════════════════════════════════════════════════
# TIDE / SSH_TOTAL MODE
# ══════════════════════════════════════════════════════════════════════════════
#
# Controls how SSH_total is obtained for storm catalog generation.
# Three modes are supported:
#
# "auto" (DEFAULT, RECOMMENDED)
#     Detect at runtime which variables are available in the unified NetCDF:
#     - If SSH_total exists → use it directly (fastest, production mode)
#     - Elif tide_daily_max + zos exist → reconstruct SSH_total = zos + tide
#     - Else → fall back to on-the-fly FES2022 computation (legacy mode)
#
# "precomputed"
#     Require SSH_total to be present in the dataset. Fail if absent.
#     Use this to enforce production-mode behavior.
#
# "runtime"
#     Always compute FES2022 tides at runtime, ignoring any pre-computed
#     fields. This is the legacy behavior from the test-mode smoke test.
#     Slow (~10 s/point × N points). Only appropriate for small domains.
#
TIDE_MODE = "auto"

# ══════════════════════════════════════════════════════════════════════════════
# THRESHOLD PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════

# These are READ from tab_TC5_optimal_pair_pu.csv at runtime.
# Do NOT hardcode percentile values here; they are loaded dynamically.
# The full metocean record is used for percentile computation.

# ══════════════════════════════════════════════════════════════════════════════
# EPISODE CLUSTERING
# ══════════════════════════════════════════════════════════════════════════════

# Maximum gap (in non-exceedance days) allowed within a single episode.
# Inherited from Step 2e: two exceedance days separated by at most
# EPISODE_MAX_GAP_DAYS non-exceedance days belong to the same episode.
EPISODE_MAX_GAP_DAYS = 1

# ══════════════════════════════════════════════════════════════════════════════
# COASTAL GRID SELECTION
# ══════════════════════════════════════════════════════════════════════════════

# Maximum distance (km) from Natural Earth coastline for a grid point to be
# classified as "coastal". Same default as Step 2a.
COASTAL_MAX_DIST_KM = 50.0

# Minimum fraction of valid (non-NaN) time steps for a variable at a grid
# point. Grid points below this threshold are logged and excluded.
MIN_VALID_FRAC = 0.80

# ══════════════════════════════════════════════════════════════════════════════
# TIDE CONFIGURATION (for runtime mode only)
# ══════════════════════════════════════════════════════════════════════════════

# Tide variable name (used internally)
TIDE_VAR = "tide"
