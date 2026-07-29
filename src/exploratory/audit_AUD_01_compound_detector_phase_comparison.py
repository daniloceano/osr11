"""AUD-01 diagnostic: does a `zos`-based COMPOUND detector still inherit
spring-neap phase locking through the wave component?

The previous diagnostic
(`audit_AUD_01_zos_vs_ssh_total_detector.py`) showed that LEVEL episodes
detected on `zos` carry no spring-neap phase locking (0 of 808 points), while
`SSH_total` episodes do (98.4 %). That leaves one path by which a redesigned
detector could still be tide-driven: if the WAVE episodes themselves were
phase-locked — plausible a priori, since wave height in shallow macrotidal
water can be modulated by tidal depth and tidal currents — then the
intersection (compound event) would remain locked even with a tide-free level
variable.

This script closes that gap. At each of the 808 native coastal points it:

1. detects Hs episodes with the production recipe (local q90, gap <= 1 day) and
   Rayleigh-tests their start dates against the spring-neap cycle;
2. builds compound events two ways — Hs from Hs, level from `SSH_total`
   (reproduces production) and level from `zos` (the proposed redesign) —
   using overlap of at least one shared calendar day, with the compound start
   date taken as the first shared day, mirroring
   `02_compound_detection/detection.py` (`date_start = overlap[0]`);
3. Rayleigh-tests both compound event sets against the spring-neap cycle.

Grouping simplification: production merges episodes union-find style, so one
compound group may span several Hs and level episodes with a non-contiguous
overlap day set. Here each contiguous run of shared days is one compound
event. This can split a merged production group into more than one event. The
`SSH_total` arm is therefore validated against the production catalogue counts,
and both arms use the identical rule, so the comparison between them is exact.

Read-only diagnostic. Does not modify the production pipeline or any published
output.

Usage:
    python -m src.exploratory.audit_AUD_01_compound_detector_phase_comparison

Output:
    outputs/audit/AUD-01_compound_detector_phase_comparison/compound_phase_by_point.csv
    outputs/audit/AUD-01_compound_detector_phase_comparison/compound_phase_by_band.csv
    outputs/audit/AUD-01_compound_detector_phase_comparison/summary.json
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
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_compound_detector_phase_comparison"

SEMI_SYNODIC_PERIOD_DAYS = 14.765294
REFERENCE_EPOCH = date(1993, 1, 23)
QUANTILE = 0.90
MAX_GAP_DAYS = 1
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


def episode_mask(series: np.ndarray, finite: np.ndarray, max_gap: int) -> np.ndarray:
    """Boolean day mask of episodes: exceedance runs bridged across <= max_gap gaps."""
    thr = np.nanquantile(series[finite], QUANTILE)
    exceeds = np.where(finite, series >= thr, False)
    idx = np.flatnonzero(exceeds)
    if idx.size == 0:
        return exceeds
    mask = exceeds.copy()
    # Bridge internal gaps of at most max_gap days, matching the clustering rule.
    gaps = np.diff(idx)
    for k in np.flatnonzero((gaps > 1) & (gaps <= max_gap + 1)):
        mask[idx[k] : idx[k + 1] + 1] = True
    return mask


def run_starts(mask: np.ndarray) -> np.ndarray:
    """Start indices of contiguous True runs."""
    if not mask.any():
        return np.empty(0, dtype=int)
    padded = np.concatenate(([False], mask))
    return np.flatnonzero(~padded[:-1] & mask)


def phase_angles(days_since_epoch: np.ndarray) -> np.ndarray:
    frac = np.mod(days_since_epoch, SEMI_SYNODIC_PERIOD_DAYS) / SEMI_SYNODIC_PERIOD_DAYS
    return 2 * np.pi * frac


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
        [
            {
                "grid_lat": p["grid_lat"],
                "grid_lon": p["grid_lon"],
                "production_compound_count": p["compound_count_total"],
            }
            for p in catalog
        ]
    )

    ds = xr.open_dataset(UNIFIED)
    times = pd.to_datetime(ds["time"].values)
    days_since_epoch = np.array(
        [(t.date() - REFERENCE_EPOCH).days for t in times], dtype=float
    )

    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in pts["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in pts["grid_lon"]],
        dims="point",
    )

    print(f"Extracting {len(pts)} coastal points ...")
    hs = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    ssh = ds["SSH_total"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    rows = []
    for i in range(len(pts)):
        h = hs[:, i].astype(float)
        z = zos[:, i].astype(float)
        s = ssh[:, i].astype(float)
        finite = np.isfinite(h) & np.isfinite(z) & np.isfinite(s)
        if finite.sum() < 1000:
            continue

        m_hs = episode_mask(h, finite, MAX_GAP_DAYS)
        m_zos = episode_mask(z, finite, MAX_GAP_DAYS)
        m_ssh = episode_mask(s, finite, MAX_GAP_DAYS)

        # Compound = shared calendar days between a wave episode and a level episode.
        comp_zos = m_hs & m_zos
        comp_ssh = m_hs & m_ssh

        st_hs = run_starts(m_hs)
        st_comp_zos = run_starts(comp_zos)
        st_comp_ssh = run_starts(comp_ssh)

        r_hs, p_hs = rayleigh_test(phase_angles(days_since_epoch[st_hs]))
        r_cz, p_cz = rayleigh_test(phase_angles(days_since_epoch[st_comp_zos]))
        r_cs, p_cs = rayleigh_test(phase_angles(days_since_epoch[st_comp_ssh]))

        rows.append(
            {
                "grid_lat": pts["grid_lat"][i],
                "grid_lon": pts["grid_lon"][i],
                "production_compound_count": pts["production_compound_count"][i],
                "n_episodes_hs": int(st_hs.size),
                "n_compound_zos": int(st_comp_zos.size),
                "n_compound_ssh_total": int(st_comp_ssh.size),
                "rayleigh_R_hs": r_hs,
                "rayleigh_p_hs": p_hs,
                "rayleigh_R_compound_zos": r_cz,
                "rayleigh_p_compound_zos": p_cz,
                "rayleigh_R_compound_ssh_total": r_cs,
                "rayleigh_p_compound_ssh_total": p_cs,
            }
        )

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)
    df["sig_hs"] = df["rayleigh_p_hs"] < 0.01
    df["sig_compound_zos"] = df["rayleigh_p_compound_zos"] < 0.01
    df["sig_compound_ssh"] = df["rayleigh_p_compound_ssh_total"] < 0.01

    band_rows = []
    for name, lo, hi in LATITUDE_BANDS:
        sub = df[df["latitude_band"] == name]
        if sub.empty:
            continue
        band_rows.append(
            {
                "band": name,
                "n_points": len(sub),
                "mean_R_hs": sub["rayleigh_R_hs"].mean(),
                "pct_sig_hs": 100.0 * sub["sig_hs"].mean(),
                "mean_R_comp_ssh": sub["rayleigh_R_compound_ssh_total"].mean(),
                "pct_sig_comp_ssh": 100.0 * sub["sig_compound_ssh"].mean(),
                "mean_R_comp_zos": sub["rayleigh_R_compound_zos"].mean(),
                "pct_sig_comp_zos": 100.0 * sub["sig_compound_zos"].mean(),
                "n_comp_ssh": sub["n_compound_ssh_total"].mean(),
                "n_comp_zos": sub["n_compound_zos"].mean(),
                "n_comp_production": sub["production_compound_count"].mean(),
            }
        )
    by_band = pd.DataFrame(band_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "compound_phase_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "compound_phase_by_band.csv", index=False)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_compound_detector_phase_comparison",
        "quantile": QUANTILE,
        "max_gap_days": MAX_GAP_DAYS,
        "n_points": int(len(df)),
        "pct_sig_hs_springneap": float(100 * df["sig_hs"].mean()),
        "pct_sig_compound_ssh_total_springneap": float(100 * df["sig_compound_ssh"].mean()),
        "pct_sig_compound_zos_springneap": float(100 * df["sig_compound_zos"].mean()),
        "mean_R_hs": float(df["rayleigh_R_hs"].mean()),
        "mean_R_compound_ssh_total": float(df["rayleigh_R_compound_ssh_total"].mean()),
        "mean_R_compound_zos": float(df["rayleigh_R_compound_zos"].mean()),
        "validation_vs_production": {
            "note": (
                "Simplified contiguous-run grouping vs production union-find; "
                "counts are expected to be close but not identical."
            ),
            "spearman_count_ssh_arm_vs_production": float(
                df["n_compound_ssh_total"].corr(
                    df["production_compound_count"], method="spearman"
                )
            ),
            "mean_count_ssh_arm": float(df["n_compound_ssh_total"].mean()),
            "mean_count_production": float(df["production_compound_count"].mean()),
        },
    }
    with (OUT_DIR / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    pd.set_option("display.width", 220)
    print(json.dumps(summary, indent=2))
    print()
    print(by_band.to_string(index=False))


if __name__ == "__main__":
    main()
