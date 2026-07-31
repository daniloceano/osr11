"""Compound event detection with the HAT as gate and as severity datum.

Supersedes the MHWS detector implemented in :mod:`detection_mhws`, whose
products are archived under ``outputs/legacy_mhws_method/``. The previous
method is left untouched and remains reproducible.

What changed and why
--------------------
The MHWS gate ``max(SWL) > MHWS`` turned out to be weakly informative along the
whole coast: the astronomical tide alone would already cross it in 73.0 % of
the events north of 15 S and 79.6 % of those south of 25 S. Worse, the physical
content of the severity varied with latitude — 56 % of the level excess at
Amapá is astronomical against 26 % in Rio Grande do Sul — so one value of the
index meant astronomy in the north and storm surge in the south. See
``outputs/audit/AUD-01_hat_gate_sensitivity/`` and AUD-01 §14.

Replacing the datum with HAT removes the astronomical contribution from the
magnitude, because ``tide <= HAT`` by definition makes the astronomical term of
the excess always non-positive, leaving the severity as surge net of the tidal
deficit.

Gate and datum are the same level, deliberately. A HAT gate with an MHWS excess
was shown to be indefensible: the inherited constant ``HAT - MHWS`` accounts for
94-99 % of the excess in the north, which would turn severity into a number
fixed by the local harmonic structure alone.

Definition implemented here
---------------------------
::

    thr_hs   = local q_hs of Hs                   from Step 2e
    thr_zos  = local q_zos of zos                 from Step 2e, tide-free

    wave episode  = Hs  >= thr_hs  , clustered with gap <= 1 day
    level episode = zos >= thr_zos , clustered with gap <= 1 day

    HAT    = max(tide_daily_max) over 1993-2025, per grid point
    SWL(d) = (zos(d) - mean(zos)) + tide_daily_max(d)

    compound event = wave episode and level episode sharing >= 1 exceedance day
                     AND max(SWL) over the shared days > HAT

    exc_wave  = peak_Hs  - thr_hs
    exc_level = max(SWL) - HAT
    integrated severity = sum over full-criterion days of
                          0.5 * [norm(Hs_d - thr_hs) + norm(SWL_d - HAT)]

``norm`` rescales by the 5th/95th percentiles of each excess pooled over the
whole domain. Those references are recomputed WITHIN this arm: reusing the MHWS
references would normalise two different event populations on one scale.

Threshold pair
--------------
Read from the Step 2e table, which since 2026-07-30 scores this very detector
rather than one built on ``SSH_total``. Pass ``--hs-pct/--zos-pct`` to override,
and ``--acceptance-arm`` to reproduce the published q90/q90 comparison arm.

Parallelism
-----------
Two explicit phases with a barrier. Phase 1 detects events independently at
each of the 808 points. The barrier then pools daily excesses in a fixed
point-event-day order and computes this arm's own Q05/Q95. Phase 2 scores
events against those global references. Both phases use ``ProcessPoolExecutor``
from the standard library; no parallel dependency is added. Before production
the first N points are evaluated serially and in parallel and their payloads
must be bit-for-bit identical.

Usage:
    conda run -n osr11 python -m src.compound_detection.detection_hat --workers 100

Output:
    outputs/storm_catalog/compound_hat/compound_metrics_hat.csv
    outputs/storm_catalog/compound_hat/compound_summary_hat.json
    outputs/current_method_hat/                (versioned copy of both)
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from .compound_core import (
    assert_matches_reference_detector,
    compound_events_at_point,
)
from .detection_mhws import (
    INTENSITY_REF_HIGH_PCT,
    INTENSITY_REF_LOW_PCT,
    MIN_FINITE_DAYS,
    UNIFIED,
    _point_metrics,
)
from .mhws_datum import mhws_at_points, still_water_level

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "compound_hat"
#: Versioned copy, because OUTPUT_DIR is inside the .gitignored
#: ``outputs/storm_catalog/``. The MHWS product was lost from disk exactly this
#: way and had to be regenerated on 2026-07-30.
SNAPSHOT_DIR = ROOT / "outputs" / "current_method_hat"
MHWS_METRICS = (
    ROOT
    / "outputs"
    / "legacy_mhws_method"
    / "hazard"
    / "compound_metrics_mhws.csv"
)
#: Enumerates the 808 coastal grid points, in the canonical Step 3.1 order.
#:
#: ``detection_mhws`` reads them from ``compound/compound_catalog.json``, which
#: was safe only while that file was another method's output. This module now
#: WRITES that file, so reading it back would make the run depend on its own
#: previous output — a stale or truncated catalogue would silently redefine the
#: domain. The Step 3.1 metadata table is the upstream source and cannot do
#: that. Verified 2026-07-31 to hold the same 808 points in the same order as
#: the superseded catalogue.
POINT_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "tables" / "tab_SC3_catalog_metadata.csv"
)
#: Event-level catalogue consumed by Steps 3.3-3.8.
EVENT_CATALOG = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
)
OPTIMAL_PAIR_FILE = (
    ROOT
    / "outputs"
    / "threshold_calibration"
    / "tables"
    / "tab_TC5_optimal_pair_pu.csv"
)

#: Totals the published q90/q90 comparison arm must reproduce. Checked only
#: when the run is made at that pair, since they are properties of it.
ACCEPTANCE_Q90 = {
    "domain_events": 37_225,
    "events_north_of_15S": 545,
    "events_south_of_25S": 24_196,
    "zero_event_points": 248,
    "grid_points": 808,
}
ACCEPTANCE_PCT = 0.90


def load_threshold_pair(source: Path = OPTIMAL_PAIR_FILE) -> tuple[float, float]:
    """Read the Step 2e threshold pair.

    ``tab_TC5_optimal_pair_pu.csv`` is the sole authorised threshold source for
    Step 3, as declared in
    ``src/03_storm_catalog_generation/config/analysis_config.py``.
    """
    if not source.exists():
        raise FileNotFoundError(
            f"Step 2e threshold pair not found: {source}. Run Step 2e first."
        )
    row = pd.read_csv(source).iloc[0]
    return float(row["thr_hs_pct"]), float(row["thr_ssh_pct"])


def _event_descriptors(
    events: list[dict[str, Any]],
    hs: np.ndarray,
    zos: np.ndarray,
    swl: np.ndarray,
) -> list[dict[str, Any]]:
    """Descriptive fields per event, for the event-level catalogue.

    The detector itself returns only what the severity calculation needs. These
    are the human-readable descriptors the downstream submodules consume:
    dates, peaks of each driver, and the wave-to-level lag.

    Window convention, and how it differs from the superseded catalogue
    ---------------------------------------------------------------------
    Peaks and the lag are taken over the **full-criterion window** — the days on
    which the wave threshold, the level threshold and the HAT gate all hold at
    once. The superseded SSH_total catalogue took them over the union of the
    contributing episodes, which could include days when the event was not
    actually in progress. Under a gated definition the event *is* the window
    where all three conditions hold, so that is where its peaks live.

    ``peak_hs`` is the exception: it is the detector's own value, taken over all
    days of the contributing wave episodes, and is passed through unchanged so
    that the catalogue and the severity calculation cannot disagree.

    Indices are returned as integers; the caller converts them to dates, so the
    full time axis never has to be shipped to a worker process.
    """
    descriptors: list[dict[str, Any]] = []
    for event in events:
        window = event["full_criterion_indices"]
        if window.size == 0:
            # Not reachable: an accepted event has at least one day above the
            # gate by construction. Fall back rather than raise, so that a
            # future change to the gate cannot silently lose events here.
            window = event["overlap_indices"]
        hs_window = hs[window]
        swl_window = swl[window]
        index_hs = int(window[int(np.nanargmax(hs_window))])
        index_swl = int(window[int(np.nanargmax(swl_window))])
        descriptors.append(
            {
                "start_index": int(event["start_index"]),
                "end_index": int(event["end_index"]),
                "overlap_duration_days": int(event["overlap_duration_days"]),
                "full_criterion_duration_days": int(
                    event["full_criterion_duration_days"]
                ),
                "peak_hs": round(float(event["peak_hs"]), 4),
                "peak_zos": round(float(np.nanmax(zos[window])), 4),
                "peak_swl": round(float(event["max_swl"]), 4),
                "exc_wave": round(float(event["exc_wave"]), 4),
                "exc_level": round(float(event["exc_level"]), 4),
                "peak_hs_index": index_hs,
                "peak_swl_index": index_swl,
                # Positive => the wave peaks AFTER the level (wave lags surge),
                # the same sign convention as the superseded catalogue.
                "peak_lag_days": index_hs - index_swl,
            }
        )
    return descriptors


def _detect_task(
    task: tuple,
) -> tuple[int, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phase-1 worker: detect one point and retain its raw excess arrays."""
    index, latitude, longitude, hs, zos, tide, n_years, hs_pct, zos_pct = task
    finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
    record: dict[str, Any] = {"grid_lat": latitude, "grid_lon": longitude}
    if finite.sum() < MIN_FINITE_DAYS:
        return index, {
            **record,
            "compound_count_total": None,
            "skip_reason": "insufficient_data",
        }, [], []

    hat = float(np.nanmax(tide[finite]))
    events, context = compound_events_at_point(
        hs=hs, zos=zos, tide=tide, finite=finite, datum=hat,
        hs_pct=hs_pct, zos_pct=zos_pct,
    )
    swl = still_water_level(zos, tide, zos_mean=context["zos_mean"])
    return index, {
        **record,
        **context,
        **_point_metrics(events, n_years),
    }, events, _event_descriptors(events, hs, zos, swl)


