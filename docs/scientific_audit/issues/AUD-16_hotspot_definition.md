# AUD-16 — Ausência de definição operacional de "hotspot"; classes de intervalo igual arbitrárias

| Campo | Valor |
|-------|-------|
| **ID** | AUD-16 |
| **Tipo** | `risco-interpretacao` |
| **Componente** | integração |
| **Etapa do fluxo** | Step 4.4 / 4.5 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | P2 |
| **Bloqueia publicação?** | Não — a definição operacional passou a existir e está declarada |
| **Status** | `resolvido` |
| **Desfecho** | `resultado-validado-mantido` |
| **Depende de** | AUD-11 *(resolvida)* |
| **Bloqueia** | — |
| **Relacionado a** | AUD-04, AUD-05, AUD-07, AUD-13, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §2.1 (parágrafo final), §8 item 13, §9.1 lista de verificação |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (medição e fechamento) |

---

## 1. Problema

O objetivo declarado do trabalho é "identify priority hotspots for adaptation
planning". Não existe definição operacional de hotspot no repositório:

- as classes publicadas são **oito intervalos iguais** em [0, 1], fixados no
  código, sem relação com a distribuição observada;
- as tabelas do artigo usam simplesmente **"top-10"**, sem critério de corte,
  sem limiar percentílico, sem quebra natural, sem teste de significância.

## 2. Por que importa cientificamente

"Top-10" é uma escolha de apresentação, não um resultado. Um leitor não sabe se o
11º município é substancialmente diferente do 10º, ou se o corte é arbitrário. Os
dados mostram que é arbitrário: 80 municípios caem na classe (0,625; 0,750] e 65
na classe (0,500; 0,625] — a distribuição é unimodal e não tem quebra natural em
lugar nenhum próximo ao 10º colocado.

Consequências:

- a recomendação de política pública ("priorizar estes dez municípios") não tem
  base estatística;
- combinado com a instabilidade documentada em AUD-07 (o top-5 muda inteiramente
  sob agregação alternativa) e com a ancoragem de escala de AUD-11, o corte
  torna-se indefensável;
- classes de intervalo igual sobre um índice cuja escala é definida por Min–Max
  dão a impressão falsa de que os limites de classe têm significado absoluto.

## 3. Evidência original

> **Desatualizada em 2026-07-31 — não usar como está.** Toda esta seção é do
> produto anterior, em que o risco ocupava 0–1 por Min–Max. Hoje ocupa
> **0–0,566**, as classes de `FIXED_BOUNDARIES["Risk_Hazard"]` **já foram
> alteradas** no código para `[0, 1e-6, 0,1 … 0,6]`, e a premissa central da
> §3.1 — "distribuição unimodal, nenhuma quebra natural" — **caiu**: existe hoje
> uma massa de **84 municípios em zero exato**, que é uma quebra natural
> genuína.
>
> Duas evidências novas, ambas de 2026-07-31, precisam entrar antes de qualquer
> definição de hotspot:
>
> - **De AUD-07** — o bootstrap sobre os 33 anos dá intervalo de 90 % com
>   largura mediana de 4,5 posições no top-10, mas **8 municípios têm intervalo
>   cobrindo a posição 10**: o corte de top-10 não separa nada. E a fronteira
>   zero/não-zero é instável — 94 municípios caem a zero em alguns sorteios,
>   restando **102 dos 280 robustamente não nulos**. Qualquer definição por
>   percentil ou por corte muda de significado sob essa instabilidade.
> - **De AUD-13** — o índice é conduzido pelo perigo (84,7 % da variância de
>   log), de modo que um "hotspot" definido sobre o risco é, na prática, um
>   hotspot de perigo.
>
> O diagnóstico §8.3 (Getis-Ord Gi\*) também precisa ser reavaliado: com 84
> empates exatos em zero, a autocorrelação espacial mede em parte a geografia da
> censura pelo portão HAT, não agrupamento de risco.

### 3.1 Distribuição nas classes publicadas

`FIXED_BOUNDARIES["Risk_Hazard"]` = `[0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]`:

| classe | n de municípios |
|---|---|
| (0,000; 0,125] | 3 |
| (0,125; 0,250] | 10 |
| (0,250; 0,375] | 26 |
| (0,375; 0,500] | 47 |
| (0,500; 0,625] | 65 |
| (0,625; 0,750] | **80** |
| (0,750; 0,875] | 39 |
| (0,875; 1,000] | 10 |

