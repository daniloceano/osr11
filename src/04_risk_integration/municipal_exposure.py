"""Municipal population exposure from the IBGE Grade Estatistica 2022.

Computes, for every coastal municipality of the study, the resident population
and the occupied households located within a set of distance bands of the
coastline. The 10 km band is the one intended for the exposure component of the
risk index; the others exist so the choice of band can be shown to matter, or
not, in a sensitivity analysis.

What this is, and what it is not
--------------------------------
This is a **proximity** criterion, not an inundation extent. No water level is
propagated over land anywhere in this workflow, so the result is the population
*residing near the coast*, never the population *affected*. The manuscript must
say so explicitly.

Two further limits are inherent to the inputs. The census counts residents on
2022-07-31, a single instant against 33 years of metocean record, and it counts
them *de jure*: the seasonal population of the resort municipalities of the
South and Southeast is invisible here. And the grid cell is 200 m in urban
census tracts but 1 km in rural ones, so the spatial support is not uniform.

Method
------
Cells are attributed by their centroid: a cell counts for the municipality that
contains its centroid, and for a distance band when its centroid falls within
that distance of the coastline. Centroid attribution keeps the totals additive —
no cell is split between two municipalities or double counted at a boundary —
at the cost of a discretisation error bounded by half a cell diagonal.

Distances are measured in EPSG:5880 (SIRGAS 2000 / Brazil Polyconic), the same
metric projection the coastal projection of the Hazard Index uses.

Inputs
------
    data/raw/ibge/grade_estatistica_2022/grade_id*.zip   (20 quadrant tiles)
    outputs/risk_index/risk_index.shp                    (municipal geometry)
    data/ne_10m_coastline/ne_10m_coastline.shp

Output
------
    outputs/exposure/municipal_exposure.csv
    outputs/exposure/municipal_exposure_metadata.json

Run
---
    python -m src.risk_integration.municipal_exposure
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

GRID_DIR = ROOT / "data" / "raw" / "ibge" / "grade_estatistica_2022"
MUNICIPALITY_SOURCE = ROOT / "outputs" / "risk_index" / "risk_index.shp"
COASTLINE_SOURCE = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"

OUTPUT_DIR = ROOT / "outputs" / "exposure"
OUTPUT_CSV = OUTPUT_DIR / "municipal_exposure.csv"
OUTPUT_METADATA = OUTPUT_DIR / "municipal_exposure_metadata.json"

METRIC_CRS = "EPSG:5880"
#: Bands in kilometres. 10 km is the exposure criterion; the rest are the
#: sensitivity ladder.
DISTANCE_BANDS_KM = (1.0, 2.0, 5.0, 10.0)
#: Field that identifies the coastal municipalities inside the national layer.
MUNICIPALITY_FILTER_FIELD = "SVI_Coast_"
COASTLINE_CLIP = (-56.0, -36.5, -27.0, 7.0)


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_municipalities() -> gpd.GeoDataFrame:
    """Coastal municipalities, at full geometric resolution, in METRIC_CRS."""
    if not MUNICIPALITY_SOURCE.exists():
        raise FileNotFoundError(
            f"{MUNICIPALITY_SOURCE} is required for the municipal geometry. "
            "It is the externally delivered file; there is no fallback."
        )
    layer = gpd.read_file(
        MUNICIPALITY_SOURCE,
        columns=["CD_MUN", "NM_MUN", "SIGLA_UF", MUNICIPALITY_FILTER_FIELD],
    )
    coastal = layer[layer[MUNICIPALITY_FILTER_FIELD].notna()].copy()
    if coastal.empty:
        raise RuntimeError(
            f"No feature carries {MUNICIPALITY_FILTER_FIELD}; the delivered "
            "layer is not the expected one"
        )
    coastal = coastal.rename(
        columns={
            "CD_MUN": "municipality_code",
            "NM_MUN": "municipality_name",
            "SIGLA_UF": "state",
        }
    ).drop(columns=[MUNICIPALITY_FILTER_FIELD])
    coastal["municipality_code"] = coastal["municipality_code"].astype(str)
    return coastal.to_crs(METRIC_CRS)


def load_coastline() -> Any:
    """Natural Earth coastline clipped to the study window, in METRIC_CRS."""
    if not COASTLINE_SOURCE.exists():
        raise FileNotFoundError(COASTLINE_SOURCE)
    layer = gpd.read_file(COASTLINE_SOURCE)
    window = layer.cx[
        COASTLINE_CLIP[0]:COASTLINE_CLIP[2],
        COASTLINE_CLIP[1]:COASTLINE_CLIP[3],
    ]
    if window.empty:
        raise RuntimeError("The coastline clip window selected no geometry")
    return window.to_crs(METRIC_CRS).geometry.union_all()


def tile_paths() -> list[Path]:
    paths = sorted(GRID_DIR.glob("grade_id*.zip"))
    if not paths:
        raise FileNotFoundError(
            f"No grid tile found in {GRID_DIR}. Run "
            "src.acquisition.download_ibge_grade first."
        )
    return paths


def accumulate_tile(
    tile: Path,
    municipalities: gpd.GeoDataFrame,
    coastline: Any,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Aggregate one tile to municipality x distance band.

    Returns the partial totals and the cell counts used for quality control.
    """
    cells = gpd.read_file(f"zip://{tile}", columns=["ID_UNICO", "TOTAL", "TOTAL_DOM"])
    stats = {"cells_read": int(len(cells))}
    cells = cells[(cells["TOTAL"] > 0) | (cells["TOTAL_DOM"] > 0)]
    stats["cells_populated"] = int(len(cells))
    if cells.empty:
        return pd.DataFrame(), stats

    cells = cells.to_crs(METRIC_CRS)
    # Cell size is recoverable from the identifier prefix and is carried through
    # so the mix of 200 m and 1 km supports stays auditable.
    cell_size_m = cells["ID_UNICO"].str.startswith("200M").map({True: 200, False: 1000})
    centroids = gpd.GeoDataFrame(
        {
            "TOTAL": cells["TOTAL"].to_numpy(),
            "TOTAL_DOM": cells["TOTAL_DOM"].to_numpy(),
            "cell_size_m": cell_size_m.to_numpy(),
        },
        geometry=cells.geometry.centroid.to_numpy(),
        crs=METRIC_CRS,
    )
    centroids["distance_km"] = centroids.geometry.distance(coastline) / 1_000.0

    joined = gpd.sjoin(
        centroids,
        municipalities[["municipality_code", "geometry"]],
        how="inner",
        predicate="within",
    )
    stats["cells_in_municipalities"] = int(len(joined))
    if joined.empty:
        return pd.DataFrame(), stats

    frames = []
    for band in DISTANCE_BANDS_KM:
        inside = joined[joined["distance_km"] <= band]
        if inside.empty:
            continue
        totals = (
            inside.groupby("municipality_code")[["TOTAL", "TOTAL_DOM"]]
            .sum()
            .rename(columns={"TOTAL": "population", "TOTAL_DOM": "households"})
        )
        totals["band_km"] = band
        frames.append(totals.reset_index())

    municipal_total = (
        joined.groupby("municipality_code")[["TOTAL", "TOTAL_DOM"]]
        .sum()
        .rename(columns={"TOTAL": "population", "TOTAL_DOM": "households"})
    )
    municipal_total["band_km"] = 0.0  # 0 means "whole municipality"
    frames.append(municipal_total.reset_index())

    return pd.concat(frames, ignore_index=True), stats


