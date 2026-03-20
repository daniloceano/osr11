"""
Exploratory Data Analysis of test datasets: WAVERYS + GLORYS + SC reported events.

Datasets:
  waverys_sc_sul_test.nc          — Significant wave height + direction (WAVERYS, 3-hourly, 1993–2025)
  glorys_sc_sul_test.nc           — Sea surface height (GLORYS12, daily, 1993–2025)
  reported_events_Karine_sc.csv   — 105 declared coastal disasters in SC, Brazil (1998–2023)
                                     (converted from .xlsx via src/preprocessing/convert_reported_events.py)

Reference for the events spreadsheet:
  Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. Identification of coastal natural
  disasters using official databases to provide support for the coastal management: the
  case of Santa Catarina, Brazil. Nat Hazards 120, 11465–11482 (2024).
  https://doi.org/10.1007/s11069-023-06150-3

Outputs:
  outputs/figures/testdata_exploration/   (PNG, 300 dpi)
  outputs/tables/testdata_exploration/    (CSV)
  data/test/README.md
  data/reported events/README.md

Run from project root:
  python src/exploratory/explore_testdata.py

Documented assumptions:
  - **TEST DATA SCOPE**: Analysis restricted to South sector municipalities and nearshore 
    grid point only, to match the limited spatial coverage of test datasets.
  - **Single-point analysis**: Hs and SSH maxima are evaluated at the SAME nearshore point
    (nearest to coast), not separately. This ensures co-located wave-surge analysis.
  - Nearshore point selection: grid cell closest to the coastline (minimum longitude).
  - Peak coincidence: window defined in CFG["coincidence_window_days"] (default 3 days).
  - City ordering in boxplots: by latitude (south to north), consistent with SC coastline.
  - Compound quick-look (Part G): empirical quantile thresholds for exploratory EDA only,
    NOT a final definition of compound events for the study.
  - Municipal coordinates: centroid of outer polygon ring (IBGE malhas v2 API).
  - Composite municipality names (e.g. "Içara/Balneário Rincão"): match tried per part.
  - Time axis format: days (not months) for Figures A and B to show short-term event detail.
"""

from __future__ import annotations

import gzip
import json
import logging
import sys
import unicodedata
import urllib.request
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy.spatial import KDTree
from scipy.stats import pearsonr

# Cartopy projection used throughout (data are in lon/lat, no reprojection needed)
_CRS = ccrs.PlateCarree()

# Natural Earth feature shorthand
def _ne(category: str, name: str, scale: str = "10m", **kw):
    """Return a pre-styled NaturalEarthFeature."""
    return cfeature.NaturalEarthFeature(category, name, scale, **kw)

# ── Configuration ─────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parents[2]

CFG = {
    # File paths
    "wave_file":   ROOT / "data/test/waverys_sc_sul_test.nc",
    "glorys_file": ROOT / "data/test/glorys_sc_sul_test.nc",
    "events_file": ROOT / "data/reported events/reported_events_Karine_sc.csv",
    "fig_dir":     ROOT / "outputs/figures/testdata_exploration",
    "tab_dir":     ROOT / "outputs/tables/testdata_exploration",
    # Variable names (as inspected from NetCDF files)
    "wave_var":    "VHM0",   # significant wave height (m)
    "dir_var":     "VMDR",   # mean wave direction (deg)
    "ssl_var":     "zos",    # sea surface height (m)
    # Analysis parameters
    "coincidence_window_days": 3,    # lag window to consider peaks coincident
    "timeseries_window_days":  15,   # days around peak for time series panels
    "compound_hs_quantile":    0.90,  # quantile threshold for compound EDA
    "compound_zos_quantile":   0.90,
    # Test data scope (limited domain)
    "target_sector":           "South",  # Only analyze South sector municipalities
    # Figure parameters
    "fig_dpi":   300,
    "cmap_hs":   "YlOrRd",
    "cmap_zos":  "RdBu_r",
}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ── Publication style ─────────────────────────────────────────────────────────

def set_pub_style() -> None:
    """Apply publication-quality matplotlib rcParams."""
    plt.rcParams.update({
        "figure.dpi":        150,
        "savefig.dpi":       CFG["fig_dpi"],
        "font.family":       "sans-serif",
        "font.size":         10,
        "axes.labelsize":    11,
        "axes.titlesize":    11,
        "xtick.labelsize":   9,
        "ytick.labelsize":   9,
        "legend.fontsize":   8.5,
        "legend.framealpha": 0.85,
        "figure.facecolor":  "white",
        "axes.facecolor":    "white",
        "axes.grid":         True,
        "grid.alpha":        0.3,
        "grid.linestyle":    "--",
        "grid.linewidth":    0.5,
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "lines.linewidth":   1.5,
    })


def make_output_dirs() -> None:
    """Create output directories."""
    CFG["fig_dir"].mkdir(parents=True, exist_ok=True)
    CFG["tab_dir"].mkdir(parents=True, exist_ok=True)
    log.info("Output directories ready.")


def save_fig(fig: plt.Figure, name: str) -> None:
    """Save figure to outputs/figures/testdata_exploration/."""
    path = CFG["fig_dir"] / f"{name}.png"
    fig.savefig(path, dpi=CFG["fig_dpi"], bbox_inches="tight")
    log.info("  -> Figure saved: %s", path.name)
    plt.close(fig)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_wave_data() -> xr.Dataset:
    """Load WAVERYS test dataset and validate expected variables."""
    path = CFG["wave_file"]
    if not path.exists():
        raise FileNotFoundError(f"WAVERYS file not found: {path}")
    ds = xr.open_dataset(path)
    _check_vars(ds, {CFG["wave_var"]}, path)
    log.info(
        "WAVERYS: %d time steps | %d lat | %d lon | %s to %s",
        ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"],
        str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10],
    )
    return ds


def load_glorys_data() -> xr.Dataset:
    """Load GLORYS12 test dataset and validate expected variables."""
    path = CFG["glorys_file"]
    if not path.exists():
        raise FileNotFoundError(f"GLORYS file not found: {path}")
    ds = xr.open_dataset(path)
    _check_vars(ds, {CFG["ssl_var"]}, path)
    log.info(
        "GLORYS:  %d time steps | %d lat | %d lon | %s to %s",
        ds.sizes["time"], ds.sizes["latitude"], ds.sizes["longitude"],
        str(ds.time.values[0])[:10], str(ds.time.values[-1])[:10],
    )
    return ds


def _check_vars(ds: xr.Dataset, required: set, path: Path) -> None:
    missing = required - set(ds.data_vars)
    if missing:
        raise ValueError(
            f"Variable(s) {missing} not found in {path.name}. "
            f"Available: {list(ds.data_vars)}"
        )


