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

Compound intensity — excess over the local threshold, rescaled domain-wide:
  Raw peak values of Hs and SSH_total are in different physical units and have
  different spatial gradients (Hs increases offshore; SSH_total depends on shelf
  geometry and tidal regime). A simple additive combination (peak_hs + peak_ssh)
  creates a metric dominated by whichever variable has larger absolute values
  and is not comparable across grid points with different baseline magnitudes.

  Each driver therefore contributes how far it rose above its OWN local q90
  detection threshold, and that excess is rescaled against the domain-wide
  distribution of excesses:
    hs_excess  = hs_peak  - thr_hs(local)
    ssh_excess = ssh_peak - thr_ssh_total(local)
    hs_peak_norm  = clip((hs_excess  - Q05_E_hs ) / (Q95_E_hs  - Q05_E_hs ), 0, 1)
    ssh_peak_norm = clip((ssh_excess - Q05_E_ssh) / (Q95_E_ssh - Q05_E_ssh), 0, 1)
    compound_intensity_norm = 0.5 * (hs_peak_norm + ssh_peak_norm)

  This yields a dimensionless [0, 1] score comparable across all grid points.
  Q05/Q95 are computed from ALL compound event excesses across the full domain.

  Subtracting the local threshold is what keeps the astronomical tide out of the
  score: SSH_total = zos + daily-maximum tide, so the ABSOLUTE sea-level peak is
  almost entirely set by the tidal regime (R^2 = 0.998 regressing the mean peak
  on the local threshold). This matches the canonical definition in
  src/03_storm_catalog_generation/02_compound_detection/detection.py — the two
  products must not diverge.

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
# The production level catalogue is segmented on tide-free ``zos``.  Keep the
# legacy ``ssh`` output keys below because the existing site API consumes them.
SSH_CATALOG = CATALOG_DIR / "catalog_zos_storms.json"
METADATA_FILE = CATALOG_DIR / "logs" / "run_metadata.json"
UNIFIED_DATASET = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
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
    """Compute summary metrics from classified storms at one grid point.

    Compound intensity fields that require domain-wide normalization are
    populated later by ``normalize_compound_intensity()``; they are set
    to None here as placeholders.
    """

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

        # ── Compound intensity (normalized — filled later) ──
        "compound_mean_intensity_norm": None,
        "compound_p95_intensity_norm": None,
        "compound_max_intensity_norm": None,
        # Normalized components (filled later)
        "compound_mean_hs_peak_norm": None,
        "compound_mean_ssh_peak_norm": None,
        # Raw peaks retained for auditability
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
        hs_peaks = [c["compound_peak_hs"] for c in compound]
        ssh_peaks = [c["compound_peak_ssh_total"] for c in compound]
        metrics["compound_mean_peak_hs"] = round(float(np.mean(hs_peaks)), 4)
        metrics["compound_mean_peak_ssh_total"] = round(float(np.mean(ssh_peaks)), 4)

    return metrics


