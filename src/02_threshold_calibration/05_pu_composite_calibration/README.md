# Step 2e — PU Composite Calibration

**Part of STEP 2 — Threshold Calibration (umbrella step)**  
**Location:** `src/02_threshold_calibration/05_pu_composite_calibration/`


> ### ⚠ Recalibrado em 2026-07-30 — par **q70/q99**
>
> Este README descreve o arcabouço PU, que permanece válido. Cinco elementos
> mudaram: o **detector pontuado** (agora Hₛ e `zos` livre de maré, com portão
> `max(SWL) > HAT` — não mais `SSH_total`), a **grade** (121 pares, com q95 e
> q99), o **termo de carga** (desvio bilateral de uma taxa esperada), os
> **pesos** (0,30/0,60/0,10) e os **alphas** (0,20/0,50/0,30).
>
> Onde o texto abaixo diz `SSH_total`, leia `zos`; onde diz q90/q90, leia
> q70/q99. Detalhe completo em `config/PARAMETER_DECISIONS.md`,
> `SCIENTIFIC_NOTES.md` e AUD-01 §14. O estado anterior está preservado em
> `outputs/legacy_threshold_calibration_ssh_total/`.

## Overview

Calibration of compound event detection thresholds using a **positive-unlabeled (PU) composite score** that addresses systematic under-reporting in coastal disaster databases.

### Why PU Calibration?

Step 2d (CSI Grid Scan) revealed that classical verification metrics are unsuitable for this application: the optimal CSI threshold pair (Hₛ=q90, SSH_total=q90) achieved CSI=0.0151 with FAR=0.984, meaning 98.4% of detected compound episodes had no matching reported disaster. This extremely high "false alarm" rate reflects **database incompleteness**, not threshold miscalibration.

Step 2e addresses this by:

1. Using an **expanded documentary database** of coastal `ressaca` events curated from news, theses, and technical reports
2. Treating unmatched detected episodes as **unlabeled** (not automatically false)
3. Applying a **soft penalty** weighted by episode plausibility
4. Performing an **independent threshold sweep** — Step 2d thresholds are NOT used

### Combined Positive-Event Set

Step 2e uses BOTH reported-event databases as its positive set P:

1. **Expanded documentary database** (primary):
   - **File:** `data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`
   - **Events:** 56 documented `ressaca` episodes (1998–2020, 14 municipalities)
   - **Sources:** Academic theses/dissertations, news archives, technical reports

2. **Legacy Leal et al. (2024) database:**
   - **File:** `data/reported events/reported_events_Karine_sc.csv`
   - **Events:** 91 unique (municipality, date) rows (1998–2020, 22 municipalities)

**Combined positive set:** 147 unique (municipality, date) pairs, 27 union municipalities. The legacy database also serves as the E_i evidence source for unmatched episode audit.

### Threshold Computation Period

Percentile thresholds are computed from the **full metocean record** (1993–2025), not from the validated period. The validated period (1998–2020) restricts only the event-matching scan (Layers 1 and 2). This ensures maximum statistical robustness for threshold estimation.

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

| From | What | Role |
|------|------|------|
| Step 1 | `data/test/metocean_sc_full_unified_waverys_grid.nc` | Unified metocean dataset |
| Documentary search | `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv` | Combined positive set component (56 events) |
| Legacy database | `reported_events_Karine_sc.csv` | Combined positive set component (91 events) + E_i evidence source |
| Step 2b | Event record infrastructure, municipality→grid matching | Infrastructure reuse |
| Step 2c | SSH_total definition (zos + FES2022 daily max tide) | Variable definition |
| Step 2d | CSI optimal pair and metrics | **Comparison only — NOT used for threshold selection** |
| Manual (optional) | `data/audit/unmatched_episode_audit.csv` | E_i override for specific episodes |

**Step 2e performs its own independent threshold sweep.** The CSI-optimal thresholds from Step 2d are retained only for methodological comparison. The combined positive-event set (147 events from both databases) is the positive set P. The legacy database additionally serves as the E_i evidence source for unmatched episode audit.

## What This Step Produces