Distribuição unimodal com moda na sexta classe. **Nenhuma quebra natural**
coincide com um limite de classe.

### 3.2 Estatísticas do índice

De `site/public/data/risk_index_metadata.json` → `numeric_stats`:

| campo | count | mín | máx | média | mediana |
|---|---|---|---|---|---|
| `Risk_Hazard` | 280 | 0,000 | 1,000 | 0,5876 | 0,6160 |
| `Risk_Hazard_raw` | 280 | 0,0924 | 0,7185 | 0,4603 | 0,4780 |

### 3.3 O corte de top-10 na prática

`outputs/article_figures/tables/top10_municipalities_by_integrated_risk.csv`:

| posição | município | `Risk_Hazard` |
|---|---|---|
| 1 | Icatu/MA | 1,000 |
| ... | | |
| 10 | Salvaterra/PA | 0,879 |

O 11º e o 12º (Vigia/PA 0,870 e Duque de Caxias/RJ 0,861) estão a 0,009 e 0,018
do 10º. **A diferença entre o 10º e o 11º é menor que o deslocamento de 0,043
induzido pela remoção de um único município** (AUD-11 §3.2). Ou seja, o corte de
top-10 é menos estável que o ruído de ancoragem da escala.

### 3.4 As classes do perigo têm o mesmo problema *(ver §3-bis: a objeção caiu)*

`FIXED_BOUNDARIES` aplica os mesmos oito intervalos iguais a `Hazard_Index`,
`Hazard_Frequency`, `Hazard_Duration`, `Hazard_Intensity` e — em escala 0–100 —
a `SVI_Coast_2022`.

---

## 3-bis. Evidência sobre o produto atual (2026-07-31)

Gerada por `src/exploratory/audit_AUD_16_hotspot_definition.py` →
`outputs/audit/AUD-16_hotspot_definition/`. Fontes:
`site/public/data/risk_index_municipalities.geojson` (280 municípios, geometria
inclusa) e `outputs/audit/AUD-07_aggregation_sensitivity/rank_confidence_intervals.csv`.

### 3-bis.1 Não existem hotspots discretos — e a evidência é dupla

Teste de unimodalidade de **Silverman (1981)**, por largura de banda crítica com
500 reamostragens. `diptest` não está disponível neste ambiente e o teste de
Silverman foi implementado no próprio script, em vez de acrescentar dependência
a um repositório de artigo.

| amostra | n | largura crítica | **p** | conclusão |
|---|---|---|---|---|
| todos | 280 | 0,0930 | **0,002** | unimodalidade **rejeitada** |
| risco > 0 | 196 | 0,0279 | **0,556** | unimodalidade **não rejeitada** |

Os dois resultados juntos dizem uma coisa só: **a distribuição é bimodal, mas o
segundo modo é a massa em zero, não um agrupamento de municípios de alto risco.**
Entre os municípios com algum evento aceito, o risco varia de forma contínua e
unimodal.

Fisher–Jenks (por *k*-médias unidimensional) confirma — a bondade de ajuste de
variância sobe suavemente, **sem cotovelo em nenhum k**:

| k | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| GVF | 0,678 | 0,832 | 0,903 | 0,929 | 0,949 | 0,965 | 0,974 |

**A alternativa §7.3 deste registro — "a ausência de quebra natural pode ser o
resultado" — deixa de ser especulação e passa a ser medida.**

### 3-bis.2 A única quebra genuína é o zero, e ela não é uma classe de gradiente

A massa de **84 municípios em zero exato** é a única descontinuidade da
distribuição. Ela não é o degrau mais baixo de um gradiente: significa *nenhum
evento composto aceito em 1993–2025*. O esquema publicado já a isola como classe
própria.

### 3-bis.3 A rota recomendada pelo §8.3 está indisponível

O registro chamava Getis-Ord Gi\* de "definição padrão na literatura e rota
recomendada", com ressalva sobre a pseudo-replicação de AUD-04. A ressalva,
quantificada:

| | valor |
|---|---|
| municípios | 280 |
| pontos de grade distintos | **178** |
| municípios no mesmo ponto (máximo) | **9** |
| pares de vizinhança por contiguidade | 650 |
| **pares de vizinhos que compartilham o mesmo ponto** | **32,6 %** |
| I de Moran global do risco | 0,813 |

