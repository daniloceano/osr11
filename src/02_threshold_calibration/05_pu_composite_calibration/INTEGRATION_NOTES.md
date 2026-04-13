# Step 2e Integration Notes

**Module:** `src/02_threshold_calibration/05_pu_composite_calibration/`

This document describes how Step 2e (PU Composite Calibration) integrates with the existing OSR11 threshold calibration pipeline.

---

## Position in the Workflow

```
STEP 2 — Threshold Calibration (umbrella step)
│
├─ 2a — Exploratory Data Analysis
│       └─ produces: spatial/temporal understanding, coastal grid points
│
├─ 2b — Preliminary Compound Event Occurrence
│       └─ produces: EventRecord infrastructure, municipality→grid mapping
│
├─ 2c — Tidal Sensitivity Analysis
│       └─ produces: SSH_total = zos + FES2022 (canonical definition)
│
├─ 2d — CSI Grid Scan [DIAGNOSTIC]
│       └─ produces: CSI metrics (for comparison only — thresholds NOT used)
│
└─ 2e — PU Composite Calibration [FINAL CALIBRATION]
        └─ produces: PU-optimal thresholds (final calibrated pair for Step 3)
```

**Important:** Step 2d was a diagnostic exploration that revealed the limitations of classical verification metrics under incomplete reporting (FAR=0.984). The CSI-optimal thresholds from Step 2d are **not** used by Step 2e or subsequent steps. Step 2e performs its own independent threshold sweep using the PU composite score.

---

## What 2e Consumes

### Primary Input: Expanded Documentary Database

| Item | Path | Description |
|------|------|-------------|
| Events CSV | `data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv` | 56 curated ressaca events (1998–2020) |
| Methodology | `data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md` | Documentary search protocol |

The expanded database was curated from news archives, academic theses/dissertations, and technical reports. Each event has:
- Explicit marine-forcing evidence
- Traceable source citation (URL + title)
- Municipality-level resolution with coastal sector attribution

### From Step 2b (Preliminary Compound)

| Item | Path/Module | Usage in 2e |
|------|-------------|-------------|
| `load_unified_dataset()` | `src/02_threshold_calibration/02_preliminary_compound/io.py` | Load metocean data |
| `build_event_records()` | `src/02_threshold_calibration/02_preliminary_compound/events.py` | Municipality→grid matching |

### From Step 2c (Tidal Sensitivity)

| Item | Path/Module | Usage in 2e |
|------|-------------|-------------|
| `build_tide_cache()` | `src/02_threshold_calibration/03_tidal_sensitivity/tides.py` | FES2022 tide series |
| `add_tide_to_ssh()` | `src/02_threshold_calibration/03_tidal_sensitivity/tides.py` | SSH_total computation |
| SSH_total definition | Canonical: `zos(00:00 UTC) + tide(daily max)` | Applied unchanged |

### From Step 2d (Diagnostic Comparison Only)

| Item | Path | Usage in 2e |
|------|------|-------------|
| `tab_TC4_metrics_full.csv` | `outputs/threshold_calibration/tables/` | **Comparison only** — not used for threshold selection |
| Directional matching window | `[D-2, D-1, D, D+1 00Z]` | Convention reused |
| Episode clustering logic | `calibration.py` | Logic reused |

**Note:** Step 2e does NOT use the CSI-optimal thresholds from Step 2d. It performs its own independent threshold sweep.

---

## What 2e Produces

### Primary Outputs

| File | Description |
|------|-------------|
| `tab_TC5_episode_audit.csv` | Per-episode table with q_i components (E_i, I_i, C_i, q_i) |
| `tab_TC5_pu_metrics_full.csv` | R_pos, B, F_soft, Score for all 81 threshold pairs |
| `tab_TC5_pu_metrics_ranked.csv` | Ranked by PU optimal selection hierarchy |
| `tab_TC5_optimal_pair_pu.csv` | Final calibrated threshold pair under PU framework |
| `tab_TC5_csi_vs_pu_comparison.csv` | Side-by-side CSI vs PU comparison |

### Figures

| File | Description |
|------|-------------|
| `fig_TC5_H1_score_heatmap.png` | Composite score across threshold pairs |
| `fig_TC5_S1_csi_vs_pu.png` | Visual comparison of CSI vs PU optimal pairs |

### Sensitivity Analysis

