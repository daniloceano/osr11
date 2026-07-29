# AUD-06 — A componente de duração é uma faixa trivial, limitada pela resolução diária, amplificada a peso 1/3

| Campo | Valor |
|-------|-------|
| **ID** | AUD-06 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | perigo |
| **Etapa do fluxo** | Step 3.2 → Step 4.4 |
| **Afeta** | código, interpretação, saídas |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — é a causa proximal da reprovação do litoral central de SC (AUD-05) |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | AUD-05 |
| **Relacionado a** | AUD-07, AUD-11 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 3), §3.1(c), §3.1(d), §6.1, §8 item 5 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

`mean_overlap_duration` varia entre **1,26 e 2,51 dias** em todo o domínio — uma
amplitude de 1,25 dia, imposta pela resolução **diária** do `zos` do GLORYS12. O
Min–Max estica essa faixa trivial para [0, 1] e a média equiponderada lhe atribui
peso 1/3 no `Hazard_Index_raw`.

Ela contribui com apenas **6,0 %** da variância do índice de perigo, mas é
exatamente o que zera o litoral central de Santa Catarina.

## 2. Por que importa cientificamente

Duas patologias distintas, ambas relevantes:

1. **Amplificação de ruído.** Uma diferença de 0,3 dia entre dois pontos — dentro
   do erro de discretização, porque as durações individuais são inteiros de dias —
   torna-se uma diferença de 0,24 numa escala 0–1 com peso 1/3. A componente
   carrega tanto peso nominal quanto a frequência, cuja faixa é 43–322 eventos.

2. **Anticorrelação destrutiva.** Spearman(frequência, duração) = **−0,550**: onde
   as tempestades são frequentes, as sobreposições individuais são curtas. A média
   aritmética das duas componentes as faz **cancelar**, em vez de reforçar. O
   `README.md` §4.4 (nota 3) reconhece isso e o trata como escolha deliberada
   ("índice compensatório explícito"), mas a consequência prática — rebaixar a
   costa de ressacas mais ativa do país — não é discutida.

## 3. Evidência original

De `outputs/storm_catalog/compound/compound_metrics.csv` (808 pontos):

**Distribuição de `mean_overlap_duration`**

| estatística | valor (dias) |
|---|---|
| mínimo | **1,26** — em (−26,6; −48,6), litoral central de SC |
| q25 | 1,59 |
| mediana | 1,71 |
| média | 1,738 |
| q75 | 1,86 |
| máximo | **2,51** — em (3,4; −50,8), offshore do Amapá |
| desvio-padrão | 0,212 |
| IQR / amplitude total | **0,216** |

**Correlações na grade nativa (Spearman)**

| par | ρ |
|---|---|
| frequência × duração | **−0,550** |
| frequência × intensidade | +0,516 |
| duração × intensidade | −0,105 |
| duração × latitude | +0,397 |

**Decomposição de variância de `Hazard_Index_raw`** (participação de covariância)

| componente | participação | desvio-padrão normalizado |
|---|---|---|
| `Hazard_Frequency` | **50,5 %** | 0,248 |
| `Hazard_Intensity` | **43,5 %** | 0,187 |
| `Hazard_Duration` | **6,0 %** | 0,169 |

**Sensibilidade da agregação** (ρ de Spearman com o `Hazard_Index` implementado,
sobre os 808 pontos):

| variante | ρ |
|---|---|
| só frequência | 0,594 |
| só duração | **0,110** |
| só intensidade | 0,871 |
| frequência + intensidade (sem duração) | **0,881** |
| média geométrica de F, D, I | 0,896 |

Remover a duração altera pouco o campo agregado (ρ = 0,881) — mas altera
decisivamente os municípios cujo ponto tem duração mínima.

**Efeito nos municípios de SC** (de `risk_index_municipalities.geojson`):

