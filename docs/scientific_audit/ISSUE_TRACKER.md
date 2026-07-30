# Rastreador central da auditoria científica — OSR11

**Última atualização:** 2026-07-29
**Origem:** [`baseline/2026-07-29_initial_review.md`](baseline/2026-07-29_initial_review.md)
**Questões abertas:** 14 de 18 · **em investigação:** 1 (AUD-17) · **resolvidas:** 3 (AUD-01, AUD-04, AUD-06) · **arquivadas:** 0

> **Três questões foram resolvidas.** AUD-01 e AUD-06 em conjunto (método do
> perigo); AUD-04 por reenquadramento — a associação município↔ponto é
> julgamento de especialista, e foi arquivada como dado de entrada versionado
> sem alterar nenhum valor. AUD-17 teve seis de seus oito itens corrigidos (correção puramente
> documental, sem efeito em nenhum valor numérico publicado — ver seu registro,
> §14).
>
> **AUD-01 e AUD-06 foram resolvidas em conjunto**, por serem indissociáveis:
> nenhuma das duas correções isoladas é defensável. O método adotado usa a maré
> como **variável condicionante** em vez de forçante, e o índice de perigo passou
> de três para **duas componentes** — `frequência + severidade integrada`.
> O método legado está preservado em `outputs/legacy_ssh_total_method/` e a
> comparação em `outputs/method_comparison_ssh_total_vs_mhws/`.
> **Site e figuras do artigo foram regenerados.**
>
> Resultado: gradiente de perigo coerente (ρ com \|latitude\| = +0,58), as duas
> componentes passam a se reforçar (ρ = +0,60, era −0,55), e o top-10 municipal
> ao norte de 20°S cai de **70 % para 50 %**. Dois critérios de aceitação de
> AUD-06 permanecem não verificados, registrados no próprio registro.
>
> As demais 15 questões estão com situação `aberto` e desfecho vazio.
>
> Relatório para coautores: [`reports/2026-07-29_relatorio_auditoria_perigo.md`](reports/2026-07-29_relatorio_auditoria_perigo.md).

Vocabulário controlado de `Tipo`, `Prioridade`, `Status` e `Desfecho`:
ver [`README.md`](README.md).

---

## 1. Situação por prioridade

| Prioridade | Total | aberto | em-investigação | aguardando-decisão | resolvido |
|---|---|---|---|---|---|
| **P0 — bloqueia publicação** | 6 | 3 | 0 | 0 | **3** |
| **P1 — resolver ou justificar** | 9 | 8 | 1 | 0 | 0 |
| **P2 — recomendado** | 3 | 3 | 0 | 0 | 0 |
| **P3 — opcional** | 0 | — | — | — | — |
| **Total** | **18** | **14** | **1** | **0** | **3** |

---

## 2. Tabela mestra

