# AUD-02 — Limiares de "onda extrema" fisicamente vazios no Norte (transferência do q90 calibrado em SC)

| Campo | Valor |
|-------|-------|
| **ID** | AUD-02 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | perigo |
| **Etapa do fluxo** | Step 2e (calibração) → Step 3.1 (catálogos) → Step 3.2 (compostos) |
| **Afeta** | dados, interpretação, saídas, documentação |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — um "evento de onda extrema" com Hs = 0,20 m não é defensável sob nenhum enquadramento |
| **Status** | `resolvido` |
| **Desfecho** | `limitacao-reconhecida` — o piso não é derivável dentro do pipeline atual, e o abrigo não é separável de célula duvidosa por nenhuma regra enunciável aqui. A quantidade passa a ser nomeada e publicada pelo que é. Ver §14, entrada de 2026-07-31 |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-13 |
| **Relacionado a** | AUD-01, AUD-18 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 2), §3.1, §8 item 2, §9.1 item 2 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (fechamento como limitação reconhecida) |

---

> ### Nota de leitura — o alvo da questão mudou, e não encolheu
>
> A §3 descreve o problema como sendo dos **hotspots do Norte** — Vigia 0,20 m,
> Chaves 0,24 m, Macapá 0,51 m. Esses municípios estão hoje em **risco zero**,
> por perigo nulo sob o portão HAT, e saíram do produto por outra via.
>
> O portão **não** esvaziou os pontos de limiar baixo: os 256 pontos abaixo de
> 1,5 m ainda carregam **17,2 % de todos os eventos aceitos**. O que mudou é
> quem eles alimentam. Medido em 2026-07-31:
>
> - **161 dos 280** municípios publicados vêm de pontos com `thr_hs` < 1,5 m;
>   **44** de pontos abaixo de 1,0 m;
> - **8 dos 20 primeiros**, incluindo o **1º** (São José do Norte/RS, 1,20 m) e o
>   **4º** (Mangaratiba/RJ, 0,78 m);
> - **todos os 20 primeiros** vêm de pontos abaixo de **2,0 m**.
>
> O dano deixou de estar na cauda descartada e passou a estar no **resultado
> publicado**. É por isso que o desfecho exige renomear a quantidade, e não
> apenas declarar uma ressalva regional.

## 1. Problema

O limiar de detecção de tempestade de onda é o **q90 local** de Hs, calibrado
com eventos de Santa Catarina e aplicado sem modificação a toda a costa
brasileira. Em pontos abrigados do Norte, isso produz limiares de 0,20 a 1,05 m —
valores que não correspondem a nenhum conceito de onda extrema e que são
excedidos por ondulação de rotina.

## 2. Por que importa cientificamente

Um limiar puramente relativo mede *raridade local*, não *severidade*. Isso é uma
escolha legítima para muitos fins, mas aqui ela é combinada com a afirmação de
que os eventos detectados são "capable of amplifying inundation, overtopping,
erosion, and port disruption". Ondas de 0,3 m não produzem nenhum desses
efeitos. A consequência é que:

- os municípios do Golfão Maranhense, da costa paraense e do Amapá recebem
  contagens de eventos "compostos" comparáveis às do Sudeste, quando o
  componente de onda ali é irrelevante;
- a componente `Hazard_Intensity`, apesar de bem construída (excesso sobre o
  limiar local, ver §7), herda um limiar de referência sem significado físico;
- é a crítica mais fácil de fazer por um revisor, porque basta olhar a coluna
  `thr_hs_abs` do CSV publicado.

## 3. Evidência original

De `outputs/storm_catalog/compound/compound_metrics.csv` (808 pontos):

