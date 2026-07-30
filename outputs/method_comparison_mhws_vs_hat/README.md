# Comparação de método — MHWS (vigente) × HAT (experimental)

Comparação componente a componente do detector vigente com um braço que troca
**apenas** o datum de nível: o portão e todos os excessos de nível passam de
MHWS para HAT. Exposição, vulnerabilidade e associação grade→município são
idênticas nos dois braços por construção.

Gerado por
[`src/exploratory/compare_methods_mhws_vs_hat.py`](../../src/exploratory/compare_methods_mhws_vs_hat.py)
a partir do instantâneo HAT produzido por
[`detection_hat.py`](../../src/03_storm_catalog_generation/02_compound_detection/detection_hat.py).
Nada aqui adota HAT, altera o catálogo vigente, atualiza o site ou regenera
figuras do artigo.

---

## 1. A diferença de método

| | MHWS vigente | HAT experimental |
|---|---|---|
| Limiar de onda | q90 local de Hs | q90 local de Hs *(igual)* |
| Limiar de nível | q90 local de `zos` | q90 local de `zos` *(igual)* |
| SWL | `(zos − média local) + maré_máx_diária` | igual |
| Portão | `max(SWL) > MHWS` | `max(SWL) > HAT` |
| Datum da severidade | `SWL_d − MHWS` | `SWL_d − HAT` |
| Datum | `A_M2 + A_S2` do FES2022 | `max(tide_daily_max)`, 1993–2025 |
| Índice | frequência + severidade integrada, pesos 1/2 | igual |

O HAT foi passado no parâmetro de datum/portão de
`compound_events_at_point`; a detecção não foi reimplementada. Portão e datum
permanecem no mesmo nível, evitando o híbrido incoerente cuja constante
`HAT − MHWS` explica 94–99% do excesso no Norte.

---

## 2. Verificação de fidelidade e paralelismo

- `thr_hs` recomputado idêntico ao de produção em **808/808** pontos;
  diferença máxima **0,000000 m**.
- As fases de detecção e pontuação foram comparadas em 30 pontos, serial ×
  paralelo, com igualdade exata de escalares e arrays (mesmos valores, dtype e
  shape).
- A concatenação dos excessos segue a ordem fixa ponto→evento→dia.
- O cálculo respeita a barreira global: detectar em paralelo → calcular
  Q05/Q95 sobre todo o braço → pontuar em paralelo.

Teste de aceitação:

| Resultado | MHWS | HAT |
|---|---:|---:|
| Eventos no domínio | 79.639 | **37.225** |
| Eventos ao norte de 15°S | 14.582 | **545** |
| Eventos ao sul de 25°S | 34.965 | **24.196** |
| Pontos sem evento | 0 | **248 de 808** |

Todos os quatro valores HAT reproduzem exatamente o diagnóstico exploratório
de `outputs/audit/AUD-01_hat_gate_sensitivity/`.

---

## 3. Normalização por braço

As referências Q05/Q95 foram recalculadas **dentro de cada braço**. Não se
reaproveitou a escala MHWS para o conjunto diferente de eventos HAT.

| Excesso agrupado no domínio | MHWS Q05 | MHWS Q95 | HAT Q05 | HAT Q95 |
|---|---:|---:|---:|---:|
| pico de onda (m) | 0,0400 | 1,4900 | 0,0500 | 1,6720 |
| pico de nível (m) | 0,0328 | 0,7607 | 0,0115 | 0,4284 |
| onda diária (m) | 0,0100 | 1,2900 | 0,0300 | 1,4900 |
| nível diário (m) | 0,0256 | 0,7231 | 0,0102 | 0,4044 |

### Pontos sem evento

Para impedir que `dropna()` normalize os braços sobre populações diferentes,
foi adotada a mesma regra nos dois lados antes de chamar
`derive_native_hazard_index()`:

> ausência de evento aceito implica frequência = 0 e severidade integrada = 0,
> pois não existe perigo derivado de evento naquele ponto.

Assim, ambos os índices são normalizados sobre os mesmos **808 pontos**. Duração
e intensidade de pico recebem zero apenas nas comparações diagnósticas
normalizadas; continuam fora do índice.

---

## 4. Resultado por componente

| Componente | Spearman MHWS×HAT | ρ(\|lat\|), MHWS | ρ(\|lat\|), HAT |
|---|---:|---:|---:|
| Frequência | **0,877** | +0,642 | +0,650 |
| Severidade integrada | **0,703** | +0,345 | +0,653 |
| Índice de perigo | **0,894** | +0,584 | +0,658 |
| Duração *(diagnóstico aposentado)* | 0,081 | −0,793 | −0,193 |
| Intensidade de pico *(diagnóstico aposentado)* | 0,778 | +0,474 | +0,634 |

Médias das componentes vigentes já normalizadas em 0–1:

