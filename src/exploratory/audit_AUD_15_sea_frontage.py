"""AUD-15 diagnostic: does the delivered municipal set follow sea frontage, and
which municipalities have none?

Two criteria of AUD-15 have stood unverified since the record was created: the
membership criterion of the coastal set is inherited from a PDF and is not
reconstructible from this repository, and no classification of which
municipalities actually front the sea exists. The record asks for the latter
because separating a municipality like Santa Rita/MA -- 4 residents within 10 km,
hazard point 77 km away -- on the grounds of low `pop_10km` would be circular:
it would use the variable being measured. A geometric criterion is needed.

This screens all 282 municipalities of the delivered set against the Natural
Earth 10 m coastline, the only coastline held in this repository. That dataset is
generalised at roughly 1:10 000 000 and **cannot support a definitive frontage
classification**: it reports no intersection for 25 municipalities, nearly all of
them unambiguously coastal -- Olinda, Itajaí and Navegantes among them -- every
one within 700 m of the drawn line. The screening is therefore reported as what
it is, and its one unambiguous result is the single case that stands an order of
magnitude apart from every other.

That case decides a criterion the record left pending, and it also corrects one:
Santa Rita/MA, which the record suspects of not being coastal "in any useful
sense", carries 1.98 km of measured frontage. Its problem is exposure and hazard
association, not membership.

Geometry is read from the delivered shapefile rather than the published GeoJSON,
whose polygons are simplified for the web map.

Usage:
    python -m src.exploratory.audit_AUD_15_sea_frontage

Output:
    outputs/audit/AUD-15_sea_frontage/frontage_by_municipality.csv
    outputs/audit/AUD-15_sea_frontage/no_frontage_candidates.csv
    outputs/audit/AUD-15_sea_frontage/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
#: Delivered source geometry, not the web-simplified GeoJSON. The published
#: GeoJSON is simplified for the map and neighbouring polygons overlap by up to
#: 0.14 km², which is enough to break adjacency tests and to shift frontage.
SHAPEFILE = ROOT / "outputs" / "risk_index" / "risk_index.shp"
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
COASTLINE = ROOT / "data" / "ne_10m_coastline" / "ne_10m_coastline.shp"
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-15_sea_frontage"

#: Field that defines membership of the coastal set in the delivered shapefile.
MEMBERSHIP_FIELD = "SVI_Coast_"

#: Brazil Polyconic. Already the metric CRS used elsewhere in this repository.
METRIC_CRS = 5880
#: Margin in degrees around the municipal bounding box when clipping the coastline.
CLIP_MARGIN_DEG = 2.0


def load_layers() -> tuple[gpd.GeoDataFrame, gpd.GeoSeries]:
    delivered = gpd.read_file(SHAPEFILE)
    municipalities = delivered[delivered[MEMBERSHIP_FIELD].notna()].reset_index(
        drop=True
    )
    coastline = gpd.read_file(COASTLINE)
    minx, miny, maxx, maxy = municipalities.to_crs(4326).total_bounds
    clipped = coastline.cx[
        minx - CLIP_MARGIN_DEG : maxx + CLIP_MARGIN_DEG,
        miny - CLIP_MARGIN_DEG : maxy + CLIP_MARGIN_DEG,
    ]
    return municipalities.to_crs(METRIC_CRS), clipped.to_crs(METRIC_CRS).geometry


def load_published_fields() -> pd.DataFrame:
    """Population and risk, joined by IBGE code from the published product."""
    with GEOJSON.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = pd.DataFrame([feature["properties"] for feature in payload["features"]])
    return frame[
        ["municipality_code", "pop_10km", "pop_municipality", "Risk_Hazard",
         "coverage_status"]
    ]


def measure_frontage(
    municipalities: gpd.GeoDataFrame, coastline: gpd.GeoSeries
) -> pd.DataFrame:
    line = coastline.union_all()
    frame = pd.DataFrame(
        {
            "municipality_code": municipalities["CD_MUN"].astype(str),
            "municipality_name": municipalities["NM_MUN"],
            "state": municipalities["NM_UF"],
            "frontage_km": municipalities.geometry.intersection(line).length / 1e3,
            "distance_to_coastline_km": municipalities.geometry.distance(line) / 1e3,
        }
    )
    published = load_published_fields()
    published["municipality_code"] = published["municipality_code"].astype(str)
    frame = frame.merge(published, on="municipality_code", how="left")
    frame["has_measured_frontage"] = frame["frontage_km"] > 0
    return frame.sort_values("distance_to_coastline_km", ascending=False).reset_index(
        drop=True
    )


def neighbour_between(
    municipalities: gpd.GeoDataFrame, name: str, coastline: gpd.GeoSeries
) -> dict[str, object]:
    """Is some adjacent municipality of the set closer to the sea than `name`?

    A municipality that lost its shore to an emancipated neighbour shows exactly
    this pattern: adjacency plus a neighbour sitting between it and the water.

    Adjacency is tested with ``intersects`` rather than ``touches`` because the
    published geometries are simplified for the web map, so neighbouring polygons
    overlap slightly instead of sharing an edge exactly -- Içara and Balneário
    Rincão overlap by 0.14 km², which makes ``touches`` false for every pair in
    this layer.
    """
    line = coastline.union_all()
    target = municipalities[municipalities["NM_MUN"] == name]
    if target.empty:
        return {"municipality": name, "found": False}
    geometry = target.geometry.iloc[0]
    adjacent = municipalities.geometry.intersects(geometry) & (
        municipalities["NM_MUN"] != name
    )
    touching = municipalities[adjacent]
    own_distance = float(geometry.distance(line) / 1e3)
    neighbours = [
        {
            "municipality_name": row["NM_MUN"],
            "state": row["NM_UF"],
            "distance_to_coastline_km": round(
                float(row.geometry.distance(line) / 1e3), 3
            ),
            "frontage_km": round(float(row.geometry.intersection(line).length / 1e3), 3),
        }
        for _, row in touching.iterrows()
    ]
    return {
        "municipality": name,
        "found": True,
        "own_distance_to_coastline_km": round(own_distance, 3),
        "adjacent_members_of_the_set": neighbours,
        "shielded_by": [
            n["municipality_name"]
            for n in neighbours
            if n["distance_to_coastline_km"] < own_distance
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    municipalities, coastline = load_layers()
    frontage = measure_frontage(municipalities, coastline)

    no_frontage = frontage[~frontage["has_measured_frontage"]].copy()
    # The generalised coastline misplaces genuinely coastal municipalities by a few
    # hundred metres. Only a gap far outside that band is evidence of anything.
    resolution_band_km = 1.5
    unambiguous = no_frontage[
        no_frontage["distance_to_coastline_km"] > resolution_band_km
    ]

    frontage.to_csv(OUT_DIR / "frontage_by_municipality.csv", index=False)
    no_frontage.to_csv(OUT_DIR / "no_frontage_candidates.csv", index=False)

    summary = {
        "sources": {
            "geometry": str(SHAPEFILE.relative_to(ROOT)),
            "published_fields": str(GEOJSON.relative_to(ROOT)),
            "coastline": str(COASTLINE.relative_to(ROOT)),
        },
        "coastline_caveat": (
            "Natural Earth 10 m is generalised at about 1:10,000,000. It reports "
            "no intersection for 25 municipalities, nearly all of them "
            "unambiguously coastal -- Olinda, Itajai and Navegantes among them -- "
            "every one within 700 m of the drawn line. This screening cannot "
            "classify frontage on its own; a definitive classification needs a "
            "coastline at survey resolution, which this repository does not hold."
        ),
        "n_municipalities": int(len(frontage)),
        "n_with_measured_frontage": int(frontage["has_measured_frontage"].sum()),
        "n_without_measured_frontage": int((~frontage["has_measured_frontage"]).sum()),
        "resolution_band_km": resolution_band_km,
        "unambiguous_no_frontage": unambiguous[
            ["municipality_name", "state", "distance_to_coastline_km", "pop_10km"]
        ].to_dict("records"),
        "icara_case": neighbour_between(municipalities, "Içara", coastline),
        "santa_rita_ma_frontage_km": float(
            frontage.loc[
                (frontage["municipality_name"] == "Santa Rita")
                & (frontage["state"] == "Maranhão"),
                "frontage_km",
            ].iloc[0]
        ),
        "membership_hypothesis": (
            "Exactly one member has no sea frontage, and it has a dated reason: "
            "Balneario Rincao was created out of Icara by state law 12.668/2003 "
            "and installed in 2013, taking the shore with it. Lima et al. (2024) "
            "report 281 municipalities and do not include Balneario Rincao, which "
            "this repository had to add by hand. The economical reading is that "
            "the inherited roster predates or ignores that split: it carries the "
            "pre-split parent, now landlocked, and misses the post-split child. "
            "That is a defect of the inherited list, not evidence that the "
            "criterion is broader than frontage -- Santa Rita/MA, the other case "
            "the record doubted, does front the sea."
        ),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    print(f"Municipalities: {len(frontage)}")
    print(f"  with measured frontage:    {summary['n_with_measured_frontage']}")
    print(f"  without measured frontage: {summary['n_without_measured_frontage']}")
    print(f"\nOutside the {resolution_band_km} km resolution band:")
    print(
        unambiguous[
            ["municipality_name", "state", "distance_to_coastline_km", "pop_10km",
             "Risk_Hazard"]
        ].to_string(index=False)
    )
    print("\nIcara case:")
    print(json.dumps(summary["icara_case"], indent=2, ensure_ascii=False))
    print(f"\nWrote {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
