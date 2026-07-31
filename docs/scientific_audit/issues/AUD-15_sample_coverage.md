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
| **Status** | `em-investigacao` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-04, AUD-08, AUD-11, AUD-12 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2 item 3, §6.5, §8 item 15, §9.2 item 13 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 |

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
      repositório, com a fonte, e é **reproduzível**. *Parcial: a fonte está
      documentada (lista de Lima et al. 2024 extraída de `municipios.pdf` pelo
      script externo, mais Balneário Rincão adicionado à mão), e isso consta do
      parágrafo de limitação. Mas o critério **em si** — frente de mar? zona
      costeira legal? distância máxima? — continua desconhecido, e a lista não é
      reconstruível a partir do repositório. Critério **não verificado**.*
- [ ] Existe classificação versionada de quais municípios têm frente de mar.
      **Não feita.** Exigiria calcular o comprimento de linha de costa dentro de
      cada polígono municipal. Critério **não verificado**.
- [ ] A situação de Içara está resolvida: associado, ou declaradamente excluído
      com justificativa. *Declarada e nomeada no manuscrito, com a avaliação de
      que é uma falha recuperável da associação e não uma ausência conceitual —
      mas **não resolvida**. Depende de AUD-04. Critério **não verificado**.*
- [ ] A situação de Fernando de Noronha está decidida e declarada.
      *Declarada por nome no parágrafo de limitação, mas **não decidida**.
      **Correção de 2026-07-31:** a primeira versão desta entrada dizia que o
      município estava fora do escopo continental porque nenhum ponto lhe seria
      apropriado. **Isso é falso.** Existem **19 pontos de grade sobre o
      arquipélago**, com limiares de onda oceânicos normais (Hₛ ≈ 2,0 m) e
      HAT ≈ 1,5 m, o mais próximo a **1,5 km** do polígono municipal; cada um
      carrega 9 a 13 candidatos, **todos rejeitados pelo portão HAT**. A
      ausência é lacuna de associação, do mesmo tipo que a de Içara — não
      questão de escopo. Associá-lo lhe daria `Hazard_Index_mun` = 0, somando-o
      aos 83 municípios sem perigo aceito. Critério **não verificado**.*
- [ ] Os municípios com `pop_10km` < 1000 estão marcados **no produto** — não
      apenas recebendo o piso silenciosamente — e o manuscrito os identifica.
      *Metade: os quatro estão identificados **por nome e valor** no README §4.2
      e no parágrafo de limitação (Santa Rita/MA 4, Calçoene/AP 101,
      Oiapoque/AP 518, Terra de Areia/RS 765). Nenhuma marcação foi acrescentada
      ao GeoJSON nem às legendas dos mapas. Critério **não verificado**.*
- [x] O manuscrito reporta **por nome** os municípios sem valor de risco e explica
      por quê. *Fernando de Noronha/PE e Içara/SC, cada um com sua causa, no
      parágrafo de limitação.*