| Município | `Hazard_Duration` | `Hazard_Frequency` | `Hazard_Intensity` | `Hazard_Index_mun` | posição |
|---|---|---|---|---|---|
| Balneário Camboriú | **0,008** | 0,283 | 0,283 | 0,089 | 280º |
| Itajaí | **0,008** | 0,283 | 0,283 | 0,089 | 275º |
| Navegantes | **0,008** | 0,283 | 0,283 | 0,089 | 273º |
| Itapema | **0,016** | 0,380 | 0,270 | 0,153 | 267º |

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/hazard_index.py` | `COMPONENT_SOURCE_FIELDS` L24–28 | Mapeia `Hazard_Duration` → `mean_overlap_duration` |
| `src/04_risk_integration/hazard_index.py` | `_minmax()` L39–51 | Normalização Min–Max sobre a grade nativa |
| `src/04_risk_integration/hazard_index.py` | L117–120 | Média equiponderada e Min–Max final |
| `src/04_risk_integration/hazard_index.py` | `metadata["component_weights"]` L145–149 | Pesos 1/3, 1/3, 1/3 explícitos |
| `src/03_storm_catalog_generation/02_compound_detection/detection.py` | `compute_compound_metrics()` L239–280 | Calcula `mean_overlap_duration`, `p95_overlap_duration` (L273), `max_overlap_duration` |
| `src/03_storm_catalog_generation/03_duration_persistence/` | submódulo 3.3 | Estatísticas de persistência independentes, não usadas pelo índice |

### Dados e saídas

- `outputs/storm_catalog/compound/compound_metrics.csv` — colunas
  `mean_overlap_duration`, `p95_overlap_duration`, `max_overlap_duration`.
  **As duas últimas já estão calculadas e não são usadas pelo índice** — são
  alternativas imediatas.
- `outputs/storm_catalog/duration_persistence/` — saídas do submódulo 3.3.
- `site/public/data/coastal_hazard_segments.geojson` — camada
  `mean_overlap_duration` publicada em dias, sem reescalonamento.

### Figuras e tabelas afetadas

- `outputs/article_figures/coastal_hazard_index_components.png` — painel de
  duração (2×2).
- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`
- `outputs/article_figures/tables/top10_municipalities_by_hazard.*`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | `Hazard_Duration = minmax_808(mean_overlap_duration)`, peso 1/3, sobre faixa de 1,26–2,51 d |
| **Pretendido/conceitual** | "Duration & Persistence" (`README.md` tabela do Step 3) como dimensão de perigo: eventos mais longos causam mais dano por mais exposição cumulativa a galgamento e erosão |

