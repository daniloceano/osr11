# Instantâneo versionado — método vigente (q70 / q99 / portão HAT)

**Criado com a regeneração do Step 3 em 2026-07-31; README acrescentado em
2026-07-31 (AUD-17).**

Cópia versionada das métricas do **método vigente**, preservada aqui porque
`outputs/storm_catalog/` é ignorado pelo Git (`.gitignore` L34) e o produto
publicado precisa de proveniência rastreável.

| Arquivo | Conteúdo |
|---|---|
| `compound_metrics_hat.csv` | Métricas nos 808 pontos nativos |
| `tab_TC5_optimal_pair_pu.csv` | Par de limiares do Step 2e (q0,70 / q0,99) — **acrescentado em 2026-08-04** |
| `tab_TC5_optimal_pair_pu.provenance.json` | Proveniência e SHA-256 do par de limiares |
| `compound_summary_hat.json` | Definição, par de limiares, Q05/Q95 do domínio, validação serial×paralela, fidelidade do detector |

Verificado em 2026-07-31: **idêntico byte a byte** a
`outputs/storm_catalog/compound_hat/`, que é o caminho lido em tempo de execução
por `src/04_risk_integration/hazard_index.py`.

## Método

- Onda: q0,70 local de `VHM0`;
- Nível: q0,99 local de `zos` **livre de maré** — a maré **não** entra no limiar;
- Portão: `max(SWL) > HAT`, com `SWL = (zos − média(zos)) + tide_daily_max` e
  `HAT = max(tide_daily_max)` em 1993–2025 por ponto;
- Severidade integrada sobre o datum HAT; duração e intensidade de pico
  permanecem publicadas como **diagnósticos**, fora do índice (AUD-06).

## Números

| Quantidade | Valor |
|---|---|
| Pontos de grade | 808 |
| Eventos compostos aceitos | **16 768** |
| Candidatos rejeitados pelo portão HAT | 15 857 |
| Pontos sem nenhum evento aceito | 208 |
| Municípios com `Hazard_Index_mun` = 0 por consequência | 83 (AUD-15) |

## Não confundir com os vizinhos

| Diretório | O que é | Eventos |
|---|---|---|
| **`outputs/current_method_hat/`** | **Este.** Método vigente, par calibrado q70/q99 | **16 768** |
| `outputs/hat_method/` | Braço HAT anterior, par **q90/q90** — termo de comparação de AUD-01, sob a chave `hat_q90` | 37 225 |
| `outputs/legacy_mhws_method/` | Braço MHWS, datum Mean High Water Springs — superseded | — |
| `outputs/legacy_ssh_total_method/` | Método `SSH_total` q90/q90 — superseded | 96 031 |

Mapa completo das saídas do Step 3: `src/03_storm_catalog_generation/RUN.md`.


---

## Adendo — 2026-08-04: o par de limiares passou a ser arquivado aqui

`outputs/threshold_calibration/` também está no `.gitignore`, e a tabela do par
ótimo é declarada em `config/analysis_config.py` como **a única fonte autorizada
de limiar do Step 3**. A combinação é perigosa: uma cópia desatualizada produz
um catálogo que discorda do publicado **sem levantar erro algum**.

Foi encontrada exatamente nesse estado em 2026-08-04. A tabela nesta máquina
ainda trazia o par superado **q90/q90**, enquanto o catálogo publicado havia
sido gerado com **q70/q99**. O produto publicado nunca esteve errado — ele foi
gerado no servidor, com a tabela correta, e `compound_metrics_hat.csv` é byte a
byte idêntico ao de lá. O risco era prospectivo: qualquer reexecução do Step 3
nesta máquina teria produzido outro catálogo, em silêncio.

Só não passou despercebido porque `export_timeseries_panel_data.py` re-detecta
os eventos e os confronta com o catálogo publicado, e abortou ao encontrar 184
eventos onde o catálogo registra 77.

Duas medidas foram tomadas:

1. a tabela vigente foi recuperada do servidor e **arquivada aqui**, com
   proveniência e SHA-256;
2. `load_threshold_pair()` em `detection_hat.py` passou a **comparar a tabela em
   tempo de execução com esta cópia** e a levantar erro quando divergirem, de
   modo que a falha seja ruidosa e não silenciosa.
