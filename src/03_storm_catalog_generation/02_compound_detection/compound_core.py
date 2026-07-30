"""Compound-event detector with the threshold percentiles as parameters.

``detection_mhws.compound_events_at_point`` hard-codes the q90/q90 pair that
Step 2e selected when it was calibrated on ``SSH_total``. The 2026-07-30
recalibration scores the production detector directly and may select a
different pair, so the detector has to accept the pair as an argument.

This module is that parameterised detector, and nothing else. It is a literal
transcription of ``detection_mhws.compound_events_at_point`` with two changes:

* the two percentiles are arguments instead of a module constant;
* the datum argument is named ``datum`` rather than ``mhws``, because it is now
  HAT — the gate and the level-excess reference are the same level, which is
  the conclusion AUD-01 §14 (2026-07-30) reached.

``detection_mhws.py`` is deliberately left untouched: it is the frozen
implementation of the superseded method, archived under
``outputs/legacy_mhws_method/``. Equality between the two implementations is
not assumed — :func:`assert_matches_reference_detector` checks it point by
point at q90/q90 with the MHWS datum, and the production entry point runs that
check before writing anything.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .detection_mhws import cluster_episode_indices, _DisjointSet
from .mhws_datum import still_water_level

#: Percentile pair of the superseded calibration, used only by the fidelity
#: check against the frozen MHWS implementation.
REFERENCE_PCT = 0.90


def compound_events_at_point(
    *,
    hs: np.ndarray,
    zos: np.ndarray,
    tide: np.ndarray,
    finite: np.ndarray,
    datum: float,
    hs_pct: float,
    zos_pct: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Detect compound events at one grid point.

    Parameters
    ----------
    hs, zos, tide : np.ndarray
        Daily maximum Hs, tide-free sea level, and daily maximum astronomical
        tide over the full record at one grid point.
    finite : np.ndarray
        Boolean mask of days on which all three fields are available.
    datum : float
        The level datum. It is BOTH the gate (an event is accepted only when
        ``max(SWL)`` over the overlap days exceeds it) and the reference of the
        level excess. Gate and datum must be the same level: the excess only
        has an interpretation as a distance from the condition that defines the
        event.
    hs_pct, zos_pct : float
        Local percentiles for the wave and level detection thresholds.

    Returns
    -------
    (events, context)
        ``events`` carries the day indices and the raw daily excesses, so that
        severity can be rescaled later against domain-pooled references without
        re-running the grouping. ``context`` carries the point-level quantities
        that describe the detection, including how many candidate events the
        gate rejected.
    """
    thr_hs = float(np.nanquantile(hs[finite], hs_pct))
    thr_zos = float(np.nanquantile(zos[finite], zos_pct))
    zos_mean = float(np.nanmean(zos[finite]))
    swl = still_water_level(zos, tide, zos_mean=zos_mean)

    hs_exceeds = np.where(finite, hs >= thr_hs, False)
    zos_exceeds = np.where(finite, zos >= thr_zos, False)

    hs_episodes = cluster_episode_indices(np.flatnonzero(hs_exceeds))
    zos_episodes = cluster_episode_indices(np.flatnonzero(zos_exceeds))

    context = {
        "thr_hs_pct": hs_pct,
        "thr_zos_pct": zos_pct,
        "thr_hs_abs": round(thr_hs, 6),
        "thr_zos_abs": round(thr_zos, 6),
        "zos_mean": round(zos_mean, 6),
        "hat_m": round(float(datum), 6),
        "n_hs_episodes": len(hs_episodes),
        "n_zos_episodes": len(zos_episodes),
    }
    if not hs_episodes or not zos_episodes:
        context.update({"n_candidate_events": 0, "n_rejected_by_hat": 0})
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
        if not np.isfinite(max_swl) or max_swl <= datum:
            rejected += 1
            continue

        peak_hs = float(np.nanmax(hs[np.asarray(sorted(hs_days), dtype=int)]))
        # Days on which ALL THREE criteria hold at once. The event is defined by
        # the joint occurrence of the two drivers plus the level condition, so
        # any duration or time integral must be taken over the days where all
        # three are satisfied.
        full_idx = overlap_idx[swl[overlap_idx] > datum]
        events.append(
            {
                "start_index": int(overlap[0]),
                "end_index": int(overlap[-1]),
                "overlap_duration_days": len(overlap),
                "full_criterion_duration_days": int(full_idx.size),
                "overlap_indices": overlap_idx,
                "full_criterion_indices": full_idx,
                "daily_exc_wave": hs[full_idx] - thr_hs,
                "daily_exc_level": swl[full_idx] - datum,
                "peak_hs": peak_hs,
                "max_swl": max_swl,
                "exc_wave": peak_hs - thr_hs,
                "exc_level": max_swl - datum,
            }
        )

    context.update(
        {
            "n_candidate_events": len(events) + rejected,
            "n_rejected_by_hat": rejected,
        }
    )
    return events, context


def assert_matches_reference_detector(
    *,
    hs: np.ndarray,
    zos: np.ndarray,
    tide: np.ndarray,
    finite: np.ndarray,
    datum: float,
) -> None:
    """Assert exact equality with the frozen MHWS detector at q90/q90.

    Guards against this transcription drifting from
    ``detection_mhws.compound_events_at_point``. Compares every event payload
    field exactly, including array dtype and shape, so a silent numerical
    change cannot pass.
    """
    from .detection_mhws import compound_events_at_point as reference

    reference_events, reference_context = reference(
        hs=hs, zos=zos, tide=tide, finite=finite, mhws=datum
    )
    events, context = compound_events_at_point(
        hs=hs, zos=zos, tide=tide, finite=finite, datum=datum,
        hs_pct=REFERENCE_PCT, zos_pct=REFERENCE_PCT,
    )

    if len(events) != len(reference_events):
        raise AssertionError(
            f"Event count differs from the reference detector: "
            f"{len(events)} != {len(reference_events)}"
        )
    for index, (left, right) in enumerate(zip(events, reference_events)):
        if left.keys() != right.keys():
            raise AssertionError(f"Event {index}: field names differ")
        for key in left:
            a, b = left[key], right[key]
            if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
                if not (
                    isinstance(a, np.ndarray)
                    and isinstance(b, np.ndarray)
                    and a.dtype == b.dtype
                    and a.shape == b.shape
                    and np.array_equal(a, b, equal_nan=True)
                ):
                    raise AssertionError(f"Event {index}: array {key!r} differs")
            elif a != b:
                raise AssertionError(
                    f"Event {index}: {key!r} differs: {a!r} != {b!r}"
                )

    shared = {
        "thr_hs_abs", "thr_zos_abs", "zos_mean",
        "n_hs_episodes", "n_zos_episodes", "n_candidate_events",
    }
    for key in shared:
        if context[key] != reference_context[key]:
            raise AssertionError(
                f"Context {key!r} differs: "
                f"{context[key]!r} != {reference_context[key]!r}"
            )
    if context["n_rejected_by_hat"] != reference_context["n_rejected_by_mhws"]:
        raise AssertionError("Rejection count differs from the reference detector")
    if context["hat_m"] != reference_context["mhws_m"]:
        raise AssertionError("Datum differs from the reference detector")


__all__ = [
    "compound_events_at_point",
    "assert_matches_reference_detector",
    "REFERENCE_PCT",
]