def _norm(values: Any, low: float, high: float) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if high <= low:
        return np.zeros_like(values)
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def _score_task(
    task: tuple[int, list[dict[str, Any]], dict[str, float]]
) -> tuple[int, dict[str, Any], list[dict[str, float]]]:
    """Phase-2 worker: score one point with the domain-pooled HAT references.

    Returns the point-level aggregates and, alongside them, the per-event
    severities in the same order as the point's event list, so the event-level
    catalogue carries exactly the numbers the aggregates were built from.
    """
    index, events, refs = task
    if not events:
        return index, {
            "mean_compound_intensity_norm": None,
            "p95_compound_intensity_norm": None,
            "max_compound_intensity_norm": None,
            # Explicit zero is the scientific choice for no accepted event:
            # absence of an event means absence of event-derived severity. It
            # also keeps the normalisation population at the full 808 points.
            "mean_integrated_severity": 0.0,
            "p95_integrated_severity": 0.0,
            "max_integrated_severity": 0.0,
        }, []

    peak = 0.5 * (
        _norm(
            [event["exc_wave"] for event in events],
            refs["peak_wave_low"], refs["peak_wave_high"],
        )
        + _norm(
            [event["exc_level"] for event in events],
            refs["peak_level_low"], refs["peak_level_high"],
        )
    )
    integrated = np.asarray(
        [
            float(
                np.sum(
                    0.5
                    * (
                        _norm(
                            event["daily_exc_wave"],
                            refs["daily_wave_low"], refs["daily_wave_high"],
                        )
                        + _norm(
                            event["daily_exc_level"],
                            refs["daily_level_low"], refs["daily_level_high"],
                        )
                    )
                )
            )
            for event in events
        ]
    )
    per_event = [
        {
            "compound_intensity_norm": round(float(peak_value), 4),
            "integrated_severity": round(float(integrated_value), 4),
        }
        for peak_value, integrated_value in zip(peak, integrated)
    ]
    return index, {
        "mean_compound_intensity_norm": round(float(np.mean(peak)), 4),
        "p95_compound_intensity_norm": round(float(np.percentile(peak, 95)), 4),
        "max_compound_intensity_norm": round(float(np.max(peak)), 4),
        "mean_integrated_severity": round(float(np.mean(integrated)), 4),
        "p95_integrated_severity": round(float(np.percentile(integrated, 95)), 4),
        "max_integrated_severity": round(float(np.max(integrated)), 4),
    }, per_event


