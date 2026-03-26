"""
Entry point for the threshold calibration analysis (OSR11 — Step 4).

This analysis performs a systematic CSI grid scan over pairs of Hₛ and SSH_total
percentile thresholds, evaluated against the 91-event SC coastal disaster database
using a causal/antecedent matching window.

Usage
-----
Run from project root::

    python src/04_threshold_calibration/main.py --all

Individual parts::

    python src/04_threshold_calibration/main.py --hits-misses
    python src/04_threshold_calibration/main.py --false-alarms
    python src/04_threshold_calibration/main.py --summary

If no argument is given, --all is assumed.

Pipeline
--------
1. Load unified metocean dataset and reported events  [reuse 02_preliminary_compound]
2. Clip dataset to validated period (event date range ± causal window margins)  [NEW]
3. Build event records (municipality → nearest grid point)  [reuse 02_preliminary_compound]
4. Compute FES2022 tidal series for each unique grid point  [reuse 03_tidal_sensitivity]
5. Build SSH_total = SSH + tide series per grid point  [NEW]
6. [--hits-misses] Layer 1: event-by-event hit/miss scan across all threshold pairs
7. [--false-alarms] Layer 2: false alarm count from validated-period scan
8. [--summary] Compute CSI/POD/FAR, select optimal pair, save tables and figures

Temporal domain restriction (Step 2)
-------------------------------------
The unified dataset spans 1993–2025 but the validation database (Leal et al., 2024)
covers only 1998–2023. Scanning the full series in Layer 2 inflates F with compound
episodes in unvalidated years (1993–1997, 2024–2025), which distorts FAR and CSI.

The preprocessing step clips the dataset to:

    [min(event_dates) + min(offsets), max(event_dates) + max(offsets)]

i.e., typically from ~1997-12-30 to ~2023-MM-DD+1 (exact dates depend on the
event database). This restricts both the false alarm scan and the quantile
threshold computation to the same validated temporal domain.

SSH_total rationale
-------------------
Following the Tidal Sensitivity Analysis (Step 3), SSH_total = SSH + FES2022 tide
is used as the sea level variable throughout. The FES2022 model provides daily
(00:00 UTC) tidal predictions consistent with the GLORYS12 snapshot convention.

Causal window
-------------
An observed event on date D is considered captured if the joint compound condition
(Hₛ ≥ thr_hs  AND  SSH_total ≥ thr_ssh) holds at any of:
    D-2, D-1, D, D+1 (operational 00Z tolerance)

See src/04_threshold_calibration/windows.py for full rationale.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_script_dir   = Path(__file__).resolve().parent
_project_root = _script_dir.parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.threshold_calibration.config.analysis_config import CFG
from src.threshold_calibration.preprocessing import clip_to_validated_period
from src.threshold_calibration.utils import make_output_dirs
from src.threshold_calibration.calibration import (
    build_ssh_total_cache,
    run_hits_misses,
    run_false_alarms,
)
from src.threshold_calibration.metrics import compute_scores, rank_combinations, select_optimal_pair
from src.threshold_calibration.summary import run_summary
from src.preliminary_compound.io import load_unified_dataset, load_reported_events
from src.preliminary_compound.events import build_event_records
from src.tidal_sensitivity.tides import build_tide_cache
from config.plot_config import apply_publication_style

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Threshold calibration (CSI grid scan) — OSR11 Step 4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If no flag is given, --all is assumed.\n"
            "--all runs hits/misses + false alarms + summary.\n"
            "--hits-misses only runs Layer 1 (faster, no false alarm scan).\n"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Run all parts (Layer 1 + Layer 2 + summary)",
    )
    group.add_argument(
        "--hits-misses", action="store_true", dest="hits_misses",
        help="Layer 1 only: event-by-event hit/miss scan (no false alarms)",
    )
    group.add_argument(
        "--false-alarms", action="store_true", dest="false_alarms",
        help="Layer 2 only: false alarm count from full-series scan",
    )
    group.add_argument(
        "--summary", action="store_true",
        help="Summary: compute metrics, select optimal pair, save tables and figures",
    )
    return parser.parse_args()


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = _parse_args()

    run_all = args.all or not any([
        getattr(args, "hits_misses", False),
        getattr(args, "false_alarms", False),
        args.summary,
    ])

    apply_publication_style()
    make_output_dirs()

    log.info("=" * 68)
    log.info("OSR11 — Threshold Calibration (Step 4: CSI Grid Scan)")
    log.info("Input:  %s", CFG["unified_file"])
    log.info("Output: %s", CFG["output_root"])
    log.info(
        "Threshold grid: Hₛ × SSH_total → %d × %d = %d pairs",
        len(CFG["hs_percentiles"]),
        len(CFG["ssh_total_percentiles"]),
        len(CFG["hs_percentiles"]) * len(CFG["ssh_total_percentiles"]),
    )
    log.info("=" * 68)

    # ── Load data (reuse preliminary_compound loaders) ─────────────────────────
    ds        = load_unified_dataset()
    df_events = load_reported_events()

    # ── Preprocessing: clip dataset to validated temporal domain ────────────────
    #
    # The unified dataset spans 1993–2025; the reported events cover 1998–2023.
    # Without this step, Layer 2 scans ~7 unvalidated years and classifies any
    # compound episode there as a false alarm, inflating F artificially.
    # Clipping anchors both quantile thresholds and the false alarm scan to the
    # same validated period. See src/04_threshold_calibration/preprocessing.py
    # for the full rationale.
    import pandas as pd
    ds, _t_clip_start, _t_clip_end = clip_to_validated_period(
        ds, df_events, CFG["match_window_offsets"]
    )
    time_index = pd.DatetimeIndex(ds.time.values)

    # ── Build event records (reuse preliminary_compound events module) ──────────
    records = build_event_records(ds, df_events)
    if not records:
        log.error("No event records built. Check data and configuration.")
        sys.exit(1)
    log.info("Built %d event records.", len(records))

    # ── Compute FES2022 tidal series (reuse tidal_sensitivity.tides) ────────────
    log.info("Computing FES2022 tidal series for all unique grid points...")
    tide_cache = build_tide_cache(records)

    # ── Build SSH_total climatological series per grid point ────────────────────
    log.info("Building SSH_total = SSH + tide series per grid point...")
    ssh_total_cache = build_ssh_total_cache(records, tide_cache)

    # ── Layer 1: hits / misses ─────────────────────────────────────────────────
    all_captures = []
    contingency  = None

    if run_all or getattr(args, "hits_misses", False):
        log.info("Layer 1: event-by-event hit/miss grid scan...")
        all_captures, contingency = run_hits_misses(
            records,
            ssh_total_cache,
            time_index,
            CFG["hs_percentiles"],
            CFG["ssh_total_percentiles"],
        )
        log.info("Layer 1 complete. Total capture evaluations: %d", len(all_captures))

    # ── Layer 2: false alarms ──────────────────────────────────────────────────
    false_alarms_df = None

    if run_all or getattr(args, "false_alarms", False):
        log.info("Layer 2: false alarm scan across full series...")
        false_alarms_df = run_false_alarms(
            records,
            ssh_total_cache,
            time_index,
            CFG["hs_percentiles"],
            CFG["ssh_total_percentiles"],
            CFG["episode_max_gap_days"],
        )
        log.info("Layer 2 complete.")

    # ── Summary ────────────────────────────────────────────────────────────────
    if run_all or args.summary:
        if contingency is None or false_alarms_df is None:
            log.error(
                "Summary requires both Layer 1 (--hits-misses) and Layer 2 (--false-alarms) "
                "results. Run with --all or supply both layers first."
            )
            sys.exit(1)

        log.info("Computing CSI/POD/FAR metrics...")
        df_metrics = compute_scores(contingency, false_alarms_df)
        df_ranked  = rank_combinations(df_metrics)
        optimal    = select_optimal_pair(df_metrics)

        run_summary(df_metrics, df_ranked, optimal, all_captures, df_events)

    log.info("=" * 68)
    log.info("Threshold calibration complete.")
    log.info("  Summary figures : %s", CFG["fig_summary_dir"])
    log.info("  Tables          : %s", CFG["tab_dir"])
    log.info("=" * 68)


if __name__ == "__main__":
    main()
