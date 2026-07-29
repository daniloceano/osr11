"""AUD-01 diagnostic: how sensitive is the excess-over-datum severity to the
choice of tidal datum?

The "excess of water" severity formulation scores an event by how far the total
water level rose above a local reference representing the level the coast
already reaches routinely. That reference has to be chosen, which reopens the
arbitrariness objection recorded in AUD-02 §7.4 — although in a much weaker
form, because the candidates are conventional tidal datums rather than a freely
invented number:

    q90  of tide_daily_max   permissive proxy of spring high water
    q95  of tide_daily_max   proxy of mean high water springs (current default)
    q99  of tide_daily_max   proxy of the higher spring tides
    max  of tide_daily_max   estimate of HAT, the highest astronomical tide,
                             which is a defined engineering datum with no
                             percentile choice at all

The concern is quantitative: in the macrotidal North the spring-neap swing is
about 1.6 m while the storm contribution is about 0.12 m, so a datum shift of a
few centimetres is comparable to the entire signal being measured. This script
therefore recomputes the severity under each datum and reports whether the
qualitative conclusion — that the northern sector scores near zero — survives
the choice, or depends on it.

Read-only diagnostic. Does not modify the production pipeline or any published
output.

Usage:
    python -m src.exploratory.audit_AUD_01_datum_sensitivity

Output:
    outputs/audit/AUD-01_datum_sensitivity/datum_sensitivity_by_point.csv
    outputs/audit/AUD-01_datum_sensitivity/datum_sensitivity_by_band.csv
    outputs/audit/AUD-01_datum_sensitivity/datum_sensitivity_summary.json
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
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_datum_sensitivity"

QUANTILE = 0.90
MAX_GAP_DAYS = 1
SETUP_COEFFICIENT = 0.2

#: label -> quantile of tide_daily_max used as the datum. 1.0 estimates HAT.
DATUMS = {
    "q90_permissive": 0.90,
    "q95_MHWS_proxy": 0.95,
    "q99_high_springs": 0.99,
    "max_HAT_estimate": 1.00,
}

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


def episode_mask(series: np.ndarray, finite: np.ndarray) -> np.ndarray:
    thr = np.nanquantile(series[finite], QUANTILE)
    exceeds = np.where(finite, series >= thr, False)
    idx = np.flatnonzero(exceeds)
    if idx.size == 0:
        return exceeds
    mask = exceeds.copy()
    gaps = np.diff(idx)
    for k in np.flatnonzero((gaps > 1) & (gaps <= MAX_GAP_DAYS + 1)):
        mask[idx[k] : idx[k + 1] + 1] = True
    return mask


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
    tide = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    rows = []
    for i in range(len(pts)):
        h = hs[:, i].astype(float)
        z = zos[:, i].astype(float)
        t = tide[:, i].astype(float)
        finite = np.isfinite(h) & np.isfinite(z) & np.isfinite(t)
        if finite.sum() < 1000:
            continue

        compound = episode_mask(h, finite) & episode_mask(z, finite)
        if not compound.any():
            continue

        total = z + t + SETUP_COEFFICIENT * h
        record = {
            "grid_lat": pts["grid_lat"][i],
            "grid_lon": pts["grid_lon"][i],
            "springneap_swing_m": float(np.nanmax(t[finite]) - np.nanmin(t[finite])),
        }
        for label, q in DATUMS.items():
            datum = float(np.nanquantile(t[finite], q))
            record[f"datum_{label}_m"] = datum
            record[f"excess_{label}_m"] = float(np.nanmean(total[compound] - datum))
            record[f"pct_events_above_datum_{label}"] = float(
                100 * np.nanmean(total[compound] > datum)
            )
        rows.append(record)

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)
    df["abs_lat"] = df["grid_lat"].abs()

    excess_cols = [f"excess_{label}_m" for label in DATUMS]
    pct_cols = [f"pct_events_above_datum_{label}" for label in DATUMS]

    by_band = (
        df.groupby("latitude_band", observed=True)[excess_cols + pct_cols]
        .mean()
        .reindex([b[0] for b in LATITUDE_BANDS])
        .dropna(how="all")
        .reset_index()
    )

    north = df[df["grid_lat"] > -15]
    south = df[df["grid_lat"] < -25]

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_datum_sensitivity",
        "detector": "uniform zos ∩ Hs (tide-free detection)",
        "datums_tested": DATUMS,
        "n_points": int(len(df)),
        "regional_bias_spearman_vs_abs_latitude": {
            col: float(df[col].corr(df["abs_lat"], method="spearman"))
            for col in excess_cols
        },
        "mean_excess_north_of_15S_m": {
            col: float(north[col].mean()) for col in excess_cols
        },
        "mean_excess_south_of_25S_m": {
            col: float(south[col].mean()) for col in excess_cols
        },
        "south_to_north_contrast": {
            col: (
                float(south[col].mean() - north[col].mean()) for col in [col]
            ).__next__()
            for col in excess_cols
        },
        "robustness_question": (
            "Does the qualitative conclusion — northern severity near zero and a "
            "strong poleward gradient — hold for every datum, or does it depend "
            "on the percentile chosen?"
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "datum_sensitivity_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "datum_sensitivity_by_band.csv", index=False)
    with (OUT_DIR / "datum_sensitivity_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    pd.set_option("display.width", 220)
    print(json.dumps(summary["regional_bias_spearman_vs_abs_latitude"], indent=2))
    print()
    print("Excesso medio por faixa (m), por escolha de datum:")
    print(by_band[["latitude_band"] + excess_cols].round(3).to_string(index=False))
    print()
    print("Percentual de eventos acima do datum:")
    print(by_band[["latitude_band"] + pct_cols].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