def _parallel_map(function: Any, tasks: list[Any], workers: int) -> list[Any]:
    with ProcessPoolExecutor(max_workers=workers) as executor:
        # executor.map preserves input order, unlike as_completed.
        return list(executor.map(function, tasks))


def _references(per_point_events: list[list[dict[str, Any]]]) -> dict[str, float]:
    """Calculate this arm's own references in deterministic point/event/day order."""
    events = [
        event for point_events in per_point_events for event in point_events
    ]
    if not events:
        raise RuntimeError("No HAT events detected anywhere; refusing to write")
    daily_wave = np.concatenate(
        [event["daily_exc_wave"] for event in events if event["daily_exc_wave"].size]
    )
    daily_level = np.concatenate(
        [event["daily_exc_level"] for event in events if event["daily_exc_level"].size]
    )
    peak_wave = [event["exc_wave"] for event in events]
    peak_level = [event["exc_level"] for event in events]
    return {
        "peak_wave_low": float(np.percentile(peak_wave, INTENSITY_REF_LOW_PCT)),
        "peak_wave_high": float(np.percentile(peak_wave, INTENSITY_REF_HIGH_PCT)),
        "peak_level_low": float(np.percentile(peak_level, INTENSITY_REF_LOW_PCT)),
        "peak_level_high": float(np.percentile(peak_level, INTENSITY_REF_HIGH_PCT)),
        "daily_wave_low": float(np.percentile(daily_wave, INTENSITY_REF_LOW_PCT)),
        "daily_wave_high": float(np.percentile(daily_wave, INTENSITY_REF_HIGH_PCT)),
        "daily_level_low": float(np.percentile(daily_level, INTENSITY_REF_LOW_PCT)),
        "daily_level_high": float(np.percentile(daily_level, INTENSITY_REF_HIGH_PCT)),
    }


