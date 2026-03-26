"""
preprocessing.py — Temporal domain restriction for Step 4 threshold calibration.

Clips the unified metocean dataset to the period covered by the reported events
database, extended by the causal matching window margins.

Rationale
---------
The reported events database (Leal et al., 2024) covers 1998–2023. The unified
metocean dataset spans 1993–2025. Without temporal restriction, Layer 2 (false
alarm detection) scans the full ~11,700-step series. Any compound episode detected
in 1993–1997 or in 2024–2025 is automatically classified as a false alarm — not
because the episode is genuinely spurious, but because the validation database does
not cover those years. This systematic inflation of F distorts FAR and CSI and can
shift the optimal threshold pair towards artificially restrictive combinations.

The preprocessing layer clips the input dataset to:

    t_start = min(event_dates) + min(offsets)   [e.g., 1998-01-XX − 2 days]
    t_end   = max(event_dates) + max(offsets)   [e.g., 2023-MM-DD + 1 day]

The causal window offsets are included in the margins so that every event's full
match window [D+min_offset, D+max_offset] falls entirely within the clipped domain.

This ensures that:

- Layer 1 (hit/miss): causal windows are evaluated within the validated period.
- Layer 2 (false alarms): the scan is restricted to the validated period, so F only
  counts episodes the database is in a position to validate or reject.
- Quantile thresholds: computed from the clipped series (~25 years instead of ~32).
  Statistical robustness is preserved: ~9,100 daily observations per grid point.

Design decision: clipping the full input dataset (rather than only passing a
restricted time_index to run_false_alarms) is the cleaner approach because it
makes both the threshold computation and the false alarm scan consistent with the
same temporal domain. It also keeps main.py simple: one preprocessing call, one
unified time_index downstream.

Assumptions
-----------
- The event date column contains valid pd.Timestamps after upstream preprocessing.
- match_window_offsets includes at least one negative offset (antecedent) and at
  least one non-negative offset (operational tolerance).
- The dataset 'time' coordinate uses the same daily 00:00 UTC convention as the
  events dataframe (tz-naive or consistently tz-aware).
- The reported events fall within the dataset's time range after clipping.
"""
from __future__ import annotations

import logging

import pandas as pd
import xarray as xr

log = logging.getLogger(__name__)


def clip_to_validated_period(
    ds: xr.Dataset,
    df_events: pd.DataFrame,
    match_window_offsets: list[int],
    date_col: str = "date",
) -> tuple[xr.Dataset, pd.Timestamp, pd.Timestamp]:
    """Clip the unified dataset to the validated temporal domain.

    The domain is defined by the event date range in df_events, extended by the
    causal matching window margins so that every event's full match window
    [D + min_offset, D + max_offset] falls within the clipped domain.

    Parameters
    ----------
    ds : xr.Dataset
        Full unified metocean dataset (e.g., 1993–2025).
    df_events : pd.DataFrame
        Reported events dataframe with at least a ``date`` column of
        pd.Timestamp values (produced by load_reported_events).
    match_window_offsets : list[int]
        Causal window day offsets relative to each event date D (e.g.,
        ``[-2, -1, 0, 1]``). The minimum and maximum values determine how far
        the clip margins extend beyond the first and last event respectively.
    date_col : str, optional
        Column in ``df_events`` that holds event dates. Default: ``"date"``.

    Returns
    -------
    ds_clipped : xr.Dataset
        Dataset restricted to [t_start, t_end].
    t_start : pd.Timestamp
        First day of the clipped domain (inclusive).
    t_end : pd.Timestamp
        Last day of the clipped domain (inclusive).

    Raises
    ------
    ValueError
        If df_events is empty, contains no valid dates, or if the clipped
        dataset turns out to be empty (domain outside dataset range).
    """
    event_dates = pd.to_datetime(df_events[date_col].dropna())
    if event_dates.empty:
        raise ValueError(
            "clip_to_validated_period: df_events contains no valid dates. "
            "Check the date column and the upstream preprocessing pipeline."
        )

    earliest_event = event_dates.min()
    latest_event   = event_dates.max()

    # Extend the clip margins by the causal window offsets so that every
    # event's full match window falls inside the retained domain.
    earliest_offset = min(match_window_offsets)  # typically −2
    latest_offset   = max(match_window_offsets)  # typically +1

    t_start = (
        pd.Timestamp(earliest_event.year, earliest_event.month, earliest_event.day)
        + pd.Timedelta(days=earliest_offset)
    )
    t_end = (
        pd.Timestamp(latest_event.year, latest_event.month, latest_event.day)
        + pd.Timedelta(days=latest_offset)
    )

    original_n = int(ds.sizes["time"])
    ds_clipped = ds.sel(time=slice(t_start, t_end))
    clipped_n  = int(ds_clipped.sizes["time"])
    removed_n  = original_n - clipped_n

    log.info(
        "[preprocessing] Temporal clip applied: %s → %s  "
        "(%d → %d steps, %d steps removed)",
        t_start.date(), t_end.date(),
        original_n, clipped_n, removed_n,
    )
    log.info(
        "[preprocessing] Event date range: %s → %s  "
        "(window margins: %+d / %+d days relative to first/last event)",
        earliest_event.date(), latest_event.date(),
        earliest_offset, latest_offset,
    )

    if clipped_n == 0:
        ds_times = ds.time.values
        raise ValueError(
            f"clip_to_validated_period: clipped dataset is empty. "
            f"Requested [{t_start.date()}, {t_end.date()}], but dataset time "
            f"range is [{ds_times[0]}, {ds_times[-1]}]. "
            f"Check that the unified dataset covers the events period."
        )

    return ds_clipped, t_start, t_end
