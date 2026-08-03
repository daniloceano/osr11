"""Generate Hs, Hs*, zos*, and coastal trend figures at eight points.

Definitions
-----------
``Hs``
    Daily maximum of 3-hourly WAVERYS VHM0.
``Hs'`` and ``zos'``
    Raw variable minus its 1993--2025 local temporal mean.
``Hs*`` and ``zos*``
    Prime anomaly minus its 1993--2025 monthly climatology. Thus ``*`` denotes
    a local-mean anomaly with the mean seasonal cycle removed.

Theil--Sen slopes are fitted to annual means, avoiding pseudoreplication from
daily serial correlation. Raw metocean cubes remain on the remote server; this
script consumes only eight-point daily extracts stored below ``outputs/``.
"""

from __future__ import annotations

import json
import string
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import TwoSlopeNorm
from scipy.stats import theilslopes

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exploratory.make_exploratory_zos_timeseries import POINTS, _add_location_map


OUTPUT_DIR = ROOT / "outputs" / "exploratory_hs_zos_trends"
HS_DAILY_CSV = OUTPUT_DIR / "data" / "hs_points" / "hs_daily_max_points.csv"
HS_COORDINATES_CSV = (
    OUTPUT_DIR / "data" / "hs_points" / "hs_daily_max_points_coordinates.csv"
)
ZOS_DATA_DIR = OUTPUT_DIR / "data" / "zos_points"
ALL_COASTAL_TRENDS_CSV = (
    OUTPUT_DIR / "data" / "coastal_trends_all_808_points.csv"
)
START_DATE = "1993-01-01"
END_DATE = "2025-12-31"
RECENT_START = "2020-01-01"


def _labels() -> dict[str, str]:
    return {slug: label for slug, label, _, _ in POINTS}


def _load_hs() -> tuple[dict[str, pd.Series], list[dict[str, Any]]]:
    if not HS_DAILY_CSV.exists() or not HS_COORDINATES_CSV.exists():
        raise FileNotFoundError(
            "Run the remote WAVERYS point extraction first; the processed daily "
            f"files are missing below {OUTPUT_DIR.relative_to(ROOT)}"
        )
    frame = pd.read_csv(HS_DAILY_CSV, parse_dates=["time"], index_col="time")
    coordinates = pd.read_csv(HS_COORDINATES_CSV).set_index("slug")
    labels = _labels()
    series: dict[str, pd.Series] = {}
    metadata: list[dict[str, Any]] = []
    for slug, _, requested_lat, requested_lon in POINTS:
        values = frame[slug].astype(float)
        if values.isna().any():
            raise ValueError(f"{slug}: daily Hs series contains missing values")
        point = coordinates.loc[slug]
        series[slug] = values
        metadata.append(
            {
                "slug": slug,
                "label": labels[slug],
                "requested_latitude": requested_lat,
                "requested_longitude": requested_lon,
                "native_latitude": float(point["native_latitude"]),
                "native_longitude": float(point["native_longitude"]),
                "n_daily_values": int(len(values)),
                "local_mean_hs_m": round(float(values.mean()), 6),
            }
        )
    return series, metadata


def _load_zos() -> dict[str, pd.Series]:
    series: dict[str, pd.Series] = {}
    for slug, label, _, _ in POINTS:
        path = ZOS_DATA_DIR / f"{slug}.nc"
        if not path.exists():
            raise FileNotFoundError(f"Missing processed zos point extract: {path}")
        with xr.open_dataset(path) as dataset:
            values = dataset["zos"].squeeze(drop=True).load().values.astype(float)
            times = pd.DatetimeIndex(dataset["time"].values)
        point_series = pd.Series(values, index=times, name=slug)
        if point_series.isna().any():
            raise ValueError(f"{label}: zos series contains missing values")
        series[slug] = point_series
    return series


def _prime(series: dict[str, pd.Series]) -> dict[str, pd.Series]:
    return {slug: values - values.mean() for slug, values in series.items()}


def _remove_monthly_climatology(
    anomalies: dict[str, pd.Series],
) -> dict[str, pd.Series]:
    deseasonalized: dict[str, pd.Series] = {}
    for slug, values in anomalies.items():
        climatology = values.groupby(values.index.month).mean()
        seasonal = pd.Series(
            values.index.month.map(climatology).to_numpy(dtype=float),
            index=values.index,
        )
        deseasonalized[slug] = values - seasonal
    return deseasonalized


def _theil_sen(values: pd.Series) -> dict[str, float]:
    annual = values.resample("YS").mean()
    years = annual.index.year.to_numpy(dtype=float)
    slope, intercept, low_slope, high_slope = theilslopes(
        annual.to_numpy(dtype=float), years, alpha=0.95
    )
    return {
        "slope_m_per_year": float(slope),
        "slope_mm_per_year": float(slope * 1000),
        "intercept": float(intercept),
        "low_slope_mm_per_year": float(low_slope * 1000),
        "high_slope_mm_per_year": float(high_slope * 1000),
        "first_year": float(years[0]),
        "last_year": float(years[-1]),
    }


