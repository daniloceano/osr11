# AUD-18 — Lacuna de validação independente fora de Santa Catarina; limiares extrapolados sem base de impactos

| Campo | Valor |
|-------|-------|
| **ID** | AUD-18 |
| **Tipo** | `lacuna-validacao` |
| **Componente** | transversal |
| **Etapa do fluxo** | Step 2d/2e (calibração) → Step 3 → Step 4 |
| **Afeta** | dados, interpretação, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo declaração explícita do domínio de calibração e do alcance da extrapolação |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-01, AUD-02, AUD-05 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §6.4, §7.3, §8 item 2 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

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

- [ ] O `README.md` §2e declara explicitamente que a calibração usou
      **exclusivamente** eventos de Santa Catarina, e nomeia a suposição de
      transferência.
- [ ] O manuscrito declara o **domínio de validade** do detector, coerente com o
      desfecho de AUD-01.
- [ ] Foi feita uma busca documentada por bases de impacto no N/NE, com resultado
      registrado — positivo ou negativo.
- [ ] Se nenhuma base for encontrada, a limitação está declarada como lacuna do
      estado da arte, não omitida.
- [ ] O `R_pos = 0,102` e o `FAR = 0,984` estão reportados no manuscrito, com a
      interpretação PU que os contextualiza.
- [ ] A extensão da grade de percentis além de q90 foi testada, e o resultado
      (ótimo de borda ou não) está reportado.
- [ ] A subestimação de Recife/Olinda/Jaboatão tem explicação registrada — seja
      "resultado correto", seja "processo não resolvido pela grade".

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada. A busca por literatura independente feita na
revisão de linha de base está resumida em
`baseline/2026-07-29_initial_review.md` §7, com as fontes listadas ao final
daquele documento.*
