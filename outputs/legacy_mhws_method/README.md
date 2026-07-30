# Legacy — método MHWS (vigente de 2026-07-29 a 2026-07-30)

Instantâneo **imutável** dos produtos de perigo e risco gerados pelo método
MHWS, que foi o método vigente entre 2026-07-29 e 2026-07-30, quando foi
substituído pelo portão e datum em HAT.

> **Não regenerar nem editar este diretório.** Ele documenta um estado
> histórico. Segue o mesmo precedente de `outputs/legacy_ssh_total_method/`,
> criado quando o método `SSH_total` foi superado pelo MHWS.

Motivo do arquivamento explícito: `outputs/storm_catalog/` e
`outputs/risk_index/` estão no `.gitignore`, portanto o
`compound_metrics_mhws.csv` **não é preservado pelo controle de versão**. Sem
este instantâneo, o resultado do método MHWS se perderia na primeira
reexecução do pipeline.

---

## O que este método fazia

### Detecção do evento composto

```
thr_hs   = q90 local de Hs          (WAVERYS VHM0, máximo diário)
thr_zos  = q90 local de zos         (GLORYS12, livre de maré)

episódio de onda  = Hs  >= thr_hs  , agrupado com gap <= 1 dia
episódio de nível = zos >= thr_zos , agrupado com gap <= 1 dia

MHWS   = A_M2 + A_S2                (constantes harmônicas FES2022)
SWL(d) = (zos(d) - média local de zos) + maré_máx_diária(d)

evento composto = episódio de onda e episódio de nível compartilhando
                  >= 1 dia de excedência (agrupamento union-find)
                  E max(SWL) na sobreposição > MHWS
```

A maré deixou de ser forçante e passou a variável condicionante: ela não decide
mais **se** o evento existe (os percentis de detecção são livres de maré), mas
decide **se a água subiu o bastante para importar** (portão) e **quanto** ela
subiu (severidade).

### Severidade

```
exc_onda_diário  = Hs(d)  - thr_hs
exc_nível_diário = SWL(d) - MHWS          nos dias de critério pleno

severidade integrada = Σ_d 0,5 · [ norm(exc_onda_d) + norm(exc_nível_d) ]
```

`norm` reescala pelos percentis Q05/Q95 de cada excesso agrupados no domínio
inteiro. Os valores usados estão em `hazard/compound_summary_mhws.json`, campo
`rescaling_reference_percentiles`.

### Índice de perigo

```
Hazard_Index_raw = [ norm(compound_count_total) + norm(mean_integrated_severity) ] / 2
Hazard_Index     = norm(Hazard_Index_raw)
```

Duas componentes, pesos 1/2. A duração foi aposentada do índice em 2026-07-29
por AUD-06 e permanece publicada apenas como diagnóstico.

---

## Resultados

### Totais no domínio

| Quantidade | Valor |
|---|---:|
| Pontos de grade | 808 |
| Eventos compostos no domínio | **79.639** |
| Candidatos rejeitados pelo portão MHWS | 30.117 (27,4 % de 109.756) |
| Pontos sem evento | **0** de 808 |
| Municípios associados a ponto sem evento | 0 |
| Período | 1993-01-01 a 2025-12-31 (33,0 anos) |

### Médias por faixa de latitude, componentes normalizadas em 0–1

| Faixa | Frequência | Severidade | Índice |
|---|---:|---:|---:|
| RS (−36…−30) | 0,740 | 0,787 | 0,826 |
| SC/PR (−30…−25) | 0,650 | 0,438 | 0,585 |
| SP/RJ (−25…−20) | 0,465 | 0,385 | 0,454 |
| ES/BA-S (−20…−15) | 0,200 | 0,286 | 0,255 |
| BA-N (−15…−10) | 0,057 | 0,287 | 0,177 |
| NE (−10…−5) | 0,050 | 0,199 | 0,125 |
| N equatorial (−5…0) | 0,048 | 0,277 | 0,167 |
| AP (0…7) | 0,117 | 0,429 | 0,288 |