Um terço da estrutura de adjacência tem perigo **idêntico por construção**. Gi\*
mediria a geometria da associação tanto quanto o campo de risco. Como AUD-04
fechou como `limitacao-reconhecida`, a rota não se abre — é um resultado
negativo, não uma pendência.

### 3-bis.4 A definição defensável vem do intervalo, não do valor

Diagnóstico §8.4, executável pela primeira vez com os intervalos de AUD-07.
Hotspot = município cujo **IC de 90 % permanece dentro das N primeiras
posições** sob reamostragem dos 33 anos de registro:

| N | municípios robustos | do top-N publicado |
|---|---|---|
| 10 | **7** | 7 de 10 |
| 20 | **14** | 14 de 20 |
| 30 | 22 | 22 de 30 |
| 50 | 33 | 33 de 50 |

**Nenhum município fora do top-N publicado é robustamente top-N.** A lista
publicada não perde ninguém — apenas contém membros que não se sustentam: 3 no
top-10 e 6 no top-20. É uma definição fundamentada, sem limiar arbitrário sobre
o valor.

### 3-bis.5 A objeção às classes de intervalo igual caiu

O §2 objetava que intervalos iguais sobre escala definida por Min–Max dão falsa
impressão de significado absoluto. **AUD-11 removeu o Min–Max**: a escala é de
âncora fixa e os limites valem igual na próxima regeneração. Distribuição sob os
três esquemas:

| esquema | contagens por classe |
|---|---|
| **intervalos iguais publicados** (0 isolado) | 84 · 1 · 41 · 72 · 63 · 17 · 2 |
| quantis dos positivos | 124 · 39 · 39 · 39 · 39 |
| Fisher–Jenks k = 4 | 130 · 62 · 60 · 27 |

Jenks recolocaria os limites a cada regeneração — o risco que o §10 adverte — e
não tem *k* preferencial, já que o GVF não tem cotovelo. Quantis sobre a amostra
completa são degenerados abaixo do percentil 30, porque 30 % dos valores são
exatamente zero.

### 3-bis.6 Sensibilidade ao corte

| regra | n selecionado | limiar |
|---|---|---|
| top-5 / 10 / 20 / 30 / 50 | 5 / 10 / 20 / 30 / 50 | 0,441 / 0,430 / 0,396 / 0,371 / 0,342 |
| p90 / p95 / p99 dos 280 | 28 / 14 / 3 | 0,373 / 0,408 / 0,449 |
| p90 / p95 / p99 dos 196 positivos | 20 / 10 / 2 | 0,395 / 0,428 / 0,470 |

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/site/export_risk_index_data.py` | `FIXED_BOUNDARIES` L461–468 | Oito intervalos iguais para seis camadas |
| `src/site/export_risk_index_data.py` | `_nice_boundaries()` L236–270 | Limites arredondados para camadas sem limites fixos |
| `src/site/export_risk_index_data.py` | `_current_available_layers()` L471–493 | Aplica os limites e as cores |
| `src/04_risk_integration/palettes.py` | `risk_colors()` | Paleta discreta compartilhada |
| `src/figures_article/make_article_top10_municipality_tables.py` | — | Gera as tabelas de top-10 |
| `src/04_risk_integration/coastal_projection.py` | — | Camadas costeiras usam as mesmas classes discretas |

### Saídas

- `site/public/data/risk_index_metadata.json` → `available_layers[].boundaries`
- `site/public/data/coastal_hazard_metadata.json` → limites de classe por camada
- `outputs/article_figures/tables/top10_municipalities_by_{integrated_risk,hazard,svi}.{csv,tex}`

### Figuras afetadas

Todas as figuras com legenda discreta:
`hazard_vulnerability_risk_multiplot.png`,
`supplementary_integrated_risk_zooms.png`,
`coastal_hazard_index_components.png`.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Oito intervalos iguais fixos; "hotspot" = os dez primeiros da lista ordenada |
| **Pretendido** | Um critério declarado que responda: *a partir de que valor um município é hotspot, e por quê?* |

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` menciona "priority hotspots" no Objetivo Geral, no Objetivo
  Específico 7 e no resumo, **sem nunca definir o termo**.
