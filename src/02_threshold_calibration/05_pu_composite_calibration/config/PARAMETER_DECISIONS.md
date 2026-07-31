# Parameter Decisions — Step 2e: PU Composite Calibration

This document explains every user-facing parameter in `analysis_config.py`,
distinguishing between fixed repository decisions and freely adjustable values.

> **Recalibration of 2026-07-30.** Five things changed on that date, all
> recorded below and in AUD-01 §14: the **scored detector**, the **sweep grid**,
> the **burden term**, the **score weights** and the **confidence alphas**. The
> superseded state is preserved in
> `outputs/legacy_threshold_calibration_ssh_total/`. The pair moved from
> **q90/q90 to q70/q99**.

---

## 1. Threshold Grid — **changed 2026-07-30**

| Parameter | Value | Adjustable? | Notes |
|-----------|-------|-------------|-------|
| `PCT_LEVELS` | `[0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]` | Yes | **The authoritative grid.** 11 levels, 121 pairs |
| `PCT_START` / `PCT_STOP` / `PCT_STEP` | 0.50 / 0.90 / 0.05 | — | **Retained but no longer the Step 2e grid source.** Kept in `CFG` so consumers that read those keys keep working |
| `EPISODE_MAX_GAP_DAYS` | 1 | Yes | Max gap within one episode |

The grid used to run q50–q90 in steps of 0.05 — 9 levels, 81 pairs, matching
Step 2d. It is now an **explicit list**, because 0.99 does not fall on a regular
0.05 step.

**Why it was extended.** AUD-02 §4 recorded that the selected optimum sat on the
q90 **edge** of the grid, "um sinal de que o ótimo pode estar fora dela".
Extending to q95 and q99 tested that directly. The answer, in
`outputs/audit/AUD-01_step2e_score_surface/`, is that the optimum was indeed
outside — but on the **level** axis, not the wave axis, and only after the
scoring criterion was repaired (§2 below).

**To change the sweep:** edit `PCT_LEVELS`. Editing the three scalars alone has
no effect on Step 2e.

---

## 2. Composite Score Weights — **changed 2026-07-30**

```
Score(θ) = w1·R_pos(θ) − w2·B(θ) − w3·F_soft(θ)/P
```

| Parameter | Value | Was | Adjustable? | Rationale |
|-----------|-------|-----|-------------|-----------|
| `W1_RECALL` | **0.30** | 0.60 | **Yes** | Positive recall |
| `W2_BURDEN` | **0.60** | 0.20 | **Yes** | Deviation from the expected detection rate |
| `W3_SOFT_PENALTY` | **0.10** | 0.20 | **Yes** | Soft unmatched penalty |

**Why they changed.** Under the previous triplet the third term dominated
without bound: `F_soft/P` reached **29.4** at q50/q50 against a maximum possible
recall contribution of **0.60**. Once the grid was extended past q90 the
consequence became visible — **Spearman(Score, accepted episodes) = −0.999**.
The score was a monotone preference for detecting nothing, and its optimum was
the emptiest pair in the grid (q99/q99: 40 accepted episodes against 147
positive events, recall 0.034, *below* the 0.190 of q90/q90). The q90/q90 pair
had only looked optimal because the grid stopped there.

The burden now carries the dominant weight because it is **the only term
anchored on an external observation** (§4). The soft penalty is retained, at
reduced weight, as a tiebreaker on the plausibility of unmatched detections
rather than as the objective.

**This is a change of scoring criterion, not of scored detector**, and was
authorised explicitly by the responsible researcher after the numbers above were
presented. Recorded in AUD-01 §14, entry of 2026-07-30.

`SENSITIVITY_WEIGHTS` retains the superseded triplet under the label
`legacy_2026_07_29`, so its behaviour stays reproducible. Applied to the new
two-sided burden it returns q99/q99, which confirms the reweighting was
necessary rather than cosmetic.

---

## 3. Confidence Weight Parameters (q_i) — **changed 2026-07-30**

```
q_i = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)
```

| Parameter | Value | Was | Adjustable? | Rationale |
|-----------|-------|-----|-------------|-----------|
| `ALPHA_E` | **0.20** | 0.60 | **Yes** | External evidence — sparse and known to under-report |
| `ALPHA_I` | **0.50** | 0.30 | **Yes** | Physical intensity |
| `ALPHA_C` | **0.30** | 0.10 | **Yes** | Context coherence |

**Why they changed, 2026-07-30.** Measured on the recalibrated sweep,
`E_i = 1` in **154 of 436 352** unmatched episodes — **0.04 %**. With
`α_E = 0.60`, `q_i` was therefore capped at **0.40 by construction** for
99.96 % of episodes, so every unmatched detection carried a penalty of at least
0.60 regardless of how physically plausible it was.

