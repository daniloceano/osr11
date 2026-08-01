# AUD-07 — Instabilidade do ranking sob escolhas alternativas de agregação do perigo

| Campo | Valor |
|-------|-------|
| **ID** | AUD-07 |
| **Tipo** | `analise-sensibilidade` |
| **Componente** | perigo → integração |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | Sim — satisfeito pela publicação das tabelas de sensibilidade e dos intervalos de confiança |
| **Status** | `resolvido` |
| **Desfecho** | `resultado-validado-mantido` |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-06, AUD-11, AUD-13, AUD-15, AUD-16 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 4), §9.1 itens 4 e 5, §10 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (medição contra o produto atual e fechamento) |

---

> ### Nota de leitura — a instabilidade registrada evaporou, e outra apareceu
>
> A §3 é de 2026-07-29 e descreve um produto superseded. **Está preservada como
> está.** A evidência vigente está na **§3-bis**.
>
> O que motivou o P0 — ρ = 0,384 sob "só frequência" — **não existe mais**: hoje
> vale **0,940**. A varredura de pesos frequência↔severidade dá ρ ≥ 0,94 em toda
> a faixa, de modo que a ponderação igual também deixou de ser uma escolha
> frágil.
>
> Em lugar disso, o bootstrap sobre os anos revelou uma instabilidade de
> **natureza diferente**, que nenhum critério original cobria: da posição ~21
> para baixo o ranking é largamente decidido por **eventos únicos**. Ver
> §3-bis.4.
>
> Fechada como `resultado-validado-mantido` por decisão do pesquisador em
> 2026-07-31. Ver §14.

## 1. Problema

O ranking municipal de risco publicado **não sobrevive** a escolhas alternativas
razoáveis da agregação do perigo. Trocando apenas a definição de `Hazard_Index`
para "frequência apenas", o ρ de Spearman com o índice publicado cai para
**0,384** e o top-5 muda integralmente — de municípios do Maranhão e do Amapá
para São Sebastião, São José do Norte, Magé, Guarujá e Guaraqueçaba.

Esta questão **não pede uma correção**: pede que a instabilidade seja medida,
publicada e discutida. Um ranking instável ainda pode ser publicado — desde que a
instabilidade seja declarada.

## 2. Por que importa cientificamente

O principal resultado do trabalho, tal como apresentado nas tabelas do artigo, é
uma lista ordenada de municípios prioritários. Se essa lista depende de uma
escolha metodológica sem justificativa física forte (média aritmética de três
componentes Min–Max, pesos iguais), então:

- a ordenação específica dentro do top-10 não tem significado defensável;
- um revisor que refizer o cálculo com outra agregação obterá outra lista e
  concluirá que o resultado é arbitrário;
- a recomendação de política pública derivada da lista é frágil.

A solução científica correta não é escolher a agregação que produz o resultado
preferido, mas **publicar a tabela de sensibilidade ao lado do resultado**.

## 3. Evidência original (2026-07-29) — **sobre o produto superseded**

> **Nenhum número desta seção descreve o produto atual.** Preservada por
> rastreabilidade. A evidência vigente está na §3-bis.

Todos os testes foram executados sobre
`site/public/data/risk_index_municipalities.geojson` (280 municípios com perigo)
e `outputs/storm_catalog/compound/compound_metrics.csv` (808 pontos).

### 3.1 Sensibilidade da agregação, no nível do risco integrado

ρ = Spearman com o `Risk_Hazard` publicado; sobreposição de top-20 e top-10:

| Variante | ρ | top-20 | top-10 | top-5 resultante |
|---|---|---|---|---|
| **implementado** (geométrico H,E,V) | 1,000 | 20/20 | 10/10 | Icatu, Turiaçu, Apicum-Açu, Macapá, Axixá |
| **perigo = só frequência** | **0,384** | 6/20 | 4/10 | **São Sebastião, S. José do Norte, Magé, Guarujá, Guaraqueçaba** |
| perigo = frequência + intensidade | 0,816 | 12/20 | 4/10 | Apicum-Açu, Icatu, Turiaçu, Cururupu, Axixá |
| perigo = média geométrica de F,D,I | 0,883 | 18/20 | 7/10 | Icatu, Macapá, Magé, Maricá, Saquarema |
| componentes normalizadas por posto | 0,967 | 17/20 | 6/10 | Icatu, Macapá, Axixá, Chaves, Vigia |
| média aritmética de H,E,V | 0,934 | 11/20 | 6/10 | Icatu, Maricá, São Sebastião, Saquarema, S. Gonçalo |
| exposição por posto de `pop_10km` | 0,773 | 10/20 | 6/10 | Magé, Macapá, Turiaçu, D. de Caxias, Maricá |
| sem exposição (H × V) | 0,803 | 9/20 | 5/10 | Calçoene, Turiaçu, Icatu, C. Mendes, Bacuri |
| sem renormalização municipal do perigo | 1,000 | 20/20 | 10/10 | idêntico (Min–Max é monotônico) |
| sem piso de recorte (piso 1e-6) | 1,000 | 20/20 | 10/10 | idêntico |

### 3.2 Sensibilidade da agregação, no nível do perigo (808 pontos)

ρ com o `Hazard_Index` implementado:

| variante | ρ |
|---|---|
| só frequência | 0,594 |
| só duração | 0,110 |
| só intensidade | 0,871 |
| frequência + intensidade | 0,881 |
| média geométrica F, D, I | 0,896 |
| componentes por posto | 0,967 |
| taxa anual (`compound_count_annual_mean`) | 0,594 |

### 3.3 Deixar-uma-componente-de-fora, no risco integrado

| componente removida | ρ com o publicado | sobreposição de top-20 |
|---|---|---|
| perigo | **0,554** | 10/20 |
| exposição | 0,803 | 9/20 |
| vulnerabilidade | 0,741 | 5/20 |

### 3.4 Amplificação pela segunda normalização

`Hazard_Index_raw` ∈ [0,1468; 0,7278]; o Min–Max final multiplica o contraste por
**1,72×**. Ver AUD-11.

---

## 3-bis. Evidência sobre o produto atual (2026-07-31)

Gerada por `src/exploratory/audit_AUD_07_aggregation_sensitivity.py` →
`outputs/audit/AUD-07_aggregation_sensitivity/`. Fontes:
`site/public/data/risk_index_municipalities.geojson` (280 municípios com risco) e
`outputs/storm_catalog/compound/compound_catalog.json` (16 768 eventos com data e
severidade). O catálogo reproduz o produto publicado: contagens **idênticas** nos
808 pontos e severidade média a **6,7e-05** (arredondamento do CSV).

### 3-bis.1 O bootstrap por município do §8.2 tornou-se degenerado

O desenho original — reamostrar municípios "recalculando todas as normalizações
dentro de cada reamostra" — existia porque o Min–Max ancorava o perigo e o risco
nos próprios extremos observados, de modo que remover um município deslocava
todos os outros (AUD-11 §3.2 mediu até 0,094).

Com as âncoras fixas de AUD-11, a dependência do conjunto caiu drasticamente. Em
200 reamostragens de municípios o deslocamento máximo de posto relativo é
**exatamente 0,0**.

> **Correção de 2026-07-31 (de AUD-11).** A redação original desta seção
> concluía daí que "o valor de um município **não depende** da amostra". **É
> forte demais.** O bootstrap acima reamostra os **valores publicados sem
> recalcular `sd(PC1)`**, e portanto demonstra uma tautologia, não a propriedade.
> `sd(PC1)` **é** estimado da amostra, de modo que a vulnerabilidade — e com ela
> o risco — depende de quem está no conjunto. AUD-11 mediu: remover **um**
> município move qualquer outro em até **0,0036** (26× menos que sob Min–Max),
> mas excluir **todo o N/NE** move até **0,292** e reordena o restante a
> **ρ = 0,696**. Ver AUD-11 §14.
>
> **O que esta seção conclui continua válido**: reamostrar municípios não é o
> teste certo para a incerteza de posto deste produto, e reamostrar **anos** é.

**Reportar intervalos por esse desenho produziria "incerteza quase nula" como
artefato do desenho, não como evidência de robustez.** O critério foi
reconduzido.

### 3-bis.2 A incerteza que existe é a do estimador de perigo

