"""
Export storm catalog metrics for the OSR11 scientific results website.

Reads Step 3 storm catalogs (Hs, SSH_total), derives compound events via
temporal overlap detection, and exports per-grid-point summary metrics
as a single JSON file consumed by the site's /results/storm-maps page.

Compound event definition (Step 4 minimal):
  A compound event exists at a grid point when an Hs storm and an SSH_total
  storm overlap in time (i.e., share at least one calendar day). The compound
  event spans the union of overlapping days. If multiple Hs storms overlap
  the same SSH_total storm (or vice versa), the resulting compound event
  covers the full union of all overlapping storms.

  - Hs_only:        Hs storm with no temporal overlap with any SSH_total storm
  - SSH_total_only:  SSH_total storm with no temporal overlap with any Hs storm
  - compound:        Group of Hs + SSH_total storms sharing at least one day

Intensity definitions:
  - For Hs_only:        peak Hs during the storm
  - For SSH_total_only: peak SSH_total during the storm
  - For compound:       joint_intensity = peak_hs + peak_ssh_total (additive)
  - compound also reports: compound_peak_hs, compound_peak_ssh_total

Period: full series from run_metadata.json (1993-01-01 to 2025-12-31)

Output: site/public/data/storm_maps_grid_metrics.json

Usage:
  conda run -n osr11 python -m src.site.export_storm_maps_data
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = ROOT / "outputs" / "storm_catalog"
HS_CATALOG = CATALOG_DIR / "catalog_hs_storms.json"
SSH_CATALOG = CATALOG_DIR / "catalog_ssh_total_storms.json"
METADATA_FILE = CATALOG_DIR / "logs" / "run_metadata.json"
OUTPUT_DIR = ROOT / "site" / "public" / "data"
OUTPUT_FILE = OUTPUT_DIR / "storm_maps_grid_metrics.json"


def load_catalog(path: Path) -> list[dict]:
    """Load a storm catalog JSON (list of grid-point dicts)."""
    with open(path) as f:
        return json.load(f)


def storm_days(storm: dict) -> set[str]:
    """Return set of calendar-day strings covered by a storm."""
    ts = storm.get("time_series", {})
    dates = ts.get("dates", [])
    if dates:
        return set(dates)
    # Fallback: generate from date_start / date_end
    from datetime import date, timedelta
    start = date.fromisoformat(storm["date_start"])
    end = date.fromisoformat(storm["date_end"])
    return {(start + timedelta(days=d)).isoformat() for d in range((end - start).days + 1)}


def classify_storms_at_point(hs_storms: list[dict], ssh_storms: list[dict]) -> dict:
    """
    Classify storms at a single grid point into Hs_only, SSH_total_only, compound.

    Returns dict with lists of classified events and summary metrics.
    """
    # Build day→storm index
    hs_by_day = defaultdict(list)
    for i, s in enumerate(hs_storms):
        for d in storm_days(s):
            hs_by_day[d].append(i)

    ssh_by_day = defaultdict(list)
    for i, s in enumerate(ssh_storms):
        for d in storm_days(s):
            ssh_by_day[d].append(i)

    # Find overlapping pairs via shared days
    hs_in_compound = set()
    ssh_in_compound = set()
    # compound groups: sets of (hs_indices, ssh_indices)
    # Use union-find style grouping
    compound_groups = []  # list of (set_of_hs_idx, set_of_ssh_idx)

    all_days = set(hs_by_day.keys()) | set(ssh_by_day.keys())
    overlap_days = set(hs_by_day.keys()) & set(ssh_by_day.keys())

    # For each overlap day, link the hs and ssh storms
    hs_to_group = {}
    ssh_to_group = {}

    for day in overlap_days:
        h_indices = hs_by_day[day]
        s_indices = ssh_by_day[day]
        if not h_indices or not s_indices:
            continue

        # Find which existing groups these storms belong to
        groups_to_merge = set()
        for hi in h_indices:
            if hi in hs_to_group:
                groups_to_merge.add(hs_to_group[hi])
        for si in s_indices:
            if si in ssh_to_group:
                groups_to_merge.add(ssh_to_group[si])

        if not groups_to_merge:
            # New group
            g_idx = len(compound_groups)
            compound_groups.append((set(h_indices), set(s_indices)))
        elif len(groups_to_merge) == 1:
            # Add to existing group
            g_idx = groups_to_merge.pop()
            compound_groups[g_idx][0].update(h_indices)
            compound_groups[g_idx][1].update(s_indices)
        else:
            # Merge multiple groups
            merged_hs = set(h_indices)
            merged_ssh = set(s_indices)
            for gi in groups_to_merge:
                merged_hs.update(compound_groups[gi][0])
                merged_ssh.update(compound_groups[gi][1])
            # Replace the lowest-index group and clear others
            keep = min(groups_to_merge)
            compound_groups[keep] = (merged_hs, merged_ssh)
            for gi in groups_to_merge:
                if gi != keep:
                    compound_groups[gi] = (set(), set())
            g_idx = keep

        # Update index maps
        for hi in compound_groups[g_idx][0]:
            hs_to_group[hi] = g_idx
        for si in compound_groups[g_idx][1]:
            ssh_to_group[si] = g_idx

    # Collect compound storm indices
    for hs_set, ssh_set in compound_groups:
        hs_in_compound.update(hs_set)
        ssh_in_compound.update(ssh_set)

    # Classify
    hs_only_storms = [s for i, s in enumerate(hs_storms) if i not in hs_in_compound]
    ssh_only_storms = [s for i, s in enumerate(ssh_storms) if i not in ssh_in_compound]

    # Compound events: extract metrics per group
    compound_events = []
    for hs_set, ssh_set in compound_groups:
        if not hs_set or not ssh_set:
            continue
        hs_peaks = [hs_storms[i]["peak_value"] for i in hs_set]
        ssh_peaks = [ssh_storms[i]["peak_value"] for i in ssh_set]
        compound_peak_hs = max(hs_peaks)
        compound_peak_ssh = max(ssh_peaks)
        compound_events.append({
            "compound_peak_hs": compound_peak_hs,
            "compound_peak_ssh_total": compound_peak_ssh,
            "joint_intensity": compound_peak_hs + compound_peak_ssh,
        })

    return {
        "hs_only": hs_only_storms,
        "ssh_only": ssh_only_storms,
        "compound": compound_events,
    }


def percentile_safe(values: list[float], q: float) -> float | None:
    """Compute percentile, returning None for empty lists."""
    if not values:
        return None
    return float(np.percentile(values, q))


def compute_grid_metrics(classified: dict, n_years: float) -> dict:
    """Compute summary metrics from classified storms at one grid point."""

    hs_only = classified["hs_only"]
    ssh_only = classified["ssh_only"]
    compound = classified["compound"]

    # ── Occurrence ──
    n_hs = len(hs_only)
    n_ssh = len(ssh_only)
    n_compound = len(compound)

    metrics = {
        # Hs_only occurrence
        "hs_only_count_total": n_hs,
        "hs_only_count_annual_mean": round(n_hs / n_years, 2) if n_years > 0 else None,

        # SSH_total_only occurrence
        "ssh_only_count_total": n_ssh,
        "ssh_only_count_annual_mean": round(n_ssh / n_years, 2) if n_years > 0 else None,

        # Compound occurrence
        "compound_count_total": n_compound,
        "compound_count_annual_mean": round(n_compound / n_years, 2) if n_years > 0 else None,

        # ── Hs_only intensity ──
        "hs_only_mean_peak": None,
        "hs_only_p95_peak": None,
        "hs_only_max_peak": None,

        # ── SSH_total_only intensity ──
        "ssh_only_mean_peak": None,
        "ssh_only_p95_peak": None,
        "ssh_only_max_peak": None,

        # ── Compound intensity ──
        "compound_mean_joint_intensity": None,
        "compound_p95_joint_intensity": None,
        "compound_max_joint_intensity": None,
        "compound_mean_peak_hs": None,
        "compound_mean_peak_ssh_total": None,
    }

    if n_hs > 0:
        peaks = [s["peak_value"] for s in hs_only]
        metrics["hs_only_mean_peak"] = round(float(np.mean(peaks)), 4)
        metrics["hs_only_p95_peak"] = round(percentile_safe(peaks, 95), 4)
        metrics["hs_only_max_peak"] = round(float(np.max(peaks)), 4)

    if n_ssh > 0:
        peaks = [s["peak_value"] for s in ssh_only]
        metrics["ssh_only_mean_peak"] = round(float(np.mean(peaks)), 4)
        metrics["ssh_only_p95_peak"] = round(percentile_safe(peaks, 95), 4)
        metrics["ssh_only_max_peak"] = round(float(np.max(peaks)), 4)

    if n_compound > 0:
        ji = [c["joint_intensity"] for c in compound]
        hs_peaks = [c["compound_peak_hs"] for c in compound]
        ssh_peaks = [c["compound_peak_ssh_total"] for c in compound]
        metrics["compound_mean_joint_intensity"] = round(float(np.mean(ji)), 4)
        metrics["compound_p95_joint_intensity"] = round(percentile_safe(ji, 95), 4)
        metrics["compound_max_joint_intensity"] = round(float(np.max(ji)), 4)
        metrics["compound_mean_peak_hs"] = round(float(np.mean(hs_peaks)), 4)
        metrics["compound_mean_peak_ssh_total"] = round(float(np.mean(ssh_peaks)), 4)

    return metrics


def main():
    # ── Load catalogs ──────────────────────────────────────────────────────
    print("Loading Hs catalog...")
    hs_catalog = load_catalog(HS_CATALOG)
    print(f"  {len(hs_catalog)} grid points")

    print("Loading SSH_total catalog...")
    ssh_catalog = load_catalog(SSH_CATALOG)
    print(f"  {len(ssh_catalog)} grid points")

    # ── Load run metadata ──────────────────────────────────────────────────
    with open(METADATA_FILE) as f:
        run_meta = json.load(f)

    period_start = run_meta["period_full_series"][0]
    period_end = run_meta["period_full_series"][1]
    from datetime import date
    d0 = date.fromisoformat(period_start)
    d1 = date.fromisoformat(period_end)
    n_years = (d1 - d0).days / 365.25
    print(f"Period: {period_start} to {period_end} ({n_years:.1f} years)")

    # ── Index SSH catalog by (lat, lon) for fast lookup ────────────────────
    ssh_index = {}
    for gp in ssh_catalog:
        key = (round(gp["grid_lat"], 5), round(gp["grid_lon"], 5))
        ssh_index[key] = gp

    # ── Process each grid point ────────────────────────────────────────────
    results = []
    n_compound_total = 0
    n_hs_only_total = 0
    n_ssh_only_total = 0

    for i, hs_gp in enumerate(hs_catalog):
        lat = hs_gp["grid_lat"]
        lon = hs_gp["grid_lon"]
        key = (round(lat, 5), round(lon, 5))

        ssh_gp = ssh_index.get(key)
        if ssh_gp is None:
            print(f"  WARNING: no SSH_total data for ({lat}, {lon}), skipping")
            continue

        classified = classify_storms_at_point(
            hs_gp.get("storms", []),
            ssh_gp.get("storms", []),
        )
        metrics = compute_grid_metrics(classified, n_years)

        n_hs_only_total += metrics["hs_only_count_total"]
        n_ssh_only_total += metrics["ssh_only_count_total"]
        n_compound_total += metrics["compound_count_total"]

        entry = {
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "thr_hs": round(hs_gp.get("thr_hs_abs", 0), 4),
            "thr_ssh": round(ssh_gp.get("thr_ssh_total_abs", 0), 4),
            **metrics,
        }
        results.append(entry)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(hs_catalog)} grid points...")

    print(f"\nDone: {len(results)} grid points")
    print(f"  Hs_only total:        {n_hs_only_total:,}")
    print(f"  SSH_total_only total:  {n_ssh_only_total:,}")
    print(f"  Compound total:        {n_compound_total:,}")

    # ── Build output ───────────────────────────────────────────────────────
    output = {
        "metadata": {
            "generated_by": "src/site/export_storm_maps_data.py",
            "period": f"{period_start} to {period_end}",
            "n_years": round(n_years, 2),
            "n_grid_points": len(results),
            "thr_hs_pct": run_meta["thr_hs_pct"],
            "thr_ssh_pct": run_meta["thr_ssh_pct"],
            "episode_max_gap_days": run_meta["episode_max_gap_days"],
            "tide_model": run_meta["tide_model"],
            "compound_definition": (
                "Temporal overlap: a compound event exists when an Hs storm and "
                "an SSH_total storm at the same grid point share at least one "
                "calendar day."
            ),
            "hs_only_definition": (
                "Hs storm with no temporal overlap with any SSH_total storm "
                "at the same grid point."
            ),
            "ssh_only_definition": (
                "SSH_total storm with no temporal overlap with any Hs storm "
                "at the same grid point."
            ),
            "joint_intensity_definition": (
                "Additive: peak_hs + peak_ssh_total within the compound event."
            ),
            "n_hs_only_total": n_hs_only_total,
            "n_ssh_only_total": n_ssh_only_total,
            "n_compound_total": n_compound_total,
        },
        "grid_points": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"\nSaved: {OUTPUT_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
