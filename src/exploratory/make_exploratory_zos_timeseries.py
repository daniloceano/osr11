"""Plot daily GLORYS12 ``zos`` and ``zos'`` at eight Brazilian coastal points.

Four exploratory figures are produced: the complete 1993--2025 record and the
2020--2025 subset for both the raw sea-surface height above the geoid (``zos``)
and its local-mean anomaly (``zos' = zos - mean(zos, 1993--2025)``).

Missing point files are downloaded directly from Copernicus Marine. The target
coordinates come from the project's canonical municipality--grid association;
the coordinates displayed in the panels are the native GLORYS12 cells actually
returned by the nearest-coordinate selection.
"""

from __future__ import annotations

import json
import string
from datetime import datetime, timezone
from pathlib import Path

import copernicusmarine
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import theilslopes


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "outputs" / "exploratory_hs_zos_trends"
DATA_DIR = OUTPUT_DIR / "data" / "zos_points"
DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
START_DATE = "1993-01-01"
END_DATE = "2025-12-31"
RECENT_START = "2020-01-01"

# Requested coordinates are the ocean cells assigned to the named coastal
# municipalities in data/external/municipal_grid_association/.
POINTS = (
    ("rio_grande", "Rio Grande", -32.4, -52.2),
    ("florianopolis", "Florianópolis", -27.8, -48.4),
    ("santos", "Santos", -24.0, -46.4),
    ("sul_bahia", "Sul da Bahia (Belmonte)", -16.0, -38.8),
    ("recife", "Recife", -8.2, -34.8),
    ("natal", "Natal", -5.8, -35.0),
    ("sao_luis", "São Luís", -2.4, -44.2),
    ("macapa", "Macapá", 0.8, -50.2),
)


def _download_missing_point(slug: str, latitude: float, longitude: float) -> Path:
    """Download one nearest native-grid daily ``zos`` series when absent."""
    path = DATA_DIR / f"{slug}.nc"
    if path.exists():
        return path
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    copernicusmarine.subset(
        dataset_id=DATASET_ID,
        variables=["zos"],
        start_datetime=START_DATE,
        end_datetime=END_DATE,
        minimum_longitude=longitude,
        maximum_longitude=longitude,
        minimum_latitude=latitude,
        maximum_latitude=latitude,
        coordinates_selection_method="nearest",
        service="timeseries",
        output_directory=DATA_DIR,
        output_filename=path.name,
        overwrite=True,
        disable_progress_bar=True,
    )
    return path


def _load_series() -> tuple[dict[str, pd.Series], list[dict[str, object]]]:
    series: dict[str, pd.Series] = {}
    points_metadata: list[dict[str, object]] = []
    for slug, label, requested_lat, requested_lon in POINTS:
        path = _download_missing_point(slug, requested_lat, requested_lon)
        with xr.open_dataset(path) as dataset:
            values = dataset["zos"].squeeze(drop=True).load()
            times = pd.DatetimeIndex(dataset["time"].values)
            native_lat = float(dataset["latitude"].values[0])
            native_lon = float(dataset["longitude"].values[0])
        point_series = pd.Series(values.values.astype(float), index=times, name=slug)
        if point_series.isna().any():
            raise ValueError(f"{label}: downloaded zos series contains missing values")
        series[slug] = point_series
        points_metadata.append(
            {
                "slug": slug,
                "label": label,
                "requested_latitude": requested_lat,
                "requested_longitude": requested_lon,
                "native_latitude": native_lat,
                "native_longitude": native_lon,
                "n_daily_values": int(len(point_series)),
                "local_mean_zos_m": round(float(point_series.mean()), 6),
                "source_file": str(path.relative_to(ROOT)),
            }
        )
    return series, points_metadata


def _add_location_map(
    figure: plt.Figure,
    grid_spec: object,
    metadata: list[dict[str, object]],
) -> plt.Axes:
    """Add a Brazil-coast locator map keyed to time-series panels A--H."""
    projection = ccrs.PlateCarree()
    axis = figure.add_subplot(grid_spec, projection=projection)
    axis.set_extent((-56.5, -32.0, -35.5, 6.0), crs=projection)
    axis.set_facecolor("#EAF3F8")
    axis.add_feature(
        cfeature.LAND.with_scale("50m"),
        facecolor="#D8D8D4",
        edgecolor="none",
        zorder=0,
    )
    axis.add_feature(
        cfeature.COASTLINE.with_scale("50m"),
        edgecolor="#30363B",
        linewidth=0.7,
        zorder=1,
    )
    axis.add_feature(
        cfeature.BORDERS.with_scale("50m"),
        edgecolor="#777777",
        linewidth=0.45,
        zorder=1,
    )
    gridlines = axis.gridlines(
        draw_labels=True,
        linewidth=0.3,
        color="#84929A",
        alpha=0.55,
        linestyle="--",
        x_inline=False,
        y_inline=False,
    )
    gridlines.top_labels = False
    gridlines.right_labels = False
    gridlines.xlabel_style = {"size": 7.5}
    gridlines.ylabel_style = {"size": 7.5}

    for panel, point in zip(string.ascii_uppercase, metadata):
        latitude = float(point["native_latitude"])
        longitude = float(point["native_longitude"])
        axis.scatter(
            longitude,
            latitude,
            transform=projection,
            s=34,
            facecolor="#D7191C",
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
        )
        axis.annotate(
            panel,
            xy=(longitude, latitude),
            xytext=(5, 0),
            textcoords="offset points",
            transform=projection,
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#111111",
            path_effects=[],
            zorder=5,
        )
    axis.set_title("Localização dos pontos", fontsize=10.5, fontweight="bold", pad=7)
    return axis


