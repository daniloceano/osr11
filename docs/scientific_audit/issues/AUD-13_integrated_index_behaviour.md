# AUD-13 — Comportamento do índice integrado: o índice é conduzido pelo perigo (84,7 %), e o cancelamento estrutural dominante é perigo × vulnerabilidade

> *Título original (2026-07-29): "dominância do perigo e cancelamento estrutural
> exposição × vulnerabilidade". Atualizado em 2026-07-31 — ver §3-bis.*

| Campo | Valor |
|-------|-------|
| **ID** | AUD-13 |
| **Tipo** | `analise-sensibilidade` |
| **Componente** | integração |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação — a decomposição de contribuições precisa acompanhar o resultado |
| **Status** | `resolvido` |
| **Desfecho** | `resultado-validado-mantido` |
| **Depende de** | AUD-01, AUD-02 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-05, AUD-07, AUD-08, AUD-09, AUD-11 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §4.1, §4.2, §8 item 11, §9.1 item 4 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (reescrita contra o produto atual e fechamento) |

---

> ### Nota de leitura — este registro foi reescrito em 2026-07-31
>
> Toda a evidência original (§3) foi levantada em 2026-07-29, **antes** do portão
> HAT (AUD-01/AUD-06), da remoção da cadeia de Min–Max e do piso (AUD-11) e da
> exposição por população efetiva (AUD-08). Ela descreve um produto que não
> existe mais e **está preservada como está**, por rastreabilidade.
>
> A evidência sobre o produto vigente está na **§3-bis**, e os critérios de
> aceitação foram reescritos na **§9**. Dois critérios de 2026-07-29 tornaram-se
> **insatisfazíveis** e um ficou **sem objeto**; nenhum foi apagado — todos estão
> anotados com a razão.
>
> Fechada como `resultado-validado-mantido` por decisão do pesquisador em
> 2026-07-31. Ver §14.

## 1. Problema

A média geométrica das três componentes está corretamente implementada e é a
escolha conceitualmente adequada para um índice conjuntivo IPCC. Mas seu
comportamento efetivo não corresponde aos pesos nominais de 1/3, e duas
propriedades estruturais não estão documentadas:

1. **O perigo domina** — 51,0 % da variância de log(`Risk_Hazard_raw`), contra
   27,0 % da exposição e 22,0 % da vulnerabilidade — porque a média geométrica
   pondera pela dispersão **logarítmica**, não pelo peso nominal.
2. **Exposição e vulnerabilidade se cancelam parcialmente** — ρ = −0,588 — porque
   municípios populosos têm SVI baixo por construção. O produto comprime a
   variabilidade final em vez de amplificá-la.

> **Atualização de 2026-07-31.** As duas propriedades acima continuam sendo o
> motivo de a questão existir, mas **nenhuma das duas descreve o produto atual**.
> A primeira intensificou-se ao ponto de mudar de natureza (84,7 %; sem o perigo
> não sobra ranking). A segunda foi rebaixada a efeito de segunda ordem — 9 % de
> compressão — e substituída por um cancelamento **perigo × vulnerabilidade**
> três vezes maior, de natureza diferente. Ver §3-bis.

## 2. Por que importa cientificamente

- Um leitor que veja "média geométrica com pesos iguais" concluirá que as três
  camadas contribuem igualmente. Não contribuem. Isso precisa ser reportado.
- A dominância do perigo é **apropriada** — desde que o perigo esteja correto.
  Como AUD-01 e AUD-02 mostram que ele não está no Norte, a dominância propaga o
  problema em vez de amortecê-lo. Esta é a razão de esta questão depender daquelas.
- O cancelamento E × V significa que a soma de duas dimensões conceitualmente
  independentes produz menos discriminação do que qualquer uma isolada. Isso é um
  comportamento não intencional de um índice conjuntivo e merece discussão.
- A inversão entre o top-10 de **perigo** (todo S/SE) e o top-10 de **risco**
  (7/10 no N) é o resultado mais importante do trabalho e precisa ser explicado
  mecanicamente, não apenas apresentado.

## 3. Evidência original (2026-07-29) — **sobre o produto superseded**

> **Nenhum número desta seção descreve o produto atual.** Preservada por
> rastreabilidade e porque é ela que documenta o que a questão foi criada para
> investigar. A evidência vigente está na §3-bis.

Todos os cálculos sobre `site/public/data/risk_index_municipalities.geojson`,
280 municípios com perigo.

### 3.1 Dispersão logarítmica das três componentes

