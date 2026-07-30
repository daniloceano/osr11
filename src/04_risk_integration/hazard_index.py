"""Canonical calculation of the native-grid Hazard Index.

The physical hazard combines two equally weighted components: compound-event
frequency and mean integrated severity. Each is Min--Max normalized over the
full native ocean grid; their mean is then Min--Max normalized over the same
domain to obtain the final 0--1 Hazard Index.

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

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NATIVE_GRID_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
#: The superseded SSH_total product, preserved for comparison. Not read here.
LEGACY_GRID_SOURCE = (
    ROOT / "outputs" / "legacy_ssh_total_method" / "hazard" / "compound_metrics.csv"
)
COMPONENT_SOURCE_FIELDS = {
    "Hazard_Frequency": "compound_count_total",
    "Hazard_Severity": "mean_integrated_severity",
}
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
    "mhws_m",
)


def _minmax(series: pd.Series) -> pd.Series:
    """Min--Max normalize finite values while preserving missing values."""
    values = pd.to_numeric(series, errors="coerce")
    finite = values[np.isfinite(values)]
    if finite.empty:
        raise ValueError(f"No finite values are available for {series.name!r}")
    lower = float(finite.min())
    upper = float(finite.max())
    if math.isclose(lower, upper):
        result = pd.Series(np.nan, index=values.index, dtype=float)
        result.loc[finite.index] = 0.0
        return result
    return (values - lower) / (upper - lower)


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
    for output_field, source_field in COMPONENT_SOURCE_FIELDS.items():
        result[output_field] = _minmax(result[source_field])

    result["Hazard_Index_raw"] = result[
        list(COMPONENT_SOURCE_FIELDS)
    ].mean(axis=1, skipna=False)
    result["Hazard_Index"] = _minmax(result["Hazard_Index_raw"])
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
        "normalization_population": "all finite native ocean grid points",
        "component_source_fields": COMPONENT_SOURCE_FIELDS,
        "component_weights": {
            "Hazard_Frequency": 0.5,
            "Hazard_Severity": 0.5,
        },
        "formula": (
            "Hazard_Index_raw = [norm(compound_count_total) + "
            "norm(mean_integrated_severity)] / 2; "
            "Hazard_Index = norm(Hazard_Index_raw)"
        ),
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