That is not a measurement of implausibility; it is a measurement of the
sparseness of the documentary record. It also contradicts the premise of the
whole PU framework: the reported record is incomplete (AUD-18 records that no
independent validation base exists), so weighting the *absence* of a documentary
match at 0.60 treats a probable false negative of the Civil Defense register as
strong evidence against the detection.

The weight moved to the two terms that do not depend on the register — the
physical intensity of the episode and its contextual coherence. Mean `q_i` rises
from 0.276 to 0.543.

`SENSITIVITY_ALPHA` retains the superseded triplet as `legacy_2026_07_29`.

---

## 4. Expected Detection Rate — **one-sided ceiling → two-sided anchor, 2026-07-30**

```
rate(θ) = [H(θ) + U(θ)] / [Y × n_municipalities]
B(θ)    = min(1, |log10( rate(θ) / BURDEN_TARGET_PER_MUNICIPALITY )|)
```

| Parameter | Value | Was | Adjustable? | Notes |
|-----------|-------|-----|-------------|-------|
| `BURDEN_TARGET_PER_MUNICIPALITY` | **2.0** | 12.0 | **Yes** | *Expected* detections/year/municipality |
| `BURDEN_MODE` | `"two_sided"` | `"ceiling"` | **Yes** | `"ceiling"` reproduces the old behaviour |
| `n_municipalities` | Runtime (27) | — | — | Union city count across both event databases |

**Why the form changed.** The former term penalised only over-detection and was
minimised at **zero** detections. It therefore pushed in the same direction as
the soft penalty, and raising its weight made the "detect nothing" pull
*stronger*, not weaker: sweeping `w2` from 0.20 to 0.69 left the optimum pinned
at the emptiest pair of the grid. A one-sided ceiling cannot anchor anything.

The term is now a **deviation from an expected rate, in both directions**. A
detector that flags far fewer episodes than expected is penalised as much as one
that floods, which is what gives the composite score an interior optimum. The
log ratio makes the penalty symmetric in relative terms — half the expected rate
costs the same as twice — and the cap at 1 keeps the term in [0, 1] like the
other two, so that `w1+w2+w3 = 1` is meaningful.

**Anchoring the rate — what the observed record does and does not fix.**
Leal et al. (2024, *Nat Hazards* **120**, 11465–11482) record **72 distinct
declared coastal disasters** in Santa Catarina over 1998–2023, i.e. **2.77
declared events per year** for the whole SC coast. Combined with the expanded
documentary archive, the Step 2e positive set holds 147 (municipality, date)
pairs over 22.4 validated years across 27 municipalities:

```
reported rate = 147 / (22.4 × 27) = 0.243 detections/municipality/year
```

That is a **lower bound, not an expectation**. Under-reporting is the premise of
the whole PU framework, and AUD-18 records that no independent validation base
exists against which to measure it. Choosing the anchor therefore means choosing
an **assumed under-reporting factor**, which is a declared assumption and is
treated as one.

**The default of 2.0 assumes the true rate is about 8× the declared rate** — one
episode per municipality every six months. The superseded 12.0 was never an
expectation; this document previously described it as "a climatologically
defensible **upper bound**", which is 49× the reported rate and unusable as the
centre of a two-sided penalty.

Sensitivity spans roughly 2× to 25× the reported rate:
    `SENSITIVITY_B_TARGET = [0.5, 1.0, 2.0, 3.0, 6.0]`

The selected pair is stable at q70/q99 for any target ≥ 2.0; at 1.0 it moves to
q85/q99 and at 0.5 to q95/q99.

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
| `SENSITIVITY_WEIGHTS` | recall_leaning (0.40/0.50/0.10), rate_anchored (0.20/0.70/0.10), penalty_leaning (0.30/0.55/0.15), default, legacy_2026_07_29 (0.60/0.20/0.20) |
| `SENSITIVITY_ALPHA` | evidence_leaning (0.30/0.45/0.25), evidence_minimal (0.10/0.55/0.35), context_leaning (0.20/0.45/0.35), default, legacy_2026_07_29 (0.60/0.30/0.10) |
| `SENSITIVITY_B_TARGET` | 0.5, 1.0, 2.0, 3.0, 6.0 detections/year/municipality |
| `SENSITIVITY_GAP_DAYS` | 0, 1, 2, 3 days |

**Result of the 14 variants (2026-07-30).** `q_zos = q99` is selected in **14 of
14**. The wave percentile is the poorly determined axis: q70 in 8, q50 in 2, q85
in 2, q95 in 1, q99 in 1. The six best pairs differ by less than 1 % in score and
span q50 to q80, so the composite score does **not** have the information to
choose the wave threshold. That matters for AUD-02: if a physical floor is
adopted for `thr_hs`, it will have to come from outside this calibration.

---

## 9. Scored Detector — **changed 2026-07-30**

Step 2e now scores **exactly the production detector**:

```
wave  : Hs  >= q_hs  local
level : zos >= q_zos local                (tide-free; NOT SSH_total)
gate  : max(SWL) > HAT over the overlap days, with
        SWL = (zos - local mean of zos) + tide_daily_max
        HAT = max(tide_daily_max) over 1993-2025, per grid point
```

