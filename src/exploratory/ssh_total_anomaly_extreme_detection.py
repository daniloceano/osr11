"""Explore extreme-event detection using SSH_total anomalies.

This is an exploratory analysis only. It keeps the production-style local q90
thresholding and episode clustering, but compares detections from:

* raw SSH_total;
* SSH_total anomaly, computed as SSH_total minus its long-term mean at each
  grid point.

Because the threshold is also a local quantile at the same grid point, this
test should be translation-invariant: subtracting a pointwise long-term mean
shifts both the series and its q90 by the same amount. The script verifies
that expectation and writes maps/tables for inspection.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


try:
    ROOT = Path(__file__).resolve().parents[2]
except IndexError:
    ROOT = Path.cwd()
DEFAULT_INPUT = ROOT / "data/unified/metocean_brazil_unified_waverys_grid.nc"
DEFAULT_SSH_CATALOG = ROOT / "outputs/storm_catalog/catalog_ssh_total_storms.json"
DEFAULT_OUTPUT = ROOT / "outputs/exploratory_ssh_total_anomaly_extremes"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

CRS = ccrs.PlateCarree()
COUNT_CMAP = LinearSegmentedColormap.from_list(
    "event_count",
    [
        "#008000",
        "#33B200",
        "#80D900",
        "#CCE600",
        "#FFE600",
        "#FFB200",
        "#FF8000",
        "#FF4000",
        "#FF0000",
        "#CC0033",
        "#99004C",
        "#660066",
    ],
)

log = logging.getLogger("ssh_total_anomaly_extreme_detection")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare raw SSH_total and SSH_total-anomaly extreme detection."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--ssh-catalog", type=Path, default=DEFAULT_SSH_CATALOG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--coastline", type=Path, default=DEFAULT_COASTLINE)
    parser.add_argument("--hs-var", default="VHM0")
    parser.add_argument("--ssh-total-var", default="SSH_total")
    parser.add_argument("--quantile", type=float, default=0.90)
    parser.add_argument("--max-gap-days", type=int, default=1)
    parser.add_argument("--dpi", type=int, default=220)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    fig_dir = args.output_dir / "figures"
    tab_dir = args.output_dir / "tables"
    data_dir = args.output_dir / "data"
    for directory in (fig_dir, tab_dir, data_dir):
        directory.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(args.input)
    validate_dataset(ds, args.hs_var, args.ssh_total_var)
    points = read_catalog_points(args.ssh_catalog)
    log.info("Loaded %d analysis points from %s", len(points), args.ssh_catalog)

    time = pd.DatetimeIndex(ds.time.values)
    day_ord = np.array([ts.toordinal() for ts in time.date], dtype=np.int32)
    lat_vals = ds.latitude.values
    lon_vals = ds.longitude.values
    lat_index = {round(float(value), 4): idx for idx, value in enumerate(lat_vals)}
    lon_index = {round(float(value), 4): idx for idx, value in enumerate(lon_vals)}

    rows = []
    for idx, point in enumerate(points, start=1):
        if idx == 1 or idx % max(1, len(points) // 10) == 0:
            log.info("Processing point %d/%d", idx, len(points))

        i_lat = lat_index[round(point["grid_lat"], 4)]
        i_lon = lon_index[round(point["grid_lon"], 4)]
        hs = np.asarray(ds[args.hs_var].isel(latitude=i_lat, longitude=i_lon).values, dtype=float)
        ssh = np.asarray(
            ds[args.ssh_total_var].isel(latitude=i_lat, longitude=i_lon).values,
            dtype=float,
        )

        rows.append(
            compare_point(
                hs=hs,
                ssh=ssh,
                day_ord=day_ord,
                q=args.quantile,
                max_gap_days=args.max_gap_days,
                grid_lat=point["grid_lat"],
                grid_lon=point["grid_lon"],
                i_lat=i_lat,
                i_lon=i_lon,
                catalog_ssh_total_episode_count=point["catalog_ssh_total_episode_count"],
                catalog_thr_ssh_total_abs=point["catalog_thr_ssh_total_abs"],
            )
        )

    point_df = pd.DataFrame(rows)
    point_df = add_derived_columns(point_df, time)
    point_path = tab_dir / "ssh_total_anomaly_extreme_detection_by_point.csv"
    point_df.to_csv(point_path, index=False)
    log.info("Wrote %s", point_path)

    grid_ds = to_grid_dataset(point_df, lat_vals, lon_vals, args)
    grid_path = data_dir / "ssh_total_anomaly_extreme_detection_grid.nc"
    grid_ds.to_netcdf(grid_path)
    log.info("Wrote %s", grid_path)

    summary = build_summary(point_df, args, time)
    summary_path = tab_dir / "ssh_total_anomaly_extreme_detection_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote %s", summary_path)

    plot_count_comparison(
        grid_ds,
        current_var="ssh_total_episode_count",
        anomaly_var="ssh_total_anomaly_episode_count",
        delta_var="delta_ssh_total_episode_count",
        title="SSH_total extreme episodes: raw field vs anomaly",
        count_label="SSH_total episode count",
        out_path=fig_dir / "fig_ssh_total_episode_count_raw_vs_anomaly.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )
    plot_count_comparison(
        grid_ds,
        current_var="compound_event_count_raw_ssh_total",
        anomaly_var="compound_event_count_ssh_total_anomaly",
        delta_var="delta_compound_event_count",
        title="Compound episodes: Hs + raw SSH_total vs Hs + SSH_total anomaly",
        count_label="Compound episode count",
        out_path=fig_dir / "fig_compound_event_count_raw_ssh_total_vs_anomaly.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )
    plot_threshold_maps(
        grid_ds,
        out_path=fig_dir / "fig_ssh_total_thresholds_raw_mean_anomaly.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )


def validate_dataset(ds: xr.Dataset, hs_var: str, ssh_var: str) -> None:
    required = {hs_var, ssh_var, "time", "latitude", "longitude"}
    available = set(ds.data_vars) | set(ds.coords) | set(ds.dims)
    missing = required - available
    if missing:
        raise ValueError(f"Missing {missing}; available data vars are {list(ds.data_vars)}")


def read_catalog_points(path: Path) -> list[dict]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    points = []
    for point in catalog:
        points.append(
            {
                "grid_lat": round(float(point["grid_lat"]), 4),
                "grid_lon": round(float(point["grid_lon"]), 4),
                "catalog_ssh_total_episode_count": len(point.get("storms", [])),
                "catalog_thr_ssh_total_abs": point.get("thr_ssh_total_abs"),
            }
        )
    return points


def compare_point(
    *,
    hs: np.ndarray,
    ssh: np.ndarray,
    day_ord: np.ndarray,
    q: float,
    max_gap_days: int,
    grid_lat: float,
    grid_lon: float,
    i_lat: int,
    i_lon: int,
    catalog_ssh_total_episode_count: int,
    catalog_thr_ssh_total_abs: float | None,
) -> dict:
    hs_thr = nanquantile(hs, q)
    ssh_thr = nanquantile(ssh, q)
    ssh_mean = float(np.nanmean(ssh)) if np.isfinite(ssh).any() else np.nan
    ssh_anom = ssh - ssh_mean
    ssh_anom_thr = nanquantile(ssh_anom, q)

    hs_mask = np.isfinite(hs) & (hs >= hs_thr)
    ssh_mask = np.isfinite(ssh) & (ssh >= ssh_thr)
    ssh_anom_mask = np.isfinite(ssh_anom) & (ssh_anom >= ssh_anom_thr)

    hs_episodes = cluster_episodes(hs_mask, day_ord, max_gap_days)
    ssh_episodes = cluster_episodes(ssh_mask, day_ord, max_gap_days)
    ssh_anom_episodes = cluster_episodes(ssh_anom_mask, day_ord, max_gap_days)
    compound_raw = count_overlapping_episode_groups(hs_episodes, ssh_episodes, len(hs))
    compound_anom = count_overlapping_episode_groups(hs_episodes, ssh_anom_episodes, len(hs))

    return {
        "grid_lat": grid_lat,
        "grid_lon": grid_lon,
        "i_lat": i_lat,
        "i_lon": i_lon,
        "hs_q90": round_or_none(hs_thr),
        "ssh_total_mean": round_or_none(ssh_mean),
        "ssh_total_q90": round_or_none(ssh_thr),
        "ssh_total_anomaly_q90": round_or_none(ssh_anom_thr),
        "ssh_total_q90_minus_mean": round_or_none(ssh_thr - ssh_mean),
        "threshold_translation_error": round_or_none(ssh_anom_thr - (ssh_thr - ssh_mean)),
        "catalog_thr_ssh_total_abs": catalog_thr_ssh_total_abs,
        "catalog_ssh_total_episode_count": catalog_ssh_total_episode_count,
        "ssh_total_exceedance_day_count": int(np.count_nonzero(ssh_mask)),
        "ssh_total_anomaly_exceedance_day_count": int(np.count_nonzero(ssh_anom_mask)),
        "ssh_total_episode_count": len(ssh_episodes),
        "ssh_total_anomaly_episode_count": len(ssh_anom_episodes),
        "ssh_total_mask_difference_day_count": int(np.count_nonzero(ssh_mask != ssh_anom_mask)),
        "compound_day_count_raw_ssh_total": int(np.count_nonzero(hs_mask & ssh_mask)),
        "compound_day_count_ssh_total_anomaly": int(np.count_nonzero(hs_mask & ssh_anom_mask)),
        "compound_event_count_raw_ssh_total": compound_raw,
        "compound_event_count_ssh_total_anomaly": compound_anom,
    }


def nanquantile(values: np.ndarray, q: float) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.nan
    return float(np.nanquantile(finite, q))


def cluster_episodes(mask: np.ndarray, day_ord: np.ndarray, max_gap_days: int) -> list[np.ndarray]:
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    episodes = []
    current = [int(idx[0])]
    for i in idx[1:]:
        gap = int(day_ord[i] - day_ord[current[-1]])
        if gap <= max_gap_days + 1:
            current.append(int(i))
        else:
            episodes.append(np.array(current, dtype=np.int32))
            current = [int(i)]
    episodes.append(np.array(current, dtype=np.int32))
    return episodes


def count_overlapping_episode_groups(
    hs_episodes: list[np.ndarray],
    ssh_episodes: list[np.ndarray],
    n_time: int,
) -> int:
    if not hs_episodes or not ssh_episodes:
        return 0

    hs_label = np.full(n_time, -1, dtype=np.int32)
    ssh_label = np.full(n_time, -1, dtype=np.int32)
    for i, ep in enumerate(hs_episodes):
        hs_label[ep] = i
    for i, ep in enumerate(ssh_episodes):
        ssh_label[ep] = i

    overlap = (hs_label >= 0) & (ssh_label >= 0)
    if not np.any(overlap):
        return 0

    pairs = set(zip(hs_label[overlap].tolist(), ssh_label[overlap].tolist()))
    parent: dict[tuple[str, int], tuple[str, int]] = {}

    def find(node: tuple[str, int]) -> tuple[str, int]:
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: tuple[str, int], b: tuple[str, int]) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    nodes = set()
    for hi, si in pairs:
        h_node = ("h", int(hi))
        s_node = ("s", int(si))
        union(h_node, s_node)
        nodes.add(h_node)
        nodes.add(s_node)

    return len({find(node) for node in nodes})


def add_derived_columns(df: pd.DataFrame, time: pd.DatetimeIndex) -> pd.DataFrame:
    years = len(np.unique(time.year))
    df = df.copy()
    df["delta_ssh_total_exceedance_day_count"] = (
        df["ssh_total_anomaly_exceedance_day_count"] - df["ssh_total_exceedance_day_count"]
    )
    df["delta_ssh_total_episode_count"] = (
        df["ssh_total_anomaly_episode_count"] - df["ssh_total_episode_count"]
    )
    df["delta_compound_day_count"] = (
        df["compound_day_count_ssh_total_anomaly"] - df["compound_day_count_raw_ssh_total"]
    )
    df["delta_compound_event_count"] = (
        df["compound_event_count_ssh_total_anomaly"]
        - df["compound_event_count_raw_ssh_total"]
    )
    df["delta_catalog_vs_recomputed_ssh_total_episode_count"] = (
        df["ssh_total_episode_count"] - df["catalog_ssh_total_episode_count"]
    )
    for col in [
        "ssh_total_episode_count",
        "ssh_total_anomaly_episode_count",
        "compound_event_count_raw_ssh_total",
        "compound_event_count_ssh_total_anomaly",
    ]:
        df[f"{col}_annual_mean"] = df[col] / years
    return df


def to_grid_dataset(
    df: pd.DataFrame,
    lat_vals: np.ndarray,
    lon_vals: np.ndarray,
    args: argparse.Namespace,
) -> xr.Dataset:
    fields = [
        "ssh_total_mean",
        "ssh_total_q90",
        "ssh_total_anomaly_q90",
        "threshold_translation_error",
        "ssh_total_exceedance_day_count",
        "ssh_total_anomaly_exceedance_day_count",
        "delta_ssh_total_exceedance_day_count",
        "ssh_total_episode_count",
        "ssh_total_anomaly_episode_count",
        "delta_ssh_total_episode_count",
        "ssh_total_mask_difference_day_count",
        "compound_day_count_raw_ssh_total",
        "compound_day_count_ssh_total_anomaly",
        "delta_compound_day_count",
        "compound_event_count_raw_ssh_total",
        "compound_event_count_ssh_total_anomaly",
        "delta_compound_event_count",
        "delta_catalog_vs_recomputed_ssh_total_episode_count",
    ]
    data_vars = {}
    for field in fields:
        arr = np.full((len(lat_vals), len(lon_vals)), np.nan, dtype=np.float32)
        for row in df.itertuples(index=False):
            arr[int(row.i_lat), int(row.i_lon)] = getattr(row, field)
        data_vars[field] = (("latitude", "longitude"), arr)

    return xr.Dataset(
        data_vars=data_vars,
        coords={"latitude": lat_vals, "longitude": lon_vals},
        attrs={
            "analysis": "Exploratory raw SSH_total vs SSH_total anomaly extreme detection",
            "input": str(args.input),
            "ssh_catalog": str(args.ssh_catalog),
            "hs_var": args.hs_var,
            "ssh_total_var": args.ssh_total_var,
            "quantile": args.quantile,
            "max_gap_days": args.max_gap_days,
            "anomaly_definition": (
                "SSH_total anomaly = SSH_total - long-term mean SSH_total at each grid point"
            ),
        },
    )


def build_summary(df: pd.DataFrame, args: argparse.Namespace, time: pd.DatetimeIndex) -> dict:
    threshold_error = df["threshold_translation_error"].abs()
    return {
        "input": str(args.input),
        "ssh_catalog": str(args.ssh_catalog),
        "hs_var": args.hs_var,
        "ssh_total_var": args.ssh_total_var,
        "quantile": args.quantile,
        "period": [str(time[0].date()), str(time[-1].date())],
        "max_gap_days": args.max_gap_days,
        "n_analysis_points": int(len(df)),
        "anomaly_definition": (
            "SSH_total anomaly = SSH_total - long-term mean SSH_total at each grid point"
        ),
        "translation_invariance_note": (
            "With local per-point quantile thresholds, subtracting a pointwise mean "
            "shifts the series and the threshold by the same amount. Event masks "
            "are expected to be unchanged apart from numerical precision."
        ),
        "threshold_translation_error_abs_max": float(threshold_error.max()),
        "ssh_total_episode_counts": {
            "raw_total": int(df["ssh_total_episode_count"].sum()),
            "anomaly_total": int(df["ssh_total_anomaly_episode_count"].sum()),
            "delta_total": int(df["delta_ssh_total_episode_count"].sum()),
            "points_changed": int((df["delta_ssh_total_episode_count"] != 0).sum()),
            "points_with_mask_difference": int(
                (df["ssh_total_mask_difference_day_count"] != 0).sum()
            ),
            "max_abs_delta_per_point": int(df["delta_ssh_total_episode_count"].abs().max()),
        },
        "compound_event_counts": {
            "raw_total": int(df["compound_event_count_raw_ssh_total"].sum()),
            "anomaly_total": int(df["compound_event_count_ssh_total_anomaly"].sum()),
            "delta_total": int(df["delta_compound_event_count"].sum()),
            "points_changed": int((df["delta_compound_event_count"] != 0).sum()),
            "max_abs_delta_per_point": int(df["delta_compound_event_count"].abs().max()),
        },
        "catalog_consistency": {
            "points_different_from_catalog": int(
                (df["delta_catalog_vs_recomputed_ssh_total_episode_count"] != 0).sum()
            ),
            "max_abs_delta_vs_catalog": int(
                df["delta_catalog_vs_recomputed_ssh_total_episode_count"].abs().max()
            ),
        },
    }


def plot_count_comparison(
    ds: xr.Dataset,
    *,
    current_var: str,
    anomaly_var: str,
    delta_var: str,
    title: str,
    count_label: str,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    lon = ds.longitude.values
    lat = ds.latitude.values
    current = ds[current_var].values
    anomaly = ds[anomaly_var].values
    delta = ds[delta_var].values
    count_values = np.concatenate([current[np.isfinite(current)], anomaly[np.isfinite(anomaly)]])
    count_vmax = float(np.nanpercentile(count_values, 98)) if count_values.size else 1.0
    count_vmax = max(count_vmax, 1.0)
    delta_values = delta[np.isfinite(delta)]
    delta_abs = float(np.nanmax(np.abs(delta_values))) if delta_values.size else 1.0
    delta_abs = max(delta_abs, 1.0)
    delta_norm = TwoSlopeNorm(vmin=-delta_abs, vcenter=0.0, vmax=delta_abs)

    fig = plt.figure(figsize=(12.4, 5.7))
    gs = fig.add_gridspec(
        nrows=2,
        ncols=3,
        height_ratios=[1.0, 0.045],
        wspace=0.035,
        hspace=0.075,
    )
    axes = [fig.add_subplot(gs[0, i], projection=CRS) for i in range(3)]
    cax_count = fig.add_subplot(gs[1, 0:2])
    cax_delta = fig.add_subplot(gs[1, 2])

    geoms = coastline_geometries(coastline)
    extent = map_extent(lon, lat)
    panels = [
        (current, "Raw SSH_total q90", COUNT_CMAP, {"vmin": 0.0, "vmax": count_vmax}),
        (anomaly, "SSH_total anomaly q90", COUNT_CMAP, {"vmin": 0.0, "vmax": count_vmax}),
        (delta, "Anomaly - raw", "RdBu_r", {"norm": delta_norm}),
    ]

    count_mesh = None
    delta_mesh = None
    for idx, (ax, (field, label, cmap, kwargs)) in enumerate(zip(axes, panels)):
        mesh = ax.pcolormesh(
            lon,
            lat,
            field,
            shading="auto",
            cmap=cmap,
            transform=CRS,
            **kwargs,
        )
        if idx < 2:
            count_mesh = mesh
        else:
            delta_mesh = mesh
        format_map_axis(ax, label, extent, geoms, idx)

    cbar_count = fig.colorbar(count_mesh, cax=cax_count, orientation="horizontal")
    cbar_count.ax.tick_params(labelsize=8)
    cbar_count.set_label(count_label, fontsize=9)
    cbar_delta = fig.colorbar(delta_mesh, cax=cax_delta, orientation="horizontal")
    cbar_delta.ax.tick_params(labelsize=8)
    cbar_delta.set_label("Delta count", fontsize=9)

    fig.suptitle(title, fontsize=12)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def plot_threshold_maps(
    ds: xr.Dataset,
    *,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    lon = ds.longitude.values
    lat = ds.latitude.values
    raw_q90 = ds["ssh_total_q90"].values
    mean = ds["ssh_total_mean"].values
    anomaly_q90 = ds["ssh_total_anomaly_q90"].values
    raw_values = raw_q90[np.isfinite(raw_q90)]
    anom_values = anomaly_q90[np.isfinite(anomaly_q90)]
    mean_values = mean[np.isfinite(mean)]
    raw_vmax = float(np.nanpercentile(raw_values, 98)) if raw_values.size else 1.0
    mean_vmax = float(np.nanpercentile(mean_values, 98)) if mean_values.size else 1.0
    anom_limit = float(np.nanpercentile(np.abs(anom_values), 98)) if anom_values.size else 1.0
    anom_limit = max(anom_limit, 0.1)
    anom_norm = TwoSlopeNorm(vmin=-anom_limit, vcenter=0.0, vmax=anom_limit)

    fig = plt.figure(figsize=(12.4, 5.7))
    gs = fig.add_gridspec(
        nrows=2,
        ncols=3,
        height_ratios=[1.0, 0.045],
        wspace=0.035,
        hspace=0.075,
    )
    axes = [fig.add_subplot(gs[0, i], projection=CRS) for i in range(3)]
    cax_raw = fig.add_subplot(gs[1, 0])
    cax_mean = fig.add_subplot(gs[1, 1])
    cax_anom = fig.add_subplot(gs[1, 2])

    geoms = coastline_geometries(coastline)
    extent = map_extent(lon, lat)
    panels = [
        (raw_q90, "Raw SSH_total q90", "magma", {"vmin": 0.0, "vmax": raw_vmax}, cax_raw),
        (mean, "Long-term mean SSH_total", "viridis", {"vmin": 0.0, "vmax": mean_vmax}, cax_mean),
        (anomaly_q90, "SSH_total anomaly q90", "RdBu_r", {"norm": anom_norm}, cax_anom),
    ]

    for idx, (ax, (field, label, cmap, kwargs, cax)) in enumerate(zip(axes, panels)):
        mesh = ax.pcolormesh(
            lon,
            lat,
            field,
            shading="auto",
            cmap=cmap,
            transform=CRS,
            **kwargs,
        )
        format_map_axis(ax, label, extent, geoms, idx)
        cbar = fig.colorbar(mesh, cax=cax, orientation="horizontal")
        cbar.ax.tick_params(labelsize=8)
        cbar.set_label("m", fontsize=9)

    fig.suptitle("SSH_total anomaly construction", fontsize=12)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def format_map_axis(ax, title: str, extent: list[float], geoms: list, idx: int) -> None:
    ax.set_title(title, fontsize=10)
    ax.set_extent(extent, crs=CRS)
    ax.set_facecolor("#f4f1ea")
    if geoms:
        ax.add_geometries(geoms, CRS, facecolor="none", edgecolor="0.15", linewidth=0.45)
    else:
        ax.coastlines(resolution="10m", linewidth=0.5)
    gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="0.55", alpha=0.45)
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = idx == 0
    gl.bottom_labels = True
    gl.xlabel_style = {"size": 7}
    gl.ylabel_style = {"size": 7}


def map_extent(lon: np.ndarray, lat: np.ndarray) -> list[float]:
    lon_pad = max(0.2, float(np.nanmax(lon) - np.nanmin(lon)) * 0.03)
    lat_pad = max(0.2, float(np.nanmax(lat) - np.nanmin(lat)) * 0.03)
    return [
        float(np.nanmin(lon) - lon_pad),
        float(np.nanmax(lon) + lon_pad),
        float(np.nanmin(lat) - lat_pad),
        float(np.nanmax(lat) + lat_pad),
    ]


def coastline_geometries(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return list(shapereader.Reader(path).geometries())
    except Exception as exc:
        log.warning("Could not read coastline %s: %s", path, exc)
        return []


def round_or_none(value: float, digits: int = 6) -> float | None:
    if not np.isfinite(value):
        return None
    return round(float(value), digits)


if __name__ == "__main__":
    main()
