# AUD-18 — Lacuna de validação independente fora de Santa Catarina; limiares extrapolados sem base de impactos

| Campo | Valor |
|-------|-------|
| **ID** | AUD-18 |
| **Tipo** | `lacuna-validacao` |
| **Componente** | transversal |
| **Etapa do fluxo** | Step 2d/2e (calibração) → Step 3 → Step 4 |
| **Afeta** | dados, interpretação, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim — satisfeito por declaração explícita do domínio de calibração e do alcance da extrapolação |
| **Status** | `resolvido` |
| **Desfecho** | `limitacao-reconhecida` |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-01, AUD-02, AUD-03, AUD-05, AUD-10 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §6.4, §7.3, §8 item 2 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (busca documentada e fechamento) |

---

> ### Nota de leitura — dois números da §3 estão superseded
>
> A §3.2 reporta **`R_pos` = 0,102** e a §3.3 diz que o ótimo está na borda da
> grade q50–q90. Ambos descrevem a calibração **anterior**. No par vigente
> **q70/q99**, `R_pos` = **0,1905** (H = 28, M = 119, U = 831), e a grade **foi
> estendida** a q95 e q99 em 2026-07-30, com o ótimo migrando para fora da borda
> antiga — no eixo do **nível**, não no da onda. Ver §3-bis.
>
> Fechada como `limitacao-reconhecida` por decisão do pesquisador em 2026-07-31.
> Ver §14.

## 1. Problema

Toda a calibração de limiares foi feita com **eventos de Santa Catarina** — 91
registros da Defesa Civil (Leal et al. 2024) e 56 documentários adicionais, 147
pares únicos município × data em 27 municípios, todos em SC. O par ótimo q90/q90
foi então aplicado a **27 graus de latitude**, cobrindo regimes de maré, clima de
ondas e geomorfologia completamente distintos.

Não existe base de impactos independente para o Norte e o Nordeste com a qual
verificar se a extrapolação é válida.

## 2. Por que importa cientificamente

Esta é a raiz comum de AUD-01 e AUD-02, e o argumento que um revisor usará para
questionar o alcance geográfico do trabalho:

- q90 em SC seleciona tempestades sinóticas; q90 no Maranhão seleciona sizígias
  (AUD-01);
- q90 de Hs em SC vale 2,3 m; no Pará vale 0,20 m (AUD-02);
- **o mesmo par de percentis produz fenômenos diferentes em regiões diferentes**,
  e não há dado de impacto fora de SC para detectar isso.

A ausência de validação não invalida o trabalho — mas o **limite de validade
precisa ser declarado**, e hoje não é.

## 3. Evidência original

### 3.1 A base de calibração é integralmente catarinense

De `README.md` §2e e de `data/reported events/`:

- 91 eventos da base da Defesa Civil de SC (Leal et al. 2024, 1998–2020);
- 56 eventos da base documentária expandida, curada de arquivos de notícia,
  teses e relatórios técnicos;
- total: **147 pares únicos município × data, em 27 municípios**, todos em SC;
- `data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md`
  documenta o protocolo de busca documentária.

### 3.2 O desempenho da calibração, mesmo em SC, é limitado

De `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv`:

| thr_hs_pct | thr_ssh_pct | H | M | U | **R_pos** | B | F_soft | Score |
|---|---|---|---|---|---|---|---|---|
| 0,90 | 0,90 | 15 | 41 | 1267 | **0,102** | 0,1768 | 966,86 | −1,2896 |

`R_pos = 0,102` — o detector captura ~10 % dos eventos reportados **na própria
região de calibração**.

Do Step 2d (diagnóstico), `README.md` §2d: par ótimo por CSI também q90/q90, com
H = 21, M = 70, F = 1298, CSI = 0,0151, **FAR = 0,984**. O próprio README conclui
que "classical verification metrics are unsuitable for this application due to
systematic under-reporting" — conclusão correta, que motivou a abordagem PU, mas
que também significa que **o detector nunca foi validado contra impactos**, nem
em SC.