| Output | Description |
|--------|-------------|
| `tab_TC5_episode_audit.csv` | Per-episode audit table with qᵢ components |
| `tab_TC5_score_decomposition.csv` | Full Score decomposition: all 81 pairs with raw/weighted terms |
| `tab_TC5_qi_decomposition.csv` | qᵢ decomposition at optimal pair: per-episode weighted contributions |
| `tab_TC5_pu_metrics_full.csv` | Composite score across all threshold pairs |
| `tab_TC5_pu_metrics_ranked.csv` | Ranked by optimal selection hierarchy |
| `tab_TC5_optimal_pair_pu.csv` | Optimal threshold pair under PU framework |
| `tab_TC5_sensitivity_weights.csv` | Weight sensitivity results |
| `tab_TC5_sensitivity_alpha.csv` | Alpha sensitivity results |
| `tab_TC5_sensitivity_b_target.csv` | B_target sensitivity results |
| `tab_TC5_sensitivity_gap_days.csv` | Episode gap tolerance sensitivity results |
| `tab_TC5_event_capture_status.csv` | Per-event capture status at optimal pair |
| `tab_TC5_positive_event_union_audit.csv` | Combined positive-event provenance audit |
| `fig_TC5_H1_score_heatmap.png` | Composite score heatmap |
| `fig_TC5_H2_recall_heatmap.png` | R_pos heatmap |
| `fig_TC5_S1_csi_vs_pu_comparison.png` | CSI vs PU optimal pair comparison |
| `fig_TC5_S2_sensitivity_weights.png` | Weight sensitivity analysis |

### Score Decomposition Table (`tab_TC5_score_decomposition.csv`)

Full equation-level decomposition for all 81 threshold pairs (21 columns):

| Column | Description |
|--------|-------------|
| `hs_percentile` | Hₛ threshold as integer percentile (50–90) |
| `ssh_percentile` | SSH_total threshold as integer percentile (50–90) |
| `H`, `M`, `U` | Hits, misses, unmatched episodes |
| `P` | Total positive events (evaluable) |
| `Y` | Validated period length (years) |
| `R_pos` | Positive recall = H/P |
| `B_raw` | Raw burden = (H+U)/(Y × B_target_effective) before min(1, ·) clip |
| `B` | Clipped burden = min(1, B_raw) |
| `F_soft` | Soft unmatched penalty = Σ(1 − qᵢ) |
| `term_recall_raw` | = R_pos (unweighted recall term) |
| `term_burden_raw` | = B (unweighted burden term) |
| `term_fsoft_raw` | = F_soft / P (unweighted normalised soft penalty) |
| `w1`, `w2`, `w3` | Component weights (0.60, 0.20, 0.20) |
| `term_recall_weighted` | = w₁ × R_pos |
| `term_burden_weighted` | = −w₂ × B |
| `term_fsoft_weighted` | = −w₃ × F_soft / P |
| `Score` | = term_recall_weighted + term_burden_weighted + term_fsoft_weighted |

### qᵢ Decomposition Table (`tab_TC5_qi_decomposition.csv`)

Per-episode confidence decomposition at the optimal pair (22 columns):

