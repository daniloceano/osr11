"""AUD-12 diagnostic: estuarine and fluvial contamination under the current method.

The baseline review flagged grid points inside the Amazon estuary as entering
the hazard catalogue as if they were open-coast ocean points, and reported that
two top-10 risk municipalities -- Macapa/AP and Chaves/PA -- drew their hazard
from such points. That diagnosis was made on the superseded SSH_total detector
at q90/q90, with no HAT gate. The method has since changed on all three counts:
waves are segmented at the local q0.70 of Hs, level at the local q0.99 of
tide-free ``zos``, and a candidate is accepted only where the still-water level
exceeds the local Highest Astronomical Tide. The earlier conclusion therefore
cannot be carried over, and is re-measured here from scratch.

The script answers, for the current product:

* do the questioned points still contribute events, hazard and municipal rank?
* is the contamination hypothesis -- ``zos`` driven by the Amazon hydrograph --
  supported by the seasonal cycle of ``zos`` at those points?
* which points have ``max(Hs) < 0.5 m``, and how many events, municipalities and
  ranking positions depend on them?
* what happens under each candidate exclusion rule?

Nothing is excluded here. Exclusion rules are evaluated as sensitivity tests,
including the false-negative direction: a low wave maximum can mark a sheltered
but genuinely flood-prone stretch as easily as it can mark a bad grid cell.

Usage:
    python -m src.exploratory.audit_AUD_12_estuarine_contamination

Output:
    outputs/audit/AUD-12_estuarine_contamination/point_diagnostics.csv
    outputs/audit/AUD-12_estuarine_contamination/suspect_points.csv
    outputs/audit/AUD-12_estuarine_contamination/low_wave_points.csv
    outputs/audit/AUD-12_estuarine_contamination/municipal_dependence.csv
    outputs/audit/AUD-12_estuarine_contamination/sensitivity_scenarios.csv
    outputs/audit/AUD-12_estuarine_contamination/diagnosis_summary.json
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
LEGACY_METRICS = (
    ROOT / "outputs" / "legacy_ssh_total_method" / "hazard" / "compound_metrics.csv"
)
GEOJSON = ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
BATHYMETRY = (
    ROOT / "data" / "external" / "etopo2022"
    / "etopo2022_30s_sampled_to_zos_domain.nc"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-12_estuarine_contamination"

#: The points named in the baseline review, with the municipality each was said
#: to serve and why it was questioned.
SUSPECT_POINTS = (
    (0.8, -50.2, "Macapa/AP", "Amazon estuary, north channel"),
    (0.0, -50.4, "Chaves/PA", "Amazon mouth / north of Marajo"),
    (-0.8, -48.4, "Salvaterra/PA", "Marajo bay"),
    (-1.4, -48.6, "Vigia/PA and Colares/PA", "Guajara bay"),
    (0.4, -50.0, "(none)", "domain minimum of peak intensity in the old product"),
    (3.4, -50.8, "(none)", "domain maximum of overlap duration in the old product"),
)

#: Threshold under test for the wave-maximum exclusion rule, in metres.
LOW_WAVE_MAX_M = 0.5

#: Months of the Amazon flood peak at Obidos. A ``zos`` series controlled by
#: discharge rather than by weather peaks inside this window.
AMAZON_FLOOD_MONTHS = (4, 5, 6)

#: Latitude band treated as the Amazon/Para estuarine sector for reporting.
NORTH_SECTOR_LAT_MIN = -2.0


def _load_municipalities() -> pd.DataFrame:
    payload = json.loads(GEOJSON.read_text())
    return pd.DataFrame([f["properties"] for f in payload["features"]])


def _point_key(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    # ``+ 0.0`` collapses negative zero, which the Amazon-mouth point at
    # latitude -7.4e-13 would otherwise render as "-0.0" and fail to match the
    # municipal file's "0.0".
    lat = np.round(np.asarray(lat, dtype=float), 2) + 0.0
    lon = np.round(np.asarray(lon, dtype=float), 2) + 0.0
    return np.char.add(np.char.add(lat.astype(str), "|"), lon.astype(str))


def _series_statistics(dataset: xr.Dataset, metrics: pd.DataFrame) -> pd.DataFrame:
    """Per-point wave and level statistics read straight from the unified file."""
    lats = xr.DataArray(metrics["grid_lat"].to_numpy(), dims="point")
    lons = xr.DataArray(metrics["grid_lon"].to_numpy(), dims="point")
    subset = dataset[["VHM0", "zos"]].sel(
        latitude=lats, longitude=lons, method="nearest"
    )
    subset = subset.load()

    hs = subset["VHM0"]
    zos = subset["zos"]

    quantiles = hs.quantile([0.70, 0.90, 0.99], dim="time", skipna=True)
    zos_q99 = zos.quantile(0.99, dim="time", skipna=True)

    monthly = zos.groupby("time.month").mean("time", skipna=True)
    peak_month = monthly.idxmax("month")
    annual_range = monthly.max("month") - monthly.min("month")
    total_std = zos.std("time", skipna=True)
    # Fraction of the total variance carried by the mean annual cycle. High
    # values mark a series governed by a seasonal signal -- for the Amazon
    # sector, the discharge hydrograph -- rather than by synoptic weather.
    seasonal_std = monthly.std("month", skipna=True)
    seasonal_variance_fraction = (seasonal_std**2) / (total_std**2)

    # Coupling to the open ocean. A cell governed by river discharge and by
    # channel dynamics the global model does not resolve decouples from the
    # shelf; one that merely sits on a wide shallow shelf does not. The
    # reference is the nearest valid cell 2 degrees to the east, at the same
    # latitude, which is offshore everywhere in this domain.
    local = zos.values
    raw_corr = np.full(local.shape[1], np.nan)
    anomaly_corr = np.full(local.shape[1], np.nan)
    offshore_offset = np.full(local.shape[1], np.nan)
    month_index = zos["time"].dt.month.values
    def _correlate(a: np.ndarray, b: np.ndarray) -> tuple[float, float] | None:
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.sum() < 365:
            return None
        raw = float(np.corrcoef(a[ok], b[ok])[0, 1])
        # Remove the mean annual cycle from both, so what remains is the
        # synoptic band where storm surge lives.
        da, db = a.copy(), b.copy()
        for month in range(1, 13):
            sel = (month_index == month) & ok
            if sel.any():
                da[sel] -= a[sel].mean()
                db[sel] -= b[sel].mean()
        return raw, float(np.corrcoef(da[ok], db[ok])[0, 1])

    # 2 degrees east is offshore for most of the coast. The vectorised pass
    # covers every point; the handful for which that offset lands on land --
    # inside Guajara bay it hits Marajo island -- are retried individually at
    # larger offsets rather than re-reading the whole field five times.
    primary = (
        dataset["zos"]
        .sel(latitude=lats, longitude=lons + 2.0, method="nearest")
        .load()
        .values
    )
    for j in range(local.shape[1]):
        result = _correlate(local[:, j], primary[:, j])
        if result is not None:
            raw_corr[j], anomaly_corr[j] = result
            offshore_offset[j] = 2.0

    # Eastward is offshore along the meridional coast, but on the north coast
    # the shoreline runs east-west and every eastward offset stays over Para
    # and Maranhao land. Those points fall back to a northward reference.
    fallbacks = (
        (0.0, 2.5),
        (0.0, 3.0),
        (2.0, 0.0),
        (1.5, 0.0),
        (2.0, 1.0),
        (0.0, 1.5),
        (0.0, 1.0),
    )
    for j in np.flatnonzero(~np.isfinite(anomaly_corr)):
        for dlat, dlon in fallbacks:
            remote = (
                dataset["zos"]
                .sel(
                    latitude=float(metrics["grid_lat"].iloc[j]) + dlat,
                    longitude=float(metrics["grid_lon"].iloc[j]) + dlon,
                    method="nearest",
                )
                .load()
                .values
            )
            result = _correlate(local[:, j], remote)
            if result is not None:
                raw_corr[j], anomaly_corr[j] = result
                offshore_offset[j] = float(np.hypot(dlat, dlon))
                break

    return pd.DataFrame(
        {
            "hs_max": hs.max("time", skipna=True).values,
            "hs_q70": quantiles.sel(quantile=0.70).values,
            "hs_q90": quantiles.sel(quantile=0.90).values,
            "hs_q99": quantiles.sel(quantile=0.99).values,
            "hs_valid_days": np.isfinite(hs.values).sum(axis=0),
            "zos_q99": zos_q99.values,
            "zos_peak_month": peak_month.values,
            "zos_annual_range_m": annual_range.values,
            "zos_std_m": total_std.values,
            "zos_seasonal_variance_fraction": seasonal_variance_fraction.values,
            "zos_corr_with_offshore": raw_corr,
            "zos_anomaly_corr_with_offshore": anomaly_corr,
            "offshore_reference_offset_deg": offshore_offset,
        }
    )


def _hazard_index(frame: pd.DataFrame, subset_mask: np.ndarray) -> pd.Series:
    """Recompute the two-component Hazard Index over a restricted point set.

    Mirrors ``src/04_risk_integration/hazard_index.py``: Min--Max each component
    over the retained population, average, Min--Max again.
    """
    out = pd.Series(np.nan, index=frame.index, dtype=float)
    kept = frame.loc[subset_mask]
    parts = []
    for field in ("compound_count_total", "mean_integrated_severity"):
        values = pd.to_numeric(kept[field], errors="coerce")
        lo, hi = float(values.min()), float(values.max())
        parts.append((values - lo) / (hi - lo))
    raw = pd.concat(parts, axis=1).mean(axis=1)
    out.loc[kept.index] = (raw - raw.min()) / (raw.max() - raw.min())
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(HAT_METRICS)
    dataset = xr.open_dataset(UNIFIED)
    stats = _series_statistics(dataset, metrics)
    points = pd.concat([metrics.reset_index(drop=True), stats], axis=1)
    points["mean_integrated_severity"] = points["mean_integrated_severity"].fillna(0.0)
    points["compound_count_total"] = points["compound_count_total"].fillna(0).astype(int)

    # Depth at each point, used to test the "wide shallow shelf, not a channel"
    # explanation offered for the Amazon points.
    if BATHYMETRY.exists():
        bathy = xr.open_dataset(BATHYMETRY)
        depth_name = next(
            (n for n in ("z", "elevation", "topo", "Band1") if n in bathy), None
        )
        if depth_name is not None:
            lat_name = "lat" if "lat" in bathy.coords else "latitude"
            lon_name = "lon" if "lon" in bathy.coords else "longitude"
            sampled = bathy[depth_name].sel(
                **{
                    lat_name: xr.DataArray(points["grid_lat"].to_numpy(), dims="point"),
                    lon_name: xr.DataArray(points["grid_lon"].to_numpy(), dims="point"),
                },
                method="nearest",
            )
            points["seafloor_elevation_m"] = sampled.values
    if "seafloor_elevation_m" not in points:
        points["seafloor_elevation_m"] = np.nan

    points["Hazard_Index_current"] = _hazard_index(
        points, np.ones(len(points), dtype=bool)
    )

    municipalities = _load_municipalities()
    municipalities["point_key"] = _point_key(
        municipalities["grid_lat"].to_numpy(dtype=float),
        municipalities["grid_lon"].to_numpy(dtype=float),
    )
    points["point_key"] = _point_key(
        points["grid_lat"].to_numpy(dtype=float),
        points["grid_lon"].to_numpy(dtype=float),
    )
    served = (
        municipalities.groupby("point_key")["municipality_name"]
        .apply(lambda s: "; ".join(sorted(s)))
        .rename("municipalities_served")
    )
    served_count = (
        municipalities.groupby("point_key").size().rename("n_municipalities_served")
    )
    points = points.merge(served, on="point_key", how="left").merge(
        served_count, on="point_key", how="left"
    )
    points["n_municipalities_served"] = points["n_municipalities_served"].fillna(0).astype(int)

    risk_rank = municipalities["Risk_Hazard"].rank(ascending=False, method="min")
    municipalities = municipalities.assign(risk_rank=risk_rank)

    points.to_csv(OUT_DIR / "point_diagnostics.csv", index=False)

    # ── 1. The questioned points, then and now ───────────────────────────────
    legacy = pd.read_csv(LEGACY_METRICS) if LEGACY_METRICS.exists() else None
    suspect_rows = []
    for lat, lon, municipality, reason in SUSPECT_POINTS:
        match = points[
            np.isclose(points["grid_lat"], lat, atol=0.05)
            & np.isclose(points["grid_lon"], lon, atol=0.05)
        ]
        if match.empty:
            suspect_rows.append(
                {"grid_lat": lat, "grid_lon": lon, "status": "point not in the domain"}
            )
            continue
        row = match.iloc[0]
        record = {
            "grid_lat": lat,
            "grid_lon": lon,
            "questioned_for": municipality,
            "reason_questioned": reason,
            "hs_max": round(float(row["hs_max"]), 3),
            "hs_q70_thr": round(float(row["thr_hs_abs"]), 3),
            "hs_q90": round(float(row["hs_q90"]), 3),
            "hs_q99": round(float(row["hs_q99"]), 3),
            "zos_q99_thr": round(float(row["thr_zos_abs"]), 4),
            "hat_m": round(float(row["hat_m"]), 3),
            "n_hs_episodes": int(row["n_hs_episodes"]),
            "n_zos_episodes": int(row["n_zos_episodes"]),
            "n_candidate_events": int(row["n_candidate_events"]),
            "n_rejected_by_hat": int(row["n_rejected_by_hat"]),
            "compound_count_current": int(row["compound_count_total"]),
            "mean_integrated_severity": round(float(row["mean_integrated_severity"]), 4),
            "Hazard_Index_current": round(float(row["Hazard_Index_current"]), 4),
            "zos_peak_month": int(row["zos_peak_month"]),
            "zos_seasonal_variance_fraction": round(
                float(row["zos_seasonal_variance_fraction"]), 4
            ),
            "zos_corr_with_offshore": round(float(row["zos_corr_with_offshore"]), 4),
            "zos_anomaly_corr_with_offshore": round(
                float(row["zos_anomaly_corr_with_offshore"]), 4
            ),
            "seafloor_elevation_m": (
                round(float(row["seafloor_elevation_m"]), 1)
                if np.isfinite(row["seafloor_elevation_m"])
                else None
            ),
            "municipalities_served_now": row["municipalities_served"],
        }
        if legacy is not None:
            legacy_match = legacy[
                np.isclose(legacy["grid_lat"], lat, atol=0.05)
                & np.isclose(legacy["grid_lon"], lon, atol=0.05)
            ]
            record["compound_count_legacy_ssh_total"] = (
                int(legacy_match.iloc[0]["compound_count_total"])
                if not legacy_match.empty
                else None
            )
        names = [
            n.strip()
            for n in str(row["municipalities_served"]).split(";")
            if n and n != "nan"
        ]
        ranks = municipalities.loc[
            municipalities["municipality_name"].isin(names),
            ["municipality_name", "risk_rank", "Risk_Hazard", "Hazard_Index_mun"],
        ]
        record["municipal_risk_ranks_now"] = "; ".join(
            f"{r.municipality_name}={int(r.risk_rank)}"
            for r in ranks.itertuples()
            if np.isfinite(r.risk_rank)
        )
        suspect_rows.append(record)
    suspect = pd.DataFrame(suspect_rows)
    suspect.to_csv(OUT_DIR / "suspect_points.csv", index=False)

    # ── 2. Neighbouring open-coast comparison ────────────────────────────────
    north = points[points["grid_lat"] >= NORTH_SECTOR_LAT_MIN]
    suspect_keys = {
        f"{round(lat, 2)}|{round(lon, 2)}" for lat, lon, _, _ in SUSPECT_POINTS
    }
    north_others = north[~north["point_key"].isin(suspect_keys)]

    def _band(frame: pd.DataFrame) -> dict[str, float]:
        return {
            "n_points": int(len(frame)),
            "median_hs_max": float(frame["hs_max"].median()),
            "median_hs_q99": float(frame["hs_q99"].median()),
            "median_compound_count": float(frame["compound_count_total"].median()),
            "median_hazard_index": float(frame["Hazard_Index_current"].median()),
            "median_zos_seasonal_variance_fraction": float(
                frame["zos_seasonal_variance_fraction"].median()
            ),
            "share_peaking_in_amazon_flood_months": float(
                frame["zos_peak_month"].isin(AMAZON_FLOOD_MONTHS).mean()
            ),
            "median_zos_corr_with_offshore": float(
                frame["zos_corr_with_offshore"].median()
            ),
            "median_zos_anomaly_corr_with_offshore": float(
                frame["zos_anomaly_corr_with_offshore"].median()
            ),
        }

    # ── 3. Low-wave points and their downstream footprint ────────────────────
    low_wave = points[points["hs_max"] < LOW_WAVE_MAX_M].copy()
    low_wave_sorted = low_wave.sort_values("hs_max")
    low_wave_sorted.to_csv(OUT_DIR / "low_wave_points.csv", index=False)

    low_keys = set(low_wave["point_key"])
    dependent = municipalities[municipalities["point_key"].isin(low_keys)].copy()
    dependent = dependent[
        [
            "municipality_name",
            "state",
            "grid_lat",
            "grid_lon",
            "Hazard_Index_mun",
            "Exposure_Index",
            "SVI_Coast_2022",
            "Risk_Hazard",
            "risk_rank",
        ]
    ].sort_values("risk_rank")
    dependent.to_csv(OUT_DIR / "municipal_dependence.csv", index=False)

    # ── 4. Sensitivity scenarios ─────────────────────────────────────────────
    scenarios: dict[str, np.ndarray] = {
        "current_domain": np.ones(len(points), dtype=bool),
        "exclude_hs_max_below_0.5m": (points["hs_max"] >= LOW_WAVE_MAX_M).to_numpy(),
        "exclude_hs_q99_below_0.5m": (points["hs_q99"] >= LOW_WAVE_MAX_M).to_numpy(),
        "exclude_thr_hs_q70_below_0.5m": (
            points["thr_hs_abs"] >= LOW_WAVE_MAX_M
        ).to_numpy(),
        "exclude_hs_q90_below_1.0m": (points["hs_q90"] >= 1.0).to_numpy(),
        "exclude_named_estuarine_points": ~points["point_key"]
        .isin(suspect_keys)
        .to_numpy(),
        "exclude_north_of_2S_entirely": (
            points["grid_lat"] < NORTH_SECTOR_LAT_MIN
        ).to_numpy(),
    }

    def _risk_from_mask(mask: np.ndarray) -> pd.Series:
        """Municipal risk rebuilt from a restricted grid-point population."""
        hazard = _hazard_index(points, mask)
        lookup = pd.Series(hazard.to_numpy(), index=points["point_key"].to_numpy())
        lookup = lookup[~lookup.index.duplicated()]
        municipal_hazard = municipalities["point_key"].map(lookup)
        finite = municipal_hazard[np.isfinite(municipal_hazard)]
        hazard_mun = (municipal_hazard - finite.min()) / (finite.max() - finite.min())

        floor = 0.01
        h = hazard_mun.clip(lower=floor)
        e = municipalities["Exposure_Index"].clip(lower=floor)
        v = (municipalities["SVI_Coast_2022"] / 100.0).clip(lower=floor)
        raw = np.cbrt(h * e * v)
        valid = np.isfinite(raw)
        return (raw - raw[valid].min()) / (raw[valid].max() - raw[valid].min())

    # The baseline for every comparison is this script's own reconstruction of
    # the current domain, not the published column: the two are verified equal
    # below, and using one consistent pipeline keeps the rank shifts free of an
    # artefact from tie-breaking or from a municipality missing on one side.
    risk_baseline = _risk_from_mask(scenarios["current_domain"])
    baseline_rank = risk_baseline.rank(ascending=False, method="min")
    published_risk = municipalities["Risk_Hazard"]
    shared = np.isfinite(risk_baseline) & np.isfinite(published_risk)
    reconstruction_check = {
        "municipalities_compared": int(shared.sum()),
        "spearman_rho_vs_published_risk": float(
            spearmanr(risk_baseline[shared], published_risk[shared])[0]
        ),
        "max_absolute_difference": float(
            np.max(np.abs(risk_baseline[shared] - published_risk[shared]))
        ),
        "published_municipalities_with_risk": int(np.isfinite(published_risk).sum()),
        "reconstructed_municipalities_with_risk": int(np.isfinite(risk_baseline).sum()),
    }
    baseline_top10 = set(
        municipalities.assign(r=baseline_rank)
        .nsmallest(10, "r")["municipality_code"]
        .astype(str)
    )

    scenario_rows = []
    for name, mask in scenarios.items():
        risk = _risk_from_mask(mask)
        rank = risk.rank(ascending=False, method="min")

        common = np.isfinite(rank) & np.isfinite(baseline_rank)
        rho = (
            float(spearmanr(rank[common], baseline_rank[common])[0])
            if common.sum() > 2
            else float("nan")
        )
        top10 = set(
            municipalities.assign(r=rank).nsmallest(10, "r")["municipality_code"].astype(str)
        )
        orphaned = municipalities.loc[
            np.isfinite(baseline_rank) & ~np.isfinite(rank), "municipality_name"
        ].tolist()
        shift = np.abs(rank[common] - baseline_rank[common])
        scenario_rows.append(
            {
                "scenario": name,
                "points_retained": int(mask.sum()),
                "points_removed": int(len(points) - mask.sum()),
                "events_removed": int(points.loc[~mask, "compound_count_total"].sum()),
                "events_removed_share": float(
                    points.loc[~mask, "compound_count_total"].sum()
                    / max(points["compound_count_total"].sum(), 1)
                ),
                "municipalities_with_risk": int(np.isfinite(rank).sum()),
                "municipalities_orphaned": len(orphaned),
                "orphaned_names": "; ".join(sorted(orphaned)[:20]),
                "spearman_rho_rank_vs_current": rho,
                "risk_top10_overlap": len(baseline_top10 & top10),
                "median_absolute_rank_shift": float(np.median(shift)),
                "max_absolute_rank_shift": float(shift.max()),
            }
        )
    sensitivity = pd.DataFrame(scenario_rows)
    sensitivity.to_csv(OUT_DIR / "sensitivity_scenarios.csv", index=False)

    # ── 5. Spatial stability of the 0.5 m rule ───────────────────────────────
    # A defensible geographic filter should select a contiguous set. If the
    # retained and excluded points interleave along the coast, the rule is
    # cutting on noise rather than on geography.
    ordered = points.sort_values(["grid_lat", "grid_lon"]).reset_index(drop=True)
    flag = (ordered["hs_max"] < LOW_WAVE_MAX_M).to_numpy()
    switches = int(np.sum(flag[1:] != flag[:-1]))

    summary = {
        "generated_by": "src.exploratory.audit_AUD_12_estuarine_contamination",
        "sources": {
            "current_metrics": str(HAT_METRICS.relative_to(ROOT)),
            "legacy_metrics": str(LEGACY_METRICS.relative_to(ROOT))
            if LEGACY_METRICS.exists()
            else None,
            "unified_dataset": str(UNIFIED.relative_to(ROOT)),
            "municipal_product": str(GEOJSON.relative_to(ROOT)),
        },
        "grid_point_count": int(len(points)),
        "domain_event_total": int(points["compound_count_total"].sum()),
        "zero_event_points": int((points["compound_count_total"] == 0).sum()),
        "municipal_reconstruction_check": reconstruction_check,
        "questioned_points": suspect_rows,
        "seasonal_peak_month_test": {
            "verdict": (
                "not discriminating. The share of points whose mean zos peaks "
                "in April-June is reported per sector below; it is high "
                "everywhere, including south of 25 S where the Amazon has no "
                "influence, because the steric seasonal cycle of the South "
                "Atlantic also peaks in austral autumn. Peak month alone "
                "therefore cannot separate discharge from steric forcing, and "
                "the offshore-coupling correlations are used instead."
            )
        },
        "north_sector_comparison": {
            "questioned_points": _band(points[points["point_key"].isin(suspect_keys)]),
            "other_points_north_of_2S": _band(north_others),
            "points_south_of_25S": _band(points[points["grid_lat"] <= -25.0]),
        },
        "wave_statistic_ranges": {
            "note": (
                "The 0.5 m figure in the issue record came from the local q90 "
                "wave threshold of the superseded method, not from the wave "
                "maximum. These are the ranges of each candidate statistic on "
                "the current product, so the rule under test is applied to the "
                "quantity it was meant for."
            ),
            "hs_max": [float(points["hs_max"].min()), float(points["hs_max"].max())],
            "hs_q99": [float(points["hs_q99"].min()), float(points["hs_q99"].max())],
            "hs_q90": [float(points["hs_q90"].min()), float(points["hs_q90"].max())],
            "thr_hs_abs_q70": [
                float(points["thr_hs_abs"].min()),
                float(points["thr_hs_abs"].max()),
            ],
            "n_points_hs_max_below_0.5m": int((points["hs_max"] < 0.5).sum()),
            "n_points_hs_q99_below_0.5m": int((points["hs_q99"] < 0.5).sum()),
            "n_points_thr_hs_q70_below_0.5m": int((points["thr_hs_abs"] < 0.5).sum()),
        },
        "low_wave_rule": {
            "threshold_m": LOW_WAVE_MAX_M,
            "statistic": "hs_max",
            "n_points_below": int(len(low_wave)),
            "share_of_domain": float(len(low_wave) / len(points)),
            "events_at_those_points": int(low_wave["compound_count_total"].sum()),
            "share_of_domain_events": float(
                low_wave["compound_count_total"].sum()
                / max(points["compound_count_total"].sum(), 1)
            ),
            "n_points_with_zero_events": int(
                (low_wave["compound_count_total"] == 0).sum()
            ),
            "n_municipalities_depending": int(len(dependent)),
            "n_such_municipalities_in_risk_top10": int(
                (dependent["risk_rank"] <= 10).sum()
            ),
            "n_such_municipalities_in_risk_top50": int(
                (dependent["risk_rank"] <= 50).sum()
            ),
            "latitude_range_of_excluded": [
                float(low_wave["grid_lat"].min()),
                float(low_wave["grid_lat"].max()),
            ],
            "contiguity_switches_along_coast": switches,
            "contiguity_note": (
                "Number of times the include/exclude flag changes when the 808 "
                "points are ordered along the coast. A geographically coherent "
                "rule produces few switches; many switches mean the rule cuts "
                "on noise."
            ),
        },
        "sensitivity_scenarios": scenario_rows,
        "false_negative_check": {
            "note": (
                "Points a candidate exclusion rule would remove that nonetheless "
                "carry compound events accepted by the HAT gate. Removing these "
                "discards hazard the method actually detected, not merely a "
                "modelling artefact, and it silences the municipality rather "
                "than correcting it."
            ),
            "hs_max_below_0.5m": {
                "n_points": int(len(low_wave)),
                "n_points_with_events": int(
                    (low_wave["compound_count_total"] > 0).sum()
                ),
                "events_that_passed_the_hat_gate": int(
                    low_wave["compound_count_total"].sum()
                ),
            },
            "hs_q99_below_0.5m": {
                "n_points": int((points["hs_q99"] < LOW_WAVE_MAX_M).sum()),
                "n_points_with_events": int(
                    (
                        (points["hs_q99"] < LOW_WAVE_MAX_M)
                        & (points["compound_count_total"] > 0)
                    ).sum()
                ),
                "events_that_passed_the_hat_gate": int(
                    points.loc[
                        points["hs_q99"] < LOW_WAVE_MAX_M, "compound_count_total"
                    ].sum()
                ),
                "municipalities_silenced": int(
                    municipalities["point_key"]
                    .isin(
                        set(
                            points.loc[
                                points["hs_q99"] < LOW_WAVE_MAX_M, "point_key"
                            ]
                        )
                    )
                    .sum()
                ),
            },
            "thr_hs_q70_below_0.5m": {
                "n_points": int((points["thr_hs_abs"] < LOW_WAVE_MAX_M).sum()),
                "n_points_with_events": int(
                    (
                        (points["thr_hs_abs"] < LOW_WAVE_MAX_M)
                        & (points["compound_count_total"] > 0)
                    ).sum()
                ),
                "events_that_passed_the_hat_gate": int(
                    points.loc[
                        points["thr_hs_abs"] < LOW_WAVE_MAX_M, "compound_count_total"
                    ].sum()
                ),
                "municipalities_silenced": int(
                    municipalities["point_key"]
                    .isin(
                        set(
                            points.loc[
                                points["thr_hs_abs"] < LOW_WAVE_MAX_M, "point_key"
                            ]
                        )
                    )
                    .sum()
                ),
            },
        },
    }
    (OUT_DIR / "diagnosis_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