| Faixa | n | mín | q25 | mediana | q75 | máx |
|---|---|---|---|---|---|---|
| RS | 79 | 1,52 | 2,14 | 2,48 | 2,68 | 3,03 |
| SC/PR | 69 | 1,26 | 2,00 | 2,33 | 2,70 | 3,08 |
| SP/RJ | 155 | 0,77 | 2,13 | 2,44 | 2,70 | 2,93 |
| ES/BA-S | 56 | 1,21 | 1,60 | 1,81 | 2,00 | 2,42 |
| BA-N | 66 | 1,45 | 1,98 | 2,10 | 2,22 | 2,35 |
| NE | 65 | 1,36 | 1,91 | 2,13 | 2,27 | 2,35 |
| N eq. (−5…0) | 195 | **0,20** | 1,42 | 1,70 | 2,06 | 2,44 |
| AP (0…7) | 123 | **0,37** | 1,36 | 1,86 | 2,12 | 2,34 |

- **35 pontos** têm `thr_hs_abs` < 1,0 m; **129 pontos** < 1,5 m.
- Valores nos pontos que alimentam hotspots do top-10 de risco:
  Vigia/PA **0,20 m**; Chaves/PA **0,24 m**; Macapá/AP **0,51 m**;
  Salvaterra/PA 0,72 m; Turiaçu/MA 0,94 m; Apicum-Açu/MA 0,95 m;
  Icatu e Axixá/MA 1,05 m.
- Para comparação, os pontos do top-10 de perigo (SP/RJ) têm 2,19 a 2,42 m.
- Spearman(`thr_hs_abs`, `thr_ssh_total_abs`) = **−0,739**: os pontos com limiar
  de onda baixo são exatamente os de maré alta — pontos abrigados, estuarinos e
  macromareais.

**Recall da calibração.** `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv`
registra `R_pos = 0,102` para o par ótimo q90/q90: mesmo em Santa Catarina, onde
foi calibrado, o detector captura ~10 % dos eventos reportados. Isso limita o
quanto o par pode ser tratado como fisicamente ancorado.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/03_storm_catalog_generation/01_storm_catalogs/main.py` | orquestrador de catálogo | Calcula o percentil local e detecta episódios POT |
| `src/03_storm_catalog_generation/01_storm_catalogs/segmentation.py` | segmentação POT | Converte excedências em episódios |
| `src/03_storm_catalog_generation/01_storm_catalogs/metrics.py` | atributos do episódio | `peak_hs`, intensidade integrada |
| `src/02_threshold_calibration/05_pu_composite_calibration/scoring.py` | `Score(θ)` | Varredura que selecionou o par q90/q90 |

### Configuração

- `src/03_storm_catalog_generation/config/analysis_config.py` L14–17 — declara
  `tab_TC5_optimal_pair_pu.csv` como a única fonte autorizada de limiar.
- `src/03_storm_catalog_generation/config/analysis_config.py` L23–26 — período de
  cômputo do percentil (registro completo 1993–2025).
- `src/02_threshold_calibration/05_pu_composite_calibration/config/analysis_config.py`
  — grade de percentis `PCT_START = 0.50`, `PCT_STOP = 0.90`, `PCT_STEP = 0.05`.
  **Nota:** a grade termina em q90; o ótimo está na borda da grade, o que é em si
  um sinal de que o ótimo pode estar fora dela.

### Dados e saídas

- `outputs/storm_catalog/catalog_hs_storms.json` — 404 535 episódios de Hs.
- `outputs/storm_catalog/compound/compound_metrics.csv` — coluna `thr_hs_abs`.
- `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv`.

### Figuras e tabelas afetadas

Mesmas de AUD-01, além de
`outputs/article_figures/pu_composite_calibration_heatmaps.png`.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | `thr_hs_local = quantil 0,90 da série local de Hs (1993–2025)`, sem piso absoluto |
| **Pretendido/conceitual** | "extreme wave events" (`README.md`, resumo e Objetivo Geral) — eventos capazes de amplificar inundação, galgamento, erosão e disrupção portuária |

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` §2e descreve a calibração como "empirically grounded" a partir
  de desastres reportados, mas **todos** os eventos usados são de Santa Catarina
  (`data/reported events/`). Nenhum ponto do documento declara que o par ótimo é
  extrapolado para 27° de latitude.