def _plot_series_figure(
    series: dict[str, pd.Series],
    metadata: list[dict[str, Any]],
    *,
    symbol: str,
    color: str,
    period_label: str,
    recent: bool,
    show_trend: bool,
    output: Path,
) -> Path:
    plotted = {
        slug: (values.loc[RECENT_START:END_DATE] if recent else values)
        for slug, values in series.items()
    }
    with plt.rc_context(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.linewidth": 0.8,
        }
    ):
        figure = plt.figure(figsize=(16.2, 10.5))
        layout = figure.add_gridspec(
            4, 3, width_ratios=(1.0, 1.0, 0.72), hspace=0.34, wspace=0.17
        )
        axes = np.empty((4, 2), dtype=object)
        shared_x_axis = None
        for row in range(4):
            for column in range(2):
                axis = figure.add_subplot(layout[row, column], sharex=shared_x_axis)
                if shared_x_axis is None:
                    shared_x_axis = axis
                axes[row, column] = axis
        _add_location_map(figure, layout[:, 2], metadata)

        for panel, axis, point in zip(string.ascii_uppercase, axes.flat, metadata):
            slug = str(point["slug"])
            values = plotted[slug]
            axis.plot(
                values.index,
                values.values,
                color=color,
                linewidth=0.45 if not recent else 0.65,
                rasterized=True,
            )
            if show_trend:
                trend = _theil_sen(values)
                trend_dates = pd.to_datetime(
                    [
                        f"{int(trend['first_year'])}-01-01",
                        f"{int(trend['last_year'])}-12-31",
                    ]
                )
                trend_values = trend["intercept"] + trend["slope_m_per_year"] * np.array(
                    [trend["first_year"], trend["last_year"]]
                )
                axis.plot(
                    trend_dates,
                    trend_values,
                    color="#111111",
                    linewidth=1.35,
                    linestyle="--",
                    label=f"Theil–Sen: {trend['slope_mm_per_year']:+.2f} mm ano⁻¹",
                    zorder=4,
                )
                axis.legend(
                    loc="upper left",
                    fontsize=7.5,
                    frameon=True,
                    framealpha=0.88,
                    handlelength=2.2,
                )
            if symbol.endswith(("′", "*")):
                axis.axhline(0.0, color="#555555", linewidth=0.65, linestyle=":")
            value_range = float(values.max() - values.min())
            padding = 0.06 * value_range if value_range > 0 else 0.05
            axis.set_ylim(float(values.min() - padding), float(values.max() + padding))
            axis.grid(True, color="#AAB4BA", linewidth=0.35, alpha=0.55, linestyle="--")
            axis.set_title(f"{panel}  {point['label']}", loc="left", fontweight="bold", pad=4)
            axis.set_ylabel(f"{symbol} (m)")

        locator = mdates.YearLocator(1 if recent else 5)
        formatter = mdates.DateFormatter("%Y")
        for axis in axes[-1, :]:
            axis.xaxis.set_major_locator(locator)
            axis.xaxis.set_major_formatter(formatter)
            axis.set_xlabel("Ano")
        for axis in axes[:-1, :].flat:
            axis.tick_params(axis="x", labelbottom=False)
        figure.suptitle(
            f"Séries temporais diárias de {symbol} — costa brasileira ({period_label})",
            fontsize=13,
            fontweight="bold",
            y=0.995,
        )
        figure.subplots_adjust(left=0.055, right=0.98, bottom=0.07, top=0.935)
        output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(figure)
    return output


def _setup_trend_map(axis: plt.Axes) -> None:
    projection = ccrs.PlateCarree()
    axis.set_extent((-56.5, -32.0, -35.5, 6.0), crs=projection)
    axis.set_facecolor("#EAF3F8")
    axis.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#D8D8D4", edgecolor="none")
    axis.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor="#30363B", linewidth=0.65)
    axis.add_feature(cfeature.BORDERS.with_scale("50m"), edgecolor="#777777", linewidth=0.4)
    grid = axis.gridlines(
        draw_labels=True,
        linewidth=0.3,
        color="#84929A",
        alpha=0.55,
        linestyle="--",
        x_inline=False,
        y_inline=False,
    )
    grid.top_labels = False
    grid.right_labels = False
    grid.xlabel_style = {"size": 7.5}
    grid.ylabel_style = {"size": 7.5}


