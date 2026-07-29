# Registro de linha de base — Revisão científica inicial (2026-07-29)

> **DOCUMENTO IMUTÁVEL — NÃO EDITAR.**
>
> Este arquivo preserva, sem alteração de conteúdo, a revisão científica e
> metodológica independente produzida em **2026-07-29** sobre os resultados de
> risco costeiro do OSR11. Ele representa o **estado inicial da revisão** e
> **não deve ser atualizado** para refletir correções, investigações ou
> decisões posteriores.
>
> Todo progresso subsequente é documentado em:
> - `docs/scientific_audit/ISSUE_TRACKER.md` — visão geral e situação atual;
> - `docs/scientific_audit/issues/AUD-*.md` — registros detalhados por questão.
>
> **Notas de contexto (não fazem parte da revisão):**
> - Os caminhos de arquivo e os links relativos no texto abaixo são relativos à
>   **raiz do repositório**, não a este diretório.
> - Todos os valores numéricos citados foram recalculados na sessão de revisão a
>   partir dos arquivos então presentes em `outputs/` e `site/public/data/`.
> - O estado do repositório na data da revisão era o commit `1abf29a`
>   (`Dismiss the municipality card when the pointer leaves the municipality`),
>   ramo `main`, árvore de trabalho limpa.
> - A única correção de forma aplicada na transcrição foi o rebaixamento dos
>   níveis de cabeçalho (`#` → `##`) a partir do título da revisão, para que este
>   arquivo tenha um único `#` de nível superior. Nenhum texto foi alterado,
>   encurtado ou reinterpretado.

---

## Parecer de revisão científica — OSR11: risco costeiro composto (Brasil)

*Revisão baseada em inspeção do código, dos dados intermediários e dos produtos finais entregues, com diagnósticos quantitativos executados sobre `outputs/` e `site/public/data/`. Todos os números citados foram recalculados por mim a partir dos arquivos do repositório.*

---

### 1. Resumo executivo

**Juízo geral:** o produto é **coerente na camada de perigo para o setor Sul/Sudeste, mas o índice integrado de risco não é defensável no estado atual** — não porque a matemática esteja errada, mas porque o padrão dominante do mapa final (hotspots concentrados no Maranhão, Pará e Amapá) é sustentado por eventos "compostos" que são, demonstravelmente, **modulação astronômica de sizígia**, e não eventos de tempestade. O mapa final não é um mapa de risco de inundação costeira composta; é, em boa medida, a superposição do gradiente Norte–Sul de vulnerabilidade social do IBGE sobre um campo de perigo contaminado pela maré na porção equatorial.

**Principais pontos fortes**

1. A cadeia perigo→exposição→vulnerabilidade está implementada com rastreabilidade incomum: `hazard_index.py` é a única implementação do índice, lê a fonte versionada `compound_metrics.csv`, e o exportador (`export_risk_index_data.py:544-583`) recalcula tudo em vez de ler as colunas entregues no shapefile. Os metadados publicados (`risk_index_metadata.json`) registram estatísticas antes e depois de cada normalização — isso é boa prática e raramente encontrado.
2. A **frequência** de eventos compostos tem estrutura espacial fisicamente correta: máximo em RS (231 eventos médios na faixa −36 a −30°) decrescendo monotonicamente para norte (55–60 em BA/NE), com máximo secundário em RJ/SP. Isso é o que se espera da climatologia de ciclones extratropicais e sistemas frontais do Atlântico Sul.
3. A **normalização da intensidade por excesso sobre o limiar local** (`02_compound_detection/detection.py`, docstring) é uma decisão metodológica correta e bem justificada — remove o baseline de maré do pico absoluto de nível. É a razão pela qual a intensidade *não* apresenta viés equatorial forte (Spearman |lat| × intensidade = 0,295 apenas).
4. A média geométrica com piso em 0,01 é conceitualmente adequada ao arcabouço IPCC (conjuntiva) e está corretamente implementada.
5. O SVI é **exatamente reprodutível** a partir das dez variáveis entregues (auditoria documentada em `src/04_risk_integration/external_svi/README.md`: r = 1,000000, PC1 = 50,5 % da variância).

**Principais preocupações** (ordenadas por consequência)

1. **Os "eventos compostos" ao norte de ~20°S estão travados em fase com o ciclo de sizígia-quadratura.** Teste de Rayleigh das datas de início contra o período de 14,765 d: R = 0,81–0,84 e p < 0,01 em **100 %** dos pontos de grade ao norte de 20°S, contra R = 0,085 e apenas 5 % significativos no RS. Isso é um resultado categórico: no Norte/Nordeste o detector está contando marés de sizígia, não tempestades.
2. **O limiar de "onda extrema" no Norte é fisicamente vazio**: `thr_hs_abs` = 0,20 m em Vigia (PA), 0,24 m em Chaves (PA), 0,51 m em Macapá (AP). 35 dos 808 pontos têm q90 de Hs abaixo de 1 m e 129 abaixo de 1,5 m. Um "evento de onda extrema" de 0,3 m não amplifica inundação alguma.
3. **A componente de duração é ruído amplificado.** O intervalo observado é 1,26–2,51 dias (limitado pela resolução diária do GLORYS); o Min–Max o estica para [0,1] e lhe dá peso 1/3. Ela contribui com apenas 6 % da variância do perigo, mas é exatamente o que zera o litoral central de SC — o mínimo global de duração está em (−26,6; −48,6), no coração da costa de ressacas.
4. **O ranking de hotspots não é robusto.** Trocando apenas a agregação do perigo para "frequência apenas", ρ de Spearman com o índice publicado cai para **0,384** e o top-5 muda integralmente (São Sebastião, São José do Norte, Magé, Guarujá, Guaraqueçaba).
5. **A regra de associação ponto-grade → município, documentada no README §4.1, não é reproduzível.** Apenas 15–31 % das atribuições correspondem ao ponto de maior contagem composta na vizinhança (30–50 km); 59 % correspondem simplesmente ao ponto mais próximo. Distância mediana 13,1 km, máxima **89,2 km** (Paracuru/CE). 178 pontos únicos servem 280 municípios; um único ponto (−2,4; −44,2) serve 9 municípios maranhenses.

**Nível de confiança no mapa de hotspots**

| Domínio | Confiança | Justificativa |
|---|---|---|
| Perigo (frequência) S/SE, 20–35°S | **Alta** | fase aleatória vs. sizígia, limiares Hs 2,1–2,7 m, padrão consistente com storm track |
| Perigo composto ao norte de ~15°S | **Muito baixa** | travamento de fase em sizígia, limiares Hs < 1 m |
| Exposição | **Média** | conceito claro e bem documentado, mas o termo relativo satura em 33 % da amostra |
| Vulnerabilidade (SVI) | **Média** | reprodutível, mas 2 de 10 indicadores entram com sinal contrário ao conceito |
| **Mapa final de hotspots** | **Baixa** | 7 dos 10 principais hotspots estão no domínio travado pela maré |

---

### 2. Metodologia efetivamente implementada

#### 2.1 Reconstrução do fluxo

