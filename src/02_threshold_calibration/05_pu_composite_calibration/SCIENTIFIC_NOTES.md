# SCIENTIFIC_NOTES — Step 2e: Threshold Calibration (PU Composite Score)

**Part of:** Step 2 — Threshold Calibration (umbrella step)

**Module**: `src/02_threshold_calibration/05_pu_composite_calibration/`
**Project**: OSR11 — Compound Coastal Flooding Hazard Assessment, Santa Catarina coast
**Authors**: Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal

---

## Research Questions

1. How should compound event detection thresholds be calibrated when the validation database
   is known to be systematically incomplete?

2. Can a positive-unlabeled (PU) framework produce well-calibrated thresholds by treating
   unmatched detected episodes as unlabeled rather than as hard false alarms?

3. What is the sensitivity of the optimal threshold pair to the choice of score component
   weights and confidence weight parameters?

---

## Motivation: The Under-Reporting Problem

### Evidence from Step 2d (Diagnostic)

Step 2d (CSI Grid Scan) was a diagnostic exploration that revealed fundamental limitations of
classical verification metrics. Using the original Civil Defense database
(91 valid municipality×event rows from 105 raw entries, corresponding to 72 unique storms),
the CSI-optimal threshold pair (Hₛ=q90, SSH_total=q90) yielded:

- **H = 21** hits (reported events captured)
- **M = 70** misses (reported events not captured)
- **F = 1,298** "false alarms" (unmatched compound episodes)
- **CSI = 0.0151**
- **FAR = 0.984**

This extremely high FAR (98.4%) demonstrates that CSI treats nearly all detected compound
episodes as false alarms. Two interpretations are possible:

1. **The thresholds are too permissive** — detecting many non-impactful ocean conditions.

2. **The disaster database is incomplete** — many detected episodes are real unreported events.

Given known limitations of Civil Defense disaster reporting (Wyatt et al., 2023; Delforge
et al., 2025), interpretation #2 is dominant. **Step 2d demonstrated that CSI is not
appropriate for this application.**

### Why Classical CSI Is Not Suitable

The classical Critical Success Index:

$$
CSI(\theta) = \frac{H(\theta)}{H(\theta) + M(\theta) + F(\theta)}
$$

assumes that F (false alarms) is known with confidence. In reality, many elements of U
(unmatched detections) may be:

1. **True false alarms** — physically unremarkable conditions misclassified as compound events
2. **True unreported events** — real coastal impacts not captured in the disaster database

Treating all U as hard false alarms biases calibration toward overly restrictive thresholds
that maximize specificity at the cost of sensitivity.

---

## Theoretical Framework: Positive-Unlabeled Learning

### PU Learning Principles

In positive-unlabeled (PU) learning (Bekker and Davis, 2020), only the positive class is
reliably labeled. The unlabeled set contains a mixture of positives and negatives, with
unknown proportions.

Applied to compound event calibration:

| Category | Interpretation |
|----------|----------------|
| **Labeled positives (P)** | Reported coastal disasters (91 events in SC database) |
| **Unlabeled (U)** | Detected compound episodes without matching reports |
| **True positives in U** | Real but unreported coastal impacts |
| **True negatives in U** | Physically unremarkable ocean conditions |

The key insight: **U should not be automatically equated to F**.

### Adaptation for Threshold Calibration

The proposed composite score applies PU principles to threshold optimization:

1. **Confirmed positives** are treated as reliable ground truth
2. **Unmatched detections** receive a soft penalty weighted by their plausibility
3. **Plausibility** is estimated from external evidence, physical intensity, and context

This is not a full PU learning model (no class prior estimation or classifier training), but
rather a PU-inspired scalarization that explicitly acknowledges the uncertain status of
unmatched detections.

---

## Reported Events Database

### Combined Positive-Event Set (Step 2e)

