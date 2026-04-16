"""
Univariate extreme value analysis (POT–GPD) for Step 3 — Hazard Characterization.

Fits a Generalized Pareto Distribution (GPD) to declustered storm peaks
(from the Step 3 catalogs) and computes return levels for specified
return periods.

Methodology:
    1. Take the per-grid-point storm peak values from the Hₛ and SSH_total
       catalogs as the POT sample. These are already declustered by the
       episode clustering in Step 3 (gap tolerance ≤ 1 day).
    2. Define excesses as: excess = peak_value - threshold_abs
       where threshold_abs is the local q90 threshold at each grid point.
    3. Fit GPD(ξ, σ) to the excesses via maximum likelihood (scipy).
    4. Compute return levels: x_T = u + (σ/ξ) * ((T * λ)^ξ - 1)
       where u = threshold, λ = mean exceedances per year, T = return period.
    5. Estimate confidence intervals via profile likelihood or delta method.

Independence guarantee:
    Storm peaks are independent by construction — the POT clustering in Step 3
    merges consecutive exceedances into single episodes and extracts one peak
    per episode. The gap tolerance of 1 day ensures that temporally adjacent
    peaks belong to the same meteorological event.

References:
    - Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values.
    - Ferro, C. A. T. & Segers, J. (2003). Inference for clusters of extreme values.
      JRSS-B, 65, 545–556.
    - Davison, A. C. & Smith, R. L. (1990). Models for exceedances over high
      thresholds. JRSS-B, 52, 393–442.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import genpareto

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    save_json,
    save_csv,
    HS_CATALOG,
    SSH_CATALOG,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "eva"

# Default return periods (years)
DEFAULT_RETURN_PERIODS = [2, 5, 10, 20, 50]

# Minimum sample size for GPD fitting
MIN_EXCEEDANCES = 10


def fit_gpd_at_point(
    peaks: np.ndarray,
    threshold: float,
    n_years: float,
    return_periods: list[int] | None = None,
) -> dict[str, Any]:
    """Fit GPD to storm peak excesses at one grid point.

    Parameters
    ----------
    peaks : array
        Storm peak values (already declustered).
    threshold : float
        Absolute threshold (local q90).
    n_years : float
        Number of years in the record.
    return_periods : list of int
        Return periods in years.

    Returns
    -------
    dict with GPD parameters, return levels, diagnostics.
    """
    return_periods = return_periods or DEFAULT_RETURN_PERIODS

    # Compute excesses
    excesses = peaks[peaks > threshold] - threshold
    n_exceed = len(excesses)

    if n_exceed < MIN_EXCEEDANCES:
        return {
            "n_exceedances": n_exceed,
            "lambda_per_year": round(n_exceed / n_years, 4) if n_years > 0 else None,
            "gpd_shape": None,
            "gpd_scale": None,
            "fit_success": False,
            "fit_message": f"insufficient_sample (n={n_exceed} < {MIN_EXCEEDANCES})",
            "return_levels": {str(T): None for T in return_periods},
            "return_levels_ci_lower": {str(T): None for T in return_periods},
            "return_levels_ci_upper": {str(T): None for T in return_periods},
        }

    lam = n_exceed / n_years  # mean exceedances per year

    # Fit GPD via MLE (scipy parameterization: c = shape ξ, scale = σ)
    try:
        c, loc, scale = genpareto.fit(excesses, floc=0)
        fit_success = True
        fit_message = "mle_converged"

        # Sanity checks
        if scale <= 0:
            fit_success = False
            fit_message = "negative_scale"
        elif np.isnan(c) or np.isnan(scale):
            fit_success = False
            fit_message = "nan_parameters"
    except Exception as e:
        c, loc, scale = np.nan, 0.0, np.nan
        fit_success = False
        fit_message = f"fit_failed: {str(e)[:80]}"

    # Return levels
    rlevels = {}
    rlevels_ci_lo = {}
    rlevels_ci_hi = {}

    if fit_success:
        for T in return_periods:
            try:
                # Return level formula for GPD
                # x_T = u + (σ/ξ) * ((T * λ)^ξ - 1)  for ξ ≠ 0
                # x_T = u + σ * ln(T * λ)              for ξ = 0
                m = T * lam
                if abs(c) < 1e-10:
                    rl = threshold + scale * np.log(m)
                else:
                    rl = threshold + (scale / c) * (m**c - 1)

                rlevels[str(T)] = round(float(rl), 4)

                # Delta method CI (approximate)
                ci = _delta_method_ci(excesses, c, scale, threshold, lam, T)
                rlevels_ci_lo[str(T)] = round(ci[0], 4) if ci[0] is not None else None
                rlevels_ci_hi[str(T)] = round(ci[1], 4) if ci[1] is not None else None

            except (OverflowError, ValueError, ZeroDivisionError):
                rlevels[str(T)] = None
                rlevels_ci_lo[str(T)] = None
                rlevels_ci_hi[str(T)] = None
    else:
        rlevels = {str(T): None for T in return_periods}
        rlevels_ci_lo = {str(T): None for T in return_periods}
        rlevels_ci_hi = {str(T): None for T in return_periods}

    return {
        "n_exceedances": n_exceed,
        "lambda_per_year": round(lam, 4),
        "gpd_shape": round(float(c), 6) if fit_success else None,
        "gpd_scale": round(float(scale), 6) if fit_success else None,
        "fit_success": fit_success,
        "fit_message": fit_message,
        "return_levels": rlevels,
        "return_levels_ci_lower": rlevels_ci_lo,
        "return_levels_ci_upper": rlevels_ci_hi,
    }


def _delta_method_ci(
    excesses: np.ndarray,
    shape: float,
    scale: float,
    threshold: float,
    lam: float,
    T: float,
    alpha: float = 0.05,
) -> tuple[float | None, float | None]:
    """Approximate confidence interval via the delta method.

    Uses the observed Fisher information matrix approximation.
    Returns (lower, upper) or (None, None) on failure.
    """
    from scipy.stats import norm

    n = len(excesses)
    if n < 5:
        return (None, None)

    try:
        m = T * lam

        # Variance of return level via delta method
        # Var(x_T) ≈ (∂x_T/∂σ)² * Var(σ) + (∂x_T/∂ξ)² * Var(ξ)
        #           + 2 * (∂x_T/∂σ)(∂x_T/∂ξ) * Cov(σ,ξ)
        # Using approximate information matrix

        # Partial derivatives of return level
        if abs(shape) < 1e-10:
            drl_dsigma = np.log(m)
            drl_dxi = 0.0
        else:
            drl_dsigma = (m**shape - 1) / shape
            drl_dxi = (scale / shape) * (m**shape * np.log(m) - (m**shape - 1) / shape)

        # Approximate variance-covariance matrix from MLE
        var_sigma = 2 * scale**2 / n
        var_xi = (1 + shape)**2 / n
        cov_sigma_xi = -scale * (1 + shape) / n

        var_rl = (drl_dsigma**2 * var_sigma
                  + drl_dxi**2 * var_xi
                  + 2 * drl_dsigma * drl_dxi * cov_sigma_xi)

        if var_rl <= 0:
            return (None, None)

        se_rl = np.sqrt(var_rl)
        z_alpha = norm.ppf(1 - alpha / 2)

        rl_point = threshold + (scale / shape) * (m**shape - 1) if abs(shape) > 1e-10 else threshold + scale * np.log(m)
        lower = rl_point - z_alpha * se_rl
        upper = rl_point + z_alpha * se_rl

        return (float(lower), float(upper))

    except Exception:
        return (None, None)


def run_eva(
    return_periods: list[int] | None = None,
) -> dict:
    """Run univariate POT-GPD analysis for Hₛ and SSH_total.

    Returns dict with grid_results for both variables.
    """
    return_periods = return_periods or DEFAULT_RETURN_PERIODS

    hs_catalog = load_catalog(HS_CATALOG)
    ssh_catalog = load_catalog(SSH_CATALOG)
    run_meta = load_run_metadata()
    n_years = get_period_years(run_meta)

    grid_results = []

    for hs_gp in hs_catalog:
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]
        muni = hs_gp.get("municipality")

        # Find matching SSH entry
        ssh_gp = None
        for g in ssh_catalog:
            if (round(g["grid_lat"], 4) == round(lat, 4) and
                    round(g["grid_lon"], 4) == round(lon, 4)):
                ssh_gp = g
                break

        # Hs EVA
        hs_storms = hs_gp.get("storms", [])
        hs_peaks = np.array([s["peak_value"] for s in hs_storms])
        hs_thr = hs_gp.get("thr_hs_abs")

        if hs_thr is not None and len(hs_peaks) > 0:
            hs_eva = fit_gpd_at_point(hs_peaks, hs_thr, n_years, return_periods)
        else:
            hs_eva = {
                "n_exceedances": 0, "fit_success": False,
                "fit_message": "no_threshold_or_no_storms",
                "return_levels": {str(T): None for T in return_periods},
            }

        # SSH_total EVA
        if ssh_gp:
            ssh_storms = ssh_gp.get("storms", [])
            ssh_peaks = np.array([s["peak_value"] for s in ssh_storms])
            ssh_thr = ssh_gp.get("thr_ssh_total_abs")

            if ssh_thr is not None and len(ssh_peaks) > 0:
                ssh_eva = fit_gpd_at_point(ssh_peaks, ssh_thr, n_years, return_periods)
            else:
                ssh_eva = {
                    "n_exceedances": 0, "fit_success": False,
                    "fit_message": "no_threshold_or_no_storms",
                    "return_levels": {str(T): None for T in return_periods},
                }
        else:
            ssh_eva = {
                "n_exceedances": 0, "fit_success": False,
                "fit_message": "no_ssh_data",
                "return_levels": {str(T): None for T in return_periods},
            }

        grid_results.append({
            "grid_lat": round(lat, 4),
            "grid_lon": round(lon, 4),
            "municipality": muni,
            # Hs EVA
            **{f"hs_{k}": v for k, v in hs_eva.items()},
            # SSH_total EVA
            **{f"ssh_total_{k}": v for k, v in ssh_eva.items()},
        })

    log.info("EVA completed for %d grid points", len(grid_results))
    return {"grid_results": grid_results, "return_periods": return_periods}


def save_eva_results(results: dict, output_dir: Path | None = None):
    """Save EVA results."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    save_json(results["grid_results"], out / "eva_metrics.json")

    # Flat CSV with return levels as columns
    rows = []
    for gr in results["grid_results"]:
        row = {
            "grid_lat": gr["grid_lat"],
            "grid_lon": gr["grid_lon"],
            "municipality": gr.get("municipality"),
            # Hs
            "hs_n_exceedances": gr.get("hs_n_exceedances"),
            "hs_lambda_per_year": gr.get("hs_lambda_per_year"),
            "hs_gpd_shape": gr.get("hs_gpd_shape"),
            "hs_gpd_scale": gr.get("hs_gpd_scale"),
            "hs_fit_success": gr.get("hs_fit_success"),
            "hs_fit_message": gr.get("hs_fit_message"),
        }
        hs_rl = gr.get("hs_return_levels", {})
        for T in results["return_periods"]:
            row[f"hs_rl_{T}yr"] = hs_rl.get(str(T))
        # SSH
        row["ssh_total_n_exceedances"] = gr.get("ssh_total_n_exceedances")
        row["ssh_total_lambda_per_year"] = gr.get("ssh_total_lambda_per_year")
        row["ssh_total_gpd_shape"] = gr.get("ssh_total_gpd_shape")
        row["ssh_total_gpd_scale"] = gr.get("ssh_total_gpd_scale")
        row["ssh_total_fit_success"] = gr.get("ssh_total_fit_success")
        row["ssh_total_fit_message"] = gr.get("ssh_total_fit_message")
        ssh_rl = gr.get("ssh_total_return_levels", {})
        for T in results["return_periods"]:
            row[f"ssh_total_rl_{T}yr"] = ssh_rl.get(str(T))
        rows.append(row)

    df = pd.DataFrame(rows)
    save_csv(df, out / "eva_return_levels.csv")
    log.info("EVA results saved to %s", out)