**Perigo** — [hazard_index.py](src/04_risk_integration/hazard_index.py)

Lê `outputs/storm_catalog/compound/compound_metrics.csv` (808 pontos, 1993–2025):

```
Hazard_Frequency = minmax_808(compound_count_total)        # 43 – 322 eventos
Hazard_Duration  = minmax_808(mean_overlap_duration)       # 1,26 – 2,51 dias
Hazard_Intensity = minmax_808(mean_compound_intensity_norm)# 0,169 – 0,510
Hazard_Index_raw = média aritmética simples das três       # 0,147 – 0,728
Hazard_Index     = minmax_808(Hazard_Index_raw)            # 0 – 1
```

O Min–Max final estica a amplitude por fator 1,72. Os âncoras: máximo de frequência em (−35,0; −54,8), **ponto de grade em águas uruguaias**, que não serve município algum; mínimo em (−10,8; −36,2), largo de Sergipe.

**Detecção a montante** ([02_compound_detection/detection.py](src/03_storm_catalog_generation/02_compound_detection/detection.py), [config/analysis_config.py:20](src/03_storm_catalog_generation/config/analysis_config.py#L20)):

```
SSH_total(d) = zos(d, 00:00 UTC) + tide_daily_max(d)     # GLORYS12 + FES2022
evento composto = sobreposição ≥ 1 dia entre episódio Hs>q90 e episódio SSH_total>q90
intensidade = 0,5·[norm(Hs_pico − thr_local) + norm(SSH_pico − thr_local)]
              com Q05/Q95 agrupados no domínio inteiro
```

**Exposição** — [municipal_exposure.py](src/04_risk_integration/municipal_exposure.py) + [exposure_index.py](src/04_risk_integration/exposure_index.py)

Grade Estatística IBGE 2022 (200 m urbano / 1 km rural), atribuição por centroide de célula, distância à linha de costa Natural Earth em EPSG:5880, bandas de 1/2/5/10 km. A banda de 10 km alimenta o índice: 30,83 M de 37,39 M residentes.

```
Exposure_absolute = clip[(log10(pop_10km) − 2)/4, 0, 1]     # balizas fixas 10² – 10⁶
Exposure_relative = clip[pop_10km / pop_municipality, 0, 1]
Exposure_Index    = sqrt(clip(abs,0.01) · clip(rel,0.01))
```

**Vulnerabilidade** — script externo (Karine Bastos Leal, INPE), 10 variáveis SIDRA 2022, z-score → PCA → PC1 (50,5 % da variância) → Min–Max 0–100.

**Integração** — [export_risk_index_data.py:556-583](src/site/export_risk_index_data.py#L556-L583)

```
Hazard_Index_mun = minmax_280(Hazard_Index)      # renormalização municipal
Risk_Hazard_raw  = (clip(H_mun)·clip(E)·clip(SVI/100))^(1/3)   piso 0,01
Risk_Hazard      = minmax_280(Risk_Hazard_raw)   # 0,092–0,719 → 0–1, fator 1,60
```

Classificação: 8 classes de intervalo igual em [0,1] (`FIXED_BOUNDARIES`). **Não existe definição operacional de "hotspot"** — nem limiar percentílico, nem quebra natural, nem critério de significância. As tabelas do artigo usam simplesmente "top-10".

#### 2.2 Divergências entre documentação, código e saídas

Encontrei **sete** inconsistências, três delas materiais:

| # | Onde | Problema | Gravidade |
|---|---|---|---|
| 1 | [README.md:405-408](README.md#L405-L408) | O bloco "Current Implementation Status" declara `Risk_Hazard = norm_municipal[(SVI/100) × Hazard_Index]` — a fórmula de **duas** componentes, superada — e descreve exposição como "spatial join of oceanic hazard metrics to municipalities", exatamente o uso que o §4.1 do mesmo README declara errado e removido | **Alta** — contradiz o §4.4 do próprio README e o código |
| 2 | [exposure_index.py:47-48](src/04_risk_integration/exposure_index.py#L47-L48) | Docstring: *"Nothing in this module feeds the published risk index."* É falso: `export_risk_index_data.py:563` importa `exposure_inform` para compor `Risk_Hazard` | **Alta** |
| 3 | [export_risk_index_data.py:818-822, 898-903](src/site/export_risk_index_data.py#L818-L822) | Os metadados publicados afirmam que `Hazard_Index_mun` *"is not used by any published field"* / *"no published field uses it"*, enquanto `integrated_risk_formula` no mesmo JSON o usa como fator. O JSON que vai ao site se autocontradiz | **Alta** |
| 4 | [README.md:293](README.md#L293) | Remete a `SCIENTIFIC_NOTES.md` → "Step 4"; **o arquivo não existe na raiz do repositório** | Média |
| 5 | [README.md:202-210](README.md#L202-L210) | Documenta a regra de seleção do ponto ("maior contagem composta dentro da associação"); não se reproduz (15–31 %) | **Alta** |
| 6 | README §4.4 | O bloco "Products generated" aparece duas vezes com conteúdos diferentes | Baixa |
| 7 | [README.md:406](README.md#L406) vs. resto | "281 coastal municipalities" vs. 282 | Baixa |

Nas **saídas**, o que está publicado corresponde ao **código**, não à documentação stale. O leitor do README (item 1) reconstruiria uma fórmula errada.

---

### 3. Coerência das camadas

#### 3.1 Perigo

**O que funciona.** A frequência é a única das três componentes com assinatura sinótica limpa:

| Faixa | thr_hs (m) | thr_SSH_total (m) | eventos (33 a) | duração (d) | intensidade |
|---|---|---|---|---|---|
| RS (−36…−30) | 2,41 | 0,59 | 231 | 1,55 | 0,434 |
| SC/PR (−30…−25) | 2,30 | 0,66 | 207 | 1,50 | 0,339 |
| SP/RJ (−25…−20) | 2,38 | 0,75 | 162 | 1,71 | 0,320 |
| ES/BA-S (−20…−15) | 1,78 | 1,28 | 83 | 1,81 | 0,315 |
| NE (−10…−5) | 2,05 | 1,36 | 61 | 1,89 | 0,267 |
| N eq. (−5…0) | 1,66 | **2,01** | 87 | 1,64 | 0,304 |
| AP (0…7) | 1,70 | **2,25** | 74 | 1,98 | 0,323 |

O gradiente de frequência acompanha a densidade de ciclogênese e passagens frontais do Atlântico Sul, e o par (limiar de Hs alto, alta frequência) no Sul é consistente com o clima de ondas de swell de SSE/S. **Isso é coerente e defensável.**

**O que não funciona.**

*(a) Travamento de fase com a sizígia.* Diagnóstico que executei sobre `compound_catalog.json` (808 pontos, teste de Rayleigh das datas de início contra o período sinódico-semi de 14,765 d):

| Faixa | R (comprimento resultante) | % de pontos com p < 0,01 |
|---|---|---|
| RS | **0,085** | **5 %** |
| SC/PR | 0,375 | 74 % |
| SP/RJ | 0,596 | 100 % |
| ES/BA-S | 0,797 | 100 % |
| BA-N | 0,814 | 100 % |
| NE | 0,837 | 100 % |
| N eq. | **0,817** | **100 %** |
| AP | **0,809** | **100 %** |

No conjunto, 88,5 % dos pontos de grade têm eventos compostos estatisticamente travados no ciclo sizígia-quadratura. No RS — a região onde a literatura documenta ressacas de origem sinótica — a fase é essencialmente aleatória, como deveria ser. **A transição ocorre entre 30° e 25°S.** Este é, para mim, o achado central da revisão: ao norte de ~20°S o catálogo composto não descreve tempestades.

O mecanismo é transparente: com `thr_SSH_total = q90` e amplitude de maré de 4–7,5 m na costa amazônica (São Marcos, MA, chega a 7,1 m em sizígia equinocial), o q90 do SSH_total é essencialmente o envelope de sizígia. As excedências ocorrem quinzenalmente por construção. Somando um limiar de Hs de 0,2–1,0 m — que também é excedido com facilidade —, a coincidência temporal é quase garantida a cada sizígia.

*(b) Incoerência de fase na definição de SSH_total.* `zos` às 00:00 UTC somado ao **máximo diário** da maré é uma soma de duas quantidades avaliadas em instantes diferentes. Onde a maré é micro/mesomareal isso é um erro pequeno; onde a maré é macromareal, o termo de maré domina e a componente de sobrelevação meteorológica fica descorrelacionada do instante do pico. O `README` §2c apresenta isso como "the canonical SSH_total definition" sem discutir a incoerência de fase.

*(c) A duração é um artefato de resolução amplificado.* Amplitude total 1,26–2,51 d, IQR/amplitude = 0,216. A resolução diária do GLORYS impõe durações inteiras em dias; a média sobre dezenas a centenas de eventos produz um número entre 1 e 2,5 quase por construção. O Min–Max transforma essa faixa trivial numa componente de amplitude plena com peso 1/3.

*(d) As três componentes não são mutuamente reforçantes.* Correlações de Spearman na grade nativa: frequência × duração = **−0,550**; frequência × intensidade = +0,516; duração × intensidade = −0,105. Decomposição de variância de `Hazard_Index_raw`: frequência 50,5 %, intensidade 43,5 %, **duração 6,0 %**. A duração quase não contribui para a variância global — mas contribui decisivamente para *rebaixar* pontos específicos, porque anticorrelaciona com a frequência. O README reconhece isso (nota 3 do §4.4) mas o trata como escolha ("índice compensatório explícito"); é uma escolha que produz, no litoral de SC, um resultado que contraria toda a evidência disponível.

*(e) Contaminação por descarga fluvial.* Macapá (0,8; −50,2) e Chaves (0,0; −50,4) estão **dentro do estuário amazônico**. O `zos` do GLORYS12 ali carrega o ciclo sazonal de descarga do Amazonas (amplitude de ordem decimétrica a métrica) e o modelo não resolve a pororoca nem a dinâmica de canal. Ambos aparecem no top-10 de risco.

#### 3.2 Exposição

**Conceitualmente bem tratada.** A documentação é explícita e correta ao afirmar que se trata de **proximidade, não de extensão modelada de inundação** ([municipal_exposure.py:9-14](src/04_risk_integration/municipal_exposure.py#L9-L14)) e ao registrar as duas limitações inerentes — população *de jure* num único instante (31/07/2022) contra 33 anos de registro metoceânico, e suporte espacial não uniforme (200 m/1 km). A adoção das balizas fixas INFORM (10²–10⁶) em vez dos extremos observados é a decisão certa e torna a escala estável.

**Problemas.**

1. **O termo relativo satura em um terço da amostra.** 92 de 282 municípios têm `pop_10km/pop_municipality` > 0,99, e 59 estão exatamente em 1,0. A mediana é 0,899. Metade do índice de exposição, portanto, quase não discrimina — e o que ela faz, na prática, é **punir municípios grandes com setor costeiro pequeno**, que é precisamente o caso de vários hotspots reais.

2. **Superestimação por incluir população não costeira** — a preocupação levantada no briefing — é, na verdade, o **problema inverso** aqui, e mais grave. O uso da razão `pop_10km/pop_municipality` penaliza sistematicamente:

| Município | pop_mun | pop_10km | fração | Exposure_Index | Risk (posição) |
|---|---|---|---|---|---|
| Campos dos Goytacazes/RJ | 483 486 | 12 174 | 0,025 | 0,115 | 0,258 (266º) |
| Linhares/ES | 166 694 | 5 386 | 0,032 | 0,118 | 0,218 (272º) |
| Barreirinhas/MA | 65 690 | 2 711 | 0,041 | 0,122 | 0,342 |
| Santa Rita/MA | 36 789 | **4** | 0,000 | 0,010 (piso) | 0,106 (278º) |

Campos dos Goytacazes contém o **Farol de São Tomé**, um dos casos de erosão costeira mais documentados do país; Linhares contém **Regência**, na foz do Rio Doce, também com erosão e inundação recorrentes. O índice os coloca no fundo do ranking. Este é um caso-livro de **problema da unidade de área modificável (MAUP)**: o município é a unidade errada para um fenômeno que ocorre numa faixa de centenas de metros.

3. **Santa Rita/MA (pop_10km = 4) e Calçoene/AP (pop_10km = 101)** provavelmente não deveriam estar no conjunto costeiro, ou deveriam ser tratados como dados ausentes em vez de receberem o piso 0,01.

#### 3.3 Vulnerabilidade

**Reprodutível e internamente consistente como análise estatística** — mas a **direcionalidade de dois indicadores contradiz o conceito**:

| Indicador | r com SVI | Direção conceitual | Coerente? |
|---|---|---|---|
| `pop_poverty` | **+0,944** | ↑ vulnerabilidade | ✓ |
| `pop_illiterate` | +0,832 | ↑ | ✓ |
| `pop_house` | +0,825 | ↑ | ✓ |
| `pop_nogarbage` | +0,783 | ↑ | ✓ |
| `pop_nonwhite` | +0,779 | ↑ | ✓ |
| `pop_nosewage` | +0,720 | ↑ | ✓ |
| `pop_nowater` | +0,569 | ↑ | ✓ |
| `pop_nopaving` | +0,342 | ↑ | ✓ (fraco) |
| `pop_agevul` | **−0,323** | ↑ | ✗ **invertido** |
| `pop_rent` | **−0,765** | ↑ | ✗ **invertido** |

A PCA não impõe direção aos indicadores individuais: ela extrai o eixo de maior variância e o sinal é ajustado *globalmente*. Como no Brasil a locação e o envelhecimento populacional se concentram em municípios urbanos e mais ricos (Balneário Camboriú, Santos, Florianópolis, Niterói, Vitória — os cinco menores SVI), esses dois indicadores entram no PC1 com carga oposta à sua interpretação conceitual. **Na prática, `SVI_Coast_2022` é um eixo de pobreza/saneamento/ruralidade** — r = 0,944 com pobreza — **não um índice de suscetibilidade a inundação costeira.** Ele mede o gradiente de desenvolvimento Norte–Sul do Brasil, que é real, mas não é específico do perigo em questão.

Consequências mensuráveis:
- ρ(SVI, log₁₀ pop_municipal) = **−0,494**: cidades maiores têm SVI menor por construção.
- ρ(SVI, Exposure_Index) = **−0,588**: exposição e vulnerabilidade se **cancelam parcialmente** dentro do produto geométrico.
- Balneário Camboriú recebe SVI = 0,000 **exatamente** — não porque tenha vulnerabilidade nula, mas porque é o mínimo do Min–Max. É um artefato de escala que o piso 0,01 mitiga mas não corrige.
- Redundância moderada: |r| médio fora da diagonal = 0,433; o bloco de saneamento (água/esgoto/lixo/pavimentação) tem r interno 0,215–0,459, então há **contagem múltipla parcial** de infraestrutura, com quatro dos dez indicadores medindo a mesma dimensão latente.

Não há **nenhum** indicador de suscetibilidade **física** (geomorfologia, tipo de costa, largura de berma, presença de dunas/manguezal, cota topográfica, obras de proteção) — apesar de o README §"Conceptual Framework" definir vulnerabilidade como incluindo "physical susceptibility (geomorphology, land use, natural barriers)" e de a tabela de fontes listar o Macrodiagnóstico do MMA como camada de vulnerabilidade. **Essa camada não foi implementada.** Trata-se de mais uma divergência documentação↔código, e é conceitualmente importante: sem ela, dois trechos com a mesma renda e o mesmo perigo — um sobre falésia rochosa, outro sobre planície arenosa a 1 m acima do nível do mar — recebem risco idêntico.

---

### 4. Coerência do índice integrado de risco

#### 4.1 Comportamento matemático

A média geométrica é a escolha certa para um índice conjuntivo, e está corretamente implementada. Mas o comportamento efetivo depende da **dispersão logarítmica** de cada componente, não do peso nominal 1/3:

| Componente | mín | p10 | mediana | p90 | máx | sd(log) |
|---|---|---|---|---|---|---|
| `Hazard_Index_mun` | 0,010 | 0,131 | 0,382 | 0,791 | 1,000 | **0,657** |
| `Exposure_Index` | 0,010 | 0,399 | 0,712 | 0,889 | 1,000 | 0,547 |
| `SVI/100` | 0,010 | 0,206 | 0,486 | 0,733 | 1,000 | 0,554 |

**Decomposição de variância de log(Risk_raw)** (soma das covariâncias normalizada):

- **Perigo: 51,0 %**
- Exposição: 27,0 %
- Vulnerabilidade: 22,0 %

Ou seja, apesar dos pesos nominais iguais, o perigo domina — o que é apropriado, **desde que o perigo esteja correto**. Como mostrei na §3.1, ao norte de 20°S ele não está.

**Correlações parciais de posto** (controlando as outras duas): ρ(Risk, H | E,V) = **0,845**; ρ(Risk, SVI | H,E) = **0,795**. Ambas altas — o índice não é degenerado, ambos os fatores importam.

#### 4.2 Compensação

O briefing pergunta se vulnerabilidade muito alta pode gerar risco alto onde o perigo é mínimo. **Sim, e é exatamente o que ocorre.** Comparação das tabelas do artigo:

| Top-10 por **perigo** (`Hazard_Index`) | Top-10 por **risco integrado** |
|---|---|
| São Sebastião/SP, Bertioga/SP, Laguna/SC, Saquarema/RJ, Santa Vitória do Palmar/RS, Araruama/RJ, Angra dos Reis/RJ, Maricá/RJ, Duque de Caxias/RJ, Guapimirim/RJ | **Icatu/MA, Turiaçu/MA, Apicum-Açu/MA, Macapá/AP, Axixá/MA**, Magé/RJ, Maricá/RJ, **Chaves/PA**, Saquarema/RJ, **Salvaterra/PA** |

O top-10 de perigo é inteiramente S/SE — fisicamente sólido. O top-10 de risco é 7/10 no Norte. A inversão é conduzida pelo SVI (0,92 em Icatu vs. 0,27 em São Sebastião) atuando sobre um perigo intermediário (0,55 vs. 1,00) que, por sua vez, é dominado por sizígia.

Composição regional do ranking final:

| | N/NE | SE/S | no domínio travado por maré (lat > −20°) |
|---|---|---|---|
| top-10 | 7 | 3 | **7/10** |
| top-20 | 15 | 5 | **15/20** |
| top-50 | 32 | 18 | **34/50** |

#### 4.3 Efeitos de normalização

Duas amplificações sequenciais, ambas documentadas mas não discutidas quanto ao efeito interpretativo:

1. `Hazard_Index_raw` ∈ [0,147; 0,728] → Min–Max multiplica o contraste por **1,72×**.
2. `Risk_Hazard_raw` ∈ [0,092; 0,719] (razão 7,8×) → Min–Max multiplica o contraste por **1,60×**, e produz um mapa que vai de 0,000 a 1,000.

O leitor do mapa final vê um contraste ~60 % maior do que existe no produto conjuntivo. Mais grave: **a âncora inferior da escala é Balneário Camboriú**, cujo `Risk_Hazard = 0,000` só existe porque seu SVI é 0,000 por artefato de Min–Max. Teste de influência que executei:

| Município removido | deslocamento médio de todos os valores publicados | deslocamento máximo |
|---|---|---|
| Balneário Camboriú | **0,0428** | **0,0945** |
| Icatu (âncora superior) | 0,0257 | 0,0420 |
| Santa Rita | 0,0000 | 0,0000 |

Retirar **um** município desloca todo o mapa publicado em 4,3 pontos percentuais em média. O índice é, portanto, **estritamente relativo ao domínio de estudo**.

#### 4.4 Limites de interpretação

`Risk_Hazard` **não** pode ser lido como risco absoluto, nem como probabilidade, nem como risco comparável a outros estudos. É um **índice de priorização relativa dentro do conjunto de 280 municípios costeiros brasileiros com associação de perigo**, condicionado ao conjunto amostral, à escolha de agregação e às âncoras de normalização. O README e os metadados deveriam declarar isso explicitamente; hoje não o fazem.

---

### 5. Avaliação dos hotspots

| Região/município | Risco (posição) | Componente condutora | Concordância com literatura/evidência técnica | Explicação provável | Confiança | Artefato potencial |
|---|---|---|---|---|---|---|
| **Icatu, Axixá, Turiaçu, Apicum-Açu, Cururupu, Guimarães, Alcântara, Cedral /MA** | 1º, 5º, 2º, 3º, 13º, 14º, 18º, 23º | SVI (0,67–0,92) × perigo médio (0,41–0,61) | **Contradição aparente** para perigo composto de tempestade; **concordância parcial** para vulnerabilidade social (MA lidera todos os índices de pobreza costeira do IBGE) | Golfão maranhense, costa de rias macromareal (amplitude até 7,1 m em sizígia equinocial em São Marcos). Eventos compostos travados em sizígia (R = 0,82, p<0,01). thr_hs = 0,94–1,05 m | **Baixa** | **Sim, provável** — maré astronômica classificada como perigo; 9 municípios compartilham o ponto (−2,4;−44,2), gerando pseudo-replicação espacial |
| **Macapá/AP** | 4º | Exposição (0,93) × perigo (0,61) | **Falta de evidência comparável** para inundação composta onda-maré | Ponto de grade (0,8; −50,2) **dentro do estuário amazônico**; `zos` contaminado por descarga fluvial sazonal; thr_hs = 0,51 m | **Muito baixa** | **Sim** — contaminação fluvial + ondas inexistentes |
| **Chaves/PA (Ilha de Marajó)** | 8º | SVI = 100,0 (máximo absoluto) | Erosão costeira em Marajó é documentada, mas por maré/correntes, não por evento composto onda-sobrelevação | thr_hs = **0,24 m**; intensidade normalizada 0,203 (quase o mínimo do domínio, 0,169) | **Muito baixa** | **Sim** — o hotspot é puro SVI; município de 12 568 km² com 19 848 habitantes |
| **Magé, Duque de Caxias, Guapimirim /RJ** | 6º, 12º, — | Perigo (0,906) × exposição | **Contradição** — Baía de Guanabara interior é abrigada de swell | Recebem o ponto oceânico (−23,0; −43,0), **35 km** de distância, na plataforma aberta ao sul do Rio. Ondas de 2,2 m não penetram até o fundo da baía | **Muito baixa** | **Sim, claro** — erro de suporte espacial. *Estes municípios sofrem inundação real, mas fluvial/pluvial, não por onda* |
| **Maricá, Saquarema, Araruama /RJ** | 7º, 9º, 22º | Perigo (0,91–0,92) | **Concordância direta** — Região dos Lagos tem ressacas e erosão documentadas; há avaliação local de vulnerabilidade e risco de inundação costeira publicada para a região | Costa retilínea exposta a swell de S/SW, plataforma estreita, orientação favorável | **Alta** | Não |
| **São Sebastião, Bertioga /SP** | 17º, 24º | Perigo (1,00 e 0,996 — os máximos municipais) | **Concordância direta** — litoral norte de SP com histórico de ressacas e o porto de São Sebastião | Máximo de frequência do SE (0,92 normalizado); fase quase aleatória vs. sizígia | **Alta** | Não. Aparecem baixo no ranking final por SVI baixo (0,26–0,27) |
| **Paraty/RJ** | 21º | Perigo (0,83) | **Concordância parcial** — Paraty tem inundação recorrente do centro histórico, mas o mecanismo dominante é maré de sizígia + chuva, não swell (baía abrigada) | Ponto de grade na Baía da Ilha Grande | Média | Possível erro de suporte |
| **São José do Norte/RS** | 25º | Perigo (0,73) + frequência (0,71) | **Concordância direta** — RS é o setor mais estudado para ressacas e erosão associadas a sobrelevação meteorológica; extremos de sobrelevação no sul do Brasil e erosão costeira estão documentados | Máxima frequência do domínio; fase aleatória vs. sizígia (R = 0,085) | **Alta** | Não |
| **Balneário Camboriú/SC** | **280º (último, 0,000)** | SVI = 0,000 (artefato) + duração = 0,008 | **Contradição frontal** — engorda de praia de R$ 31 milhões em 2021, erosão crônica documentada | Ver §6 | — | **Sim** |
| **Itajaí, Navegantes, Itapema /SC** | 275º, 273º, 267º | duração ≈ 0 | **Contradição frontal** — fechamento do canal de acesso ao Complexo Portuário de Itajaí por 5 dias em maio, > R$ 1 milhão de prejuízo a armadores; São Francisco do Sul, Itapoá e Imbituba também com acessos fechados | Ver §6 | — | **Sim** |

---

### 6. Hotspots esperados que não aparecem

Esta seção é, em minha avaliação, tão diagnóstica quanto a anterior.

#### 6.1 O litoral central de Santa Catarina — o caso mais grave

Balneário Camboriú (280º), Itajaí (275º), Navegantes (273º), Itapema (267º) formam o **fundo absoluto** do ranking. Todos os quatro compartilham ou vizinham o ponto de grade (−27,0; −48,4) / (−27,2; −48,4).

**Mecanismo do erro, rastreado:**

1. O mínimo global de `mean_overlap_duration` (1,26 d) está em (−26,6; −48,6) — nesta mesma região. Portanto `Hazard_Duration` ≈ 0,008–0,016 para esses municípios.
2. Os pontos escolhidos estão **abrigados**: em (−27,0; −48,4) `thr_hs` = 1,82 m, contra 2,33 m a apenas 0,2° a leste (−27,0; −48,2) e 2,58 m em (−28,2; −48,4). O ponto atribuído está na sombra da Ilha de Santa Catarina / enseadas internas, com `compound_count` = 122 contra 245 no ponto exposto próximo.
3. `Hazard_Index_mun` cai para 0,089.
4. Balneário Camboriú recebe SVI = 0,000 por ser o mínimo do Min–Max.
5. Produto geométrico com piso: (0,089 × 0,885 × 0,01)^(1/3) = 0,092 → **exatamente o mínimo da escala publicada**.

Esta é a **cidade brasileira com o caso de engorda de praia mais visível do país** e o porto com registro documentado de interrupção operacional por ressaca. O índice a coloca em zero. Isso, por si só, invalida o mapa como instrumento de priorização de adaptação — e é o teste de sanidade que qualquer revisor de periódico aplicará primeiro.

**Correções concretas:** (i) selecionar o ponto de grade **mais exposto** dentro de um raio, ou usar a média dos pontos da faixa costeira em vez de um único ponto; (ii) remover a duração do índice ou usar percentil em vez de Min–Max; (iii) não permitir que o Min–Max do SVI produza 0 exato — usar posto percentílico ou balizas fixas.

#### 6.2 Campos dos Goytacazes/RJ (Farol de São Tomé) e Linhares/ES (Regência)

266º e 272º. Ambos com erosão costeira severa e bem documentada. Rebaixados pelo termo `Exposure_relative` (0,025 e 0,032), porque a maior parte da população municipal é interiorana. **MAUP em estado puro.** A informação de que existe um núcleo costeiro exposto está no dado (12 174 e 5 386 residentes em 10 km — não é pouco em termos absolutos), mas o termo relativo a destrói.

#### 6.3 Rio Grande / São José do Norte / Tramandaí–Cidreira (RS)

São José do Norte aparece em 25º, o que é razoável. Mas Osório (268º) e Santa Vitória do Palmar (baixo) ficam rebaixados apesar de o RS ter o maior perigo de frequência do domínio. Causa: SVI baixo (0,26 médio no RS) e exposição relativa baixa. **Aqui a compensação atua na direção contrária ao que a evidência física indica.**

#### 6.4 Recife / Olinda / Jaboatão (PE)

Não aparecem no top-50 apesar de erosão costeira crônica, ocupação urbana na linha de praia e recifes degradados. Causa: `Hazard_Frequency` médio no PE = 0,063 — quase nulo. Isto **pode** estar correto (o NE tem baixa frequência de eventos compostos onda-sobrelevação), mas note que a resolução de 1/12° do GLORYS e a batimetria dos recifes não resolvem os processos que efetivamente causam a inundação ali (galgamento sobre linha de recife em preamar de sizígia).

#### 6.5 Fernando de Noronha e Içara/SC

Excluídos do produto (sem `grid_lat`/`grid_lon` na associação externa). São **duas ausências silenciosas** — o mapa publicado tem 280 de 282 municípios e a nota está apenas no JSON de metadados. Deve constar do artigo.

---

### 7. Comparação com a literatura e relatórios técnicos

#### 7.1 Evidência que **apoia** os resultados

| Achado do estudo | Evidência independente | Tipo de concordância |
|---|---|---|
| Máximo de frequência de eventos compostos no RS/SC, decrescendo para norte | Estudos de hindcast hidrodinâmico e de resposta de ondas durante ressacas na costa sul do Brasil, e trabalhos sobre sobrelevações extremas no sul do Brasil e erosão associada | **Direta** |
| Hotspots de perigo em SC central (Tijucas–Florianópolis) e na Região dos Lagos/RJ | [Spotting areas critical to storm waves and surge impacts on coasts with data scarcity: Santa Catarina](https://link.springer.com/article/10.1007/s11069-022-05275-1) identifica hotspots em Tijucas e Florianópolis; [avaliação local de vulnerabilidade e risco de inundação na Região dos Lagos/RJ](https://revistas.ufpr.br/abequa/article/view/14106) | **Direta** — mas note que o **perigo** do OSR11 acerta e o **risco integrado** rebaixa SC |
| Gradiente Norte–Sul de vulnerabilidade social costeira (MA/PA no topo) | [Multiscale Analysis of Coastal Social Vulnerability to Extreme Events in Brazil](https://www.researchgate.net/publication/370893395_Multiscale_Analysis_of_Coastal_Social_Vulnerability_to_Extreme_Events_in_Brazil) (SVI-Coast, 281 municípios, mesma metodologia PCA); [Social Vulnerability and Human Development of Brazilian Coastal Populations](https://frontiersin.org/articles/10.3389/fevo.2021.664272/full) | **Direta** — a camada de vulnerabilidade reproduz o padrão conhecido |
| Alta exposição populacional na faixa de 10 km (30,8 M de 37,4 M) | Consistente com a caracterização de alta densidade populacional na zona costeira do [Macrodiagnóstico da Zona Costeira e Marinha (MMA)](https://www.gov.br/mma/pt-br/noticias/macrodiagnostico-costeiro-vai-orientar-politicas-para-o-litoral-brasileiro) | **Direta** |

#### 7.2 Evidência que **contradiz ou qualifica**

| Resultado do estudo | Evidência contrária | Tipo |
|---|---|---|
| Itajaí/Navegantes entre os 10 municípios de **menor** risco | Fechamento do canal de acesso ao Complexo Portuário de Itajaí por 5 dias por ressaca, com > R$ 1 milhão de prejuízo apenas a armadores; acessos de São Francisco do Sul, Itapoá e Imbituba também fechados no mesmo evento ([Grupo Acquaplan](http://grupoacquaplan.com.br/prejuizos-nos-portos-de-santa-catarina-poderiam-ser-reduzidos-com-um-sistema-de-oceanografia-operacional/)) | **Contradição frontal** |
| Balneário Camboriú com risco = 0,000 | Engorda de praia de R$ 31 milhões (2021); erosão crônica documentada na literatura de erosão do litoral catarinense | **Contradição frontal** |
| MA/PA/AP como principais hotspots de inundação **composta onda–sobrelevação** | Regime macromareal de 4 m (Baía do Guajará/PA) a 7,5 m (São Marcos/MA), com até 7,1 m em sizígia equinocial; clima de ondas offshore da Bacia Pará-Maranhão com Hs modesta. O forçante dominante ali é maré astronômica + descarga fluvial, não sobrelevação meteorológica coincidente com swell extremo ([Assessment of the tidal current energy resource in São Marcos Bay](https://link.springer.com/article/10.1007/s40722-015-0031-5); [Offshore wave climate of the Pará-Maranhão Basin](http://www.scielo.br/j/ocr/a/pnZhMMwk77TxsvM4GpbSS7x/?lang=en)) | **Contradição de mecanismo** — o hotspot pode ser real como risco de inundação costeira, mas não pelo processo que o estudo declara medir |
| Campos dos Goytacazes/Linhares no fundo do ranking | Erosão severa documentada em Farol de São Tomé e Regência | **Contradição** |

#### 7.3 Lacunas de validação

- **Não existe base independente de impactos** para o Norte/Nordeste comparável à base da Defesa Civil de SC (Leal et al. 2024, 91 eventos). Toda a calibração de limiares (Steps 2d/2e) foi feita com **eventos de Santa Catarina** e os limiares q90/q90 foram então **transferidos para toda a costa brasileira**. Isso é uma suposição de transferência de limiar não testada, e é precisamente onde ela falha: q90 em SC seleciona tempestades; q90 no Maranhão seleciona sizígias. O README §2e não discute esse limite de extrapolação.
- Não localizei estudo revisado por pares que aplique um índice composto onda–sobrelevação à costa brasileira inteira com resolução municipal — o trabalho é genuinamente inédito nessa cobertura, o que aumenta o valor do artigo **e** a exigência de robustez.
- O S2ID/Atlas Digital é reconhecido no próprio README como sistematicamente sub-reportado; não pode servir de validação, e corretamente não foi usado como tal.

---

### 8. Possíveis artefatos e limitações (ordenados por consequência)

1. **Travamento de fase com sizígia ao norte de ~20°S** (R = 0,81–0,84, p<0,01 em 100 % dos pontos). Torna o perigo composto não interpretável como perigo de tempestade em >60 % do domínio. *Diagnóstico já executado — reproduzir e publicar.*
2. **Transferência de limiar q90 calibrado em SC para toda a costa.** Produz `thr_hs` de 0,20–0,51 m no Norte. Correção: piso físico absoluto para Hs (p.ex. `max(q90_local, 1,5 m)` ou q99 local), e/ou usar anomalia de nível não maré (`zos` puro) em vez de SSH_total no componente meteorológico.
3. **Regra de associação ponto→município não reproduzível** (15–31 % de acerto contra a regra documentada; 59 % contra "vizinho mais próximo"; mediana 13,1 km, máximo 89,2 km). Um único ponto serve 9 municípios do MA. Reimplementar no repositório; a auditoria do SVI já identifica esta como "a única lacuna de reprodutibilidade em aberto no Step 4".
4. **Erro de suporte espacial em baías abrigadas** (Magé, Duque de Caxias, Guapimirim, Paraty, e — no sentido inverso — Itajaí/Balneário Camboriú). Um ponto oceânico aberto atribuído a município de fundo de baía, ou um ponto abrigado atribuído a município exposto.
5. **Duração como componente de peso 1/3 sobre amplitude de 1,25 dia** limitada pela resolução diária do GLORYS. Contribui 6 % da variância, mas zera o litoral de SC.
6. **`Exposure_relative` e o MAUP.** Satura em 33 % da amostra (>0,99) e penaliza sistematicamente municípios grandes com setor costeiro pequeno mas de alto risco real.
7. **Dois indicadores de SVI com direcionalidade invertida** (`pop_rent` r = −0,765; `pop_agevul` r = −0,323). O SVI é, funcionalmente, um índice de pobreza (r = 0,944), não de suscetibilidade costeira.
8. **Ausência total da camada de vulnerabilidade física**, apesar de documentada no arcabouço conceitual e na tabela de fontes (Macrodiagnóstico MMA).
9. **Min–Max em cadeia (três vezes)** amplifica contraste em 1,72× e depois 1,60×; a escala publicada é ancorada em municípios individuais — remover Balneário Camboriú desloca todo o mapa em 0,043 em média (máx. 0,094).
10. **Contaminação por descarga fluvial** no estuário amazônico (Macapá, Chaves) e possivelmente em outras desembocaduras.
11. **Cancelamento estrutural exposição × vulnerabilidade** (ρ = −0,588): o produto geométrico comprime a variabilidade final em vez de amplificá-la.
12. **Incoerência de fase em `SSH_total`** = zos(00Z) + maré(máx diária): duas quantidades em instantes distintos.
13. **Ausência de definição operacional de hotspot.** As classes são intervalos iguais arbitrários; "hotspot" = "top-10" nas tabelas do artigo, sem critério.
14. **População sazonal invisível** (censo *de jure*). Afeta desproporcionalmente os balneários de SC/SP/RJ — justamente onde o perigo é maior. Já reconhecido na docstring, mas precisa ir para o artigo.
15. **Dois municípios silenciosamente ausentes** do produto (Fernando de Noronha, Içara).
16. **Inconsistências documentação↔código** (§2.2), incluindo três afirmações factualmente falsas em docstrings e nos metadados publicados no site.

---

### 9. Testes de robustez recomendados

#### 9.1 Essenciais antes da submissão

1. **Publicar o diagnóstico de travamento de fase com a sizígia** (teste de Rayleigh contra 14,765 d, por ponto de grade) como figura ou material suplementar. Isso define, de forma objetiva e defensável, o **domínio de validade** do detector. Recomendo restringir a análise composta a latitudes ao sul de ~20°S, ou introduzir um segundo detector baseado em anomalia de nível **não maré** para o setor macromareal.
2. **Impor piso físico ao limiar de Hs** e reexecutar. Nenhum "evento de onda extrema" pode ter Hs de 0,2 m.
3. **Reimplementar e auditar a associação ponto→município** no repositório, com regra explícita (proponho: média dos *k* pontos dentro de 30 km da linha de costa do município, ponderada por distância, ou o ponto mais exposto — mas a regra deve ser declarada e reproduzível). Reportar a distância mediana e máxima no artigo.
4. **Teste de deixar-uma-componente-de-fora** (já executado, reportar): remover perigo ρ = 0,554; remover exposição ρ = 0,803; remover vulnerabilidade ρ = 0,741. Sobreposição de top-20: 10/20, 9/20 e 5/20 respectivamente.
5. **Sensibilidade à agregação do perigo** (já executado, reportar):

   | Variante | ρ com o publicado | top-20 | top-5 |
   |---|---|---|---|
   | implementado | 1,000 | 20/20 | Icatu, Turiaçu, Apicum-Açu, Macapá, Axixá |
   | **só frequência** | **0,384** | 6/20 | **São Sebastião, S. José do Norte, Magé, Guarujá, Guaraqueçaba** |
   | freq + intensidade | 0,816 | 12/20 | Apicum-Açu, Icatu, Turiaçu, Cururupu, Axixá |
   | média geométrica F,D,I | 0,883 | 18/20 | Icatu, Macapá, Magé, Maricá, Saquarema |
   | componentes por posto | 0,967 | 17/20 | Icatu, Macapá, Axixá, Chaves, Vigia |
   | média aritmética H,E,V | 0,934 | 11/20 | Icatu, Maricá, São Sebastião, Saquarema, S. Gonçalo |
   | exposição por posto | 0,773 | 10/20 | Magé, Macapá, Turiaçu, D. de Caxias, Maricá |
   | sem exposição (H×V) | 0,803 | 9/20 | Calçoene, Turiaçu, Icatu, C. Mendes, Bacuri |

   **A conclusão que essa tabela impõe: o top-5 não é robusto.** Não pode ser apresentado como resultado sem essa tabela ao lado.
6. **Corrigir as inconsistências documentação↔código** da §2.2 — em particular o bloco stale do README (fórmula de duas componentes) e as três afirmações falsas em docstrings/metadados. Criar o `SCIENTIFIC_NOTES.md` referenciado.
7. **Verificação de sanidade contra casos conhecidos.** Um mapa de risco costeiro brasileiro que coloca Balneário Camboriú e Itajaí no fundo do ranking será rejeitado. Documentar a causa e corrigi-la, ou justificá-la explicitamente.

#### 9.2 Fortemente recomendados

8. Substituir Min–Max por **posto percentílico** ou balizas fixas nas três componentes, eliminando a dependência do índice a municípios-âncora individuais (deslocamento de 0,043 ao remover um município).
9. **Normalização média vs. máximo vs. ponderada por extensão de costa** na agregação municipal — comparar as três.
10. **Sensibilidade à banda de exposição** (1/2/5/10 km, já calculadas em `municipal_exposure.csv` — usar).
11. **Reexame da direcionalidade do SVI**: reportar as cargas do PC1 por indicador e discutir explicitamente que `pop_rent` e `pop_agevul` entram com sinal contrário à interpretação conceitual. Considerar um índice aditivo com direcionalidade imposta como alternativa, comparando os rankings.
12. **Bootstrap dos postos** (reamostragem de municípios) para produzir intervalos de confiança sobre as posições no ranking — sem isso, "Icatu é o 1º e Turiaçu o 2º" não tem significado estatístico.
13. **Excluir ou marcar** os municípios com `pop_10km` < 1000 (4 casos) e reportar os 2 municípios sem perigo associado.

#### 9.3 Melhorias opcionais

14. Incorporar a camada de vulnerabilidade **física** do Macrodiagnóstico MMA (geomorfologia, barreiras naturais), como o próprio arcabouço conceitual promete.
15. Substituir o município pelo **setor censitário costeiro** como unidade de análise, o que resolveria diretamente o MAUP (Campos dos Goytacazes, Linhares) — é a unidade adotada por avaliações locais de vulnerabilidade costeira no Brasil.
16. Estimar população sazonal (domicílios de uso ocasional do Censo 2022 estão disponíveis) para os balneários.
17. Avaliar a sensibilidade a `mean` vs. `p95` de intensidade e duração.

---

### 10. Conclusão

**Classificação: coerente por partes, mas metodologicamente frágil no produto integrado.**

Mais precisamente, o trabalho divide-se em duas metades com estatutos científicos diferentes:

- **A caracterização de perigo no setor 20–35°S é cientificamente coerente** e constitui, por si só, uma contribuição publicável. A estrutura espacial da frequência, os limiares de Hs, a normalização de intensidade por excesso sobre o limiar local e a fase aleatória em relação à sizígia sustentam a interpretação sinótica. O top-10 municipal por perigo (São Sebastião, Bertioga, Laguna, Saquarema, Santa Vitória do Palmar, Araruama, Angra, Maricá) é fisicamente defensável e concorda com a literatura de ressacas.

- **O índice integrado de risco, no domínio nacional, não é defensável no estado atual.** Sete dos dez principais hotspots estão na região onde eu demonstro que o detector responde à maré astronômica, com limiares de onda "extrema" de 0,2–1,0 m; e o ranking se inverte completamente sob uma escolha alternativa razoável de agregação do perigo (ρ = 0,384). Simultaneamente, o índice coloca no fundo do ranking os dois casos de impacto costeiro mais documentados do país.

**O que **pode** ser afirmado em um artigo científico:**

- A frequência, duração e intensidade de coocorrências temporais Hs–SSH_total ao longo da costa brasileira, 1993–2025, com a estrutura espacial descrita — **desde que** o artigo declare que a coocorrência ao norte de ~20°S é modulada pelo ciclo de sizígia e apresente o diagnóstico de fase.
- Que a costa Sul/Sudeste concentra o perigo composto de origem sinótica, com máximos em RS, litoral norte de SP e Região dos Lagos/RJ.
- Que a população residente a até 10 km da costa nos 282 municípios é de 30,8 milhões (IBGE 2022), com a ressalva explícita de proximidade ≠ inundação modelada.
- Que o SVI_Coast_2022 reproduz o gradiente Norte–Sul de vulnerabilidade social já estabelecido na literatura, e é exatamente reprodutível.
- Que a superposição das três camadas **prioriza** municípios do Golfão Maranhense e do estuário amazônico — **apresentado como resultado condicional**, com a advertência de que o perigo naquele setor tem natureza mareal e que a priorização ali reflete predominantemente vulnerabilidade social.

**O que **não** pode ser afirmado:**

- Que Icatu, Turiaçu, Apicum-Açu, Macapá ou Chaves são hotspots de **inundação costeira composta onda–sobrelevação**. A evidência no próprio repositório contradiz isso.
- Qualquer ordenação específica dentro do top-10 sem intervalos de confiança e sem a tabela de sensibilidade da §9.1.5.
- Que o índice mede risco **absoluto** ou é comparável a outros domínios. É estritamente relativo e depende do conjunto amostral (remover um município desloca todo o mapa).
- Que Balneário Camboriú, Itajaí ou Navegantes têm risco baixo.
- Que a vulnerabilidade **física** foi considerada — ela não foi implementada.

---

### Lista de verificação antes da submissão

- [ ] Publicar o teste de Rayleigh sizígia-quadratura por ponto de grade e definir o domínio de validade do detector
- [ ] Impor piso físico ao `thr_hs` e reexecutar os Steps 3.2 e 4
- [ ] Reimplementar, auditar e documentar a associação ponto de grade → município; reportar distâncias mediana/máxima e o número de pontos únicos (178) para 280 municípios
- [ ] Corrigir a atribuição em baías abrigadas (Guanabara, Ilha Grande) e em costas expostas mal amostradas (Itajaí, Balneário Camboriú)
- [ ] Reavaliar a componente de duração (remover, ou substituir Min–Max por percentil)
- [ ] Tabela de sensibilidade da agregação do perigo e de deixar-uma-componente-de-fora no material suplementar
- [ ] Bootstrap dos postos com intervalos de confiança sobre o ranking
- [ ] Substituir Min–Max por posto/balizas fixas, ou reportar a análise de influência (0,043 médio ao remover um município)
- [ ] Reportar as cargas do PC1 e discutir a direcionalidade invertida de `pop_rent` e `pop_agevul`
- [ ] Declarar explicitamente que a vulnerabilidade física não foi incorporada, ou incorporá-la
- [ ] Declarar que exposição = proximidade, não inundação modelada; e que a população é *de jure* (sem sazonais)
- [ ] Reportar os 2 municípios sem perigo (Fernando de Noronha, Içara) e os 4 com `pop_10km` < 1000
- [ ] Definir operacionalmente "hotspot" (limiar percentílico ou quebra natural), não "top-10"
- [ ] Declarar que `Risk_Hazard` é índice de **priorização relativa**, não risco absoluto
- [ ] Corrigir as sete inconsistências documentação↔código da §2.2, criar `SCIENTIFIC_NOTES.md`, remover o bloco stale do README com a fórmula de duas componentes
- [ ] Executar o teste de sanidade contra casos conhecidos (Itajaí, Balneário Camboriú, Farol de São Tomé, Regência) e documentar o resultado

**Sources:**
- [Spotting areas critical to storm waves and surge impacts on coasts with data scarcity: a case study in Santa Catarina, Brazil — Natural Hazards](https://link.springer.com/article/10.1007/s11069-022-05275-1)
- [Hydrodynamic and Waves Response during Storm Surges on the Southern Brazilian Coast: A Hindcast Study — Water (MDPI)](https://www.mdpi.com/2073-4441/12/12/3538)
- [Extreme storm surges in the south of Brazil: Atmospheric conditions and shore erosion](https://www.researchgate.net/publication/250052519_Extreme_storm_surges_in_the_south_of_Brazil_Atmospheric_conditions_and_shore_erosion)
- [Multiscale Analysis of Coastal Social Vulnerability to Extreme Events in Brazil](https://www.researchgate.net/publication/370893395_Multiscale_Analysis_of_Coastal_Social_Vulnerability_to_Extreme_Events_in_Brazil)
- [Social Vulnerability and Human Development of Brazilian Coastal Populations — Frontiers in Ecology and Evolution](https://frontiersin.org/articles/10.3389/fevo.2021.664272/full)
- [Avaliação local da vulnerabilidade e riscos de inundação na zona costeira da Região dos Lagos, RJ](https://revistas.ufpr.br/abequa/article/view/14106)
- [Macrodiagnóstico da Zona Costeira e Marinha — MMA](https://www.gov.br/mma/pt-br/noticias/macrodiagnostico-costeiro-vai-orientar-politicas-para-o-litoral-brasileiro)
- [Vulnerabilidade das praias de Santa Catarina a eventos de erosão e inundação costeira](https://revistas.ufpr.br/abequa/article/view/47281)
- [Prejuízos nos portos de Santa Catarina — Grupo Acquaplan](http://grupoacquaplan.com.br/prejuizos-nos-portos-de-santa-catarina-poderiam-ser-reduzidos-com-um-sistema-de-oceanografia-operacional/)
- [Assessment of the tidal current energy resource in São Marcos Bay, Brazil](https://link.springer.com/article/10.1007/s40722-015-0031-5)
- [Offshore wave climate of the Pará-Maranhão Basin, Amazonian continental shelf](http://www.scielo.br/j/ocr/a/pnZhMMwk77TxsvM4GpbSS7x/?lang=en)
