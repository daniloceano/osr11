"""Archive the municipality-to-grid-point association as a versioned dataset.

The association that assigns one ocean grid point to each coastal municipality
was established by visual inspection in a GIS, municipality by municipality,
by the author of the delivered municipal file. It is therefore an **input
dataset produced by expert judgement**, not a derived product: there is no rule
to re-execute, and none can be recovered.

Until now it existed only inside ``outputs/risk_index/risk_index.shp``, which is
excluded from version control by ``.gitignore``. Losing that file would have
meant losing the hazard value of all 280 municipalities irrecoverably. This
extracts the association into a small versioned CSV with provenance metadata,
so the dataset survives independently of the shapefile.

Nothing is recomputed and no value changes: the extracted pairs are exactly
those the exporter already consumes.

Usage:
    python -m src.risk_integration.archive_municipal_grid_association

Output:
    data/external/municipal_grid_association/municipal_grid_association.csv
    data/external/municipal_grid_association/provenance.json
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHAPEFILE = ROOT / "outputs" / "risk_index" / "risk_index.shp"
GRID_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
OUT_DIR = ROOT / "data" / "external" / "municipal_grid_association"
OUT_CSV = OUT_DIR / "municipal_grid_association.csv"
OUT_PROVENANCE = OUT_DIR / "provenance.json"

METRIC_CRS = "EPSG:5880"


def _resolve(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not SOURCE_SHAPEFILE.exists():
        raise FileNotFoundError(
            f"{SOURCE_SHAPEFILE} not found. The association can only be extracted "
            "from the delivered municipal file."
        )

    layer = gpd.read_file(SOURCE_SHAPEFILE)
    columns = list(layer.columns)
    code_col = _resolve(columns, ("CD_MUN", "geocode", "code_muni"))
    name_col = _resolve(columns, ("NM_MUN", "municipali", "municipio"))
    state_col = _resolve(columns, ("SIGLA_UF", "uf"))
    lat_col = _resolve(columns, ("grid_lat",))
    lon_col = _resolve(columns, ("grid_lon",))
    missing = [
        label
        for label, col in (
            ("municipality_code", code_col), ("municipality_name", name_col),
            ("grid_lat", lat_col), ("grid_lon", lon_col),
        )
        if col is None
    ]
    if missing:
        raise ValueError(f"Delivered file lacks required field(s): {', '.join(missing)}")

    table = pd.DataFrame(
        {
            "municipality_code": layer[code_col].astype(str),
            "municipality_name": layer[name_col],
            "state": layer[state_col] if state_col else None,
            "grid_lat": pd.to_numeric(layer[lat_col], errors="coerce"),
            "grid_lon": pd.to_numeric(layer[lon_col], errors="coerce"),
        }
    )

    # Distance from each municipal polygon to its assigned point, carried in the
    # archive so the support of every assignment is inspectable without redoing
    # the geometry.
    projected = layer.to_crs(METRIC_CRS)
    points = gpd.GeoSeries(
        gpd.points_from_xy(table["grid_lon"], table["grid_lat"]), crs="EPSG:4326"
    ).to_crs(METRIC_CRS)
    distances = np.full(len(table), np.nan)
    for i, (geometry, point) in enumerate(zip(projected.geometry, points)):
        if geometry is None or geometry.is_empty or point is None or point.is_empty:
            continue
        distances[i] = geometry.distance(point) / 1000.0
    table["distance_to_polygon_km"] = np.round(distances, 3)

    associated = table.dropna(subset=["grid_lat", "grid_lon"]).copy()
    associated = associated.sort_values("municipality_code").reset_index(drop=True)

    # Verify every assigned point exists in the native grid, so the archive
    # cannot silently carry an assignment that resolves to nothing.
    unresolved: list[str] = []
    if GRID_METRICS.exists():
        grid = pd.read_csv(GRID_METRICS)
        known = {
            (round(la, 4), round(lo, 4))
            for la, lo in zip(grid["grid_lat"], grid["grid_lon"])
        }
        unresolved = [
            f"{row.municipality_name} ({row.municipality_code})"
            for row in associated.itertuples()
            if (round(row.grid_lat, 4), round(row.grid_lon, 4)) not in known
        ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    associated.to_csv(OUT_CSV, index=False)

    shared = associated.groupby(["grid_lat", "grid_lon"]).size()
    provenance = {
        "dataset": "Municipality-to-ocean-grid-point association (OSR11)",
        "produced_by": "Karine Bastos Leal (INPE)",
        "method": (
            "Established by visual inspection in QGIS, municipality by "
            "municipality, selecting a nearby grid point with substantial "
            "compound-event activity. Both criteria — proximity and event "
            "activity — were weighed together by eye. There is no script: the "
            "association is expert judgement, and is archived here as an input "
            "dataset rather than as a reproducible derivation."
        ),
        "method_source": (
            "Personal communication from the author, relayed 2026-07-30. "
            "Recorded in docs/scientific_audit/issues/"
            "AUD-04_grid_to_municipality_transfer.md, section 3.1."
        ),
        "extracted_from": str(SOURCE_SHAPEFILE.relative_to(ROOT)),
        "extracted_from_sha256": _sha256(SOURCE_SHAPEFILE),
        "extracted_on": date.today().isoformat(),
        "extracted_by": "src/04_risk_integration/archive_municipal_grid_association.py",
        "why_archived": (
            "outputs/risk_index/ is excluded by .gitignore, so the association "
            "was not under version control. It cannot be recomputed if lost."
        ),
        "records": int(len(associated)),
        "municipalities_without_association": int(
            len(table) - len(associated)
        ),
        "unique_grid_points": int(len(shared)),
        "max_municipalities_per_point": int(shared.max()),
        "distance_to_polygon_km": {
            "median": float(associated["distance_to_polygon_km"].median()),
            "q75": float(associated["distance_to_polygon_km"].quantile(0.75)),
            "max": float(associated["distance_to_polygon_km"].max()),
            "n_above_30km": int((associated["distance_to_polygon_km"] > 30).sum()),
        },
        "validation": {
            "assignments_resolving_to_a_known_grid_point": int(
                len(associated) - len(unresolved)
            ),
            "unresolved": unresolved,
        },
        "known_limitations": [
            "Municipalities at the head of Guanabara Bay (Magé, Guapimirim) have "
            "no ocean grid point within 30 km; their assignment necessarily "
            "refers to the open shelf and does not represent conditions inside "
            "the bay. This is a limitation of grid coverage, not of the "
            "association: no assignment rule can resolve it.",
            "178 grid points serve 280 municipalities, so hazard values are not "
            "spatially independent between neighbouring municipalities.",
        ],
    }
    with OUT_PROVENANCE.open("w") as f:
        json.dump(provenance, f, indent=2, ensure_ascii=False)

    print(f"Wrote {OUT_CSV.relative_to(ROOT)} ({len(associated)} records)")
    print(f"Wrote {OUT_PROVENANCE.relative_to(ROOT)}")
    print(
        f"  unique points: {provenance['unique_grid_points']} · "
        f"max per point: {provenance['max_municipalities_per_point']} · "
        f"median distance: {provenance['distance_to_polygon_km']['median']:.1f} km"
    )
    if unresolved:
        print(f"  WARNING: {len(unresolved)} assignment(s) do not resolve to a grid point")


if __name__ == "__main__":
    main()
