"""
Entry point for the threshold calibration analysis (OSR11 — Step 3).

Runs all analysis parts or individual ones via CLI arguments.

Usage
-----
Run from project root::

    python src/02_preliminary_compound/main.py --all

Or as a module::

    python -m src.preliminary_compound.main --all

Individual parts::

    python src/02_preliminary_compound/main.py --event-figures
    python src/02_preliminary_compound/main.py --summary

If no argument is given, --all is assumed.

Pipeline
--------
1. Load unified metocean dataset (data/test/metocean_sc_sul_unified_waverys_grid.nc)
2. Load reported events (data/reported events/reported_events_Karine_sc.csv)
3. Build event records (nearest grid point, 7-day window, full climatological series)
4. Compute q90 thresholds per municipality
5. Compute per-event metrics (raw, normalised, concomitance)
6. [Part TC-1] Generate per-event figures (with MagicA POT exceedance shading)
7. [Summary] Save consolidated table and summary figures
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path to enable absolute imports
_script_dir   = Path(__file__).resolve().parent
_project_root = _script_dir.parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.preliminary_compound.config.analysis_config import CFG
from src.preliminary_compound.io import load_unified_dataset, load_reported_events
from src.preliminary_compound.events import build_event_records
from src.preliminary_compound.thresholds import compute_thresholds, compute_event_metrics
from src.preliminary_compound.event_figures import run_event_figures
from src.preliminary_compound.summary import run_summary
from src.preliminary_compound.utils import make_output_dirs
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
        description="Preliminary compound event occurrence analysis — OSR11 Step 3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If no flag is given, --all is assumed.\n"
            "--all runs event figures + summary.\n"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Run all parts (TC-1 event figures + summary table and figures)",
    )
    group.add_argument(
        "--event-figures", action="store_true", dest="event_figures",
        help="Part TC-1: per-event time series figures with MagicA exceedance shading",
    )
    group.add_argument(
        "--summary", action="store_true",
        help="Summary: consolidated metrics table and cross-event summary figures",
    )
    return parser.parse_args()


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = _parse_args()

    run_all = args.all or not any([args.event_figures, args.summary])

    apply_publication_style()
    make_output_dirs()

    log.info("=" * 68)
    log.info("OSR11 — Preliminary Compound Event Occurrence Analysis (Step 2)")
    log.info("Input:  %s", CFG["unified_file"])
    log.info("Output: %s", CFG["output_root"])
    log.info("=" * 68)

    # ── Load data ─────────────────────────────────────────────────────────────
    ds       = load_unified_dataset()
    df_events = load_reported_events()

    # ── Build event records ───────────────────────────────────────────────────
    records = build_event_records(ds, df_events)
    if not records:
        log.error("No event records built. Check data and configuration.")
        sys.exit(1)

    # ── Compute thresholds and metrics ─────────────────────────────────────────
    thresholds = compute_thresholds(records)
    metrics_df = compute_event_metrics(records, thresholds)

    # ── Part TC-1: per-event figures ──────────────────────────────────────────
    if run_all or args.event_figures:
        run_event_figures(records, thresholds, metrics_df)

    # ── Summary ───────────────────────────────────────────────────────────────
    if run_all or args.summary:
        run_summary(metrics_df, thresholds)

    log.info("=" * 68)
    log.info("Preliminary compound event occurrence analysis complete.")
    log.info("  Event figures : %s", CFG["fig_events_dir"])
    log.info("  Summary figures: %s", CFG["fig_summary_dir"])
    log.info("  Tables        : %s", CFG["tab_dir"])
    log.info("=" * 68)


if __name__ == "__main__":
    main()