| Componente | mín | p10 | mediana | p90 | máx | **sd(log)** | CV |
|---|---|---|---|---|---|---|---|
| `Hazard_Index_mun` | 0,010 | 0,131 | 0,382 | 0,791 | 1,000 | **0,657** | 0,543 |
| `Exposure_Index` | 0,010 | 0,399 | 0,712 | 0,889 | 1,000 | 0,547 | 0,300 |
| `SVI/100` | 0,010 | 0,206 | 0,486 | 0,733 | 1,000 | 0,554 | 0,444 |

### 3.2 Decomposição de variância de log(`Risk_Hazard_raw`)

Participação de covariância, normalizada (soma = 1):

| Componente | participação |
|---|---|
| **Perigo** | **51,0 %** |
| Exposição | 27,0 % |
| Vulnerabilidade | 22,0 % |

### 3.3 Matriz de correlação de Spearman

| | `Hazard_Index_mun` | `Exposure_Index` | `SVI/100` | `Risk_Hazard` |
|---|---|---|---|---|
| `Hazard_Index_mun` | 1,000 | 0,148 | −0,175 | **0,668** |
| `Exposure_Index` | 0,148 | 1,000 | **−0,588** | 0,198 |
| `SVI/100` | −0,175 | −0,588 | 1,000 | 0,297 |
| `Risk_Hazard` | 0,668 | 0,198 | 0,297 | 1,000 |

### 3.4 Correlações parciais de posto

| relação | ρ parcial |
|---|---|
| Risco × Perigo, controlando E e V | **0,845** |
| Risco × SVI, controlando H e E | **0,795** |

Ambas altas — o índice **não** é degenerado; ambos os fatores importam. Isso é um
resultado positivo e deve ser reportado como tal.

### 3.5 Ranking por componente isolada, contra o risco publicado

| ranking por | ρ com o risco | sobreposição de top-20 |
|---|---|---|
| perigo apenas | 0,668 | 5/20 |
| exposição apenas | 0,198 | 1/20 |
| vulnerabilidade apenas | 0,297 | 3/20 |

Nenhuma componente isolada reproduz o ranking — o índice **acrescenta**
informação em relação a qualquer camada isolada.

### 3.6 Deixar-uma-componente-de-fora

| removida | ρ | top-20 |
|---|---|---|
| perigo | 0,554 | 10/20 |
| exposição | 0,803 | 9/20 |
| vulnerabilidade | 0,741 | 5/20 |

### 3.7 A inversão perigo → risco

| Top-10 por **perigo** | Top-10 por **risco** |
|---|---|
| São Sebastião/SP, Bertioga/SP, Laguna/SC, Saquarema/RJ, Santa Vitória do Palmar/RS, Araruama/RJ, Angra dos Reis/RJ, Maricá/RJ, Duque de Caxias/RJ, Guapimirim/RJ | Icatu/MA, Turiaçu/MA, Apicum-Açu/MA, Macapá/AP, Axixá/MA, Magé/RJ, Maricá/RJ, Chaves/PA, Saquarema/RJ, Salvaterra/PA |

Médias por região (corte em 15°S):

| | Risco | SVI | `Hazard_Index_mun` |
|---|---|---|---|
| Norte de 15°S (n = 165) | 0,610 | 60,0 | 0,335 |
| Sul de 15°S (n = 115) | 0,556 | 28,0 | 0,514 |

Composição do top-N:

| | N/NE | SE/S |
|---|---|---|
| top-10 | 7 | 3 |
| top-20 | 15 | 5 |
| top-50 | 32 | 18 |

---

## 3-bis. Evidência sobre o produto atual (2026-07-31)

Gerada por `src/exploratory/audit_AUD_13_component_contributions.py` →
`outputs/audit/AUD-13_component_contributions/`. Fonte:
`site/public/data/risk_index_municipalities.geojson` — **280 municípios com
risco, dos quais 196 com risco positivo e 84 em zero exato**; faixa
0 – 0,566342.

### 3-bis.1 As quantidades em log só existem sobre um subconjunto

`Risk_Hazard_raw` vale exatamente zero em 84 municípios, logo **a decomposição
de variância de log(risco) que a §8.1 pede é indefinida sobre a amostra**. Tudo
que envolve logaritmo abaixo está restrito aos **196 com risco positivo**, e
essa restrição é uma escolha, não o diagnóstico pedido.

| Componente | mín | p10 | mediana | p90 | máx | **sd(log)** | CV |
|---|---|---|---|---|---|---|---|
| `Hazard_Index_mun` | 0,010 | 0,024 | 0,158 | 0,645 | 0,799 | **1,255** | 0,875 |
| `Exposure_Index` | 0,010 | 0,163 | 0,486 | 0,712 | 0,835 | 0,662 | 0,446 |
| `Vulnerability_CDF_PC1` | 0,012 | 0,088 | 0,303 | 0,928 | 0,995 | 0,948 | 0,747 |

