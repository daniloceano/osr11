"""Local Hs and zos thresholds over the whole coast, for every grid percentile.

AUD-02 records that a ``thr_hs`` of 0.20 m is not defensible as an "extreme
wave" under any framing, and AUD-02 §8.3 asks for the sensitivity of the
selected pair to percentiles beyond q90. The Step 2e recalibration of
2026-07-30 extends the sweep grid to q95 and q99, so the question becomes
quantitative: how far does the wave-threshold floor rise across the 808
production points as the percentile rises?

This script answers exactly that, read-only. It computes, at each of the 808
coastal grid points and for each percentile of the new Step 2e grid:

    thr_hs  = local quantile of VHM0
    thr_zos = local quantile of zos
    HAT     = max(tide_daily_max) over 1993-2025

and reports the minimum, the percentile distribution, and the number of points
below the 1.0 m and 1.5 m marks that AUD-02 §3 uses.

Usage:
    conda run -n osr11 python -m src.exploratory.audit_AUD_02_threshold_grid_floor

Outputs:
    outputs/audit/AUD-02_threshold_grid_floor/thresholds_by_point.csv
    outputs/audit/AUD-02_threshold_grid_floor/thresholds_by_percentile.csv
    outputs/audit/AUD-02_threshold_grid_floor/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
POINT_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-02_threshold_grid_floor"

#: The Step 2e grid as of 2026-07-30.
PERCENTILES = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]
MIN_FINITE_DAYS = 1000
#: The two marks AUD-02 §3 counts points against.
FLOORS_M = (1.0, 1.5)


def main() -> None:
    points = pd.DataFrame(
        [
            {"grid_lat": p["grid_lat"], "grid_lon": p["grid_lon"]}
            for p in json.loads(POINT_SOURCE.read_text())
        ]
    )
    ds = xr.open_dataset(UNIFIED)
    lat_idx = xr.DataArray(
        [
            int(np.abs(ds["latitude"].values - value).argmin())
            for value in points["grid_lat"]
        ],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [
            int(np.abs(ds["longitude"].values - value).argmin())
            for value in points["grid_lon"]
        ],
        dims="point",
    )
    hs = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    ds.close()

    rows: list[dict] = []
    for index in range(len(points)):
        hs_series = hs[:, index].astype(float)
        zos_series = zos[:, index].astype(float)
        tide_series = tide[:, index].astype(float)
        finite = (
            np.isfinite(hs_series)
            & np.isfinite(zos_series)
            & np.isfinite(tide_series)
        )
        record: dict = {
            "grid_lat": float(points["grid_lat"][index]),
            "grid_lon": float(points["grid_lon"][index]),
            "n_finite_days": int(finite.sum()),
        }
        if finite.sum() < MIN_FINITE_DAYS:
            rows.append(record)
            continue
        record["hat_m"] = round(float(np.nanmax(tide_series[finite])), 6)
        for percentile in PERCENTILES:
            tag = f"{round(percentile * 100)}"
            record[f"thr_hs_q{tag}"] = round(
                float(np.nanquantile(hs_series[finite], percentile)), 6
            )
            record[f"thr_zos_q{tag}"] = round(
                float(np.nanquantile(zos_series[finite], percentile)), 6
            )
        rows.append(record)

    by_point = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_point.to_csv(OUT_DIR / "thresholds_by_point.csv", index=False)

    summary_rows: list[dict] = []
    for percentile in PERCENTILES:
        tag = f"{round(percentile * 100)}"
        column = by_point[f"thr_hs_q{tag}"].dropna()
        entry = {
            "percentile": percentile,
            "n_points": int(len(column)),
            "thr_hs_min_m": round(float(column.min()), 4),
            "thr_hs_p05_m": round(float(column.quantile(0.05)), 4),
            "thr_hs_median_m": round(float(column.median()), 4),
            "thr_hs_max_m": round(float(column.max()), 4),
        }
        for floor in FLOORS_M:
            entry[f"n_points_below_{floor:g}m"] = int((column < floor).sum())
        zos_column = by_point[f"thr_zos_q{tag}"].dropna()
        entry["thr_zos_min_m"] = round(float(zos_column.min()), 4)
        entry["thr_zos_median_m"] = round(float(zos_column.median()), 4)
        summary_rows.append(entry)

    by_percentile = pd.DataFrame(summary_rows)
    by_percentile.to_csv(OUT_DIR / "thresholds_by_percentile.csv", index=False)

    hat = by_point["hat_m"].dropna()
    summary = {
        "generated_by": "src.exploratory.audit_AUD_02_threshold_grid_floor",
        "question": (
            "How far does the local Hs threshold floor rise across the 808 "
            "production grid points as the Step 2e percentile grid is extended "
            "to q95 and q99?"
        ),
        "n_points": int(len(by_point)),
        "percentiles": PERCENTILES,
        "aud_02_reference": {
            "published_thr_hs_min_m": 0.20,
            "published_points_below_1m": 35,
            "published_points_below_1_5m": 129,
            "note": (
                "AUD-02 §3 values, computed at q90 on the published "
                "compound_metrics.csv of the SSH_total method."
            ),
        },
        "by_percentile": by_percentile.to_dict("records"),
        "hat_m": {
            "min": round(float(hat.min()), 4),
            "median": round(float(hat.median()), 4),
            "max": round(float(hat.max()), 4),
        },
    }
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    print(by_percentile.to_string(index=False))


if __name__ == "__main__":
    main()