O perigo estima uma taxa de eventos e uma severidade média a partir de **33 anos**
de registro. O bootstrap vigente reamostra os **anos** com reposição, reconta os
eventos aceitos por ponto a partir do catálogo evento a evento, recalcula a média
de severidade sobre os anos sorteados, e propaga ao risco municipal com exposição
e vulnerabilidade fixas. 1000 sorteios, semente 7, IC de 90 %. O script **levanta
erro** se o sorteio-identidade não reproduzir o risco publicado.

Largura mediana do intervalo de posto, por faixa da posição publicada:

| faixa | n | largura mediana | largura máxima |
|---|---|---|---|
| 1–10 | 10 | **4,5** | 8 |
| 11–20 | 10 | 7,0 | 10 |
| 21–50 | 30 | 19,0 | 118 |
| 51–100 | 50 | 26,6 | 164 |
| 101–196 | 96 | **45,0** | 124 |
| 197–280 | 84 | 70,0 | 70 |

**O topo é firme e o meio não é interpretável.** São José do Norte/RS,
Guaraqueçaba/PR e Magé/RJ ocupam as posições 1, 2 e 3 em praticamente todos os
sorteios (intervalos degenerados). Mas **8 municípios têm intervalo cobrindo a
posição 10**: as posições ~4 a 11 são intercambiáveis, e "top-10" não é um corte
nítido. Insumo direto para AUD-16.

### 3-bis.3 A sensibilidade à agregação, e à ponderação

ρ de Spearman contra o ranking publicado:

| variante | ρ agora | era |
|---|---|---|
| só frequência | **0,940** | **0,384** |
| só severidade | 0,974 | — |
| sem exposição (H × V) | 0,914 | 0,803 |
| sem vulnerabilidade (H × E) | 0,923 | 0,741 |
| perigo isolado | 0,893 | — |
| **componentes por posto percentílico** | **0,638** | 0,967 |
| **média aritmética H,E,V** | **0,551** | 0,934 |
| sem perigo (E × V) | −0,223 | 0,554 |

Varredura do peso entre as duas componentes do perigo — o §8.4 pedia um simplex
sobre **três**, e o perigo carrega **duas** desde que AUD-01/AUD-06 removeram a
duração, de modo que o simplex é um segmento:

| w_frequência | 0,0 | 0,2 | 0,4 | **0,5** | 0,6 | 0,8 | 1,0 |
|---|---|---|---|---|---|---|---|
| ρ com o publicado | 0,974 | 0,990 | 0,999 | **1,000** | 0,998 | 0,984 | 0,940 |
| top-10 preservado | 4 | 6 | 9 | **10** | 9 | 9 | 8 |

**ρ ≥ 0,94 em toda a faixa.** A ponderação igual não é uma escolha frágil — é
praticamente indiferente. A crítica "pesos iguais sem justificativa" fica
respondida por medição.

**A instabilidade remanescente está inteiramente na forma funcional**:
conjuntiva contra compensatória (0,551) e nível contra posto (0,638). Não está
na escolha nem na ponderação das componentes.

### 3-bis.4 Achado novo: da posição ~21 para baixo, o ranking é decidido por eventos únicos

Nenhum critério original cobria isto, e é o achado mais consequente da questão.

| pos | município | eventos em 33 anos | Freq | Sev | `Hazard_Index_mun` | Risco |
|---|---|---|---|---|---|---|
| 1 | São José do Norte/RS | 93 | 0,939 | 0,608 | 0,774 | 0,566 |
| 3 | Magé/RJ | 56 | 0,566 | 0,688 | 0,627 | 0,468 |
| 6 | Guarujá/SP | 70 | 0,707 | 0,547 | 0,627 | 0,438 |
| **21** | **Guimarães/MA** | **1** | 0,010 | 0,283 | 0,146 | **0,394** |
| 22 | Alcântara/MA | 1 | 0,010 | 0,237 | 0,124 | 0,394 |
| 28 | Raposa/MA | 1 | 0,010 | 0,237 | 0,124 | 0,374 |
| 32 | Icatu/MA | 1 | 0,010 | 0,204 | 0,107 | 0,368 |

**94 dos 196 municípios com risco positivo têm menos de 10 eventos aceitos; 90
têm menos de 5.** O primeiro deles é o **21º do país**.

