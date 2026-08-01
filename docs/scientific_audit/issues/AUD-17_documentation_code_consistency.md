# AUD-17 — Oito inconsistências entre documentação, código e saídas, três delas materiais

| Campo | Valor |
|-------|-------|
| **ID** | AUD-17 |
| **Tipo** | `inconsistencia-documental` (confirmado por inspeção) |
| **Componente** | transversal |
| **Etapa do fluxo** | Step 4 (principalmente), README raiz |
| **Afeta** | documentação, saídas (metadados publicados) |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo correção — o README, como está, leva o leitor a reconstruir uma fórmula errada |
| **Status** | `em-investigacao` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-04, AUD-08, AUD-09, AUD-10, AUD-11, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §2.2, §8 item 16, §9.1 item 6 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 |

---

## 1. Problema

Oito divergências verificadas entre o que a documentação afirma, o que o código
faz e o que as saídas contêm — sete na revisão de linha de base, uma
(#8) encontrada durante a criação desta auditoria. Três são materiais: um leitor
do `README.md` reconstruiria a fórmula de risco **errada**, e duas
docstrings/metadados contêm afirmações **factualmente falsas** sobre o próprio
código.

Estão agrupadas numa única questão porque compartilham o mesmo tipo de trabalho
(correção de texto), o mesmo critério de aceitação (documentação e código
concordam) e a mesma verificação (releitura dirigida).

## 2. Por que importa cientificamente

- O `README.md` é o documento de entrada do repositório e o que será apontado na
  declaração de disponibilidade de código do manuscrito. Se ele descreve uma
  fórmula superada, a reprodutibilidade declarada é falsa.
- `risk_index_metadata.json` é **publicado no site** e se autocontradiz: afirma
  que um campo não é usado por nenhum produto publicado, enquanto a fórmula de
  risco no mesmo arquivo o usa como fator.
- Uma docstring que afirma "nada neste módulo alimenta o índice de risco
  publicado" leva um agente futuro — ou um coautor — a modificar o módulo
  acreditando que a mudança é inócua.

## 3. Evidência original — as sete inconsistências

### #1 — README declara a fórmula de risco superada · **Material**

`README.md` L405–408, seção "Current Implementation Status":

> *"Exposure spatialized via spatial join of oceanic hazard metrics to
> municipalities"*
> *"Risk_Hazard = norm_municipal[(SVI/100) × Hazard_Index]"*

Duas afirmações erradas:

- a fórmula é a de **duas** componentes, superada. A implementada
  (`export_risk_index_data.py` L576–583) é a média geométrica de **três**;
- descrever exposição como "spatial join of oceanic hazard metrics to
  municipalities" é exatamente o uso que o §4.1 do **mesmo README** declara
  errado e removido em 2026-07-28.

O §4.4 do README está correto. O documento se contradiz internamente.

### #2 — Docstring de `exposure_index.py` afirma não alimentar o risco · **Material**

`src/04_risk_integration/exposure_index.py` L47–48:

> *"Nothing in this module feeds the published risk index. It is wired into the
> website exposure layer and the exploratory comparisons only."*

Falso. `src/site/export_risk_index_data.py`:

- L48–55 importa `CLIP_FLOOR`, `GOALPOST_MAX_INHABITANTS`,
  `GOALPOST_MIN_INHABITANTS`, `exposure_absolute`, `exposure_inform`,
  `exposure_relative`;
- L563 chama `exposure_inform(population, municipal_population)`;
- L578 usa o resultado como fator de `Risk_Hazard_raw`.

### #3 — Metadados publicados afirmam que `Hazard_Index_mun` não é usado · **Material**

`src/site/export_risk_index_data.py`:

- L818–822 (`municipal_hazard_renormalization.purpose`):
  *"Provide a hazard component whose amplitude matches SVI/100 for equal-weight
  aggregations. It is not used by any published field."*
- L898–903 (`methodology.Hazard_Index_mun`):
  *"Provided for equal-weight aggregations; no published field uses it."*

Ambas falsas. No mesmo JSON, `integrated_risk_formula.expression` (L836–839) é:

```
Risk_Hazard_raw = (clip(Hazard_Index_mun) * clip(Exposure_Index)
                   * clip(SVI_Coast_2022/100)) ** (1/3)
```

E `export_risk_index_data.py` L577 confirma. O arquivo publicado no site
contradiz a si mesmo.

### #4 — `SCIENTIFIC_NOTES.md` referenciado não existe na raiz

`README.md` L293 remete a *"`SCIENTIFIC_NOTES.md` → 'Step 4 — Exposure,
Vulnerability & Risk Integration'"*. **O arquivo não existe na raiz do
repositório.** Existem apenas versões em submódulos:

- `src/02_threshold_calibration/04_csi_grid_scan/SCIENTIFIC_NOTES.md`
- `src/02_threshold_calibration/05_pu_composite_calibration/SCIENTIFIC_NOTES.md`
- `src/03_storm_catalog_generation/SCIENTIFIC_NOTES.md`

Nenhum contém uma seção "Step 4".

### #5 — Regra de associação documentada não se reproduz · **Material**

`README.md` L202–210 descreve a seleção do ponto como *"the point with the
highest compound-event count within the association"*. Reproduz-se em apenas
15–31 % dos municípios. Rastreado em detalhe em **AUD-04**; registrado aqui
apenas para completude do catálogo.

### #6 — Bloco "Products generated" duplicado no README

O §4.4 do `README.md` contém **duas** listas "Products generated" com conteúdos
diferentes (L286–292 e L295–302). A segunda repete parcialmente a primeira e
descreve `Risk_Hazard_raw` como *"unnormalized product of SVI fraction and
multimetric hazard"* — de novo a fórmula de duas componentes.

### #7 — Contagem de municípios inconsistente

`README.md` L406 diz *"281 coastal municipalities"*; o restante do documento
(L200, L217, L226, L93) diz **282**. O valor correto é 282 — 281 de
Lima et al. (2024) mais Balneário Rincão, conforme
`src/04_risk_integration/external_svi/README.md`.

### #8 — Mapa de estrutura do repositório desatualizado no README · *encontrada em 2026-07-29, na criação desta estrutura*

`README.md` L480–485 lista, sob `src/03_storm_catalog_generation/`, os módulos
`main.py`, `segmentation.py`, `metrics.py`, `io.py`, `tides.py` e `figures.py`
como se estivessem na raiz do diretório do Step 3. **Todos estão em
`src/03_storm_catalog_generation/01_storm_catalogs/`.**

Verificado:

```
src/03_storm_catalog_generation/
├── 01_storm_catalogs/   ← main.py, segmentation.py, metrics.py,
│                           io.py, tides.py, figures.py estão AQUI
├── 02_compound_detection/ … 08_site_export/
├── config/  shared/
└── hazard_characterization.py   ← este sim está na raiz
```

Consequência prática: um agente ou coautor que use o mapa do README para
localizar o código de detecção POT não encontra os arquivos. Esta inconsistência
**induziu erro real** durante a criação desta auditoria, corrigido em AUD-02 §4
e AUD-03 §4.

O README também lista `src/04_risk_integration/` com apenas três módulos
(`hazard_index.py`, `coastal_projection.py`, `palettes.py`); o diretório contém
ainda `exposure_index.py`, `municipal_exposure.py` e `external_svi/`.

### Item adicional já auditado, não contado entre os sete

`pop_house` é publicado **pré-normalizado** (Min–Max 0–1) enquanto o manuscrito o
define como residentes por domicílio (2,40–4,45 raw). A auditoria de 2026-07-28
(`src/04_risk_integration/external_svi/README.md`) demonstrou ser **inócuo para o
índice** e **real para a tabela publicada**, com a recomendação: *"Either the
manuscript definition or the published column should be changed so they agree."*
Pendência aberta.

## 4. Localização exata

| # | Arquivo | Linhas |
|---|---|---|
| 1 | `README.md` | 405–408 |
| 2 | `src/04_risk_integration/exposure_index.py` | 47–48 |
| 3 | `src/site/export_risk_index_data.py` | 818–822, 898–903 |
| 4 | `README.md` | 293 |
| 5 | `README.md` | 202–210 |
| 6 | `README.md` | 286–292 e 295–302 |
| 7 | `README.md` | 406 |
| 8 | `README.md` | 480–485 (Step 3) e 496–499 (Step 4) |
| extra | `outputs/risk_index/risk_index.shp` (col. `pop_house` vs. `pop_house_`) | — |
| novo (2026-07-29) | `src/figures_article/README.md` | 92–97 — mesma fórmula de duas componentes, aplicada à Figura C do multiplot; script já lê 4 painéis |
| novo (2026-07-29) | `site/README.md` | 214–222 — mesma fórmula de duas componentes; afirmação falsa de que `Hazard_Index_mun` não é oferecido como camada de mapa (é, ver `RiskIntegrationMap.tsx` e `available_layers` do metadata) |

### Saídas afetadas

- `site/public/data/risk_index_metadata.json` — contém as afirmações falsas de #3
  e é regenerado a cada execução do exportador.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Código correto; documentação parcialmente desatualizada; metadados publicados autocontraditórios |
| **Pretendido** | Documentação, código e metadados descrevendo a mesma coisa |

Vale registrar que **o código é a fonte confiável** em todos os sete casos. Este
não é um problema de implementação.

## 6. Divergência documentação ↔ implementação ↔ saídas

É a própria questão. Resumo por nível:

| Inconsistência | Documentação | Código | Saídas |
|---|---|---|---|
| #1 | errada | correto | corretas |
| #2 | errada (docstring) | correto | corretas |
| #3 | errada | correto | **erradas** (JSON publicado) |
| #4 | referência quebrada | — | — |
| #5 | errada | não implementa a regra | não verificáveis |
| #6 | duplicada e parcialmente errada | correto | corretas |
| #7 | inconsistente | correto | corretas |
| #8 | mapa de estrutura errado | correto | corretas |

## 7. Explicações alternativas plausíveis

1. **São resíduos de refatorações sucessivas**, todas documentadas no histórico
   do repositório (o índice migrou de duas para três componentes; a exposição foi
   redefinida em 2026-07-28). O README foi atualizado em algumas seções e não em
   outras. Explicação mais provável.
2. **A docstring #2 pode ter sido escrita antes** de o módulo ser conectado ao
   exportador e nunca revisada. Verificável no histórico do git.
3. **O `SCIENTIFIC_NOTES.md` da raiz pode ter sido planejado e não escrito.** As
   regras do projeto (`~/.claude/rules/scientific_notes_rules.md`) exigem esse
   arquivo para repositórios de artigo; a ausência é uma pendência real, não
   apenas uma referência quebrada.

## 8. Diagnósticos propostos

1. **Verificar cada uma das sete no estado atual do código** antes de corrigir —
   os números de linha citados são de 2026-07-29 e podem ter mudado.
2. **Varredura sistemática** de todas as fórmulas presentes em documentação e
   docstrings, confrontando com a implementação. Um script simples que extraia
   expressões de blocos de código dos `.md` e as compare com o código pode
   automatizar parte disso.
3. **Verificar o histórico do git** de `exposure_index.py` e
   `export_risk_index_data.py` para datar cada inconsistência e evitar que
   reapareçam.
4. **Auditar os demais README de submódulo** quanto às mesmas fórmulas.

## 9. Critérios objetivos de resolução

- [x] #1 — `README.md` "Current Implementation Status" descreve a fórmula de
      **três** componentes e a definição corrigida de exposição, coerente com §4.4.
      *(L397–400, verificado 2026-07-29)*
- [x] #2 — a docstring de `exposure_index.py` declara corretamente que o módulo
      alimenta `Risk_Hazard` via `export_risk_index_data.py`.
      *(L47–55, verificado 2026-07-29)*
- [x] #3 — os dois blocos de metadados sobre `Hazard_Index_mun` descrevem
      corretamente seu uso como fator do risco; **o JSON publicado foi corrigido**
      e validado como JSON íntegro. *(Correção aplicada diretamente ao arquivo
      publicado, não por regeneração completa — ver §14 sobre o motivo.)*
- [ ] #4 — existe `SCIENTIFIC_NOTES.md` na raiz, com a seção "Step 4" referenciada,
      seguindo as seções obrigatórias de `~/.claude/rules/scientific_notes_rules.md`;
      **ou** a referência foi removida do README. **Adiado deliberadamente** — ver §10.
- [x] #5 — remetido a AUD-04, **fechado em 2026-07-30**: o `README.md` §4.1 passou a descrever o método real da associação (inspeção visual em SIG, arbitrando proximidade e atividade de eventos) em vez da regra determinística que nunca existiu.
- [x] #6 — existe uma única lista "Products generated" no §4.4, correta.
      *(L286–294, verificado 2026-07-29)*
- [x] #7 — todas as menções à contagem de municípios dizem 282, com a nota sobre
      Balneário Rincão. *(única ocorrência de "281" remanescente é a citação correta
      de Lima et al. 2024 em L93; verificado por `grep -n "281" README.md`)*
- [x] #8 — o mapa de estrutura do `README.md` reflete a árvore real de
      `src/03_storm_catalog_generation/` e de `src/04_risk_integration/`,
      verificado contra a saída de `find src -name '*.py'`.
- [ ] extra — `pop_house` e sua definição no manuscrito concordam. **Não tocado**
      nesta sessão — exige decidir qual dos dois lados muda (decisão fora do escopo
      de uma correção puramente factual).
- [x] Uma releitura completa do `README.md` confirma que nenhuma fórmula ou
      descrição contradiz o código. **Verificado numericamente em 2026-07-31**, o
      que é mais forte que releitura: as **nove** fórmulas de §4.4
      (`Hazard_Frequency`, `Hazard_Severity`, `Hazard_Index_mun`, `pop_eff`,
      `Exposure_absolute`, `Exposure_relative`, `Exposure_Index`, `V`,
      `Risk_Hazard`) foram aplicadas aos campos publicados e **todas reproduzem o
      produto** com desvio máximo de **1,3e-06**, atribuível ao arredondamento a
      seis casas do GeoJSON. Ver §14.
- [x] #9 *(nova, 2026-07-31)* — a documentação não afirma mais que os Steps 3.1 e
      3.3–3.8 leem catálogos `SSH_total` superseded. Corrigido em `README.md`
      (§Step 3, §Current Implementation Status), `site/content/methodology.ts` e
      `site/content/project.ts`, contra `outputs/storm_catalog/logs/run_metadata.json`.
- [x] #10 *(nova, 2026-07-31)* — nenhum texto de documentação, do site ou de
      docstring descreve o Hazard Index com **três** componentes ou com a duração
      como componente. Verificado por `grep` em `README.md`, `site/**`, `src/**`.
- [x] #11 *(nova, 2026-07-31)* — nenhum texto descreve
      `Risk_Hazard_raw = (SVI/100) × Hazard_Index`. Verificado por `grep`.
- [x] #12 *(nova, 2026-07-31)* — as contagens de episódios, eventos e municípios
      publicadas no site batem com os produtos atuais.
- [x] #13 *(nova, 2026-07-31)* — a página do Step 2d declara que é diagnóstica e
      superseded, em vez de apresentar o par q90/q90 como resultado corrente.
- [x] **Rechecagem obrigatória depois de AUD-09 e AUD-12** — ver §15.
      **Resolvida por não ocorrência**: AUD-12 fechou sem excluir ponto algum e
      AUD-09 fechou sem tocar no SVI, logo nenhum dos dois gatilhos disparou. Os
      blocos condicionais da §15 ficam preservados como registro, vazios.

## 15. Checklist de rechecagem, a executar depois de AUD-09 e AUD-12

> Criada em 2026-07-31. AUD-09 e AUD-12 estão em `aguardando-decisao`; ambas
> podem ainda alterar produtos numéricos. Enquanto isso não se resolver, AUD-17
> permanece `em-investigacao`, e **nenhum** item abaixo pode ser marcado.
>
> ---
>
> ### RESOLUÇÃO, 2026-07-31 — os dois gatilhos **não dispararam**
>
> **AUD-12 fechou** como `resultado-validado-mantido`, com a recomendação
> explícita de **nenhum filtro**: nenhum ponto de grade foi excluído.
> **AUD-09 fechou** como `resultado-validado-mantido` **sem tocar no SVI** — a
> auditoria de direcionalidade demonstrou que não há indicador invertido, o PCA
> não foi refeito, e a mudança de escala (Φ em vez de Min–Max) foi decidida em
> AUD-11, é monótona e não alterou nenhuma carga nem a ordenação.
>
> **Portanto os dois blocos condicionais abaixo estão VAZIOS por não ocorrência,
> não por terem sido cumpridos.** Ficam preservados como registro do que teria
> sido preciso rechecar se os gatilhos tivessem disparado. Nenhum item deles
> exige ação.
>
> A verificação que **foi** feita, e que substitui esses blocos, está na §14,
> entrada de 2026-07-31 (varredura exaustiva): as fórmulas do `README.md` §4.4
> foram confrontadas **numericamente** com o produto publicado, e as nove
> reproduzem-no dentro do arredondamento do GeoJSON.

**Se AUD-09 mudar o SVI** *(gatilho não disparado — bloco vazio)* (o cenário hoje considerado improvável — não há erro
de codificação; o gatilho seria uma decisão de escopo sobre as âncoras de
Min–Max, junto com AUD-11):

- [ ] Tabela de cargas do PC1 em `README.md` §4.3 — recalcular todos os dez valores.
- [ ] Variância explicada por PC1 e PC2 (hoje 50,5 % e 16,5 %).
- [ ] r com `pop_poverty` (hoje +0,940) e ρ com log da população (hoje −0,491).
- [ ] Municípios de SVI exatamente 0 e 100 (hoje Balneário Camboriú e Chaves/PA),
      citados no README §4.3, nas limitações do manuscrito e em AUD-11.
- [ ] Extremos de SVI citados em AUD-09 §3.4 e no relatório para coautores.
- [ ] Regenerar `site/public/data/risk_index_municipalities.geojson` e
      `risk_index_metadata.json`, e as figuras do artigo dependentes
      (`hazard_vulnerability_risk_multiplot`, tabelas top-10,
      `supplementary_integrated_risk_zooms`).
- [ ] Reconferir todas as posições de ranking citadas em texto — em AUD-12 §14
      (Macapá 172º, Chaves 94º, Salvaterra 192º, Vigia 185º, Colares 188º), em
      AUD-15 §14 (faixa 191–280 dos 83 municípios de perigo nulo) e no README.
- [ ] Reconferir o parágrafo AUD-09 das limitações do manuscrito, inteiro.

**Se AUD-12 excluir pontos** *(gatilho não disparado — bloco vazio)* (hoje **não** recomendado):

- [ ] Contagem de pontos de grade: 808 aparece em `README.md`, em
      `site/content/*.ts`, nas páginas de metodologia e em vários metadados.
- [ ] Total de eventos compostos: **16 768**, e candidatos rejeitados pelo
      portão: **15 857**.
- [ ] Pontos sem evento aceito: **208** — e, por consequência, os **83**
      municípios de `Hazard_Index_mun` = 0 de AUD-15, com sua faixa de posições.
- [ ] Municípios com valor de risco: **280 de 282**; a lista de ausentes muda se
      algum município ficar órfão.
- [ ] Regenerar o índice de perigo nativo, a projeção costeira, o produto
      municipal e todas as figuras do artigo.
- [ ] Reconferir os números de AUD-03 §14, que são por ponto e mudam de
      denominador se o domínio mudar.
- [ ] Reconferir a recontagem de AUD-15 por inteiro.

**Independente das duas** — pendências herdadas que continuam abertas:

- [ ] #4 — `SCIENTIFIC_NOTES.md` na raiz, com a seção "Step 4" referenciada em
      `README.md`. Adiado desde 2026-07-29 para não escrever duas vezes; o
      método do Step 3 agora está estável, então o bloqueio é só o Step 4.
- [x] #5 — fechou com AUD-04 em 2026-07-30. *Duplicava o item já marcado na §9;
      a duplicata é que estava desatualizada.*
- [ ] "extra" — `pop_house` publicado pré-normalizado contra a definição do
      manuscrito. Exige decidir qual dos dois lados muda.
- [x] Varredura exaustiva dos `README.md` de submódulo do Step 2 e do Step 3, que
      nunca foi feita por inteiro. **Feita em 2026-07-31** sobre os **22**
      arquivos `.md` de `src/`, mais `README.md`, `site/content/` e `site/app/`,
      contra nove classes de resíduo. **Um achado material**, corrigido:
      `src/02_threshold_calibration/04_csi_grid_scan/README.md` L103 dizia que o
      par percentílico é "**currently** q90/q90", o que descreve o par do próprio
      diagnóstico como se fosse o par operante do projeto. Ver §14.
- [x] #14 *(nova, 2026-07-31)* — os diretórios de saída com esquema antigo estão
      **marcados e documentados**. `outputs/storm_catalog/compound/` revelou-se
      **misturado**, não legado: `compound_catalog.json` é corrente (regenerado
      2026-07-31, 16 768 eventos, idêntico a `compound_hat/` — 808/808 pontos,
      diferença máxima 0), enquanto `compound_metrics.csv` e
      `compound_summary.json` são de 2026-07-28 e reportam 96 031 eventos.
      Marcados com README em disco (`outputs/storm_catalog/README.md`,
      `compound/README.md`, `compound_mhws/README.md`) e na cópia versionada em
      `src/03_storm_catalog_generation/RUN.md`, já que `outputs/storm_catalog/`
      é ignorado pelo Git. Nada foi renomeado nem removido: três diagnósticos
      exploratórios de comparação antes/depois leem os arquivos legados por
      caminho. Corrigido também `outputs/hat_method/README.md`, que ainda dizia
      *"Não substitui o método MHWS vigente"*, e acrescentado
      `outputs/current_method_hat/README.md`, que não existia.

---

## 10. Riscos de alteração prematura

- **Corrigir o README antes de AUD-01, AUD-04 e AUD-06** significa reescrever
  duas vezes, porque essas questões podem mudar o método. Recomenda-se corrigir
  agora as inconsistências que descrevem o **estado atual** (#1, #2, #3, #6, #7) e
  adiar #4 (o `SCIENTIFIC_NOTES.md` deve refletir o método final).
- **Editar `export_risk_index_data.py`** para corrigir #3 exige **regenerar** o
  JSON publicado; corrigir apenas o código-fonte deixa o site com o texto antigo.
- Cuidado para não corrigir uma docstring de forma que passe a descrever um
  comportamento **desejado** em vez do **implementado** — o erro seria simétrico.

## 11. Condições sob as quais o resultado atual pode ser mantido

Nenhuma. Afirmações factualmente falsas sobre o próprio código não têm
justificativa. Esta é a única questão da auditoria sem cenário de manutenção do
estado atual.

É também a **mais barata de resolver** e a única que pode ser fechada
integralmente sem depender de nenhuma decisão científica.

## 12. Produtos a jusante que exigiriam regeneração

Apenas para #3. **Atualizado 2026-07-29**: a regeneração completa via

```bash
python -m src.site.export_risk_index_data   # regenera risk_index_metadata.json
```

foi testada e descartada nesta sessão porque produz uma diferença de
simplificação de geometria não relacionada (ver §14, achado "d") neste
ambiente. `site/public/data/risk_index_metadata.json` foi corrigido por edição
direta das duas strings falsas, preservando o restante do arquivo
byte-a-byte. **Se o exportador for executado por qualquer outro motivo no
futuro** (nova associação de município, novo catálogo, etc.), a regeneração
completa passará a ser o caminho correto novamente — a edição cirúrgica foi
uma medida desta sessão, não uma prática permanente.

As demais correções (#1, #2, #6, #7, #8) são de texto sem efeito em produto.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | `src/02_threshold_calibration/04_csi_grid_scan/README.md` (L103), este registro (§9, §14, §15) | Varredura exaustiva dos 22 `.md` de `src/` + verificação numérica das nove fórmulas de §4.4 contra o produto publicado. **Nenhum valor numérico alterado** |
| 2026-07-29 | `e2680ed` | `main` | `README.md`, `site/README.md`, `site/public/data/risk_index_metadata.json`, `src/04_risk_integration/exposure_index.py`, `src/site/export_risk_index_data.py`, `src/figures_article/README.md` | Correção de #1, #2, #3, #6, #7, #8 e dos dois resíduos adicionais encontrados por varredura. Puramente documental; nenhum valor numérico publicado alterado |

> **Nota.** A criação da estrutura de auditoria em `docs/scientific_audit/`
> **não** corrigiu nenhuma destas sete inconsistências. O commit `e2680ed`,
> acima, é que as corrigiu — e apenas as seis sem decisão científica pendente.
> Os itens **#4** (`SCIENTIFIC_NOTES.md` na raiz) e **#5** (remetido a AUD-04),
> mais o item "extra" (`pop_house`), **permanecem abertos** no estado descrito
> na §3.
>
> O commit foi criado pelo autor do repositório e agrega, além destas
> correções, a estrutura `docs/scientific_audit/` e o primeiro script
> diagnóstico de AUD-01 — seu escopo é, portanto, mais amplo que esta questão.

## 14. Histórico de investigação

### 2026-07-29 — Catalogação; descoberta da inconsistência #8

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | As sete inconsistências da revisão de linha de base persistem? Existem outras? |
| **Dados e métodos** | Releitura dirigida de `README.md`, `exposure_index.py`, `export_risk_index_data.py`; varredura automática de todos os caminhos de arquivo citados nos registros da auditoria contra o sistema de arquivos |
| **Scripts executados** | Nenhum versionado — verificação por `grep` e `find` durante a criação de `docs/scientific_audit/` |
| **Novas saídas geradas** | Nenhuma |
| **Achados** | As sete persistem, sem alteração. Descoberta a **#8**: o mapa de estrutura do README aponta `segmentation.py`, `metrics.py`, `io.py`, `tides.py`, `figures.py` e `main.py` na raiz de `src/03_storm_catalog_generation/`, quando estão em `01_storm_catalogs/`; e omite três módulos de `src/04_risk_integration/` |
| **Interpretação** | A #8 tem consequência prática demonstrada: induziu erro de referência na redação de AUD-02 §4 e AUD-03 §4, corrigido na mesma sessão. Um agente futuro que confie no mapa do README não encontra o código de detecção POT |
| **Alterações implementadas** | **Nenhuma no código nem no README.** Apenas correção dos caminhos dentro dos registros AUD-02 e AUD-03 desta auditoria |
| **Validação realizada** | Varredura automática confirma que todo caminho citado nos registros existe, exceto os prospectivos de `outputs/audit/` e `src/exploratory/audit_*.py`, que são saídas ainda a criar |
| **Incerteza remanescente** | Não foi feita varredura exaustiva dos README de submódulo (diagnóstico 4) |
| **Próxima decisão necessária** | Aplicar as correções de #1, #2, #3, #6, #7 e #8, que descrevem o estado atual e não dependem de decisão científica pendente. Adiar #4 (`SCIENTIFIC_NOTES.md`) e #5 (remetida a AUD-04) |

### 2026-07-29 — Correção de #1, #2, #3, #6, #7, #8; varredura por resíduos além dos arquivos citados

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | As seis correções sem decisão científica pendente (#1, #2, #3, #6, #7, #8) podem ser aplicadas sem alterar nenhum resultado numérico, e existem inconsistências do mesmo tipo em arquivos não citados no registro original? |
| **Dados e métodos** | Releitura de `README.md` (L286–312, L397–401, L472–499), `src/04_risk_integration/exposure_index.py` (L1–56), `src/site/export_risk_index_data.py` (L544–583, L790–920). Reconstrução da fórmula a partir do código (não da documentação), conforme exigido pelo procedimento. Varredura por `grep -rn` de todas as frases citadas como falsas em #1–#3, #6, #7 em todo o repositório (`.py`, `.md`, `.json`), para além dos arquivos listados na §4 do registro original |
| **Scripts executados** | Nenhum script novo. `grep`/`find` para varredura textual; `python -m src.site.export_risk_index_data` executado uma vez para testar a regeneração do JSON publicado (ver "Achados" sobre por que o resultado foi descartado) |
| **Novas saídas geradas** | Nenhuma output de análise. `site/public/data/risk_index_metadata.json` foi editado diretamente (duas strings), não regenerado |
| **Achados** | (a) As seis inconsistências descritas em #1, #2, #3, #6, #7, #8 foram confirmadas byte a byte no estado atual do código antes da correção — nenhuma tinha sido corrigida por sessões anteriores. (b) `export_risk_index_data.py` L577 confirma a fórmula de três componentes; nenhuma ambiguidade. (c) A varredura por resíduos encontrou **duas inconsistências adicionais do mesmo tipo**, não listadas no registro original: `src/figures_article/README.md:97` descrevia a fórmula de duas componentes para a Figura C do multiplot artigo, enquanto o script `make_article_hazard_vulnerability_risk_multiplot.py` (L73–99) já lê `Hazard_Index_mun` e `Exposure_Index` como painéis A e B — o script tem 4 painéis, a documentação descrevia 3; `site/README.md:214-222` também continha a fórmula de duas componentes e afirmava que `Hazard_Index_mun` "is not offered as a map layer", o que é falso: `risk_index_metadata.json.available_layers` e `site/components/RiskIntegrationMap.tsx` confirmam que é uma camada selecionável. Ambas corrigidas pelo mesmo critério do item #1/#3 (código como fonte de verdade, sem ambiguidade). (d) **Efeito colateral identificado e revertido**: a regeneração completa via `python -m src.site.export_risk_index_data` produz um `risk_index_municipalities.geojson` com simplificação de geometria numericamente diferente da versão versionada (46.977 vs. 47.730 coordenadas após simplificação; `coordinates_after` no metadata muda também), embora **todas as 282 propriedades municipais e a ordem dos registros permaneçam idênticas** (verificado por comparação campo a campo em Python — zero municípios com qualquer propriedade numérica alterada). A causa provável é deriva de versão do GEOS/Shapely neste ambiente frente ao ambiente que gerou o commit anterior, não uma mudança de dado ou de método. Como esse efeito está fora do escopo de uma correção textual, a regeneração completa foi **descartada** (`git checkout` do geojson e do metadata.json) e as duas strings falsas do metadata foram corrigidas por edição direta e cirúrgica do JSON publicado, preservando geometria e `generated_at`/`coordinates_after` originais |
| **Interpretação** | Confirma a conclusão do registro original: em todos os casos verificados, o código é a fonte confiável e a documentação estava desatualizada por resíduo de refatoração. Nenhuma das correções aplicadas envolveu escolha metodológica. O efeito colateral de simplificação geométrica (item d) é uma **descoberta nova**, de natureza puramente ambiental/de reprodutibilidade de biblioteca, não uma fragilidade científica — registrada aqui para rastreabilidade, mas **não é uma sub-questão de AUD-17** nem foi convertida em questão nova, por não afetar nenhum valor publicado |
| **Alterações implementadas** | `README.md` (fórmula de 2→3 componentes em "Current Implementation Status"; contagem 281→282; lista "Products generated" duplicada consolidada em uma única lista correta; mapa de estrutura de `03_storm_catalog_generation/` e `04_risk_integration/` corrigido); `src/04_risk_integration/exposure_index.py` (docstring corrigida, distinguindo `exposure_inform` — usada no risco — de `exposure_absolute`/`exposure_relative` — publicadas mas não usadas no produto de risco — das variantes puramente exploratórias); `src/site/export_risk_index_data.py` (dois blocos de metadados `purpose`/`methodology.Hazard_Index_mun` corrigidos); `site/public/data/risk_index_metadata.json` (as mesmas duas strings, editadas diretamente); `src/figures_article/README.md` (fórmula e contagem de painéis corrigidas); `site/README.md` (fórmula e afirmação sobre camada de mapa corrigidas). **Nenhum arquivo em `outputs/` foi alterado. Nenhum valor de `Risk_Hazard`, `Hazard_Index` ou qualquer campo numérico publicado mudou** |
| **Validação realizada** | (1) JSON publicado validado com `json.load` após a edição — íntegro. (2) Comparação campo a campo do `risk_index_municipalities.geojson` candidato (gerado, depois descartado) contra o commitado: 282/282 municípios com propriedades idênticas, mesma ordem, zero diferenças numéricas — confirma que a correção de metadados não teria alterado nenhum resultado científico mesmo se a regeneração completa tivesse sido mantida. (3) `grep -rn` pós-edição confirma que nenhuma das frases falsas originais (fórmula de duas componentes, "not used by any published field", "spatial join of oceanic hazard metrics", "281 coastal municipalities" fora do contexto correto) permanece em nenhum arquivo do repositório fora dos documentos imutáveis de auditoria |
| **Incerteza remanescente** | (1) Deriva de simplificação geométrica entre ambientes (achado d) não foi investigada a fundo — não se sabe se é GEOS, Shapely, GDAL/pyogrio, ou uma diferença de plataforma; recomenda-se registrar a versão exata das bibliotecas geoespaciais no `environment.yml` se ainda não estiver fixada, mas isso é uma melhoria de reprodutibilidade de infraestrutura, não uma questão de auditoria científica. (2) A varredura por resíduos não foi exaustiva sobre todos os `README.md` de submódulo do Step 2/Step 3 (apenas os que citam `Risk_Hazard =` ou `Hazard_Index_mun` foram varridos); nenhuma ocorrência adicional foi encontrada nessa varredura direcionada, mas uma varredura completa de todo o repositório não foi realizada |
| **Próxima decisão necessária** | #4 (`SCIENTIFIC_NOTES.md` na raiz) permanece deliberadamente adiado até que o método final do Step 3/4 esteja decidido (AUD-01 e relacionadas), para não escrever o documento duas vezes. #5 fecha junto com AUD-04. O item "extra" (`pop_house` pré-normalizado) exige decidir se a definição do manuscrito ou a coluna publicada deve mudar — não é uma correção puramente factual e não foi tocado. Nenhuma consulta ao usuário foi necessária nesta sessão: todas as seis correções aplicadas eram inequívocas pelo critério da §3 do procedimento |

### 2026-07-31 — Cinco inconsistências novas (#9–#13), todas criadas pela mudança de método

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Depois da adoção do detector q70/q99 com portão HAT (AUD-01/AUD-06) e da regeneração do Step 3, que afirmações da documentação, do site e das docstrings ficaram falsas? |
| **Dados e métodos** | Varredura dirigida por `grep` sobre `README.md`, `site/content/*.ts`, `site/app/**/*.tsx`, `src/**/*.py` e `src/**/*.md`, procurando as classes de resíduo listadas na instrução de sessão: q90/q90; `SSH_total` como variável segmentada; três componentes no Hazard Index; duração média como resultado principal; intensidade de pico no lugar da severidade integrada; contagens antigas de eventos ou pontos; Step 3 descrito como parcial; vulnerabilidade física declarada; contagens municipais antigas. Cada achado foi confrontado com a **fonte de verdade correspondente** — `outputs/storm_catalog/logs/run_metadata.json`, os cabeçalhos dos CSV do Step 3, `src/04_risk_integration/hazard_index.py` e `src/site/export_risk_index_data.py` — antes de qualquer edição |
| **Scripts executados** | Nenhum novo. `grep`/`sed`; verificação cruzada dos limiares do Step 3.1 contra os do Step 3.2 em Python |
| **Novas saídas geradas** | Nenhuma |
| **Achados** | **#9 — Step 3 descrito como parcialmente superseded, e não está.** `README.md` §Step 3 marcava 3.1 e 3.3–3.8 como *(superseded inputs)* e afirmava que liam catálogos `SSH_total` a q90/q90; `site/content/methodology.ts` e `site/content/project.ts` repetiam a afirmação. É **falso** desde o commit `eee6142` (2026-07-31 02:50): `outputs/storm_catalog/logs/run_metadata.json` registra `level_var: "zos"`, `level_is_tide_free: true`, `thr_hs_pct: 0.7`, `thr_level_pct: 0.99`, e os CSV de 3.3–3.8 trazem colunas `zos_*` e não `ssh_total_*`. Verificação adicional: os limiares de nível de 3.1 e 3.2 **coincidem exatamente nos 808 pontos** (diferença máxima 0,0 m) e as contagens de episódios diferem no máximo em 1. **#10 — Hazard Index de três componentes.** Resíduo extenso: `site/content/{project,results,methodology}.ts`, `site/app/methodology/hazard-index/page.tsx` (título "The three components of the index", peso 1/3, "as três componentes devem compartilhar escala"), `site/app/methodology/compound-detection/page.tsx`, `site/app/results/risk-integration/page.tsx` e `src/03_storm_catalog_generation/SCIENTIFIC_NOTES.md`. Curiosamente a página do índice já tinha o bloco de equação com a fórmula de **duas** componentes, mas toda a prosa em volta ainda dizia três — meia correção anterior. **#11 — `Risk_Hazard_raw = (SVI/100) × Hazard_Index`** ainda em `site/content/methodology.ts`, `site/content/results.ts`, `site/app/methodology/compound-detection/page.tsx` e no metadado `published_formula` de `src/exploratory/make_exploratory_risk_with_exposure.py` — a mesma fórmula de duas componentes que #1 corrigira no README em 2026-07-29, sobrevivendo em quatro outros arquivos. **#12 — contagens antigas**: "404 535 Hₛ + 324 929 SSH_total", "~96k eventos compostos" e "281 municípios" em `site/content/*.ts` e em `src/03_storm_catalog_generation/{PIPELINE_SETUP,SCIENTIFIC_NOTES}.md`. Os valores atuais são 707 453, 42 455, 16 768 e 282. **#13 — a página do Step 2d não se declara superseded**: apresentava o par q90/q90 como resultado, sem nenhuma indicação de que é diagnóstico e de que a calibração de produção é do Step 2e. Também encontrado, e **não** corrigido: `outputs/storm_catalog/compound/` e `compound_mhws/` seguem na árvore corrente com o schema antigo, e o docstring de `src/site/export_risk_index_data.py` L89 ainda aponta `compound/compound_metrics.csv` como fonte do perigo, quando o código lê `compound_hat/compound_metrics_hat.csv` via `hazard_index.py` |
| **Interpretação** | Mesma etiologia dos oito originais — resíduo de refatoração —, mas com uma diferença que vale registrar: **a regeneração do Step 3 criou a inconsistência #9 ao *melhorar* o produto**. A documentação era verdadeira quando foi escrita e passou a ser falsa por causa de um commit que corrigiu ciência. Isso é o argumento mais forte a favor de manter AUD-17 aberta enquanto AUD-09 e AUD-12 puderem mexer nos produtos, e é a razão da checklist da §15. Em todos os treze casos o código continua sendo a fonte confiável; nenhuma correção envolveu escolha metodológica |
| **Alterações implementadas** | `README.md` (§Step 3 reescrito como completo, com a proveniência do rerun; §Current Implementation Status; §2c com a limitação de fase de AUD-03; §Conceptual Framework e tabela de fontes por AUD-10; §4.2 por AUD-14 e AUD-15; §4.3 reescrita com as cargas do PC1 por AUD-09; seção nova "Declared limitations for the manuscript"); `site/content/{project,results,methodology}.ts`; `site/app/methodology/hazard-index/page.tsx`; `site/app/methodology/compound-detection/page.tsx` (22 substituições: variável de nível, portão HAT, tabelas de métricas, fórmula de risco, Assumptions); `site/app/results/risk-integration/page.tsx`; `site/app/results/threshold-calibration/csi-scan/page.tsx` (banner de superseded); `src/03_storm_catalog_generation/{SCIENTIFIC_NOTES.md,config/analysis_config.py}`; `src/exploratory/make_exploratory_risk_with_exposure.py`. **Nenhum arquivo de `outputs/` alterado; nenhum valor numérico publicado mudou** |
| **Validação realizada** | (1) Cada afirmação corrigida foi conferida contra a fonte de verdade antes da edição, nunca contra outra documentação. (2) Coincidência exata dos limiares de nível entre Step 3.1 e Step 3.2 verificada nos 808 pontos. (3) Contagem de `Hazard_Index_mun == 0` (83) e de exposição no piso (2) conferidas diretamente no GeoJSON publicado. (4) Verificação estrutural dos sete arquivos `.ts`/`.tsx` editados — contagem de crases, chaves, parênteses, colchetes e balanço de tags — comparada contra o estado pré-edição via `git stash`: **o delta de aberturas é igual ao delta de fechamentos em todos**, ou seja nenhuma edição desbalanceou marcação. (5) `grep` posterior confirma que nenhuma das frases falsas permanece fora dos documentos imutáveis de auditoria |
| **Incerteza remanescente** | (1) **O build do site não foi executado.** Não há Node.js neste ambiente — `npm` não existe, `node_modules/` está ausente e nenhum ambiente conda o fornece. A verificação estrutural acima é um substituto, não um compilador: ela não detectaria erro de tipo TypeScript nem prop inválida. **O build precisa ser rodado antes do deploy.** (2) A varredura foi dirigida às classes de resíduo listadas na instrução; não foi exaustiva sobre todos os `README.md` de submódulo. (3) `PIPELINE_SETUP.md` e `SCIENTIFIC_NOTES.md` do Step 3 mantêm tabelas de tempo de execução e contagens antigas fora dos pontos corrigidos. (4) Os diretórios de saída legados não foram marcados nem movidos |
| **Próxima decisão necessária** | Manter `em-investigacao`. Rodar o build do site num ambiente com Node. Executar a checklist da §15 quando AUD-09 e AUD-12 fecharem |

### 2026-07-31 (cont.) — Marcação dos diretórios de saída com esquema antigo (#14)

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Quais diretórios de `outputs/` carregam esquema de método superseded, e é seguro renomeá-los ou removê-los? |
| **Dados e métodos** | Inspeção de datas de modificação e de cabeçalhos de coluna em `outputs/storm_catalog/{compound,compound_mhws,compound_hat}/` e nos três `catalog_*.json`; conferência cruzada de `compound/compound_catalog.json` contra `compound_hat/compound_metrics_hat.csv` ponto a ponto; `git ls-files` e `.gitignore` para saber o que é versionado; `grep` dos consumidores de cada caminho |
| **Scripts executados** | Nenhum novo. Verificação em Python e `cmp` |
| **Novas saídas geradas** | `outputs/storm_catalog/README.md`, `outputs/storm_catalog/compound/README.md`, `outputs/storm_catalog/compound_mhws/README.md`, `outputs/current_method_hat/README.md` |
| **Achados** | (a) **`compound/` não é um diretório legado — é misturado**, o que é pior. `compound_catalog.json` foi regenerado em 2026-07-31 e confere exatamente com o produto vigente (808/808 pontos casados, diferença máxima de `compound_count_total` = 0, soma 16 768 nos dois). Os outros dois arquivos são de 2026-07-28 e o sumário reporta **96 031** eventos. Quem abre os dois lado a lado vê 16 768 contra 96 031 sem nenhuma indicação de que são métodos diferentes. (b) `compound_mhws/` é legado inteiro, e `catalog_ssh_total_storms.json` (2026-04-15) também. (c) **`outputs/storm_catalog/` é ignorado pelo Git**, de modo que um README ali não é rastreável — a documentação durável precisava ir para um arquivo versionado. (d) `outputs/hat_method/README.md` terminava com *"Este é um braço comparativo. Não substitui o método MHWS vigente"*, falso desde 2026-07-31, e o instantâneo que ele descreve é do par **q90/q90** (37 225 eventos), não do par calibrado. (e) `outputs/current_method_hat/` — o instantâneo versionado do produto vigente — **não tinha README nenhum**, embora seja idêntico byte a byte ao caminho lido em tempo de execução |
| **Interpretação** | Marcar, não apagar. Os arquivos legados são lidos por caminho por três diagnósticos exploratórios (`make_exploratory_hazard_index_comparison.py`, `make_exploratory_q90_hs_zos_fes_coastal_map.py`, `audit_AUD_01_validity_domain_partition.py`) e por cinco que leem o braço MHWS — e são justamente as comparações antes/depois que sustentam AUD-01, AUD-02 e AUD-06. Renomeá-los quebraria a reprodutibilidade da própria auditoria, que é o oposto do objetivo. A marcação por README preserva a rastreabilidade e remove a armadilha |
| **Alterações implementadas** | Quatro README novos (acima); tabela de saídas de `src/03_storm_catalog_generation/RUN.md` reescrita com as linhas legadas tachadas e uma advertência sobre o diretório misturado; `outputs/hat_method/README.md` corrigido. **Nenhum arquivo de dados renomeado, movido ou removido; nenhum valor numérico alterado** |
| **Validação realizada** | `cmp` confirma que `outputs/current_method_hat/` é idêntico byte a byte a `outputs/storm_catalog/compound_hat/` nos dois arquivos. O par de limiares de cada instantâneo foi lido do próprio `compound_summary_hat.json`: `hat_method` sem par registrado e 37 225 eventos; `current_method_hat` e `compound_hat` com 0,7/0,99 e 16 768 |
| **Incerteza remanescente** | Os README de `outputs/storm_catalog/` **não são versionados** e desaparecem se o diretório for regenerado do zero. A cópia durável é a tabela de `RUN.md`; se o Step 3 for reexecutado, os README de disco precisam ser reescritos à mão, ou o passo de escrita deveria ser incorporado ao próprio pipeline — melhoria não implementada |
| **Próxima decisão necessária** | Nenhuma. Correção factual sem escolha metodológica |

### 2026-07-31 (cont.) — Varredura pós-implementação das normalizações fixas

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | As superfícies atuais do site, READMEs, docstrings e metadados publicados descrevem a implementação de AUD-08/AUD-09/AUD-11, sem resíduos da cadeia Min–Max/piso anterior? |
| **Dados e métodos** | Varredura dirigida por `rg` sobre `README.md`, `site/`, `src/site/` e `src/figures_article/`, seguida de confronto com `hazard_index.py`, `exposure_index.py` e `integrated_risk()`. Arquivos explicitamente legados e comparações antes/depois foram preservados. |
| **Scripts executados** | `python -m src.site.export_risk_index_data`; `python -m src.site.export_coastal_hazard_data`; `PYTHONPATH=. pytest -q tests`; `npm run lint`; `npm run build` em `site/`. |
| **Novas saídas geradas** | `site/public/data/risk_index_metadata.json` e `site/public/data/coastal_hazard_metadata.json`, regenerados pelas fontes corrigidas. Os GeoJSON foram verificados e permaneceram sem diferença versionada. |
| **Achados** | O cálculo já usava âncoras fixas e risco sem piso/Min–Max, mas ainda havia prosa falsa no cabeçalho do exportador de risco, nos dois READMEs principais, no README das figuras, em `site/content/`, nas páginas de Compound Detection/Hazard Index/Risk Integration e no metadado costeiro. Também havia descrição obsoleta do multiplot como quatro painéis e do `Hazard_Index_mun` como renormalizado. |
| **Alterações implementadas** | Todas as superfícies atuais passaram a registrar: hazard com âncoras 99 e 1; nenhuma segunda ou municipal Min–Max; exposição baseada em `pop_eff` das quatro bandas cumulativas e goalposts fixos; vulnerabilidade `Phi(PC1/sd, ddof=0)`; risco geométrico sem piso e sem Min–Max final. O rótulo `actual_field` de `Hazard_Index` e as descrições do exportador costeiro foram corrigidos na fonte geradora. |
| **Validação realizada** | Testes científicos: 4 aprovados. Site: ESLint aprovado; build estático Next.js aprovado, 21 páginas. JSON carregado com sucesso. Varredura residual encontrou apenas a fórmula antiga dentro do campo explicitamente `superseded` e frases que afirmam corretamente a ausência de piso/Min–Max. |
| **Incerteza remanescente** | AUD-17 permanece aberta pelas pendências independentes já registradas; esta passagem resolve apenas os resíduos factuais relacionados à normalização atual. |
| **Próxima decisão necessária** | Nenhuma para esta classe de inconsistência. Manter fórmulas antigas somente em arquivos `legacy`, diagnósticos comparativos e campos marcados `superseded`. |

### 2026-07-31 — Varredura exaustiva dos submódulos e verificação numérica das fórmulas

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Três: (a) a varredura exaustiva dos `.md` de submódulo, registrada como incerteza remanescente desde 2026-07-29 e nunca feita, revela resíduo? (b) As fórmulas do `README.md` §4.4 de fato reproduzem o produto publicado? (c) As seis sessões de auditoria posteriores introduziram inconsistências novas? |
| **Dados e métodos** | Inventário completo: **22** arquivos `.md` em `src/`, mais `README.md`, `site/content/` e `site/app/`. Varredura por nove classes de resíduo — `q90/q90`; `SSH_total` como variável segmentada; perigo de três componentes ou duração como componente; piso de 0,01 e `CLIP_FLOOR`; `norm_municipal`; e as contagens antigas 96 031, 404 535, 324 929 e "281 municípios" — excluindo deliberadamente os contextos `legacy`, `superseded` e de comparação antes/depois. Depois, **verificação numérica**: cada uma das nove fórmulas de §4.4 aplicada aos campos publicados de `risk_index_municipalities.geojson` e de `compound_metrics_hat.csv`, e confrontada com o campo correspondente |
| **Scripts executados** | Nenhum novo. `grep`/`find` para a varredura; verificação numérica em Python, ad hoc |
| **Novas saídas geradas** | Nenhuma |
| **Achados** | (a) **Um achado material, corrigido**: `src/02_threshold_calibration/04_csi_grid_scan/README.md` L103 afirmava que o par percentílico é "**currently** q90/q90". O Step 2d é diagnóstico e q90/q90 é o ótimo **dele**, mas "currently" descreve-o como par operante do projeto, que é q70/q99. Reescrito para dizer explicitamente que q90/q90 **não** é o par operante. (b) **O encadeamento dos Steps 3 e 4 está limpo** — nenhuma das nove classes de resíduo aparece fora de contexto legado. As ocorrências de `SSH_total` em `src/01_data_preparation/preprocessing/README.md` e em `src/02_threshold_calibration/04_csi_grid_scan/RUN.md` estão **corretas**: o Step 1 de fato deriva essa variável e o Step 2c de fato a confirmou; são etapas a montante, não resíduo. (c) O `README.md` do Step 2e traz um aviso global — "onde o texto abaixo diz `SSH_total`, leia `zos`; onde diz q90/q90, leia q70/q99" — que **mitiga sem corrigir**; fica registrado como fraqueza conhecida, não como inconsistência. (d) **Consistência numérica confirmada**: 808 pontos, 16 768 eventos, 208 pontos sem evento, 282/280 municípios e 84 riscos nulos batem em todos os arquivos que os citam. (e) **As nove fórmulas de §4.4 reproduzem o produto publicado**, desvio máximo **1,3e-06** — arredondamento do GeoJSON |
| **Interpretação** | A varredura que faltava era menos grave do que o registro temia, e por uma razão específica: as inconsistências #9–#14 de 2026-07-31 já haviam varrido o Step 3, o Step 4 e o site, que são justamente onde o método mudou. O que restava não varrido era o Step 2, cuja documentação descreve etapas a montante que **não** mudaram — daí um único achado. A verificação numérica é o ganho real desta entrada: substitui "uma releitura confirma que nada contradiz o código" por uma demonstração de que a documentação **reconstrói o produto**, que é o que um leitor da declaração de disponibilidade de código precisa |
| **Alterações implementadas** | `src/02_threshold_calibration/04_csi_grid_scan/README.md` L103. **Nenhum valor numérico publicado alterado** |
| **Validação realizada** | A verificação numérica é ela própria a validação: partiu dos campos publicados, não do código, de modo que confirma documentação **e** produto simultaneamente |
| **Incerteza remanescente** | (1) O aviso global do `README.md` do Step 2e continua sendo mitigação, não correção — o texto abaixo dele segue dizendo `SSH_total` e q90/q90. (2) `PIPELINE_SETUP.md` e `SCIENTIFIC_NOTES.md` do Step 3 mantêm tabelas de tempo de execução antigas fora dos pontos corrigidos, já registrado em 2026-07-31. (3) **O build do site não foi executado nas últimas seis sessões** — o pesquisador declarou em 2026-07-31 que verifica localmente |
| **Próxima decisão necessária** | Duas, do pesquisador, e são as únicas que impedem AUD-17 de fechar: **#4** (`SCIENTIFIC_NOTES.md` na raiz) e o item **"extra"** (`pop_house`). Ver a entrada seguinte |

### 2026-07-31 — As duas pendências que restam exigem decisão

| Campo | Conteúdo |
|-------|----------|
| **#4 — `SCIENTIFIC_NOTES.md` na raiz** | `README.md` L293 remete a *"`SCIENTIFIC_NOTES.md` → 'Step 4 — Exposure, Vulnerability & Risk Integration'"* e **o arquivo não existe na raiz**. Existem versões em submódulos, nenhuma com seção "Step 4". Foi **adiado deliberadamente desde 2026-07-29** para não escrever o documento duas vezes, enquanto o método pudesse mudar. **O bloqueio acabou**: todas as questões de método estão fechadas — AUD-01, AUD-02, AUD-06, AUD-11, AUD-13 — e o método está estável desde `eee6142`. As opções são **escrever o documento** ou **remover a referência**; a primeira é exigida pelas regras de repositório de artigo do pesquisador |
| **"extra" — `pop_house`** | Publicado **pré-normalizado** (Min–Max 0–1) enquanto o manuscrito o define como residentes por domicílio (2,40–4,45). A auditoria de 2026-07-28 demonstrou ser **inócuo para o índice** — Min–Max e z-score são afins, matrizes padronizadas idênticas a 5,7e-15 — e **real para a tabela publicada**. Exige decidir qual lado muda. **Recomendação**: alterar a **definição no manuscrito** para descrever a coluna como ela é, porque a alternativa exige recomputar um produto de autoria externa, o que a auditoria evitou deliberadamente em todas as outras decisões sobre o SVI |
| **Estado da questão** | `em-investigacao`. Todos os demais critérios da §9 e da §15 estão verificados |
