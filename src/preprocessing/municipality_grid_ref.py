"""
Preprocessing script: municipality → nearest valid grid point reference table.

This script resolves each unique municipality in the reported-events database to
its nearest ocean grid point in the unified metocean dataset, and assesses data
coverage (valid fraction over the full time series) for each matched point.

The output CSV is used as the primary municipality→grid reference for all
subsequent analysis steps (STEP3 tidal sensitivity, STEP4 threshold calibration),
replacing the single-time-step validity check previously used inside
``build_event_records``.

Output
------
    outputs/preprocessing/municipality_grid_ref.csv

Columns:
    municipality    : municipality name (as in reported_events_Karine_sc.csv)
    muni_lat        : approximate coastal latitude (from hardcoded lookup)
    muni_lon        : approximate coastal longitude
    grid_lat        : matched grid point latitude (nearest with sufficient coverage)
    grid_lon        : matched grid point longitude
    grid_dist_km    : distance from municipality coords to matched grid point (km)
    hs_valid_frac   : fraction of non-NaN time steps for VHM0 at the matched point
    ssh_valid_frac  : fraction of non-NaN time steps for zos at the matched point
    data_quality    : 'ok' if both fractions ≥ MIN_VALID_FRACTION, else 'insufficient_data'
    coord_source    : 'hardcoded' (only source currently implemented here)

Usage
-----
Run from project root::

    python src/preprocessing/municipality_grid_ref.py

Re-run whenever the unified dataset or the reported-events CSV changes.

Notes
-----
This script must be run before any analysis step that relies on the
preprocessing reference.  If the reference is absent, ``build_event_records``
falls back to the Part E table or hardcoded coordinates with a single-time-step
validity check.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# ── Project root on sys.path ────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ── Paths ───────────────────────────────────────────────────────────────────────
UNIFIED_FILE = _ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc"
EVENTS_FILE  = _ROOT / "data/reported events/reported_events_Karine_sc.csv"
OUTPUT_DIR   = _ROOT / "outputs/preprocessing"
OUTPUT_FILE  = OUTPUT_DIR / "municipality_grid_ref.csv"

# Variable names in the unified dataset
HS_VAR  = "VHM0"
SSH_VAR = "zos"

# Minimum fraction of non-NaN time steps required at the matched grid point
# for BOTH HS_VAR and SSH_VAR.  Points below this threshold are flagged as
# 'insufficient_data' and the next nearest sufficient point is used if available.
MIN_VALID_FRACTION: float = 0.80

# ── Hardcoded coastal positions for all SC municipalities ────────────────────────
# Source: approximate coastal centroid from IBGE / OpenStreetMap.
# Identical to _SOUTH_SC_COORDS in src/02_preliminary_compound/events.py.
_SOUTH_SC_COORDS: dict[str, tuple[float, float]] = {
    # South sector
    "Araranguá":                     (-28.94, -49.50),
    "Balneário Arroio do Silva":     (-28.97, -49.40),
    "Balneário Gaivota":             (-29.17, -49.56),
    "Balneário Rincão":              (-28.84, -49.23),
    "Içara":                         (-28.71, -49.30),
    "Içara/Balneário Rincão":        (-28.84, -49.23),
    "Garopaba":                      (-28.02, -48.62),
    "Laguna":                        (-28.48, -48.77),
    "Passo de Torres":               (-29.36, -49.73),
    "Jaguaruna":                     (-28.61, -49.02),
    "Imbituba":                      (-28.23, -48.67),
    # Central sector
    "Florianópolis":                 (-27.60, -48.55),
    "Palhoça":                       (-27.65, -48.67),
    "Tijucas":                       (-27.24, -48.64),
    # Central-north sector
    "Bombinhas":                     (-27.13, -48.50),
    "Porto Belo":                    (-27.16, -48.54),
    "Itapema":                       (-27.09, -48.61),
    "Balneário Camboriú":            (-26.99, -48.63),
    "Navegantes":                    (-26.90, -48.65),
    "Itajaí":                        (-26.91, -48.66),
    "Penha":                         (-26.77, -48.65),
    "Balneário Piçarras":            (-26.77, -48.66),
    # North sector
    "Barra Velha":                   (-26.63, -48.68),
    "Balneário Barra do Sul":        (-26.46, -48.60),
    "Araquari":                      (-26.37, -48.72),
    "São Francisco do Sul":          (-26.24, -48.64),
    "Itapoá":                        (-26.11, -48.62),
}


def build_reference_table(
    ds: xr.Dataset,
    municipalities: list[str],
) -> pd.DataFrame:
    """Build the municipality → grid reference table.

    For each municipality, finds the nearest grid point with sufficient valid
    data (both HS_VAR and SSH_VAR non-NaN for ≥ MIN_VALID_FRACTION of time steps).

    Parameters
    ----------
    ds : xr.Dataset
        Unified daily metocean dataset.
    municipalities : list[str]
        Unique municipality names from the reported-events CSV.

    Returns
    -------
    pd.DataFrame with one row per municipality.
    """
    lat_grid = ds.latitude.values
    lon_grid = ds.longitude.values

    # Compute valid fraction over the full time series once for all grid points.
    log.info("Computing valid-data fraction over full time series for all grid points...")
    hs_valid_frac_grid  = (~np.isnan(ds[HS_VAR].values)).mean(axis=0)   # shape (lat, lon)
    ssh_valid_frac_grid = (~np.isnan(ds[SSH_VAR].values)).mean(axis=0)
    both_sufficient     = (
        (hs_valid_frac_grid  >= MIN_VALID_FRACTION) &
        (ssh_valid_frac_grid >= MIN_VALID_FRACTION)
    )

    n_sufficient = int(both_sufficient.sum())
    log.info(
        "  Grid points with ≥%.0f%% valid data: %d / %d",
        MIN_VALID_FRACTION * 100, n_sufficient, both_sufficient.size,
    )

    rows = []
    for muni in municipalities:
        muni_lat, muni_lon = _SOUTH_SC_COORDS.get(muni, (np.nan, np.nan))

        if np.isnan(muni_lat):
            log.warning("  No hardcoded coordinates for '%s' — skipping.", muni)
            continue

        grid_lat, grid_lon, dist_km, hs_frac, ssh_frac = _find_best_grid_point(
            lat_grid, lon_grid,
            hs_valid_frac_grid, ssh_valid_frac_grid, both_sufficient,
            muni_lat, muni_lon,
        )

        quality = (
            "ok" if (hs_frac >= MIN_VALID_FRACTION and ssh_frac >= MIN_VALID_FRACTION)
            else "insufficient_data"
        )
        if quality == "insufficient_data":
            log.warning(
                "  %-30s → (%.4f, %.4f)  dist=%.1f km  "
                "Hs_valid=%.1f%%  SSH_valid=%.1f%%  [INSUFFICIENT DATA]",
                muni, grid_lat, grid_lon, dist_km,
                hs_frac * 100, ssh_frac * 100,
            )
        else:
            log.info(
                "  %-30s → (%.4f, %.4f)  dist=%.1f km  "
                "Hs_valid=%.1f%%  SSH_valid=%.1f%%",
                muni, grid_lat, grid_lon, dist_km,
                hs_frac * 100, ssh_frac * 100,
            )

        rows.append({
            "municipality":   muni,
            "muni_lat":       muni_lat,
            "muni_lon":       muni_lon,
            "grid_lat":       grid_lat,
            "grid_lon":       grid_lon,
            "grid_dist_km":   round(dist_km, 2),
            "hs_valid_frac":  round(float(hs_frac),  4),
            "ssh_valid_frac": round(float(ssh_frac), 4),
            "data_quality":   quality,
            "coord_source":   "hardcoded",
        })

    return pd.DataFrame(rows)


def _find_best_grid_point(
    lat_grid: np.ndarray,
    lon_grid: np.ndarray,
    hs_valid_frac_grid: np.ndarray,
    ssh_valid_frac_grid: np.ndarray,
    both_sufficient: np.ndarray,
    target_lat: float,
    target_lon: float,
) -> tuple[float, float, float, float, float]:
    """Return (grid_lat, grid_lon, dist_km, hs_frac, ssh_frac) for the best point.

    'Best' means nearest point in ``both_sufficient``.  If no point satisfies
    the threshold, falls back to the globally nearest point regardless of coverage.
    """
    candidate_mask = both_sufficient

    # If no point passes the threshold, fall back to the nearest point overall
    if not candidate_mask.any():
        log.warning(
            "  No grid point meets the %.0f%% validity threshold — "
            "using nearest point regardless of coverage.",
            MIN_VALID_FRACTION * 100,
        )
        candidate_mask = np.ones_like(both_sufficient, dtype=bool)

    min_dist = np.inf
    best_i, best_j = 0, 0
    for i, lat_g in enumerate(lat_grid):
        for j, lon_g in enumerate(lon_grid):
            if candidate_mask[i, j]:
                dist = (lat_g - target_lat) ** 2 + (lon_g - target_lon) ** 2
                if dist < min_dist:
                    min_dist = dist
                    best_i, best_j = i, j

    grid_lat = float(lat_grid[best_i])
    grid_lon = float(lon_grid[best_j])
    dist_km  = float(np.sqrt(min_dist)) * 111.0
    hs_frac  = float(hs_valid_frac_grid[best_i, best_j])
    ssh_frac = float(ssh_valid_frac_grid[best_i, best_j])
    return grid_lat, grid_lon, dist_km, hs_frac, ssh_frac


def main() -> None:
    log.info("=" * 68)
    log.info("OSR11 — Preprocessing: municipality–grid reference table")
    log.info("Input  (unified): %s", UNIFIED_FILE)
    log.info("Input  (events) : %s", EVENTS_FILE)
    log.info("Output          : %s", OUTPUT_FILE)
    log.info("=" * 68)

    # ── Load inputs ────────────────────────────────────────────────────────────
    log.info("Loading unified dataset...")
    ds = xr.open_dataset(UNIFIED_FILE)
    log.info("  time=%d  lat=%d  lon=%d", ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"])

    log.info("Loading reported events...")
    df_events = pd.read_csv(EVENTS_FILE)
    # The raw CSV uses "Municipalities"; rename to match the project convention
    if "Municipalities" in df_events.columns and "municipality" not in df_events.columns:
        df_events = df_events.rename(columns={"Municipalities": "municipality"})
    municipalities = sorted(df_events["municipality"].dropna().unique().tolist())
    log.info("  Unique municipalities: %d", len(municipalities))

    # ── Build reference table ──────────────────────────────────────────────────
    df_ref = build_reference_table(ds, municipalities)

    # ── Summary ────────────────────────────────────────────────────────────────
    n_ok   = (df_ref["data_quality"] == "ok").sum()
    n_flag = (df_ref["data_quality"] == "insufficient_data").sum()
    log.info("-" * 68)
    log.info("Reference table: %d municipalities", len(df_ref))
    log.info("  ok               : %d", n_ok)
    log.info("  insufficient_data: %d", n_flag)
    if n_flag > 0:
        flagged = df_ref[df_ref["data_quality"] == "insufficient_data"]["municipality"].tolist()
        log.warning("  Flagged: %s", flagged)

    # ── Save ───────────────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df_ref.to_csv(OUTPUT_FILE, index=False)
    log.info("Reference table saved → %s", OUTPUT_FILE)
    log.info("=" * 68)


if __name__ == "__main__":
    main()
