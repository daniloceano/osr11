"""
Entry point for Step 2e — PU Composite Calibration (OSR11).

Performs an INDEPENDENT threshold sweep using the positive-unlabeled (PU)
composite score to calibrate compound event detection thresholds under
systematic under-reporting.

This step does NOT load or reuse the Step 2d CSI metrics as input for
threshold selection. The Step 2d outputs (tab_TC4_*.csv) are used ONLY for
methodological comparison in the final summary.

Usage
-----
Run from the project root::

    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --all

Individual components::

    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --hits-misses
    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --unmatched
    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --scoring
    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --sensitivity
    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --figures
    python src/02_threshold_calibration/05_pu_composite_calibration/main.py --summary

If no flag is given, --all is assumed.

Pipeline (--all)
----------------
1. Load data: unified metocean dataset + expanded events + legacy events
2. Clip dataset to validated temporal domain (event date range ± window margins)
3. Build event records (expanded events → municipality → grid point)
4. Compute FES2022 tidal series for unique grid points
5. Build SSH_total = SSH + tide per grid point
6. [--hits-misses] Layer 1: event-by-event hit/miss scan across all pairs
7. [--unmatched]   Layer 2: collect unmatched episode details per pair
8. [--scoring]     Build audit table (q_i components), compute composite scores
9. [--sensitivity] Sensitivity analysis over weights, alphas, B_target
10. [--figures]    Generate heatmaps and comparison figures
11. [--summary]    Save all output tables and print summary

Validated temporal domain
-------------------------
Clips to [min(expanded_event_dates) − 2 days, max(expanded_event_dates) + 1 day].
This restricts both threshold computation and the false-alarm scan to the period
covered by the expanded documentary database (1998–2020 approximately).

n_years calculation
-------------------
The number of validated years is derived from the clipped dataset's time range:
    n_years = (t_end - t_start).days / 365.25
This is used to normalise the annual burden B(θ).
"""
from __future__ import annotations

import argparse
import logging
import json
import pickle
import sys
from pathlib import Path

# ── Project root on sys.path ──────────────────────────────────────────────────
# Path: osr11/src/02_threshold_calibration/05_pu_composite_calibration/main.py
#   parents[0] = 05_pu_composite_calibration → 02_threshold_calibration/
#   parents[1] = 02_threshold_calibration    → src/
#   parents[2] = src                         → osr11/  (project root)
_script_dir   = Path(__file__).resolve().parent
_project_root = _script_dir.parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pandas as pd

from src.pu_composite_calibration.config.analysis_config import CFG
from src.pu_composite_calibration.utils import (
    make_output_dirs,
    build_percentile_levels,
    load_expanded_events,
    load_legacy_events,
    load_unified_dataset,
    setup_logging,
)
from src.pu_composite_calibration.scoring import (
    build_ssh_total_cache_pu,
    run_hits_misses_pu,
    run_unmatched_all_pairs,
    compute_pu_scores,
    rank_combinations_pu,
    select_optimal_pair_pu,
)
from src.pu_composite_calibration.audit import (
    build_episode_audit_table,
    attach_ssh_total_to_records,
)

from src.csi_grid_scan.preprocessing import clip_to_validated_period
from src.preliminary_compound.events import build_event_records
from src.tidal_sensitivity.tides import build_tide_cache

log = logging.getLogger(__name__)

