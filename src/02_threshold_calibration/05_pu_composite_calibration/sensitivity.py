"""
Sensitivity analysis for Step 2e — PU Composite Calibration.

Tests robustness of the optimal threshold pair to parameter choices by
re-running the composite score computation under alternative configurations.

Three sensitivity experiments
------------------------------
1. WEIGHT sensitivity: alternative (w1, w2, w3) triplets
   — tests sensitivity to the relative importance of recall vs. burden vs. penalty

2. ALPHA sensitivity: alternative (α_E, α_I, α_C) triplets
   — tests sensitivity to the relative importance of evidence vs. intensity vs. context

3. B_TARGET sensitivity: alternative annual burden targets
   — tests sensitivity to the operational detection-rate target

Each experiment re-uses the pre-computed audit table (q_i values), which is
independent of (w1, w2, w3) and (α_E, α_I, α_C) only if the audit table itself
is recomputed for each alpha variant. However:
  - The w1/w2/w3 and B_target experiments can reuse the same audit_df.
  - The alpha experiment (α_E, α_I, α_C) changes q_i, so audit_df must be
    recomputed for each alpha configuration.

For the alpha sensitivity experiment, we rebuild q_i from the stored E_i, I_i,
C_i component columns (which are independent of alpha) rather than re-running
the full audit pipeline. This makes alpha sensitivity fast even for large episode
sets.

Output tables
-------------
    tab_TC5_sensitivity_weights.csv    — score and optimal pair per weight preset
    tab_TC5_sensitivity_alpha.csv      — score and optimal pair per alpha preset
    tab_TC5_sensitivity_b_target.csv   — score and optimal pair per B_target value
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.pu_composite_calibration.audit import EpisodeRecord
from src.pu_composite_calibration.scoring import (
    compute_pu_scores,
    rank_combinations_pu,
    select_optimal_pair_pu,
)

log = logging.getLogger(__name__)


def _recompute_q_i(
    audit_df: pd.DataFrame,
    alpha_E: float,
    alpha_I: float,
    alpha_C: float,
) -> pd.DataFrame:
    """Recompute q_i for all episodes using new alpha values.

    Requires audit_df to have columns E_i, I_i, C_i (individual components).
    Returns a copy of audit_df with updated q_i.
    """
    df = audit_df.copy()
    df["q_i"] = np.clip(
        alpha_E * df["E_i"] + alpha_I * df["I_i"] + alpha_C * df["C_i"],
        0.0, 1.0,
    ).round(4)
    return df


def run_weight_sensitivity(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
) -> pd.DataFrame:
    """Re-run scoring under alternative (w1, w2, w3) weight triplets.

    Parameters
    ----------
    contingency_df, unmatched_episodes, audit_df : from main.py
    n_years : float
    P : int
    cfg : dict

    Returns
    -------
    DataFrame with columns:
        label, w1, w2, w3, thr_hs_pct, thr_ssh_pct, H, U, R_pos, B, F_soft, Score
    """
    weight_configs = cfg.get("sensitivity_weights", [])
    rows: list[dict] = []

    for wc in weight_configs:
        alt_cfg = dict(cfg)
        alt_cfg["w1_recall"]       = wc["w1"]
        alt_cfg["w2_burden"]       = wc["w2"]
        alt_cfg["w3_soft_penalty"] = wc["w3"]

        df_scores = compute_pu_scores(
            contingency_df, unmatched_episodes, audit_df, n_years, P, alt_cfg
        )
        opt = select_optimal_pair_pu(df_scores)
        rows.append({
            "label":       wc.get("label", ""),
            "w1":          wc["w1"],
            "w2":          wc["w2"],
            "w3":          wc["w3"],
            "thr_hs_pct":  opt["thr_hs_pct"],
            "thr_ssh_pct": opt["thr_ssh_pct"],
            "H":           opt["H"],
            "U":           opt["U"],
            "R_pos":       opt["R_pos"],
            "B":           opt["B"],
            "F_soft":      opt["F_soft"],
            "Score":       opt["Score"],
        })
        log.info(
            "  [weight sensitivity] %s → hs=q%.0f/ssh=q%.0f  Score=%.4f",
            wc.get("label", ""), opt["thr_hs_pct"] * 100, opt["thr_ssh_pct"] * 100,
            opt["Score"],
        )

    return pd.DataFrame(rows)


def run_alpha_sensitivity(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
) -> pd.DataFrame:
    """Re-run scoring under alternative (α_E, α_I, α_C) confidence weight triplets.

    Recomputes q_i from stored E_i/I_i/C_i columns (no full audit rerun needed).

    Returns
    -------
    DataFrame with columns:
        label, alpha_E, alpha_I, alpha_C, thr_hs_pct, thr_ssh_pct,
        H, U, R_pos, B, F_soft, Score
    """
    alpha_configs = cfg.get("sensitivity_alpha", [])
    rows: list[dict] = []

    for ac in alpha_configs:
        alt_audit = _recompute_q_i(audit_df, ac["alpha_E"], ac["alpha_I"], ac["alpha_C"])
        df_scores = compute_pu_scores(
            contingency_df, unmatched_episodes, alt_audit, n_years, P, cfg
        )
        opt = select_optimal_pair_pu(df_scores)
        rows.append({
            "label":       ac.get("label", ""),
            "alpha_E":     ac["alpha_E"],
            "alpha_I":     ac["alpha_I"],
            "alpha_C":     ac["alpha_C"],
            "thr_hs_pct":  opt["thr_hs_pct"],
            "thr_ssh_pct": opt["thr_ssh_pct"],
            "H":           opt["H"],
            "U":           opt["U"],
            "R_pos":       opt["R_pos"],
            "B":           opt["B"],
            "F_soft":      opt["F_soft"],
            "Score":       opt["Score"],
        })
        log.info(
            "  [alpha sensitivity] %s → hs=q%.0f/ssh=q%.0f  Score=%.4f",
            ac.get("label", ""), opt["thr_hs_pct"] * 100, opt["thr_ssh_pct"] * 100,
            opt["Score"],
        )

    return pd.DataFrame(rows)


def run_b_target_sensitivity(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
) -> pd.DataFrame:
    """Re-run scoring under alternative B_target values.

    Column schema (explicit)
    -----------------------
    b_target_per_muni   : float — per-municipality burden target tested (ep/yr/muni)
    n_municipalities    : int   — number of unique municipalities in this analysis
    b_target_total      : float — effective domain budget = b_target_per_muni × n_municipalities
    Score               : float — composite score at optimal pair
    R_pos               : float — positive recall at optimal pair
    B                   : float — normalised annual burden at optimal pair
    F_soft              : float — soft unmatched penalty at optimal pair
    H                   : int   — hits (matched events captured) at optimal pair
    U                   : int   — unmatched detected episodes at optimal pair
    thr_hs_pct          : float — optimal Hs threshold (fractional, e.g. 0.7 = q70)
    thr_ssh_pct         : float — optimal SSH threshold (fractional, e.g. 0.7 = q70)
    hs_percentile       : int   — optimal Hs threshold as integer percentile (e.g. 70)
    ssh_percentile      : int   — optimal SSH threshold as integer percentile (e.g. 70)
    """
    b_targets = cfg.get("sensitivity_b_target", [])

    # n_municipalities is constant across all B_target variants.
    # Derive from unmatched episodes (same source used in compute_pu_scores).
    if unmatched_episodes:
        n_municipalities = len({ep.municipality for ep in unmatched_episodes})
    else:
        n_municipalities = max(1, cfg.get("_n_municipalities_fallback", 1))
    log.info(
        "B_target sensitivity: %d municipalities detected from unmatched episodes.",
        n_municipalities,
    )

    rows: list[dict] = []

    for bt in b_targets:
        alt_cfg = dict(cfg)
        alt_cfg["b_target_per_municipality"] = bt

        df_scores = compute_pu_scores(
            contingency_df, unmatched_episodes, audit_df, n_years, P, alt_cfg,
            n_municipalities=n_municipalities,
        )
        opt = select_optimal_pair_pu(df_scores)
        rows.append({
            "b_target_per_muni":  bt,
            "n_municipalities":   n_municipalities,
            "b_target_total":     bt * n_municipalities,
            "Score":              opt["Score"],
            "R_pos":              opt["R_pos"],
            "B":                  opt["B"],
            "F_soft":             opt["F_soft"],
            "H":                  opt["H"],
            "U":                  opt["U"],
            "thr_hs_pct":         opt["thr_hs_pct"],
            "thr_ssh_pct":        opt["thr_ssh_pct"],
            "hs_percentile":      round(opt["thr_hs_pct"] * 100),
            "ssh_percentile":     round(opt["thr_ssh_pct"] * 100),
        })
        log.info(
            "  [B_target sensitivity] b_target_per_muni=%.0f × %d munis = %.0f ep/yr"
            " → hs=q%.0f/ssh=q%.0f  Score=%.4f",
            bt, n_municipalities, bt * n_municipalities,
            opt["thr_hs_pct"] * 100, opt["thr_ssh_pct"] * 100, opt["Score"],
        )

    return pd.DataFrame(rows)


def run_gap_sensitivity(
    contingency_df: pd.DataFrame,
    records: list,
    ssh_total_cache: dict,
    time_index: "pd.DatetimeIndex",
    legacy_df: "pd.DataFrame",
    n_years: float,
    P: int,
    cfg: dict,
) -> pd.DataFrame:
    """Re-run Layer 2 + scoring under alternative EPISODE_MAX_GAP_DAYS values.

    Unlike the weight/alpha/B_target experiments, changing the gap tolerance
    requires re-running the full unmatched-episode collection (Layer 2) and
    rebuilding the audit table, because episode clustering boundaries change.
    Layer 1 (hits/misses) is NOT affected — the compound condition at each
    event is independent of gap tolerance.

    Parameters
    ----------
    contingency_df : DataFrame [thr_hs_pct, thr_ssh_pct, H, M] from Layer 1.
    records : list[EventRecord]
    ssh_total_cache : dict
    time_index : pd.DatetimeIndex — validated-period time index for the scan
    legacy_df : pd.DataFrame — legacy events for audit E_i calculation
    n_years : float — validated period duration in years
    P : int — total positive events
    cfg : dict — configuration dictionary

    Returns
    -------
    DataFrame with columns:
        gap_days, thr_hs_pct, thr_ssh_pct, H, U, R_pos, B, F_soft, Score
    """
    from src.pu_composite_calibration.scoring import (
        run_unmatched_all_pairs,
        compute_pu_scores,
        select_optimal_pair_pu,
    )
    from src.pu_composite_calibration.audit import (
        build_episode_audit_table,
        attach_ssh_total_to_records,
    )
    from src.pu_composite_calibration.utils import build_percentile_levels

    gap_values = cfg.get("sensitivity_gap_days", [0, 1, 2, 3])
    hs_pcts  = build_percentile_levels(cfg["pct_start"], cfg["pct_stop"], cfg["pct_step"])
    ssh_pcts = build_percentile_levels(cfg["pct_start"], cfg["pct_stop"], cfg["pct_step"])

    # n_municipalities for burden: use union count from records
    n_municipalities = len({rec.municipality for rec in records})

    # Pre-compute records_by_muni (needed for audit table)
    records_by_muni = attach_ssh_total_to_records(records, ssh_total_cache)

    rows: list[dict] = []

    for gap_val in gap_values:
        log.info(
            "  [gap sensitivity] EPISODE_MAX_GAP_DAYS=%d — running Layer 2...",
            gap_val,
        )
        # Re-run Layer 2 with the alternative gap value
        unmatched = run_unmatched_all_pairs(
            records, ssh_total_cache, time_index,
            hs_pcts, ssh_pcts,
            gap_val,
            cfg["match_window_offsets"],
        )
        log.info(
            "    Layer 2 complete: %d unmatched episodes (gap=%d)",
            len(unmatched), gap_val,
        )

        # Rebuild audit table for these episodes
        audit = build_episode_audit_table(
            unmatched, records_by_muni, legacy_df, cfg
        )

        # Compute scores
        df_scores = compute_pu_scores(
            contingency_df, unmatched, audit, n_years, P, cfg,
            n_municipalities=n_municipalities,
        )
        opt = select_optimal_pair_pu(df_scores)

        rows.append({
            "gap_days":     gap_val,
            "thr_hs_pct":  opt["thr_hs_pct"],
            "thr_ssh_pct": opt["thr_ssh_pct"],
            "H":           opt["H"],
            "U":           opt["U"],
            "R_pos":       opt["R_pos"],
            "B":           opt["B"],
            "F_soft":      opt["F_soft"],
            "Score":       opt["Score"],
            "hs_percentile":  round(opt["thr_hs_pct"] * 100),
            "ssh_percentile": round(opt["thr_ssh_pct"] * 100),
        })
        log.info(
            "  [gap sensitivity] gap=%d → hs=q%.0f/ssh=q%.0f  Score=%.4f  U=%d",
            gap_val,
            opt["thr_hs_pct"] * 100, opt["thr_ssh_pct"] * 100,
            opt["Score"], opt["U"],
        )

    return pd.DataFrame(rows)


def run_all_sensitivity(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
    records: list | None = None,
    ssh_total_cache: dict | None = None,
    time_index: "pd.DatetimeIndex | None" = None,
    legacy_df: "pd.DataFrame | None" = None,
) -> None:
    """Run all sensitivity experiments and save results.

    Outputs are written to CFG["tab_dir"]:
        tab_TC5_sensitivity_weights.csv
        tab_TC5_sensitivity_alpha.csv
        tab_TC5_sensitivity_b_target.csv
        tab_TC5_sensitivity_gap_days.csv   (if records/ssh_total_cache/time_index provided)
    """
    tab_dir = Path(cfg["tab_dir"])
    tab_dir.mkdir(parents=True, exist_ok=True)

    log.info("Sensitivity experiment 1/4: weight triplets...")
    df_w = run_weight_sensitivity(contingency_df, unmatched_episodes, audit_df,
                                  n_years, P, cfg)
    df_w.to_csv(tab_dir / "tab_TC5_sensitivity_weights.csv", index=False)
    log.info("Saved: tab_TC5_sensitivity_weights.csv")

    log.info("Sensitivity experiment 2/4: alpha triplets...")
    df_a = run_alpha_sensitivity(contingency_df, unmatched_episodes, audit_df,
                                 n_years, P, cfg)
    df_a.to_csv(tab_dir / "tab_TC5_sensitivity_alpha.csv", index=False)
    log.info("Saved: tab_TC5_sensitivity_alpha.csv")

    log.info("Sensitivity experiment 3/4: B_target values...")
    df_b = run_b_target_sensitivity(contingency_df, unmatched_episodes, audit_df,
                                    n_years, P, cfg)
    df_b.to_csv(tab_dir / "tab_TC5_sensitivity_b_target.csv", index=False)
    log.info("Saved: tab_TC5_sensitivity_b_target.csv")

    # Gap sensitivity requires records, ssh_total_cache, and time_index
    df_g = None
    if records is not None and ssh_total_cache is not None and time_index is not None:
        log.info("Sensitivity experiment 4/4: EPISODE_MAX_GAP_DAYS...")
        df_g = run_gap_sensitivity(
            contingency_df, records, ssh_total_cache, time_index,
            legacy_df, n_years, P, cfg,
        )
        df_g.to_csv(tab_dir / "tab_TC5_sensitivity_gap_days.csv", index=False)
        log.info("Saved: tab_TC5_sensitivity_gap_days.csv")
    else:
        log.warning(
            "Gap sensitivity skipped — requires records, ssh_total_cache, and "
            "time_index (pass via run_all_sensitivity kwargs)."
        )

    # Summary: count how many configurations agree on optimal pair
    _print_sensitivity_concordance(df_w, df_a, df_b, df_g)


def _print_sensitivity_concordance(df_w, df_a, df_b, df_g=None) -> None:
    """Log a concordance summary: how many sensitivity runs agree on the optimal pair."""
    parts = [
        df_w[["thr_hs_pct", "thr_ssh_pct"]],
        df_a[["thr_hs_pct", "thr_ssh_pct"]],
        df_b[["thr_hs_pct", "thr_ssh_pct"]],
    ]
    if df_g is not None:
        parts.append(df_g[["thr_hs_pct", "thr_ssh_pct"]])
    all_opts = pd.concat(parts, ignore_index=True)

    counts = (
        all_opts
        .value_counts()
        .reset_index()
        .rename(columns={0: "count"})
    )
    log.info(
        "Sensitivity concordance: %d unique optimal pairs across %d configurations",
        len(counts), len(all_opts),
    )
    for _, row in counts.iterrows():
        log.info(
            "  hs=q%.0f / ssh=q%.0f — selected in %d/%d configurations",
            row["thr_hs_pct"] * 100, row["thr_ssh_pct"] * 100,
            row.get("count", row.iloc[2] if len(row) > 2 else "?"),
            len(all_opts),
        )