Step 2e uses a single harmonized positive-event set assembled from two input databases
(see `load_combined_events()` in utils.py). The combined set is the analytical object;
individual database provenance is retained in `tab_TC5_positive_event_union_audit.csv`
for reproducibility and audit purposes, but is not a primary analytical distinction.

**Combined set:**
- **P = 147** unique (municipality, date) pairs
- **27 unique municipalities** across 5 coastal sectors (SC coast)
- **Period:** 1998–2020
- **Exact overlaps:** 0 (confirmed by audit)
- **Near-matches:** 1 (Florianópolis, ±3 days; not a duplicate)
- **B_target_effective:** 12 ep/yr/muni × 27 munis = 324 ep/yr

All 147 events are treated as equally reliable positive labels within the PU framework.

**Database provenance (for reproducibility):**

| Component | N | Period | Primary sources |
|-----------|---|--------|----------------|
| Documentary archive | 56 | 1998–2020 | Theses, news, technical reports |
| Civil Defense records (Leal et al.) | 91 | 1998–2023 | Civil Defense disaster records |
| **Combined (union)** | **147** | 1998–2020 | **both** |

See `tab_TC5_positive_event_union_audit.csv` for the full per-row provenance audit.

**Step 2d compatibility note:**
Step 2d uses 91 municipality×event rows (from the Civil Defense database) with the CSI
framework. Step 2e uses 147 events (combined set) with the PU framework. The comparison
table `tab_TC5_csi_vs_pu_comparison.csv` accounts for this difference when comparing
optimal pairs across steps.

---

## Mathematical Framework

### Event Sets and Notation

Let:
- $\mathcal{R} = \{r_j\}_{j=1}^{P}$ — set of reported coastal-impact events
- $P = |\mathcal{R}| = 147$ — combined positive-event set (expanded 56 + legacy 91, 0 exact overlaps, 27 municipalities)
- $\theta = (\tau_{Hs}, \tau_{SSH})$ — candidate threshold pair (local percentiles)
- $H(\theta)$ — number of reported events captured (hits)
- $M(\theta)$ — number of reported events not captured (misses)
- $U(\theta)$ — number of detected compound episodes left unmatched
- $Y$ — number of years in the validated period (1998–2020 = 23 years)

The directional matching window follows the convention established in Step 2d:

$$
\mathcal{W}(D_j) = \{D_j - 2, D_j - 1, D_j\} \cup \{D_j + 1\; 00\mathrm{Z}\}
$$

### Positive Recall

$$
R_{pos}(\theta) = \frac{H(\theta)}{P}
$$

The proportion of confirmed positive events captured by the threshold pair. This is the most
reliable metric because P is known with confidence.

### Annual Burden

The raw annual detection rate:

$$
B_{raw}(\theta) = \frac{H(\theta) + U(\theta)}{Y}
$$

Normalised burden (dimensionless):

$$
B(\theta) = \min\left(1, \frac{B_{raw}(\theta)}{B_{target}^{eff}}\right)
$$

Where the effective annual budget scales with the number of municipalities analysed:

$$
B_{target}^{eff} = B_{target}^{muni} \times N_{muni}
$$

- $B_{target}^{muni}$ — per-municipality annual tolerance (default: 12 episodes/year/municipality)
- $N_{muni}$ — number of unique municipalities with valid grid coverage in the analysis

**Rationale:** One compound coastal event per month per municipality (12/year) is
climatologically plausible for the SC coast. Scaling by $N_{muni}$ ensures the
domain-wide budget grows proportionally with spatial coverage, avoiding unfair
penalisation of analyses that include more municipalities. This term penalises
threshold pairs that generate an unrealistically large total detection rate.

### Confidence Weight (qᵢ)

Each unmatched episode $u_i \in U(\theta)$ receives a confidence weight:

$$
q_i = \text{clip}\left(\alpha_E E_i + \alpha_I I_i + \alpha_C C_i, 0, 1\right)
$$