### 3.3 O par ótimo está na borda da grade

`PCT_START = 0.50`, `PCT_STOP = 0.90`, `PCT_STEP = 0.05` — 81 pares. O ótimo é
(0,90; 0,90), o canto superior da grade. Um ótimo de borda sugere que o verdadeiro
ótimo pode estar fora do espaço explorado.

### 3.4 Ausência de comparável no Norte/Nordeste

- O S2ID/Atlas Digital é reconhecido no próprio `README.md` como sistematicamente
  sub-reportado e **não** é usado como validação a jusante — decisão
  metodologicamente correta.
- Não há base regional de eventos costeiros para MA, PA, AP, PI, CE, RN, PB, PE,
  AL, SE, BA equivalente à de SC.
- `outputs/documentary_events_table/` contém a tabela suplementar de eventos, mas
  restrita ao domínio catarinense.

### 3.5 Caso concreto de subestimação possivelmente correta

Recife, Olinda e Jaboatão dos Guararapes (PE) não aparecem no top-50, apesar de
erosão costeira crônica e ocupação urbana na linha de praia.
`Hazard_Frequency` médio no PE = **0,063**. Isso **pode** estar correto — o NE tem
baixa frequência de compostos onda–sobrelevação — mas o mecanismo local dominante
(galgamento sobre linha de recife em preamar de sizígia) não é resolvido pela
grade de 1/12° do GLORYS12 nem pelo WAVERYS a ~0,2°. Sem base de impactos
regional, não é possível distinguir "resultado correto" de "processo não
resolvido".

### 3.6 Ineditismo do trabalho

Não foi localizado, na revisão de linha de base, estudo revisado por pares que
aplique um índice composto onda–sobrelevação à costa brasileira inteira com
resolução municipal. O trabalho é genuinamente inédito nessa cobertura — o que
**aumenta** seu valor e simultaneamente a exigência de robustez, porque não há
referência com a qual comparar.

---

## 3-bis. Situação em 2026-07-31

### 3-bis.1 O desempenho do detector melhorou, e o número da §3.2 caducou

De `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv`, par
vigente:

| thr_hs_pct | thr_ssh_pct | H | M | U | **R_pos** | B | Score |
|---|---|---|---|---|---|---|---|
| 0,70 | 0,99 | 28 | 119 | 831 | **0,1905** | 0,1482 | −0,3178 |

Contra `R_pos` = 0,102 do par q90/q90 superseded: o detector passou a capturar
**~19 %** dos eventos reportados em SC, quase o dobro. O FAR = 0,984 da §3.2 é do
Step 2d, diagnóstico e superseded, e permanece citável apenas como tal.

**A leitura correta continua sendo a de AUD-18 §7.4**, e ela não mudou: sob
arcabouço PU os "negativos" são **não rotulados**, não negativos. Um recall de
0,19 contra uma referência incompleta é **piso** do recall verdadeiro, e um FAR
calculado contra a mesma referência não é interpretável como taxa de alarme
falso.

### 3-bis.2 O ótimo de borda foi testado — e saiu da borda pelo eixo errado

O §8.3 pedia estender a grade além de q90. **Feito em 2026-07-30**
(`audit_AUD_02_threshold_grid_floor`, registrado em AUD-02 §14): a grade foi a
q95 e q99, e o ótimo migrou para **q70/q99**. Confirma-se que o ótimo estava fora
da grade — mas no eixo do **nível**, não no da onda. O percentil de nível q99 é
selecionado em **14 de 14** variantes de sensibilidade, enquanto o de onda é o
eixo mal determinado, com os seis melhores pares dentro de 1 % do score cobrindo
q50–q80. Consequência já absorvida por AUD-02.

### 3-bis.3 Busca documentada por base de impactos no N/NE — **negativo qualificado**