| ID | Título | Tipo | Componente | Etapa | Afeta | Prio | Bloqueia publicação? | Status | Desfecho | Depende de | Registro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **AUD-01** | Eventos compostos travados em fase com a sizígia ao norte de ~20°S | fragilidade-metodologica | perigo | 3.2 (orig. 2e) | dados, interp., saídas, doc. | **P0** | **Sim** | `resolvido` | `metodologia-alterada` | **06** | [AUD-01](issues/AUD-01_compound_detector_tidal_phase_locking.md) |
| **AUD-02** | Limiares de "onda extrema" fisicamente vazios no Norte (0,20–1,05 m) | fragilidade-metodologica | perigo | 2e → 3.1/3.2 | dados, interp., saídas, doc. | **P0** | **Sim** | `aberto` | — | — | [AUD-02](issues/AUD-02_hs_threshold_transfer.md) |
| **AUD-03** | Incoerência de fase em `SSH_total` (zos 00Z + maré máx. diária) | fragilidade-metodologica | perigo | 2c → 3.1/3.2 | código, dados, interp., doc. | P1 | Não | `aberto` | — | — | [AUD-03](issues/AUD-03_ssh_total_phase_coherence.md) |
| **AUD-04** | Transferência grade → município: regra não reproduzível e suporte inadequado | **erro-implementacao** | perigo → integração | 4.1 | código, dados, interp., saídas, doc. | **P0** | **Sim** | `resolvido` | `limitacao-reconhecida` | — | [AUD-04](issues/AUD-04_grid_to_municipality_transfer.md) |
| **AUD-05** | Validação contra casos costeiros conhecidos (suíte de aceitação) | lacuna-validacao | integração | 4.4 | interp., saídas | **P0** | **Sim** | `aberto` | — | 01, 02, 04, 06, 08, 09, 11 | [AUD-05](issues/AUD-05_known_case_validation.md) |
| **AUD-06** | Duração: faixa trivial (1,26–2,51 d) amplificada a peso 1/3 | fragilidade-metodologica | perigo | 3.2 → 4.4 | código, interp., saídas | **P0** | **Sim** | `resolvido` | `metodologia-alterada` | 01 | [AUD-06](issues/AUD-06_duration_component_validity.md) |
| **AUD-07** | Instabilidade do ranking sob agregação alternativa do perigo (ρ = 0,384) | analise-sensibilidade | perigo → integração | 4.4 | interp., saídas, doc. | **P0** | **Sim** | `aberto` | — | — | [AUD-07](issues/AUD-07_hazard_aggregation_stability.md) |
| **AUD-08** | Exposição: saturação do termo relativo e MAUP | fragilidade-metodologica | exposição | 4.2 → 4.4 | código, interp., saídas | P1 | Sim, salvo qualificação | `aberto` | — | — | [AUD-08](issues/AUD-08_exposure_spatial_support.md) |
| **AUD-09** | SVI: dois indicadores com direcionalidade invertida; eixo de pobreza | fragilidade-metodologica | vulnerabilidade | 4.3 | dados, interp., saídas, doc. | P1 | Sim, salvo qualificação | `aberto` | — | — | [AUD-09](issues/AUD-09_svi_directionality.md) |
| **AUD-10** | Camada de vulnerabilidade física ausente, apesar de declarada | inconsistencia-documental | vulnerabilidade | 4.3 | interp., doc. | P1 | Sim, salvo qualificação | `aberto` | — | — | [AUD-10](issues/AUD-10_physical_vulnerability_missing.md) |
| **AUD-11** | Min–Max em cadeia, ancoragem amostral e limites de interpretação | risco-interpretacao | integração | 4.4 | código, interp., saídas, doc. | P1 | Sim, salvo qualificação | `aberto` | — | — | [AUD-11](issues/AUD-11_minmax_chain_and_sample_anchoring.md) |
| **AUD-12** | Contaminação estuarina e fluvial no estuário amazônico | qualidade-dados | perigo | 2a → 3.1/3.2 | dados, interp., saídas | P1 | Sim, salvo qualificação | `aberto` | — | 01 | [AUD-12](issues/AUD-12_estuarine_river_contamination.md) |
| **AUD-13** | Índice integrado: dominância do perigo e cancelamento E × V | analise-sensibilidade | integração | 4.4 | interp., saídas, doc. | P1 | Sim, salvo qualificação | `aberto` | — | 01, 02 | [AUD-13](issues/AUD-13_integrated_index_behaviour.md) |
| **AUD-14** | População sazonal invisível (censo *de jure*) | qualidade-dados | exposição | 4.2 | dados, interp., doc. | P2 | Não | `aberto` | — | — | [AUD-14](issues/AUD-14_seasonal_population.md) |
| **AUD-15** | Cobertura amostral: 2 municípios ausentes, 4 com exposição degenerada | qualidade-dados | integração | 4.1/4.2/4.4 | dados, interp., saídas, doc. | P2 | Não | `aberto` | — | — | [AUD-15](issues/AUD-15_sample_coverage.md) |
| **AUD-16** | Ausência de definição operacional de "hotspot" | risco-interpretacao | integração | 4.4/4.5 | interp., saídas, doc. | P2 | Não | `aberto` | — | 11 | [AUD-16](issues/AUD-16_hotspot_definition.md) |
| **AUD-17** | Oito inconsistências documentação ↔ código ↔ saídas | **inconsistencia-documental** | transversal | 4 + README | doc., saídas | P1 | Sim, salvo correção | `em-investigacao` | — | — | [AUD-17](issues/AUD-17_documentation_code_consistency.md) |
| **AUD-18** | Lacuna de validação independente fora de SC; limiares extrapolados | lacuna-validacao | transversal | 2d/2e → 3 → 4 | dados, interp., doc. | P1 | Sim, salvo declaração | `aberto` | — | — | [AUD-18](issues/AUD-18_independent_validation_gap.md) |