### 3-bis.2 Decomposição de variância de log(risco), nos 196

| Componente | participação | era em 2026-07-29 |
|---|---|---|
| **Perigo** | **84,7 %** | 51,0 % |
| Exposição | 35,0 % | 27,0 % |
| Vulnerabilidade | **−19,7 %** | 22,0 % |

A participação negativa não é erro: a vulnerabilidade está anticorrelacionada
com o agregado e **reduz** a dispersão do índice em vez de somar a ela.

### 3-bis.3 Correlações de Spearman

| par | 280 municípios | 196 com risco > 0 | era (280) |
|---|---|---|---|
| perigo ~ exposição | +0,278 | +0,314 | +0,148 |
| **perigo ~ vulnerabilidade** | **−0,601** | −0,702 | −0,175 |
| exposição ~ vulnerabilidade | −0,467 | −0,522 | **−0,588** |
| perigo ~ risco | **+0,893** | +0,708 | +0,668 |
| exposição ~ risco | +0,374 | +0,466 | +0,198 |
| **vulnerabilidade ~ risco** | **−0,372** | −0,247 | **+0,297** |

**A correlação marginal da vulnerabilidade com o risco trocou de sinal.**

### 3-bis.4 Correlações parciais de posto (196)

| relação | ρ parcial |
|---|---|
| Risco × Perigo, controlando E e V | **+0,890** |
| Risco × Exposição, controlando H e V | **+0,753** |
| Risco × Vulnerabilidade, controlando H e E | **+0,790** |

As três continuam altas. Combinado com o marginal negativo de V, isto é
**supressão, não degenerescência**: a vulnerabilidade discrimina
condicionalmente, e sua correlação marginal é invertida pela anticorrelação com
o perigo. O índice **não** é redundante.

### 3-bis.5 Agregações alternativas

ρ de Spearman contra o ranking publicado, com sobreposição de top-10:

| variante | ρ (280) | top-10 | ρ (196) | era (280) |
|---|---|---|---|---|
| perigo = só frequência | 0,940 | 8/10 | 0,829 | **0,384** |
| perigo = só severidade | 0,974 | 4/10 | 0,932 | — |
| **média aritmética H,E,V** | **0,550** | **4/10** | 0,648 | **0,934** |
| sem exposição (H × V) | 0,914 | 4/10 | 0,789 | 0,803 |
| sem vulnerabilidade (H × E) | 0,923 | 3/10 | 0,782 | 0,741 |
| **sem perigo (E × V)** | **−0,223** | **0/10** | **+0,092** | 0,554 |
| perigo isolado | 0,893 | 2/10 | 0,708 | 0,668 |
| exposição isolada | 0,374 | 1/10 | 0,466 | 0,198 |
| vulnerabilidade isolada | **−0,372** | 0/10 | −0,247 | 0,297 |

Dois resultados invertem o quadro de 2026-07-29:

- **A instabilidade que motivava AUD-07 dissolveu-se no eixo em que foi
  medida** — "só frequência" foi de ρ = 0,384 para 0,940 — e **migrou para o
  eixo da agregação**: aritmética contra geométrica foi de 0,934 para **0,550**.
  A escolha conjuntiva deixou de ser preferência conceitual e passou a
  determinar o resultado.
- **Sem o perigo não sobra ranking**: ρ = +0,092 entre os 196. O índice
  integrado é, operacionalmente, o índice de perigo modulado.

### 3-bis.6 O cancelamento trocou de par

Teste de embaralhamento (2000 sorteios, semente 13), preservando as marginais.
Razão < 1 significa que a anticorrelação **comprime** a variância do índice:

| par quebrado | var(log risco) independente | razão | leitura |
|---|---|---|---|
| exposição × vulnerabilidade | 0,1342 | **0,911** | comprime 9 % |
| **perigo × vulnerabilidade** | 0,3683 | **0,332** | **comprime por um fator de 3** |

O cancelamento E × V — objeto declarado desta questão — passou a ser de segunda
ordem. **O cancelamento que hoje domina é H × V**, e ele tem natureza distinta:
E × V é um fato social brasileiro (municípios populosos são menos privados),
enquanto H × V é a interseção de **dois gradientes geográficos independentes**,
um físico e um socioeconômico. A defesa de um não serve ao outro.

### 3-bis.7 A inversão perigo → risco deixou de existir