def _plot_trend_maps(coastal_trends: pd.DataFrame) -> Path:
    specs = (
        ("Hs′", "hs_prime_trend_mm_per_year", "hs"),
        ("zos′", "zos_prime_trend_mm_per_year", "zos"),
        ("Hs*", "hs_star_trend_mm_per_year", "hs"),
        ("zos*", "zos_star_trend_mm_per_year", "zos"),
    )
    limits = {
        family: max(
            float(coastal_trends[field].abs().max())
            for _, field, candidate_family in specs
            if candidate_family == family
        )
        for family in ("hs", "zos")
    }
    projection = ccrs.PlateCarree()
    figure, axes = plt.subplots(
        2,
        2,
        figsize=(10.8, 11.2),
        subplot_kw={"projection": projection},
    )
    for panel, (axis, (symbol, field, family)) in enumerate(zip(axes.flat, specs)):
        _setup_trend_map(axis)
        values = coastal_trends[field].to_numpy(dtype=float)
        limit = max(limits[family], 0.1)
        norm = TwoSlopeNorm(vmin=-limit, vcenter=0.0, vmax=limit)
        scatter = axis.scatter(
            coastal_trends["grid_lon"],
            coastal_trends["grid_lat"],
            c=values,
            cmap="RdBu_r",
            norm=norm,
            s=18,
            edgecolor="none",
            transform=projection,
            zorder=5,
        )
        axis.set_title(f"{string.ascii_uppercase[panel]}  Tendência de {symbol}", fontweight="bold")
        colorbar = figure.colorbar(scatter, ax=axis, orientation="horizontal", pad=0.055, shrink=0.86)
        colorbar.set_label("Theil–Sen (mm ano⁻¹)")
    figure.suptitle(
        f"Tendências costeiras de Hs e zos — {len(coastal_trends)} pontos (1993–2025)",
        fontsize=13,
        fontweight="bold",
        y=0.99,
    )
    figure.subplots_adjust(left=0.07, right=0.97, bottom=0.055, top=0.95, hspace=0.20, wspace=0.16)
    output = OUTPUT_DIR / "hs_zos_trend_maps.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output


def main() -> None:
    hs, metadata = _load_hs()
    zos = _load_zos()
    hs_prime = _prime(hs)
    zos_prime = _prime(zos)
    hs_star = _remove_monthly_climatology(hs_prime)
    zos_star = _remove_monthly_climatology(zos_prime)

    outputs = [
        _plot_series_figure(
            hs,
            metadata,
            symbol="Hs",
            color="#6A3D9A",
            period_label="1993–2025",
            recent=False,
            show_trend=True,
            output=OUTPUT_DIR / "hs_timeseries_1993_2025.png",
        ),
        _plot_series_figure(
            hs_prime,
            metadata,
            symbol="Hs′",
            color="#C06C24",
            period_label="1993–2025",
            recent=False,
            show_trend=True,
            output=OUTPUT_DIR / "hs_prime_timeseries_1993_2025.png",
        ),
        _plot_series_figure(
            hs,
            metadata,
            symbol="Hs",
            color="#6A3D9A",
            period_label="2020–2025",
            recent=True,
            show_trend=False,
            output=OUTPUT_DIR / "hs_timeseries_2020_2025.png",
        ),
        _plot_series_figure(
            hs_prime,
            metadata,
            symbol="Hs′",
            color="#C06C24",
            period_label="2020–2025",
            recent=True,
            show_trend=False,
            output=OUTPUT_DIR / "hs_prime_timeseries_2020_2025.png",
        ),
        _plot_series_figure(
            hs_star,
            metadata,
            symbol="Hs*",
            color="#3A7D44",
            period_label="1993–2025; ciclo sazonal removido",
            recent=False,
            show_trend=True,
            output=OUTPUT_DIR / "hs_star_timeseries_1993_2025.png",
        ),
        _plot_series_figure(
            zos_star,
            metadata,
            symbol="zos*",
            color="#2D6A9F",
            period_label="1993–2025; ciclo sazonal removido",
            recent=False,
            show_trend=True,
            output=OUTPUT_DIR / "zos_star_timeseries_1993_2025.png",
        ),
    ]

    trend_sets = {
        "Hs′": {slug: _theil_sen(values) for slug, values in hs_prime.items()},
        "zos′": {slug: _theil_sen(values) for slug, values in zos_prime.items()},
        "Hs*": {slug: _theil_sen(values) for slug, values in hs_star.items()},
        "zos*": {slug: _theil_sen(values) for slug, values in zos_star.items()},
    }
    if not ALL_COASTAL_TRENDS_CSV.exists():
        raise FileNotFoundError(
            "Missing remote-processed full-coast trends: "
            f"{ALL_COASTAL_TRENDS_CSV.relative_to(ROOT)}"
        )
    coastal_trends = pd.read_csv(ALL_COASTAL_TRENDS_CSV)
    if len(coastal_trends) != 808:
        raise ValueError(f"Expected 808 coastal trend points, found {len(coastal_trends)}")
    outputs.append(_plot_trend_maps(coastal_trends))

    metadata_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": [START_DATE, END_DATE],
        "hs_source": "WAVERYS VHM0, remote 3-hourly raw files aggregated to daily maximum",
        "zos_source": "GLORYS12 zos daily point extracts",
        "prime_definition": "variable - local 1993-2025 temporal mean",
        "star_definition": "prime anomaly - local 1993-2025 monthly climatology",
        "trend_estimator": "Theil-Sen slope fitted to annual means, 95% slope interval",
        "full_coast_trend_points": int(len(coastal_trends)),
        "full_coast_trends_table": str(ALL_COASTAL_TRENDS_CSV.relative_to(ROOT)),
        "points": metadata,
        "trends": trend_sets,
        "outputs": [str(path.relative_to(ROOT)) for path in outputs],
    }
    metadata_path = OUTPUT_DIR / "trend_analysis_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for path in outputs:
        print(path.relative_to(ROOT))
    print(metadata_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
