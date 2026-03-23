"""
Event extraction for threshold calibration.

For each reported event (municipality + date):
1. Resolves the municipality to its nearest grid point in the unified dataset,
   using either the pre-computed Part E grid-association table (if available)
   or a fallback lookup of approximate coastal coordinates.
2. Extracts the full climatological series at that point (for threshold
   computation).
3. Extracts the 7-day window centred on the reported date
   (3 days before + event day + 3 days after).

Design
------
Municipality coordinates are resolved in priority order:
  (a) Pre-computed grid table from Part E (outputs/south_sc_test_data_exploratory/
      tables/tab_municipality_grid_association.csv) — most accurate.
  (b) Hardcoded approximate coastal positions for South SC municipalities
      (known from IBGE / OpenStreetMap; suitable for this test domain).
  (c) Domain-centre fallback (logs a warning).

Events whose reported date falls outside the dataset time range are skipped
with a warning.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.threshold_calibration.config.analysis_config import CFG

log = logging.getLogger(__name__)

# ── Approximate coastal positions for all SC municipalities ──────────────────
# Source: approximate coastal centroid derived from IBGE / OpenStreetMap.
# Used as fallback when the Part E grid table is not available.
# Covers all five sectors of the Leal et al. (2024) database:
# North, Central-north, Central, Central-south, South.
# Coordinates are (latitude, longitude) in decimal degrees.
_SOUTH_SC_COORDS: dict[str, tuple[float, float]] = {
    # ── South sector ──────────────────────────────────────────────────────────
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
    # ── Central sector ────────────────────────────────────────────────────────
    "Florianópolis":                 (-27.60, -48.55),
    "Palhoça":                       (-27.65, -48.67),
    "Tijucas":                       (-27.24, -48.64),
    # ── Central-south sector ──────────────────────────────────────────────────
    # Garopaba already listed under South sector above
    # ── Central-north sector ──────────────────────────────────────────────────
    "Bombinhas":                     (-27.13, -48.50),
    "Porto Belo":                    (-27.16, -48.54),
    "Itapema":                       (-27.09, -48.61),
    "Balneário Camboriú":            (-26.99, -48.63),
    "Navegantes":                    (-26.90, -48.65),
    "Itajaí":                        (-26.91, -48.66),
    "Penha":                         (-26.77, -48.65),
    "Balneário Piçarras":            (-26.77, -48.66),
    # ── North sector ──────────────────────────────────────────────────────────
    "Barra Velha":                   (-26.63, -48.68),
    "Balneário Barra do Sul":        (-26.46, -48.60),
    "Araquari":                      (-26.37, -48.72),
    "São Francisco do Sul":          (-26.24, -48.64),
    "Itapoá":                        (-26.11, -48.62),
}

# Path to the pre-computed Part E grid association table
_PART_E_TABLE = (
    Path(CFG["output_root"]).parents[0]  # outputs/
    / "south_sc_test_data_exploratory"
    / "tables"
    / "tab_municipality_grid_association.csv"
)


@dataclass
class EventRecord:
    """All data needed to analyse one reported event at one municipality."""
    event_idx: int
    disaster_id: int
    municipality: str
    date: pd.Timestamp
    grid_lat: float
    grid_lon: float
    grid_dist_km: float
    coord_source: str   # 'part_e', 'hardcoded', or 'domain_centre'

    # Full climatological series at the grid point (for threshold computation)
    hs_clim: pd.Series = field(repr=False)
    ssh_clim: pd.Series = field(repr=False)

    # 7-day window series centred on the event date
    hs_window: pd.Series = field(repr=False)
    ssh_window: pd.Series = field(repr=False)

    @property
    def window_start(self) -> pd.Timestamp:
        return self.hs_window.index[0]

    @property
    def window_end(self) -> pd.Timestamp:
        return self.hs_window.index[-1]


def build_event_records(
    ds: xr.Dataset,
    df_events: pd.DataFrame,
) -> list[EventRecord]:
    """Build one EventRecord per reported event row.

    Parameters
    ----------
    ds : xr.Dataset
        Unified daily metocean dataset (VHM0 + zos on WAVERYS grid).
    df_events : pd.DataFrame
        Cleaned and sector-filtered reported events table.

    Returns
    -------
    list of EventRecord
    """
    log.info("== Building event records ==")

    lat_grid = ds.latitude.values
    lon_grid = ds.longitude.values
    half_w   = CFG["event_half_window_days"]
    hs_var   = CFG["hs_var"]
    ssh_var  = CFG["ssh_var"]

    # ── Resolve municipality → grid point ─────────────────────────────────────
    muni_grid, coord_source = _build_muni_grid_map(ds, df_events)

    records: list[EventRecord] = []
    skipped = 0

    for idx, row in df_events.iterrows():
        muni = str(row["municipality"])
        date = row["date"]

        if pd.isna(date):
            log.warning("  Skipping event %s (%s): missing date", idx, muni)
            skipped += 1
            continue

        # Grid point for this municipality
        if muni in muni_grid:
            target_lat, target_lon = muni_grid[muni]
        else:
            # Use hardcoded coordinates if available
            target_lat = float(lat_grid[len(lat_grid) // 2])
            target_lon = float(lon_grid[len(lon_grid) // 2])
            log.warning(
                "  Municipality '%s' not in grid map; will search for nearest valid point.", muni
            )

        # Find nearest grid cell with BOTH variables having valid data
        grid_lat, grid_lon, dist_km = _find_nearest_valid_point(
            ds, target_lat, target_lon, hs_var, ssh_var
        )
        
        if grid_lat is None:
            log.warning(
                "  Skipping event %s / %s: no valid grid point found with both variables",
                idx, muni,
            )
            skipped += 1
            continue

        # ── Full climatological series ─────────────────────────────────────
        hs_clim  = _extract_series(ds, hs_var,  grid_lat, grid_lon)
        ssh_clim = _extract_series(ds, ssh_var, grid_lat, grid_lon)

        # ── 7-day event window ─────────────────────────────────────────────
        win_start = date - pd.Timedelta(days=half_w)
        win_end   = date + pd.Timedelta(days=half_w)
        hs_win  = hs_clim.loc[win_start:win_end]
        ssh_win = ssh_clim.loc[win_start:win_end]

        if len(hs_win) == 0 or len(ssh_win) == 0:
            log.warning(
                "  Skipping event %s / %s (%s): date %s outside dataset range",
                idx, muni, date.date(), date.date(),
            )
            skipped += 1
            continue

        records.append(EventRecord(
            event_idx    = int(idx),
            disaster_id  = int(row["disaster_id"]),
            municipality = muni,
            date         = date,
            grid_lat     = grid_lat,
            grid_lon     = grid_lon,
            grid_dist_km = dist_km,
            coord_source = coord_source,
            hs_clim      = hs_clim,
            ssh_clim     = ssh_clim,
            hs_window    = hs_win,
            ssh_window   = ssh_win,
        ))

    log.info("Event records: %d valid | %d skipped", len(records), skipped)
    return records


# ── Private helpers ────────────────────────────────────────────────────────────

def _build_muni_grid_map(
    ds: xr.Dataset,
    df_events: pd.DataFrame,
) -> tuple[dict[str, tuple[float, float]], str]:
    """Return (muni→(lat, lon), source_label) for all unique municipalities."""

    # (a) Try Part E pre-computed table
    if _PART_E_TABLE.exists():
        return _load_from_part_e_table(df_events), "part_e"

    # (b) Hardcoded coordinates
    municipalities = df_events["municipality"].dropna().unique().tolist()
    result: dict[str, tuple[float, float]] = {}
    missing = []
    for muni in municipalities:
        if muni in _SOUTH_SC_COORDS:
            result[muni] = _SOUTH_SC_COORDS[muni]
        else:
            missing.append(muni)
    if missing:
        log.warning(
            "No hardcoded coords for municipalities: %s — will use domain centre.",
            missing,
        )
    log.info(
        "Municipality coords: hardcoded lookup (%d/%d mapped)",
        len(result), len(municipalities),
    )
    return result, "hardcoded"


def _load_from_part_e_table(
    df_events: pd.DataFrame,
) -> dict[str, tuple[float, float]]:
    """Load municipality→grid-point mapping from the Part E CSV."""
    df_e = pd.read_csv(_PART_E_TABLE)
    result: dict[str, tuple[float, float]] = {}
    for _, row in df_e.iterrows():
        muni = str(row.get("municipality", ""))
        lat  = float(row.get("wave_grid_lat", row.get("grid_lat", np.nan)))
        lon  = float(row.get("wave_grid_lon", row.get("grid_lon", np.nan)))
        if pd.notna(lat) and pd.notna(lon):
            result[muni] = (lat, lon)
    log.info("Part E grid table loaded: %d municipalities mapped", len(result))
    return result


def _find_nearest_valid_point(
    ds: xr.Dataset,
    target_lat: float,
    target_lon: float,
    hs_var: str,
    ssh_var: str,
) -> tuple[float | None, float | None, float]:
    """Find the nearest grid point that has valid data for BOTH variables.
    
    Parameters
    ----------
    ds : xr.Dataset
        Dataset with VHM0 and zos variables
    target_lat, target_lon : float
        Target coordinates (municipality location)
    hs_var, ssh_var : str
        Variable names for significant wave height and sea surface height
    
    Returns
    -------
    (grid_lat, grid_lon, distance_km) or (None, None, -1) if no valid point found
    """
    lat_grid = ds.latitude.values
    lon_grid = ds.longitude.values
    
    # Get one time slice to check data validity
    hs_sample = ds[hs_var].isel(time=0).values
    ssh_sample = ds[ssh_var].isel(time=0).values
    
    # Find points where BOTH variables are valid (not NaN)
    both_valid = ~np.isnan(hs_sample) & ~np.isnan(ssh_sample)
    
    if not both_valid.any():
        log.error("No grid points have both %s and %s data!", hs_var, ssh_var)
        return None, None, -1.0
    
    # Calculate distances to all valid points
    min_dist = np.inf
    best_lat, best_lon = None, None
    
    for i, lat_g in enumerate(lat_grid):
        for j, lon_g in enumerate(lon_grid):
            if both_valid[i, j]:
                # Simple Euclidean distance in degrees
                dist = np.sqrt((lat_g - target_lat)**2 + (lon_g - target_lon)**2)
                if dist < min_dist:
                    min_dist = dist
                    best_lat = lat_g
                    best_lon = lon_g
    
    # Convert distance from degrees to km (approximate)
    dist_km = min_dist * 111.0  # 1 degree ≈ 111 km
    
    return float(best_lat), float(best_lon), dist_km


def _extract_series(
    ds: xr.Dataset,
    var: str,
    lat: float,
    lon: float,
) -> pd.Series:
    """Extract a 1-D daily time series at the nearest grid point."""
    da = ds[var].sel(latitude=lat, longitude=lon, method="nearest")
    return pd.Series(
        da.values.astype(float),
        index=pd.DatetimeIndex(ds.time.values),
        name=var,
    )