- `src/02_threshold_calibration/05_pu_composite_calibration/SCIENTIFIC_NOTES.md`
  deve ser lido antes de mexer aqui — pode conter justificativa não refletida no
  README.
- As saídas correspondem ao código; a divergência é entre o rótulo científico
  ("onda extrema") e o valor efetivo.

## 7. Explicações alternativas plausíveis

1. **Limiar relativo é a escolha correta por desenho.** O objetivo pode ser
   detectar anomalias locais, comparáveis entre regimes distintos. Nesse caso a
   correção é de nomenclatura: "excedência local de Hs", não "onda extrema".
2. **A normalização de intensidade já corrige o problema.** `normalize_compound_intensity()`
   (`detection.py` L286) usa o **excesso sobre o limiar local**, com percentis
   Q05/Q95 agrupados no domínio inteiro. Isso já impede que um ponto de limiar
   baixo receba intensidade alta artificialmente — e é confirmado pelos dados:
   Chaves/PA tem `mean_compound_intensity_norm` = 0,203, próximo do mínimo do
   domínio (0,169). **A frequência, porém, não é corrigida por nada.**
3. **Os pontos de limiar muito baixo podem estar em células mal representadas**
   do WAVERYS (~0,2°) — pontos internos a estuários e baías onde o modelo global
   de ondas não é válido. Nesse caso o problema é de **seleção de pontos de
   grade**, não de limiar, e a correção é excluí-los (ver AUD-12).
4. **O piso absoluto tem sua própria arbitrariedade.** Escolher 1,5 m é tão
   arbitrário quanto não escolher nada, a menos que o valor seja ancorado em
   algum critério (ex.: altura de galgamento, percentil nacional).

## 8. Diagnósticos propostos

1. **Mapear `thr_hs_abs` sobre a linha de costa** com `coastal_projection.py` e
   sobrepor a batimetria/geometria, para identificar quais pontos de limiar baixo
   são estuarinos ou abrigados.
2. **Quantificar o efeito de um piso absoluto:** recalcular `compound_count_total`
   sob `thr_hs = max(q90_local, X)` para X ∈ {1,0; 1,5; 2,0} m e sob `q95`/`q99`
   locais. Comparar mapas e rankings (Spearman e sobreposição de top-20).
   *Nota:* este teste exige reprocessar os catálogos ou, no mínimo, refiltrar
   `catalog_hs_storms.json` por `peak_hs`.
3. **Testar a sensibilidade do par ótimo do Step 2e** estendendo a grade de
   percentis para além de q90 (q92, q95, q97), já que o ótimo atual está na
   borda da grade. Reutilizar `src/02_threshold_calibration/05_pu_composite_calibration/sensitivity.py`.
4. **Verificar se os pontos de `thr_hs` < 1 m são válidos no WAVERYS**:
   distância à costa, profundidade, fração de células vizinhas com dado.
5. **Relacionar `thr_hs_abs` com o clima de ondas offshore** da região
   correspondente, para separar "abrigo real" de "célula inválida".

## 9. Critérios objetivos de resolução

### 9.1 Critérios de 2026-07-29 — situação de cada um

Os critérios originais pressupunham que **um piso seria adotado**. Como o
desfecho é não adotar nenhum, três deles ficam sem objeto. Um critério cujo
pressuposto caiu não é automaticamente satisfeito: é anulado, com a razão.