# ── Intermediate-result cache paths (for partial runs) ────────────────────────
_CACHE_DIR   = CFG["log_dir"]
_HM_CACHE    = Path(_CACHE_DIR) / "pu_cache_hits_misses.pkl"
_EP_CACHE    = Path(_CACHE_DIR) / "pu_cache_unmatched_episodes.pkl"
_META_CACHE  = Path(_CACHE_DIR) / "pu_cache_scoring_metadata.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PU Composite Calibration — OSR11 Step 2e",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "If no flag is given, --all is assumed.\n"
            "--all runs the full pipeline.\n"
            "--hits-misses only runs Layer 1 (event capture scan).\n"
            "--unmatched   only runs Layer 2 (unmatched episode collection).\n"
            "--scoring     computes q_i weights and composite scores.\n"
            "--sensitivity runs weight/alpha/B_target sensitivity experiments.\n"
            "--figures     generates heatmaps and comparison plots.\n"
            "--summary     exports tables and prints result summary.\n"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all",         action="store_true", help="Full pipeline")
    group.add_argument("--hits-misses", action="store_true", dest="hits_misses",
                       help="Layer 1 only")
    group.add_argument("--unmatched",   action="store_true",
                       help="Layer 2 only (requires prior --hits-misses)")
    group.add_argument("--scoring",     action="store_true",
                       help="Scoring only (requires --hits-misses and --unmatched results)")
    group.add_argument("--sensitivity", action="store_true",
                       help="Sensitivity analysis (requires scoring results)")
    group.add_argument("--figures",     action="store_true",
                       help="Figures only (requires scoring results)")
    group.add_argument("--summary",     action="store_true",
                       help="Export tables and print summary (requires scoring results)")
    return parser.parse_args()


def _load_data_and_records(cfg: dict):
    """Load dataset, events, clip to validated period, build event records.

    Returns
    -------
    tuple: (ds_clipped, time_index, records, events_expanded_df, legacy_df, n_years)
    """
    # ── Load data ─────────────────────────────────────────────────────────────
    ds           = load_unified_dataset(cfg["unified_file"])
    events_exp   = load_expanded_events(cfg["events_file"])
    legacy_df    = load_legacy_events(cfg["events_file_legacy"])

    # ── Clip to validated temporal domain ─────────────────────────────────────
    ds, t_start, t_end = clip_to_validated_period(
        ds, events_exp, cfg["match_window_offsets"]
    )
    time_index = pd.DatetimeIndex(ds.time.values)

    n_years = (t_end - t_start).days / 365.25
    log.info(
        "Validated period: %s → %s  (%.1f years)",
        t_start.date(), t_end.date(), n_years,
    )

    # ── Build event records ───────────────────────────────────────────────────
    # build_event_records uses CFG from src.preliminary_compound.config which
    # sets hs_var='VHM0', ssh_var='zos', event_half_window_days=3.
    # We pass the expanded events DataFrame directly; the function accepts any
    # DataFrame with 'municipality', 'date', and 'disaster_id' columns.
    records = build_event_records(ds, events_exp)
    if not records:
        log.error("No event records built from expanded events database.")
        sys.exit(1)
    log.info("Built %d event records from expanded events database.", len(records))

    return ds, time_index, records, events_exp, legacy_df, n_years


