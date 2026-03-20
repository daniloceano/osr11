"""
Part A — Spatial maximum analysis and map generation.

Identifies the temporal maximum of Hs and SSH at a single nearshore grid point
and generates:
- Spatial map panels with Hs shading and SSH contours.
- Short-window time series panels centred on the event peak.

Nearshore-point strategy
------------------------
The nearshore point is selected as the non-NaN WAVERYS grid cell that is
closest to the Natural Earth 10 m coastline (minimum distance to any coastline
vertex among all valid ocean cells within *max_coastal_dist_km*).  This is
physically and scientifically correct: it guarantees the selected cell
(a) carries actual ocean model data and (b) lies nearest to the land–sea
boundary, which is where compound wave–surge impacts are felt.

Previous heuristic (minimum longitude) was not valid for domains where the
coastline deviates from a meridional orientation.  The NE-coastline approach
works for any domain geometry.

Both Hs and SSH are evaluated at the same co-located nearshore point so that
the two variables refer to the same geographic location, which is the analysis
intent for compound event assessment at the coast.
"""
from __future__ import annotations

import logging

import sys
from pathlib import Path
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.gridspec import GridSpec

# Add project root to sys.path to enable absolute imports
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import STYLE
from src.explore_test_data_south_sc.utils import fmt_time_ax, peaks_coincident, save_fig, span, vline

log = logging.getLogger(__name__)

# Cartopy projection used throughout (data are in geographic lon/lat)
_CRS = ccrs.PlateCarree()


def _ne(category: str, name: str, scale: str = "10m", **kw) -> cfeature.NaturalEarthFeature:
    """Return a pre-styled NaturalEarthFeature."""
    return cfeature.NaturalEarthFeature(category, name, scale, **kw)


# ── Public analysis function ──────────────────────────────────────────────────

def run_spatial_analysis(
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
) -> tuple[dict, dict]:
    """Part A: identify Hs and SSH maxima at a single nearshore point.

    Both variables are evaluated at the same grid point (the coastal WAVERYS
    cell closest to the NE 10 m coastline) so co-location is guaranteed.

    Generates figures with:
    - Two maps (top): WAVERYS period-maximum Hs and GLORYS period-maximum SSH,
      each masked to coastal grid points only.
    - Two time series panels (bottom): Hs and SSH at the nearshore point,
      restricted to a window around the reference event date.

    Returns
    -------
    max_hs, max_zos : dict
        Each dict contains: value, time, lat, lon, t_idx, lat_idx, lon_idx.
    """
    from src.explore_test_data_south_sc.coastal import find_coastal_points

    log.info("== Part A: Spatial maximum analysis (nearshore point) ==")

    da_hs  = ds_wave[CFG["wave_var"]]
    da_zos = ds_gl[CFG["ssl_var"]]

    # ── Coastal masks for both grids ──────────────────────────────────────
    wave_coastal, _ = find_coastal_points(
        da_hs.latitude.values, da_hs.longitude.values,
        da_hs.mean(dim="time").values,
        shp_path=CFG["ne_coastline_shp"], max_dist_km=CFG["max_coastal_dist_km"],
    )
    gl_coastal, _ = find_coastal_points(
        da_zos.latitude.values, da_zos.longitude.values,
        da_zos.mean(dim="time").values,
        shp_path=CFG["ne_coastline_shp"], max_dist_km=CFG["max_coastal_dist_km"],
    )

    # ── Period-maximum fields (coastal points only) ───────────────────────
    hs_max_arr  = da_hs.max("time").values.copy()
    zos_max_arr = da_zos.max("time").values.copy()
    hs_max_arr[~wave_coastal]  = np.nan   # mask non-coastal cells
    zos_max_arr[~gl_coastal]   = np.nan

    # Wrap back as DataArrays to keep coordinate info
    hs_max_field  = da_hs.max("time").copy(data=hs_max_arr)
    zos_max_field = da_zos.max("time").copy(data=zos_max_arr)

    # ── Nearshore point ───────────────────────────────────────────────────
    nearshore = _find_nearshore_point(da_hs)

    hs_at_point  = da_hs.sel(
        latitude=nearshore["lat"], longitude=nearshore["lon"], method="nearest"
    )
    zos_at_point = da_zos.sel(
        latitude=nearshore["lat"], longitude=nearshore["lon"], method="nearest"
    )

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
            subtitle="Coincident peaks — combined figure",
        )
    else:
        _spatial_event_fig(
            hs_max_field, zos_max_field, da_hs, da_zos,
            max_hs, max_zos, t_ref=max_hs["time"],
            fname="fig_A1a_spatial_max_Hs_event",
            subtitle=f"Centred on $H_s$ peak — {max_hs['time'].strftime('%Y-%m-%d')}",
        )
        _spatial_event_fig(
            hs_max_field, zos_max_field, da_hs, da_zos,
            max_hs, max_zos, t_ref=max_zos["time"],
            fname="fig_A1b_spatial_max_SSH_event",
            subtitle=f"Centred on SSH peak — {max_zos['time'].strftime('%Y-%m-%d')}",
        )

    return max_hs, max_zos


