# Legacy — método `SSH_total` (superado em 2026-07-29)

Instantâneo **imutável** dos produtos de perigo e risco gerados pelo método
vigente até 2026-07-29, preservado para comparação e para responder a
questionamentos de revisores sobre a diferença entre os dois métodos.

> **Não regenerar nem editar este diretório.** Ele documenta um estado
> histórico. O método atual e seus produtos ficam em outro lugar — ver
> §"Onde está o método novo".

Motivo do arquivamento explícito: `outputs/storm_catalog/` e
`outputs/risk_index/` estão no `.gitignore`, portanto o `compound_metrics.csv`
antigo **não é preservado pelo controle de versão**. Sem este instantâneo, o
resultado legado se perderia na primeira reexecução.

---

## O que este método fazia

### Detecção do evento composto

```
thr_hs   = q90 local de Hs                    (WAVERYS VHM0, máx. diário)
thr_ssh  = q90 local de SSH_total

SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)
               zos  = nível dinâmico GLORYS12
               tide = maré astronômica FES2022, máximo diário

episódio de onda  = Hs        > thr_hs  , agrupado com gap ≤ 1 dia
episódio de nível = SSH_total > thr_ssh , agrupado com gap ≤ 1 dia

evento composto = sobreposição de ≥ 1 dia de calendário entre um episódio
                  de onda e um episódio de nível (agrupamento union-find)
```

### Intensidade do evento

```
exc_onda  = pico_Hs        − thr_hs
exc_nível = pico_SSH_total − thr_ssh

intensidade = 0,5 · [ norm(exc_onda) + norm(exc_nível) ]
              norm() reescala pelos Q05/Q95 dos excessos, agrupados no domínio
```

### Índice de perigo

```
Hazard_Frequency = minmax_808(compound_count_total)
Hazard_Duration  = minmax_808(mean_overlap_duration)
Hazard_Intensity = minmax_808(mean_compound_intensity_norm)
Hazard_Index_raw = (F + D + I) / 3
Hazard_Index     = minmax_808(Hazard_Index_raw)
```

### Risco integrado

```
Hazard_Index_mun = minmax_280(Hazard_Index)
Risk_Hazard_raw  = (clip(Hazard_Index_mun) · clip(Exposure_Index)
                    · clip(SVI_Coast_2022/100)) ^ (1/3)      piso 0,01
Risk_Hazard      = minmax_280(Risk_Hazard_raw)
```

---

## Por que foi superado

Diagnóstico completo em
[`docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md`](../../docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md).

Em resumo: como `SSH_total` inclui a maré astronômica, e como no setor
macromareal a maré responde por 96–98 % da variância do nível, o limiar q90
local passava a ser, na prática, o envelope de sizígia. As excedências ocorriam
quinzenalmente **por construção**, sem tempestade envolvida.

Evidência quantitativa:

| Diagnóstico | Resultado |
|---|---|
| Teste de Rayleigh dos eventos compostos contra o período de sizígia (14,765 d) | **88,5 %** dos 808 pontos com travamento significativo (p < 0,01) |
| Idem, ao norte de 20°S | **100 %** dos pontos |
| Idem, no Rio Grande do Sul | 5 % — fase essencialmente aleatória, como se espera de forçante sinótico |
| `var(maré) / var(SSH_total)` | 0,22 no RS → **0,985** no Norte equatorial |
| Fração de eventos com sinal de tempestade independente (`zos` acima do próprio q90) | RS 0,92 · SP/RJ 0,78 · **N equatorial 0,17** |

A última linha é o discriminador: no Sul o travamento de fase reflete
**modulação mareal de tempestades reais**, que é física legítima; no Norte
reflete **eventos que se sustentam apenas na maré**.

---

## Conteúdo do instantâneo

| Arquivo | O que é |
|---|---|
| `hazard/compound_metrics.csv` | métricas compostas por ponto de grade (808 pontos) — fonte do índice de perigo |
| `hazard/compound_summary.json` | sumário da execução da detecção composta |
| `hazard/hazard_index_native_grid.csv` | índice de perigo derivado, com as três componentes normalizadas |
| `hazard/hazard_index_metadata.json` | metadados do índice de perigo, incluindo estatísticas por campo |
| `risk/risk_index_municipalities.geojson` | produto municipal publicado (280 municípios com risco) |
| `risk/risk_index_metadata.json` | metadados publicados do risco |

**Não incluído:** `outputs/storm_catalog/compound/compound_catalog.json`
(catálogo completo de eventos, ~44 MB). Permanece no disco em seu caminho
original, mas não é versionado por causa do tamanho. Ele é regenerável a
partir dos catálogos de tempestade do Step 3.1.

---

## Onde está o método novo

| | Legado (aqui) | Novo método |
|---|---|---|
| Código da detecção | `src/03_storm_catalog_generation/02_compound_detection/detection.py` | `.../detection_mhws.py` |
| Métricas compostas | `hazard/compound_metrics.csv` | `outputs/storm_catalog/compound_mhws/compound_metrics_mhws.csv` |
| Comparação lado a lado | — | `outputs/method_comparison_ssh_total_vs_mhws/` |

O código de produção do método legado **não foi alterado**, de modo que este
instantâneo é integralmente reproduzível.

---

**Arquivado em:** 2026-07-29
**Estado do repositório na data:** ramo `main`, commit mais recente `e2680ed`
