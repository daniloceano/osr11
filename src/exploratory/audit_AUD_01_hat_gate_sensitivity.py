"""AUD-01 diagnostic: what changes if the level gate is HAT instead of MHWS,
and is it coherent to gate on one datum while measuring the excess over another?

The MHWS condition was adopted to keep the astronomical tide as a conditioning
variable rather than a magnitude. In the macrotidal North that conditioning is
weak in a specific way: MHWS is a level the tide reaches unaided on every spring
cycle, so a candidate wave-and-surge overlap that happens to land on a spring
tide passes the gate whether or not the meteorological contribution mattered.

Three questions are asked, per grid point, over the full 808-point ocean grid:

1. **Does the gate require the meteorology?** For every accepted event, would
   the tide *alone* have carried the level over the gate on the same overlap
   days — that is, is ``max(tide) > gate`` without any help from ``zos'``? A gate
   that is satisfied by astronomy alone in most events is not selecting compound
   conditions; it is selecting tidal phase.

2. **What survives an HAT gate?** HAT is estimated as the maximum of
   ``tide_daily_max`` over 1993-2025, a 33-year record that covers the 18.6-year
   nodal cycle, so no percentile has to be chosen. Event counts, the rejection
   rate and the tide-alone fraction are recomputed with the gate at HAT.

3. **How is the daily excess composed?** On the days that satisfy all three
   criteria the level excess decomposes exactly as

       SWL - gate = zos' + (tide - gate),

   a meteorological term plus an astronomical one. The two are reported
   separately for each gate, and additionally for the hybrid the analyst asked
   about — gate at HAT, excess still measured over MHWS — where the identity
   becomes ``SWL - MHWS = zos' + (tide - HAT) + (HAT - MHWS)`` and the last term
   is a per-point constant that no event can avoid.

Read-only diagnostic. Does not modify the production pipeline, the published
catalogue, or any index. Nothing here is adopted.

Usage:
    conda run -n osr python -m src.exploratory.audit_AUD_01_hat_gate_sensitivity

Output:
    outputs/audit/AUD-01_hat_gate_sensitivity/hat_gate_by_point.csv
    outputs/audit/AUD-01_hat_gate_sensitivity/hat_gate_by_band.csv
    outputs/audit/AUD-01_hat_gate_sensitivity/hat_gate_summary.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from src.compound_detection.detection_mhws import (
    MIN_FINITE_DAYS,
    compound_events_at_point,
)
from src.compound_detection.mhws_datum import mhws_at_points, still_water_level

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
POINT_SOURCE = (
    ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_hat_gate_sensitivity"

LATITUDE_BANDS = [
    ("RS", -36.0, -30.0),
    ("SC/PR", -30.0, -25.0),
    ("SP/RJ", -25.0, -20.0),
    ("ES/BA-S", -20.0, -15.0),
    ("BA-N", -15.0, -10.0),
    ("NE", -10.0, -5.0),
    ("N_equatorial", -5.0, 0.0),
    ("AP", 0.0, 7.0),
]


def band_of(latitude: float) -> str:
    for name, lower, upper in LATITUDE_BANDS:
        if lower <= latitude < upper:
            return name
    return "outside"


def gate_diagnostics(
    *,
    hs: np.ndarray,
    zos: np.ndarray,
    tide: np.ndarray,
    finite: np.ndarray,
    gate: float,
) -> dict[str, Any]:
    """Detection statistics and excess decomposition for one level gate."""
    events, context = compound_events_at_point(
        hs=hs, zos=zos, tide=tide, finite=finite, mhws=gate
    )
    zos_anomaly = zos - context["zos_mean"]
    swl = still_water_level(zos, tide, zos_mean=context["zos_mean"])

    if not events:
        return {
            "n_candidates": context["n_candidate_events"],
            "n_accepted": 0,
            "n_rejected": context["n_rejected_by_mhws"],
            "frac_tide_alone": None,
            "full_days": 0,
            "mean_excess_m": None,
            "mean_meteo_term_m": None,
            "mean_astro_term_m": None,
        }

    # Would the tide alone have cleared the gate on the same overlap days?
    tide_alone = 0
    for event in events:
        overlap = np.asarray(event["overlap_indices"], dtype=int)
        if float(np.nanmax(tide[overlap])) > gate:
            tide_alone += 1

    full = np.concatenate(
        [np.asarray(e["full_criterion_indices"], dtype=int) for e in events]
    )
    excess = swl[full] - gate
    meteo = zos_anomaly[full]
    astro = tide[full] - gate

    return {
        "n_candidates": context["n_candidate_events"],
        "n_accepted": len(events),
        "n_rejected": context["n_rejected_by_mhws"],
        "frac_tide_alone": round(tide_alone / len(events), 4),
        "full_days": int(full.size),
        "mean_excess_m": round(float(np.mean(excess)), 4),
        "mean_meteo_term_m": round(float(np.mean(meteo)), 4),
        "mean_astro_term_m": round(float(np.mean(astro)), 4),
        # kept so the hybrid can be evaluated on exactly these days
        "_full_indices": full,
        "_swl": swl,
        "_zos_anomaly": zos_anomaly,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (UNIFIED, POINT_SOURCE):
        if not path.exists():
            raise FileNotFoundError(path)

    catalogue = json.loads(POINT_SOURCE.read_text())
    points = pd.DataFrame(
        [{"grid_lat": p["grid_lat"], "grid_lon": p["grid_lon"]} for p in catalogue]
    )
    mhws = mhws_at_points(points["grid_lat"].values, points["grid_lon"].values)

    ds = xr.open_dataset(UNIFIED)
    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in points["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in points["grid_lon"]],
        dims="point",
    )
    log.info("Extracting series for %d points ...", len(points))
    hs_all = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos_all = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide_all = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values

    rows: list[dict[str, Any]] = []
    for i in range(len(points)):
        hs = hs_all[:, i].astype(float)
        zos = zos_all[:, i].astype(float)
        tide = tide_all[:, i].astype(float)
        finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
        if finite.sum() < MIN_FINITE_DAYS or not np.isfinite(mhws[i]):
            continue

        # HAT from the record itself: 33 years span the 18.6-year nodal cycle,
        # so the maximum is a defensible estimate with no percentile to choose.
        hat = float(np.nanmax(tide[finite]))
        row: dict[str, Any] = {
            "grid_lat": float(points["grid_lat"][i]),
            "grid_lon": float(points["grid_lon"][i]),
            "latitude_band": band_of(float(points["grid_lat"][i])),
            "mhws_m": round(float(mhws[i]), 4),
            "hat_m": round(hat, 4),
            "hat_minus_mhws_m": round(hat - float(mhws[i]), 4),
            "springneap_swing_m": round(
                float(np.nanmax(tide[finite]) - np.nanmin(tide[finite])), 4
            ),
        }

        for label, gate in (("mhws", float(mhws[i])), ("hat", hat)):
            stats = gate_diagnostics(
                hs=hs, zos=zos, tide=tide, finite=finite, gate=gate
            )
            if label == "hat" and stats["n_accepted"] > 0:
                # The hybrid: qualify on HAT, measure the excess over MHWS. The
                # identity SWL - MHWS = zos' + (tide - HAT) + (HAT - MHWS) makes
                # the inherited constant explicit.
                full = stats["_full_indices"]
                hybrid = stats["_swl"][full] - float(mhws[i])
                row["hybrid_mean_excess_over_mhws_m"] = round(
                    float(np.mean(hybrid)), 4
                )
                row["hybrid_inherited_constant_m"] = round(hat - float(mhws[i]), 4)
                row["hybrid_constant_share"] = round(
                    (hat - float(mhws[i])) / float(np.mean(hybrid)), 4
                ) if float(np.mean(hybrid)) > 0 else None
            for key, value in stats.items():
                if not key.startswith("_"):
                    row[f"{label}_{key}"] = value
        rows.append(row)
        if (i + 1) % 100 == 0:
            log.info("  %d / %d", i + 1, len(points))

    frame = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_DIR / "hat_gate_by_point.csv", index=False)

    aggregate = {
        "n_points": "size",
        "mhws_m": "mean",
        "hat_m": "mean",
        "hat_minus_mhws_m": "mean",
        "mhws_n_accepted": "mean",
        "hat_n_accepted": "mean",
        "mhws_frac_tide_alone": "mean",
        "hat_frac_tide_alone": "mean",
        "mhws_mean_excess_m": "mean",
        "mhws_mean_meteo_term_m": "mean",
        "mhws_mean_astro_term_m": "mean",
        "hat_mean_excess_m": "mean",
        "hat_mean_meteo_term_m": "mean",
        "hat_mean_astro_term_m": "mean",
        "hybrid_mean_excess_over_mhws_m": "mean",
        "hybrid_constant_share": "mean",
    }
    by_band = (
        frame.assign(n_points=1)
        .groupby("latitude_band")
        .agg({k: v for k, v in aggregate.items() if k in frame or k == "n_points"})
        .round(4)
    )
    by_band.to_csv(OUT_DIR / "hat_gate_by_band.csv")

    north = frame[frame["grid_lat"] > -15.0]
    south = frame[frame["grid_lat"] < -25.0]
    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_hat_gate_sensitivity",
        "question": (
            "Does the MHWS level gate require the meteorological contribution, "
            "what survives an HAT gate, and is a HAT gate with an MHWS excess "
            "internally coherent?"
        ),
        "hat_definition": "max of tide_daily_max over 1993-2025 (33 years)",
        "n_points": int(len(frame)),
        "north_of_15S": {
            "n_points": int(len(north)),
            "mean_mhws_m": round(float(north["mhws_m"].mean()), 4),
            "mean_hat_m": round(float(north["hat_m"].mean()), 4),
            "mean_hat_minus_mhws_m": round(float(north["hat_minus_mhws_m"].mean()), 4),
            "events_mhws_gate": int(north["mhws_n_accepted"].sum()),
            "events_hat_gate": int(north["hat_n_accepted"].sum()),
            "frac_tide_alone_mhws": round(
                float(north["mhws_frac_tide_alone"].mean()), 4
            ),
            "frac_tide_alone_hat": round(
                float(north["hat_frac_tide_alone"].mean()), 4
            ),
            "mhws_excess_meteo_m": round(
                float(north["mhws_mean_meteo_term_m"].mean()), 4
            ),
            "mhws_excess_astro_m": round(
                float(north["mhws_mean_astro_term_m"].mean()), 4
            ),
            "hat_excess_meteo_m": round(
                float(north["hat_mean_meteo_term_m"].mean()), 4
            ),
            "hat_excess_astro_m": round(
                float(north["hat_mean_astro_term_m"].mean()), 4
            ),
        },
        "south_of_25S": {
            "n_points": int(len(south)),
            "mean_mhws_m": round(float(south["mhws_m"].mean()), 4),
            "mean_hat_m": round(float(south["hat_m"].mean()), 4),
            "mean_hat_minus_mhws_m": round(float(south["hat_minus_mhws_m"].mean()), 4),
            "events_mhws_gate": int(south["mhws_n_accepted"].sum()),
            "events_hat_gate": int(south["hat_n_accepted"].sum()),
            "frac_tide_alone_mhws": round(
                float(south["mhws_frac_tide_alone"].mean()), 4
            ),
            "frac_tide_alone_hat": round(
                float(south["hat_frac_tide_alone"].mean()), 4
            ),
            "mhws_excess_meteo_m": round(
                float(south["mhws_mean_meteo_term_m"].mean()), 4
            ),
            "mhws_excess_astro_m": round(
                float(south["mhws_mean_astro_term_m"].mean()), 4
            ),
            "hat_excess_meteo_m": round(
                float(south["hat_mean_meteo_term_m"].mean()), 4
            ),
            "hat_excess_astro_m": round(
                float(south["hat_mean_astro_term_m"].mean()), 4
            ),
        },
        "domain_totals": {
            "events_mhws_gate": int(frame["mhws_n_accepted"].sum()),
            "events_hat_gate": int(frame["hat_n_accepted"].sum()),
            "points_with_zero_events_under_hat": int(
                (frame["hat_n_accepted"] == 0).sum()
            ),
        },
    }
    (OUT_DIR / "hat_gate_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    log.info("Saved: %s", OUT_DIR)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
