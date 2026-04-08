# Parameter Decisions — Step 2e: PU Composite Calibration

This document explains every user-facing parameter in `analysis_config.py`,
distinguishing between fixed repository decisions and freely adjustable values.

---

## 1. Threshold Grid

| Parameter | Default | Adjustable? | Notes |
|-----------|---------|-------------|-------|
| `PCT_START` | 0.50 | Yes | First percentile level (q50) |
| `PCT_STOP` | 0.90 | Yes | Last percentile level (q90) |
| `PCT_STEP` | 0.05 | Yes | Step between levels (5 pp) |
| `EPISODE_MAX_GAP_DAYS` | 1 | Yes | Max gap within one episode |

**Fixed by repository:** Same grid as Step 2d (81 pairs) to enable direct comparison.
**Adjustable if needed:** Extend to q95 or use 2% step for finer resolution.

---

## 2. Composite Score Weights

```
Score(θ) = w1·R_pos(θ) − w2·B(θ) − w3·F_soft(θ)/P
```

| Parameter | Default | Adjustable? | Rationale |
|-----------|---------|-------------|-----------|
| `W1_RECALL` | 0.60 | **Yes** | Positive recall is the primary objective |
| `W2_BURDEN` | 0.20 | **Yes** | Annual burden penalty |
| `W3_SOFT_PENALTY` | 0.20 | **Yes** | Soft unmatched penalty |

**User decision required:** These weights express a value judgement about the
relative importance of capturing known events vs. limiting total detections.
The default w1=0.60 reflects that recall is the dominant concern.
Alternative presets are provided in `SENSITIVITY_WEIGHTS` for robustness checks.

---

## 3. Confidence Weight Parameters (q_i)

```
q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)
```

| Parameter | Default | Adjustable? | Rationale |
|-----------|---------|-------------|-----------|
| `ALPHA_E` | 0.60 | **Yes** | External evidence dominates plausibility |
| `ALPHA_I` | 0.30 | **Yes** | Physical intensity is secondary |
| `ALPHA_C` | 0.10 | **Yes** | Context coherence is a weak heuristic |

**User decision required:** The relative weight of evidence vs. intensity vs.
context is a methodological choice. α_E=0.60 reflects that documentary
corroboration is stronger evidence than physical plausibility alone.
Alternative presets are in `SENSITIVITY_ALPHA`.

---

## 4. Annual Burden Target (per municipality)

```
B_target_effective = B_TARGET_PER_MUNICIPALITY × n_municipalities
B(θ) = min(1, [H(θ) + U(θ)] / [Y × B_target_effective])
```

| Parameter | Default | Adjustable? | Notes |
|-----------|---------|-------------|-------|
| `B_TARGET_PER_MUNICIPALITY` | 12.0 | **Yes** | Episodes per year per municipality |
| `n_municipalities` | Runtime | — | Derived from event records (unique municipalities with valid grid coverage) |

**Scientific rationale:** One compound coastal event per month per municipality
(12/year) is a climatologically defensible upper bound for the SC coast. Events
are seasonal and clustered, and not every municipality is hit in every storm, so
12/year is permissive but not unrealistic.

**Why scale by n_municipalities?** Total detections grow proportionally with
spatial coverage. An analysis with 14 municipalities should have a budget of
12 × 14 = 168 total detections/year, not the same flat budget as an analysis
with 4 municipalities. Without this scaling, adding more municipalities
artificially increases apparent overdetection.

**Typical effective value:** For the expanded events database (14 unique municipalities):
    B_target_effective = 12 × 14 = 168 ep/yr

Sensitivity to this choice is tested via:
    `SENSITIVITY_B_TARGET = [6, 12, 18, 24]`  (all in ep/yr/municipality)

---

## 5. Context Coherence Parameters (C_i)

### Active Season (C_i^season)

| Parameter | Default | Adjustable? | Notes |
|-----------|---------|-------------|-------|
| `ACTIVE_SEASON_MONTHS` | [4, 5, 6, 7, 8, 9, 10] | Yes | April–October |

