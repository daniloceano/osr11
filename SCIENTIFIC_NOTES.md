# SCIENTIFIC_NOTES — OSR11: compound coastal risk on the Brazilian coast

**Scope.** The scientific record of the project: questions, framing, equations,
data, decisions and their justification, results and their interpretation, and
the limits of what may be concluded. Software structure, execution order and
environment belong to [`README.md`](README.md) and to the module documentation.

**Status.** The method has been stable since 2026-07-31. The independent
scientific review of 2026-07-29 opened eighteen issues; all are resolved, and the
seven that closed as declared limitations are reproduced in
§ *Caveats and Limitations*. Full record:
[`docs/scientific_audit/ISSUE_TRACKER.md`](docs/scientific_audit/ISSUE_TRACKER.md).

---

## Research Questions

1. **Where, along the Brazilian coast, do sea-level extremes and elevated
   significant wave height co-occur often enough to matter?** Compound occurrence
   is the object; neither variable alone is.
2. **Does that co-occurrence carry a coherent regional structure**, or is it an
   artefact of how the detection threshold interacts with local variance?
3. **What is the joint distribution of exposed population and social
   susceptibility over that hazard field**, at the finest unit for which all
   three layers exist?
4. **Does an index built from the three layers recover the coastal impacts
   already documented in Brazil** — and where it does not, can each divergence be
   attributed to an identified mechanism rather than to noise?
5. **What is not measurable with the data held here**, and how far do the
   conclusions extend beyond the sector where the detector was calibrated?

Question 5 is not rhetorical. It became the organising question of the audit, and
most of the limitations below are answers to it.

---

## Physical / Statistical Framework

### The compound event

Coastal flooding at the shoreline is driven by the still water level and by the
wave field acting together. Neither is sufficient: a high tide without waves
produces limited overtopping, and large waves at low water dissipate offshore.
The detector therefore requires three conditions on the same day at the same grid
point:

1. **wave criterion** — significant wave height above its local percentile
   threshold, `Hs > thr_hs`;
2. **level criterion** — tide-free sea-surface height above its local percentile
   threshold, `zos > thr_zos`;
3. **acceptance gate** — the still water level over the shared days must exceed
   the local highest astronomical tide, `max(SWL) > HAT`.

The third condition is what makes the event physically meaningful rather than
merely statistically rare, and it is the change that resolved the dominant
pathology of the first implementation (§ *Methodology*, AUD-01).

### Why the level variable is tide-free

An earlier implementation segmented episodes on `SSH_total = zos + tide_daily_max`,
that is, on a variable containing the astronomical tide. Taking a local
percentile of that variable selects, in macrotidal sectors, the days of spring
tide — a deterministic astronomical cycle, not a meteorological event. The
diagnostic is unambiguous: the phase of detected events against the
spring–neap cycle gave a Rayleigh statistic of R = 0.82 (p < 0.01) in the
Maranhão sector, against R = 0.085 in Rio Grande do Sul.

Segmentation therefore runs on **tide-free `zos`**, and the tide re-enters as a
**conditioning variable** through the HAT gate rather than as a forcing term.

### The risk index

Risk is the conjunctive combination of hazard, exposure and vulnerability, as the
IPCC framework implies — the absence of any one of them removes the potential for
adverse consequence. The geometric mean has that property; an arithmetic mean
does not, and would let a large population compensate for the absence of a
physical driver.

```
Hazard_Frequency = min(compound_count_total / 99, 1)
Hazard_Severity  = min(fillna(mean_integrated_severity, 0) / 1, 1)
Hazard_Index     = (Hazard_Frequency + Hazard_Severity) / 2

pop_eff           = 0.4·pop_1km + 0.3·pop_2km + 0.2·pop_5km + 0.1·pop_10km
Exposure_absolute = clip[(log10(pop_eff) − 2) / (6 − 2), 0, 1]
Exposure_relative = pop_eff / pop_municipality
Exposure_Index    = sqrt(Exposure_absolute · Exposure_relative)

V           = Φ(PC1 / sd(PC1))
Risk_Hazard = (Hazard_Index · Exposure_Index · V)^(1/3)
```

