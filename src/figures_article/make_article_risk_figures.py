"""Shared generators for the article coastal-risk figures and ranking tables.

The three dedicated entry points are:

- ``make_article_coastal_compound_event_rate_map.py``
- ``make_article_hazard_vulnerability_risk_multiplot.py``
- ``make_article_top10_municipality_tables.py``

This module keeps the data readers, plotting utilities, output validation, and
an all-in-one compatibility command. Run each dedicated script from the
repository root when regenerating a single artifact.

Run from the repository root:

    python -m src.figures_article.make_article_risk_figures
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import cartopy.crs as ccrs
from cartopy.io import shapereader
import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap, Normalize
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd
import pyogrio
from scipy.spatial import cKDTree
from shapely.geometry import GeometryCollection, LineString, MultiLineString
from shapely.ops import linemerge, unary_union

try:
    from config.plot_config import STYLE, apply_publication_style

    apply_publication_style()
except Exception:
    STYLE = None


ROOT = Path(__file__).resolve().parents[2]
RISK_DIR = ROOT / "outputs" / "risk_index"
RISK_SHP = RISK_DIR / "risk_index.shp"
CURRENT_RISK_GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
CURRENT_RISK_METADATA = ROOT / "site" / "public" / "data" / "risk_index_metadata.json"
OCEAN_HAZARD_CANDIDATES = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_metrics.csv",
    ROOT / "site" / "public" / "data" / "hazard_characterization_grid_metrics.json",
    ROOT / "site" / "public" / "data" / "storm_maps_grid_metrics.json",
)
COASTLINE_SHP = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"
COMPOUND_SUMMARY_PATH = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_summary.json"
)
OUT_DIR = ROOT / "outputs" / "article_figures"
METADATA_DIR = OUT_DIR / "metadata"
TABLE_DIR = OUT_DIR / "tables"

OUTPUT_CRS = "EPSG:4326"
SIMPLIFY_TOLERANCE_DEGREES = 0.001
MAP_EXTENT = (-56.0, -27.0, -36.5, 7.0)
BRAZIL_MAP_EXTENT = (-74.5, -32.0, -35.5, 6.5)
COASTAL_MAP_EXTENT = (
    MAP_EXTENT[0],
    BRAZIL_MAP_EXTENT[1],
    BRAZIL_MAP_EXTENT[2],
    BRAZIL_MAP_EXTENT[3],
)
ARTICLE_FIGURE_FORMAT = "png"
ARTICLE_FIGURE_DPI = 300
ORDINAL_FILENAME_PATTERN = re.compile(
    r"^(?:(?:fig(?:ure)?|main_figure|primary)_?\d+|[a-z]?\d+)_",
    re.IGNORECASE,
)

NO_DATA_COLOR = "#e5e7eb"
BOUNDARY_COLOR = "#ffffff"
COAST_COLOR = "#334155"
GRID_COLOR = "#cbd5e1"
RISK_CMAP = "YlOrRd"

LAND_COLOR = "#ddddda"
OCEAN_COLOR = "#e9f3f7"
STATE_BORDER_COLOR = "#9a9a96"
COUNTRY_BORDER_COLOR = "#555553"
ARTICLE_COAST_COLOR = "#252525"
COASTAL_PROJECTION_CRS = "EPSG:5880"
COASTLINE_MUNICIPAL_BUFFER_M = 30_000.0
COASTLINE_SEGMENT_MAX_LENGTH_M = 5_000.0
COASTAL_COLOR_CLASSES = 9

# Same green-yellow-orange-red sequence used by the Composite Score heatmap,
# inverted relative to that panel's displayed direction and intentionally
# stopped at red so that the upper municipal classes do not return to purple.
MUNICIPAL_INDEX_COLORS_LOW_TO_HIGH = (
    "#008000",
    "#33B200",
    "#80D900",
    "#CCE600",
    "#FFE600",
    "#FFB200",
    "#FF8000",
    "#FF4000",
    "#FF0000",
)


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
    FieldSpec("state_name", "State", ("NM_UF", "state_name", "estado")),
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
    if CURRENT_RISK_GEOJSON.exists():
        gdf = gpd.read_file(CURRENT_RISK_GEOJSON)
        source_crs = str(gdf.crs) if gdf.crs else OUTPUT_CRS
        if gdf.crs is None:
            gdf = gdf.set_crs(OUTPUT_CRS)
        elif str(gdf.crs).upper() != OUTPUT_CRS:
            gdf = gdf.to_crs(OUTPUT_CRS)

        required_layers = ("SVI_Coast_2022", "Hazard_Index", "Risk_Hazard")
        missing_layers = [key for key in required_layers if key not in gdf.columns]
        if missing_layers:
            raise RuntimeError(
                f"Current risk GeoJSON is missing required fields: {', '.join(missing_layers)}"
            )

        web_metadata = {}
        if CURRENT_RISK_METADATA.exists():
            web_metadata = json.loads(CURRENT_RISK_METADATA.read_text())

        layer_keys = [key for key in ("SVI_Coast_2022", "Hazard_Index", "Risk_Comp", "Risk_Hazard") if key in gdf.columns]
        layer_aliases = {
            key: web_metadata.get("field_aliases", {}).get("layers", {}).get(key, key)
            for key in layer_keys
        }
        support_aliases = {
            key: key
            for key in (
                "municipality_name",
                "state",
                "state_name",
                "municipality_code",
                "compound_c",
                "mean_overl",
                "mean_compo",
            )
            if key in gdf.columns
        }
        stats = {key: _numeric_stats(gdf[key]) for key in layer_keys}
        metadata = {
            "source_path": _relative(CURRENT_RISK_GEOJSON),
            "metadata_path": _relative(CURRENT_RISK_METADATA) if CURRENT_RISK_METADATA.exists() else None,
            "source_crs": source_crs,
            "output_crs": OUTPUT_CRS,
            "source_feature_count": int(len(gdf)),
            "filtered_feature_count": int(len(gdf)),
            "schema_geometry": "GeoJSON",
            "scope": web_metadata.get("scope", "compound_count_only"),
            "geometry_type_counts": gdf.geometry.geom_type.value_counts().to_dict(),
            "field_aliases": {
                "layers": layer_aliases,
                "support": support_aliases,
            },
            "risk_panel_key": "Risk_Hazard",
            "stats": stats,
            "simplification": web_metadata.get("simplification"),
        }
        return gdf, metadata

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
    if "compound_c" in aliases:
        df["compound_c"] = pd.to_numeric(raw[aliases["compound_c"]], errors="coerce")
        df["Hazard_Index"] = df["compound_c"]
        hazard_mode = "compound_count_only_current_scope"
        hazard_components = ["compound_c"]
    elif "Hazard_Index" in aliases:
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
            "Hazard_Index": "Hazard index",
            "Risk_Hazard": "Integrated risk index",
            "Risk_Comp": "Risk_Comp",
        }
        if key in compact_labels:
            return compact_labels[key]
    if key == "SVI_Coast_2022":
        return "Social Vulnerability Index (0-100)"
    if key == "Hazard_Index":
        return "Compound-count Hazard Index (relative)"
    if key == "Risk_Hazard":
        return "Compound-count Risk Index (relative)"
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
    """Save one article figure using the repository-wide PNG-only policy."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ORDINAL_FILENAME_PATTERN.match(stem):
        raise ValueError(f"Article figure stem must be semantic, not ordinal: {stem!r}")
    path = OUT_DIR / f"{stem}.{ARTICLE_FIGURE_FORMAT}"
    fig.savefig(path, dpi=ARTICLE_FIGURE_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [_relative(path)]


def _iter_json_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_json_strings(item)


def _clean_obsolete_article_images() -> None:
    """Remove formats and ordinal filenames forbidden by the current policy."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUT_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pdf", ".svg"}:
            path.unlink()
        elif path.suffix.lower() == ".png" and ORDINAL_FILENAME_PATTERN.match(path.stem):
            path.unlink()


def validate_article_figure_outputs() -> None:
    """Fail clearly when images or manifest paths violate article-figure rules."""
    errors: list[str] = []
    image_extensions = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}
    for path in OUT_DIR.rglob("*"):
        if not path.is_file() or path.name == "README.md":
            continue
        suffix = path.suffix.lower()
        if suffix in image_extensions and suffix != ".png":
            errors.append(f"non-PNG article figure: {_relative(path)}")
        if suffix == ".png" and ORDINAL_FILENAME_PATTERN.match(path.stem):
            errors.append(f"ordinal article-figure filename: {_relative(path)}")

    for manifest in METADATA_DIR.glob("*.json"):
        if "legacy" in manifest.stem.lower():
            continue
        with manifest.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        for value in _iter_json_strings(payload):
            suffix = Path(value).suffix.lower()
            if suffix not in image_extensions:
                continue
            if suffix != ".png":
                errors.append(f"non-PNG path in {_relative(manifest)}: {value}")
                continue
            figure_path = Path(value)
            if not figure_path.is_absolute():
                figure_path = ROOT / figure_path
            if ORDINAL_FILENAME_PATTERN.match(figure_path.stem):
                errors.append(f"ordinal path in {_relative(manifest)}: {value}")
            if not figure_path.is_file():
                errors.append(f"missing figure recorded in {_relative(manifest)}: {value}")

    if errors:
        raise RuntimeError("Article-figure validation failed:\n- " + "\n- ".join(errors))


def _geometry_intersects_extent(
    geometry: object,
    extent: tuple[float, float, float, float],
) -> bool:
    minx, miny, maxx, maxy = geometry.bounds
    west, east, south, north = extent
    return not (maxx < west or minx > east or maxy < south or miny > north)


@lru_cache(maxsize=1)
def _natural_earth_context() -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    land_path = shapereader.natural_earth(
        resolution="10m",
        category="physical",
        name="land",
    )
    country_path = shapereader.natural_earth(
        resolution="10m",
        category="cultural",
        name="admin_0_boundary_lines_land",
    )
    state_path = shapereader.natural_earth(
        resolution="10m",
        category="cultural",
        name="admin_1_states_provinces_lines",
    )
    land = tuple(
        geometry
        for geometry in shapereader.Reader(land_path).geometries()
        if _geometry_intersects_extent(geometry, BRAZIL_MAP_EXTENT)
    )
    countries = tuple(
        geometry
        for geometry in shapereader.Reader(country_path).geometries()
        if _geometry_intersects_extent(geometry, BRAZIL_MAP_EXTENT)
    )
    brazil_states = tuple(
        record.geometry
        for record in shapereader.Reader(state_path).records()
        if record.attributes.get("ADM0_NAME") == "Brazil"
        and _geometry_intersects_extent(record.geometry, BRAZIL_MAP_EXTENT)
    )
    return land, countries, brazil_states


def _setup_article_geo_axis(
    axis: plt.Axes,
    title: str | None,
    *,
    extent: tuple[float, float, float, float] = BRAZIL_MAP_EXTENT,
    draw_left_labels: bool = True,
    draw_bottom_labels: bool = True,
) -> None:
    crs = ccrs.PlateCarree()
    land, _, _ = _natural_earth_context()
    axis.set_facecolor(OCEAN_COLOR)
    axis.add_geometries(
        land,
        crs=crs,
        facecolor=LAND_COLOR,
        edgecolor="none",
        zorder=0.5,
    )
    axis.set_extent(extent, crs=crs)
    grid = axis.gridlines(
        crs=crs,
        draw_labels=True,
        linewidth=0.35,
        color="#9aa9b0",
        alpha=0.55,
        linestyle="--",
        zorder=1.2,
    )
    grid.top_labels = False
    grid.right_labels = False
    grid.left_labels = draw_left_labels
    grid.bottom_labels = draw_bottom_labels
    grid.xlabel_style = {"size": 8, "color": "#374151"}
    grid.ylabel_style = {"size": 8, "color": "#374151"}
    if title:
        axis.set_title(title, loc="left", fontsize=10.5, fontweight="bold", pad=7)


def _draw_administrative_boundaries(axis: plt.Axes) -> None:
    crs = ccrs.PlateCarree()
    _, countries, brazil_states = _natural_earth_context()
    axis.add_geometries(
        brazil_states,
        crs=crs,
        facecolor="none",
        edgecolor=STATE_BORDER_COLOR,
        linewidth=0.42,
        alpha=0.95,
        zorder=5,
    )
    axis.add_geometries(
        countries,
        crs=crs,
        facecolor="none",
        edgecolor=COUNTRY_BORDER_COLOR,
        linewidth=0.72,
        alpha=0.98,
        zorder=5.2,
    )


def _municipal_palette(number_of_classes: int) -> ListedColormap:
    indices = np.rint(
        np.linspace(0, len(MUNICIPAL_INDEX_COLORS_LOW_TO_HIGH) - 1, number_of_classes)
    ).astype(int)
    colors = tuple(MUNICIPAL_INDEX_COLORS_LOW_TO_HIGH[index] for index in indices)
    return ListedColormap(colors, name="composite_score_inverted_green_to_red")


def _municipal_boundaries(series: pd.Series, key: str) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"No finite values available for {key}")
    if key == "Hazard_Index":
        return np.linspace(0.0, 1.0, 9)
    if key == "SVI_Coast_2022":
        return np.linspace(0.0, 100.0, 9)
    upper = float(values.max())
    boundaries = MaxNLocator(
        nbins=7,
        steps=[1, 2, 2.5, 5, 10],
    ).tick_values(0.0, upper)
    boundaries = boundaries[boundaries >= 0.0]
    if boundaries[-1] < upper:
        boundaries = np.append(boundaries, upper)
    return boundaries


def _plot_municipal_layer_discrete(
    axis: plt.Axes,
    gdf: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame | None,
    key: str,
    title: str,
    panel: str,
    *,
    draw_left_labels: bool,
) -> dict[str, Any]:
    boundaries = _municipal_boundaries(gdf[key], key)
    cmap = _municipal_palette(len(boundaries) - 1)
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)
    _setup_article_geo_axis(
        axis,
        title,
        extent=MAP_EXTENT,
        draw_left_labels=draw_left_labels,
    )
    gdf.plot(
        ax=axis,
        facecolor="#c7c7c4",
        edgecolor="#f8fafc",
        linewidth=0.16,
        zorder=2,
    )
    valid = gdf[gdf[key].notna()].copy()
    valid.plot(
        ax=axis,
        column=key,
        cmap=cmap,
        norm=norm,
        edgecolor="#f8fafc",
        linewidth=0.16,
        zorder=3,
    )
    _draw_administrative_boundaries(axis)
    _plot_coastline(axis, coastline)
    axis.set_extent(MAP_EXTENT, crs=ccrs.PlateCarree())
    _panel_label(axis, panel)

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    colorbar = axis.figure.colorbar(
        mappable,
        ax=axis,
        orientation="vertical",
        boundaries=boundaries,
        ticks=boundaries,
        spacing="uniform",
        fraction=0.040,
        pad=0.025,
        drawedges=True,
    )
    colorbar.ax.tick_params(labelsize=8, length=2.8)
    colorbar.outline.set_linewidth(0.7)
    return {
        "key": key,
        "boundaries": boundaries.tolist(),
        "colors": list(cmap.colors),
        "statistics": _numeric_stats(gdf[key]),
    }


def make_hazard_vulnerability_risk_multiplot(
    gdf: gpd.GeoDataFrame,
    coastline: gpd.GeoDataFrame | None,
    risk_key: str,
    *,
    write_metadata: bool = True,
) -> list[str]:
    layers = [
        ("Hazard_Index", "A", "Compound-event count hazard"),
        ("SVI_Coast_2022", "B", "Social vulnerability"),
        (
            risk_key,
            "C",
            "Integrated risk" if risk_key == "Risk_Hazard" else "Risk_Comp fallback",
        ),
    ]
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(14.4, 6.2),
        constrained_layout=False,
        subplot_kw={"projection": ccrs.PlateCarree()},
    )
    fig.subplots_adjust(
        left=0.045,
        right=0.985,
        top=0.955,
        bottom=0.055,
        wspace=0.14,
    )
    panels: list[dict[str, Any]] = []
    for index, (axis, (key, panel, title)) in enumerate(zip(axes, layers)):
        panels.append(_plot_municipal_layer_discrete(
            axis,
            gdf,
            coastline,
            key,
            title,
            panel,
            draw_left_labels=index == 0,
        ))
    outputs = _save_figure(fig, "hazard_vulnerability_risk_multiplot")
    if write_metadata:
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        metadata_path = METADATA_DIR / "article_hazard_vulnerability_risk_metadata.json"
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "output": outputs[0],
            "risk_key": risk_key,
            "panels": panels,
            "palette": {
                "source": "Composite Score heatmap color sequence",
                "orientation": "inverted relative to displayed heatmap; low green to high red",
                "purple_tail_omitted": True,
                "reason": "upper municipal classes must be red rather than purple",
            },
            "annotations": {
                "figure_title_drawn": False,
                "panel_titles_drawn": True,
                "colorbar_labels_drawn": False,
                "bottom_interpretation_note_drawn": False,
            },
            "map_context": {
                "extent": list(MAP_EXTENT),
                "land_color": LAND_COLOR,
                "ocean_color": OCEAN_COLOR,
                "country_boundaries": "Natural Earth 10m admin_0_boundary_lines_land",
                "brazilian_state_boundaries": "Natural Earth 10m admin_1_states_provinces_lines",
            },
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, default=_to_jsonable) + "\n",
            encoding="utf-8",
        )
    return outputs


def _line_parts(geometry: object) -> list[LineString]:
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, (MultiLineString, GeometryCollection)):
        parts: list[LineString] = []
        for part in geometry.geoms:
            parts.extend(_line_parts(part))
        return parts
    return []


def build_coastal_compound_event_segments(
    municipalities: gpd.GeoDataFrame,
    ocean_df: pd.DataFrame,
    coastline: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    """Assign every short Brazilian coastal segment to its nearest grid point."""
    if coastline.empty:
        raise ValueError("The coastline layer is empty")
    ocean = ocean_df.reset_index(drop=True).copy()
    if "compound_c" not in ocean:
        raise ValueError("The ocean-grid source lacks compound-event counts")

    municipalities_projected = municipalities.to_crs(COASTAL_PROJECTION_CRS)
    coastline_projected = coastline.to_crs(COASTAL_PROJECTION_CRS)
    municipal_coastal_buffer = municipalities_projected.geometry.union_all().buffer(
        COASTLINE_MUNICIPAL_BUFFER_M
    )

    clipped_lines: list[LineString] = []
    for geometry in coastline_projected.geometry:
        clipped_lines.extend(
            _line_parts(geometry.intersection(municipal_coastal_buffer))
        )
    if not clipped_lines:
        raise RuntimeError("No Natural Earth coastline intersects the coastal municipalities")

    segment_geometries: list[LineString] = []
    segment_midpoints: list[np.ndarray] = []
    for line in clipped_lines:
        coordinates = np.asarray(line.coords, dtype=float)
        for start, end in zip(coordinates[:-1], coordinates[1:]):
            length = float(np.linalg.norm(end - start))
            number_of_segments = max(
                1,
                int(np.ceil(length / COASTLINE_SEGMENT_MAX_LENGTH_M)),
            )
            points = start + (end - start) * np.linspace(
                0.0,
                1.0,
                number_of_segments + 1,
            )[:, None]
            for segment_start, segment_end in zip(points[:-1], points[1:]):
                segment_geometries.append(
                    LineString([segment_start, segment_end])
                )
                segment_midpoints.append((segment_start + segment_end) / 2.0)

    ocean_points = gpd.GeoDataFrame(
        ocean,
        geometry=gpd.points_from_xy(ocean["longitude"], ocean["latitude"]),
        crs=OUTPUT_CRS,
    ).to_crs(COASTAL_PROJECTION_CRS)
    point_coordinates = np.asarray(
        [(point.x, point.y) for point in ocean_points.geometry],
        dtype=float,
    )
    nearest_distance_m, nearest_position = cKDTree(point_coordinates).query(
        np.asarray(segment_midpoints),
        k=1,
    )
    source_rows = ocean.iloc[nearest_position].reset_index(drop=True)
    segments = gpd.GeoDataFrame(
        {
            "source_grid_index": nearest_position.astype(int),
            "source_longitude": source_rows["longitude"].to_numpy(dtype=float),
            "source_latitude": source_rows["latitude"].to_numpy(dtype=float),
            "compound_event_count": source_rows["compound_c"].to_numpy(dtype=float),
            "nearest_grid_distance_km": nearest_distance_m / 1_000.0,
        },
        geometry=segment_geometries,
        crs=COASTAL_PROJECTION_CRS,
    ).to_crs(OUTPUT_CRS)
    used_positions = np.unique(nearest_position)
    metadata = {
        "method": (
            "Natural Earth 10m coastline clipped to a 30-km buffer around "
            "the coastal-municipality union; linework split into segments no "
            "longer than 5 km in EPSG:5880; each segment assigned the nearest "
            "native ocean grid point by projected midpoint distance"
        ),
        "projected_crs": COASTAL_PROJECTION_CRS,
        "municipal_buffer_m": COASTLINE_MUNICIPAL_BUFFER_M,
        "maximum_segment_length_m": COASTLINE_SEGMENT_MAX_LENGTH_M,
        "clipped_line_count": len(clipped_lines),
        "segment_count": len(segments),
        "native_grid_point_count": len(ocean),
        "native_grid_points_used": int(len(used_positions)),
        "nearest_distance_km": {
            "minimum": float(np.min(nearest_distance_m) / 1_000.0),
            "median": float(np.median(nearest_distance_m) / 1_000.0),
            "p90": float(np.quantile(nearest_distance_m, 0.90) / 1_000.0),
            "p99": float(np.quantile(nearest_distance_m, 0.99) / 1_000.0),
            "maximum": float(np.max(nearest_distance_m) / 1_000.0),
        },
        "assigned_value_statistics": _numeric_stats(
            segments["compound_event_count"]
        ),
    }
    return segments, metadata


def _compound_event_rate_boundaries(values: pd.Series) -> np.ndarray:
    finite = pd.to_numeric(values, errors="coerce").dropna()
    if finite.empty:
        raise ValueError("No compound-event rates available for coastal segments")
    step = math.ceil(
        float(finite.max()) / COASTAL_COLOR_CLASSES * 10.0
    ) / 10.0
    return np.arange(COASTAL_COLOR_CLASSES + 1, dtype=float) * step


def make_coastal_compound_event_rate_map(
    municipalities: gpd.GeoDataFrame,
    ocean_df: pd.DataFrame,
    coastline: gpd.GeoDataFrame | None,
    ocean_metadata: dict[str, Any],
    *,
    write_metadata: bool = True,
) -> list[str]:
    if coastline is None or coastline.empty:
        raise FileNotFoundError(COASTLINE_SHP)
    if not COMPOUND_SUMMARY_PATH.exists():
        raise FileNotFoundError(COMPOUND_SUMMARY_PATH)
    summary_document = json.loads(
        COMPOUND_SUMMARY_PATH.read_text(encoding="utf-8")
    )
    catalog_summary = summary_document["summary"]
    number_of_years = float(catalog_summary["n_years"])
    if number_of_years <= 0:
        raise ValueError("The catalog record length must be positive")

    annual_ocean_df = ocean_df.copy()
    annual_ocean_df["compound_event_count_total"] = annual_ocean_df[
        "compound_c"
    ]
    annual_ocean_df["compound_c"] = (
        annual_ocean_df["compound_event_count_total"] / number_of_years
    )
    segments, assignment_metadata = build_coastal_compound_event_segments(
        municipalities,
        annual_ocean_df,
        coastline,
    )
    segments = segments.rename(
        columns={
            "compound_event_count": "compound_event_rate_per_year",
        }
    )
    boundaries = _compound_event_rate_boundaries(
        segments["compound_event_rate_per_year"]
    )
    magma = plt.get_cmap("magma")
    cmap = ListedColormap(
        magma(np.linspace(0.95, 0.12, len(boundaries) - 1)),
        name="magma_discrete_reversed_without_black_endpoint",
    )
    norm = BoundaryNorm(boundaries, cmap.N, clip=True)

    fig = plt.figure(figsize=(8.4, 8.0), constrained_layout=False)
    axis = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    fig.subplots_adjust(left=0.07, right=0.965, top=0.98, bottom=0.12)
    _setup_article_geo_axis(
        axis,
        None,
        extent=COASTAL_MAP_EXTENT,
    )
    _draw_administrative_boundaries(axis)
    _plot_coastline(axis, coastline)
    class_indices = np.digitize(
        segments["compound_event_rate_per_year"].to_numpy(dtype=float),
        boundaries[1:-1],
    )
    for class_index in range(len(boundaries) - 1):
        class_geometries = segments.geometry[class_indices == class_index].tolist()
        if not class_geometries:
            continue
        dissolved = unary_union(class_geometries)
        merged = dissolved if isinstance(dissolved, LineString) else linemerge(dissolved)
        axis.add_geometries(
            _line_parts(merged),
            crs=ccrs.PlateCarree(),
            facecolor="none",
            edgecolor=cmap(class_index),
            linewidth=4.0,
            zorder=8,
        )
    axis.set_extent(COASTAL_MAP_EXTENT, crs=ccrs.PlateCarree())

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    fig.canvas.draw()
    map_position = axis.get_position()
    colorbar_axis = fig.add_axes(
        [
            map_position.x0,
            max(0.025, map_position.y0 - 0.085),
            map_position.width,
            0.026,
        ]
    )
    colorbar = fig.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        boundaries=boundaries,
        ticks=boundaries,
        spacing="uniform",
        drawedges=True,
        fraction=0.055,
        pad=0.065,
        aspect=34,
    )
    colorbar.set_label(
        r"Compound events year$^{-1}$",
        fontsize=10,
    )
    colorbar.ax.tick_params(labelsize=9, length=3)
    colorbar.outline.set_linewidth(0.75)

    outputs = _save_figure(fig, "coastal_compound_event_rate_per_year")
    if write_metadata:
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        metadata_path = (
            METADATA_DIR
            / "article_coastal_compound_event_rate_per_year_metadata.json"
        )
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "output": outputs[0],
            "ocean_grid_source": ocean_metadata,
            "catalog_summary": _relative(COMPOUND_SUMMARY_PATH),
            "period": catalog_summary["period"],
            "number_of_years": number_of_years,
            "formula": (
                "compound_event_rate_per_year = "
                "compound_count_total / number_of_years"
            ),
            "coastline_source": _relative(COASTLINE_SHP),
            "coastal_assignment": assignment_metadata,
            "colorbar": {
                "type": "discrete",
                "units": "events per year",
                "number_of_colors": len(boundaries) - 1,
                "boundaries": boundaries.tolist(),
                "colormap": "matplotlib magma sampled from 0.95 to 0.12",
                "orientation": "low counts light; high counts dark",
                "label_drawn": True,
                "label": "Compound events year^-1",
                "width_matches_map_axis": True,
            },
            "figure_title_drawn": False,
            "map_context": {
                "extent": list(COASTAL_MAP_EXTENT),
                "land_color": LAND_COLOR,
                "ocean_color": OCEAN_COLOR,
                "country_boundaries": "Natural Earth 10m admin_0_boundary_lines_land",
                "brazilian_state_boundaries": "Natural Earth 10m admin_1_states_provinces_lines",
            },
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, default=_to_jsonable) + "\n",
            encoding="utf-8",
        )
    return outputs


def _format_municipality(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "Unknown"
    text = str(value)
    return text.title() if text.isupper() else text


BRAZILIAN_STATE_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}


def _top10_table_frame(
    gdf: gpd.GeoDataFrame,
    key: str,
    value_label: str,
) -> pd.DataFrame:
    columns = ["municipality_name", "state", key]
    if "state_name" in gdf.columns:
        columns.insert(2, "state_name")
    ranked = gdf.loc[gdf[key].notna(), columns].copy()
    ranked["municipality_name"] = ranked["municipality_name"].map(_format_municipality)
    ranked["state"] = ranked["state"].fillna("").astype(str)
    if "state_name" not in ranked:
        ranked["state_name"] = ranked["state"].map(BRAZILIAN_STATE_NAMES)
    else:
        fallback = ranked["state"].map(BRAZILIAN_STATE_NAMES)
        ranked["state_name"] = ranked["state_name"].fillna(fallback)
    ranked[key] = pd.to_numeric(ranked[key], errors="coerce")
    ranked = ranked.dropna(subset=[key]).sort_values(
        [key, "municipality_name"],
        ascending=[False, True],
        kind="stable",
    ).head(10)
    ranked.insert(0, "Rank", np.arange(1, len(ranked) + 1))
    ranked = ranked.rename(
        columns={
            "municipality_name": "Municipality",
            "state_name": "State",
            "state": "UF",
            key: value_label,
        }
    )
    return ranked[["Rank", "Municipality", "State", "UF", value_label]]


def make_top10_municipality_tables(
    gdf: gpd.GeoDataFrame,
    risk_key: str,
    *,
    write_metadata: bool = True,
) -> list[str]:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    specifications = (
        (
            "Hazard_Index",
            "Hazard index",
            "hazard",
            "Top 10 Brazilian coastal municipalities by compound-event-count hazard index.",
            "tab:top10-municipal-hazard",
            3,
        ),
        (
            "SVI_Coast_2022",
            "SVI",
            "svi",
            "Top 10 Brazilian coastal municipalities by Social Vulnerability Index (SVI).",
            "tab:top10-municipal-svi",
            1,
        ),
        (
            risk_key,
            "Risk index",
            "integrated_risk",
            "Top 10 Brazilian coastal municipalities by integrated compound-risk index.",
            "tab:top10-municipal-integrated-risk",
            3,
        ),
    )
    outputs: list[str] = []
    metadata_tables: dict[str, Any] = {}
    for key, value_label, stem, caption, label, decimals in specifications:
        table = _top10_table_frame(gdf, key, value_label)
        csv_path = TABLE_DIR / f"top10_municipalities_by_{stem}.csv"
        tex_path = TABLE_DIR / f"top10_municipalities_by_{stem}.tex"
        table.to_csv(csv_path, index=False, float_format=f"%.{decimals}f")
        formatted = table.copy()
        formatted[value_label] = formatted[value_label].map(
            lambda value: f"{value:.{decimals}f}"
        )
        latex = formatted.to_latex(
            index=False,
            escape=True,
            caption=caption,
            label=label,
            column_format="rlllr",
            position="htbp",
        )
        tex_path.write_text(latex, encoding="utf-8")
        outputs.extend((_relative(csv_path), _relative(tex_path)))
        metadata_tables[stem] = {
            "field": key,
            "value_label": value_label,
            "rows": table.to_dict(orient="records"),
            "csv": _relative(csv_path),
            "latex": _relative(tex_path),
        }

    if write_metadata:
        METADATA_DIR.mkdir(parents=True, exist_ok=True)
        metadata_path = METADATA_DIR / "article_top10_municipality_tables_metadata.json"
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "risk_key": risk_key,
            "ranking": "descending; municipality name ascending as deterministic tie-breaker",
            "tables": metadata_tables,
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, default=_to_jsonable) + "\n",
            encoding="utf-8",
        )
        outputs.append(_relative(metadata_path))
    return outputs


def make_final_integrated_risk(
    gdf: gpd.GeoDataFrame, coastline: gpd.GeoDataFrame | None, risk_key: str
) -> list[str]:
    if risk_key != "Risk_Hazard":
        title = "Relative coastal risk based on Risk_Comp fallback"
    else:
        title = "Relative coastal risk from compound-event count and social vulnerability"

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
        "Hazard_Index = norm(compound_c)\nRisk_Hazard =\n(SVI_Coast_2022 / 100) x Hazard_Index",
        transform=ax_rank.transAxes,
        fontsize=7.5,
        color="#475569",
        va="top",
        linespacing=1.35,
    )
    return _save_figure(fig, "final_integrated_risk")


def make_original_ocean_hazard_points(
    ocean_df: pd.DataFrame,
    coastline: gpd.GeoDataFrame | None,
    ocean_meta: dict[str, Any],
) -> list[str]:
    fig, ax = plt.subplots(figsize=(7.6, 8.2), constrained_layout=False)
    fig.subplots_adjust(left=0.075, right=0.88, top=0.93, bottom=0.105)
    values = ocean_df["Hazard_Index"]
    norm = Normalize(float(values.min()), float(values.max()))
    _setup_map_axis(ax, "Original oceanic compound-event count points")
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
    if ocean_meta["hazard_index_mode"] in {"compound_count_only", "compound_count_only_current_scope"}:
        cbar.set_label("Compound-event count", fontsize=8)
    else:
        cbar.set_label("Oceanic Hazard_Index (relative)", fontsize=8)
    cbar.ax.tick_params(labelsize=7, length=2.5)
    cbar.outline.set_linewidth(0.7)
    mode_text = {
        "read": "Hazard_Index read directly from source.",
        "computed_minmax_mean": "Hazard_Index computed as mean of min-max normalized count, overlap duration, and intensity.",
        "compound_count_only": "Fallback: only compound-event count was available.",
        "compound_count_only_current_scope": "Current scope: compound-event count is used as the hazard signal.",
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
    return _save_figure(fig, "original_ocean_hazard_points")


def main() -> None:
    _clean_obsolete_article_images()
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    gdf, risk_meta = read_risk_data()
    coastline = read_coastline()
    ocean_df, ocean_meta = read_ocean_hazard_data()

    risk_key = risk_meta["risk_panel_key"]
    generated: dict[str, list[str]] = {}
    generated["coastal_compound_event_rate_per_year"] = make_coastal_compound_event_rate_map(
        gdf,
        ocean_df,
        coastline,
        ocean_meta,
    )
    generated["hazard_vulnerability_risk_multiplot"] = make_hazard_vulnerability_risk_multiplot(
        gdf, coastline, risk_key
    )
    generated["top10_municipality_tables"] = make_top10_municipality_tables(
        gdf,
        risk_key,
    )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "risk_data": risk_meta,
        "ocean_hazard": ocean_meta,
        "outputs": generated,
        "interpretation_caveat": (
            "Risk indices are comparative across Brazilian coastal municipalities. "
            "They should not be read as absolute expected damage or absence/presence of coastal hazard."
        ),
    }
    summary_path = METADATA_DIR / "article_risk_figure_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=_to_jsonable)
        f.write("\n")

    validate_article_figure_outputs()

    print("\nOSR11 article risk figures and tables generated")
    print("-----------------------------------------------")
    print(f"Risk data: {risk_meta['source_path']}")
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