def _assert_serial_parallel(
    tasks: list[Any], workers: int, n_points: int
) -> dict[str, Any]:
    def assert_exact(left: Any, right: Any, path: str = "root") -> None:
        """Compare numerical payloads exactly, independent of pickle layout."""
        if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
            if not (
                isinstance(left, np.ndarray)
                and isinstance(right, np.ndarray)
                and left.dtype == right.dtype
                and left.shape == right.shape
                and np.array_equal(left, right, equal_nan=True)
            ):
                raise AssertionError(f"Serial/parallel array mismatch at {path}")
            return
        if isinstance(left, dict) and isinstance(right, dict):
            if left.keys() != right.keys():
                raise AssertionError(f"Serial/parallel keys differ at {path}")
            for key in left:
                assert_exact(left[key], right[key], f"{path}.{key}")
            return
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            if len(left) != len(right):
                raise AssertionError(f"Serial/parallel lengths differ at {path}")
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                assert_exact(left_item, right_item, f"{path}[{index}]")
            return
        if (
            isinstance(left, (float, np.floating))
            and isinstance(right, (float, np.floating))
            and np.isnan(left)
            and np.isnan(right)
        ):
            return
        if left != right:
            raise AssertionError(
                f"Serial/parallel values differ at {path}: {left!r} != {right!r}"
            )

    subset = tasks[:n_points]
    serial = [_detect_task(task) for task in subset]
    parallel = _parallel_map(_detect_task, subset, min(workers, n_points))
    assert_exact(serial, parallel, "phase_1")

    refs = _references([item[2] for item in serial])
    score_tasks = [(item[0], item[2], refs) for item in serial]
    serial_scores = [_score_task(task) for task in score_tasks]
    parallel_scores = _parallel_map(_score_task, score_tasks, min(workers, n_points))
    assert_exact(serial_scores, parallel_scores, "phase_2")
    return {
        "n_points": n_points,
        "comparison": (
            "exact scalar equality and NumPy array_equal with identical "
            "dtype/shape (NaNs equal)"
        ),
        "phase_1": "identical",
        "phase_2": "identical",
    }


