"""Export the municipal risk-index layer for the results website.

Reads ``outputs/risk_index/risk_index.shp`` — the externally delivered municipal
file, which supplies the geometry, ``SVI_Coast_2022``, the ten IBGE/SIDRA
indicators, ``PC1`` and the pre-associated ``grid_lat``/``grid_lon`` — reprojects
to EPSG:4326, simplifies the geometry for browser use, transfers the normalized
native-grid multimetric Hazard Index to the municipalities, and writes:

    site/public/data/risk_index_municipalities.geojson
    site/public/data/risk_index_metadata.json

The published risk is the conjunctive, IPCC-style geometric mean of its three
components,

    Risk_Hazard_raw = (Hazard_Index_mun * Exposure_Index * SVI/100) ** (1/3)

each floored at 0.01 first. The geometric mean is what preserves the property
the IPCC framework implies — that risk requires a hazard, someone exposed to it,
and a susceptibility, all three — whereas an arithmetic mean would let a large
population compensate for the absence of a physical driver.

There is a single product and a single source of municipal attributes. The
delivered ``Haz_index`` / ``Risk_comp`` / ``Risk_harza`` fields are not read: the
hazard and the risk are recalculated here from the versioned native-grid
metrics. The exposure counts come from ``outputs/exposure/municipal_exposure.csv``.
A missing or incomplete input raises instead of falling back.

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
import pandas as pd
import pyogrio
from shapely import get_num_coordinates

from src.risk_integration.coastal_projection import COASTAL_MAP_EXTENT
from src.risk_integration.exposure_index import (
    CLIP_FLOOR,
    GOALPOST_MAX_INHABITANTS,
    GOALPOST_MIN_INHABITANTS,
    exposure_absolute,
    exposure_inform,
    exposure_relative,
)
from src.risk_integration.hazard_index import (
    NATIVE_GRID_SOURCE,
    derive_native_hazard_index as _derive_native_hazard_index,
)
from src.risk_integration.palettes import risk_colors


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "outputs" / "risk_index"
SOURCE_FILE = SOURCE_DIR / "risk_index.shp"
EXPOSURE_CSV = ROOT / "outputs" / "exposure" / "municipal_exposure.csv"
#: Distance band whose population feeds the exposure component.
EXPOSURE_FIELD = "pop_10km"
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


#: The only quantity read from the delivered shapefile. Its hazard and risk
#: columns are deliberately ignored: they were computed with a superseded
#: definition and are recalculated here from
#: ``outputs/storm_catalog/compound/compound_metrics.csv``. Shapefile DBF names
#: are truncated to ten characters, hence the spelling variants.
SOURCE_LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        key="SVI_Coast_2022",
        label="Social Vulnerability Index",
        unit="0-100",
        description="Social Vulnerability Index from IBGE/SIDRA 2022 variables, PCA/PC1 normalized to 0-100.",
        candidates=("SVI_Coast_2022", "SVI_Coast_", "SVI_Coast", "SVI_Coas"),
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


def _require_exposure() -> pd.DataFrame:
    """Municipal exposure counts. Required: risk has three components now."""
    if not EXPOSURE_CSV.exists():
        raise FileNotFoundError(
            f"{EXPOSURE_CSV} is required for the exposure component of the risk "
            "index. Run src.risk_integration.municipal_exposure first; there is "
            "no fallback to a risk index without exposure."
        )
    exposure = pd.read_csv(EXPOSURE_CSV, dtype={"municipality_code": str})
    missing = [
        column
        for column in ("municipality_code", EXPOSURE_FIELD, "pop_municipality")
        if column not in exposure.columns
    ]
    if missing:
        raise ValueError(
            f"{EXPOSURE_CSV} lacks required column(s): {', '.join(missing)}"
        )
    return exposure[["municipality_code", EXPOSURE_FIELD, "pop_municipality"]]


def _require_source_files() -> None:
    required = (".shp", ".shx", ".dbf", ".prj")
    missing = [suffix for suffix in required if not (SOURCE_DIR / f"risk_index{suffix}").exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing required shapefile component(s) in {SOURCE_DIR}: "
            f"{', '.join(missing)}. The externally delivered municipal file "
            "(geometry, SVI_Coast_2022, the ten IBGE/SIDRA indicators, PC1 and "
            "the pre-associated grid_lat/grid_lon) is the only accepted source "
            "for this export; there is no fallback."
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


def _nice_boundaries(
    series: pd.Series,
    class_count: int = 8,
) -> list[float]:
    """Rounded class limits covering the observed range of ``series``."""
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return [0.0, 1.0]
    lower = float(values.min())
    upper = float(values.max())
    if math.isclose(lower, upper):
        return [round(lower, 6), round(lower + 1.0, 6)]
    raw_step = (upper - lower) / class_count
    magnitude = 10.0 ** math.floor(math.log10(raw_step))
    normalized = raw_step / magnitude
    nice = next(
        candidate
        for candidate in (1.0, 2.0, 2.5, 5.0, 10.0)
        if normalized <= candidate
    )
    step = nice * magnitude
    decimals = max(0, min(6, -math.floor(math.log10(step)) + 1))
    start = math.floor(lower / step) * step
    boundaries: list[float] = []
    value = start
    while value < upper + step * 0.5:
        boundaries.append(round(value, decimals))
        value += step
    if len(boundaries) < 2:
        boundaries.append(round(start + step, decimals))
    # Guarantee that the top class limit is above the largest observed value,
    # so no value falls outside the published legend.
    while boundaries[-1] < upper:
        boundaries.append(round(boundaries[-1] + step, decimals))
    return boundaries


#: Layer catalogue of the municipal product. Raw (pre-normalization) stages are
#: published next to the normalized ones so the effect of each Min--Max step is
#: visible. ``Hazard_Index_mun`` stays in the GeoJSON properties but is not
#: offered as a map layer.
CURRENT_LAYER_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "key": "Risk_Hazard",
        "label": "Integrated coastal risk (normalized)",
        "short_label": "Risk (0–1)",
        "unit": "0–1",
        "stage": "normalized",
        "group": "Integrated risk",
        "actual_field": (
            "derived:norm_municipal((Hazard_Index_mun*Exposure_Index*"
            "SVI_Coast_2022/100)^(1/3))"
        ),
        "description": (
            "Final integrated risk: the geometric mean of hazard, exposure and "
            "vulnerability, Min-Max normalized across the coastal "
            "municipalities. Conjunctive by construction — a component near zero "
            "pulls the whole index down, which is the property the IPCC risk "
            "framework implies."
        ),
    },
    {
        "key": "Risk_Hazard_raw",
        "label": "Integrated coastal risk (before normalization)",
        "short_label": "Risk (raw)",
        "unit": "dimensionless product",
        "stage": "raw",
        "group": "Integrated risk",
        "actual_field": (
            "derived:(Hazard_Index_mun*Exposure_Index*SVI_Coast_2022/100)^(1/3)"
        ),
        "description": (
            "The geometric mean of the three components before the municipal "
            "Min-Max step, with each floored at 0.01 so that a municipality at "
            "the bottom of a Min-Max scale is not handed zero risk as a scaling "
            "artefact."
        ),
    },
    {
        "key": "Exposure_Index",
        "label": "Population exposure",
        "short_label": "Exposure",
        "unit": "0–1",
        "stage": "input",
        "group": "Exposure",
        "actual_field": "derived:geomean(goalposts(log10(pop_10km)), pop_10km/pop_municipality)",
        "description": (
            "Resident population within 10 km of the coastline, on a log scale "
            "between fixed goalposts, paired by geometric mean with the share of "
            "the municipal population inside the band. Following INFORM, which "
            "computes physical exposure both ways because the count favours the "
            "metropolitan municipalities and the share favours the small "
            "fully-coastal ones. Proximity, not modelled inundation."
        ),
    },
    {
        "key": "Exposure_absolute",
        "label": "Exposure half — absolute count between goalposts",
        "short_label": "Exposure (absolute)",
        "unit": "0–1",
        "stage": "component",
        "group": "Exposure",
        "actual_field": "derived:goalposts(log10(pop_10km), 1e2, 1e6)",
        "description": (
            "How many people, on a log scale fixed between 100 and 1,000,000 "
            "inhabitants. Fixed goalposts keep the scale independent of which "
            "municipalities are in the set: 0.5 always denotes 10,000 people."
        ),
    },
    {
        "key": "Exposure_relative",
        "label": "Exposure half — share of the municipal population within 10 km",
        "short_label": "Exposure (share)",
        "unit": "0–1",
        "stage": "component",
        "group": "Exposure",
        "actual_field": "derived:pop_10km/pop_municipality",
        "description": (
            "How coastal the municipality is rather than how many people it "
            "holds. A hamlet entirely on the shore and a city entirely on the "
            "shore both reach 1, which is why it is paired with the absolute "
            "half instead of used alone."
        ),
    },
    {
        "key": "Hazard_Index",
        "label": "Multimetric compound-event hazard",
        "short_label": "Hazard Index",
        "unit": "0–1",
        "stage": "normalized",
        "group": "Physical hazard",
        "actual_field": "transferred:norm_native(Hazard_Index_raw)",
        "description": (
            "The Hazard Index normalized on the 808-point native ocean grid "
            "and transferred to the municipality without renormalization. "
            "Because the most hazardous grid point is not associated with any "
            "municipality, the municipal maximum is below 1."
        ),
    },
    {
        "key": "Hazard_Index_raw",
        "label": "Hazard components mean (before normalization)",
        "short_label": "Hazard (raw)",
        "unit": "dimensionless mean",
        "stage": "raw",
        "group": "Physical hazard",
        "actual_field": "transferred:mean(Hazard_Frequency,Hazard_Severity)",
        "description": (
            "The equal-weight mean of the three normalized components, before "
            "the final Min-Max step. It spans a narrow interval, which is "
            "exactly why the second normalization is applied."
        ),
    },
    {
        "key": "Hazard_Index_mun",
        "label": "Hazard rescaled over the municipalities",
        "short_label": "Hazard (municipal)",
        "unit": "0–1",
        "stage": "normalized",
        "group": "Physical hazard",
        "actual_field": "derived:norm_municipal(Hazard_Index)",
        "description": (
            "The transferred Hazard Index rescaled to span [0,1] across the "
            "municipalities. This is the field that enters the risk product: on "
            "the native-grid scale the municipal maximum is 0.829, because the "
            "most hazardous ocean point serves no municipality, and using it "
            "inside a product would silently down-weight the hazard against the "
            "other two components."
        ),
    },
    {
        "key": "Hazard_Frequency",
        "label": "Normalized compound-event frequency",
        "short_label": "Frequency",
        "unit": "0–1",
        "stage": "component",
        "group": "Physical hazard",
        "actual_field": "transferred:norm_native(compound_count_total)",
        "description": (
            "Compound-event count over 1993-2025, Min-Max normalized across "
            "the native ocean grid."
        ),
    },
    {
        "key": "Hazard_Severity",
        "label": "Normalized compound-event duration",
        "short_label": "Duration",
        "unit": "0–1",
        "stage": "component",
        "group": "Physical hazard",
        "actual_field": "transferred:norm_native(mean_integrated_severity)",
        "description": (
            "Mean overlap duration, Min-Max normalized across the native "
            "ocean grid."
        ),
    },
    {
        "key": "mean_overlap_duration",
        "label": "Normalized compound-event intensity",
        "short_label": "Intensity",
        "unit": "0–1",
        "stage": "component",
        "group": "Physical hazard",
        "actual_field": "transferred:mean_overlap_duration (diagnostic, not an index component)",
        "description": (
            "Mean compound intensity, Min-Max normalized across the native "
            "ocean grid."
        ),
    },
    {
        "key": "SVI_Coast_2022",
        "label": "Social Vulnerability Index",
        "short_label": "SVI",
        "unit": "0–100",
        "stage": "input",
        "group": "Social vulnerability",
        "actual_field": "SVI_Coast_2022",
        "description": (
            "Ten IBGE/SIDRA 2022 socioeconomic and infrastructure variables "
            "standardized, reduced by PCA, sign-adjusted so higher means more "
            "vulnerable, and normalized to 0-100."
        ),
    },
)

FIXED_BOUNDARIES: dict[str, list[float]] = {
    "Risk_Hazard": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
    "Hazard_Index": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
    "Hazard_Frequency": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
    "Hazard_Severity": [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0],
    "SVI_Coast_2022": [0.0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5, 100.0],
}


def _current_available_layers(export: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for definition in CURRENT_LAYER_DEFINITIONS:
        key = definition["key"]
        if key not in export:
            continue
        boundaries = FIXED_BOUNDARIES.get(key) or _nice_boundaries(export[key])
        span = abs(boundaries[-1] - boundaries[0])
        layers.append(
            {
                **definition,
                "decimals": 0 if span >= 10 else 2 if span >= 1 else 3,
                "boundaries": boundaries,
                "colors": risk_colors(min(len(boundaries) - 1, 8)),
                "palette": "risk",
                "palette_source": (
                    "green-to-red palette of the article "
                    "hazard/vulnerability/risk figure"
                ),
                "stats": _numeric_stats(export[key]),
            }
        )
    return layers


def _derive_current_scope(
    base_export: gpd.GeoDataFrame,
    native_hazard: pd.DataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    missing_required = [
        key
        for key in (
            "compound_c",
            "SVI_Coast_2022",
            "grid_lat",
            "grid_lon",
        )
        if key not in base_export
    ]
    if missing_required:
        raise ValueError(
            "Cannot derive the municipal risk product. Missing required field(s): "
            + ", ".join(missing_required)
        )

    export = base_export.copy()
    svi_fraction = export["SVI_Coast_2022"].astype(float) / 100.0

    native_lookup = native_hazard.copy()
    native_lookup["_lat_key"] = native_lookup["grid_lat"].round(6)
    native_lookup["_lon_key"] = native_lookup["grid_lon"].round(6)
    native_lookup = native_lookup.set_index(["_lat_key", "_lon_key"])
    municipality_keys = pd.MultiIndex.from_arrays(
        [
            pd.to_numeric(export["grid_lat"], errors="coerce").round(6),
            pd.to_numeric(export["grid_lon"], errors="coerce").round(6),
        ],
        names=["_lat_key", "_lon_key"],
    )
    transfer_fields = (
        "Hazard_Frequency",
        "Hazard_Severity",
        "Hazard_Index_raw",
        "Hazard_Index",
    )
    transferred = native_lookup.loc[:, list(transfer_fields)].reindex(
        municipality_keys
    )
    transferred.index = export.index
    for field in transfer_fields:
        export[field] = transferred[field].map(_to_jsonable)

    hazard = pd.to_numeric(export["Hazard_Index"], errors="coerce")

    # ``Hazard_Index`` deliberately keeps the native-grid scale: the most
    # hazardous of the 808 ocean points serves no municipality, so the municipal
    # maximum stays below 1 (see SCIENTIFIC_NOTES, 2026-07-27). That scale is
    # the right one for reading the municipal layer against the coastal field,
    # but it gives the hazard a narrower amplitude than SVI/100 in any
    # equal-weight aggregation, which silently down-weights it.
    # ``Hazard_Index_mun`` is the same field rescaled to [0,1] over the
    # municipalities. The risk product needs the three components to span
    # comparable amplitudes; the native-grid scale would silently down-weight
    # the hazard, since it reaches only 0.829 across municipalities.
    hazard_mun = _minmax(hazard)
    export["Hazard_Index_mun"] = hazard_mun.map(_to_jsonable)

    # Exposure. See src/04_risk_integration/exposure_index.py for the rationale
    # and for the three candidates that were rejected.
    population = pd.to_numeric(export[EXPOSURE_FIELD], errors="coerce")
    municipal_population = pd.to_numeric(export["pop_municipality"], errors="coerce")
    exposure = exposure_inform(population, municipal_population)
    export["Exposure_Index"] = exposure.map(_to_jsonable)
    export["Exposure_absolute"] = exposure_absolute(population).map(_to_jsonable)
    export["Exposure_relative"] = exposure_relative(
        population, municipal_population
    ).map(_to_jsonable)

    # Conjunctive risk: the geometric mean preserves the property the IPCC
    # framework implies, that risk needs all three to be present. An arithmetic
    # mean would let a large population compensate for the absence of a physical
    # driver. Components are floored at CLIP_FLOOR first, so that a municipality
    # sitting at the bottom of a Min--Max scale is not handed zero risk as a
    # scaling artefact — Balneário Camboriú is exactly at SVI = 0.
    floor = lambda series: series.clip(lower=CLIP_FLOOR, upper=1.0)  # noqa: E731
    risk_raw = (
        floor(hazard_mun) * floor(exposure) * floor(svi_fraction)
    ) ** (1.0 / 3.0)
    risk = _minmax(risk_raw)

    export["Risk_Hazard_raw"] = risk_raw.map(_to_jsonable)
    export["Risk_Hazard"] = risk.map(_to_jsonable)
    transfer_metadata = {
        "method": (
            "Exact lookup by grid_lat/grid_lon rounded to 6 decimals from the "
            "native-grid Hazard Index to each municipality's pre-associated "
            "ocean point"
        ),
        "municipality_feature_count": int(len(export)),
        "matched_hazard_count": int(hazard.notna().sum()),
        "missing_hazard_count": int(hazard.isna().sum()),
        # ``_to_jsonable`` maps non-finite values to None; without it the
        # records carry NaN, which json.dump would emit as the literal ``NaN``
        # and JSON.parse in the browser rejects.
        "missing_municipalities": [
            {key: _to_jsonable(value) for key, value in record.items()}
            for record in export.loc[
                hazard.isna(),
                ["municipality_name", "state", "grid_lat", "grid_lon"],
            ].to_dict(orient="records")
        ],
    }
    return export, transfer_metadata


def build_site_risk_data() -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
    # The delivered shapefile is the only accepted source. Reading a previously
    # exported GeoJSON instead used to keep the exporter running when the
    # shapefile was absent, but it silently re-simplified already simplified
    # geometry and could publish a product built from a stale export. A missing
    # or incomplete source must fail here rather than produce plausible output.
    _require_source_files()
    source_path = SOURCE_FILE
    source_info = pyogrio.read_info(SOURCE_FILE)
    source_fields = list(source_info["fields"])

    layer_field_map: dict[str, str] = {}
    for spec in SOURCE_LAYER_SPECS:
        field = _resolve_field(source_fields, spec.candidates)
        if field is None:
            raise ValueError(
                f"The delivered shapefile has no column for {spec.key!r}. "
                "Checked candidates: "
                + json.dumps(list(spec.candidates))
                + f". Columns present: {json.dumps(source_fields)}"
            )
        layer_field_map[spec.key] = field

    support_field_map = {
        key: field
        for key, candidates in SUPPORT_FIELD_CANDIDATES.items()
        if (field := _resolve_field(source_fields, (key, *candidates))) is not None
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

    base_export = gpd.GeoDataFrame(geometry=gdf.geometry, crs=OUTPUT_CRS)
    for key, field in support_field_map.items():
        base_export[key] = gdf[field].map(_to_jsonable)
    for spec in SOURCE_LAYER_SPECS:
        base_export[spec.key] = gdf[layer_field_map[spec.key]].map(_to_jsonable)

    # The IBGE boundary layer and the SIDRA table spell the same attributes
    # differently; fill the title-case name/state from the uppercase columns when
    # a row carries only the latter.
    if "municipality_name" in base_export and "municipio" in gdf:
        base_export["municipality_name"] = base_export["municipality_name"].fillna(gdf["municipio"].map(_to_jsonable))
    if "state" in base_export and "uf" in gdf:
        base_export["state"] = base_export["state"].fillna(gdf["uf"].map(_to_jsonable))

    exposure_counts = _require_exposure()
    codes = base_export["municipality_code"].astype(str)
    lookup = exposure_counts.set_index("municipality_code")
    for column in (EXPOSURE_FIELD, "pop_municipality"):
        base_export[column] = codes.map(lookup[column])
    unmatched = int(base_export[EXPOSURE_FIELD].isna().sum())
    if unmatched:
        raise ValueError(
            f"{unmatched} municipalities have no exposure count. The delivered "
            "municipal file and outputs/exposure/municipal_exposure.csv must "
            "describe the same set."
        )

    common_metadata: dict[str, Any] = {
        "generated_by": "src.site.export_risk_index_data",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source_path.relative_to(ROOT)),
        "source_mode": "original_shapefile",
        "upstream_source_path": str(SOURCE_FILE.relative_to(ROOT)),
        "source_components": _source_components(),
        "source_crs": source_crs,
        "output_crs": OUTPUT_CRS,
        "source_feature_count": int(source_info["features"]),
        "feature_count": int(len(base_export)),
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

    native_hazard, native_hazard_metadata = _derive_native_hazard_index()
    current_export, hazard_transfer_metadata = _derive_current_scope(
        base_export,
        native_hazard,
    )
    current_numeric_stats = {
        key: _numeric_stats(current_export[key])
        for key in (
            "SVI_Coast_2022",
            "Hazard_Frequency",
            "Hazard_Severity",
            "Hazard_Index_raw",
            "Hazard_Index",
            "Hazard_Index_mun",
            "Exposure_Index",
            "Exposure_absolute",
            "Exposure_relative",
            EXPOSURE_FIELD,
            "pop_municipality",
            "Risk_Hazard",
            "Risk_Hazard_raw",
            "compound_c",
            "mean_overl",
            "mean_compo",
        )
        if key in current_export
    }
    current_metadata: dict[str, Any] = {
        **common_metadata,
        "scope": "normalized_multimetric_native_grid",
        "map_extent": list(COASTAL_MAP_EXTENT),
        "basemap": "site/public/data/coastal_basemap.geojson",
        "audit_fields": {
            "note": (
                "Present in the GeoJSON properties for reproducibility but not "
                "offered as map layers on the website."
            ),
            "fields": [EXPOSURE_FIELD, "pop_municipality"],
        },
        "available_layers": _current_available_layers(current_export),
        "missing_expected_layers": [
            key
            for key in (
                "SVI_Coast_2022",
                "compound_c",
                "mean_overl",
                "mean_compo",
                "grid_lat",
                "grid_lon",
            )
            if key not in current_export
        ],
        "field_aliases": {
            "layers": {
                "SVI_Coast_2022": layer_field_map.get("SVI_Coast_2022"),
                "Hazard_Frequency": (
                    "transferred:norm_native(compound_count_total)"
                ),
                "Hazard_Severity": (
                    "transferred:norm_native(mean_integrated_severity)"
                ),

                "Hazard_Index_raw": (
                    "transferred:mean(Hazard_Frequency,Hazard_Severity)"
                ),
                "Hazard_Index": (
                    "transferred:norm_native(Hazard_Index_raw)"
                ),
                "Hazard_Index_mun": (
                    "derived:norm_municipal(Hazard_Index)"
                ),
                "Exposure_Index": (
                    "derived:geomean(goalposts(log10(pop_10km),1e2,1e6),"
                    "pop_10km/pop_municipality)"
                ),
                "Risk_Hazard_raw": (
                    "derived:(Hazard_Index_mun*Exposure_Index*"
                    "SVI_Coast_2022/100)^(1/3)"
                ),
                "Risk_Hazard": "derived:norm_municipal(Risk_Hazard_raw)",
            },
            "support": support_field_map,
        },
        "numeric_stats": current_numeric_stats,
        "native_hazard_index": native_hazard_metadata,
        "hazard_transfer": hazard_transfer_metadata,
        "hazard_index_normalization": {
            "method": "Min-Max after equal-weight component aggregation",
            "population": "all finite native ocean grid points",
            "input_field": "Hazard_Index_raw",
            "input_stats": native_hazard_metadata["numeric_stats"][
                "Hazard_Index_raw"
            ],
            "output_field": "Hazard_Index",
            "output_range": [0.0, 1.0],
            "formula": (
                "(Hazard_Index_raw - min(Hazard_Index_raw)) / "
                "(max(Hazard_Index_raw) - min(Hazard_Index_raw))"
            ),
        },
        "municipal_hazard_renormalization": {
            "method": "Min-Max over the municipalities",
            "purpose": (
                "Provide a hazard component whose amplitude matches SVI/100 "
                "for equal-weight aggregations. Used as the hazard factor of "
                "Risk_Hazard_raw; see integrated_risk_formula."
            ),
            "population": (
                "Brazilian coastal municipalities with a finite transferred "
                "Hazard_Index"
            ),
            "input_field": "Hazard_Index",
            "input_stats": _numeric_stats(current_export["Hazard_Index"]),
            "output_field": "Hazard_Index_mun",
            "output_range": [0.0, 1.0],
            "formula": (
                "(Hazard_Index - min(Hazard_Index)) / "
                "(max(Hazard_Index) - min(Hazard_Index))"
            ),
        },
        "integrated_risk_formula": {
            "expression": (
                "Risk_Hazard_raw = (clip(Hazard_Index_mun) * clip(Exposure_Index) "
                "* clip(SVI_Coast_2022/100)) ** (1/3)"
            ),
            "aggregation": "geometric mean of three components",
            "clip_floor": CLIP_FLOOR,
            "rationale": (
                "Conjunctive: the IPCC framework defines risk as emerging from "
                "the interaction of hazard, exposure and vulnerability, which "
                "implies that the absence of any one of them removes the "
                "potential for adverse consequences. An arithmetic mean would "
                "allow a large population to compensate for the absence of a "
                "physical driver. The floor prevents a municipality at the "
                "bottom of a Min-Max scale from receiving zero risk as a "
                "scaling artefact."
            ),
            "superseded": "norm_municipal((SVI_Coast_2022/100) * Hazard_Index)",
        },
        "integrated_risk_normalization": {
            "method": "Min-Max",
            "population": (
                "Brazilian coastal municipalities with finite SVI_Coast_2022, "
                "Hazard_Index and Exposure_Index"
            ),
            "input_field": "Risk_Hazard_raw",
            "input_stats": _numeric_stats(current_export["Risk_Hazard_raw"]),
            "output_field": "Risk_Hazard",
            "output_range": [0.0, 1.0],
            "formula": (
                "(Risk_Hazard_raw - min(Risk_Hazard_raw)) / "
                "(max(Risk_Hazard_raw) - min(Risk_Hazard_raw))"
            ),
        },
        "methodology": {
            "SVI_Coast_2022": "IBGE/SIDRA 2022 socioeconomic and infrastructure variables standardized with StandardScaler, submitted to PCA, PC1 sign-adjusted so higher values mean higher vulnerability, then normalized 0-100.",
            "exposure": (
                "The Hazard Index is calculated first on all 808 native ocean "
                "grid points. Each municipality receives the value at its "
                "pre-associated grid point, selected by the existing spatial "
                "association workflow."
            ),
            "Hazard_Frequency": (
                "Min-Max normalization across the native grid of "
                "compound_count_total."
            ),
            "Hazard_Severity": (
                "Min-Max normalization across the native grid of "
                "mean_integrated_severity: the compound severity summed over "
                "the days on which all detection criteria hold, so magnitude "
                "and persistence enter as one quantity."
            ),
            "mean_overlap_duration": (
                "Published diagnostic only. Retired from the hazard index in "
                "2026-07-29 (AUD-06): it measured the coincidence of two "
                "percentile tests, was discretised into whole days, and "
                "anticorrelated with frequency."
            ),
            "Hazard_Index_raw": (
                "Equal-weight mean of Hazard_Frequency and Hazard_Severity."
            ),
            "Hazard_Index": (
                "Min-Max normalization to [0,1] of Hazard_Index_raw across "
                "the 808 native ocean grid points, transferred without "
                "renormalization to municipalities."
            ),
            "Hazard_Index_mun": (
                "Min-Max renormalization of the transferred Hazard_Index over "
                "the municipalities, so that the hazard spans [0,1] like "
                "SVI/100 for equal-weight aggregations. Used as the hazard "
                "factor of Risk_Hazard_raw."
            ),
            "Exposure_Index": (
                "Resident population within 10 km of the coastline (IBGE Grade "
                "Estatistica 2022, 200 m urban / 1 km rural cells) on a log "
                f"scale between fixed goalposts of {GOALPOST_MIN_INHABITANTS:,.0f} "
                f"and {GOALPOST_MAX_INHABITANTS:,.0f} inhabitants, combined by "
                "geometric mean with the share of the municipal population "
                "inside the band. Proximity, not modelled inundation."
            ),
            "Risk_Hazard_raw": (
                "Geometric mean of Hazard_Index_mun, Exposure_Index and "
                f"SVI_Coast_2022/100, each floored at {CLIP_FLOOR}."
            ),
            "Risk_Hazard": (
                "Min-Max normalization to [0,1] of Risk_Hazard_raw across "
                "municipalities with finite SVI and hazard values."
            ),
        },
    }
    return current_export, current_metadata


def save_site_risk_data(
    current_gdf: gpd.GeoDataFrame,
    current_metadata: dict[str, Any],
) -> None:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    current_gdf.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    # allow_nan=False keeps NaN/Infinity out of the payload: they are valid
    # Python but invalid JSON, and would break JSON.parse on the website.
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(
            current_metadata,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        f.write("\n")
    print(f"Saved: {OUTPUT_GEOJSON} ({OUTPUT_GEOJSON.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Saved: {OUTPUT_METADATA} ({OUTPUT_METADATA.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    current_gdf, current_metadata = build_site_risk_data()
    save_site_risk_data(current_gdf, current_metadata)
    print("Layer definitions:")
    for layer in current_metadata["available_layers"]:
        print(f"  {layer['key']} <- {layer['actual_field']} ({layer['stats']['count']} values)")
    if current_metadata["missing_expected_layers"]:
        print("Missing expected layers:", ", ".join(current_metadata["missing_expected_layers"]))


if __name__ == "__main__":
    main()
