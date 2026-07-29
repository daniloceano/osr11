# AUD-08 — Exposição: saturação do termo relativo e problema da unidade de área modificável (MAUP)

| Campo | Valor |
|-------|-------|
| **ID** | AUD-08 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | exposição |
| **Etapa do fluxo** | Step 4.2 → Step 4.4 |
| **Afeta** | código, interpretação, saídas |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação explícita — o termo penaliza sistematicamente municípios com erosão costeira documentada |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | AUD-05 |
| **Relacionado a** | AUD-13, AUD-14, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2, §6.2, §8 item 6, §9.2 itens 10 e 15 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

O `Exposure_Index` é a média geométrica de uma metade **absoluta**
(`log10(pop_10km)` entre balizas fixas) e uma metade **relativa**
(`pop_10km / pop_municipality`). A metade relativa tem dois defeitos:

1. **Satura em um terço da amostra** — 92 de 282 municípios têm razão > 0,99,
   dos quais 59 exatamente em 1,0 — e portanto quase não discrimina.
2. **Penaliza sistematicamente municípios grandes com setor costeiro pequeno**,
   que é exatamente o caso de vários hotspots reais de erosão costeira brasileira.

## 2. Por que importa cientificamente

O município é a unidade errada para um fenômeno que ocorre numa faixa de
centenas de metros. Ao dividir a população costeira pela população municipal
total, o índice não mede exposição: mede **quão costeiro é o município**, que é
uma propriedade do recorte administrativo, não do risco.

O resultado é um caso-livro de MAUP:

- **Campos dos Goytacazes/RJ**, que contém o Farol de São Tomé — um dos casos de
  erosão costeira mais documentados do país — recebe `Exposure_relative` = 0,025
  e cai para a 266ª posição de 280.
- **Linhares/ES**, que contém Regência, na foz do Rio Doce, recebe 0,032 e cai
  para 272ª.

Os 12 174 e 5 386 residentes dentro de 10 km desses municípios não são poucos em
termos absolutos; a informação existe no dado e é destruída pela razão.

## 3. Evidência original

De `outputs/exposure/municipal_exposure.csv` e
`site/public/data/risk_index_municipalities.geojson`:

### 3.1 Saturação do termo relativo

| estatística de `pop_10km / pop_municipality` | valor |
|---|---|
| mediana | 0,899 |
| n com razão > 0,99 | **92 de 282 (33 %)** |
| n com razão ≥ 1,00 (saturados no teto) | **59** |

O termo absoluto também satura, mas muito menos: pela docstring de
`exposure_index.py` L58–60, um município atinge o piso e cinco o teto, deixando
98 % na escala contínua.

### 3.2 Municípios penalizados pela razão

| Município | `pop_municipality` | `pop_10km` | razão | `Exposure_Index` | `Risk_Hazard` (posição) |
|---|---|---|---|---|---|
| Santa Rita/MA | 36 789 | **4** | 0,000 | 0,010 (piso) | 0,106 (278º) |
| Calçoene/AP | 10 554 | 101 | 0,010 | 0,010 (piso) | 0,129 (277º) |
| Oiapoque/AP | 27 264 | 518 | 0,019 | 0,058 | 0,237 (270º) |
| **Campos dos Goytacazes/RJ** | 483 486 | 12 174 | 0,025 | 0,115 | **0,258 (266º)** |
| **Linhares/ES** | 166 694 | 5 386 | 0,032 | 0,118 | **0,218 (272º)** |
| Barreirinhas/MA | 65 690 | 2 711 | 0,041 | 0,122 | 0,342 |
| São João Batista/MA | 18 979 | 1 303 | 0,069 | 0,138 | 0,424 |
| Itapipoca/CE | 130 429 | 9 574 | 0,073 | 0,191 | 0,259 |

### 3.3 Totais agregados

De `outputs/exposure/municipal_exposure_metadata.json`:

| banda | população | domicílios |
|---|---|---|
| município inteiro | 37 391 121 | 13 714 191 |
| 10 km | **30 827 637** | 11 396 273 |
| 5 km | 21 552 910 | 8 053 549 |
| 2 km | 11 537 220 | 4 388 613 |
| 1 km | 5 935 668 | 2 274 428 |

**As quatro bandas já estão calculadas** — a escada de sensibilidade está
disponível e nunca foi usada.

### 3.4 Contribuição ao índice final

- `Exposure_Index`: mín 0,010; p10 0,399; mediana 0,712; p90 0,889; máx 1,000;
  sd(log) = 0,547.
