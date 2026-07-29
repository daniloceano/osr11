# AUD-13 — Comportamento do índice integrado: dominância do perigo e cancelamento estrutural exposição × vulnerabilidade

| Campo | Valor |
|-------|-------|
| **ID** | AUD-13 |
| **Tipo** | `analise-sensibilidade` |
| **Componente** | integração |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação — a decomposição de contribuições precisa acompanhar o resultado |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | AUD-01, AUD-02 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-05, AUD-07, AUD-08, AUD-09, AUD-11 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §4.1, §4.2, §8 item 11, §9.1 item 4 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

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

## 3. Evidência original

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

- [ ] A decomposição de variância (51/27/22) está versionada e publicada no
      manuscrito ou material suplementar.
- [ ] O cancelamento E × V (ρ = −0,588) está reportado e discutido, com o efeito
      sobre a variância do índice quantificado pelo diagnóstico 6.
- [ ] As correlações parciais (0,845 e 0,795) estão reportadas — elas demonstram
      que o índice não é degenerado e são um argumento **a favor** do método.
- [ ] Existe decomposição por município para, no mínimo, os 20 primeiros e os 20
      últimos.
- [ ] A inversão perigo → risco está explicada mecanicamente no manuscrito, não
      apenas apresentada.
- [ ] O manuscrito declara que os pesos nominais iguais **não** implicam
      contribuição igual, e reporta as contribuições efetivas.
- [ ] A análise foi refeita após AUD-01 e AUD-02, ou está registrado por que não
      foi necessário.

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29, com scripts ad hoc não versionados.*