def normalize_compound_intensity(
    all_classified: list[dict],
    results: list[dict],
) -> dict:
    """Compute domain-wide normalization, then fill compound intensity fields.

    Returns a dict with the normalization reference values used.
    """
    # Collect ALL compound event excesses over the local thresholds
    all_hs_excess = []
    all_ssh_excess = []
    for classified, entry in zip(all_classified, results):
        thr_hs = entry.get("thr_hs")
        thr_ssh = entry.get("thr_ssh")
        if thr_hs is None or thr_ssh is None:
            continue
        for c in classified["compound"]:
            all_hs_excess.append(c["compound_peak_hs"] - thr_hs)
            all_ssh_excess.append(c["compound_peak_ssh_total"] - thr_ssh)

    if not all_hs_excess:
        return {"hs_ref_low": None, "hs_ref_high": None,
                "ssh_ref_low": None, "ssh_ref_high": None}

    hs_ref_low = float(np.percentile(all_hs_excess, 5))
    hs_ref_high = float(np.percentile(all_hs_excess, 95))
    ssh_ref_low = float(np.percentile(all_ssh_excess, 5))
    ssh_ref_high = float(np.percentile(all_ssh_excess, 95))

    hs_range = max(hs_ref_high - hs_ref_low, 1e-9)
    ssh_range = max(ssh_ref_high - ssh_ref_low, 1e-9)

    print(f"\n  Normalization refs (domain-wide compound excesses over local q90):")
    print(f"    Hs:  Q05={hs_ref_low:.4f} m,  Q95={hs_ref_high:.4f} m")
    print(f"    SSH: Q05={ssh_ref_low:.4f} m,  Q95={ssh_ref_high:.4f} m")

    # For each grid point, normalize compound events and compute stats
    for classified, entry in zip(all_classified, results):
        compound = classified["compound"]
        thr_hs = entry.get("thr_hs")
        thr_ssh = entry.get("thr_ssh")
        if not compound or thr_hs is None or thr_ssh is None:
            continue

        int_norms = []
        hs_norms = []
        ssh_norms = []
        for c in compound:
            hn = np.clip(
                (c["compound_peak_hs"] - thr_hs - hs_ref_low) / hs_range, 0, 1
            )
            sn = np.clip(
                (c["compound_peak_ssh_total"] - thr_ssh - ssh_ref_low) / ssh_range,
                0,
                1,
            )
            ci = 0.5 * (hn + sn)
            int_norms.append(float(ci))
            hs_norms.append(float(hn))
            ssh_norms.append(float(sn))

        entry["compound_mean_intensity_norm"] = round(float(np.mean(int_norms)), 4)
        entry["compound_p95_intensity_norm"] = round(float(np.percentile(int_norms, 95)), 4)
        entry["compound_max_intensity_norm"] = round(float(np.max(int_norms)), 4)
        entry["compound_mean_hs_peak_norm"] = round(float(np.mean(hs_norms)), 4)
        entry["compound_mean_ssh_peak_norm"] = round(float(np.mean(ssh_norms)), 4)

    return {
        "hs_ref_low": round(hs_ref_low, 4),
        "hs_ref_high": round(hs_ref_high, 4),
        "ssh_ref_low": round(ssh_ref_low, 4),
        "ssh_ref_high": round(ssh_ref_high, 4),
    }


