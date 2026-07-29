# AUD-15 — Cobertura amostral: municípios ausentes do produto e municípios com dado de exposição degenerado

| Campo | Valor |
|-------|-------|
| **ID** | AUD-15 |
| **Tipo** | `qualidade-dados` |
| **Componente** | integração |
| **Etapa do fluxo** | Step 4.1 / 4.2 / 4.4 |
| **Afeta** | dados, interpretação, saídas, documentação |
| **Prioridade** | P2 |
| **Bloqueia publicação?** | Não — mas as ausências precisam ser reportadas, hoje só constam de um JSON de metadados |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-04, AUD-08, AUD-11, AUD-12 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2 item 3, §6.5, §8 item 15, §9.2 item 13 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

Três defeitos de cobertura, agrupados porque compartilham a mesma resolução —
uma definição explícita e versionada do conjunto amostral:

1. **Dois municípios são silenciosamente excluídos** do produto final por não
   terem associação de perigo: Fernando de Noronha/PE e Içara/SC. O mapa publicado
   tem 280 de 282 municípios, e a informação consta apenas de um campo de JSON.
2. **Quatro municípios têm `pop_10km` < 1000**, dois deles absurdamente baixos —
   Santa Rita/MA com **4** habitantes e Calçoene/AP com 101 — recebendo o piso de
   exposição de 0,01 e caindo ao fundo do ranking.
3. **Não existe critério documentado** de pertencimento ao conjunto costeiro. A
   lista vem do shapefile externo, herdada de Lima et al. (2024) mais Balneário
   Rincão.

## 2. Por que importa cientificamente

- **Fernando de Noronha** é o único município oceânico insular do conjunto e um
  caso de interesse específico; sua exclusão silenciosa de um mapa nacional será
  notada.
- **Içara/SC** está no setor de maior perigo do domínio; sua ausência não é
  neutra.
- **Santa Rita/MA**, com 4 residentes a até 10 km da costa e ponto de perigo a
  **77 km**, provavelmente não é um município costeiro em nenhum sentido útil.
  Sua presença no conjunto contamina as estatísticas descritivas e as
  normalizações Min–Max.
- Um conjunto amostral sem critério explícito é um problema de reprodutibilidade:
  outro pesquisador não consegue reconstruir a lista.

## 3. Evidência original

### 3.1 Municípios sem perigo

De `site/public/data/risk_index_metadata.json` → `hazard_transfer`:

```json
"municipality_feature_count": 282,
"matched_hazard_count": 280,
"missing_hazard_count": 2,
"missing_municipalities": [
  {"municipality_name": "Fernando de Noronha", "state": "PE",
   "grid_lat": null, "grid_lon": null},
  {"municipality_name": "Içara", "state": "SC",
   "grid_lat": null, "grid_lon": null}
]
```

Ambos têm SVI e exposição (Fernando de Noronha: SVI = 39,22, `pop_10km` = 3 161;
Içara: SVI = 20,55, `pop_10km` = 9 870), mas nenhum ponto de grade associado —
falha do fluxo externo de associação (AUD-04).

### 3.2 Municípios com exposição degenerada

| Município | `pop_municipality` | `pop_10km` | `Exposure_Index` | posição no risco |
|---|---|---|---|---|
| **Santa Rita/MA** | 36 789 | **4** | 0,010 (piso) | 278º de 280 |
| **Calçoene/AP** | 10 554 | 101 | 0,010 (piso) | 277º |
| Oiapoque/AP | 27 264 | 518 | 0,058 | 270º |

Total: **4 municípios** com `pop_10km` < 1000.

Santa Rita/MA agrava-se por receber o perigo de um ponto a **77,0 km**
(o segundo maior desvio do conjunto — AUD-04 §3).

### 3.3 Contexto do conjunto amostral

De `src/04_risk_integration/external_svi/README.md`:

- A lista de municípios costeiros é extraída de um PDF (`municipios.pdf`) pelo
  script externo;
- **Balneário Rincão (4220000)** é adicionado separadamente — criado em 2013 e
  ausente dos agregados padrão do SIDRA. É por isso que o arquivo entregue tem
  **282** municípios onde Lima et al. (2024) reportam 281.

### 3.4 Efeito nas normalizações