O mecanismo é a assimetria entre as duas componentes. A frequência é ancorada em
99 eventos, então um evento vale 0,010. A severidade é uma **média condicional**
— não escala com quantos eventos a sustentam —, então um único dia moderado
devolve 0,283. A média aritmética das duas dá 0,146, e a média geométrica com
`Vulnerability_CDF_PC1` ≈ 0,98 leva Guimarães à 21ª posição do Brasil **por causa
de um único dia em 33 anos**.

Consequência medida no bootstrap: **94 municípios caem a risco exatamente zero em
alguns sorteios** — Guimarães, Alcântara, Raposa e Icatu em **34 %** deles.
Somados aos **84 sempre nulos**, apenas **102 dos 280 são robustamente não
nulos**. A fronteira zero/não-zero é ela própria amostralmente instável, o que
atinge diretamente a categoria "risco zero" de AUD-15 e a definição de hotspot de
AUD-16.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/hazard_index.py` | `derive_native_hazard_index()` L75–171 | Única implementação da agregação do perigo |
| `src/04_risk_integration/hazard_index.py` | L117–120 | `mean(axis=1, skipna=False)` seguido de `_minmax` |
| `src/04_risk_integration/hazard_index.py` | `component_weights` L145–149 | Pesos declarados nos metadados |
| `src/site/export_risk_index_data.py` | L576–583 | Média geométrica das três componentes |
| `src/exploratory/make_exploratory_hazard_index_comparison.py` | — | **Já existe** um comparador entre a definição antiga (só contagem) e a atual; é a base natural para estender a comparação |
| `src/exploratory/make_exploratory_risk_with_exposure.py` | — | Comparador de variantes de risco com exposição |
| `src/exploratory/make_exploratory_exposure_normalization.py` | — | Comparador de normalizações de exposição |

### Dados e saídas

- `outputs/exploratory_hazard_index_comparison/` — saídas existentes.
- `outputs/exploratory_exposure/exposure_normalization_summary.json` e
  `risk_with_exposure_summary.json` — comparações já feitas.
- `site/public/data/risk_index_metadata.json` → `native_hazard_index`,
  `hazard_index_normalization`, `integrated_risk_formula`.

### Figuras e tabelas afetadas

- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.*` — o
  produto diretamente instável.
- `outputs/article_figures/tables/top10_municipalities_by_hazard.*`
- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Média aritmética equiponderada de três componentes Min–Max, seguida de novo Min–Max. Nenhuma análise de sensibilidade publicada |
| **Pretendido** | Uma escolha de agregação justificada, acompanhada de tabela de sensibilidade e de intervalos de confiança sobre as posições |

## 6. Divergência documentação ↔ implementação ↔ saídas

Não há divergência: documentação, código e saídas concordam. A lacuna é a
**ausência** de análise de sensibilidade publicada, apesar de o repositório já
conter três scripts exploratórios que fazem comparações parciais
(`make_exploratory_hazard_index_comparison.py`,
`make_exploratory_risk_with_exposure.py`,
`make_exploratory_exposure_normalization.py`). Esses resultados nunca foram
consolidados em produto de artigo.

## 7. Explicações alternativas plausíveis

1. **A instabilidade pode ser esperada e aceitável.** Índices compostos são
   notoriamente sensíveis a escolhas de agregação; a literatura de indicadores
   (INFORM, IPCC) reconhece isso. O padrão da área é publicar a sensibilidade,
   não eliminá-la.
2. **A variante "só frequência" pode não ser uma alternativa razoável.** Se a
   frequência isolada é conceitualmente inferior ao índice multimétrico, o ρ =
   0,384 é irrelevante. Contra-argumento: a frequência é a componente mais
   fisicamente interpretável e a única com estrutura espacial sinótica limpa.
3. **Boa parte da instabilidade pode vir de AUD-01/AUD-02**, não da agregação: se
   o perigo do Norte for corrigido, as variantes podem convergir. **Este é o teste
   decisivo** e deve ser refeito após a resolução daquelas questões.
4. **As posições podem ser estatisticamente indistinguíveis.** Se o intervalo de
   confiança das posições for largo, "Icatu é 1º e Turiaçu é 2º" nunca teve
   significado, e a instabilidade entre variantes é apenas a manifestação disso.

## 8. Diagnósticos propostos

