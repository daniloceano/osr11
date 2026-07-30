# Legacy — calibração de limiares do Step 2e sobre `SSH_total` (superada em 2026-07-30)

Instantâneo **imutável** da calibração PU composta (Step 2e) como ela estava
antes da recalibração de 2026-07-30. É o estado que produziu o par **q90/q90**
usado por todos os métodos anteriores — `SSH_total`, MHWS — e, por herança não
justificada, também pela primeira versão do braço HAT.

> **Não regenerar nem editar este diretório.** `outputs/threshold_calibration/`
> está no `.gitignore`, portanto estas saídas **não são preservadas pelo
> controle de versão**. Sem este instantâneo elas se perderiam na primeira
> reexecução do Step 2e.

---

## 1. O que esta calibração fazia

### Alvo

Base de eventos costeiros reportados de Santa Catarina, conjunto positivo
combinado:

- base documentária expandida (56 eventos, 14 municípios, 1998–2020);
- base legada Leal et al. (2024) / Defesa Civil (91 eventos, 22 municípios);
- união deduplicada: **147 pares (município, data)** de **27 municípios**;
- `P` = 147 eventos avaliáveis com associação de grade válida.

### Detector pontuado

```
onda   : Hs        >= q_hs  local
nível  : SSH_total >= q_ssh local

SSH_total(d) = zos(d, 00:00 UTC) + maré_máx_diária(d)     (FES2022)
```

**Não havia portão de nível.** O evento era capturado se, em algum instante da
janela causal `[D−2, D−1, D, D+1]`, ambos os limiares fossem excedidos
simultaneamente.

### Score

```
Score(θ) = w1·R_pos(θ) − w2·B(θ) − w3·F_soft(θ)/P

R_pos  = H/P                                  recall dos positivos
B      = min(1, (H+U)/(Y · B_target_efetivo)) carga anual normalizada
F_soft = Σ_i (1 − q_i)                        penalidade branda dos não casados
q_i    = clip(α_E·E_i + α_I·I_i + α_C·C_i, 0, 1)
```

com `w1 = 0,60`, `w2 = 0,20`, `w3 = 0,20`; `α_E = 0,60`, `α_I = 0,30`,
`α_C = 0,10`; `B_target = 12 ep/ano/município × 27 municípios = 324 ep/ano`;
janela de casamento `[−2, −1, 0, +1]`; `EPISODE_MAX_GAP_DAYS = 1`.

### Grade de limiares

`PCT_START = 0,50`, `PCT_STOP = 0,90`, `PCT_STEP = 0,05` — **9 valores, 81
pares**. A grade terminava em q90.

---

## 2. Par selecionado

| Campo | Valor |
|---|---:|
| `thr_hs_pct` | **0,90** |
| `thr_ssh_pct` | **0,90** |
| H (eventos capturados) | 35 |
| M (perdidos) | 112 |
| U (episódios não casados) | 3.069 |
| `R_pos` | 0,2381 |
| `B` | 0,4281 |
| `F_soft` | 2.364,18 |
| **Score** | **−3,159332** |

### Os cinco melhores pares

| rank | q_hs | q_ssh | H | U | R_pos | B | F_soft | Score |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,90 | 0,90 | 35 | 3.069 | 0,2381 | 0,4281 | 2.364,18 | −3,159332 |
| 2 | 0,90 | 0,85 | 38 | 3.928 | 0,2585 | 0,5470 | 3.015,83 | −4,057466 |
| 3 | 0,85 | 0,90 | 45 | 4.145 | 0,3061 | 0,5779 | 3.178,97 | −4,257033 |
| 4 | 0,90 | 0,80 | 42 | 4.530 | 0,2857 | 0,6305 | 3.462,91 | −4,666126 |
| 5 | 0,90 | 0,75 | 46 | 5.009 | 0,3129 | 0,6972 | 3.820,60 | −5,149770 |

**O ótimo está no canto mais restritivo da grade.** O score cresce
monotonicamente com o percentil porque o termo `−w3·F_soft/P` domina: em
q90/q90 vale −3,216, contra +0,143 do termo de recall. Na prática, o score
selecionava o par que **minimizava o número de detecções não casadas**, e a
grade impedia que ele fosse além de q90. AUD-02 §4 já registrava esse sinal:
"o ótimo está na borda da grade, o que é em si um sinal de que o ótimo pode
estar fora dela".

### Sensibilidade

