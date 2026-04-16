"""
Per-episode attribute computation for Step 3.

For each storm episode, computes:
- event_id, date_start, date_end, duration_days
- peak_value, peak_date
- integrated_intensity = Σ max(value - threshold, 0) over episode days
- time_series (dates + values)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def compute_episode_attributes(
    *,
    dates: pd.DatetimeIndex,
    values: pd.Series,
    threshold: float,
    var_prefix: str,
    grid_lat: float,
    grid_lon: float,
) -> dict:
    """Compute all per-event attributes for one storm episode.

    Parameters
    ----------
    dates : pd.DatetimeIndex
        Dates composing this episode (sorted).
    values : pd.Series
        Full time series (used to extract values on episode dates).
    threshold : float
        Absolute threshold value used for exceedance detection.
    var_prefix : str
        "hs" or "ssh_total".
    grid_lat, grid_lon : float
        Grid point coordinates (for event_id).

    Returns
    -------
    dict with all per-event attributes (see README §4.2).
    """
    ep_values = values.reindex(dates)
    finite_mask = ep_values.notna()
    ep_finite = ep_values[finite_mask]

    date_start = dates[0]
    date_end = dates[-1]
    duration_days = len(dates)

    if len(ep_finite) > 0:
        peak_value = float(ep_finite.max())
        peak_date = ep_finite.idxmax()
    else:
        peak_value = float("nan")
        peak_date = date_start

    # Integrated intensity: Σ max(value - threshold, 0)
    exceedance = np.maximum(ep_finite.values - threshold, 0.0)
    integrated_intensity = float(np.sum(exceedance))

    # Event ID: <var>_<lat>_<lon>_<YYYYMMDD>
    event_id = (
        f"{var_prefix}_{grid_lat:.2f}_{grid_lon:.2f}_"
        f"{date_start.strftime('%Y%m%d')}"
    )

    return {
        "event_id": event_id,
        "date_start": date_start.strftime("%Y-%m-%d"),
        "date_end": date_end.strftime("%Y-%m-%d"),
        "duration_days": duration_days,
        "peak_value": round(peak_value, 4),
        "peak_date": peak_date.strftime("%Y-%m-%d") if isinstance(peak_date, pd.Timestamp) else str(peak_date),
        "integrated_intensity": round(integrated_intensity, 4),
        "time_series": {
            "dates": [d.strftime("%Y-%m-%d") for d in dates],
            "values": [round(float(v), 4) if np.isfinite(v) else None for v in ep_values.values],
        },
    }
