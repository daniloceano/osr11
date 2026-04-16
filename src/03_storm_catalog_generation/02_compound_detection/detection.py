"""
Compound event detection for Step 3 — Hazard Characterization.

Identifies compound coastal events as temporal overlaps between independent
Hₛ and SSH_total storm episodes at the same grid point.

Compound event definition (Zscheischler et al. 2020):
    A compound event exists at a grid point when an Hₛ storm and an SSH_total
    storm overlap in time (share ≥ 1 calendar day). The compound event spans
    the union of overlapping days. If multiple Hₛ storms overlap the same
    SSH_total storm (or vice versa), they form a single compound event group.

    - Hs_only:        Hₛ storm with no temporal overlap with any SSH_total storm
    - SSH_total_only:  SSH_total storm with no temporal overlap with any Hₛ storm
    - compound:        Group of Hₛ + SSH_total storms sharing ≥ 1 calendar day

Normalized compound intensity (domain-wide):
    hs_peak_norm  = clip((hs_peak - Q05_hs) / (Q95_hs - Q05_hs), 0, 1)
    ssh_peak_norm = clip((ssh_peak - Q05_ssh) / (Q95_ssh - Q05_ssh), 0, 1)
    compound_intensity_norm = 0.5 * (hs_peak_norm + ssh_peak_norm)

References:
    - Zscheischler et al. (2020). A typology of compound weather and climate
      events. Nature Reviews Earth & Environment, 1, 333–347.
    - Camus et al. (2021). Compound coastal flooding potential.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    storm_days,
    build_grid_index,
    safe_percentile,
    save_json,
    HS_CATALOG,
    SSH_CATALOG,
)

log = logging.getLogger(__name__)

# ── Output paths ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT / "outputs" / "storm_catalog" / "compound"


def classify_storms_at_point(
    hs_storms: list[dict],
    ssh_storms: list[dict],
) -> dict[str, Any]:
    """Classify storms at a single grid point into Hs_only, SSH_total_only, compound.

    Uses union-find style grouping on temporal overlap (≥ 1 shared calendar day).

    Returns dict with:
        - hs_only: list of Hs storms not in any compound event
        - ssh_only: list of SSH_total storms not in any compound event
        - compound_events: list of compound event dicts with detailed attributes
    """
    # Build day→storm index
    hs_by_day: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(hs_storms):
        for d in storm_days(s):
            hs_by_day[d].append(i)

    ssh_by_day: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(ssh_storms):
        for d in storm_days(s):
            ssh_by_day[d].append(i)

    # Union-find grouping via shared overlap days
    overlap_days = set(hs_by_day.keys()) & set(ssh_by_day.keys())

    hs_to_group: dict[int, int] = {}
    ssh_to_group: dict[int, int] = {}
    compound_groups: list[tuple[set[int], set[int]]] = []

    for day in overlap_days:
        h_indices = hs_by_day[day]
        s_indices = ssh_by_day[day]
        if not h_indices or not s_indices:
            continue

        groups_to_merge = set()
        for hi in h_indices:
            if hi in hs_to_group:
                groups_to_merge.add(hs_to_group[hi])
        for si in s_indices:
            if si in ssh_to_group:
                groups_to_merge.add(ssh_to_group[si])

        if not groups_to_merge:
            g_idx = len(compound_groups)
            compound_groups.append((set(h_indices), set(s_indices)))
        elif len(groups_to_merge) == 1:
            g_idx = groups_to_merge.pop()
            compound_groups[g_idx][0].update(h_indices)
            compound_groups[g_idx][1].update(s_indices)
        else:
            merged_hs = set(h_indices)
            merged_ssh = set(s_indices)
            for gi in groups_to_merge:
                merged_hs.update(compound_groups[gi][0])
                merged_ssh.update(compound_groups[gi][1])
            keep = min(groups_to_merge)
            compound_groups[keep] = (merged_hs, merged_ssh)
            for gi in groups_to_merge:
                if gi != keep:
                    compound_groups[gi] = (set(), set())
            g_idx = keep

        for hi in compound_groups[g_idx][0]:
            hs_to_group[hi] = g_idx
        for si in compound_groups[g_idx][1]:
            ssh_to_group[si] = g_idx

    # Collect compound storm indices
    hs_in_compound: set[int] = set()
    ssh_in_compound: set[int] = set()
    for hs_set, ssh_set in compound_groups:
        hs_in_compound.update(hs_set)
        ssh_in_compound.update(ssh_set)

    # Classify
    hs_only = [s for i, s in enumerate(hs_storms) if i not in hs_in_compound]
    ssh_only = [s for i, s in enumerate(ssh_storms) if i not in ssh_in_compound]

    # Build detailed compound events
    compound_events = []
    for hs_set, ssh_set in compound_groups:
        if not hs_set or not ssh_set:
            continue
        compound_events.append(
            _build_compound_event(hs_storms, ssh_storms, hs_set, ssh_set)
        )

    return {
        "hs_only": hs_only,
        "ssh_only": ssh_only,
        "compound_events": compound_events,
    }


def _build_compound_event(
    hs_storms: list[dict],
    ssh_storms: list[dict],
    hs_indices: set[int],
    ssh_indices: set[int],
) -> dict[str, Any]:
    """Build a detailed compound event record from overlapping storms."""
    # Collect all days covered by Hs and SSH storms in this group
    hs_days: set[str] = set()
    ssh_days: set[str] = set()
    for i in hs_indices:
        hs_days.update(storm_days(hs_storms[i]))
    for i in ssh_indices:
        ssh_days.update(storm_days(ssh_storms[i]))

    overlap = sorted(hs_days & ssh_days)
    union = sorted(hs_days | ssh_days)

    # Peak values
    hs_peaks = [hs_storms[i]["peak_value"] for i in hs_indices]
    ssh_peaks = [ssh_storms[i]["peak_value"] for i in ssh_indices]
    peak_hs = max(hs_peaks)
    peak_ssh = max(ssh_peaks)

    # Peak dates
    hs_peak_dates = [hs_storms[i].get("peak_date", hs_storms[i]["date_start"]) for i in hs_indices]
    ssh_peak_dates = [ssh_storms[i].get("peak_date", ssh_storms[i]["date_start"]) for i in ssh_indices]

    # Peak lag: days between Hs peak and SSH peak (positive = Hs peaks first)
    hs_peak_date = max(
        ((hs_storms[i]["peak_value"], hs_storms[i].get("peak_date", hs_storms[i]["date_start"]))
         for i in hs_indices),
        key=lambda x: x[0],
    )[1]
    ssh_peak_date = max(
        ((ssh_storms[i]["peak_value"], ssh_storms[i].get("peak_date", ssh_storms[i]["date_start"]))
         for i in ssh_indices),
        key=lambda x: x[0],
    )[1]

    try:
        peak_lag_days = (
            date.fromisoformat(hs_peak_date) - date.fromisoformat(ssh_peak_date)
        ).days
    except (ValueError, TypeError):
        peak_lag_days = None

    # Integrated intensities
    hs_integ = sum(
        hs_storms[i].get("integrated_intensity", 0) for i in hs_indices
    )
    ssh_integ = sum(
        ssh_storms[i].get("integrated_intensity", 0) for i in ssh_indices
    )

    return {
        "date_start": overlap[0] if overlap else union[0],
        "date_end": overlap[-1] if overlap else union[-1],
        "overlap_duration_days": len(overlap),
        "union_duration_days": len(union),
        "n_hs_storms": len(hs_indices),
        "n_ssh_storms": len(ssh_indices),
        "peak_hs": round(peak_hs, 4),
        "peak_ssh_total": round(peak_ssh, 4),
        "peak_hs_date": hs_peak_date,
        "peak_ssh_date": ssh_peak_date,
        "peak_lag_days": peak_lag_days,
        "hs_integrated_intensity": round(hs_integ, 4),
        "ssh_integrated_intensity": round(ssh_integ, 4),
    }


def compute_compound_metrics(
    classified: dict[str, Any],
    n_years: float,
) -> dict[str, Any]:
    """Compute per-grid-point compound summary metrics.

    Returns dict with all required compound metrics.
    """
    events = classified["compound_events"]
    n = len(events)

    if n == 0:
        return {
            "compound_count_total": 0,
            "compound_count_annual_mean": 0.0,
            "mean_overlap_duration": None,
            "p95_overlap_duration": None,
            "max_overlap_duration": None,
            "mean_peak_lag_days": None,
            "mean_compound_intensity_norm": None,
            "p95_compound_intensity_norm": None,
            "max_compound_intensity_norm": None,
        }

    overlaps = [e["overlap_duration_days"] for e in events]
    lags = [e["peak_lag_days"] for e in events if e["peak_lag_days"] is not None]

    return {
        "compound_count_total": n,
        "compound_count_annual_mean": round(n / n_years, 2) if n_years > 0 else None,
        "mean_overlap_duration": round(float(np.mean(overlaps)), 2),
        "p95_overlap_duration": round(float(np.percentile(overlaps, 95)), 2),
        "max_overlap_duration": int(np.max(overlaps)),
        "mean_peak_lag_days": round(float(np.mean(lags)), 2) if lags else None,
        # Normalized intensity fields — populated by normalize_compound_intensity()
        "mean_compound_intensity_norm": None,
        "p95_compound_intensity_norm": None,
        "max_compound_intensity_norm": None,
    }


def normalize_compound_intensity(
    all_classified: list[dict],
    all_metrics: list[dict],
) -> dict[str, float | None]:
    """Compute domain-wide normalization and fill intensity fields.

    Returns normalization reference values.
    """
    all_hs_peaks = []
    all_ssh_peaks = []
    for classified in all_classified:
        for e in classified["compound_events"]:
            all_hs_peaks.append(e["peak_hs"])
            all_ssh_peaks.append(e["peak_ssh_total"])

    if not all_hs_peaks:
        return {"hs_ref_low": None, "hs_ref_high": None,
                "ssh_ref_low": None, "ssh_ref_high": None}

    hs_ref_low = float(np.percentile(all_hs_peaks, 5))
    hs_ref_high = float(np.percentile(all_hs_peaks, 95))
    ssh_ref_low = float(np.percentile(all_ssh_peaks, 5))
    ssh_ref_high = float(np.percentile(all_ssh_peaks, 95))

    hs_range = max(hs_ref_high - hs_ref_low, 1e-9)
    ssh_range = max(ssh_ref_high - ssh_ref_low, 1e-9)

    for classified, metrics in zip(all_classified, all_metrics):
        events = classified["compound_events"]
        if not events:
            continue

        int_norms = []
        for e in events:
            hn = float(np.clip((e["peak_hs"] - hs_ref_low) / hs_range, 0, 1))
            sn = float(np.clip((e["peak_ssh_total"] - ssh_ref_low) / ssh_range, 0, 1))
            int_norms.append(0.5 * (hn + sn))

        metrics["mean_compound_intensity_norm"] = round(float(np.mean(int_norms)), 4)
        metrics["p95_compound_intensity_norm"] = round(float(np.percentile(int_norms, 95)), 4)
        metrics["max_compound_intensity_norm"] = round(float(np.max(int_norms)), 4)

    return {
        "hs_ref_low": round(hs_ref_low, 4),
        "hs_ref_high": round(hs_ref_high, 4),
        "ssh_ref_low": round(ssh_ref_low, 4),
        "ssh_ref_high": round(ssh_ref_high, 4),
    }


def run_compound_detection(
    hs_catalog_path: Path | None = None,
    ssh_catalog_path: Path | None = None,
) -> dict[str, Any]:
    """Run compound detection over all grid points.

    Returns a dict with:
        - grid_results: list of per-grid-point dicts (metrics + classified events)
        - normalization_refs: domain-wide normalization reference values
        - summary: domain-wide aggregate statistics
    """
    hs_catalog = load_catalog(hs_catalog_path or HS_CATALOG)
    ssh_catalog = load_catalog(ssh_catalog_path or SSH_CATALOG)
    run_meta = load_run_metadata()
    n_years = get_period_years(run_meta)

    ssh_index = build_grid_index(ssh_catalog)

    grid_results = []
    all_classified = []
    all_metrics = []

    for hs_gp in hs_catalog:
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]
        key = (round(lat, 5), round(lon, 5))

        ssh_gp = ssh_index.get(key)
        if ssh_gp is None:
            log.warning("No SSH_total data for (%.4f, %.4f), skipping", lat, lon)
            continue

        classified = classify_storms_at_point(
            hs_gp.get("storms", []),
            ssh_gp.get("storms", []),
        )
        metrics = compute_compound_metrics(classified, n_years)

        grid_results.append({
            "grid_lat": round(lat, 4),
            "grid_lon": round(lon, 4),
            "municipality": hs_gp.get("municipality"),
            "thr_hs_abs": hs_gp.get("thr_hs_abs"),
            "thr_ssh_total_abs": ssh_gp.get("thr_ssh_total_abs"),
            **metrics,
            "compound_events": classified["compound_events"],
        })
        all_classified.append(classified)
        all_metrics.append(metrics)

    # Domain-wide normalization
    norm_refs = normalize_compound_intensity(all_classified, all_metrics)

    # Update grid_results with normalized metrics
    for gr, m in zip(grid_results, all_metrics):
        gr["mean_compound_intensity_norm"] = m["mean_compound_intensity_norm"]
        gr["p95_compound_intensity_norm"] = m["p95_compound_intensity_norm"]
        gr["max_compound_intensity_norm"] = m["max_compound_intensity_norm"]

    # Summary
    total_compound = sum(m["compound_count_total"] for m in all_metrics)
    total_hs_only = sum(len(c["hs_only"]) for c in all_classified)
    total_ssh_only = sum(len(c["ssh_only"]) for c in all_classified)

    summary = {
        "n_grid_points": len(grid_results),
        "n_compound_total": total_compound,
        "n_hs_only_total": total_hs_only,
        "n_ssh_only_total": total_ssh_only,
        "period": f"{run_meta['period_full_series'][0]} to {run_meta['period_full_series'][1]}",
        "n_years": round(n_years, 2),
    }

    log.info(
        "Compound detection complete: %d compound, %d Hs-only, %d SSH-only across %d grid points",
        total_compound, total_hs_only, total_ssh_only, len(grid_results),
    )

    return {
        "grid_results": grid_results,
        "normalization_refs": norm_refs,
        "summary": summary,
    }


def save_compound_results(results: dict[str, Any], output_dir: Path | None = None):
    """Save compound detection results to disk."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    # Save compound catalog (with events for downstream use)
    save_json(results["grid_results"], out / "compound_catalog.json")

    # Save summary
    save_json({
        "summary": results["summary"],
        "normalization_refs": results["normalization_refs"],
    }, out / "compound_summary.json")

    # Save metrics-only CSV (without event details)
    import pandas as pd
    rows = []
    for gr in results["grid_results"]:
        row = {k: v for k, v in gr.items() if k != "compound_events"}
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out / "compound_metrics.csv", index=False)
    log.info("Compound results saved to %s", out)