**Fixed by repository:** The April–October window captures the climatological
peak of austral autumn–winter storm activity affecting the Santa Catarina coast
(extratropical cyclone season). Outside this window (November–March), compound
events can still occur but are less frequent.

### Exposed Municipalities (C_i^exposure)

**AUTHORITATIVE DECISION (Step 2e):**

```
EXPOSED_MUNICIPALITIES = [
    "Itapoá",
    "São Francisco do Sul",
    "Araquari",
    "Balneário Barra do Sul",
    "Barra Velha",
]
```

These five municipalities correspond to the **Northern sector** of the Santa
Catarina coast (approximately 26.1°S to 26.6°S).

**Scientific rationale:**
1. The northern sector receives wave energy from a different directional window
   compared to the central and southern sectors, being more exposed to NE swell.
2. GLORYS12 and WAVERYS grid coverage is partially degraded in this region
   (near-coastal bathymetric complexity), so genuine compound events here may
   fail to be detected by the model even when they occurred in reality.
3. By assigning C_i^exposure = 1 to northern-sector episodes, the framework
   partially compensates for the systematic model under-detection in this region,
   increasing the soft plausibility of unmatched detections there.

**How to adjust:** Replace this list with names from
`src/02_threshold_calibration/02_preliminary_compound/events.py::_SOUTH_SC_COORDS`.
Names must match exactly (accent-sensitive).

---

## 6. External Evidence (E_i): Adaptation Note

**Ideal definition:** E_i = 1 if at least one independent external source
(Civil Defense bulletin, municipal emergency report, independent news coverage)
confirms a coastal impact at this municipality within the episode's temporal window.

**Repository adaptation (current implementation):**
Because the repository has limited documentary density for the full 1998–2020
period, E_i is computed from the two available documentary datasets:

1. **Primary positive set** (`ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`,
   56 events): Used to define P (positive labels). Unmatched episodes are those
   not paired with any record in this set.

2. **Legacy Civil Defense database** (`reported_events_Karine_sc.csv`, 105 rows,
   91 unique disaster IDs): Used as corroborating evidence for unmatched episodes.
   If a legacy event falls within the episode's spatiotemporal window at the same
   municipality, E_i = 1.

3. **Optional manual override** (`data/audit/unmatched_episode_audit.csv`): A
   researcher-curated CSV that can override E_i for specific episodes. This file
   is optional — if absent or incomplete, non-audited episodes fall back to the
   rule-based approach above.

**Known limitation:** This adaptation uses a subset of the documentary record
that is not fully independent from the positive set. In a fully-equipped study,
E_i would rely on a broader and truly independent evidence layer (e.g., news
archive scraping, broader Civil Defense records at national level, social media
monitoring). The current approach is documented as an operational compromise.

---

## 7. Matching Window (Fixed)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `MATCH_WINDOW_OFFSETS` | [-2, -1, 0, 1] | Inherited from Steps 2b–2d |

**Fixed by repository:** The [D-2, D-1, D, D+1 00Z] window is established in
Step 2c (Tidal Sensitivity) and used consistently throughout Step 2. Changing it
would require re-running all prior steps.

---

## 8. Sensitivity Analysis Presets

These are not primary parameters but document which alternatives are tested
to assess robustness.

| Setting | Alternatives tested |
|---------|---------------------|
| `SENSITIVITY_WEIGHTS` | high_recall (w1=0.70), balanced (w1=0.50), default |
| `SENSITIVITY_ALPHA` | evidence_heavy (α_E=0.70), intensity_moderate (α_E=0.50), default |
| `SENSITIVITY_B_TARGET` | 5, 10, 15, 20 episodes/year |

---

## 9. SSH_total Definition (Fixed)

```
SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)
```

**Fixed by repository:** Inherited from Steps 2c–2d. Not adjustable in Step 2e
without re-running the full pipeline.

**Known approximation:** GLORYS12 provides only one SSH value per day (00:00 UTC
snapshot); a true daily-maximum SSH cannot be derived from this product. The
daily-maximum FES2022 tide combined with the midnight GLORYS12 SSH represents
the "background SSH + worst-case tidal contribution" on any given day.
