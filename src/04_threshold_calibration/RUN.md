# Step 4 — Threshold Calibration (CSI Grid Scan): Quick-Start Guide

## Prerequisites

All previous steps must be complete:
- **Step 2**: `src/02_preliminary_compound/` — produces the EventRecord infrastructure
- **Step 3**: `src/03_tidal_sensitivity/` — confirms SSH_total = SSH + FES2022 as the sea level variable
- Data files: `data/test/metocean_sc_full_unified_waverys_grid.nc` and `data/reported events/reported_events_Karine_sc.csv` must exist.
- Tide model files: `data/tide_models_clipped_brasil/fes2022b/` must be present.

## Run the full analysis

```bash
# From project root
python src/04_threshold_calibration/main.py --all
```

This runs:
1. FES2022 tidal series computation (reuses Step 3)
2. Layer 1: event-by-event hit/miss grid scan (81 threshold pairs × 91 events)
3. Layer 2: false alarm detection from the full series
4. Metrics computation (CSI, POD, FAR)
5. Summary tables and figures

Expected runtime: ~5–15 minutes depending on whether tide files are cached.

## Run individual layers

```bash
# Layer 1 only (faster — no false alarm scan)
python src/04_threshold_calibration/main.py --hits-misses

# Layer 2 only
python src/04_threshold_calibration/main.py --false-alarms

# Summary only (requires previous layer outputs to be held in memory)
# Note: --all is the recommended entry point
python src/04_threshold_calibration/main.py --summary
```

## Outputs

All outputs are written to `outputs/threshold_calibration/`:

```
outputs/threshold_calibration/
├── tables/
│   ├── tab_TC4_metrics_full.csv       # CSI/POD/FAR for all 81 threshold pairs
│   ├── tab_TC4_metrics_ranked.csv     # Same, sorted by optimal selection hierarchy
│   ├── tab_TC4_event_hits.csv         # Per-event captures across all threshold pairs
│   ├── tab_TC4_event_hits_optimal.csv # Per-event captures at the optimal pair
│   ├── tab_TC4_lag_summary.csv        # Capture lag distribution (D-2 to D+1)
│   └── tab_TC4_optimal_pair.csv       # Single-row summary of the optimal threshold pair
├── figures/
│   └── summary/
│       ├── fig_TC4_H1_csi_heatmap.png     # CSI across all threshold combinations
│       ├── fig_TC4_H2_far_heatmap.png     # FAR across all threshold combinations
│       ├── fig_TC4_H3_pod_heatmap.png     # POD across all threshold combinations
│       ├── fig_TC4_S1_ranking_scatter.png # POD vs FAR scatter (bubble = CSI)
│       ├── fig_TC4_S2_event_hits.png      # Per-event hit/miss at optimal pair
│       ├── fig_TC4_S3_lag_distribution.png# Capture lag distribution
│       └── fig_TC4_S4_sector_pod.png      # POD by coastal sector
└── logs/
    └── log_TC4_run_summary.txt        # Human-readable run summary
```

## Key methodological choices

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| SSH variable | SSH_total = SSH + FES2022 | Consistent with Step 3 (tidal sensitivity) |
| Threshold grid | q50–q90 in steps of 0.05 | 9 levels per variable, 81 pairs total |
| Match window | [D-2, D-1, D, D+1] | Causal/antecedent; D+1 is 00Z tolerance |
| Metric | CSI primary, FAR secondary | Balances hits vs false alarms |
| Local thresholds | Full climatological series | Consistent with Steps 2–3 |

See `src/04_threshold_calibration/SCIENTIFIC_NOTES.md` for full methodological documentation.