Diagnóstico §8.1. Reconhecimento por busca bibliográfica e de bases públicas,
executado em 2026-07-31. **Não é levantamento arquivístico exaustivo**, e nenhuma
das fontes abaixo teve seu conteúdo verificado nesta sessão — apenas existência,
escopo e natureza.

| Fonte | Cobre N/NE? | É datada? | Serve para validar o detector? |
|---|---|---|---|
| **Panorama da Erosão Costeira no Brasil** (Muehe, org., MMA, 2018) — capítulo por estado costeiro | **Sim, todos** | **Não** | **Não.** Diagnostica **onde** a linha de costa recua, não **quando** houve evento. Serve a teste de sanidade qualitativo |
| **S2ID / Atlas Digital de Desastres** (SEDEC/MIDR), municipal, atualização anual | Sim | Sim | **Não como está.** Dirigido por declaração de emergência; sub-reporte sistemático já reconhecido no `README.md`, razão pela qual foi excluído da validação a jusante |
| **Atlas Brasileiro de Desastres Naturais** (CEPED/UFSC, 1991–2012), 26 volumes estaduais | Sim | Sim | Mesma origem declaratória do S2ID; herda o mesmo viés |
| **Ressacas do mar em Fortaleza/CE** (Paula, Morais, Ferreira & Dias, 2015, em *Ressacas do Mar / Temporais e Gestão Costeira*) | **Um município** | **Sim** | Parcialmente — é o análogo mais próximo do que Leal et al. (2024) oferece para SC, mas **um município não calibra uma costa** |
| **GLOSS-Brasil** (CHM/Marinha, 13 marégrafos) e **RMPG** (IBGE) | Sim, com estações no N/NE | Série contínua | **Sim, para a componente de nível** — validaria `zos` + maré diretamente. **Nunca usado neste ciclo**; é o passo de validação mais tratável que resta. Coincide com a lacuna registrada em AUD-03 |
| Bases regionais de ressaca do **RJ** (ex.: 1979–2013, RGCI n.º 146) | Não — é SE | Sim | Fora do domínio da lacuna |

**Resultado: a lacuna é real, mas não é irremediável — é não explorada.** Não
existe, no N/NE, equivalente à base catarinense de 147 pares
município×data, e portanto **recalibração regional continua impossível**. Mas
existem duas rotas parciais nomeadas: verificação qualitativa contra Muehe (2018)
e verificação da componente de nível contra marégrafos GLOSS/RMPG. Nenhuma das
duas foi executada neste ciclo.

Nenhum script foi escrito para esta seção: não há cálculo, e emitir uma tabela
fixa por script daria aparência de diagnóstico a um levantamento bibliográfico.

### 3-bis.4 O domínio de validade foi caracterizado, e deliberadamente **não** aplicado

AUD-01 mediu a razão sobrelevação(q99)/modulação de sizígia por ponto e
encontrou-a **genuinamente bimodal**, com antimodo em **0,257** — intervalo 32×
maior que o típico, portanto uma partição derivada do dado e não imposta — e
geograficamente coerente, separando 268 pontos "surge-competitive" (35°S a
19,8°S) de 540 "tide-dominated"
(`outputs/audit/AUD-01_validity_domain_partition/`).