def _assert_detector_fidelity(
    tasks: list[Any], mhws: np.ndarray, n_points: int
) -> dict[str, Any]:
    """Check the parameterised detector against the frozen MHWS one at q90."""
    checked = 0
    for task in tasks[:n_points]:
        index, _, _, hs, zos, tide, _, _, _ = task
        if not np.isfinite(mhws[index]):
            continue
        finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
        if finite.sum() < MIN_FINITE_DAYS:
            continue
        assert_matches_reference_detector(
            hs=hs, zos=zos, tide=tide, finite=finite, datum=float(mhws[index])
        )
        checked += 1
    return {
        "n_points_checked": checked,
        "reference": "detection_mhws.compound_events_at_point at q90/q90 with the MHWS datum",
        "result": "identical",
    }


def build_event_catalogue(
    rows: list[dict[str, Any]],
    descriptors: list[list[dict[str, Any]]],
    severities: list[list[dict[str, float]]],
    times: pd.DatetimeIndex,
    municipalities: dict[tuple[float, float], str],
) -> list[dict[str, Any]]:
    """Assemble the event-level compound catalogue consumed by Steps 3.3-3.8.

    One entry per grid point, each carrying its detection context and the list
    of accepted events with dates rather than day indices.

    Schema change from the superseded SSH_total catalogue
    ----------------------------------------------------
    ``peak_ssh_total`` and ``thr_ssh_total_abs`` are gone. The level driver is
    now reported as three separate quantities, because under a gated method they
    are three different things and collapsing them is what made the old product
    hard to interpret:

    ``peak_zos``      the tide-free level, which is what the threshold is on;
    ``peak_swl``      the still-water level, which is what the gate is on;
    ``exc_level``     ``peak_swl - HAT``, the severity-bearing excess.

    ``full_criterion_duration_days`` is new: the number of days on which all
    three conditions hold. It is the duration the severity integral runs over,
    and it is always <= ``overlap_duration_days``.
    """
    catalogue: list[dict[str, Any]] = []
    for row, point_descriptors, point_severities in zip(
        rows, descriptors, severities
    ):
        latitude = float(row["grid_lat"])
        longitude = float(row["grid_lon"])

        events: list[dict[str, Any]] = []
        # A point skipped for insufficient data has no severities; zip stops at
        # the shorter sequence, which is the intended behaviour there.
        for descriptor, severity in zip(point_descriptors, point_severities):
            events.append(
                {
                    "date_start": times[descriptor["start_index"]].date().isoformat(),
                    "date_end": times[descriptor["end_index"]].date().isoformat(),
                    "overlap_duration_days": descriptor["overlap_duration_days"],
                    "full_criterion_duration_days": descriptor[
                        "full_criterion_duration_days"
                    ],
                    "peak_hs": descriptor["peak_hs"],
                    "peak_zos": descriptor["peak_zos"],
                    "peak_swl": descriptor["peak_swl"],
                    "exc_wave": descriptor["exc_wave"],
                    "exc_level": descriptor["exc_level"],
                    "peak_hs_date": times[descriptor["peak_hs_index"]]
                    .date()
                    .isoformat(),
                    "peak_swl_date": times[descriptor["peak_swl_index"]]
                    .date()
                    .isoformat(),
                    "peak_lag_days": descriptor["peak_lag_days"],
                    "compound_intensity_norm": severity["compound_intensity_norm"],
                    "integrated_severity": severity["integrated_severity"],
                }
            )

        entry = {
            "grid_lat": latitude,
            "grid_lon": longitude,
            "municipality": municipalities.get((round(latitude, 2), round(longitude, 2))),
        }
        # Detection context and point aggregates, minus the coordinates already
        # written above. Copied wholesale so the catalogue cannot drift from the
        # metrics table: both are views of the same rows.
        entry.update(
            {
                key: value
                for key, value in row.items()
                if key not in ("grid_lat", "grid_lon")
            }
        )
        entry["compound_events"] = events
        catalogue.append(entry)
    return catalogue


