"""Animate daily GLORYS12 ``zos`` anomalies along the Maranhão–Pará coast.

The plotted field is the 2024 daily sea-surface-height anomaly relative to the
1993–2023 mean for the same calendar day.  GLORYS12 ``zos`` is tide-free
dynamic sea-surface height and is used here as a storm-surge proxy; it can also
contain steric, circulation, and river-discharge signals, especially on the
Amazon shelf.

Run on swell
------------
PATH=/home/danilocs/.conda/envs/cgfd-usp-mpas/bin:$PATH \
python -m src.exploratory.animate_zos_surge_marapa

Inputs
------
data/raw/glorys/glorys_zos_YYYY-MM.nc

Outputs
-------
outputs/exploratory_zos_surge_animation_2024/animations/*.mp4
outputs/exploratory_zos_surge_animation_2024/metadata/animation_metadata.json
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cartopy.io import shapereader
from matplotlib.colors import BoundaryNorm, ListedColormap


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "data/raw/glorys"
DEFAULT_OUTPUT = REPO_ROOT / "outputs/exploratory_zos_surge_animation_2024"
COASTLINE = REPO_ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

# Includes the complete Maranhão–Pará–Amapá coastline and enough adjacent ocean
# to make along-shelf propagation visible.
WEST, EAST, SOUTH, NORTH = -52.0, -41.5, -4.5, 5.5
BASELINE_START, BASELINE_END = 1993, 2023
TARGET_YEAR = 2024
# User-supplied palette, read from right to left and stopped at #661631.
# The first class collects every negative value and the second covers
# 0–0.1 m. Remaining class boundaries are recalculated for each animation so
# that the right edge is exactly the maximum within its domain and period.
SURGE_COLORS = [
    "#525252",
    "#4E4B65",
    "#48519C",
    "#3B7FBD",
    "#D9E545",
    "#E6AF40",
    "#E68E42",
    "#E46E44",
    "#D23A66",
    "#A4294F",
    "#661631",
]
PERIODS = {
    "january_2024_daily": ("2024-01-01", "2024-01-31"),
    "july_2024_daily": ("2024-07-01", "2024-07-31"),
    "year_2024_daily": ("2024-01-01", "2024-12-31"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fps-month", type=int, default=4)
    parser.add_argument("--fps-year", type=int, default=12)
    parser.add_argument("--dpi", type=int, default=150)
    return parser.parse_args()


def input_files(input_dir: Path) -> list[Path]:
    files = sorted(input_dir.glob("glorys_zos_????-??.nc"))
    expected = (TARGET_YEAR - BASELINE_START + 1) * 12
    if len(files) < expected:
        raise FileNotFoundError(
            f"Expected at least {expected} monthly files for "
            f"{BASELINE_START}–{TARGET_YEAR}; found {len(files)} in {input_dir}"
        )
    return files


def load_domain(files: list[Path]) -> xr.DataArray:
    ds = xr.open_mfdataset(
        files,
        combine="by_coords",
        data_vars="minimal",
        coords="minimal",
        compat="override",
        chunks={"time": 366},
    )
    zos = ds["zos"].sel(
        longitude=slice(WEST, EAST),
        latitude=slice(SOUTH, NORTH),
        time=slice(f"{BASELINE_START}-01-01", f"{TARGET_YEAR}-12-31"),
    )
    # Loading the small regional subset prevents repeated reads during encoding.
    return zos.load()


def daily_anomaly(zos: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    baseline = zos.sel(time=slice(f"{BASELINE_START}-01-01", f"{BASELINE_END}-12-31"))
    climatology = baseline.groupby("time.dayofyear").mean("time", skipna=True)
    target = zos.sel(time=slice(f"{TARGET_YEAR}-01-01", f"{TARGET_YEAR}-12-31"))
    anomaly = target.groupby("time.dayofyear") - climatology
    anomaly.name = "zos_daily_anomaly"
    anomaly.attrs.update(
        units="m",
        long_name="Daily zos anomaly relative to same-calendar-day climatology",
        baseline=f"{BASELINE_START}-{BASELINE_END}",
    )
    return anomaly, climatology


def format_decimal(value: float) -> str:
    """Format a colourbar boundary compactly with a Portuguese decimal comma."""
    return f"{value:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def period_color_scale(field: xr.DataArray) -> dict[str, object]:
    """Create discrete bounds whose right edge equals the period-domain maximum."""
    field_min = float(field.min(skipna=True))
    field_max = float(field.max(skipna=True))
    if not np.isfinite(field_min) or not np.isfinite(field_max):
        raise ValueError("Cannot build a colour scale from an all-NaN field")
    if field_max <= 0:
        raise ValueError(f"Period-domain maximum must be positive; got {field_max}")

    negative_edge = min(field_min, -np.finfo(float).eps)
    if field_max <= 0.1:
        bounds = np.array([negative_edge, 0.0, field_max])
        colors = SURGE_COLORS[:2]
        labels = ["<0", f"0–{format_decimal(field_max)}"]
    else:
        # Nine intervals use the nine remaining colours after the fixed
        # negative and 0–0.1 m classes.
        upper_edges = np.linspace(0.1, field_max, 10)[1:]
        bounds = np.concatenate(([negative_edge, 0.0, 0.1], upper_edges))
        colors = SURGE_COLORS
        labels = ["<0", "0–0,1"]
        labels.extend(
            f"{format_decimal(left)}–{format_decimal(right)}"
            for left, right in zip(bounds[2:-1], bounds[3:])
        )

    return {
        "minimum_m": field_min,
        "maximum_m": field_max,
        "bounds_m": bounds,
        "ticks_m": (bounds[:-1] + bounds[1:]) / 2,
        "tick_labels": labels,
        "colors": colors,
    }


def draw_coastline(ax: plt.Axes) -> None:
    geometries = shapereader.Reader(str(COASTLINE)).geometries()
    ax.add_geometries(
        geometries,
        crs=ccrs.PlateCarree(),
        facecolor="0.88",
        edgecolor="0.15",
        linewidth=0.7,
        zorder=3,
    )


def make_animation(
    field: xr.DataArray,
    output: Path,
    fps: int,
    dpi: int,
) -> dict[str, object]:
    projection = ccrs.PlateCarree()
    scale = period_color_scale(field)
    bounds = scale["bounds_m"]
    ticks = scale["ticks_m"]
    tick_labels = scale["tick_labels"]
    colors = scale["colors"]
    cmap = ListedColormap(colors, name="user_surge_discrete")
    norm = BoundaryNorm(bounds, cmap.N, clip=True)
    fig, ax = plt.subplots(
        figsize=(9.0, 7.2),
        constrained_layout=True,
        subplot_kw={"projection": projection},
    )
    ax.set_extent([WEST, EAST, SOUTH, NORTH], crs=projection)
    ax.set_facecolor("0.88")
    draw_coastline(ax)
    gridlines = ax.gridlines(
        draw_labels=True,
        linewidth=0.4,
        color="0.35",
        alpha=0.5,
        linestyle=":",
    )
    gridlines.top_labels = False
    gridlines.right_labels = False
    gridlines.xlabel_style = {"size": 9}
    gridlines.ylabel_style = {"size": 9}

    mesh = ax.pcolormesh(
        field.longitude,
        field.latitude,
        field.isel(time=0),
        transform=projection,
        cmap=cmap,
        norm=norm,
        shading="auto",
        zorder=1,
    )
    colorbar = fig.colorbar(
        mesh,
        ax=ax,
        orientation="horizontal",
        pad=0.06,
        shrink=0.96,
        boundaries=bounds,
        ticks=ticks,
        spacing="uniform",
    )
    colorbar.ax.set_xticklabels(tick_labels, rotation=38, ha="right", fontsize=7.5)
    colorbar.set_label(
        f"Anomalia diária de zos (m) — referência {BASELINE_START}–{BASELINE_END}"
    )
    title = ax.set_title("", fontsize=13, weight="semibold")
    ax.text(
        0.01,
        0.015,
        "GLORYS12 · média diária · proxy de sobrelevação dinâmica",
        transform=ax.transAxes,
        fontsize=8.5,
        bbox={"facecolor": "white", "alpha": 0.78, "edgecolor": "none", "pad": 2.5},
        zorder=4,
    )

    def update(frame: int):
        values = field.isel(time=frame).values
        mesh.set_array(values.ravel())
        date = np.datetime_as_string(field.time.values[frame], unit="D")
        title.set_text(f"Maranhão–Pará–Amapá | anomalia de zos | {date}")
        return mesh, title

    movie = animation.FuncAnimation(
        fig,
        update,
        frames=field.sizes["time"],
        interval=1000 / fps,
        blit=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = animation.FFMpegWriter(
        fps=fps,
        codec="libx264",
        bitrate=2400,
        extra_args=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    movie.save(output, writer=writer, dpi=dpi)
    plt.close(fig)
    return {
        "type": "discrete",
        "minimum_m": scale["minimum_m"],
        "maximum_m": scale["maximum_m"],
        "bounds_m": bounds.tolist(),
        "tick_labels": tick_labels,
        "colors": colors,
        "maximum_rule": "exact maximum within animation domain and period",
    }


def main() -> None:
    args = parse_args()
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required to encode MP4 animations")

    files = input_files(args.input_dir)
    zos = load_domain(files)
    anomaly, climatology = daily_anomaly(zos)

    generated: list[dict[str, object]] = []
    for name, (start, end) in PERIODS.items():
        subset = anomaly.sel(time=slice(start, end))
        fps = args.fps_year if name.startswith("year") else args.fps_month
        output = args.output_dir / "animations" / f"zos_anomaly_marapa_{name}.mp4"
        color_scale = make_animation(subset, output, fps, args.dpi)
        generated.append(
            {
                "path": str(output.relative_to(REPO_ROOT)),
                "start": start,
                "end": end,
                "frames": int(subset.sizes["time"]),
                "fps": fps,
                "size_bytes": output.stat().st_size,
                "color_scale": color_scale,
            }
        )
        print(f"Wrote {output}")

    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": "CMEMS GLORYS12V1",
        "product": "GLOBAL_MULTIYEAR_PHY_001_030",
        "variable": "zos",
        "source_files": "data/raw/glorys/glorys_zos_YYYY-MM.nc",
        "source_file_count": len(files),
        "temporal_resolution": "daily mean (one value per day)",
        "target_year": TARGET_YEAR,
        "domain": {"west": WEST, "east": EAST, "south": SOUTH, "north": NORTH},
        "processing": (
            "2024 daily zos minus the 1993–2023 mean for the same day of year; "
            "no temporal interpolation"
        ),
        "color_scale_policy": {
            "type": "discrete and period-specific",
            "negative_values": "#525252",
            "zero_to_0.1_m": "#4E4B65",
            "maximum_rule": "exact maximum within each animation domain and period",
            "full_palette": SURGE_COLORS,
        },
        "interpretation": (
            "Tide-free dynamic sea-surface-height anomaly used as a surge proxy. "
            "It is not a pure meteorological residual and may include steric, "
            "circulation, and river-discharge variability on the Amazon shelf."
        ),
        "climatology_shape": dict(climatology.sizes),
        "animations": generated,
    }
    metadata_path = args.output_dir / "metadata" / "animation_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
