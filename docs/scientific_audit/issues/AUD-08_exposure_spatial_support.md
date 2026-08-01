# AUD-08 — Exposição: saturação do termo relativo e problema da unidade de área modificável (MAUP)

| Campo | Valor |
|-------|-------|
| **ID** | AUD-08 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | exposição |
| **Etapa do fluxo** | Step 4.2 → Step 4.4 |
| **Afeta** | código, interpretação, saídas |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim — satisfeito: saturação eliminada, MAUP medido e declarado com casos nomeados |
| **Status** | `resolvido` |
| **Desfecho** | `mitigado-parcialmente` — a saturação foi **eliminada** pela população efetiva; o MAUP **permanece**, medido e declarado como viés direcional |
| **Depende de** | — |
| **Bloqueia** | AUD-05 |
| **Relacionado a** | AUD-13, AUD-14, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2, §6.2, §8 item 6, §9.2 itens 10 e 15 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (medição contra o produto atual e fechamento) |

---

> ### Nota de leitura — dos dois defeitos da §1, um foi eliminado e o outro não
>
> **A saturação acabou.** Sob `pop_10km`, 59 de 282 municípios encostavam no
> teto do termo relativo e 92 passavam de 0,99. Sob `pop_eff`: **zero e zero**,
> mediana 0,373. Toda a §3.1 descreve um defeito que a decisão de 2026-07-31
> dissolveu — e que nunca havia sido remedido.
>
> **O MAUP continua**, e a população efetiva não o toca. Removê-lo do índice
> levaria Itaboraí/RJ de 118º a **9º** e Campos dos Goytacazes de 159º a **72º**
> — mas também o Rio de Janeiro em 49 posições, que é a distorção oposta.
>
> **O critério 5 diagnostica o MAUP no lugar errado**: pede suporte mais fino que
> o municipal, quando a população já é contada em grade de 200 m/1 km. O MAUP
> está no **denominador**, não na contagem. Ver §3-bis.
>
> Fechada como `mitigado-parcialmente` por decisão do pesquisador em 2026-07-31.

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

- [x] A escada de bandas (1/2/5/10 km) foi executada e seu efeito no ranking está
      quantificado e publicado. *`outputs/audit/AUD-08_exposure_support/band_ladder.csv`,
      contra o produto atual. ρ com o publicado: `pop_1km` 0,924 (com **30**
      municípios de exposição nula), `pop_2km` 0,963 (13), `pop_5km` 0,986 (4),
      `pop_10km` 0,976 (1), `pop_eff` 1,000 (2, e por construção). O registro
      chamava este de "o teste de robustez mais barato do repositório e ainda não
      feito"; agora está versionado.*
- [x] A saturação do termo relativo está quantificada, e está demonstrado se a
      metade absoluta compensa ou não a perda de discriminação. **A pergunta
      mudou de objeto: a saturação foi eliminada, não compensada.** *Sob
      `pop_10km`, 59 de 282 municípios no teto exato e 92 acima de 0,99, mediana
      0,899. Sob `pop_eff`: **nenhum** no teto, **nenhum** acima de 0,99, mediana
      **0,373**. Os 59 que antes saturavam hoje se espalham. A metade absoluta
      não precisa compensar nada — o defeito nº 1 da §1 deste registro foi
      **dissolvido** pela decisão de população efetiva, e ninguém havia medido.*
- [x] Está decidido e justificado: manter [0, 1], adotar balizas realistas, ou
      remover o termo relativo. **Mantido [0, 1], e agora com justificativa
      medida.** *O motivo que levaria a balizas realistas era a saturação, que
      não existe mais — o intervalo natural [0, 1] passou a ser percorrido sem
      encostar no teto, que é a condição sob a qual o pareamento INFORM (Box 2)
      funciona como projetado. Remover o termo relativo foi testado e **movimenta
      o índice para outra distorção**: favorece as metrópoles, com a cidade do
      Rio de Janeiro ganhando 49 posições. Declarado no `README.md`.*
