# AUD-05 — Validação contra casos costeiros conhecidos: o produto reprova nos testes de sanidade mais óbvios

| Campo | Valor |
|-------|-------|
| **ID** | AUD-05 |
| **Tipo** | `lacuna-validacao` |
| **Componente** | integração (transversal) |
| **Etapa do fluxo** | Step 4.4 (produto final) |
| **Afeta** | interpretação, saídas |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — é o primeiro teste que um revisor brasileiro aplicará |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | AUD-01, AUD-02, AUD-04, AUD-06, AUD-08, AUD-09, AUD-11 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-13, AUD-16, AUD-18 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §5, §6.1–6.4, §7.2, §9.1 item 7 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

O mapa municipal de risco integrado coloca no **fundo absoluto do ranking**
nacional exatamente os municípios com os casos de impacto costeiro mais
documentados do Brasil, e coloca no topo municípios sem registro conhecido de
inundação por evento composto onda–sobrelevação.

Esta questão é a **suíte de testes de aceitação** do produto final. Ela não tem
correção própria: fecha quando as questões das quais depende forem resolvidas e
o mapa resultante explicar cada caso de referência.

## 2. Por que importa cientificamente

Um índice de risco costeiro é um instrumento de priorização de adaptação. Se ele
não recupera os casos que a Defesa Civil, as autoridades portuárias e a
literatura já identificaram, ele não pode ser usado para o fim declarado — e será
recusado por revisores e por gestores.

Igualmente importante: **concordância com a literatura não é critério de
correção.** Um hotspot novo pode ser válido. O que esta questão exige é que
**cada** divergência seja explicada por um mecanismo identificado, não que o
mapa seja forçado a concordar.

## 3. Evidência original

### 3.1 Casos de referência que o produto **reprova**

| Município | Posição (de 280) | `Risk_Hazard` | Evidência independente |
|---|---|---|---|
| **Balneário Camboriú/SC** | **280º (último)** | **0,000** | Engorda de praia de R$ 31 milhões (2021); erosão crônica documentada |
| **Itajaí/SC** | 275º | 0,191 | Canal de acesso ao Complexo Portuário fechado por 5 dias por ressaca; > R$ 1 milhão de prejuízo só a armadores |
| **Navegantes/SC** | 273º | 0,211 | Mesmo evento; erosão documentada na orla |
| **Itapema/SC** | 267º | 0,257 | Litoral central de SC, mesmo setor |
| **Campos dos Goytacazes/RJ** | 266º | 0,258 | Contém o Farol de São Tomé, um dos casos de erosão mais documentados do país |
| **Linhares/ES** | 272º | 0,218 | Contém Regência, foz do Rio Doce, erosão e inundação recorrentes |

**Mecanismo do caso de SC, rastreado na revisão de linha de base:**

1. O mínimo global de `mean_overlap_duration` (1,26 d) está em (−26,6; −48,6),
   no próprio setor → `Hazard_Duration` ≈ 0,008–0,016 (AUD-06).
2. Os pontos atribuídos são **abrigados**: (−27,0; −48,4) tem `thr_hs` = 1,82 m e
   `compound_count` = 122, contra 2,58 m e 245 em (−28,2; −48,4) (AUD-04).
3. `Hazard_Index_mun` = 0,089.
4. Balneário Camboriú recebe `SVI_Coast_2022` = 0,000 **exatamente**, por ser o
   mínimo do Min–Max (AUD-09).
5. Produto geométrico com piso: (0,089 × 0,885 × 0,01)^(1/3) = 0,0924 =
   **exatamente a âncora inferior da escala publicada** (AUD-11).

Os casos de Campos dos Goytacazes e Linhares têm mecanismo distinto: são
rebaixados por `Exposure_relative` = 0,025 e 0,032 (AUD-08).

### 3.2 Casos que o produto **aprova** (controles positivos)

| Município | Posição | Componente condutora | Evidência |
|---|---|---|---|
| Maricá/RJ | 7º | perigo 0,911 | Região dos Lagos: ressacas e erosão documentadas |
| Saquarema/RJ | 9º | perigo 0,920 | idem |
| Araruama/RJ | 22º | perigo 0,917 | idem |
| São Sebastião/SP | 17º | perigo **1,000** (máx.) | Litoral norte de SP, ressacas e porto |
| Bertioga/SP | 24º | perigo 0,996 | idem |
| São José do Norte/RS | 25º | perigo 0,727 | RS, setor mais estudado para sobrelevação |

**Observação decisiva:** o **top-10 por perigo** (`Hazard_Index`) é inteiramente
S/SE e fisicamente sólido — São Sebastião, Bertioga, Laguna, Saquarema, Santa
Vitória do Palmar, Araruama, Angra dos Reis, Maricá, Duque de Caxias, Guapimirim.
A reprovação ocorre apenas no **índice integrado**.