---

## 3. Grafo de dependências

```
AUD-01 (sizígia) ────┬──► AUD-05 (validação de casos)
AUD-02 (limiar Hs) ──┤        ▲
AUD-04 (associação) ─┤        │
AUD-06 (duração) ────┤        │
AUD-08 (exposição) ──┤        │
AUD-09 (SVI) ────────┤        │
AUD-11 (Min–Max) ────┴────────┘

AUD-01 ◄──► AUD-06   PAR INDISSOCIÁVEL (demonstrado em 2026-07-29):
                     nenhuma das duas correções isoladas é defensável.
                     top-10 ao N de 20°S — legado+3comp 70 % · legado+2comp 90 %
                                         · MHWS+3comp   90 % · MHWS+2comp   30 %

AUD-01 ──► AUD-12 (contaminação estuarina)
AUD-01, AUD-02 ──► AUD-13 (comportamento do índice)
AUD-11 ──► AUD-16 (definição de hotspot)

Sem dependências (podem começar imediatamente):
  AUD-01, AUD-02, AUD-03, AUD-04, AUD-06, AUD-07,
  AUD-08, AUD-09, AUD-10, AUD-11, AUD-14, AUD-15,
  AUD-17, AUD-18
```

**AUD-05 é terminal**: não tem correção própria; é a suíte de aceitação que
fecha quando as sete questões das quais depende fecharem.

---

## 4. Agrupamento por natureza do problema

| Natureza | Questões |
|---|---|
| **Erro de implementação confirmado** | AUD-04 (regra documentada não se reproduz), AUD-17 (afirmações falsas no código e nos metadados publicados) |
| **Fragilidade metodológica** | AUD-01, AUD-02, AUD-03, AUD-06, AUD-08, AUD-09 |
| **Lacuna de validação** | AUD-05, AUD-18 |
| **Risco de interpretação** | AUD-11, AUD-16 |
| **Qualidade de dados** | AUD-12, AUD-14, AUD-15 |
| **Análise de sensibilidade pendente** | AUD-07, AUD-13 |
| **Inconsistência documental** | AUD-10, AUD-17 |
| **Melhoria opcional** | *nenhuma registrada como questão autônoma — ver §7* |

---

## 5. Agrupamento por componente do risco

| Componente | Questões |
|---|---|
| **Perigo** | AUD-01, AUD-02, AUD-03, AUD-06, AUD-12 |
| **Exposição** | AUD-08, AUD-14 |
| **Vulnerabilidade** | AUD-09, AUD-10 |
| **Integração** | AUD-05, AUD-07, AUD-11, AUD-13, AUD-15, AUD-16 |
| **Transversal** | AUD-17, AUD-18 |

---

## 6. Ordem de trabalho recomendada

A ordem abaixo respeita as dependências e concentra os reprocessamentos caros
(catálogos do Step 3) em uma única execução.

| Onda | Questões | Racional |
|---|---|---|
| **1 — sem custo de reprocessamento** | AUD-17, AUD-07, AUD-13, AUD-11 | Correção documental e consolidação de diagnósticos já executados. Nenhuma depende de decisão científica pendente; AUD-17 pode fechar integralmente |
| **2 — decisões sobre o detector** | AUD-01, AUD-02, AUD-03, AUD-12, AUD-18 | Todas tocam o catálogo do Step 3. **Decidir as cinco em conjunto e reprocessar uma única vez** |
| **3 — camadas municipais** | AUD-04, AUD-06, AUD-08, AUD-09, AUD-15 | Posteriores ao Step 3; exigem apenas reexecutar o exportador e as figuras |
| **4 — enquadramento e escopo** | AUD-10, AUD-14, AUD-16 | Predominantemente documentais; dependem do método final |
| **5 — aceitação** | AUD-05 | Fecha por último, verificando o produto resultante |

---

## 7. Achados da revisão **não** convertidos em questão autônoma

