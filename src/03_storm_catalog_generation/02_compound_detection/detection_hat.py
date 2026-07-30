"""Build the HAT-conditioned compound-event arm for the AUD-01 comparison.

The detector, calibration, episode grouping, and severity equations are the
published MHWS implementation.  The only methodological change is the level
datum: ``HAT = max(tide_daily_max)`` over 1993--2025 is passed to
``compound_events_at_point`` as both gate and level-excess datum.

The calculation has two explicit phases.  Phase 1 detects events independently
at each of the 808 points.  A barrier then pools daily excesses in stable point
order and calculates arm-specific Q05/Q95 references.  Phase 2 scores events
with those global references and aggregates point metrics.  Both phases use
``ProcessPoolExecutor``; no third-party parallel dependency is required.

Before production, the first 30 points are evaluated serially and in parallel
and their event payloads and point metrics must be bit-for-bit identical.

Usage:
    conda run -n osr11 python -m src.compound_detection.detection_hat --workers 100

Output:
    outputs/hat_method/compound_metrics_hat.csv
    outputs/hat_method/compound_summary_hat.json
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

from .detection_mhws import (
    INTENSITY_REF_HIGH_PCT,
    INTENSITY_REF_LOW_PCT,
    MIN_FINITE_DAYS,
    POINT_SOURCE,
    THRESHOLD_PCT,
    UNIFIED,
    _point_metrics,
    compound_events_at_point,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "hat_method"
MHWS_METRICS = (
    ROOT
    / "outputs"
    / "storm_catalog"
    / "compound_mhws"
    / "compound_metrics_mhws.csv"
)

EXPECTED = {
    "domain_events": 37_225,
    "events_north_of_15S": 545,
    "events_south_of_25S": 24_196,
    "zero_event_points": 248,
    "grid_points": 808,
}


def _detect_task(
    task: tuple[int, float, float, np.ndarray, np.ndarray, np.ndarray, float]
) -> tuple[int, dict[str, Any], list[dict[str, Any]]]:
    """Phase-1 worker: detect one point and retain its raw excess arrays."""
    index, latitude, longitude, hs, zos, tide, n_years = task
    finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
    record: dict[str, Any] = {
        "grid_lat": latitude,
        "grid_lon": longitude,
    }
    if finite.sum() < MIN_FINITE_DAYS:
        return index, {
            **record,
            "compound_count_total": None,
            "skip_reason": "insufficient_data",
        }, []

    hat = float(np.nanmax(tide[finite]))
    events, context = compound_events_at_point(
        hs=hs,
        zos=zos,
        tide=tide,
        finite=finite,
        mhws=hat,
    )
    # Rename the datum field without changing the reused detector.
    context["hat_m"] = context.pop("mhws_m")
    context["n_rejected_by_hat"] = context.pop("n_rejected_by_mhws")
    return index, {
        **record,
        **context,
        **_point_metrics(events, n_years),
    }, events


def _norm(values: Any, low: float, high: float) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if high <= low:
        return np.zeros_like(values)
    return np.clip((values - low) / (high - low), 0.0, 1.0)


def _score_task(
    task: tuple[int, list[dict[str, Any]], dict[str, float]]
) -> tuple[int, dict[str, Any]]:
    """Phase-2 worker: score one point with the domain-pooled HAT references."""
    index, events, refs = task
    if not events:
        return index, {
            "mean_compound_intensity_norm": None,
            "p95_compound_intensity_norm": None,
            "max_compound_intensity_norm": None,
            # Explicit zero is the scientific choice for no accepted event:
            # absence of an event means absence of event-derived severity.
            "mean_integrated_severity": 0.0,
            "p95_integrated_severity": 0.0,
            "max_integrated_severity": 0.0,
        }

    peak = 0.5 * (
        _norm(
            [event["exc_wave"] for event in events],
            refs["peak_wave_low"],
            refs["peak_wave_high"],
        )
        + _norm(
            [event["exc_level"] for event in events],
            refs["peak_level_low"],
            refs["peak_level_high"],
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
                            refs["daily_wave_low"],
                            refs["daily_wave_high"],
                        )
                        + _norm(
                            event["daily_exc_level"],
                            refs["daily_level_low"],
                            refs["daily_level_high"],
                        )
                    )
                )
            )
            for event in events
        ]
    )
    return index, {
        "mean_compound_intensity_norm": round(float(np.mean(peak)), 4),
        "p95_compound_intensity_norm": round(float(np.percentile(peak, 95)), 4),
        "max_compound_intensity_norm": round(float(np.max(peak)), 4),
        "mean_integrated_severity": round(float(np.mean(integrated)), 4),
        "p95_integrated_severity": round(float(np.percentile(integrated, 95)), 4),
        "max_integrated_severity": round(float(np.max(integrated)), 4),
    }


def _parallel_map(function: Any, tasks: list[Any], workers: int) -> list[Any]:
    with ProcessPoolExecutor(max_workers=workers) as executor:
        # executor.map preserves input order, unlike as_completed.
        return list(executor.map(function, tasks))


def _references(per_point_events: list[list[dict[str, Any]]]) -> dict[str, float]:
    """Calculate HAT-only references in deterministic point/event/day order."""
    events = [
        event
        for point_events in per_point_events
        for event in point_events
    ]
    if not events:
        raise RuntimeError("No HAT events detected anywhere; refusing to write")
    daily_wave = np.concatenate(
        [event["daily_exc_wave"] for event in events if event["daily_exc_wave"].size]
    )
    daily_level = np.concatenate(
        [event["daily_exc_level"] for event in events if event["daily_exc_level"].size]
    )
    return {
        "peak_wave_low": float(
            np.percentile(
                [event["exc_wave"] for event in events],
                INTENSITY_REF_LOW_PCT,
            )
        ),
        "peak_wave_high": float(
            np.percentile(
                [event["exc_wave"] for event in events],
                INTENSITY_REF_HIGH_PCT,
            )
        ),
        "peak_level_low": float(
            np.percentile(
                [event["exc_level"] for event in events],
                INTENSITY_REF_LOW_PCT,
            )
        ),
        "peak_level_high": float(
            np.percentile(
                [event["exc_level"] for event in events],
                INTENSITY_REF_HIGH_PCT,
            )
        ),
        "daily_wave_low": float(
            np.percentile(daily_wave, INTENSITY_REF_LOW_PCT)
        ),
        "daily_wave_high": float(
            np.percentile(daily_wave, INTENSITY_REF_HIGH_PCT)
        ),
        "daily_level_low": float(
            np.percentile(daily_level, INTENSITY_REF_LOW_PCT)
        ),
        "daily_level_high": float(
            np.percentile(daily_level, INTENSITY_REF_HIGH_PCT)
        ),
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
    parallel_scores = _parallel_map(
        _score_task, score_tasks, min(workers, n_points)
    )
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


def _acceptance(metrics: pd.DataFrame) -> dict[str, int]:
    counts = metrics["compound_count_total"].fillna(0)
    observed = {
        "domain_events": int(counts.sum()),
        "events_north_of_15S": int(
            metrics.loc[metrics["grid_lat"] > -15.0, "compound_count_total"]
            .fillna(0)
            .sum()
        ),
        "events_south_of_25S": int(
            metrics.loc[metrics["grid_lat"] < -25.0, "compound_count_total"]
            .fillna(0)
            .sum()
        ),
        "zero_event_points": int((counts == 0).sum()),
        "grid_points": int(len(metrics)),
    }
    if observed != EXPECTED:
        raise AssertionError(
            f"HAT acceptance totals differ: observed={observed}, expected={EXPECTED}"
        )
    return observed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=100)
    parser.add_argument("--validate-points", type=int, default=30)
    args = parser.parse_args()
    if args.workers < 1 or args.validate_points < 1:
        parser.error("workers and validate-points must be positive")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (UNIFIED, POINT_SOURCE, MHWS_METRICS):
        if not path.exists():
            raise FileNotFoundError(path)

    catalogue = json.loads(POINT_SOURCE.read_text())
    points = pd.DataFrame(
        [
            {"grid_lat": point["grid_lat"], "grid_lon": point["grid_lon"]}
            for point in catalogue
        ]
    )
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
    tide_all = ds["tide_daily_max"].isel(
        latitude=lat_idx, longitude=lon_idx
    ).values
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
        )
        for index in range(len(points))
    ]
    validation = _assert_serial_parallel(
        tasks, args.workers, min(args.validate_points, len(tasks))
    )
    log.info("Serial/parallel validation passed on %d points", validation["n_points"])

    phase_1 = _parallel_map(_detect_task, tasks, args.workers)
    phase_1.sort(key=lambda item: item[0])
    rows = [item[1] for item in phase_1]
    events = [item[2] for item in phase_1]

    refs = _references(events)
    score_tasks = [
        (index, point_events, refs)
        for index, point_events in enumerate(events)
    ]
    phase_2 = _parallel_map(_score_task, score_tasks, args.workers)
    phase_2.sort(key=lambda item: item[0])
    for row, (_, scores) in zip(rows, phase_2):
        row.update(scores)

    metrics = pd.DataFrame(rows)
    acceptance = _acceptance(metrics)

    mhws = pd.read_csv(MHWS_METRICS)
    fidelity = metrics[["grid_lat", "grid_lon", "thr_hs_abs"]].merge(
        mhws[["grid_lat", "grid_lon", "thr_hs_abs"]],
        on=["grid_lat", "grid_lon"],
        suffixes=("_hat", "_mhws"),
        validate="one_to_one",
    )
    difference = (
        fidelity["thr_hs_abs_hat"] - fidelity["thr_hs_abs_mhws"]
    ).abs()
    if len(fidelity) != EXPECTED["grid_points"] or not (difference == 0).all():
        raise AssertionError(
            "thr_hs fidelity failed: "
            f"{int((difference == 0).sum())}/{len(fidelity)} exact; "
            f"max difference={difference.max()}"
        )

    summary = {
        "generated_by": "src.compound_detection.detection_hat",
        "method": "HAT-conditioned comparison arm; not adopted",
        "definition": {
            "hat": "max(tide_daily_max) over 1993-2025 at each point",
            "gate": "max(SWL) over shared days > HAT",
            "level_excess": "SWL - HAT",
            "unchanged_detector": "compound_events_at_point from detection_mhws.py",
            "zero_event_policy": (
                "compound_count_total=0 and mean_integrated_severity=0; "
                "absence of accepted events is absence of event-derived hazard"
            ),
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
        "rescaling_reference_percentiles": refs,
        "acceptance_test": acceptance,
        "thr_hs_fidelity": {
            "reference": str(MHWS_METRICS.relative_to(ROOT)),
            "exact_points": int((difference == 0).sum()),
            "total_points": int(len(fidelity)),
            "maximum_absolute_difference_m": float(difference.max()),
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(OUTPUT_DIR / "compound_metrics_hat.csv", index=False)
    (OUTPUT_DIR / "compound_summary_hat.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    log.info("Acceptance test passed: %s", acceptance)
    log.info("Saved versioned HAT snapshot: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
