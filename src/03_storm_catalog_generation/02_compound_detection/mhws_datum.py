"""Mean High Water Springs (MHWS) datum from the FES2022 harmonic constants.

MHWS is the average height of the high waters at spring tides. At springs the
M2 and S2 constituents come into phase, so the high water rises to
approximately the sum of their amplitudes above mean sea level:

    MHWS = Z0 + (A_M2 + A_S2)

with Z0 the local mean sea level. Because the datum is expressed as a height
*above mean sea level*, whatever is compared against it must also be referenced
to mean sea level — see :func:`still_water_level` and the note on ``zos`` below.

Why a defined datum rather than a percentile
--------------------------------------------
MHWS is a standard hydrographic datum (IHO; it is the level charted on
nautical charts), not a threshold chosen by the analyst. Using a percentile of
the tide instead would reintroduce exactly the failure this method removes: a
fixed percentile corresponds to a *different* tidal datum in each tidal regime,
because the percentile equivalent of MHWS depends on the local S2/M2 ratio and
form factor, which vary along the Brazilian coast.

The related datum HAT (Highest Astronomical Tide, the maximum over an 18.6-year
nodal cycle) is also defined and unambiguous, but it is a ceiling reached about
once per nodal cycle. The adaptation argument this method rests on — that
settlement and morphology adjust to the water levels they see routinely —
points to the fortnightly spring high water, not to a once-in-19-years level.

Reference frame of ``zos``
--------------------------
GLORYS12 ``zos`` is sea surface height above the **geoid**, so its time mean is
the mean dynamic topography, which is non-zero and varies along the coast.
MHWS is a height above **local mean sea level**. The two therefore sit on
different zeros, and the mean of ``zos`` must be removed before they are
compared. This never mattered under the previous method, which compared
``SSH_total`` against a percentile of itself, so any constant offset cancelled;
it matters here because the datum is external.

Usage:
    from ..02_compound_detection.mhws_datum import mhws_at_points
    mhws_m = mhws_at_points(lats, lons)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
FES_DIR = (
    ROOT
    / "data"
    / "tide_models_clipped_brasil"
    / "fes2022b"
    / "ocean_tide_20241025"
)
#: Constituents whose amplitudes sum to the spring high water above MSL.
MHWS_CONSTITUENTS = ("m2", "s2")


def _load_amplitude(constituent: str) -> xr.DataArray:
    path = FES_DIR / f"{constituent}_fes2022.nc"
    if not path.exists():
        raise FileNotFoundError(f"FES2022 constituent not found: {path}")
    with xr.open_dataset(path) as ds:
        if "amplitude" not in ds:
            raise ValueError(f"{path} has no 'amplitude' variable")
        amplitude = ds["amplitude"].load()
    units = str(amplitude.attrs.get("units", "")).lower()
    if units not in {"cm", "centimeter", "centimetres", "centimeters"}:
        raise ValueError(
            f"{path}: expected amplitude in cm, found units={units!r}. "
            "Refusing to guess the scale."
        )
    return amplitude


def mhws_grid() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (lat, lon, mhws_m) with lon in the -180..180 convention.

    ``mhws_m`` is ``A_M2 + A_S2`` converted to metres, NaN over land.
    """
    amplitudes = [_load_amplitude(c) for c in MHWS_CONSTITUENTS]
    total_cm = amplitudes[0]
    for extra in amplitudes[1:]:
        total_cm = total_cm + extra

    lat = np.asarray(total_cm["lat"].values, dtype=float)
    lon = np.asarray(total_cm["lon"].values, dtype=float)
    # FES2022 is distributed on 0..360; the catalogue uses -180..180.
    lon = np.where(lon > 180.0, lon - 360.0, lon)
    order = np.argsort(lon)
    values_m = np.asarray(total_cm.values, dtype=float) / 100.0
    return lat, lon[order], values_m[:, order]


def mhws_at_points(
    lats: np.ndarray,
    lons: np.ndarray,
    *,
    max_distance_deg: float = 0.75,
) -> np.ndarray:
    """MHWS in metres at each (lat, lon), from the nearest valid ocean cell.

    Coastal grid points can fall on a land cell of the tide model, so the
    lookup searches the nearest cell carrying a finite amplitude rather than
    the nearest cell outright. Points with no valid cell within
    ``max_distance_deg`` return NaN instead of borrowing a distant value.
    """
    lat, lon, values = mhws_grid()
    lon_mesh, lat_mesh = np.meshgrid(lon, lat)
    finite = np.isfinite(values)
    if not finite.any():
        raise ValueError("FES2022 amplitudes contain no finite cells")

    tree = cKDTree(np.column_stack([lat_mesh[finite], lon_mesh[finite]]))
    valid_values = values[finite]

    query = np.column_stack([np.asarray(lats, float), np.asarray(lons, float)])
    distance, index = tree.query(query, k=1)
    result = valid_values[index]
    result[distance > max_distance_deg] = np.nan
    return result


def still_water_level(
    zos: np.ndarray,
    tide_daily_max: np.ndarray,
    *,
    zos_mean: float,
) -> np.ndarray:
    """Daily still water level referenced to local mean sea level.

    ``zos`` is de-meaned so that it expresses the departure from local mean sea
    level, the same zero MHWS is measured from. The tide term is already a
    departure from mean sea level by construction.
    """
    return (zos - zos_mean) + tide_daily_max


__all__ = ["mhws_grid", "mhws_at_points", "still_water_level", "MHWS_CONSTITUENTS"]
