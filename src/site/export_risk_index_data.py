"""Export Karine's municipal risk-index shapefile for the results website.

Reads ``outputs/risk_index/risk_index.shp``, filters the municipalities with
available risk/vulnerability fields, reprojects to EPSG:4326, simplifies the
geometry for browser use, and writes:

    site/public/data/risk_index_municipalities.geojson
    site/public/data/risk_index_metadata.json

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

SIMPLIFY_TOLERANCE_DEGREES = 0.001
OUTPUT_CRS = "EPSG:4326"


@dataclass(frozen=True)
class LayerSpec:
    key: str
    label: str
    unit: str
    description: str
    candidates: tuple[str, ...]


LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        key="SVI_Coast_2022",
        label="Social Vulnerability Index",
        unit="0-100",
        description="Social Vulnerability Index from IBGE/SIDRA 2022 variables, PCA/PC1 normalized to 0-100.",
        candidates=("SVI_Coast_2022", "SVI_Coast_", "SVI_Coast", "SVI_Coas"),
    ),
    LayerSpec(
        key="Hazard_Index",
        label="Compound-event hazard index",
        unit="index",
        description="Mean of normalized compound-event frequency, mean overlap duration, and mean compound-event intensity.",
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
        label="Integrated coastal risk",
        unit="index",
        description="(SVI_Coast_2022 / 100) x Hazard_Index.",
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


def _where_clause(fields: list[str]) -> str:
    return " OR ".join(f"{field} IS NOT NULL" for field in fields)


def build_site_risk_data() -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    _require_source_files()

    source_info = pyogrio.read_info(SOURCE_FILE)
    source_fields = list(source_info["fields"])

    layer_field_map: dict[str, str] = {}
    missing_layers: list[str] = []
    for spec in LAYER_SPECS:
        field = _resolve_field(source_fields, spec.candidates)
        if field is None:
            missing_layers.append(spec.key)
        else:
            layer_field_map[spec.key] = field

    if not layer_field_map:
        raise ValueError(
            "No expected risk-index fields were found. Checked candidates: "
            + json.dumps({spec.key: spec.candidates for spec in LAYER_SPECS}, indent=2)
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

    export = gpd.GeoDataFrame(geometry=gdf.geometry, crs=OUTPUT_CRS)
    for key, field in support_field_map.items():
        export[key] = gdf[field].map(_to_jsonable)
    for spec in LAYER_SPECS:
        field = layer_field_map.get(spec.key)
        if field is not None:
            export[spec.key] = gdf[field].map(_to_jsonable)

    # Stable display fallbacks if uppercase IBGE/SIDRA fields are present but the
    # title-case IBGE boundary fields are not populated for a row.
    if "municipality_name" in export and "municipio" in gdf:
        export["municipality_name"] = export["municipality_name"].fillna(gdf["municipio"].map(_to_jsonable))
    if "state" in export and "uf" in gdf:
        export["state"] = export["state"].fillna(gdf["uf"].map(_to_jsonable))

    available_layers = []
    for spec in LAYER_SPECS:
        field = layer_field_map.get(spec.key)
        if field is None:
            continue
        stats = _numeric_stats(gdf[field])
        available_layers.append(
            {
                "key": spec.key,
                "label": spec.label,
                "unit": spec.unit,
                "description": spec.description,
                "actual_field": field,
                "stats": stats,
            }
        )

    numeric_stats = {
        key: _numeric_stats(gdf[field])
        for key, field in {**layer_field_map, **support_field_map}.items()
        if field in gdf and np.issubdtype(gdf[field].dropna().dtype, np.number)
    }

    metadata: dict[str, Any] = {
        "generated_by": "src.site.export_risk_index_data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(SOURCE_FILE.relative_to(ROOT)),
        "source_components": _source_components(),
        "source_crs": source_crs,
        "output_crs": OUTPUT_CRS,
        "source_feature_count": int(source_info["features"]),
        "feature_count": int(len(export)),
        "geometry_type_counts": gdf.geometry.geom_type.value_counts().to_dict(),
        "bbox": [round(float(v), 6) for v in gdf.total_bounds],
        "simplification": {
            "enabled": True,
            "tolerance_degrees": SIMPLIFY_TOLERANCE_DEGREES,
            "preserve_topology": True,
            "coordinates_before": coords_before,
            "coordinates_after": coords_after,
        },
        "available_layers": available_layers,
        "missing_expected_layers": missing_layers,
        "field_aliases": {
            "layers": layer_field_map,
            "support": support_field_map,
        },
        "source_fields": source_fields,
        "numeric_stats": numeric_stats,
        "methodology": {
            "SVI_Coast_2022": "IBGE/SIDRA 2022 socioeconomic and infrastructure variables standardized with StandardScaler, submitted to PCA, PC1 sign-adjusted so higher values mean higher vulnerability, then normalized 0-100.",
            "exposure": "Oceanic compound-event hazard metrics spatialized and associated with coastal municipalities by spatial join.",
            "Hazard_Index": "[norm(compound_c) + norm(mean_overl) + norm(mean_compo)] / 3.",
            "Risk_Comp": "(SVI_Coast_2022 / 100) x norm(compound_c).",
            "Risk_Hazard": "(SVI_Coast_2022 / 100) x Hazard_Index.",
        },
    }
    return export, metadata


def save_site_risk_data(gdf: gpd.GeoDataFrame, metadata: dict[str, Any]) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Saved: {OUTPUT_GEOJSON} ({OUTPUT_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Saved: {OUTPUT_METADATA} ({OUTPUT_METADATA.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    gdf, metadata = build_site_risk_data()
    save_site_risk_data(gdf, metadata)
    print("Layer field aliases:")
    for layer in metadata["available_layers"]:
        print(f"  {layer['key']} <- {layer['actual_field']} ({layer['stats']['count']} values)")
    if metadata["missing_expected_layers"]:
        print("Missing expected layers:", ", ".join(metadata["missing_expected_layers"]))


if __name__ == "__main__":
    main()