O par q90/q90 é selecionado em **todas** as variantes testadas — pesos
(`high_recall`, `balanced`, `default`), alphas (`evidence_heavy`,
`intensity_moderate`, `default`), `B_target` (6, 12, 18, 24 ep/ano/município) e
tolerância de gap (0, 1, 2, 3 dias). Ver as quatro tabelas
`tab_TC5_sensitivity_*.csv`. A estabilidade não é evidência de robustez
física: decorre de o ótimo estar preso à borda da grade em todas as variantes.

---

## 3. Por que foi substituída

**Data em que deixou de ser vigente: 2026-07-30.**

A calibração pontuava pares de limiar contra `SSH_total = zos + maré`. O método
vigente desde 2026-07-29 (MHWS) **já não lia `SSH_total`** — detectava sobre
`zos` livre de maré —, e o método adotado em 2026-07-30 detecta sobre `zos` com
portão em HAT. Manter uma calibração feita sobre uma variável que o detector
não lê é inconsistência científica, e estava registrada como incerteza
remanescente no fechamento de AUD-01 de 2026-07-29:

> "**A calibração do Step 2e não foi refeita** — o par q90/q90 foi otimizado
> sobre `SSH_total` e segue aplicado à variável nova, sem recalibração nem
> justificativa escrita."

A recalibração de 2026-07-30 troca o detector pontuado pelo detector de
produção (onda `Hs ≥ q_hs`, nível `zos ≥ q_zos`, portão `max(SWL) > HAT`) e
estende a grade para incluir q95 e q99 — 11 valores, 121 pares —, atacando
também o sinal de ótimo na borda. Todo o restante da maquinaria de pontuação
(janela de casamento, auditoria de episódios, score composto, pesos, alphas,
`B_target`, análise de sensibilidade) permanece **idêntico**.

Decisão do pesquisador responsável, **Danilo Couto de Souza**, registrada na
§14 de `docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md`.

---

## 4. Conteúdo

| Arquivo | Conteúdo |
|---|---|
| `tables/tab_TC5_optimal_pair_pu.csv` | o par selecionado, q90/q90 |
| `tables/tab_TC5_pu_metrics_full.csv` | score composto dos 81 pares |
| `tables/tab_TC5_pu_metrics_ranked.csv` | os mesmos 81 pares ordenados |
| `tables/tab_TC5_score_decomposition.csv` | decomposição termo a termo do score |
| `tables/tab_TC5_sensitivity_weights.csv` | sensibilidade a `w1/w2/w3` |
| `tables/tab_TC5_sensitivity_alpha.csv` | sensibilidade a `α_E/α_I/α_C` |
| `tables/tab_TC5_sensitivity_b_target.csv` | sensibilidade a `B_target` |
| `tables/tab_TC5_sensitivity_gap_days.csv` | sensibilidade ao gap de episódio |
| `tables/tab_TC5_csi_vs_pu_comparison.csv` | comparação com o Step 2d (CSI) |
| `tables/tab_TC5_event_capture_status.csv` | captura evento a evento no par ótimo |
| `tables/tab_TC5_event_provenance.csv` | proveniência dos 147 positivos |
| `tables/tab_TC5_positive_event_union_audit.csv` | auditoria da união das duas bases |
| `tables/tab_TC5_qi_decomposition.csv` | decomposição de `q_i` no par ótimo |
| `figures/fig_TC5_H1_score_heatmap.png` | heatmap do score na grade 9 × 9 |
| `figures/fig_TC5_H2_recall_heatmap.png` | heatmap de `R_pos` |
| `figures/fig_TC5_H3_burden_heatmap.png` | heatmap de `B` |
| `figures/fig_TC5_H4_fsoft_heatmap.png` | heatmap de `F_soft` |
| `figures/fig_TC5_S1_csi_vs_pu.png` | CSI (Step 2d) × PU (Step 2e) |
| `figures/fig_TC5_S2_sensitivity_weights.png` | sensibilidade a pesos |
| `figures/fig_TC5_S3_sensitivity_b_target.png` | sensibilidade a `B_target` |
| `figures/fig_TC5_S4_sensitivity_gap_days.png` | sensibilidade ao gap |
| `figures/fig_TC5_A1_qi_distribution.png` | distribuição dos pesos de confiança `q_i` |
| `figures/fig_TC5_E1_event_capture.png` | captura por evento no par ótimo |

**Não versionado por tamanho:** `tab_TC5_episode_audit.csv` (121 MB, auditoria
episódio a episódio de todos os não casados dos 81 pares). É integralmente
regenerável a partir do código e dos dados de entrada, e o
`tab_TC5_score_decomposition.csv` já preserva o valor agregado de `F_soft` por
par, que é o que efetivamente entra no score.
