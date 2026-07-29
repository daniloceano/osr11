"""Illustrate the opposing behaviour of AUD-01 severity terms B and C.

The diagnostic keeps the production detector unchanged: local q90 episodes of
``zos`` are intersected with local q90 episodes of ``VHM0`` after bridging a
maximum gap of one day.  Astronomical tide is used only after detection.

The upper row contrasts two 60-day windows at a micromareal point in Rio Grande
do Sul and a macromareal point in Maranhão.  The annotated compound-event days
were selected because both occur during high astronomical tide and have similar
dimensionless tidal phase C, while their excess over the local q95 tidal datum
B is strongly different.  The lower row shows this contrast over all native
coastal points using the existing AUD-01 point summary.

This is a read-only exploratory audit.  It does not alter the production
pipeline and writes only below ``outputs/audit/``.

Usage
-----
Run from the repository root::

    python src/exploratory/audit_AUD_01_severity_illustration.py

Outputs
-------
``outputs/audit/AUD-01_severity_illustration/figures/``
    PNG illustration.
``outputs/audit/AUD-01_severity_illustration/selected_windows.csv``
    Daily values, detector mask, and annotations used in the upper panels.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

from config.plot_config import STYLE, apply_publication_style, panel_label


UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
SEVERITY_BY_POINT = (
    ROOT
    / "outputs"
    / "audit"
    / "AUD-01_severity_tide_term"
    / "severity_by_point.csv"
)
DATUM_SENSITIVITY = (
    ROOT
    / "outputs"
    / "audit"
    / "AUD-01_datum_sensitivity"
    / "datum_sensitivity_by_band.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_severity_illustration"
FIGURE_DIR = OUT_DIR / "figures"
FIGURE_PATH = FIGURE_DIR / "AUD-01_severity_illustration.png"
WINDOW_DATA_PATH = OUT_DIR / "selected_windows.csv"

QUANTILE = 0.90
MAX_GAP_DAYS = 1
SETUP_COEFFICIENT = 0.2
DATUM_QUANTILE = 0.95
WINDOW_DAYS = 60

POINTS = (
    {
        "name": "RS",
        "title": "RS — micromareal, dominado pela ressaca",
        "grid_lat": -32.0,
        "grid_lon": -51.8,
        "event_date": "2020-04-03",
    },
    {
        "name": "Maranhão",
        "title": "Maranhão — macromareal, dominado pela maré",
        "grid_lat": -2.4,
        "grid_lon": -44.0,
        "event_date": "2023-12-13",
    },
)

LATITUDE_BANDS = (
    ("RS", -35.0, -30.0),
    ("SC/PR", -30.0, -25.0),
    ("SP/RJ", -25.0, -20.0),
    ("ES/BA-S", -20.0, -15.0),
    ("BA-N", -15.0, -10.0),
    ("NE", -10.0, -5.0),
    ("N_eq", -5.0, 0.0),
    ("AP", 0.0, 7.0),
)

TIDE_COLOR = "#64748b"
TOTAL_COLOR = "#0969a2"
DATUM_COLOR = "#b45309"
EVENT_COLOR = "#f4b942"
B_COLOR = "#146c94"
C_COLOR = "#a33a3a"


def episode_mask(series: np.ndarray, finite: np.ndarray) -> np.ndarray:
    """Return local-q90 exceedance episodes with one-day gaps bridged."""
    threshold = np.nanquantile(series[finite], QUANTILE)
    exceeds = np.where(finite, series >= threshold, False)
    indices = np.flatnonzero(exceeds)
    if indices.size == 0:
        return exceeds
    for k in np.flatnonzero(np.diff(indices) == MAX_GAP_DAYS + 1):
        exceeds[indices[k] : indices[k + 1] + 1] = True
    return exceeds


def extract_point(ds: xr.Dataset, point: dict[str, object]) -> pd.DataFrame:
    """Extract one native point and reproduce the tide-free detector."""
    selected = ds.sel(
        latitude=float(point["grid_lat"]),
        longitude=float(point["grid_lon"]),
        method="nearest",
    )
    frame = selected[["VHM0", "zos", "tide_daily_max"]].to_dataframe().reset_index()
    frame = frame.rename(columns={"time": "date"})
    frame["date"] = pd.to_datetime(frame["date"])

    hs = frame["VHM0"].to_numpy(dtype=float)
    zos = frame["zos"].to_numpy(dtype=float)
    tide = frame["tide_daily_max"].to_numpy(dtype=float)
    finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
    compound = episode_mask(hs, finite) & episode_mask(zos, finite)

    datum = float(np.nanquantile(tide[finite], DATUM_QUANTILE))
    tide_median = float(np.nanmedian(tide[finite]))
    tide_range = float(np.nanmax(tide[finite]) - np.nanmin(tide[finite]))
    frame["total_m"] = zos + tide + SETUP_COEFFICIENT * hs
    frame["datum_m"] = datum
    frame["B_m"] = frame["total_m"] - datum
    frame["C"] = (tide - tide_median) / tide_range
    frame["compound_event"] = compound
    frame["point"] = str(point["name"])
    frame["grid_lat"] = float(selected["latitude"].values)
    frame["grid_lon"] = float(selected["longitude"].values)

    event_date = pd.Timestamp(str(point["event_date"]))
    event_row = frame.loc[frame["date"].eq(event_date)]
    if event_row.empty or not bool(event_row["compound_event"].iloc[0]):
        raise RuntimeError(f"{point['name']}: {event_date.date()} is not compound")

    half_before = WINDOW_DAYS // 2
    start = event_date - pd.Timedelta(days=half_before)
    end = start + pd.Timedelta(days=WINDOW_DAYS - 1)
    return frame.loc[frame["date"].between(start, end)].copy()


def shade_compound_days(ax: plt.Axes, frame: pd.DataFrame) -> None:
    """Shade compound-event days as full one-day intervals."""
    for date in frame.loc[frame["compound_event"], "date"]:
        ax.axvspan(
            date - pd.Timedelta(hours=12),
            date + pd.Timedelta(hours=12),
            color=EVENT_COLOR,
            alpha=0.28,
            linewidth=0,
            zorder=0,
        )


def plot_time_panel(
    ax: plt.Axes, frame: pd.DataFrame, point: dict[str, object], panel: str
) -> None:
    """Plot one 60-day window and annotate B and C on the selected event."""
    shade_compound_days(ax, frame)
    ax.plot(
        frame["date"],
        frame["tide_daily_max"],
        color=TIDE_COLOR,
        lw=STYLE.linewidth_thin,
        label="Máximo diário da maré",
        zorder=2,
    )
    ax.plot(
        frame["date"],
        frame["total_m"],
        color=TOTAL_COLOR,
        lw=STYLE.linewidth_thick,
        label=r"Total = zos + maré + 0,2 H$_s$",
        zorder=3,
    )
    datum = float(frame["datum_m"].iloc[0])
    ax.axhline(
        datum,
        color=DATUM_COLOR,
        lw=1.2,
        ls="--",
        label=f"Datum local q95(maré) = {datum:.2f} m",
        zorder=1,
    )

    event_date = pd.Timestamp(str(point["event_date"]))
    event = frame.loc[frame["date"].eq(event_date)].iloc[0]
    total = float(event["total_m"])
    b_value = float(event["B_m"])
    c_value = float(event["C"])
    ax.annotate(
        "",
        xy=(event_date, total),
        xytext=(event_date, datum),
        arrowprops={
            "arrowstyle": "<->",
            "color": B_COLOR,
            "lw": 1.8,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=5,
    )
    label_x = event_date + pd.Timedelta(days=2)
    ax.text(
        label_x,
        (total + datum) / 2,
        f"Excesso = {b_value * 100:.0f} cm\nFase = {c_value:+.2f}",
        color=B_COLOR,
        fontsize=STYLE.font_size_annotation + 0.5,
        va="center",
        ha="left",
        bbox={"facecolor": "white", "edgecolor": B_COLOR, "alpha": 0.9, "pad": 2.5},
        zorder=6,
    )
    ax.plot(event_date, total, "o", ms=4.5, color=TOTAL_COLOR, zorder=6)
    ax.set_title(str(point["title"]))
    ax.set_ylabel("Nível do mar (m)")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.tick_params(axis="x", rotation=25)
    ax.legend(loc="upper left", frameon=True)
    ax.text(
        -0.04,
        1.02,
        f"({panel})",
        transform=ax.transAxes,
        fontsize=STYLE.font_size_panel_label,
        fontweight=STYLE.panel_label_fontweight,
        ha="left",
        va="bottom",
        clip_on=False,
    )


def latitude_profile(
    ax: plt.Axes, severity: pd.DataFrame, datum_sensitivity: pd.DataFrame
) -> None:
    """Plot point scatter and latitude-binned means of B and C."""
    b_name = "B_excess_over_local_datum_m"
    c_name = "C_dimensionless_tidal_phase"
    clean = severity.dropna(subset=["grid_lat", b_name, c_name]).copy()

    for i, (label, lo, hi) in enumerate(LATITUDE_BANDS):
        if i % 2 == 0:
            ax.axvspan(lo, hi, color="#e2e8f0", alpha=0.34, lw=0, zorder=0)
        ax.axvline(lo, color="#94a3b8", lw=0.45, alpha=0.55, zorder=0)
        ax.text(
            (lo + hi) / 2,
            0.97,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=7.2,
            color="#475569",
        )
    ax.axvline(7.0, color="#94a3b8", lw=0.45, alpha=0.55, zorder=0)

    ax_c = ax.twinx()

    datum_columns = [
        "excess_q90_permissive_m",
        "excess_q95_MHWS_proxy_m",
        "excess_q99_high_springs_m",
        "excess_max_HAT_estimate_m",
    ]
    band_centres = {
        label: (lo + hi) / 2 for label, lo, hi in LATITUDE_BANDS
    }
    sensitivity = datum_sensitivity.copy()
    sensitivity["latitude"] = sensitivity["latitude_band"].replace(
        {"N_equatorial": "N_eq"}
    ).map(band_centres)
    sensitivity = sensitivity.dropna(subset=["latitude"]).sort_values("latitude")
    envelope_min = sensitivity[datum_columns].min(axis=1)
    envelope_max = sensitivity[datum_columns].max(axis=1)
    ax.fill_between(
        sensitivity["latitude"].to_numpy(dtype=float),
        envelope_min.to_numpy(dtype=float),
        envelope_max.to_numpy(dtype=float),
        color=B_COLOR,
        alpha=0.10,
        linewidth=0,
        label="Envelope: q90, q95, q99 e HAT",
        zorder=0.5,
    )

    ax.scatter(
        clean["grid_lat"],
        clean[b_name],
        s=10,
        color=B_COLOR,
        alpha=0.18,
        edgecolors="none",
        label="Excesso, pontos nativos",
        zorder=1,
    )
    ax_c.scatter(
        clean["grid_lat"],
        clean[c_name],
        s=10,
        color=C_COLOR,
        alpha=0.16,
        edgecolors="none",
        label="Fase, pontos nativos",
        zorder=1,
    )

    # The native grid is spaced by 0.2°.  A 2° bin suppresses repeated
    # coastline points at the same latitude while retaining the regional shape.
    edges = np.arange(-35.0, 7.0001 + 2.0, 2.0)
    clean["lat_bin"] = pd.cut(clean["grid_lat"], edges, include_lowest=True)
    binned = clean.groupby("lat_bin", observed=True).agg(
        latitude=("grid_lat", "mean"),
        B=(b_name, "mean"),
        C=(c_name, "mean"),
    )
    ax.plot(
        binned["latitude"],
        binned["B"],
        color=B_COLOR,
        lw=2.6,
        label="Excesso, média em faixas de 2°",
        zorder=4,
    )
    ax_c.plot(
        binned["latitude"],
        binned["C"],
        color=C_COLOR,
        lw=2.4,
        label="Fase, média em faixas de 2°",
        zorder=4,
    )
    ax_c.axhline(0.0, color=C_COLOR, lw=0.7, ls=":", alpha=0.8)

    rho_b = clean[b_name].corr(clean["grid_lat"].abs(), method="spearman")
    rho_c = clean[c_name].corr(clean["grid_lat"].abs(), method="spearman")
    ax.text(
        0.015,
        0.08,
        (
            rf"Spearman vs |latitude|:  excesso = {rho_b:+.3f}"
            rf"   fase = {rho_c:+.3f}"
        ),
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9, "pad": 3},
        zorder=8,
    )

    ax.set_xlim(-35.0, 7.0)
    ax.set_xlabel("Latitude (°N)")
    ax.set_ylabel("Excesso de água acima do datum (m)", color=B_COLOR)
    ax_c.set_ylabel("Fase da maré (adimensional)", color=C_COLOR)
    ax.tick_params(axis="y", colors=B_COLOR)
    ax_c.tick_params(axis="y", colors=C_COLOR)
    ax_c.spines["right"].set_visible(True)
    ax_c.spines["right"].set_color(C_COLOR)
    ax.set_title("Perfil costeiro nos 808 pontos nativos")
    handles_b, labels_b = ax.get_legend_handles_labels()
    handles_c, labels_c = ax_c.get_legend_handles_labels()
    ax.legend(
        handles_b + handles_c,
        labels_b + labels_c,
        ncol=2,
        loc="upper left",
        bbox_to_anchor=(0.0, 0.91),
        frameon=True,
    )
    panel_label(ax, "c")


def main() -> None:
    """Generate the illustration and its reproducibility table."""
    for path in (UNIFIED, SEVERITY_BY_POINT, DATUM_SENSITIVITY):
        if not path.exists():
            raise FileNotFoundError(path)

    apply_publication_style()
    with xr.open_dataset(UNIFIED) as ds:
        windows = [extract_point(ds, point) for point in POINTS]
    severity = pd.read_csv(SEVERITY_BY_POINT)
    datum_sensitivity = pd.read_csv(DATUM_SENSITIVITY)

    selected = pd.concat(windows, ignore_index=True)
    selected["is_annotated_day"] = False
    for point in POINTS:
        selected.loc[
            selected["point"].eq(point["name"])
            & selected["date"].eq(pd.Timestamp(str(point["event_date"]))),
            "is_annotated_day",
        ] = True

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    selected[
        [
            "point",
            "grid_lat",
            "grid_lon",
            "date",
            "VHM0",
            "zos",
            "tide_daily_max",
            "total_m",
            "datum_m",
            "B_m",
            "C",
            "compound_event",
            "is_annotated_day",
        ]
    ].to_csv(WINDOW_DATA_PATH, index=False)

    fig = plt.figure(figsize=(13.0, 9.0))
    grid = fig.add_gridspec(2, 2, height_ratios=(1.0, 1.18), hspace=0.34, wspace=0.18)
    time_axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]

    for ax, frame, point, label in zip(time_axes, windows, POINTS, ("a", "b")):
        plot_time_panel(ax, frame, point, label)

    # A shared scale is essential to the intended visual comparison.
    y_min = min(float(frame[["tide_daily_max", "total_m", "datum_m"]].min().min()) for frame in windows)
    y_max = max(float(frame[["tide_daily_max", "total_m", "datum_m"]].max().max()) for frame in windows)
    padding = 0.08 * (y_max - y_min)
    for ax in time_axes:
        ax.set_ylim(y_min - padding, y_max + padding)

    profile_ax = fig.add_subplot(grid[1, :])
    latitude_profile(profile_ax, severity, datum_sensitivity)
    fig.suptitle(
        "AUD-01 — Maré na severidade: excesso de água versus fase da maré",
        fontsize=13,
        fontweight="bold",
        y=0.985,
    )
    fig.savefig(FIGURE_PATH, dpi=STYLE.dpi_export, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved figure: {FIGURE_PATH}")
    print(f"Saved supporting data: {WINDOW_DATA_PATH}")
    for point, frame in zip(POINTS, windows):
        event = frame.loc[frame["date"].eq(pd.Timestamp(str(point["event_date"])))].iloc[0]
        print(
            f"{point['name']}: {point['event_date']}, "
            f"B={event['B_m'] * 100:.1f} cm, C={event['C']:+.3f}"
        )


if __name__ == "__main__":
    main()