def compute_zos_diagnostic(
    results: list[dict],
    thr_ssh_pct: float,
    n_years: float,
    episode_max_gap_days: int,
) -> int:
    """Compute zos-raw (no tide) diagnostic storm metrics.

    Opens the unified dataset, extracts the ``zos`` variable, and runs
    threshold–exceedance–clustering at each grid point already present
    in *results*.  Metrics are written directly into each result entry.

    This is a **diagnostic / comparison** layer.  The canonical
    sea-level analysis uses SSH_total (= zos + tide_daily_max).

    Returns the domain-wide total storm count.
    """
    import xarray as xr

    print("\n── zos diagnostic layer (raw dynamic SSH, no tide) ─────────────")
    ds = xr.open_dataset(UNIFIED_DATASET)
    lats = ds.latitude.values
    lons = ds.longitude.values
    zos_data = ds["zos"].values  # (time, lat, lon) float32
    ds.close()
    print(f"  Loaded zos: shape={zos_data.shape}")

    pct_q = thr_ssh_pct * 100  # 0.9 → 90
    n_zos_total = 0

    for i, entry in enumerate(results):
        lat_idx = int(np.argmin(np.abs(lats - entry["lat"])))
        lon_idx = int(np.argmin(np.abs(lons - entry["lon"])))
        series = zos_data[:, lat_idx, lon_idx]
        valid = ~np.isnan(series)

        if int(valid.sum()) == 0:
            entry["zos_raw_thr"] = None
            entry["zos_raw_count_total"] = 0
            entry["zos_raw_count_annual_mean"] = 0.0
            entry["zos_raw_mean_peak"] = None
            entry["zos_raw_p95_peak"] = None
            entry["zos_raw_max_peak"] = None
            continue

        thr = float(np.nanpercentile(series, pct_q))

        # Exceedance indices (NaN → not exceedance)
        exceed_idx = np.where((series >= thr) & valid)[0]

        if len(exceed_idx) == 0:
            entry["zos_raw_thr"] = round(thr, 4)
            entry["zos_raw_count_total"] = 0
            entry["zos_raw_count_annual_mean"] = 0.0
            entry["zos_raw_mean_peak"] = None
            entry["zos_raw_p95_peak"] = None
            entry["zos_raw_max_peak"] = None
            continue

        # Cluster episodes (same gap convention as Step 3)
        episodes: list[list[int]] = []
        current = [exceed_idx[0]]
        for idx in exceed_idx[1:]:
            if idx - current[-1] <= episode_max_gap_days + 1:
                current.append(idx)
            else:
                episodes.append(current)
                current = [idx]
        episodes.append(current)

        n_storms = len(episodes)
        n_zos_total += n_storms

        peaks = np.array([float(np.nanmax(series[ep])) for ep in episodes])

        entry["zos_raw_thr"] = round(thr, 4)
        entry["zos_raw_count_total"] = n_storms
        entry["zos_raw_count_annual_mean"] = round(n_storms / n_years, 2)
        entry["zos_raw_mean_peak"] = round(float(peaks.mean()), 4)
        entry["zos_raw_p95_peak"] = round(float(np.percentile(peaks, 95)), 4)
        entry["zos_raw_max_peak"] = round(float(peaks.max()), 4)

        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(results)} grid points...")

    print(f"  Total zos_raw storms: {n_zos_total:,}")
    return n_zos_total


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

    # ── Process each grid point (pass 1: classify + per-point metrics) ─────
    results = []
    all_classified = []
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
            "thr_ssh": round(ssh_gp.get("thr_zos_abs", 0), 4),
            **metrics,
        }
        results.append(entry)
        all_classified.append(classified)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(hs_catalog)} grid points...")

    print(f"\nDone: {len(results)} grid points")
    print(f"  Hs_only total:        {n_hs_only_total:,}")
    print(f"  SSH_total_only total:  {n_ssh_only_total:,}")
    print(f"  Compound total:        {n_compound_total:,}")

    # ── Pass 2: domain-wide normalization of compound intensity ─────────────
    norm_refs = normalize_compound_intensity(all_classified, results)

    # ── Pass 3: zos diagnostic layer (raw dynamic SSH, no tide) ────────────
    n_zos_raw_total = compute_zos_diagnostic(
        results, run_meta["thr_level_pct"], n_years, run_meta["episode_max_gap_days"]
    )

    # ── Build output ───────────────────────────────────────────────────────
    output = {
        "metadata": {
            "generated_by": "src/site/export_storm_maps_data.py",
            "period": f"{period_start} to {period_end}",
            "n_years": round(n_years, 2),
            "n_grid_points": len(results),
            "thr_hs_pct": run_meta["thr_hs_pct"],
            # Backward-compatible site key; this is now the zos percentile.
            "thr_ssh_pct": run_meta["thr_level_pct"],
            "level_var": run_meta.get("level_var", "zos"),
            "level_is_tide_free": run_meta.get("level_is_tide_free", True),
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
            "compound_intensity_definition": (
                "Normalized compound intensity: 0.5 * (hs_peak_norm + ssh_peak_norm), "
                "where each component is the excess of the event peak over its own "
                "local q90 detection threshold, scaled to [0, 1] using the domain-wide "
                "Q05/Q95 of those excesses. Dimensionless and comparable across grid "
                "points. Subtracting the local threshold keeps the astronomical tide "
                "out of the score. Matches the canonical definition in "
                "src/03_storm_catalog_generation/02_compound_detection/detection.py."
            ),
            "compound_intensity_normalization": norm_refs,
            "zos_raw_definition": (
                "DIAGNOSTIC ONLY — not the canonical sea-level analysis. "
                "Storm detection applied to raw dynamic SSH (zos from GLORYS12) "
                "without tidal component, using local q90 threshold computed "
                "on the zos series itself. For comparison with SSH_total only."
            ),
            "n_hs_only_total": n_hs_only_total,
            "n_ssh_only_total": n_ssh_only_total,
            "n_compound_total": n_compound_total,
            "n_zos_raw_total": n_zos_raw_total,
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
