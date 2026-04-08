# Step 2e — PU Composite Calibration

**Part of STEP 2 — Threshold Calibration (umbrella step)**  
**Location:** `src/02_threshold_calibration/05_pu_composite_calibration/`

## Overview

Calibration of compound event detection thresholds using a **positive-unlabeled (PU) composite score** that addresses systematic under-reporting in coastal disaster databases.

### Why PU Calibration?

Step 2d (CSI Grid Scan) revealed that classical verification metrics are unsuitable for this application: the optimal CSI threshold pair (Hₛ=q90, SSH_total=q90) achieved CSI=0.0151 with FAR=0.984, meaning 98.4% of detected compound episodes had no matching reported disaster. This extremely high "false alarm" rate reflects **database incompleteness**, not threshold miscalibration.

Step 2e addresses this by:

1. Using an **expanded documentary database** of coastal `ressaca` events curated from news, theses, and technical reports
2. Treating unmatched detected episodes as **unlabeled** (not automatically false)
3. Applying a **soft penalty** weighted by episode plausibility
4. Performing an **independent threshold sweep** — Step 2d thresholds are NOT used

### Reported Events Database

Step 2e uses the expanded documentary database:

- **File:** `data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`
- **Methodology:** `data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md`
- **Events:** 56 documented `ressaca` episodes (1998–2020)
- **Sources:** Academic theses/dissertations, news archives, technical reports, Civil Defense materials
- **Curation:** Each event has explicit marine-forcing evidence, traceable source citations, and municipality-level resolution

The expanded database was curated specifically to support PU calibration by providing:
- Higher event density through forensic documentary search
- Source traceability (URL + title for each event)
- Explicit coastal-marine impact criteria (not generic flood reports)
- Municipality × date deduplication with episode-level logic

## Methodological Framework

### The Classical CSI Problem

Classical CSI is defined as:

```
CSI(θ) = H(θ) / [H(θ) + M(θ) + F(θ)]
```

This assumes `F` (false alarms) is known with confidence. Under incomplete reporting, many unmatched detections may arise because impact records are missing, not because the physical event did not occur. Treating U (unmatched) as F over-penalizes physically plausible compound episodes.

### Composite Score Definition

The PU composite score replaces CSI with:

```
Score(θ) = w₁·R_pos(θ) − w₂·B(θ) − w₃·F_soft(θ)/P
```

Where:

| Term | Definition | Interpretation |
|------|------------|----------------|
| R_pos(θ) | H(θ) / P | Positive recall — fraction of reported events captured |
| B(θ) | min(1, B_raw(θ) / B_target) | Annual burden — normalized detection rate |
| F_soft(θ) | Σᵢ(1 − qᵢ) | Soft unmatched penalty — sum of (1 − plausibility) |

### Confidence Weight (qᵢ)

Each unmatched episode receives a confidence weight:

```
qᵢ = clip(α_E·Eᵢ + α_I·Iᵢ + α_C·Cᵢ, 0, 1)
```

| Component | Range | Description |
|-----------|-------|-------------|
| Eᵢ | {0, 1} | External evidence (Civil Defense, news sources) |
| Iᵢ | [0, 1] | Physical intensity (percentile exceedance) |
| Cᵢ | [0, 1] | Context coherence (season + neighbors + exposure) |

**Default weights:** α_E=0.60, α_I=0.30, α_C=0.10

### Score Component Weights

**Default:** w₁=0.60, w₂=0.20, w₃=0.20

The rationale:
- w₁ (recall): Primary objective — recover confirmed observed events
- w₂ (burden): Penalize operationally excessive annual detections
- w₃ (soft penalty): Penalize unmatched detections proportionally to lack of evidence

## What This Step Consumes

| From | What |
|------|------|
| Step 1 | `data/test/metocean_sc_full_unified_waverys_grid.nc` — unified dataset |
| Documentary search | `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv` — 56 curated events |
| Step 2b | Event record infrastructure, municipality→grid matching |
| Step 2c | SSH_total definition (zos + FES2022 daily max tide) |
| Step 2d | CSI metrics (for diagnostic comparison only — thresholds NOT used) |
| Manual | `data/audit/unmatched_episode_audit.csv` — external evidence flags (Eᵢ) |

