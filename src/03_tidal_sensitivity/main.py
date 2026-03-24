"""
Entry point for the tidal sensitivity analysis (OSR11 — Step 2b).

This analysis extends the preliminary compound event occurrence analysis
(src/02_preliminary_compound) by adding FES2022 astronomical tide to the
GLORYS12 SSH signal.

Usage
-----
Run from project root::

    python src/03_tidal_sensitivity/main.py --all

Individual parts::

    python src/03_tidal_sensitivity/main.py --event-figures
    python src/03_tidal_sensitivity/main.py --summary

If no argument is given, --all is assumed.

Pipeline
--------
1. Load unified metocean dataset and reported events  [reuse 02_preliminary_compound]
2. Build event records (municipality → nearest grid point)
3. Compute SSH-only q90 thresholds  [reuse 02_preliminary_compound]
4. Compute FES2022 tidal series for each unique grid point  [NEW]
5. Compute SSH_total = SSH + tide  [NEW]
6. Compute SSH_total q90 thresholds  [NEW]
7. Compute per-event metrics (SSH-only + SSH_total + detection_change)  [NEW]
8. [--event-figures] Generate 3-panel per-event figures (Hs / SSH / SSH_total)
9. [--summary] Generate summary tables and comparison figures
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

from src.tidal_sensitivity.config.analysis_config import CFG
from src.tidal_sensitivity.utils import make_output_dirs
from src.tidal_sensitivity.tides import build_tide_cache
from src.tidal_sensitivity.thresholds import compute_thresholds_total, compute_event_metrics_total
from src.tidal_sensitivity.event_figures import run_event_figures
from src.tidal_sensitivity.summary import run_summary
from src.preliminary_compound.io import load_unified_dataset, load_reported_events
from src.preliminary_compound.events import build_event_records
from src.preliminary_compound.thresholds import compute_thresholds
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
        description="Tidal sensitivity analysis — OSR11 Step 2b",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If no flag is given, --all is assumed.\n"
            "--all runs event figures + summary.\n"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Run all parts (event figures + summary)",
    )
    group.add_argument(
        "--event-figures", action="store_true", dest="event_figures",
        help="Generate 3-panel per-event figures (Hs / SSH / SSH_total)",
    )
    group.add_argument(
        "--summary", action="store_true",
        help="Summary: tables and comparison figures",
    )
    return parser.parse_args()


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = _parse_args()

    run_all = args.all or not any([args.event_figures, args.summary])

    apply_publication_style()
    make_output_dirs()

    log.info("=" * 68)
    log.info("OSR11 — Tidal Sensitivity Analysis (Step 2b)")
    log.info("Input:  %s", CFG["unified_file"])
    log.info("Output: %s", CFG["output_root"])
    log.info("=" * 68)

    # ── Load data (reuse preliminary_compound loaders) ─────────────────────────
    ds        = load_unified_dataset()
    df_events = load_reported_events()

    # ── Build event records ────────────────────────────────────────────────────
    records = build_event_records(ds, df_events)
    if not records:
        log.error("No event records built. Check data and configuration.")
        sys.exit(1)
    log.info("Built %d event records.", len(records))

    # ── SSH-only thresholds (reuse preliminary_compound) ───────────────────────
    log.info("Computing SSH-only q90 thresholds...")
    thresholds_ssh = compute_thresholds(records)

    # ── Compute FES2022 tidal series ───────────────────────────────────────────
    log.info("Computing FES2022 tidal series for all grid points...")
    tide_cache = build_tide_cache(records)

    # ── SSH_total thresholds ───────────────────────────────────────────────────
    log.info("Computing SSH_total (SSH + tide) q90 thresholds...")
    thresholds_total = compute_thresholds_total(records, tide_cache)

    # ── Per-event metrics (SSH-only + SSH_total) ───────────────────────────────
    log.info("Computing per-event metrics (SSH-only + SSH_total)...")
    metrics_df = compute_event_metrics_total(records, thresholds_ssh, thresholds_total, tide_cache)

    # ── Part TS-1: per-event figures ───────────────────────────────────────────
    if run_all or args.event_figures:
        run_event_figures(records, thresholds_ssh, thresholds_total, metrics_df, tide_cache)

    # ── Summary ────────────────────────────────────────────────────────────────
    if run_all or args.summary:
        run_summary(metrics_df, thresholds_total, tide_cache, records)

    log.info("=" * 68)
    log.info("Tidal sensitivity analysis complete.")
    log.info("  Event figures  : %s", CFG["fig_events_dir"])
    log.info("  Summary figures: %s", CFG["fig_summary_dir"])
    log.info("  Tables         : %s", CFG["tab_dir"])
    log.info("=" * 68)


if __name__ == "__main__":
    main()