| Faixa | Freq. MHWS | Freq. HAT | Sever. MHWS | Sever. HAT | Índice MHWS | Índice HAT |
|---|---:|---:|---:|---:|---:|---:|
| RS | 0,740 | 0,595 | 0,787 | 0,734 | 0,826 | 0,664 |
| SC/PR | 0,650 | 0,366 | 0,438 | 0,497 | 0,585 | 0,432 |
| SP/RJ | 0,465 | 0,227 | 0,385 | 0,427 | 0,454 | 0,327 |
| ES/BA-S | 0,200 | 0,015 | 0,286 | 0,217 | 0,255 | 0,116 |
| BA-N | 0,057 | 0,000 | 0,287 | 0,009 | 0,177 | 0,005 |
| NE | 0,050 | 0,001 | 0,199 | 0,008 | 0,125 | 0,004 |
| N equatorial | 0,048 | 0,003 | 0,277 | 0,063 | 0,167 | 0,033 |
| AP | 0,117 | 0,007 | 0,429 | 0,112 | 0,288 | 0,060 |

O HAT não produz apenas uma redução suave. Em BA-N e NE, frequência e
severidade são empurradas praticamente ao piso; o índice médio cai para 0,005 e
0,004. Ao norte de 15°S, a perda é de **96,3% dos eventos** (14.582 → 545).

### Relação entre as componentes

No braço MHWS, frequência e severidade se reforçam com ρ = **+0,599**, conforme
o produto vigente. Sob HAT, a correlação sobe para **+0,958**. Isso não é
evidência independente de maior coerência física: os dois campos passam a
compartilhar a mesma massa de 248 zeros, imposta pelo portão extremo.

### Componentes aposentadas

A duração quase perde toda concordância entre braços (ρ = 0,081) e continua com
gradiente latitudinal oposto ao perigo climatológico. A intensidade de pico
mantém concordância moderada-alta (ρ = 0,778), mas muda junto com seu datum e
suas referências de normalização. Ambas são diagnóstico; nenhuma recebe peso
no índice.

---

## 5. Risco municipal

| Métrica | Resultado |
|---|---:|
| Municípios comparados | 280 |
| Spearman do risco MHWS×HAT | **0,700** |
| Sobreposição do top-10 | **4 de 10** |
| Top-10 ao norte de 20°S, MHWS | 50% |
| Top-10 ao norte de 20°S, HAT | **0%** |
| Municípios associados a ponto sem evento, MHWS | 0 |
| Municípios associados a ponto sem evento, HAT | **96** |

Top-10 sob HAT: São José do Norte/RS, Magé/RJ, Tavares/RS, Maricá/RJ, São
Sebastião/SP, Duque de Caxias/RJ, Mostardas/RS, Saquarema/RJ, Bertioga/SP e
Paraty/RJ. Os quatro nomes compartilhados com o top-10 MHWS são São José do
Norte, Magé, Maricá e Saquarema.

Deslocamentos ilustrativos:

- Apicum-Açu/MA: 1º → 167º;
- Turiaçu/MA: 2º → 169º;
- Macapá/AP: 16º → 134º;
- Presidente Kennedy/ES: 236º → 122º;
- Itajaí/SC: 230º → 126º;
- Bombinhas/SC: 189º → 88º.

A lista completa, inclusive as 15 maiores subidas e quedas, está em
`comparison_summary.json` e `risk_by_municipality.csv`.

---

## 6. Leitura crítica

O braço HAT reforça o gradiente Sul→N do índice e remove todos os municípios ao
norte de 20°S do top-10. Porém, faz isso em grande parte eliminando o suporte
amostral: zera 248 pontos e reduz os eventos ao norte de 15°S em 96,3%. Portanto
o resultado não demonstra que HAT “corrige” o risco nortista; demonstra que um
portão próximo do máximo astronômico observado funciona como **exclusão
implícita de domínio**.

A concordância alta do índice na grade (ρ = 0,894) convive com mudanças grandes
no produto de decisão: risco municipal ρ = 0,700 e apenas 4/10 municípios
compartilhados no topo. A escolha do datum não é um detalhe de escala.

---

## 7. Limitações

O HAT é o máximo de uma amostra de 33 anos: uma estatística de ordem extrema,
dependente do comprimento e da janela do registro. Isso contrasta com
`A_M2 + A_S2`, estimador analítico. Um portão em HAT torna o conjunto de eventos
dependente de 1993–2025 e não transferível diretamente a projeções.

Além disso:

- 248 pontos e 96 municípios associados ficam sem evento;
- o HAT estimado por máximo amostral carrega erro de discretização temporal da
  `tide_daily_max` e dependência das constituintes presentes na série;
- a calibração q90/q90 permanece a vigente; não foi alterada nem refeita;
- exposição, vulnerabilidade e associação grade→município permanecem sujeitas
  às limitações já registradas em AUD-04;
- AUD-02, AUD-12 e AUD-18 não são resolvidos por esta comparação.

Estes resultados não autorizam adotar HAT como método vigente.

---

## 8. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `comparison_summary.json` | estatísticas por componente/faixa, cobertura e ranking |
| `hazard_by_point.csv` | MHWS e HAT lado a lado nos 808 pontos |
| `risk_by_municipality.csv` | risco, posições e deslocamentos dos 280 municípios |
| `figures/map_frequency_mhws_vs_hat.png` | frequência, braços e diferença |
| `figures/map_severity_mhws_vs_hat.png` | severidade integrada |
| `figures/map_index_mhws_vs_hat.png` | índice de perigo |
| `figures/map_duration_diagnostic_mhws_vs_hat.png` | duração aposentada |
| `figures/map_peak_intensity_diagnostic_mhws_vs_hat.png` | pico aposentado |

O instantâneo versionado do braço HAT está em `outputs/hat_method/`.

---

**Gerado em:** 2026-07-30