Where:
- $E_i \in \{0, 1\}$ — external evidence indicator (binary)
- $I_i \in [0, 1]$ — physical intensity index (continuous)
- $C_i \in [0, 1]$ — context coherence index (continuous)

Default weights: $\alpha_E = 0.60$, $\alpha_I = 0.30$, $\alpha_C = 0.10$

#### External Evidence Component (Eᵢ) — Repository Adaptation

Binary flag indicating documentary corroboration:

$$
E_i = \begin{cases}
1 & \text{if documentary evidence supports the episode} \\
0 & \text{otherwise}
\end{cases}
$$

**Ideal definition:** $E_i = 1$ if at least one independent external source
(Civil Defense bulletin, municipal emergency report, independent news article)
confirms coastal impact at the episode's municipality within the causal window.
This ideally requires a broader, truly independent evidence layer.

**Repository adaptation (current implementation):** Because the repository has
limited documentary density, $E_i$ is computed from all event records available
under `data/reported events/`:

1. **Legacy Civil Defense database** (`reported_events_Karine_sc.csv`, 105 rows /
   91 unique disaster IDs): Any legacy event at the same municipality and overlapping
   temporal window sets $E_i = 1$. This is meaningful because many legacy events are
   NOT in the expanded positive set (e.g., events after 2020, North-sector events
   with lower documentary density in the expanded search).

2. **Optional manual override** (`data/audit/unmatched_episode_audit.csv`): A
   researcher-curated CSV can set $E_i$ explicitly for specific episodes.
   Manual overrides take priority over the rule-based approach.

**Note on independence:** This adaptation uses documentary sources that partially
overlap with those used to define P. In the ideal case, $E_i$ would rely on a
broader, fully independent evidence layer (national Civil Defense portal, broader
news archive, social media monitoring). The current approach is an operational
compromise documented here. The weight $\alpha_E = 0.60$ reflects confidence in
the evidence quality; analysts who judge the overlap problematic should reduce
$\alpha_E$ (see `config/PARAMETER_DECISIONS.md`).

#### Physical Intensity Component (Iᵢ)

Quantifies how far the episode exceeds thresholds in percentile space:

$$
I_i = \text{clip}\left[
\frac{1}{2}\left(
\frac{\phi_{Hs}(u_i) - p_{Hs}}{1 - p_{Hs}} +
\frac{\phi_{SSH}(u_i) - p_{SSH}}{1 - p_{SSH}}
\right), 0, 1
\right]
$$

Where:
- $\phi_{Hs}(u_i)$ — empirical percentile of the episode's Hₛ peak
- $\phi_{SSH}(u_i)$ — empirical percentile of the episode's SSH_total peak
- $p_{Hs}$, $p_{SSH}$ — threshold percentile levels

This index equals 0 when peaks are at the threshold and approaches 1 when peaks approach the
upper tail of both variables.

#### Context Coherence Component (Cᵢ)

Mean of three binary indicators:

$$
C_i = \frac{1}{3}\left(C_i^{season} + C_i^{multi} + C_i^{exposure}\right)
$$

Where:
- $C_i^{season} = 1$ if the episode occurs during the climatologically active season
  (April–October for SC storm-wave impacts)
- $C_i^{multi} = 1$ if at least one neighboring municipality or adjacent grid point also
  registers a temporally consistent compound episode within ±1 day
- $C_i^{exposure} = 1$ if the municipality is in the Northern sector of the Santa
  Catarina coast (Itapoá, São Francisco do Sul, Araquari, Balneário Barra do Sul,
  Barra Velha). **Rationale:** GLORYS12 and WAVERYS coverage is partially degraded
  in this region, so real events there are more likely to appear as unmatched
  detections. Assigning $C_i^{exposure} = 1$ increases plausibility of unmatched
  episodes in the north, compensating for systematic model under-detection.

### Soft Unmatched Penalty

