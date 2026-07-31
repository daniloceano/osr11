"""AUD-03 diagnostic: what the daily-phase mismatch still costs, under the current method.

``zos`` from GLORYS12 is a single sample at 00:00 UTC; ``tide_daily_max`` from
FES2022 is the largest astronomical tide of the day, which occurs at an
arbitrary hour. Adding them produces a level that is not realised at any real
instant. There is no sub-daily ``zos`` to correct this with, so the mismatch is
inherent to the input, not to the analysis.

What changed is where the mismatch enters. The superseded method segmented level
episodes on ``SSH_total = zos(00Z) + tide_daily_max``, so the phase error sat
inside the detection threshold itself. Since 2026-07-31 the level catalogue is
segmented on tide-free ``zos``, and the sum only re-enters through

* the acceptance gate, ``max(SWL) > HAT``, and
* the level term of the integrated severity, ``SWL - HAT``,

with ``SWL(d) = (zos(d) - mean(zos)) + tide_daily_max(d)``.

The error is bounded without any new data. Under linear interpolation between
consecutive 00:00 UTC samples, the true ``zos`` at the hour of high water lies
between ``zos(d)`` and ``zos(d+1)``. Substituting each bound gives the widest
and narrowest ``SWL`` compatible with the record, and the question becomes how
often the gate decision differs between them.

Usage:
    python -m src.exploratory.audit_AUD_03_ssh_phase_coherence

Output:
    outputs/audit/AUD-03_ssh_phase_coherence/phase_error_by_point.csv
    outputs/audit/AUD-03_ssh_phase_coherence/band_summary.csv
    outputs/audit/AUD-03_ssh_phase_coherence/diagnosis_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
HAT_METRICS = (
    ROOT / "outputs" / "storm_catalog" / "compound_hat" / "compound_metrics_hat.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-03_ssh_phase_coherence"

#: Latitude bands used throughout the audit, north to south.
BANDS = (
    ("AP", 1.0, 6.01),
    ("N eq.", -2.0, 1.0),
    ("NE", -12.0, -2.0),
    ("ES/BA-S", -21.0, -12.0),
    ("SP/RJ", -25.0, -21.0),
    ("SC/PR", -29.0, -25.0),
    ("RS", -35.0, -29.0),
)


def _run_survival(
    current: np.ndarray, alternative: np.ndarray
) -> tuple[int, int]:
    """Count runs of consecutive passing days, and how many lose every day.

    ``current`` and ``alternative`` are boolean day masks. A run is a maximal
    block of consecutive ``True`` in ``current``; it is lost when no day inside
    it is ``True`` in ``alternative``.
    """
    padded = np.concatenate(([False], current, [False]))
    edges = np.flatnonzero(padded[1:] != padded[:-1])
    starts, ends = edges[0::2], edges[1::2]
    if starts.size == 0:
        return 0, 0
    lost = sum(1 for s, e in zip(starts, ends) if not alternative[s:e].any())
    return int(starts.size), int(lost)


def _band_of(lat: float) -> str:
    for name, low, high in BANDS:
        if low <= lat < high:
            return name
    return "out of band"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(HAT_METRICS)
    dataset = xr.open_dataset(UNIFIED)
    lats = xr.DataArray(metrics["grid_lat"].to_numpy(), dims="point")
    lons = xr.DataArray(metrics["grid_lon"].to_numpy(), dims="point")
    subset = (
        dataset[["zos", "tide_daily_max"]]
        .sel(latitude=lats, longitude=lons, method="nearest")
        .load()
    )
    zos = subset["zos"].values
    tide = subset["tide_daily_max"].values

    zos_mean = np.nanmean(zos, axis=0)
    demeaned = zos - zos_mean

    # The three level series. ``current`` is what the pipeline uses; ``low`` and
    # ``high`` bracket every value the true high-water zos can take under linear
    # interpolation between consecutive daily samples.
    next_day = np.vstack([demeaned[1:], demeaned[-1:]])
    swl_current = demeaned + tide
    swl_low = np.minimum(demeaned, next_day) + tide
    swl_high = np.maximum(demeaned, next_day) + tide
    swl_mid = 0.5 * (demeaned + next_day) + tide

    hat = metrics["hat_m"].to_numpy(dtype=float)

    n_points = zos.shape[1]
    rows = []
    for j in range(n_points):
        finite = np.isfinite(swl_current[:, j]) & np.isfinite(swl_high[:, j])
        if finite.sum() < 365:
            continue
        envelope = (swl_high[:, j] - swl_low[:, j])[finite]
        daily_step = np.abs(np.diff(demeaned[:, j][np.isfinite(demeaned[:, j])]))

        gate_current = swl_current[finite, j] > hat[j]
        gate_low = swl_low[finite, j] > hat[j]
        gate_high = swl_high[finite, j] > hat[j]
        # Two directed flip counts, each relative to what the pipeline does
        # today. A day that passes now but fails at the lower bound might be a
        # spurious pass; a day that fails now but passes at the upper bound
        # might be a missed one.
        pass_now_fails_low = int(np.sum(gate_current & ~gate_low))
        fails_now_passes_high = int(np.sum(~gate_current & gate_high))

        # The gate is applied per candidate event, over the days a wave and a
        # level episode share, and one qualifying day is enough. Counting
        # isolated days therefore overstates the effect. Grouping consecutive
        # gate-passing days into runs is a closer proxy for that unit: a run
        # survives if any of its days still passes at the lower bound.
        runs_total, runs_lost = _run_survival(gate_current, gate_low)

        rho = float(
            spearmanr(swl_current[finite, j], swl_mid[finite, j])[0]
        )

        rows.append(
            {
                "grid_lat": float(metrics["grid_lat"].iloc[j]),
                "grid_lon": float(metrics["grid_lon"].iloc[j]),
                "band": _band_of(float(metrics["grid_lat"].iloc[j])),
                "hat_m": float(hat[j]),
                "zos_std_m": float(np.nanstd(demeaned[:, j])),
                "tide_daily_max_mean_m": float(np.nanmean(tide[:, j])),
                "phase_envelope_mean_m": float(np.mean(envelope)),
                "phase_envelope_p95_m": float(np.percentile(envelope, 95)),
                "phase_envelope_over_zos_std": float(
                    np.mean(envelope) / max(np.nanstd(demeaned[:, j]), 1e-9)
                ),
                "median_abs_daily_zos_step_m": float(np.median(daily_step)),
                "days_total": int(finite.sum()),
                "days_passing_gate_current": int(gate_current.sum()),
                "days_passing_gate_lower_bound": int(gate_low.sum()),
                "days_passing_gate_upper_bound": int(gate_high.sum()),
                "days_pass_now_fail_at_lower_bound": pass_now_fails_low,
                "days_fail_now_pass_at_upper_bound": fails_now_passes_high,
                "share_of_passing_days_at_risk": float(
                    pass_now_fails_low / max(int(gate_current.sum()), 1)
                ),
                "gate_passing_runs": runs_total,
                "gate_passing_runs_lost_at_lower_bound": runs_lost,
                "share_of_runs_at_risk": float(runs_lost / max(runs_total, 1)),
                "spearman_current_vs_midpoint": rho,
            }
        )

    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "phase_error_by_point.csv", index=False)

    band_summary = (
        table.groupby("band")
        .agg(
            n_points=("grid_lat", "size"),
            median_tide_daily_max_m=("tide_daily_max_mean_m", "median"),
            median_zos_std_m=("zos_std_m", "median"),
            median_phase_envelope_m=("phase_envelope_mean_m", "median"),
            median_phase_envelope_over_zos_std=("phase_envelope_over_zos_std", "median"),
            median_spearman_current_vs_midpoint=("spearman_current_vs_midpoint", "median"),
            total_days=("days_total", "sum"),
            total_days_passing_gate_current=("days_passing_gate_current", "sum"),
            total_days_pass_now_fail_at_lower_bound=(
                "days_pass_now_fail_at_lower_bound", "sum"
            ),
            total_days_fail_now_pass_at_upper_bound=(
                "days_fail_now_pass_at_upper_bound", "sum"
            ),
            total_runs=("gate_passing_runs", "sum"),
            total_runs_lost=("gate_passing_runs_lost_at_lower_bound", "sum"),
            median_spearman_below_threshold=(
                "spearman_current_vs_midpoint", lambda s: float((s < 0.99).sum())
            ),
        )
        .reset_index()
        .rename(columns={"median_spearman_below_threshold": "n_points_rho_below_0.99"})
    )
    band_summary["share_of_runs_at_risk"] = band_summary[
        "total_runs_lost"
    ] / band_summary["total_runs"].clip(lower=1)
    band_summary["share_of_passing_days_at_risk"] = band_summary[
        "total_days_pass_now_fail_at_lower_bound"
    ] / band_summary["total_days_passing_gate_current"].clip(lower=1)
    band_summary["gate_pass_rate"] = band_summary[
        "total_days_passing_gate_current"
    ] / band_summary["total_days"].clip(lower=1)
    band_summary.to_csv(OUT_DIR / "band_summary.csv", index=False)

    summary = {
        "generated_by": "src.exploratory.audit_AUD_03_ssh_phase_coherence",
        "scope_under_the_current_method": {
            "level_detection_threshold": (
                "local q0.99 of tide-free zos. The phase mismatch does NOT "
                "enter here: no tide is added before the percentile is taken."
            ),
            "hat_gate": (
                "max(SWL) > HAT, with SWL = (zos - mean(zos)) + tide_daily_max. "
                "The mismatch enters here."
            ),
            "integrated_severity": (
                "level term is SWL - HAT on full-criterion days. The mismatch "
                "enters here."
            ),
        },
        "points_analysed": int(len(table)),
        "phase_envelope_m": {
            "note": (
                "Width of the interval within which the true high-water zos must "
                "lie, given only daily 00:00 UTC sampling and linear "
                "interpolation. This is the magnitude of the phase error, in "
                "metres, per day."
            ),
            "domain_median": float(table["phase_envelope_mean_m"].median()),
            "domain_p95": float(table["phase_envelope_p95_m"].median()),
            "domain_max_point_mean": float(table["phase_envelope_mean_m"].max()),
        },
        "phase_envelope_relative_to_local_zos_variability": {
            "domain_median": float(table["phase_envelope_over_zos_std"].median()),
            "domain_max": float(table["phase_envelope_over_zos_std"].max()),
        },
        "rank_preservation": {
            "note": (
                "Spearman correlation between the SWL series actually used and "
                "the mid-interval alternative, per point. The ordering of days "
                "is what the gate and the severity integral depend on."
            ),
            "median_over_points": float(
                table["spearman_current_vs_midpoint"].median()
            ),
            "minimum_over_points": float(table["spearman_current_vs_midpoint"].min()),
            "n_points_below_0.99": int(
                (table["spearman_current_vs_midpoint"] < 0.99).sum()
            ),
        },
        "gate_decision_stability": {
            "note": (
                "Day-level upper bound on the effect of the phase mismatch. A "
                "day counted here sits close enough to HAT that substituting "
                "the other end of the interpolation interval would flip its "
                "accept/reject decision. This OVERSTATES the effect on the "
                "product: the gate is applied per candidate event, over the "
                "days shared by a wave and a level episode, and it needs only "
                "one qualifying day, so an event survives unless every one of "
                "its days flips at once."
            ),
            "total_days": int(table["days_total"].sum()),
            "total_days_passing_gate_current": int(
                table["days_passing_gate_current"].sum()
            ),
            "total_days_pass_now_fail_at_lower_bound": int(
                table["days_pass_now_fail_at_lower_bound"].sum()
            ),
            "total_days_fail_now_pass_at_upper_bound": int(
                table["days_fail_now_pass_at_upper_bound"].sum()
            ),
            "share_of_passing_days_at_risk": float(
                table["days_pass_now_fail_at_lower_bound"].sum()
                / max(table["days_passing_gate_current"].sum(), 1)
            ),
            "run_level": {
                "note": (
                    "Consecutive gate-passing days grouped into runs, a closer "
                    "proxy for the unit the gate actually decides on. A run is "
                    "lost only if every one of its days flips at once."
                ),
                "total_runs": int(table["gate_passing_runs"].sum()),
                "runs_lost_at_lower_bound": int(
                    table["gate_passing_runs_lost_at_lower_bound"].sum()
                ),
                "share_of_runs_at_risk": float(
                    table["gate_passing_runs_lost_at_lower_bound"].sum()
                    / max(table["gate_passing_runs"].sum(), 1)
                ),
            },
        },
        "band_summary": band_summary.to_dict(orient="records"),
        "tide_gauge_comparison": {
            "performed": False,
            "reason": (
                "No observed sea-level series is present in the repository. "
                "data/raw/ holds GLORYS12, WAVERYS and IBGE only, and "
                "'data/reported events/' holds a documentary storm-surge event "
                "list for Santa Catarina with no water levels. A GLOSS/IBGE or "
                "Marinha do Brasil tide-gauge comparison would require a new "
                "acquisition with its own provenance record, which is outside "
                "the scope of this diagnostic and is recorded as remaining "
                "uncertainty."
            ),
        },
    }
    (OUT_DIR / "diagnosis_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
