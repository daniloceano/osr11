"""Canonical calculation of the native-grid Hazard Index.

The physical hazard combines two equally weighted components: compound-event
frequency and mean integrated severity. Both use fixed, sample-independent
anchors; their mean is the final 0--1 Hazard Index, without another Min--Max.

Why two components and not three
--------------------------------
The index previously carried a third component, the mean overlap duration.
It was removed after the audit recorded in
``docs/scientific_audit/issues/AUD-06_duration_component_validity.md``, for
three reasons established there:

* it measured the number of days on which two percentile tests happened to
  agree, which is a statistical coincidence rather than a physical duration;
* it was discretised into whole days by the daily resolution of the sea-level
  field, so a range of roughly one day domain-wide was stretched to the full
  [0, 1] scale and given a full one-third weight while contributing 6 % of the
  variance of the index;
* it anticorrelated with frequency (Spearman -0.550), so the two components
  cancelled inside the equal-weight mean instead of reinforcing, which is what
  placed the most storm-exposed stretch of the Brazilian coast at the bottom of
  the ranking.

Duration and the peak intensity remain computed and published as diagnostics;
they simply no longer enter the index. The integrated severity that replaces
them carries magnitude and persistence as a single quantity, so the two can no
longer cancel, and being a time integral it is not bounded by the daily
discretisation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NATIVE_GRID_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv"
)
#: The superseded MHWS product, preserved for comparison. Not read here.
LEGACY_GRID_SOURCE = (
    ROOT / "outputs" / "legacy_mhws_method" / "hazard" / "compound_metrics_mhws.csv"
)
#: The SSH_total product superseded before it. Not read here either.
LEGACY_SSH_TOTAL_GRID_SOURCE = (
    ROOT / "outputs" / "legacy_ssh_total_method" / "hazard" / "compound_metrics.csv"
)
COMPONENT_SOURCE_FIELDS = {
    "Hazard_Frequency": "compound_count_total",
    "Hazard_Severity": "mean_integrated_severity",
}
FREQUENCY_ANCHOR_EVENTS = 99.0
SEVERITY_ANCHOR = 1.0
#: Carried through unchanged for display and audit; none takes part in the
#: index. ``mean_overlap_duration`` and ``mean_full_criterion_duration`` are the
#: duration diagnostics retired from the index by AUD-06;
#: ``mean_compound_intensity_norm`` is the peak-based severity, superseded by
#: the integrated form but retained so the two can be compared.
PASSTHROUGH_SOURCE_FIELDS = (
    "compound_count_annual_mean",
    "mean_overlap_duration",
    "mean_full_criterion_duration",
    "mean_compound_intensity_norm",
    "mean_compound_intensity_norm_abspeak",
    "thr_hs_abs",
    "thr_zos_abs",
    # Level datum of the current method. ``mhws_m`` is the superseded field
    # name; both are listed so a legacy CSV still passes its datum through.
    "hat_m",
    "mhws_m",
)


def numeric_stats(series: pd.Series) -> dict[str, float | int | None]:
    """Summary statistics of the finite values of ``series``."""
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    if finite.empty:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }
    return {
        "count": int(len(finite)),
        "min": round(float(finite.min()), 6),
        "max": round(float(finite.max()), 6),
        "mean": round(float(finite.mean()), 6),
        "median": round(float(finite.median()), 6),
    }


def derive_native_hazard_index(
    source: Path = NATIVE_GRID_SOURCE,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Calculate the official 0--1 Hazard Index on the native ocean grid."""
    if not source.exists():
        raise FileNotFoundError(
            "The current multimetric Hazard Index requires the native-grid "
            f"compound metrics: {source}"
        )
    grid = pd.read_csv(source)
    required = {
        "grid_lat",
        "grid_lon",
        *COMPONENT_SOURCE_FIELDS.values(),
    }
    missing = sorted(required.difference(grid.columns))
    if missing:
        try:
            display_source = source.relative_to(ROOT)
        except ValueError:
            display_source = source
        raise ValueError(
            f"{display_source} lacks required field(s): "
            + ", ".join(missing)
        )

    passthrough_fields = [
        field for field in PASSTHROUGH_SOURCE_FIELDS if field in grid
    ]
    result = grid[
        [
            "grid_lat",
            "grid_lon",
            *COMPONENT_SOURCE_FIELDS.values(),
            *passthrough_fields,
        ]
    ].copy()
    for field in result.columns:
        result[field] = pd.to_numeric(result[field], errors="coerce")
    counts = result["compound_count_total"].fillna(0.0)
    severity = result["mean_integrated_severity"].fillna(0.0)
    if (counts < 0).any() or (severity < 0).any():
        raise ValueError("Hazard source components must be non-negative")
    result["Hazard_Frequency"] = (counts / FREQUENCY_ANCHOR_EVENTS).clip(0.0, 1.0)
    result["Hazard_Severity"] = (severity / SEVERITY_ANCHOR).clip(0.0, 1.0)
    result["Hazard_Index"] = (
        result["Hazard_Frequency"] + result["Hazard_Severity"]
    ) / 2.0
    result["Hazard_Index_raw"] = result["Hazard_Index"]
    result = result.dropna(
        subset=[
            "grid_lat",
            "grid_lon",
            *COMPONENT_SOURCE_FIELDS,
            "Hazard_Index_raw",
            "Hazard_Index",
        ]
    ).copy()
    if result.duplicated(["grid_lat", "grid_lon"]).any():
        raise ValueError(
            f"{source} contains duplicated grid_lat/grid_lon coordinates"
        )

    try:
        source_label = str(source.relative_to(ROOT))
    except ValueError:
        source_label = str(source)
    metadata = {
        "source": source_label,
        "implementation": "src/04_risk_integration/hazard_index.py",
        "grid_point_count": int(len(result)),
        "normalization_population": "fixed anchors, independent of sample extrema",
        "component_source_fields": COMPONENT_SOURCE_FIELDS,
        "component_weights": {
            "Hazard_Frequency": 0.5,
            "Hazard_Severity": 0.5,
        },
        "formula": (
            "Hazard_Frequency=min(compound_count_total/99,1); "
            "Hazard_Severity=min(fillna(mean_integrated_severity,0)/1,1); "
            "Hazard_Index=(Hazard_Frequency+Hazard_Severity)/2"
        ),
        "fixed_anchors": {
            "frequency_events": FREQUENCY_ANCHOR_EVENTS,
            "frequency_rationale": "3 accepted events/year over 33 years (1993-2025)",
            "severity": SEVERITY_ANCHOR,
            "severity_rationale": "one full-criterion day at the domain maximum daily excess",
        },
        "retired_component": {
            "field": "mean_overlap_duration",
            "retired_on": "2026-07-29",
            "reason": (
                "AUD-06: measured the coincidence of two percentile tests rather "
                "than a physical duration, was discretised into whole days over a "
                "domain-wide range of about one day, and anticorrelated with "
                "frequency (Spearman -0.550) so that the two cancelled inside the "
                "equal-weight mean. Retained as a published diagnostic."
            ),
        },
        "numeric_stats": {
            key: numeric_stats(result[key])
            for key in dict.fromkeys(
                (
                    "compound_count_total",
                    "mean_integrated_severity",
                    *passthrough_fields,
                    *COMPONENT_SOURCE_FIELDS,
                    "Hazard_Index_raw",
                    "Hazard_Index",
                )
            )
        },
    }
    return result, metadata
