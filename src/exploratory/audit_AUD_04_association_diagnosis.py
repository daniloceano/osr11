"""AUD-04 diagnostic: audit the delivered grid-point to municipality association.

Each municipality receives its hazard from a single ocean grid point, chosen by
a workflow external to the repository. The documented rule (README Sec. 4.1) is
"the point with the highest compound-event count within the association". This
verifies, against the current data, whether that rule reproduces, how far the
assigned points are, and how many municipalities share a point.

Nothing is corrected here. This establishes the facts before any rule is
proposed, and re-measures the baseline-review numbers on the current hazard
field, which changed when the compound detector was revised (AUD-01/AUD-06).

Usage:
    python -m src.exploratory.audit_AUD_04_association_diagnosis

Output:
    outputs/audit/AUD-04_association_diagnosis/association_by_municipality.csv
    outputs/audit/AUD-04_association_diagnosis/diagnosis_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
MUNICIPAL_SHAPEFILE = ROOT / "outputs" / "risk_index" / "risk_index.shp"
GRID_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-04_association_diagnosis"

#: SIRGAS 2000 / Brazil Polyconic, the metric CRS used elsewhere in the project.
METRIC_CRS = "EPSG:5880"
#: Neighbourhood radii over which the documented rule is tested, in metres.
TEST_RADII_M = (30_000.0, 50_000.0)
#: Distance above which an assignment is flagged for individual justification.
DISTANCE_FLAG_M = 30_000.0


def _resolve(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def main() -> None:
    for path in (MUNICIPAL_SHAPEFILE, GRID_METRICS):
        if not path.exists():
            raise FileNotFoundError(path)

    municipalities = gpd.read_file(MUNICIPAL_SHAPEFILE)
    columns = list(municipalities.columns)
    code_col = _resolve(columns, ("CD_MUN", "geocode", "code_muni"))
    name_col = _resolve(columns, ("NM_MUN", "municipio", "municipali"))
    state_col = _resolve(columns, ("SIGLA_UF", "uf"))
    lat_col = _resolve(columns, ("grid_lat",))
    lon_col = _resolve(columns, ("grid_lon",))
    if not all((code_col, name_col, lat_col, lon_col)):
        raise ValueError("Shapefile lacks the expected identity/association fields")

    grid = pd.read_csv(GRID_METRICS)
    grid = grid.dropna(subset=["grid_lat", "grid_lon", "compound_count_total"])

    points = gpd.GeoDataFrame(
        grid.copy(),
        geometry=gpd.points_from_xy(grid["grid_lon"], grid["grid_lat"]),
        crs="EPSG:4326",
    ).to_crs(METRIC_CRS)
    point_xy = np.column_stack([points.geometry.x.values, points.geometry.y.values])
    tree = cKDTree(point_xy)

    municipalities = municipalities.to_crs(METRIC_CRS)
    assigned_key = list(
        zip(municipalities[lat_col].round(4), municipalities[lon_col].round(4))
    )
    grid_key = {
        (round(la, 4), round(lo, 4)): i
        for i, (la, lo) in enumerate(zip(grid["grid_lat"], grid["grid_lon"]))
    }

    rows = []
    for position, (_, feature) in enumerate(municipalities.iterrows()):
        geometry = feature.geometry
        key = assigned_key[position]
        assigned_index = grid_key.get(key)

        record = {
            "municipality_code": feature[code_col],
            "municipality_name": feature[name_col],
            "state": feature[state_col] if state_col else None,
            "assigned_lat": feature[lat_col],
            "assigned_lon": feature[lon_col],
            "assigned_resolved": assigned_index is not None,
        }
        if geometry is None or geometry.is_empty:
            rows.append(record)
            continue

        # Distance from the municipal polygon to the assigned point.
        if assigned_index is not None:
            assigned_point = points.geometry.iloc[assigned_index]
            record["distance_assigned_km"] = geometry.distance(assigned_point) / 1000.0
            record["assigned_compound_count"] = float(
                points["compound_count_total"].iloc[assigned_index]
            )
            record["assigned_thr_hs"] = float(points["thr_hs_abs"].iloc[assigned_index])

        # Nearest point to the polygon, by brute force over the polygon boundary
        # representative point set. Using the polygon centroid alone would bias
        # elongated coastal municipalities.
        distances = points.geometry.distance(geometry)
        nearest_index = int(distances.values.argmin())
        record["nearest_lat"] = float(points["grid_lat"].iloc[nearest_index])
        record["nearest_lon"] = float(points["grid_lon"].iloc[nearest_index])
        record["distance_nearest_km"] = float(distances.values[nearest_index]) / 1000.0
        record["assigned_is_nearest"] = (
            assigned_index is not None and assigned_index == nearest_index
        )

        # Documented rule: highest compound count within radius R of the polygon.
        for radius in TEST_RADII_M:
            within = np.flatnonzero(distances.values <= radius)
            if within.size == 0:
                record[f"assigned_is_maxcount_{int(radius/1000)}km"] = False
                record[f"n_candidates_{int(radius/1000)}km"] = 0
                continue
            counts = points["compound_count_total"].values[within]
            best = int(within[int(np.argmax(counts))])
            record[f"assigned_is_maxcount_{int(radius/1000)}km"] = (
                assigned_index is not None and assigned_index == best
            )
            record[f"n_candidates_{int(radius/1000)}km"] = int(within.size)
        rows.append(record)

    table = pd.DataFrame(rows)
    resolved = table[table["assigned_resolved"] & table["distance_assigned_km"].notna()]

    shared = (
        resolved.groupby(["assigned_lat", "assigned_lon"])
        .size()
        .sort_values(ascending=False)
    )

    summary = {
        "generated_by": "src.exploratory.audit_AUD_04_association_diagnosis",
        "hazard_source": str(GRID_METRICS.relative_to(ROOT)),
        "note": (
            "Re-measured on the revised compound catalogue (AUD-01/AUD-06), so "
            "the counts differ from the baseline review, which used the "
            "superseded SSH_total catalogue."
        ),
        "n_municipalities": int(len(table)),
        "n_resolved": int(len(resolved)),
        "rule_reproducibility": {
            "assigned_is_nearest_pct": float(100 * resolved["assigned_is_nearest"].mean()),
            **{
                f"assigned_is_maxcount_{int(r/1000)}km_pct": float(
                    100 * resolved[f"assigned_is_maxcount_{int(r/1000)}km"].mean()
                )
                for r in TEST_RADII_M
            },
        },
        "distance_assigned_km": {
            "min": float(resolved["distance_assigned_km"].min()),
            "q25": float(resolved["distance_assigned_km"].quantile(0.25)),
            "median": float(resolved["distance_assigned_km"].median()),
            "q75": float(resolved["distance_assigned_km"].quantile(0.75)),
            "max": float(resolved["distance_assigned_km"].max()),
            f"n_above_{int(DISTANCE_FLAG_M/1000)}km": int(
                (resolved["distance_assigned_km"] > DISTANCE_FLAG_M / 1000).sum()
            ),
        },
        "point_sharing": {
            "unique_points_used": int(len(shared)),
            "municipalities_served": int(shared.sum()),
            "max_municipalities_per_point": int(shared.max()),
            "points_serving_4_or_more": int((shared >= 4).sum()),
            "top_shared": [
                {"lat": float(la), "lon": float(lo), "municipalities": int(n)}
                for (la, lo), n in shared.head(6).items()
            ],
        },
        "farthest_assignments": resolved.nlargest(10, "distance_assigned_km")[
            ["municipality_name", "state", "distance_assigned_km", "distance_nearest_km"]
        ].to_dict("records"),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_DIR / "association_by_municipality.csv", index=False)
    with (OUT_DIR / "diagnosis_summary.json").open("w") as f:
        json.dump(summary, f, indent=2, default=float)

    print(json.dumps(
        {k: v for k, v in summary.items() if k != "farthest_assignments"},
        indent=2, default=float,
    ))
    print()
    print("Atribuições mais distantes:")
    for record in summary["farthest_assignments"]:
        print(
            f"  {record['municipality_name']:<28}{record['state'] or '':<4}"
            f"atribuído {record['distance_assigned_km']:>6.1f} km   "
            f"mais próximo {record['distance_nearest_km']:>6.1f} km"
        )


if __name__ == "__main__":
    main()
