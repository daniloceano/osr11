"""
Core threshold sweep and composite score computation for Step 2e.

This module is SELF-CONTAINED with respect to the causal-window and episode-
clustering logic. It does not import from src.csi_grid_scan to avoid a known
import-chain issue (windows.py imports from src.threshold_calibration.config
which does not exist at the umbrella level). The logic below is equivalent to
the Step 2d implementation but independent by design, consistent with Step 2e's
mandate to perform its own threshold sweep.

Pipeline
--------
1. build_ssh_total_cache_pu  — compute SSH_total = SSH + tide per grid point
2. run_hits_misses_pu        — Layer 1: event-by-event hit/miss across all pairs
3. collect_unmatched_episodes_for_pair  — Layer 2: gather episode details (not
                                         just counts) for one pair
4. run_unmatched_all_pairs   — Layer 2 for all pairs
5. compute_pu_scores         — assemble composite Score(θ) for all pairs
6. rank_combinations_pu      — sort by Score descending
7. select_optimal_pair_pu    — return the top-ranked pair

Score formula
-------------
    Score(θ) = w1 · R_pos(θ)  −  w2 · B(θ)  −  w3 · F_soft(θ) / P

    R_pos(θ) = H(θ) / P                      [positive recall]
    B(θ)     = min(1, (H+U)/(Y × B_target))  [annual burden, normalised]
    F_soft(θ) = Σᵢ (1 − qᵢ)                  [soft unmatched penalty]
    P        = total positive (reported) events
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import xarray as xr

from src.pu_composite_calibration.audit import EpisodeRecord

log = logging.getLogger(__name__)


# ── Local helpers (copied from Step 2d logic; self-contained) ─────────────────

def _local_threshold(series: pd.Series, pct: float) -> float:
    """Compute percentile threshold from the finite values of a climatological series."""
    finite = series.dropna()
    if finite.empty:
        return np.nan
    return float(finite.quantile(pct))


def _build_causal_window(
    date: pd.Timestamp,
    time_index: pd.DatetimeIndex,
    offsets: list[int],
) -> list[pd.Timestamp]:
    """Return admissible match timestamps for event date D.

    Only returns timestamps that exist in time_index.
    """
    D = pd.Timestamp(date.year, date.month, date.day)
    window = []
    for off in offsets:
        t = D + pd.Timedelta(days=off)
        if t in time_index:
            window.append(t)
    return window


def _cluster_episodes(
    compound_mask: pd.Series,
    max_gap_days: int,
) -> list[pd.DatetimeIndex]:
    """Group compound days into independent episodes.

    Two compound days belong to the same episode if the gap between them is
    at most max_gap_days + 1 calendar days (i.e., at most max_gap_days
    non-compound days may separate them within one episode).
    """
    days = compound_mask[compound_mask].index.sort_values()
    if len(days) == 0:
        return []

    episodes: list[pd.DatetimeIndex] = []
    current: list[pd.Timestamp] = [days[0]]

    for d in days[1:]:
        gap = (d - current[-1]).days
        if gap <= max_gap_days + 1:
            current.append(d)
        else:
            episodes.append(pd.DatetimeIndex(current))
            current = [d]
    episodes.append(pd.DatetimeIndex(current))
    return episodes


def _episode_is_paired(
    episode: pd.DatetimeIndex,
    event_windows: list[list[pd.Timestamp]],
) -> bool:
    """Return True if any day of the episode falls within any event causal window."""
    episode_set = set(episode)
    for window in event_windows:
        if episode_set & set(window):
            return True
    return False


def _build_event_windows_for_point(
    records: list,
    grid_lat: float,
    grid_lon: float,
    time_index: pd.DatetimeIndex,
    offsets: list[int],
) -> list[list[pd.Timestamp]]:
    """Return causal windows for all events at a given grid point."""
    windows = []
    key_lat = round(grid_lat, 4)
    key_lon = round(grid_lon, 4)
    for rec in records:
        if (
            round(float(rec.grid_lat), 4) == key_lat
            and round(float(rec.grid_lon), 4) == key_lon
        ):
            w = _build_causal_window(rec.date, time_index, offsets)
            if w:
                windows.append(w)
    return windows


# ── SSH_total cache ────────────────────────────────────────────────────────────

def build_ssh_total_cache_pu(
    records: list,
    tide_cache: dict,
) -> dict[tuple[float, float], pd.Series]:
    """Build SSH_total = SSH + FES2022 tide for each unique grid point.

    Reuses add_tide_to_ssh and get_tide_for_record from the tidal_sensitivity
    module. These functions are in a module with a simpler import chain than
    the csi_grid_scan module.

    Parameters
    ----------
    records : list[EventRecord]
    tide_cache : dict mapping (lat, lon) → tide pd.Series

    Returns
    -------
    dict mapping (lat, lon) → SSH_total pd.Series
    """
    from src.tidal_sensitivity.tides import add_tide_to_ssh, get_tide_for_record

    cache: dict[tuple[float, float], pd.Series] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key in cache:
            continue
        tide = get_tide_for_record(rec, tide_cache)
        ssh_total = add_tide_to_ssh(rec.ssh_clim, tide)
        cache[key] = ssh_total

    log.info("SSH_total cache built for %d unique grid points.", len(cache))
    return cache


# ── Layer 1: event-by-event hit/miss ─────────────────────────────────────────

def _evaluate_event_pu(
    rec,
    ssh_total_clim: pd.Series,
    thr_hs_pct: float,
    thr_ssh_pct: float,
    time_index: pd.DatetimeIndex,
    offsets: list[int],
) -> bool:
    """Check if one event is captured at a given threshold pair.

    Returns
    -------
    bool — True if compound condition holds at any admissible timestamp.
    """
    thr_hs  = _local_threshold(rec.hs_clim, thr_hs_pct)
    thr_ssh = _local_threshold(ssh_total_clim, thr_ssh_pct)

    match_times = _build_causal_window(rec.date, time_index, offsets)

    if not match_times or np.isnan(thr_hs) or np.isnan(thr_ssh):
        return False

    for t in match_times:
        hs_val  = rec.hs_clim.get(t, np.nan)
        ssh_val = ssh_total_clim.get(t, np.nan)
        if not (np.isnan(hs_val) or np.isnan(ssh_val)):
            if hs_val >= thr_hs and ssh_val >= thr_ssh:
                return True
    return False


def run_hits_misses_pu(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    offsets: list[int],
) -> pd.DataFrame:
    """Layer 1: hit/miss for all threshold pairs.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict mapping (lat, lon) → SSH_total pd.Series
    time_index : pd.DatetimeIndex
    hs_percentiles, ssh_percentiles : list of float
    offsets : list[int]

    Returns
    -------
    DataFrame with columns [thr_hs_pct, thr_ssh_pct, H, M]
    """
    n_pairs = len(hs_percentiles) * len(ssh_percentiles)
    pair_idx = 0
    rows: list[dict] = []

    for hs_pct in hs_percentiles:
        for ssh_pct in ssh_percentiles:
            pair_idx += 1
            if pair_idx == 1 or pair_idx % 9 == 1:
                log.info(
                    "  [Layer 1] pair %d/%d  hs=q%.0f  ssh=q%.0f",
                    pair_idx, n_pairs,
                    round(hs_pct * 100), round(ssh_pct * 100),
                )

            H = M = 0
            for rec in records:
                key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
                ssh_total_clim = ssh_total_cache.get(key, pd.Series(dtype=float))
                captured = _evaluate_event_pu(
                    rec, ssh_total_clim, hs_pct, ssh_pct, time_index, offsets
                )
                if captured:
                    H += 1
                else:
                    M += 1

            rows.append({"thr_hs_pct": hs_pct, "thr_ssh_pct": ssh_pct, "H": H, "M": M})

    return pd.DataFrame(rows)


# ── Layer 2: unmatched episode collection ────────────────────────────────────

def collect_unmatched_episodes_for_pair(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    thr_hs_pct: float,
    thr_ssh_pct: float,
    max_gap_days: int,
    offsets: list[int],
) -> list[EpisodeRecord]:
    """Collect unmatched episodes for one threshold pair, with full metadata.

    Unlike Step 2d's _count_fa_detailed() which only returns counts, this
    function returns EpisodeRecord objects containing peak Hₛ, peak SSH_total,
    dates, and municipality — required by audit.py for q_i computation.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict
    time_index : pd.DatetimeIndex
    thr_hs_pct, thr_ssh_pct : float
    max_gap_days : int
    offsets : list[int]

    Returns
    -------
    list[EpisodeRecord]
    """
    # Collect unique grid points and their series
    unique_points: dict[tuple[float, float], tuple] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key not in unique_points:
            unique_points[key] = (rec.hs_clim, ssh_total_cache.get(key, pd.Series(dtype=float)))

    # Build reverse mapping: grid point → list of municipalities
    point_to_munis: dict[tuple[float, float], list[str]] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        point_to_munis.setdefault(key, [])
        if rec.municipality not in point_to_munis[key]:
            point_to_munis[key].append(rec.municipality)

    # Short prefix for episode IDs
    hs_tag  = f"hs{round(thr_hs_pct * 100):02d}"
    ssh_tag = f"ssh{round(thr_ssh_pct * 100):02d}"

    episodes_out: list[EpisodeRecord] = []

    for (lat, lon), (hs_clim, ssh_total_clim) in unique_points.items():
        if hs_clim.empty or ssh_total_clim.empty:
            continue

        thr_hs  = _local_threshold(hs_clim, thr_hs_pct)
        thr_ssh = _local_threshold(ssh_total_clim, thr_ssh_pct)

        if np.isnan(thr_hs) or np.isnan(thr_ssh):
            continue

        hs_aligned  = hs_clim.reindex(time_index)
        ssh_aligned = ssh_total_clim.reindex(time_index)

        compound_mask = (hs_aligned >= thr_hs) & (ssh_aligned >= thr_ssh)
        ep_list = _cluster_episodes(compound_mask, max_gap_days)

        if not ep_list:
            continue

        event_windows = _build_event_windows_for_point(records, lat, lon, time_index, offsets)

        for ep_days in ep_list:
            if _episode_is_paired(ep_days, event_windows):
                continue  # matched → hit; skip

            d_start = ep_days[0]
            d_end   = ep_days[-1]

            # Peak values within the episode
            hs_ep  = hs_aligned.loc[d_start:d_end].dropna()
            ssh_ep = ssh_aligned.loc[d_start:d_end].dropna()
            hs_peak  = float(hs_ep.max())  if not hs_ep.empty  else np.nan
            ssh_peak = float(ssh_ep.max()) if not ssh_ep.empty else np.nan

            munis = point_to_munis.get((lat, lon), ["unknown"])
            for muni in munis:
                muni_tag   = muni[:3].upper().replace(" ", "_")
                date_tag   = d_start.strftime("%Y%m%d")
                episode_id = f"{hs_tag}_{ssh_tag}_{muni_tag}_{date_tag}"

                episodes_out.append(EpisodeRecord(
                    episode_id  = episode_id,
                    thr_hs_pct  = thr_hs_pct,
                    thr_ssh_pct = thr_ssh_pct,
                    municipality = muni,
                    grid_lat    = lat,
                    grid_lon    = lon,
                    date_start  = d_start,
                    date_end    = d_end,
                    hs_peak     = hs_peak,
                    ssh_peak    = ssh_peak,
                    n_days      = len(ep_days),
                ))

    return episodes_out


def run_unmatched_all_pairs(
    records: list,
    ssh_total_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    max_gap_days: int,
    offsets: list[int],
) -> list[EpisodeRecord]:
    """Layer 2: collect unmatched episodes for ALL threshold pairs.

    Returns
    -------
    list[EpisodeRecord] — concatenated across all pairs.
    """
    n_pairs = len(hs_percentiles) * len(ssh_percentiles)
    pair_idx = 0
    all_episodes: list[EpisodeRecord] = []

    for hs_pct in hs_percentiles:
        for ssh_pct in ssh_percentiles:
            pair_idx += 1
            if pair_idx == 1 or pair_idx % 9 == 1:
                log.info(
                    "  [Layer 2] pair %d/%d  hs=q%.0f  ssh=q%.0f",
                    pair_idx, n_pairs,
                    round(hs_pct * 100), round(ssh_pct * 100),
                )
            ep_list = collect_unmatched_episodes_for_pair(
                records, ssh_total_cache, time_index,
                hs_pct, ssh_pct, max_gap_days, offsets,
            )
            all_episodes.extend(ep_list)
            log.debug(
                "    pair hs=q%.0f/ssh=q%.0f → %d unmatched episodes",
                round(hs_pct * 100), round(ssh_pct * 100), len(ep_list),
            )

    log.info(
        "Layer 2 complete. Total unmatched episodes across all pairs: %d",
        len(all_episodes),
    )
    return all_episodes


# ── Composite score computation ───────────────────────────────────────────────

def compute_positive_recall(H: int, P: int) -> float:
    """R_pos = H / P.  Returns 0.0 if P = 0 (degenerate case)."""
    if P == 0:
        return 0.0
    return float(H) / float(P)


def compute_annual_burden(
    H: int,
    U: int,
    n_years: float,
    b_target_per_muni: float,
    n_municipalities: int,
) -> float:
    """B(θ) = min(1, (H + U) / (Y × B_target_effective)).

    The effective target is:
        B_target_effective = b_target_per_muni × n_municipalities

    This scales the total acceptable annual detection budget proportionally
    with the number of municipalities under analysis.

    Parameters
    ----------
    H : int — hits (matched detected episodes)
    U : int — unmatched detected episodes
    n_years : float — length of validated period in years
    b_target_per_muni : float — acceptable annual detections *per municipality*
    n_municipalities : int — number of unique municipalities in the analysis

    Returns
    -------
    float in [0, 1]
    """
    b_target_effective = b_target_per_muni * max(n_municipalities, 1)
    if b_target_effective <= 0 or n_years <= 0:
        return 1.0
    b_raw = (H + U) / (n_years * b_target_effective)
    return float(min(1.0, b_raw))


def compute_soft_penalty(audit_df: pd.DataFrame, thr_hs_pct: float, thr_ssh_pct: float) -> float:
    """F_soft(θ) = Σᵢ (1 − qᵢ) for the given threshold pair.

    Parameters
    ----------
    audit_df : DataFrame from audit.build_episode_audit_table
    thr_hs_pct, thr_ssh_pct : float

    Returns
    -------
    float ≥ 0
    """
    if audit_df.empty:
        return 0.0
    mask = (audit_df["thr_hs_pct"] == thr_hs_pct) & (audit_df["thr_ssh_pct"] == thr_ssh_pct)
    subset = audit_df[mask]
    if subset.empty:
        return 0.0
    return float((1.0 - subset["q_i"]).sum())


def compute_composite_score(
    R_pos: float,
    B: float,
    F_soft: float,
    P: int,
    w1: float,
    w2: float,
    w3: float,
) -> float:
    """Score(θ) = w1·R_pos − w2·B − w3·F_soft/P.

    Normalising F_soft by P keeps the third term on a comparable scale to R_pos.

    Parameters
    ----------
    R_pos : float — positive recall in [0, 1]
    B     : float — annual burden in [0, 1]
    F_soft: float — soft unmatched penalty (sum of 1−qᵢ)
    P     : int   — total positive events (denominator)
    w1, w2, w3 : float — component weights

    Returns
    -------
    float — composite score (higher is better)
    """
    if P == 0:
        return 0.0
    return float(w1 * R_pos - w2 * B - w3 * F_soft / P)


def compute_pu_scores(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
    n_municipalities: int | None = None,
) -> pd.DataFrame:
    """Assemble composite PU scores for all threshold pairs.

    Parameters
    ----------
    contingency_df : DataFrame [thr_hs_pct, thr_ssh_pct, H, M] from Layer 1.
    unmatched_episodes : list[EpisodeRecord] from Layer 2.
    audit_df : DataFrame from audit.build_episode_audit_table.
    n_years : float — validated period duration in years.
    P : int — total positive events (len of expanded events database).
    cfg : dict — configuration dictionary.
    n_municipalities : int or None
        Number of unique municipalities in the analysis. If None, inferred
        from unmatched_episodes (falls back to 1 if episodes list is empty).

    Returns
    -------
    DataFrame with columns:
        thr_hs_pct, thr_ssh_pct, H, M, U,
        R_pos, B, F_soft, Score
    """
    w1 = cfg["w1_recall"]
    w2 = cfg["w2_burden"]
    w3 = cfg["w3_soft_penalty"]
    b_target_per_muni = cfg.get("b_target_per_municipality", cfg.get("b_target", 10.0))

    # Resolve n_municipalities
    if n_municipalities is None:
        if unmatched_episodes:
            n_municipalities = len({ep.municipality for ep in unmatched_episodes})
        else:
            n_municipalities = 1
    b_target_effective = b_target_per_muni * n_municipalities
    log.info(
        "Annual burden target: %.0f ep/yr/muni × %d munis = %.0f ep/yr",
        b_target_per_muni, n_municipalities, b_target_effective,
    )

    # Count unmatched episodes per pair from the episode list
    u_counts: dict[tuple, int] = {}
    for ep in unmatched_episodes:
        key = (ep.thr_hs_pct, ep.thr_ssh_pct)
        u_counts[key] = u_counts.get(key, 0) + 1

    rows: list[dict] = []
    for _, row in contingency_df.iterrows():
        hs_pct  = row["thr_hs_pct"]
        ssh_pct = row["thr_ssh_pct"]
        H = int(row["H"])
        M = int(row["M"])

        key = (hs_pct, ssh_pct)
        # U counts the number of unique episode LOCATIONS (municipality-level)
        # from the Layer 2 scan.  When multiple municipalities share the same
        # grid point, each counts separately.
        U = u_counts.get(key, 0)

        R_pos  = compute_positive_recall(H, P)
        B      = compute_annual_burden(H, U, n_years, b_target_per_muni, n_municipalities)
        F_soft = compute_soft_penalty(audit_df, hs_pct, ssh_pct)
        score  = compute_composite_score(R_pos, B, F_soft, P, w1, w2, w3)

        rows.append({
            "thr_hs_pct":  hs_pct,
            "thr_ssh_pct": ssh_pct,
            "H":           H,
            "M":           M,
            "U":           U,
            "R_pos":       round(R_pos, 4),
            "B":           round(B, 4),
            "F_soft":      round(F_soft, 4),
            "Score":       round(score, 6),
        })

    return pd.DataFrame(rows)


def rank_combinations_pu(df_scores: pd.DataFrame) -> pd.DataFrame:
    """Return df_scores sorted by optimal pair selection hierarchy.

    Selection hierarchy:
        1. Highest Score
        2. Lowest B (annual burden tiebreaker)
        3. Highest R_pos (recall tiebreaker)
        4. Highest percentile sum (most restrictive — last tiebreaker)

    Returns a copy with 'rank' column prepended (1 = best).
    """
    df = df_scores.copy()
    df["pct_sum"] = df["thr_hs_pct"] + df["thr_ssh_pct"]
    df = df.sort_values(
        by=["Score", "B", "R_pos", "pct_sum"],
        ascending=[False, True, False, False],
    ).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    df = df.drop(columns=["pct_sum"])
    return df


def select_optimal_pair_pu(df_scores: pd.DataFrame) -> dict:
    """Identify and return the PU-optimal threshold pair.

    Parameters
    ----------
    df_scores : output of compute_pu_scores()

    Returns
    -------
    dict with keys: thr_hs_pct, thr_ssh_pct, H, M, U, R_pos, B, F_soft, Score
    """
    ranked = rank_combinations_pu(df_scores)
    best = ranked.iloc[0]
    log.info(
        "PU-optimal pair: hs=q%.0f / ssh=q%.0f → "
        "Score=%.4f  R_pos=%.3f  B=%.3f  F_soft=%.1f  H=%d  U=%d",
        best["thr_hs_pct"] * 100,
        best["thr_ssh_pct"] * 100,
        best["Score"],
        best["R_pos"],
        best["B"],
        best["F_soft"],
        best["H"],
        best["U"],
    )
    return best.drop("rank").to_dict()
