"""Shared inputs and utilities for the article calibration figures."""
from __future__ import annotations

import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.figures_article.make_article_risk_figures import (  # noqa: E402
    COASTLINE_SHP,
    CURRENT_RISK_GEOJSON,
    METADATA_DIR,
    _relative,
)

MUNICIPALITIES_GEOJSON = CURRENT_RISK_GEOJSON
SCORE_DATA = ROOT / "site/public/data/tc5_score_decomposition.json"
GRID_REFERENCE = ROOT / "outputs/preprocessing/municipality_grid_ref.csv"
EXPANDED_EVENTS = ROOT / "data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv"
LEGACY_EVENTS = ROOT / "data/reported events/reported_events_Karine_sc.csv"

SECTOR_ORDER = ("North", "Central-north", "Central", "Central-south", "South")
# The legacy event table contains conflicting historical labels for Garopaba.
# Use the study's canonical municipality-level classification in article maps.
SECTOR_OVERRIDES = {"garopaba": "Central-south"}


def normalise_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.casefold().strip().split())


def load_score_frame() -> pd.DataFrame:
    with SCORE_DATA.open(encoding="utf-8") as handle:
        frame = pd.DataFrame(json.load(handle))
    required = {"hs_percentile", "ssh_percentile", "R_pos", "B", "term_fsoft_raw", "Score"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing score-decomposition fields: {sorted(missing)}")
    return frame


def study_municipalities() -> pd.DataFrame:
    expanded = pd.read_csv(EXPANDED_EVENTS, usecols=["city", "coastal_sector"]).rename(
        columns={"city": "municipality", "coastal_sector": "sector"}
    )
    legacy = pd.read_csv(LEGACY_EVENTS, usecols=["Municipalities", "Coastal Sectors"]).rename(
        columns={"Municipalities": "municipality", "Coastal Sectors": "sector"}
    )
    events = pd.concat([expanded, legacy], ignore_index=True).dropna()
    events["name_key"] = events["municipality"].map(normalise_name)
    events["sector"] = events["sector"].astype(str).str.strip()
    for name_key, sector in SECTOR_OVERRIDES.items():
        events.loc[events["name_key"] == name_key, "sector"] = sector
    conflicts = events.groupby("name_key")["sector"].nunique()
    if (conflicts > 1).any():
        names = conflicts[conflicts > 1].index.tolist()
        raise ValueError(f"Conflicting coastal sectors for municipalities: {names}")
    return events.drop_duplicates("name_key")[["name_key", "municipality", "sector"]]


def load_map_data() -> tuple[gpd.GeoDataFrame, pd.DataFrame, gpd.GeoDataFrame]:
    study = study_municipalities()
    brazil_municipalities = gpd.read_file(MUNICIPALITIES_GEOJSON).to_crs("EPSG:4326")
    municipalities = brazil_municipalities[brazil_municipalities["state"] == "SC"].copy()
    municipalities["name_key"] = municipalities["municipality_name"].map(normalise_name)
    municipalities.loc[municipalities["name_key"] == "icara", "name_key"] = "icara/balneario rincao"
    municipalities = municipalities.merge(study, on="name_key", how="inner")

    grid = pd.read_csv(GRID_REFERENCE)
    grid["name_key"] = grid["municipality"].map(normalise_name)
    grid = grid.merge(study[["name_key", "sector"]], on="name_key", how="inner")
    grid = grid.dropna(subset=["grid_lat", "grid_lon"])
    return municipalities, grid, brazil_municipalities


def write_combined_summary(
    heatmap_outputs: list[str],
    map_outputs: list[str],
    heatmap_color_logic: dict[str, object],
) -> Path:
    """Preserve the legacy combined-entry-point metadata contract."""
    municipalities, grid, _ = load_map_data()
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {
            "pu_composite_calibration_heatmaps": heatmap_outputs,
            "santa_catarina_study_area_and_grid_points": map_outputs,
        },
        "inputs": {
            "score_decomposition": _relative(SCORE_DATA),
            "municipality_polygons": _relative(MUNICIPALITIES_GEOJSON),
            "municipality_grid_reference": _relative(GRID_REFERENCE),
            "expanded_events": _relative(EXPANDED_EVENTS),
            "legacy_events": _relative(LEGACY_EVENTS),
            "coastline_reference": _relative(COASTLINE_SHP),
            "coastline_geometry": _relative(MUNICIPALITIES_GEOJSON),
        },
        "heatmap_color_logic": heatmap_color_logic,
        "map_counts": {
            "study_municipalities": int(len(municipalities)),
            "associated_municipalities": int(grid["name_key"].nunique()),
            "unique_grid_points": int(len(grid.drop_duplicates(["grid_lat", "grid_lon"]))),
        },
        "map_geometry": {
            "coastline_method": (
                "Municipal-polygon boundary classified by a 2 km buffer around the "
                "Natural Earth 10 m coastline reference"
            ),
            "coastline_alignment": "Exact subset of municipal-polygon boundary",
            "state_boundary_method": "Shared SC/PR and SC/RS municipal-polygon edges",
            "land_mask_method": (
                "Regional Natural Earth 10 m land polygon with its near-coast edge "
                "replaced by the SC municipal geometry"
            ),
            "land_color": "#D8D8D4",
            "ocean_color": "#EAF3F8",
        },
    }
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    path = METADATA_DIR / "article_calibration_figure_summary.json"
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
