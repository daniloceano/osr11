# AUD-04 — Transferência do perigo da grade oceânica para o município: regra não reproduzível e suporte espacial inadequado

| Campo | Valor |
|-------|-------|
| **ID** | AUD-04 |
| **Tipo** | `erro-implementacao` (confirmado: a regra documentada não se reproduz) |
| **Componente** | perigo → integração |
| **Etapa do fluxo** | Step 4.1 |
| **Afeta** | código, dados, interpretação, saídas, documentação |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — é a única lacuna de reprodutibilidade declarada em aberto no Step 4, e determina o valor de perigo de todos os 280 municípios |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-13 |
| **Relacionado a** | AUD-06, AUD-12, AUD-15, AUD-17 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 5), §2.1, §5, §6.1, §8 itens 3 e 4, §9.1 item 3 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

Cada município recebe o valor do `Hazard_Index` de **um único** ponto de grade
oceânico, pré-associado por um fluxo de trabalho **externo ao repositório** e não
auditado. Duas falhas:

1. **A regra documentada não se reproduz.** O `README.md` §4.1 afirma que o ponto
   escolhido é "the point with the highest compound-event count within the
   association". Apenas 15–31 % das atribuições correspondem a isso.
2. **Um único ponto é um suporte espacial inadequado.** Distâncias de até 89 km,
   pontos oceânicos abertos atribuídos a municípios de fundo de baía, e pontos
   abrigados atribuídos a municípios de costa exposta.

## 2. Por que importa cientificamente

O `Hazard_Index` domina 51 % da variância de log(`Risk_Hazard_raw`). Se a
atribuição do ponto está errada, o mapa de risco está errado, ponto a ponto,
independentemente de todo o resto estar correto.

Os dois casos mais graves apontam em direções opostas, o que descarta a hipótese
de um viés sistemático simples:

- **Magé, Duque de Caxias, Guapimirim (RJ)** — municípios no fundo da Baía de
  Guanabara — recebem o ponto de plataforma aberta (−23,0; −43,0), a 35 km, com
  `Hazard_Index_mun` = 0,906. Swell de 2,2 m não penetra até o fundo da baía.
  Estes municípios sofrem inundação real, mas fluvial e pluvial.
- **Itajaí, Navegantes, Balneário Camboriú, Itapema (SC)** — costa exposta —
  recebem pontos abrigados com `Hazard_Index_mun` = 0,089, colocando-os no fundo
  do ranking nacional (ver AUD-05).

Além disso, a atribuição de um mesmo ponto a vários municípios cria
**pseudo-replicação espacial**: blocos de municípios com perigo idêntico que
aparecem no mapa como agrupamentos coerentes de hotspots sem que haja informação
independente por trás.

## 3. Evidência original

Diagnósticos executados sobre `site/public/data/risk_index_municipalities.geojson`
e `outputs/storm_catalog/compound/compound_metrics.csv`, com geometria em
EPSG:5880:

**Reprodutibilidade da regra documentada**

| Raio de vizinhança | atribuído = ponto de maior `compound_count_total` | atribuído = ponto mais próximo |
|---|---|---|
| 30 km | **31 %** | 59 % |
| 50 km | **15 %** | 59 % |

**Distância município (polígono) → ponto atribuído**

| estatística | km |
|---|---|
| mínimo | 0,0 |
| q25 | 7,5 |
| mediana | **13,1** |
| q75 | 19,1 |
| máximo | **89,2** |

Casos extremos: Paracuru/CE 89,2 km; Santa Rita/MA 77,0 km;
São João Batista/MA 74,4 km; São Gonçalo do Amarante/CE 73,3 km;
Vigia/PA 61,1 km; Bacabeira/MA 51,7 km; Colares/PA 49,7 km;
Duque de Caxias/RJ 35,2 km.

**Compartilhamento de pontos**

- **178 pontos únicos** servem **280 municípios**.
- (−2,4; −44,2) serve **9** municípios do MA; (−23,0; −43,0) serve 6 do RJ;
  (−9,6; −35,6) serve 5 de AL; (−2,4; −44,0) serve 5 do MA.

**Efeito de usar o vizinho mais próximo em vez do atribuído**

- Coincidência de ponto: 166 de 280 (59 %).
- Spearman(`HI_atribuído`, `HI_vizinho_mais_próximo`) = 0,921.
- Média(`HI_atribuído` − `HI_vizinho`) = **+0,0030** — sem viés agregado
  detectável, o que **não** exclui erros individuais grandes:

