"""Regional seasonal mean-intensity figures for q90 compound events.

Exploratory analysis only. Replicates the seasonal region/map figures produced
for compound episode counts, but uses mean normalized compound intensity.

Intensity follows the Step 3 storm-catalog convention:

    hs_peak_norm = clip((hs_peak - Q05_hs) / (Q95_hs - Q05_hs), 0, 1)
    ssh_peak_norm = clip((ssh_peak - Q05_ssh) / (Q95_ssh - Q05_ssh), 0, 1)
    compound_intensity_norm = 0.5 * (hs_peak_norm + ssh_peak_norm)

Here Q05/Q95 are computed across all compound-event peaks detected in this
exploratory comparison, pooling the global-q90 and seasonal-q90 methods so the
two methods share a common intensity scale.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr


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
from src.exploratory.seasonal_q90_region_bars import (  # noqa: E402
    COUNT_CMAP,
    CRS,
    METHOD_ORDER,
    REGION_COLORS,
    REGION_ORDER,
    _coastline_geometries,
    _extent,
    classify_region,
)


DEFAULT_OUTPUT = ROOT / "outputs/exploratory_seasonal_q90_compounds_region_bars"
log = logging.getLogger("seasonal_q90_region_intensity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seasonal mean-intensity figures for global-vs-seasonal q90 compound events."
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

    event_rows = []
    n_points = len(points_df)
    for idx, row in enumerate(points_df.itertuples(index=False), start=1):
        if idx == 1 or idx % max(1, n_points // 10) == 0:
            log.info("Processing point %d/%d", idx, n_points)

        i_lat = int(row.i_lat)
        i_lon = int(row.i_lon)
        hs = hs_data[:, i_lat, i_lon]
        ssh = ssh_data[:, i_lat, i_lon]
        point_events = compare_point_events_by_season(
            hs=hs,
            ssh=ssh,
            season_code=season_code,
            day_ord=day_ord,
            q=args.quantile,
            max_gap_days=args.max_gap_days,
        )

        for method, events in point_events.items():
            for event in events:
                event_rows.append(
                    {
                        "grid_lat": float(row.grid_lat),
                        "grid_lon": float(row.grid_lon),
                        "i_lat": i_lat,
                        "i_lon": i_lon,
                        "region": row.region,
                        "method": method,
                        **event,
                    }
                )

    events_df = pd.DataFrame(event_rows)
    if events_df.empty:
        raise RuntimeError("No compound events were detected; cannot compute intensity figures.")

    norm_refs = add_normalized_intensity(events_df)
    events_path = tab_dir / "compound_event_intensity_by_point_region_season.csv"
    events_df.to_csv(events_path, index=False)
    log.info("Wrote %s", events_path)

    point_intensity = build_point_intensity_table(events_df, points_df)
    point_path = tab_dir / "compound_mean_intensity_by_point_region_season.csv"
    point_intensity.to_csv(point_path, index=False)
    log.info("Wrote %s", point_path)

    region_event = build_region_event_weighted_table(events_df, points_df)
    region_point = build_region_point_weighted_table(point_intensity, points_df)
    region_intensity = region_event.merge(
        region_point,
        on=["region", "method", "season", "n_analysis_points"],
        how="outer",
    )
    region_intensity_path = tab_dir / "compound_mean_intensity_by_region_season.csv"
    region_intensity.to_csv(region_intensity_path, index=False)
    log.info("Wrote %s", region_intensity_path)

    metadata = {
        "input": str(args.input),
        "hs_var": args.hs_var,
        "ssh_total_var": args.ssh_total_var,
        "quantile": args.quantile,
        "threshold_methods": METHOD_ORDER,
        "intensity_definition": (
            "0.5 * (normalized Hs peak + normalized SSH_total peak), "
            "with Q05/Q95 normalization pooled across detected global-q90 and "
            "seasonal-q90 compound events."
        ),
        "normalization_refs": norm_refs,
        "n_compound_event_rows": int(len(events_df)),
    }
    metadata_path = tab_dir / "compound_mean_intensity_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log.info("Wrote %s", metadata_path)

    plot_region_bars(
        region_event,
        out_path=fig_dir / "fig_compound_mean_intensity_by_region_season_global_vs_seasonal.png",
        dpi=args.dpi,
        value_col="mean_compound_intensity_norm_event_weighted",
        ylabel="Mean compound intensity (norm.)",
        title="Mean compound intensity by season and coastal Brazil region",
    )
    plot_region_bars(
        region_point,
        out_path=fig_dir / "fig_compound_mean_intensity_per_point_by_region_season_global_vs_seasonal.png",
        dpi=args.dpi,
        value_col="mean_compound_intensity_norm_point_weighted",
        ylabel="Mean point compound intensity (norm.)",
        title="Mean point compound intensity by season and coastal Brazil region",
    )
    plot_seasonal_intensity_maps(
        point_intensity,
        lat_vals=ds.latitude.values,
        lon_vals=ds.longitude.values,
        out_path=fig_dir / "fig_compound_mean_intensity_seasonal_maps_global_vs_seasonal_q90.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )


def compare_point_events_by_season(
    *,
    hs: np.ndarray,
    ssh: np.ndarray,
    season_code: np.ndarray,
    day_ord: np.ndarray,
    q: float,
    max_gap_days: int,
) -> dict[str, list[dict]]:
    hs_global_thr = _nanquantile(hs, q)
    ssh_global_thr = _nanquantile(ssh, q)
    hs_season_thr = np.array([_nanquantile(hs[season_code == s], q) for s in range(4)])
    ssh_season_thr = np.array([_nanquantile(ssh[season_code == s], q) for s in range(4)])

    hs_global = np.isfinite(hs) & (hs >= hs_global_thr)
    ssh_global = np.isfinite(ssh) & (ssh >= ssh_global_thr)
    hs_seasonal = np.isfinite(hs) & (hs >= hs_season_thr[season_code])
    ssh_seasonal = np.isfinite(ssh) & (ssh >= ssh_season_thr[season_code])

    return {
        "Global q90": compound_event_records(
            hs, ssh, hs_global, ssh_global, season_code, day_ord, max_gap_days
        ),
        "Seasonal q90": compound_event_records(
            hs, ssh, hs_seasonal, ssh_seasonal, season_code, day_ord, max_gap_days
        ),
    }


def compound_event_records(
    hs: np.ndarray,
    ssh: np.ndarray,
    hs_mask: np.ndarray,
    ssh_mask: np.ndarray,
    season_code: np.ndarray,
    day_ord: np.ndarray,
    max_gap_days: int,
) -> list[dict]:
    hs_episodes = _cluster_episodes(hs_mask, day_ord, max_gap_days)
    ssh_episodes = _cluster_episodes(ssh_mask, day_ord, max_gap_days)
    groups = compound_episode_groups(hs_episodes, ssh_episodes, len(hs_mask))

    records = []
    for group_id, group in enumerate(groups):
        hs_idx = np.unique(np.concatenate([hs_episodes[i] for i in sorted(group["hs"])])).astype(np.int32)
        ssh_idx = np.unique(np.concatenate([ssh_episodes[i] for i in sorted(group["ssh"])])).astype(np.int32)
        start_idx = int(group["start_idx"])
        records.append(
            {
                "season": str(SEASON_NAMES[int(season_code[start_idx])]),
                "event_start_index": start_idx,
                "event_group_id": group_id,
                "peak_hs": float(np.nanmax(hs[hs_idx])) if hs_idx.size else np.nan,
                "peak_ssh_total": float(np.nanmax(ssh[ssh_idx])) if ssh_idx.size else np.nan,
                "n_hs_episodes": int(len(group["hs"])),
                "n_ssh_episodes": int(len(group["ssh"])),
            }
        )
    return records


def compound_episode_groups(
    hs_episodes: list[np.ndarray],
    ssh_episodes: list[np.ndarray],
    n_time: int,
) -> list[dict]:
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

    groups_by_root: dict[tuple[str, int], dict] = {}
    for (h_idx, s_idx), start_idx in pair_to_start.items():
        root = find(pair_nodes[(h_idx, s_idx)][0])
        group = groups_by_root.setdefault(root, {"hs": set(), "ssh": set(), "start_idx": start_idx})
        group["hs"].add(int(h_idx))
        group["ssh"].add(int(s_idx))
        group["start_idx"] = min(int(group["start_idx"]), int(start_idx))

    return sorted(groups_by_root.values(), key=lambda item: int(item["start_idx"]))


def add_normalized_intensity(events: pd.DataFrame) -> dict[str, float]:
    hs_ref_low = float(np.nanpercentile(events["peak_hs"], 5))
    hs_ref_high = float(np.nanpercentile(events["peak_hs"], 95))
    ssh_ref_low = float(np.nanpercentile(events["peak_ssh_total"], 5))
    ssh_ref_high = float(np.nanpercentile(events["peak_ssh_total"], 95))
    hs_range = max(hs_ref_high - hs_ref_low, 1e-9)
    ssh_range = max(ssh_ref_high - ssh_ref_low, 1e-9)

    hs_norm = np.clip((events["peak_hs"].to_numpy(float) - hs_ref_low) / hs_range, 0.0, 1.0)
    ssh_norm = np.clip(
        (events["peak_ssh_total"].to_numpy(float) - ssh_ref_low) / ssh_range,
        0.0,
        1.0,
    )
    events["peak_hs_norm"] = hs_norm
    events["peak_ssh_total_norm"] = ssh_norm
    events["compound_intensity_norm"] = 0.5 * (hs_norm + ssh_norm)

    return {
        "hs_ref_low_q05": round(hs_ref_low, 4),
        "hs_ref_high_q95": round(hs_ref_high, 4),
        "ssh_total_ref_low_q05": round(ssh_ref_low, 4),
        "ssh_total_ref_high_q95": round(ssh_ref_high, 4),
    }


def build_point_intensity_table(events: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        events
        .groupby(["grid_lat", "grid_lon", "i_lat", "i_lon", "region", "method", "season"], as_index=False)
        .agg(
            compound_event_count=("compound_intensity_norm", "size"),
            mean_compound_intensity_norm=("compound_intensity_norm", "mean"),
            p95_compound_intensity_norm=("compound_intensity_norm", lambda s: float(np.nanpercentile(s, 95))),
            mean_peak_hs=("peak_hs", "mean"),
            mean_peak_ssh_total=("peak_ssh_total", "mean"),
        )
    )

    skeleton_rows = []
    for point in points.itertuples(index=False):
        for method in METHOD_ORDER:
            for season in SEASON_NAMES:
                skeleton_rows.append(
                    {
                        "grid_lat": float(point.grid_lat),
                        "grid_lon": float(point.grid_lon),
                        "i_lat": int(point.i_lat),
                        "i_lon": int(point.i_lon),
                        "region": point.region,
                        "method": method,
                        "season": str(season),
                    }
                )
    skeleton = pd.DataFrame(skeleton_rows)
    merged = skeleton.merge(
        grouped,
        on=["grid_lat", "grid_lon", "i_lat", "i_lon", "region", "method", "season"],
        how="left",
    )
    merged["compound_event_count"] = merged["compound_event_count"].fillna(0).astype(int)
    return merged


def build_region_event_weighted_table(events: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    region_point_counts = (
        points.groupby("region", as_index=False)
        .size()
        .rename(columns={"size": "n_analysis_points"})
    )
    grouped = (
        events
        .groupby(["region", "method", "season"], as_index=False)
        .agg(
            compound_event_count=("compound_intensity_norm", "size"),
            mean_compound_intensity_norm_event_weighted=("compound_intensity_norm", "mean"),
            p95_compound_intensity_norm_event_weighted=("compound_intensity_norm", lambda s: float(np.nanpercentile(s, 95))),
            mean_peak_hs_event_weighted=("peak_hs", "mean"),
            mean_peak_ssh_total_event_weighted=("peak_ssh_total", "mean"),
        )
    )
    return complete_region_table(grouped, region_point_counts)


def build_region_point_weighted_table(point_intensity: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    region_point_counts = (
        points.groupby("region", as_index=False)
        .size()
        .rename(columns={"size": "n_analysis_points"})
    )
    grouped = (
        point_intensity
        .groupby(["region", "method", "season"], as_index=False)
        .agg(
            points_with_events=("mean_compound_intensity_norm", lambda s: int(np.isfinite(s).sum())),
            mean_compound_intensity_norm_point_weighted=("mean_compound_intensity_norm", "mean"),
            mean_peak_hs_point_weighted=("mean_peak_hs", "mean"),
            mean_peak_ssh_total_point_weighted=("mean_peak_ssh_total", "mean"),
        )
    )
    return complete_region_table(grouped, region_point_counts)


def complete_region_table(df: pd.DataFrame, region_point_counts: pd.DataFrame) -> pd.DataFrame:
    skeleton = pd.MultiIndex.from_product(
        [REGION_ORDER, METHOD_ORDER, SEASON_NAMES.tolist()],
        names=["region", "method", "season"],
    ).to_frame(index=False)
    out = skeleton.merge(df, on=["region", "method", "season"], how="left")
    out = out.merge(region_point_counts, on="region", how="left")
    out["n_analysis_points"] = out["n_analysis_points"].fillna(0).astype(int)
    out["region"] = pd.Categorical(out["region"], REGION_ORDER, ordered=True)
    out["method"] = pd.Categorical(out["method"], METHOD_ORDER, ordered=True)
    out["season"] = pd.Categorical(out["season"], SEASON_NAMES.tolist(), ordered=True)
    return out.sort_values(["region", "season", "method"]).reset_index(drop=True)


def plot_region_bars(
    values_df: pd.DataFrame,
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
        sub = values_df[values_df["region"] == region]
        for offset, method in [(-width / 2, "Global q90"), (width / 2, "Seasonal q90")]:
            vals = []
            for season in SEASON_NAMES:
                row = sub[(sub["method"] == method) & (sub["season"] == season)]
                vals.append(float(row[value_col].iloc[0]) if not row.empty else np.nan)
            ax.bar(
                x + offset,
                vals,
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
        ax.set_ylim(0, 1)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="0.85", linewidth=0.6)
        ax.set_axisbelow(True)
        if region == "S":
            ax.legend(frameon=False)

    fig.suptitle(title, fontsize=14)
    fig.savefig(out_path, dpi=dpi)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def plot_seasonal_intensity_maps(
    point_intensity: pd.DataFrame,
    *,
    lat_vals: np.ndarray,
    lon_vals: np.ndarray,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
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
            rows = point_intensity[
                (point_intensity["season"] == season) & (point_intensity["method"] == method)
            ]
            for row in rows.itertuples(index=False):
                field[int(row.i_lat), int(row.i_lon)] = float(row.mean_compound_intensity_norm)

            mesh = ax.pcolormesh(
                lon_vals,
                lat_vals,
                field,
                shading="auto",
                cmap=COUNT_CMAP,
                vmin=0.0,
                vmax=1.0,
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
    cbar.set_label("Mean compound intensity (norm.)")
    fig.suptitle("Mean compound intensity by season", fontsize=12)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    log.info("Wrote %s", out_path)


if __name__ == "__main__":
    main()
