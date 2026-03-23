"""
Entry point for the south SC test data exploratory analysis.

Runs all analysis parts or individual ones via CLI arguments.
All datasets are loaded upfront; parts share the same loaded objects.

Usage
-----
Run from project root::

    python src/explore_test_data_south_sc/main.py --all

Or run as a module::

    python -m src.explore_test_data_south_sc.main --all

Run individual parts::

    python src/explore_test_data_south_sc/main.py --maps
    python src/explore_test_data_south_sc/main.py --timeseries
    python src/explore_test_data_south_sc/main.py --reported-events
    python src/explore_test_data_south_sc/main.py --municipalities
    python src/explore_test_data_south_sc/main.py --sector-boxplots
    python src/explore_test_data_south_sc/main.py --statistics
    python src/explore_test_data_south_sc/main.py --write-readmes

If no argument is given, --all is assumed.

Parts that depend on the municipality-grid association (--sector-boxplots,
--statistics) will run Part E automatically when called in isolation.
Parts B (--timeseries) will run Part A automatically to obtain peak locations.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path to enable absolute imports
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Now use absolute imports that work from anywhere
from src.explore_test_data_south_sc.boxplots import run_sector_figures
from src.explore_test_data_south_sc.config.analysis_config import CFG
from src.explore_test_data_south_sc.io import (
    load_glorys_data,
    load_reported_events,
    load_wave_data,
)
from src.explore_test_data_south_sc.maps import run_spatial_analysis
from src.explore_test_data_south_sc.metadata import write_data_readmes
from src.explore_test_data_south_sc.municipalities import run_municipality_grid_association
from src.explore_test_data_south_sc.reported_events import run_reported_events_eda
from src.explore_test_data_south_sc.statistics import run_additional_analyses
from src.explore_test_data_south_sc.timeseries import run_timeseries_analysis
from src.explore_test_data_south_sc.utils import make_output_dirs
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
        description="South SC test data exploratory analysis (OSR11)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If no flag is given, --all is assumed.\n"
            "Parts B and F/G compute their prerequisites automatically when run alone."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Run all analysis parts (A, B, D, E, F, G) and write data READMEs",
    )
    group.add_argument("--maps",           action="store_true",
                       help="Part A: spatial maximum maps (nearshore point analysis)")
    group.add_argument("--timeseries",     action="store_true",
                       help="Part B: time series at peak grid points")
    group.add_argument("--reported-events", action="store_true", dest="reported_events",
                       help="Part D: exploratory analysis of the reported events database")
    group.add_argument("--municipalities",  action="store_true",
                       help="Part E: municipality–grid association via IBGE API")
    group.add_argument("--sector-boxplots", action="store_true", dest="sector_boxplots",
                       help="Part F: per-sector map + Hs/SSH boxplot figures")
    group.add_argument("--statistics",      action="store_true",
                       help="Part G: scatter, seasonal cycle, compound quick-look, distributions")
    group.add_argument("--write-readmes",   action="store_true", dest="write_readmes",
                       help="Regenerate data/test/README.md and data/reported events/README.md")
    return parser.parse_args()


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = _parse_args()

    run_all = args.all or not any([
        args.maps, args.timeseries, args.reported_events,
        args.municipalities, args.sector_boxplots, args.statistics,
        args.write_readmes,
    ])

    apply_publication_style()
    make_output_dirs()

    log.info("=" * 62)
    log.info("OSR11 — South SC test data exploratory analysis")
    log.info("Output root: %s", CFG["output_root"])
    log.info("=" * 62)

    # Load all datasets upfront (shared across parts)
    ds_wave   = load_wave_data()
    ds_gl     = load_glorys_data()
    df_events = load_reported_events()

    # Lazily computed prerequisites
    max_hs = max_zos = grid_table = None

    # ── Part A: spatial maximum maps ─────────────────────────────────────
    if run_all or args.maps:
        max_hs, max_zos = run_spatial_analysis(ds_wave, ds_gl)

    # ── Part B: time series at peak grid points ───────────────────────────
    if run_all or args.timeseries:
        if max_hs is None or max_zos is None:
            log.info("(Running Part A as prerequisite for Part B)")
            max_hs, max_zos = run_spatial_analysis(ds_wave, ds_gl)
        run_timeseries_analysis(ds_wave, ds_gl, max_hs, max_zos)

    # ── Part E: municipality–grid association ─────────────────────────────
    # Run before Part D so that grid_table is available for the D2 SSH panel.
    if run_all or args.municipalities or args.sector_boxplots or args.statistics \
            or args.reported_events:
        if grid_table is None:
            grid_table = run_municipality_grid_association(df_events, ds_wave, ds_gl)

    # ── Part D: reported events EDA ───────────────────────────────────────
    # grid_table is passed so that D2 can show SSH at event dates.
    # When --reported-events is called in isolation, Part E runs automatically above.
    if run_all or args.reported_events:
        run_reported_events_eda(df_events, ds_gl=ds_gl, grid_table=grid_table)

    # ── Part F: per-sector figures ────────────────────────────────────────
    if run_all or args.sector_boxplots:
        run_sector_figures(df_events, grid_table, ds_wave, ds_gl)

    # ── Part G: additional analyses ───────────────────────────────────────
    if run_all or args.statistics:
        run_additional_analyses(ds_wave, ds_gl, df_events, grid_table)

    # ── Data README files ─────────────────────────────────────────────────
    if run_all or args.write_readmes:
        write_data_readmes()

    log.info("=" * 62)
    log.info("Analysis complete.")
    log.info("  Figures  : %s", CFG["fig_dir"])
    log.info("  Tables   : %s", CFG["tab_dir"])
    log.info("=" * 62)


if __name__ == "__main__":
    main()