**Note:** Step 2e performs its own independent threshold sweep. The CSI-optimal thresholds from Step 2d are retained only for methodological comparison.

## What This Step Produces

| Output | Description |
|--------|-------------|
| `tab_TC5_episode_audit.csv` | Per-episode audit table with qᵢ components |
| `tab_TC5_pu_metrics_full.csv` | Composite score across all threshold pairs |
| `tab_TC5_pu_metrics_ranked.csv` | Ranked by optimal selection hierarchy |
| `tab_TC5_optimal_pair_pu.csv` | Optimal threshold pair under PU framework |
| `tab_TC5_sensitivity_*.csv` | Sensitivity analysis results |
| `fig_TC5_H1_score_heatmap.png` | Composite score heatmap |
| `fig_TC5_H2_recall_heatmap.png` | R_pos heatmap |
| `fig_TC5_S1_csi_vs_pu_comparison.png` | CSI vs PU optimal pair comparison |
| `fig_TC5_S2_sensitivity_weights.png` | Weight sensitivity analysis |

## Module Structure

```
src/02_threshold_calibration/05_pu_composite_calibration/
├── __init__.py              # Module docstring
├── README.md                # This file
├── RUN.md                   # Quick-start guide
├── SCIENTIFIC_NOTES.md      # Full methodological documentation
├── config/
│   ├── __init__.py
│   └── analysis_config.py   # Weights, paths, parameters
├── main.py                  # CLI orchestrator (to be implemented)
├── scoring.py               # Composite score computation (to be implemented)
├── audit.py                 # qᵢ component calculations (to be implemented)
├── sensitivity.py           # Sensitivity analysis (to be implemented)
├── figures.py               # Visualization (to be implemented)
└── utils.py                 # Helpers (to be implemented)
```

## Relationship to Step 2d

| Aspect | Step 2d (CSI Grid Scan) | Step 2e (PU Composite) |
|--------|------------------------|------------------------|
| **Purpose** | Diagnostic exploration | Threshold calibration |
| **Objective** | Maximize CSI | Maximize composite score |
| **Events database** | Leal et al. (91 events) | Expanded documentary (56 events) |
| **Unmatched episodes** | Counted as F (hard false alarms) | Weighted by plausibility qᵢ |
| **Under-reporting** | Not addressed | Explicitly modeled |
| **Threshold output** | CSI-optimal (for comparison only) | PU-optimal (final calibrated pair) |

**Step 2d was diagnostic, not prescriptive.** It revealed that classical CSI metrics fail under incomplete reporting (FAR=0.984). The CSI-optimal thresholds from Step 2d are **not used** by subsequent steps. Step 2e performs its own independent threshold sweep and produces the **final calibrated threshold pair** for use in Step 3 (Storm Catalog Generation).

## Manual Audit Process

Before running the full composite calibration, the researcher should:

1. **Export unmatched episodes** from Step 2d false alarm analysis
2. **Audit top-priority episodes** (highest Iᵢ values) for external evidence
3. **Record Eᵢ flags** in `data/audit/unmatched_episode_audit.csv`

The audit can be incremental — non-audited episodes default to Eᵢ=0 while still contributing through Iᵢ and Cᵢ.

### Audit CSV Format

```csv
episode_id,municipality_code,date_start,date_end,E_i,evidence_source,audit_date,auditor_notes
ep_001,4205407,2015-06-15,2015-06-16,1,"SC Civil Defense bulletin 2015-06-16",2026-04-08,Confirmed flooding in Florianópolis
ep_002,4209102,2018-07-12,2018-07-12,0,,2026-04-08,No corroborating sources found
```

## References

- Bekker, J., and Davis, J. (2020). Learning from positive and unlabeled data: a survey. *Machine Learning*, 109, 719-760.
- Delforge, D., et al. (2025). EM-DAT: the Emergency Events Database. *IJDRR*, 124, 105509.
- Donges, J. F., et al. (2016). Event coincidence analysis for quantifying statistical interrelationships. *EPJST*, 225, 471-487.
- Wyatt, F. R., et al. (2023). Investigating bias in impact observation sources. *IJDRR*, 90, 103639.
