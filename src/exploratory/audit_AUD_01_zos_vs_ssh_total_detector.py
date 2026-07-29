"""AUD-01 diagnostic: is a `zos`-only level detector free of spring-neap phase locking?

Tests the premise behind the proposed detector redesign — separating the
astronomical tide (FES2022) from the dynamic sea level (GLORYS12 `zos`) and
detecting level episodes on `zos` alone, so that the astronomical signal stops
driving detection in the macrotidal North.

For each of the 808 native coastal grid points, using the same production
recipe (local q90 threshold, episodes clustered with a maximum gap of 1 day):

1. detects level episodes on `zos` and, for comparison, on `SSH_total`;
2. applies the Rayleigh test of the episode start dates against the
   semi-synodic (spring-neap) period, as in
   `audit_AUD_01_rayleigh_phase_test.py`;
3. decomposes the variance of `SSH_total` into tide and residual parts;
4. reports the physical magnitude of q90(zos), to check whether a zos-only
   threshold is meaningful in the North or merely moves the "physically empty
   threshold" problem (AUD-02) from waves to level;
5. runs a second Rayleigh test of the `zos` episodes against the ANNUAL cycle,
   to check whether zos-only detection in the Amazon sector would trade tidal
   phase locking for seasonal river-discharge phase locking (AUD-12).

Read-only diagnostic. Does not modify the production pipeline or any published
output.

Usage:
    python -m src.exploratory.audit_AUD_01_zos_vs_ssh_total_detector

Output:
    outputs/audit/AUD-01_zos_vs_ssh_total_detector/detector_comparison_by_point.csv
    outputs/audit/AUD-01_zos_vs_ssh_total_detector/detector_comparison_by_band.csv
    outputs/audit/AUD-01_zos_vs_ssh_total_detector/summary.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
CATALOG = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_zos_vs_ssh_total_detector"

SEMI_SYNODIC_PERIOD_DAYS = 14.765294
REFERENCE_EPOCH = date(1993, 1, 23)
QUANTILE = 0.90
MAX_GAP_DAYS = 1  # production EPISODE_MAX_GAP_DAYS
MIN_EVENTS = 10

LATITUDE_BANDS = [
    ("RS", -36.0, -30.0),
    ("SC/PR", -30.0, -25.0),
    ("SP/RJ", -25.0, -20.0),
    ("ES/BA-S", -20.0, -15.0),
    ("BA-N", -15.0, -10.0),
    ("NE", -10.0, -5.0),
    ("N_equatorial", -5.0, 0.0),
    ("AP", 0.0, 7.0),
]


def rayleigh_test(angles_rad: np.ndarray) -> tuple[float, float]:
    """(R, p) for the Rayleigh test of circular uniformity (Mardia & Jupp 2000)."""
    n = angles_rad.size
    if n < MIN_EVENTS:
        return float("nan"), float("nan")
    c = np.cos(angles_rad).sum()
    s = np.sin(angles_rad).sum()
    r = np.hypot(c, s) / n
    z = n * r**2
    p = np.exp(-z) * (
        1
        + (2 * z - z**2) / (4 * n)
        - (24 * z - 132 * z**2 + 76 * z**3 - 9 * z**4) / (288 * n**2)
    )
    return float(r), float(np.clip(p, 0.0, 1.0))


def episode_start_indices(exceeds: np.ndarray, max_gap: int) -> np.ndarray:
    """Start indices of episodes: exceedance runs separated by <= max_gap gaps.

    Mirrors the production clustering rule (two exceedance days belong to the
    same episode if separated by at most `max_gap` non-exceedance days).
    """
    idx = np.flatnonzero(exceeds)
    if idx.size == 0:
        return np.empty(0, dtype=int)
    breaks = np.flatnonzero(np.diff(idx) > max_gap + 1)
    starts = np.concatenate(([idx[0]], idx[breaks + 1]))
    return starts


def phase_angles_spring_neap(days_since_epoch: np.ndarray) -> np.ndarray:
    frac = np.mod(days_since_epoch, SEMI_SYNODIC_PERIOD_DAYS) / SEMI_SYNODIC_PERIOD_DAYS
    return 2 * np.pi * frac


def phase_angles_annual(day_of_year: np.ndarray) -> np.ndarray:
    return 2 * np.pi * (day_of_year / 365.25)


def band_for_latitude(lat: float) -> str | None:
    for name, lo, hi in LATITUDE_BANDS:
        if lo <= lat < hi:
            return name
    return None


def main() -> None:
    for path in (UNIFIED, CATALOG):
        if not path.exists():
            raise FileNotFoundError(path)

    with CATALOG.open() as f:
        catalog = json.load(f)
    pts = pd.DataFrame(
        [{"grid_lat": p["grid_lat"], "grid_lon": p["grid_lon"]} for p in catalog]
    )

    ds = xr.open_dataset(UNIFIED)
    times = pd.to_datetime(ds["time"].values)
    days_since_epoch = np.array(
        [(t.date() - REFERENCE_EPOCH).days for t in times], dtype=float
    )
    day_of_year = times.dayofyear.values.astype(float)

    # Vectorised point extraction: nearest native cell for each catalogue point.
    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in pts["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in pts["grid_lon"]],
        dims="point",
    )

    print(f"Extracting {len(pts)} coastal points from {UNIFIED.name} ...")
    zos = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values  # (time, point)
    ssh = ds["SSH_total"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    rows = []
    for i in range(len(pts)):
        z = zos[:, i].astype(float)
        s = ssh[:, i].astype(float)
        t = tide[:, i].astype(float)
        finite = np.isfinite(z) & np.isfinite(s) & np.isfinite(t)
        if finite.sum() < 1000:
            continue

        z_thr = np.nanquantile(z[finite], QUANTILE)
        s_thr = np.nanquantile(s[finite], QUANTILE)

        z_starts = episode_start_indices(np.where(finite, z >= z_thr, False), MAX_GAP_DAYS)
        s_starts = episode_start_indices(np.where(finite, s >= s_thr, False), MAX_GAP_DAYS)

        r_zos, p_zos = rayleigh_test(phase_angles_spring_neap(days_since_epoch[z_starts]))
        r_ssh, p_ssh = rayleigh_test(phase_angles_spring_neap(days_since_epoch[s_starts]))
        ann_angles = phase_angles_annual(day_of_year[z_starts])
        r_zos_ann, p_zos_ann = rayleigh_test(ann_angles)

        # Mean annual phase, expressed as the peak day-of-year: distinguishes a
        # winter storm-season signal (south) from a river-discharge signal
        # (Amazon sector, AUD-12), which peak in different months.
        if ann_angles.size >= MIN_EVENTS:
            mean_angle = np.arctan2(np.sin(ann_angles).mean(), np.cos(ann_angles).mean())
            peak_doy = float(np.mod(mean_angle, 2 * np.pi) / (2 * np.pi) * 365.25)
        else:
            peak_doy = float("nan")

        var_tide = float(np.nanvar(t[finite]))
        var_ssh = float(np.nanvar(s[finite]))
        var_zos = float(np.nanvar(z[finite]))

        rows.append(
            {
                "grid_lat": pts["grid_lat"][i],
                "grid_lon": pts["grid_lon"][i],
                "zos_q90_m": z_thr,
                "ssh_total_q90_m": s_thr,
                "tide_range_proxy_m": float(np.nanmax(t[finite]) - np.nanmin(t[finite])),
                "n_episodes_zos": int(z_starts.size),
                "n_episodes_ssh_total": int(s_starts.size),
                "rayleigh_R_zos_springneap": r_zos,
                "rayleigh_p_zos_springneap": p_zos,
                "rayleigh_R_ssh_total_springneap": r_ssh,
                "rayleigh_p_ssh_total_springneap": p_ssh,
                "rayleigh_R_zos_annual": r_zos_ann,
                "rayleigh_p_zos_annual": p_zos_ann,
                "zos_annual_peak_doy": peak_doy,
                "var_tide": var_tide,
                "var_zos": var_zos,
                "var_ssh_total": var_ssh,
                "var_ratio_tide_over_ssh": var_tide / var_ssh if var_ssh > 0 else np.nan,
            }
        )

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)
    df["sig_zos_springneap_p01"] = df["rayleigh_p_zos_springneap"] < 0.01
    df["sig_ssh_springneap_p01"] = df["rayleigh_p_ssh_total_springneap"] < 0.01
    df["sig_zos_annual_p01"] = df["rayleigh_p_zos_annual"] < 0.01

    band_rows = []
    for name, lo, hi in LATITUDE_BANDS:
        sub = df[df["latitude_band"] == name]
        if sub.empty:
            continue
        band_rows.append(
            {
                "band": name,
                "n_points": len(sub),
                "mean_zos_q90_m": sub["zos_q90_m"].mean(),
                "mean_ssh_total_q90_m": sub["ssh_total_q90_m"].mean(),
                "mean_var_ratio_tide_over_ssh": sub["var_ratio_tide_over_ssh"].mean(),
                "mean_R_ssh_springneap": sub["rayleigh_R_ssh_total_springneap"].mean(),
                "pct_sig_ssh_springneap": 100.0 * sub["sig_ssh_springneap_p01"].mean(),
                "mean_R_zos_springneap": sub["rayleigh_R_zos_springneap"].mean(),
                "pct_sig_zos_springneap": 100.0 * sub["sig_zos_springneap_p01"].mean(),
                "mean_R_zos_annual": sub["rayleigh_R_zos_annual"].mean(),
                "pct_sig_zos_annual": 100.0 * sub["sig_zos_annual_p01"].mean(),
                # Circular mean of the per-point annual peak, as a month (1-12).
                "zos_annual_peak_month": float(
                    np.mod(
                        np.arctan2(
                            np.sin(2 * np.pi * sub["zos_annual_peak_doy"] / 365.25).mean(),
                            np.cos(2 * np.pi * sub["zos_annual_peak_doy"] / 365.25).mean(),
                        ),
                        2 * np.pi,
                    )
                    / (2 * np.pi)
                    * 12.0
                    + 1.0
                ),
            }
        )
    by_band = pd.DataFrame(band_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "detector_comparison_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "detector_comparison_by_band.csv", index=False)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_zos_vs_ssh_total_detector",
        "quantile": QUANTILE,
        "max_gap_days": MAX_GAP_DAYS,
        "n_points": int(len(df)),
        "pct_sig_ssh_total_springneap_overall": float(100 * df["sig_ssh_springneap_p01"].mean()),
        "pct_sig_zos_springneap_overall": float(100 * df["sig_zos_springneap_p01"].mean()),
        "pct_sig_zos_annual_overall": float(100 * df["sig_zos_annual_p01"].mean()),
        "spearman_R_zos_vs_latitude": float(
            df["rayleigh_R_zos_springneap"].corr(df["grid_lat"], method="spearman")
        ),
        "spearman_R_ssh_vs_latitude": float(
            df["rayleigh_R_ssh_total_springneap"].corr(df["grid_lat"], method="spearman")
        ),
    }
    with (OUT_DIR / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    pd.set_option("display.width", 200)
    print(json.dumps(summary, indent=2))
    print()
    print(by_band.to_string(index=False))


if __name__ == "__main__":
    main()