$$
F_{soft}(\theta) = \sum_{i=1}^{U(\theta)} (1 - q_i)
$$

Interpretation:
- If $q_i = 0$ (no evidence of real event): full penalty contribution (1.0)
- If $q_i = 1$ (strong evidence of real event): no penalty contribution (0.0)
- If $0 < q_i < 1$: partial penalty contribution

### Composite Calibration Score

$$
\text{Score}(\theta) = w_1 R_{pos}(\theta) - w_2 B(\theta) - w_3 \frac{F_{soft}(\theta)}{P}
$$

Default weights: $w_1 = 0.60$, $w_2 = 0.20$, $w_3 = 0.20$

**Rationale:**
- $R_{pos}$ rewards recovery of confirmed observed events (primary objective)
- $B$ penalizes threshold pairs generating operationally excessive detections
- $F_{soft}/P$ penalizes unmatched detections proportionally to lack of evidence

The score is maximized over the threshold grid:

$$
\theta^* = \arg\max_{\theta \in \Theta} \text{Score}(\theta)
$$

### Optimal Pair Selection Hierarchy

If multiple threshold pairs yield similar scores:

1. **Higher $R_{pos}(\theta)$** — prioritize confirmed-positive capture
2. **Lower $B(\theta)$** — prefer operationally manageable detection rates
3. **Lower $F_{soft}(\theta)/P$** — prefer pairs with more plausible unmatched episodes
4. **Higher percentile sum** — prefer more restrictive pairs (parsimony)

---

## Implementation Steps

### Step 1: Independent Threshold Sweep

**Step 2e performs its own independent threshold sweep. It does NOT load or
re-use the Step 2d CSI metrics grid or false alarm list as analytical inputs.**

The same threshold grid (q50–q90 in 5% steps, 81 pairs) is swept from scratch
using the combined harmonized positive-event set (147 events, 27 municipalities) as
the positive set P. The Step 2d outputs are used only for the final comparison table
(tab_TC5_csi_vs_pu_comparison.csv).

**Step 2e sweep:**
1. Load unified metocean dataset; clip to validated period [1998–2020 ± window]
2. Build EventRecord objects from the 147 combined positive events
3. Compute SSH_total = zos + FES2022 tide per grid point
4. Layer 1 (hits/misses): evaluate each event against each threshold pair
5. Layer 2 (unmatched): collect episode details including peak Hₛ and SSH_total

### Step 2: Compute Physical Intensity (Iᵢ)

For each unmatched episode:
1. Extract peak Hₛ and SSH_total values
2. Compute empirical percentiles at the corresponding grid point
3. Calculate Iᵢ using the formula above

### Step 3: Compute Context Coherence (Cᵢ)

For each unmatched episode:
1. Check if date falls in active season months
2. Check for temporally consistent detections at neighboring grid points
3. Check if municipality is in the high-exposure list
4. Average the three binary indicators

### Step 4: Load External Evidence (Eᵢ)

Load the audit database (`data/audit/unmatched_episode_audit.csv`):
- Join on episode_id or (municipality_code, date_start)
- Default Eᵢ = 0 for non-audited episodes

### Step 5: Compute Confidence Weights

For each unmatched episode:
$$
q_i = \text{clip}(\alpha_E E_i + \alpha_I I_i + \alpha_C C_i, 0, 1)
$$

### Step 6: Compute Score Components

For each threshold pair θ:
1. $R_{pos}(\theta) = H(\theta) / P$
2. $B(\theta) = \min(1, (H(\theta) + U(\theta)) / (Y \cdot B_{target}))$
3. $F_{soft}(\theta) = \sum_i (1 - q_i)$ over unmatched episodes for this θ

### Step 7: Compute Composite Score

$$
\text{Score}(\theta) = w_1 R_{pos}(\theta) - w_2 B(\theta) - w_3 F_{soft}(\theta) / P
$$

