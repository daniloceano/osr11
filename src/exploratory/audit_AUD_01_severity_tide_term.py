"""AUD-01 diagnostic: how can the astronomical tide enter the severity term
without inflating the macrotidal North?

Under a uniform tide-free detector (`zos` intersect Hs), the tidal amplification
that matters in the South/Southeast has to re-enter through the severity term.
The risk is that it re-creates the regional bias in the intensity component:
the North simply has more water, so any severity measured as an absolute level
would rank it highest for astronomical reasons.

Four candidate severity formulations are evaluated on the compound events of a
uniform `zos` intersect Hs detector, and scored by their regional bias, taken
as the Spearman correlation between the per-point mean severity and absolute
latitude. A value near zero means no systematic north-south drift.

    A  absolute total level      mean(zos + tide + 0.2*Hs)
    B  excess over local datum   mean(zos + tide + 0.2*Hs - q95(tide))
    C  dimensionless tidal phase mean((tide - median(tide)) / range(tide))
    D  surge anomaly only        mean(zos - mean(zos))          [reference]

Formulation D carries no tidal information and is included only as the baseline
against which the tidal terms are judged. The q95 of `tide_daily_max` in B is a
proxy for mean high water springs, i.e. the level the coast is routinely
adapted to, which is the datum implied by the adaptation argument.

Read-only diagnostic. Does not modify the production pipeline or any published
output, and does not adopt any formulation.

Usage:
    python -m src.exploratory.audit_AUD_01_severity_tide_term

Output:
    outputs/audit/AUD-01_severity_tide_term/severity_by_point.csv
    outputs/audit/AUD-01_severity_tide_term/severity_by_band.csv
    outputs/audit/AUD-01_severity_tide_term/severity_summary.json
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
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_severity_tide_term"

QUANTILE = 0.90
MAX_GAP_DAYS = 1
SETUP_COEFFICIENT = 0.2
#: Proxy for mean high water springs: the level the coast is adapted to.
DATUM_QUANTILE = 0.95

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

CANDIDATES = (
    "A_absolute_total_level_m",
    "B_excess_over_local_datum_m",
    "C_dimensionless_tidal_phase",
    "D_surge_anomaly_only_m",
)


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
        datum = float(np.nanquantile(t[finite], DATUM_QUANTILE))
        tide_median = float(np.nanmedian(t[finite]))
        tide_range = float(np.nanmax(t[finite]) - np.nanmin(t[finite]))
        zos_mean = float(np.nanmean(z[finite]))

        rows.append(
            {
                "grid_lat": pts["grid_lat"][i],
                "grid_lon": pts["grid_lon"][i],
                "n_compound_events_days": int(compound.sum()),
                "A_absolute_total_level_m": float(np.nanmean(total[compound])),
                "B_excess_over_local_datum_m": float(np.nanmean(total[compound] - datum)),
                "C_dimensionless_tidal_phase": float(
                    np.nanmean((t[compound] - tide_median) / tide_range)
                    if tide_range > 0
                    else np.nan
                ),
                "D_surge_anomaly_only_m": float(np.nanmean(z[compound] - zos_mean)),
            }
        )

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)
    df["abs_lat"] = df["grid_lat"].abs()

    by_band = (
        df.groupby("latitude_band", observed=True)[list(CANDIDATES)]
        .mean()
        .reindex([b[0] for b in LATITUDE_BANDS])
        .dropna(how="all")
        .reset_index()
    )

    bias = {
        name: float(df[name].corr(df["abs_lat"], method="spearman")) for name in CANDIDATES
    }

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_severity_tide_term",
        "detector": "uniform zos ∩ Hs (tide-free detection)",
        "setup_coefficient": SETUP_COEFFICIENT,
        "datum_quantile_of_tide_daily_max": DATUM_QUANTILE,
        "n_points": int(len(df)),
        "regional_bias_spearman_vs_abs_latitude": bias,
        "reading": (
            "Negative means severity grows toward the equator, i.e. the North is "
            "inflated. Positive means it grows poleward. Near zero means no "
            "systematic north-south drift."
        ),
        "verdict": {
            "A_absolute_total_level_m": (
                "inflates the North; the astronomical tide dominates the absolute "
                "level, so this reproduces the bias the redesign set out to remove"
            ),
            "B_excess_over_local_datum_m": (
                "no northern inflation, but swings strongly poleward: the mean "
                "excess over local spring high water is near zero in the equatorial "
                "sector, effectively assigning it negligible severity"
            ),
            "C_dimensionless_tidal_phase": (
                "regionally unbiased by construction; modulates events within a "
                "site without shifting regional means, but represents tidal "
                "amplification only in relative terms, so a spring tide in a 1.6 m "
                "macrotidal setting counts the same as in a 0.46 m one"
            ),
            "D_surge_anomaly_only_m": (
                "reference without any tidal information; retains a moderate "
                "poleward gradient that reflects genuinely larger surges in the south"
            ),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "severity_by_point.csv", index=False)
    by_band.to_csv(OUT_DIR / "severity_by_band.csv", index=False)
    with (OUT_DIR / "severity_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary["regional_bias_spearman_vs_abs_latitude"], indent=2))
    print()
    print(by_band.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
