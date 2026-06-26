"""Create an exploratory map of long-term mean GLORYS zos.

This is a small standalone helper for the Brazil-wide monthly quicklook output.
It expects a unified NetCDF with a ``zos`` variable and writes both a PNG map
and a NetCDF field containing ``zos_longterm_mean``.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import warnings

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import TwoSlopeNorm


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data/unified/metocean_brazil_unified_waverys_grid.nc"
DEFAULT_OUTPUT_DIR = ROOT / "outputs/monthly_quicklook_brazil_all"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a long-term mean map for GLORYS zos."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--coastline", type=Path, default=DEFAULT_COASTLINE)
    parser.add_argument("--var", default="zos")
    parser.add_argument("--dpi", type=int, default=220)
    return parser.parse_args()


def coord_name(da: xr.DataArray, candidates: tuple[str, ...]) -> str:
    for name in candidates:
        if name in da.coords or name in da.dims:
            return name
    raise KeyError(f"None of {candidates!r} found in {da.name!r}")


def sort_lat_lon(da: xr.DataArray) -> xr.DataArray:
    lat_name = coord_name(da, ("latitude", "lat", "y"))
    lon_name = coord_name(da, ("longitude", "lon", "x"))
    if np.any(np.diff(da[lat_name].values) < 0):
        da = da.sortby(lat_name)
    if np.any(np.diff(da[lon_name].values) < 0):
        da = da.sortby(lon_name)
    return da


def plot_mean_map(
    mean_zos: xr.DataArray,
    *,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    lat_name = coord_name(mean_zos, ("latitude", "lat", "y"))
    lon_name = coord_name(mean_zos, ("longitude", "lon", "x"))
    lat = mean_zos[lat_name].values
    lon = mean_zos[lon_name].values
    values = mean_zos.values
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("No finite values available to plot.")

    vmax = float(np.nanpercentile(np.abs(finite), 98))
    if np.isclose(vmax, 0.0):
        vmax = float(np.nanmax(np.abs(finite)))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)

    crs = ccrs.PlateCarree()
    fig = plt.figure(figsize=(7.2, 9.6))
    ax = plt.axes(projection=crs)
    mesh = ax.pcolormesh(
        lon,
        lat,
        values,
        transform=crs,
        shading="auto",
        cmap="RdBu_r",
        norm=norm,
    )

    if coastline.exists():
        geometries = list(shapereader.Reader(str(coastline)).geometries())
        ax.add_geometries(
            geometries,
            crs,
            facecolor="none",
            edgecolor="0.12",
            linewidth=0.45,
            zorder=3,
        )
    else:
        ax.coastlines(resolution="10m", linewidth=0.5)

    lon_span = float(np.nanmax(lon) - np.nanmin(lon))
    lat_span = float(np.nanmax(lat) - np.nanmin(lat))
    ax.set_extent(
        [
            float(np.nanmin(lon)) - max(0.2, 0.02 * lon_span),
            float(np.nanmax(lon)) + max(0.2, 0.02 * lon_span),
            float(np.nanmin(lat)) - max(0.2, 0.02 * lat_span),
            float(np.nanmax(lat)) + max(0.2, 0.02 * lat_span),
        ],
        crs=crs,
    )

    grid = ax.gridlines(
        draw_labels=True,
        linewidth=0.25,
        color="0.35",
        alpha=0.45,
        linestyle="--",
    )
    grid.top_labels = False
    grid.right_labels = False
    grid.xlabel_style = {"size": 8}
    grid.ylabel_style = {"size": 8}

    colorbar = fig.colorbar(mesh, ax=ax, orientation="vertical", pad=0.025, shrink=0.82)
    colorbar.set_label("Mean zos (m)")

    period = mean_zos.attrs.get("period", "")
    ax.set_title(
        f"Long-term mean sea level (GLORYS zos)\n{period} | all valid model cells",
        fontsize=12,
        pad=12,
    )
    fig.text(
        0.13,
        0.035,
        (
            f"finite cells={finite.size:,} | min={np.nanmin(finite):.3f} m | "
            f"mean={np.nanmean(finite):.3f} m | max={np.nanmax(finite):.3f} m"
        ),
        fontsize=8,
        color="0.25",
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(args.input)

    fig_dir = args.output_dir / "figures"
    data_dir = args.output_dir / "data"
    fig_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Opening {args.input}", flush=True)
    ds = xr.open_dataset(args.input)
    if args.var not in ds:
        raise ValueError(f"{args.var!r} not found. Available: {list(ds.data_vars)}")

    da = sort_lat_lon(ds[args.var])
    time_name = coord_name(da, ("time",))
    print(f"Computing {args.var}.mean({time_name!r})", flush=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)
        mean_zos = da.mean(time_name, skipna=True).astype("float32").load()

    period = f"{str(ds[time_name].values[0])[:10]} to {str(ds[time_name].values[-1])[:10]}"
    mean_zos = mean_zos.rename(f"{args.var}_longterm_mean")
    mean_zos.attrs.update(
        {
            "long_name": "Long-term mean GLORYS sea surface height above geoid",
            "units": da.attrs.get("units", "m"),
            "source_file": str(args.input),
            "period": period,
        }
    )

    data_path = data_dir / "longterm_mean_zos.nc"
    mean_zos.to_dataset().to_netcdf(data_path)
    print(f"Wrote data: {data_path}", flush=True)

    out_path = fig_dir / "fig_longterm_mean_zos.png"
    plot_mean_map(mean_zos, out_path=out_path, coastline=args.coastline, dpi=args.dpi)
    finite = mean_zos.values[np.isfinite(mean_zos.values)]
    print(f"Wrote figure: {out_path}", flush=True)
    print(
        f"Stats: min={np.nanmin(finite):.6f}, mean={np.nanmean(finite):.6f}, "
        f"max={np.nanmax(finite):.6f}, cells={finite.size}",
        flush=True,
    )


if __name__ == "__main__":
    main()
