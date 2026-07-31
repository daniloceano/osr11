# SCIENTIFIC_NOTES — Step 2e: Threshold Calibration (PU Composite Score)

**Part of:** Step 2 — Threshold Calibration (umbrella step)

**Module**: `src/02_threshold_calibration/05_pu_composite_calibration/`
**Project**: OSR11 — Compound Coastal Flooding Hazard Assessment, Santa Catarina coast
**Authors**: Danilo Couto de Souza, Carolina Barnez Gramcianinov, Ricardo de Camargo, Karine Bastos Leal

---


> ### ⚠ Recalibração de 2026-07-30
>
> Estas notas descrevem o arcabouço PU, que permanece válido. **Cinco elementos
> mudaram nessa data** e estão registrados na seção "Recalibração de 2026-07-30"
> ao final deste documento, no `config/PARAMETER_DECISIONS.md` e na §14 de
> AUD-01: o **detector pontuado**, a **grade de varredura**, o **termo de
> carga**, os **pesos do score** e os **alphas de confiança**. O par selecionado
> passou de **q90/q90 para q70/q99**. Onde o texto abaixo diz `SSH_total`, leia
> `zos` livre de maré com portão em HAT.

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

---

## 2026-07-30 — Recalibração sobre o detector de produção

### O que mudou, e por quê

Até esta data o Step 2e pontuava pares de limiar contra
`SSH_total = zos + maré`. O método de produção abandonou essa variável em
2026-07-29, quando a maré passou de forçante a variável condicionante, e sob o
portão HAT adotado em 2026-07-30 não a lê de forma alguma. **Calibrar sobre uma
variável que o detector não lê é inconsistência científica**, e estava
registrada como incerteza remanescente no fechamento de AUD-01 de 2026-07-29.

O detector pontuado passa a ser exatamente o de produção:

$$
\text{onda: } H_s(d) \ge q_{hs}^{\,\text{local}}
\qquad
\text{nível: } \eta(d) \ge q_{zos}^{\,\text{local}}
$$

$$
\text{portão: } \max_{d \in \mathcal{O}} \mathrm{SWL}(d) > \mathrm{HAT}
\qquad
\mathrm{SWL}(d) = \bigl(\eta(d) - \overline{\eta}\bigr) + \tau_{\max}(d)
$$

com $\eta$ = `zos` do GLORYS12 (livre de maré), $\tau_{\max}$ = máximo diário
da maré FES2022, $\overline{\eta}$ = média local de `zos` sobre 1993–2025,
$\mathcal{O}$ = dias de sobreposição do evento, e

$$
\mathrm{HAT} = \max_{1993 \le t \le 2025} \tau_{\max}(t)
$$

por ponto de grade. A de-mediação de $\eta$ é necessária porque `zos` é
referenciado ao geoide e HAT ao nível médio local.

**Um detector, duas camadas.** As Layers 1 e 2 passam a chamar a mesma função de
detecção, de modo que um acerto e um episódio não casado são o mesmo objeto
visto dos dois lados da relação de casamento. Sem portão as duas formulações
coincidem — um episódio intersecta a janela causal exatamente quando um de seus
dias compostos o faz —, portanto é generalização estrita, não troca de critério.

**Pressupostos preservados.** Percentis, média local de `zos` e HAT vêm do
registro **completo** 1993–2025; a varredura de acerto/erro continua restrita ao
período validado pelas bases de eventos (1998–2020). Janela causal
$[D-2, D-1, D, D+1]$ inalterada.

### Grade estendida

A grade passou de 9 níveis (q50–q90, passo 0,05; 81 pares) para **11 níveis
explícitos** — q50 a q90 em passo 0,05, mais **q95 e q99** — totalizando **121
pares**. AUD-02 §4 registrava que o ótimo estava na **borda** da grade, "um
sinal de que o ótimo pode estar fora dela". Estender testou isso diretamente.

### Achado: o score composto não tinha ótimo interior

Sob o detector correto e a grade estendida,

$$
\rho_{\text{Spearman}}\bigl(\text{Score},\; n_{\text{episódios aceitos}}\bigr) = -0{,}999
$$