- As legendas das tabelas de artigo dizem "Top 10 Brazilian coastal
  municipalities by normalized integrated compound-risk index" — o que é
  descritivamente honesto, mas o texto do manuscrito provavelmente usará
  "hotspot".
- Código e saídas concordam. A lacuna é conceitual e documental.

## 7. Explicações alternativas plausíveis

1. **"Top-10" é uma convenção de apresentação aceitável** em trabalhos de
   priorização, desde que apresentado como tal e não como classe estatística.
2. **Intervalos iguais são a escolha cartográfica padrão** para índices
   normalizados 0–1 e têm a vantagem de serem imediatamente legíveis. Quebras
   naturais (Jenks) mudam a cada regeneração, o que prejudica a comparabilidade
   entre figuras.
3. **A ausência de quebra natural pode ser o resultado.** Se o risco costeiro
   brasileiro varia continuamente, sem agrupamentos, então **não existem
   hotspots discretos** — e essa é uma conclusão científica legítima e
   interessante, que o trabalho poderia afirmar.
4. **Um critério percentílico é igualmente arbitrário.** Escolher o decil
   superior não é mais fundamentado que escolher os dez primeiros; apenas
   escala com o tamanho do conjunto.

## 8. Diagnósticos propostos

1. **Testar a existência de agrupamentos** na distribuição de `Risk_Hazard`:
   estimativa de densidade por kernel, teste de unimodalidade (dip de Hartigan),
   e classificação por quebras naturais de Jenks com número de classes variável.
   *Saída esperada:* determinar se existem hotspots discretos ou se a distribuição
   é contínua.
2. **Sensibilidade ao corte**: para N ∈ {5, 10, 15, 20, 30, 50} e para os
   percentis 90, 95, 99, listar os municípios selecionados e medir a estabilidade
   sob as variantes de agregação de AUD-07.
3. **Autocorrelação espacial**: aplicar Getis-Ord Gi* ou LISA sobre
   `Risk_Hazard` com a matriz de vizinhança municipal, o que dá uma definição de
   hotspot **estatisticamente fundamentada** — agrupamentos espaciais
   significativos, não apenas valores altos. *Esta é a definição padrão de
   "hotspot" na literatura de análise espacial e é a rota recomendada.*
   **Atenção:** a pseudo-replicação de AUD-04 (178 pontos para 280 municípios)
   inflaciona artificialmente a autocorrelação e precisa ser considerada.
4. **Combinar com os intervalos de confiança** do bootstrap de AUD-07: definir
   hotspot como município cujo limite inferior do intervalo de confiança excede
   um limiar.
5. **Comparar intervalos iguais, quantis e Jenks** quanto ao mapa resultante.

## 9. Critérios objetivos de resolução

- [x] Existe um teste de unimodalidade/agrupamento da distribuição de
      `Risk_Hazard`, com resultado reportado. *Silverman por largura de banda
      crítica, 500 reamostragens: p = **0,002** sobre os 280 (rejeita) e
      **0,556** sobre os 196 positivos (não rejeita). Fisher–Jenks sem cotovelo,
      GVF de 0,678 a 0,974. §3-bis.1.*
- [x] Existe uma definição operacional de "hotspot" declarada no manuscrito, com
      justificativa. *Por **intervalo de confiança**, não por percentil nem por
      autocorrelação: município cujo IC de 90 % permanece dentro das N primeiras
      posições sob reamostragem dos 33 anos. Sete a N = 10, catorze a N = 20.
      Declarada no glossário do `README.md`, em `site/content/project.ts` e em
      `site/content/results.ts`. §3-bis.4.*
- [x] Se a distribuição for contínua e sem agrupamentos, o manuscrito **afirma
      isso** em vez de impor um corte, e apresenta o resultado como gradiente de
      prioridade. *Afirmado nas três superfícies acima: gradiente contínuo de
      prioridade, com a única quebra genuína sendo a massa de 84 municípios em
      zero — que é uma declaração sobre o registro, não a classe mais baixa de um
      gradiente.*
- [x] A sensibilidade ao corte está reportada. *§3-bis.6 e
      `cut_sensitivity.csv`, com a lista nominal dos selecionados por regra para
      N ∈ {5, 10, 15, 20, 30, 50} e percentis 90/95/99, sobre a amostra completa
      e sobre os positivos.*