def main(args: argparse.Namespace | None = None) -> None:
    setup_logging()
    if args is None:
        args = _parse_args()

    run_all = args.all or not any([
        getattr(args, "hits_misses", False),
        getattr(args, "unmatched",   False),
        getattr(args, "scoring",     False),
        getattr(args, "sensitivity", False),
        getattr(args, "figures",     False),
        getattr(args, "summary",     False),
    ])

    make_output_dirs(CFG)
    Path(_CACHE_DIR).mkdir(parents=True, exist_ok=True)

    log.info("=" * 68)
    log.info("OSR11 — Step 2e: PU Composite Calibration")
    log.info("Events: %s",  CFG["events_file"])
    log.info("Output: %s", CFG["output_root"])
    log.info("=" * 68)

    # ── Build threshold grid ───────────────────────────────────────────────────
    hs_pcts  = build_percentile_levels(CFG["pct_start"], CFG["pct_stop"], CFG["pct_step"])
    ssh_pcts = build_percentile_levels(CFG["pct_start"], CFG["pct_stop"], CFG["pct_step"])
    n_pairs  = len(hs_pcts) * len(ssh_pcts)
    log.info(
        "Threshold grid: %d × %d = %d pairs  (q%.0f–q%.0f, step=%.0f%%)",
        len(hs_pcts), len(ssh_pcts), n_pairs,
        CFG["pct_start"] * 100, CFG["pct_stop"] * 100, CFG["pct_step"] * 100,
    )

    # ── Load data (required for most stages) ──────────────────────────────────
    need_data = run_all or any([
        getattr(args, "hits_misses", False),
        getattr(args, "unmatched", False),
    ])

    records = None
    tide_cache = None
    ssh_total_cache = None
    time_index = None
    events_exp = None
    legacy_df  = None
    n_years    = None

    if need_data:
        ds, time_index, records, events_exp, legacy_df, n_years = \
            _load_data_and_records(CFG)

        # ── FES2022 tidal series ───────────────────────────────────────────────
        log.info("Computing FES2022 daily-maximum tidal series...")
        tide_cache = build_tide_cache(records, daily_max=True)

        # Validate tide (same check as Step 2d)
        failed = [k for k, v in tide_cache.items() if v is None or not v.notna().any()]
        if failed:
            raise RuntimeError(
                f"FES2022 tide failed for {len(failed)} grid point(s).\n"
                "Ensure you are running inside the 'osr11' conda environment "
                "(eo-tides must be installed) and that FES2022 model files exist."
            )
        log.info("FES2022 tide validated for %d grid point(s).", len(tide_cache))

        # ── SSH_total cache ────────────────────────────────────────────────────
        log.info("Building SSH_total = SSH + tide per grid point...")
        ssh_total_cache = build_ssh_total_cache_pu(records, tide_cache)

    # ── Layer 1: hits / misses ────────────────────────────────────────────────
    contingency_df = None

    if run_all or getattr(args, "hits_misses", False):
        log.info("Layer 1: event-by-event hit/miss scan...")
        contingency_df = run_hits_misses_pu(
            records, ssh_total_cache, time_index,
            hs_pcts, ssh_pcts,
            CFG["match_window_offsets"],
        )
        # Save intermediate result
        contingency_df.to_pickle(str(_HM_CACHE))
        log.info("Layer 1 complete. Cache saved: %s", _HM_CACHE)

    # ── Layer 2: unmatched episode collection ─────────────────────────────────
    unmatched_episodes = None

    if run_all or getattr(args, "unmatched", False):
        log.info("Layer 2: collecting unmatched episode details...")
        unmatched_episodes = run_unmatched_all_pairs(
            records, ssh_total_cache, time_index,
            hs_pcts, ssh_pcts,
            CFG["episode_max_gap_days"],
            CFG["match_window_offsets"],
        )
        # Save intermediate result
        with open(_EP_CACHE, "wb") as f:
            pickle.dump(unmatched_episodes, f)
        log.info(
            "Layer 2 complete. %d total unmatched episodes. Cache saved: %s",
            len(unmatched_episodes), _EP_CACHE,
        )

    # ── Scoring ───────────────────────────────────────────────────────────────
    df_scores  = None
    audit_df   = None
    optimal    = None
    df_ranked  = None
    P          = None   # total positive events (len of expanded events DB)

    if run_all or getattr(args, "scoring", False):
        # Load cached intermediate results if not produced in this run
        if contingency_df is None:
            if not _HM_CACHE.exists():
                log.error(
                    "--scoring requires Layer 1 results. Run --hits-misses first "
                    "(cache not found: %s).", _HM_CACHE
                )
                sys.exit(1)
            contingency_df = pd.read_pickle(str(_HM_CACHE))

        if unmatched_episodes is None:
            if not _EP_CACHE.exists():
                log.error(
                    "--scoring requires Layer 2 results. Run --unmatched first "
                    "(cache not found: %s).", _EP_CACHE
                )
                sys.exit(1)
            with open(_EP_CACHE, "rb") as f:
                unmatched_episodes = pickle.load(f)

        # Load data for audit if not already loaded
        if records is None:
            ds, time_index, records, events_exp, legacy_df, n_years = \
                _load_data_and_records(CFG)
            tide_cache = build_tide_cache(records, daily_max=True)
            ssh_total_cache = build_ssh_total_cache_pu(records, tide_cache)

        # Determine n_years from clipped time index
        if n_years is None:
            n_years = (time_index[-1] - time_index[0]).days / 365.25

        P = len(events_exp)
        n_municipalities = len({rec.municipality for rec in records})
        log.info(
            "Scoring: P=%d positive events | %.1f validated years | "
            "%d unique municipalities | %d unmatched episodes",
            P, n_years, n_municipalities, len(unmatched_episodes),
        )
        log.info(
            "Annual burden target: %.0f ep/yr/muni × %d munis = %.0f ep/yr total",
            CFG["b_target_per_municipality"],
            n_municipalities,
            CFG["b_target_per_municipality"] * n_municipalities,
        )

        # Build audit table (q_i components for all unmatched episodes)
        log.info("Building episode audit table (q_i components)...")
        records_by_muni = attach_ssh_total_to_records(records, ssh_total_cache)
        audit_df = build_episode_audit_table(
            unmatched_episodes, records_by_muni, legacy_df, CFG
        )

        # Compute composite scores
        log.info("Computing composite PU scores...")
        df_scores = compute_pu_scores(
            contingency_df, unmatched_episodes, audit_df, n_years, P, CFG,
            n_municipalities=n_municipalities,
        )
        df_ranked  = rank_combinations_pu(df_scores)
        optimal    = select_optimal_pair_pu(df_scores)

        # ── Save tables ────────────────────────────────────────────────────────
        tab_dir = Path(CFG["tab_dir"])
        tab_dir.mkdir(parents=True, exist_ok=True)

        audit_df.to_csv(tab_dir / "tab_TC5_episode_audit.csv", index=False)
        log.info("Saved: tab_TC5_episode_audit.csv")

        df_scores.to_csv(tab_dir / "tab_TC5_pu_metrics_full.csv", index=False)
        log.info("Saved: tab_TC5_pu_metrics_full.csv")

        df_ranked.to_csv(tab_dir / "tab_TC5_pu_metrics_ranked.csv", index=False)
        log.info("Saved: tab_TC5_pu_metrics_ranked.csv")

        pd.DataFrame([optimal]).to_csv(
            tab_dir / "tab_TC5_optimal_pair_pu.csv", index=False
        )
        log.info("Saved: tab_TC5_optimal_pair_pu.csv")

        # ── Step 2d comparison table ───────────────────────────────────────────
        _save_csi_comparison(optimal, tab_dir)

        # ── Scoring metadata (for partial re-runs like --sensitivity alone) ────
        Path(_META_CACHE).parent.mkdir(parents=True, exist_ok=True)
        with open(_META_CACHE, "w") as f:
            json.dump({"n_years": n_years, "P": P}, f)
        log.info("Saved scoring metadata: %s", _META_CACHE)

    # ── Sensitivity analysis ──────────────────────────────────────────────────
    if run_all or getattr(args, "sensitivity", False):
        if df_scores is None:
            df_scores, df_ranked, optimal, audit_df = _load_scores_or_exit()

        # Load intermediate caches if not already in memory
        if contingency_df is None:
            if not _HM_CACHE.exists():
                log.error(
                    "--sensitivity requires Layer 1 cache. Run --hits-misses first "
                    "(cache not found: %s).", _HM_CACHE
                )
                sys.exit(1)
            contingency_df = pd.read_pickle(str(_HM_CACHE))

        if unmatched_episodes is None:
            if not _EP_CACHE.exists():
                log.error(
                    "--sensitivity requires Layer 2 cache. Run --unmatched first "
                    "(cache not found: %s).", _EP_CACHE
                )
                sys.exit(1)
            with open(_EP_CACHE, "rb") as f:
                unmatched_episodes = pickle.load(f)

        # Load n_years and P from metadata saved during scoring.
        # Fallback: derive P from the full metrics CSV (H+M is constant across pairs).
        # n_years cannot be recovered from CSVs alone — metadata file is required.
        if n_years is None or P is None:
            if _META_CACHE.exists():
                with open(_META_CACHE) as f:
                    _meta = json.load(f)
                n_years = _meta["n_years"]
                P = _meta["P"]
                log.info(
                    "Loaded scoring metadata: n_years=%.2f  P=%d", n_years, P
                )
            else:
                # Attempt partial recovery from the saved metrics CSV
                _scores_path = Path(CFG["tab_dir"]) / "tab_TC5_pu_metrics_full.csv"
                if not _scores_path.exists():
                    log.error(
                        "--sensitivity requires scoring metadata but neither "
                        "%s nor %s exist. Run --scoring first.",
                        _META_CACHE, _scores_path,
                    )
                    sys.exit(1)
                _df_tmp = pd.read_csv(_scores_path)
                # P = H + M is constant across all threshold pairs by definition
                _row0 = _df_tmp.iloc[0]
                P = int(round(_row0["H"] + _row0["M"]))
                # n_years: derive from burden equation if B < 1 at that row
                # B = (H+U)/(n_years * b_target_eff)  →  n_years = (H+U)/(B * b_target_eff)
                _b_val = float(_row0["B"])
                _u_val = float(_row0["U"])
                _h_val = float(_row0["H"])
                _b_tgt = CFG["b_target_per_municipality"]
                # n_municipalities not in CSV; use unmatched_episodes to derive it
                _n_munis = len({ep.municipality for ep in unmatched_episodes}) if unmatched_episodes else 1
                _b_eff = _b_tgt * max(_n_munis, 1)
                if _b_val > 0 and _b_val < 1.0 and _b_eff > 0:
                    n_years = (_h_val + _u_val) / (_b_val * _b_eff)
                    log.warning(
                        "Scoring metadata not found — n_years derived from burden "
                        "equation: %.2f years. Run --scoring to persist accurate metadata.",
                        n_years,
                    )
                else:
                    log.error(
                        "Cannot derive n_years from existing CSVs (B=%.4f is saturated "
                        "or zero). Run --scoring first to generate %s.",
                        _b_val, _META_CACHE,
                    )
                    sys.exit(1)

        from src.pu_composite_calibration.sensitivity import run_all_sensitivity
        log.info("Running sensitivity analysis...")
        run_all_sensitivity(
            contingency_df=contingency_df,
            unmatched_episodes=unmatched_episodes,
            audit_df=audit_df,
            n_years=n_years,
            P=P,
            cfg=CFG,
        )

    # ── Figures ───────────────────────────────────────────────────────────────
    if run_all or getattr(args, "figures", False):
        if df_scores is None:
            df_scores, df_ranked, optimal, audit_df = _load_scores_or_exit()

        from src.pu_composite_calibration.figures import run_all_figures
        from config.plot_config import apply_publication_style
        apply_publication_style()
        log.info("Generating figures...")
        run_all_figures(df_scores, df_ranked, optimal, audit_df, CFG)

    # ── Summary ───────────────────────────────────────────────────────────────
    if run_all or getattr(args, "summary", False):
        if optimal is None:
            tab_dir = Path(CFG["tab_dir"])
            opt_path = tab_dir / "tab_TC5_optimal_pair_pu.csv"
            if not opt_path.exists():
                log.error(
                    "--summary requires scoring results. Run --scoring first "
                    "(tab_TC5_optimal_pair_pu.csv not found)."
                )
                sys.exit(1)
            optimal = pd.read_csv(opt_path).iloc[0].to_dict()

        _print_summary(optimal)

    log.info("=" * 68)
    log.info("Step 2e PU Composite Calibration complete.")
    log.info("  Tables : %s", CFG["tab_dir"])
    log.info("  Figures: %s", CFG["fig_dir"])
    log.info("=" * 68)


