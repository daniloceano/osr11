"""Canonical calculation of the native-grid multimetric Hazard Index.

The current physical hazard combines three equally weighted components:
compound-event frequency, mean overlap duration, and mean normalized
compound-event intensity. Each component is Min--Max normalized over the full
native ocean grid. Their mean is then Min--Max normalized over the same domain
to obtain the final 0--1 Hazard Index.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
NATIVE_GRID_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv"
)
COMPONENT_SOURCE_FIELDS = {
    "Hazard_Frequency": "compound_count_total",
    "Hazard_Duration": "mean_overlap_duration",
    "Hazard_Intensity": "mean_compound_intensity_norm",
}
PASSTHROUGH_SOURCE_FIELDS = ("compound_count_annual_mean",)


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


def _numeric_stats(series: pd.Series) -> dict[str, float | int | None]:
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
            "Hazard_Frequency": 1.0 / 3.0,
            "Hazard_Duration": 1.0 / 3.0,
            "Hazard_Intensity": 1.0 / 3.0,
        },
        "formula": (
            "Hazard_Index_raw = [norm(compound_count_total) + "
            "norm(mean_overlap_duration) + "
            "norm(mean_compound_intensity_norm)] / 3; "
            "Hazard_Index = norm(Hazard_Index_raw)"
        ),
        "numeric_stats": {
            key: _numeric_stats(result[key])
            for key in (
                "compound_count_total",
                *passthrough_fields,
                "mean_overlap_duration",
                "mean_compound_intensity_norm",
                "Hazard_Frequency",
                "Hazard_Duration",
                "Hazard_Intensity",
                "Hazard_Index_raw",
                "Hazard_Index",
            )
        },
    }
    return result, metadata