1. **Consolidar as tabelas §3.1 a §3.3 em um produto versionado** —
   `src/exploratory/audit_AUD_07_aggregation_sensitivity.py` →
   `outputs/audit/AUD-07_aggregation_sensitivity/` — com CSV, figura e JSON de
   resumo, aproveitando os três scripts exploratórios existentes.
2. **Bootstrap das posições**: reamostrar municípios com reposição (n = 1000),
   recalcular todas as normalizações dentro de cada reamostra, e produzir
   intervalo de confiança de 90 % para a posição de cada município.
   *Saída esperada:* saber se o top-10 é distinguível do top-30.
3. **Matriz de concordância entre variantes**: ρ de Spearman de todas as
   variantes contra todas, e índice de estabilidade de top-N para
   N ∈ {5, 10, 20, 50}.
4. **Análise de sensibilidade de pesos**: varrer os pesos das três componentes do
   perigo num simplex e mapear a região de pesos em que o top-5 permanece estável.
5. **Repetir §3.1 após AUD-01 e AUD-02** para verificar se a instabilidade
   diminui quando o perigo do Norte é corrigido.

## 9. Critérios objetivos de resolução

### 9.1 Critérios de 2026-07-29 — situação de cada um

| # | Critério original | Situação em 2026-07-31 |
|---|---|---|
| 1 | Tabela de sensibilidade da agregação versionada e no suplementar | **[x] SATISFEITO.** `variant_agreement_matrix.csv` (todas contra todas) e `variant_topn_stability.csv` (N = 5, 10, 20, 50) |
| 2 | Tabela de deixar-uma-componente-de-fora versionada | **[x] SATISFEITO.** Nas mesmas saídas, e em `outputs/audit/AUD-13_component_contributions/` |
| 3 | Intervalo de confiança por bootstrap para a posição de cada município do top-20 | **[x] SATISFEITO com o desenho trocado, e a troca é obrigatória.** O bootstrap por município que o §8.2 especifica passou a medir **exatamente zero** (§3-bis.1): com âncoras fixas, o valor de um município não depende da amostra. Reportá-lo seria publicar um artefato de desenho como robustez. Substituído por bootstrap sobre os **33 anos de registro** |
| 4 | Agregação justificada por critério declarado **antes** de observar o resultado | **[x] SATISFEITO.** A justificativa conjuntiva IPCC é anterior à mudança de método e está em `export_risk_index_data.py::integrated_risk_formula.rationale`. E a ponderação deixou de ser uma escolha: ρ ≥ 0,94 em toda a varredura (§3-bis.3) |
| 5 | Se ρ de "só frequência" < 0,6 após AUD-01/02, declarar a ordenação não robusta e apresentar faixas | **DISPARADO EM SENTIDO CONTRÁRIO — e insuficiente.** ρ subiu de 0,384 para **0,940**, portanto a condição literal não se aplica. Mas o bootstrap por anos mostrou que a ordenação **não é** interpretável abaixo da posição ~20 (§3-bis.2 e §3-bis.4), por uma razão que este critério não previa. A exigência de faixas é mantida, por outro motivo — critério F da §9.2 |
| 6 | Nenhuma tabela de top-10 publicada sem referência cruzada à sensibilidade | **[x] SATISFEITO.** A legenda de `top10_municipalities_by_integrated_risk.tex` passou a declarar que as posições 1–3 são estáveis e que os intervalos de 4–11 se sobrepõem, remetendo às tabelas suplementares. Só a legenda mudou; nenhum valor |

### 9.2 Critérios vigentes (2026-07-31)

- [x] **A.** A degenerescência do bootstrap por município está **demonstrada**, não
      assumida. *200 sorteios, deslocamento máximo de posto relativo 0,0.*
- [x] **B.** Existe intervalo de confiança de posto por bootstrap sobre o período
      de registro, versionado e por município.
      *`rank_confidence_intervals.csv`, 1000 sorteios, IC de 90 %, com validação
      de que o sorteio-identidade reproduz o risco publicado.*
- [x] **C.** A varredura de ponderação do perigo está reportada. *ρ ≥ 0,94 de
      100 % frequência a 100 % severidade; o 50/50 não é escolha frágil.*
- [x] **D.** Está declarado **onde** a instabilidade remanescente reside: na forma
      funcional (aritmética 0,551; posto percentílico 0,638), não na escolha nem
      na ponderação das componentes.