Da análise de influência (AUD-11 §3.2): remover Santa Rita não desloca nenhum
valor (deslocamento 0,0000) porque não é âncora. Portanto, incluí-la ou não **não
afeta a escala** — mas afeta as estatísticas descritivas reportadas e a contagem
de municípios no manuscrito.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/site/export_risk_index_data.py` | L596–602 | Constrói `missing_municipalities` nos metadados |
| `src/site/export_risk_index_data.py` | L671–682 | Levanta erro se algum município não tiver contagem de exposição — mas **não** levanta se faltar perigo |
| `src/site/export_risk_index_data.py` | L640 `_where_clause()` | Filtro de leitura do shapefile |
| `src/04_risk_integration/municipal_exposure.py` | `load_municipalities()` L86–111 | Filtra por `SVI_Coast_` não nulo — a definição operacional efetiva do conjunto |
| `src/04_risk_integration/municipal_exposure.py` | `MUNICIPALITY_FILTER_FIELD` L75 | `"SVI_Coast_"` |
| `src/04_risk_integration/external_svi/build_svi_coast_2022.py` | passos 1, 2, 4 | Extração da lista do PDF e adição de Balneário Rincão |

### Dados e saídas

- `outputs/risk_index/risk_index.shp` — fonte da lista.
- `outputs/exposure/municipal_exposure.csv` — 282 linhas.
- `site/public/data/risk_index_municipalities.geojson` — 282 feições, 280 com
  `Risk_Hazard`.
- `site/public/data/risk_index_metadata.json` → `hazard_transfer.missing_municipalities`.

### Figuras e tabelas afetadas

Todos os mapas municipais exibem dois municípios sem valor, sem legenda que
explique a ausência.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Conjunto herdado de fonte externa; ausências registradas apenas em metadados; municípios com exposição degenerada recebem piso e permanecem no conjunto |
| **Pretendido** | Critério de pertencimento explícito e versionado; ausências reportadas no produto e no manuscrito; municípios com dado insuficiente marcados como tal, não recebendo um valor plausível |

## 6. Divergência documentação ↔ implementação ↔ saídas

- `README.md` §Step 4 declara: *"The delivered municipal file carries 282
  municipalities with SVI; 280 of them have a hazard association and therefore a
  risk value."* **Isto está correto e documentado** — não é uma divergência.
- `README.md` L406 diz "281 coastal municipalities" na seção "Current
  Implementation Status", conflitando com 282 no restante. Inconsistência #7 de
  AUD-17.
- O que falta é o **nome** dos dois municípios ausentes fora do JSON de
  metadados, e a decisão sobre os quatro com exposição degenerada.

## 7. Explicações alternativas plausíveis

1. **Fernando de Noronha pode legitimamente não ter ponto de grade costeiro
   continental.** É um arquipélago a 350 km da costa; os 808 pontos foram
   selecionados ao longo da costa continental. Excluí-lo é defensável — só
   precisa ser declarado, não silencioso.
2. **Içara pode ser uma falha corrigível.** Está no litoral continental de SC,
   entre municípios que têm associação. É provável que seja um defeito do fluxo
   externo (AUD-04) e não uma ausência conceitual.
3. **Santa Rita/MA pode estar corretamente no conjunto** se a lista de Lima et al.
   (2024) usar um critério administrativo (municípios da zona costeira legal) e
   não geográfico. Nesse caso o conjunto está certo e o problema é que a exposição
   por proximidade não é a métrica adequada para municípios da zona costeira legal
   sem frente de mar.
4. **O piso de 0,01 pode ser preferível a excluir.** Excluir municípios muda a
   contagem reportada e o conjunto de normalização; o piso mantém a completude ao
   custo de um valor pouco significativo.

## 8. Diagnósticos propostos

1. **Documentar o critério de pertencimento**: obter de Lima et al. (2024) ou do
   PDF de origem a definição usada (frente de mar? zona costeira legal? distância
   máxima?), e registrá-la no repositório.
2. **Diagnosticar Içara**: verificar se existe ponto de grade a distância razoável
   e por que a associação externa falhou. Provável correção via AUD-04.
3. **Decidir sobre Fernando de Noronha**: incluir com ponto oceânico próprio, ou
   excluir declaradamente do escopo continental.
4. **Classificar os municípios de frente de mar**: para cada um dos 282, calcular
   o comprimento de linha de costa dentro do polígono municipal. Municípios com
   comprimento zero não têm frente de mar e devem ser tratados à parte.
   *Saída esperada:* separar Santa Rita e similares por critério objetivo, não por
   `pop_10km` baixo.
5. **Testar a sensibilidade a exclusões**: recalcular todo o índice sem os
   municípios sem frente de mar e sem os `pop_10km` < 1000; medir ρ, mudanças de
   posição e efeito nas normalizações.

## 9. Critérios objetivos de resolução

- [ ] O critério de pertencimento ao conjunto costeiro está documentado no
      repositório, com a fonte, e é reproduzível.
- [ ] Existe classificação versionada de quais municípios têm frente de mar.
- [ ] A situação de Içara está resolvida: associado, ou declaradamente excluído
      com justificativa.
- [ ] A situação de Fernando de Noronha está decidida e declarada.
- [ ] Os municípios com `pop_10km` < 1000 estão marcados no produto — não apenas
      recebendo o piso silenciosamente — e o manuscrito os identifica.
- [ ] O manuscrito reporta **por nome** os municípios sem valor de risco e explica
      por quê.
- [ ] A discrepância 281/282 no README está corrigida (AUD-17 #7).
- [ ] O teste de sensibilidade a exclusões foi executado e reportado.

## 10. Riscos de alteração prematura

- **Excluir municípios muda o conjunto de normalização** e, portanto, todos os
  valores publicados (AUD-11). Deve ser decidido junto com a escolha de
  normalização.
- **Excluir com base em `pop_10km` baixo** é um critério circular — usa a variável
  que se quer medir. O critério deve ser geométrico (frente de mar).
- **Adicionar Fernando de Noronha com um ponto oceânico próprio** introduz um
  ponto fora dos 808 e quebra a coerência do domínio de normalização do perigo.

## 11. Condições sob as quais o resultado atual pode ser mantido

Aceitável manter os 282 com 280 valorados, se:

1. Os dois ausentes forem nomeados e explicados no manuscrito e na legenda dos
   mapas;
2. Os quatro com `pop_10km` < 1000 forem identificados, com nota de que seu valor
   de exposição está no piso;
3. O critério de pertencimento for documentado, ainda que herdado de Lima et al.
   (2024);
4. O teste de sensibilidade a exclusões mostrar ρ > 0,99.

## 12. Produtos a jusante que exigiriam regeneração

Se o conjunto mudar:

```bash
python -m src.risk_integration.municipal_exposure
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_top10_municipality_tables
```

Se apenas houver documentação: nenhum produto muda; apenas README, legendas e
manuscrito.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29.*