### Step 8: Select Optimal Pair

Rank all threshold pairs by Score (descending), apply tiebreakers, select θ*.

---

## Sensitivity Analysis

### Required Experiments

Per methodology document (Section 2.X.9):

1. **Alternative weight triplets** for (w₁, w₂, w₃):
   - (0.70, 0.15, 0.15) — high recall priority
   - (0.50, 0.25, 0.25) — balanced
   - (0.60, 0.20, 0.20) — default

2. **Alternative confidence weights** for (α_E, α_I, α_C):
   - (0.70, 0.20, 0.10) — evidence-heavy
   - (0.50, 0.40, 0.10) — intensity-moderate
   - (0.60, 0.30, 0.10) — default

3. **Alternative B_target values**: 5, 10, 15, 20 episodes/year

4. **Comparison with classical CSI**: Side-by-side optimal pair comparison

### Robustness Analysis

1. **Event bootstrap**: Resample R with replacement, recompute Score(θ) for each pair.
   Quantifies sensitivity to the finite set of reported positives.

2. **Leave-one-year-out**: Recompute optimization excluding one year at a time. Tests
   whether the optimal pair depends on a particular storm season.

3. **Leave-one-sector-out**: Repeat excluding one coastal sector at a time. Tests
   spatial robustness and identifies regional bias.

---

## Interpretation and Limitations

### Expected Advantages

1. **Explicitly recognizes database incompleteness** — consistent with disaster-database
   literature (Wyatt et al., 2023; Delforge et al., 2025)

2. **Preserves most reliable information** — confirmed positives anchor the calibration

3. **Avoids excessive annual detections** — B term provides operational constraint

4. **Transparent audit pathway** — evidence can be added incrementally as database improves

### Known Limitations

1. **Heuristic confidence weight** — qᵢ is not a calibrated probability; it is a bounded
   plausibility score. Sensitivity analysis is mandatory.

2. **Audit burden** — full Eᵢ assessment for 1,298 episodes is impractical. Rolling top-K
   prioritization by Iᵢ is recommended.

3. **Temporal asynchronism** — SSH_total combines midnight SSH with daily-max tide (inherited
   from Step 2c/2d).

4. **Single-domain calibration** — parameters are tuned for SC coast; generalization requires
   re-calibration.

---

## References

Bekker, J., and Davis, J. (2020). Learning from positive and unlabeled data: a survey.
*Machine Learning*, 109, 719-760. https://doi.org/10.1007/s10994-020-05877-5

Delforge, D., Wathelet, V., Below, R., et al. (2025). EM-DAT: the Emergency Events Database.
*International Journal of Disaster Risk Reduction*, 124, 105509.
https://doi.org/10.1016/j.ijdrr.2025.105509

Donges, J. F., Schleussner, C.-F., Siegmund, J. F., and Donner, R. V. (2016). Event
coincidence analysis for quantifying statistical interrelationships between event time series.
*European Physical Journal Special Topics*, 225, 471-487.
https://doi.org/10.1140/epjst/e2015-50233-y

Green, J., Haigh, I. D., Quinn, N., et al. (2025). Review article: A comprehensive review of
compound flooding literature with a focus on coastal and estuarine regions. *Natural Hazards
and Earth System Sciences*, 25, 747-816. https://doi.org/10.5194/nhess-25-747-2025

Marcos, M., Rohmer, J., Vousdoukas, M. I., et al. (2019). Increased extreme coastal water
levels due to the combined action of storm surges and wind waves. *Geophysical Research
Letters*, 46, 4356-4364. https://doi.org/10.1029/2019GL082599

Wyatt, F. R., Lusk, B., Robbins, J. C., et al. (2023). Investigating bias in impact
observation sources and implications for impact-based forecast evaluation. *International
Journal of Disaster Risk Reduction*, 90, 103639.
https://doi.org/10.1016/j.ijdrr.2023.103639