- [x] Os casos de Campos dos Goytacazes e Linhares têm a contribuição de cada
      componente decomposta, e a posição resultante é aceita explicitamente ou
      corrigida. **Decompostos; posições aceitas, com o viés declarado.**
      *Campos dos Goytacazes: 483 486 habitantes, `pop_eff` 8 825,
      `Exposure_absolute` 0,486 contra `Exposure_relative` **0,018**,
      `Exposure_Index` 0,094 — **159º**, subiria a **72º** sem o termo relativo.
      Linhares: `pop_eff` 3 623, relativo 0,022, **188º** → 164º. Os dois subiram
      em relação ao produto de 2026-07-29 (266º e 272º), mas o mecanismo
      permanece. `denominator_penalty.csv` lista os mais penalizados.*
- [x] Existe pelo menos uma estimativa da magnitude do efeito MAUP, por
      comparação com um suporte espacial mais fino. **Feita, com o critério
      reformulado — o enunciado original diagnostica o MAUP no lugar errado.**
      *A população **já** é contada na Grade Estatística do IBGE a **200 m em
      área urbana e 1 km em rural**, suporte **mais fino que setor censitário**;
      não há o que refinar na contagem. O MAUP está na **unidade de reporte e no
      denominador**, e é isso que foi medido: mediana de 0,373 da população
      municipal dentro de `pop_eff`, e o contrafactual sem o termo relativo dá
      ρ = 0,977 com deslocamentos de até **+109 posições** (Itaboraí/RJ).*
- [x] O manuscrito declara que a exposição é **proximidade, não inundação
      modelada**, e que a unidade municipal introduz MAUP. *A primeira metade já
      constava do glossário do `README.md`; **a segunda não constava em lugar
      nenhum** e foi acrescentada em 2026-07-31 como parágrafo de limitação, com
      os casos nomeados e o viés declarado como **piso**, não como estimativa
      centrada.*
