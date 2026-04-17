"""
Dependence analysis (Hₛ–SSH_total) for Step 3 — Hazard Characterization.

Computes measures of statistical dependence between wave height and total
sea level extremes, using paired samples derived from compound events.

Core metrics:
    - Kendall's τ: rank correlation (robust, non-parametric)
    - Spearman's ρ: monotone rank correlation
    - χ (chi): extremal dependence coefficient
    - χ̄ (chi-bar): extremal dependence below asymptotic independence

χ and χ̄ quantify the strength of dependence in the tails of the joint
distribution. They are central to understanding whether Hₛ and SSH_total
tend to be simultaneously extreme.

Sampling strategy:
    Paired samples are derived from compound events at each grid point —
    specifically, the (peak_hs, peak_ssh_total) pairs from each compound
    event. This ensures that the dependence analysis is based on co-occurring
    extremes, consistent with the compound event framework.

Minimum sample size:
    χ and χ̄ require a minimum sample of 20 compound events per grid point
    to produce stable estimates. Points below this threshold → NaN + metadata.
    τ and ρ require a minimum of 5 paired samples.

References:
    - Coles, S. G., Heffernan, J. E. & Tawn, J. A. (1999). Dependence
      measures for extreme value analyses. Extremes, 2, 339–365.
    - Ledford, A. W. & Tawn, J. A. (1996). Statistics for near independence
      in multivariate extreme values. Biometrika, 83(1), 169–187.
    - Ledford, A. W. & Tawn, J. A. (1997). Modelling dependence within
      joint tail regions. JRSS-B, 59(2), 475–499.
    - Camus, P., Haigh, I. D., Nasr, A. A., Wahl, T., Darby, S. E., &
      Nicholls, R. J. (2021). Regional analysis of multivariate compound
      flooding potential. NHESS, 21, 2021–2042.
    - Petroliagkis, T. I. (2018). Estimations of statistical dependence as
      joint return period modulator of compound events — Part 1: Storm
      surge and wave height. NHESS, 18, 1937–1953.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import kendalltau, spearmanr

from ..shared.catalog_utils import (
    save_json,
    save_csv,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "dependence"

# Minimum samples for different metrics
MIN_SAMPLES_RANK = 5
MIN_SAMPLES_CHI = 20


def compute_chi(u: np.ndarray, v: np.ndarray, quantile: float = 0.95) -> float | None:
    """Compute the extremal dependence coefficient χ.

    χ = lim_{u→1} P(F_Y(Y) > u | F_X(X) > u)

    Estimated empirically at a given quantile threshold.
    χ > 0 indicates asymptotic dependence.
    χ = 0 indicates asymptotic independence.

    Parameters
    ----------
    u, v : array
        Paired samples (e.g., Hs peaks and SSH_total peaks).
    quantile : float
        Quantile threshold for tail estimation (default 0.95).

    Returns
    -------
    float or None if insufficient data above threshold.
    """
    n = len(u)
    if n < MIN_SAMPLES_CHI:
        return None

    # Convert to ranks (empirical CDF)
    u_ranks = _empirical_cdf(u)
    v_ranks = _empirical_cdf(v)

    # Count joint exceedances above quantile
    above_u = u_ranks > quantile
    above_v = v_ranks > quantile

    n_u = np.sum(above_u)
    if n_u == 0:
        return None

    n_joint = np.sum(above_u & above_v)
    chi = n_joint / n_u

    return float(chi)


def compute_chi_bar(u: np.ndarray, v: np.ndarray, quantile: float = 0.95) -> float | None:
    """Compute the sub-asymptotic dependence coefficient χ̄.

    χ̄ = 2 * log(P(F_X(X) > u)) / log(P(F_X(X) > u, F_Y(Y) > u)) - 1

    Interpretation (must be read jointly with χ):
        If χ > 0: asymptotic dependence; χ̄ = 1 by definition (not informative).
        If χ = 0 (asymptotic independence): χ̄ ∈ (−1, 1] measures residual
        strength of tail association (Ledford & Tawn, 1996; 1997).
            χ̄ close to 1: slow decay → strong sub-asymptotic association
            χ̄ close to 0: faster decay toward independence
            χ̄ < 0: negative tail association

    Parameters
    ----------
    u, v : array
        Paired samples.
    quantile : float
        Quantile threshold.

    Returns
    -------
    float or None if insufficient data.
    """
    n = len(u)
    if n < MIN_SAMPLES_CHI:
        return None

    u_ranks = _empirical_cdf(u)
    v_ranks = _empirical_cdf(v)

    above_u = u_ranks > quantile
    above_v = v_ranks > quantile

    p_u = np.mean(above_u)
    p_joint = np.mean(above_u & above_v)

    if p_u <= 0 or p_joint <= 0:
        return None

    log_p_u = np.log(p_u)
    log_p_joint = np.log(p_joint)

    if log_p_joint == 0:
        return None

    chi_bar = 2 * log_p_u / log_p_joint - 1

    return float(np.clip(chi_bar, -1, 1))


def _empirical_cdf(x: np.ndarray) -> np.ndarray:
    """Compute empirical CDF values (Weibull plotting position)."""
    n = len(x)
    ranks = np.empty(n)
    order = np.argsort(x)
    ranks[order] = np.arange(1, n + 1) / (n + 1)
    return ranks


def compute_dependence_at_point(
    hs_peaks: np.ndarray,
    ssh_peaks: np.ndarray,
    chi_quantile: float = 0.95,
) -> dict[str, Any]:
    """Compute all dependence metrics for one grid point.

    Parameters
    ----------
    hs_peaks : array
        Hₛ peak values from compound events.
    ssh_peaks : array
        SSH_total peak values from compound events (paired).
    chi_quantile : float
        Quantile for χ/χ̄ estimation.

    Returns
    -------
    dict with tau, rho, chi, chi_bar, sample sizes, warnings.
    """
    n = len(hs_peaks)

    result: dict[str, Any] = {
        "n_compound_pairs": n,
        "tau": None,
        "tau_p_value": None,
        "rho": None,
        "rho_p_value": None,
        "chi": None,
        "chi_bar": None,
        "chi_quantile": chi_quantile,
        "warnings": [],
    }

    if n < MIN_SAMPLES_RANK:
        result["warnings"].append(f"insufficient_pairs (n={n} < {MIN_SAMPLES_RANK})")
        return result

    # Kendall's τ
    try:
        tau_val, tau_p = kendalltau(hs_peaks, ssh_peaks)
        result["tau"] = round(float(tau_val), 4)
        result["tau_p_value"] = round(float(tau_p), 6)
    except Exception as e:
        result["warnings"].append(f"tau_failed: {str(e)[:60]}")

    # Spearman's ρ
    try:
        rho_val, rho_p = spearmanr(hs_peaks, ssh_peaks)
        result["rho"] = round(float(rho_val), 4)
        result["rho_p_value"] = round(float(rho_p), 6)
    except Exception as e:
        result["warnings"].append(f"rho_failed: {str(e)[:60]}")

    # χ and χ̄ (require larger samples)
    if n >= MIN_SAMPLES_CHI:
        chi_val = compute_chi(hs_peaks, ssh_peaks, chi_quantile)
        chi_bar_val = compute_chi_bar(hs_peaks, ssh_peaks, chi_quantile)
        result["chi"] = round(chi_val, 4) if chi_val is not None else None
        result["chi_bar"] = round(chi_bar_val, 4) if chi_bar_val is not None else None
    else:
        result["warnings"].append(
            f"chi/chi_bar: insufficient_compound_events (n={n} < {MIN_SAMPLES_CHI})"
        )

    return result


def run_dependence(
    compound_catalog_path: Path | None = None,
    chi_quantile: float = 0.95,
) -> dict:
    """Run dependence analysis over all grid points.

    Uses paired (peak_hs, peak_ssh_total) from compound events.
    """
    compound_path = compound_catalog_path or (
        ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
    )
    if not compound_path.exists():
        raise FileNotFoundError(
            f"Compound catalog not found: {compound_path}\n"
            "Run compound detection (02_compound_detection) first."
        )

    with open(compound_path) as f:
        compound_data = json.load(f)

    grid_results = []
    for gp in compound_data:
        events = gp.get("compound_events", [])

        hs_peaks = np.array([e["peak_hs"] for e in events if "peak_hs" in e])
        ssh_peaks = np.array([e["peak_ssh_total"] for e in events if "peak_ssh_total" in e])

        # Ensure paired
        min_len = min(len(hs_peaks), len(ssh_peaks))
        hs_peaks = hs_peaks[:min_len]
        ssh_peaks = ssh_peaks[:min_len]

        dep = compute_dependence_at_point(hs_peaks, ssh_peaks, chi_quantile)

        grid_results.append({
            "grid_lat": gp["grid_lat"],
            "grid_lon": gp["grid_lon"],
            "municipality": gp.get("municipality"),
            **dep,
        })

    log.info("Dependence analysis completed for %d grid points", len(grid_results))
    return {"grid_results": grid_results, "chi_quantile": chi_quantile}


def save_dependence_results(results: dict, output_dir: Path | None = None):
    """Save dependence analysis results."""
    import pandas as pd
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    save_json(results["grid_results"], out / "dependence_metrics.json")

    rows = []
    for gr in results["grid_results"]:
        rows.append({
            "grid_lat": gr["grid_lat"],
            "grid_lon": gr["grid_lon"],
            "municipality": gr.get("municipality"),
            "n_compound_pairs": gr["n_compound_pairs"],
            "tau": gr["tau"],
            "tau_p_value": gr["tau_p_value"],
            "rho": gr["rho"],
            "rho_p_value": gr["rho_p_value"],
            "chi": gr["chi"],
            "chi_bar": gr["chi_bar"],
            "chi_quantile": gr["chi_quantile"],
            "warnings": "; ".join(gr.get("warnings", [])),
        })
    df = pd.DataFrame(rows)
    save_csv(df, out / "dependence_metrics.csv")
    log.info("Dependence results saved to %s", out)
