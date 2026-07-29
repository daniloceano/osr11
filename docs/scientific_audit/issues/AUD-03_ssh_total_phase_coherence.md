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
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-01, AUD-02, AUD-12 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.1(b), §8 item 12 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

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

- [ ] A magnitude do erro de fase está quantificada em centímetros e como fração
      do desvio-padrão local de `SSH_total`, por faixa de latitude.
- [ ] A correlação de posto entre a `SSH_total` atual e pelo menos uma
      formulação coerente em fase está calculada por ponto; se ρ ≥ 0,99 na
      mediana, o efeito é declarado desprezível **com o número reportado**.
- [ ] Existe pelo menos uma comparação com nível observado (maregrafo) em um
      ponto do Sul e um do Norte, ou está registrado que o dado não está
      disponível e por quê.
- [ ] `README.md` §2c e
      `src/03_storm_catalog_generation/config/analysis_config.py` declaram a
      incoerência de fase, sua magnitude medida e a justificativa da escolha.
- [ ] A decisão está tomada: manter a definição atual com a limitação declarada,
      ou substituí-la.

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada. A revisão de linha de base identificou a
incoerência por inspeção da definição, sem quantificá-la.*
