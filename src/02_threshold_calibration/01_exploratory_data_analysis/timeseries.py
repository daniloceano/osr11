"""
Part B — Time series at peak grid points.

Generates a four-panel figure showing Hs and SSH at both the Hs-peak and
SSH-peak grid points, each panel with its own explicit temporal window to
keep the x-axis clean regardless of whether the two peaks are coincident.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

# Allow running this module directly (python timeseries.py)
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.explore_test_data_south_sc.config.analysis_config import CFG
from config.plot_config import STYLE
from src.explore_test_data_south_sc.utils import fmt_time_ax, save_fig, span, vline

log = logging.getLogger(__name__)


def run_timeseries_analysis(
    ds_wave: xr.Dataset,
    ds_gl: xr.Dataset,
    max_hs: dict,
    max_zos: dict,
) -> None:
    """Part B: time series at the grid points of maximum Hs and maximum SSH.

    Four panels, each with explicit xlim:
    - Panel 0: Hs at Hs-peak point, window around Hs peak.
    - Panel 1: SSH at Hs-peak point, same window.
    - Panel 2: SSH at SSH-peak point, window around SSH peak.
    - Panel 3: Hs at SSH-peak point, same window.
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

    def _win(t_ref: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
        return (
            t_ref - pd.Timedelta(days=win // 2),
            t_ref + pd.Timedelta(days=win // 2),
        )

    def _extract(
        da: xr.DataArray, lat: float, lon: float,
        t0: pd.Timestamp, t1: pd.Timestamp,
    ) -> xr.DataArray:
        return da.sel(latitude=lat, longitude=lon, method="nearest").sel(
            time=slice(t0, t1)
        )

    t0_hs, t1_hs   = _win(max_hs["time"])
    t0_zos, t1_zos = _win(max_zos["time"])

    fig, axes = plt.subplots(4, 1, figsize=(STYLE.fig_width_double + 1, 10))

    # ── Panel 0: Hs at Hs-peak point ────────────────────────────────────
    ser = _extract(da_hs, max_hs["lat"], max_hs["lon"], t0_hs, t1_hs)
    axes[0].plot(pd.to_datetime(ser.time.values), ser.values,
                 color=STYLE.color_hs, lw=1.4)
    vline(axes[0], max_hs["time"], STYLE.color_hs)
    span(axes[0], max_hs["time"], win)
    axes[0].set_xlim(pd.Timestamp(t0_hs), pd.Timestamp(t1_hs))
    axes[0].set_ylabel("$H_s$ (m)")
    axes[0].set_title(
        f"$H_s$ at Hs-peak point  ({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[0].annotate(
        f"Max = {max_hs['value']:.2f} m\n{max_hs['time'].strftime('%Y-%m-%d %H:%M')}",
        xy=(max_hs["time"], max_hs["value"]),
        xytext=(10, -18), textcoords="offset points",
        fontsize=7.5, color=STYLE.color_hs,
        arrowprops=dict(arrowstyle="-", color=STYLE.color_hs, lw=0.7),
    )
    fmt_time_ax(axes[0])

    # ── Panel 1: SSH at Hs-peak point ───────────────────────────────────
    ser = _extract(da_zos, max_hs["lat"], max_hs["lon"], t0_hs, t1_hs)
    axes[1].plot(pd.to_datetime(ser.time.values), ser.values,
                 color=STYLE.color_ssh, lw=1.4)
    vline(axes[1], max_hs["time"], STYLE.color_hs, label="Hs peak")
    span(axes[1], max_hs["time"], win)
    axes[1].set_xlim(pd.Timestamp(t0_hs), pd.Timestamp(t1_hs))
    axes[1].set_ylabel("SSH (m)")
    axes[1].set_title(
        f"SSH at Hs-peak point  ({max_hs['lat']:.2f}°S, {max_hs['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[1].legend(fontsize=7.5, loc="upper left")
    fmt_time_ax(axes[1])

    # ── Panel 2: SSH at SSH-peak point ──────────────────────────────────
    ser = _extract(da_zos, max_zos["lat"], max_zos["lon"], t0_zos, t1_zos)
    axes[2].plot(pd.to_datetime(ser.time.values), ser.values,
                 color=STYLE.color_ssh, lw=1.4)
    vline(axes[2], max_zos["time"], STYLE.color_ssh)
    span(axes[2], max_zos["time"], win)
    axes[2].set_xlim(pd.Timestamp(t0_zos), pd.Timestamp(t1_zos))
    axes[2].set_ylabel("SSH (m)")
    axes[2].set_title(
        f"SSH at SSH-peak point  ({max_zos['lat']:.2f}°S, {max_zos['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[2].annotate(
        f"Max = {max_zos['value']:.3f} m\n{max_zos['time'].strftime('%Y-%m-%d')}",
        xy=(max_zos["time"], max_zos["value"]),
        xytext=(10, -18), textcoords="offset points",
        fontsize=7.5, color=STYLE.color_ssh,
        arrowprops=dict(arrowstyle="-", color=STYLE.color_ssh, lw=0.7),
    )
    fmt_time_ax(axes[2])

    # ── Panel 3: Hs at SSH-peak point ───────────────────────────────────
    ser = _extract(da_hs, max_zos["lat"], max_zos["lon"], t0_zos, t1_zos)
    axes[3].plot(pd.to_datetime(ser.time.values), ser.values,
                 color=STYLE.color_hs, lw=1.4)
    vline(axes[3], max_zos["time"], STYLE.color_ssh, label="SSH peak")
    span(axes[3], max_zos["time"], win)
    axes[3].set_xlim(pd.Timestamp(t0_zos), pd.Timestamp(t1_zos))
    axes[3].set_ylabel("$H_s$ (m)")
    axes[3].set_title(
        f"$H_s$ at SSH-peak point  ({max_zos['lat']:.2f}°S, {max_zos['lon']:.2f}°W)",
        fontsize=9,
    )
    axes[3].legend(fontsize=7.5, loc="upper left")
    fmt_time_ax(axes[3])

    fig.suptitle(
        "Time series at peak-value grid points\n"
        "(dashed line = peak instant  ·  shaded band = time window)",
        fontsize=10, y=1.01,
    )
    plt.tight_layout()
    save_fig(fig, "fig_B1_timeseries_at_maxima")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )
    from config.plot_config import apply_publication_style
    from src.explore_test_data_south_sc.utils import make_output_dirs
    from src.explore_test_data_south_sc.io import load_glorys_data, load_wave_data
    from src.explore_test_data_south_sc.maps import run_spatial_analysis

    apply_publication_style()
    make_output_dirs()

    _ds_wave = load_wave_data()
    _ds_gl   = load_glorys_data()
    _max_hs, _max_zos = run_spatial_analysis(_ds_wave, _ds_gl)

    run_timeseries_analysis(_ds_wave, _ds_gl, _max_hs, _max_zos)
