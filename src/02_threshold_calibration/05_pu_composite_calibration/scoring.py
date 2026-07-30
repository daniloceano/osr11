"""
Core threshold sweep and composite score computation for Step 2e.

This module is SELF-CONTAINED with respect to the causal-window and episode-
clustering logic. It does not import from src.csi_grid_scan to avoid a known
import-chain issue (windows.py imports from src.threshold_calibration.config
which does not exist at the umbrella level). The logic below is equivalent to
the Step 2d implementation but independent by design, consistent with Step 2e's
mandate to perform its own threshold sweep.

Scored detector — recalibrated 2026-07-30
-----------------------------------------
The detector scored here IS the production detector. It used to be a pair of
percentile tests on Hs and on ``SSH_total = zos + tide``. Production stopped
reading ``SSH_total`` on 2026-07-29 (MHWS method) and, under the HAT gate
adopted on 2026-07-30, detects on tide-free ``zos`` with an explicit level
gate. Scoring threshold pairs against a variable the detector never reads is a
scientific inconsistency; the recalibration is recorded in AUD-01 §14::

    wave  : Hs  >= q_hs  local                (unchanged)
    level : zos >= q_zos local                (was SSH_total)
    gate  : max(SWL) > HAT over the overlap days, with
            SWL = (zos - local mean of zos) + tide_daily_max
            HAT = max(tide_daily_max) over 1993-2025, per grid point

The matching window and the episode-audit machinery (E_i, I_i, C_i, q_i) are
untouched. Three quantities in the SCORING criterion were changed on the same
date, by explicit decision, after the recalibrated sweep showed the previous
criterion had no interior optimum — it preferred, monotonically, to detect
nothing. See AUD-01 §14 and outputs/audit/AUD-01_step2e_score_surface/:

  * the burden term became a TWO-SIDED deviation from an expected detection
    rate anchored on Leal et al. (2024), instead of a one-sided ceiling that
    was minimised at zero detections;
  * the score weights moved from 0.60/0.20/0.20 to 0.30/0.60/0.10, so the only
    externally anchored term carries the decision;
  * the confidence alphas moved from 0.60/0.30/0.10 to 0.20/0.50/0.30, because
    E_i = 1 in only 0.04 % of episodes, which capped q_i at 0.40 by
    construction and measured the sparseness of the documentary record rather
    than the implausibility of a detection.

One detector, both layers. Layers 1 and 2 now call the same
:func:`accepted_episodes_at_point`, so a "hit" and an "unmatched episode" are
by construction the same object seen from the two sides of the matching
relation. Under the previous implementation Layer 1 asked a day-level question
and Layer 2 an episode-level one; without a gate the two are equivalent (an
episode intersects a causal window exactly when one of its compound days does),
so this is a strict generalisation, not a change of criterion.

Threshold period vs. scan period is unchanged: percentiles, the local mean of
``zos``, and HAT all come from the FULL 1993-2025 record, while the hit/miss
and unmatched scan is restricted to the validated event-database period.

Pipeline
--------
1. build_level_cache_pu      — per grid point: zos, SWL and HAT
2. accepted_episodes_at_point— the production detector at one point/pair
3. run_hits_misses_pu        — Layer 1: event-by-event hit/miss across all pairs
4. collect_unmatched_episodes_for_pair  — Layer 2: gather episode details (not
                                         just counts) for one pair
5. run_unmatched_all_pairs   — Layer 2 for all pairs
6. run_detection_census      — accepted-episode sample size per pair
7. compute_pu_scores         — assemble composite Score(θ) for all pairs
8. build_score_decomposition — export full equation-level decomposition
9. rank_combinations_pu      — sort by Score descending
10. select_optimal_pair_pu   — return the top-ranked pair

Score formula
-------------
    Score(θ) = w1 · R_pos(θ)  −  w2 · B(θ)  −  w3 · F_soft(θ) / P

    R_pos(θ) = H(θ) / P                          [positive recall]
    rate(θ)  = (H+U) / (Y × n_municipalities)    [detections/muni/year]
    B(θ)     = min(1, |log10(rate(θ)/target)|)   [two-sided rate deviation]
    F_soft(θ) = Σᵢ (1 − qᵢ)                      [soft unmatched penalty]
    P        = total positive (reported) events
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
import logging

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


# ── Level cache: the material the production gate needs ───────────────────────

@dataclass
class PointLevelData:
    """Everything the production level test needs at one grid point.

    ``zos`` is the detection variable — tide-free, so the percentile threshold
    measures meteorological rarity rather than the spring-tide envelope.
    ``swl`` and ``hat`` serve the gate and are never thresholded by percentile.
    """

    zos: pd.Series = field(repr=False)      # tide-free level, full record
    swl: pd.Series = field(repr=False)      # (zos - mean) + tide_daily_max
    hat: float                              # max(tide_daily_max), full record
    zos_mean: float                         # local mean of zos, full record


def build_level_cache_pu(
    records: list,
    tide_cache: dict,
) -> dict[tuple[float, float], PointLevelData]:
    """Build the tide-free level series, the SWL and the HAT per grid point.

    ``zos`` is taken straight from the event record; it is already the raw
    GLORYS12 field, referenced to the geoid. The mean is removed inside
    ``swl`` because HAT is a height above local mean sea level while ``zos`` is
    a height above the geoid — the same reasoning as
    ``mhws_datum.still_water_level``, which this mirrors exactly.

    ``hat`` is ``max(tide_daily_max)`` over the FULL 1993-2025 record, the same
    estimator the production detector uses. 33 years cover the 18.6-year nodal
    cycle.

    Parameters
    ----------
    records : list[EventRecord]
    tide_cache : dict mapping (lat, lon) → daily-maximum tide pd.Series

    Returns
    -------
    dict mapping (lat, lon) → PointLevelData
    """
    from src.tidal_sensitivity.tides import get_tide_for_record

    cache: dict[tuple[float, float], PointLevelData] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key in cache:
            continue
        tide = get_tide_for_record(rec, tide_cache)
        zos = rec.ssh_clim
        tide_aligned = tide.reindex(zos.index)
        zos_mean = float(zos.dropna().mean()) if zos.notna().any() else np.nan
        swl = (zos - zos_mean) + tide_aligned
        hat = float(tide.dropna().max()) if tide.notna().any() else np.nan
        cache[key] = PointLevelData(
            zos=zos, swl=swl, hat=hat, zos_mean=zos_mean
        )

    finite_hat = [v.hat for v in cache.values() if np.isfinite(v.hat)]
    log.info(
        "Level cache built for %d unique grid points. HAT %.3f–%.3f m.",
        len(cache),
        min(finite_hat) if finite_hat else float("nan"),
        max(finite_hat) if finite_hat else float("nan"),
    )
    return cache


#: Backwards-compatible alias. The old name described the SSH_total cache that
#: the superseded detector consumed; the object it returns is different now.
build_ssh_total_cache_pu = build_level_cache_pu


# ── The production detector, at one grid point and one threshold pair ─────────

def accepted_episodes_at_point(
    hs_clim: pd.Series,
    level: PointLevelData,
    thr_hs_pct: float,
    thr_zos_pct: float,
    time_index: pd.DatetimeIndex,
    max_gap_days: int,
) -> tuple[list[pd.DatetimeIndex], float, float]:
    """Detect the accepted compound episodes at one point for one pair.

    This is the production detector: two tide-free percentile tests select the
    candidate compound days, and the gate ``max(SWL) > HAT`` decides which
    episodes survive. The gate is applied to the episode as a whole, exactly as
    ``compound_events_at_point`` applies it to the overlap days of a compound
    group, because it asks whether the water rose above the datum *at some
    point during the event*, not on every day of it.

    Returns
    -------
    (accepted episodes, thr_hs absolute, thr_zos absolute)
        The absolute thresholds are returned so callers can report them without
        recomputing the percentiles.
    """
    thr_hs = _local_threshold(hs_clim, thr_hs_pct)
    thr_zos = _local_threshold(level.zos, thr_zos_pct)
    if np.isnan(thr_hs) or np.isnan(thr_zos) or not np.isfinite(level.hat):
        return [], thr_hs, thr_zos

    hs_aligned = hs_clim.reindex(time_index)
    zos_aligned = level.zos.reindex(time_index)
    swl_aligned = level.swl.reindex(time_index)

    compound_mask = (hs_aligned >= thr_hs) & (zos_aligned >= thr_zos)
    episodes = _cluster_episodes(compound_mask, max_gap_days)
    if not episodes:
        return [], thr_hs, thr_zos

    swl_values = swl_aligned.to_numpy(dtype=float)
    position = pd.Series(np.arange(len(time_index)), index=time_index)

    accepted: list[pd.DatetimeIndex] = []
    for episode in episodes:
        idx = position.reindex(episode).to_numpy(dtype=float)
        idx = idx[np.isfinite(idx)].astype(int)
        if idx.size == 0:
            continue
        window = swl_values[idx]
        if not np.isfinite(window).any():
            continue
        if float(np.nanmax(window)) > level.hat:
            accepted.append(episode)
    return accepted, thr_hs, thr_zos


def _point_index(records: list) -> dict[tuple[float, float], list]:
    """Group event records by their grid point."""
    grouped: dict[tuple[float, float], list] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        grouped.setdefault(key, []).append(rec)
    return grouped


def _hs_clim_by_point(records: list) -> dict[tuple[float, float], pd.Series]:
    series: dict[tuple[float, float], pd.Series] = {}
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        if key not in series:
            series[key] = rec.hs_clim
    return series


# ── Layer 1: event-by-event hit/miss ─────────────────────────────────────────

def _hits_misses_for_pair(
    records: list,
    level_cache: dict,
    time_index: pd.DatetimeIndex,
    thr_hs_pct: float,
    thr_zos_pct: float,
    max_gap_days: int,
    offsets: list[int],
) -> tuple[int, int]:
    """Return (H, M) for one threshold pair.

    An event is captured when at least one ACCEPTED compound episode at its
    grid point shares a day with its causal window. Episodes are detected once
    per grid point and reused for every event there.
    """
    hs_by_point = _hs_clim_by_point(records)
    H = M = 0
    for point, point_records in _point_index(records).items():
        level = level_cache.get(point)
        if level is None:
            M += len(point_records)
            continue
        accepted, _, _ = accepted_episodes_at_point(
            hs_by_point[point], level, thr_hs_pct, thr_zos_pct,
            time_index, max_gap_days,
        )
        accepted_days: set = set()
        for episode in accepted:
            accepted_days.update(episode)
        for rec in point_records:
            window = _build_causal_window(rec.date, time_index, offsets)
            if window and accepted_days & set(window):
                H += 1
            else:
                M += 1
    return H, M


def run_hits_misses_pu(
    records: list,
    level_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    offsets: list[int],
    max_gap_days: int = 1,
    workers: int = 1,
) -> pd.DataFrame:
    """Layer 1: hit/miss for all threshold pairs.

    Parameters
    ----------
    records : list[EventRecord]
    level_cache : dict mapping (lat, lon) → PointLevelData
    time_index : pd.DatetimeIndex — validated scan period
    hs_percentiles, ssh_percentiles : list of float
    offsets : list[int] — causal window offsets
    max_gap_days : int — episode clustering tolerance
    workers : int — process pool size; 1 runs serially

    Returns
    -------
    DataFrame with columns [thr_hs_pct, thr_ssh_pct, H, M]
    """
    pairs = [(hs, ssh) for hs in hs_percentiles for ssh in ssh_percentiles]
    log.info(
        "[Layer 1] %d pairs over %d grid points (workers=%d)",
        len(pairs), len(_point_index(records)), workers,
    )
    tasks = [
        (records, level_cache, time_index, hs, ssh, max_gap_days, offsets)
        for hs, ssh in pairs
    ]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # executor.map preserves input order, unlike as_completed.
            results = list(executor.map(_hits_misses_task, tasks))
    else:
        results = [_hits_misses_task(task) for task in tasks]

    return pd.DataFrame(
        [
            {"thr_hs_pct": hs, "thr_ssh_pct": ssh, "H": H, "M": M}
            for (hs, ssh), (H, M) in zip(pairs, results)
        ]
    )


def _hits_misses_task(task: tuple) -> tuple[int, int]:
    return _hits_misses_for_pair(*task)


# ── Layer 2: unmatched episode collection ────────────────────────────────────

def _episodes_with_metadata_for_pair(
    records: list,
    level_cache: dict,
    time_index: pd.DatetimeIndex,
    thr_hs_pct: float,
    thr_zos_pct: float,
    max_gap_days: int,
    offsets: list[int],
) -> tuple[list[EpisodeRecord], dict]:
    """Detect accepted episodes for one pair and split them matched/unmatched.

    Returns the UNMATCHED episodes as ``EpisodeRecord`` objects (one per
    municipality sharing the grid point, as before) plus a census dictionary
    describing the sample size the score is being computed on.

    ``ssh_peak`` carries the episode maximum of ``zos`` — the detection
    variable — so that ``audit.compute_I_i`` keeps comparing a peak against the
    percentile of the series that produced it. ``swl_peak`` carries the gated
    quantity and is reported alongside.
    """
    hs_by_point = _hs_clim_by_point(records)
    point_records = _point_index(records)

    point_to_munis: dict[tuple[float, float], list[str]] = {}
    for point, recs in point_records.items():
        names: list[str] = []
        for rec in recs:
            if rec.municipality not in names:
                names.append(rec.municipality)
        point_to_munis[point] = names

    hs_tag = f"hs{round(thr_hs_pct * 100):02d}"
    ssh_tag = f"ssh{round(thr_zos_pct * 100):02d}"

    episodes_out: list[EpisodeRecord] = []
    n_accepted = n_matched = n_points_with_episodes = 0
    thr_hs_values: list[float] = []
    thr_zos_values: list[float] = []

    for point, recs in point_records.items():
        lat, lon = point
        level = level_cache.get(point)
        hs_clim = hs_by_point[point]
        if level is None or hs_clim.empty or level.zos.empty:
            continue

        accepted, thr_hs, thr_zos = accepted_episodes_at_point(
            hs_clim, level, thr_hs_pct, thr_zos_pct, time_index, max_gap_days
        )
        if np.isfinite(thr_hs):
            thr_hs_values.append(float(thr_hs))
        if np.isfinite(thr_zos):
            thr_zos_values.append(float(thr_zos))
        if not accepted:
            continue
        n_accepted += len(accepted)
        n_points_with_episodes += 1

        event_windows = [
            window
            for window in (
                _build_causal_window(rec.date, time_index, offsets) for rec in recs
            )
            if window
        ]

        hs_aligned = hs_clim.reindex(time_index)
        zos_aligned = level.zos.reindex(time_index)
        swl_aligned = level.swl.reindex(time_index)

        for ep_days in accepted:
            if _episode_is_paired(ep_days, event_windows):
                n_matched += 1
                continue  # matched → hit; skip

            d_start = ep_days[0]
            d_end = ep_days[-1]

            hs_ep = hs_aligned.loc[d_start:d_end].dropna()
            zos_ep = zos_aligned.loc[d_start:d_end].dropna()
            swl_ep = swl_aligned.loc[d_start:d_end].dropna()
            hs_peak = float(hs_ep.max()) if not hs_ep.empty else np.nan
            zos_peak = float(zos_ep.max()) if not zos_ep.empty else np.nan
            swl_peak = float(swl_ep.max()) if not swl_ep.empty else np.nan

            for muni in point_to_munis.get(point, ["unknown"]):
                muni_tag = muni[:3].upper().replace(" ", "_")
                date_tag = d_start.strftime("%Y%m%d")
                episode_id = f"{hs_tag}_{ssh_tag}_{muni_tag}_{date_tag}"

                episodes_out.append(EpisodeRecord(
                    episode_id=episode_id,
                    thr_hs_pct=thr_hs_pct,
                    thr_ssh_pct=thr_zos_pct,
                    municipality=muni,
                    grid_lat=lat,
                    grid_lon=lon,
                    date_start=d_start,
                    date_end=d_end,
                    hs_peak=hs_peak,
                    ssh_peak=zos_peak,
                    n_days=len(ep_days),
                    swl_peak=swl_peak,
                    hat=float(level.hat),
                ))

    census = {
        "thr_hs_pct": thr_hs_pct,
        "thr_ssh_pct": thr_zos_pct,
        "n_accepted_episodes": n_accepted,
        "n_accepted_matched": n_matched,
        "n_accepted_unmatched": n_accepted - n_matched,
        "n_points_with_episodes": n_points_with_episodes,
        "n_points": len(point_records),
        "median_thr_hs_abs": (
            round(float(np.median(thr_hs_values)), 4) if thr_hs_values else None
        ),
        "min_thr_hs_abs": (
            round(float(np.min(thr_hs_values)), 4) if thr_hs_values else None
        ),
        "median_thr_zos_abs": (
            round(float(np.median(thr_zos_values)), 4) if thr_zos_values else None
        ),
    }
    return episodes_out, census


def collect_unmatched_episodes_for_pair(
    records: list,
    level_cache: dict,
    time_index: pd.DatetimeIndex,
    thr_hs_pct: float,
    thr_ssh_pct: float,
    max_gap_days: int,
    offsets: list[int],
) -> list[EpisodeRecord]:
    """Collect unmatched episodes for one threshold pair, with full metadata.

    Unlike Step 2d's ``_count_fa_detailed()`` which only returns counts, this
    returns ``EpisodeRecord`` objects carrying peak Hₛ, peak ``zos``, peak SWL,
    dates and municipality — required by ``audit.py`` for the q_i computation.
    """
    episodes, _ = _episodes_with_metadata_for_pair(
        records, level_cache, time_index,
        thr_hs_pct, thr_ssh_pct, max_gap_days, offsets,
    )
    return episodes


def _unmatched_task(task: tuple) -> tuple[list[EpisodeRecord], dict]:
    return _episodes_with_metadata_for_pair(*task)


def run_unmatched_all_pairs(
    records: list,
    level_cache: dict,
    time_index: pd.DatetimeIndex,
    hs_percentiles: list[float],
    ssh_percentiles: list[float],
    max_gap_days: int,
    offsets: list[int],
    workers: int = 1,
    return_census: bool = False,
):
    """Layer 2: collect unmatched episodes for ALL threshold pairs.

    Returns
    -------
    list[EpisodeRecord], or (list[EpisodeRecord], census DataFrame) when
    ``return_census`` is set. The census reports, per pair, how many accepted
    episodes the score was computed on — the sample size that decides whether a
    high-percentile pair is informative or degenerate.
    """
    pairs = [(hs, ssh) for hs in hs_percentiles for ssh in ssh_percentiles]
    log.info("[Layer 2] %d pairs (workers=%d)", len(pairs), workers)
    tasks = [
        (records, level_cache, time_index, hs, ssh, max_gap_days, offsets)
        for hs, ssh in pairs
    ]
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(_unmatched_task, tasks))
    else:
        results = [_unmatched_task(task) for task in tasks]

    all_episodes: list[EpisodeRecord] = []
    census_rows: list[dict] = []
    for episodes, census in results:
        all_episodes.extend(episodes)
        census_rows.append(census)

    log.info(
        "Layer 2 complete. Total unmatched episode-municipality rows: %d",
        len(all_episodes),
    )
    if return_census:
        return all_episodes, pd.DataFrame(census_rows)
    return all_episodes


def build_detection_census(
    census_df: pd.DataFrame,
    contingency_df: pd.DataFrame,
    P: int,
) -> pd.DataFrame:
    """Annotate the per-pair census with recall and a degeneracy flag.

    A pair is flagged ``degenerate`` when it accepts fewer compound episodes
    over the whole calibration domain than there are positive events to
    recall. Below that line the composite score is not discriminating between
    detectors — it is ranking noise, because the detector cannot in principle
    reach a meaningful recall and the burden and soft-penalty terms both
    collapse toward zero, which the score reads as an improvement.
    """
    merged = census_df.merge(
        contingency_df, on=["thr_hs_pct", "thr_ssh_pct"], validate="one_to_one"
    )
    merged["P"] = P
    merged["R_pos"] = (merged["H"] / P).round(6) if P else 0.0
    merged["episodes_per_positive"] = (
        merged["n_accepted_episodes"] / P
    ).round(4) if P else np.nan
    merged["degenerate"] = merged["n_accepted_episodes"] < P
    merged["near_empty"] = merged["n_accepted_episodes"] < 10
    return merged.sort_values(["thr_hs_pct", "thr_ssh_pct"]).reset_index(drop=True)


# ── Composite score computation ───────────────────────────────────────────────

def compute_positive_recall(H: int, P: int) -> float:
    """R_pos = H / P.  Returns 0.0 if P = 0 (degenerate case)."""
    if P == 0:
        return 0.0
    return float(H) / float(P)


def detection_rate_per_municipality(
    H: int, U: int, n_years: float, n_municipalities: int
) -> float:
    """Detections per municipality per year at one threshold pair."""
    denominator = n_years * max(n_municipalities, 1)
    if denominator <= 0:
        return float("nan")
    return (H + U) / denominator


def compute_annual_burden(
    H: int,
    U: int,
    n_years: float,
    b_target_per_muni: float,
    n_municipalities: int,
    mode: str = "two_sided",
) -> float:
    """Burden term B(θ), in [0, 1].

    ``two_sided`` (current, adopted 2026-07-30)::

        rate = (H + U) / (Y × n_municipalities)
        B    = min(1, |log10(rate / target)|)

    A deviation from the expected detection rate, penalised symmetrically in
    relative terms: detecting half the expected rate costs exactly as much as
    detecting twice. This is what gives the composite score an interior
    optimum. The superseded one-sided form was minimised at ZERO detections, so
    it pulled in the same direction as the soft penalty and could not anchor
    anything; raising its weight only strengthened the pull towards an empty
    detector. See AUD-01 §14 and outputs/audit/AUD-01_step2e_score_surface/.

    ``ceiling`` (superseded, kept reproducible)::

        B = min(1, (H + U) / (Y × target × n_municipalities))

    Parameters
    ----------
    H : int — hits (matched detected episodes)
    U : int — unmatched detected episodes
    n_years : float — length of validated period in years
    b_target_per_muni : float — expected annual detections *per municipality*
        under ``two_sided``; the acceptable ceiling under ``ceiling``
    n_municipalities : int — number of unique municipalities in the analysis
    mode : str — "two_sided" or "ceiling"

    Returns
    -------
    float in [0, 1]
    """
    if b_target_per_muni <= 0 or n_years <= 0:
        return 1.0
    rate = detection_rate_per_municipality(H, U, n_years, n_municipalities)
    if not np.isfinite(rate):
        return 1.0

    if mode == "ceiling":
        return float(min(1.0, rate / b_target_per_muni))
    if mode != "two_sided":
        raise ValueError(f"Unknown burden mode: {mode!r}")

    # A detector that flags nothing is maximally wrong under a two-sided
    # anchor, so the log of a zero rate saturates the penalty rather than
    # diverging.
    if rate <= 0:
        return 1.0
    return float(min(1.0, abs(np.log10(rate / b_target_per_muni))))


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
    burden_mode = cfg.get("burden_mode", "two_sided")
    log.info(
        "Burden anchor: %.2f detections/municipality/year over %d munis "
        "(mode=%s)",
        b_target_per_muni, n_municipalities, burden_mode,
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
        B      = compute_annual_burden(
            H, U, n_years, b_target_per_muni, n_municipalities, burden_mode
        )
        F_soft = compute_soft_penalty(audit_df, hs_pct, ssh_pct)
        score  = compute_composite_score(R_pos, B, F_soft, P, w1, w2, w3)

        rows.append({
            "thr_hs_pct":  hs_pct,
            "thr_ssh_pct": ssh_pct,
            "H":           H,
            "M":           M,
            "U":           U,
            "rate_per_muni_yr": round(
                detection_rate_per_municipality(H, U, n_years, n_municipalities), 4
            ),
            "R_pos":       round(R_pos, 4),
            "B":           round(B, 4),
            "F_soft":      round(F_soft, 4),
            "Score":       round(score, 6),
        })

    return pd.DataFrame(rows)


def build_score_decomposition(
    contingency_df: pd.DataFrame,
    unmatched_episodes: list[EpisodeRecord],
    audit_df: pd.DataFrame,
    n_years: float,
    P: int,
    cfg: dict,
    n_municipalities: int | None = None,
) -> pd.DataFrame:
    """Build the full Score decomposition table for all threshold pairs.

    For each pair, exports every intermediate quantity used to compute Score(θ)
    so that the contribution of each term is transparent.

    Returns
    -------
    DataFrame with columns:
        hs_percentile, ssh_percentile, H, M, U, P, Y (n_years),
        R_pos, B_raw, B, F_soft, term_recall_raw, term_burden_raw,
        term_fsoft_raw, w1, w2, w3, term_recall_weighted,
        term_burden_weighted, term_fsoft_weighted, Score
    """
    w1 = cfg["w1_recall"]
    w2 = cfg["w2_burden"]
    w3 = cfg["w3_soft_penalty"]
    b_target_per_muni = cfg.get("b_target_per_municipality", cfg.get("b_target", 10.0))

    if n_municipalities is None:
        if unmatched_episodes:
            n_municipalities = len({ep.municipality for ep in unmatched_episodes})
        else:
            n_municipalities = 1
    burden_mode = cfg.get("burden_mode", "two_sided")

    u_counts: dict[tuple, int] = {}
    for ep in unmatched_episodes:
        key = (ep.thr_hs_pct, ep.thr_ssh_pct)
        u_counts[key] = u_counts.get(key, 0) + 1

    rows: list[dict] = []
    for _, row in contingency_df.iterrows():
        hs_pct = row["thr_hs_pct"]
        ssh_pct = row["thr_ssh_pct"]
        H = int(row["H"])
        M = int(row["M"])
        U = u_counts.get((hs_pct, ssh_pct), 0)

        R_pos = float(H) / float(P) if P > 0 else 0.0
        rate = detection_rate_per_municipality(H, U, n_years, n_municipalities)
        # B_raw is the uncapped deviation, so the decomposition table shows how
        # far a pair sits from the anchor even where the cap hides it.
        b_raw = (
            abs(np.log10(rate / b_target_per_muni))
            if (burden_mode == "two_sided" and rate > 0 and b_target_per_muni > 0)
            else (rate / b_target_per_muni if b_target_per_muni > 0 else 1.0)
        )
        B = compute_annual_burden(
            H, U, n_years, b_target_per_muni, n_municipalities, burden_mode
        )
        F_soft = compute_soft_penalty(audit_df, hs_pct, ssh_pct)

        term_fsoft_raw = F_soft / P if P > 0 else 0.0
        term_recall_weighted = w1 * R_pos
        term_burden_weighted = -w2 * B
        term_fsoft_weighted = -w3 * term_fsoft_raw
        score = term_recall_weighted + term_burden_weighted + term_fsoft_weighted

        rows.append({
            "hs_percentile": round(hs_pct * 100),
            "ssh_percentile": round(ssh_pct * 100),
            "H": H,
            "M": M,
            "U": U,
            "P": P,
            "Y": round(n_years, 2),
            "n_municipalities": n_municipalities,
            "rate_per_muni_yr": round(rate, 6),
            "burden_target_per_muni_yr": b_target_per_muni,
            "burden_mode": burden_mode,
            "R_pos": round(R_pos, 6),
            "B_raw": round(b_raw, 6),
            "B": round(B, 6),
            "F_soft": round(F_soft, 4),
            "term_recall_raw": round(R_pos, 6),
            "term_burden_raw": round(B, 6),
            "term_fsoft_raw": round(term_fsoft_raw, 6),
            "w1": w1,
            "w2": w2,
            "w3": w3,
            "term_recall_weighted": round(term_recall_weighted, 6),
            "term_burden_weighted": round(term_burden_weighted, 6),
            "term_fsoft_weighted": round(term_fsoft_weighted, 6),
            "Score": round(score, 6),
        })

    df = pd.DataFrame(rows)
    log.info(
        "Score decomposition table: %d rows × %d columns",
        len(df), len(df.columns),
    )
    return df


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


def get_event_capture_status(
    records: list,
    level_cache: dict,
    time_index: "pd.DatetimeIndex",
    thr_hs_pct: float,
    thr_ssh_pct: float,
    offsets: list[int],
    max_gap_days: int = 1,
    events_combined: "pd.DataFrame | None" = None,
) -> pd.DataFrame:
    """Return per-event capture status and peak values at a specific threshold pair.

    Evaluates each event against the production detector at the given pair and
    reports the peak of every quantity the detector reads inside the causal
    window, for the scatter diagnostics (analogous to Step 2d's
    plot_peak_scatter data preparation).

    Parameters
    ----------
    records : list[EventRecord]
    level_cache : dict mapping (lat, lon) → PointLevelData
    time_index : pd.DatetimeIndex
    thr_hs_pct, thr_ssh_pct : float — threshold percentiles (e.g. 0.90)
    offsets : list[int] — causal window offsets (e.g. [-2, -1, 0, 1])
    max_gap_days : int — episode clustering tolerance
    events_combined : optional combined events DataFrame with 'disaster_id' and
        'source' columns.  When supplied, the source label ("expanded",
        "legacy", "both") is joined to each row by disaster_id.

    Returns
    -------
    DataFrame with columns:
        event_idx     : int
        disaster_id   : int
        municipality  : str
        date          : pd.Timestamp
        captured      : bool  — an accepted episode overlaps the causal window
        peak_hs_causal : float — max Hₛ in causal window [D-2, D+1]
        peak_ssh_causal: float — max zos in causal window (detection variable)
        peak_swl_causal: float — max SWL in causal window (gated quantity)
        thr_hs        : float — local Hₛ threshold at the event's grid point
        thr_ssh       : float — local zos threshold at the event's grid point
        hat           : float — local HAT datum, the gate level
        source        : str   — "expanded" | "legacy" | "both" | "unknown"
        coastal_sector: str   — coastal sector name (empty if unknown)
    """
    # Provenance lookup keyed by disaster_id (if available)
    source_map: dict[int, str] = {}
    sector_map_ev: dict[int, str] = {}
    if events_combined is not None and "disaster_id" in events_combined.columns:
        if "source" in events_combined.columns:
            source_map = dict(
                zip(events_combined["disaster_id"].astype(int),
                    events_combined["source"].astype(str))
            )
        if "coastal_sector" in events_combined.columns:
            sector_map_ev = dict(
                zip(events_combined["disaster_id"].astype(int),
                    events_combined["coastal_sector"].astype(str))
            )

    # Detect once per grid point and reuse for every event there.
    hs_by_point = _hs_clim_by_point(records)
    accepted_days_by_point: dict[tuple[float, float], set] = {}
    thresholds_by_point: dict[tuple[float, float], tuple[float, float]] = {}
    for point in _point_index(records):
        level = level_cache.get(point)
        if level is None:
            accepted_days_by_point[point] = set()
            thresholds_by_point[point] = (float("nan"), float("nan"))
            continue
        accepted, thr_hs, thr_zos = accepted_episodes_at_point(
            hs_by_point[point], level, thr_hs_pct, thr_ssh_pct,
            time_index, max_gap_days,
        )
        days: set = set()
        for episode in accepted:
            days.update(episode)
        accepted_days_by_point[point] = days
        thresholds_by_point[point] = (thr_hs, thr_zos)

    rows: list[dict] = []
    for rec in records:
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        level = level_cache.get(key)
        thr_hs, thr_ssh = thresholds_by_point.get(key, (float("nan"), float("nan")))

        window = _build_causal_window(rec.date, time_index, offsets)
        captured = bool(window) and bool(
            accepted_days_by_point.get(key, set()) & set(window)
        )

        # Peak values within causal window [D-2, D+1]
        event_dt  = pd.Timestamp(rec.date)
        win_start = event_dt - pd.Timedelta(days=2)
        win_end   = event_dt + pd.Timedelta(days=1)

        hs_win = rec.hs_clim.loc[win_start:win_end]
        if level is not None and not level.zos.empty:
            zos_win = level.zos.loc[win_start:win_end]
            swl_win = level.swl.loc[win_start:win_end]
        else:
            zos_win = swl_win = pd.Series(dtype=float)

        peak_hs  = float(hs_win.max())  if hs_win.notna().any()  else float("nan")
        peak_zos = float(zos_win.max()) if zos_win.notna().any() else float("nan")
        peak_swl = float(swl_win.max()) if swl_win.notna().any() else float("nan")

        rows.append({
            "event_idx":      int(rec.event_idx),
            "disaster_id":    int(rec.disaster_id),
            "municipality":   rec.municipality,
            "date":           pd.Timestamp(rec.date),
            "captured":       captured,
            "peak_hs_causal": peak_hs,
            "peak_ssh_causal": peak_zos,
            "peak_swl_causal": peak_swl,
            "thr_hs":         thr_hs,
            "thr_ssh":        thr_ssh,
            "hat":            float(level.hat) if level is not None else float("nan"),
            "source":         source_map.get(int(rec.disaster_id), "unknown"),
            "coastal_sector": sector_map_ev.get(int(rec.disaster_id), ""),
        })

    df = pd.DataFrame(rows)
    n_hit  = int(df["captured"].sum())
    n_miss = len(df) - n_hit
    log.info(
        "Event capture status at hs=q%.0f / ssh=q%.0f: H=%d  M=%d  (of %d evaluable events)",
        thr_hs_pct * 100, thr_ssh_pct * 100, n_hit, n_miss, len(df),
    )
    return df
