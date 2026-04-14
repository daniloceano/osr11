# Step 2d — CSI Grid Scan

**Part of STEP 2 — Threshold Calibration (umbrella step)**  
**Location:** `src/02_threshold_calibration/04_csi_grid_scan/`

## Overview

Systematic exploration of Hₛ and SSH_total exceedance thresholds using a CSI (Critical Success Index) grid scan. Evaluated against the 91-event Santa Catarina coastal disaster database (Leal et al., 2024) using a causal/antecedent temporal matching window.

**This step is DIAGNOSTIC.** Its optimal threshold pair (q90/q90) is retained for methodological comparison only. Step 2e (PU Composite Calibration) performs the final independent calibration and is the authoritative source of thresholds for Step 3.

## What this step does

Steps 2a–2c established that a fixed q90 threshold leaves only 2–26 of 91 reported events detected as concurrent exceedances. This low rate is expected: q90 is a starting point, not a calibrated threshold. Step 2d answers the diagnostic question:

> **Which pair of (Hₛ, SSH_total) thresholds best separates the 91 reported coastal disasters from background ocean conditions, under the classical CSI framework?**

This is answered by sweeping 81 threshold combinations (q50–q90 in 0.05 steps for each variable) and computing, for each pair:

- **H** — number of observed events captured by the causal window rule
- **M** — number of observed events missed
- **F** — number of compound episodes in the full series not associated with any observed event (false alarms)
- **POD** = H / (H + M)
- **FAR** = F / (H + F)
- **CSI** = H / (H + M + F)

The threshold pair that maximises CSI (with FAR as tiebreaker) is identified. The extremely high FAR at the optimal pair (q90/q90: FAR=0.984) revealed that classical verification metrics are unsuitable due to systematic Civil Defense database under-reporting. This diagnostic finding motivated the PU composite approach in Step 2e.

**Downstream use:** The Step 2d outputs are used by Step 2e for methodological comparison only. Step 2e performs its own independent threshold sweep. The final calibrated thresholds for Step 3 come from Step 2e.

## Causal matching window

An observed event reported on date **D** is considered **captured** if the joint compound condition (Hₛ ≥ thr_hs AND SSH_total ≥ thr_ssh) holds at any of:

```
D-2, D-1, D, D+1 00Z
```

The window is **asymmetric**: it accepts antecedents (the forcing may precede the reported impact) and includes D+1 00Z as an operational tolerance for the midnight-UTC snapshot convention. Compound episodes detected after D+1 are **not** counted as matches.

## Threshold computation vs. validated scan

**Threshold computation:** Local percentile thresholds are computed from the **full metocean record** (1993–2025, ~12,053 daily observations per grid point). This ensures maximum statistical robustness and eliminates edge effects at the boundaries of the event database period.

**Validation scan:** The event-matching scan (Layers 1 and 2) is restricted to the period covered by the reported events database, extended by the causal window margins:

```
t_start = min(event_dates) + min(offsets)   [earliest event − 2 days]
t_end   = max(event_dates) + max(offsets)   [latest event + 1 day]
```

**Why restrict the scan:** The SC disaster database covers only 1998–2023. Any compound episode in 1993–1997 or 2024–2025 has no validation event to pair with and would be automatically counted as a false alarm. This inflates F, distorts FAR, and shifts the optimal threshold pair towards artificially restrictive combinations. Clipping the scan to the validated period eliminates this bias while keeping thresholds derived from the full climatological record.

Implementation: `preprocessing.py::clip_to_validated_period()`. Event records are built from the full dataset via `build_event_records(ds_full, ...)` before temporal clipping.

## What is reused from previous steps

| From | What |
|------|------|
| `src/02_threshold_calibration/02_preliminary_compound/io.py` | `load_unified_dataset()`, `load_reported_events()` |
| `src/02_threshold_calibration/02_preliminary_compound/events.py` | `build_event_records()` — municipality→grid matching |
| `src/02_threshold_calibration/03_tidal_sensitivity/tides.py` | `build_tide_cache()`, `add_tide_to_ssh()` — SSH_total computation |

No new geographic matching is performed. The same grid points established in Step 2b are used throughout.

## Module structure

```
src/02_threshold_calibration/04_csi_grid_scan/
├── main.py              # CLI orchestrator (--all, --hits-misses, --false-alarms, --summary)
├── preprocessing.py     # Temporal domain restriction: clip dataset to validated period
├── RUN.md               # Quick-start guide
├── README.md            # This file
├── SCIENTIFIC_NOTES.md  # Full methodological documentation
├── config/
│   └── analysis_config.py   # Threshold grid, window offsets, output paths
├── windows.py           # Causal window [D-2, D-1, D, D+1 00Z]
├── calibration.py       # Layer 1 (hit/miss) + Layer 2 (false alarms)
├── metrics.py           # POD, FAR, CSI; ranking; optimal pair selection
├── figures.py           # Heatmaps (H1–H3) + summary figures (S1–S4)
├── summary.py           # Table and figure orchestration
└── utils.py             # Output dirs, save_fig, helpers
```

## Outputs

See `RUN.md` for the complete output list. The key outputs are:

- `tab_TC4_metrics_full.csv` — full grid scan metrics
- `tab_TC4_metrics_ranked.csv` — ranked by optimal selection hierarchy
- `tab_TC4_event_hits_optimal.csv` — per-event hit/miss at the optimal pair
- `tab_TC4_optimal_pair.csv` — diagnostic optimal threshold pair (used by Step 2e for comparison only; NOT used by Step 3)
- `fig_TC4_H1_csi_heatmap.png` — CSI across all threshold pairs (primary diagnostic figure)