**Why.** The calibration used to build `SSH_total = zos + tide` per point and
score threshold pairs against it. Production stopped reading `SSH_total` on
2026-07-29, when the tide became a conditioning variable rather than a forcing,
and under the HAT gate adopted on 2026-07-30 it does not read it at all.
Scoring pairs against a variable the detector never reads is a scientific
inconsistency; it was recorded as an open uncertainty in the AUD-01 closure of
2026-07-29 and is resolved here.

**One detector, both layers.** Layers 1 and 2 now call the same
`accepted_episodes_at_point`, so a "hit" and an "unmatched episode" are the same
object seen from the two sides of the matching relation. Without a gate the two
formulations coincide — an episode intersects a causal window exactly when one
of its compound days does — so this is a strict generalisation, not a change of
criterion.

**Column names kept, meaning changed.** `thr_ssh_pct` is retained throughout the
tables and the downstream code; since this date it carries the **`zos`**
percentile, not an `SSH_total` percentile. Likewise `EpisodeRecord.ssh_peak`
carries the episode maximum of `zos`, so that `compute_I_i` keeps comparing a
peak against the percentile of the very series that produced it. `swl_peak` and
`hat` were added as gate diagnostics.

---

## 10. The selected pair — **q70/q99**

| | q90/q90 (superseded) | **q70/q99 (selected)** |
|---|---:|---:|
| Accepted compound episodes in SC | 1 224 | **484** |
| H — reported events captured | 28 of 147 | **28 of 147** |
| `R_pos` | 0.1905 | **0.1905** |
| U — unmatched episodes | 2 214 | **831** |
| Detection rate /municipality/year | 3.71 | **1.42** (target 2.0) |
| `B` | 0.2684 | **0.1482** |
| `F_soft` | 1 142.0 | **420.4** |
| **Score** | −0.8808 | **−0.3178** |

Both scored under the **same** new detector, so the comparison is like for like;
the table is written to `tab_TC5_selected_vs_incumbent.csv` on every run.

**The new pair does not win by detecting fewer reported events.** Recall is
identical. It wins by producing **62 % less unmatched noise** at the same
recall, and by landing closer to the anchored rate.

It is **not degenerate**: 484 accepted episodes over 12 of 12 SC grid points,
3.29 episodes per positive event. `tab_TC5_detection_census.csv` reports the
sample size behind every pair and flags the 11 pairs that accept fewer episodes
than there are positives to recall — without it, a near-empty pair looks
excellent to any score whose penalties collapse toward zero.

**Known cost, recorded in AUD-02 §14.** q70 lowers the wave percentile, and with
it the `thr_hs` floor across the 808 production points: minimum 0.20 m → **0.14
m**, points below 1.0 m 35 → **56**, below 1.5 m 129 → **256**. This was
measured and presented before execution, and the responsible researcher chose to
proceed. AUD-02 remains open and is now **aggravated**.

**Column names.** `thr_ssh_pct` and `EpisodeRecord.ssh_peak` keep their names for
compatibility with `audit.py`, the figures and Step 3, but now carry the **`zos`**
percentile and the **`zos`** peak. The tide-free level threshold is visibly a
different quantity: median 0.277 m at q90 in SC, against 0.66 m for `SSH_total`.

**Known approximation, unchanged:** GLORYS12 provides one `zos` value per day
(00:00 UTC snapshot) while the tide is a daily maximum, so `SWL` does not share a
timestamp between its two terms and slightly overstates the instantaneous level.

### Selected pair, 2026-07-30

**q70 / q99.** Against the superseded q90/q90 under the *same* detector:

| | q90/q90 | **q70/q99** |
|---|---:|---:|
| accepted episodes (SC) | 1 224 | **484** |
| H (of P = 147) | 28 | **28** |
| `R_pos` | 0.1905 | **0.1905** |
| U | 2 214 | **831** |
| rate (det./muni/yr) | 3.71 | **1.42** |
| `B` | 0.2684 | **0.1482** |
| `F_soft` | 1 142.0 | **420.4** |
| **Score** | −0.8808 | **−0.3178** |

Identical recall with **62 % fewer unmatched detections**. The pair does not win
by detecting fewer reported events; it wins by detecting less noise. It is not
degenerate: 484 episodes over 12 of 12 SC grid points, 3.29 episodes per
positive event. Full surface in `tab_TC5_detection_census.csv` and
`tab_TC5_selected_vs_incumbent.csv`.

**Consequence for AUD-02, recorded honestly:** q70 *lowers* the wave threshold.
The minimum `thr_hs` over the 808 production points falls from 0.20 m to
**0.14 m**, and points below 1.5 m rise from 129 to **256**. This worsens AUD-02,
which blocks publication. It was presented to the responsible researcher before
execution and he chose to proceed. See AUD-02 §14.
