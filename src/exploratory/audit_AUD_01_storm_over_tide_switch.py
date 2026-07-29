"""AUD-01 diagnostic: test a proposed regime-dependent detector switch.

Proposal under evaluation (user, 2026-07-29): define a dimensionless ratio

    q = (wave setup + surge) / astronomical tide component
      = (0.2 * Hs_q99 + surge_q99_anomaly) / spring-neap swing of daily high water

and switch the level variable on it — where q > 1 the storm contribution
matches or exceeds the astronomical one, so the tide may be kept in the
detection variable (`SSH_total`); where q < 1 the level is tide-dominated, so
detection uses `zos` only. The stated aim is to keep the whole coast, and thus
the national-coverage claim, without letting the astronomical signal drive
detection in the macrotidal sector.

The decisive question is not whether q is a sensible ratio — it is — but
whether the branch it selects actually delivers a tide-free catalogue on BOTH
sides. This script therefore cross-tabulates q against the measured spring-neap
phase locking of the compound detector under each branch, using the Rayleigh
statistics already produced by
`audit_AUD_01_compound_detector_phase_comparison.py`.

It reports:

1. q per point and the resulting partition at q = 1;
2. within the q > 1 branch (which would keep `SSH_total`), how many points are
   still significantly phase-locked under that variable — the failure mode;
3. the same for the q < 1 branch under `zos`;
4. the size of the discontinuity the switch would introduce, by comparing
   compound counts under the two variables for points adjacent to q = 1.

Read-only diagnostic. Does not modify the production pipeline or any published
output, and does not apply any switch.

Usage:
    python -m src.exploratory.audit_AUD_01_storm_over_tide_switch

Output:
    outputs/audit/AUD-01_storm_over_tide_switch/switch_by_point.csv
    outputs/audit/AUD-01_storm_over_tide_switch/switch_summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "unified" / "metocean_brazil_unified_waverys_grid.nc"
MAGNITUDE_CSV = (
    ROOT / "outputs" / "audit" / "AUD-01_surge_vs_tide_magnitude" / "surge_vs_tide_by_point.csv"
)
PHASE_CSV = (
    ROOT
    / "outputs"
    / "audit"
    / "AUD-01_compound_detector_phase_comparison"
    / "compound_phase_by_point.csv"
)
OUT_DIR = ROOT / "outputs" / "audit" / "AUD-01_storm_over_tide_switch"

#: First-order setup coefficient. A crude but conventional scaling of setup
#: with offshore wave height; used here only as the proposal specifies it.
SETUP_COEFFICIENT = 0.2


def main() -> None:
    for path in (UNIFIED, MAGNITUDE_CSV, PHASE_CSV):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run the prior AUD-01 diagnostics first."
            )

    mag = pd.read_csv(MAGNITUDE_CSV)
    phase = pd.read_csv(PHASE_CSV)

    ds = xr.open_dataset(UNIFIED)
    lat_idx = xr.DataArray(
        [int(np.abs(ds["latitude"].values - v).argmin()) for v in mag["grid_lat"]],
        dims="point",
    )
    lon_idx = xr.DataArray(
        [int(np.abs(ds["longitude"].values - v).argmin()) for v in mag["grid_lon"]],
        dims="point",
    )
    print(f"Extracting Hs at {len(mag)} coastal points ...")
    hs = ds["VHM0"].isel(latitude=lat_idx, longitude=lon_idx).values
    print("Extraction complete.")

    hs_q99 = np.full(len(mag), np.nan)
    for i in range(len(mag)):
        col = hs[:, i].astype(float)
        finite = np.isfinite(col)
        if finite.sum() >= 1000:
            hs_q99[i] = np.quantile(col[finite], 0.99)

    df = mag.copy()
    df["hs_q99_m"] = hs_q99
    df["wave_setup_proxy_cm"] = 100 * SETUP_COEFFICIENT * df["hs_q99_m"]
    df["storm_component_cm"] = df["wave_setup_proxy_cm"] + df["surge_q99_anomaly_cm"]
    df["q_storm_over_tide"] = df["storm_component_cm"] / df["springneap_swing_cm"]

    key = lambda d: list(zip(d["grid_lat"].round(4), d["grid_lon"].round(4)))  # noqa: E731
    df["_key"] = key(df)
    phase["_key"] = key(phase)
    df = df.merge(
        phase[
            [
                "_key",
                "n_compound_zos",
                "n_compound_ssh_total",
                "rayleigh_R_compound_zos",
                "rayleigh_p_compound_zos",
                "rayleigh_R_compound_ssh_total",
                "rayleigh_p_compound_ssh_total",
            ]
        ],
        on="_key",
        how="inner",
    ).drop(columns="_key")

    df["branch"] = np.where(df["q_storm_over_tide"] > 1.0, "keep_tide_SSH_total", "zos_only")
    # Phase locking of the catalogue the switch would actually produce.
    df["selected_R"] = np.where(
        df["branch"] == "keep_tide_SSH_total",
        df["rayleigh_R_compound_ssh_total"],
        df["rayleigh_R_compound_zos"],
    )
    df["selected_p"] = np.where(
        df["branch"] == "keep_tide_SSH_total",
        df["rayleigh_p_compound_ssh_total"],
        df["rayleigh_p_compound_zos"],
    )
    df["selected_locked"] = df["selected_p"] < 0.01

    keep_tide = df[df["branch"] == "keep_tide_SSH_total"]
    zos_only = df[df["branch"] == "zos_only"]

    # Discontinuity at the switch: for points near q = 1, how different are the
    # two catalogues that the branch chooses between?
    near = df[(df["q_storm_over_tide"] > 0.7) & (df["q_storm_over_tide"] < 1.4)]
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_jump = (
            (near["n_compound_ssh_total"] - near["n_compound_zos"]).abs()
            / near[["n_compound_ssh_total", "n_compound_zos"]].mean(axis=1)
        )

    summary = {
        "generated_by": "src.exploratory.audit_AUD_01_storm_over_tide_switch",
        "setup_coefficient": SETUP_COEFFICIENT,
        "q_definition": "(0.2*Hs_q99 + surge_q99_anomaly) / spring-neap swing",
        "n_points": int(len(df)),
        "q_distribution": {
            "min": float(df["q_storm_over_tide"].min()),
            "p10": float(df["q_storm_over_tide"].quantile(0.10)),
            "median": float(df["q_storm_over_tide"].median()),
            "p90": float(df["q_storm_over_tide"].quantile(0.90)),
            "max": float(df["q_storm_over_tide"].max()),
        },
        "partition_at_q_1": {
            "keep_tide_SSH_total": {
                "n_points": int(len(keep_tide)),
                "lat_min": float(keep_tide["grid_lat"].min()) if len(keep_tide) else None,
                "lat_max": float(keep_tide["grid_lat"].max()) if len(keep_tide) else None,
            },
            "zos_only": {
                "n_points": int(len(zos_only)),
                "lat_min": float(zos_only["grid_lat"].min()) if len(zos_only) else None,
                "lat_max": float(zos_only["grid_lat"].max()) if len(zos_only) else None,
            },
        },
        "FAILURE_TEST_phase_locking_of_selected_catalogue": {
            "note": (
                "Points whose selected branch still yields a spring-neap-locked "
                "compound catalogue. Any count above chance in the keep_tide "
                "branch means the switch does not deliver a tide-free catalogue "
                "there."
            ),
            "keep_tide_branch_points_still_locked": int(keep_tide["selected_locked"].sum()),
            "keep_tide_branch_pct_still_locked": (
                float(100 * keep_tide["selected_locked"].mean()) if len(keep_tide) else None
            ),
            "keep_tide_branch_mean_R": (
                float(keep_tide["selected_R"].mean()) if len(keep_tide) else None
            ),
            "zos_branch_points_still_locked": int(zos_only["selected_locked"].sum()),
            "zos_branch_pct_still_locked": (
                float(100 * zos_only["selected_locked"].mean()) if len(zos_only) else None
            ),
            "overall_pct_locked_after_switch": float(100 * df["selected_locked"].mean()),
        },
        "discontinuity_at_switch": {
            "n_points_near_q1": int(len(near)),
            "median_relative_jump_in_compound_count": (
                float(np.nanmedian(rel_jump)) if len(near) else None
            ),
            "note": (
                "Relative difference between the two candidate catalogues for "
                "points bracketing q = 1; a large value means neighbouring "
                "points land on materially different counts purely because of "
                "which side of the switch they fall."
            ),
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / "switch_by_point.csv", index=False)
    with (OUT_DIR / "switch_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(json.dumps(summary, indent=2))

    bands = [
        ("RS", -36, -30),
        ("SC/PR", -30, -25),
        ("SP/RJ", -25, -20),
        ("ES/BA-S", -20, -15),
        ("BA-N", -15, -10),
        ("NE", -10, -5),
        ("N_eq", -5, 0),
        ("AP", 0, 7),
    ]
    print()
    print(f"{'band':<14}{'n':>5}{'q_med':>8}{'%keep_tide':>12}{'%locked_after':>15}")
    for name, lo, hi in bands:
        sub = df[(df["grid_lat"] >= lo) & (df["grid_lat"] < hi)]
        if sub.empty:
            continue
        print(
            f"{name:<14}{len(sub):>5}{sub['q_storm_over_tide'].median():>8.2f}"
            f"{100 * (sub['branch'] == 'keep_tide_SSH_total').mean():>12.0f}"
            f"{100 * sub['selected_locked'].mean():>15.0f}"
        )


if __name__ == "__main__":
    main()