- Participação na variância de log(`Risk_Hazard_raw`): **27,0 %**.
- Spearman(`Exposure_Index`, `Risk_Hazard`) = 0,198 — a menor das três.
- Spearman(`Exposure_Index`, `SVI/100`) = **−0,588** (ver AUD-13).
- Deixar-a-exposição-de-fora: ρ = 0,803 com o índice publicado.
- Trocar por posto de `pop_10km`: ρ = 0,773, top-20 = 10/20.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/exposure_index.py` | `exposure_relative()` L126–139 | O termo problemático; `clip(0,1)` no teto |
| `src/04_risk_integration/exposure_index.py` | `exposure_absolute()` L105–123 | Metade absoluta, balizas fixas |
| `src/04_risk_integration/exposure_index.py` | `exposure_inform()` L142–157 | Combinação geométrica com piso `CLIP_FLOOR` = 0,01 (L66) |
| `src/04_risk_integration/exposure_index.py` | `GOALPOST_MIN/MAX` L61–62 | 10² e 10⁶ habitantes |
| `src/04_risk_integration/exposure_index.py` | `all_variants()` L166–176 | Quatro candidatos: `E_inform`, `E_log10`, `E_rank`, `E_linear` |
| `src/04_risk_integration/municipal_exposure.py` | `accumulate_tile()` L138–200 | Agregação por centroide de célula |
| `src/04_risk_integration/municipal_exposure.py` | `DISTANCE_BANDS_KM` L73 | `(1.0, 2.0, 5.0, 10.0)` |
| `src/site/export_risk_index_data.py` | `EXPOSURE_FIELD` L68 | `pop_10km` — a banda escolhida |
| `src/site/export_risk_index_data.py` | L561–568 | Aplicação de `exposure_inform` |
| `src/exploratory/make_exploratory_exposure_normalization.py` | — | Comparador já existente das quatro variantes |

### Dados e saídas

- `outputs/exposure/municipal_exposure.csv` — 282 linhas, bandas de 1/2/5/10 km.
- `outputs/exposure/municipal_exposure_metadata.json`
- `outputs/exploratory_exposure/exposure_normalization_summary.json`
- `outputs/exploratory_exposure/risk_with_exposure_summary.json`
- `site/public/data/exposure_municipalities.geojson`,
  `site/public/data/exposure_metadata.json`

### Figuras afetadas

- `outputs/exploratory_exposure/exposure_normalization_comparison.png`
- `outputs/exploratory_exposure/risk_with_exposure_comparison.png`
- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png` (indireta)

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | `E = sqrt(clip(abs, 0.01) · clip(rel, 0.01))`, com `rel = pop_10km / pop_municipality` limitado a [0, 1] |
| **Pretendido/conceitual** | Presença de pessoas onde o perigo atua. `municipal_exposure.py` L9–14 declara corretamente que é **proximidade, não extensão modelada de inundação** |

A metade relativa segue a recomendação INFORM (Box 2) de combinar valor absoluto
e relativo. Mas o próprio módulo reconhece a limitação de transferência
(`exposure_index.py` L38–45): a INFORM define as balizas do termo relativo na
faixa realista, que em escala nacional é uma fração de porcento; aqui usou-se o
intervalo natural [0, 1] porque a fração municipal costeira efetivamente o
percorre. É essa decisão que causa a saturação.

## 6. Divergência documentação ↔ implementação ↔ saídas

**Uma divergência confirmada e material:** a docstring de
`src/04_risk_integration/exposure_index.py` L47–48 afirma

> *"Nothing in this module feeds the published risk index. It is wired into the
> website exposure layer and the exploratory comparisons only."*

Isso é **falso**: `src/site/export_risk_index_data.py` L48–55 importa
`exposure_inform`, `exposure_absolute` e `exposure_relative`, e a L563 os usa
para compor `Risk_Hazard`. Ver AUD-17, inconsistência #2.

## 7. Explicações alternativas plausíveis

1. **A recomendação INFORM é sólida e o pareamento absoluto/relativo é correto.**
   O problema não seria o conceito, mas as balizas do termo relativo. Redefini-las
   para a faixa realista observada (ex.: p05–p95 da razão) preservaria o conceito
   e eliminaria a saturação.
2. **Municípios com fração costeira baixa podem ter risco genuinamente baixo em
   termos populacionais agregados.** Se 97,5 % da população de Campos dos
   Goytacazes está a mais de 10 km da costa, o risco *municipal médio* é de fato
   baixo. O problema seria a unidade de análise, não o índice.
3. **A banda de 10 km pode ser larga demais.** Uma banda de 1 ou 2 km
   discriminaria melhor a população efetivamente exposta e alteraria as razões.
   O dado já existe.
