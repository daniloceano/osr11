"""Export municipal risk-index layers for the results website.

Reads ``outputs/risk_index/risk_index.shp``, filters the municipalities with
available risk/vulnerability fields, reprojects to EPSG:4326, simplifies the
geometry for browser use, and writes the current compound-count-only scope plus
the original multi-metric product as a legacy export:

    site/public/data/risk_index_municipalities.geojson
    site/public/data/risk_index_metadata.json
    site/public/data/risk_index_legacy_municipalities.geojson
    site/public/data/risk_index_legacy_metadata.json

Usage:
    python -m src.site.export_risk_index_data
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pyogrio
from shapely import get_num_coordinates


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "outputs" / "risk_index"
SOURCE_FILE = SOURCE_DIR / "risk_index.shp"
SITE_DATA_DIR = ROOT / "site" / "public" / "data"
OUTPUT_GEOJSON = SITE_DATA_DIR / "risk_index_municipalities.geojson"
OUTPUT_METADATA = SITE_DATA_DIR / "risk_index_metadata.json"
OUTPUT_LEGACY_GEOJSON = SITE_DATA_DIR / "risk_index_legacy_municipalities.geojson"
OUTPUT_LEGACY_METADATA = SITE_DATA_DIR / "risk_index_legacy_metadata.json"

SIMPLIFY_TOLERANCE_DEGREES = 0.001
OUTPUT_CRS = "EPSG:4326"


@dataclass(frozen=True)
class LayerSpec:
    key: str
    label: str
    unit: str
    description: str
    candidates: tuple[str, ...]


LEGACY_LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        key="SVI_Coast_2022",
        label="Social Vulnerability Index",
        unit="0-100",
        description="Social Vulnerability Index from IBGE/SIDRA 2022 variables, PCA/PC1 normalized to 0-100.",
        candidates=("SVI_Coast_2022", "SVI_Coast_", "SVI_Coast", "SVI_Coas"),
    ),
    LayerSpec(
        key="Hazard_Index",
        label="Legacy multi-metric compound-event hazard index",
        unit="index",
        description="Legacy mean of normalized compound-event frequency, mean overlap duration, and mean compound-event intensity.",
        candidates=("Hazard_Index", "Haz_index", "Hazard_In", "azard_Inde", "HazardInd"),
    ),
    LayerSpec(
        key="Risk_Comp",
        label="Risk based on SVI and compound-event frequency",
        unit="index",
        description="(SVI_Coast_2022 / 100) x normalized compound-event frequency.",
        candidates=("Risk_Comp", "Risk_comp", "risk_index", "Risk_Com"),
    ),
    LayerSpec(
        key="Risk_Hazard",
        label="Legacy integrated coastal risk",
        unit="index",
        description="Legacy (SVI_Coast_2022 / 100) x multi-metric Hazard_Index.",
        candidates=("Risk_Hazard", "Risk_harza", "Risk_Haza", "risk_inde1"),
    ),
)

SUPPORT_FIELD_CANDIDATES: dict[str, tuple[str, ...]] = {
    "municipality_code": ("CD_MUN", "geocode", "code_muni"),
    "municipality_name": ("NM_MUN", "municipio", "municipali"),
    "state": ("SIGLA_UF", "uf"),
    "state_name": ("NM_UF",),
    "compound_c": ("compound_c",),
    "mean_overl": ("mean_overl",),
    "mean_compo": ("mean_compo",),
    "grid_lat": ("grid_lat",),
    "grid_lon": ("grid_lon",),
    "PC1": ("PC1",),
    "pop_house": ("pop_house",),
    "pop_rent": ("pop_rent",),
    "pop_poverty": ("pop_povert", "pop_poverty"),
    "pop_agevul": ("pop_agevul",),
    "pop_nonwhite": ("pop_nonwhi", "pop_nonwhite"),
    "pop_illiterate": ("pop_illite", "pop_illiterate"),
    "pop_nowater": ("pop_nowate", "pop_nowater"),
    "pop_nosewage": ("pop_nosewa", "pop_nosewage"),
    "pop_nogarbage": ("pop_nogarb", "pop_nogarbage"),
    "pop_nopaving": ("pop_nopavi", "pop_nopaving"),
}


def _source_components() -> dict[str, bool]:
    return {
        suffix: (SOURCE_DIR / f"risk_index{suffix}").exists()
        for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg", ".qmd")
    }


def _require_source_files() -> None:
    required = (".shp", ".shx", ".dbf", ".prj")
    missing = [suffix for suffix in required if not (SOURCE_DIR / f"risk_index{suffix}").exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required shapefile component(s) in {SOURCE_DIR}: {', '.join(missing)}"
        )


def _normalize_name(name: str) -> str:
    return name.lower().replace("_", "")


def _resolve_field(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    exact = {col: col for col in columns}
    for candidate in candidates:
        if candidate in exact:
            return candidate

    lower_map = {col.lower(): col for col in columns}
    for candidate in candidates:
        match = lower_map.get(candidate.lower())
        if match:
            return match

    normalized_map = {_normalize_name(col): col for col in columns}
    for candidate in candidates:
        match = normalized_map.get(_normalize_name(candidate))
        if match:
            return match

    return None


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return round(value, 6) if math.isfinite(value) else None
    if isinstance(value, str):
        return value
    if hasattr(value, "item"):
        return _to_jsonable(value.item())
    return value


def _numeric_stats(series) -> dict[str, float | int | None]:
    values = series.dropna().astype(float)
    if values.empty:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {
        "count": int(values.count()),
        "min": round(float(values.min()), 6),
        "max": round(float(values.max()), 6),
        "mean": round(float(values.mean()), 6),
        "median": round(float(values.median()), 6),
    }


def _minmax(series):
    values = series.astype(float)
    valid = values.dropna()
    if valid.empty:
        return values * np.nan
    vmin = float(valid.min())
    vmax = float(valid.max())
    if math.isclose(vmin, vmax):
        return values.where(values.isna(), 0.0)
    return (values - vmin) / (vmax - vmin)


def _where_clause(fields: list[str]) -> str:
    return " OR ".join(f"{field} IS NOT NULL" for field in fields)


def _current_available_layers(export: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    return [
        {
            "key": "Risk_Hazard",
            "label": "Current final coastal risk",
            "unit": "index",
            "description": "(SVI_Coast_2022 / 100) x Hazard_Index, where Hazard_Index is norm(compound_c).",
            "actual_field": "derived:(SVI_Coast_2022/100)*norm(compound_c)",
            "stats": _numeric_stats(export["Risk_Hazard"]),
        },
        {
            "key": "Hazard_Index",
            "label": "Compound-event frequency hazard",
            "unit": "index",
            "description": "Min-Max normalized compound-event count (compound_c) over 1993-2025.",
            "actual_field": "derived:norm(compound_c)",
            "stats": _numeric_stats(export["Hazard_Index"]),
        },
        {
            "key": "SVI_Coast_2022",
            "label": "Social Vulnerability Index",
            "unit": "0-100",
            "description": "Social Vulnerability Index from IBGE/SIDRA 2022 variables, PCA/PC1 normalized to 0-100.",
            "actual_field": "SVI_Coast_2022",
            "stats": _numeric_stats(export["SVI_Coast_2022"]),
        },
    ]


def _derive_current_scope(legacy_export: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    missing_required = [key for key in ("compound_c", "SVI_Coast_2022") if key not in legacy_export]
    if missing_required:
        raise ValueError(
            "Cannot derive the current compound-count risk scope. Missing required field(s): "
            + ", ".join(missing_required)
        )

    export = legacy_export.copy()
    for key in ("Hazard_Index", "Risk_Comp", "Risk_Hazard"):
        if key in export:
            export[f"Legacy_{key}"] = export[key]

    hazard = _minmax(export["compound_c"])
    svi_fraction = export["SVI_Coast_2022"].astype(float) / 100.0
    risk = svi_fraction * hazard

    export["Hazard_Index"] = hazard.map(_to_jsonable)
    export["Risk_Hazard"] = risk.map(_to_jsonable)
    # Kept for downstream compatibility. Under the current scope, the compound
    # frequency-only risk is the final integrated risk.
    export["Risk_Comp"] = risk.map(_to_jsonable)
    return export


def build_site_risk_data() -> tuple[gpd.GeoDataFrame, dict[str, Any], gpd.GeoDataFrame, dict[str, Any]]:
    _require_source_files()

    source_info = pyogrio.read_info(SOURCE_FILE)
    source_fields = list(source_info["fields"])

    layer_field_map: dict[str, str] = {}
    missing_layers: list[str] = []
    for spec in LEGACY_LAYER_SPECS:
        field = _resolve_field(source_fields, spec.candidates)
        if field is None:
            missing_layers.append(spec.key)
        else:
            layer_field_map[spec.key] = field

    if not layer_field_map:
        raise ValueError(
            "No expected risk-index fields were found. Checked candidates: "
            + json.dumps({spec.key: spec.candidates for spec in LEGACY_LAYER_SPECS}, indent=2)
        )

    support_field_map = {
        key: field
        for key, candidates in SUPPORT_FIELD_CANDIDATES.items()
        if (field := _resolve_field(source_fields, candidates)) is not None
    }

    read_fields = sorted(set(layer_field_map.values()) | set(support_field_map.values()))
    gdf = pyogrio.read_dataframe(
        SOURCE_FILE,
        columns=read_fields,
        where=_where_clause(list(layer_field_map.values())),
    )

    if gdf.empty:
        raise ValueError("Risk-index shapefile contains no features with populated expected layer fields.")

    source_crs = str(gdf.crs) if gdf.crs else None
    if gdf.crs is None:
        raise ValueError("Risk-index shapefile has no CRS. Refusing to export without a projection.")
    if str(gdf.crs).upper() != OUTPUT_CRS:
        gdf = gdf.to_crs(OUTPUT_CRS)

    coords_before = int(sum(get_num_coordinates(geom) for geom in gdf.geometry))
    gdf.geometry = gdf.geometry.simplify(SIMPLIFY_TOLERANCE_DEGREES, preserve_topology=True)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    coords_after = int(sum(get_num_coordinates(geom) for geom in gdf.geometry))

    legacy_export = gpd.GeoDataFrame(geometry=gdf.geometry, crs=OUTPUT_CRS)
    for key, field in support_field_map.items():
        legacy_export[key] = gdf[field].map(_to_jsonable)
    for spec in LEGACY_LAYER_SPECS:
        field = layer_field_map.get(spec.key)
        if field is not None:
            legacy_export[spec.key] = gdf[field].map(_to_jsonable)

    # Stable display fallbacks if uppercase IBGE/SIDRA fields are present but the
    # title-case IBGE boundary fields are not populated for a row.
    if "municipality_name" in legacy_export and "municipio" in gdf:
        legacy_export["municipality_name"] = legacy_export["municipality_name"].fillna(gdf["municipio"].map(_to_jsonable))
    if "state" in legacy_export and "uf" in gdf:
        legacy_export["state"] = legacy_export["state"].fillna(gdf["uf"].map(_to_jsonable))

    legacy_available_layers = []
    for spec in LEGACY_LAYER_SPECS:
        field = layer_field_map.get(spec.key)
        if field is None:
            continue
        stats = _numeric_stats(gdf[field])
        legacy_available_layers.append(
            {
                "key": spec.key,
                "label": spec.label,
                "unit": spec.unit,
                "description": spec.description,
                "actual_field": field,
                "stats": stats,
            }
        )

    legacy_numeric_stats = {
        key: _numeric_stats(gdf[field])
        for key, field in {**layer_field_map, **support_field_map}.items()
        if field in gdf and np.issubdtype(gdf[field].dropna().dtype, np.number)
    }

    common_metadata: dict[str, Any] = {
        "generated_by": "src.site.export_risk_index_data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(SOURCE_FILE.relative_to(ROOT)),
        "source_components": _source_components(),
        "source_crs": source_crs,
        "output_crs": OUTPUT_CRS,
        "source_feature_count": int(source_info["features"]),
        "feature_count": int(len(legacy_export)),
        "geometry_type_counts": gdf.geometry.geom_type.value_counts().to_dict(),
        "bbox": [round(float(v), 6) for v in gdf.total_bounds],
        "simplification": {
            "enabled": True,
            "tolerance_degrees": SIMPLIFY_TOLERANCE_DEGREES,
            "preserve_topology": True,
            "coordinates_before": coords_before,
            "coordinates_after": coords_after,
        },
        "field_aliases": {
            "layers": layer_field_map,
            "support": support_field_map,
        },
        "source_fields": source_fields,
    }

    legacy_metadata: dict[str, Any] = {
        **common_metadata,
        "scope": "legacy_multimetric",
        "available_layers": legacy_available_layers,
        "missing_expected_layers": missing_layers,
        "numeric_stats": legacy_numeric_stats,
        "methodology": {
            "SVI_Coast_2022": "IBGE/SIDRA 2022 socioeconomic and infrastructure variables standardized with StandardScaler, submitted to PCA, PC1 sign-adjusted so higher values mean higher vulnerability, then normalized 0-100.",
            "exposure": "Oceanic compound-event hazard metrics spatialized and associated with coastal municipalities by spatial join.",
            "Hazard_Index": "[norm(compound_c) + norm(mean_overl) + norm(mean_compo)] / 3.",
            "Risk_Comp": "(SVI_Coast_2022 / 100) x norm(compound_c).",
            "Risk_Hazard": "(SVI_Coast_2022 / 100) x Hazard_Index.",
        },
    }

    current_export = _derive_current_scope(legacy_export)
    current_numeric_stats = {
        key: _numeric_stats(current_export[key])
        for key in (
            "SVI_Coast_2022",
            "Hazard_Index",
            "Risk_Comp",
            "Risk_Hazard",
            "Legacy_Hazard_Index",
            "Legacy_Risk_Comp",
            "Legacy_Risk_Hazard",
            "compound_c",
            "mean_overl",
            "mean_compo",
        )
        if key in current_export
    }
    current_metadata: dict[str, Any] = {
        **common_metadata,
        "scope": "compound_count_only",
        "available_layers": _current_available_layers(current_export),
        "missing_expected_layers": [
            key for key in ("SVI_Coast_2022", "compound_c") if key not in current_export
        ],
        "field_aliases": {
            "layers": {
                "SVI_Coast_2022": layer_field_map.get("SVI_Coast_2022"),
                "Hazard_Index": "derived:norm(compound_c)",
                "Risk_Comp": "derived:(SVI_Coast_2022/100)*norm(compound_c)",
                "Risk_Hazard": "derived:(SVI_Coast_2022/100)*norm(compound_c)",
                "Legacy_Hazard_Index": layer_field_map.get("Hazard_Index"),
                "Legacy_Risk_Comp": layer_field_map.get("Risk_Comp"),
                "Legacy_Risk_Hazard": layer_field_map.get("Risk_Hazard"),
            },
            "support": support_field_map,
        },
        "legacy_outputs": {
            "geojson": str(OUTPUT_LEGACY_GEOJSON.relative_to(ROOT)),
            "metadata": str(OUTPUT_LEGACY_METADATA.relative_to(ROOT)),
        },
        "numeric_stats": current_numeric_stats,
        "methodology": {
            "SVI_Coast_2022": "IBGE/SIDRA 2022 socioeconomic and infrastructure variables standardized with StandardScaler, submitted to PCA, PC1 sign-adjusted so higher values mean higher vulnerability, then normalized 0-100.",
            "exposure": "Oceanic compound-event metrics remain associated with coastal municipalities by the existing spatial join, selecting the associated grid point with the highest compound_c.",
            "Hazard_Index": "Current scope: norm(compound_c). Overlap duration and compound-event intensity are retained as diagnostics/legacy fields, but are not included in the current hazard layer because of interpretation uncertainty near river mouths.",
            "Risk_Comp": "(SVI_Coast_2022 / 100) x norm(compound_c). Kept as a compatibility alias for the current final risk.",
            "Risk_Hazard": "(SVI_Coast_2022 / 100) x Hazard_Index, with Hazard_Index = norm(compound_c).",
        },
        "legacy_methodology": legacy_metadata["methodology"],
    }
    return current_export, current_metadata, legacy_export, legacy_metadata


def save_site_risk_data(
    current_gdf: gpd.GeoDataFrame,
    current_metadata: dict[str, Any],
    legacy_gdf: gpd.GeoDataFrame,
    legacy_metadata: dict[str, Any],
) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    current_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(current_metadata, f, ensure_ascii=False, indent=2)
        f.write("\n")
    legacy_gdf.to_file(OUTPUT_LEGACY_GEOJSON, driver="GeoJSON")
    with open(OUTPUT_LEGACY_METADATA, "w", encoding="utf-8") as f:
        json.dump(legacy_metadata, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Saved: {OUTPUT_GEOJSON} ({OUTPUT_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Saved: {OUTPUT_METADATA} ({OUTPUT_METADATA.stat().st_size / 1024:.1f} KB)")
    print(f"Saved: {OUTPUT_LEGACY_GEOJSON} ({OUTPUT_LEGACY_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Saved: {OUTPUT_LEGACY_METADATA} ({OUTPUT_LEGACY_METADATA.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    current_gdf, current_metadata, legacy_gdf, legacy_metadata = build_site_risk_data()
    save_site_risk_data(current_gdf, current_metadata, legacy_gdf, legacy_metadata)
    print("Current layer definitions:")
    for layer in current_metadata["available_layers"]:
        print(f"  {layer['key']} <- {layer['actual_field']} ({layer['stats']['count']} values)")
    if current_metadata["missing_expected_layers"]:
        print("Missing current expected layers:", ", ".join(current_metadata["missing_expected_layers"]))
    print("Legacy layer field aliases:")
    for layer in legacy_metadata["available_layers"]:
        print(f"  {layer['key']} <- {layer['actual_field']} ({layer['stats']['count']} values)")
    if legacy_metadata["missing_expected_layers"]:
        print("Missing legacy expected layers:", ", ".join(legacy_metadata["missing_expected_layers"]))


if __name__ == "__main__":
    main()
