"""Regional seasonal bar charts for global-vs-seasonal q90 compound events.

Exploratory analysis only. Counts compound *episodes* by the season of the
first overlap day between Hs and SSH_total episodes, comparing:

* global q90 thresholds computed from the full record;
* seasonal q90 thresholds computed separately for DJF/MAM/JJA/SON.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import cartopy.crs as ccrs
from cartopy.io import shapereader
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib.colors import LinearSegmentedColormap


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.exploratory.seasonal_q90_compound_compare import (  # noqa: E402
    DEFAULT_COASTLINE,
    DEFAULT_INPUT,
    SEASON_BY_MONTH,
    SEASON_NAMES,
    _cluster_episodes,
    _nanquantile,
    identify_analysis_points,
)


DEFAULT_OUTPUT = ROOT / "outputs/exploratory_seasonal_q90_compounds_region_bars"
REGION_ORDER = ["S", "SE", "NE", "N"]
METHOD_ORDER = ["Global q90", "Seasonal q90"]
REGION_COLORS = {
    "Global q90": "#476A9A",
    "Seasonal q90": "#D95F02",
}
COUNT_CMAP = LinearSegmentedColormap.from_list(
    "compound_count",
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
CRS = ccrs.PlateCarree()

log = logging.getLogger("seasonal_q90_region_bars")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bar charts of compound episodes by season and Brazil coastal region."
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
    for directory in (fig_dir, tab_dir):
        directory.mkdir(parents=True, exist_ok=True)

    ds = xr.open_dataset(args.input)
    for var in [args.hs_var, args.ssh_total_var]:
        if var not in ds:
            raise ValueError(f"{var!r} not found in {args.input}. Available: {list(ds.data_vars)}")

    points_df = identify_analysis_points(
        ds,
        args.hs_var,
        args.ssh_total_var,
        args.coastline,
        args.coastal_max_dist_km,
        args.min_valid_frac,
    )
    points_df["region"] = points_df["grid_lat"].map(classify_region)
    points_df = points_df[points_df["region"].isin(REGION_ORDER)].copy()
    log.info("Analysis points by region: %s", points_df["region"].value_counts().to_dict())

    time = pd.DatetimeIndex(ds.time.values)
    season_code = np.array([SEASON_BY_MONTH[m] for m in time.month], dtype=np.int8)
    day_ord = np.array([ts.toordinal() for ts in time.date], dtype=np.int32)

    hs_data = ds[args.hs_var].values
    ssh_data = ds[args.ssh_total_var].values

    rows = []
    n_points = len(points_df)
    for idx, row in enumerate(points_df.itertuples(index=False), start=1):
        if idx == 1 or idx % max(1, n_points // 10) == 0:
            log.info("Processing point %d/%d", idx, n_points)
        hs = hs_data[:, int(row.i_lat), int(row.i_lon)]
        ssh = ssh_data[:, int(row.i_lat), int(row.i_lon)]

        point_counts = compare_point_by_season(
            hs=hs,
            ssh=ssh,
            season_code=season_code,
            day_ord=day_ord,
            q=args.quantile,
            max_gap_days=args.max_gap_days,
        )
        for method, counts in point_counts.items():
            for season, count in counts.items():
                rows.append(
                    {
                        "grid_lat": float(row.grid_lat),
                        "grid_lon": float(row.grid_lon),
                        "i_lat": int(row.i_lat),
                        "i_lon": int(row.i_lon),
                        "region": row.region,
                        "method": method,
                        "season": season,
                        "compound_event_count": int(count),
                    }
                )

    point_counts_df = pd.DataFrame(rows)
    point_counts_path = tab_dir / "compound_event_counts_by_point_region_season.csv"
    point_counts_df.to_csv(point_counts_path, index=False)
    log.info("Wrote %s", point_counts_path)

    region_counts = (
        point_counts_df
        .groupby(["region", "method", "season"], as_index=False)["compound_event_count"]
        .sum()
    )
    region_counts["region"] = pd.Categorical(region_counts["region"], REGION_ORDER, ordered=True)
    region_counts["method"] = pd.Categorical(region_counts["method"], METHOD_ORDER, ordered=True)
    region_counts["season"] = pd.Categorical(region_counts["season"], SEASON_NAMES.tolist(), ordered=True)
    region_counts = region_counts.sort_values(["region", "season", "method"]).reset_index(drop=True)

    region_point_counts = (
        points_df.groupby("region", as_index=False)
        .size()
        .rename(columns={"size": "n_analysis_points"})
    )
    region_counts = region_counts.merge(region_point_counts, on="region", how="left")
    region_counts["events_per_point"] = (
        region_counts["compound_event_count"] / region_counts["n_analysis_points"]
    )

    region_counts_path = tab_dir / "compound_event_counts_by_region_season.csv"
    region_counts.to_csv(region_counts_path, index=False)
    log.info("Wrote %s", region_counts_path)

    plot_region_bars(
        region_counts,
        out_path=fig_dir / "fig_compound_events_by_region_season_global_vs_seasonal.png",
        dpi=args.dpi,
        value_col="compound_event_count",
        ylabel="Compound episode count",
        title="Compound episodes by season and coastal Brazil region",
    )
    plot_region_bars(
        region_counts,
        out_path=fig_dir / "fig_compound_events_per_point_by_region_season_global_vs_seasonal.png",
        dpi=args.dpi,
        value_col="events_per_point",
        ylabel="Compound episodes per analysis point",
        title="Compound episodes per point by season and coastal Brazil region",
    )
    plot_seasonal_count_maps(
        point_counts_df,
        lat_vals=ds.latitude.values,
        lon_vals=ds.longitude.values,
        out_path=fig_dir / "fig_compound_event_count_seasonal_maps_global_vs_seasonal_q90.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )


def compare_point_by_season(
    *,
    hs: np.ndarray,
    ssh: np.ndarray,
    season_code: np.ndarray,
    day_ord: np.ndarray,
    q: float,
    max_gap_days: int,
) -> dict[str, dict[str, int]]:
    hs_global_thr = _nanquantile(hs, q)
    ssh_global_thr = _nanquantile(ssh, q)
    hs_season_thr = np.array([_nanquantile(hs[season_code == s], q) for s in range(4)])
    ssh_season_thr = np.array([_nanquantile(ssh[season_code == s], q) for s in range(4)])

    hs_global = np.isfinite(hs) & (hs >= hs_global_thr)
    ssh_global = np.isfinite(ssh) & (ssh >= ssh_global_thr)
    hs_seasonal = np.isfinite(hs) & (hs >= hs_season_thr[season_code])
    ssh_seasonal = np.isfinite(ssh) & (ssh >= ssh_season_thr[season_code])

    return {
        "Global q90": compound_event_season_counts(
            hs_global, ssh_global, season_code, day_ord, max_gap_days
        ),
        "Seasonal q90": compound_event_season_counts(
            hs_seasonal, ssh_seasonal, season_code, day_ord, max_gap_days
        ),
    }


def compound_event_season_counts(
    hs_mask: np.ndarray,
    ssh_mask: np.ndarray,
    season_code: np.ndarray,
    day_ord: np.ndarray,
    max_gap_days: int,
) -> dict[str, int]:
    hs_episodes = _cluster_episodes(hs_mask, day_ord, max_gap_days)
    ssh_episodes = _cluster_episodes(ssh_mask, day_ord, max_gap_days)
    event_start_indices = compound_event_start_indices(hs_episodes, ssh_episodes, len(hs_mask))

    counts = {name: 0 for name in SEASON_NAMES.tolist()}
    for i_start in event_start_indices:
        counts[str(SEASON_NAMES[int(season_code[i_start])])] += 1
    return counts


def compound_event_start_indices(
    hs_episodes: list[np.ndarray],
    ssh_episodes: list[np.ndarray],
    n_time: int,
) -> list[int]:
    if not hs_episodes or not ssh_episodes:
        return []

    hs_label = np.full(n_time, -1, dtype=np.int32)
    ssh_label = np.full(n_time, -1, dtype=np.int32)
    for i, ep in enumerate(hs_episodes):
        hs_label[ep] = i
    for i, ep in enumerate(ssh_episodes):
        ssh_label[ep] = i

    overlap_idx = np.flatnonzero((hs_label >= 0) & (ssh_label >= 0))
    if overlap_idx.size == 0:
        return []

    pair_to_start: dict[tuple[int, int], int] = {}
    for idx in overlap_idx:
        pair = (int(hs_label[idx]), int(ssh_label[idx]))
        pair_to_start[pair] = min(pair_to_start.get(pair, int(idx)), int(idx))

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

    pair_nodes = {}
    for h_idx, s_idx in pair_to_start:
        h_node = ("h", h_idx)
        s_node = ("s", s_idx)
        union(h_node, s_node)
        pair_nodes[(h_idx, s_idx)] = (h_node, s_node)

    group_starts: dict[tuple[str, int], int] = {}
    for pair, start_idx in pair_to_start.items():
        root = find(pair_nodes[pair][0])
        group_starts[root] = min(group_starts.get(root, start_idx), start_idx)
    return sorted(group_starts.values())


def classify_region(lat: float) -> str:
    """Approximate coastal Brazil macro-region from latitude.

    Boundaries follow major coastal state transitions:
    S/SE: PR-SP around 25.3 S; SE/NE: ES-BA around 18.3 S;
    NE/N: MA-PA around 1.4 S. This is sufficient for an exploratory map-free
    aggregation using model grid-point coordinates.
    """
    if lat <= -25.3:
        return "S"
    if lat <= -18.3:
        return "SE"
    if lat <= -1.4:
        return "NE"
    return "N"


def plot_region_bars(
    counts: pd.DataFrame,
    *,
    out_path: Path,
    dpi: int,
    value_col: str,
    ylabel: str,
    title: str,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.2), constrained_layout=True)
    axes = axes.ravel()
    x = np.arange(len(SEASON_NAMES))
    width = 0.36

    for ax, region in zip(axes, REGION_ORDER):
        sub = counts[counts["region"] == region]
        for offset, method in [(-width / 2, "Global q90"), (width / 2, "Seasonal q90")]:
            values = []
            for season in SEASON_NAMES:
                row = sub[(sub["method"] == method) & (sub["season"] == season)]
                values.append(float(row[value_col].iloc[0]) if not row.empty else 0.0)
            ax.bar(
                x + offset,
                values,
                width=width,
                label=method,
                color=REGION_COLORS[method],
                edgecolor="0.2",
                linewidth=0.4,
            )

        n_points = int(sub["n_analysis_points"].iloc[0]) if not sub.empty else 0
        ax.set_title(f"{region} (n={n_points} pts)")
        ax.set_xticks(x)
        ax.set_xticklabels(SEASON_NAMES)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="0.85", linewidth=0.6)
        ax.set_axisbelow(True)
        if region == "S":
            ax.legend(frameon=False)

    fig.suptitle(title, fontsize=14)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def plot_seasonal_count_maps(
    point_counts: pd.DataFrame,
    *,
    lat_vals: np.ndarray,
    lon_vals: np.ndarray,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    finite_counts = point_counts["compound_event_count"].to_numpy(dtype=float)
    finite_counts = finite_counts[np.isfinite(finite_counts)]
    vmax = float(np.nanpercentile(finite_counts, 98)) if finite_counts.size else 1.0
    if vmax <= 0:
        vmax = 1.0

    fig = plt.figure(figsize=(5.2, 10.8), constrained_layout=False)
    gs = fig.add_gridspec(
        5,
        3,
        height_ratios=[1.0, 1.0, 1.0, 1.0, 0.05],
        width_ratios=[1.0, 0.08, 1.0],
        left=0.12,
        right=0.98,
        bottom=0.05,
        top=0.925,
        wspace=0.02,
        hspace=0.12,
    )
    axes = np.empty((len(SEASON_NAMES), len(METHOD_ORDER)), dtype=object)
    for i in range(len(SEASON_NAMES)):
        axes[i, 0] = fig.add_subplot(gs[i, 0], projection=CRS)
        axes[i, 1] = fig.add_subplot(gs[i, 2], projection=CRS)
        label_ax = fig.add_subplot(gs[i, 1])
        label_ax.axis("off")
        label_ax.text(
            0.55,
            0.5,
            str(SEASON_NAMES[i]),
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
        )
    cax = fig.add_subplot(gs[4, :])
    geoms = _coastline_geometries(coastline)
    extent = _extent(lon_vals, lat_vals)
    mesh = None

    for i, season in enumerate(SEASON_NAMES):
        for j, method in enumerate(METHOD_ORDER):
            ax = axes[i, j]
            field = np.full((len(lat_vals), len(lon_vals)), np.nan, dtype=np.float32)
            season_rows = point_counts[
                (point_counts["season"] == season) & (point_counts["method"] == method)
            ]
            for row in season_rows.itertuples(index=False):
                field[int(row.i_lat), int(row.i_lon)] = float(row.compound_event_count)

            mesh = ax.pcolormesh(
                lon_vals,
                lat_vals,
                field,
                shading="auto",
                cmap=COUNT_CMAP,
                vmin=0.0,
                vmax=vmax,
                transform=CRS,
            )
            if i == 0:
                ax.set_title(method, fontsize=12)
            ax.set_extent(extent, crs=CRS)
            ax.set_facecolor("#f4f1ea")
            if geoms:
                ax.add_geometries(geoms, CRS, facecolor="none", edgecolor="0.15", linewidth=0.45)
            gl = ax.gridlines(draw_labels=True, linewidth=0.25, color="0.55", alpha=0.45)
            gl.top_labels = False
            gl.right_labels = False
            gl.left_labels = j == 0
            gl.bottom_labels = i == len(SEASON_NAMES) - 1
            gl.xlabel_style = {"size": 8}
            gl.ylabel_style = {"size": 8}

    cbar = fig.colorbar(mesh, cax=cax, orientation="horizontal")
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label("Compound episode count")
    fig.suptitle("Compound counts by season", fontsize=12)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
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