4. **A saturação pode ser inofensiva na prática.** Se os 92 municípios saturados
   forem discriminados adequadamente pela metade absoluta, a média geométrica
   ainda funciona. Isso é verificável.
5. **O caso de Campos/Linhares pode ser corrigido por AUD-04 e não por AUD-08**,
   se o problema real for o perigo atribuído. Verificável separando as causas.

## 8. Diagnósticos propostos

1. **Escada de bandas de distância**: recalcular `Exposure_Index` e
   `Risk_Hazard` para 1, 2, 5 e 10 km (dado já disponível em
   `municipal_exposure.csv`); comparar mapas, ρ de Spearman e sobreposição de
   top-20. *Este é o teste de robustez mais barato do repositório e ainda não foi
   feito.*
2. **Balizas realistas para o termo relativo**: substituir [0, 1] por [p05, p95]
   da razão observada, ou por balizas fixas justificadas; medir a redução da
   saturação e o efeito no ranking.
3. **Comparar as quatro variantes já implementadas** (`E_inform`, `E_log10`,
   `E_rank`, `E_linear`) no nível do risco final, consolidando
   `make_exploratory_exposure_normalization.py` e
   `make_exploratory_risk_with_exposure.py` em um produto de artigo.
4. **Verificar a discriminação residual**: entre os 92 municípios com razão >
   0,99, qual a dispersão de `Exposure_Index`? Se for alta, a metade absoluta
   está fazendo o trabalho e a saturação é inofensiva.
5. **Teste de MAUP direto**: recalcular a exposição por **setor censitário
   costeiro** para um subconjunto (RJ, ES, SC) e comparar com o valor municipal.
   Quantificar a distorção para Campos dos Goytacazes e Linhares.
6. **Separar causas para Campos/Linhares**: decompor a posição de cada um em
   contribuição de perigo, exposição e SVI, e simular a posição sob
   `Exposure_relative` removido.

## 9. Critérios objetivos de resolução

- [ ] A escada de bandas (1/2/5/10 km) foi executada e seu efeito no ranking está
      quantificado e publicado.
- [ ] A saturação do termo relativo está quantificada, e está demonstrado se a
      metade absoluta compensa ou não a perda de discriminação.
- [ ] Está decidido e justificado: manter [0, 1], adotar balizas realistas, ou
      remover o termo relativo. A justificativa referencia a metodologia INFORM e
      declara o desvio, se houver.
- [ ] Os casos de Campos dos Goytacazes e Linhares têm a contribuição de cada
      componente decomposta, e a posição resultante é aceita explicitamente ou
      corrigida.
- [ ] Existe pelo menos uma estimativa da magnitude do efeito MAUP, por
      comparação com um suporte espacial mais fino (setor censitário) em ao menos
      um estado.
- [ ] O manuscrito declara que a exposição é **proximidade, não inundação
      modelada**, e que a unidade municipal introduz MAUP.
- [ ] A docstring falsa de `exposure_index.py` L47–48 está corrigida (AUD-17).

## 10. Riscos de alteração prematura

- **Remover o termo relativo** faz o índice favorecer as metrópoles, exatamente o
  problema que a INFORM Box 2 procura evitar. Rio de Janeiro e São Paulo
  dominariam o ranking por população.
- **Estreitar a banda para 1 km** reduz a população contada de 30,8 M para 5,9 M e
  altera a interpretação do resultado principal — o número "30,8 milhões de
  residentes a até 10 km" é uma das afirmações mais citáveis do trabalho.
- **Mudar para setor censitário** é uma mudança de unidade de análise que exige
  reconstruir também o SVI e a associação de perigo, e não é compatível com o
  cronograma de um artigo em preparação. É melhoria futura (AUD-08 §11).

## 11. Condições sob as quais o resultado atual pode ser mantido

Aceitável se:

1. A escada de bandas mostrar que o ranking é estável (ρ > 0,9 entre 5 e 10 km);
2. A saturação for demonstrada inofensiva pelo diagnóstico 4;
3. O manuscrito declarar a limitação MAUP e citar explicitamente Campos dos
   Goytacazes e Linhares como casos em que a unidade municipal subestima o risco
   costeiro local;
4. A escolha de [0, 1] como balizas do termo relativo for justificada — o módulo
   já contém o embrião da justificativa em L38–45.

## 12. Produtos a jusante que exigiriam regeneração

```bash
python -m src.risk_integration.municipal_exposure      # só se as bandas mudarem
python -m src.site.export_risk_index_data
python -m src.exploratory.make_exploratory_exposure_normalization
python -m src.exploratory.make_exploratory_risk_with_exposure
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
```

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*