- [x] **E.** O achado dos **eventos únicos** está registrado com número — 94 dos
      196 municípios com risco positivo têm menos de 10 eventos, 90 têm menos de
      5, e o primeiro deles é o 21º — e declarado no parágrafo de limitação.
- [x] **F.** O manuscrito apresenta o resultado como **faixas de prioridade**
      abaixo do top-20, e não afirma ordenação onde os intervalos se sobrepõem.
      *Parágrafo de limitação e legenda da tabela do artigo.*
- [ ] **G.** *(remetido, não pendente aqui)* A instabilidade da fronteira
      zero/não-zero — 94 municípios que caem a zero em alguns sorteios — atinge a
      categoria "risco zero" de **AUD-15** e a definição de hotspot de **AUD-16**,
      ambas abertas. Registrado nas duas.

## 10. Riscos de alteração prematura

- **Escolher a agregação depois de ver os rankings** é seleção de resultado. O
  critério deve ser fixado e declarado antes.
- **Substituir Min–Max por posto** (ρ = 0,967 no risco) parece atraente, mas
  destrói a informação de magnitude: dois municípios com perigo muito diferente
  ficam separados por uma posição. Interage com AUD-11 e deve ser decidido em
  conjunto.
- Executar esta análise **antes** de AUD-01, AUD-02, AUD-04 e AUD-06 produz uma
  tabela que terá de ser refeita. Recomenda-se produzir a infraestrutura agora e
  reexecutá-la ao final.

## 11. Condições sob as quais o resultado atual pode ser mantido

O ranking atual pode ser publicado se:

1. A tabela de sensibilidade acompanhá-lo, com a variante "só frequência"
   incluída, sem omissão;
2. Os intervalos de confiança por bootstrap forem apresentados;
3. O texto apresentar o resultado como **faixas de prioridade** em vez de
   ordenação estrita, quando as faixas se sobrepuserem;
4. A escolha da média aritmética equiponderada for justificada explicitamente.

## 12. Produtos a jusante que exigiriam regeneração

Se apenas a análise for adicionada: nenhum produto existente muda; são criados
novos em `outputs/audit/AUD-07_aggregation_sensitivity/`.