O score era uma **preferência monótona por detectar menos**. Seu ótimo era
q99/q99, com 40 episódios aceitos em Santa Catarina contra 147 eventos
positivos e recall 0,034 — *menor* que o do q90/q90 (0,190). O termo dominante
era $-w_3 F_{\text{soft}}/P$, que atingia $-29{,}4$ contra um máximo de $+0{,}60$
do termo de recall. O q90/q90 só parecia ótimo porque a grade parava nele.

### Três correções de critério, autorizadas explicitamente

**(1) Carga bilateral.** O termo de carga era um teto unilateral,

$$
B_{\text{antigo}}(\theta) = \min\!\left(1,\ \frac{H+U}{Y \cdot B_{\text{alvo}} \cdot N_{\text{mun}}}\right)
$$

minimizado em **zero** detecções, logo empurrando na mesma direção da penalidade
branda. Aumentar $w_2$ fortalecia a atração para o vazio: varrer $w_2$ de 0,20 a
0,69 **não movia o ótimo**. A forma nova é um desvio simétrico de uma taxa
esperada:

$$
r(\theta) = \frac{H(\theta) + U(\theta)}{Y \cdot N_{\text{mun}}}
\qquad
B(\theta) = \min\!\left(1,\ \left|\log_{10} \frac{r(\theta)}{r^{*}}\right|\right)
$$

Detectar metade da taxa esperada custa o mesmo que detectar o dobro, e o teto em
1 mantém o termo em $[0,1]$ como os outros dois, tornando $w_1+w_2+w_3=1$
interpretável.

**(2) Pesos** $0{,}60/0{,}20/0{,}20 \rightarrow 0{,}30/0{,}60/0{,}10$, para que o
único termo ancorado em observação carregue a decisão.

**(3) Alphas** $0{,}60/0{,}30/0{,}10 \rightarrow 0{,}20/0{,}50/0{,}30$. Medido
sobre a varredura: $E_i = 1$ em **154 de 436 352** episódios (**0,04 %**). Com
$\alpha_E = 0{,}60$, o peso de confiança ficava limitado a
$q_i \le 0{,}40$ **por construção** em 99,96 % dos casos. Isso não media
implausibilidade: media a escassez do registro documental, e contradizia a
premissa do próprio arcabouço PU. O peso migrou para os dois termos que não
dependem do registro. $\overline{q_i}$ sobe de 0,276 para 0,543.

### Ancoragem da taxa esperada

Leal et al. (2024) registram 72 desastres costeiros declarados distintos em
Santa Catarina entre 1998 e 2023, isto é **2,77 eventos/ano** para a costa
inteira. Com a base documentária expandida, o conjunto positivo tem 147 pares
(município, data) em 22,4 anos e 27 municípios:

$$
r_{\text{reportada}} = \frac{147}{22{,}4 \times 27} = 0{,}243 \ \text{detecções município}^{-1}\,\text{ano}^{-1}
$$

**Isto é piso, não expectativa.** A subnotificação é a premissa do arcabouço PU,
e AUD-18 registra que não existe base independente para medi-la. O alvo adotado,
$r^{*} = 2{,}0$, **assume subnotificação de ~8×** — uma hipótese declarada, com
sensibilidade de 0,5 a 6,0 anexa.

**[INCERTO]** O fator de subnotificação não é medido em lugar nenhum deste
trabalho. A seleção é estável em q70/q99 para $r^{*} \ge 2{,}0$; em
$r^{*} = 1{,}0$ move para q85/q99 e em $r^{*} = 0{,}5$ para q95/q99.

### Par selecionado e sua comparação

**q70/q99.** Contra o q90/q90 superado, **sob o mesmo detector**: recall idêntico
($H = 28$ de 147), $B$ 0,148 contra 0,268, $F_{\text{soft}}$ 420,4 contra
1 142,0, Score $-0{,}318$ contra $-0{,}881$, episódios aceitos 484 contra 1 224,
taxa 1,42 contra 3,71 detecções/município/ano para um alvo de 2,0.

**O par novo não vence por detectar menos eventos reportados — vence por
detectar 62 % menos ruído com o mesmo recall.**

### Robustez e o eixo mal determinado