- [x] A discrepância 281/282 no README está corrigida (AUD-17 #7).
      *Corrigida em 2026-07-29 no README; os resíduos remanescentes em
      `site/content/results.ts` e `site/content/project.ts` foram corrigidos em
      2026-07-31.*
- [x] O teste de sensibilidade a exclusões foi executado e reportado.
      *Remover os quatro municípios de exposição degenerada deixa a ordenação
      publicada intacta: ρ = 1,000, deslocamento máximo de posto 0. Eles não
      ancoram nenhuma normalização.*
- [ ] **Critério novo (2026-07-31, de AUD-07).** A fronteira zero/não-zero é
      **amostralmente instável** e isso precisa estar declarado junto com a
      categoria de risco zero. O bootstrap sobre os 33 anos de registro
      (`outputs/audit/AUD-07_aggregation_sensitivity/`) mostra que, além dos 84
      sempre nulos, **94 municípios caem a risco exatamente zero em alguns
      sorteios** — Guimarães/MA, Alcântara/MA, Raposa/MA e Icatu/MA em **34 %**
      deles, apesar de ocuparem as posições 21, 22, 28 e 32. Apenas **102 dos
      280** são robustamente não nulos. A causa é que 94 dos 196 municípios com
      risco positivo têm menos de dez eventos aceitos e 90 têm menos de cinco.
      Rotular "risco zero" como categoria própria sem dizer que a fronteira se
      move é meia declaração. Critério **não verificado**.
- [ ] **Critério novo (2026-07-31).** Os **83 municípios cujo ponto de perigo não
      aceitou nenhum evento composto** — `Hazard_Index_mun` exatamente 0,
      posições 191 a 280 — estão declarados no produto, no site e no manuscrito,
      com a advertência de que sua ordenação interna não carrega informação de
      perigo. *Declarados no README (§Current Implementation Status, limitações
      do manuscrito) e na página de metodologia do índice. **Não** marcados no
      GeoJSON nem nas legendas dos mapas. Critério **não verificado**.*

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
| 2026-07-31 | *(não commitado)* | `main` | `src/exploratory/audit_AUD_15_sample_coverage.py` (novo), `README.md` (§4.2, §Current Implementation Status, limitações do manuscrito), `site/app/methodology/hazard-index/page.tsx` | Recontagem + declaração. **Nenhum município excluído; nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

### 2026-07-31 — Recontagem sobre os produtos atuais; uma categoria nova e maior

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Os números de cobertura de 2026-07-29 continuam válidos depois da regeneração do Step 3? Quais municípios estão ausentes, sem SVI, ou com exposição degenerada, e por quê — nominalmente? |
| **Dados e métodos** | `site/public/data/risk_index_municipalities.geojson` (282 feições), `site/public/data/risk_index_metadata.json`, `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv` e `data/external/municipal_grid_association/`. Cada município foi cruzado com a **atividade do ponto de grade a que está associado**, uma verificação que o método anterior não permitia fazer: com o portão HAT, uma associação válida pode apontar para um ponto que não aceitou evento algum |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_15_sample_coverage` |
| **Novas saídas geradas** | `outputs/audit/AUD-15_sample_coverage/{coverage_by_municipality.csv, absent_and_degenerate_cases.csv, coverage_summary.json}` |
| **Achados** | (a) **Os números antigos continuam válidos onde eram sobre associação**: 282 municípios entregues, 282 com SVI, 280 com associação, perigo e risco, 2 ausentes. Os dois ausentes são os mesmos — **Fernando de Noronha/PE** (SVI 39,2; `pop_10km` 3 161) e **Içara/SC** (SVI 20,5; `pop_10km` 9 870) — e a recontagem **confere** com `risk_index_metadata.json`. **Ambos são lacuna de associação, e ambos são recuperáveis** (ver a entrada de correção abaixo). (b) **A contagem de exposição degenerada estava incompleta.** São quatro, como o registro dizia, mas o quarto nunca fora nomeado: Santa Rita/MA (**4** residentes a até 10 km), Calçoene/AP (101), Oiapoque/AP (518) e **Terra de Areia/RS (765)**. Apenas os dois primeiros ficam no piso de 0,01 de exposição. Removendo os quatro, ρ = 1,000 e deslocamento máximo de posto 0 — não ancoram nada. (c) **Categoria nova, e é a maior:** **83 dos 280** municípios com risco derivam seu perigo de um ponto que **não aceitou nenhum evento composto**, portanto têm `Hazard_Index_mun` exatamente **0,000** e um risco sustentado inteiramente pelo piso de 0,01. Concentram-se no N/NE (CE 18, AL 15, RN 14, PE 12, SE 7, BA 7, PB 3, MA 3, PA 3, AP 1) e ocupam as posições **191 a 280** — todo o terço inferior do ranking. Dentro desse grupo a ordenação é determinada só por exposição e vulnerabilidade e não carrega informação de perigo. Isso **não** era possível sob o método anterior, em que todo ponto tinha eventos; é uma consequência direta do portão HAT (208 dos 808 pontos ficaram sem evento aceito) |
| **Interpretação** | Duas das três falhas de cobertura do registro original permanecem exatamente como estavam, e a terceira — ausência de critério de pertencimento — também. Mas a mudança de método criou um problema de cobertura **de outra natureza e uma ordem de grandeza maior**: quase um terço da amostra tem perigo nulo por construção. Isso não é um defeito do método (é o portão funcionando: onde o nível nunca alcança o HAT, não há inundação costeira composta a reportar), mas é uma limitação de leitura séria, porque um mapa colorido dá a esses 83 municípios uma posição que parece um gradiente de perigo e não é |
| **Alterações implementadas** | Nenhuma no conjunto amostral. Nenhum município excluído. Declaração dos ausentes por nome, dos quatro degenerados por nome e valor, e dos 83 sem perigo com sua faixa de posições, no README e na página de metodologia do índice; parágrafo pronto para o manuscrito |
| **Validação realizada** | A recontagem foi conferida contra `risk_index_metadata.json` campo a campo (`municipality_feature_count` 282, `matched_hazard_count` 280, lista de ausentes) — **concordam**. A contagem de `Hazard_Index_mun == 0` foi verificada independentemente no GeoJSON: 83, e a faixa de posições 191–280 confirmada |
| **Incerteza remanescente** | (1) **O critério de pertencimento continua desconhecido** — herdado de um PDF, não reconstruível a partir do repositório. (2) Não existe classificação de frente de mar; sem ela, Santa Rita/MA não pode ser separada por critério geométrico em vez de por `pop_10km` baixo, que seria circular. (3) **Içara continua sem associação** e depende de AUD-04. (4) As ausências e os casos degenerados estão declarados em texto, mas **não marcados no GeoJSON nem nas legendas dos mapas** — o registro pedia que deixassem de ser apenas um campo de JSON técnico, e hoje são texto no README, o que é melhor mas ainda não é o produto. (5) O efeito dos 83 municípios de perigo nulo sobre as normalizações e sobre a definição de hotspot não foi analisado — interage com AUD-11 e AUD-16 |
| **Próxima decisão necessária** | Três, do pesquisador: (a) marcar ou não os casos no produto (GeoJSON e legendas), que é trabalho de código; (b) tentar ou dispensar a recuperação de Içara via AUD-04; (c) decidir se os 83 municípios de perigo nulo devem ser exibidos como categoria própria nos mapas em vez de receberem cor de risco baixo. Enquanto essas estiverem abertas, AUD-15 **não pode** fechar |

### 2026-07-31 (correção) — Fernando de Noronha **não** está fora de escopo

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | A entrada anterior afirmou que nenhum dos 808 pontos seria apropriado para Fernando de Noronha, por ser um arquipélago a ~350 km da costa. Isso é verdade? |
| **Dados e métodos** | Distância mínima entre cada ponto de `compound_metrics_hat.csv` e o polígono municipal, em EPSG:5880; e inspeção de todos os pontos da grade na janela do arquipélago |
| **Scripts executados** | Verificação em `geopandas`, não versionada |
| **Achados** | **A afirmação anterior era falsa.** O domínio vai de 55° W a 28° W e cobre o arquipélago com folga. Há **19 pontos de grade** na janela (−4,6 a −3,1 S; −33,2 a −31,6 W), com `thr_hs_abs` entre 1,98 e 2,15 m — valores oceânicos perfeitamente normais, não degenerados — e `hat_m` entre 1,48 e 1,51 m. O ponto mais próximo do polígono, (−3,8; −32,4), está a **1,5 km**. Cada um dos 19 carrega **9 a 13 candidatos**, e em todos os 19 o portão HAT rejeita **100 %** deles: nenhum ponto do arquipélago tem evento aceito. Para comparação, Içara tem seu ponto mais próximo a **16,5 km**, com **77 eventos aceitos**, e três candidatos dentro de 30 km |
| **Interpretação** | As duas ausências são do mesmo tipo — **lacuna de associação**, não decisão de escopo — e as duas são recuperáveis por edição de uma linha no arquivo de associação. A consequência difere: Içara receberia perigo real (77 eventos no ponto vizinho) e entraria no ranking com valor; Fernando de Noronha receberia `Hazard_Index_mun` = 0 e se juntaria aos 83 municípios sem perigo aceito. Isso é um **resultado**, não um defeito: o arquipélago é oceânico, o HAT ali é 1,5 m, e em 33 anos nenhum evento composto alcançou esse nível. Excluí-lo silenciosamente esconderia esse resultado; associá-lo o publica |
| **Alterações implementadas** | Correção do critério de aceitação correspondente na §9, que estava marcado como satisfeito sobre premissa errada, e do parágrafo de limitação em `README.md` |
| **Validação realizada** | 19 pontos listados individualmente com limiar, HAT, candidatos e rejeições; distâncias calculadas em CRS métrico |
| **Incerteza remanescente** | A representatividade de uma célula de ~0,2° sobre um arquipélago de 17 km² é discutível — o WAVERYS ali descreve mar aberto, não a zona de arrebentação das enseadas. Isso vale igualmente para os 19 pontos e não distingue nenhum deles |
| **Próxima decisão necessária** | Associar os dois municípios (uma linha cada em `data/external/municipal_grid_association/municipal_grid_association.csv`) ou declarar exclusão **com a razão correta**, que não é "fora do domínio" |


### 2026-07-31 — DECISÃO: remover o piso de 0,01; perigo nulo passa a dar risco nulo

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31. Registro canônico: **AUD-11 §14** |
| **Decisão** | Remover `CLIP_FLOOR = 0,01`. Com o perigo passando a ter zero natural (AUD-11), a média geométrica torna-se genuinamente conjuntiva e os **83 municípios cujo ponto não aceitou nenhum evento passam a ter risco exatamente zero**, em vez de uma posição entre 191 e 280 sustentada pelo piso |
| **Consequência medida** | 84 municípios com risco exatamente zero (83 por perigo nulo, 1 por exposição degenerada — Santa Rita/MA, com 4 residentes). Os 83 **empatam** em zero: a ordenação interna deles, que não carregava informação de perigo, desaparece — o que é o comportamento pretendido |
| **Exigência de rotulagem** | "Risco zero" aqui significa **"nenhum evento composto atendeu aos critérios em 1993–2025"**, não impossibilidade física. São 33 anos de amostra finita. O mapa e o manuscrito devem usar essa formulação, e os municípios em zero devem ser uma **categoria própria** na legenda, não a cor mais clara de um gradiente contínuo |
| **Fernando de Noronha** | O pesquisador aceitou que permaneça ausente: *"área preservada → baixo risco"*. Coerente com o esquema novo — se associado, receberia perigo zero (os 19 pontos do arquipélago rejeitam 100 % dos candidatos) e, portanto, risco exatamente zero. A ausência e o zero passam a ser o mesmo resultado |
| **Içara** | Encaminhado a **Karine Bastos Leal** para verificação da associação. Ponto mais próximo a 16,5 km, com 77 eventos aceitos: se associado, entra no ranking com perigo real, não com zero |
| **Critérios que continuam abertos** | Critério de pertencimento ao conjunto; classificação de frente de mar; marcação dos casos no GeoJSON e nas legendas. AUD-15 **não fecha** |
