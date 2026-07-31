# AUD-03 — Incoerência de fase na definição de `SSH_total` (zos a 00Z + máximo diário da maré)

| Campo | Valor |
|-------|-------|
| **ID** | AUD-03 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | perigo |
| **Etapa do fluxo** | Step 2c (definição canônica) → Step 3.1 / 3.2 |
| **Afeta** | código, dados, interpretação, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Não isoladamente; exige declaração explícita da limitação no manuscrito |
| **Status** | `aguardando-decisao` |
| **Desfecho** | — *(proposto: `limitacao-reconhecida`)* |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-01, AUD-02, AUD-12 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.1(b), §8 item 12 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 |

---

## 1. Problema

`SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)` soma duas quantidades
avaliadas em **instantes diferentes do dia**: a anomalia de nível do GLORYS12
tomada às 00:00 UTC e o máximo diário da maré astronômica FES2022, que ocorre em
uma hora arbitrária. O resultado não corresponde ao nível efetivo em nenhum
instante real.

## 2. Por que importa cientificamente

- Onde a maré é micro ou mesomareal (Sul/Sudeste), o erro é pequeno em termos
  absolutos e a variável se comporta aproximadamente como "nível alto do dia".
- Onde a maré é macromareal (Norte), o termo de maré domina a soma e a
  componente meteorológica entra **descorrelacionada** do instante do pico:
  `SSH_total` passa a ser essencialmente o envelope de maré com um ruído aditivo.
  Isso amplifica o mecanismo descrito em AUD-01.
- Um revisor de oceanografia física perguntará por que não se usou o nível total
  horário, ou o `zos` interpolado para a hora da preamar. A resposta precisa
  estar no manuscrito.

A magnitude do erro é quantificável e provavelmente pequena em relação ao
próprio q90 no Sul — por isso a prioridade é P1, não P0. Mas ela precisa ser
**medida**, não presumida.

## 3. Evidência original

A revisão de linha de base identificou a incoerência por leitura da definição em
`src/03_storm_catalog_generation/config/analysis_config.py` L19–21:

```
SSH_total definition (canonical, inherited from Step 2c):
    SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)
    Using raw zos without tide is incorrect.
```

Evidência circunstancial de que o termo de maré domina no Norte
(`compound_metrics.csv`, coluna `thr_ssh_total_abs`, médias por faixa):

| Faixa | thr_SSH_total (m) |
|---|---|
| RS | 0,59 |
| SC/PR | 0,66 |
| SP/RJ | 0,75 |
| ES/BA-S | 1,28 |
| NE | 1,36 |
| N eq. | **2,01** |
| AP | **2,25** |

Spearman(`thr_ssh_total_abs`, latitude) = **+0,863** — o limiar de nível é
essencialmente uma função da amplitude de maré local.