$q_{zos} = q99$ é selecionado em **14 de 14** variantes de sensibilidade. O
percentil de **onda** é o eixo mal determinado: q70 em 8 variantes, q50 em 2,
q85 em 2, q95 em 1, q99 em 1; os seis melhores pares diferem em menos de 1 % no
score e cobrem de q50 a q80.

**Consequência para AUD-02:** o score composto **não tem informação** para
escolher o limiar de onda, e o valor que devolve (q70) *rebaixa* o piso de
`thr_hs` — mínimo de 0,20 m para 0,14 m nos 808 pontos, e de 129 para 256 pontos
abaixo de 1,5 m. Se um piso físico absoluto for adotado, terá de vir de fora
desta calibração.

### Caveats

1. **[PRELIMINAR]** O alvo de taxa é hipótese, não medida; ver acima.
2. A mudança de critério de pontuação foi autorizada caso a caso e está
   registrada em AUD-01 §14 e em `config/PARAMETER_DECISIONS.md`. Não é uma
   escolha derivada dos dados.
3. A calibração continua feita **exclusivamente com eventos de Santa Catarina**
   e aplicada a 27° de latitude (AUD-18, não resolvida).
4. As colunas `thr_ssh_pct` e `ssh_peak` mantêm os nomes antigos por
   compatibilidade, mas carregam o percentil e o pico de `zos`.


---

## Recalibração de 2026-07-30

### Por que a calibração foi refeita

O Step 2e construía `SSH_total = zos + maré` por ponto e pontuava pares de
limiar contra a base de eventos reportados de SC. O método de produção deixou de
ler `SSH_total` em 2026-07-29, quando a maré passou de forçante a variável
condicionante, e sob o portão HAT adotado em 2026-07-30 não a lê de forma alguma.
Calibrar sobre uma variável que o detector não lê é inconsistência científica, e
isso já constava como incerteza remanescente no fechamento de AUD-01 de
2026-07-29.

### Detector pontuado (novo)

$$
\begin{aligned}
\text{onda:}\quad & H_s(d) \ge q_{h_s}\ \text{local} \\
\text{nível:}\quad & \mathrm{zos}(d) \ge q_{\mathrm{zos}}\ \text{local}
   \quad\text{(livre de maré)} \\
\text{portão:}\quad & \max_{d \in \Omega} \mathrm{SWL}(d) > \mathrm{HAT}
\end{aligned}
$$

com $\Omega$ o conjunto de dias de sobreposição do episódio,

$$
\mathrm{SWL}(d) = \big[\mathrm{zos}(d) - \overline{\mathrm{zos}}\big]
                  + \mathrm{maré}_{\max}(d),
\qquad
\mathrm{HAT} = \max_{1993\text{--}2025} \mathrm{maré}_{\max}(d).
$$

A de-mediação de `zos` é necessária porque o GLORYS12 referencia `zos` ao
geoide, enquanto o HAT é altura acima do nível médio local. Sob o método antigo
o offset cancelava contra o próprio percentil; aqui não cancela, porque o datum
é externo.

**Pressuposto declarado.** `zos` (GLORYS12, sem forçante de maré) e FES2022 são
modelos independentes, e sua soma linear ignora a interação não linear
maré–sobrelevação, isto é, a supressão de sobrelevação em preamar em águas
rasas. Isso é potencialmente relevante justamente na plataforma amazônica.

### Grade de limiares

Onze níveis explícitos, `[0,50 … 0,90, 0,95, 0,99]`, 121 pares. A extensão
testa diretamente o sinal registrado em AUD-02 §4: o ótimo anterior estava na
borda q90 da grade de nove níveis. A resposta foi afirmativa, mas **no eixo do
nível**: `q_zos = q99` é selecionado em 14 de 14 variantes de sensibilidade.

### O achado que motivou a mudança de critério

Sob o detector correto e a grade estendida,

$$
\rho_{\text{Spearman}}\big(\text{Score},\ n_{\text{episódios aceitos}}\big) = -0{,}999 .
$$