| # | Critério original | Situação em 2026-07-31 |
|---|---|---|
| 1 | Mapa versionado de `thr_hs_abs` + lista dos pontos abaixo do piso, **classificados** em abrigado real / estuarino / célula duvidosa | **PARCIAL, e a classificação é ANULADA.** A tabulação existe e está versionada (§9.2 A). A **classificação não é operacionalizável**: a orientação da linha de costa abriga pontos que não estão em baía alguma, de modo que "abrigo real" e "célula duvidosa" não se separam por nenhuma regra enunciável neste repositório — e uma classificação não enunciável seria arbitragem disfarçada de critério. Mesma conclusão a que AUD-12 chegou por outro caminho |
| 2 | Efeito de duas alternativas de limiar sobre contagem, perigo e ranking | **PARCIAL.** O eixo do percentil foi varrido e reportado (`audit_AUD_02_threshold_grid_floor`, §14 de 2026-07-30): nem em q99 o mínimo chega a 0,3 m. O efeito de um **piso absoluto** sobre o ranking **não foi medido** — e deixa de ser exigível, porque nenhum piso é adotado. Fica registrado como não medido, não como dispensável |
| 3 | Escolha final justificada por critério explícito, não por conveniência do resultado | **[x] SATISFEITO.** O critério declarado é negativo e verificável: a calibração PU **demonstravelmente não determina** o eixo da onda (seis melhores pares dentro de 1 % do score, cobrindo q50–q80; `q_zos` = q99 selecionado em 14 de 14 variantes), e a âncora externa natural — setup/runup a partir de Hₛ — exige declividade de face de praia, camada física que **AUD-10 já fechou como ausente**. A escolha foi feita **antes** de olhar o ranking resultante |
| 4 | Nenhum ponto abaixo do piso alimenta município publicado | **SEM OBJETO.** Não há piso. Reconduzido ao critério C da §9.2, que exige o oposto: **declarar** quantos alimentam, e onde |
| 5 | `README.md` §2e declara o domínio de calibração e o alcance da extrapolação | **[x] SATISFEITO.** §2e passou a declarar que os 147 pares são **integralmente de Santa Catarina** e que o par é aplicado a 27° de latitude. Compartilhado com AUD-18 |
| 6 | Produtos a jusante regenerados e verificados | **SEM OBJETO.** Nenhum valor numérico muda; o desfecho é de nomenclatura e declaração |

### 9.2 Critérios vigentes (2026-07-31)

- [x] **A.** Existe tabela versionada e reproduzível de `thr_hs_abs` por setor e
      **por estado**, publicável como material suplementar.
      *`outputs/audit/AUD-02_threshold_exposure/{thresholds_by_latitude_band.csv,
      thresholds_by_state.csv, municipal_threshold_exposure.csv}`. A tabela por
      estado é a que responde à pergunta do leitor — MA mediana **0,90 m** com 24
      de 33 municípios abaixo de 1,0 m; PA mínimo **0,14 m**; RS mediana 1,71 m.*
- [x] **B.** A quantidade **não é mais chamada de "onda extrema"** onde o texto
      descreve o que o detector seleciona. *`README.md` §2e e glossário,
      `site/content/project.ts`, `site/components/Hero.tsx`: passa a
      "local significant-wave-height exceedance", com a definição operacional
      explícita. O título do projeto foi mantido — descreve o fenômeno de
      interesse, não a quantidade detectada — e agora vem acompanhado da
      qualificação.*
- [x] **C.** A exposição do **resultado publicado** aos limiares baixos está
      declarada, com número. *161 de 280 municípios abaixo de 1,5 m, 44 abaixo de
      1,0 m, 8 dos 20 primeiros e **todos os 20 primeiros abaixo de 2,0 m**.
      README, parágrafo de limitação. É o número que um revisor calcula sozinho.*
- [x] **D.** Está declarado que os pontos abrigados — em baía ou por orientação
      da linha de costa — são limitação do WAVERYS como **driver de larga
      escala**, e não pontos a filtrar. *Parágrafo de limitação; casos nomeados:
      Mangaratiba/RJ (4º, 0,78 m, Baía de Sepetiba) e Magé/RJ (3º, fundo da Baía
      de Guanabara).*
- [x] **E.** O caminho de superação está registrado como **trabalho futuro
      nomeado**, não como pendência vaga. *Formulação direta de setup/runup a
      partir de Hₛ, que exige a camada física de AUD-10.*
- [ ] **F.** *(remetido, não pendente aqui)* A declaração do **domínio de
      validade** do detector. Pertence a **AUD-18**, que permanece aberta.

## 10. Riscos de alteração prematura

- Impor um piso absoluto **muda a definição de evento** e invalida a coerência
  com o Step 2e, cuja pontuação PU foi otimizada sob a definição relativa. O
  `R_pos` em SC pode cair.
