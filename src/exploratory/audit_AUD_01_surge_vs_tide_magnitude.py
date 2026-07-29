"""AUD-01 / AUD-02 diagnostic: how large is the meteorological surge compared
with the astronomical tide, in absolute (physical) terms?

Motivated by the impact-physics framing: coastal damage occurs when the total
water level crosses a physical elevation (berm, dune crest, defence crest).
Under that framing the question is not which component is "rare" but which
component can actually move the total level across such a threshold.

For each of the 808 native coastal grid points this quantifies, in centimetres:

* the surge anomaly at the q90 detection threshold — what a `zos`-based
  detector would call an "event";
* the surge anomaly at q99 — a genuinely extreme surge;
* the spring-neap modulation of daily high water, i.e. the range of
  `tide_daily_max`, which is how much the astronomical tide alone moves the
  daily maximum level between neap and spring;
* the seasonal amplitude of `zos` (first two annual harmonics) and the
  synoptic residual standard deviation, to separate low-frequency from
  synoptic-band variability.

The decision-relevant ratio is surge(q99) / spring-neap swing: where it
approaches or exceeds 1, the surge genuinely competes with the tide in setting
the total level and a compound surge-wave event is physically meaningful; where
it is a few per cent, whether the level crosses a given elevation is decided by
the tide and the meteorological contribution is a perturbation.

Read-only diagnostic. Does not modify the production pipeline or any published
output.

Usage:
    python -m src.exploratory.audit_AUD_01_surge_vs_tide_magnitude

Output:
    outputs/audit/AUD-01_surge_vs_tide_magnitude/surge_vs_tide_by_point.csv
    outputs/audit/AUD-01_surge_vs_tide_magnitude/surge_vs_tide_by_band.csv
    outputs/audit/AUD-01_surge_vs_tide_magnitude/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
CATALOG = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_surge_vs_tide_magnitude"

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


def seasonal_amplitude(values: np.ndarray, doy: np.ndarray) -> tuple[float, np.ndarray]:
    """Peak-to-peak amplitude of the first two annual harmonics, and the
    day-of-year climatology used to build the synoptic residual."""
    series = pd.Series(values)
    clim_by_doy = series.groupby(doy).mean()
    d = clim_by_doy.index.values.astype(float)
    y = clim_by_doy.values
    design = np.column_stack(
        [np.ones_like(d)]
        + [fn(2 * np.pi * k * d / 365.25) for k in (1, 2) for fn in (np.sin, np.cos)]
    )
    ok = np.isfinite(y)
    beta = np.linalg.lstsq(design[ok], y[ok], rcond=None)[0]
    fit = design @ beta
    climatology = series.groupby(doy).transform("mean").values
    return float(np.nanmax(fit) - np.nanmin(fit)), climatology


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
    doy = pd.to_datetime(ds["time"].values).dayofyear.values

    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in pts["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in pts["grid_lon"]],
        dims="point",
    )

    print(f"Extracting {len(pts)} coastal points ...")
    zos = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    rows = []
    for i in range(len(pts)):
        z = zos[:, i].astype(float)
        t = tide[:, i].astype(float)
        finite = np.isfinite(z) & np.isfinite(t)
        if finite.sum() < 1000:
            continue

        zf = np.where(finite, z, np.nan)
        mean_z = float(np.nanmean(zf))
        seas_amp, clim = seasonal_amplitude(zf, doy)
        resid_std = float(np.nanstd(zf - clim))

        surge_q90 = float(np.nanquantile(zf, 0.90) - mean_z)
        surge_q99 = float(np.nanquantile(zf, 0.99) - mean_z)
        swing = float(np.nanmax(t[finite]) - np.nanmin(t[finite]))

        rows.append(
            {
                "grid_lat": pts["grid_lat"][i],
                "grid_lon": pts["grid_lon"][i],
                "surge_q90_anomaly_cm": 100 * surge_q90,
                "surge_q99_anomaly_cm": 100 * surge_q99,
                "springneap_swing_cm": 100 * swing,
                "surge_q99_over_swing": surge_q99 / swing if swing > 0 else np.nan,
                "zos_seasonal_amplitude_cm": 100 * seas_amp,
                "zos_synoptic_residual_std_cm": 100 * resid_std,
                "seasonal_over_synoptic": seas_amp / resid_std if resid_std > 0 else np.nan,
            }
        )

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)

    agg = {
        "surge_q90_anomaly_cm": "mean",
        "surge_q99_anomaly_cm": "mean",
        "springneap_swing_cm": "mean",
        "surge_q99_over_swing": "mean",
        "zos_seasonal_amplitude_cm": "mean",
        "zos_synoptic_residual_std_cm": "mean",
        "seasonal_over_synoptic": "mean",
    }
    by_band = (
        df.groupby("latitude_band", observed=True)
        .agg(agg)
        .reindex([b[0] for b in LATITUDE_BANDS])
        .dropna(how="all")
        .reset_index()
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "surge_vs_tide_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "surge_vs_tide_by_band.csv", index=False)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_surge_vs_tide_magnitude",
        "n_points": int(len(df)),
        "interpretation": (
            "surge_q99_over_swing near or above 1 means the meteorological surge "
            "competes with the astronomical tide in setting the total water level; "
            "a few per cent means the tide decides whether a given elevation is "
            "crossed and the surge is a perturbation."
        ),
        "surge_q99_over_swing_min": float(df["surge_q99_over_swing"].min()),
        "surge_q99_over_swing_max": float(df["surge_q99_over_swing"].max()),
        "spearman_ratio_vs_latitude": float(
            df["surge_q99_over_swing"].corr(df["grid_lat"], method="spearman")
        ),
    }
    with (OUT_DIR / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    pd.set_option("display.width", 220)
    print(json.dumps(summary, indent=2))
    print()
    print(by_band.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
