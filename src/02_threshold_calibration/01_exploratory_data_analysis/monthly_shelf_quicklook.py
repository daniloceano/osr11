"""Monthly quicklook maps for WAVERYS Hs and GLORYS sea level.

The script computes, for each calendar month:

* climatological monthly mean;
* monthly q90;
* monthly maximum;

It can either plot all valid model cells or restrict the analysis to an
external mask.  It is intentionally standalone so it can be run against either
the small local fixture or the production unified NetCDF on a server.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable
import warnings

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "data/test/metocean_sc_full_unified_waverys_grid.nc"
DEFAULT_MASK = ROOT / "data/processed/caderno10_1_2_hazard_hotspots/shelf_mask_200m.nc"
DEFAULT_OUTPUT = ROOT / "outputs/south_sc_test_data_exploratory/monthly_shelf_quicklook"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CRS = ccrs.PlateCarree()
WAVE_CMAP = LinearSegmentedColormap.from_list(
    "osr11_wave",
    [
        "#E6F7FF",
        "#A6DEF7",
        "#4CBFE6",
        "#0099D1",
        "#007AB8",
        "#1AA64C",
        "#8CCC00",
        "#E6CC00",
        "#FF8000",
        "#D90000",
    ],
)
SEA_LEVEL_CMAP = LinearSegmentedColormap.from_list(
    "osr11_sea_level",
    [
        "#FDF5D0",
        "#FCEAA1",
        "#F8E070",
        "#F4B354",
        "#EC8439",
        "#E05020",
        "#C84232",
        "#AF3540",
        "#96274B",
        "#7C1B55",
        "#600F5F",
        "#3E0668",
    ],
)

log = logging.getLogger("monthly_shelf_quicklook")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create monthly climatology, q90, and maximum maps for VHM0 and zos."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Unified NetCDF containing both variables. Ignored per variable if --wave-input or --ssh-input is provided.",
    )
    parser.add_argument(
        "--wave-input",
        type=Path,
        default=None,
        help="Optional NetCDF for the wave variable. Defaults to --input.",
    )
    parser.add_argument(
        "--ssh-input",
        type=Path,
        default=None,
        help="Optional NetCDF for the sea-level variable. Defaults to --input.",
    )
    parser.add_argument("--mask", type=Path, default=DEFAULT_MASK, help="NetCDF with shelf_mask_200m.")
    parser.add_argument(
        "--plot-all",
        action="store_true",
        help="Plot all valid model cells instead of applying the external mask.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directory for figures and tables.")
    parser.add_argument("--wave-var", default="VHM0", help="WAVERYS Hs variable name.")
    parser.add_argument("--ssh-var", default="zos", help="GLORYS sea-level variable name.")
    parser.add_argument("--mask-var", default="shelf_mask_200m", help="Shelf mask variable name.")
    parser.add_argument("--quantile", type=float, default=0.90, help="Monthly quantile to map.")
    parser.add_argument("--coastline", type=Path, default=DEFAULT_COASTLINE, help="Optional coastline shapefile.")
    parser.add_argument("--dpi", type=int, default=220, help="Figure DPI.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = args.output_dir / "figures"
    tab_dir = args.output_dir / "tables"
    data_dir = args.output_dir / "data"
    for directory in (fig_dir, tab_dir, data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    mask_da = None
    domain_label = "all valid model cells"
    if not args.plot_all:
        mask_ds = xr.open_dataset(args.mask)
        if args.mask_var not in mask_ds:
            raise ValueError(f"Mask variable {args.mask_var!r} not found in {args.mask}")
        mask_da = _sort_lat_lon(mask_ds[args.mask_var])
        domain_label = "200 m shelf mask"

    outputs = []
    outputs.append(
        process_variable(
            nc_path=args.wave_input or args.input,
            var_name=args.wave_var,
            label="Hs (WAVERYS)",
            short_name="hs",
            units="m",
            mask_da=mask_da,
            domain_label=domain_label,
            q=args.quantile,
            fig_dir=fig_dir,
            tab_dir=tab_dir,
            data_dir=data_dir,
            coastline=args.coastline,
            dpi=args.dpi,
            cmap=WAVE_CMAP,
            diverging=False,
        )
    )
    outputs.append(
        process_variable(
            nc_path=args.ssh_input or args.input,
            var_name=args.ssh_var,
            label="Sea level (GLORYS zos)",
            short_name="zos",
            units="m",
            mask_da=mask_da,
            domain_label=domain_label,
            q=args.quantile,
            fig_dir=fig_dir,
            tab_dir=tab_dir,
            data_dir=data_dir,
            coastline=args.coastline,
            dpi=args.dpi,
            cmap=SEA_LEVEL_CMAP,
            diverging=False,
        )
    )

    summary = pd.concat(outputs, ignore_index=True)
    summary_path = tab_dir / "monthly_shelf_quicklook_summary.csv"
    summary.to_csv(summary_path, index=False)
    log.info("Wrote summary table: %s", summary_path)


def process_variable(
    *,
    nc_path: Path,
    var_name: str,
    label: str,
    short_name: str,
    units: str,
    mask_da: xr.DataArray | None,
    domain_label: str,
    q: float,
    fig_dir: Path,
    tab_dir: Path,
    data_dir: Path,
    coastline: Path,
    dpi: int,
    cmap: str,
    diverging: bool,
) -> pd.DataFrame:
    if not nc_path.exists():
        raise FileNotFoundError(f"Input file not found: {nc_path}")

    log.info("Opening %s from %s", var_name, nc_path)
    ds = xr.open_dataset(nc_path)
    if var_name not in ds:
        raise ValueError(f"Variable {var_name!r} not found in {nc_path}. Available: {list(ds.data_vars)}")

    da = _sort_lat_lon(ds[var_name])
    lat_name = _coord_name(da, ("latitude", "lat", "y"))
    lon_name = _coord_name(da, ("longitude", "lon", "x"))
    time_name = _coord_name(da, ("time",))

    valid_spatial = da.notnull().any(time_name)
    if mask_da is None:
        analysis_mask = valid_spatial
        mask_description = "all valid model cells"
    else:
        mask = _mask_on_grid(mask_da, da[lat_name], da[lon_name])
        analysis_mask = mask & valid_spatial
        mask_description = "external mask interpolated nearest to source grid"

    n_masked = int(analysis_mask.sum().item())
    n_total = int(analysis_mask.size)
    if n_masked == 0:
        raise ValueError(
            f"The analysis mask has no overlap with valid {var_name} cells in {nc_path}."
        )
    log.info("%s: %d/%d grid cells retained (%s)", var_name, n_masked, n_total, domain_label)

    masked = da.where(analysis_mask)
    monthly_mean = masked.groupby(f"{time_name}.month").mean(time_name, skipna=True)
    monthly_max = masked.groupby(f"{time_name}.month").max(time_name, skipna=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered", category=RuntimeWarning)
        monthly_q = masked.groupby(f"{time_name}.month").quantile(q, dim=time_name, skipna=True)
    if "quantile" in monthly_q.coords:
        monthly_q = monthly_q.drop_vars("quantile")
    monthly_mean = monthly_mean.rename(f"{var_name}_monthly_mean")
    monthly_q = monthly_q.rename(f"{var_name}_monthly_q{int(q * 100):02d}")
    monthly_max = monthly_max.rename(f"{var_name}_monthly_max")

    out_ds = xr.Dataset(
        {
            monthly_mean.name: monthly_mean.astype("float32"),
            monthly_q.name: monthly_q.astype("float32"),
            monthly_max.name: monthly_max.astype("float32"),
            "analysis_mask_on_grid": analysis_mask.astype("int8"),
        }
    )
    out_ds.attrs.update(
        {
            "source_file": str(nc_path),
            "source_variable": var_name,
            "mask": mask_description,
            "quantile": q,
            "note": "Local quicklook product; use production NetCDF for final maps.",
        }
    )
    nc_out = data_dir / f"monthly_shelf_quicklook_{short_name}.nc"
    out_ds.to_netcdf(nc_out)
    log.info("Wrote monthly fields: %s", nc_out)

    plot_month_grid(
        monthly_mean,
        title=f"{label} monthly climatology - {domain_label}",
        label=f"Mean {var_name} ({units})",
        out_path=fig_dir / f"fig_monthly_climatology_{short_name}.png",
        coastline=coastline,
        dpi=dpi,
        cmap=cmap,
        diverging=diverging,
    )
    plot_month_grid(
        monthly_q,
        title=f"{label} monthly q{int(q * 100)} - {domain_label}",
        label=f"q{int(q * 100)} {var_name} ({units})",
        out_path=fig_dir / f"fig_monthly_q{int(q * 100):02d}_{short_name}.png",
        coastline=coastline,
        dpi=dpi,
        cmap=cmap,
        diverging=diverging,
    )
    plot_month_grid(
        monthly_max,
        title=f"{label} monthly maximum - {domain_label}",
        label=f"Maximum {var_name} ({units})",
        out_path=fig_dir / f"fig_monthly_max_{short_name}.png",
        coastline=coastline,
        dpi=dpi,
        cmap=cmap,
        diverging=diverging,
    )

    stats = _summary_table(
        monthly_mean=monthly_mean,
        monthly_q=monthly_q,
        monthly_max=monthly_max,
        var_name=var_name,
        short_name=short_name,
        nc_path=nc_path,
        q=q,
        retained_cells=n_masked,
        total_cells=n_total,
        domain_label=domain_label,
    )
    stats_path = tab_dir / f"monthly_shelf_quicklook_{short_name}.csv"
    stats.to_csv(stats_path, index=False)
    log.info("Wrote variable summary: %s", stats_path)
    return stats


def _mask_on_grid(mask_da: xr.DataArray, target_lat: xr.DataArray, target_lon: xr.DataArray) -> xr.DataArray:
    mask_lat = _coord_name(mask_da, ("latitude", "lat", "y"))
    mask_lon = _coord_name(mask_da, ("longitude", "lon", "x"))
    interp_mask = mask_da.interp(
        {mask_lat: target_lat, mask_lon: target_lon},
        method="nearest",
    )
    interp_mask = interp_mask.rename({mask_lat: target_lat.name, mask_lon: target_lon.name})
    return interp_mask.fillna(0) > 0.5


def plot_month_grid(
    da: xr.DataArray,
    *,
    title: str,
    label: str,
    out_path: Path,
    coastline: Path,
    dpi: int,
    cmap: str,
    diverging: bool,
) -> None:
    lat_name = _coord_name(da, ("latitude", "lat", "y"))
    lon_name = _coord_name(da, ("longitude", "lon", "x"))

    values = da.values
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError(f"No finite values available to plot {da.name}")

    if diverging and np.nanmin(finite) < 0 < np.nanmax(finite):
        vmax = float(np.nanpercentile(np.abs(finite), 98))
        norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
        vmin = vmax = None
    else:
        norm = None
        vmin = float(np.nanpercentile(finite, 2))
        vmax = float(np.nanpercentile(finite, 98))
        if np.isclose(vmin, vmax):
            vmin = float(np.nanmin(finite))
            vmax = float(np.nanmax(finite))

    fig, axes_grid = plt.subplots(
        3,
        4,
        figsize=(9.2, 10.4),
        subplot_kw={"projection": CRS},
        constrained_layout=False,
    )
    fig.subplots_adjust(
        left=0.055,
        right=0.985,
        top=0.925,
        bottom=0.105,
        wspace=0.015,
        hspace=0.18,
    )
    axes = axes_grid.ravel()

    lon = da[lon_name].values
    lat = da[lat_name].values
    extent = _extent(lon, lat)
    coastline_geoms = _coastline_geometries(coastline)
    mesh = None
    for month in range(1, 13):
        ax = axes[month - 1]
        field = da.sel(month=month)
        mesh = ax.pcolormesh(
            lon,
            lat,
            field.values,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            norm=norm,
            shading="auto",
            transform=CRS,
        )
        ax.set_title(MONTH_LABELS[month - 1], fontsize=10)
        ax.set_extent(extent, crs=CRS)
        ax.set_facecolor("#f4f1ea")
        if coastline_geoms:
            ax.add_geometries(coastline_geoms, CRS, facecolor="none", edgecolor="0.15", linewidth=0.45)
        gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="0.55", alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        gl.left_labels = month in (1, 5, 9)
        gl.bottom_labels = month >= 9
        gl.xlabel_style = {"size": 7}
        gl.ylabel_style = {"size": 7}

    fig.suptitle(title, fontsize=14, y=0.975)
    if mesh is not None:
        cbar = fig.colorbar(mesh, ax=axes, orientation="horizontal", shrink=0.88, pad=0.035, aspect=44)
        cbar.set_label(label)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    log.info("Wrote figure: %s", out_path)


def _summary_table(
    *,
    monthly_mean: xr.DataArray,
    monthly_q: xr.DataArray,
    monthly_max: xr.DataArray,
    var_name: str,
    short_name: str,
    nc_path: Path,
    q: float,
    retained_cells: int,
    total_cells: int,
    domain_label: str,
) -> pd.DataFrame:
    rows = []
    for month in range(1, 13):
        mean_field = monthly_mean.sel(month=month)
        q_field = monthly_q.sel(month=month)
        max_field = monthly_max.sel(month=month)
        rows.append(
            {
                "variable": var_name,
                "short_name": short_name,
                "source_file": str(nc_path),
                "month": month,
                "month_label": MONTH_LABELS[month - 1],
                "monthly_mean_domain_mean": _nanmean(mean_field),
                "monthly_mean_spatial_min": _nanmin(mean_field),
                "monthly_mean_spatial_max": _nanmax(mean_field),
                f"monthly_q{int(q * 100):02d}_domain_mean": _nanmean(q_field),
                f"monthly_q{int(q * 100):02d}_spatial_min": _nanmin(q_field),
                f"monthly_q{int(q * 100):02d}_spatial_max": _nanmax(q_field),
                "monthly_max_domain_mean": _nanmean(max_field),
                "monthly_max_spatial_min": _nanmin(max_field),
                "monthly_max_spatial_max": _nanmax(max_field),
                "analysis_domain": domain_label,
                "retained_cells": retained_cells,
                "total_grid_cells": total_cells,
            }
        )
    return pd.DataFrame(rows)


def _coord_name(obj: xr.DataArray, candidates: Iterable[str]) -> str:
    for name in candidates:
        if name in obj.coords or name in obj.dims:
            return name
    raise ValueError(f"Could not identify coordinate among {tuple(candidates)} for {obj.name}")


def _sort_lat_lon(da: xr.DataArray) -> xr.DataArray:
    for coord in ("latitude", "lat"):
        if coord in da.coords and da[coord].size > 1 and da[coord].values[0] > da[coord].values[-1]:
            da = da.sortby(coord)
    for coord in ("longitude", "lon"):
        if coord in da.coords and da[coord].size > 1 and da[coord].values[0] > da[coord].values[-1]:
            da = da.sortby(coord)
    return da


def _extent(lon: np.ndarray, lat: np.ndarray) -> list[float]:
    lon_pad = max(0.1, float(np.nanmax(lon) - np.nanmin(lon)) * 0.04)
    lat_pad = max(0.1, float(np.nanmax(lat) - np.nanmin(lat)) * 0.04)
    return [
        float(np.nanmin(lon) - lon_pad),
        float(np.nanmax(lon) + lon_pad),
        float(np.nanmin(lat) - lat_pad),
        float(np.nanmax(lat) + lat_pad),
    ]


def _coastline_geometries(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return list(shapereader.Reader(path).geometries())
    except Exception as exc:  # pragma: no cover - plotting should degrade gracefully
        log.warning("Could not read coastline shapefile %s: %s", path, exc)
        return []


def _nanmean(da: xr.DataArray) -> float:
    value = da.mean(skipna=True).item()
    return float(value) if pd.notnull(value) else np.nan


def _nanmin(da: xr.DataArray) -> float:
    value = da.min(skipna=True).item()
    return float(value) if pd.notnull(value) else np.nan


def _nanmax(da: xr.DataArray) -> float:
    value = da.max(skipna=True).item()
    return float(value) if pd.notnull(value) else np.nan


if __name__ == "__main__":
    main()
