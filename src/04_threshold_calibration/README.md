# Step 4 — Threshold Calibration (CSI Grid Scan)

## Overview

Systematic optimisation of Hₛ and SSH_total exceedance thresholds using a CSI (Critical Success Index) grid scan. Evaluated against the 91-event Santa Catarina coastal disaster database (Leal et al., 2024) using a causal/antecedent temporal matching window.

## What this step does

Steps 2 and 3 established that a fixed q90 threshold leaves only 2–13 of 91 reported events detected as concurrent exceedances. This low rate is expected: q90 is a starting point, not a calibrated threshold. Step 4 answers the question:

> **Which pair of (Hₛ, SSH_total) thresholds best separates the 91 reported coastal disasters from background ocean conditions?**

This is answered by sweeping 81 threshold combinations (q50–q90 in 0.05 steps for each variable) and computing, for each pair:

- **H** — number of observed events captured by the causal window rule
- **M** — number of observed events missed
- **F** — number of compound episodes in the full series not associated with any observed event (false alarms)
- **POD** = H / (H + M)
- **FAR** = F / (H + F)
- **CSI** = H / (H + M + F)

The threshold pair that maximises CSI (with FAR as tiebreaker) is selected as the calibrated detection framework for Step 5 (Storm Catalog Generation).

## Causal matching window

An observed event reported on date **D** is considered **captured** if the joint compound condition (Hₛ ≥ thr_hs AND SSH_total ≥ thr_ssh) holds at any of:

```
D-2, D-1, D, D+1 00Z
```

The window is **asymmetric**: it accepts antecedents (the forcing may precede the reported impact) and includes D+1 00Z as an operational tolerance for the midnight-UTC snapshot convention. Compound episodes detected after D+1 are **not** counted as matches.

## Temporal domain restriction (preprocessing)

Before the grid scan, the unified dataset is clipped to the period covered by the
reported events database, extended by the causal window margins:

```
t_start = min(event_dates) + min(offsets)   [earliest event − 2 days]
t_end   = max(event_dates) + max(offsets)   [latest event + 1 day]
```

**Why this matters:** The unified dataset spans 1993–2025 but the SC disaster database
covers only 1998–2023. Any compound episode in 1993–1997 or 2024–2025 has no validation
event to pair with and would be automatically counted as a false alarm. This inflates F,
distorts FAR, and shifts the optimal threshold pair towards artificially restrictive
combinations. Clipping the dataset to the validated period eliminates this bias.

**Effect on thresholds:** Local percentile thresholds are now computed from the clipped
series (~25 years, ~9,100 daily observations per grid point). This is statistically
equivalent to the full 32-year series for percentile estimation purposes.

Implementation: `src/04_threshold_calibration/preprocessing.py`, function
`clip_to_validated_period()`. Called from `main.py` immediately after loading.

## What is reused from previous steps

| From | What |
|------|------|
| `src/02_preliminary_compound/io.py` | `load_unified_dataset()`, `load_reported_events()` |
| `src/02_preliminary_compound/events.py` | `build_event_records()` — municipality→grid matching |
| `src/03_tidal_sensitivity/tides.py` | `build_tide_cache()`, `add_tide_to_ssh()` — SSH_total computation |

No new geographic matching is performed. The same grid points established in Step 2 are used throughout.

## Module structure

```
src/04_threshold_calibration/
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
- `tab_TC4_optimal_pair.csv` — optimal threshold pair reference (used by Step 5)
- `fig_TC4_H1_csi_heatmap.png` — CSI across all threshold pairs (primary result figure)
