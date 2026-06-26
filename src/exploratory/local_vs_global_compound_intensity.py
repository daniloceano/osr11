"""Compare domain-wide and local normalization of compound-event intensity.

Exploratory analysis only. This script reuses the consolidated compound-event
catalog and recomputes mean normalized intensity per point with two scales:

* domain-wide Q05/Q95 peak references, matching the production Step 3 method;
* local Q05/Q95 peak references, computed independently at each grid point.

The event detection itself is not modified.
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
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "outputs/storm_catalog/compound/compound_catalog.json"
DEFAULT_SUMMARY = ROOT / "outputs/storm_catalog/compound/compound_summary.json"
DEFAULT_OUTPUT = ROOT / "outputs/exploratory_local_intensity_normalization"
DEFAULT_COASTLINE = ROOT / "data/ne_10m_coastline/ne_10m_coastline.shp"

CRS = ccrs.PlateCarree()
INTENSITY_CMAP = LinearSegmentedColormap.from_list(
    "compound_intensity",
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

log = logging.getLogger("local_vs_global_compound_intensity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare domain-wide and local compound-intensity normalization."
    )
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
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

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    events = flatten_events(catalog)
    if events.empty:
        raise RuntimeError(f"No compound events found in {args.catalog}")

    global_refs = compute_reference_quantiles(events)
    log.info("Domain-wide refs: %s", global_refs)

    point_metrics = compute_point_metrics(catalog, global_refs)
    point_metrics_path = tab_dir / "compound_intensity_global_vs_local_by_point.csv"
    point_metrics.to_csv(point_metrics_path, index=False)
    log.info("Wrote %s", point_metrics_path)

    metadata = {
        "catalog": str(args.catalog),
        "summary": str(args.summary),
        "n_grid_points": int(len(point_metrics)),
        "n_compound_events": int(len(events)),
        "domain_wide_refs_recomputed_from_catalog": {
            key: round(float(value), 6) for key, value in global_refs.items()
        },
        "production_summary_refs": load_summary_refs(args.summary),
        "intensity_definition": (
            "0.5 * (normalized peak_hs + normalized peak_ssh_total). "
            "The current/global panel uses Q05/Q95 references pooled across all "
            "compound events in the domain. The local panel computes Q05/Q95 "
            "separately for the compound events at each grid point."
        ),
    }
    metadata_path = tab_dir / "compound_intensity_global_vs_local_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log.info("Wrote %s", metadata_path)

    plot_comparison_map(
        point_metrics,
        out_path=fig_dir / "fig_compound_mean_intensity_global_vs_local_normalization.png",
        coastline=args.coastline,
        dpi=args.dpi,
    )


def flatten_events(catalog: list[dict]) -> pd.DataFrame:
    rows = []
    for point in catalog:
        for event in point.get("compound_events", []):
            rows.append(
                {
                    "grid_lat": float(point["grid_lat"]),
                    "grid_lon": float(point["grid_lon"]),
                    "peak_hs": float(event["peak_hs"]),
                    "peak_ssh_total": float(event["peak_ssh_total"]),
                }
            )
    return pd.DataFrame(rows)


def compute_reference_quantiles(events: pd.DataFrame) -> dict[str, float]:
    return {
        "hs_ref_low": float(np.nanpercentile(events["peak_hs"].to_numpy(), 5)),
        "hs_ref_high": float(np.nanpercentile(events["peak_hs"].to_numpy(), 95)),
        "ssh_ref_low": float(np.nanpercentile(events["peak_ssh_total"].to_numpy(), 5)),
        "ssh_ref_high": float(np.nanpercentile(events["peak_ssh_total"].to_numpy(), 95)),
    }


def compute_point_metrics(catalog: list[dict], global_refs: dict[str, float]) -> pd.DataFrame:
    rows = []
    for point in catalog:
        events = point.get("compound_events", [])
        hs_peaks = np.array([float(event["peak_hs"]) for event in events], dtype=float)
        ssh_peaks = np.array([float(event["peak_ssh_total"]) for event in events], dtype=float)

        if len(events) == 0:
            local_refs = {
                "local_hs_ref_low": np.nan,
                "local_hs_ref_high": np.nan,
                "local_ssh_ref_low": np.nan,
                "local_ssh_ref_high": np.nan,
            }
            global_intensity = np.array([], dtype=float)
            local_intensity = np.array([], dtype=float)
        else:
            local_refs = {
                "local_hs_ref_low": float(np.nanpercentile(hs_peaks, 5)),
                "local_hs_ref_high": float(np.nanpercentile(hs_peaks, 95)),
                "local_ssh_ref_low": float(np.nanpercentile(ssh_peaks, 5)),
                "local_ssh_ref_high": float(np.nanpercentile(ssh_peaks, 95)),
            }
            global_intensity = normalized_compound_intensity(
                hs_peaks,
                ssh_peaks,
                global_refs["hs_ref_low"],
                global_refs["hs_ref_high"],
                global_refs["ssh_ref_low"],
                global_refs["ssh_ref_high"],
            )
            local_intensity = normalized_compound_intensity(
                hs_peaks,
                ssh_peaks,
                local_refs["local_hs_ref_low"],
                local_refs["local_hs_ref_high"],
                local_refs["local_ssh_ref_low"],
                local_refs["local_ssh_ref_high"],
            )

        global_mean = safe_mean(global_intensity)
        local_mean = safe_mean(local_intensity)
        rows.append(
            {
                "grid_lat": float(point["grid_lat"]),
                "grid_lon": float(point["grid_lon"]),
                "municipality": point.get("municipality"),
                "compound_count_total": int(point.get("compound_count_total", len(events))),
                "production_mean_compound_intensity_norm": point.get(
                    "mean_compound_intensity_norm"
                ),
                "global_mean_compound_intensity_norm_recomputed": global_mean,
                "local_mean_compound_intensity_norm": local_mean,
                "delta_local_minus_global": safe_difference(local_mean, global_mean),
                "local_p95_compound_intensity_norm": safe_percentile(local_intensity, 95),
                "local_max_compound_intensity_norm": safe_max(local_intensity),
                **local_refs,
            }
        )

    df = pd.DataFrame(rows)
    return df.sort_values(["grid_lat", "grid_lon"]).reset_index(drop=True)


def normalized_compound_intensity(
    hs_peaks: np.ndarray,
    ssh_peaks: np.ndarray,
    hs_ref_low: float,
    hs_ref_high: float,
    ssh_ref_low: float,
    ssh_ref_high: float,
) -> np.ndarray:
    hs_range = max(float(hs_ref_high - hs_ref_low), 1e-9)
    ssh_range = max(float(ssh_ref_high - ssh_ref_low), 1e-9)
    hs_norm = np.clip((hs_peaks - hs_ref_low) / hs_range, 0.0, 1.0)
    ssh_norm = np.clip((ssh_peaks - ssh_ref_low) / ssh_range, 0.0, 1.0)
    return 0.5 * (hs_norm + ssh_norm)


def safe_mean(values: np.ndarray) -> float | None:
    if values.size == 0 or not np.isfinite(values).any():
        return None
    return round(float(np.nanmean(values)), 4)


def safe_percentile(values: np.ndarray, q: float) -> float | None:
    if values.size == 0 or not np.isfinite(values).any():
        return None
    return round(float(np.nanpercentile(values, q)), 4)


def safe_max(values: np.ndarray) -> float | None:
    if values.size == 0 or not np.isfinite(values).any():
        return None
    return round(float(np.nanmax(values)), 4)


def safe_difference(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left - right), 4)


def load_summary_refs(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("normalization_refs")


def plot_comparison_map(
    point_metrics: pd.DataFrame,
    *,
    out_path: Path,
    coastline: Path,
    dpi: int,
) -> None:
    lat_vals = np.array(sorted(point_metrics["grid_lat"].dropna().unique()), dtype=float)
    lon_vals = np.array(sorted(point_metrics["grid_lon"].dropna().unique()), dtype=float)
    geoms = coastline_geometries(coastline)
    extent = map_extent(lon_vals, lat_vals)

    global_field = field_from_points(
        point_metrics,
        lat_vals,
        lon_vals,
        "global_mean_compound_intensity_norm_recomputed",
    )
    local_field = field_from_points(
        point_metrics,
        lat_vals,
        lon_vals,
        "local_mean_compound_intensity_norm",
    )
    delta_field = field_from_points(
        point_metrics,
        lat_vals,
        lon_vals,
        "delta_local_minus_global",
    )

    delta_abs = np.abs(delta_field[np.isfinite(delta_field)])
    delta_limit = float(np.ceil(max(delta_abs.max(initial=0.05), 0.05) * 20.0) / 20.0)
    delta_norm = TwoSlopeNorm(vmin=-delta_limit, vcenter=0.0, vmax=delta_limit)

    fig = plt.figure(figsize=(12.4, 5.7))
    gs = fig.add_gridspec(
        nrows=2,
        ncols=3,
        height_ratios=[1.0, 0.045],
        wspace=0.035,
        hspace=0.075,
    )
    axes = [fig.add_subplot(gs[0, i], projection=CRS) for i in range(3)]
    cax_intensity = fig.add_subplot(gs[1, 0:2])
    cax_delta = fig.add_subplot(gs[1, 2])

    panels = [
        (
            global_field,
            "Current: domain-wide Q05/Q95",
            INTENSITY_CMAP,
            {"vmin": 0.0, "vmax": 1.0},
        ),
        (
            local_field,
            "Test: local Q05/Q95",
            INTENSITY_CMAP,
            {"vmin": 0.0, "vmax": 1.0},
        ),
        (
            delta_field,
            "Local - domain-wide",
            "RdBu_r",
            {"norm": delta_norm},
        ),
    ]

    intensity_mesh = None
    delta_mesh = None
    for idx, (ax, (field, title, cmap, kwargs)) in enumerate(zip(axes, panels)):
        mesh = ax.pcolormesh(
            lon_vals,
            lat_vals,
            field,
            shading="auto",
            cmap=cmap,
            transform=CRS,
            **kwargs,
        )
        if idx < 2:
            intensity_mesh = mesh
        else:
            delta_mesh = mesh

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

    cbar_intensity = fig.colorbar(intensity_mesh, cax=cax_intensity, orientation="horizontal")
    cbar_intensity.ax.tick_params(labelsize=8)
    cbar_intensity.set_label("Mean compound intensity (norm.)", fontsize=9)

    cbar_delta = fig.colorbar(delta_mesh, cax=cax_delta, orientation="horizontal")
    cbar_delta.ax.tick_params(labelsize=8)
    cbar_delta.set_label("Delta local - domain-wide", fontsize=9)

    fig.suptitle("Compound-event mean intensity normalization test", fontsize=12)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    log.info("Wrote %s", out_path)


def field_from_points(
    point_metrics: pd.DataFrame,
    lat_vals: np.ndarray,
    lon_vals: np.ndarray,
    value_col: str,
) -> np.ndarray:
    field = np.full((len(lat_vals), len(lon_vals)), np.nan, dtype=np.float32)
    lat_index = {round(float(value), 4): idx for idx, value in enumerate(lat_vals)}
    lon_index = {round(float(value), 4): idx for idx, value in enumerate(lon_vals)}
    for row in point_metrics.itertuples(index=False):
        value = getattr(row, value_col)
        if pd.isna(value):
            continue
        i_lat = lat_index[round(float(row.grid_lat), 4)]
        i_lon = lon_index[round(float(row.grid_lon), 4)]
        field[i_lat, i_lon] = float(value)
    return field


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


if __name__ == "__main__":
    main()