- [x] As classes cartográficas estão justificadas, ou substituídas.
      **Justificadas, e a objeção original caiu.** *O §2 objetava a intervalos
      iguais sobre escala de Min–Max; AUD-11 removeu o Min–Max e a escala passou
      a ter âncora fixa, de modo que os limites valem igual na próxima
      regeneração. O zero já é classe própria. Jenks foi comparado e recusado:
      recolocaria os limites a cada regeneração — o risco do §10 — e não tem k
      preferencial. §3-bis.5.*
- [x] Nenhuma afirmação do tipo "os dez principais hotspots são X" aparece sem
      referência à instabilidade documentada em AUD-07. *A definição adotada **é**
      a de AUD-07; e a legenda de `top10_municipalities_by_integrated_risk.tex`
      já declara que as posições 4–11 não se distinguem.*
- [x] **Critério novo.** A rota Getis-Ord Gi\* do §8.3 está **avaliada e
      registrada como indisponível**, com número, e não deixada como pendência.
      *32,6 % dos pares de vizinhança compartilham o mesmo ponto de grade — 178
      pontos para 280 municípios, até 9 por ponto — logo têm perigo idêntico por
      construção. Gi\* mediria a geometria da associação. Depende de AUD-04, que
      fechou como `limitacao-reconhecida`. §3-bis.3.*

## 10. Riscos de alteração prematura

- **Adotar Jenks** faz os limites de classe mudarem a cada regeneração dos dados,
  quebrando a comparabilidade entre versões das figuras — problema real num
  projeto em que os dados ainda vão mudar por AUD-01/02/04.
- **Adotar Getis-Ord Gi\*** antes de resolver AUD-04 produz agrupamentos
  artificiais, porque municípios que compartilham ponto de grade têm perigo
  idêntico por construção — a autocorrelação medida seria em parte um artefato de
  pseudo-replicação.
- **Mudar o corte para produzir uma lista mais plausível** é seleção de resultado.

## 11. Condições sob as quais o resultado atual pode ser mantido

Aceitável manter intervalos iguais e top-10, se:

1. O termo "hotspot" for substituído por "municípios de maior índice" onde não
   houver critério estatístico;
2. A sensibilidade ao corte for reportada;
3. As classes forem declaradas como escolha cartográfica, não como categorias de
   risco;
4. AUD-07 fornecer os intervalos de confiança que contextualizam a lista.

## 12. Produtos a jusante que exigiriam regeneração

Se as classes mudarem:

```bash
python -m src.site.export_risk_index_data
python -m src.site.export_coastal_hazard_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_top10_municipality_tables
```

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_16_hotspot_definition.py`, `outputs/audit/AUD-16_hotspot_definition/`. **Alterados:** este registro (§3-bis, §9, §13, §14), `README.md` (glossário: definição de hotspot; parágrafo de limitação), `site/content/project.ts`, `site/content/results.ts`, `docs/scientific_audit/ISSUE_TRACKER.md` | Diagnóstico + definição declarada. **Nenhum valor numérico publicado alterado; nenhuma classe cartográfica alterada** |

## 14. Histórico de investigação

*Nenhuma investigação registrada além da contagem de classes do diagnóstico de
linha de base de 2026-07-29.*

### 2026-07-31 — Não existem hotspots discretos; a definição defensável é a de intervalo

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | A distribuição de `Risk_Hazard` tem agrupamentos discretos? Se não, que definição operacional de hotspot é defensável? E a rota Getis-Ord do §8.3 é viável? |
| **Dados e métodos** | `risk_index_municipalities.geojson` (280 com risco, geometria inclusa) e os intervalos de posto de AUD-07. Teste de unimodalidade de Silverman (1981) por largura de banda crítica com 500 reamostragens; Fisher–Jenks por *k*-médias unidimensional com GVF para k = 2…8; sensibilidade ao corte por N e por percentil; definição por intervalo; e viabilidade de autocorrelação espacial com contiguidade por interseção de polígonos. **`diptest`, `jenkspy` e `libpysal` não estão disponíveis neste ambiente**; os três procedimentos foram implementados no próprio script em vez de acrescentar dependências a um repositório de artigo |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_16_hotspot_definition` |
| **Novas saídas geradas** | `outputs/audit/AUD-16_hotspot_definition/{distribution_structure.json, jenks_classes.csv, cut_sensitivity.csv, class_scheme_comparison.csv, interval_based_hotspots.csv, summary.json}` |
| **Achados** | (a) **Não há hotspots discretos.** Silverman rejeita unimodalidade sobre os 280 (p = 0,002) e **não** rejeita sobre os 196 positivos (p = 0,556): a bimodalidade é a massa em zero, não um agrupamento de alto risco. Fisher–Jenks confirma — GVF sobe suavemente de 0,678 a 0,974 **sem cotovelo**. (b) **A única quebra genuína é o zero**, e ela não é classe de gradiente: significa nenhum evento aceito em 1993–2025. (c) **Gi\* está indisponível**: 32,6 % dos 650 pares de vizinhança compartilham o mesmo ponto de grade — 178 pontos para 280 municípios, até 9 por ponto —, com I de Moran de 0,813 sobre uma adjacência cujo terço tem perigo idêntico por construção. (d) **A definição por intervalo funciona**: 7 municípios mantêm o IC de 90 % dentro do top-10 e 14 dentro do top-20; nenhum município fora do top-N publicado é robustamente top-N, de modo que a lista publicada não perde ninguém — apenas contém 3 membros não robustos no top-10. (e) **A objeção às classes de intervalo igual caiu** com a remoção do Min–Max por AUD-11: a escala tem âncora fixa e os limites valem igual na próxima regeneração |
| **Interpretação** | A questão foi criada porque "hotspot = top-10" não é critério. A medição mostra que o problema era mais profundo do que a falta de critério: **não existe a coisa que o critério deveria delimitar**. O risco costeiro brasileiro varia continuamente entre os municípios que registram eventos, e a única fronteira real é entre registrar e não registrar. Isso é uma conclusão científica legítima — a §7.3 já a listava como possibilidade — e é mais informativa do que um corte imposto. O que resta é uma definição de **prioridade robusta**, não de agrupamento, e ela sai dos intervalos de AUD-07 sem nenhum limiar arbitrário sobre o valor |
| **Alterações implementadas** | Nenhuma em valor publicado nem em classe cartográfica. Definição de hotspot declarada no glossário do README, em `site/content/project.ts` e em `site/content/results.ts`; o termo "priority hotspots" foi trocado por "priority areas" nas definições de Risco, ficando "hotspot" reservado ao sentido operacional |
| **Validação realizada** | Os dois testes de Silverman são consistentes entre si e com o Fisher–Jenks: rejeitar sobre a amostra completa e não rejeitar sobre os positivos é exatamente o padrão esperado de uma distribuição inflada em zero. As contagens de classe reproduzem os 84 zeros e os 196 positivos, conferindo com AUD-15 e AUD-13 |
| **Incerteza remanescente** | (1) **Não foi gerada figura de KDE** — o §8.1 a sugeria; os números bastam para o fechamento, mas o manuscrito provavelmente a quer. (2) A definição por intervalo **não foi propagada às figuras nem ao site como camada**: continua sendo texto, não símbolo no mapa. (3) O teste de Silverman herda a limitação do bootstrap de AUD-07: os anos são tratados como trocáveis. (4) O I de Moran foi calculado com pesos binários de contiguidade e **não** foi corrigido para a pseudo-replicação — serve para mostrar que Gi\* é inviável, não como medida de agrupamento |
| **Próxima decisão necessária** | Do pesquisador: aceitar o desfecho, ou ir além adotando Jenks e levando a definição de intervalo ao mapa |

### 2026-07-31 — DECISÃO: fechar como `resultado-validado-mantido`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | Fechar com três declarações e **nenhuma mudança de produto**: o manuscrito afirma que não há hotspots discretos e apresenta gradiente de prioridade; a definição operacional adotada é a de intervalo (7 no top-10, 14 no top-20); a rota Getis-Ord fica registrada como indisponível, com o número, e não como pendência |
| **Não adotado, deliberadamente** | **Jenks**, porque recolocaria os limites a cada regeneração e não tem *k* preferencial; e **levar a definição de intervalo ao mapa**, que seria mudança de produto e excede o que "declarar" implica |
| **O que o desfecho NÃO cobre** | (1) A figura de KDE. (2) A propagação da definição às figuras e ao site como camada. (3) A instabilidade da fronteira zero/não-zero herdada de AUD-07 — 94 municípios caem a zero em alguns sorteios —, que permanece anotada em **AUD-15**, aberta |