### Gradiente latitudinal e ranking municipal

| Métrica | Valor |
|---|---:|
| ρ(\|lat\|, `Hazard_Index`) | +0,584 |
| ρ(\|lat\|, `Hazard_Severity`) | +0,345 |
| ρ interno frequência × severidade | +0,599 |
| Municípios no produto de risco | 280 |
| Top-10 municipal ao norte de 20°S | 50 % |

As posições municipais completas estão em `risk/risk_index_municipalities.geojson`.

---

## Por que deixou de ser vigente

**Data em que deixou de ser vigente: 2026-07-30.**

O portão `max(SWL) > MHWS` mostrou-se pouco informativo em toda a costa: a maré
astronômica sozinha já o cruzaria em 73,0 % dos eventos ao norte de 15°S e em
79,6 % ao sul de 25°S (diagnóstico de 2026-07-30,
`outputs/audit/AUD-01_hat_gate_sensitivity/`). Além disso, o conteúdo físico da
severidade variava com a latitude — no Amapá 56 % do excesso é astronômico,
contra 26 % no Rio Grande do Sul —, de modo que um mesmo valor do índice
significava astronomia no Norte e sobrelevação no Sudeste.

A decisão de substituir MHWS por HAT, como portão **e** como datum da
severidade, foi tomada pelo pesquisador responsável, **Danilo Couto de Souza**,
em 2026-07-30, e está registrada na §14 de
`docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md`.

> **Registro honesto exigido pela auditoria.** A adoção do HAT ocorreu com o
> critério falsificável (c) — estabilidade do ranking municipal no Sul/Sudeste —
> **reprovado**, e contra a conclusão explícita do §6 de
> `outputs/method_comparison_mhws_vs_hat/README.md`, que diz que os resultados
> da comparação "não autorizam adotar HAT como método vigente". A decisão foi
> do pesquisador responsável. Ver a entrada de §14 de 2026-07-30 para os
> números completos.

---

## Conteúdo

| Arquivo | Conteúdo |
|---|---|
| `hazard/compound_metrics_mhws.csv` | métricas de evento composto nos 808 pontos |
| `hazard/compound_summary_mhws.json` | definição do método, Q05/Q95 de normalização, totais |
| `hazard/hazard_index_native_grid.csv` | índice de perigo e componentes na grade nativa |
| `hazard/hazard_index_metadata.json` | fórmula, população de normalização, estatísticas |
| `hazard/coastal_hazard_segments.geojson` | camada de perigo publicada no site |
| `hazard/coastal_hazard_metadata.json` | metadados da camada de perigo |
| `risk/risk_index_municipalities.geojson` | risco integrado municipal publicado |
| `risk/risk_index_metadata.json` | metadados do risco municipal |

`hazard/compound_metrics_mhws.csv` e `compound_summary_mhws.json` foram
regenerados por `python -m src.compound_detection.detection_mhws` em 2026-07-30,
antes de qualquer escrita do método novo, e verificados contra os valores já
publicados em `outputs/method_comparison_mhws_vs_hat/hazard_by_point.csv`:
igualdade **exata** em 808/808 pontos para contagem, severidade integrada,
`thr_hs_abs`, duração média e intensidade de pico; total de 79.639 eventos e
30.117 rejeições idênticos ao registrado. O produto é, portanto, o legado
fiel, não uma reconstrução aproximada.

## Onde está o método novo

Método vigente a partir de 2026-07-30: portão e datum em HAT, com o par de
limiares recalibrado no Step 2e sobre o detector novo.

- detecção: `src/03_storm_catalog_generation/02_compound_detection/detection_hat.py`
- calibração: `src/02_threshold_calibration/05_pu_composite_calibration/`
- comparação MHWS × HAT: `outputs/method_comparison_mhws_vs_hat/`
- calibração legada: `outputs/legacy_threshold_calibration_ssh_total/`