Every anchor is **fixed**, not taken from the sample: 99 events over 33 years is
three events per year; the severity goalpost of 1.0 is one day at full criterion
in the domain's maximum daily excess; the exposure goalposts are 10² and 10⁶
inhabitants. There is no floor and no final Min–Max. The consequence is that a
municipality's value does not depend on which other municipalities are present —
with one measured exception recorded under *Assumptions*.

---

## Datasets and Variables

| Dataset | Version / product | Variables used | Resolution | Period |
|---|---|---|---|---|
| CMEMS **GLORYS12** | global reanalysis | `zos` (sea surface height) | 1/12°, daily | 1993–2025 |
| CMEMS **WAVERYS** | global wave reanalysis | `VHM0` (significant wave height) | ~0.2°, daily | 1993–2025 |
| **FES2022** | tidal atlas | daily maximum astronomical tide, HAT | clipped to Brazil | 1993–2025 |
| **ERA5** | ECMWF/C3S reanalysis | atmospheric forcing, synoptic context | 0.25° | 1993–2025 |
| **IBGE Grade Estatística 2022** | statistical population grid | resident population | 200 m urban / 1 km rural | 2022-07-31 |
| **IBGE/SIDRA 2022 Census** | ten socioeconomic indicators | see below | municipal | 2022 |
| **SC reported events** | Leal et al. (2024) + expanded documentary base | 147 municipality×date pairs | municipal | 1998–2020 |

**Domain.** 808 coastal grid points from 35°S to 7°N; 282 coastal municipalities,
280 of which carry a risk value.

**SVI indicators (ten).** `pop_poverty`, `pop_illiterate`, `pop_house`,
`pop_nogarbage`, `pop_nonwhite`, `pop_nosewage`, `pop_nowater`, `pop_nopaving`,
`pop_agevul`, `pop_rent`. Provenance and reproduction audit:
`src/04_risk_integration/external_svi/README.md`.

---

## Methodology

### Threshold calibration (Step 2)

Thresholds are selected by a **positive-unlabeled** composite score rather than by
classical verification. The reason is structural: the reported-event databases
under-report, so a detection with no matching record may be a real event that was
never recorded — the "negatives" are unlabelled, not negative. Classical metrics
are therefore not interpretable here, which the CSI diagnostic of Step 2d
demonstrates with FAR = 0.984.

The selected pair is **q70 for Hs and q99 for tide-free `zos`**, with
`R_pos` = 0.19 against the 147 reported pairs.

An important negative result: **the score does not determine the wave axis**. Its
six best-scoring pairs lie within 1 % of one another and span q50–q80, while the
level percentile q99 is selected in all fourteen sensitivity variants. The wave
threshold is therefore weakly identified by the calibration, which is why no
absolute floor could be derived from it (AUD-02).

### Hazard characterisation (Step 3)

Episodes are segmented by peaks-over-threshold on each variable, intersected on
shared days, and each candidate is passed through the HAT gate. Of the candidate
events, **15 857 were rejected by the gate and 16 768 accepted**; **208 of the
808 points accepted no event at all** over 33 years.

The hazard carries **two** components, frequency and integrated severity. Duration
was removed: it was dominated by the minimum of the domain rather than by physical
signal, and it depressed exactly the sector with the best-documented impacts
(AUD-06). The two surviving components **reinforce** each other (ρ = +0.60),
against ρ = −0.55 for the superseded three-component version.

### Integration (Step 4)

Exposure is a distance-weighted mean of the cumulative 1, 2, 5 and 10 km bands.
Because the bands are nested, the weights produce an automatic distance decay with
legible per-ring weights of 1.0, 0.6, 0.3 and 0.1. A useful identity: weighting the
numerator already weights the ratio, so a single weight set serves both the
absolute and the relative term.

Vulnerability enters as Φ(PC1/sd(PC1)). PC1 has no natural scale — mean 0,
sd 2.247, range −5.06 to +5.75, 48 % negative — and cannot enter a geometric mean
raw. The normal CDF is bounded in (0,1), produces no exact anchor, and is monotone,
so the ordering of the delivered SVI is preserved exactly (ρ = 1.0000).

---

## Assumptions