**A restrição não foi aplicada**, porque a decisão adotada em AUD-01 — detector
sobre `zos` livre de maré, com portão HAT — elimina a patologia por construção em
vez de excluir domínio. Para AUD-18 a consequência é direta: **o domínio de
validade a declarar não é um recorte geográfico, e sim a advertência de que o
mesmo detector significa físicas diferentes ao longo da costa**, com a razão
surge/maré variando por quase duas ordens de grandeza (ρ = −0,81 com a latitude).

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/02_threshold_calibration/05_pu_composite_calibration/scoring.py` | `Score(θ)` | Varredura de limiares |
| `src/02_threshold_calibration/05_pu_composite_calibration/audit.py` | auditoria de episódios | Pesos de confiança `q_i` |
| `src/02_threshold_calibration/05_pu_composite_calibration/sensitivity.py` | — | Presets alternativos `SENSITIVITY_WEIGHTS`, `SENSITIVITY_ALPHA` |
| `src/02_threshold_calibration/04_csi_grid_scan/metrics.py` | CSI, FAR | Diagnóstico do Step 2d |
| `src/03_storm_catalog_generation/config/analysis_config.py` | L14–17 | Declara `tab_TC5_optimal_pair_pu.csv` como única fonte de limiar |

### Configuração e documentação de origem

- `src/02_threshold_calibration/05_pu_composite_calibration/config/PARAMETER_DECISIONS.md`
  — documenta que a grade termina em q90 e que estendê-la "to q95 or use 2% step"
  é ajustável.
- `src/02_threshold_calibration/05_pu_composite_calibration/SCIENTIFIC_NOTES.md`
- `src/02_threshold_calibration/04_csi_grid_scan/SCIENTIFIC_NOTES.md`

### Dados

- `data/reported events/reported_events_Karine_sc.csv`
- `data/reported events/ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`
- `data/reported events/ressaca_sc_eventos_sc_1998_2020_repository_methodology.md`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Par de percentis calibrado em SC, aplicado uniformemente aos 808 pontos de −35° a +6° de latitude |
| **Pretendido** | Ou uma calibração regionalizada, ou uma declaração explícita do domínio de validade e das suposições de transferência |

## 6. Divergência documentação ↔ implementação ↔ saídas

- `README.md` §2e descreve a calibração como *"empirically grounded detection
  framework"* sem declarar que a base empírica é integralmente de um estado.
- Nenhum documento declara uma **suposição de transferência de limiar**.
- Código e saídas concordam entre si.

## 7. Explicações alternativas plausíveis

1. **Um limiar percentílico é, por desenho, transferível.** É essa a razão de se
   usar percentis em vez de valores absolutos: eles se adaptam ao regime local. O
   que não se transfere é o **significado físico** do que está acima do percentil.
   Distinção central para o manuscrito.
2. **A base de SC pode ser representativa do S/SE.** Se o domínio de validade for
   declarado como 20–35°S, a extrapolação é curta e defensável — e coincide com o
   domínio que passa no teste de fase de AUD-01.
3. **A ausência de base no N/NE pode ser irremediável.** Se não existe registro
   sistemático de eventos costeiros ali, nenhuma validação é possível, e a
   limitação é do estado da arte, não do trabalho. Isso é declarável e aceitável.
4. **O `R_pos` baixo pode ser esperado sob sub-reporte severo.** O arcabouço PU
   existe precisamente porque os "negativos" não são negativos: são não rotulados.
   Um recall de 10 % contra uma base incompleta não significa 10 % de acerto real.
   O README já argumenta nessa direção.
5. **Fontes alternativas de validação podem existir** e não terem sido
   procuradas: registros de autoridades portuárias, boletins da Marinha,
   ocorrências de defesa civil municipal, arquivos de imprensa regional.

## 8. Diagnósticos propostos

1. **Levantar a existência de bases de impacto regionais** para pelo menos um
   ponto do NE e um do N. Candidatos: registros de capitanias dos portos,
   ocorrências municipais de defesa civil, arquivos de imprensa regional, e a
   literatura de erosão costeira por estado.
   *Saída esperada:* saber se a lacuna é irremediável ou apenas não explorada.
2. **Testar a transferibilidade indiretamente**: aplicar o detector calibrado em
   SC aos eventos documentados na literatura de erosão costeira de outros estados
   (mesmo poucos casos), e verificar taxa de detecção.
3. **Estender a grade de percentis** além de q90 (q92, q95, q97) e verificar se o
   ótimo permanece na borda. Baixo custo — a infraestrutura existe em
   `sensitivity.py`.
4. **Calibração regionalizada como teste**: dividir a costa em 3 setores e
   verificar se o par ótimo mudaria, usando apenas os dados de SC como âncora e
   um critério físico (amplitude de maré, clima de ondas) para os demais.
5. **Documentar formalmente a suposição de transferência** e suas condições de
   validade, mesmo que não seja testável.
6. **Análise de resolução para o NE**: verificar se a grade do GLORYS12 e do
   WAVERYS resolve a plataforma recifal de PE, e reportar como limitação
   específica para a subestimação de Recife/Olinda.

## 9. Critérios objetivos de resolução

- [x] O `README.md` §2e declara explicitamente que a calibração usou
      **exclusivamente** eventos de Santa Catarina, e nomeia a suposição de
      transferência. *Bloco "Calibration domain, and what the wave threshold is",
      acrescentado em 2026-07-31 junto com o fechamento de AUD-02: 147 pares
      integralmente de SC, aplicados de 35°S a 7°N, com a suposição de
      transferência nomeada.*
- [x] O manuscrito declara o **domínio de validade** do detector, coerente com o
      desfecho de AUD-01. *E a forma da declaração mudou por causa daquele
      desfecho: como AUD-01 **não** aplicou a partição, o domínio não é um recorte
      geográfico, e sim a advertência de que o mesmo detector significa físicas
      diferentes ao longo da costa, com a razão surge/maré variando por quase duas
      ordens de grandeza. §3-bis.4 e parágrafo de limitação.*
- [x] Foi feita uma busca documentada por bases de impacto no N/NE, com resultado
      registrado — positivo ou negativo. *§3-bis.3, com seis famílias de fonte
      avaliadas quanto a cobertura, se são datadas, e se serviriam ao detector.
      **Negativo qualificado.** Declarado que é reconhecimento, não levantamento
      exaustivo, e que o conteúdo das fontes não foi verificado.*
- [x] Se nenhuma base for encontrada, a limitação está declarada como lacuna do
      estado da arte, não omitida. **E a declaração é mais precisa que isso.** *A
      lacuna é real para **recalibração** — não há equivalente aos 147 pares de SC
      — mas **não é irremediável**: duas rotas parciais estão nomeadas
      (verificação qualitativa contra Muehe 2018; verificação da componente de
      nível contra marégrafos GLOSS/RMPG, que é o passo mais tratável e coincide
      com a lacuna de AUD-03). Declarar "nenhuma validação é possível" seria mais
      cômodo e menos verdadeiro.*
- [x] O `R_pos` e o `FAR` estão reportados no manuscrito, com a interpretação PU
      que os contextualiza. **Com os valores corrigidos.** *O `R_pos` = 0,102 do
      registro é do par superseded; no par vigente q70/q99 vale **0,1905**
      (H = 28, M = 119, U = 831). O FAR = 0,984 é do Step 2d, diagnóstico e
      superseded, citável só como tal. Ambos no `README.md` §2e, com a leitura PU:
      recall contra referência incompleta é **piso**, e FAR contra a mesma
      referência não é taxa de alarme falso.*
- [x] A extensão da grade de percentis além de q90 foi testada, e o resultado
      está reportado. *Feito em 2026-07-30 (`audit_AUD_02_threshold_grid_floor`):
      grade estendida a q95 e q99, ótimo migrou para **q70/q99**. O ótimo estava
      de fato fora da borda — mas no eixo do **nível**, não no da onda. §3-bis.2.*
- [x] A subestimação de Recife/Olinda/Jaboatão tem explicação registrada.
      *Registrada no fechamento de AUD-02 (§14, 2026-07-31) e no parágrafo de
      limitação de AUD-13: erosão de forte componente antrópica (Rocha, 2018),
      sinal heterogêneo entre setores adjacentes da mesma orla (Gregório et al.,
      2017) e portanto organizado abaixo da célula do WAVERYS, e cota de dano
      local abaixo do HAT. Os três municípios estão hoje em risco zero — "nenhum
      evento composto aceito em 1993–2025", não impossibilidade física.*

## 10. Riscos de alteração prematura

- **Calibrar regionalmente sem base de impactos regional** é impossível: não há
  como otimizar contra dados que não existem. Qualquer regionalização seria
  arbitrária e pior que a extrapolação atual, porque esconderia a arbitrariedade
  sob aparência de rigor.
- **Estender a grade de percentis** pode mudar o par ótimo e invalidar toda a
  cadeia do Step 3. Fazer apenas como diagnóstico, e adotar somente se houver
  justificativa forte.
- **Buscar validação seletiva** — procurar apenas eventos que o detector captura
  — é viés de confirmação. A busca deve ser definida por região e período, não
  por resultado.

## 11. Condições sob as quais o resultado atual pode ser mantido

Plenamente aceitável manter a calibração atual, desde que:

1. O domínio de calibração seja declarado;
2. A suposição de transferência seja nomeada e discutida;
3. O domínio de validade seja restringido ou qualificado conforme AUD-01;
4. A ausência de base de impactos no N/NE seja declarada como limitação;
5. `R_pos` e `FAR` sejam reportados honestamente.

Desfecho esperado: `limitacao-reconhecida`, possivelmente combinado com
`metodologia-alterada` se AUD-01 restringir o domínio.

## 12. Produtos a jusante que exigiriam regeneração

Se o par de limiares mudar (por extensão da grade ou regionalização), a cadeia
completa a partir da calibração:

```bash
python -m src.02_threshold_calibration.05_pu_composite_calibration.main
python -m src.03_storm_catalog_generation.01_storm_catalogs.main \
       --mode production --tide-mode auto --workers 20