| Top-10 por **perigo** | Top-10 por **risco** |
|---|---|
| Santa Vitória do Palmar/RS, Tavares/RS, São José do Norte/RS, Laguna/SC, Jaguaruna/SC, Bertioga/SP, São Sebastião/SP, Mostardas/RS, Araranguá/SC, Balneário Rincão/SC | São José do Norte/RS, Guaraqueçaba/PR, Magé/RJ, Mangaratiba/RJ, Paraty/RJ, Guarujá/SP, Balneário Gaivota/SC, São Sebastião/SP, Saquarema/RJ, Passo de Torres/SC |

| | N/NE | SE/S | era N/NE |
|---|---|---|---|
| top-10 | **0** | 10 | 7 |
| top-20 | **0** | 20 | 15 |
| top-50 | 9 | 41 | 32 |

Médias por região (corte em 15°S):

| | n | Risco | SVI | `Hazard_Index_mun` |
|---|---|---|---|---|
| Norte de 15°S | 165 | 0,114 | 60,1 | **0,030** |
| Sul de 15°S | 115 | 0,312 | 28,0 | **0,445** |

### 3-bis.8 O mecanismo: o portão HAT é monotônico em latitude

Este é o elemento que a §3 nunca teve — sem ele, "o perigo domina, e isso é
apropriado desde que o perigo esteja correto" (§7.1) fica sem sustentação.

De `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv`, 808 pontos:

| Faixa | pontos | HAT médio (m) | `thr_hs` médio (m) | pontos sem evento aceito | eventos médios |
|---|---|---|---|---|---|
| 35–28°S | 104 | **0,49** | 1,94 | 0 | 84,0 |
| 28–23°S | 123 | 0,71 | 1,74 | 0 | 49,3 |
| 23–15°S | 127 | 1,09 | 1,73 | 13 | 8,3 |
| 15–8°S | 91 | 1,39 | 1,69 | **63** | 0,3 |
| 8–2°S | 163 | 1,77 | 1,70 | **91** | 0,5 |
| 2°S–7°N | 195 | **2,61** | 1,28 | 41 | 1,7 |

**A barra a vencer cresce por um fator de 5 do RS ao Amapá, por razões de maré
que nada têm a ver com tempestade**, exatamente onde o forçante meteorológico
enfraquece. Resultado: **208 dos 808 pontos sem nenhum evento aceito em 33
anos**, e estados inteiros em perigo zero — AL 15/15, SE 7/7, CE 18/20,
PE 12/13 (inclui Recife e Olinda), RN 14/23.

### 3-bis.9 Decomposição por município

`municipality_contributions.csv` traz, para os 196 com risco positivo, o desvio
de cada componente em relação à sua mediana, em unidades do desvio-padrão
logarítmico da própria componente. Permite a leitura pedida na §8.2 — "este
município está onde está porque V está x desvios acima e H y abaixo" — numa
escala que admite os zeros por exclusão explícita, e não por artifício.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/site/export_risk_index_data.py` | L570–583 | Média geométrica com piso; comentário justificando a escolha conjuntiva |
| `src/site/export_risk_index_data.py` | `integrated_risk_formula` L835–853 | Metadados da fórmula e da racionalidade IPCC |
| `src/site/export_risk_index_data.py` | L546–555 | Justificativa de `Hazard_Index_mun` |
| `src/04_risk_integration/exposure_index.py` | `CLIP_FLOOR` L66 | Piso 0,01 |
| `src/exploratory/make_exploratory_risk_with_exposure.py` | — | Comparador existente de variantes de risco |

### Dados e saídas

- `site/public/data/risk_index_metadata.json` → `numeric_stats`,
  `integrated_risk_formula`, `integrated_risk_normalization`.
- `outputs/exploratory_exposure/risk_with_exposure_summary.json`

### Figuras e tabelas afetadas

- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png` — a figura
  que apresenta as três camadas lado a lado e é o principal veículo desta questão.
- `outputs/article_figures/tables/top10_municipalities_by_*.{csv,tex}`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | `Risk = (clip(H)·clip(E)·clip(V))^(1/3)`, pesos nominais 1/3, dispersões logarítmicas desiguais |
| **Pretendido/conceitual** | Índice conjuntivo IPCC em que as três dimensões contribuem de forma declarada e compreendida |

A fórmula está correta. O que falta é **medir e declarar** seu comportamento.

## 6. Divergência documentação ↔ implementação ↔ saídas

