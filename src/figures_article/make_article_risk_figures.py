"""Generate publication figures for the municipal coastal risk analysis.

Outputs are written to ``outputs/article_figures/``:

- fig01_hazard_vulnerability_risk_multiplot.{png,pdf,svg}
- fig02_final_integrated_risk.{png,pdf,svg}
- fig03_original_ocean_hazard_points.{png,pdf,svg}

Run from the repository root:

    python -m src.figures_article.make_article_risk_figures
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd
import pyogrio

try:
    from config.plot_config import STYLE, apply_publication_style

    apply_publication_style()
except Exception:
    STYLE = None


ROOT = Path(__file__).resolve().parents[2]
RISK_DIR = ROOT / "outputs" / "risk_index"
RISK_SHP = RISK_DIR / "risk_index.shp"
OCEAN_HAZARD_CANDIDATES = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv",
    ROOT / "site" / "public" / "data" / "hazard_characterization_grid_metrics.json",
    ROOT / "site" / "public" / "data" / "storm_maps_grid_metrics.json",
)
COASTLINE_SHP = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"
OUT_DIR = ROOT / "outputs" / "article_figures"

OUTPUT_CRS = "EPSG:4326"
SIMPLIFY_TOLERANCE_DEGREES = 0.001
MAP_EXTENT = (-56.0, -27.0, -36.5, 7.0)
SAVE_EXTENSIONS = ("png", "pdf", "svg")

NO_DATA_COLOR = "#e5e7eb"
BOUNDARY_COLOR = "#ffffff"
COAST_COLOR = "#334155"
GRID_COLOR = "#cbd5e1"
RISK_CMAP = "YlOrRd"


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    candidates: tuple[str, ...]


RISK_LAYER_SPECS = (
    FieldSpec("SVI_Coast_2022", "Social Vulnerability Index", ("SVI_Coast_2022", "SVI_Coast_", "SVI_Coast", "SVI_Coa", "SVI")),
    FieldSpec("Hazard_Index", "Hazard Index", ("Hazard_Index", "Haz_index", "Hazard_In", "Hazard", "azard_Inde")),
    FieldSpec("Risk_Comp", "Risk_Comp", ("Risk_Comp", "Risk_comp", "Risk_Com", "risk_index")),
    FieldSpec("Risk_Hazard", "Risk_Hazard", ("Risk_Hazard", "Risk_harza", "Risk_Haza", "Risk_Haz", "risk_inde1")),
)

RISK_SUPPORT_SPECS = (
    FieldSpec("municipality_name", "Municipality", ("NM_MUN", "municipio", "municipali")),
    FieldSpec("state", "UF", ("SIGLA_UF", "uf")),
    FieldSpec("municipality_code", "Municipality code", ("CD_MUN",)),
    FieldSpec("compound_c", "compound_c", ("compound_c", "compound", "comp_c")),
    FieldSpec("mean_overl", "mean_overl", ("mean_overl", "mean_ove", "mean_overlap_duration")),
    FieldSpec("mean_compo", "mean_compo", ("mean_compo", "mean_com", "mean_compound_intensity_norm")),
)

OCEAN_FIELD_SPECS = (
    FieldSpec("latitude", "Latitude", ("grid_lat", "lat", "latitude", "y")),
    FieldSpec("longitude", "Longitude", ("grid_lon", "lon", "longitude", "x")),
    FieldSpec("compound_c", "Compound-event count", ("compound_c", "compound_count_total", "compound_count", "comp_c")),
    FieldSpec("mean_overl", "Mean overlap duration", ("mean_overl", "mean_overlap_duration", "compound_mean_overlap_duration")),
    FieldSpec("mean_compo", "Mean compound-event intensity", ("mean_compo", "mean_compound_intensity_norm", "compound_mean_intensity_norm")),
    FieldSpec("Hazard_Index", "Hazard Index", ("Hazard_Index", "Haz_index", "hazard_index")),
)


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _norm_name(name: str) -> str:
    return name.lower().replace("_", "").replace("-", "")


def _resolve_field(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    if not columns:
        return None
    exact = {col: col for col in columns}
    for candidate in candidates:
        if candidate in exact:
            return candidate
    lower = {col.lower(): col for col in columns}
    for candidate in candidates:
        match = lower.get(candidate.lower())
        if match:
            return match
    normalized = {_norm_name(col): col for col in columns}
    for candidate in candidates:
        match = normalized.get(_norm_name(candidate))
        if match:
            return match
    return None


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return round(value, 6) if math.isfinite(value) else None
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _numeric_stats(series: pd.Series) -> dict[str, float | int | None]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"count": 0, "min": None, "mean": None, "median": None, "max": None}
    return {
        "count": int(values.count()),
        "min": round(float(values.min()), 6),
        "mean": round(float(values.mean()), 6),
        "median": round(float(values.median()), 6),
        "max": round(float(values.max()), 6),
    }


def _minmax(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    vmin = values.min(skipna=True)
    vmax = values.max(skipna=True)
    if pd.isna(vmin) or pd.isna(vmax) or math.isclose(float(vmin), float(vmax)):
        return pd.Series(np.nan, index=values.index)
    return (values - vmin) / (vmax - vmin)


def _source_components() -> dict[str, bool]:
    return {
        suffix: (RISK_DIR / f"risk_index{suffix}").exists()
        for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qmd")
    }


def _where_clause(fields: list[str]) -> str:
    return " OR ".join(f"{field} IS NOT NULL" for field in fields)


def read_risk_data() -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    required_components = (".shp", ".shx", ".dbf", ".prj")
    missing_components = [suffix for suffix in required_components if not (RISK_DIR / f"risk_index{suffix}").exists()]
    if missing_components:
        raise FileNotFoundError(
            f"Missing required risk-index shapefile components in {RISK_DIR}: {', '.join(missing_components)}"
        )

    info = pyogrio.read_info(RISK_SHP)
    source_fields = list(info["fields"])
    layer_aliases = {
        spec.key: field
        for spec in RISK_LAYER_SPECS
        if (field := _resolve_field(source_fields, spec.candidates)) is not None
    }
    support_aliases = {
        spec.key: field
        for spec in RISK_SUPPORT_SPECS
        if (field := _resolve_field(source_fields, spec.candidates)) is not None
    }

    if "Risk_Hazard" not in layer_aliases and "Risk_Comp" not in layer_aliases:
        raise RuntimeError("Neither Risk_Hazard nor Risk_Comp was found in the municipal risk shapefile.")
    for required in ("Hazard_Index", "SVI_Coast_2022"):
        if required not in layer_aliases:
            raise RuntimeError(f"Required layer {required} was not found in the municipal risk shapefile.")

    read_fields = sorted(set(layer_aliases.values()) | set(support_aliases.values()))
    value_fields = list(layer_aliases.values())
    gdf = pyogrio.read_dataframe(RISK_SHP, columns=read_fields, where=_where_clause(value_fields))
    if gdf.empty:
        raise RuntimeError("No municipal features with populated risk-index fields were found.")

    source_crs = str(gdf.crs) if gdf.crs else None
    if gdf.crs is None:
        raise RuntimeError("Risk-index shapefile has no CRS.")
    if str(gdf.crs).upper() != OUTPUT_CRS:
        gdf = gdf.to_crs(OUTPUT_CRS)

    coords_before = int(gdf.geometry.count())
    gdf = gdf.copy()
    gdf.geometry = gdf.geometry.simplify(SIMPLIFY_TOLERANCE_DEGREES, preserve_topology=True)
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    coords_after = int(gdf.geometry.count())

    # Canonical property names used by plotting functions.
    for key, source in {**support_aliases, **layer_aliases}.items():
        gdf[key] = gdf[source]

    risk_key = "Risk_Hazard" if "Risk_Hazard" in layer_aliases else "Risk_Comp"
    stats = {key: _numeric_stats(gdf[key]) for key in layer_aliases}
    metadata = {
        "source_path": _relative(RISK_SHP),
        "source_components": _source_components(),
        "source_crs": source_crs,
        "output_crs": OUTPUT_CRS,
        "source_feature_count": int(info["features"]),
        "filtered_feature_count": int(len(gdf)),
        "schema_geometry": info.get("geometry_type"),
        "geometry_type_counts": gdf.geometry.geom_type.value_counts().to_dict(),
        "source_fields": source_fields,
        "field_aliases": {
            "layers": layer_aliases,
            "support": support_aliases,
        },
        "risk_panel_key": risk_key,
        "stats": stats,
        "simplification": {
            "tolerance_degrees": SIMPLIFY_TOLERANCE_DEGREES,
            "preserve_topology": True,
            "features_before": coords_before,
            "features_after": coords_after,
        },
    }
    return gdf, metadata


def read_coastline() -> gpd.GeoDataFrame | None:
    if not COASTLINE_SHP.exists():
        return None
    coast = gpd.read_file(COASTLINE_SHP)
    if coast.crs is None:
        coast = coast.set_crs(OUTPUT_CRS)
    elif str(coast.crs).upper() != OUTPUT_CRS:
        coast = coast.to_crs(OUTPUT_CRS)
    xmin, xmax = MAP_EXTENT[0], MAP_EXTENT[1]
    ymin, ymax = MAP_EXTENT[2], MAP_EXTENT[3]
    return coast.cx[xmin:xmax, ymin:ymax]


def _read_json_grid_points(path: Path) -> pd.DataFrame:
    obj = json.loads(path.read_text())
    if isinstance(obj, dict) and isinstance(obj.get("grid_points"), list):
        return pd.DataFrame(obj["grid_points"])
    if isinstance(obj, list):
        records = []
        for entry in obj:
            records.append({k: v for k, v in entry.items() if not isinstance(v, list)})
        return pd.DataFrame(records)
    raise RuntimeError(f"Unsupported JSON structure for ocean hazard file: {path}")


def read_ocean_hazard_data() -> tuple[pd.DataFrame, dict[str, Any]]:
    source_path = next((path for path in OCEAN_HAZARD_CANDIDATES if path.exists()), None)
    if source_path is None:
        raise FileNotFoundError(
            "No original oceanic hazard data file found. Checked: "
            + ", ".join(_relative(path) for path in OCEAN_HAZARD_CANDIDATES)
        )

    if source_path.suffix.lower() == ".csv":
        raw = pd.read_csv(source_path)
    elif source_path.suffix.lower() == ".json":
        raw = _read_json_grid_points(source_path)
    else:
        raise RuntimeError(f"Unsupported ocean hazard input format: {source_path.suffix}")

    columns = list(raw.columns)
    aliases = {
        spec.key: field
        for spec in OCEAN_FIELD_SPECS
        if (field := _resolve_field(columns, spec.candidates)) is not None
    }
    for required in ("latitude", "longitude"):
        if required not in aliases:
            raise RuntimeError(f"Ocean hazard file lacks a {required} coordinate field: {_relative(source_path)}")

    df = pd.DataFrame(
        {
            "latitude": pd.to_numeric(raw[aliases["latitude"]], errors="coerce"),
            "longitude": pd.to_numeric(raw[aliases["longitude"]], errors="coerce"),
        }
    )
    hazard_mode = "read"
    hazard_components: list[str] = []
    if "Hazard_Index" in aliases:
        df["Hazard_Index"] = pd.to_numeric(raw[aliases["Hazard_Index"]], errors="coerce")
    else:
        required_components = ("compound_c", "mean_overl", "mean_compo")
        missing = [key for key in required_components if key not in aliases]
        if missing:
            if "compound_c" not in aliases:
                raise RuntimeError(
                    "Ocean hazard file has neither Hazard_Index nor the required components "
                    f"for computation. Missing: {', '.join(missing)}"
                )
            df["compound_c"] = pd.to_numeric(raw[aliases["compound_c"]], errors="coerce")
            df["Hazard_Index"] = df["compound_c"]
            hazard_mode = "compound_count_only"
            hazard_components = ["compound_c"]
        else:
            for key in required_components:
                df[key] = pd.to_numeric(raw[aliases[key]], errors="coerce")
            normed = [_minmax(df[key]) for key in required_components]
            df["Hazard_Index"] = pd.concat(normed, axis=1).mean(axis=1)
            hazard_mode = "computed_minmax_mean"
            hazard_components = list(required_components)

    df = df.dropna(subset=["latitude", "longitude", "Hazard_Index"]).copy()
    metadata = {
        "source_path": _relative(source_path),
        "source_shape": list(raw.shape),
        "field_aliases": aliases,
        "hazard_index_mode": hazard_mode,
        "hazard_components": hazard_components,
        "feature_count": int(len(df)),
        "stats": {
            "Hazard_Index": _numeric_stats(df["Hazard_Index"]),
            **{key: _numeric_stats(df[key]) for key in hazard_components if key in df},
        },
        "bounds": [
            round(float(df["longitude"].min()), 6),
            round(float(df["latitude"].min()), 6),
            round(float(df["longitude"].max()), 6),
            round(float(df["latitude"].max()), 6),
        ],
    }
    return df, metadata


def _setup_map_axis(ax: plt.Axes, title: str) -> None:
    xmin, xmax, ymin, ymax = MAP_EXTENT
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title, loc="left", fontweight="bold", fontsize=9.5, pad=6)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks(np.arange(-55, -25, 5))
    ax.set_yticks(np.arange(-35, 10, 5))
    ax.tick_params(axis="both", labelsize=7, length=2.8, color="#64748b")
    ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.45, alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color("#94a3b8")
        spine.set_linewidth(0.8)


def _plot_coastline(ax: plt.Axes, coastline: gpd.GeoDataFrame | None) -> None:
    if coastline is not None and not coastline.empty:
        coastline.plot(ax=ax, color=COAST_COLOR, linewidth=0.45, zorder=4)


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        0.02,
        0.98,
        label,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10.5,
        fontweight="bold",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.95},
        zorder=10,
    )


def _layer_norm(series: pd.Series, key: str) -> Normalize:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return Normalize(0, 1)
    if key == "SVI_Coast_2022" and values.min() >= 0 and values.max() <= 100:
        return Normalize(0, 100)
    return Normalize(float(values.min()), float(values.max()))


def _colorbar_label(key: str, compact: bool = False) -> str:
    if compact:
        compact_labels = {
            "SVI_Coast_2022": "SVI (0-100)",
            "Hazard_Index": "Hazard Index",
            "Risk_Hazard": "Integrated Risk",
            "Risk_Comp": "Risk_Comp",
        }
        if key in compact_labels:
            return compact_labels[key]
    if key == "SVI_Coast_2022":
        return "Social Vulnerability Index (0-100)"
    if key == "Hazard_Index":
        return "Hazard Index (relative)"
    if key == "Risk_Hazard":
        return "Integrated Risk Index (relative)"
    if key == "Risk_Comp":
        return "Frequency-weighted Risk Index (relative)"
    return key


def _plot_municipal_layer(
    ax: plt.Axes,
    gdf: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame | None,
    key: str,
    title: str,
    panel: str | None = None,
    cbar_orientation: str = "horizontal",
    cbar_fraction: float = 0.055,
    cbar_pad: float = 0.06,
    compact_cbar_label: bool = False,
) -> ScalarMappable:
    norm = _layer_norm(gdf[key], key)
    gdf.plot(ax=ax, facecolor=NO_DATA_COLOR, edgecolor=BOUNDARY_COLOR, linewidth=0.12, zorder=1)
    valid = gdf[gdf[key].notna()].copy()
    valid.plot(
        ax=ax,
        column=key,
        cmap=RISK_CMAP,
        norm=norm,
        edgecolor=BOUNDARY_COLOR,
        linewidth=0.12,
        zorder=2,
    )
    _plot_coastline(ax, coastline)
    _setup_map_axis(ax, title)
    if panel:
        _panel_label(ax, panel)
    mappable = ScalarMappable(norm=norm, cmap=plt.get_cmap(RISK_CMAP))
    mappable.set_array([])
    cbar = ax.figure.colorbar(
        mappable,
        ax=ax,
        orientation=cbar_orientation,
        fraction=cbar_fraction,
        pad=cbar_pad,
    )
    cbar.set_label(_colorbar_label(key, compact=compact_cbar_label), fontsize=8)
    cbar.ax.tick_params(labelsize=7, length=2.5)
    cbar.outline.set_linewidth(0.7)
    return mappable


def _save_figure(fig: plt.Figure, stem: str) -> list[str]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for ext in SAVE_EXTENSIONS:
        path = OUT_DIR / f"{stem}.{ext}"
        if ext == "png":
            fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        else:
            fig.savefig(path, bbox_inches="tight", facecolor="white")
        outputs.append(_relative(path))
    plt.close(fig)
    return outputs


def make_figure_1(gdf: gpd.GeoDataFrame, coastline: gpd.GeoDataFrame | None, risk_key: str) -> list[str]:
    layers = [
        ("Hazard_Index", "A", "Physical compound-event hazard"),
        ("SVI_Coast_2022", "B", "Social vulnerability"),
        (risk_key, "C", "Integrated risk" if risk_key == "Risk_Hazard" else "Risk_Comp fallback"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 6.2), constrained_layout=False)
    fig.subplots_adjust(left=0.045, right=0.985, top=0.865, bottom=0.105, wspace=0.18)
    for ax, (key, panel, title) in zip(axes, layers):
        _plot_municipal_layer(
            ax,
            gdf,
            coastline,
            key,
            title,
            panel=panel,
            cbar_orientation="vertical",
            cbar_fraction=0.034,
            cbar_pad=0.012,
            compact_cbar_label=True,
        )
    fig.suptitle(
        "Municipal-scale components of coastal compound-event risk along the Brazilian coast",
        fontsize=12.5,
        fontweight="bold",
        y=0.955,
    )
    fig.text(
        0.5,
        0.03,
        "Indices are comparative across coastal municipalities; lower values indicate lower relative social-vulnerability-weighted risk, not absence of coastal hazard.",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color="#475569",
    )
    return _save_figure(fig, "fig01_hazard_vulnerability_risk_multiplot")


def _format_municipality(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "Unknown"
    text = str(value)
    return text.title() if text.isupper() else text


def make_figure_2(gdf: gpd.GeoDataFrame, coastline: gpd.GeoDataFrame | None, risk_key: str) -> list[str]:
    if risk_key != "Risk_Hazard":
        title = "Relative coastal risk based on Risk_Comp fallback"
    else:
        title = "Relative integrated coastal risk associated with compound wave-surge events"

    fig = plt.figure(figsize=(11.4, 7.6), constrained_layout=False)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=(3.3, 1.7),
        left=0.055,
        right=0.985,
        top=0.93,
        bottom=0.06,
        wspace=0.26,
    )
    ax_map = fig.add_subplot(gs[0, 0])
    ax_rank = fig.add_subplot(gs[0, 1])

    _plot_municipal_layer(
        ax_map,
        gdf,
        coastline,
        risk_key,
        title,
        panel=None,
        cbar_orientation="vertical",
        cbar_fraction=0.038,
        cbar_pad=0.025,
    )

    ranked = (
        gdf[gdf[risk_key].notna()]
        .sort_values(risk_key, ascending=False)
        .head(10)
        .copy()
    )
    top_points = ranked.geometry.representative_point()
    for rank, (_, row) in enumerate(ranked.iterrows(), start=1):
        point = top_points.loc[row.name]
        ax_map.scatter(point.x, point.y, s=68, facecolor="white", edgecolor="#0f172a", linewidth=0.9, zorder=8)
        ax_map.text(point.x, point.y, str(rank), ha="center", va="center", fontsize=7, fontweight="bold", zorder=9)

    ax_rank.axis("off")
    table_rows = []
    for rank, (_, row) in enumerate(ranked.iterrows(), start=1):
        muni = _format_municipality(row.get("municipality_name"))
        uf = row.get("state") if pd.notna(row.get("state")) else ""
        table_rows.append([rank, f"{muni} ({uf})", f"{row[risk_key]:.3f}"])

    table = ax_rank.table(
        cellText=table_rows,
        colLabels=["Rank", "Municipality", "Index"],
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        colWidths=[0.13, 0.67, 0.20],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(6.8)
    table.scale(1.0, 1.28)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        cell.set_linewidth(0.4)
        if row == 0:
            cell.set_facecolor("#f1f5f9")
            cell.set_text_props(weight="bold", color="#0f172a")
        else:
            cell.set_facecolor("white")

    ax_rank.text(
        0.0,
        0.52,
        "Interpretation caveat",
        transform=ax_rank.transAxes,
        fontsize=8.5,
        fontweight="bold",
        color="#0f172a",
    )
    ax_rank.text(
        0.0,
        0.48,
        "The index is relative/comparative.\nA municipality can have relevant\nphysical coastal hazards while ranking\nlower after social vulnerability weighting.",
        transform=ax_rank.transAxes,
        fontsize=7.5,
        color="#475569",
        va="top",
        linespacing=1.35,
    )
    ax_rank.text(
        0.0,
        0.25,
        "Formula",
        transform=ax_rank.transAxes,
        fontsize=8.5,
        fontweight="bold",
        color="#0f172a",
    )
    ax_rank.text(
        0.0,
        0.21,
        "Risk_Hazard =\n(SVI_Coast_2022 / 100) x Hazard_Index",
        transform=ax_rank.transAxes,
        fontsize=7.5,
        color="#475569",
        va="top",
        linespacing=1.35,
    )
    return _save_figure(fig, "fig02_final_integrated_risk")


def make_figure_3(
    ocean_df: pd.DataFrame,
    coastline: gpd.GeoDataFrame | None,
    ocean_meta: dict[str, Any],
) -> list[str]:
    fig, ax = plt.subplots(figsize=(7.6, 8.2), constrained_layout=False)
    fig.subplots_adjust(left=0.075, right=0.88, top=0.93, bottom=0.105)
    values = ocean_df["Hazard_Index"]
    norm = Normalize(float(values.min()), float(values.max()))
    _setup_map_axis(ax, "Original oceanic compound-event hazard points")
    _plot_coastline(ax, coastline)
    scatter = ax.scatter(
        ocean_df["longitude"],
        ocean_df["latitude"],
        c=values,
        cmap=RISK_CMAP,
        norm=norm,
        s=20,
        edgecolors="#0f172a",
        linewidths=0.18,
        alpha=0.95,
        zorder=5,
    )
    cbar = fig.colorbar(scatter, ax=ax, orientation="vertical", fraction=0.04, pad=0.025)
    if ocean_meta["hazard_index_mode"] == "compound_count_only":
        cbar.set_label("Compound-event count", fontsize=8)
    else:
        cbar.set_label("Oceanic Hazard_Index (relative)", fontsize=8)
    cbar.ax.tick_params(labelsize=7, length=2.5)
    cbar.outline.set_linewidth(0.7)
    mode_text = {
        "read": "Hazard_Index read directly from source.",
        "computed_minmax_mean": "Hazard_Index computed as mean of min-max normalized count, overlap duration, and intensity.",
        "compound_count_only": "Fallback: only compound-event count was available.",
    }[ocean_meta["hazard_index_mode"]]
    fig.text(
        0.075,
        0.035,
        f"n = {len(ocean_df)} ocean grid points. {mode_text}",
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="#334155",
    )
    return _save_figure(fig, "fig03_original_ocean_hazard_points")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdf, risk_meta = read_risk_data()
    coastline = read_coastline()
    ocean_df, ocean_meta = read_ocean_hazard_data()

    risk_key = risk_meta["risk_panel_key"]
    generated: dict[str, list[str]] = {}
    generated["figure_1"] = make_figure_1(gdf, coastline, risk_key)
    generated["figure_2"] = make_figure_2(gdf, coastline, risk_key)
    generated["figure_3"] = make_figure_3(ocean_df, coastline, ocean_meta)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "risk_shapefile": risk_meta,
        "ocean_hazard": ocean_meta,
        "outputs": generated,
        "interpretation_caveat": (
            "Risk indices are comparative across Brazilian coastal municipalities. "
            "They should not be read as absolute expected damage or absence/presence of coastal hazard."
        ),
    }
    summary_path = OUT_DIR / "article_risk_figure_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=_to_jsonable)
        f.write("\n")

    print("\nOSR11 article risk figures generated")
    print("------------------------------------")
    print(f"Risk shapefile: {_relative(RISK_SHP)}")
    print(f"Risk features used: {risk_meta['filtered_feature_count']} / {risk_meta['source_feature_count']}")
    print(f"Risk panel: {risk_key}")
    print("Risk field aliases:")
    for key, field in risk_meta["field_aliases"]["layers"].items():
        print(f"  {key} <- {field} | {risk_meta['stats'][key]}")
    print(f"Ocean hazard source: {ocean_meta['source_path']}")
    print(f"Ocean Hazard_Index mode: {ocean_meta['hazard_index_mode']}")
    print(f"Ocean field aliases: {ocean_meta['field_aliases']}")
    print("Generated files:")
    for files in generated.values():
        for file in files:
            print(f"  {file}")
    print(f"  {_relative(summary_path)}")


if __name__ == "__main__":
    main()