def _plot(
    series: dict[str, pd.Series],
    metadata: list[dict[str, object]],
    *,
    anomaly: bool,
    recent: bool,
) -> Path:
    plot_series: dict[str, pd.Series] = {}
    for slug, values in series.items():
        transformed = values - values.mean() if anomaly else values
        if recent:
            transformed = transformed.loc[RECENT_START:END_DATE]
        plot_series[slug] = transformed

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
                axis = figure.add_subplot(
                    layout[row, column],
                    sharex=shared_x_axis,
                )
                if shared_x_axis is None:
                    shared_x_axis = axis
                axes[row, column] = axis
        _add_location_map(figure, layout[:, 2], metadata)
        axes_flat = list(axes.flat)
        for panel, axis, point in zip(string.ascii_uppercase, axes_flat, metadata):
            slug = str(point["slug"])
            values = plot_series[slug]
            axis.plot(
                values.index,
                values.values,
                color="#176B87" if not anomaly else "#B24C63",
                linewidth=0.45 if not recent else 0.65,
                rasterized=True,
            )
            if not recent:
                annual = values.resample("YS").mean()
                years = annual.index.year.to_numpy(dtype=float)
                slope, intercept, _, _ = theilslopes(
                    annual.to_numpy(dtype=float), years, alpha=0.95
                )
                trend_dates = pd.to_datetime(
                    [f"{int(years[0])}-01-01", f"{int(years[-1])}-12-31"]
                )
                trend_values = intercept + slope * np.array([years[0], years[-1]])
                axis.plot(
                    trend_dates,
                    trend_values,
                    color="#111111",
                    linewidth=1.35,
                    linestyle="--",
                    label=f"Theil–Sen: {slope * 1000:+.2f} mm ano⁻¹",
                    zorder=4,
                )
                axis.legend(
                    loc="upper left",
                    fontsize=7.5,
                    frameon=True,
                    framealpha=0.88,
                    handlelength=2.2,
                )
            if anomaly:
                axis.axhline(0.0, color="#555555", linewidth=0.65, linestyle=":", zorder=1)
            value_range = float(values.max() - values.min())
            padding = 0.06 * value_range if value_range > 0 else 0.05
            axis.set_ylim(float(values.min() - padding), float(values.max() + padding))
            axis.grid(True, color="#AAB4BA", linewidth=0.35, alpha=0.55, linestyle="--")
            axis.set_title(
                f"{panel}  {point['label']}",
                loc="left",
                fontweight="bold",
                pad=4,
            )
            axis.set_ylabel("zos′ (m)" if anomaly else "zos (m)")

        locator = mdates.YearLocator(1 if recent else 5)
        formatter = mdates.DateFormatter("%Y")
        for axis in axes[-1, :]:
            axis.xaxis.set_major_locator(locator)
            axis.xaxis.set_major_formatter(formatter)
            axis.set_xlabel("Ano")
        for axis in axes[:-1, :].flat:
            axis.tick_params(axis="x", labelbottom=False)
        for axis in axes_flat:
            axis.tick_params(axis="x", rotation=0)

        variable = "zos′" if anomaly else "zos"
        period = "2020–2025" if recent else "1993–2025"
        figure.suptitle(
            f"Séries temporais diárias de {variable} — costa brasileira ({period})",
            fontsize=13,
            fontweight="bold",
            y=0.995,
        )
        figure.subplots_adjust(
            left=0.055,
            right=0.98,
            bottom=0.07,
            top=0.935,
        )
        suffix = "2020_2025" if recent else "1993_2025"
        variable_slug = "zos_prime" if anomaly else "zos"
        output = OUTPUT_DIR / f"{variable_slug}_timeseries_{suffix}.png"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        figure.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(figure)
    return output


def main() -> None:
    series, points_metadata = _load_series()
    outputs = [
        _plot(series, points_metadata, anomaly=False, recent=False),
        _plot(series, points_metadata, anomaly=True, recent=False),
        _plot(series, points_metadata, anomaly=False, recent=True),
        _plot(series, points_metadata, anomaly=True, recent=True),
    ]
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": DATASET_ID,
        "source_product": "GLOBAL_MULTIYEAR_PHY_001_030 (GLORYS12V1)",
        "temporal_resolution": "daily mean",
        "full_period": [START_DATE, END_DATE],
        "recent_period": [RECENT_START, END_DATE],
        "zos_definition": "sea_surface_height_above_geoid",
        "zos_prime_definition": "zos - local mean(zos) over 1993-01-01 to 2025-12-31",
        "shared_y_limits_within_each_figure": False,
        "locator_map": "Brazilian coast with native GLORYS12 points keyed A-H",
        "trend": {
            "estimator": "Theil-Sen slope fitted to annual means",
            "displayed_on": "1993-2025 figures only",
            "reported_unit": "mm per year",
        },
        "points": points_metadata,
        "outputs": [str(path.relative_to(ROOT)) for path in outputs],
    }
    metadata_path = OUTPUT_DIR / "zos_timeseries_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for path in outputs:
        print(path.relative_to(ROOT))
    print(metadata_path.relative_to(ROOT))


if __name__ == "__main__":
    main()