Se a agregação for alterada: cadeia de AUD-06 §12 (do exportador às figuras;
catálogos não precisam ser reprocessados).

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_07_aggregation_sensitivity.py`, `outputs/audit/AUD-07_aggregation_sensitivity/`. **Alterados:** este registro (§3-bis, §9, §13, §14), `README.md` (parágrafo de limitação), `src/figures_article/make_article_top10_municipality_tables.py` (legenda), `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.tex` (só a legenda), `docs/scientific_audit/ISSUE_TRACKER.md`, AUD-15 e AUD-16 (referência cruzada) | Diagnóstico + declaração. **Nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

*Os resultados da §3 foram produzidos no diagnóstico de linha de base de
2026-07-29, com scripts ad hoc não versionados. Consolidá-los em script
versionado é o diagnóstico 1.*

### 2026-07-31 — Medição contra o produto atual; o bootstrap teve de ser redesenhado

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | A instabilidade de ρ = 0,384 sobrevive ao portão HAT e à remoção da cadeia de Min–Max? E qual é a incerteza de posto do produto vigente? |
| **Dados e métodos** | `risk_index_municipalities.geojson` (280 com risco) e `compound_catalog.json` (16 768 eventos com `date_start` e `integrated_severity`). Matriz de concordância todas-contra-todas; estabilidade de top-N para N ∈ {5, 10, 20, 50}; varredura do peso frequência↔severidade; e **dois** bootstraps — o do §8.2, por município, e um novo por **ano**, com 1000 sorteios e semente 7 |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_07_aggregation_sensitivity` |
| **Novas saídas geradas** | `outputs/audit/AUD-07_aggregation_sensitivity/{variant_agreement_matrix.csv, variant_topn_stability.csv, hazard_weight_sensitivity.csv, rank_confidence_intervals.csv, summary.json}` |
| **Achados** | (a) **O bootstrap por município mede exatamente zero**: deslocamento máximo de posto relativo 0,0 em 200 sorteios. Com âncoras fixas o valor de um município não depende da amostra, e o desenho do §8.2 perdeu a razão de existir. (b) **A instabilidade que motivou o P0 evaporou**: "só frequência" foi de **0,384 para 0,940**, "só severidade" 0,974. (c) **A ponderação é indiferente**: ρ ≥ 0,94 de 100 % frequência a 100 % severidade. (d) **A instabilidade remanescente está na forma funcional**: média aritmética 0,551, componentes por posto percentílico 0,638 — as únicas variantes que movem o resultado. (e) **Bootstrap por ano**: as posições 1, 2 e 3 são degeneradas; largura mediana do IC de 90 % é 4,5 posições no top-10 e 7 em 11–20, mas **45 na faixa 101–196**. Oito municípios têm intervalo cobrindo a posição 10 — o corte de top-10 não é nítido. (f) **Achado novo e não previsto por nenhum critério**: **94 dos 196 municípios com risco positivo têm menos de 10 eventos aceitos, 90 têm menos de 5**, e o primeiro deles é o **21º** — Guimarães/MA, com **um único evento em 33 anos**. No bootstrap, 94 municípios caem a risco exatamente zero em alguns sorteios (Guimarães, Alcântara, Raposa e Icatu em 34 %), de modo que apenas **102 dos 280 são robustamente não nulos** |
| **Interpretação** | A questão fecha bem no que foi criada para medir e mal no que não previa. O ranking é robusto no topo e à ponderação; a ordenação abaixo da posição ~20 não é interpretável, e a razão não é a agregação: é que a **severidade é uma média condicional que não escala com raridade**. Um ponto com um evento moderado recebe severidade 0,28 e, com frequência 0,010, perigo 0,146 — que a média geométrica com vulnerabilidade ≈ 0,98 converte em 21ª posição nacional. Isso é uma propriedade da definição de perigo que ninguém escolheu deliberadamente, e a fronteira zero/não-zero herda a mesma fragilidade |
| **Alterações implementadas** | Nenhuma em valor publicado. Script novo; legenda da tabela de top-10 do artigo passou a remeter à incerteza de posto (só a legenda; o CSV não mudou) |
| **Validação realizada** | (1) O catálogo evento a evento reproduz o produto: contagens **idênticas** nos 808 pontos, severidade média a 6,7e-05. (2) O bootstrap **levanta erro** se o sorteio-identidade não reproduzir o risco publicado. (3) A degenerescência do bootstrap por município foi medida, não assumida |
| **Incerteza remanescente** | (1) O bootstrap por anos trata os anos como trocáveis: **ignora tendência e autocorrelação interanual**, de modo que os intervalos são um piso da incerteza, não uma estimativa completa. (2) Nenhuma correção foi feita para a assimetria frequência↔severidade; ela é declarada, não tratada. (3) A instabilidade da fronteira zero/não-zero não foi propagada às figuras nem às legendas |
| **Próxima decisão necessária** | Do pesquisador: declarar, restringir a leitura a faixas, ou tratar a assimetria como fragilidade metodológica e abrir questão nova para a definição de perigo |

### 2026-07-31 — DECISÃO: fechar como `resultado-validado-mantido`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | **Declarar.** Publicar as tabelas de sensibilidade e os intervalos de posto; declarar no manuscrito que a ordenação é interpretável no top-20 e não abaixo disso; registrar o achado dos eventos únicos como limitação nomeada. **Nenhum valor muda, e a definição de perigo não é alterada** |
| **Por que não tratar a assimetria agora** | A correção certa não é óbvia — severidade ponderada pela contagem, contagem mínima, ou outra —, e escolher uma **depois** de ver quais municípios ela remove tem exatamente o problema de seleção de resultado que a §10 deste registro adverte. Alterar a definição de perigo também reabriria **AUD-13**, fechada no mesmo dia, e obrigaria a regenerar toda a cadeia municipal. Fica registrado como candidato a trabalho futuro, com o diagnóstico já versionado para quem o retomar |
| **O que o desfecho NÃO cobre** | (1) A instabilidade da fronteira zero/não-zero nas figuras e legendas — **AUD-15** e **AUD-16**, ambas abertas, e ambas agora com esta evidência anotada. (2) A tendência e a autocorrelação interanual, ignoradas pelo bootstrap |
