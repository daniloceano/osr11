"""
Trend analysis for Step 3 — Hazard Characterization.

Implements Mann–Kendall trend test and Sen slope estimator for annual
time series derived from storm catalogs.

Handles lag-1 autocorrelation via the modified Mann–Kendall approach
(Hamed & Rao 1998) when significant autocorrelation is detected.

Annual series tested (see TREND_METRICS — 8 series):
    - annual_hs_count
    - annual_zos_count
    - annual_compound_count
    - annual_mean_hs_peak
    - annual_mean_zos_peak
    - annual_mean_hs_duration
    - annual_mean_zos_duration
    - annual_mean_overlap_duration

Note: ``annual_mean_compound_intensity_norm`` is allocated in ``build_annual_series``
but is intentionally NOT populated nor registered in ``TREND_METRICS`` — see
SCIENTIFIC_NOTES (Submodule 3.5) for the rationale.

References:
    - Mann, H. B. (1945). Nonparametric tests against trend. Econometrica.
    - Kendall, M. G. (1975). Rank Correlation Methods.
    - Sen, P. K. (1968). Estimates of the regression coefficient based on
      Kendall's tau. JASA.
    - Hamed, K. H. & Rao, A. R. (1998). A modified Mann-Kendall trend test
      for autocorrelated data. J. Hydrology, 204, 182–196.
    - Yue, S. et al. (2002). The influence of autocorrelation on the ability
      to detect trend in hydrological series. Hydrological Processes.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    flatten_catalog,
    build_grid_index,
    save_json,
    save_csv,
    HS_CATALOG,
    LEVEL_CATALOG,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "trends"


# ══════════════════════════════════════════════════════════════════════════════
# MANN-KENDALL IMPLEMENTATION
# ══════════════════════════════════════════════════════════════════════════════


def _mann_kendall_s(x: np.ndarray) -> tuple[int, int]:
    """Compute the Mann-Kendall S statistic and count of valid pairs.

    S = Σ_i Σ_{j>i} sign(x_j - x_i)
    """
    n = len(x)
    s = 0
    n_pairs = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = x[j] - x[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1
            n_pairs += 1
    return s, n_pairs


def _tied_groups(x: np.ndarray) -> list[int]:
    """Count tied group sizes."""
    unique, counts = np.unique(x, return_counts=True)
    return [int(c) for c in counts if c > 1]


def _variance_s(n: int, tied: list[int]) -> float:
    """Compute variance of S under H0 (no trend), accounting for ties."""
    var = n * (n - 1) * (2 * n + 5)
    for t in tied:
        var -= t * (t - 1) * (2 * t + 5)
    return var / 18.0


def _lag1_autocorrelation(x: np.ndarray) -> float:
    """Compute lag-1 autocorrelation coefficient."""
    n = len(x)
    if n < 3:
        return 0.0
    xm = x - np.mean(x)
    c0 = np.sum(xm**2)
    if c0 == 0:
        return 0.0
    c1 = np.sum(xm[:-1] * xm[1:])
    return c1 / c0


def _modified_variance_correction(x: np.ndarray, n: int) -> float:
    """Compute the Hamed & Rao (1998) variance correction factor n/S*.

    Returns a multiplier for the original variance.
    """
    # Compute all autocorrelation lags needed
    # n/S* = 1 + (2/n) * Σ_{i=1}^{n-1} (n-i) * r_i
    xm = x - np.mean(x)
    c0 = np.sum(xm**2)
    if c0 == 0:
        return 1.0

    correction = 0.0
    for lag in range(1, n):
        r_lag = np.sum(xm[:n - lag] * xm[lag:]) / c0
        correction += (n - lag) * r_lag

    nss = 1.0 + (2.0 / n) * correction
    return max(nss, 1.0)  # Cannot reduce variance below original


def mann_kendall_test(
    x: np.ndarray,
    alpha: float = 0.05,
    check_autocorrelation: bool = True,
) -> dict[str, Any]:
    """Perform the Mann-Kendall trend test.

    If check_autocorrelation is True and significant lag-1 autocorrelation
    is found, uses the Hamed & Rao (1998) modified variance.

    Parameters
    ----------
    x : array-like
        Time series values (ordered in time).
    alpha : float
        Significance level.
    check_autocorrelation : bool
        Whether to test and correct for lag-1 autocorrelation.

    Returns
    -------
    dict with keys: statistic_s, z_score, p_value, significant, direction,
        method, lag1_autocorrelation, sen_slope, sen_intercept.
    """
    x = np.asarray(x, dtype=float)

    # Remove NaN
    valid = ~np.isnan(x)
    x = x[valid]
    n = len(x)

    if n < 4:
        return {
            "statistic_s": None,
            "z_score": None,
            "p_value": None,
            "significant": False,
            "direction": "insufficient_data",
            "method": "insufficient_data",
            "lag1_autocorrelation": None,
            "sen_slope": None,
            "sen_intercept": None,
            "n_years": n,
        }

    # Compute S
    s, _ = _mann_kendall_s(x)

    # Tied groups
    tied = _tied_groups(x)

    # Base variance
    var_s = _variance_s(n, tied)

    # Check autocorrelation
    method = "original_mann_kendall"
    r1 = _lag1_autocorrelation(x)

    if check_autocorrelation and n >= 10:
        # Test if lag-1 autocorrelation is significant
        # Simple approximation: |r1| > 1.96 / sqrt(n) at α=0.05
        r1_threshold = 1.96 / np.sqrt(n)
        if abs(r1) > r1_threshold:
            correction = _modified_variance_correction(x, n)
            var_s *= correction
            method = "modified_mann_kendall_hamed_rao_1998"
            log.debug(
                "Significant lag-1 autocorrelation (r1=%.3f > %.3f). "
                "Using modified variance (correction=%.3f)",
                r1, r1_threshold, correction,
            )

    # Z score
    if var_s <= 0:
        z = 0.0
    else:
        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0.0

    # Two-sided p-value
    p = 2.0 * (1.0 - sp_stats.norm.cdf(abs(z)))

    # Direction
    if p <= alpha:
        direction = "increasing" if s > 0 else "decreasing"
    else:
        direction = "no_trend"

    # Sen slope
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            if j != i:
                slopes.append((x[j] - x[i]) / (j - i))
    sen_slope = float(np.median(slopes)) if slopes else None

    # Sen intercept
    if sen_slope is not None:
        sen_intercept = float(np.median(x - sen_slope * np.arange(n)))
    else:
        sen_intercept = None

    return {
        "statistic_s": int(s),
        "z_score": round(z, 4),
        "p_value": round(p, 6),
        "significant": bool(p <= alpha),
        "direction": direction,
        "method": method,
        "lag1_autocorrelation": round(r1, 4),
        "sen_slope": round(sen_slope, 6) if sen_slope is not None else None,
        "sen_intercept": round(sen_intercept, 6) if sen_intercept is not None else None,
        "n_years": n,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ANNUAL SERIES CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════


def build_annual_series(
    hs_catalog: list[dict],
    level_catalog: list[dict],
    compound_catalog: dict[tuple, list],
    grid_lat: float,
    grid_lon: float,
    year_range: tuple[int, int],
) -> dict[str, np.ndarray]:
    """Build annual time series for all metrics at one grid point.

    Returns dict mapping metric_name -> array of annual values.
    """
    years = np.arange(year_range[0], year_range[1] + 1)
    n_years = len(years)

    # Find grid point in catalogs
    key_hs = None
    for gp in hs_catalog:
        if (round(gp["grid_lat"], 4) == round(grid_lat, 4) and
                round(gp["grid_lon"], 4) == round(grid_lon, 4)):
            key_hs = gp
            break

    key_level = None
    for gp in level_catalog:
        if (round(gp["grid_lat"], 4) == round(grid_lat, 4) and
                round(gp["grid_lon"], 4) == round(grid_lon, 4)):
            key_level = gp
            break

    hs_storms = key_hs.get("storms", []) if key_hs else []
    level_storms = key_level.get("storms", []) if key_level else []
    compound_key = (round(grid_lat, 4), round(grid_lon, 4))
    compound_events = compound_catalog.get(compound_key, [])

    # Initialize annual arrays
    series = {
        "annual_hs_count": np.zeros(n_years),
        "annual_zos_count": np.zeros(n_years),
        "annual_compound_count": np.zeros(n_years),
        "annual_mean_hs_peak": np.full(n_years, np.nan),
        "annual_mean_zos_peak": np.full(n_years, np.nan),
        "annual_mean_compound_intensity_norm": np.full(n_years, np.nan),
        "annual_mean_hs_duration": np.full(n_years, np.nan),
        "annual_mean_zos_duration": np.full(n_years, np.nan),
        "annual_mean_overlap_duration": np.full(n_years, np.nan),
    }

    # Aggregate Hs
    hs_by_year: dict[int, list[dict]] = {y: [] for y in years}
    for s in hs_storms:
        yr = int(s["date_start"][:4])
        if yr in hs_by_year:
            hs_by_year[yr].append(s)

    for i, yr in enumerate(years):
        storms = hs_by_year[yr]
        series["annual_hs_count"][i] = len(storms)
        if storms:
            series["annual_mean_hs_peak"][i] = np.mean([s["peak_value"] for s in storms])
            series["annual_mean_hs_duration"][i] = np.mean([s["duration_days"] for s in storms])

    # Aggregate the tide-free level catalogue
    level_by_year: dict[int, list[dict]] = {y: [] for y in years}
    for s in level_storms:
        yr = int(s["date_start"][:4])
        if yr in level_by_year:
            level_by_year[yr].append(s)

    for i, yr in enumerate(years):
        storms = level_by_year[yr]
        series["annual_zos_count"][i] = len(storms)
        if storms:
            series["annual_mean_zos_peak"][i] = np.mean([s["peak_value"] for s in storms])
            series["annual_mean_zos_duration"][i] = np.mean([s["duration_days"] for s in storms])

    # Aggregate compound
    compound_by_year: dict[int, list[dict]] = {y: [] for y in years}
    for e in compound_events:
        yr = int(e["date_start"][:4])
        if yr in compound_by_year:
            compound_by_year[yr].append(e)

    for i, yr in enumerate(years):
        events = compound_by_year[yr]
        series["annual_compound_count"][i] = len(events)
        if events:
            overlaps = [e["overlap_duration_days"] for e in events]
            series["annual_mean_overlap_duration"][i] = np.mean(overlaps)

    return series


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

# Metrics to test (with units for slope)
TREND_METRICS = {
    "annual_hs_count": "events/year",
    "annual_zos_count": "events/year",
    "annual_compound_count": "events/year",
    "annual_mean_hs_peak": "m/year",
    "annual_mean_zos_peak": "m/year",
    "annual_mean_hs_duration": "days/year",
    "annual_mean_zos_duration": "days/year",
    "annual_mean_overlap_duration": "days/year",
}


def run_trends(
    compound_catalog_path: Path | None = None,
    alpha: float = 0.05,
) -> dict:
    """Run Mann–Kendall trend analysis over all grid points for all metrics.

    Returns dict with grid_results (one row per grid point × metric).
    """
    import json

    hs_catalog = load_catalog(HS_CATALOG)
    level_catalog = load_catalog(LEVEL_CATALOG)
    run_meta = load_run_metadata()

    year_start = int(run_meta["period_full_series"][0][:4])
    year_end = int(run_meta["period_full_series"][1][:4])

    # Load compound catalog
    compound_path = compound_catalog_path or (
        ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
    )
    compound_catalog: dict[tuple, list] = {}
    if compound_path.exists():
        with open(compound_path) as f:
            compound_data = json.load(f)
        for gp in compound_data:
            key = (round(gp["grid_lat"], 4), round(gp["grid_lon"], 4))
            compound_catalog[key] = gp.get("compound_events", [])

    # Build grid point list from Hs catalog
    grid_results = []
    for gp_idx, hs_gp in enumerate(hs_catalog):
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]

        annual = build_annual_series(
            hs_catalog, level_catalog, compound_catalog,
            lat, lon, (year_start, year_end),
        )

        point_results = {
            "grid_lat": round(lat, 4),
            "grid_lon": round(lon, 4),
            "municipality": hs_gp.get("municipality"),
        }

        for metric, unit in TREND_METRICS.items():
            values = annual[metric]
            result = mann_kendall_test(values, alpha=alpha)
            point_results[f"{metric}_slope"] = result["sen_slope"]
            point_results[f"{metric}_slope_unit"] = unit
            point_results[f"{metric}_p_value"] = result["p_value"]
            point_results[f"{metric}_significant"] = result["significant"]
            point_results[f"{metric}_direction"] = result["direction"]
            point_results[f"{metric}_method"] = result["method"]
            point_results[f"{metric}_lag1_autocorr"] = result["lag1_autocorrelation"]

        grid_results.append(point_results)

        if (gp_idx + 1) % 100 == 0:
            log.info("Trends: processed %d/%d grid points", gp_idx + 1, len(hs_catalog))

    log.info("Trend analysis completed for %d grid points", len(grid_results))
    return {"grid_results": grid_results}


def save_trend_results(results: dict, output_dir: Path | None = None):
    """Save trend analysis results."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results["grid_results"])
    save_csv(df, out / "trend_metrics.csv")
    save_json(results["grid_results"], out / "trend_metrics.json")
    log.info("Trend results saved to %s", out)