def _save_csi_comparison(optimal: dict, tab_dir: Path) -> None:
    """Write CSI vs PU comparison table using Step 2d outputs if available."""
    csi_path = Path(CFG.get("optimal_pair_file", ""))
    csi_row = {}
    if csi_path.exists():
        try:
            csi_row = pd.read_csv(csi_path).iloc[0].to_dict()
        except Exception:
            pass

    rows = []
    if csi_row:
        rows.append({
            "method": "CSI (Step 2d)",
            "events_db": "Legacy (91 unique IDs / 105 rows)",
            "validated_period": "1998–2023",
            "thr_hs_pct": csi_row.get("thr_hs_pct", "—"),
            "thr_ssh_pct": csi_row.get("thr_ssh_pct", "—"),
            "H": csi_row.get("H", "—"),
            "metric_primary": f"CSI={csi_row.get('CSI', '—'):.4f}"
            if isinstance(csi_row.get("CSI"), float) else "—",
            "FAR": csi_row.get("FAR", "—"),
        })
    rows.append({
        "method": "PU Composite (Step 2e)",
        "events_db": "Expanded documentary (56 events)",
        "validated_period": "1998–2020",
        "thr_hs_pct": optimal.get("thr_hs_pct", "—"),
        "thr_ssh_pct": optimal.get("thr_ssh_pct", "—"),
        "H": optimal.get("H", "—"),
        "metric_primary": f"Score={optimal.get('Score', '—'):.4f}"
        if isinstance(optimal.get("Score"), float) else "—",
        "FAR": "N/A (PU framework)",
    })

    pd.DataFrame(rows).to_csv(
        tab_dir / "tab_TC5_csi_vs_pu_comparison.csv", index=False
    )
    log.info("Saved: tab_TC5_csi_vs_pu_comparison.csv")