python -m src.03_storm_catalog_generation.hazard_characterization --module all
# depois: cadeia de AUD-01 §12
```

Se apenas houver declaração: nenhum produto muda.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Alterados:** este registro (§3-bis, §9, §13, §14 e nota de leitura), `README.md` (§2e: desempenho do detector com leitura PU; parágrafo de limitação), `docs/scientific_audit/ISSUE_TRACKER.md` | Busca documentada + declaração. **Nenhum script novo — não há cálculo; nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

*Nenhuma investigação registrada. A busca por literatura independente feita na
revisão de linha de base está resumida em
`baseline/2026-07-29_initial_review.md` §7, com as fontes listadas ao final
daquele documento.*

### 2026-07-31 — Busca documentada por base regional; e dois números do registro caducaram

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Existe base de impactos costeiros no N/NE com a qual verificar a extrapolação? A lacuna é irremediável ou apenas não explorada (§8.1)? E os números de desempenho do registro continuam válidos? |
| **Dados e métodos** | Leitura de `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` e de `outputs/audit/AUD-01_validity_domain_partition/partition_summary.json`; e reconhecimento bibliográfico e de bases públicas por busca na web, avaliando cada candidata quanto a cobertura geográfica, existência de **datas** e adequação a validar um detector de eventos datados |
| **Scripts executados** | Nenhum. Não há cálculo nesta questão; emitir uma tabela fixa por script daria aparência de diagnóstico a um levantamento bibliográfico |
| **Novas saídas geradas** | Nenhuma. O registro é a documentação da busca, e é versionado |
| **Achados** | (a) **`R_pos` subiu**: 0,102 no par q90/q90 superseded para **0,1905** no par vigente q70/q99 (H = 28, M = 119, U = 831). O número da §3.2 caducou. (b) **O ótimo de borda já foi testado** em 2026-07-30: a grade foi a q95/q99 e o ótimo migrou — mas no eixo do **nível**, não no da onda. A §3.3 caducou. (c) **A busca devolve negativo qualificado.** Não existe no N/NE equivalente aos 147 pares município×data de SC, logo **recalibração regional continua impossível**. Mas três fontes servem parcialmente e estão nomeadas: *Panorama da Erosão Costeira no Brasil* (Muehe, org., MMA, 2018), com capítulo por estado costeiro, que diagnostica **onde** a costa recua e não **quando** houve evento — teste qualitativo apenas; a análise datada de ressacas em Fortaleza/CE (Paula, Morais, Ferreira & Dias, 2015), que é o análogo mais próximo do que Leal et al. (2024) dá para SC, mas cobre **um município**; e as redes maregráficas **GLOSS-Brasil** (CHM/Marinha) e **RMPG** (IBGE), com estações no N/NE, que validariam a **componente de nível** diretamente e **nunca foram usadas**. (d) O S2ID e o Atlas Digital cobrem o N/NE e são datados, mas são dirigidos por declaração de emergência e já estavam excluídos por sub-reporte. (e) **O domínio de validade foi caracterizado e deliberadamente não aplicado** por AUD-01: a partição por razão surge/maré é bimodal com antimodo em 0,257 e intervalo 32× o típico, mas a decisão adotada elimina a patologia por construção em vez de excluir domínio |
| **Interpretação** | A pergunta do §8.1 era binária — irremediável ou não explorada — e a resposta é **não explorada**, o que é menos confortável e mais verdadeiro. Declarar "nenhuma validação é possível no N/NE" encerraria a questão sem custo e seria falso: a validação da componente de **nível** contra marégrafos é tratável hoje, com dado público, e é o passo que também fecharia a lacuna registrada em AUD-03. O que de fato não é possível é **recalibrar** fora de SC, por ausência de conjunto positivo datado com cobertura regional. A distinção entre "não dá para recalibrar" e "não dá para verificar nada" é a substância desta questão, e o manuscrito precisa fazê-la |
| **Alterações implementadas** | Nenhuma em valor publicado. `README.md` §2e ganhou o bloco de desempenho do detector com a leitura PU e os números corrigidos; parágrafo de limitação escrito |
| **Validação realizada** | `R_pos` e o par vigente lidos diretamente da tabela de calibração, não de documentação secundária. A partição de domínio conferida no `partition_summary.json` de AUD-01 |
| **Incerteza remanescente** | (1) **O reconhecimento não é exaustivo** e o conteúdo das fontes **não foi verificado** nesta sessão — apenas existência, escopo e natureza. A página do MMA que descreve o volume de Muehe está sob acesso restrito e não pôde ser lida. (2) Nenhuma das duas rotas parciais foi executada. (3) Não foi procurada base de autoridade portuária nem de capitania, que o §8.1 listava entre os candidatos |
| **Próxima decisão necessária** | Do pesquisador: fechar por declaração, ou executar a verificação contra marégrafos antes de fechar |

### 2026-07-31 — DECISÃO: fechar como `limitacao-reconhecida`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | Fechar por declaração. O domínio de calibração, a suposição de transferência, os números de desempenho com leitura PU e o resultado da busca — negativo qualificado, com rotas nomeadas — ficam declarados no `README.md` e no parágrafo de limitação. **Nenhuma alteração de método, de escopo geográfico ou de valor publicado** |
| **O que fica declarado, e não deve ser suavizado** | O detector é empiricamente ancorado **apenas no Sul/Sudeste**. Fora dali é extrapolação cujo significado físico muda com a razão surge/maré, que varia por quase duas ordens de grandeza. As fontes que poderiam testá-lo parcialmente **existem e foram identificadas**, mas não foram usadas neste ciclo |
| **Trabalho futuro nomeado, em ordem de tratabilidade** | (1) **Comparação com marégrafos GLOSS-Brasil/RMPG** no N/NE — dado público, valida a componente de nível, e fecha também a lacuna de AUD-03. (2) Teste de sanidade qualitativo contra os capítulos estaduais de Muehe (2018). (3) Busca em registros de capitania e de autoridade portuária, não realizada |
| **O que o desfecho NÃO cobre** | (1) A suíte de casos conhecidos — **AUD-05**, a última P0 aberta. (2) A validação da componente de nível, que continua pendente em AUD-03, fechada como limitação reconhecida pelo mesmo motivo |