# ── Spatial utility functions ─────────────────────────────────────────────────

def find_spatial_max(da: xr.DataArray) -> dict:
    """Find the global maximum of a DataArray and return its time and location.

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


# ── Internal helpers ──────────────────────────────────────────────────────────

def _find_nearshore_point(da: xr.DataArray) -> dict:
    """Return the nearshore grid point closest to the Natural Earth coastline.

    Strategy
    --------
    1. Compute the temporal mean of the DataArray to identify valid (non-NaN)
       ocean cells.
    2. Load the NE 10 m coastline vertices from the local shapefile.
    3. Build a KDTree on coastline vertices (approximate-km coordinates).
    4. Among all valid cells within *max_coastal_dist_km* of the coastline,
       select the cell with the minimum distance to any coastline vertex.

    This replaces the previous heuristic of minimum longitude, which was not
    scientifically valid for non-meridional coastlines.
    """
    from src.explore_test_data_south_sc.coastal import find_coastal_points

    lat_vals  = da.latitude.values
    lon_vals  = da.longitude.values
    data_mean = da.mean(dim="time").values

    coastal_mask, dist_to_coast = find_coastal_points(
        lat_vals, lon_vals, data_mean,
        shp_path    = CFG["ne_coastline_shp"],
        max_dist_km = CFG["max_coastal_dist_km"],
    )

    if not coastal_mask.any():
        log.warning(
            "No coastal grid points found via NE coastline — "
            "falling back to minimum-longitude heuristic."
        )
        valid_mask = ~np.isnan(data_mean)
        vi, vj = np.where(valid_mask)
        min_pos = int(np.argmin(lon_vals[vj]))
        i_lat, i_lon = int(vi[min_pos]), int(vj[min_pos])
    else:
        # Among coastal cells, pick the one with minimum distance to coastline
        coast_dists  = dist_to_coast.copy()
        coast_dists[~coastal_mask] = np.inf
        i_lat, i_lon = np.unravel_index(np.argmin(coast_dists), coast_dists.shape)
        i_lat, i_lon = int(i_lat), int(i_lon)

    log.info(
        "Nearshore point (NE coastline): (%.2f°S, %.2f°W) | dist to coast = %.1f km",
        lat_vals[i_lat], lon_vals[i_lon],
        float(dist_to_coast[i_lat, i_lon]) if not np.isnan(dist_to_coast[i_lat, i_lon]) else -1,
    )

    return {
        "lat":     float(lat_vals[i_lat]),
        "lon":     float(lon_vals[i_lon]),
        "lat_idx": i_lat,
        "lon_idx": i_lon,
    }


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
    """Two coastal maps (top) + Hs and SSH time series (bottom).

    Layout
    ------
    - Row 0 (maps): left = WAVERYS period-max Hs (coastal points only);
                    right = GLORYS period-max SSH (coastal points only).
      No legends on the maps — the nearshore point is annotated directly.
    - Row 1: Hs time series at the nearshore point.
    - Row 2: SSH time series at the nearshore point.
      Time series info is placed in the subplot title, not in legends.

    Time series panels are restricted to [t_ref ± window/2] via xlim.
    """
    win = CFG["timeseries_window_days"]
    t0  = t_ref - pd.Timedelta(days=win // 2)
    t1  = t_ref + pd.Timedelta(days=win // 2)

    hs_ts  = da_hs.sel(
        latitude=max_hs["lat"], longitude=max_hs["lon"], method="nearest"
    ).sel(time=slice(t0, t1))
    zos_ts = da_zos.sel(
        latitude=max_zos["lat"], longitude=max_zos["lon"], method="nearest"
    ).sel(time=slice(t0, t1))

    fig = plt.figure(figsize=(STYLE.fig_width_double + 2, 11))
    gs  = GridSpec(
        3, 2, figure=fig,
        height_ratios=[2.4, 1, 1],
        hspace=0.25, wspace=0.15,
    )
    ax_map_hs  = fig.add_subplot(gs[0, 0], projection=_CRS)
    ax_map_ssh = fig.add_subplot(gs[0, 1], projection=_CRS)
    ax_hs      = fig.add_subplot(gs[1, :])
    ax_zos     = fig.add_subplot(gs[2, :])

    lon_w = hs_max_field.longitude.values
    lat_w = hs_max_field.latitude.values
    lon_g = zos_max_field.longitude.values
    lat_g = zos_max_field.latitude.values
    pad   = 0.12

    def _base_map(ax: plt.Axes, lon: np.ndarray, lat: np.ndarray) -> None:
        ax.set_extent(
            [lon.min() - pad, lon.max() + pad, lat.min() - pad, lat.max() + pad],
            crs=_CRS,
        )
        ax.add_feature(_ne("physical", "land",  facecolor="#f0ede8"), zorder=0)
        ax.add_feature(_ne("physical", "ocean", facecolor="#daeeff"), zorder=0)
        ax.add_feature(
            _ne("physical", "coastline", edgecolor="black", facecolor="none"),
            linewidth=0.8, zorder=3,
        )
        ax.add_feature(
            _ne("cultural", "admin_1_states_provinces_lines",
                edgecolor="dimgray", facecolor="none"),
            linewidth=0.5, zorder=3,
        )
        gl = ax.gridlines(
            draw_labels=True, linewidth=0.4, color="gray",
            alpha=0.5, linestyle="--", crs=_CRS,
        )
        gl.top_labels   = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 7.5}
        gl.ylabel_style = {"size": 7.5}

    # ── Left map: WAVERYS max Hs (coastal points) ─────────────────────────
    _base_map(ax_map_hs, lon_w, lat_w)
    pcm = ax_map_hs.pcolormesh(
        lon_w, lat_w, hs_max_field.values,
        cmap=STYLE.cmap_hs, shading="auto", transform=_CRS, zorder=1,
    )
    cb = fig.colorbar(pcm, ax=ax_map_hs, pad=0.07, shrink=0.8, aspect=18)
    cb.set_label("Max $H_s$ (m)", fontsize=8.5)
    ax_map_hs.plot(
        max_hs["lon"], max_hs["lat"], "o",
        color="purple", ms=10, mec="white", mew=1.1, zorder=5, transform=_CRS,
    )
    ax_map_hs.set_title(
        f"WAVERYS — period-max $H_s$ (coastal points)\n"
        f"Nearshore point  ·  Peak: {max_hs['time'].strftime('%Y-%m-%d')}",
        fontsize=9,
    )

    # ── Right map: GLORYS max SSH (coastal points) ────────────────────────
    _base_map(ax_map_ssh, lon_g, lat_g)
    # Use pcolormesh for SSH too, with a diverging colormap
    pcm2 = ax_map_ssh.pcolormesh(
        lon_g, lat_g, zos_max_field.values,
        cmap=STYLE.cmap_ssh, shading="auto", transform=_CRS, zorder=1,
    )
    cb2 = fig.colorbar(pcm2, ax=ax_map_ssh, pad=0.07, shrink=0.8, aspect=18)
    cb2.set_label("Max SSH (m)", fontsize=8.5)
    ax_map_ssh.plot(
        max_zos["lon"], max_zos["lat"], "o",
        color="purple", ms=10, mec="white", mew=1.1, zorder=5, transform=_CRS,
    )
    ax_map_ssh.set_title(
        f"GLORYS — period-max SSH (coastal points)\n"
        f"Nearshore point  ·  Peak: {max_zos['time'].strftime('%Y-%m-%d')}",
        fontsize=9,
    )

    # ── Hs time series ────────────────────────────────────────────────────
    t_hs = pd.to_datetime(hs_ts.time.values)
    ax_hs.plot(t_hs, hs_ts.values, color=STYLE.color_hs, lw=1.4)
    vline(ax_hs, max_hs["time"], STYLE.color_hs)
    if t0 <= t_ref <= t1 and t_ref != max_hs["time"]:
        vline(ax_hs, t_ref, "gray")
    span(ax_hs, t_ref, win)
    ax_hs.set_ylabel("$H_s$ (m)")
    ax_hs.set_xlim(pd.Timestamp(t0), pd.Timestamp(t1))
    peak_in_win = t0 <= max_hs["time"] <= t1
    ax_hs.set_title(
        f"$H_s$ at nearshore point ({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)  ·  "
        f"Peak: {max_hs['time'].strftime('%Y-%m-%d %H:%M')} = {max_hs['value']:.2f} m"
        + ("" if peak_in_win else "  [peak outside window]"),
        fontsize=8.5,
    )
    if peak_in_win:
        ax_hs.annotate(
            f"{max_hs['value']:.2f} m",
            xy=(max_hs["time"], max_hs["value"]),
            xytext=(6, 4), textcoords="offset points",
            fontsize=7.5, color=STYLE.color_hs, fontweight="bold",
        )
    fmt_time_ax(ax_hs)

    # ── SSH time series ───────────────────────────────────────────────────
    t_zos = pd.to_datetime(zos_ts.time.values)
    ax_zos.plot(t_zos, zos_ts.values, color=STYLE.color_ssh, lw=1.4)
    vline(ax_zos, max_zos["time"], STYLE.color_ssh)
    if t0 <= t_ref <= t1 and t_ref != max_zos["time"]:
        vline(ax_zos, t_ref, "gray")
    span(ax_zos, t_ref, win)
    ax_zos.set_ylabel("SSH (m)")
    ax_zos.set_xlim(pd.Timestamp(t0), pd.Timestamp(t1))
    peak_in_win_ssh = t0 <= max_zos["time"] <= t1
    ax_zos.set_title(
        f"SSH at nearshore point ({max_zos['lat']:.2f}°S, {max_zos['lon']:.2f}°W)  ·  "
        f"Peak: {max_zos['time'].strftime('%Y-%m-%d')} = {max_zos['value']:.3f} m"
        + ("" if peak_in_win_ssh else "  [peak outside window]"),
        fontsize=8.5,
    )
    fmt_time_ax(ax_zos)

    fig.suptitle(
        f"{subtitle} "
        f" Window: {t0.strftime('%Y-%m-%d')} – {t1.strftime('%Y-%m-%d')}",
        fontsize=12, color="#333333", y=0.92,
    )
    save_fig(fig, fname)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    from config.plot_config import apply_publication_style
    from src.explore_test_data_south_sc.utils import make_output_dirs
    from src.explore_test_data_south_sc.io import load_glorys_data, load_wave_data

    apply_publication_style()
    make_output_dirs()

    _ds_wave = load_wave_data()
    _ds_gl   = load_glorys_data()

    run_spatial_analysis(_ds_wave, _ds_gl)