**A magnitude do erro de fase ainda não foi quantificada.** Nenhum diagnóstico
foi executado sobre este ponto específico na revisão de linha de base.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/02_threshold_calibration/03_tidal_sensitivity/tides.py` | integração FES2022 | Onde a definição foi estabelecida (Step 2c) |
| `src/03_storm_catalog_generation/01_storm_catalogs/tides.py` | cálculo de maré em tempo de execução | Modo `--tide-mode auto` |
| `src/03_storm_catalog_generation/01_storm_catalogs/io.py` | leitura e montagem de `SSH_total` | Reconstrói `zos + tide_daily_max` quando pré-computado |
| `src/01_data_preparation/preprocessing/interpolate_glorys_to_waverys_grid.py` | regrade | Etapa anterior; confirma a resolução temporal diária do `zos` |

### Configuração

- `src/03_storm_catalog_generation/config/analysis_config.py` L19–21 (definição),
  L110 (`SSH_TOTAL_VAR`), L111 (`TIDE_DAILY_MAX_VAR`), L114–131 (modos de maré),
  L171 (`TIDE_VAR`).
- `data/tide_models_clipped_brasil/` — modelos FES2022 (não versionado).

### Dados e saídas

- `data/unified/*.nc` — datasets metoceânicos unificados.
- `outputs/storm_catalog/catalog_ssh_total_storms.json` — 324 929 episódios.
- `outputs/tidal_sensitivity/` — saídas do Step 2c.

### Figuras e tabelas afetadas

Indiretamente, todas as de AUD-01. Diretamente, as figuras do Step 2c em
`outputs/tidal_sensitivity/`.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | `zos` amostrado a 00:00 UTC + máximo diário da maré, somados escalarmente |
| **Pretendido/conceitual** | Nível total diário máximo — isto é, `max_t[zos(t) + tide(t)]` dentro do dia, com ambos os termos no mesmo instante |

A diferença entre as duas formulações é
`zos(00Z) − zos(t_maré_máxima)`, cuja magnitude é limitada pela variabilidade
sub-diária de `zos` — que o GLORYS12 diário **não resolve**. Este é o ponto
central: a formulação atual pode ser a única possível com o dado disponível.

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` §2c apresenta a definição como canônica e reporta o ganho de
  detecção (22 → 26 eventos em SC), sem discutir a incoerência de fase nem seu
  comportamento diferencial entre regimes de maré.
- Implementação e saídas concordam entre si. A lacuna é de **discussão**, não de
  execução.

## 7. Explicações alternativas plausíveis

1. **A formulação é a melhor possível com dado diário.** O `zos` do GLORYS12 é
   diário; não há informação sub-diária para interpolar. Tomar o máximo da maré
   e somá-lo ao único valor disponível de `zos` é uma aproximação defensável do
   nível total máximo do dia, e conservadora no sentido de nunca subestimar a
   maré.
2. **O erro é pequeno onde importa.** A variabilidade sub-diária de `zos` em
   águas costeiras é dominada por processos de plataforma com escala de horas a
   dias; num dia de tempestade o `zos` varia lentamente, e `zos(00Z)` é uma boa
   estimativa do valor médio diário. Se isso for verdade, o erro é de segunda
   ordem.
3. **O uso de percentil local absorve parte do viés.** Como o limiar é o q90 da
   própria série `SSH_total` construída dessa forma, um viés sistemático é
   parcialmente absorvido pelo limiar. O que não é absorvido é o **ruído**
   introduzido na ordenação dos dias.

## 8. Diagnósticos propostos

1. **Quantificar a variabilidade sub-diária de `zos`** usando um produto horário
   independente para um subconjunto de pontos (ex.: ERA5 já baixado, ou dados de
   maregrafo do GLOSS/IBGE onde disponíveis). Estimar a distribuição de
   `zos(00Z) − zos(t_HW)`.
   *Saída esperada:* magnitude típica do erro em cm, por faixa de latitude.
2. **Comparar `SSH_total` atual com uma versão coerente em fase**, calculada como
   `zos_diário_médio + tide_daily_max` e como `max_t[zos_interp(t) + tide(t)]`
   com `zos` interpolado linearmente entre dias. Recalcular o q90 e a contagem de
   episódios em pontos representativos de cada regime de maré.
3. **Verificar se a ordenação dos dias muda**: correlação de posto entre a série
   `SSH_total` atual e as alternativas, por ponto. Se ρ > 0,99, o problema é
   irrelevante na prática e a questão fecha como `limitacao-reconhecida`.
4. **Comparar contra maregrafos** em 3 a 5 locais com série longa (Rio Grande,
   Cananéia, Salvador, Fortaleza, Belém), verificando a correlação de
   `SSH_total` com o nível observado máximo diário.

## 9. Critérios objetivos de resolução

> **Reformulados em 2026-07-31.** Os critérios originais falavam de `SSH_total`
> como variável segmentada. Desde 2026-07-31 o limiar de nível é o q99 de `zos`
> livre de maré, e a soma só reaparece no portão HAT e na severidade integrada.
> O texto abaixo preserva a intenção de cada critério e a reexpressa sobre o
> método vigente; a redação original está no histórico do git deste arquivo.

- [x] A magnitude do erro de fase está quantificada em centímetros e como fração
      do desvio-padrão local de `zos`, por faixa de latitude.
      *Mediana do domínio 1,2 cm/dia (p95 3,2 cm); ≈1 cm no Norte macromareal
      (17–19 % do desvio-padrão local) contra 5–10 cm no Sul micromareal
      (50–66 %). Ver §14, entrada de 2026-07-31.*
- [x] A correlação de posto entre a série de nível atual e pelo menos uma
      formulação coerente em fase está calculada por ponto; se ρ ≥ 0,99 na
      mediana, o efeito é declarado desprezível **com o número reportado**.
      *Mediana do domínio ρ = 0,9997 — acima do limiar —, mas a mediana esconde
      a estrutura latitudinal: ρ ≥ 0,9996 no Norte e ρ = 0,93–0,98 no Sul, com
      247 dos 808 pontos abaixo de 0,99, todos ao sul de 21° S. O efeito é
      declarado desprezível **no Norte** e **não desprezível no Sul**, contra a
      expectativa da revisão de linha de base.*
- [x] Existe pelo menos uma comparação com nível observado (maregrafo) em um
      ponto do Sul e um do Norte, **ou** está registrado que o dado não está
      disponível e por quê. *Registrado: não há série de nível observado no
      repositório. `data/raw/` contém apenas GLORYS12, WAVERYS e IBGE, e
      `data/reported events/` traz uma lista documental de eventos de SC sem
      níveis de água. Uma comparação com maregrafo do GLOSS/IBGE ou da Marinha
      exigiria nova aquisição com registro de proveniência próprio — fica como
      incerteza remanescente e passo de validação em aberto.*
- [x] `README.md` §2c e
      `src/03_storm_catalog_generation/config/analysis_config.py` declaram a
      incoerência de fase, sua magnitude medida e a justificativa da escolha.
      *README §2c: bloco de citação após a descrição do Step 2c.
      `analysis_config.py`: seção "Phase incoherence of SWL" no docstring do
      módulo.*
- [x] A decisão está tomada: manter a definição atual com a limitação declarada,
      ou substituí-la. *Manter. Não há alternativa: o `zos` do GLORYS12 é
      diário e interpolá-lo para escala horária criaria variabilidade
      sub-diária que o modelo não contém.*
- [x] Existe texto de limitação pronto para o manuscrito.
      *`README.md` → "Declared limitations for the manuscript", primeiro
      parágrafo.*

## 10. Riscos de alteração prematura

- Mudar a definição de `SSH_total` **invalida o Step 2c e o Step 2e por
  completo**: os limiares foram calibrados sobre esta variável. A cadeia inteira
  teria de ser refeita, incluindo a calibração PU.
- Interpolar `zos` para escala horária cria variabilidade sub-diária espúria que
  o modelo não contém — pode piorar em vez de melhorar.
- O ganho esperado é provavelmente pequeno no Sul, onde o trabalho é sólido, e o
  custo é alto. Esta questão provavelmente deve fechar como
  `limitacao-reconhecida` — **mas só depois de medida**.

## 11. Condições sob as quais o resultado atual pode ser mantido

Fortemente provável que o resultado atual seja mantido, desde que:

1. A magnitude do erro seja medida e reportada;
2. O manuscrito declare explicitamente que `SSH_total` é uma **aproximação do
   nível total máximo diário**, limitada pela resolução diária do GLORYS12;
3. Fique claro que a aproximação degrada com o aumento da amplitude de maré, o
   que reforça a discussão de AUD-01.

## 12. Produtos a jusante que exigiriam regeneração

Só se a definição mudar — e nesse caso a cadeia é ainda maior que a de AUD-01,
porque inclui a recalibração:

```bash
python -m src.02_threshold_calibration.03_tidal_sensitivity.main
python -m src.02_threshold_calibration.05_pu_composite_calibration.main
# depois, a cadeia completa de AUD-01 §12
```

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(não commitado)* | `main` | `src/exploratory/audit_AUD_03_ssh_phase_coherence.py` (novo), `README.md` (§2c e limitações do manuscrito), `src/03_storm_catalog_generation/config/analysis_config.py` (docstring), `site/app/methodology/compound-detection/page.tsx` (item "Still-water-level timing" das Assumptions) | Diagnóstico novo + declaração da limitação. **Nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

### 2026-07-31 — Quantificação do erro de fase; a limitação é maior no Sul, não no Norte

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Sob o método vigente — limiar de nível no q99 de `zos` livre de maré, maré atuando como portão `max(SWL) > HAT` — qual é a magnitude do erro de fase, e onde ele importa? |
| **Dados e métodos** | `data/unified/metocean_brazil_unified_waverys_grid.nc`, 808 pontos, 12 053 dias. Como não existe `zos` sub-diário, o valor verdadeiro na hora da preamar foi **limitado**, não estimado: sob interpolação linear entre amostras diárias consecutivas, ele está entre `zos(d)` e `zos(d+1)`. Substituindo cada extremo obtêm-se `SWL_low` e `SWL_high`, e a largura desse intervalo é o erro de fase. Métricas: largura em cm e como fração de `sd(zos)` local; ρ de Spearman entre a `SWL` usada e a variante do ponto médio; e, no portão, quantos dias mudariam de decisão em cada extremo — por dia e por corrida de dias consecutivos acima do HAT |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_03_ssh_phase_coherence` |
| **Novas saídas geradas** | `outputs/audit/AUD-03_ssh_phase_coherence/{phase_error_by_point.csv, band_summary.csv, diagnosis_summary.json}` |
| **Achados** | (a) **O escopo da questão encolheu.** O limiar de nível não usa mais a soma: episódios são segmentados em `zos` livre de maré, sem maré antes do percentil. O erro de fase sobrevive apenas no portão HAT e no termo de nível da severidade integrada. (b) **Magnitude:** mediana do domínio **1,2 cm/dia**, p95 3,2 cm, máximo por ponto 16 cm. (c) **A estrutura latitudinal é o inverso da prevista pela revisão de linha de base.** O erro é ≈1 cm no Norte macromareal (AP, N eq., NE, ES/BA-S: 17–19 % do `sd(zos)` local, ρ ≥ 0,9996) e **5–10 cm no Sul micromareal** (RS 10,5 cm / 66 %, SC/PR 7,6 cm / 59 %, SP/RJ 5,2 cm / 50 %; ρ = 0,93–0,98). A razão é dupla: `sd(zos)` é três vezes maior no Sul (0,16 m contra 0,05 m), e o HAT ali é baixo (0,22 m contra 1,76 m no N eq.), de modo que a `SWL` o cruza em 3–9 % dos dias contra 0,1–0,3 % no Norte — muitos dias ficam perto da fronteira de decisão. (d) **Estabilidade do portão:** 49,0 % dos dias que hoje passam o portão mudariam de decisão no extremo desfavorável (13,7–19,3 % no Norte, 50–52 % no Sul). Agrupando dias consecutivos em corridas — proxy mais próximo da unidade que o portão de fato decide, já que basta um dia qualificado — a fração cai pouco, para 45,5 %: os desvios são fortemente correlacionados dentro de um evento. (e) **É ruído, não viés:** 89 922 dias hoje aprovados seriam perdidos e 91 274 hoje reprovados seriam ganhos — quase simétrico —, de modo que a contagem não é sistematicamente inflada nem deprimida |
| **Interpretação** | A limitação é inerente à base e não tem correção possível: o `zos` do GLORYS12 é diário, e interpolá-lo para escala horária inventaria variabilidade sub-diária que o modelo não contém. O que mudou é **onde** ela vale e **quanto**. O reenquadramento do método (AUD-01) removeu o erro de fase do limiar de detecção, que era o lugar mais danoso, e o confinou ao portão e à severidade. O achado inesperado — o erro é ~10× maior no Sul — não invalida o Sul: como é aproximadamente simétrico, o campo agregado de perigo é estável (ρ = 0,93–0,98 na ordenação dos dias), mas a atribuição de **eventos individuais** no Sul carrega incerteza de nível diário. Isso é relevante para AUD-05, que valida casos costeiros conhecidos, quase todos em SC |
| **Alterações implementadas** | Nenhuma no método. Declaração da limitação em `README.md` §2c, no docstring de `analysis_config.py`, nas Assumptions da página de metodologia do site, e um parágrafo pronto para o manuscrito em `README.md` → "Declared limitations for the manuscript" |
| **Validação realizada** | O script reproduz `hat_m` e as coordenadas diretamente de `compound_metrics_hat.csv`, de modo que o portão avaliado é o mesmo do produto. A métrica por corridas foi acrescentada depois de a primeira versão usar um denominador errado (dias indeterminados sobre dias aprovados, que produzia razões acima de 1); a versão publicada usa contagens direcionadas explícitas |
| **Incerteza remanescente** | (1) **Nenhuma comparação com nível observado.** Não há maregrafo no repositório; sem ele não é possível dizer se o `zos` do GLORYS12 acerta o nível costeiro observado, apenas se é internamente coerente. (2) O limite por interpolação linear é o **pior caso**, não o caso esperado — o valor verdadeiro está dentro do intervalo, e a variante do ponto médio preserva a ordenação com ρ = 0,93–0,98. (3) O efeito não foi medido **no nível de evento** do detector: isso exigiria reexecutar `detection_hat` com `SWL_low` e `SWL_high`, o que não foi feito. Os dias que o portão de fato avalia são os compartilhados por um episódio de onda e um de nível, um subconjunto mais extremo do que todos os dias acima do HAT, portanto provavelmente menos sujeito a inversão do que os 45–49 % reportados |
| **Próxima decisão necessária** | Confirmar o fechamento como `limitacao-reconhecida`. A decisão científica — manter a definição — não tem alternativa com os dados disponíveis; o que resta é o aval do pesquisador sobre o texto da limitação e sobre deixar a comparação com maregrafo como trabalho futuro |
