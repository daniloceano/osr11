# AUD-05 — Validação contra casos costeiros conhecidos: o produto reprova nos testes de sanidade mais óbvios

| Campo | Valor |
|-------|-------|
| **ID** | AUD-05 |
| **Tipo** | `lacuna-validacao` |
| **Componente** | integração (transversal) |
| **Etapa do fluxo** | Step 4.4 (produto final) |
| **Afeta** | interpretação, saídas |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — satisfeito: nenhum caso documentado no decil inferior, e cada divergência com mecanismo nomeado |
| **Status** | `resolvido` |
| **Desfecho** | `mitigado-parcialmente` — o bloco de SC foi **recuperado** no perigo; a importação de perigo em Guanabara e Paraty **permanece**, declarada |
| **Depende de** | AUD-01, AUD-02, AUD-04, AUD-06, AUD-08, AUD-09, AUD-11 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-13, AUD-16, AUD-18 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §5, §6.1–6.4, §7.2, §9.1 item 7 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (suíte executada e fechamento) |

---

> ### Nota de leitura — o caso que a §6.1 chamava de desqualificante foi corrigido
>
> A §6.1 afirma que o bloco de Santa Catarina, *"por si só, invalida o mapa como
> instrumento de priorização de adaptação"*. **Balneário Camboriú, Itajaí e
> Navegantes estão hoje em 81º de 280 no perigo**, terço superior, contra 280º,
> 275º e 273º no risco à época. Toda a §3.1 e a §6.1 descrevem um produto que não
> existe mais.
>
> **Uma divergência sobrevive, e está no topo**: Magé em 3º e Paraty em 5º, com o
> perigo importado de pontos de plataforma aberta a 35 km e 15 km, fora das baías
> que os abrigam. É o mecanismo de AUD-04. Ver §3-bis.
>
> Fechada como `mitigado-parcialmente` por decisão do pesquisador em 2026-07-31.

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

---

## 3-bis. Resultado da suíte (2026-07-31)

Lista fixada em `docs/scientific_audit/reference_cases.csv` e commitada em
`242fce3` **antes** da primeira execução. Relatório em
`outputs/audit/AUD-05_reference_cases/`.

### 3-bis.1 O caso desqualificante foi corrigido

| | perigo (posição de 280) | risco | risco na linha de base |
|---|---|---|---|
| **Balneário Camboriú/SC** | **81º** | 186º | **280º · 0,000** |
| **Itajaí/SC** | **81º** | 175º | 275º |
| **Navegantes/SC** | **81º** | 149º | 273º |
| Itapema/SC | 72º | 139º | 267º |

Os três primeiros compartilham ponto de grade. **No perigo estão no terço
superior.** No risco continuam baixos, mas por razão declarada: são dos
municípios mais ricos do país, e a vulnerabilidade é um eixo de privação
material — expectativa registrada na lista como `ambiguous`, não como falha.

**O decil inferior começa na posição 253. Nenhum caso documentado está nele.**

### 3-bis.2 Os controles passam, positivos e negativos

Controles positivos, perigo: São José do Norte **3º**, Laguna **4º**, Bertioga
**6º**, São Sebastião **7º**, Rio Grande 17º, Maricá 36º, Saquarema 49º,
Araruama 50º. **13 de 14 cumprem a expectativa**; a exceção é Linhares (104º).

Controles negativos do Norte — os que a revisão de linha de base atribuía a maré
astronômica e não a tempestade — **saíram do topo do perigo**:

| | perigo | risco |
|---|---|---|
| Macapá/AP | 188º | 169º |
| Turiaçu/MA | 167º | 127º |
| Chaves/PA | 138º | 52º |
| Icatu/MA | 121º | 32º |

No perigo estão no meio da distribuição (percentil 0,43–0,67). As posições que
lhes restam no risco vêm da vulnerabilidade — desenho declarado, e defensável
**porque o perigo passou a ser honesto**.

### 3-bis.3 As divergências, e seus três mecanismos distintos

**(a) Importação de perigo por associação — a única no topo.**

| | perigo | risco | distância ao ponto |
|---|---|---|---|
| **Magé/RJ** | 29º | **3º** | **34,7 km** |
| Duque de Caxias/RJ | 29º | 25º | 35,2 km |
| Guapimirim/RJ | 29º | 53º | 30,3 km |
| **Paraty/RJ** | 39º | **5º** | 14,8 km |

