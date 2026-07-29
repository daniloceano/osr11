"""AUD-01 diagnostic: Rayleigh test of compound-event start dates against the
semi-synodic (spring-neap) period, per native ocean grid point.

Reproduces the central finding of the 2026-07-29 baseline scientific review
(docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md,
Sec. 3): whether `compound_events[].date_start` in
outputs/storm_catalog/compound/compound_catalog.json clusters in phase with
the 14.765294-day spring-neap tidal cycle, which would indicate the detector
is responding to astronomical tide rather than storm-driven surge.

This is a read-only diagnostic. It does not touch the production pipeline or
any published output.

Usage:
    python -m src.exploratory.audit_AUD_01_rayleigh_phase_test

Output:
    outputs/audit/AUD-01_rayleigh_phase_test/rayleigh_by_point.csv
    outputs/audit/AUD-01_rayleigh_phase_test/rayleigh_by_latitude_band.csv
    outputs/audit/AUD-01_rayleigh_phase_test/summary.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_rayleigh_phase_test"

#: Semi-synodic (spring-neap) period, days. Half the synodic month (29.530588 d).
SEMI_SYNODIC_PERIOD_DAYS = 14.765294

#: Reference new-moon epoch used by the baseline review (AUD-01 Sec. 7, item 3).
REFERENCE_EPOCH = date(1993, 1, 23)

#: Points with fewer events than this are dropped (unstable Rayleigh statistic).
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
    """Return (R, p) for the Rayleigh test of uniformity on a circle.

    p uses the standard higher-order correction (Mardia & Jupp, 2000, eq.
    6.3.6; Zar 1999), valid for the sample sizes present here (n >= 10).
    """
    n = angles_rad.size
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


def phase_angles(date_strings: list[str]) -> np.ndarray:
    days_since_epoch = np.array(
        [(date.fromisoformat(d) - REFERENCE_EPOCH).days for d in date_strings],
        dtype=float,
    )
    phase_fraction = np.mod(days_since_epoch, SEMI_SYNODIC_PERIOD_DAYS) / SEMI_SYNODIC_PERIOD_DAYS
    return 2 * np.pi * phase_fraction


def band_for_latitude(lat: float) -> str | None:
    for name, lo, hi in LATITUDE_BANDS:
        if lo <= lat < hi:
            return name
    return None


def main() -> None:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(f"Compound catalog not found: {CATALOG_PATH}")

    with CATALOG_PATH.open() as f:
        catalog = json.load(f)

    per_point_rows = []
    for point in catalog:
        events = point.get("compound_events", [])
        if len(events) < MIN_EVENTS:
            continue
        starts = [e["date_start"] for e in events]
        angles = phase_angles(starts)
        r, p = rayleigh_test(angles)
        per_point_rows.append(
            {
                "grid_lat": point["grid_lat"],
                "grid_lon": point["grid_lon"],
                "municipality": point.get("municipality"),
                "n_events": len(events),
                "thr_hs_abs": point.get("thr_hs_abs"),
                "thr_ssh_total_abs": point.get("thr_ssh_total_abs"),
                "rayleigh_R": r,
                "rayleigh_p": p,
                "significant_p01": p < 0.01,
            }
        )

    per_point = pd.DataFrame(per_point_rows).sort_values(
        ["grid_lat", "grid_lon"], ascending=[False, True]
    )
    per_point["latitude_band"] = per_point["grid_lat"].map(band_for_latitude)

    band_rows = []
    for name, lo, hi in LATITUDE_BANDS:
        subset = per_point[per_point["latitude_band"] == name]
        if subset.empty:
            continue
        band_rows.append(
            {
                "band": name,
                "lat_range": f"[{lo}, {hi})",
                "n_points": len(subset),
                "mean_R": subset["rayleigh_R"].mean(),
                "median_R": subset["rayleigh_R"].median(),
                "pct_significant_p01": 100.0 * subset["significant_p01"].mean(),
                "mean_thr_hs_abs": subset["thr_hs_abs"].mean(),
                "mean_thr_ssh_total_abs": subset["thr_ssh_total_abs"].mean(),
            }
        )
    by_band = pd.DataFrame(band_rows)

    spearman_R_lat = per_point["rayleigh_R"].corr(per_point["grid_lat"], method="spearman")
    spearman_R_thr_ssh = per_point["rayleigh_R"].corr(
        per_point["thr_ssh_total_abs"], method="spearman"
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    per_point.to_csv(OUT_DIR / "rayleigh_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "rayleigh_by_latitude_band.csv", index=False)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_rayleigh_phase_test",
        "source": str(CATALOG_PATH.relative_to(ROOT)),
        "reference_epoch": REFERENCE_EPOCH.isoformat(),
        "period_days": SEMI_SYNODIC_PERIOD_DAYS,
        "min_events_threshold": MIN_EVENTS,
        "n_points_total_in_catalog": len(catalog),
        "n_points_tested": int(len(per_point)),
        "pct_points_significant_p01_overall": float(100.0 * per_point["significant_p01"].mean()),
        "spearman_R_vs_latitude": float(spearman_R_lat),
        "spearman_R_vs_thr_ssh_total_abs": float(spearman_R_thr_ssh),
    }
    with (OUT_DIR / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print()
    print(by_band.to_string(index=False))


if __name__ == "__main__":
    main()