def write_event_catalogue(
    catalogue: list[dict[str, Any]], destination: Path
) -> None:
    """Write the event-level catalogue as JSON, converting NumPy scalars."""

    class _Encoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            return super().default(o)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(catalogue, cls=_Encoder))
    size_mb = destination.stat().st_size / 1e6
    total = sum(len(entry["compound_events"]) for entry in catalogue)
    log.info(
        "Wrote %s (%.1f MB, %d grid points, %d events)",
        destination, size_mb, len(catalogue), total,
    )


def _band_counts(metrics: pd.DataFrame) -> dict[str, int]:
    counts = metrics["compound_count_total"].fillna(0)
    return {
        "domain_events": int(counts.sum()),
        "events_north_of_15S": int(
            metrics.loc[metrics["grid_lat"] > -15.0, "compound_count_total"]
            .fillna(0).sum()
        ),
        "events_south_of_25S": int(
            metrics.loc[metrics["grid_lat"] < -25.0, "compound_count_total"]
            .fillna(0).sum()
        ),
        "zero_event_points": int((counts == 0).sum()),
        "grid_points": int(len(metrics)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=100)
    parser.add_argument("--validate-points", type=int, default=30)
    parser.add_argument(
        "--hs-pct", type=float, default=None,
        help="Override the Step 2e wave percentile",
    )
    parser.add_argument(
        "--zos-pct", type=float, default=None,
        help="Override the Step 2e level percentile",
    )
    parser.add_argument(
        "--acceptance-arm", action="store_true",
        help="Run at q90/q90 and assert the published comparison totals",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Write elsewhere than the production catalogue directory",
    )
    parser.add_argument(
        "--no-snapshot", action="store_true",
        help="Skip the versioned copy under outputs/current_method_hat/",
    )
    parser.add_argument(
        "--event-catalog", type=Path, default=None,
        help=(
            "Write the event-level catalogue elsewhere than "
            "outputs/storm_catalog/compound/compound_catalog.json"
        ),
    )
    parser.add_argument(
        "--no-event-catalog", action="store_true",
        help=(
            "Skip the event-level catalogue. Steps 3.3-3.8 read it, so a "
            "production run should not use this."
        ),
    )
    args = parser.parse_args()
    if args.workers < 1 or args.validate_points < 1:
        parser.error("workers and validate-points must be positive")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if args.acceptance_arm:
        hs_pct = zos_pct = ACCEPTANCE_PCT
        pair_source = "acceptance arm (q90/q90, published comparison)"
    elif args.hs_pct is not None and args.zos_pct is not None:
        hs_pct, zos_pct = float(args.hs_pct), float(args.zos_pct)
        pair_source = "command line override"
    elif args.hs_pct is not None or args.zos_pct is not None:
        parser.error("--hs-pct and --zos-pct must be given together")
    else:
        hs_pct, zos_pct = load_threshold_pair()
        pair_source = str(OPTIMAL_PAIR_FILE.relative_to(ROOT))
    log.info(
        "Threshold pair: Hs=q%.0f / zos=q%.0f  (from %s)",
        hs_pct * 100, zos_pct * 100, pair_source,
    )

    output_dir = args.output_dir or OUTPUT_DIR
    for path in (UNIFIED, POINT_SOURCE, MHWS_METRICS):
        if not path.exists():
            raise FileNotFoundError(path)

    point_table = pd.read_csv(POINT_SOURCE)
    points = point_table[["grid_lat", "grid_lon"]].copy()
    municipalities = {
        (round(float(lat), 2), round(float(lon), 2)): (
            None if pd.isna(name) else str(name)
        )
        for lat, lon, name in zip(
            point_table["grid_lat"],
            point_table["grid_lon"],
            point_table.get("municipality", pd.Series([None] * len(point_table))),
        )
    }
    ds = xr.open_dataset(UNIFIED)
    # Reading the last values forces the NetCDF backend to traverse metadata
    # and data; a truncated file fails before the expensive parallel work.
    for field in ("VHM0", "zos", "tide_daily_max"):
        _ = float(ds[field].isel(time=-1).max(skipna=True).load())
    times = pd.to_datetime(ds["time"].values)
    n_years = (times[-1] - times[0]).days / 365.25
    lat_idx = xr.DataArray(
        [
            int(np.abs(ds["latitude"].values - value).argmin())
            for value in points["grid_lat"]
        ],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [
            int(np.abs(ds["longitude"].values - value).argmin())
            for value in points["grid_lon"]
        ],
        dims="point",
    )
    log.info("Extracting series for %d points", len(points))
    hs_all = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos_all = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide_all = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    ds.close()

    tasks = [
        (
            index,
            float(points.iloc[index]["grid_lat"]),
            float(points.iloc[index]["grid_lon"]),
            hs_all[:, index].astype(float),
            zos_all[:, index].astype(float),
            tide_all[:, index].astype(float),
            n_years,
            hs_pct,
            zos_pct,
        )
        for index in range(len(points))
    ]

    n_validate = min(args.validate_points, len(tasks))
    mhws = mhws_at_points(points["grid_lat"].values, points["grid_lon"].values)
    fidelity_detector = _assert_detector_fidelity(tasks, mhws, n_validate)
    log.info(
        "Parameterised detector matches the frozen MHWS detector at q90 on "
        "%d points", fidelity_detector["n_points_checked"],
    )

    validation = _assert_serial_parallel(tasks, args.workers, n_validate)
    log.info("Serial/parallel validation passed on %d points", validation["n_points"])

    phase_1 = _parallel_map(_detect_task, tasks, args.workers)
    phase_1.sort(key=lambda item: item[0])
    rows = [item[1] for item in phase_1]
    events = [item[2] for item in phase_1]
    descriptors = [item[3] for item in phase_1]

    refs = _references(events)
    score_tasks = [
        (index, point_events, refs) for index, point_events in enumerate(events)
    ]
    phase_2 = _parallel_map(_score_task, score_tasks, args.workers)
    phase_2.sort(key=lambda item: item[0])
    per_event_severity = [item[2] for item in phase_2]
    for row, (_, scores, _) in zip(rows, phase_2):
        row.update(scores)

    metrics = pd.DataFrame(rows)
    counts = _band_counts(metrics)
    if args.acceptance_arm and counts != ACCEPTANCE_Q90:
        raise AssertionError(
            f"Acceptance totals differ: observed={counts}, expected={ACCEPTANCE_Q90}"
        )

    # thr_hs fidelity is only expected to reproduce the published product when
    # the wave percentile is unchanged; at any other percentile the threshold
    # is a different quantity by design.
    reference = pd.read_csv(MHWS_METRICS)
    merged = metrics[["grid_lat", "grid_lon", "thr_hs_abs"]].merge(
        reference[["grid_lat", "grid_lon", "thr_hs_abs"]],
        on=["grid_lat", "grid_lon"], suffixes=("_new", "_mhws"),
        validate="one_to_one",
    )
    difference = (merged["thr_hs_abs_new"] - merged["thr_hs_abs_mhws"]).abs()
    thr_hs_fidelity = {
        "reference": str(MHWS_METRICS.relative_to(ROOT)),
        "comparable": bool(hs_pct == ACCEPTANCE_PCT),
        "exact_points": int((difference == 0).sum()),
        "total_points": int(len(merged)),
        "maximum_absolute_difference_m": float(difference.max()),
    }
    if hs_pct == ACCEPTANCE_PCT and not (difference == 0).all():
        raise AssertionError(
            "thr_hs fidelity failed at q90: "
            f"{int((difference == 0).sum())}/{len(merged)} exact; "
            f"max difference={difference.max()}"
        )

    thr_hs = pd.to_numeric(metrics["thr_hs_abs"], errors="coerce").dropna()
    summary = {
        "generated_by": "src.compound_detection.detection_hat",
        "method": "HAT-gated compound detection; HAT is both gate and severity datum",
        "supersedes": "outputs/legacy_mhws_method/ (MHWS detector)",
        "threshold_pair": {
            "thr_hs_pct": hs_pct,
            "thr_zos_pct": zos_pct,
            "source": pair_source,
        },
        "definition": {
            "wave_threshold": f"local q{hs_pct:.2f} of VHM0",
            "level_threshold": f"local q{zos_pct:.2f} of zos (tide-free)",
            "episode_max_gap_days": 1,
            "hat": "max(tide_daily_max) over 1993-2025 at each point",
            "gate": "max(SWL) over the shared days > HAT",
            "swl": "(zos - mean(zos)) + tide_daily_max",
            "level_excess": "SWL - HAT",
            "peak_intensity_diagnostic": (
                "0.5 * [norm(peak_Hs - thr_hs) + norm(max(SWL) - HAT)]"
            ),
            "integrated_severity_index_component": (
                "sum over full-criterion days of 0.5 * [norm(Hs_d - thr_hs) + "
                "norm(SWL_d - HAT)], daily excesses pooled domain-wide"
            ),
            "duration_status": (
                "computed and published as a diagnostic, no longer a hazard "
                "index component (AUD-06)"
            ),
            "zero_event_policy": (
                "compound_count_total=0 and mean_integrated_severity=0; "
                "absence of accepted events is absence of event-derived hazard, "
                "and the normalisation population stays at 808 points"
            ),
            "wave_setup": "not used; waves act as driver and severity term only",
        },
        "period": {
            "start": str(times[0].date()),
            "end": str(times[-1].date()),
            "years": round(n_years, 2),
        },
        "grid_point_count": int(len(metrics)),
        "compound_event_total": counts["domain_events"],
        "candidates_rejected_by_hat_gate": int(
            pd.to_numeric(metrics.get("n_rejected_by_hat"), errors="coerce")
            .fillna(0).sum()
        ),
        "band_counts": counts,
        "thr_hs_distribution_m": {
            "min": round(float(thr_hs.min()), 4),
            "p05": round(float(thr_hs.quantile(0.05)), 4),
            "median": round(float(thr_hs.median()), 4),
            "max": round(float(thr_hs.max()), 4),
            "n_points_below_1m": int((thr_hs < 1.0).sum()),
            "n_points_below_1_5m": int((thr_hs < 1.5).sum()),
        },
        "parallelism": {
            "workers": args.workers,
            "phase_order": [
                "parallel detection",
                "global ordered Q05/Q95 barrier",
                "parallel scoring",
            ],
            "serial_parallel_validation": validation,
        },
        "detector_fidelity": fidelity_detector,
        "rescaling_reference_percentiles": {
            "low_pct": INTENSITY_REF_LOW_PCT,
            "high_pct": INTENSITY_REF_HIGH_PCT,
            **{key: round(value, 6) for key, value in refs.items()},
        },
        "thr_hs_fidelity": thr_hs_fidelity,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(output_dir / "compound_metrics_hat.csv", index=False)
    (output_dir / "compound_summary_hat.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    log.info("Compound events: %d", counts["domain_events"])
    log.info("Points with zero events: %d", counts["zero_event_points"])
    log.info("Wrote %s", output_dir / "compound_metrics_hat.csv")

    if not args.no_event_catalog:
        catalogue = build_event_catalogue(
            rows, descriptors, per_event_severity, times, municipalities,
        )
        catalogue_total = sum(
            len(entry["compound_events"]) for entry in catalogue
        )
        if catalogue_total != counts["domain_events"]:
            raise AssertionError(
                "Event-level catalogue and metrics table disagree on the event "
                f"count: {catalogue_total} != {counts['domain_events']}"
            )
        write_event_catalogue(catalogue, args.event_catalog or EVENT_CATALOG)

    if not args.no_snapshot and output_dir == OUTPUT_DIR:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        metrics.to_csv(SNAPSHOT_DIR / "compound_metrics_hat.csv", index=False)
        (SNAPSHOT_DIR / "compound_summary_hat.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        log.info("Versioned snapshot: %s", SNAPSHOT_DIR)


if __name__ == "__main__":
    main()