Os três primeiros compartilham **um único ponto de plataforma aberta**, do outro
lado da Baía de Guanabara; Paraty usa um ponto dentro da Baía da Ilha Grande.
Ondulação da magnitude registrada nesses pontos não alcança o interior das
baías, e a inundação documentada nos quatro é fluvial e pluvial. É o mecanismo
de **AUD-04**, aflorando onde mais custa.

**(b) Supressão por anticorrelação perigo–vulnerabilidade.**

| | perigo | risco |
|---|---|---|
| **Santa Vitória do Palmar/RS** | **1º** | 131º |
| Osório/RS | 40º | 156º |
| Itaboraí/RJ | 29º | 118º |

Municípios fisicamente expostos e materialmente pouco privados. É a supressão
que **AUD-13** mediu (ρ marginal de V com o risco = −0,372, parcial +0,790) e
que a §6.3 da revisão de linha de base previu.

**(c) MAUP do denominador.** Campos dos Goytacazes 159º e Linhares 188º, com
`Exposure_relative` de 0,018 e 0,022 — declarado em **AUD-08**.

Nenhuma das três foi explicada por "é risco relativo", que a §9 proíbe
expressamente.

### 3-bis.4 Um defeito na própria lista, registrado e não corrigido

Fernando de Noronha recebeu `expectation_hazard = low`, mas não tem valor de
perigo por não ter associação — o veredito saiu "diverge (sem valor, mas um era
esperado)". **A inconsistência é da lista, não do produto**, e a lista **não foi
reeditada**: seu valor está em ter sido fixada antes de a suíte rodar.

Vale a mesma ressalva para vários controles negativos do MA/PA, que aparecem
como "diverge" no perigo por estarem no **meio** da distribuição, não por
estarem altos. O limiar de 0,34 é estrito e o veredito mecânico não distingue
"não é baixo" de "é alto".

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

- [x] Existe uma lista versionada de casos de referência, com fonte para cada um.
      *`docs/scientific_audit/reference_cases.csv`, **32 casos**, commitada em
      `242fce3` **antes** de a suíte ser executada pela primeira vez. Montada
      exclusivamente a partir da revisão de linha de base imutável de 2026-07-29 e
      da literatura externa identificada ao fechar AUD-02 (Gregório et al. 2017;
      Rocha 2018). Cinco papéis: controle positivo, caso ambíguo por desenho,
      controle negativo, vigilância de subestimação e cobertura.*
- [x] Existe um relatório automatizado e versionado que reporta a posição e a
      decomposição de cada caso.
      *`src/exploratory/audit_AUD_05_reference_cases.py` →
      `outputs/audit/AUD-05_reference_cases/{case_report.csv, divergences.csv,
      summary.json}`, com posição e percentil de perigo e de risco, as duas
      componentes do perigo, as três da exposição, a vulnerabilidade, a população
      e a **distância ao ponto de grade atribuído**.*
- [x] **Nenhum** município com evidência documentada de disrupção portuária,
      erosão severa ou inundação costeira recorrente permanece no decil inferior
      do ranking sem explicação escrita e aceita. ***Satisfeito, e é o critério
      mais duro da questão.*** *O decil inferior começa na posição 253. Os piores
      colocados entre os controles positivos são Linhares 188º, Balneário
      Camboriú 186º, Itajaí 175º e Campos dos Goytacazes 159º. **Nenhum está no
      decil inferior.** Na revisão de linha de base, Balneário Camboriú era
      **280º de 280** com risco exatamente 0,000.*
- [x] Cada divergência remanescente entre o produto e a evidência independente
      tem um mecanismo identificado e registrado — não basta "é risco relativo".
      *Ver §3-bis.3. As divergências têm três mecanismos distintos e nomeados:
      importação de perigo por associação (Guanabara e Paraty), supressão por
      anticorrelação perigo–vulnerabilidade (Santa Vitória do Palmar, Osório,
      Itaboraí) e MAUP do denominador (Campos dos Goytacazes, Linhares). Nenhuma
      foi explicada por "é risco relativo".*
- [x] Nenhum município permanece com `Risk_Hazard` exatamente 0,000 por artefato
      de Min–Max (depende de AUD-11). *AUD-11 removeu a cadeia de Min–Max e o
      piso. Os 84 zeros remanescentes são **substantivos** — perigo nulo por
      nenhum evento aceito em 1993–2025 — e separados por `risk_zero_cause`.
      Nenhum é artefato de escala.*