def build_exposure() -> tuple[pd.DataFrame, dict[str, Any]]:
    municipalities = load_municipalities()
    coastline = load_coastline()
    tiles = tile_paths()

    partials: list[pd.DataFrame] = []
    tile_stats: dict[str, dict[str, int]] = {}
    for tile in tiles:
        frame, stats = accumulate_tile(tile, municipalities, coastline)
        tile_stats[tile.name] = stats
        if not frame.empty:
            partials.append(frame)
        print(
            f"  {tile.name}: {stats['cells_populated']:>8,} populated cells, "
            f"{stats.get('cells_in_municipalities', 0):>8,} inside municipalities"
        )

    if not partials:
        raise RuntimeError("No tile contributed any populated cell")

    stacked = (
        pd.concat(partials, ignore_index=True)
        .groupby(["municipality_code", "band_km"], as_index=False)[
            ["population", "households"]
        ]
        .sum()
    )

    wide = municipalities[
        ["municipality_code", "municipality_name", "state"]
    ].copy()
    for band in (0.0, *DISTANCE_BANDS_KM):
        suffix = "municipality" if band == 0.0 else f"{band:g}km"
        slice_ = stacked[stacked["band_km"] == band].set_index("municipality_code")
        for source, label in (("population", "pop"), ("households", "dom")):
            wide[f"{label}_{suffix}"] = (
                wide["municipality_code"].map(slice_[source]).fillna(0).astype("int64")
            )

    metadata = {
        "generated_by": "src.risk_integration.municipal_exposure",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "grid_source": _relative(GRID_DIR),
        "grid_provenance": "data/metadata/ibge_grade_estatistica_2022_download.json",
        "municipality_source": _relative(MUNICIPALITY_SOURCE),
        "coastline_source": _relative(COASTLINE_SOURCE),
        "metric_crs": METRIC_CRS,
        "distance_bands_km": list(DISTANCE_BANDS_KM),
        "attribution": (
            "Cell centroid: a cell counts for the municipality containing its "
            "centroid and for a band when its centroid is within that distance "
            "of the coastline. Totals are additive; the discretisation error is "
            "bounded by half a cell diagonal (141 m for 200 m cells, 707 m for "
            "1 km cells)."
        ),
        "interpretation": (
            "Proximity, not modelled inundation. Resident (de jure) population "
            "on 2022-07-31; seasonal population is not represented."
        ),
        "municipality_count": int(len(wide)),
        "tile_count": len(tiles),
        "tiles": tile_stats,
        "totals": {
            column: int(wide[column].sum())
            for column in wide.columns
            if column.startswith(("pop_", "dom_"))
        },
    }
    return wide, metadata


def main() -> None:
    print(f"Municipal exposure from {GRID_DIR.name}")
    exposure, metadata = build_exposure()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exposure.to_csv(OUTPUT_CSV, index=False)
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"\n{len(exposure)} municipalities -> {_relative(OUTPUT_CSV)}")
    for column, value in metadata["totals"].items():
        print(f"  {column:22s} {value:>12,}")


if __name__ == "__main__":
    main()