### 3.3 Casos de plausibilidade duvidosa no topo

> **Desatualizada em 2026-07-31 — não usar como está.** Os quatro casos abaixo
> saíram do topo: Macapá está em **169º**, Chaves em **52º**, e Icatu, Turiaçu,
> Apicum-Açu e Axixá deixaram o top-10 (Icatu 32º, Turiaçu 127º). Salvaterra e
> Vigia estão em **risco zero**. O agrupamento duvidoso do topo passou a ser
> outro, e nasce do desfecho de AUD-02: **as baías abrigadas do RJ** — Magé em
> **3º** (fundo da Baía de Guanabara) e Mangaratiba em **4º** (Baía de Sepetiba,
> `thr_hs` = **0,78 m**). Magé já constava desta lista pelo mecanismo de
> associação (AUD-04); Mangaratiba é novo e tem as duas causas somadas. Toda a
> §3 deste registro é anterior ao portão HAT e à remoção da cadeia de Min–Max,
> e precisa ser remedida antes de qualquer julgamento — ver a nota de manutenção
> no `ISSUE_TRACKER.md`.

| Município | Posição | Problema |
|---|---|---|
| Magé, Duque de Caxias/RJ | 6º, 12º | Fundo da Baía de Guanabara, abrigada de swell — perigo 0,906 vem de ponto de plataforma aberta a 35 km (AUD-04) |
| Macapá/AP | 4º | Ponto dentro do estuário amazônico; `thr_hs` = 0,51 m (AUD-02, AUD-12) |
| Chaves/PA | 8º | `thr_hs` = **0,24 m**; hotspot é puro SVI = 100,0 (AUD-02, AUD-09) |
| Icatu, Turiaçu, Apicum-Açu, Axixá/MA | 1º, 2º, 3º, 5º | Costa macromareal, eventos travados em sizígia (AUD-01) |

### 3.4 Caso de subestimação a esclarecer

Recife, Olinda e Jaboatão dos Guararapes (PE) não aparecem no top-50, apesar de
erosão costeira crônica e ocupação urbana na linha de praia.
`Hazard_Frequency` médio no PE = 0,063. **Isto pode estar correto** — o NE tem
baixa frequência de compostos onda-sobrelevação — mas o mecanismo local de
inundação (galgamento sobre linha de recife em preamar de sizígia) não é
resolvido pela grade de 1/12° do GLORYS12. Ver AUD-18.

## 4. Localização exata

### Código

Esta questão não tem código próprio. Ela avalia a saída de:

- `src/site/export_risk_index_data.py::build_site_risk_data()`
- `src/figures_article/make_article_top10_municipality_tables.py`

### Dados e saídas

- `site/public/data/risk_index_municipalities.geojson` — objeto do teste.
- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.csv`
- `outputs/article_figures/tables/top10_municipalities_by_hazard.csv`
- `data/reported events/` — base da Defesa Civil de SC (Leal et al. 2024) e base
  documentária expandida; fonte de casos de referência para SC.
- `outputs/documentary_events_table/` — tabela suplementar de eventos
  documentados.

### Figuras afetadas

- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`
- `outputs/article_figures/supplementary_integrated_risk_zooms.png`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Nenhum teste de sanidade automatizado. Nenhuma lista de casos de referência versionada |
| **Pretendido** | Uma lista versionada de casos de referência positivos e negativos, e um relatório automatizado que reporte a posição de cada um no ranking a cada regeneração do produto |

## 6. Divergência documentação ↔ implementação ↔ saídas

O `README.md` §Stakeholders declara que o produto se destina a autoridades
portuárias, governos locais, Marinha e defesa civil. Nenhum documento do
repositório confronta o produto com casos conhecidos. A base da Defesa Civil de
SC é usada **apenas** na calibração de limiares (Step 2e) e é explicitamente
declarada como não utilizada em validação a jusante, por sub-reporte sistemático.
Isso é defensável para validação estatística, mas não impede o uso dos casos mais
documentados como **teste de sanidade qualitativo**.

## 7. Explicações alternativas plausíveis

1. **O índice mede risco relativo dentro do conjunto, não risco absoluto.**
   Balneário Camboriú pode ter perigo físico moderado e vulnerabilidade social
   genuinamente baixa (é dos municípios mais ricos do país); um índice
   conjuntivo de risco *social* corretamente a coloca abaixo de Icatu. **O erro
   estaria na leitura, não no índice** — mas isso não explica a posição 280º de
   280, nem o valor exatamente 0,000.
2. **Impacto econômico ≠ risco social.** O prejuízo portuário de Itajaí é um
   risco a **ativos e operações**, dimensão que o índice não mede (a exposição é
   populacional). Um índice de exposição de ativos daria outro resultado.