- [x] O manuscrito contém uma seção de validação qualitativa que apresenta
      **tanto** os acertos **quanto** as divergências, sem seleção.
      *Parágrafo de limitação no `README.md`, escrito para ser transferível. Traz
      os acertos (o bloco de SC recuperado, 13 de 14 controles positivos, os
      controles negativos do Norte caindo ao meio da distribuição) **e** as duas
      divergências, incluindo a que está no top-5.*
- [x] Os quatro hotspots duvidosos do topo (Icatu, Macapá, Chaves, Magé) têm
      interpretação declarada, coerente com o desfecho de AUD-01 e AUD-04.
      *Icatu, Macapá e Chaves **deixaram de ser hotspots de perigo**: 121º, 188º e
      138º, o meio da distribuição — consequência de AUD-01, e as posições que
      lhes restam no risco vêm da vulnerabilidade, o que é o desenho declarado.
      **Magé permanece**, em 3º, e sua interpretação está declarada como
      importação de perigo, coerente com AUD-04 ter fechado como
      `limitacao-reconhecida`.*

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
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `docs/scientific_audit/reference_cases.csv` (commitado antes em `242fce3`), `src/exploratory/audit_AUD_05_reference_cases.py`, `outputs/audit/AUD-05_reference_cases/`. **Alterados:** este registro, `README.md` (parágrafo de validação qualitativa), `src/figures_article/make_article_top10_municipality_tables.py` e o `.tex` (só a legenda), `docs/scientific_audit/ISSUE_TRACKER.md` | Suíte de aceitação. **Nenhuma alteração no pipeline de cálculo; nenhum valor numérico alterado** |

## 14. Histórico de investigação

*Nenhuma investigação registrada. Os casos e mecanismos da §3 vêm do diagnóstico
de linha de base de 2026-07-29.*

