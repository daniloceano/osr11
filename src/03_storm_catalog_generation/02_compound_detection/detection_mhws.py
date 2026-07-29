"""Compound event detection with the tide as a conditioning variable (MHWS method).

Supersedes the ``SSH_total`` detector implemented in :mod:`detection`, whose
products are archived under ``outputs/legacy_ssh_total_method/``. The previous
method is left untouched and remains reproducible.

What changed and why
--------------------
The former detector applied a local q90 threshold to
``SSH_total = zos + tide``. Where the tide is macrotidal it carries 96-98 % of
the variance of that sum, so the q90 became the spring-tide envelope and
exceedances recurred fortnightly *by construction*, with no storm involved.
A Rayleigh test of compound start dates against the 14.765-day spring-neap
period found significant phase locking at 88.5 % of the 808 grid points, and at
100 % of the points north of 20 S. See
``docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md``.

The correction separates the two roles the tide plays. It is a *predictable
oscillation the coast is adapted to*, so it must not decide **whether** an event
occurred; and it is an *amplifier of impact*, so it should decide **how severe**
the event was, and **whether the water actually got high enough to matter**.

    detection   drivers only, tide-free   ->  did a storm occur?
    condition   still water level > MHWS  ->  did water exceed the routine maximum?
    severity    excess over MHWS          ->  how far above it?

Definition implemented here
---------------------------
::

    thr_hs   = q90 local of Hs                    (unchanged)
    thr_zos  = q90 local of zos                   (was SSH_total)

    wave episode  = Hs  >= thr_hs  , clustered with gap <= 1 day
    level episode = zos >= thr_zos , clustered with gap <= 1 day

    MHWS   = A_M2 + A_S2                          (FES2022 harmonic constants)
    SWL(d) = (zos(d) - mean(zos)) + tide_daily_max(d)

    compound event = wave episode and level episode sharing >= 1 exceedance day
                     AND max(SWL) over the shared days > MHWS

    exc_wave  = peak_Hs      - thr_hs
    exc_level = max(SWL)     - MHWS
    intensity = 0.5 * [ norm(exc_wave) + norm(exc_level) ]

``norm`` rescales by the 5th/95th percentiles of each excess pooled over the
whole domain, exactly as in the previous method, so the metric stays comparable
between grid points while the local baseline is removed first.

No wave setup term appears anywhere. Waves act as a driver and as one half of
the intensity; adding ``0.2*Hs`` to the level would partly double-count them,
would turn the level into a total-water-level proxy, and would invite a
critique that a period- and slope-dependent setup formulation should have been
used instead — which the available data (no wave period, no beach slope) cannot
support.

Grouping fidelity
-----------------
Episodes are grouped exactly as in :func:`detection.classify_storms_at_point`:
wave and level episodes connected transitively through shared exceedance days
form a single compound event, and the shared days are the intersection of the
day sets of the two sides. Following :func:`shared.catalog_utils.storm_days`,
an episode contributes only its **exceedance** days; days bridged across a gap
are not part of the set.

Usage:
    python -m src.compound_detection.detection_mhws

Output:
    outputs/storm_catalog/compound_mhws/compound_metrics_mhws.csv
    outputs/storm_catalog/compound_mhws/compound_summary_mhws.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from .mhws_datum import mhws_at_points, still_water_level

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
#: Point list of the production catalogue, so both methods cover the same grid.
POINT_SOURCE = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "compound_mhws"

THRESHOLD_PCT = 0.90
EPISODE_MAX_GAP_DAYS = 1
INTENSITY_REF_LOW_PCT = 5.0
INTENSITY_REF_HIGH_PCT = 95.0
MIN_FINITE_DAYS = 1000


def cluster_episode_indices(
    exceed_idx: np.ndarray, max_gap_days: int = EPISODE_MAX_GAP_DAYS
) -> list[np.ndarray]:
    """Split sorted exceedance indices into episodes.

    Two exceedance days belong to the same episode when at most
    ``max_gap_days`` non-exceedance days separate them, i.e. when their index
    difference is at most ``max_gap_days + 1``. Mirrors
    :func:`segmentation.cluster_episodes`.
    """
    if exceed_idx.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(exceed_idx) > max_gap_days + 1)
    return np.split(exceed_idx, breaks + 1)


class _DisjointSet:
    """Minimal union-find used to group episodes connected by shared days."""

    def __init__(self, size: int) -> None:
        self._parent = list(range(size))

    def find(self, a: int) -> int:
        while self._parent[a] != a:
            self._parent[a] = self._parent[self._parent[a]]
            a = self._parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra


def compound_events_at_point(
    *,
    hs: np.ndarray,
    zos: np.ndarray,
    tide: np.ndarray,
    finite: np.ndarray,
    mhws: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Detect compound events at one grid point under the MHWS method.

    Returns the accepted events and the point-level quantities that describe
    the detection, including how many candidates the MHWS condition rejected.
    """
    thr_hs = float(np.nanquantile(hs[finite], THRESHOLD_PCT))
    thr_zos = float(np.nanquantile(zos[finite], THRESHOLD_PCT))
    zos_mean = float(np.nanmean(zos[finite]))
    swl = still_water_level(zos, tide, zos_mean=zos_mean)

    hs_exceeds = np.where(finite, hs >= thr_hs, False)
    zos_exceeds = np.where(finite, zos >= thr_zos, False)

    hs_episodes = cluster_episode_indices(np.flatnonzero(hs_exceeds))
    zos_episodes = cluster_episode_indices(np.flatnonzero(zos_exceeds))

    context = {
        "thr_hs_abs": round(thr_hs, 6),
        "thr_zos_abs": round(thr_zos, 6),
        "zos_mean": round(zos_mean, 6),
        "mhws_m": round(float(mhws), 6),
        "n_hs_episodes": len(hs_episodes),
        "n_zos_episodes": len(zos_episodes),
    }
    if not hs_episodes or not zos_episodes:
        context.update({"n_candidate_events": 0, "n_rejected_by_mhws": 0})
        return [], context

    # Each exceedance day belongs to exactly one episode of its own variable,
    # so a shared day induces a single edge between one wave and one level
    # episode. Connected components of that graph are the compound groups.
    day_to_hs: dict[int, int] = {}
    for i, days in enumerate(hs_episodes):
        for d in days:
            day_to_hs[int(d)] = i
    day_to_zos: dict[int, int] = {}
    for i, days in enumerate(zos_episodes):
        for d in days:
            day_to_zos[int(d)] = i

    n_hs, n_zos = len(hs_episodes), len(zos_episodes)
    dsu = _DisjointSet(n_hs + n_zos)
    shared_days = sorted(set(day_to_hs) & set(day_to_zos))
    for day in shared_days:
        dsu.union(day_to_hs[day], n_hs + day_to_zos[day])

    groups: dict[int, dict[str, set]] = {}
    for day in shared_days:
        root = dsu.find(day_to_hs[day])
        group = groups.setdefault(root, {"hs": set(), "zos": set()})
        group["hs"].add(day_to_hs[day])
        group["zos"].add(day_to_zos[day])

    events: list[dict[str, Any]] = []
    rejected = 0
    for group in groups.values():
        hs_days: set[int] = set()
        for i in group["hs"]:
            hs_days.update(int(d) for d in hs_episodes[i])
        zos_days: set[int] = set()
        for i in group["zos"]:
            zos_days.update(int(d) for d in zos_episodes[i])

        overlap = sorted(hs_days & zos_days)
        if not overlap:
            continue
        overlap_idx = np.asarray(overlap, dtype=int)

        max_swl = float(np.nanmax(swl[overlap_idx]))
        if not np.isfinite(max_swl) or max_swl <= mhws:
            rejected += 1
            continue

        peak_hs = float(np.nanmax(hs[np.asarray(sorted(hs_days), dtype=int)]))
        events.append(
            {
                "start_index": int(overlap[0]),
                "end_index": int(overlap[-1]),
                "overlap_duration_days": len(overlap),
                "peak_hs": peak_hs,
                "max_swl": max_swl,
                "exc_wave": peak_hs - thr_hs,
                "exc_level": max_swl - mhws,
            }
        )

    context.update(
        {
            "n_candidate_events": len(events) + rejected,
            "n_rejected_by_mhws": rejected,
        }
    )
    return events, context