- `README.md` §4.4 e os metadados descrevem a fórmula corretamente e justificam
  a escolha geométrica contra a aritmética ("An arithmetic mean would let a large
  population compensate for the absence of a physical driver"). Isso é bom.
- **O que falta:** nenhum documento reporta a decomposição de variância, o
  cancelamento E × V, nem a dominância efetiva do perigo.
- A inconsistência de metadados sobre `Hazard_Index_mun` (AUD-17 #3) é a única
  divergência formal, e está rastreada em AUD-11.

## 7. Explicações alternativas plausíveis

1. **A dominância do perigo é o comportamento desejado.** Um índice de risco
   costeiro **deve** ser conduzido pelo perigo físico; se o perigo estiver
   correto, 51 % é apropriado e não constitui problema.
2. **O cancelamento E × V pode ser um fato social, não um artefato.** No Brasil,
   população e privação de fato se anticorrelacionam na zona costeira. O índice
   está capturando a realidade: cidades grandes são menos vulneráveis
   socialmente. Suprimir isso seria distorcer o dado.
3. **A compressão de variabilidade é uma propriedade conhecida da média
   geométrica** com componentes anticorrelacionadas, e é preferível à alternativa:
   uma média aritmética permitiria que população alta compensasse a ausência de
   perigo — o cenário que a escolha geométrica existe para evitar.
4. **A inversão perigo → risco é o resultado científico do trabalho, não um
   defeito.** Que o risco social máximo não coincida com o perigo físico máximo é
   uma descoberta com consequência direta de política pública. **Isso só se
   sustenta se o perigo no Norte for válido** — daí a dependência de AUD-01.

## 8. Diagnósticos propostos

> **Situação em 2026-07-31.** Os seis diagnósticos abaixo foram propostos contra
> o produto superseded. Desfecho de cada um:
>
> | # | Situação | Razão |
> |---|---|---|
> | 1 | **Executado**, contra o produto atual | §3-bis; script versionado |
> | 2 | **Executado com escala trocada** | Em log era indefinido com 84 zeros; feito em desvios padronizados sobre os 196 (§3-bis.9) |
> | 3 | **Não executado** | Figura de barras empilhadas; o CSV de contribuições a torna dispensável para o fechamento, e a figura do artigo já apresenta as três camadas (§4) |
> | 4 | **Executado, e mudou de estatuto** | Era contrafactual inerte (ρ = 0,934); virou o teste mais informativo do conjunto (ρ = 0,550) |
> | 5 | **Executado** — é o que esta reescrita inteira faz | AUD-01 fechou; AUD-02 segue aberta, e a consequência está declarada na §9 |
> | 6 | **Executado**, e revelou que o par relevante é outro | §3-bis.6: E × V comprime 9 %, H × V comprime por fator 3 |
>
> **Diagnóstico novo, não previsto na lista original e indispensável ao
> fechamento:** a mecânica do campo de perigo (§3-bis.8). Sem ela não é possível
> julgar se a dominância do perigo é apropriada.

1. **Consolidar as tabelas §3.1 a §3.6 em produto versionado** —
   `src/exploratory/audit_AUD_13_component_contributions.py` →
   `outputs/audit/AUD-13_component_contributions/`.
2. **Decomposição por município**: para cada um, a contribuição de cada
   componente a log(`Risk_Hazard_raw`) em relação à mediana, permitindo dizer
   "Icatu é 1º porque V está 0,63 desvios acima e H 0,21 acima". Isso alimenta
   diretamente a tabela de hotspots do manuscrito e a suíte de AUD-05.
3. **Figura de contribuição** — gráfico de barras empilhadas das três
   contribuições para os 20 primeiros e os 20 últimos municípios.
4. **Testar a média aritmética** como contrafactual e reportar a diferença
   (ρ = 0,934, top-20 = 11/20 já medidos), documentando o que a escolha
   geométrica efetivamente muda.
5. **Repetir toda a análise após AUD-01 e AUD-02**, para verificar se a
   dominância do perigo e a composição regional do top-N mudam.
6. **Quantificar o efeito do cancelamento**: comparar a variância de
   log(`Risk_raw`) observada com a que existiria se E e V fossem independentes
   (mesmas marginais, correlação zero, por embaralhamento).

## 9. Critérios objetivos de resolução

### 9.1 Critérios de 2026-07-29 — situação de cada um

Nenhum foi apagado. Um critério cujo problema original deixou de existir **não é
automaticamente satisfeito**: é anulado, e a anulação precisa da razão.

| # | Critério original | Situação em 2026-07-31 |
|---|---|---|
| 1 | Decomposição de variância (51/27/22) publicada | **ANULADO e reconduzido.** Os três números são do produto superseded, e a decomposição em log é **indefinida** com 84 zeros. Substituído pelo critério A da §9.2 |
| 2 | Cancelamento E × V (ρ = −0,588) reportado, com efeito quantificado | **ANULADO e reconduzido.** O par mede hoje 9 % de compressão e deixou de ser o mecanismo relevante. Substituído pelo critério C da §9.2, sobre H × V |
| 3 | Correlações parciais (0,845 e 0,795) reportadas | **[x] MANTIDO e satisfeito.** Continuam altas (0,890 / 0,753 / 0,790) e seguem sendo argumento a favor do método — agora com peso maior, porque coexistem com um marginal negativo. §3-bis.4 |
| 4 | Decomposição por município para os 20 primeiros e 20 últimos | **[x] SATISFEITO com escala trocada.** Em log seria indefinido; feito em desvios padronizados sobre os 196, para todos, não só 40. §3-bis.9 |
| 5 | Inversão perigo → risco explicada mecanicamente | **SEM OBJETO.** Não há mais inversão: o top-20 do risco é 20/20 S/SE. O que exige explicação mecânica é a **censura latitudinal** que a substituiu. Reconduzido ao critério D da §9.2 |
| 6 | Manuscrito declara que pesos iguais ≠ contribuição igual | **[x] MANTIDO e satisfeito.** §3-bis.2 e o parágrafo de limitação |
| 7 | Análise refeita após AUD-01 e AUD-02 | **[x] PARCIAL, e declarado.** Refeita após AUD-01 (fechada). **AUD-02 segue aberta**, e a consequência está no critério E da §9.2 |

### 9.2 Critérios vigentes (2026-07-31)

- [x] **A.** A decomposição de contribuições está versionada e reproduzível, com
      a restrição amostral declarada. *`outputs/audit/AUD-13_component_contributions/`;
      perigo 84,7 %, exposição 35,0 %, vulnerabilidade −19,7 %, sobre os 196 com
      risco positivo, com a impossibilidade sobre os 280 registrada no
      `summary.json` e na §3-bis.1.*
- [x] **B.** Está reportado que a correlação **marginal** entre vulnerabilidade
      e risco é **negativa** (−0,372), e que isso **não** significa que a
      vulnerabilidade reduza o risco. *§3-bis.3 e §3-bis.4: é supressão, e a
      explicação é a anticorrelação perigo–vulnerabilidade.*
- [x] **C.** O cancelamento estruturalmente dominante está identificado e
      quantificado. *§3-bis.6: H × V comprime a variância por um fator de 3,
      contra 9 % de E × V. Declarado que os dois têm naturezas distintas.*
- [x] **D.** A concentração do perigo no S/SE tem explicação mecânica, e não
      apenas descritiva. *§3-bis.8: o portão HAT cresce de 0,49 m a 2,61 m para
      o norte por razões de maré, contra um forçante que enfraquece na mesma
      direção; 208 dos 808 pontos sem evento aceito.*
- [x] **E.** Está declarado que a dominância do perigo (ρ = 0,893; sem o perigo
      ρ = +0,092) **propaga** as limitações das questões que governam o perigo,
      nomeadamente **AUD-02, que permanece aberta**. *Parágrafo de limitação do
      manuscrito e §14 abaixo.*
- [x] **F.** Está declarado que parte da anticorrelação perigo–vulnerabilidade é
      **produzida pela geografia do portão**, e não apenas pelo clima de
      tempestades. *§14 e parágrafo de limitação. É a ressalva que um revisor
      obtém plotando HAT contra latitude.*
- [x] **G.** A sensibilidade à escolha de agregação está medida e reportada, com
      a justificativa da escolha conjuntiva declarada **independentemente** do
      resultado que produz. *§3-bis.5: aritmética dá ρ = 0,550 e top-10 4/10. A
      justificativa IPCC é anterior à mudança de método e está em
      `export_risk_index_data.py::integrated_risk_formula.rationale`.*
- [ ] **H.** *(remetido, não pendente aqui)* A rotulagem dos 84 municípios em
      zero exato como categoria própria nos mapas e legendas. **Pertence a
      AUD-15**, que a registra como critério aberto desde 2026-07-31. Não
      bloqueia AUD-13.

## 10. Riscos de alteração prematura

- **Reponderar as componentes para igualar as contribuições efetivas** parece
  atraente mas é circular: os pesos passariam a depender da dispersão observada,
  tornando o índice dependente do domínio amostral de uma forma nova e pior
  (interage com AUD-11).
- **Trocar para média aritmética** destrói a propriedade conjuntiva que é o
  fundamento IPCC declarado do índice.
- **"Corrigir" o cancelamento E × V** — por exemplo, ortogonalizando as
  componentes — introduziria uma transformação difícil de interpretar e afastaria
  o índice de qualquer referencial estabelecido.

Esta questão provavelmente fecha como `resultado-validado-mantido` acompanhado de
documentação nova, sem alteração de código.

## 11. Condições sob as quais o resultado atual pode ser mantido

Muito provável. Basta que:

1. As tabelas de contribuição sejam publicadas;
2. A dominância do perigo seja declarada e defendida como apropriada;
3. O cancelamento E × V seja discutido como propriedade estrutural do Brasil
   costeiro, não escondido;
4. AUD-01 e AUD-02 tenham desfecho que valide o perigo, ou o manuscrito declare
   explicitamente que a dominância do perigo propaga a limitação daquelas
   questões.

## 12. Produtos a jusante que exigiriam regeneração

Nenhum, se a resolução for documental. Se a fórmula mudar, cadeia de AUD-11 §12.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_13_component_contributions.py`, `outputs/audit/AUD-13_component_contributions/`. **Alterados:** este registro (§3-bis, §8, §9, §13, §14), `README.md` (parágrafo de limitação), `docs/scientific_audit/ISSUE_TRACKER.md` | Diagnóstico + documentação. **Nenhum valor numérico publicado alterado; nenhuma mudança de fórmula, de associação ou de figura** |

## 14. Histórico de investigação

*Os resultados da §3 foram produzidos no diagnóstico de linha de base de
2026-07-29, com scripts ad hoc não versionados.*

### 2026-07-31 — Remedição contra o produto atual; a questão mudou de objeto

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | As duas propriedades estruturais que motivaram AUD-13 — dominância do perigo e cancelamento E × V — continuam válidas depois do portão HAT, da remoção da cadeia de Min–Max e do piso, e da exposição por população efetiva? |
| **Dados e métodos** | `site/public/data/risk_index_municipalities.geojson` (280 com risco, 196 com risco positivo) e `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv` (808 pontos). Decomposição de variância, correlações de posto marginais e parciais, contrafactuais de agregação, e teste de embaralhamento por par com marginais preservadas (2000 sorteios, semente 13). Acrescentada a estratificação do portão HAT por faixa de latitude, que a lista de diagnósticos original não previa |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_13_component_contributions` |
| **Novas saídas geradas** | `outputs/audit/AUD-13_component_contributions/{component_behaviour.csv, rank_correlations.csv, aggregation_contrafactuals.csv, hazard_gate_latitude_gradient.csv, municipality_contributions.csv, summary.json}` |
| **Achados** | (a) **A dominância do perigo deixou de ser dominância e virou identidade**: 51,0 % → **84,7 %** da variância de log(risco); ρ(H, risco) = 0,893; removendo o perigo da fórmula, ρ = **−0,223** sobre os 280 e **+0,092** sobre os 196 — sem o perigo não sobra ranking. (b) **A correlação marginal da vulnerabilidade com o risco trocou de sinal**, de +0,297 para **−0,372**, enquanto a parcial permanece **+0,790**: é supressão, não degenerescência. (c) **O cancelamento trocou de par**: E × V comprime a variância em 9 % (razão 0,911), H × V comprime por um **fator de 3** (razão 0,332). (d) **A inversão perigo → risco desapareceu**: o top-20 do risco é 20/20 S/SE, contra 15/20 no N/NE antes. (e) **O mecanismo é o portão HAT**, monotônico em latitude: o HAT médio vai de 0,49 m (35–28°S) a 2,61 m (2°S–7°N), enquanto o forçante enfraquece na mesma direção; 208 dos 808 pontos ficam sem evento aceito, e AL, SE, CE, PE e RN quase inteiros vão a perigo zero. (f) **A instabilidade de AUD-07 migrou de eixo**: "só frequência" foi de ρ = 0,384 para 0,940, enquanto aritmética contra geométrica foi de 0,934 para **0,550**. (g) **O diagnóstico central pedido pela §8.1 é indefinido** sobre a amostra completa: log(0) em 84 municípios |
| **Interpretação** | A questão deixou de ser a que foi criada. Ela nasceu para descrever o comportamento de um índice em que três camadas contribuíam de forma desigual mas todas contribuíam; hoje descreve um índice que é, operacionalmente, o índice de perigo modulado por exposição e vulnerabilidade. A fórmula não mudou — mudou o campo de perigo, que se tornou quase binário, e a média geométrica pondera pela dispersão logarítmica, de modo que a álgebra apenas propagou a física do detector. **O resultado é defensável e é um achado real**: o perigo composto onda–sobrelevação no Brasil concentra-se onde a vulnerabilidade social é menor, porque o forçante é extratropical e o S/SE é o setor mais desenvolvido do país. A ressalva que não pode ser omitida é que **parte da anticorrelação H × V é produzida pela geografia do próprio portão** — a amplitude de maré cresce para o norte por razões independentes do clima de tempestades —, de modo que a direção do achado está correta mas sua magnitude está inflada pelo método |
| **Alterações implementadas** | Nenhuma em código de produção, fórmula, associação, produto ou figura. Script diagnóstico novo, reescrita deste registro, parágrafo de limitação no `README.md` |
| **Validação realizada** | O script reproduz, a partir dos produtos publicados, todos os números citados na §3-bis, e grava `summary.json` com a restrição amostral declarada explicitamente. A contagem de 84 zeros e de 196 positivos confere com `risk_zero_cause` e `coverage_status` do GeoJSON, e com a recontagem independente de AUD-15 |
| **Incerteza remanescente** | (1) **AUD-02 permanece aberta**, e com ρ(H, risco) = 0,893 o índice propaga integralmente qualquer fragilidade do limiar de onda. (2) A decomposição de variância sobre a amostra completa continua impossível enquanto houver zeros exatos; nenhuma escala alternativa foi adotada como padrão. (3) A separação entre "forçante genuinamente mais fraco" e "barra mais alta por maré maior" na anticorrelação H × V **não foi quantificada** — exigiria um contrafactual com portão de amplitude fixa, que não foi executado |
| **Próxima decisão necessária** | Nenhuma nesta questão. A rotulagem dos 84 municípios em zero pertence a AUD-15; a validade do limiar de onda, a AUD-02; a declaração de domínio, a AUD-18 |

### 2026-07-31 — DECISÃO: fechar como `resultado-validado-mantido`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31, sobre a remedição acima |
| **Decisão** | **Nenhuma alteração no produto.** O comportamento do índice é aceito como resultado científico: no Brasil, o perigo composto concentra-se onde a vulnerabilidade social é menor. A questão fecha com documentação, sem mudança de fórmula, de agregação ou de escopo |
| **Fundamentação sobre o caso de Recife** | O caso que mais expõe o desfecho é Pernambuco, com 12 de 13 municípios em perigo zero, Recife incluída. O pesquisador apresentou três argumentos, todos aceitos: **(i)** os processos erosivos ali têm forte componente antrópica — Rocha (2018) atribui a degradação do sistema de dunas frontais de Boa Viagem primariamente a ação humana mal planejada; **(ii)** o sinal é heterogêneo praia a praia, enquanto este trabalho analisa um forçante de larga escala — Gregório et al. (2017) medem, em 48 anos na mesma orla contígua de Pina e Boa Viagem, **tendências de sinal oposto entre setores adjacentes** (setor B progradando 2,5 m/ano em 1960–1974 enquanto A, C e D recuavam), concluindo que "não há relação linear"; a escala em que o sinal de Recife se organiza está **abaixo** da célula do WAVERYS (~0,2°) e do GLORYS12 (1/12°); **(iii)** há ocupação abundante abaixo da cota de preamar de sizígia, de modo que o dano ali começa por planejamento urbano em marés ordinárias, e não pelo evento composto que este índice detecta |
| **Ressalva registrada, e aceita** | O argumento (iii) sustenta a decisão **e** delimita o que o produto tem licença para afirmar. Se a ocupação está abaixo do HAT, então **o limiar de dano local está abaixo do portão**, e o zero de Recife é uma propriedade do limiar escolhido, não a ausência de perigo costeiro. As duas leituras são simultaneamente verdadeiras. O produto já registra a causa corretamente — o GeoJSON publica `risk_zero_cause = hazard_zero_no_accepted_event_1993_2025` —, e o manuscrito deve usar essa formulação, nunca "risco zero" sem qualificação |
| **Referências incorporadas** | Gregório, M. N.; Araújo, T. C. M.; Mendonça, F. J. B.; Gonçalves, R. M.; Mendonça, R. L. (2017). Mudanças posicionais da linha de costa nas praias do Pina e de Boa Viagem, Recife, PE, Brasil. *Tropical Oceanography*, 45(1). DOI 10.5914/tropocean.v45i1.15200 · Rocha, J. I. C. (2018). Alterações nas dunas da Praia de Boa Viagem — Recife (PE) originadas por Ação Antrópica. *Investigaciones Geográficas*, 56, 138–152. DOI 10.5354/0719-5370.2018.48066 |
| **Fonte não verificada** | O pesquisador indicou um terceiro trabalho (`pdfs.semanticscholar.org/efc3/1cb024a9b588cba0b2826a3213c29b711375.pdf`). **Não foi lido**: o ambiente desta sessão não tem extrator de PDF instalado. Nenhuma afirmação deste registro se apoia nele; se for citado no manuscrito, precisa ser conferido |
| **O que o desfecho NÃO cobre** | (1) A rotulagem dos 84 zeros nos mapas — **AUD-15**. (2) A validade do limiar de onda, que o índice propaga integralmente — **AUD-02, aberta**. (3) A declaração de domínio de validade do detector — **AUD-18, aberta**. Fechar AUD-13 não fecha nenhuma das três, e o parágrafo de limitação diz isso |
