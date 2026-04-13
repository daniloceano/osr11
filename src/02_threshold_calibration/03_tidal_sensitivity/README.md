# Step 2c — Tidal Sensitivity Analysis

**Part of STEP 2 — Threshold Calibration (umbrella step)**  
**Location:** `src/02_threshold_calibration/03_tidal_sensitivity/`

**Purpose:** Evaluate how much compound event detection changes when the FES2022
astronomical tide is added to the GLORYS12 SSH signal, forming a total sea level
(SSH_total = zos + tide).

---

## What it does

Two parallel analyses are run on the same 91 reported SC coastal disasters:

1. **SSH-only** — concurrent Hₛ q90 AND SSH q90 exceedance within a 7-day event window
2. **SSH_total** — concurrent Hₛ q90 AND SSH_total q90 exceedance in the same window

Events are classified by `detection_change`:

| Category   | Definition |
|------------|------------|
| `new`       | Only detected with SSH_total (tide is required to exceed q90) |
| `maintained`| Detected in both analyses |
| `lost`      | Only detected without tide (SSH_total q90 is too high) |
| `neither`   | Not detected in either analysis |

---

## Temporal conventions

| Variable | Source | Convention |
|---|---|---|
| VHM0 (Hₛ) | WAVERYS 3-hourly → unified dataset | **Daily maximum** |
| zos (SSH) | GLORYS12 daily | **00:00 UTC snapshot** |
| FES2022 tide | eo-tides hourly evaluation → daily resample | **Daily maximum** |
| SSH_total | Computed | `zos(00:00 UTC) + tide(daily max)` |

**Why daily maximum for tide?**  
VHM0 in the unified dataset is the daily maximum from 3-hourly WAVERYS fields.
Using the 00:00 UTC tide snapshot would capture an arbitrary tidal phase (possibly
a trough at midnight), making SSH_total physically inconsistent with the Hₛ
convention. The daily maximum tide represents the peak tidal loading within the
calendar day, which is the relevant quantity for compound hazard assessment.

**Known limitation — temporal asynchronism:**  
`SSH_total = zos(00:00 UTC) + tide(daily max)` combines a midnight SSH snapshot with
a tide that may have peaked at a different time. This is inherent to GLORYS12's
daily-only output and cannot be resolved without sub-daily SSH data.

---

## Results (current run)

| Metric | Value |
|---|---|
| Events | 91 |
| SSH-only detections | 22 |
| SSH_total detections | 26 |
| New detections with tide | 7 |
| Lost detections with tide | 3 |
| Maintained | 19 |
| Neither | 62 |

Adding the FES2022 daily-maximum tide **increases** detection from 22 to 26 events
(+4 net). The mean SSH_total across grid points is ~+0.53 m (compared to the
SSH mean of ~+0.05 m), confirming the tide makes a physically meaningful positive
contribution to the total sea level.

---

## Run

```bash
conda run -n osr11 python -m src.tidal_sensitivity.main --all
```

Or individually:

```bash
# Per-event figures only
conda run -n osr11 python -m src.tidal_sensitivity.main --event-figures

# Summary figures and tables only
conda run -n osr11 python -m src.tidal_sensitivity.main --summary
```

**Expected runtime:** ~15 minutes (FES2022 hourly evaluation for 10 grid points × 32 years)

---

## Outputs

| File | Description |
|---|---|
| `outputs/tidal_sensitivity/tables/tab_TS_event_metrics.csv` | Per-event metrics (SSH-only + SSH_total) |
| `outputs/tidal_sensitivity/tables/tab_TS_tidal_thresholds.csv` | q90 thresholds for SSH_total per municipality |
| `outputs/tidal_sensitivity/figures/summary/fig_TS_C1_detection_comparison.png` | Grouped bar chart: SSH vs SSH_total concurrent fraction |
| `outputs/tidal_sensitivity/figures/summary/fig_TS_C2_scatter_ssh_vs_total.png` | Scatter of normalised maxima coloured by detection change |
| `outputs/tidal_sensitivity/figures/summary/fig_TS_C3_detection_change_by_sector.png` | Detection change counts by sector |
| `outputs/tidal_sensitivity/figures/summary/fig_TS_C4_tidal_fraction.png` | Tidal fraction of SSH_total maximum per event |
| `outputs/tidal_sensitivity/figures/events/fig_TS_event_*.png` | Per-event 3-panel figures (Hₛ / SSH / SSH_total) |

---

## Relationship to other steps

- **Reuses:** `src/02_threshold_calibration/02_preliminary_compound` (Step 2b) — data loading, event record building, SSH-only thresholds
- **Feeds into:** `src/02_threshold_calibration/04_csi_grid_scan` (Step 2d — CSI Grid Scan, diagnostic) — same SSH_total definition and Hₛ daily-maximum convention
- **Feeds into:** `src/02_threshold_calibration/05_pu_composite_calibration` (Step 2e — PU Composite Calibration, final calibration) — SSH_total = zos + FES2022 daily max tide is the mandatory sea-level variable; tides.py is reused directly