O conceito é correto — persistência **é** uma dimensão de perigo costeiro. O
problema é que a métrica escolhida (`mean`, em dias inteiros, sobre um dado
diário) não tem resolução para expressá-lo.

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` §4.4 nota 3 declara a anticorrelação e a trata como escolha
  consciente. **Não é uma divergência**, é uma escolha documentada — mas suas
  consequências não estão documentadas.
- `src/site/export_risk_index_data.py` L420–431 descreve `Hazard_Duration` como
  "Mean overlap duration, Min-Max normalized across the native ocean grid" —
  correto, mas sem menção à amplitude de 1,25 dia.
- Não há divergência entre código e saídas.

## 7. Explicações alternativas plausíveis

1. **A faixa estreita pode ser um resultado físico real.** Eventos compostos
   costeiros no Atlântico Sul podem genuinamente durar 1–2,5 dias; a estreiteza
   reflete a natureza do fenômeno, não falta de resolução. Nesse caso, a questão
   é se vale a pena incluir uma componente com tão pouca variabilidade.
2. **A duração pode ser informativa apesar da baixa variância.** Uma componente
   com 6 % da variância pode ainda discriminar corretamente casos extremos. É
   preciso verificar se os pontos de duração mínima são fisicamente distintos, ou
   apenas ruído amostral.
3. **O problema pode ser da estatística escolhida, não da componente.**
   `p95_overlap_duration` e `max_overlap_duration` já estão calculados e têm
   amplitude maior. Trocar `mean` por `p95` pode resolver sem remover a dimensão.
4. **A anticorrelação com a frequência pode ser desejável.** Um índice
   compensatório que equilibra "muitos eventos curtos" contra "poucos eventos
   longos" é conceitualmente defensável. O problema não é a compensação, é a
   amplificação de uma faixa trivial a peso pleno.
5. **O caso de SC pode ser causado principalmente por AUD-04** (ponto abrigado) e
   não pela duração. As duas causas coexistem; é preciso separá-las
   quantitativamente.

## 8. Diagnósticos propostos

1. **Quantificar o erro de discretização.** Distribuição das durações individuais
   (não da média) por ponto, a partir de `compound_catalog.json` →
   `compound_events[].overlap_duration_days`. Verificar quantos valores distintos
   existem (esperado: poucos inteiros pequenos) e calcular o erro padrão da média.
   *Critério:* se o erro padrão da média for comparável à diferença entre pontos,
   a componente é ruído.
2. **Comparar `mean` × `p95` × `max`** como definição da componente: mapas, ρ de
   Spearman entre variantes, e efeito no ranking municipal.
3. **Separar as causas do caso SC:** recalcular `Hazard_Index_mun` para Itajaí,
   Navegantes, Balneário Camboriú e Itapema sob quatro cenários — (a) atual;
   (b) sem duração; (c) com o ponto de grade exposto (AUD-04); (d) ambos.
   *Saída esperada:* atribuição percentual de cada causa.
4. **Testar `Hazard_Index` sem duração** (F + I)/2 no domínio completo: ρ com o
   atual já medido em 0,881; medir o efeito no ranking **municipal** de risco e a
   sobreposição de top-20.
5. **Normalização por posto em vez de Min–Max** para as três componentes
   (interage com AUD-11): ρ = 0,967 já medido no nível do risco; medir no nível do
   perigo.
6. **Verificar se o submódulo 3.3** (`duration_persistence`) oferece uma métrica
   melhor: tempo entre eventos, intensidade integrada, duração p95.

## 9. Critérios objetivos de resolução

- [ ] O erro de discretização da duração média está quantificado por ponto, e
      está demonstrado se as diferenças entre pontos excedem ou não esse erro.
- [ ] Pelo menos três definições alternativas da componente (`mean`, `p95`,
      remoção) foram comparadas quanto a: mapa costeiro, ρ de Spearman com o
      atual, e sobreposição de top-20 no ranking municipal de risco.
- [ ] A contribuição da duração para a posição dos municípios de SC está
      separada da contribuição do ponto de grade abrigado (AUD-04), com
      percentuais.
- [ ] A decisão está tomada e justificada: manter `mean` com peso 1/3, trocar a
      estatística, alterar o peso, ou remover a componente. A justificativa é
      física ou estatística, **não** a concordância com um resultado desejado.
- [ ] Se a componente for mantida, o manuscrito reporta explicitamente sua
      amplitude (1,26–2,51 d), sua participação de 6 % na variância e a
      anticorrelação com a frequência.
- [ ] Produtos a jusante regenerados (§12).

## 10. Riscos de alteração prematura

- **Remover a duração** contraria o desenho declarado do índice
  (frequência–duração–intensidade) e exige reescrever a seção de métodos. É
  também uma perda conceitual: persistência é uma dimensão legítima de perigo.
- **Trocar `mean` por `max`** torna a componente sensível a um único evento por
  ponto — troca ruído de discretização por ruído amostral.
- **Alterar pesos** abre a porta para pesos escolhidos pelo resultado. Se os
  pesos deixarem de ser iguais, o critério de escolha precisa ser declarado antes
  de ver o efeito.
- Corrigir apenas a duração **não** resolve o caso de SC: AUD-04 contribui de
  forma independente. Alterar as duas ao mesmo tempo sem separar as causas
  impede saber o que funcionou.

## 11. Condições sob as quais o resultado atual pode ser mantido

A componente pode ser mantida como está se:

1. O diagnóstico 1 mostrar que as diferenças entre pontos excedem o erro de
   discretização — ou seja, o sinal é real;
2. O manuscrito reportar a amplitude, a participação de 6 % e a anticorrelação;
3. AUD-04 for resolvido, de modo que a reprovação de SC deixe de existir por
   outra via;
4. A tabela de sensibilidade da agregação (AUD-07) for publicada.

## 12. Produtos a jusante que exigiriam regeneração

```bash
python -m src.site.export_coastal_hazard_data
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_top10_municipality_tables
```

Os catálogos **não** precisam ser reprocessados: `mean_overlap_duration`,
`p95_overlap_duration` e `max_overlap_duration` já estão em
`compound_metrics.csv`.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*

### 2026-07-29 — Esta questão passou a ser **bloqueante** para AUD-01

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Não dirigida a AUD-06. Surgiu ao implementar o método MHWS de AUD-01: como a componente de duração se comporta sob o detector novo? |
| **Dados e métodos** | Comparação por faixa de latitude das três componentes normalizadas do perigo, entre o detector legado (`SSH_total`) e o novo (`zos` ∩ Hs condicionado a MHWS). Ver `outputs/method_comparison_ssh_total_vs_mhws/` e AUD-01 §14 (entrada de 2026-07-29, implementação) |
| **Scripts executados** | `python -m src.compound_detection.detection_mhws`; `python -m src.exploratory.compare_methods_ssh_total_vs_mhws` |
| **Achados** | **(1) A componente inverteu sob o detector novo.** `Hazard_Duration` médio: RS 0,235 → **0,039** (passa a ser o mínimo do domínio); N equatorial 0,301 → **0,431** (passa a ser o máximo). A duração média da sobreposição no N equatorial vai de 1,64 para **5,31 dias**. **(2) Causa física identificada**: sob detecção livre de maré, os episódios de nível no trópico são anomalias de `zos` de baixa frequência com 7–8 dias de duração, não tempestades sinóticas; a sobreposição herda essa persistência. **A componente passa a medir persistência de estado oceanográfico, não duração de tempestade.** **(3) Consequência decisiva**: com a duração mantida a peso 1/3, o perigo no N equatorial **sobe** de 0,234 para 0,334 apesar de frequência (0,153 → 0,048) e intensidade (0,394 → 0,239) terem caído, e o top-10 municipal ao norte de 20°S passa de 70 % para **90 %**. **(4) As correções não são separáveis**: top-10 ao norte de 20°S sob as quatro combinações — legado+3comp **70 %**, legado+2comp **90 %**, MHWS+3comp **90 %**, MHWS+2comp **30 %** |
| **Interpretação** | A duração deixou de ser uma fragilidade de peso secundário (6,0 % da variância do `Hazard_Index_raw` sob o método antigo, conforme a revisão de linha de base) e passou a ser **o componente dominante do erro**. O achado (4) estabelece que **AUD-01 e AUD-06 formam um par indissociável**: nenhuma das duas correções isoladas é defensável, e adotar o detector novo sem decidir a duração produz resultado pior que o publicado. Isso eleva de fato a prioridade prática desta questão, embora ela já estivesse classificada como P0 |
| **Alterações implementadas** | Nenhuma. A remoção da duração foi **calculada como diagnóstico**, não adotada — é decisão científica do usuário |
| **Validação realizada** | As quatro combinações usam a mesma função `derive_native_hazard_index` e a mesma exposição/SVI, variando apenas a fonte de métricas e o conjunto de componentes agregadas |
| **Incerteza remanescente** | As alternativas listadas na §8 desta questão — remover a componente, substituir Min–Max por percentil, usar p95 em vez da média, ou redefinir a duração (por exemplo, a duração do episódio de onda, ou dos dias com `SWL > MHWS`) — **não foram comparadas entre si**. Só a remoção completa foi quantificada |
| **Próxima decisão necessária** | Decisão do usuário sobre o tratamento da duração. É pré-requisito para adotar o método de AUD-01 |
