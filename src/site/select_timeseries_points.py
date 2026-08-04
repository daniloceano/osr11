"""Automatic selection of the grid points whose time series the site exposes.

The hazard-characterization page lets the reader open the daily `Hs`, `zos` and
astronomical-tide series at a handful of grid points. Which points those are
must not be an editorial decision: AUD-04 recorded what happens when points are
picked by hand, so the selection here is made from the data alone and frozen in
a versioned CSV that can be re-derived and audited.

Method
------
1. Candidate set — the grid points that actually serve at least one
   municipality (``data/external/municipal_grid_association``). The panel sits
   inside a municipal risk product, so highlighting a point that feeds no
   municipality would be incoherent.
2. Feature space, z-scored over the candidate set:

   * ``surge_q99_over_swing`` — surge(q99) over the spring-neap swing, the
     regime discriminator (AUD-01);
   * ``hat_m`` — tidal magnitude, the HAT datum of the current method;
   * ``thr_hs_abs`` — energy of the local wave climate;
   * ``Hazard_Frequency``, ``Hazard_Severity`` — the two components of the
     index, as normalized in ``src.risk_integration.hazard_index``.

   The Rayleigh R of the phase test is deliberately excluded: phase behaviour
   is what the reader is meant to discover in the chart, so using it as a
   selection feature would make the panel circular.
3. Stratify the candidates by ``surge_q99_over_swing`` into k strata of equal
   count and take the medoid of each stratum in the standardized feature space
   (KMeans with a single cluster, then the real point nearest the centroid).
   Stratifying guarantees regime coverage by construction and stops the
   clustering from returning several points bunched in the Amazon sector, which
   is oversampled by the grid (324 of the 808 native points).
4. The nearest municipality is attached afterwards, as a label only. Points are
   selected by data and named by geography, never the reverse.

Usage:
    conda run -n osr python -m src.site.select_timeseries_points [--k 8]

Output:
    outputs/site_timeseries_points/selected_points.csv
    outputs/site_timeseries_points/selection_metadata.json
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.risk_integration.hazard_index import derive_native_hazard_index

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
ASSOCIATION = (
    ROOT
    / "data"
    / "external"
    / "municipal_grid_association"
    / "municipal_grid_association.csv"
)
SURGE_VS_TIDE = (
    ROOT
    / "outputs"
    / "audit"
    / "AUD-01_surge_vs_tide_magnitude"
    / "surge_vs_tide_by_point.csv"
)
OUTPUT_DIR = ROOT / "outputs" / "site_timeseries_points"
OUTPUT_CSV = OUTPUT_DIR / "selected_points.csv"
OUTPUT_METADATA = OUTPUT_DIR / "selection_metadata.json"

#: Standardized before use; ``surge_q99_over_swing`` doubles as the
#: stratification variable.
FEATURES = (
    "surge_q99_over_swing",
    # Level datum of the current method. Was ``mhws_m`` until 2026-07-30.
    "hat_m",
    "thr_hs_abs",
    "Hazard_Frequency",
    "Hazard_Severity",
)
STRATIFY_BY = "surge_q99_over_swing"

#: Points added on top of the automatic selection to cover a coastal sector the
#: stratified rule leaves unrepresented. The rule stratifies on the physical
#: regime, not on geography, so a sector whose regime resembles another's can end
#: up with no point at all — which is what happened between Bahia and Maranhao,
#: leaving Ceara, Rio Grande do Norte, Paraiba, Pernambuco, Alagoas, Sergipe and
#: Piaui without one.
#:
#: These are deliberate, named and justified additions, kept separate from the
#: automatic set and flagged in the output so that no reader mistakes the
#: combined list for a purely algorithmic selection. Adding a point never removes
#: or displaces an automatically selected one.
COVERAGE_ADDITIONS: tuple[dict[str, str], ...] = (
    {
        "municipality": "Natal",
        "state": "RN",
        "reason": (
            "The automatic strata leave the entire Northeast without a point, "
            "the sector between Bahia and Maranhao. That sector is also where "
            "AUD-18 records the absence of an independent impact database, so a "
            "monitoring point there carries diagnostic value beyond coverage."
        ),
    },
)
DEFAULT_K = 9
#: Fixed so that the selection is reproducible bit for bit.
RANDOM_STATE = 0


def _round_key(frame: pd.DataFrame) -> pd.DataFrame:
    """Round the coordinates so the three sources join exactly."""
    out = frame.copy()
    for field in ("grid_lat", "grid_lon"):
        out[field] = pd.to_numeric(out[field], errors="coerce").round(4)
    return out


def build_candidate_table() -> pd.DataFrame:
    """Join the candidate points with their selection features."""
    association = _round_key(pd.read_csv(ASSOCIATION))
    candidates = (
        association[["grid_lat", "grid_lon"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    municipalities = (
        association.groupby(["grid_lat", "grid_lon"])
        .agg(
            n_municipalities=("municipality_code", "nunique"),
        )
        .reset_index()
    )
    # Label only: the municipality whose polygon lies closest to the point.
    nearest = (
        association.sort_values("distance_to_polygon_km")
        .groupby(["grid_lat", "grid_lon"], as_index=False)
        .first()[
            [
                "grid_lat",
                "grid_lon",
                "municipality_name",
                "state",
                "distance_to_polygon_km",
            ]
        ]
        .rename(columns={"municipality_name": "nearest_municipality"})
    )

    surge = _round_key(pd.read_csv(SURGE_VS_TIDE))[
        [
            "grid_lat",
            "grid_lon",
            "surge_q99_over_swing",
            "surge_q99_anomaly_cm",
            "springneap_swing_cm",
            "latitude_band",
        ]
    ]
    hazard, _ = derive_native_hazard_index()
    hazard = _round_key(hazard)[
        [
            "grid_lat",
            "grid_lon",
            "hat_m",
            "thr_hs_abs",
            "Hazard_Frequency",
            "Hazard_Severity",
            "Hazard_Index",
            "compound_count_total",
            "mean_integrated_severity",
        ]
    ]

    table = (
        candidates.merge(municipalities, on=["grid_lat", "grid_lon"], how="left")
        .merge(nearest, on=["grid_lat", "grid_lon"], how="left")
        .merge(surge, on=["grid_lat", "grid_lon"], how="left")
        .merge(hazard, on=["grid_lat", "grid_lon"], how="left")
    )
    missing = table[list(FEATURES)].isna().any(axis=1)
    if missing.any():
        raise ValueError(
            f"{int(missing.sum())} candidate point(s) lack selection features; "
            "the three sources are not aligned on the same grid"
        )

    # Points with no accepted compound event are excluded from the candidate
    # set. They are legitimate members of the hazard grid — the zero-event
    # policy keeps them at frequency 0 and severity 0 so that every arm
    # normalises over the same 808 points — but a medoid landing on one would
    # render a time-series panel with no shaded event at all. Under the HAT
    # gate 208 of the 808 points are in that state, so this is not a corner
    # case. The exclusion is applied AFTER the features are computed, so it
    # removes candidates without altering any normalisation.
    alive = pd.to_numeric(table["compound_count_total"], errors="coerce") > 0
    n_dropped = int((~alive).sum())
    if n_dropped:
        log.info(
            "Excluding %d of %d candidate points with zero accepted compound "
            "events; a medoid there would render an empty panel",
            n_dropped, len(table),
        )
    table = table.loc[alive].reset_index(drop=True)
    if len(table) < 2:
        raise ValueError(
            "Fewer than two candidate points have accepted compound events"
        )
    return table


def select_points(table: pd.DataFrame, k: int) -> pd.DataFrame:
    """Return the medoid of each of the k equal-count strata."""
    if k < 2 or k > len(table):
        raise ValueError(f"k must lie in [2, {len(table)}]; got {k}")

    features = table[list(FEATURES)].to_numpy(dtype=float)
    mean = features.mean(axis=0)
    std = features.std(axis=0, ddof=0)
    if not np.all(std > 0):
        raise ValueError("A selection feature is constant over the candidates")
    z = (features - mean) / std

    # Equal-count strata of the regime discriminator. ``rank`` breaks ties by
    # order of appearance, so the strata are exactly balanced.
    order = table[STRATIFY_BY].rank(method="first").to_numpy()
    stratum = np.minimum(((order - 1) * k / len(table)).astype(int), k - 1)

    rows = []
    for index in range(k):
        members = np.flatnonzero(stratum == index)
        centroid = (
            KMeans(n_clusters=1, n_init=10, random_state=RANDOM_STATE)
            .fit(z[members])
            .cluster_centers_[0]
        )
        distance = np.linalg.norm(z[members] - centroid, axis=1)
        medoid = members[int(np.argmin(distance))]
        row = table.iloc[medoid].to_dict()
        row["stratum"] = index
        row["stratum_size"] = int(members.size)
        row["stratum_surge_over_swing_min"] = float(
            table[STRATIFY_BY].to_numpy()[members].min()
        )
        row["stratum_surge_over_swing_max"] = float(
            table[STRATIFY_BY].to_numpy()[members].max()
        )
        row["distance_to_centroid_z"] = float(distance.min())
        rows.append(row)

    selected = pd.DataFrame(rows).sort_values("grid_lat").reset_index(drop=True)
    selected.insert(0, "point_id", [f"p{i + 1:02d}" for i in range(len(selected))])
    return selected


def _append_coverage_additions(
    table: pd.DataFrame, selected: pd.DataFrame
) -> pd.DataFrame:
    """Add the named coverage points and renumber the set by latitude."""
    rows = [selected]
    for addition in COVERAGE_ADDITIONS:
        match = table[
            (table["nearest_municipality"] == addition["municipality"])
            & (table["state"] == addition["state"])
        ]
        if match.empty:
            raise ValueError(
                f"Coverage addition {addition['municipality']}/{addition['state']} "
                "is not among the candidate points"
            )
        if len(match) > 1:
            raise ValueError(
                f"Coverage addition {addition['municipality']}/{addition['state']} "
                f"matches {len(match)} candidates; the name is ambiguous"
            )
        already = selected[
            (selected["grid_lat"] == match["grid_lat"].iloc[0])
            & (selected["grid_lon"] == match["grid_lon"].iloc[0])
        ]
        if not already.empty:
            continue
        row = match.copy()
        row["selection_method"] = "coverage_addition"
        rows.append(row)

    combined = pd.concat(rows, ignore_index=True)
    combined = combined.sort_values("grid_lat").reset_index(drop=True)
    combined["point_id"] = [f"p{i:02d}" for i in range(1, len(combined) + 1)]
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the selection without writing the frozen CSV",
    )
    args = parser.parse_args()

    table = build_candidate_table()
    selected = select_points(table, args.k)
    selected["selection_method"] = "stratified_medoid"
    selected = _append_coverage_additions(table, selected)

    columns = [
        "point_id",
        "grid_lat",
        "grid_lon",
        "nearest_municipality",
        "state",
        "latitude_band",
        "distance_to_polygon_km",
        "n_municipalities",
        "stratum",
        "stratum_size",
        "stratum_surge_over_swing_min",
        "stratum_surge_over_swing_max",
        "distance_to_centroid_z",
        "selection_method",
        *FEATURES,
        "surge_q99_anomaly_cm",
        "springneap_swing_cm",
        "compound_count_total",
        "mean_integrated_severity",
        "Hazard_Index",
    ]
    selected = selected[columns]

    with pd.option_context("display.width", 200, "display.max_columns", 40):
        print(
            selected[
                [
                    "point_id",
                    "grid_lat",
                    "grid_lon",
                    "nearest_municipality",
                    "state",
                    "surge_q99_over_swing",
                    "hat_m",
                    "thr_hs_abs",
                    "Hazard_Frequency",
                    "Hazard_Severity",
                ]
            ].round(3)
        )

    if args.dry_run:
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    selected.to_csv(OUTPUT_CSV, index=False)
    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_additions": [
            {**addition, "included": bool(
                (selected["nearest_municipality"] == addition["municipality"]).any()
            )}
            for addition in COVERAGE_ADDITIONS
        ],
        "selection_method_counts": {
            method: int(count)
            for method, count in selected["selection_method"].value_counts().items()
        },
        "implementation": "src/site/select_timeseries_points.py",
        "candidate_source": str(ASSOCIATION.relative_to(ROOT)),
        "candidate_count": int(len(table)),
        "feature_sources": {
            "surge_q99_over_swing": str(SURGE_VS_TIDE.relative_to(ROOT)),
            "hat_m": "src/04_risk_integration/hazard_index.py",
            "thr_hs_abs": "src/04_risk_integration/hazard_index.py",
            "Hazard_Frequency": "src/04_risk_integration/hazard_index.py",
            "Hazard_Severity": "src/04_risk_integration/hazard_index.py",
        },
        "features": list(FEATURES),
        "excluded_feature": {
            "field": "rayleigh_R",
            "reason": (
                "Phase behaviour is the finding the chart is meant to reveal; "
                "selecting on it would make the panel circular."
            ),
        },
        "stratify_by": STRATIFY_BY,
        "k": int(args.k),
        "random_state": RANDOM_STATE,
        "rule": (
            "k equal-count strata of surge_q99_over_swing; within each stratum "
            "the point nearest the centroid of the z-scored feature space "
            "(medoid) is selected. Municipality names are labels attached after "
            "selection and never enter the criterion."
        ),
        "output": str(OUTPUT_CSV.relative_to(ROOT)),
    }
    OUTPUT_METADATA.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"\nSaved: {OUTPUT_CSV}")
    print(f"Saved: {OUTPUT_METADATA}")


if __name__ == "__main__":
    main()
