"""
Unified site export for Step 3 — Hazard Characterization.

Merges metrics from all submodules into a single JSON consumed by the
results website's interactive maps. This replaces the previous limited
export in ``src/site/export_storm_maps_data.py`` with the full suite
of hazard characterization outputs.

Output fields per grid point:
    - Compound detection: counts, rates, intensity (normalized)
    - Duration & persistence: storm_count, mean/p95/max duration, intensity
    - Seasonality: monthly counts, peak month, seasonal split
    - Trends: Mann–Kendall slopes + significance for 8 annual series
    - EVA: GPD parameters + return levels (2, 5, 10, 20, 50 yr)
    - Dependence: τ, ρ, χ, χ̄

Output: site/public/data/hazard_characterization_grid_metrics.json

Usage:
    conda run -n osr python -m src.03_storm_catalog_generation.08_site_export.export
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from ..shared.catalog_utils import (
    load_catalog,
    load_run_metadata,
    get_period_years,
    HS_CATALOG,
    LEVEL_CATALOG,
)

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
OUTPUTS = ROOT / "outputs" / "storm_catalog"
SITE_DATA_DIR = ROOT / "site" / "public" / "data"

# Submodule output paths
COMPOUND_DIR = OUTPUTS / "compound"
DURATION_DIR = OUTPUTS / "duration_persistence"
SEASON_DIR = OUTPUTS / "seasonality"
TRENDS_DIR = OUTPUTS / "trends"
EVA_DIR = OUTPUTS / "eva"
DEPEND_DIR = OUTPUTS / "dependence"


def _load_json(path: Path) -> list[dict] | dict | None:
    """Load JSON or return None if missing."""
    if not path.exists():
        log.warning("Missing output: %s", path)
        return None
    with open(path) as f:
        return json.load(f)


def _index_by_latlon(data: list[dict]) -> dict[tuple, dict]:
    """Index list of grid-point dicts by (lat, lon) tuple."""
    idx = {}
    for item in data:
        key = (round(item["grid_lat"], 4), round(item["grid_lon"], 4))
        idx[key] = item
    return idx


def _safe_round(val, decimals=4):
    """Round if numeric, pass through None/str."""
    if val is None or isinstance(val, (str, bool)):
        return val
    try:
        return round(float(val), decimals)
    except (TypeError, ValueError):
        return val


def run_site_export() -> dict:
    """Merge all submodule outputs into a single site JSON.

    Returns the complete output structure.
    """
    run_meta = load_run_metadata()
    n_years = get_period_years(run_meta)
    hs_catalog = load_catalog(HS_CATALOG)

    # Load submodule outputs
    compound_data = _load_json(COMPOUND_DIR / "compound_catalog.json")
    duration_data = _load_json(DURATION_DIR / "duration_persistence_metrics.json")
    season_data = _load_json(SEASON_DIR / "seasonality_metrics.json")
    trends_data = _load_json(TRENDS_DIR / "trend_metrics.json")
    eva_data = _load_json(EVA_DIR / "eva_metrics.json")
    depend_data = _load_json(DEPEND_DIR / "dependence_metrics.json")

    # Index all by (lat, lon)
    compound_idx = _index_by_latlon(compound_data) if compound_data else {}
    duration_idx = _index_by_latlon(duration_data) if duration_data else {}
    season_idx = _index_by_latlon(season_data) if season_data else {}
    trends_idx = _index_by_latlon(trends_data) if trends_data else {}
    eva_idx = _index_by_latlon(eva_data) if eva_data else {}
    depend_idx = _index_by_latlon(depend_data) if depend_data else {}

    # Build grid points
    grid_points = []
    for gp in hs_catalog:
        lat = round(gp["grid_lat"], 4)
        lon = round(gp["grid_lon"], 4)
        key = (lat, lon)

        entry = {
            "lat": lat,
            "lon": lon,
            "municipality": gp.get("municipality"),
            "thr_hs": _safe_round(gp.get("thr_hs_abs")),
        }

        # ── Compound ──
        comp = compound_idx.get(key, {})
        entry["compound_count_total"] = comp.get("compound_count_total", 0)
        entry["compound_count_annual_mean"] = _safe_round(comp.get("compound_count_annual_mean"))
        entry["compound_mean_intensity_norm"] = _safe_round(comp.get("mean_compound_intensity_norm"))
        entry["compound_p95_intensity_norm"] = _safe_round(comp.get("p95_compound_intensity_norm"))
        entry["compound_max_intensity_norm"] = _safe_round(comp.get("max_compound_intensity_norm"))
        entry["compound_mean_overlap_duration"] = _safe_round(comp.get("mean_overlap_duration"))
        entry["compound_mean_peak_lag_days"] = _safe_round(comp.get("mean_peak_lag_days"))

        # ── Duration & persistence ──
        dur = duration_idx.get(key, {})
        for prefix in ("hs", "zos"):
            entry[f"{prefix}_storm_count_total"] = dur.get(f"{prefix}_storm_count_total")
            entry[f"{prefix}_storm_count_annual_mean"] = _safe_round(dur.get(f"{prefix}_storm_count_annual_mean"))
            entry[f"{prefix}_mean_duration_days"] = _safe_round(dur.get(f"{prefix}_mean_duration_days"))
            entry[f"{prefix}_p95_duration_days"] = _safe_round(dur.get(f"{prefix}_p95_duration_days"))
            entry[f"{prefix}_max_duration_days"] = _safe_round(dur.get(f"{prefix}_max_duration_days"))
            entry[f"{prefix}_mean_integrated_intensity"] = _safe_round(dur.get(f"{prefix}_mean_integrated_intensity"))
            entry[f"{prefix}_mean_interevent_time_days"] = _safe_round(dur.get(f"{prefix}_mean_interevent_time_days"))

        # ── Seasonality ──
        sea = season_idx.get(key, {})
        for prefix in ("hs", "zos", "compound"):
            entry[f"{prefix}_peak_month"] = sea.get(f"{prefix}_peak_month")
            mc = sea.get(f"{prefix}_monthly_counts")
            if mc is not None:
                entry[f"{prefix}_monthly_counts"] = mc
            sc = sea.get(f"{prefix}_seasonal_counts")
            if sc is not None:
                entry[f"{prefix}_seasonal_counts"] = sc

        # ── Trends ──
        tr = trends_idx.get(key, {})
        for metric in [
            "annual_hs_count", "annual_zos_count", "annual_compound_count",
            "annual_mean_hs_peak", "annual_mean_zos_peak",
            "annual_mean_hs_duration", "annual_mean_zos_duration",
            "annual_mean_overlap_duration",
        ]:
            entry[f"{metric}_slope"] = _safe_round(tr.get(f"{metric}_slope"), 6)
            entry[f"{metric}_p_value"] = _safe_round(tr.get(f"{metric}_p_value"), 6)
            entry[f"{metric}_significant"] = tr.get(f"{metric}_significant")
            entry[f"{metric}_direction"] = tr.get(f"{metric}_direction")

        # ── EVA ──
        ev = eva_idx.get(key, {})
        for prefix in ("hs", "zos"):
            entry[f"{prefix}_gpd_shape"] = _safe_round(ev.get(f"{prefix}_gpd_shape"), 6)
            entry[f"{prefix}_gpd_scale"] = _safe_round(ev.get(f"{prefix}_gpd_scale"), 6)
            entry[f"{prefix}_fit_success"] = ev.get(f"{prefix}_fit_success")
            rl = ev.get(f"{prefix}_return_levels", {})
            for T in [2, 5, 10, 20, 50]:
                entry[f"{prefix}_rl_{T}yr"] = _safe_round(rl.get(str(T)))

        # ── Dependence ──
        dep = depend_idx.get(key, {})
        entry["tau"] = _safe_round(dep.get("tau"))
        entry["rho"] = _safe_round(dep.get("rho"))
        entry["chi"] = _safe_round(dep.get("chi"))
        entry["chi_bar"] = _safe_round(dep.get("chi_bar"))
        entry["n_compound_pairs"] = dep.get("n_compound_pairs")

        grid_points.append(entry)

    # Count available modules
    modules_present = []
    for name, idx in [
        ("compound", compound_idx), ("duration_persistence", duration_idx),
        ("seasonality", season_idx), ("trends", trends_idx),
        ("eva", eva_idx), ("dependence", depend_idx),
    ]:
        if idx:
            modules_present.append(name)

    output = {
        "metadata": {
            "generated_by": "src.03_storm_catalog_generation.08_site_export.export",
            "generated_at": datetime.now().isoformat(),
            "period": f"{run_meta['period_full_series'][0]} to {run_meta['period_full_series'][1]}",
            "n_years": round(n_years, 2),
            "n_grid_points": len(grid_points),
            "modules_included": modules_present,
            "thr_hs_pct": run_meta.get("thr_hs_pct"),
            "thr_level_pct": run_meta.get("thr_level_pct"),
            "level_var": run_meta.get("level_var"),
            "level_is_tide_free": run_meta.get("level_is_tide_free"),
            "episode_max_gap_days": run_meta.get("episode_max_gap_days"),
            "tide_model": run_meta.get("tide_model"),
        },
        "grid_points": grid_points,
    }

    log.info(
        "Site export built: %d grid points, modules: %s",
        len(grid_points), modules_present,
    )
    return output


def save_site_export(output: dict, output_path: Path | None = None):
    """Save unified site JSON."""
    path = output_path or (SITE_DATA_DIR / "hazard_characterization_grid_metrics.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(output, f, separators=(",", ":"))
    size_mb = path.stat().st_size / (1024 * 1024)
    log.info("Saved site export: %s (%.1f MB)", path, size_mb)
    print(f"Saved: {path} ({size_mb:.1f} MB)")


def main():
    logging.basicConfig(level=logging.INFO)
    output = run_site_export()
    save_site_export(output)


if __name__ == "__main__":
    main()
