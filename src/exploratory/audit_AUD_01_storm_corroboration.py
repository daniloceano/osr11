"""AUD-01 diagnostic: does spring-neap phase locking mean "tidal artefact" or
"tidal modulation of a genuine storm"?

A high Rayleigh R on compound start dates is ambiguous on its own. Two very
different situations produce it:

(a) the tide DOMINATES the level, so the q90 exceedance is decided by the tide
    alone and no storm need be present — the events are spring tides, which is
    the artefact AUD-01 diagnosed;
(b) the tide MODULATES the level, so an event still requires a storm, but a
    storm arriving on a spring tide is likelier to push the total level past
    the local q90 — which is genuine physics and precisely the amplification a
    compound framework should capture.

R alone cannot separate them. This script separates them directly, by asking
whether the `SSH_total`-detected compound events are corroborated by an
independent storm signal: for each point, the fraction of `SSH_total`-based
compound events that contain at least one day on which `zos` — a tide-free
variable — also exceeds its own local q90.

A high corroborated fraction means a storm was present and the tide merely set
the timing (case b). A low one means the events stand on the tide alone
(case a).

This is the discriminator that determines whether a regime switch keyed on the
storm-to-tide ratio q is well placed, or whether it leaves genuinely artefactual
events inside the branch that keeps the tide.

Read-only diagnostic. Does not modify the production pipeline or any published
output.

Usage:
    python -m src.exploratory.audit_AUD_01_storm_corroboration

Output:
    outputs/audit/AUD-01_storm_corroboration/corroboration_by_point.csv
    outputs/audit/AUD-01_storm_corroboration/corroboration_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
CATALOG = ROOT / "outputs" / "storm_catalog" / "compound" / "compound_catalog.json"
SWITCH_CSV = (
    ROOT / "outputs" / "audit" / "AUD-01_storm_over_tide_switch" / "switch_by_point.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_storm_corroboration"

QUANTILE = 0.90
MAX_GAP_DAYS = 1

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


def episode_mask(series: np.ndarray, finite: np.ndarray, max_gap: int) -> np.ndarray:
    thr = np.nanquantile(series[finite], QUANTILE)
    exceeds = np.where(finite, series >= thr, False)
    idx = np.flatnonzero(exceeds)
    if idx.size == 0:
        return exceeds
    mask = exceeds.copy()
    gaps = np.diff(idx)
    for k in np.flatnonzero((gaps > 1) & (gaps <= max_gap + 1)):
        mask[idx[k] : idx[k + 1] + 1] = True
    return mask


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs as (start, end_exclusive)."""
    if not mask.any():
        return []
    padded = np.concatenate(([False], mask, [False]))
    starts = np.flatnonzero(~padded[:-1] & padded[1:])
    ends = np.flatnonzero(padded[:-1] & ~padded[1:])
    return list(zip(starts, ends))


def band_for_latitude(lat: float) -> str | None:
    for name, lo, hi in LATITUDE_BANDS:
        if lo <= lat < hi:
            return name
    return None


def main() -> None:
    for path in (UNIFIED, CATALOG, SWITCH_CSV):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run audit_AUD_01_storm_over_tide_switch first."
            )

    with CATALOG.open() as f:
        catalog = json.load(f)
    pts = pd.DataFrame(
        [{"grid_lat": p["grid_lat"], "grid_lon": p["grid_lon"]} for p in catalog]
    )

    ds = xr.open_dataset(UNIFIED)
    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in pts["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in pts["grid_lon"]],
        dims="point",
    )

    print(f"Extracting {len(pts)} coastal points ...")
    hs = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    zos = ds["zos"].isel(latitude=lat_idx, longitude=lon_idx).values
    ssh = ds["SSH_total"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    rows = []
    for i in range(len(pts)):
        h = hs[:, i].astype(float)
        z = zos[:, i].astype(float)
        s = ssh[:, i].astype(float)
        finite = np.isfinite(h) & np.isfinite(z) & np.isfinite(s)
        if finite.sum() < 1000:
            continue

        m_hs = episode_mask(h, finite, MAX_GAP_DAYS)
        m_ssh = episode_mask(s, finite, MAX_GAP_DAYS)
        m_zos = episode_mask(z, finite, MAX_GAP_DAYS)

        compound_ssh = m_hs & m_ssh
        events = runs(compound_ssh)
        if not events:
            continue

        corroborated = sum(1 for a, b in events if m_zos[a:b].any())
        rows.append(
            {
                "grid_lat": pts["grid_lat"][i],
                "grid_lon": pts["grid_lon"][i],
                "n_compound_ssh_total": len(events),
                "n_storm_corroborated": corroborated,
                "storm_corroborated_fraction": corroborated / len(events),
            }
        )

    df = pd.DataFrame(rows)
    df["latitude_band"] = df["grid_lat"].map(band_for_latitude)

    switch = pd.read_csv(SWITCH_CSV)
    key = lambda d: list(zip(d["grid_lat"].round(4), d["grid_lon"].round(4)))  # noqa: E731
    df["_key"] = key(df)
    switch["_key"] = key(switch)
    df = df.merge(
        switch[["_key", "q_storm_over_tide", "branch", "selected_locked"]],
        on="_key",
        how="inner",
    ).drop(columns="_key")

    keep_tide = df[df["branch"] == "keep_tide_SSH_total"]
    locked_in_keep = keep_tide[keep_tide["selected_locked"]]

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_storm_corroboration",
        "definition": (
            "fraction of SSH_total-based compound events containing at least one "
            "day on which zos also exceeds its own local q90"
        ),
        "n_points": int(len(df)),
        "overall_median_corroborated_fraction": float(
            df["storm_corroborated_fraction"].median()
        ),
        "keep_tide_branch": {
            "n_points": int(len(keep_tide)),
            "median_corroborated_fraction": float(
                keep_tide["storm_corroborated_fraction"].median()
            ),
        },
        "locked_points_inside_keep_tide_branch": {
            "n_points": int(len(locked_in_keep)),
            "median_corroborated_fraction": (
                float(locked_in_keep["storm_corroborated_fraction"].median())
                if len(locked_in_keep)
                else None
            ),
            "interpretation_note": (
                "If this fraction is high, the residual phase locking inside the "
                "keep-tide branch reflects tidal modulation of real storms "
                "(case b) rather than tide-only events (case a)."
            ),
        },
        "spearman_corroboration_vs_q": float(
            df["storm_corroborated_fraction"].corr(df["q_storm_over_tide"], method="spearman")
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "corroboration_by_point.csv", index=False)
    with (OUT_DIR / "corroboration_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))
    print()
    print(f"{'band':<14}{'n':>5}{'q_med':>8}{'corrob_med':>12}{'%locked':>10}")
    for name, lo, hi in LATITUDE_BANDS:
        sub = df[df["latitude_band"] == name]
        if sub.empty:
            continue
        print(
            f"{name:<14}{len(sub):>5}{sub['q_storm_over_tide'].median():>8.2f}"
            f"{sub['storm_corroborated_fraction'].median():>12.2f}"
            f"{100 * sub['selected_locked'].mean():>10.0f}"
        )


if __name__ == "__main__":
    main()