3. **Capacidade adaptativa alta reduz risco legitimamente.** Balneário Camboriú
   fez uma engorda de R$ 31 milhões — evidência de capacidade de resposta, que o
   arcabouço IPCC trata como redutora de risco. O SVI captura isso indiretamente.
4. **Os hotspots do Norte podem ser válidos como risco de inundação costeira**
   (maré + ondas), mesmo não sendo válidos como compostos meteorológicos. Ver
   AUD-01 §7.

Nenhuma dessas explicações justifica a posição de Campos dos Goytacazes e
Linhares, que é claramente um artefato de MAUP (AUD-08).

## 8. Diagnósticos propostos

1. **Criar uma lista versionada de casos de referência** em
   `docs/scientific_audit/` ou `data/reported events/`, com colunas: município,
   código IBGE, tipo de evidência, fonte, expectativa qualitativa (alto / médio /
   baixo risco), justificativa. Incluir os controles positivos **e** negativos.
2. **Script de relatório de sanidade** que, a cada regeneração do produto,
   imprima a posição de cada caso de referência e a decomposição das suas três
   componentes. Sugestão: `src/exploratory/audit_AUD_05_reference_cases.py` →
   `outputs/audit/AUD-05_reference_cases/`.
3. **Decomposição forense por município de referência**: para cada um, reportar
   `Hazard_Frequency`, `Hazard_Duration`, `Hazard_Intensity`, `Hazard_Index_mun`,
   `Exposure_absolute`, `Exposure_relative`, `SVI`, ponto de grade, distância ao
   ponto, e a contribuição de cada fator a log(`Risk_Hazard_raw`).
4. **Reexecutar o relatório após cada questão dependente ser resolvida**, para
   verificar se a posição migra na direção esperada.
5. **Comparar o ranking de perigo com o ranking de risco** para os casos de
   referência, documentando quais reprovações são de perigo e quais são de
   integração — a distinção é essencial para a discussão do manuscrito.

## 9. Critérios objetivos de resolução

- [ ] Existe uma lista versionada de casos de referência, com fonte para cada um.
- [ ] Existe um relatório automatizado e versionado que reporta a posição e a
      decomposição de cada caso.
- [ ] **Nenhum** município com evidência documentada de disrupção portuária,
      erosão severa ou inundação costeira recorrente permanece no decil inferior
      do ranking sem explicação escrita e aceita.
- [ ] Cada divergência remanescente entre o produto e a evidência independente
      tem um mecanismo identificado e registrado — não basta "é risco relativo".
- [ ] Nenhum município permanece com `Risk_Hazard` exatamente 0,000 por artefato
      de Min–Max (depende de AUD-11).
- [ ] O manuscrito contém uma seção de validação qualitativa que apresenta
      **tanto** os acertos (Região dos Lagos, litoral norte de SP, RS) **quanto**
      as divergências, sem seleção.
- [ ] Os quatro hotspots duvidosos do topo (Icatu, Macapá, Chaves, Magé) têm
      interpretação declarada, coerente com o desfecho de AUD-01 e AUD-04.

## 10. Riscos de alteração prematura

- **Ajustar o método até que os casos conhecidos apareçam no topo é seleção de
  resultado** e destrói o valor científico do trabalho. Os casos de referência
  são um *teste*, não um alvo de ajuste.
- Qualquer mudança aqui deve vir da resolução das questões dependentes, com
  justificativa própria, e só então ser reavaliada por esta suíte.
- Excluir casos inconvenientes da lista de referência depois de vê-los reprovar
  é o pior desfecho possível. A lista deve ser fixada **antes** das correções.

## 11. Condições sob as quais o resultado atual pode ser mantido

O produto pode ser mantido essencialmente como está se:

1. AUD-11 for resolvido de modo que nenhum município receba 0,000 por artefato;
2. O manuscrito **reenquadrar** explicitamente `Risk_Hazard` como índice de
   priorização de **risco social** relativo, declarando que risco a ativos,
   infraestrutura portuária e patrimônio **não** é medido;
3. A seção de validação apresentar os casos de SC e do RJ/ES como divergências
   conhecidas, com o mecanismo de cada uma explicado;
4. AUD-01, AUD-02 e AUD-04 tiverem desfecho registrado.

Ainda assim, a posição 280ª de Balneário Camboriú é difícil de defender
publicamente e provavelmente exigirá correção de AUD-09 e AUD-11.

## 12. Produtos a jusante que exigiriam regeneração

Nenhum diretamente por esta questão — ela é diagnóstica. A regeneração virá das
questões dependentes.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada. Os casos e mecanismos da §3 vêm do diagnóstico
de linha de base de 2026-07-29.*