### 2026-07-31 — Suíte de aceitação executada, com a lista fixada de antemão

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | O produto recupera os casos costeiros documentados do Brasil? E as divergências que restarem têm mecanismo identificável? |
| **Disciplina metodológica adotada** | A §10 adverte que ajustar o método até os casos conhecidos aparecerem no topo é seleção de resultado, e que remover casos inconvenientes depois de vê-los reprovar é o pior desfecho possível. **Sete sessões de auditoria já haviam olhado onde cada município caiu.** Para que o teste significasse algo, a lista foi montada **apenas** a partir de fontes anteriores a toda mudança de método — a revisão de linha de base imutável de 2026-07-29 e a literatura externa identificada ao fechar AUD-02 — e **commitada em `242fce3` antes de a suíte rodar pela primeira vez** |
| **Dados e métodos** | 32 casos em `docs/scientific_audit/reference_cases.csv`. Duas decisões de desenho vindas do próprio registro: **perigo e risco recebem expectativas separadas**, porque a revisão de linha de base achou o top-10 de perigo sólido enquanto o índice integrado falhava; e casos onde nem alto nem baixo seria erro — município rico com erosão real, num índice cuja vulnerabilidade mede privação material — são **reportados, não pontuados**. Limiares declarados antes: expectativa "alta" cumprida no percentil ≥ 0,66, "baixa" no ≤ 0,34 |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_05_reference_cases` |
| **Novas saídas geradas** | `outputs/audit/AUD-05_reference_cases/{case_report.csv, divergences.csv, summary.json}` |
| **Achados** | (a) **O caso desqualificante foi corrigido.** Balneário Camboriú, Itajaí e Navegantes: **81º de 280 no perigo**, contra 280º, 275º e 273º no risco da linha de base. No risco continuam baixos (186º, 175º, 149º) mas por razão declarada — estão entre os municípios mais ricos do país. (b) **13 de 14 controles positivos cumprem a expectativa de perigo**, vários com folga: São José do Norte 3º, Laguna 4º, Bertioga 6º, São Sebastião 7º, Rio Grande 17º. A exceção é Linhares, 104º. (c) **Nenhum caso documentado no decil inferior** — que começa em 253º; o pior é Linhares em 188º. (d) **Os controles negativos do Norte saíram do topo do perigo**: Macapá 188º, Turiaçu 167º, Chaves 138º, Icatu 121º, todos no meio da distribuição. As posições que lhes restam no risco — Icatu 32º, Chaves 52º — vêm da vulnerabilidade, e são defensáveis porque o perigo é honesto. (e) **Uma divergência sobrevive, no topo**: **Magé 3º e Paraty 5º**. Magé, Duque de Caxias e Guapimirim compartilham um ponto de plataforma aberta a **34,7 / 35,2 / 30,3 km**, do outro lado da Baía de Guanabara; Paraty usa um ponto a **14,8 km** dentro da Baía da Ilha Grande. (f) **Divergência oposta, igualmente reportável**: Santa Vitória do Palmar é **1ª em perigo e 131ª em risco**; Osório 40º/156º; Itaboraí 29º/118º |
| **Interpretação** | A suíte separa três mecanismos distintos, e é essa separação que a torna útil. **Importação de perigo por associação** (Guanabara, Paraty): o perigo vem de fora da baía que abriga o município, e a inundação real ali é fluvial e pluvial — é AUD-04 aflorando onde mais custa, no top-5. **Supressão** (Santa Vitória do Palmar, Osório, Itaboraí): municípios fisicamente expostos e materialmente pouco privados, rebaixados pela anticorrelação que AUD-13 mediu. **MAUP do denominador** (Campos dos Goytacazes, Linhares): declarado em AUD-08. Nenhuma foi explicada por "é risco relativo", que a §9 proíbe expressamente. O saldo é que o produto passa no teste que a revisão de linha de base disse que ele reprovaria, e falha num ponto que ela também já havia identificado |
| **Alterações implementadas** | **Nenhuma no pipeline de cálculo.** Lista de referência nova, script diagnóstico read-only, parágrafo de validação qualitativa no `README.md`, e nota de ressalva na legenda de `top10_municipalities_by_integrated_risk.tex` — só a legenda; o CSV não mudou |
| **Validação realizada** | O script levanta erro se qualquer caso de referência não existir no conjunto entregue. Os 33 casaram. As distâncias ao ponto de grade foram calculadas em EPSG:5880 a partir do polígono municipal |
| **Incerteza remanescente** | (1) **Defeito na própria lista, registrado e não corrigido**: Fernando de Noronha recebeu `expectation_hazard = low`, mas não tem valor de perigo por não ter associação, e o veredito saiu "diverge (sem valor, mas um era esperado)". A inconsistência é da lista, não do produto — e **a lista não foi reeditada**, porque seu valor está em ter sido fixada antes. (2) Vários controles negativos do MA/PA saem como "diverge" no perigo por estarem no **meio** da distribuição (percentil 0,43–0,64), não por estarem altos; o limiar de 0,34 é estrito e o veredito mecânico não distingue "não é baixo" de "é alto". (3) A suíte não cobre casos do NE fora de PE, por não haver base de impactos regional — é a lacuna de AUD-18 |
| **Próxima decisão necessária** | Do pesquisador: aceitar e declarar a importação de perigo em Guanabara e Paraty, ou reabrir AUD-04 para aquele bloco |

### 2026-07-31 — DECISÃO: fechar como `mitigado-parcialmente`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | **Opção A — aceitar e declarar**, sem alterar o pipeline. Magé em 3º e Paraty em 5º permanecem, com o mecanismo nomeado no manuscrito e na legenda da tabela do artigo |
| **Coerência com decisão anterior** | AUD-04 fechou como `limitacao-reconhecida`: a associação município↔ponto é julgamento de especialista, versionada como dado de entrada. **Reabrir uma baía depois de ver o ranking seria seleção sobre o resultado** — exatamente o que a §10 desta questão proíbe |
| **Exigência que acompanha a decisão** | Declarar é aceitável; publicar a tabela de top-10 sem a ressalva **não é**. A legenda de `top10_municipalities_by_integrated_risk.tex` passou a registrar que Magé e Paraty carregam perigo importado de 35 km e 15 km, e que a inundação documentada ali é fluvial e pluvial |
| **Por que `mitigado-parcialmente`** | O bloco de SC — o caso que a §6.1 chamava de desqualificante — foi **recuperado**. A importação de perigo **permanece**. Nem `resultado-validado-mantido`, que esconderia a recuperação, nem `metodologia-alterada`, já que esta questão não tem correção própria |
| **O que o desfecho NÃO cobre** | (1) A importação de perigo, declarada e não corrigida. (2) A ausência de casos de referência no N/NE fora de PE — **AUD-18**. (3) O `SCIENTIFIC_NOTES.md` da raiz — **AUD-17 #4**, adiado para depois desta questão |