O score composto **não tem ótimo interior**: é uma preferência monótona por
detectar menos. Seu ótimo era q99/q99, com 40 episódios aceitos em SC contra 147
positivos e recall 0,034 — *menor* que o de q90/q90. A causa é que
$w_3 \cdot F_{\text{soft}}/P$ não era limitado: chegava a 29,4, contra um máximo
de 0,60 do termo de recall. O q90/q90 só parecia ótimo porque a grade parava
nele.

Segundo achado: $E_i = 1$ em 154 de 436 352 episódios (0,04 %), de modo que
$\alpha_E = 0{,}60$ limitava $q_i$ a 0,40 **por construção** em 99,96 % dos casos.
O termo media a escassez do registro documental, não a implausibilidade da
detecção — o que contradiz a premissa do próprio arcabouço PU.

### Critério revisado

$$
\mathrm{Score}(\theta) = w_1 R_{\text{pos}}(\theta)
                          - w_2 B(\theta)
                          - w_3 \frac{F_{\text{soft}}(\theta)}{P},
$$

com $w = (0{,}30;\ 0{,}60;\ 0{,}10)$ e o termo de carga agora **bilateral**:

$$
r(\theta) = \frac{H(\theta) + U(\theta)}{Y \cdot n_{\text{mun}}},
\qquad
B(\theta) = \min\!\left(1,\ \left|\log_{10}\frac{r(\theta)}{r^{*}}\right|\right).
$$

O teto unilateral anterior, $\min(1, r/r^*)$, era minimizado em **zero**
detecções, logo empurrava na mesma direção da penalidade branda. Foi verificado
numericamente que aumentar $w_2$ sozinho não move o ótimo: varrendo de 0,20 a
0,69, ele permanece em q99/q99. O logaritmo torna a penalidade simétrica em
termos relativos — metade da taxa esperada custa o mesmo que o dobro — e o teto
mantém os três termos em $[0,1]$, tornando $w_1+w_2+w_3=1$ interpretável.

Alphas: $(\alpha_E, \alpha_I, \alpha_C) = (0{,}20;\ 0{,}50;\ 0{,}30)$. O peso
migra da evidência externa para os dois termos que não dependem do registro.
$\overline{q_i}$ sobe de 0,276 para 0,543.

### Ancoragem de $r^{*}$ e sua incerteza

Leal et al. (2024) registram 72 desastres costeiros declarados distintos em SC
entre 1998 e 2023, isto é 2,77 eventos/ano para a costa inteira. Com a base
documentária expandida, o conjunto positivo dá

$$
r_{\text{reportado}} = \frac{147}{22{,}4 \times 27}
                      = 0{,}243\ \text{detecções município}^{-1}\text{ano}^{-1}.
$$

**Isto é piso, não expectativa.** A subnotificação é a premissa do arcabouço PU
e AUD-18 registra que não existe base independente para medi-la. O valor adotado,
$r^{*} = 2{,}0$, **assume subnotificação de ≈ 8×**. É hipótese declarada, com
sensibilidade de 0,5 a 6,0 anexa: a seleção é estável em q70/q99 para
$r^{*} \ge 2{,}0$, move para q85/q99 em 1,0 e q95/q99 em 0,5.

### Resultado

Par selecionado **q70/q99**. Contra q90/q90 sob o **mesmo** detector: recall
idêntico ($H = 28$ de 147), $U$ de 2 214 para 831, $B$ de 0,268 para 0,148,
Score de −0,881 para −0,318. O par novo não vence por detectar menos eventos
reportados — vence por produzir 62 % menos ruído com o mesmo recall.

### Ressalvas

1. **AUD-02 piora.** q70 rebaixa o piso de `thr_hs` nos 808 pontos: mínimo
   0,20 → 0,14 m, pontos abaixo de 1,5 m de 129 → 256. A questão bloqueia
   publicação e ficou mais distante de ser resolvida.
2. **O percentil de onda é o eixo mal determinado.** Os seis melhores pares
   diferem em menos de 1 % no score e cobrem de q50 a q80. O score não tem
   informação para escolher o limiar de onda; se um piso físico for adotado,
   terá de vir de fora desta calibração.
3. $r^{*}$ é hipótese, não medida (ver acima).
4. A calibração continua feita **apenas com eventos de Santa Catarina** e
   aplicada a toda a costa — AUD-18 permanece aberta e intocada.