| Município | HI atribuído | HI vizinho | Δ |
|---|---|---|---|
| Caraguatatuba/SP | 0,275 | 0,829 | **−0,554** |
| Mostardas/RS | 0,564 | 0,293 | +0,271 |
| Florianópolis/SC | 0,421 | 0,158 | +0,263 |
| Amapá/AP | 0,475 | 0,730 | −0,255 |
| São Bento do Norte/RN | 0,029 | 0,281 | −0,252 |
| Chaves/PA | 0,325 | 0,092 | +0,233 |
| Ilhabela/SP | 0,717 | 0,490 | +0,227 |
| Itaguaí/RJ | 0,491 | 0,716 | −0,225 |

**Evidência de que os pontos de SC são abrigados** (de `compound_metrics.csv`):

| ponto | thr_hs (m) | compound_count | mean_overlap_duration |
|---|---|---|---|
| (−27,0; −48,4) *atribuído* | 1,82 | 122 | 1,27 |
| (−27,0; −48,2) | 2,33 | 172 | 1,43 |
| (−28,2; −48,4) | 2,58 | 245 | 1,58 |

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/site/export_risk_index_data.py` | `_derive_current_scope()` L496–604 | Faz a transferência |
| `src/site/export_risk_index_data.py` | L519–542 | Lookup exato por `grid_lat`/`grid_lon` arredondados a 6 casas |
| `src/site/export_risk_index_data.py` | `SUPPORT_FIELD_CANDIDATES` L109–110 | Lê `grid_lat`/`grid_lon` do shapefile entregue |
| `src/04_risk_integration/coastal_projection.py` | `attach_nearest_municipality()` L268 | **Já existe** uma implementação de associação por `sjoin_nearest` em EPSG:5880 — usada apenas para rotular segmentos costeiros, sem participar do índice |
| `src/04_risk_integration/coastal_projection.py` | `project_values_to_coastline()` L142 | Projeção grade → costa; base natural para uma associação reimplementada |

**O código que produziu `grid_lat`/`grid_lon` não existe no repositório.**
`src/04_risk_integration/external_svi/README.md` declara explicitamente:
*"The association between the 808 ocean grid points and the municipalities [...]
was produced elsewhere and remains unaudited. That is the one reproducibility gap
still open in Step 4."*

### Configuração

- `src/04_risk_integration/coastal_projection.py` L40 `COASTAL_MAP_EXTENT`,
  parâmetros de buffer (30 km) e comprimento máximo de segmento (5 km).

### Dados e saídas

- `outputs/risk_index/risk_index.shp` — **fonte externa** de `grid_lat`,
  `grid_lon`, geometria, `SVI_Coast_2022`. Não versionado (`.gitignore`).
- `site/public/data/risk_index_municipalities.geojson` — produto.
- `site/public/data/risk_index_metadata.json` → `hazard_transfer.method`.

### Figuras e tabelas afetadas

- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`
- `outputs/article_figures/supplementary_integrated_risk_zooms.png`
- `outputs/article_figures/tables/top10_municipalities_by_hazard.*`
- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.*`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Lookup exato de um par `(grid_lat, grid_lon)` fornecido externamente; regra de escolha desconhecida e não reproduzível |
| **Documentado** | "the point with the highest compound-event count within the association" (`README.md` §4.1) |
| **Pretendido/conceitual** | Um valor de perigo representativo da **frente costeira exposta** do município |

## 6. Divergência documentação ↔ implementação ↔ saídas

Divergência tripla, e é a mais séria do repositório:

- **Documentação** afirma uma regra determinística.
- **Implementação** não contém regra alguma — apenas consome o resultado.
- **Saídas** são consistentes com a entrada externa, que não pode ser verificada.

Componente da inconsistência #5 catalogada em
`baseline/2026-07-29_initial_review.md` §2.2, também rastreada em AUD-17.

## 7. Explicações alternativas plausíveis

1. **A regra documentada pode estar correta mas ter sido aplicada a um conjunto
   candidato diferente** — por exemplo, apenas pontos dentro de um buffer
   específico, ou apenas pontos da faixa costeira de um recorte anterior. O teste
   de 30/50 km pode não refletir o conjunto usado.
2. **A associação pode ter sido feita sobre uma versão anterior de
   `compound_metrics.csv`**, quando as contagens eram outras. Nesse caso a regra
   era válida quando aplicada e ficou obsoleta — o que reforça a necessidade de
   reimplementar dentro do repositório.
3. **O critério pode ter sido "ponto mais próximo do centroide"** em vez do
   polígono. A coincidência de 59 % com o vizinho mais próximo do polígono sugere
   que a regra é predominantemente de proximidade com alguma variação.
4. **Os casos de baía podem ser deliberados.** Se o objetivo for caracterizar o
   forçante oceânico regional a que o município está sujeito, atribuir o ponto de
   plataforma aberta a um município de fundo de baía é defensável — desde que
   declarado, e desde que a interpretação do índice mude de acordo.

## 8. Diagnósticos propostos

1. **Reimplementar a associação** em `src/04_risk_integration/`, com regra
   explícita e parametrizada. Candidatas a comparar:
   - (a) ponto mais próximo do polígono municipal;
   - (b) ponto de maior `compound_count_total` dentro de um raio R;
   - (c) **média dos k pontos** dentro de R, ponderada por distância inversa;
   - (d) média dos pontos associados aos **segmentos costeiros** do município,
        reutilizando `coastal_projection.py::project_values_to_coastline()` e
        `attach_nearest_municipality()` — a rota mais coerente com o resto do
        repositório, porque a geometria já é a mesma das figuras e do site;
   - (e) ponto **mais exposto** (maior `thr_hs_abs`) dentro de R.
2. **Comparar as cinco variantes** entre si e com a associação entregue:
   ρ de Spearman do `Hazard_Index` municipal, sobreposição de top-20, e mudança
   de posição de cada município no ranking final de risco.
3. **Classificar cada município** quanto à exposição da sua frente costeira
   (oceano aberto / baía semiabrigada / estuário / fundo de baía), por inspeção
   geométrica automatizável (razão entre comprimento da linha de costa e
   distância ao oceano aberto). Verificar se o ponto atribuído é coerente com a
   classe.
4. **Auditar a distância**: publicar o histograma e a lista de municípios com
   distância acima de 30 km.
5. **Quantificar a pseudo-replicação**: número efetivo de graus de liberdade
   espaciais (178 pontos para 280 municípios) e efeito sobre qualquer estatística
   de agrupamento regional.
6. **Solicitar o código original** da associação, conforme já recomendado em
   `src/04_risk_integration/external_svi/README.md`.

## 9. Critérios objetivos de resolução

- [ ] Existe, dentro do repositório, um módulo versionado que produz
      `grid_lat`/`grid_lon` (ou diretamente o `Hazard_Index` municipal) a partir
      de entradas versionadas, com regra declarada e parâmetros explícitos.
- [ ] A regra implementada é reproduzível: executar o módulo duas vezes produz
      resultado idêntico, e o resultado bate com a regra descrita no `README.md`
      em ≥ 99 % dos municípios.
- [ ] As cinco variantes de associação foram comparadas quantitativamente, e a
      escolhida está justificada por um critério físico declarado — não pela
      concordância com o resultado anterior.
- [ ] Nenhum município recebe perigo de um ponto a mais de 30 km, **ou** cada
      exceção está listada e justificada individualmente.
- [ ] Os casos de baía (Guanabara: Magé, Duque de Caxias, Guapimirim, São Gonçalo;
      Ilha Grande: Paraty, Angra dos Reis) e os de costa exposta subestimada
      (Itajaí, Navegantes, Balneário Camboriú, Itapema, Caraguatatuba) recebem
      valores coerentes com a exposição real da sua frente costeira, ou a
      discrepância está explicada.
- [ ] O número de pontos únicos e a distribuição de municípios por ponto estão
      reportados no manuscrito.
- [ ] Produtos a jusante regenerados (§12).

## 10. Riscos de alteração prematura

- **Mudar a associação muda todos os 280 valores de perigo simultaneamente**, e
  portanto todo o mapa de risco e todas as tabelas do artigo. Deve ser feito uma
  única vez, com a regra decidida.
- **Adotar a média de k pontos suaviza o campo** e reduz o contraste do
  `Hazard_Index` municipal, o que interage com AUD-11 (a renormalização
  `Hazard_Index_mun` reamplificaria artificialmente esse contraste reduzido).
- **Adotar o ponto mais exposto** introduz viés otimista de perigo — resolve o
  caso SC mas piora os casos de baía.
- Reimplementar a associação **não** resolve AUD-01 nem AUD-02: um ponto bem
  escolhido com limiar sem sentido continua sem sentido.

## 11. Condições sob as quais o resultado atual pode ser mantido

Difícil de sustentar. A associação atual só poderia ser mantida se:

1. O código original fosse obtido, versionado e auditado, demonstrando que a
   regra é determinística e cientificamente justificada;
2. Os casos de baía e de costa exposta subestimada fossem explicados por essa
   regra;
3. O `README.md` fosse corrigido para descrever a regra efetiva.

Enquanto o código externo não existir no repositório, **a reprodutibilidade do
Step 4 não pode ser declarada**, o que é um problema de conformidade com
políticas de disponibilidade de dados e código da maioria dos periódicos.

## 12. Produtos a jusante que exigiriam regeneração

```bash
python -m src.site.export_risk_index_data
python -m src.site.export_coastal_hazard_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_top10_municipality_tables
```

Os catálogos e as métricas de grade **não** precisam ser reprocessados: a
associação é posterior ao Step 3.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29, cujos números estão na §3.*
