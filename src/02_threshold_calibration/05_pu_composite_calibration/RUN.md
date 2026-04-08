# Step 2e — PU Composite Calibration: Quick-Start Guide

## Prerequisites

Steps 2b, 2c must be complete. Step 2d outputs are used for comparison ONLY —
they are **not** required inputs for running Step 2e.

Required data files:
- `data/test/metocean_sc_full_unified_waverys_grid.nc`
- `data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`  (primary)
- `data/reported events/reported_events_Karine_sc.csv`  (used for E_i corroboration)
- `data/tide_models_clipped_brasil/fes2022b/`  (FES2022 model)

Required conda environment: `osr11`  (must include `eo-tides` for FES2022 evaluation)

## Run the Full Analysis

```bash
# From project root
conda run -n osr11 python src/02_threshold_calibration/05_pu_composite_calibration/main.py --all

# Or, if already inside the osr11 environment:
python src/02_threshold_calibration/05_pu_composite_calibration/main.py --all
```

This runs the full pipeline:
1. Load expanded events database (56 episodes, 1998–2020) and legacy database
2. Clip metocean dataset to validated temporal domain
3. Build event records (expanded events → municipality → grid point)
4. Compute FES2022 daily-maximum tidal series per grid point
5. Build SSH_total = SSH + tide series per grid point
6. Layer 1: event-by-event hit/miss scan across all 81 threshold pairs
7. Layer 2: collect unmatched episode details for all pairs
8. Build episode audit table: compute E_i, I_i, C_i, q_i for each unmatched episode
9. Compute composite PU scores for all pairs
10. Select PU-optimal threshold pair
11. Run sensitivity analysis (weights, alphas, B_target)
12. Generate heatmaps and comparison figures

**Expected runtime:** ~15–30 minutes  (dominated by FES2022 tide evaluation and Layer 2 scan)

## Run Individual Components

```bash
# Layer 1 only (hit/miss scan — fast, saves intermediate cache)
python .../main.py --hits-misses

# Layer 2 only (unmatched episode collection — slow)
python .../main.py --unmatched

# Scoring only (requires cached Layer 1 and Layer 2 results)
python .../main.py --scoring

# Sensitivity analysis only (requires scoring results)
python .../main.py --sensitivity

# Figures only (requires scoring results)
python .../main.py --figures

# Summary print only (requires scoring results)
python .../main.py --summary
```

## Manual Audit (Optional Enhancement)

The E_i component is computed automatically from the legacy database.
For additional accuracy, a researcher-curated audit CSV can be provided:

```
data/audit/unmatched_episode_audit.csv
```

Required columns: `episode_id`, `E_i`

Optional columns: `municipality_code`, `date_start`, `date_end`,
`evidence_source`, `audit_date`, `auditor_notes`

Manual overrides take priority over the automatic rule-based approach.
Episodes without manual entries fall back to automatic rule (legacy database check).

## Outputs

All outputs are written to `outputs/threshold_calibration/`:

```
outputs/threshold_calibration/
├── tables/
│   ├── tab_TC5_episode_audit.csv           # Per-episode q_i components
│   ├── tab_TC5_pu_metrics_full.csv         # Score/R_pos/B/F_soft for all 81 pairs
│   ├── tab_TC5_pu_metrics_ranked.csv       # Ranked by PU optimal hierarchy
│   ├── tab_TC5_optimal_pair_pu.csv         # Final calibrated threshold pair
│   ├── tab_TC5_csi_vs_pu_comparison.csv    # Comparison with Step 2d (diagnostic)
│   ├── tab_TC5_sensitivity_weights.csv     # Weight sensitivity
│   ├── tab_TC5_sensitivity_alpha.csv       # Confidence weight sensitivity
│   └── tab_TC5_sensitivity_b_target.csv   # B_target sensitivity
├── figures/summary/
│   ├── fig_TC5_H1_score_heatmap.png        # Composite Score surface
│   ├── fig_TC5_H2_recall_heatmap.png       # R_pos surface
│   ├── fig_TC5_H3_burden_heatmap.png       # B(θ) surface
│   ├── fig_TC5_H4_fsoft_heatmap.png        # F_soft/P surface
│   ├── fig_TC5_S1_csi_vs_pu.png            # CSI vs PU comparison
│   ├── fig_TC5_S2_sensitivity_weights.png  # Weight sensitivity
│   ├── fig_TC5_S3_sensitivity_b_target.png # B_target sensitivity
│   └── fig_TC5_A1_qi_distribution.png      # q_i histogram at optimal pair
└── logs/
    └── pu_cache_hits_misses.pkl            # Layer 1 intermediate cache
    └── pu_cache_unmatched_episodes.pkl     # Layer 2 intermediate cache
```

## Key Methodological Parameters

All parameters are in:
`src/02_threshold_calibration/05_pu_composite_calibration/config/analysis_config.py`
Documentation: `config/PARAMETER_DECISIONS.md`

| Parameter | Default | Adjustable? |
|-----------|---------|-------------|
| w₁ (recall weight) | 0.60 | Yes |
| w₂ (burden weight) | 0.20 | Yes |
| w₃ (soft penalty weight) | 0.20 | Yes |
| α_E (evidence weight) | 0.60 | Yes |
| α_I (intensity weight) | 0.30 | Yes |
| α_C (context weight) | 0.10 | Yes |
| B_TARGET_PER_MUNICIPALITY | 12 ep/yr/muni | Yes — effective = 12 × n_municipalities |
| ACTIVE_SEASON_MONTHS | [4–10] | Yes |
| EXPOSED_MUNICIPALITIES | Northern sector (5 cities) | See PARAMETER_DECISIONS.md |
| MATCH_WINDOW_OFFSETS | [-2,-1,0,+1] | Fixed (inherited from Step 2b–2d) |

## Important: Step 2d vs Step 2e

Step 2e performs its **own independent threshold sweep**.
The CSI-optimal pair (q90/q90) from Step 2d is **not** used for threshold
selection in Step 2e. It appears only in the comparison table.

See `SCIENTIFIC_NOTES.md` for full methodological documentation.
