"""
Causal/antecedent matching window for the threshold calibration.

Purpose
-------
For each observed coastal disaster (reported date D), we define a set of
admissible match timestamps: the compound condition may be detected at any
of these times and the event is still considered captured.

Window definition
-----------------
    match_times = [D-2, D-1, D, D+1 00Z]

Rationale
---------
- D-2, D-1  : allow the joint forcing to be detected before the impact
              reaches its peak and is recorded by Civil Defense.
- D          : the reported event day itself.
- D+1 00Z   : operational tolerance. The unified dataset contains daily
              snapshots at midnight UTC (00:00 UTC), not daily means. If the
              peak compound condition occurred during civil day D (e.g., at
              18:00 UTC), it will appear as the 00:00 UTC snapshot of D+1
              after the daily aggregation. This single extra step avoids
              unjustly penalising events that straddle the UTC midnight
              boundary.

What is NOT included
--------------------
D+2 and beyond: any compound episode detected two or more days after the
reported event date is NOT considered a match. The matching logic is
explicitly asymmetric — it accepts antecedents and allows for the D+1 00Z
convention, but does not reach forward in time after that tolerance.

Time index compatibility
------------------------
Each offset is only included if the corresponding timestamp exists in the
dataset's time coordinate. Missing timestamps (e.g., outside the data range)
are silently skipped.
"""
from __future__ import annotations

import pandas as pd

from src.threshold_calibration.config.analysis_config import CFG


def build_causal_window(
    date: pd.Timestamp,
    time_index: pd.DatetimeIndex,
) -> list[pd.Timestamp]:
    """Return the list of admissible match timestamps for event date D.

    Parameters
    ----------
    date : pd.Timestamp
        The reported event date (civil day, no time component assumed).
    time_index : pd.DatetimeIndex
        Full time coordinate of the dataset (daily 00:00 UTC snapshots).

    Returns
    -------
    list of pd.Timestamp
        Timestamps from time_index that fall within the causal window
        [D-2, D-1, D, D+1]. May be empty if the event date is far outside
        the dataset range.
    """
    offsets = CFG["match_window_offsets"]  # default: [-2, -1, 0, 1]
    # Normalise date to midnight UTC (same convention as the dataset)
    date_midnight = pd.Timestamp(date.year, date.month, date.day, 0, 0, 0, tz=None)

    # Build candidate timestamps and filter against the actual time index
    time_set = set(time_index)
    result = []
    for off in offsets:
        candidate = date_midnight + pd.Timedelta(days=off)
        # Also try timezone-naive normalisation in case time_index has tzinfo
        if candidate in time_set:
            result.append(candidate)
        else:
            # Try matching by date only (handles tz-naive vs tz-aware edge cases)
            for t in time_index:
                if (
                    t.year == candidate.year
                    and t.month == candidate.month
                    and t.day == candidate.day
                ):
                    result.append(t)
                    break
    return result


def window_label(offsets: list[int]) -> str:
    """Return a human-readable label describing the match window."""
    parts = []
    for off in sorted(offsets):
        if off < 0:
            parts.append(f"D{off}")
        elif off == 0:
            parts.append("D")
        else:
            parts.append(f"D+{off} 00Z")
    return ", ".join(parts)
