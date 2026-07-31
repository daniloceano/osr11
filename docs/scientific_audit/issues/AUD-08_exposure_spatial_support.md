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
| **Status** | `em-investigacao` |
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


### 2026-07-31 — Banda de distância: 1 km é inviável com a grade do IBGE

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | O pesquisador propôs baixar a exposição de `pop_10km` para `pop_1km`, por entender que as pessoas mais próximas da orla são as efetivamente expostas. O dado sustenta essa banda? |
| **Dados e métodos** | `outputs/exposure/municipal_exposure.csv`, bandas de 1, 2, 5 e 10 km já calculadas. Risco reconstruído para cada banda sob o esquema novo (sem Min–Max, sem piso — ver AUD-11), comparado ao ranking publicado |
| **Achados** | (a) **14 dos 282 municípios têm `pop_1km` = 0.** Com o piso removido, exposição zero ⇒ risco zero: eles somem do produto **por artefato de dado**, não por resultado. (b) Dois deles têm perigo substancial: **Itaboraí/RJ** (223 854 habitantes no município, 29 916 dentro de 10 km, H = 0,63) e **Paulo Lopes/SC** (8 316 dentro de 10 km, H = 0,63). Nenhum dos dois tem população literalmente ausente da faixa costeira — têm o núcleo urbano recuado. (c) **A grade estatística do IBGE é de 200 m em área urbana e 1 km em área rural.** Uma faixa de 1 km está *no limite* da célula rural: um município cujo povoamento comece a 1,5 km da costa lê **zero**, o que é falso como exposição e é exatamente o MAUP que esta questão registra. (d) O efeito no ranking é maior que o da mudança de normalização: |
| **Comparação das bandas** | |

| Banda | Municípios com pop = 0 | Zerados por exposição | ρ com o publicado | Desloc. mediano | Top-10 |
|---|---|---|---|---|---|
| `pop_1km` | **14** | **13** | 0,832 | 35 | **2/10** |
| `pop_2km` | 5 | 4 | 0,885 | 27 | 4/10 |
| `pop_5km` | 2 | 2 | 0,929 | 20 | 7/10 |
| `pop_10km` *(atual)* | 0 | 0 | 0,954 | 21 | 8/10 |

| Campo | Conteúdo |
|-------|----------|
| **Interpretação** | A intenção é fisicamente correta — a exposição a inundação costeira decai rapidamente com a distância da orla, e 10 km é generoso. O problema é de **suporte espacial**, não de conceito: a resolução da grade não sustenta uma faixa de 1 km, e o efeito colateral não é ruído, é a supressão de municípios com perigo real. Uma banda que zera Itaboraí publica a afirmação de que ninguém ali está exposto, o que é indefensável |
| **Opções** | **(i)** 2 km — honra a intenção, 5 zeros. **(ii)** 5 km — compromisso, 2 zeros, top-10 7/10. **(iii)** 1 km tratando `pop = 0` como **sem dado** em vez de zero, isto é, recuando para a banda seguinte com o registro da substituição, o que preserva a intenção sem a supressão espúria. **(iv)** manter 10 km |
| **Recomendação** | **(iii) ou (ii).** Não (i) nem 1 km puro: o custo é a supressão de municípios com perigo, não uma escolha de escala |
| **Alterações implementadas** | Nenhuma. Documentação apenas |
| **Próxima decisão necessária** | Do pesquisador: escolher a banda. É a única peça faltante do pacote de implementação de AUD-11 |


### 2026-07-31 — DECISÃO: exposição por média ponderada das bandas, com decaimento por distância

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31, depois de o diagnóstico da entrada anterior mostrar que a banda de 1 km pura suprime 13 municípios por artefato de resolução |
| **Decisão** | A exposição deixa de usar uma banda única. Passa a usar uma **população efetiva**, média ponderada das bandas cumulativas de 1, 5 e 10 km, com pesos decrescentes |

```
pop_efetiva = w1·pop_1km + w5·pop_5km + w10·pop_10km        (Σw = 1)

Exposure_absolute = clip[(log10(pop_efetiva) − 2) / (6 − 2), 0, 1]
Exposure_relative = pop_efetiva / pop_municipality
Exposure_Index    = √(Exposure_absolute × Exposure_relative)
```

#### Por que isto funciona: as bandas são aninhadas

`pop_1km ⊂ pop_5km ⊂ pop_10km`, verificado sem nenhuma violação nos 282
municípios. Uma pessoa a 0,5 km da costa é contada nos **três** termos; uma a
7 km, só no terceiro. A ponderação das cumulativas produz, portanto, um
**decaimento por distância automático**, e o peso efetivo por pessoa é legível
por anel:

| Anel | Peso efetivo por pessoa |
|---|---|
| 0–1 km | `w1 + w5 + w10` = **1,000** |
| 1–5 km | `w5 + w10` |
| 5–10 km | `w10` |

**É pelos pesos de anel que a escolha deve ser julgada**, não pelos `w`
brutos: eles dizem quanto vale uma pessoa a cada distância.

#### Identidade que simplifica a implementação

O pesquisador pediu a mesma ponderação para a população relativa. Ela sai de
graça:

```
pop_efetiva / P  ≡  w1·(pop_1km/P) + w5·(pop_5km/P) + w10·(pop_10km/P)
```

Verificado numericamente: `max|diff| = 2,22e-16`. **Ponderar o numerador já é
ponderar a fração.** Um único conjunto de pesos serve aos dois termos, e a
implementação calcula `pop_efetiva` uma só vez.

#### O problema dos zeros desaparece

**Nenhum município fica com `pop_efetiva` = 0** em qualquer esquema de peso
testado, contra 14 sob `pop_1km` puro. E `pop_efetiva ≤ pop_10km` sempre, porque
os pesos somam 1 e as bandas são aninhadas — a quantidade continua
interpretável como "população efetivamente exposta, sob decaimento por
distância", limitada acima pela população dentro de 10 km.

Os dois casos críticos passam a **degradar em vez de sumir**, que é o
comportamento correto — a população deles *está* recuada, e deve pesar menos,
não desaparecer:

| Município | pop_1km | pop_5km | pop_10km | pop_efetiva (A) | Exposure_Index | Perigo |
|---|---|---|---|---|---|---|
| Itaboraí/RJ | 0 | 0 | 29 916 | **5 983** | 0,109 | 0,627 |
| Paulo Lopes/SC | 0 | 658 | 8 316 | **1 861** | 0,255 | 0,630 |

#### Esquemas de peso testados

Efeito no ranking, sob o esquema de normalização de AUD-11 (sem Min–Max, sem piso):

| Esquema | w1 / w5 / w10 | Pesos de anel (0–1 / 1–5 / 5–10) | Zerados por exposição | ρ | Desloc. mediano | Top-10 |
|---|---|---|---|---|---|---|
| **A** | 0,50 / 0,30 / 0,20 | **1,00 / 0,50 / 0,20** | 0 | 0,954 | 17 | 6/10 |
| B | 0,60 / 0,30 / 0,10 | 1,00 / 0,40 / 0,10 | 0 | 0,948 | 20 | 6/10 |
| C | 0,50 / 0,33 / 0,17 | 1,00 / 0,50 / 0,17 | 0 | 0,952 | 18 | 6/10 |
| D | 0,77 / 0,15 / 0,08 | 1,00 / 0,23 / 0,08 | 0 | 0,943 | 22 | 4/10 |
| E *(controle, sem decaimento)* | 1/3 cada | 1,00 / 0,67 / 0,33 | 0 | 0,957 | 16 | 8/10 |
| *(referência)* só 10 km | 0 / 0 / 1 | 1,00 / 1,00 / 1,00 | 0 | 0,954 | 21 | 8/10 |
| *(referência)* só 1 km | 1 / 0 / 0 | 1,00 / 0 / 0 | **13** | 0,832 | 35 | 2/10 |

**Recomendação: esquema A.** Os pesos de anel são **1,00 / 0,50 / 0,20** — "uma
pessoa na primeira faixa vale uma; entre 1 e 5 km vale meia; entre 5 e 10 km
vale um quinto". É a formulação mais legível para um revisor, o decaimento é
monótono e nítido, e o custo em movimentação de ranking é o menor entre os
esquemas com decaimento real.

| Campo | Conteúdo |
|-------|----------|
| **O que isto resolve** | A supressão de municípios por artefato de resolução da grade. Nenhum município é anulado por exposição; os de núcleo recuado recebem peso reduzido, que é o resultado pretendido |
| **O que NÃO resolve** | O MAUP em si, que é o objeto desta questão. Os pesos continuam sendo uma **escolha**, e a resolução da grade do IBGE (200 m urbano, 1 km rural) continua limitando o termo de 1 km — `pop_1km` = 0 em Itaboraí pode ser em parte artefato de célula. A diferença é que agora o esquema **degrada suavemente** em vez de suprimir. Isso precisa estar declarado no manuscrito |
| **Não testado** | A banda de 2 km existe em `municipal_exposure.csv` e não entra no esquema. Um esquema de quatro bandas não foi avaliado |
| **Alterações implementadas** | Nenhuma. Documentação apenas; implementação em sessão própria |
| **Confirmação pendente** | Os pesos exatos. O pesquisador decidiu a **estrutura** (média ponderada, pesos decrescentes); A é a recomendação, mas B, C ou D são igualmente implementáveis |
