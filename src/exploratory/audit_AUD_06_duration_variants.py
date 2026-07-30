"""AUD-06 diagnostic: candidate replacements for the duration component.

The implemented third hazard component is ``mean_overlap_duration``: the mean
number of calendar days on which a wave exceedance and a level exceedance were
simultaneously active. It measures how long two percentile tests happened to
agree, which is a statistical construct rather than a physical duration, it is
discretised into whole days over a range of about 1.25 days domain-wide, and it
anticorrelates with frequency (Spearman -0.550), so the two components cancel
in the equal-weight mean. See AUD-06.

This computes four candidate replacements plus the current definition as a
reference, on the MHWS detector, so they can be compared on the same events.

    reference   mean of the DRIVER overlap (Hs and zos exceedances)
                — the current definition, carried over

    option 1    mean of the FULL-CRITERION overlap: days on which all three
                conditions hold simultaneously, Hs >= thr_hs AND zos >= thr_zos
                AND SWL > MHWS. Consistent with the event definition, which
                requires all three; counting only two of them is incoherent

    option 2    mean integrated intensity: the daily compound intensity summed
                over the full-criterion days, so magnitude and persistence enter
                as one quantity instead of two competing components

    option 3    mean integrated excess: metre-days of still water level above
                MHWS, the physically direct measure of time spent above the
                level the coast is adapted to

    option 4    p95 of the full-criterion overlap, i.e. the same definition as
                option 1 read at a different point of the distribution — the
                cheapest change, since it alters the statistic and not the
                quantity

Options 2 and 3 are time integrals and therefore not bounded by the daily
discretisation the way a day count is. Option 3 uses only the level term;
option 2 combines level and wave.

Read-only diagnostic. Adopts nothing and writes no production output.

Usage:
    python -m src.exploratory.audit_AUD_06_duration_variants

Output:
    outputs/audit/AUD-06_duration_variants/duration_variants_by_point.csv
    outputs/audit/AUD-06_duration_variants/duration_variants_summary.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.compound_detection.detection_mhws import (
    MIN_FINITE_DAYS,
    POINT_SOURCE,
    THRESHOLD_PCT,
    UNIFIED,
    compound_events_at_point,
)
from src.compound_detection.mhws_datum import mhws_at_points, still_water_level

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_mhws" / "compound_metrics_mhws.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-06_duration_variants"

INTENSITY_REF_LOW_PCT = 5.0
INTENSITY_REF_HIGH_PCT = 95.0

VARIANT_FIELDS = (
    "reference_driver_overlap_days",
    "opt1_full_criterion_days",
    "opt2_integrated_intensity",
    "opt3_integrated_excess_m_days",
    "opt4_p95_full_criterion_days",
)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    for path in (UNIFIED, POINT_SOURCE):
        if not path.exists():
            raise FileNotFoundError(path)

    with POINT_SOURCE.open() as f:
        catalogue = json.load(f)
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
    log.info("Extracting series ...")
    hs_all = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos_all = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    tide_all = ds["tide_daily_max"].isel(latitude=lat_idx, longitude=lon_idx).values
    log.info("Extraction complete.")

    # First pass: events plus the daily excesses needed to set the pooled
    # rescaling references for the integrated-intensity variant.
    per_point: list[dict | None] = []
    daily_wave_excess: list[float] = []
    daily_level_excess: list[float] = []

    for i in range(len(points)):
        hs = hs_all[:, i].astype(float)
        zos = zos_all[:, i].astype(float)
        tide = tide_all[:, i].astype(float)
        finite = np.isfinite(hs) & np.isfinite(zos) & np.isfinite(tide)
        if finite.sum() < MIN_FINITE_DAYS or not np.isfinite(mhws[i]):
            per_point.append(None)
            continue

        events, context = compound_events_at_point(
            hs=hs, zos=zos, tide=tide, finite=finite, mhws=float(mhws[i])
        )
        if not events:
            per_point.append({"events": [], "context": context})
            continue

        thr_hs = context["thr_hs_abs"]
        swl = still_water_level(zos, tide, zos_mean=context["zos_mean"])
        datum = float(mhws[i])

        for event in events:
            idx = event["overlap_indices"]
            full = idx[swl[idx] > datum]
            event["_full_idx"] = full
            if full.size:
                daily_wave_excess.extend((hs[full] - thr_hs).tolist())
                daily_level_excess.extend((swl[full] - datum).tolist())
        per_point.append(
            {"events": events, "context": context, "swl": swl, "hs": hs, "datum": datum}
        )

    if not daily_wave_excess:
        raise RuntimeError("No full-criterion days anywhere; refusing to write")

    refs = {
        "wave_low": float(np.percentile(daily_wave_excess, INTENSITY_REF_LOW_PCT)),
        "wave_high": float(np.percentile(daily_wave_excess, INTENSITY_REF_HIGH_PCT)),
        "level_low": float(np.percentile(daily_level_excess, INTENSITY_REF_LOW_PCT)),
        "level_high": float(np.percentile(daily_level_excess, INTENSITY_REF_HIGH_PCT)),
    }

    def _norm(values: np.ndarray, low: float, high: float) -> np.ndarray:
        if high <= low:
            return np.zeros_like(values)
        return np.clip((values - low) / (high - low), 0.0, 1.0)

    rows: list[dict] = []
    for i in range(len(points)):
        record = {
            "grid_lat": float(points["grid_lat"][i]),
            "grid_lon": float(points["grid_lon"][i]),
        }
        state = per_point[i]
        if state is None or not state.get("events"):
            rows.append({**record, **{f: np.nan for f in VARIANT_FIELDS},
                         "compound_count_total": 0 if state else np.nan})
            continue

        events = state["events"]
        swl, hs, datum = state["swl"], state["hs"], state["datum"]
        thr_hs = state["context"]["thr_hs_abs"]

        driver_days, full_days, integrated_intensity, integrated_excess = [], [], [], []
        for event in events:
            full = event["_full_idx"]
            driver_days.append(event["overlap_duration_days"])
            full_days.append(int(full.size))
            if full.size:
                wave_norm = _norm(hs[full] - thr_hs, refs["wave_low"], refs["wave_high"])
                level_norm = _norm(
                    swl[full] - datum, refs["level_low"], refs["level_high"]
                )
                integrated_intensity.append(float(np.sum(0.5 * (wave_norm + level_norm))))
                integrated_excess.append(float(np.sum(swl[full] - datum)))
            else:
                integrated_intensity.append(0.0)
                integrated_excess.append(0.0)

        rows.append(
            {
                **record,
                "compound_count_total": len(events),
                "reference_driver_overlap_days": float(np.mean(driver_days)),
                "opt1_full_criterion_days": float(np.mean(full_days)),
                "opt2_integrated_intensity": float(np.mean(integrated_intensity)),
                "opt3_integrated_excess_m_days": float(np.mean(integrated_excess)),
                "opt4_p95_full_criterion_days": float(np.percentile(full_days, 95)),
            }
        )

    df = pd.DataFrame(rows)

    # Validation: the reference variant must reproduce the production metric,
    # otherwise the recomputed events diverged from the committed detector.
    validation: dict[str, object] = {"status": "not_run"}
    if PRODUCTION_METRICS.exists():
        prod = pd.read_csv(PRODUCTION_METRICS)
        key = lambda d: list(zip(d["grid_lat"].round(6), d["grid_lon"].round(6)))  # noqa: E731
        df["_k"], prod["_k"] = key(df), key(prod)
        merged = df.merge(
            prod[["_k", "compound_count_total", "mean_overlap_duration"]],
            on="_k", suffixes=("", "_prod"),
        )
        count_diff = (
            merged["compound_count_total"] - merged["compound_count_total_prod"]
        ).abs()
        dur_diff = (
            merged["reference_driver_overlap_days"].round(2)
            - merged["mean_overlap_duration"]
        ).abs()
        validation = {
            "status": "ok" if count_diff.max() == 0 and dur_diff.max() <= 0.01 else "MISMATCH",
            "max_abs_count_difference": int(count_diff.max()),
            "max_abs_mean_duration_difference": float(dur_diff.max()),
            "points_compared": int(len(merged)),
        }
        df = df.drop(columns="_k")

    summary = {
        "generated_by": "src.exploratory.audit_AUD_06_duration_variants",
        "detector": "MHWS (zos ∩ Hs conditioned on SWL > MHWS)",
        "threshold_pct": THRESHOLD_PCT,
        "variants": {
            "reference_driver_overlap_days": "mean days with Hs and zos exceedance (current definition)",
            "opt1_full_criterion_days": "mean days with Hs and zos exceedance AND SWL > MHWS",
            "opt2_integrated_intensity": "mean sum over full-criterion days of 0.5*[norm(Hs excess) + norm(SWL excess)]",
            "opt3_integrated_excess_m_days": "mean sum over full-criterion days of (SWL - MHWS), metre-days",
            "opt4_p95_full_criterion_days": "95th percentile of the full-criterion day count",
        },
        "daily_excess_reference_percentiles": {k: round(v, 6) for k, v in refs.items()},
        "validation_against_production": validation,
        "statistics": {
            field: {
                "min": round(float(df[field].min()), 4),
                "max": round(float(df[field].max()), 4),
                "median": round(float(df[field].median()), 4),
                "spearman_vs_abs_latitude": round(
                    float(df[field].corr(df["grid_lat"].abs(), method="spearman")), 4
                ),
                "spearman_vs_frequency": round(
                    float(df[field].corr(df["compound_count_total"], method="spearman")), 4
                ),
            }
            for field in VARIANT_FIELDS
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "duration_variants_by_point.csv", index=False)
    with (OUT_DIR / "duration_variants_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(validation, indent=2))
    print()
    print(f"{'variante':<34}{'mín':>9}{'máx':>10}{'mediana':>10}{'ρ|lat|':>9}{'ρ freq':>9}")
    for field in VARIANT_FIELDS:
        s = summary["statistics"][field]
        print(
            f"{field:<34}{s['min']:>9.3f}{s['max']:>10.3f}{s['median']:>10.3f}"
            f"{s['spearman_vs_abs_latitude']:>9.3f}{s['spearman_vs_frequency']:>9.3f}"
        )


if __name__ == "__main__":
    main()