| Column | Description |
|--------|-------------|
| `episode_id` | Unique episode identifier |
| `municipality` | Municipality name |
| `date_start`, `date_end` | Episode date range |
| `hs_peak`, `ssh_peak` | Peak Hₛ and SSH_total during episode |
| `n_days` | Episode duration |
| `E_i` | External evidence (0 or 1) |
| `I_i` | Physical intensity score ∈ [0, 1] |
| `C_season`, `C_multi`, `C_exposure` | Context coherence sub-indicators |
| `C_i` | Composite context coherence = mean(C_season, C_multi, C_exposure) |
| `alpha_E`, `alpha_I`, `alpha_C` | Confidence weight parameters (0.60, 0.30, 0.10) |
| `contrib_E` | = α_E × E_i (external evidence contribution) |
| `contrib_I` | = α_I × I_i (intensity contribution) |
| `contrib_C` | = α_C × C_i (context contribution) |
| `q_i_raw` | = contrib_E + contrib_I + contrib_C (before clip) |
| `q_i` | = clip(q_i_raw, 0, 1) (final confidence weight) |
| `penalty_component` | = 1 − q_i (this episode's contribution to F_soft) |

## Module Structure

```
src/02_threshold_calibration/05_pu_composite_calibration/
├── __init__.py              # Module docstring
├── README.md                # This file
├── RUN.md                   # Quick-start guide
├── SCIENTIFIC_NOTES.md      # Full methodological documentation
├── INTEGRATION_NOTES.md     # Workflow integration context
├── config/
│   ├── __init__.py
│   ├── analysis_config.py   # All user-editable parameters (weights, paths, etc.)
│   └── PARAMETER_DECISIONS.md  # Rationale for each parameter
├── main.py                  # CLI orchestrator (--all, --hits-misses, --scoring, …)
├── scoring.py               # Independent threshold sweep + composite score
├── audit.py                 # q_i component calculations (E_i, I_i, C_i)
├── sensitivity.py           # Sensitivity analysis (weights, alphas, B_target)
├── figures.py               # Heatmaps, comparison plots, q_i distribution
└── utils.py                 # Data loading, directory setup, logging
```

## Relationship to Step 2d

| Aspect | Step 2d (CSI Grid Scan) | Step 2e (PU Composite) |
|--------|------------------------|------------------------|
| **Purpose** | Diagnostic exploration | Threshold calibration |
| **Objective** | Maximize CSI | Maximize composite score |
| **Events database** | Leal et al. (91 rows / 72 unique storms) | Combined: expanded (56) + legacy (91) = 147 events |
| **Positive count P** | 91 (municipality×event pairs) | 147 (combined municipality×date pairs, 27 municipalities) |
| **Unmatched episodes** | Counted as F (hard false alarms) | Weighted by plausibility qᵢ |
| **Under-reporting** | Not addressed | Explicitly modeled |
| **Threshold output** | CSI-optimal (comparison only) | PU-optimal (final calibrated pair) |

**Step 2d was diagnostic, not prescriptive.** It revealed that classical CSI metrics fail under incomplete reporting (FAR=0.984). The CSI-optimal thresholds from Step 2d are **not used** by Step 2e or any subsequent step. Step 2e performs its own independent threshold sweep and produces the **final calibrated threshold pair** for use in Step 3 (Storm Catalog Generation).

**Event count note:** The legacy database has 105 raw CSV rows → 91 valid rows → 72 unique disaster IDs (storms). Step 2d uses 91 as the denominator. Step 2e uses P=147 from the combined positive-event set (expanded 56 + legacy 91, 0 exact overlaps, 27 union municipalities).

## Sensitivity Analysis

Four dimensions of sensitivity are tested, all with the optimal pair confirmed at q90/q90:

| Experiment | Parameter | Values tested | Result |
|-----------|-----------|---------------|--------|
| Weights | (w₁, w₂, w₃) | high_recall, balanced, default | q90/q90 stable |
| Alpha | (α_E, α_I, α_C) | evidence_heavy, intensity_moderate, default | q90/q90 stable |
| B_target | Per-municipality budget | 6, 12, 18, 24 ep/yr/muni | q90/q90 stable |
| Gap days | EPISODE_MAX_GAP_DAYS | 0, 1, 2, 3 | q90/q90 stable; Score: -3.22 → -3.02 |

## Context Coherence: Northern-Sector Exposure

**C_i^exposure = 1** for municipalities in the **Northern sector** of the Santa Catarina coast:

- Itapoá, São Francisco do Sul, Araquari, Balneário Barra do Sul, Barra Velha

These municipalities are treated as high-exposure because GLORYS12/WAVERYS grid
coverage is partially degraded in the northern sector (shallow bathymetry, complex
coastline), making genuine coastal impacts more likely to appear as unmatched
detections. This is configured in `config/analysis_config.py::EXPOSED_MUNICIPALITIES`.

See `config/PARAMETER_DECISIONS.md` for full rationale.

## External Evidence (E_i): Automatic + Optional Override

**Automatic (default):** E_i is computed by checking whether any legacy Civil Defense
record (`reported_events_Karine_sc.csv`) falls within the episode's municipality and
temporal window. No manual audit required for basic operation.

**Optional manual override:** A researcher-curated CSV at `data/audit/unmatched_episode_audit.csv`
can override E_i for specific episodes. Only the `episode_id` and `E_i` columns are required.
When present, manual flags take priority over the automatic rule.

```csv
episode_id,E_i,evidence_source,audit_date,auditor_notes
hs85_ssh80_FLO_20150619,1,"SC Civil Defense bulletin",2026-04-08,Confirmed flooding
hs70_ssh75_BAR_20180712,0,,2026-04-08,No corroborating sources found
```

## References

- Bekker, J., and Davis, J. (2020). Learning from positive and unlabeled data: a survey. *Machine Learning*, 109, 719-760.
- Delforge, D., et al. (2025). EM-DAT: the Emergency Events Database. *IJDRR*, 124, 105509.
- Donges, J. F., et al. (2016). Event coincidence analysis for quantifying statistical interrelationships. *EPJST*, 225, 471-487.
- Wyatt, F. R., et al. (2023). Investigating bias in impact observation sources. *IJDRR*, 90, 103639.