| File | Description |
|------|-------------|
| `tab_TC5_sensitivity_weights.csv` | Optimal pair under alternative (w₁, w₂, w₃) |
| `tab_TC5_sensitivity_alpha.csv` | Optimal pair under alternative (α_E, α_I, α_C) |
| `tab_TC5_sensitivity_btarget.csv` | Optimal pair under alternative B_target values |

---

## Manual Audit Inputs Required

Step 2e requires external evidence flags (E_i) for unmatched episodes. These are provided via a manually curated CSV file:

**Path:** `data/audit/unmatched_episode_audit.csv`

**Format:**
```csv
episode_id,municipality_code,date_start,date_end,E_i,evidence_source,audit_date,auditor_notes
```

**Audit process:**
1. Export unmatched episodes from Step 2d (run `--export-audit`)
2. For each high-priority episode (sorted by I_i descending):
   - Search Civil Defense bulletins, municipal reports, news archives
   - Record E_i = 1 if corroborating evidence found, E_i = 0 otherwise
3. Non-audited episodes default to E_i = 0

**Recommended audit scope:** Top 100–200 episodes by I_i (physical intensity). Full audit of 1,298 episodes is impractical.

---

## How 2e Fits the Scientific Narrative

### Problem Statement

Step 2d (CSI Grid Scan) was a diagnostic exploration that revealed fundamental limitations of classical verification metrics under incomplete reporting. The optimal CSI threshold pair (Hₛ=q90, SSH_total=q90) achieved FAR=0.984, meaning 98.4% of detected compound episodes had no matching reported disaster.

This extremely high "false alarm" rate could indicate:
1. Overly permissive thresholds (detecting non-impactful conditions)
2. Systematically incomplete disaster database (under-reporting)

Given known Civil Defense reporting limitations (Wyatt et al., 2023; Delforge et al., 2025), interpretation #2 is dominant. Step 2d demonstrated that **CSI is not appropriate for this application**.

### Step 2e Solution

Step 2e addresses this by:

1. **Using an expanded documentary database** curated from news, theses, and technical reports (56 events vs 91 in the original Civil Defense database, but with more rigorous marine-forcing evidence)

2. **Treating unmatched episodes as unlabeled** rather than false alarms, applying a soft penalty weighted by episode plausibility

3. **Performing an independent threshold sweep** — Step 2e does NOT inherit thresholds from Step 2d

### Relationship to Steps 3+

The threshold pair selected in Step 2e (θ*_PU) is the **final calibrated output** used by:

- **Step 3 (Storm Catalog Generation):** Threshold for identifying exceedance episodes
- **Step 4 (Compound Event Detection):** Same threshold applied to compound identification
- **Step 5 (Exposure Analysis):** Compound event frequency based on calibrated thresholds

The CSI-optimal pair from Step 2d will be reported alongside the PU-optimal pair for methodological comparison, demonstrating why the PU approach is necessary under database incompleteness.

---

## Backward Compatibility

Step 2e is **additive** to the existing pipeline:

- Does not modify any Step 2a–2d code or outputs
- Imports reusable functions rather than duplicating logic
- Uses the same output directory structure (`outputs/threshold_calibration/`)
- Follows naming conventions (`tab_TC5_*`, `fig_TC5_*`)

The module alias `pu_composite_calibration` is registered in `src/__init__.py` for backward-compatible imports:

```python
from src.pu_composite_calibration.config import CFG
```

---

## Step 2e Status

Step 2e is **complete**. All implementation tasks are done:

- `scoring.py` — composite score computation (independent threshold sweep, PU metrics, optimal pair selection)
- `audit.py` — E_i, I_i, C_i calculations and episode audit table
- `main.py` — full CLI with `--all`, `--hits-misses`, `--unmatched`, `--scoring`, `--sensitivity`, `--figures`, `--summary`
- `figures.py` — heatmaps, comparison plots, q_i distribution
- `sensitivity.py` — weight, alpha, and B_target sensitivity experiments

The PU-optimal threshold pair is stored in `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` and is the authoritative threshold source for Step 3 (Storm Catalog Generation).

## Next Step

**Step 3 — Storm Catalog Generation** (`src/03_storm_catalog_generation/`):
Apply the PU-optimal threshold pair (`tab_TC5_optimal_pair_pu.csv`) to the full 1993–2025 metocean dataset to generate independent Hₛ and SSH_total storm catalogs at each coastal grid point.
