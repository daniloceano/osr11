# Step 2e — PU Composite Calibration: Quick-Start Guide

## Prerequisites

All previous steps must be complete:

- **Step 2b:** `src/02_threshold_calibration/02_preliminary_compound/` — EventRecord infrastructure
- **Step 2c:** `src/02_threshold_calibration/03_tidal_sensitivity/` — SSH_total definition
- **Step 2d:** `src/02_threshold_calibration/04_csi_grid_scan/` — CSI metrics and false alarm list

Required data files:
- `data/test/metocean_sc_full_unified_waverys_grid.nc`
- `data/reported events/reported_events_Karine_sc.csv`
- `data/tide_models_clipped_brasil/fes2022b/`
- `outputs/threshold_calibration/tables/tab_TC4_metrics_full.csv` (from Step 2d)

## Manual Audit (Required Before Full Run)

The PU composite score requires external evidence flags (Eᵢ) for unmatched episodes. Before running the full analysis:

1. **Create the audit directory:**
   ```bash
   mkdir -p data/audit
   ```

2. **Export unmatched episodes from Step 2d** (automatic if running with `--export-audit`):
   ```bash
   python -m src.pu_composite_calibration.main --export-audit
   ```

3. **Audit top-priority episodes** — check Civil Defense bulletins, municipal reports, and news sources for each unmatched episode. Record findings in:
   ```
   data/audit/unmatched_episode_audit.csv
   ```

4. **CSV format:**
   ```csv
   episode_id,municipality_code,date_start,date_end,E_i,evidence_source,audit_date,auditor_notes
   ```

**Note:** The audit can be partial. Non-audited episodes default to Eᵢ=0 while still contributing through physical intensity (Iᵢ) and context coherence (Cᵢ).

## Run the Full Analysis

```bash
# From project root
python -m src.pu_composite_calibration.main --all

# Direct invocation
python src/02_threshold_calibration/05_pu_composite_calibration/main.py --all
```

This runs:
1. Load Step 2d results (CSI metrics, false alarm list)
2. Compute physical intensity (Iᵢ) for all unmatched episodes
3. Compute context coherence (Cᵢ) for all unmatched episodes
4. Load external evidence flags (Eᵢ) from audit database
5. Calculate confidence weights (qᵢ) and soft penalty
6. Compute composite score for all threshold pairs
7. Select optimal pair under PU framework
8. Generate summary tables and figures

**Expected runtime:** ~5–10 minutes (depends on audit database size)

## Run Individual Components

```bash
# Export audit template only
python -m src.pu_composite_calibration.main --export-audit

# Compute confidence weights only (requires audit database)
python -m src.pu_composite_calibration.main --compute-weights

# Run scoring only (requires computed weights)
python -m src.pu_composite_calibration.main --scoring

# Sensitivity analysis
python -m src.pu_composite_calibration.main --sensitivity

# Summary figures only
python -m src.pu_composite_calibration.main --summary
```

## Outputs

All outputs are written to `outputs/threshold_calibration/`:

```
outputs/threshold_calibration/
├── tables/
│   ├── tab_TC5_episode_audit.csv           # Per-episode audit table with qᵢ components
│   ├── tab_TC5_pu_metrics_full.csv         # Composite score for all threshold pairs
│   ├── tab_TC5_pu_metrics_ranked.csv       # Ranked by optimal selection hierarchy
│   ├── tab_TC5_optimal_pair_pu.csv         # Optimal threshold pair (PU framework)
│   ├── tab_TC5_csi_vs_pu_comparison.csv    # Side-by-side comparison with Step 2d
│   └── tab_TC5_sensitivity_*.csv           # Sensitivity analysis results
├── figures/
│   └── summary/
│       ├── fig_TC5_H1_score_heatmap.png    # Composite score across threshold pairs
│       ├── fig_TC5_H2_recall_heatmap.png   # R_pos across threshold pairs
│       ├── fig_TC5_H3_burden_heatmap.png   # B(θ) across threshold pairs
│       ├── fig_TC5_S1_csi_vs_pu.png        # CSI vs PU optimal comparison
│       ├── fig_TC5_S2_sensitivity_w.png    # Weight sensitivity analysis
│       └── fig_TC5_S3_sensitivity_alpha.png# Confidence weight sensitivity
└── logs/
    └── log_TC5_run_summary.txt             # Human-readable run summary
```

## Key Methodological Parameters

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| w₁ (recall) | 0.60 | Primary objective: capture reported events |
| w₂ (burden) | 0.20 | Penalize excessive annual detections |
| w₃ (soft penalty) | 0.20 | Penalize unmatched proportionally |
| α_E (evidence) | 0.60 | External evidence dominates plausibility |
| α_I (intensity) | 0.30 | Physical extremity matters |
| α_C (context) | 0.10 | Weak heuristic weight |
| B_target | 10 ep/yr | Operational audit capacity |

To modify parameters, edit `src/02_threshold_calibration/05_pu_composite_calibration/config/analysis_config.py`.

## Comparison with Step 2d

After running, check `tab_TC5_csi_vs_pu_comparison.csv` to compare:

| Metric | Step 2d (CSI) | Step 2e (PU) |
|--------|---------------|--------------|
| Optimal Hₛ | q90 | (computed) |
| Optimal SSH | q90 | (computed) |
| Hits | 21 | (computed) |
| Misses | 70 | (computed) |
| False alarms | 1,298 (hard) | F_soft (soft) |

See `src/02_threshold_calibration/05_pu_composite_calibration/SCIENTIFIC_NOTES.md` for full methodological documentation.