def _load_scores_or_exit():
    """Load scoring results from disk or exit with a helpful error message."""
    tab_dir = Path(CFG["tab_dir"])
    scores_path = tab_dir / "tab_TC5_pu_metrics_full.csv"
    opt_path    = tab_dir / "tab_TC5_optimal_pair_pu.csv"
    audit_path  = tab_dir / "tab_TC5_episode_audit.csv"
    ranked_path = tab_dir / "tab_TC5_pu_metrics_ranked.csv"

    for p in [scores_path, opt_path, audit_path, ranked_path]:
        if not p.exists():
            log.error(
                "Required file not found: %s\nRun with --scoring (or --all) first.",
                p,
            )
            sys.exit(1)

    df_scores  = pd.read_csv(scores_path)
    df_ranked  = pd.read_csv(ranked_path)
    optimal    = pd.read_csv(opt_path).iloc[0].to_dict()
    audit_df   = pd.read_csv(audit_path)
    return df_scores, df_ranked, optimal, audit_df


def _print_summary(optimal: dict) -> None:
    """Print a human-readable result summary to stdout."""
    log.info("")
    log.info("══════════════════════════════════════════════════════════════════")
    log.info("  Step 2e — PU Composite Calibration: OPTIMAL THRESHOLD PAIR")
    log.info("══════════════════════════════════════════════════════════════════")
    log.info("  Hₛ threshold   : q%.0f", optimal.get("thr_hs_pct", 0) * 100)
    log.info("  SSH threshold  : q%.0f", optimal.get("thr_ssh_pct", 0) * 100)
    log.info("  Composite Score: %.4f", optimal.get("Score", float("nan")))
    log.info("  R_pos (recall) : %.3f  (H=%d confirmed events captured)",
             optimal.get("R_pos", 0.0), int(optimal.get("H", 0)))
    log.info("  B (burden)     : %.3f", optimal.get("B", float("nan")))
    log.info("  F_soft         : %.1f  (U=%d unmatched, soft-penalised)",
             optimal.get("F_soft", 0.0), int(optimal.get("U", 0)))
    log.info("══════════════════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