1. **Threshold transfer.** A local percentile is portable across regimes even
   though its absolute value and physical meaning are not. This is why percentiles
   were chosen; it is also why the detected quantity is a **local exceedance**
   rather than an absolute extreme. *Not testable outside Santa Catarina with the
   data held here.*
2. **HAT as the damage threshold.** The gate assumes coastal flooding begins when
   the still water level exceeds the highest astronomical tide. Where the urban
   fabric sits below that level — Recife is the documented case — damage begins
   **below** the gate, and the detector will not see it.
3. **Daily phase coherence.** GLORYS12 supplies one `zos` sample per day at
   00:00 UTC while the tidal term is that day's maximum, so the still water level
   is not realised at any real instant. Measured effect: median 1.2 cm/day, but
   5–10 cm in the micro-tidal south, where it matters most (AUD-03).
4. **The point-to-municipality association is expert judgement.** It was produced
   externally by visual inspection in GIS, arbitrating proximity against event
   activity, and is versioned as an input rather than re-derived here (AUD-04).
5. **Fixed anchors remove sample dependence — with one exception.** Hazard and
   exposure use fixed goalposts and are independent of set membership. `sd(PC1)`
   in the vulnerability term is **estimated from the sample**: removing one
   municipality moves any other by at most 0.0036, but excluding the whole
   North/Northeast changes `sd(PC1)` by −57 % and reorders the remainder at
   ρ = 0.70. **Published values are conditional on the 282-municipality domain**,
   and any subset analysis must recompute the scale rather than slice these values.
6. **Exposure is proximity, not modelled inundation.** It counts residents *near*
   the coast, never residents *affected*.

---

## Results and Interpretation

### The hazard field is regionally coherent

After the HAT gate, hazard correlates with |latitude| at ρ = +0.58 and decays
monotonically northward. The mechanism is transparent and worth stating because it
also generates the main limitation: mean HAT rises from **0.49 m** at 35–28°S to
**2.61 m** at 2°S–7°N, while the meteorological forcing weakens in the same
direction. The bar to clear grows fivefold exactly where the driver weakens.

### The index is hazard-led, and vulnerability is suppressed

On the 196 municipalities with positive risk, hazard accounts for **84.7 %** of
the variance of log risk, exposure 35.0 %, vulnerability **−19.7 %** — a negative
share meaning that vulnerability *compresses* rather than expands the dispersion.
Removing hazard from the formula leaves ρ = +0.092 against the published ranking:
**the integrated index is operationally the hazard index**, modulated.

This produces a result that must not be misread. The **marginal** rank correlation
between vulnerability and risk is **−0.372**, which does not mean that
vulnerability reduces risk: the **partial** correlation, controlling hazard and
exposure, is **+0.790**. This is suppression, caused by a strong
hazard–vulnerability anticorrelation (ρ = −0.601) that compresses the variance of
log risk by a factor of three.

**Interpretation.** Compound wave–surge hazard in Brazil concentrates in the
South/Southeast, where social deprivation is lowest, because the forcing is
extratropical. That is a genuine and welcome finding. Part of the *magnitude* of
the anticorrelation is nevertheless produced by the geography of the gate itself,
and no fixed-amplitude-gate counterfactual has been run to separate the two.

### There are no discrete hotspots

Silverman's critical-bandwidth test rejects unimodality over all 280
municipalities (*p* = 0.002) but **does not reject it** over the 196 with positive
risk (*p* = 0.556). The bimodality is the point mass at zero, not a cluster of
high-risk municipalities. Fisher–Jenks agrees: goodness of variance fit rises
smoothly from 0.678 to 0.974 with **no elbow at any class count**.

The coastal risk of Brazil varies **continuously**. The only genuine break is the
84 municipalities at exactly zero, and that is a statement about the record — no
accepted compound event in 1993–2025 — not the lowest class of a gradient.
"Hotspot" is therefore used only in an interval sense: a municipality whose 90 %
rank interval stays inside the first N positions. Seven qualify at N = 10 and
fourteen at N = 20.

### The ranking is firm at the top and not interpretable in the middle