- Um piso alto demais elimina eventos reais em regiões de baixa energia,
  produzindo `compound_count_total` = 0 em alguns pontos e quebrando o Min–Max
  do `Hazard_Index` (ver `hazard_index.py::_minmax`, que levanta erro se não
  houver valores finitos).
- Reprocessar os catálogos é a operação mais cara do repositório; deve ser feita
  em conjunto com as decisões de AUD-01 e AUD-03.

## 11. Condições sob as quais o resultado atual pode ser mantido

Aceitável sem alteração de código **apenas** se:

1. A quantidade for renomeada de "onda extrema" para "excedência local de Hs"
   em todo o manuscrito, figuras e site;
2. A tabela de `thr_hs_abs` por região for publicada como material suplementar,
   para que o leitor veja o que o limiar significa em cada setor;
3. AUD-01 tiver sido resolvido — os dois problemas juntos são o que produz os
   hotspots do Norte, e resolver apenas um não basta.

Mesmo assim, permanece o problema de que a **frequência** não é corrigida pela
normalização de intensidade, e é a frequência que domina 50,5 % da variância do
`Hazard_Index_raw`.

## 12. Produtos a jusante que exigiriam regeneração

Idênticos aos de AUD-01 §12 — a cadeia completa, do catálogo às figuras.
Coordenar a reexecução com AUD-01 e AUD-03 para evitar reprocessamentos
sucessivos.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_02_threshold_exposure.py`, `outputs/audit/AUD-02_threshold_exposure/`. **Alterados:** este registro (§9, §13, §14 e nota de leitura), `README.md` (§2e, glossário, parágrafo de limitação), `site/content/project.ts`, `site/components/Hero.tsx`, `docs/scientific_audit/ISSUE_TRACKER.md`, AUD-13 (critério E) | Diagnóstico + renomeação + declaração. **Nenhum valor numérico publicado alterado; nenhum ponto filtrado; nenhum catálogo reprocessado** |
| 2026-07-30 | `7eb8cc8` e seguintes | `main` | **Novos:** `src/exploratory/audit_AUD_02_threshold_grid_floor.py`, `outputs/audit/AUD-02_threshold_grid_floor/`. **Alterados indiretamente:** o par de limiares em `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` e, por consequência, `thr_hs_abs` em todo o catálogo | Diagnóstico do piso de `thr_hs` em toda a grade de percentis, e efeito colateral da recalibração de AUD-01 sobre esta questão. Nenhuma alteração foi feita **para** AUD-02; a questão permanece aberta e agravada |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*

### 2026-07-29 — Achado incidental da investigação de AUD-01: a patologia não é exclusiva do Hs

> **Nota de escopo.** Esta entrada registra um achado obtido durante a
> investigação de **AUD-01**, não uma execução dos diagnósticos próprios de
> AUD-02 (§8), que permanecem **não executados**. A situação da questão segue
> `aberto`.

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Não dirigida a AUD-02. Surgiu ao avaliar uma proposta do usuário de trocar o nível de `SSH_total` para `zos` puro: qual seria a magnitude física do limiar q90 sobre `zos`? |
| **Dados e métodos** | `python -m src.exploratory.audit_AUD_01_surge_vs_tide_magnitude`; anomalia de `zos` em q90 relativa à média local, por ponto e por faixa de latitude |
| **Achados** | A anomalia de sobrelevação em q90 vale **5,8 a 8,6 cm** nas faixas de BA-N ao Amapá (contra 21,3 cm no RS). Um detector de nível baseado em `zos` que mantivesse o limiar percentílico local chamaria uma anomalia de ~6 cm de "evento de sobrelevação" |
| **Interpretação** | **A patologia diagnosticada em AUD-02 não é uma propriedade do Hs — é uma propriedade do limiar percentílico local aplicado a uma variável cuja variância colapsa regionalmente.** O q90 mede raridade local, não severidade; onde a variabilidade meteorológica é pequena, o q90 seleciona flutuações fisicamente irrelevantes, seja em onda (0,20 m em Vigia) seja em nível (6 cm no Norte). Isso **amplia** o alcance de AUD-02: qualquer redesenho do detector que preserve limiares percentílicos locais herda o problema, apenas mudando a variável em que ele se manifesta. Reforça a alternativa já listada em AUD-02 §7.4 e §9 (piso físico absoluto), agora com um segundo caso concreto que a sustenta |
| **Alterações implementadas** | Nenhuma |
| **Incerteza remanescente** | A ancoragem de um piso absoluto continua sem critério definido — é a mesma lacuna registrada em AUD-02 §7.4. Ver também a ressalva de AUD-01 §14 (2026-07-29, magnitude física): não é possível distinguir "sinal ausente na natureza" de "sinal não resolvido pelo GLORYS12" sem maregrafo no Norte (AUD-18) |
| **Próxima decisão necessária** | Decisão estruturante pendente do usuário, comum a AUD-01, AUD-02 e AUD-18: substituir o limiar percentílico local por piso físico absoluto nos forçantes |

### 2026-07-30 — Efeito da grade nova e do par recalibrado sobre o piso de `thr_hs`: **piora**

> **Nota de escopo.** Esta entrada registra o efeito colateral, sobre AUD-02, da
> recalibração do Step 2e feita para AUD-01. Os diagnósticos próprios de AUD-02
> (§8) permanecem **não executados**, com exceção parcial do §8.3, coberto
> abaixo. A situação da questão segue `aberto`, agora **agravada**.

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Duas. **(1)** Cobre o diagnóstico §8.3: estender a grade de percentis do Step 2e além de q90 move o par ótimo, e o que isso faz com o piso de `thr_hs`? **(2)** O par efetivamente selecionado pela recalibração melhora, piora ou não altera AUD-02? |
| **Dados e métodos** | `thr_hs` e `thr_zos` locais calculados nos **808** pontos de produção, para cada um dos 11 percentis da grade nova (q50 a q99), a partir de `data/unified/metocean_brazil_unified_waverys_grid.nc` sobre 1993–2025. Contagem de pontos abaixo dos dois marcos que AUD-02 §3 usa, 1,0 m e 1,5 m |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_02_threshold_grid_floor` |
| **Novas saídas geradas** | `outputs/audit/AUD-02_threshold_grid_floor/{thresholds_by_point.csv, thresholds_by_percentile.csv, summary.json}` |
| **Validação** | O diagnóstico reproduz **exatamente** os valores publicados em AUD-02 §3 no q90: mínimo **0,20 m**, **35** pontos abaixo de 1,0 m e **129** abaixo de 1,5 m. A concordância vale como verificação de que a extração e o cálculo de percentil deste script são os mesmos do pipeline |
| **Achado 1 — subir o percentil eleva o piso, mas pouco** | Mínimo de `thr_hs` nos 808 pontos: q50 **0,07 m**, q70 0,14, q85 0,19, q90 **0,20**, q95 0,23, q99 **0,27 m**. Pontos abaixo de 1,0 m: 83 → 56 → 44 → **35** → 31 → **21**. Abaixo de 1,5 m: 436 → 256 → 160 → **129** → 90 → **61**. Ou seja: **nem no extremo q99 o limiar mínimo de "onda extrema" chega a 0,3 m.** Estender a grade **atenua** a patologia, mas não a resolve sob nenhum enquadramento — 61 pontos abaixo de 1,5 m continuam sendo 7,5 % da costa |
| **Achado 2 — o par selecionado PIORA a questão** | A recalibração selecionou **q70/q99**: q99 no **nível**, q70 na **onda**. Como AUD-02 é sobre a onda, o efeito é o oposto do desejável. Contra o q90 vigente até então: mínimo **0,20 m → 0,14 m**; pontos abaixo de 1,0 m **35 → 56**; abaixo de 1,5 m **129 → 256**, praticamente o dobro |
| **Interpretação** | O diagnóstico §8.3 fica respondido e a nota de AUD-02 §4 — "o ótimo está na borda da grade, o que é em si um sinal de que o ótimo pode estar fora dela" — confirma-se, mas **não na direção que ajudaria esta questão**. O ótimo estava fora da grade no eixo do **nível**, não no da onda: `q_zos = q99` é selecionado em 14 de 14 variantes de sensibilidade, enquanto o percentil de onda é o eixo mal determinado da seleção, com os seis melhores pares diferindo em menos de 1 % no score e cobrindo de q50 a q80. O score composto simplesmente **não tem informação** para escolher o limiar de onda, e o valor que ele devolve rebaixa o piso. Isso reforça a alternativa de AUD-02 §7.4 e §9: se um piso físico absoluto for adotado, ele terá de vir de fora da calibração PU, porque a calibração demonstravelmente não o determina |
| **Alterações implementadas** | Nenhuma **para** AUD-02. O script é read-only e não aplica piso algum. A mudança de `thr_hs` no catálogo é consequência da adoção de AUD-01, apresentada ao pesquisador responsável **antes** da execução, com estes números, e por ele autorizada |
| **Incerteza remanescente** | (1) A ancoragem de um piso absoluto continua sem critério definido — mesma lacuna de §7.4. (2) Os critérios de resolução de §9 permanecem **todos** não atendidos, e agora sobre uma população maior de pontos problemáticos. (3) Como AUD-02 bloqueia publicação e a distância até o piso defensável **aumentou**, a questão passa a ser mais urgente, não menos |
| **Próxima decisão necessária** | Decidir o tratamento do limiar de onda de forma independente da calibração PU, já que esta não o determina. As opções continuam sendo as de §7 e §11: piso físico absoluto com ancoragem declarada; restrição de domínio pela partição de AUD-01 (antimodo em 0,257, que remove 97 % dos pontos com `thr_hs` < 1,0 m); ou renomear a quantidade para "excedência local de Hs" em todo o manuscrito, figuras e site |