Registrados aqui para que a rastreabilidade fique completa e nenhum achado se
perca por omissão.

| Achado da revisão | Onde foi absorvido | Por quê |
|---|---|---|
| Pontos fortes (§1): rastreabilidade do código, estrutura espacial correta da frequência, normalização de intensidade por excesso local, média geométrica conjuntiva, SVI reprodutível | Citados como evidência dentro de AUD-02 §7.2, AUD-09 §3.5, AUD-13 §7.3 | Não são fragilidades. Preservados no registro de linha de base e usados como contra-argumento nas questões relevantes |
| Reconstrução da metodologia implementada (§2.1) | `baseline/…` §2.1; replicada por partes nas §4 de cada questão | É contexto, não problema acionável |
| Anomalia de `pop_house` pré-normalizado | AUD-17 §3, item adicional | Já auditado em 2026-07-28 e demonstrado inócuo para o índice; pendência apenas de coerência entre coluna publicada e definição no manuscrito |
| Pseudo-replicação espacial (178 pontos para 280 municípios) | AUD-04 §2 e §3; consequência tratada em AUD-16 §10 | É uma consequência direta da associação, não um problema independente |
| Casos Campos dos Goytacazes e Linhares (§6.2) | AUD-08 §3.2 (causa) e AUD-05 §3.1 (teste) | Mesmo mecanismo do MAUP da exposição; separá-los duplicaria contexto |
| Subestimação de Osório e Santa Vitória do Palmar (§6.3) | AUD-13 §7 (compensação E × V) | Manifestação do cancelamento estrutural, já rastreado |
| Subestimação de Recife/Olinda/Jaboatão (§6.4) | AUD-18 §3.5 | É uma lacuna de validação (não há base regional para decidir se está certo), não uma fragilidade de método |
| Melhoria opcional: setor censitário costeiro como unidade (§9.3 item 15) | AUD-08 §8.5 e §10 | Alternativa de suporte espacial dentro da questão de exposição; não é problema autônomo |
| Melhoria opcional: sensibilidade `mean` vs. `p95` (§9.3 item 17) | AUD-06 §8.2 | Diagnóstico dentro da questão da duração |
| Melhoria opcional: estimar população sazonal (§9.3 item 16) | AUD-14 §8.3–8.4 | Diagnóstico dentro da questão da população sazonal |
| Lista de verificação pré-submissão (§9.1 lista final) | Distribuída pelos critérios de resolução (§9) das questões correspondentes | Cada item tem dono; manter uma segunda lista criaria duas fontes de verdade |

Nenhum achado da revisão de linha de base foi descartado.

### Achado novo, posterior à revisão de linha de base

| Achado | Onde foi registrado | Quando |
|---|---|---|
| O mapa de estrutura do `README.md` (L480–485, L496–499) aponta módulos do Step 3 e do Step 4 em diretórios onde eles não estão | AUD-17 §3 item **#8** | 2026-07-29, durante a criação desta estrutura. Induziu erro real de referência, corrigido em AUD-02 §4 e AUD-03 §4 |

---

## 8. Como atualizar este rastreador

1. Ao mudar a situação de uma questão, atualize **a linha da tabela mestra** e o
   cabeçalho do registro correspondente. As duas devem sempre concordar.
2. Ao fechar uma questão, preencha **Desfecho** nos dois lugares e atualize os
   contadores da §1 e do cabeçalho.
3. Ao arquivar, mova a linha para a §9 e o arquivo para `issues/archive/`.
   **Nunca apague uma linha.**
4. Ao criar uma questão nova, use o próximo `AUD-NN` livre, copie
   [`ISSUE_TEMPLATE.md`](ISSUE_TEMPLATE.md), e acrescente linha na tabela mestra,
   nos agrupamentos das §4 e §5, e no grafo da §3 se houver dependência.
5. **Não marque nada como `resolvido` sem que todos os critérios de aceitação da
   §9 do registro estejam verificados e o histórico da §14 documente a
   verificação.** Alteração de código não é evidência de resolução.

---

## 9. Questões arquivadas

*Nenhuma.*

| ID | Título | Desfecho | Absorvida por | Data |
|---|---|---|---|---|
| — | — | — | — | — |
