"""Export the daily series and compound events behind the site's time-series panel.

For each grid point frozen by ``src.site.select_timeseries_points`` this writes
one JSON file holding the full daily record (1993-2025) of significant wave
height, tide-free sea level and astronomical tide, the detected compound
events, and the point-level hazard metrics. The site loads one such file on
demand when the reader clicks a marker.

Nothing here re-derives the method. The detection comes from
``compound_events_at_point``; the domain-pooled rescaling references that turn
daily excesses into the integrated severity are read from the published
``compound_summary_mhws.json`` rather than recomputed, so a severity shown on
the site is the same number that entered the hazard index.

Storage
-------
The three daily series are written as whole centimetres (integers, ``null``
where the record is missing), which halves the file against decimal metres and
is well below the precision of any of the underlying products. The still water
level is not stored: the client reconstructs it as ``zos_anomaly + tide``, the
same definition ``still_water_level`` applies.

A monthly overview series is written alongside, for the navigation strip: 396
points instead of 12 053, enough to show seasonality and to pick a window
without putting a 12 000-vertex path in the DOM.

Usage:
    conda run -n osr python -m src.site.export_timeseries_panel_data

Input:
    outputs/site_timeseries_points/selected_points.csv
    data/unified/metocean_brazil_unified_waverys_grid.nc
    outputs/storm_catalog/compound_mhws/compound_summary_mhws.json
    outputs/storm_catalog/compound_mhws/compound_metrics_mhws.csv

Output:
    site/public/data/timeseries/index.json
    site/public/data/timeseries/<point_id>.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from src.compound_detection.detection_mhws import compound_events_at_point
from src.compound_detection.mhws_datum import mhws_at_points, still_water_level

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
SELECTED_POINTS = (
    ROOT / "outputs" / "site_timeseries_points" / "selected_points.csv"
)
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
CATALOG_DIR = ROOT / "outputs" / "storm_catalog" / "compound_mhws"
CATALOG_SUMMARY = CATALOG_DIR / "compound_summary_mhws.json"
CATALOG_METRICS = CATALOG_DIR / "compound_metrics_mhws.csv"
OUTPUT_DIR = ROOT / "site" / "public" / "data" / "timeseries"
OUTPUT_INDEX = OUTPUT_DIR / "index.json"

#: Point-level diagnostics carried into each file for the hover panel. The two
#: index components are flagged separately in ``INDEX_COMPONENTS``.
POINT_METRIC_FIELDS = (
    "compound_count_total",
    "compound_count_annual_mean",
    "mean_overlap_duration",
    "mean_full_criterion_duration",
    "mean_compound_intensity_norm",
    "mean_integrated_severity",
    "n_candidate_events",
    "n_rejected_by_mhws",
)
INDEX_COMPONENTS = ("compound_count_total", "mean_integrated_severity")


def _cm(values: np.ndarray) -> list[int | None]:
    """Whole centimetres, with ``None`` where the record is missing."""
    finite = np.isfinite(values)
    rounded = np.where(finite, np.round(values * 100.0), 0).astype(int)
    return [int(v) if ok else None for v, ok in zip(rounded, finite)]


def _norm(values: np.ndarray, low: float, high: float) -> np.ndarray:
    """The rescaling used by the detector, with the published references."""
    if high <= low:
        return np.zeros_like(np.asarray(values, dtype=float))
    return np.clip(
        (np.asarray(values, dtype=float) - low) / (high - low), 0.0, 1.0
    )


def _monthly_overview(
    times: pd.DatetimeIndex,
    hs: np.ndarray,
    swl: np.ndarray,
    full_days: np.ndarray,
) -> dict[str, list]:
    """Monthly aggregate for the navigation strip.

    The level is aggregated by its monthly maximum rather than its mean: the
    panel is about extremes, and a mean of the still water level would flatten
    the spring-neap signal the strip is meant to advertise.
    """
    frame = pd.DataFrame(
        {"hs": hs, "swl": swl, "event_day": full_days.astype(float)},
        index=times,
    )
    grouped = frame.resample("MS")
    hs_mean = grouped["hs"].mean()
    swl_max = grouped["swl"].max()
    event_days = grouped["event_day"].sum()
    return {
        "month_start": [d.strftime("%Y-%m") for d in hs_mean.index],
        "hs_mean_cm": _cm(hs_mean.to_numpy(dtype=float)),
        "swl_max_cm": _cm(swl_max.to_numpy(dtype=float)),
        "event_days": [int(v) for v in event_days.to_numpy()],
    }


def export_point(
    row: pd.Series,
    *,
    ds: xr.Dataset,
    times: pd.DatetimeIndex,
    mhws: float,
    refs: dict[str, float],
    metrics: pd.DataFrame,
) -> dict[str, Any]:
    """Build the JSON payload of one grid point."""
    lat_index = int(np.abs(ds["latitude"].values - row["grid_lat"]).argmin())
    lon_index = int(np.abs(ds["longitude"].values - row["grid_lon"]).argmin())
    selector = {"latitude": lat_index, "longitude": lon_index}
    hs = ds["VHM0"].isel(**selector).values.astype(float)
    zos = ds["zos"].isel(**selector).values.astype(float)
    tide = ds["tide_daily_max"].isel(**selector).values.astype(float)
    finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)

    events, context = compound_events_at_point(
        hs=hs, zos=zos, tide=tide, finite=finite, mhws=mhws
    )
    zos_anomaly = zos - context["zos_mean"]
    swl = still_water_level(zos, tide, zos_mean=context["zos_mean"])

    published = metrics[
        (metrics["grid_lat"].round(4) == round(float(row["grid_lat"]), 4))
        & (metrics["grid_lon"].round(4) == round(float(row["grid_lon"]), 4))
    ]
    if len(published) != 1:
        raise ValueError(
            f"{row['point_id']}: {len(published)} rows in the published metrics "
            "match this point; expected exactly one"
        )
    published_row = published.iloc[0]
    if int(published_row["compound_count_total"]) != len(events):
        raise ValueError(
            f"{row['point_id']}: re-detection found {len(events)} events but the "
            f"published catalogue records {int(published_row['compound_count_total'])}"
        )

    full_days = np.zeros(len(times), dtype=bool)
    exported_events: list[dict[str, Any]] = []
    for event in events:
        full_idx = np.asarray(event["full_criterion_indices"], dtype=int)
        full_days[full_idx] = True
        peak_intensity = 0.5 * (
            _norm(
                np.array([event["exc_wave"]]),
                refs["peak_wave_low"],
                refs["peak_wave_high"],
            )[0]
            + _norm(
                np.array([event["exc_level"]]),
                refs["peak_level_low"],
                refs["peak_level_high"],
            )[0]
        )
        integrated = float(
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
        exported_events.append(
            {
                "start_index": int(event["start_index"]),
                "end_index": int(event["end_index"]),
                # Days on which all three criteria hold; possibly not contiguous,
                # which is why they travel as an explicit list. These are the days
                # the chart shades.
                "full_indices": [int(i) for i in full_idx],
                "overlap_duration_days": int(event["overlap_duration_days"]),
                "full_criterion_duration_days": int(
                    event["full_criterion_duration_days"]
                ),
                "peak_hs_m": round(float(event["peak_hs"]), 3),
                "max_swl_m": round(float(event["max_swl"]), 4),
                "exc_level_m": round(float(event["exc_level"]), 4),
                "peak_intensity_norm": round(float(peak_intensity), 4),
                "integrated_severity": round(integrated, 4),
            }
        )

    point_metrics = {
        field: (
            None
            if pd.isna(published_row.get(field))
            else float(published_row[field])
        )
        for field in POINT_METRIC_FIELDS
        if field in published_row
    }

    return {
        "point_id": row["point_id"],
        "lat": float(row["grid_lat"]),
        "lon": float(row["grid_lon"]),
        "label": row["nearest_municipality"],
        "state": row["state"],
        "period": {
            "start": times[0].strftime("%Y-%m-%d"),
            "end": times[-1].strftime("%Y-%m-%d"),
            "n_days": int(len(times)),
        },
        "thresholds": {
            "thr_hs_abs_m": round(float(context["thr_hs_abs"]), 3),
            "thr_zos_abs_m": round(float(context["thr_zos_abs"]), 4),
            "thr_zos_anomaly_m": round(
                float(context["thr_zos_abs"] - context["zos_mean"]), 4
            ),
            "zos_mean_m": round(float(context["zos_mean"]), 4),
            "mhws_m": round(float(context["mhws_m"]), 4),
        },
        "point_metrics": point_metrics,
        "index_components": list(INDEX_COMPONENTS),
        "selection_features": {
            "surge_q99_over_swing": round(float(row["surge_q99_over_swing"]), 4),
            "mhws_m": round(float(row["mhws_m"]), 4),
            "thr_hs_abs": round(float(row["thr_hs_abs"]), 4),
            "Hazard_Frequency": round(float(row["Hazard_Frequency"]), 4),
            "Hazard_Severity": round(float(row["Hazard_Severity"]), 4),
        },
        "daily": {
            "units": "cm",
            "note": "swl = zos_anomaly + tide, referenced to local mean sea level",
            "hs_cm": _cm(hs),
            "zos_anomaly_cm": _cm(zos_anomaly),
            "tide_cm": _cm(tide),
        },
        "monthly": _monthly_overview(times, hs, swl, full_days),
        "events": exported_events,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (SELECTED_POINTS, UNIFIED, CATALOG_SUMMARY, CATALOG_METRICS):
        if not path.exists():
            raise FileNotFoundError(path)

    selected = pd.read_csv(SELECTED_POINTS)
    summary = json.loads(CATALOG_SUMMARY.read_text())
    refs = summary["rescaling_reference_percentiles"]
    metrics = pd.read_csv(CATALOG_METRICS)

    ds = xr.open_dataset(UNIFIED)
    times = pd.to_datetime(ds["time"].values)
    mhws = mhws_at_points(
        selected["grid_lat"].values, selected["grid_lon"].values
    )
    if not np.all(np.isfinite(mhws)):
        raise ValueError("A selected point has no MHWS datum")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index_entries = []
    for position, (_, row) in enumerate(selected.iterrows()):
        payload = export_point(
            row,
            ds=ds,
            times=times,
            mhws=float(mhws[position]),
            refs=refs,
            metrics=metrics,
        )
        destination = OUTPUT_DIR / f"{row['point_id']}.json"
        destination.write_text(json.dumps(payload, separators=(",", ":")))
        size_kb = destination.stat().st_size / 1024
        log.info(
            "%s  %s/%s  %d events  %.0f KB",
            row["point_id"],
            payload["label"],
            payload["state"],
            len(payload["events"]),
            size_kb,
        )
        index_entries.append(
            {
                "point_id": row["point_id"],
                "lat": payload["lat"],
                "lon": payload["lon"],
                "label": payload["label"],
                "state": payload["state"],
                "latitude_band": row["latitude_band"],
                "file": f"{row['point_id']}.json",
                "file_size_kb": round(size_kb, 1),
                "n_municipalities_served": int(row["n_municipalities"]),
                "n_events": len(payload["events"]),
                "selection_features": payload["selection_features"],
                "thresholds": payload["thresholds"],
                "point_metrics": payload["point_metrics"],
            }
        )

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "implementation": "src/site/export_timeseries_panel_data.py",
        "source_dataset": str(UNIFIED.relative_to(ROOT)),
        "detection": summary["method"],
        "definition": summary["definition"],
        "period": summary["period"],
        "selection": {
            "frozen_at": str(SELECTED_POINTS.relative_to(ROOT)),
            "implementation": "src/site/select_timeseries_points.py",
            "rule": (
                "Medoids of equal-count strata of the surge-to-tide ratio in a "
                "z-scored physical feature space, over the grid points that "
                "serve at least one municipality. Municipality names are labels "
                "attached after selection."
            ),
        },
        "index_components": {
            "compound_count_total": "Hazard_Frequency",
            "mean_integrated_severity": "Hazard_Severity",
        },
        "retired_from_index": {
            "fields": ["mean_overlap_duration", "mean_compound_intensity_norm"],
            "retired_on": "2026-07-29",
            "note": (
                "Published as diagnostics only; removed from the hazard index by "
                "AUD-06."
            ),
        },
        "points": index_entries,
    }
    OUTPUT_INDEX.write_text(json.dumps(index, indent=2) + "\n")
    total_mb = sum(
        (OUTPUT_DIR / entry["file"]).stat().st_size for entry in index_entries
    ) / 1024 / 1024
    log.info("Saved: %s", OUTPUT_INDEX)
    log.info("Total point payload: %.2f MB", total_mb)


if __name__ == "__main__":
    main()
