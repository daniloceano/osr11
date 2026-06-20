"""Compare compound detections using global versus seasonal q90 thresholds.

This is an exploratory analysis only. It does not modify or call the
production storm-catalog pipeline outputs.

Definitions
-----------
Global q90:
    One local q90 threshold per variable and grid point, computed from the
    full daily 1993-2025 record.

Seasonal q90:
    One local q90 threshold per variable, grid point, and season
    (DJF/MAM/JJA/SON), computed from the full daily record restricted to each
    season.

Compound day:
    Hs and SSH_total exceed their corresponding thresholds on the same day.

Compound episode:
    Hs exceedance episodes and SSH_total exceedance episodes overlap by at
    least one calendar day. Episodes use the same gap tolerance as Step 3:
    one non-exceedance day may occur inside an episode.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Iterable

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_INPUT = ROOT / "data/unified/metocean_brazil_unified_waverys_grid.nc"
DEFAULT_OUTPUT = ROOT / "outputs/exploratory_seasonal_q90_compounds"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

SEASON_NAMES = np.array(["DJF", "MAM", "JJA", "SON"], dtype=object)
SEASON_BY_MONTH = {
    12: 0,
    1: 0,
    2: 0,
    3: 1,
    4: 1,
    5: 1,
    6: 2,
    7: 2,
    8: 2,
    9: 3,
    10: 3,
    11: 3,
}
CRS = ccrs.PlateCarree()
log = logging.getLogger("seasonal_q90_compound_compare")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare compound detections with global q90 and seasonal q90."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--hs-var", default="VHM0")
    parser.add_argument("--ssh-total-var", default="SSH_total")
    parser.add_argument("--quantile", type=float, default=0.90)
    parser.add_argument("--max-gap-days", type=int, default=1)
    parser.add_argument("--coastal-max-dist-km", type=float, default=50.0)
    parser.add_argument("--min-valid-frac", type=float, default=0.80)
    parser.add_argument("--coastline", type=Path, default=DEFAULT_COASTLINE)
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
    _validate_dataset(ds, args.hs_var, args.ssh_total_var)

    log.info("Loaded %s", args.input)
    log.info("Variables: Hs=%s, SSH_total=%s", args.hs_var, args.ssh_total_var)

    points_df = identify_analysis_points(
        ds,
        args.hs_var,
        args.ssh_total_var,
        args.coastline,
        args.coastal_max_dist_km,
        args.min_valid_frac,
    )
    log.info("Analysis points: %d", len(points_df))

    time = pd.DatetimeIndex(ds.time.values)
    season_code = np.array([SEASON_BY_MONTH[m] for m in time.month], dtype=np.int8)
    day_ord = np.array([ts.toordinal() for ts in time.date], dtype=np.int32)

    hs_data = ds[args.hs_var].values
    ssh_data = ds[args.ssh_total_var].values
    lat_vals = ds.latitude.values
    lon_vals = ds.longitude.values

    rows = []
    n_points = len(points_df)
    for idx, row in points_df.iterrows():
        if idx == 0 or (idx + 1) % max(1, n_points // 10) == 0:
            log.info("Processing point %d/%d", idx + 1, n_points)

        i_lat = int(row["i_lat"])
        i_lon = int(row["i_lon"])
        hs = hs_data[:, i_lat, i_lon]
        ssh = ssh_data[:, i_lat, i_lon]

        result = compare_point(
            hs=hs,
            ssh=ssh,
            season_code=season_code,
            day_ord=day_ord,
            q=args.quantile,
            max_gap_days=args.max_gap_days,
        )
        result.update(
            {
                "grid_lat": float(lat_vals[i_lat]),
                "grid_lon": float(lon_vals[i_lon]),
                "i_lat": i_lat,
                "i_lon": i_lon,
                "hs_valid_frac": float(row["hs_valid_frac"]),
                "ssh_total_valid_frac": float(row["ssh_total_valid_frac"]),
                "dist_to_coast_km": float(row["dist_to_coast_km"]),
            }
        )
        rows.append(result)

    out_df = pd.DataFrame(rows)
    out_df = add_derived_columns(out_df, time)
    csv_path = tab_dir / "seasonal_q90_compound_counts_by_point.csv"
    out_df.to_csv(csv_path, index=False)
    log.info("Wrote %s", csv_path)

    grid_ds = to_grid_dataset(out_df, lat_vals, lon_vals, args)
    nc_path = data_dir / "seasonal_q90_compound_counts_grid.nc"
    grid_ds.to_netcdf(nc_path)
    log.info("Wrote %s", nc_path)

    summary = build_summary(out_df, args, time)
    summary_path = tab_dir / "seasonal_q90_compound_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote %s", summary_path)

    plot_count_maps(
        grid_ds,
        metric="compound_event_count",
        title="Compound episode count: global q90 vs seasonal q90",
        out_path=fig_dir / "fig_compound_episode_count_global_vs_seasonal.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )
    plot_count_maps(
        grid_ds,
        metric="compound_day_count",
        title="Compound day count: global q90 vs seasonal q90",
        out_path=fig_dir / "fig_compound_day_count_global_vs_seasonal.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )
    plot_scatter(
        out_df,
        out_path=fig_dir / "fig_compound_episode_count_scatter.png",
        dpi=args.dpi,
    )


def _validate_dataset(ds: xr.Dataset, hs_var: str, ssh_var: str) -> None:
    required = {hs_var, ssh_var, "time", "latitude", "longitude"}
    available = set(ds.data_vars) | set(ds.coords) | set(ds.dims)
    missing = required - available
    if missing:
        raise ValueError(f"Missing {missing}; available data vars are {list(ds.data_vars)}")


def identify_analysis_points(
    ds: xr.Dataset,
    hs_var: str,
    ssh_var: str,
    coastline: Path,
    coastal_max_dist_km: float,
    min_valid_frac: float,
) -> pd.DataFrame:
    from src.exploratory_data_analysis.coastal import find_coastal_points

    lat = ds.latitude.values
    lon = ds.longitude.values
    hs_mean = ds[hs_var].mean(dim="time", skipna=True).values
    coastal_mask, dist_to_coast = find_coastal_points(
        lat,
        lon,
        hs_mean,
        shp_path=coastline,
        max_dist_km=coastal_max_dist_km,
    )

    hs_valid = np.isfinite(ds[hs_var].values).mean(axis=0)
    ssh_valid = np.isfinite(ds[ssh_var].values).mean(axis=0)
    valid_mask = coastal_mask & (hs_valid >= min_valid_frac) & (ssh_valid >= min_valid_frac)

    rows = []
    for i_lat, i_lon in np.argwhere(valid_mask):
        rows.append(
            {
                "i_lat": int(i_lat),
                "i_lon": int(i_lon),
                "grid_lat": float(lat[i_lat]),
                "grid_lon": float(lon[i_lon]),
                "hs_valid_frac": float(hs_valid[i_lat, i_lon]),
                "ssh_total_valid_frac": float(ssh_valid[i_lat, i_lon]),
                "dist_to_coast_km": float(dist_to_coast[i_lat, i_lon]),
            }
        )
    return pd.DataFrame(rows)


def compare_point(
    *,
    hs: np.ndarray,
    ssh: np.ndarray,
    season_code: np.ndarray,
    day_ord: np.ndarray,
    q: float,
    max_gap_days: int,
) -> dict:
    hs_global_thr = _nanquantile(hs, q)
    ssh_global_thr = _nanquantile(ssh, q)

    hs_season_thr = np.array([_nanquantile(hs[season_code == s], q) for s in range(4)])
    ssh_season_thr = np.array([_nanquantile(ssh[season_code == s], q) for s in range(4)])

    hs_global_mask = np.isfinite(hs) & (hs >= hs_global_thr)
    ssh_global_mask = np.isfinite(ssh) & (ssh >= ssh_global_thr)
    hs_season_mask = np.isfinite(hs) & (hs >= hs_season_thr[season_code])
    ssh_season_mask = np.isfinite(ssh) & (ssh >= ssh_season_thr[season_code])

    global_counts = _compound_counts(hs_global_mask, ssh_global_mask, day_ord, max_gap_days)
    seasonal_counts = _compound_counts(hs_season_mask, ssh_season_mask, day_ord, max_gap_days)

    out = {
        "hs_global_q90": hs_global_thr,
        "ssh_total_global_q90": ssh_global_thr,
    }
    for s, name in enumerate(SEASON_NAMES):
        out[f"hs_{name}_q90"] = hs_season_thr[s]
        out[f"ssh_total_{name}_q90"] = ssh_season_thr[s]
    for key, value in global_counts.items():
        out[f"global_{key}"] = value
    for key, value in seasonal_counts.items():
        out[f"seasonal_{key}"] = value
    return out


def _nanquantile(values: np.ndarray, q: float) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.nan
    return float(np.nanquantile(finite, q))


def _compound_counts(
    hs_mask: np.ndarray,
    ssh_mask: np.ndarray,
    day_ord: np.ndarray,
    max_gap_days: int,
) -> dict[str, int]:
    compound_day_count = int(np.count_nonzero(hs_mask & ssh_mask))
    hs_episodes = _cluster_episodes(hs_mask, day_ord, max_gap_days)
    ssh_episodes = _cluster_episodes(ssh_mask, day_ord, max_gap_days)
    compound_event_count = _count_overlapping_episode_groups(
        hs_episodes,
        ssh_episodes,
        len(hs_mask),
    )
    return {
        "compound_day_count": compound_day_count,
        "compound_event_count": compound_event_count,
        "hs_episode_count": len(hs_episodes),
        "ssh_total_episode_count": len(ssh_episodes),
    }


def _cluster_episodes(mask: np.ndarray, day_ord: np.ndarray, max_gap_days: int) -> list[np.ndarray]:
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


def _count_overlapping_episode_groups(
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
    years = (time[-1] - time[0]).days / 365.25
    df = df.copy()
    for metric in ("compound_day_count", "compound_event_count"):
        df[f"delta_{metric}"] = df[f"seasonal_{metric}"] - df[f"global_{metric}"]
        df[f"global_{metric}_annual_mean"] = df[f"global_{metric}"] / years
        df[f"seasonal_{metric}_annual_mean"] = df[f"seasonal_{metric}"] / years
        denom = df[f"global_{metric}"].replace(0, np.nan)
        df[f"pct_change_{metric}"] = 100.0 * df[f"delta_{metric}"] / denom
    return df


def to_grid_dataset(
    df: pd.DataFrame,
    lat_vals: np.ndarray,
    lon_vals: np.ndarray,
    args: argparse.Namespace,
) -> xr.Dataset:
    fields = [
        "global_compound_event_count",
        "seasonal_compound_event_count",
        "delta_compound_event_count",
        "pct_change_compound_event_count",
        "global_compound_day_count",
        "seasonal_compound_day_count",
        "delta_compound_day_count",
        "pct_change_compound_day_count",
    ]
    data_vars = {}
    for field in fields:
        arr = np.full((len(lat_vals), len(lon_vals)), np.nan, dtype=np.float32)
        for row in df.itertuples(index=False):
            arr[int(row.i_lat), int(row.i_lon)] = getattr(row, field)
        data_vars[field] = (("latitude", "longitude"), arr)

    ds = xr.Dataset(
        data_vars=data_vars,
        coords={"latitude": lat_vals, "longitude": lon_vals},
        attrs={
            "analysis": "Exploratory global-vs-seasonal q90 compound comparison",
            "input": str(args.input),
            "hs_var": args.hs_var,
            "ssh_total_var": args.ssh_total_var,
            "quantile": args.quantile,
            "max_gap_days": args.max_gap_days,
            "coastal_max_dist_km": args.coastal_max_dist_km,
            "min_valid_frac": args.min_valid_frac,
        },
    )
    return ds


def build_summary(df: pd.DataFrame, args: argparse.Namespace, time: pd.DatetimeIndex) -> dict:
    event_delta = df["delta_compound_event_count"]
    day_delta = df["delta_compound_day_count"]
    return {
        "input": str(args.input),
        "hs_var": args.hs_var,
        "ssh_total_var": args.ssh_total_var,
        "quantile": args.quantile,
        "threshold_period": [str(time[0].date()), str(time[-1].date())],
        "seasonal_thresholds": "DJF/MAM/JJA/SON q90 per point and variable",
        "max_gap_days": args.max_gap_days,
        "n_analysis_points": int(len(df)),
        "compound_events": {
            "global_total": int(df["global_compound_event_count"].sum()),
            "seasonal_total": int(df["seasonal_compound_event_count"].sum()),
            "delta_total": int(event_delta.sum()),
            "points_increased": int((event_delta > 0).sum()),
            "points_decreased": int((event_delta < 0).sum()),
            "points_unchanged": int((event_delta == 0).sum()),
            "mean_global_per_point": float(df["global_compound_event_count"].mean()),
            "mean_seasonal_per_point": float(df["seasonal_compound_event_count"].mean()),
            "median_delta_per_point": float(event_delta.median()),
        },
        "compound_days": {
            "global_total": int(df["global_compound_day_count"].sum()),
            "seasonal_total": int(df["seasonal_compound_day_count"].sum()),
            "delta_total": int(day_delta.sum()),
            "points_increased": int((day_delta > 0).sum()),
            "points_decreased": int((day_delta < 0).sum()),
            "points_unchanged": int((day_delta == 0).sum()),
            "mean_global_per_point": float(df["global_compound_day_count"].mean()),
            "mean_seasonal_per_point": float(df["seasonal_compound_day_count"].mean()),
            "median_delta_per_point": float(day_delta.median()),
        },
    }


def plot_count_maps(
    ds: xr.Dataset,
    *,
    metric: str,
    title: str,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    lon = ds.longitude.values
    lat = ds.latitude.values
    fields = [
        (f"global_{metric}", "Global q90", "viridis"),
        (f"seasonal_{metric}", "Seasonal q90", "viridis"),
        (f"delta_{metric}", "Seasonal - global", "RdBu_r"),
    ]

    global_values = np.concatenate(
        [
            ds[f"global_{metric}"].values[np.isfinite(ds[f"global_{metric}"].values)],
            ds[f"seasonal_{metric}"].values[np.isfinite(ds[f"seasonal_{metric}"].values)],
        ]
    )
    count_vmax = float(np.nanpercentile(global_values, 98)) if global_values.size else 1.0
    if count_vmax <= 0:
        count_vmax = 1.0

    delta_values = ds[f"delta_{metric}"].values
    finite_delta = delta_values[np.isfinite(delta_values)]
    delta_abs = float(np.nanpercentile(np.abs(finite_delta), 98)) if finite_delta.size else 1.0
    if delta_abs <= 0:
        delta_abs = 1.0

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(11.4, 5.6),
        subplot_kw={"projection": CRS},
        constrained_layout=False,
    )
    fig.subplots_adjust(left=0.055, right=0.985, bottom=0.13, top=0.88, wspace=0.06)

    geoms = _coastline_geometries(coastline)
    extent = _extent(lon, lat)
    for ax, (field, label, cmap) in zip(axes, fields):
        values = ds[field].values
        if field.startswith("delta"):
            vmin, vmax = -delta_abs, delta_abs
        else:
            vmin, vmax = 0.0, count_vmax
        mesh = ax.pcolormesh(
            lon,
            lat,
            values,
            shading="auto",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            transform=CRS,
        )
        ax.set_title(label, fontsize=11)
        ax.set_extent(extent, crs=CRS)
        ax.set_facecolor("#f4f1ea")
        if geoms:
            ax.add_geometries(geoms, CRS, facecolor="none", edgecolor="0.15", linewidth=0.45)
        gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="0.55", alpha=0.45)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {"size": 8}
        gl.ylabel_style = {"size": 8}
        cbar = fig.colorbar(mesh, ax=ax, orientation="horizontal", shrink=0.86, pad=0.055)
        cbar.ax.tick_params(labelsize=8)

    fig.suptitle(title, fontsize=14)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    log.info("Wrote %s", out_path)


def plot_scatter(df: pd.DataFrame, *, out_path: Path, dpi: int) -> None:
    x = df["global_compound_event_count"].values
    y = df["seasonal_compound_event_count"].values
    lim = max(float(np.nanmax(x)), float(np.nanmax(y))) * 1.03
    fig, ax = plt.subplots(figsize=(6.2, 5.6), constrained_layout=True)
    ax.scatter(x, y, s=14, alpha=0.65, c=df["grid_lat"], cmap="viridis")
    ax.plot([0, lim], [0, lim], color="0.25", lw=1.0, ls="--")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Compound episodes with global q90")
    ax.set_ylabel("Compound episodes with seasonal q90")
    ax.set_title("Per-point compound episode counts")
    ax.grid(True, color="0.8", lw=0.5)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def _extent(lon: np.ndarray, lat: np.ndarray) -> list[float]:
    lon_pad = max(0.2, float(np.nanmax(lon) - np.nanmin(lon)) * 0.03)
    lat_pad = max(0.2, float(np.nanmax(lat) - np.nanmin(lat)) * 0.03)
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
    except Exception as exc:
        log.warning("Could not read coastline %s: %s", path, exc)
        return []


if __name__ == "__main__":
    main()
