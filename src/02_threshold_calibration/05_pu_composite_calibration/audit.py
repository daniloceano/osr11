"""
Confidence weight (qᵢ) computation for Step 2e — PU Composite Calibration.

Each unmatched detected episode receives a plausibility weight:

    q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)

Components
----------
E_i  ∈ {0, 1}   External evidence: does any available documentary record
                 corroborate this episode? Checked against the legacy Civil
                 Defense database (and optional manual override CSV).

I_i  ∈ [0, 1]   Physical intensity: how extreme are the episode's Hₛ and
                 SSH_total peaks relative to the detection threshold?

C_i  ∈ [0, 1]   Context coherence: mean of three binary indicators:
                    C_i^season   — episode in the climatological active season
                    C_i^multi    — concurrent detection in a neighboring municipality
                    C_i^exposure — municipality in the high-exposure northern sector

The soft unmatched penalty is:

    F_soft(θ) = Σ_i (1 − q_i)

A fully corroborated episode (E_i=1, I_i≈1, C_i≈1) → q_i≈1 → penalty≈0.
A genuinely anomalous, isolated, off-season episode → q_i≈0 → penalty≈1.

Adaptation note: E_i as documentary evidence
---------------------------------------------
The ideal definition of E_i requires an independent external evidence layer
(Civil Defense bulletins, news archives, social media) broader than the datasets
already used to define P. Because this repository has limited documentary density,
E_i is computed from:

  1. The legacy Civil Defense database (reported_events_Karine_sc.csv, 105 rows /
     91 unique events). Any legacy event that spatiotemporally overlaps an unmatched
     episode sets E_i = 1 for that episode.

  2. An optional researcher-curated manual override CSV
     (data/audit/unmatched_episode_audit.csv). When populated, manual flags take
     priority over the rule-based approach above.

Although neither source is fully independent, together they provide meaningful
signal: legacy events NOT in the expanded positive set (e.g., events from 2021–2023,
or North-sector events absent from the expanded database) can still corroborate
unmatched episodes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ── Episode record (carries all data needed for q_i computation) ──────────────

@dataclass
class EpisodeRecord:
    """One unmatched detected episode at one grid point / municipality."""
    episode_id: str               # unique string key, e.g. "hs70_ssh75_FLO_20150619"
    thr_hs_pct: float
    thr_ssh_pct: float
    municipality: str
    grid_lat: float
    grid_lon: float
    date_start: pd.Timestamp
    date_end: pd.Timestamp
    hs_peak: float                # episode maximum Hₛ value
    ssh_peak: float               # episode maximum SSH_total value
    n_days: int                   # number of compound days in episode


# ── E_i: external evidence ────────────────────────────────────────────────────

def compute_E_i_from_database(
    episode: EpisodeRecord,
    legacy_df: pd.DataFrame,
    match_offsets: list[int],
) -> int:
    """Compute E_i for one episode using the legacy Civil Defense database.

    E_i = 1 if any legacy event matches the episode's municipality AND falls
    within the episode's expanded temporal window:
        [date_start + min_offset, date_end + max_offset]

    Parameters
    ----------
    episode : EpisodeRecord
    legacy_df : DataFrame with columns [municipality, date]
        The legacy Leal et al. (2024) database (from utils.load_legacy_events).
    match_offsets : list[int]
        Causal window offsets (e.g., [-2, -1, 0, 1]).

    Returns
    -------
    int — 0 or 1
    """
    if legacy_df.empty:
        return 0

    early = episode.date_start + pd.Timedelta(days=min(match_offsets))
    late  = episode.date_end   + pd.Timedelta(days=max(match_offsets))

    mask = (
        (legacy_df["municipality"] == episode.municipality)
        & (legacy_df["date"] >= early)
        & (legacy_df["date"] <= late)
    )
    return int(mask.any())


def load_E_i_overrides(audit_csv_path: Path) -> dict[str, int]:
    """Load manual E_i overrides from the researcher-curated audit CSV.

    The CSV is optional. If absent or empty, an empty dict is returned and
    E_i falls back to the rule-based database approach.

    Expected columns:
        episode_id : str  — matches EpisodeRecord.episode_id
        E_i        : int  — 0 or 1

    Additional columns (municipality_code, date_start, date_end, evidence_source,
    audit_date, auditor_notes) are allowed and ignored.

    Parameters
    ----------
    audit_csv_path : Path

    Returns
    -------
    dict mapping episode_id → E_i override value.
    """
    path = Path(audit_csv_path)
    if not path.exists():
        log.debug("Audit CSV not found (%s); E_i overrides disabled.", path)
        return {}

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        log.warning("Could not read audit CSV %s: %s — E_i overrides disabled.", path, exc)
        return {}

    if "episode_id" not in df.columns or "E_i" not in df.columns:
        log.warning(
            "Audit CSV at %s lacks 'episode_id' or 'E_i' column — "
            "E_i overrides disabled. Found columns: %s",
            path, list(df.columns),
        )
        return {}

    overrides = {}
    for _, row in df.iterrows():
        eid = str(row["episode_id"]).strip()
        try:
            ei_val = int(row["E_i"])
        except (ValueError, TypeError):
            continue
        if ei_val not in (0, 1):
            continue
        overrides[eid] = ei_val

    log.info("Manual E_i overrides loaded: %d entries from %s", len(overrides), path)
    return overrides


# ── I_i: physical intensity ───────────────────────────────────────────────────

def compute_I_i(
    episode: EpisodeRecord,
    thr_hs_pct: float,
    thr_ssh_pct: float,
    hs_clim: pd.Series,
    ssh_clim: pd.Series,
) -> float:
    """Compute physical intensity score I_i ∈ [0, 1].

    Measures how far above the detection threshold the episode's peak values are,
    normalised by the remaining tail of the distribution:

        I_i = 0.5 × [
            (φ_Hs(peak_hs) − thr_hs_pct) / (1 − thr_hs_pct)
            + (φ_SSH(peak_ssh) − thr_ssh_pct) / (1 − thr_ssh_pct)
        ]

    where φ_Hs(peak_hs) is the empirical percentile of episode's Hₛ peak in the
    local climatological series.

    I_i = 0  when peak values are at the detection threshold.
    I_i → 1  when peak values approach the upper tail of the distribution.

    Parameters
    ----------
    episode : EpisodeRecord
    thr_hs_pct, thr_ssh_pct : float
        Detection thresholds as percentiles (e.g., 0.75 for q75).
    hs_clim, ssh_clim : pd.Series
        Full climatological series at the grid point (for empirical CDF estimation).

    Returns
    -------
    float in [0, 1]
    """
    def _exceedance(peak: float, series: pd.Series, thr_pct: float) -> float:
        finite = series.dropna()
        if finite.empty or np.isnan(peak):
            return 0.0
        pct_rank = float((finite <= peak).sum()) / len(finite)
        # Normalise by remaining tail above threshold
        tail = 1.0 - thr_pct
        if tail <= 0:
            return 0.0
        return float(np.clip((pct_rank - thr_pct) / tail, 0.0, 1.0))

    i_hs  = _exceedance(episode.hs_peak,  hs_clim,  thr_hs_pct)
    i_ssh = _exceedance(episode.ssh_peak, ssh_clim, thr_ssh_pct)
    return float(np.clip(0.5 * (i_hs + i_ssh), 0.0, 1.0))


# ── C_i: context coherence ────────────────────────────────────────────────────

def compute_C_season(episode: EpisodeRecord, active_months: list[int]) -> int:
    """C_i^season = 1 if episode start falls within the active storm season.

    Parameters
    ----------
    episode : EpisodeRecord
    active_months : list[int]
        Month numbers (1–12) considered the active season (e.g., [4,5,6,7,8,9,10]).

    Returns
    -------
    int — 0 or 1
    """
    return int(episode.date_start.month in active_months)


def compute_C_multi(
    episode: EpisodeRecord,
    all_episodes_this_pair: list[EpisodeRecord],
    tolerance_days: int = 1,
) -> int:
    """C_i^multi = 1 if another municipality has a concurrent unmatched episode.

    "Concurrent" means the other episode overlaps or is within tolerance_days of
    this episode's dates.

    Parameters
    ----------
    episode : EpisodeRecord
    all_episodes_this_pair : list[EpisodeRecord]
        ALL unmatched episodes at the current threshold pair.
    tolerance_days : int
        Maximum gap (in days) between episode date ranges to count as concurrent.

    Returns
    -------
    int — 0 or 1
    """
    for other in all_episodes_this_pair:
        if other.episode_id == episode.episode_id:
            continue
        if other.municipality == episode.municipality:
            continue
        # Check temporal overlap with tolerance
        gap = max(
            0,
            (other.date_start - episode.date_end).days,
            (episode.date_start - other.date_end).days,
        )
        if gap <= tolerance_days:
            return 1
    return 0


def compute_C_exposure(episode: EpisodeRecord, exposed_municipalities: list[str]) -> int:
    """C_i^exposure = 1 if the episode's municipality is in the exposed set.

    Parameters
    ----------
    episode : EpisodeRecord
    exposed_municipalities : list[str]
        Municipalities with high-exposure designation (northern sector by default).

    Returns
    -------
    int — 0 or 1
    """
    return int(episode.municipality in exposed_municipalities)


def compute_C_i(C_season: int, C_multi: int, C_exposure: int) -> float:
    """C_i = mean of three binary context coherence indicators.

    Returns
    -------
    float in {0.0, 1/3, 2/3, 1.0}
    """
    return float(C_season + C_multi + C_exposure) / 3.0


# ── q_i: composite confidence weight ─────────────────────────────────────────

def compute_q_i(
    E_i: int,
    I_i: float,
    C_i: float,
    alpha_E: float,
    alpha_I: float,
    alpha_C: float,
) -> float:
    """Composite confidence weight for one unmatched episode.

        q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)

    Parameters
    ----------
    E_i : int — 0 or 1
    I_i : float — in [0, 1]
    C_i : float — in [0, 1]
    alpha_E, alpha_I, alpha_C : float — weights (should sum to 1.0)

    Returns
    -------
    float in [0, 1]
    """
    return float(np.clip(alpha_E * E_i + alpha_I * I_i + alpha_C * C_i, 0.0, 1.0))


# ── Full audit table ──────────────────────────────────────────────────────────

def build_episode_audit_table(
    unmatched_episodes: list[EpisodeRecord],
    records_by_muni: dict[str, any],   # municipality → EventRecord (for clim series)
    legacy_df: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    """Build the per-episode audit table with all q_i components.

    For each unmatched episode across all threshold pairs, computes:
        E_i, I_i, C_season, C_multi, C_exposure, C_i, q_i

    Parameters
    ----------
    unmatched_episodes : list[EpisodeRecord]
        All unmatched episodes from all threshold pairs (from scoring.py).
    records_by_muni : dict
        Maps municipality name → representative EventRecord (used to get clim series).
    legacy_df : pd.DataFrame
        Legacy events (from utils.load_legacy_events).
    cfg : dict
        Configuration dictionary (from analysis_config.CFG).

    Returns
    -------
    DataFrame with columns:
        episode_id, thr_hs_pct, thr_ssh_pct, municipality,
        date_start, date_end, hs_peak, ssh_peak, n_days,
        E_i, I_i, C_season, C_multi, C_exposure, C_i, q_i
    """
    alpha_E = cfg["alpha_E"]
    alpha_I = cfg["alpha_I"]
    alpha_C = cfg["alpha_C"]
    active_months = cfg["active_season_months"]
    exposed_munis = cfg["exposed_municipalities"]
    offsets = cfg["match_window_offsets"]

    # Load manual overrides (if available)
    overrides = load_E_i_overrides(cfg.get("audit_database", Path("nonexistent.csv")))

    log.info(
        "Building episode audit table for %d unmatched episodes...",
        len(unmatched_episodes),
    )

    # Index episodes by (thr_hs_pct, thr_ssh_pct) for multi-municipality lookup
    eps_by_pair: dict[tuple, list[EpisodeRecord]] = {}
    for ep in unmatched_episodes:
        key = (ep.thr_hs_pct, ep.thr_ssh_pct)
        eps_by_pair.setdefault(key, []).append(ep)

    rows: list[dict] = []
    for ep in unmatched_episodes:
        pair_key = (ep.thr_hs_pct, ep.thr_ssh_pct)
        pair_eps = eps_by_pair[pair_key]

        # ── E_i ──────────────────────────────────────────────────────────────
        if ep.episode_id in overrides:
            E_i = overrides[ep.episode_id]
        else:
            E_i = compute_E_i_from_database(ep, legacy_df, offsets)

        # ── I_i ──────────────────────────────────────────────────────────────
        rec = records_by_muni.get(ep.municipality)
        if rec is not None:
            from src.tidal_sensitivity.tides import add_tide_to_ssh, get_tide_for_record  # noqa: F401
            # Use the climatological series stored on the EventRecord
            hs_clim  = rec.hs_clim
            ssh_clim = getattr(rec, "_ssh_total_clim", None)
            if ssh_clim is None:
                # Fall back to raw SSH clim (without tide) for intensity ranking
                ssh_clim = rec.ssh_clim
        else:
            hs_clim = ssh_clim = pd.Series(dtype=float)

        I_i = compute_I_i(ep, ep.thr_hs_pct, ep.thr_ssh_pct, hs_clim, ssh_clim)

        # ── C_i ──────────────────────────────────────────────────────────────
        C_season   = compute_C_season(ep, active_months)
        C_multi    = compute_C_multi(ep, pair_eps)
        C_exposure = compute_C_exposure(ep, exposed_munis)
        C_i        = compute_C_i(C_season, C_multi, C_exposure)

        # ── q_i ──────────────────────────────────────────────────────────────
        q_i_raw = alpha_E * E_i + alpha_I * I_i + alpha_C * C_i
        q_i = compute_q_i(E_i, I_i, C_i, alpha_E, alpha_I, alpha_C)

        rows.append({
            "episode_id":   ep.episode_id,
            "thr_hs_pct":   ep.thr_hs_pct,
            "thr_ssh_pct":  ep.thr_ssh_pct,
            "municipality": ep.municipality,
            "date_start":   ep.date_start,
            "date_end":     ep.date_end,
            "hs_peak":      ep.hs_peak,
            "ssh_peak":     ep.ssh_peak,
            "n_days":       ep.n_days,
            "E_i":          E_i,
            "I_i":          round(I_i, 4),
            "C_season":     C_season,
            "C_multi":      C_multi,
            "C_exposure":   C_exposure,
            "C_i":          round(C_i, 4),
            "alpha_E":      alpha_E,
            "alpha_I":      alpha_I,
            "alpha_C":      alpha_C,
            "contrib_E":    round(alpha_E * E_i, 4),
            "contrib_I":    round(alpha_I * I_i, 4),
            "contrib_C":    round(alpha_C * C_i, 4),
            "q_i_raw":      round(q_i_raw, 4),
            "q_i":          round(q_i, 4),
            "penalty_component": round(1.0 - q_i, 4),
        })

    df = pd.DataFrame(rows)
    log.info(
        "Audit table complete: %d rows | median q_i=%.3f | "
        "E_i=1 in %.1f%% of episodes",
        len(df),
        df["q_i"].median() if not df.empty else 0.0,
        100.0 * df["E_i"].mean() if not df.empty else 0.0,
    )
    return df


def attach_ssh_total_to_records(
    records: list,
    ssh_total_cache: dict,
) -> dict[str, any]:
    """Build a municipality → EventRecord mapping and attach SSH_total clim series.

    Used by build_episode_audit_table to look up climatological series for I_i.
    When multiple EventRecords share a municipality, the first is used.

    Parameters
    ----------
    records : list[EventRecord]
    ssh_total_cache : dict mapping (lat, lon) → SSH_total pd.Series

    Returns
    -------
    dict mapping municipality name → EventRecord (with _ssh_total_clim set)
    """
    muni_map: dict[str, any] = {}
    for rec in records:
        if rec.municipality in muni_map:
            continue
        key = (round(float(rec.grid_lat), 6), round(float(rec.grid_lon), 6))
        ssh_total = ssh_total_cache.get(key, pd.Series(dtype=float))
        rec._ssh_total_clim = ssh_total
        muni_map[rec.municipality] = rec
    return muni_map


def build_qi_decomposition(
    audit_df: pd.DataFrame,
    optimal: dict,
) -> pd.DataFrame:
    """Extract q_i decomposition table for the optimal threshold pair.

    Filters the full audit table to the optimal pair and formats it for
    transparent diagnosis of which terms drive each episode's q_i.

    Parameters
    ----------
    audit_df : DataFrame from build_episode_audit_table (with decomposition columns).
    optimal : dict with keys thr_hs_pct, thr_ssh_pct.

    Returns
    -------
    DataFrame with user-friendly columns for the optimal pair only.
    """
    hs_pct = optimal["thr_hs_pct"]
    ssh_pct = optimal["thr_ssh_pct"]
    mask = (audit_df["thr_hs_pct"] == hs_pct) & (audit_df["thr_ssh_pct"] == ssh_pct)
    df = audit_df[mask].copy()

    cols = [
        "episode_id", "municipality", "date_start", "date_end",
        "hs_peak", "ssh_peak", "n_days",
        "E_i", "I_i",
        "C_season", "C_multi", "C_exposure", "C_i",
        "alpha_E", "alpha_I", "alpha_C",
        "contrib_E", "contrib_I", "contrib_C",
        "q_i_raw", "q_i", "penalty_component",
    ]
    # Keep only columns that exist
    cols = [c for c in cols if c in df.columns]
    df = df[cols].sort_values("penalty_component", ascending=False).reset_index(drop=True)

    log.info(
        "q_i decomposition table (optimal pair q%.0f/q%.0f): %d episodes | "
        "mean penalty=%.3f | max penalty=%.3f",
        hs_pct * 100, ssh_pct * 100, len(df),
        df["penalty_component"].mean() if not df.empty else 0.0,
        df["penalty_component"].max() if not df.empty else 0.0,
    )
    return df