def load_reported_events() -> pd.DataFrame:
    """
    Load and clean the reported events CSV.
    
    TEST DATA MODIFICATION: Filters to South sector municipalities only,
    as the test domain covers only the southern portion of SC coast.
    """
    path = CFG["events_file"]
    if not path.exists():
        raise FileNotFoundError(f"Events file not found: {path}")

    df = pd.read_csv(path)

    # Rename columns to snake_case
    rename = {
        "Disaster ID":                    "disaster_id",
        "Dates of occurrence (mm/dd/yyyy)": "date",
        "Months":                          "month",
        "Municipalities":                  "municipality",
        "Coastal Sectors":                 "coastal_sector",
        "EM or SPC":                       "disaster_type",
        "hgt":                             "hgt_m",
        "Wspd (m/s)":                      "wspd_ms",
        "Wdir (m/s)":                      "wdir_deg",   # label says m/s but values are degrees
        "Hs (m)":                          "hs_m",
        "Hsdir (°)":                       "hsdir_deg",
        "HsPp (s)":                        "hspp_s",
        "WP":                              "weather_pattern",
        "Number of Human Damage":          "n_human_damage",
        "Material Damage (BRL)":           "material_damage_brl",
        "Environmental Damage (BRL)":      "env_damage_brl",
        "Public Economic Losses (BRL)":    "public_losses_brl",
        "Private Economic Losses (BRL)":   "private_losses_brl",
    }
    df = df.rename(columns=rename)

    # Normalize text fields
    for col in ["municipality", "coastal_sector", "disaster_type", "month"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Replace asterisks (original missing data marker) with NaN
    df = df.replace("*", pd.NA)

    # Convert numeric columns
    num_cols = [
        "hgt_m", "wspd_ms", "wdir_deg", "hs_m", "hsdir_deg", "hspp_s",
        "n_human_damage", "material_damage_brl", "env_damage_brl",
        "public_losses_brl", "private_losses_brl",
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows without event ID or municipality
    df = df.dropna(subset=["disaster_id", "municipality"]).reset_index(drop=True)

    # FILTER: Keep only target sector municipalities (test data scope)
    target_sector = CFG["target_sector"]
    n_before = len(df)
    df = df[df["coastal_sector"] == target_sector].copy().reset_index(drop=True)
    n_after = len(df)
    
    log.info(
        "Filtered to %s sector: %d → %d events (%d removed)",
        target_sector, n_before, n_after, n_before - n_after
    )

    log.info(
        "Reported events: %d records | %d municipalities | %s to %s",
        len(df), df["municipality"].nunique(),
        df["date"].min().date(), df["date"].max().date(),
    )
    return df


# ── Spatial analysis ──────────────────────────────────────────────────────────

def find_spatial_max(da: xr.DataArray) -> dict:
    """
    Find the global maximum of a DataArray and return its time and location.

    Strategy: (1) time series of the instantaneous spatial maximum;
    (2) find the time step with the highest value; (3) locate that point.
    """
    flat_max = da.max(dim=["latitude", "longitude"])
    t_idx = int(np.nanargmax(flat_max.values))
    snap = da.isel(time=t_idx).values
    i_lat, i_lon = np.unravel_index(np.nanargmax(snap), snap.shape)

    return {
        "value":   float(snap[i_lat, i_lon]),
        "time":    pd.Timestamp(da.time.values[t_idx]),
        "lat":     float(da.latitude.values[i_lat]),
        "lon":     float(da.longitude.values[i_lon]),
        "t_idx":   t_idx,
        "lat_idx": int(i_lat),
        "lon_idx": int(i_lon),
    }


def find_nearshore_point(da: xr.DataArray) -> dict:
    """
    Find the nearshore grid point (closest to coast = minimum longitude).
    
    Returns a dict with the coordinates and indices of the nearshore point.
    This ensures wave and surge analyses are co-located at the same nearshore location.
    """
    lon_vals = da.longitude.values
    lat_vals = da.latitude.values
    
    # Find the westernmost (minimum) longitude
    i_lon = np.argmin(lon_vals)
    # Use the middle latitude for this longitude
    i_lat = len(lat_vals) // 2
    
    log.info(
        "Nearshore point selected: (%+.2f, %+.2f) [closest to coast]",
        lat_vals[i_lat], lon_vals[i_lon]
    )
    
    return {
        "lat":     float(lat_vals[i_lat]),
        "lon":     float(lon_vals[i_lon]),
        "lat_idx": int(i_lat),
        "lon_idx": int(i_lon),
    }


def peaks_coincident(t1: pd.Timestamp, t2: pd.Timestamp, window_days: int) -> bool:
    """Return True if two timestamps are within window_days of each other."""
    return abs((t1 - t2).total_seconds()) <= window_days * 86_400


# ── Municipality coordinates via IBGE API ─────────────────────────────────────

def _norm(name: str) -> str:
    """Normalize accents and case for fuzzy name matching."""
    return (
        unicodedata.normalize("NFD", name)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def _ibge_get(url: str, timeout: int = 15) -> object | None:
    """
    GET request to IBGE API; returns None on failure.

    Handles gzip-encoded responses automatically — IBGE API may return
    Content-Encoding: gzip regardless of the Accept-Encoding header sent.
    """
    try:
        req = urllib.request.Request(url, headers={"Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return json.loads(gzip.decompress(raw))
    except Exception as exc:
        log.warning("IBGE API request failed (%s): %s", url[:70], exc)
        return None


def _polygon_centroid(rings: list) -> tuple[float, float]:
    """Simple centroid from mean of GeoJSON polygon exterior ring coordinates."""
    coords = np.array(rings[0])  # [[lon, lat], ...]
    return float(coords[:, 1].mean()), float(coords[:, 0].mean())  # lat, lon


def fetch_ibge_coords(names: list[str]) -> pd.DataFrame:
    """
    Fetch approximate centroid coordinates for a list of SC municipality names
    using the IBGE localidades and malhas APIs.

    Strategy: centroid of the outer polygon ring from IBGE malhas v2.
    Source: IBGE Localidades API v1 + IBGE Malhas v2
            (https://servicodados.ibge.gov.br)

    Composite names (e.g. "A/B"): match is attempted for each part.

    Returns a DataFrame with: municipality, ibge_code, lat, lon, coord_source.
    """
    log.info("Fetching SC municipality list from IBGE API...")
    raw = _ibge_get(
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados/SC/municipios"
    )
    if raw is None:
        log.warning("IBGE API unavailable — municipality coordinates will be NaN.")
        return pd.DataFrame(
            {"municipality": names, "ibge_code": pd.NA,
             "lat": np.nan, "lon": np.nan, "coord_source": "ibge_unavailable"}
        )

    ibge_lookup = {_norm(m["nome"]): m for m in raw}
    records = []

    for raw_name in names:
        parts = [p.strip() for p in raw_name.replace("/", "|").split("|")]
        matched = next(
            (ibge_lookup[_norm(p)] for p in parts if _norm(p) in ibge_lookup), None
        )

        if matched is None:
            log.warning("  Not found in IBGE list: %r", raw_name)
            records.append({
                "municipality": raw_name, "ibge_code": pd.NA,
                "lat": np.nan, "lon": np.nan, "coord_source": "not_found",
            })
            continue

        code = matched["id"]
        geo = _ibge_get(
            f"https://servicodados.ibge.gov.br/api/v2/malhas/{code}"
            f"?resolucao=2&formato=application/vnd.geo+json"
        )
        if geo is None:
            records.append({
                "municipality": raw_name, "ibge_code": code,
                "lat": np.nan, "lon": np.nan, "coord_source": "api_error",
            })
            continue

        try:
            geom = geo["features"][0]["geometry"]
            if geom["type"] == "Polygon":
                lat, lon = _polygon_centroid(geom["coordinates"])
            elif geom["type"] == "MultiPolygon":
                largest = max(geom["coordinates"], key=lambda p: len(p[0]))
                lat, lon = _polygon_centroid(largest)
            else:
                raise ValueError(f"Unexpected geometry type: {geom['type']}")

            records.append({
                "municipality":  raw_name,
                "ibge_code":     code,
                "lat":           lat,
                "lon":           lon,
                "coord_source":  f"IBGE malhas v2 — code {code} — outer polygon centroid",
            })
            log.info("  %s -> IBGE %s -> (%.3fS, %.3fW)", raw_name, code, lat, lon)

        except Exception as exc:
            log.warning("  Failed to parse IBGE geometry for %r: %s", raw_name, exc)
            records.append({
                "municipality": raw_name, "ibge_code": code,
                "lat": np.nan, "lon": np.nan, "coord_source": "parse_error",
            })

    return pd.DataFrame(records)


def nearest_grid_point(
    lat_ref: float, lon_ref: float,
    lat_grid: np.ndarray, lon_grid: np.ndarray,
) -> dict:
    """
    Find nearest grid point to (lat_ref, lon_ref) using KDTree on a 2D grid.
    Approximate distance in km via equirectangular projection.
    """
    lats, lons = np.meshgrid(lat_grid, lon_grid, indexing="ij")
    tree = KDTree(np.column_stack([lats.ravel(), lons.ravel()]))
    _, idx = tree.query([lat_ref, lon_ref])
    i_lat, i_lon = np.unravel_index(idx, lats.shape)

    dlat = (lat_grid[i_lat] - lat_ref) * 111.0
    dlon = (lon_grid[i_lon] - lon_ref) * 111.0 * np.cos(np.radians(lat_ref))

    return {
        "grid_lat": float(lat_grid[i_lat]),
        "grid_lon": float(lon_grid[i_lon]),
        "lat_idx":  int(i_lat),
        "lon_idx":  int(i_lon),
        "dist_km":  float(np.sqrt(dlat**2 + dlon**2)),
    }


def build_grid_table(
    muni_coords: pd.DataFrame,
    lat_wave: np.ndarray, lon_wave: np.ndarray,
    lat_gl: np.ndarray, lon_gl: np.ndarray,
) -> pd.DataFrame:
    """
    Associate each municipality to the nearest WAVERYS and GLORYS grid points.
    Flags municipalities outside the test domain bounding box.
    """
    lat_min, lat_max = lat_wave.min(), lat_wave.max()
    lon_min, lon_max = lon_wave.min(), lon_wave.max()

    rows = []
    for _, row in muni_coords.iterrows():
        lat, lon = row["lat"], row["lon"]
        in_domain = (
            not np.isnan(lat) and not np.isnan(lon)
            and lat_min <= lat <= lat_max
            and lon_min <= lon <= lon_max
        )
        r = {"municipality": row["municipality"], "muni_lat": lat,
             "muni_lon": lon, "in_test_domain": in_domain}

        if in_domain:
            wp = nearest_grid_point(lat, lon, lat_wave, lon_wave)
            gp = nearest_grid_point(lat, lon, lat_gl, lon_gl)
            r.update({
                "wave_grid_lat": wp["grid_lat"], "wave_grid_lon": wp["grid_lon"],
                "wave_dist_km":  wp["dist_km"],
                "gl_grid_lat":   gp["grid_lat"], "gl_grid_lon":   gp["grid_lon"],
                "gl_dist_km":    gp["dist_km"],
            })
        else:
            r.update({
                "wave_grid_lat": np.nan, "wave_grid_lon": np.nan, "wave_dist_km": np.nan,
                "gl_grid_lat":   np.nan, "gl_grid_lon":   np.nan, "gl_dist_km":   np.nan,
            })
        rows.append(r)

    return pd.DataFrame(rows)


# ── Plotting helpers ───────────────────────────────────────────────────────────

SECTOR_COLORS = {
    "North":          "#1f77b4",
    "Central-north":  "#ff7f0e",
    "Central":        "#2ca02c",
    "Central-south":  "#d62728",
    "South":          "#9467bd",
}


def _fmt_time_ax(ax: plt.Axes, *, minor: bool = True) -> None:
    """Apply clean date formatting to a time axis (day-level precision)."""
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    if minor:
        ax.xaxis.set_minor_locator(mdates.DayLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def _vline(
    ax: plt.Axes,
    t: pd.Timestamp,
    color: str,
    label: str | None = None,
) -> None:
    """Draw a vertical dashed line at time t."""
    ax.axvline(t, color=color, lw=1.3, ls="--", alpha=0.85, label=label, zorder=4)


def _span(ax: plt.Axes, t_center: pd.Timestamp, window_days: int) -> None:
    """Shade the temporal window around t_center."""
    t0 = t_center - pd.Timedelta(days=window_days // 2)
    t1 = t_center + pd.Timedelta(days=window_days // 2)
    ax.axvspan(t0, t1, color="gold", alpha=0.12, zorder=0)


# ── Part A: Spatial maximum maps ──────────────────────────────────────────────

def run_spatial_analysis(
    ds_wave: xr.Dataset, ds_gl: xr.Dataset
) -> tuple[dict, dict]:
    """
    Part A: identify maxima of Hs and SSH at the SAME nearshore point.
    Generate spatial maps (shading + contours) with time series panels.
    
    TEST DATA MODIFICATION: Uses a single nearshore point (closest to coast)
    to ensure wave-surge co-location in this limited-domain exploratory analysis.
    """
    log.info("== Part A: Spatial maximum analysis (nearshore point) ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]

    # Maximum fields over the full period
    hs_max_field  = da_hs.max("time")
    zos_max_field = da_zos.max("time")

    # Select the nearshore point (same for both variables)
    nearshore = find_nearshore_point(da_hs)
    
    # Extract time series at this nearshore point
    hs_at_point  = da_hs.sel(latitude=nearshore["lat"], longitude=nearshore["lon"], method="nearest")
    zos_at_point = da_zos.sel(latitude=nearshore["lat"], longitude=nearshore["lon"], method="nearest")
    
    # Find temporal maxima at this single point
    hs_t_idx  = int(np.nanargmax(hs_at_point.values))
    zos_t_idx = int(np.nanargmax(zos_at_point.values))
    
    max_hs = {
        "value":   float(hs_at_point.values[hs_t_idx]),
        "time":    pd.Timestamp(hs_at_point.time.values[hs_t_idx]),
        "lat":     nearshore["lat"],
        "lon":     nearshore["lon"],
        "t_idx":   hs_t_idx,
        "lat_idx": nearshore["lat_idx"],
        "lon_idx": nearshore["lon_idx"],
    }
    
    max_zos = {
        "value":   float(zos_at_point.values[zos_t_idx]),
        "time":    pd.Timestamp(zos_at_point.time.values[zos_t_idx]),
        "lat":     nearshore["lat"],
        "lon":     nearshore["lon"],
        "t_idx":   zos_t_idx,
        "lat_idx": nearshore["lat_idx"],
        "lon_idx": nearshore["lon_idx"],
    }

    log.info(
        "VHM0 max at nearshore point: %.2f m — %s",
        max_hs["value"], max_hs["time"].strftime("%Y-%m-%d %H:%M"),
    )
    log.info(
        "zos  max at nearshore point: %.4f m — %s",
        max_zos["value"], max_zos["time"].strftime("%Y-%m-%d"),
    )

    coincident = peaks_coincident(
        max_hs["time"], max_zos["time"], CFG["coincidence_window_days"]
    )
    log.info(
        "Peaks coincident (window=%d days): %s",
        CFG["coincidence_window_days"], coincident,
    )

    if coincident:
        _spatial_event_fig(
            hs_max_field, zos_max_field, da_hs, da_zos,
            max_hs, max_zos, t_ref=max_hs["time"],
            fname="fig_A1_spatial_max_combined",
            subtitle="Coincident peaks — combined figure (nearshore point)",
        )
    else:
        _spatial_event_fig(
            hs_max_field, zos_max_field, da_hs, da_zos,
            max_hs, max_zos, t_ref=max_hs["time"],
            fname="fig_A1a_spatial_max_Hs_event",
            subtitle=f"Centred on Hs peak — {max_hs['time'].strftime('%Y-%m-%d')} (nearshore point)",
        )
        _spatial_event_fig(
            hs_max_field, zos_max_field, da_hs, da_zos,
            max_hs, max_zos, t_ref=max_zos["time"],
            fname="fig_A1b_spatial_max_SSH_event",
            subtitle=f"Centred on SSH peak — {max_zos['time'].strftime('%Y-%m-%d')} (nearshore point)",
        )

    return max_hs, max_zos


def _spatial_event_fig(
    hs_max_field: xr.DataArray,
    zos_max_field: xr.DataArray,
    da_hs: xr.DataArray,
    da_zos: xr.DataArray,
    max_hs: dict,
    max_zos: dict,
    t_ref: pd.Timestamp,
    fname: str,
    subtitle: str,
) -> None:
    """
    Figure: spatial map panel (top) + Hs time series + SSH time series.

    The time series panels are restricted to the event window [t0, t1] via
    explicit xlim. This prevents out-of-window vertical marker lines from
    distorting the x-axis when the Hs and SSH peaks are not coincident.
    """
    win = CFG["timeseries_window_days"]
    t0  = t_ref - pd.Timedelta(days=win // 2)
    t1  = t_ref + pd.Timedelta(days=win // 2)

    # Time series at the nearshore point (not domain max) within the event window
    hs_ts  = da_hs.sel(
        latitude=max_hs["lat"], longitude=max_hs["lon"], 
        method="nearest", time=slice(t0, t1)
    )
    zos_ts = da_zos.sel(
        latitude=max_zos["lat"], longitude=max_zos["lon"], 
        method="nearest", time=slice(t0, t1)
    )

    fig = plt.figure(figsize=(10, 12))
    gs  = GridSpec(3, 1, figure=fig, height_ratios=[2.6, 1, 1], hspace=0.5)
    ax_map = fig.add_subplot(gs[0], projection=_CRS)
    ax_hs  = fig.add_subplot(gs[1])
    ax_zos = fig.add_subplot(gs[2])

    # ── Spatial map (cartopy) ─────────────────────────────────────────
    lon_w = hs_max_field.longitude.values
    lat_w = hs_max_field.latitude.values
    lon_g = zos_max_field.longitude.values
    lat_g = zos_max_field.latitude.values

    pad = 0.12
    ax_map.set_extent(
        [lon_w.min() - pad, lon_w.max() + pad,
         lat_w.min() - pad, lat_w.max() + pad],
        crs=_CRS,
    )

    # Background: land + ocean
    ax_map.add_feature(_ne("physical", "land",  facecolor="#f0ede8"), zorder=0)
    ax_map.add_feature(_ne("physical", "ocean", facecolor="#daeeff"), zorder=0)
    ax_map.add_feature(
        _ne("physical", "coastline", edgecolor="black", facecolor="none"),
        linewidth=0.8, zorder=3,
    )
    ax_map.add_feature(
        _ne("cultural", "admin_1_states_provinces_lines",
            edgecolor="dimgray", facecolor="none"),
        linewidth=0.5, zorder=3,
    )

    # Gridlines
    gl = ax_map.gridlines(
        draw_labels=True, linewidth=0.4, color="gray",
        alpha=0.5, linestyle="--", crs=_CRS,
    )
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = {"size": 8}
    gl.ylabel_style = {"size": 8}

    # Hs max field (shaded)
    pcm = ax_map.pcolormesh(
        lon_w, lat_w, hs_max_field.values,
        cmap=CFG["cmap_hs"], shading="auto",
        transform=_CRS, zorder=1,
    )
    cb = fig.colorbar(pcm, ax=ax_map, pad=0.08, shrink=0.75, aspect=20)
    cb.set_label("Max $H_s$ (m)", fontsize=9)

    # SSH max field (contours)
    cs = ax_map.contour(
        lon_g, lat_g, zos_max_field.values,
        levels=7, colors="steelblue", linewidths=0.9, alpha=0.85,
        transform=_CRS, zorder=2,
    )
    ax_map.clabel(cs, inline=True, fontsize=7, fmt="%.3f m")

    # Nearshore point marker (same for both variables)
    ax_map.plot(
        max_hs["lon"], max_hs["lat"], "o",
        color="purple", ms=12, mec="white", mew=1.2, zorder=5,
        label=f"Nearshore point: $H_s$ = {max_hs['value']:.2f} m, SSH = {max_zos['value']:.3f} m",
        transform=_CRS,
    )
    ax_map.legend(loc="upper right", fontsize=8)
    ax_map.set_title(
        "Period maxima (1993–2025) — Nearshore point analysis\n"
        "Shading: max $H_s$  ·  Contours: max SSH  ·  Marker: analysis point",
        fontsize=10,
    )

    # Text annotation at analysis point
    ax_map.text(
        max_hs["lon"] + 0.05, max_hs["lat"] - 0.12,
        f"Nearshore point\n({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)",
        fontsize=6.5, color="purple", fontweight="bold",
        transform=_CRS, zorder=6,
    )

    # ── Hs time series ────────────────────────────────────────────────
    # Time series at the nearshore point
    t_hs = pd.to_datetime(hs_ts.time.values)
    ax_hs.plot(t_hs, hs_ts.values, color="#d62728", lw=1.4,
               label="$H_s$ at nearshore point")
    _vline(ax_hs, max_hs["time"], "#d62728",
           label=f"Hs peak {max_hs['time'].strftime('%Y-%m-%d')}")
    if t0 <= t_ref <= t1 and t_ref != max_hs["time"]:
        _vline(ax_hs, t_ref, "gray", label="Reference time")
    _span(ax_hs, t_ref, win)
    ax_hs.set_ylabel("$H_s$ (m)")
    ax_hs.set_xlim(pd.Timestamp(t0), pd.Timestamp(t1))
    ax_hs.legend(loc="upper left", fontsize=7.5)
    ax_hs.annotate(
        f"{max_hs['value']:.2f} m",
        xy=(max_hs["time"], max_hs["value"]),
        xytext=(6, 4), textcoords="offset points",
        fontsize=7.5, color="#d62728", fontweight="bold",
    )
    _fmt_time_ax(ax_hs)

    # ── SSH time series ───────────────────────────────────────────────
    t_zos = pd.to_datetime(zos_ts.time.values)
    ax_zos.plot(t_zos, zos_ts.values, color="steelblue", lw=1.4,
                label="SSH at nearshore point")
    _vline(ax_zos, max_zos["time"], "steelblue",
           label=f"SSH peak {max_zos['time'].strftime('%Y-%m-%d')}")
    if t0 <= t_ref <= t1 and t_ref != max_zos["time"]:
        _vline(ax_zos, t_ref, "gray", label="Reference time")
    _span(ax_zos, t_ref, win)
    ax_zos.set_ylabel("SSH (m)")
    ax_zos.set_xlim(pd.Timestamp(t0), pd.Timestamp(t1))
    ax_zos.legend(loc="upper left", fontsize=7.5)
    _fmt_time_ax(ax_zos)

    # Note if the SSH peak or Hs peak falls outside this window
    if not (t0 <= max_zos["time"] <= t1):
        ax_zos.text(
            0.02, 0.05,
            f"SSH peak ({max_zos['time'].strftime('%Y-%m-%d')}) outside window",
            transform=ax_zos.transAxes, fontsize=7, color="steelblue",
            style="italic",
        )
    if not (t0 <= max_hs["time"] <= t1):
        ax_hs.text(
            0.02, 0.05,
            f"Hs peak ({max_hs['time'].strftime('%Y-%m-%d')}) outside window",
            transform=ax_hs.transAxes, fontsize=7, color="#d62728",
            style="italic",
        )

    fig.suptitle(
        f"Reference date: {t_ref.strftime('%Y-%m-%d')}  ·  {subtitle}\n"
        f"Time window: {t0.strftime('%Y-%m-%d')} – {t1.strftime('%Y-%m-%d')}",
        fontsize=10, color="#333333", y=1.01,
    )
    save_fig(fig, fname)


# ── Part B: Time series at peak locations ─────────────────────────────────────

def run_timeseries_analysis(
    ds_wave: xr.Dataset, ds_gl: xr.Dataset,
    max_hs: dict, max_zos: dict,
) -> None:
    """
    Part B: time series at the grid points of maximum Hs and maximum SSH.
    Four panels: Hs and SSH at each of the two peak locations.
    Explicit xlim set per panel to keep each window clean.
    """
    log.info("== Part B: Time series at peak grid points ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]
    win    = CFG["timeseries_window_days"]

    same_point = (
        abs(max_hs["lat"] - max_zos["lat"]) < 0.01
        and abs(max_hs["lon"] - max_zos["lon"]) < 0.01
    )
    log.info("Hs-max and SSH-max at same grid point: %s", same_point)

    def _win(t_ref):
        return (
            t_ref - pd.Timedelta(days=win // 2),
            t_ref + pd.Timedelta(days=win // 2),
        )

    t0_hs, t1_hs   = _win(max_hs["time"])
    t0_zos, t1_zos = _win(max_zos["time"])

    def _extract(da, lat, lon, t0, t1):
        return da.sel(latitude=lat, longitude=lon, method="nearest").sel(
            time=slice(t0, t1)
        )

    fig, axes = plt.subplots(4, 1, figsize=(11, 10))

    # Panel 0: Hs at Hs-max point, window around Hs peak
    ser = _extract(da_hs, max_hs["lat"], max_hs["lon"], t0_hs, t1_hs)
    axes[0].plot(pd.to_datetime(ser.time.values), ser.values, color="#d62728", lw=1.4)
    _vline(axes[0], max_hs["time"], "#d62728")
    _span(axes[0], max_hs["time"], win)
    axes[0].set_xlim(pd.Timestamp(t0_hs), pd.Timestamp(t1_hs))
    axes[0].set_ylabel("$H_s$ (m)")
    axes[0].set_title(
        f"$H_s$ at Hs-peak grid point  ({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[0].annotate(
        f"Max = {max_hs['value']:.2f} m\n{max_hs['time'].strftime('%Y-%m-%d %H:%M')}",
        xy=(max_hs["time"], max_hs["value"]),
        xytext=(10, -18), textcoords="offset points",
        fontsize=7.5, color="#d62728",
        arrowprops=dict(arrowstyle="-", color="#d62728", lw=0.7),
    )
    _fmt_time_ax(axes[0])

    # Panel 1: SSH at Hs-max point, same window
    ser = _extract(da_zos, max_hs["lat"], max_hs["lon"], t0_hs, t1_hs)
    axes[1].plot(pd.to_datetime(ser.time.values), ser.values, color="steelblue", lw=1.4)
    _vline(axes[1], max_hs["time"], "#d62728", label="Hs peak")
    _span(axes[1], max_hs["time"], win)
    axes[1].set_xlim(pd.Timestamp(t0_hs), pd.Timestamp(t1_hs))
    axes[1].set_ylabel("SSH (m)")
    axes[1].set_title(
        f"SSH at Hs-peak grid point  ({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[1].legend(fontsize=7.5, loc="upper left")
    _fmt_time_ax(axes[1])

    # Panel 2: SSH at SSH-max point, window around SSH peak
    ser = _extract(da_zos, max_zos["lat"], max_zos["lon"], t0_zos, t1_zos)
    axes[2].plot(pd.to_datetime(ser.time.values), ser.values, color="steelblue", lw=1.4)
    _vline(axes[2], max_zos["time"], "steelblue")
    _span(axes[2], max_zos["time"], win)
    axes[2].set_xlim(pd.Timestamp(t0_zos), pd.Timestamp(t1_zos))
    axes[2].set_ylabel("SSH (m)")
    axes[2].set_title(
        f"SSH at SSH-peak grid point  ({max_zos['lat']:.2f}°S, {max_zos['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[2].annotate(
        f"Max = {max_zos['value']:.3f} m\n{max_zos['time'].strftime('%Y-%m-%d')}",
        xy=(max_zos["time"], max_zos["value"]),
        xytext=(10, -18), textcoords="offset points",
        fontsize=7.5, color="steelblue",
        arrowprops=dict(arrowstyle="-", color="steelblue", lw=0.7),
    )
    _fmt_time_ax(axes[2])

    # Panel 3: Hs at SSH-max point, same window
    ser = _extract(da_hs, max_zos["lat"], max_zos["lon"], t0_zos, t1_zos)
    axes[3].plot(pd.to_datetime(ser.time.values), ser.values, color="#d62728", lw=1.4)
    _vline(axes[3], max_zos["time"], "steelblue", label="SSH peak")
    _span(axes[3], max_zos["time"], win)
    axes[3].set_xlim(pd.Timestamp(t0_zos), pd.Timestamp(t1_zos))
    axes[3].set_ylabel("$H_s$ (m)")
    axes[3].set_title(
        f"$H_s$ at SSH-peak grid point  ({max_zos['lat']:.2f}°S, {max_zos['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[3].legend(fontsize=7.5, loc="upper left")
    _fmt_time_ax(axes[3])

    fig.suptitle(
        "Time series at peak-value grid points\n"
        "(dashed line = peak instant  ·  shaded band = time window)",
        fontsize=10, y=1.01,
    )
    plt.tight_layout()
    save_fig(fig, "fig_B1_timeseries_at_maxima")


# ── Part D: Reported events EDA ───────────────────────────────────────────────

def run_reported_events_eda(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Part D: exploratory analysis of the reported events spreadsheet.
    Generates summary tables and figures (counts, boxplots, seasonality).
    """
    log.info("== Part D: Reported events EDA ==")

    # ── Summary tables ────────────────────────────────────────────────
    muni_count = (
        df.groupby("municipality")
        .agg(
            n_events       =("disaster_id", "count"),
            coastal_sector =("coastal_sector", "first"),
            hs_mean        =("hs_m", "mean"),
            hs_median      =("hs_m", "median"),
            hs_max         =("hs_m", "max"),
            wspd_mean      =("wspd_ms", "mean"),
        )
        .reset_index()
        .sort_values("n_events", ascending=False)
    )
    muni_count.to_csv(CFG["tab_dir"] / "tab_events_by_municipality.csv", index=False)
    log.info("  -> tab_events_by_municipality.csv")

    sector_count = (
        df.groupby("coastal_sector")
        .agg(
            n_events        =("disaster_id", "count"),
            n_municipalities=("municipality", "nunique"),
            hs_mean         =("hs_m", "mean"),
            hs_max          =("hs_m", "max"),
        )
        .reset_index()
        .sort_values("n_events", ascending=False)
    )
    sector_count.to_csv(CFG["tab_dir"] / "tab_events_by_sector.csv", index=False)
    log.info("  -> tab_events_by_sector.csv")

    # ── Fig D1: event count by municipality and sector ────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    mc   = muni_count.sort_values("n_events", ascending=True)
    bars = ax1.barh(mc["municipality"], mc["n_events"],
                    color="#4C72B0", edgecolor="white", lw=0.4)
    ax1.set_xlabel("Number of events")
    ax1.set_title("Events by municipality", fontsize=11)
    ax1.tick_params(axis="y", labelsize=7.5)
    for bar, val in zip(bars, mc["n_events"]):
        ax1.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                 str(val), va="center", fontsize=7)

    sc_order = sector_count.sort_values("n_events", ascending=False)["coastal_sector"].tolist()
    colors   = [SECTOR_COLORS.get(s, "gray") for s in sc_order]
    n_vals   = sector_count.set_index("coastal_sector").loc[sc_order, "n_events"]
    ax2.bar(sc_order, n_vals, color=colors, edgecolor="white", lw=0.5)
    ax2.set_xlabel("Coastal sector")
    ax2.set_ylabel("Number of events")
    ax2.set_title("Events by coastal sector", fontsize=11)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=20, ha="right")
    for i, (_, v) in enumerate(zip(sc_order, n_vals)):
        ax2.text(i, v + 0.3, str(v), ha="center", fontsize=8.5)

    fig.suptitle("Declared coastal disasters — Santa Catarina, Brazil (1998–2023)", fontsize=12)
    plt.tight_layout()
    save_fig(fig, "fig_D1_events_municipality_sector")

    # ── Fig D2: Hs boxplot by municipality (ordered by median) ────────
    muni_order = (
        df.groupby("municipality")["hs_m"].median()
        .sort_values(ascending=False).index.tolist()
    )
    fig, ax = plt.subplots(figsize=(13, 5))
    data_bp = [df.loc[df["municipality"] == m, "hs_m"].dropna().values for m in muni_order]
    bp = ax.boxplot(
        data_bp, patch_artist=True, showfliers=True,
        medianprops=dict(color="black", lw=1.5),
        flierprops=dict(marker="o", ms=3, alpha=0.45),
    )
    for patch in bp["boxes"]:
        patch.set_facecolor("#4C72B0")
        patch.set_alpha(0.7)
    ax.set_xticks(range(1, len(muni_order) + 1))
    ax.set_xticklabels(muni_order, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("$H_s$ at event date (m)")
    ax.set_title(
        "$H_s$ distribution by municipality — reported events database\n"
        "(reanalysis values at event date  ·  ordered by median)",
        fontsize=10,
    )
    plt.tight_layout()
    save_fig(fig, "fig_D2_Hs_boxplot_by_municipality")

    # ── Fig D3: Hs boxplot by coastal sector ──────────────────────────
    sector_order_hs = (
        df.groupby("coastal_sector")["hs_m"].median()
        .sort_values(ascending=False).index.tolist()
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    data_bp2  = [df.loc[df["coastal_sector"] == s, "hs_m"].dropna().values for s in sector_order_hs]
    colors_bp = [SECTOR_COLORS.get(s, "#aaaaaa") for s in sector_order_hs]
    bp2 = ax.boxplot(
        data_bp2, patch_artist=True, showfliers=True,
        medianprops=dict(color="black", lw=1.5),
        flierprops=dict(marker="o", ms=4, alpha=0.5),
    )
    for patch, col in zip(bp2["boxes"], colors_bp):
        patch.set_facecolor(col)
        patch.set_alpha(0.75)
    ax.set_xticks(range(1, len(sector_order_hs) + 1))
    ax.set_xticklabels(sector_order_hs, rotation=15, ha="right", fontsize=9.5)
    ax.set_ylabel("$H_s$ at event date (m)")
    ax.set_title(
        "$H_s$ distribution by coastal sector — reported events database\n"
        "(ordered by median)",
        fontsize=10,
    )
    plt.tight_layout()
    save_fig(fig, "fig_D3_Hs_boxplot_by_sector")

    # ── Fig D4: monthly event count (seasonality) ─────────────────────
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly = df.dropna(subset=["date"]).groupby(df["date"].dt.month).size()

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(monthly.index, monthly.values, color="#2ca02c", edgecolor="white", lw=0.5)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names)
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of events")
    ax.set_title(
        "Monthly distribution of reported coastal disasters\n"
        "Santa Catarina — all sectors combined",
        fontsize=10,
    )
    plt.tight_layout()
    save_fig(fig, "fig_D4_monthly_seasonality")

    return muni_count, sector_count


# ── Part E: Municipality–grid association ─────────────────────────────────────

def run_municipality_grid_association(
    df_events: pd.DataFrame,
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
) -> pd.DataFrame:
    """
    Part E: fetch IBGE coordinates and associate municipalities to the
    WAVERYS/GLORYS grid via nearest-neighbour search.
    """
    log.info("== Part E: Municipality–grid association ==")

    municipalities = sorted(df_events["municipality"].dropna().unique().tolist())
    log.info("Unique municipalities in database: %d", len(municipalities))

    muni_coords = fetch_ibge_coords(municipalities)

    grid_table = build_grid_table(
        muni_coords,
        ds_wave.latitude.values, ds_wave.longitude.values,
        ds_gl.latitude.values,  ds_gl.longitude.values,
    )

    # Attach coastal sector from events
    sector_map = df_events.groupby("municipality")["coastal_sector"].first()
    grid_table["coastal_sector"] = grid_table["municipality"].map(sector_map)

    cols = ["municipality", "coastal_sector", "muni_lat", "muni_lon",
            "in_test_domain", "wave_grid_lat", "wave_grid_lon", "wave_dist_km",
            "gl_grid_lat", "gl_grid_lon", "gl_dist_km"]
    grid_table = grid_table[[c for c in cols if c in grid_table.columns]]

    out = CFG["tab_dir"] / "tab_municipality_grid_association.csv"
    grid_table.to_csv(out, index=False)
    log.info("  -> tab_municipality_grid_association.csv")

    n_in  = grid_table["in_test_domain"].sum()
    n_out = (~grid_table["in_test_domain"]).sum()
    log.info("  %d municipalities IN test domain | %d OUTSIDE", n_in, n_out)
    if n_out > 0:
        outside = grid_table.loc[~grid_table["in_test_domain"], "municipality"].tolist()
        log.info("  Outside domain: %s", outside)

    return grid_table


# ── Part F: Per-sector figures ────────────────────────────────────────────────

def run_sector_figures(
    df_events: pd.DataFrame,
    grid_table: pd.DataFrame,
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
) -> None:
    """
    Part F: one figure per coastal sector, 1×3 layout.

    Left panel   — map: municipality locations, nearest grid points, domain bbox.
    Centre panel — Hs boxplot.
    Right panel  — SSH boxplot.

    Municipality ordering in boxplots: by latitude (south to north),
    consistent with the SC coastline orientation.

    Municipalities inside the test domain → boxplots use the full WAVERYS/GLORYS
    time series (1993–2025).
    Municipalities outside the test domain → Hs boxplot uses reanalysis values
    from the reported events spreadsheet (only at event dates).
    SSH boxplots are only available for in-domain municipalities.

    Note on missing SSH panels: sectors whose municipalities all fall outside
    the test domain (North and Central-north) have no SSH grid data available.
    This is a geographic limitation of the test cutout, not a data error.
    """
    log.info("== Part F: Per-sector figures ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]
    lat_w  = ds_wave.latitude.values
    lon_w  = ds_wave.longitude.values
    sectors = sorted(df_events["coastal_sector"].dropna().unique().tolist())

    for sector in sectors:
        log.info("  Sector: %s", sector)
        color = SECTOR_COLORS.get(sector, "gray")

        sector_munis = df_events[df_events["coastal_sector"] == sector]["municipality"].unique()
        gt_sec = grid_table[grid_table["municipality"].isin(sector_munis)].copy()
        gt_in  = gt_sec[gt_sec["in_test_domain"]].copy()

        # Sort cities south to north (ascending latitude)
        gt_sec_sorted = gt_sec.sort_values("muni_lat", ascending=True)
        gt_in_sorted  = gt_in.sort_values("muni_lat", ascending=True)
        munis_all = gt_sec_sorted["municipality"].tolist()
        munis_in  = gt_in_sorted["municipality"].tolist()

        # Extract grid time series for in-domain municipalities
        hs_grid:  dict[str, np.ndarray] = {}
        zos_grid: dict[str, np.ndarray] = {}
        for _, row in gt_in_sorted.iterrows():
            muni = row["municipality"]
            raw = da_hs.sel(
                latitude=row["wave_grid_lat"], longitude=row["wave_grid_lon"],
                method="nearest",
            ).values
            hs_grid[muni] = raw[np.isfinite(raw)]
            raw = da_zos.sel(
                latitude=row["gl_grid_lat"], longitude=row["gl_grid_lon"],
                method="nearest",
            ).values
            zos_grid[muni] = raw[np.isfinite(raw)]

        # Hs from events spreadsheet (for out-of-domain municipalities)
        hs_events: dict[str, np.ndarray] = {
            m: df_events.loc[df_events["municipality"] == m, "hs_m"].dropna().values
            for m in munis_all
        }

        # ── Figure: 1×3 layout ────────────────────────────────────────
        n_all = max(len(munis_all), 1)
        n_in_d = max(len(munis_in), 1)
        # Width: map (2 units) + Hs boxplot + SSH boxplot, each min 3 cm per city
        box_w = max(3.5, n_all * 0.9)
        fig_w = min(22, 6 + box_w + max(2.5, n_in_d * 0.9))
        fig   = plt.figure(figsize=(fig_w, 6.5))
        gs    = GridSpec(
            1, 3, figure=fig,
            width_ratios=[1.8, box_w / 4, max(2.5, n_in_d * 0.9) / 4],
            wspace=0.35,
        )
        ax_map = fig.add_subplot(gs[0, 0], projection=_CRS)
        ax_hs  = fig.add_subplot(gs[0, 1])
        ax_zos = fig.add_subplot(gs[0, 2])

        # ── Map panel (cartopy) ───────────────────────────────────────
        all_lats = gt_sec_sorted["muni_lat"].dropna().tolist() + [lat_w.min(), lat_w.max()]
        all_lons = gt_sec_sorted["muni_lon"].dropna().tolist() + [lon_w.min(), lon_w.max()]
        pad_map = 0.35
        ax_map.set_extent(
            [min(all_lons) - pad_map, max(all_lons) + pad_map,
             min(all_lats) - pad_map, max(all_lats) + pad_map],
            crs=_CRS,
        )

        ax_map.add_feature(_ne("physical", "land",  facecolor="#f0ede8"), zorder=0)
        ax_map.add_feature(_ne("physical", "ocean", facecolor="#daeeff"), zorder=0)
        ax_map.add_feature(
            _ne("physical", "coastline", edgecolor="black", facecolor="none"),
            linewidth=0.8, zorder=3,
        )
        ax_map.add_feature(
            _ne("cultural", "admin_1_states_provinces_lines",
                edgecolor="dimgray", facecolor="none"),
            linewidth=0.5, zorder=3,
        )

        gl = ax_map.gridlines(
            draw_labels=True, linewidth=0.4, color="gray",
            alpha=0.5, linestyle="--", crs=_CRS,
        )
        gl.top_labels   = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 7}
        gl.ylabel_style = {"size": 7}

        for _, row in gt_sec_sorted.iterrows():
            if pd.isna(row["muni_lat"]):
                continue
            if row["in_test_domain"]:
                ax_map.plot(
                    row["muni_lon"], row["muni_lat"], "o",
                    color=color, ms=8, mec="black", mew=0.6,
                    zorder=5, transform=_CRS,
                )
                ax_map.plot(
                    row["wave_grid_lon"], row["wave_grid_lat"], "s",
                    mfc="none", mec=color, mew=1.3, ms=7,
                    zorder=4, transform=_CRS,
                )
                ax_map.plot(
                    [row["muni_lon"], row["wave_grid_lon"]],
                    [row["muni_lat"], row["wave_grid_lat"]],
                    "k--", lw=0.55, alpha=0.4,
                    zorder=3, transform=_CRS,
                )
            else:
                ax_map.plot(
                    row["muni_lon"], row["muni_lat"], "o",
                    mfc="white", mec="gray", ms=7, mew=0.9,
                    zorder=5, transform=_CRS,
                )
            ax_map.text(
                row["muni_lon"] + 0.04, row["muni_lat"] + 0.04,
                row["municipality"],
                fontsize=5.5, color="black",
                transform=_CRS, zorder=6,
            )

        # Domain bounding box
        ax_map.add_patch(Rectangle(
            (lon_w.min(), lat_w.min()),
            lon_w.max() - lon_w.min(), lat_w.max() - lat_w.min(),
            lw=1.0, edgecolor="dimgray", facecolor="none",
            ls=":", alpha=0.8, transform=_CRS, zorder=4,
        ))

        ax_map.set_title(f"Sector: {sector}", fontsize=10, fontweight="bold")
        legend_elems = [
            Line2D([0], [0], marker="o", color="w", markerfacecolor=color,
                   mec="black", ms=7, label="City (in domain)"),
            Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
                   mec="gray", ms=7, label="City (outside domain)"),
            Line2D([0], [0], marker="s", color="w", markerfacecolor="none",
                   mec=color, ms=7, label="Nearest WAVERYS point"),
            Line2D([0], [0], color="dimgray", ls=":", lw=1.0, label="Test domain"),
        ]
        ax_map.legend(handles=legend_elems, fontsize=6, loc="best")

        # ── Hs boxplot ────────────────────────────────────────────────
        # In-domain: full grid time series; out-of-domain: events spreadsheet Hs
        bp_labels: list[str] = []
        bp_data:   list[np.ndarray] = []
        bp_is_grid: list[bool] = []

        for m in munis_all:
            if m in hs_grid and len(hs_grid[m]) > 0:
                bp_labels.append(m)
                bp_data.append(hs_grid[m])
                bp_is_grid.append(True)
            elif len(hs_events.get(m, [])) > 0:
                bp_labels.append(m)
                bp_data.append(hs_events[m])
                bp_is_grid.append(False)

        if bp_data:
            bp_hs = ax_hs.boxplot(
                bp_data, patch_artist=True, showfliers=True,
                medianprops=dict(color="black", lw=1.4),
                flierprops=dict(marker="o", ms=2.5, alpha=0.4),
            )
            for patch, is_grid in zip(bp_hs["boxes"], bp_is_grid):
                patch.set_facecolor(color if is_grid else "lightgray")
                patch.set_alpha(0.75)
            ax_hs.set_xticks(range(1, len(bp_labels) + 1))
            ax_hs.set_xticklabels(bp_labels, rotation=45, ha="right", fontsize=7.5)
            ax_hs.set_ylabel("$H_s$ (m)", fontsize=9)
            ax_hs.set_title("$H_s$", fontsize=10, fontweight="bold")
            # Legend explaining colour coding
            from matplotlib.patches import Patch
            ax_hs.legend(
                handles=[
                    Patch(facecolor=color, alpha=0.75, label="Grid series (1993–2025)"),
                    Patch(facecolor="lightgray", alpha=0.75, label="Events DB only"),
                ],
                fontsize=6.5, loc="upper right",
            )
        else:
            ax_hs.text(0.5, 0.5, "No Hs data", transform=ax_hs.transAxes,
                       ha="center", va="center", fontsize=9, color="gray")
            ax_hs.set_title("$H_s$", fontsize=10, fontweight="bold")

        # ── SSH boxplot ───────────────────────────────────────────────
        zos_labels: list[str] = []
        zos_data:   list[np.ndarray] = []
        for m in munis_in:
            if m in zos_grid and len(zos_grid[m]) > 0:
                zos_labels.append(m)
                zos_data.append(zos_grid[m])

        if zos_data:
            bp_zos = ax_zos.boxplot(
                zos_data, patch_artist=True, showfliers=True,
                medianprops=dict(color="black", lw=1.4),
                flierprops=dict(marker="o", ms=2.5, alpha=0.4),
            )
            for patch in bp_zos["boxes"]:
                patch.set_facecolor("steelblue")
                patch.set_alpha(0.7)
            ax_zos.set_xticks(range(1, len(zos_labels) + 1))
            ax_zos.set_xticklabels(zos_labels, rotation=45, ha="right", fontsize=7.5)
            ax_zos.set_ylabel("SSH (m)", fontsize=9)
            ax_zos.set_title("SSH", fontsize=10, fontweight="bold")
        else:
            # Explain why SSH is absent — geographic limitation of the test domain
            ax_zos.text(
                0.5, 0.55,
                "No SSH grid data\nfor this sector",
                transform=ax_zos.transAxes,
                ha="center", va="center", fontsize=9, color="gray",
            )
            ax_zos.text(
                0.5, 0.35,
                f"All {len(sector_munis)} sector municipalities\nare outside the test domain\n"
                f"({lat_w.min():.1f}° to {lat_w.max():.1f}°S)",
                transform=ax_zos.transAxes,
                ha="center", va="center", fontsize=7.5, color="gray",
                style="italic",
            )
            ax_zos.set_title("SSH", fontsize=10, fontweight="bold")

        safe_name = sector.replace(" ", "_").replace("-", "_")
        save_fig(fig, f"fig_F_{safe_name}_sector")


# ── Part G: Additional analyses ───────────────────────────────────────────────

def run_additional_analyses(
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
    df_events: pd.DataFrame,
    grid_table: pd.DataFrame,
) -> None:
    """
    Part G: supplementary exploratory analyses.
      G1 — Descriptive statistics by municipality (table)
      G2 — Scatter Hs vs SSH (domain daily means)
      G3 — Monthly seasonal cycle
      G4 — Compound co-occurrence quick-look [EDA only]
      G5 — Top simultaneous Hs/SSH events (table + highlighted time series)
      G6 — Marginal distributions of Hs and SSH
    """
    log.info("== Part G: Additional analyses ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]

    # Domain-mean daily time series (common base for comparisons)
    hs_daily  = da_hs.mean(["latitude", "longitude"]).resample(time="1D").mean()
    zos_daily = da_zos.mean(["latitude", "longitude"]).resample(time="1D").mean()

    common = np.intersect1d(hs_daily.time.values, zos_daily.time.values)
    hs_c   = hs_daily.sel(time=common).values
    zos_c  = zos_daily.sel(time=common).values
    times  = pd.to_datetime(common)

    valid  = np.isfinite(hs_c) & np.isfinite(zos_c)
    hs_v, zos_v, t_v = hs_c[valid], zos_c[valid], times[valid]

    # ── G1: descriptive statistics by municipality ─────────────────────
    gt_in = grid_table[grid_table["in_test_domain"]].copy()
    stats_rows = []
    for _, row in gt_in.iterrows():
        hs_s = da_hs.sel(
            latitude=row["wave_grid_lat"], longitude=row["wave_grid_lon"],
            method="nearest",
        ).values
        zos_s = da_zos.sel(
            latitude=row["gl_grid_lat"], longitude=row["gl_grid_lon"],
            method="nearest",
        ).values
        hs_s  = hs_s[np.isfinite(hs_s)]
        zos_s = zos_s[np.isfinite(zos_s)]
        if len(hs_s) == 0 or len(zos_s) == 0:
            continue
        stats_rows.append({
            "municipality":  row["municipality"],
            "coastal_sector": row.get("coastal_sector", pd.NA),
            "hs_mean":   np.nanmean(hs_s),
            "hs_median": np.nanmedian(hs_s),
            "hs_p75":    np.nanpercentile(hs_s, 75),
            "hs_p90":    np.nanpercentile(hs_s, 90),
            "hs_p99":    np.nanpercentile(hs_s, 99),
            "hs_max":    np.nanmax(hs_s),
            "zos_mean":  np.nanmean(zos_s),
            "zos_median":np.nanmedian(zos_s),
            "zos_p75":   np.nanpercentile(zos_s, 75),
            "zos_p90":   np.nanpercentile(zos_s, 90),
            "zos_p99":   np.nanpercentile(zos_s, 99),
            "zos_max":   np.nanmax(zos_s),
        })

    if stats_rows:
        pd.DataFrame(stats_rows).to_csv(
            CFG["tab_dir"] / "tab_descriptive_stats_by_municipality.csv", index=False
        )
        log.info("  -> tab_descriptive_stats_by_municipality.csv")

    # ── G2: scatter Hs vs SSH ─────────────────────────────────────────
    r_val, p_val = pearsonr(hs_v, zos_v)

    q_hs  = np.nanpercentile(hs_v, CFG["compound_hs_quantile"]  * 100)
    q_zos = np.nanpercentile(zos_v, CFG["compound_zos_quantile"] * 100)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sc = ax.scatter(hs_v, zos_v, c=t_v.year, cmap="viridis", s=4, alpha=0.35, lw=0)
    cb = fig.colorbar(sc, ax=ax, pad=0.01, shrink=0.9)
    cb.set_label("Year")
    ax.axvline(q_hs,  color="#d62728",  ls="--", lw=0.9, alpha=0.8,
               label=f"$H_s$ q{int(CFG['compound_hs_quantile']*100)} = {q_hs:.2f} m")
    ax.axhline(q_zos, color="steelblue", ls="--", lw=0.9, alpha=0.8,
               label=f"SSH q{int(CFG['compound_zos_quantile']*100)} = {q_zos:.3f} m")
    ax.set_xlabel("Domain-mean daily $H_s$ (m)")
    ax.set_ylabel("Domain-mean daily SSH (m)")
    ax.set_title(
        f"$H_s$ vs SSH — domain daily means\n"
        f"Pearson r = {r_val:.3f}  "
        f"({'p < 0.001' if p_val < 0.001 else f'p = {p_val:.3f}'})",
        fontsize=10,
    )
    ax.legend(fontsize=8)
    plt.tight_layout()
    save_fig(fig, "fig_G2_scatter_Hs_SSH")

    # ── G3: seasonal cycle ────────────────────────────────────────────
    hs_df  = pd.DataFrame({"hs":  hs_c,  "month": times.month})
    zos_df = pd.DataFrame({"zos": zos_c, "month": times.month})

    def _monthly_stats(series: pd.Series) -> pd.DataFrame:
        return series.groupby("month")[series.columns[-1]].agg(
            median="median",
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
        )

    hs_mon  = hs_df.groupby("month")["hs"].agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
    )
    zos_mon = zos_df.groupby("month")["zos"].agg(
        median="median",
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
    )
    months      = np.arange(1, 13)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True)
    ax1.plot(months, hs_mon["median"].values, color="#d62728", lw=2, marker="o", ms=5)
    ax1.fill_between(months, hs_mon["q25"].values, hs_mon["q75"].values,
                     color="#d62728", alpha=0.18, label="IQR")
    ax1.set_ylabel("Domain-mean $H_s$ (m)")
    ax1.set_title("Seasonal cycle — monthly median (1993–2025)", fontsize=10)
    ax1.legend(fontsize=8)

    ax2.plot(months, zos_mon["median"].values, color="steelblue", lw=2, marker="o", ms=5)
    ax2.fill_between(months, zos_mon["q25"].values, zos_mon["q75"].values,
                     color="steelblue", alpha=0.18, label="IQR")
    ax2.set_ylabel("Domain-mean SSH (m)")
    ax2.set_xticks(months)
    ax2.set_xticklabels(month_names)
    ax2.legend(fontsize=8)
    plt.tight_layout()
    save_fig(fig, "fig_G3_seasonal_cycle")

    # ── G4: compound co-occurrence quick-look [EDA] ───────────────────
    # NOTE: thresholds are empirical quantiles for exploratory purposes only.
    # They do NOT constitute a final compound-event definition for the study.
    compound = (hs_v >= q_hs) & (zos_v >= q_zos)
    n_comp = compound.sum()
    pct    = 100 * n_comp / len(hs_v)
    log.info(
        "  Compound quick-look [EDA]: Hs >= q%.0f (%.2f m) AND SSH >= q%.0f (%.3f m) "
        "-> %d days (%.1f%%)",
        CFG["compound_hs_quantile"] * 100, q_hs,
        CFG["compound_zos_quantile"] * 100, q_zos,
        n_comp, pct,
    )

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.scatter(hs_v[~compound], zos_v[~compound],
               color="#999999", s=4, alpha=0.25, lw=0, label="Background")
    ax.scatter(
        hs_v[compound], zos_v[compound],
        color="crimson", s=12, alpha=0.75, lw=0,
        label=(
            f"Co-occurrence [EDA]\n"
            f"$H_s$\u2265q{int(CFG['compound_hs_quantile']*100)} "
            f"& SSH\u2265q{int(CFG['compound_zos_quantile']*100)}\n"
            f"n = {n_comp} days ({pct:.1f}%)"
        ),
    )
    ax.axvline(q_hs,  color="#d62728",   ls="--", lw=0.9, alpha=0.8)
    ax.axhline(q_zos, color="steelblue", ls="--", lw=0.9, alpha=0.8)
    ax.set_xlabel("Domain-mean daily $H_s$ (m)")
    ax.set_ylabel("Domain-mean daily SSH (m)")
    ax.set_title(
        "Compound co-occurrence quick-look  [Exploratory EDA]\n"
        "Empirical quantile thresholds — not a final event definition",
        fontsize=9.5,
    )
    ax.legend(fontsize=8)
    plt.tight_layout()
    save_fig(fig, "fig_G4_compound_quicklook")

    # ── G5: top compound events ───────────────────────────────────────
    compound_df = pd.DataFrame({
        "date":        t_v[compound],
        "hs_mean_m":   hs_v[compound],
        "ssh_mean_m":  zos_v[compound],
        "hs_ssh_sum":  hs_v[compound] + zos_v[compound],
    }).sort_values("hs_ssh_sum", ascending=False).head(20)
    compound_df.to_csv(CFG["tab_dir"] / "tab_top_compound_events_eda.csv", index=False)
    log.info("  -> tab_top_compound_events_eda.csv (%d EDA events)", len(compound_df))

    # Time series figure — last 10 years for legibility
    t_start  = t_v.max() - pd.DateOffset(years=10)
    mask_plt = t_v >= t_start
    t_plt    = t_v[mask_plt]
    hs_plt   = hs_v[mask_plt]
    zos_plt  = zos_v[mask_plt]

    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    ax_a.plot(t_plt, hs_plt, color="#d62728", lw=0.75, alpha=0.85)
    ax_a.axhline(q_hs, color="#d62728", ls="--", lw=0.9, alpha=0.7,
                 label=f"q{int(CFG['compound_hs_quantile']*100)} = {q_hs:.2f} m")
    ax_a.set_ylabel("$H_s$ (m)")
    ax_a.set_title(
        f"Domain-mean daily time series (last 10 years) with compound highlights [EDA]\n"
        f"Red lines = days with $H_s$ \u2265 q{int(CFG['compound_hs_quantile']*100)} "
        f"AND SSH \u2265 q{int(CFG['compound_zos_quantile']*100)}",
        fontsize=9.5,
    )
    ax_a.legend(fontsize=8)

    ax_b.plot(t_plt, zos_plt, color="steelblue", lw=0.75, alpha=0.85)
    ax_b.axhline(q_zos, color="steelblue", ls="--", lw=0.9, alpha=0.7,
                 label=f"q{int(CFG['compound_zos_quantile']*100)} = {q_zos:.3f} m")
    ax_b.set_ylabel("SSH (m)")
    ax_b.legend(fontsize=8)
    _fmt_time_ax(ax_b, minor=False)

    for t_comp in t_v[compound]:
        if t_comp >= t_start:
            for ax in (ax_a, ax_b):
                ax.axvline(pd.Timestamp(t_comp), color="crimson", lw=0.6, alpha=0.35)

    plt.tight_layout()
    save_fig(fig, "fig_G5_timeseries_compound_highlights")

    # ── G6: marginal distributions ────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    ax1.hist(hs_v, bins=60, color="#d62728", edgecolor="white", lw=0.3, alpha=0.8,
             density=True)
    ax1.axvline(q_hs, color="black", ls="--", lw=1.1,
                label=f"q{int(CFG['compound_hs_quantile']*100)} = {q_hs:.2f} m")
    ax1.axvline(np.nanmedian(hs_v), color="#d62728", ls="-", lw=1.1,
                label=f"Median = {np.nanmedian(hs_v):.2f} m")
    ax1.set_xlabel("Domain-mean daily $H_s$ (m)")
    ax1.set_ylabel("Density")
    ax1.set_title("$H_s$ distribution\n(daily means, 1993–2025)", fontsize=10)
    ax1.legend(fontsize=8)

    ax2.hist(zos_v, bins=60, color="steelblue", edgecolor="white", lw=0.3, alpha=0.8,
             density=True)
    ax2.axvline(q_zos, color="black", ls="--", lw=1.1,
                label=f"q{int(CFG['compound_zos_quantile']*100)} = {q_zos:.3f} m")
    ax2.axvline(np.nanmedian(zos_v), color="steelblue", ls="-", lw=1.1,
                label=f"Median = {np.nanmedian(zos_v):.3f} m")
    ax2.set_xlabel("Domain-mean daily SSH (m)")
    ax2.set_ylabel("Density")
    ax2.set_title("SSH distribution\n(daily means, 1993–2025)", fontsize=10)
    ax2.legend(fontsize=8)

    plt.tight_layout()
    save_fig(fig, "fig_G6_distributions_Hs_SSH")


# ── Data directory README files ───────────────────────────────────────────────

def write_data_readmes() -> None:
    """Write README.md files for data/test/ and data/test/reported events/."""
    log.info("== Writing README files ==")
    _write_test_readme()
    _write_events_readme()


def _write_test_readme() -> None:
    path = ROOT / "data/test/README.md"
    path.write_text(
        """\
# data/test/

Test datasets for the OSR11 project, used for exploratory development and
validation of the coastal risk analysis pipeline.

These are small domain cutouts of the operational datasets, covering the southern
Santa Catarina coast (approx. −29.4 to −27.6°S, −50 to −48°W) for the full 1993–2025 period.

## Files

### `waverys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | WAVERYS (Copernicus Marine — GLOBAL_MULTIYEAR_WAV_001_032) |
| Variables           | `VHM0` — spectral significant wave height (m) · `VMDR` — mean wave direction (°) |
| Temporal resolution | 3-hourly                                       |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 10 latitude × 11 longitude points (~0.2° spacing) |
| Purpose             | Exploratory analysis of wave conditions, southern SC coast |

### `glorys_sc_sul_test.nc`

| Field               | Value                                          |
|---------------------|------------------------------------------------|
| Source              | GLORYS12 (Copernicus Marine — GLOBAL_MULTIYEAR_PHY_001_030) |
| Variables           | `zos` — sea surface height (m, relative to mean sea level) |
| Temporal resolution | Daily                                          |
| Period              | 1993-01-01 to 2025-12-31                       |
| Grid                | 25 latitude × 25 longitude points (~1/12° ≈ 0.083° spacing) |
| Purpose             | Exploratory analysis of sea level variability, southern SC coast |

## Spatial domain

```
Latitude:  −29.4°S to −27.6°S
Longitude: −50.0°W to −48.0°W
```

This domain covers the southern portion of the Santa Catarina coast, roughly from
the Florianópolis–Palhoça area southward to near the border with Rio Grande do Sul.

> ⚠️ **Important**: Municipalities in the northern and central-north sectors of SC
> (e.g. Itapoá, São Francisco do Sul, Balneário Camboriú, Navegantes) are **outside**
> this test domain. Grid-based statistics are therefore unavailable for those municipalities.

> 📊 **Analysis scope**: The exploratory script `explore_testdata.py` filters the 
> reported events dataset to **South sector municipalities only**, to match this 
> limited domain. This is clearly documented in the code and outputs.

## Known limitations

- Test cutouts only — they do not replace the full operational datasets.
- The domain does not cover the entire Santa Catarina coastline.
- **Exploratory analyses (Parts A–B) use a single nearshore point** (closest to coast)
  for co-located Hs and SSH evaluation, rather than independent spatial maxima.
- Results from these files are exploratory and should not be interpreted as final.

## Subdirectories

- `reported events/` — Excel table of declared coastal disasters in SC (1998–2023)
""",
        encoding="utf-8",
    )
    log.info("  -> data/test/README.md")


def _write_events_readme() -> None:
    path = ROOT / "data/reported events/README.md"
    path.write_text(
        """\
# data/test/reported events/

## `reported_events_Karine_sc.csv`

Table of 105 coastal disasters declared by municipalities in Santa Catarina (SC), Brazil,
covering the period 1998–2023.

**Note**: This CSV file is generated from the original `reported_events_Karine_sc.xlsx`
using the preprocessing script `src/preprocessing/convert_reported_events.py`.

## Source

> Leal, K.B., Robaina, L.E.S., Körting, T.S. et al. Identification of coastal natural
> disasters using official databases to provide support for the coastal management:
> the case of Santa Catarina, Brazil.
> *Nat Hazards* **120**, 11465–11482 (2024).
> <https://doi.org/10.1007/s11069-023-06150-3>

The database was constructed from Brazilian official civil defence records and public
registers to identify coastal natural disasters associated with wave and meteorological
forcing events.

## File structure

The original Excel spreadsheet has two header rows:
- **Row 0**: full table caption (long string)
- **Row 1**: actual column names

The CSV file is generated with `skiprows=1` to use row 1 as the header.

Correct reading: `pd.read_csv(path)`.

## Column descriptions

| Original name                          | Internal name (snake_case) | Description                                                        |
|----------------------------------------|----------------------------|--------------------------------------------------------------------|
| Disaster ID                            | disaster_id                | Event identifier (integer; may repeat across municipalities for the same event) |
| Dates of occurrence (mm/dd/yyyy)       | date                       | Date of disaster declaration                                       |
| Months                                 | month                      | Month name (text)                                                  |
| Municipalities                         | municipality               | Municipality name (Portuguese)                                     |
| Coastal Sectors                        | coastal_sector             | Coastal sector: North, Central-north, Central, Central-south, South |
| EM or SPC                              | disaster_type              | Disaster classification code; `*` = not available                 |
| hgt                                    | hgt_m                      | Geopotential height at 500 hPa (m)                                 |
| Wspd (m/s)                             | wspd_ms                    | Wind speed (m/s)                                                   |
| Wdir (m/s)                             | wdir_deg                   | Wind direction (°) — column label says "m/s" but values are degrees |
| Hs (m)                                 | hs_m                       | Significant wave height at event date (m), extracted from reanalysis |
| Hsdir (°)                              | hsdir_deg                  | Mean wave direction (°)                                            |
| HsPp (s)                               | hspp_s                     | Peak period (s)                                                    |
| WP                                     | weather_pattern            | Weather pattern classification (integer code)                      |
| Number of Human Damage                 | n_human_damage             | Number of people affected; `*` = not available                     |
| Material Damage (BRL)                  | material_damage_brl        | Material damage in BRL; `*` = not available                        |
| Environmental Damage (BRL)             | env_damage_brl             | Environmental damage in BRL; `*` = not available                   |
| Public Economic Losses (BRL)           | public_losses_brl          | Public economic losses in BRL; `*` = not available                 |
| Private Economic Losses (BRL)          | private_losses_brl         | Private economic losses in BRL; `*` = not available                |

## Missing data

The asterisk (`*`) in the original file indicates information not available in source records.
The loading script converts `*` to `NaN`.

## Limitations

1. **Geographic scope**: SC coastal municipalities only; not the full Brazilian coastline.
2. **Temporal coverage**: 1998–2023 (non-continuous; depends on official declarations).
3. **Non-unique Disaster ID**: one event may affect multiple municipalities under the same ID.
4. **Undeclared events**: physically significant events not officially declared are absent.
5. **Unit inconsistency**: the `Wdir` column is labelled "m/s" in the original file,
   but values are in degrees (°). Preserved as observed — no automatic correction applied.
6. **Monetary values**: expressed in BRL at year of occurrence; no inflation adjustment.
7. **Hs and atmospheric variables**: extracted from reanalysis at the event date —
   they are not direct observations.
""",
        encoding="utf-8",
    )
    log.info("  -> data/reported events/README.md")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    set_pub_style()
    make_output_dirs()

    log.info("=" * 62)
    log.info("OSR11 — Test data EDA")
    log.info("Project root: %s", ROOT)
    log.info("=" * 62)

    ds_wave   = load_wave_data()
    ds_gl     = load_glorys_data()
    df_events = load_reported_events()

    # Part A: spatial maximum maps
    max_hs, max_zos = run_spatial_analysis(ds_wave, ds_gl)

    # Part B: time series at peak grid points
    run_timeseries_analysis(ds_wave, ds_gl, max_hs, max_zos)

    # Part D: reported events EDA
    run_reported_events_eda(df_events)

    # Part E: IBGE coordinates + grid association
    grid_table = run_municipality_grid_association(df_events, ds_wave, ds_gl)

    # Part F: per-sector figures
    run_sector_figures(df_events, grid_table, ds_wave, ds_gl)

    # Part G: additional analyses
    run_additional_analyses(ds_wave, ds_gl, df_events, grid_table)

    # Write data directory README files
    write_data_readmes()

    log.info("=" * 62)
    log.info("EDA complete.")
    log.info("  Figures : %s", CFG["fig_dir"])
    log.info("  Tables  : %s", CFG["tab_dir"])
    log.info("=" * 62)


if __name__ == "__main__":
    main()