- [x] A docstring falsa de `exposure_index.py` L47–48 está corrigida (AUD-17).
      *Corrigida em 2026-07-29, commit `e2680ed`.*

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
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_08_exposure_support.py`, `outputs/audit/AUD-08_exposure_support/`. **Alterados:** este registro (§9, §13, §14 e nota de leitura), `README.md` (parágrafo de limitação novo), `docs/scientific_audit/ISSUE_TRACKER.md` | Remedição + declaração do MAUP. **Nenhum valor numérico publicado alterado** |

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

> **Nota de 2026-07-31.** O esquema implementado foi de **quatro** bandas —
> `pop_eff = 0,4·pop_1km + 0,3·pop_2km + 0,2·pop_5km + 0,1·pop_10km`, pesos de
> anel 1,0 / 0,6 / 0,3 / 0,1 — e não o de três recomendado acima. A ressalva
> "**Não testado:** a banda de 2 km existe e não entra no esquema; um esquema de
> quatro bandas não foi avaliado" ficou, portanto, **superada pela
> implementação**.

### 2026-07-31 — Remedição: a saturação acabou, o MAUP não

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Os dois defeitos da §1 sobrevivem à população efetiva? E qual é a magnitude do MAUP, medida onde ele de fato está? |
| **Dados e métodos** | `site/public/data/risk_index_municipalities.geojson` (282 entregues, 280 com risco). Saturação do termo relativo nas cinco opções de suporte; escada de bandas com a receita publicada aplicada a cada uma; e contrafactual sem o termo relativo, com o perigo e a vulnerabilidade fixos |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_08_exposure_support` |
| **Novas saídas geradas** | `outputs/audit/AUD-08_exposure_support/{saturation_by_band.csv, band_ladder.csv, denominator_penalty.csv, summary.json}` |
| **Achados** | (a) **A saturação foi eliminada.** `pop_10km`: mediana 0,899, 92 acima de 0,99, **59 no teto exato**. `pop_eff`: mediana **0,373**, **0** e **0**. Os 59 que saturavam hoje se espalham. (b) **`pop_eff` é o único suporte testado que evita os dois modos de falha ao mesmo tempo**: `pop_1km` deixa 14 municípios sem residente contado (30 com exposição nula, contando a baliza de 100 habitantes), `pop_10km` satura um quinto da amostra, `pop_eff` não faz nem um nem outro. (c) **O MAUP permanece e é direcional.** Sem o termo relativo: **Itaboraí/RJ 118º → 9º (+109)**, **Campos dos Goytacazes 159º → 72º (+87)**, Araruama/RJ 67º → 11º, Araranguá/SC 106º → 57º, **Rio de Janeiro 100º → 51º**, Guapimirim/RJ 53º → 13º, Osório/RS 156º → 122º. ρ global 0,977, top-20 14/20. (d) Campos dos Goytacazes tem `Exposure_absolute` = 0,486 contra `Exposure_relative` = **0,018**: 483 486 habitantes municipais para 8 825 de população efetiva costeira |
| **Interpretação** | O registro tratava saturação e MAUP como duas faces do mesmo problema. **São separáveis, e a decisão de 2026-07-31 separou-os na prática**: a média ponderada das bandas resolveu inteiramente o primeiro e não tocou no segundo. Isso muda o desfecho de "escolher entre manter [0,1], adotar balizas realistas ou remover o termo relativo" para "manter, agora que a razão para mexer nas balizas desapareceu". O contrafactual fecha a terceira opção: remover o termo relativo não corrige o viés, **troca-o de sinal** — Campos sobe 87 posições, mas o Rio de Janeiro sobe 49, e um índice que ordena metrópoles por tamanho é exatamente o que o pareamento INFORM existe para evitar. O que resta é declarar o viés como **piso**: a posição de municípios grandes e parcialmente interiores é um limite inferior |
| **Achado metodológico sobre o próprio critério 5** | Ele pede comparação com "suporte espacial mais fino (setor censitário)". A população **já** é contada na Grade Estatística do IBGE a 200 m urbano / 1 km rural, que é **mais fino que setor censitário**. Não há refinamento a fazer na contagem, e não existe setor censitário no repositório. O MAUP deste produto está na **unidade de reporte e no denominador municipal** — foi assim que o medi, e o critério foi reformulado em vez de declarado impossível |
| **Alterações implementadas** | Script novo e parágrafo de limitação no `README.md` — a declaração de MAUP **não existia em lugar nenhum**, apenas a de proximidade-não-inundação. **Nenhum valor numérico publicado alterado** |
| **Validação realizada** | A receita de exposição do script reproduz `Exposure_absolute`, `Exposure_relative` e `Exposure_Index` publicados; a escada com `pop_eff` devolve ρ = 1,000 e deslocamento mediano 0, como tem de ser. Uma primeira versão do contrafactual incluía os municípios de risco nulo e mostrava Recife e Olinda "ganhando" 80 posições — **artefato de empate**, já que os 84 zeros formam um bloco único e a movimentação vinha de onde o bloco começa. Corrigido: o cálculo passou a excluí-los |
| **Incerteza remanescente** | (1) **O MAUP não foi eliminado**, apenas medido e declarado. (2) A magnitude reportada é a do contrafactual extremo — remover o termo por inteiro —, e não uma estimativa de quanto o índice "deveria" mudar; serve como cota, não como correção. (3) Nenhuma unidade de reporte alternativa foi testada: manter o município é herança do SVI e da associação, não escolha desta questão |
| **Próxima decisão necessária** | Do pesquisador: aceitar as posições de Campos dos Goytacazes e Linhares com o viés declarado, ou reabrir a forma do termo relativo |

### 2026-07-31 — DECISÃO: fechar como `mitigado-parcialmente`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | **Manter o termo relativo e as posições resultantes**, com o viés declarado no manuscrito. Nenhuma alteração de fórmula |
| **Por que `mitigado-parcialmente`** | Dos dois defeitos que criaram a questão, um foi **eliminado** — a saturação, por construção, pela população efetiva — e o outro **permanece**. Nem `resultado-validado-mantido`, que sugeriria que nada precisou mudar, nem `metodologia-alterada`, que sugeriria que a mudança resolveu a questão |
| **O que fica declarado** | O ranking de municípios grandes e parcialmente interiores é **piso**, não estimativa centrada; Campos dos Goytacazes e Linhares são nomeados; e a distorção está no **denominador**, não no suporte da contagem, que já é de 200 m/1 km |
| **O que o desfecho NÃO cobre** | (1) A eliminação do MAUP, que exigiria trocar a unidade de reporte — herança do SVI e da associação, fora do alcance desta questão. (2) A suíte de casos conhecidos — **AUD-05**, última questão aberta, e onde Campos dos Goytacazes reaparece como caso de referência |