### 2026-07-31 — O alvo mudou: o dano saiu da cauda e entrou no topo do ranking

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | O portão HAT esvaziou os pontos de limiar baixo? Se não, que parte do produto publicado ainda depende deles? |
| **Dados e métodos** | `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv` (808 pontos) cruzado com `site/public/data/risk_index_municipalities.geojson` (280 com risco), por coordenada de grade arredondada a 3 casas — junção **total**, 0 sem par. Tabulação de `thr_hs_abs` por faixa de latitude e por estado, e contagem da exposição do ranking |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_02_threshold_exposure` |
| **Novas saídas geradas** | `outputs/audit/AUD-02_threshold_exposure/{thresholds_by_latitude_band.csv, thresholds_by_state.csv, municipal_threshold_exposure.csv, summary.json}` |
| **Achados** | (a) **O portão não esvaziou nada**: os 256 pontos com `thr_hs` < 1,5 m seguem carregando **2 891 de 16 768** eventos aceitos — **17,2 %** —, e só 51 deles ficaram sem evento. (b) **Os municípios afetados trocaram de região.** Os hotspots do Norte que a §3 nomeia — Vigia, Chaves, Macapá — estão em risco zero por perigo nulo, e saíram por outra via. Quem depende de limiar baixo hoje é o **topo do ranking**: **161 de 280** municípios vêm de pontos abaixo de 1,5 m, **44** abaixo de 1,0 m, **8 dos 20 primeiros** — entre eles o **1º, São José do Norte/RS, com `thr_hs` = 1,20 m**, onde o q90 mediano do RS é 2,48 m — e **todos os 20 primeiros** abaixo de 2,0 m. (c) Por estado, a mediana vai de **0,90 m no MA** (24 de 33 municípios abaixo de 1,0 m) e 0,905 m no AP a 1,71 m no RS. (d) Caso extremo no Sudeste: **Mangaratiba/RJ, 4º do país, `thr_hs` = 0,78 m**, ponto dentro da Baía de Sepetiba; com Magé/RJ em 3º, no fundo da Baía de Guanabara, forma-se um agrupamento novo — **baías abrigadas do RJ no topo** — que é o sucessor direto do problema dos hotspots do Norte |
| **Interpretação** | A recalibração para q70 rebaixou o piso em todo o domínio, e o portão HAT removeu do produto justamente os municípios que a §3 usava como ilustração. O resultado é que a questão **piorou de lugar**: antes contaminava municípios que o revisor descartaria de qualquer forma; agora sustenta o resultado principal. Isso muda o desfecho aceitável — uma ressalva regional não basta, porque o problema não é regional |
| **Alterações implementadas** | Nenhuma em código de produção. Script diagnóstico novo, read-only |
| **Validação realizada** | A junção município↔ponto levanta erro se algum município ficar sem par; executou com 0 sem par. Uma versão anterior desta análise, feita sem arredondamento da chave, deixou 278 de 280 sem par e produziu contagens falsas — o script agora falha em vez de reportar silenciosamente |
| **Incerteza remanescente** | O efeito de um piso absoluto sobre o ranking continua **não medido**. Sob o desfecho adotado deixa de ser exigível, mas se um piso for considerado no futuro, é o primeiro diagnóstico a rodar |
| **Próxima decisão necessária** | Do pesquisador: das três opções da §11, qual adotar |

### 2026-07-31 — DECISÃO: fechar como `limitacao-reconhecida`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31, sobre os achados acima |
| **Decisão** | **Nenhum piso, nenhum filtro de ponto, nenhum reprocessamento.** A quantidade é declarada pelo que é — excedência local de Hₛ — e a limitação é reconhecida no manuscrito |
| **Fundamentação — por que o piso não é derivável aqui** | Não é escolha de conveniência, é uma indisponibilidade demonstrada em duas camadas. **Primeira:** a calibração PU não determina o eixo da onda — os seis melhores pares ficam dentro de 1 % do score cobrindo de q50 a q80, enquanto `q_zos` = q99 é selecionado em 14 de 14 variantes de sensibilidade. O escore simplesmente não tem informação sobre o limiar de onda. **Segunda:** a âncora teria de vir de fora, e a âncora natural é uma formulação de **setup/runup a partir de Hₛ**, que exige declividade de face de praia — precisamente a camada de suscetibilidade física que **AUD-10 já fechou como `limitacao-reconhecida`**. O piso não é derivável dentro deste pipeline porque depende de uma camada que o projeto já reconheceu não ter |
| **Fundamentação — por que os pontos abrigados não são filtráveis** | O §8.5 pedia separar "abrigo real" de "célula inválida". Essa separação **não é operacionalizável**: a orientação da linha de costa produz abrigo de ondulação em pontos que não estão em baía nenhuma, e o WAVERYS a ~0,2° é um **driver de larga escala mesmo nos pontos não abrigados**. Sem uma regra enunciável, qualquer filtro seria arbitragem com aparência de critério — a mesma conclusão a que **AUD-12** chegou por outro caminho, e pela mesma razão |
| **Trabalho futuro nomeado** | Uma formulação direta de wave setup/runup a partir de Hₛ substituiria o limiar percentílico por um limiar com significado físico local, e resolveria simultaneamente o piso e o abrigo. Depende da camada física de AUD-10. Registrado como direção, não como promessa |
| **O que o desfecho exige, e foi feito** | (1) Renomear a quantidade onde o texto descreve o que o detector seleciona; (2) publicar a tabela de `thr_hs` por setor e por estado como suplementar; (3) **declarar com número** a exposição do topo do ranking. Ver §9.2 |
| **O que o desfecho NÃO cobre** | (1) O **domínio de validade** do detector — **AUD-18**, aberta. (2) A reprovação dos casos costeiros conhecidos e o agrupamento novo das baías do RJ — **AUD-05**, aberta, e sua §3.3 ainda lista os hotspots do Norte como problema. (3) **AUD-13** fechou declarando que o índice propaga AUD-02 integralmente (ρ = 0,893); a declaração foi atualizada para "limitação declarada" em vez de "questão aberta" |