def _point_metrics(
    events: list[dict[str, Any]], n_years: float
) -> dict[str, Any]:
    if not events:
        return {
            "compound_count_total": 0,
            "compound_count_annual_mean": 0.0,
            "mean_overlap_duration": None,
            "p95_overlap_duration": None,
            "max_overlap_duration": None,
        }
    overlaps = [e["overlap_duration_days"] for e in events]
    return {
        "compound_count_total": len(events),
        "compound_count_annual_mean": round(len(events) / n_years, 2)
        if n_years > 0
        else None,
        "mean_overlap_duration": round(float(np.mean(overlaps)), 2),
        "p95_overlap_duration": round(float(np.percentile(overlaps, 95)), 2),
        "max_overlap_duration": int(np.max(overlaps)),
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (UNIFIED, POINT_SOURCE):
        if not path.exists():
            raise FileNotFoundError(path)

    with POINT_SOURCE.open() as f:
        catalogue = json.load(f)
    points = pd.DataFrame(
        [{"grid_lat": p["grid_lat"], "grid_lon": p["grid_lon"]} for p in catalogue]
    )
    log.info("Grid points: %d", len(points))

    mhws = mhws_at_points(points["grid_lat"].values, points["grid_lon"].values)
    log.info(
        "MHWS: %d of %d points resolved (%.2f-%.2f m)",
        int(np.isfinite(mhws).sum()),
        len(mhws),
        float(np.nanmin(mhws)),
        float(np.nanmax(mhws)),
    )

    ds = xr.open_dataset(UNIFIED)
    times = pd.to_datetime(ds["time"].values)
    n_years = (times[-1] - times[0]).days / 365.25

    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in points["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in points["grid_lon"]],
        dims="point",
    )
    log.info("Extracting series ...")
    hs_all = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos_all = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide_all = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    log.info("Extraction complete.")

    rows: list[dict[str, Any]] = []
    per_point_events: list[list[dict[str, Any]]] = []
    skipped: list[dict[str, Any]] = []

    for i in range(len(points)):
        hs = hs_all[:, i].astype(float)
        zos = zos_all[:, i].astype(float)
        tide = tide_all[:, i].astype(float)
        finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)

        record = {
            "grid_lat": float(points["grid_lat"][i]),
            "grid_lon": float(points["grid_lon"][i]),
        }
        if finite.sum() < MIN_FINITE_DAYS or not np.isfinite(mhws[i]):
            skipped.append(
                {
                    **record,
                    "reason": "insufficient_data"
                    if finite.sum() < MIN_FINITE_DAYS
                    else "no_mhws_datum",
                }
            )
            per_point_events.append([])
            rows.append({**record, "compound_count_total": None})
            continue

        events, context = compound_events_at_point(
            hs=hs, zos=zos, tide=tide, finite=finite, mhws=float(mhws[i])
        )
        per_point_events.append(events)
        rows.append({**record, **context, **_point_metrics(events, n_years)})

    # Domain-pooled rescaling of both excesses, as in the previous method.
    wave_excesses = [e["exc_wave"] for evs in per_point_events for e in evs]
    level_excesses = [e["exc_level"] for evs in per_point_events for e in evs]
    if not wave_excesses:
        raise RuntimeError("No compound events detected anywhere; refusing to write")

    refs = {
        "wave_low": float(np.percentile(wave_excesses, INTENSITY_REF_LOW_PCT)),
        "wave_high": float(np.percentile(wave_excesses, INTENSITY_REF_HIGH_PCT)),
        "level_low": float(np.percentile(level_excesses, INTENSITY_REF_LOW_PCT)),
        "level_high": float(np.percentile(level_excesses, INTENSITY_REF_HIGH_PCT)),
    }

    def _norm(value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.0
        return float(np.clip((value - low) / (high - low), 0.0, 1.0))

    for row, events in zip(rows, per_point_events):
        if not events:
            row.update(
                {
                    "mean_compound_intensity_norm": None,
                    "p95_compound_intensity_norm": None,
                    "max_compound_intensity_norm": None,
                }
            )
            continue
        intensities = [
            0.5
            * (
                _norm(e["exc_wave"], refs["wave_low"], refs["wave_high"])
                + _norm(e["exc_level"], refs["level_low"], refs["level_high"])
            )
            for e in events
        ]
        row.update(
            {
                "mean_compound_intensity_norm": round(float(np.mean(intensities)), 4),
                "p95_compound_intensity_norm": round(
                    float(np.percentile(intensities, 95)), 4
                ),
                "max_compound_intensity_norm": round(float(np.max(intensities)), 4),
            }
        )

    metrics = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_DIR / "compound_metrics_mhws.csv", index=False)

    total_events = int(metrics["compound_count_total"].fillna(0).sum())
    total_rejected = int(metrics.get("n_rejected_by_mhws", pd.Series(dtype=float)).fillna(0).sum())
    summary = {
        "generated_by": "src.storm_catalog_generation.compound_detection.detection_mhws",
        "method": "MHWS-conditioned compound detection (tide as conditioning variable)",
        "supersedes": "outputs/legacy_ssh_total_method/ (SSH_total detector)",
        "definition": {
            "wave_threshold": f"local q{THRESHOLD_PCT:.2f} of VHM0",
            "level_threshold": f"local q{THRESHOLD_PCT:.2f} of zos (tide-free)",
            "episode_max_gap_days": EPISODE_MAX_GAP_DAYS,
            "condition": "max(SWL) over shared days > MHWS",
            "swl": "(zos - mean(zos)) + tide_daily_max",
            "mhws": "A_M2 + A_S2 from FES2022 harmonic constants",
            "intensity": "0.5 * [norm(peak_Hs - thr_hs) + norm(max(SWL) - MHWS)]",
            "wave_setup": "not used; waves act as driver and intensity term only",
        },
        "period": {
            "start": str(times[0].date()),
            "end": str(times[-1].date()),
            "years": round(n_years, 2),
        },
        "grid_point_count": int(len(metrics)),
        "points_skipped": skipped,
        "compound_event_total": total_events,
        "candidates_rejected_by_mhws_condition": total_rejected,
        "intensity_reference_percentiles": {
            "low_pct": INTENSITY_REF_LOW_PCT,
            "high_pct": INTENSITY_REF_HIGH_PCT,
            **{k: round(v, 6) for k, v in refs.items()},
        },
    }
    with (OUTPUT_DIR / "compound_summary_mhws.json").open("w") as f:
        json.dump(summary, f, indent=2)

    log.info("Compound events: %d", total_events)
    log.info("Rejected by MHWS condition: %d", total_rejected)
    log.info("Wrote %s", OUTPUT_DIR / "compound_metrics_mhws.csv")


if __name__ == "__main__":
    main()