Bootstrapping the 33 years of record, the median width of the 90 % rank interval
is **4.5 positions** in the top 10 and **45** in the band 101–196. Ranks 1–3 are
degenerate; eight municipalities have intervals covering rank 10, so "top-10" is a
presentation cut, not a statistical class.

Aggregation and weighting are robust — ρ ≥ 0.94 across the whole
frequency–severity weight sweep — and what instability remains lives in the
**functional form**: an arithmetic mean gives ρ = 0.550, percentile-rank
components ρ = 0.638.

**A property that must be declared**: 94 of the 196 municipalities with positive
risk rest on fewer than ten accepted events, and 90 on fewer than five. The
highest-ranked of them is 21st nationally, on a **single event in 33 years**. The
severity term is a conditional mean and does not scale with rarity, so a rare
moderate day scores much like a frequent one.

### Validation against reference cases

Thirty-two municipalities with independent evidence were fixed as a reference
list *before* the comparison was run. **The index recovers the case that the
review identified as disqualifying**: Balneário Camboriú, Itajaí and Navegantes,
placed at ranks 280, 275 and 273 of 280 in the first implementation, now sit at
**rank 81 of 280 on hazard**. **No municipality with documented disruption, severe
erosion or recurrent coastal flooding remains in the bottom decile.**

Thirteen of fourteen positive controls meet their hazard expectation. The negative
controls also behave: Macapá, Turiaçu, Chaves and Icatu fall to hazard ranks 188,
167, 138 and 121 — the middle of the distribution.

One divergence survives, and it is at the top: **Magé 3rd and Paraty 5th**, both
inside sheltered bays, drawing hazard from open-shelf points 35 and 15 km away.
See *Caveats*.

---

## Caveats and Limitations

The twelve declared limitations are written out in full, with numbers and
reproducing scripts, in [`README.md`](README.md) → *Declared limitations for the
manuscript*. In brief:

1. **The wave criterion measures local rarity, not absolute severity.** Its
   absolute value spans 0.14–2.40 m; median 0.90 m in Maranhão against 1.71 m in
   Rio Grande do Sul. **161 of 280** municipalities draw hazard from points below
   1.5 m, including the first-ranked. No floor is derivable here: the calibration
   does not determine the wave axis, and an external anchor would need a
   setup/runup formulation and beach-face slope, which this project does not hold.
2. **Calibrated in one state, applied to 27° of latitude.** Every positive event
   is from Santa Catarina. A documented reconnaissance for a comparable reference
   in the North/Northeast returned a **qualified negative**: recalibration is
   impossible, but two partial routes exist and were not used — a qualitative check
   against Muehe (2018) and a tide-gauge comparison against GLOSS-Brasil/RMPG.
3. **Vulnerability is social only.** No physical susceptibility layer:
   construction typology, terrain elevation, beach slope, dunes, reefs, hard
   defences and drainage are all absent.
4. **The vulnerability index is a deprivation axis**, r = +0.940 with poverty. Two
   indicators carry negative PC1 loadings; the audit confirmed these are empirical
   results and **not** coding errors. No comparison against the reference
   SVI-Coast of Lima et al. (2024) was performed.
5. **Exposure is de jure and instantaneous**; the seasonal population of the
   resort municipalities is invisible, and the bias understates exposure in exactly
   the sector carrying the highest hazard.
6. **The municipal unit distorts exposure through the denominator.** Dropping the
   relative term would move Itaboraí from 118th to 9th and Campos dos Goytacazes
   from 159th to 72nd — but also Rio de Janeiro by 49 positions, which is the
   opposite distortion. The ranking of large, partly inland municipalities is a
   **lower bound**.
7. **Two entries in the top five carry imported hazard.** Magé and Paraty sit
   inside sheltered bays and draw hazard from open-shelf points 35 and 15 km away;
   the flooding documented at both is fluvial and pluvial rather than wave-driven.
   Declared rather than corrected, because re-drawing the association for one bay
   after seeing the ranking would be selection on the outcome.
8. **Zero means no accepted event in 1993–2025**, never impossibility. The
   boundary is itself sampling-dependent: besides the 84 always at zero, a further
   94 municipalities fall to zero in some resamples, leaving only **102 of 280**
   robustly non-zero.
9. **The index is a relative prioritisation** among the municipalities analysed
   here — not absolute risk, not a probability, and not comparable with other
   studies or with a future revision of this one.

---

## Next Steps

In order of tractability, not of ambition:

1. **Tide-gauge validation of the level component** against GLOSS-Brasil (CHM/Navy)
   and RMPG (IBGE) stations in the North and Northeast. Public data, and it closes
   two declared limitations at once — the absence of independent validation outside
   Santa Catarina and the unverified daily phase assumption.
2. **Wave setup computed directly from Hs**, which would replace the percentile
   criterion with a locally meaningful physical threshold and resolve both the
   floor and the sheltering problem. Requires the physical susceptibility layer.
3. **A physical vulnerability layer** — terrain elevation, beach-face slope,
   natural and hard barriers — which is the single largest conceptual gap.
4. **A severity term that scales with rarity**, so that a hazard resting on one
   event in 33 years does not score like one resting on ninety.
5. **High-resolution unstructured-grid modelling** in the estuarine and reef
   sectors, where the global products do not resolve the dominant processes.

---

## References

- Leal, K. B., et al. (2024). *Identification of coastal natural disasters using
  official databases to provide support for the coastal management: the case of
  Santa Catarina, Brazil.*
- Lima, K. B., et al. (2024). SVI-Coast for Brazilian coastal municipalities.
  *Natural Hazards*. DOI [10.1007/s11069-023-06246-w](https://doi.org/10.1007/s11069-023-06246-w)
- Gregório, M. N., Araújo, T. C. M., Mendonça, F. J. B., Gonçalves, R. M., &
  Mendonça, R. L. (2017). Mudanças posicionais da linha de costa nas praias do
  Pina e de Boa Viagem, Recife, PE, Brasil. *Tropical Oceanography*, 45(1).
  DOI [10.5914/tropocean.v45i1.15200](https://doi.org/10.5914/tropocean.v45i1.15200)
- Rocha, J. I. C. (2018). Alterações nas dunas da Praia de Boa Viagem — Recife (PE)
  originadas por Ação Antrópica. *Investigaciones Geográficas*, 56, 138–152.
  DOI [10.5354/0719-5370.2018.48066](https://doi.org/10.5354/0719-5370.2018.48066)
- Muehe, D. (org.) (2018). *Panorama da Erosão Costeira no Brasil.* Ministério do
  Meio Ambiente, Brasília.
- Bekker, J., & Davis, J. (2020). Learning from positive and unlabeled data: a
  survey. *Machine Learning*, 109, 719–760.
- Silverman, B. W. (1981). Using kernel density estimates to investigate
  multimodality. *Journal of the Royal Statistical Society B*, 43(1), 97–99.
- IPCC (2014). *Climate Change 2014: Impacts, Adaptation, and Vulnerability.*
  Risk framing as the interaction of hazard, exposure and vulnerability.
- INFORM (2017). *Index for Risk Management — Concept and Methodology.* Joint
  Research Centre. Box 2 on pairing absolute and relative exposure; §6.3 on fixed
  goalposts.

---

## Step 4 — Exposure, Vulnerability & Risk Integration

*Referenced from [`README.md`](README.md).* The equations are in
§ *Physical / Statistical Framework*; the decisions and their justification in
§ *Methodology*; the behaviour of the integrated index and the reference-case
validation in § *Results and Interpretation*; and the limitations that qualify
any use of the product in § *Caveats and Limitations*.

The three decisions of this step that most affect interpretation, each with its
audit record:

| Decision | Rationale | Record |
|---|---|---|
| Effective population over four cumulative bands, replacing a single 10 km band | Removes the ceiling saturation of the relative term (59 municipalities at the ceiling → 0) without suppressing municipalities by grid resolution | AUD-08 |
| Fixed anchors throughout; the Min–Max chain and the 0.01 floor removed | A municipality's value stops depending on which other municipalities are present, and hazard zero becomes substantive rather than floored | AUD-11 |
| Vulnerability as Φ(PC1/sd(PC1)), with the 0–100 SVI preserved as a published layer | PC1 has no natural scale; the normal CDF is bounded, anchor-free and monotone, so the delivered ordering is preserved exactly | AUD-09 |
