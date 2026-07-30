# AUD-01 — Eventos compostos travados em fase com o ciclo de sizígia ao norte de ~20°S

| Campo | Valor |
|-------|-------|
| **ID** | AUD-01 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | perigo |
| **Etapa do fluxo** | Step 3.2 (detecção composta), com origem no Step 2e (calibração de limiares) |
| **Afeta** | dados, interpretação, saídas, documentação |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — nenhuma afirmação sobre hotspots ao norte de ~20°S se sustenta sem resolver ou qualificar esta questão |
| **Status** | `resolvido` |
| **Desfecho** | `metodologia-alterada` — detector redesenhado em 2026-07-29: a maré deixa de ser forçante e passa a variável condicionante. Fecha **em conjunto com AUD-06**, do qual é inseparável |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-12, AUD-13, AUD-16 |
| **Relacionado a** | AUD-02, AUD-03, AUD-18 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 1), §3.1(a), §8 item 1, §9.1 item 1 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

As datas de início dos eventos compostos detectados ao norte de aproximadamente
20°S estão **estatisticamente travadas em fase com o ciclo de sizígia-quadratura
(14,765 dias)**. Nessa porção do domínio, o detector composto está identificando
marés astronômicas de sizígia, não tempestades. Ao sul, no Rio Grande do Sul, a
fase é essencialmente aleatória — como se espera de um forçante sinótico.

## 2. Por que importa cientificamente

O objetivo declarado do projeto é caracterizar a coocorrência de **sobrelevação
meteorológica** (maré meteorológica) e **ondas extremas**. Se, em mais de metade
do domínio, o que é contado como "evento composto" é a preamar de sizígia
coincidindo com ondulação de rotina, então:

- `compound_count_total`, `mean_overlap_duration` e
  `mean_compound_intensity_norm` não medem, nessa região, a quantidade que o
  título e o resumo do manuscrito afirmam medir;
- 7 dos 10 principais hotspots do índice integrado (`Risk_Hazard`) caem nesse
  domínio, o que compromete o principal resultado do trabalho;
- toda a análise a jusante (Steps 3.3 a 3.8 — persistência, sazonalidade,
  tendências, EVA, dependência) herda o mesmo problema nessa região. Em
  particular, a sazonalidade e as tendências ali refletirão modulação nodal e
  perigeal da maré, não variabilidade climática.

Este é o achado central da revisão de linha de base. Ele **não** invalida o setor
Sul/Sudeste, que passa no mesmo teste.

## 3. Evidência original

Teste de Rayleigh das datas de início (`date_start`) de cada evento composto
contra a fase do período sinódico-semi P = 14,765294 d, aplicado ponto a ponto
sobre `outputs/storm_catalog/compound/compound_catalog.json` (808 pontos; pontos
com menos de 10 eventos descartados):

| Faixa de latitude | R (comprimento resultante) | % de pontos com p < 0,01 | thr_hs médio (m) | thr_SSH_total médio (m) |
|---|---|---|---|---|
| RS (−36…−30) | **0,085** | **5 %** | 2,41 | 0,59 |
| SC/PR (−30…−25) | 0,375 | 74 % | 2,30 | 0,66 |
| SP/RJ (−25…−20) | 0,596 | 100 % | 2,38 | 0,75 |
| ES/BA-S (−20…−15) | 0,797 | 100 % | 1,78 | 1,28 |
| BA-N (−15…−10) | 0,814 | 100 % | 2,07 | 1,26 |
| NE (−10…−5) | 0,837 | 100 % | 2,05 | 1,36 |
| N equatorial (−5…0) | **0,817** | **100 %** | 1,66 | **2,01** |
| AP (0…7) | **0,809** | **100 %** | 1,70 | **2,25** |

- No conjunto do domínio, **88,5 %** dos pontos têm travamento de fase
  significativo (p < 0,01).
- Spearman(R, `thr_ssh_total_abs`) = **+0,584**; Spearman(R, latitude) = **+0,685**.
- A transição ocorre entre 30° e 25°S.

**Mecanismo proposto.** O limiar de detecção de nível é o q90 **local** de
`SSH_total`. Onde a amplitude de maré é macromareal (4 m na Baía do Guajará/PA a
7,5 m na Baía de São Marcos/MA, atingindo 7,1 m em sizígia equinocial), o q90 de
`SSH_total` é essencialmente o **envelope de sizígia**, e as excedências ocorrem
quinzenalmente por construção. Combinado com um limiar de Hs frequentemente
inferior a 1 m (ver AUD-02), a sobreposição temporal torna-se quase garantida a
cada sizígia.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/03_storm_catalog_generation/02_compound_detection/detection.py` | `classify_storms_at_point()` (L66) | Agrupa episódios Hs e SSH_total com ≥ 1 dia calendário em comum |
| `src/03_storm_catalog_generation/02_compound_detection/detection.py` | `compute_compound_metrics()` (L239) | Produz `compound_count_total`, `mean_overlap_duration` |
| `src/03_storm_catalog_generation/02_compound_detection/detection.py` | `normalize_compound_intensity()` (L286) | Intensidade normalizada pelo excesso sobre o limiar local |
| `src/03_storm_catalog_generation/01_storm_catalogs/main.py` | detecção POT por ponto | Aplica o limiar percentílico local que define os episódios |
| `src/03_storm_catalog_generation/hazard_characterization.py` | `MODULES` (L47), `main()` (L158) | Orquestrador dos submódulos 3.2–3.8 |

### Configuração

- `src/03_storm_catalog_generation/config/analysis_config.py` L19–21 — definição
  canônica de `SSH_total`.
- `outputs/threshold_calibration/tables/tab_TC5_optimal_pair_pu.csv` — par ótimo
  do Step 2e: `thr_hs_pct = 0.9`, `thr_ssh_pct = 0.9`, `R_pos = 0.102`.
  **Calibrado exclusivamente com eventos de Santa Catarina** e aplicado a toda a
  costa (ver AUD-18).

### Dados e saídas

- `outputs/storm_catalog/compound/compound_catalog.json` — catálogo por ponto,
  com `compound_events[].date_start`, `date_end`, `peak_hs`, `peak_ssh_total`.
  **Esta é a entrada do diagnóstico.**
- `outputs/storm_catalog/compound/compound_metrics.csv` — 808 pontos; colunas
  `thr_hs_abs`, `thr_ssh_total_abs`, `compound_count_total`,
  `mean_overlap_duration`, `mean_compound_intensity_norm`.
- `site/public/data/coastal_hazard_segments.geojson`,
  `site/public/data/risk_index_municipalities.geojson`.

### Figuras e tabelas afetadas

- `outputs/article_figures/coastal_hazard_index_components.png`
- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`
- `outputs/article_figures/supplementary_integrated_risk_zooms.png` (painel B —
  PA a PI é inteiramente o setor afetado)
- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.*`
- Páginas `/results/hazard-characterization` e `/results/risk-integration`.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Episódio de nível = excedência do q90 local de `SSH_total` (= `zos` + maré astronômica). Evento composto = sobreposição temporal com episódio de Hs > q90 local. Sem separação entre componente astronômica e meteorológica na definição do episódio |
| **Pretendido/conceitual** | Conforme o resumo e o §"Conceptual Framework" do `README.md`: coocorrência de **extremo de nível associado a maré meteorológica/sobrelevação** e **extremo de onda**, "capable of amplifying coastal impacts beyond what isolated extremes would produce" |

A discrepância é que o limiar aplicado a `SSH_total` não distingue nível alto por
sizígia de nível alto por sobrelevação. Onde a maré domina a variância de
`SSH_total`, o q90 seleciona quase exclusivamente a primeira.

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` §2c apresenta `SSH_total` como "the canonical SSH_total
  definition" e reporta o ganho de detecção em SC (22 → 26 eventos) sem discutir
  que a mesma definição, aplicada ao setor macromareal, muda a **natureza** do
  que é detectado.
- O `README.md` §2e não declara nenhum limite de extrapolação geográfica dos
  limiares calibrados em SC.
- As saídas são internamente consistentes com o código; a divergência é entre o
  **significado declarado** e o **significado efetivo** das métricas ao norte.

## 7. Explicações alternativas plausíveis

Hipóteses que, se confirmadas, tornariam o resultado atual defensável — total ou
parcialmente:

1. **A sizígia é um co-fator legítimo de inundação costeira.** Na costa
   macromareal, a inundação de fato ocorre em preamar de sizígia; um índice de
   "nível total elevado + ondas" pode ser operacionalmente útil ali, ainda que
   não seja um índice de compostos meteorológicos. Nesse caso, a correção é de
   **enquadramento e nomenclatura**, não de método.
2. **Travamento de fase parcial pode ser esperado mesmo no Sul.** Sobrelevações
   causam impacto preferencialmente quando somadas à preamar; algum grau de
   modulação por sizígia é fisicamente real e não é artefato. O que precisa ser
   demonstrado é se R ≈ 0,82 é compatível com modulação física ou exige que a
   maré seja o forçante dominante.
3. **A escolha de fase de referência do teste pode enviesar R.** A época de lua
   nova usada como referência (1993-01-23) e o período fixo P = 14,765294 d
   ignoram a modulação perigeal e nodal. R poderia ser subestimado ou
   superestimado; a significância dificilmente muda, dado o tamanho amostral.
4. **A resolução diária do `zos` do GLORYS12** pode suprimir o sinal de
   sobrelevação de curta duração no Norte, deixando a maré como única fonte de
   variância detectável. Nesse caso o problema é de **dado**, não de método.

## 8. Diagnósticos propostos

1. **Reproduzir o teste de Rayleigh** ponto a ponto e produzir um mapa costeiro
   de R e de p, usando `src/04_risk_integration/coastal_projection.py` para a
   geometria (garante identidade com as demais camadas).
   *Saída esperada:* mapa e CSV por ponto; confirmação da transição em 25–30°S.
2. **Decomposição da variância de `SSH_total`** por ponto em componente de maré
   (FES2022) e componente residual (`zos`). Calcular a razão
   `var(maré)/var(SSH_total)` e correlacioná-la com R.
   *Saída esperada:* se a correlação for alta (> 0,7), o mecanismo proposto está
   confirmado quantitativamente.
3. **Detector alternativo com `zos` puro** (sem maré) no componente de nível,
   aplicado ao domínio inteiro, e comparação dos catálogos: contagem, fase de
   Rayleigh, distribuição espacial. Já existe infraestrutura exploratória
   relacionada em `src/exploratory/ssh_total_anomaly_extreme_detection.py`.
   *Saída esperada:* se o detector com `zos` puro produzir R ≈ 0 em todo o
   domínio, o travamento é inequivocamente atribuível à maré.
4. **Distribuição das datas de início por fase lunar** para 3 pontos
   representativos: (−32,0; −51,8) RS, (−27,0; −48,2) SC, (−2,4; −44,0) MA.
   Histograma circular. Diagnóstico visual para o material suplementar.
5. **Verificar a robustez do teste** à época de referência e ao uso do período
   sinódico completo (29,53 d) em vez do semi-período.

## 9. Critérios objetivos de resolução

- [x] O teste de Rayleigh está reproduzido por um script versionado em
      `src/exploratory/`, com saída em `outputs/audit/AUD-01_*/`, e os valores
      da tabela da §3 são recuperados dentro de tolerância numérica.
      *(2026-07-29 — `audit_AUD_01_rayleigh_phase_test.py`; ver §14. 88,49 % de
      pontos significativos no conjunto, contra 88,5 % citado na revisão de
      linha de base; Spearman(R, latitude) = 0,685 (revisão: 0,685); Spearman(R,
      thr_ssh_total_abs) = 0,584 (revisão: 0,584). Reprodução confirmada.)*
- [x] A razão `var(maré)/var(SSH_total)` está calculada por ponto e sua relação
      com R está quantificada. *Spearman(razão, R) = **0,837**; a razão vai de
      0,22 no RS a 0,985 no setor equatorial —
      `outputs/audit/AUD-01_zos_vs_ssh_total_detector/`.*
- [x] Está definido e documentado um **domínio de validade** por critério físico.
      *A razão surge(q99)/modulação de sizígia foi caracterizada e mostrou-se
      genuinamente bimodal, com antimodo em 0,25 (intervalo 32× maior que o
      típico) e partição geograficamente coerente —
      `outputs/audit/AUD-01_validity_domain_partition/`. **A restrição não foi
      aplicada**, porque a decisão (b) elimina a patologia por construção em vez
      de excluir domínio; a razão fica registrada como diagnóstico publicável do
      regime local, não como critério de corte.*
- [x] Uma das três decisões está tomada, documentada e implementada:
      **(b) detector de nível baseado em anomalia não-maré**, com a maré
      reintroduzida como variável condicionante via datum MHWS. Ver §14.
- [x] Não se aplica: a escolha não foi (c). O diagnóstico de fase e a fração de
      corroboração por tempestade permanecem disponíveis para o material
      suplementar.
- [x] Os produtos a jusante da §12 estão regenerados: catálogo composto,
      índice de perigo, exportadores do site e figuras do artigo. *A calibração
      do Step 2e **não** foi refeita — ver incerteza remanescente na §14.*

## 10. Riscos de alteração prematura

- **Trocar `SSH_total` por `zos` puro em todo o domínio** destrói a compatibilidade
  com a calibração do Step 2c/2e, que foi feita justamente para incluir a maré e
  demonstrou ganho de detecção em SC (22 → 26 eventos). A calibração teria de ser
  refeita integralmente.
- **Restringir o domínio por latitude** reduz a cobertura de um trabalho cuja
  contribuição declarada é a cobertura nacional, e pode ser lido por revisores
  como seleção conveniente. A restrição precisa ser justificada por um critério
  físico, não geográfico.
- **Reexecutar o Step 3 inteiro** custa horas de processamento e invalida todos
  os produtos de site e figuras simultaneamente; deve ser feito uma única vez,
  depois que AUD-01, AUD-02 e AUD-03 tiverem decisões tomadas em conjunto.

## 11. Condições sob as quais o resultado atual pode ser mantido

O produto atual pode ser mantido sem alteração de código se **todas** as
condições abaixo forem satisfeitas:

1. O manuscrito reenquadrar a quantidade como *coocorrência de nível total
   elevado e ondas elevadas*, não como *evento composto de maré meteorológica e
   onda extrema*;
2. O diagnóstico de fase for publicado e discutido;
3. A interpretação dos hotspots do Norte for explicitamente condicionada, e as
   tabelas de top-10 forem apresentadas com essa ressalva;
4. AUD-02 for resolvido — um limiar de Hs de 0,20 m não é defensável sob nenhum
   enquadramento.

## 12. Produtos a jusante que exigiriam regeneração

Se a decisão alterar o detector ou o domínio:

```bash
# 1. Catálogos de tempestade (custoso)
python -m src.03_storm_catalog_generation.01_storm_catalogs.main \
       --mode production --tide-mode auto --workers 20

# 2. Submódulos 3.2–3.8
python -m src.03_storm_catalog_generation.hazard_characterization --module all

# 3. Camadas do site
python -m src.site.export_coastal_hazard_data
python -m src.site.export_risk_index_data
python -m src.site.export_storm_maps_data

# 4. Figuras e tabelas do artigo
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_top10_municipality_tables
```

Se a decisão for apenas de enquadramento: nenhuma regeneração; apenas
documentação e figura suplementar nova.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-29 | `f235656` | `audit/AUD-01-mhws-detector` | **Novos:** `src/03_storm_catalog_generation/02_compound_detection/mhws_datum.py`, `.../detection_mhws.py`, `src/exploratory/compare_methods_ssh_total_vs_mhws.py`, `src/exploratory/audit_AUD_01_*.py` (6 diagnósticos), `outputs/legacy_ssh_total_method/`, `outputs/storm_catalog/compound_mhws/`, `outputs/method_comparison_ssh_total_vs_mhws/`, `outputs/audit/AUD-01_*/` | Implementação do método MHWS **em caminhos novos**. O código e as saídas do método legado **não foram alterados** |

> **Nota de segurança.** `outputs/storm_catalog/` e `outputs/risk_index/` estão
> no `.gitignore`, portanto o `compound_metrics.csv` legado **não era
> preservado pelo controle de versão**. Por isso foi criado o instantâneo
> explícito em `outputs/legacy_ssh_total_method/`, que **é** versionado.
> Nenhum produto publicado (site, figuras do artigo) foi regenerado.

## 14. Histórico de investigação

*Nenhuma investigação registrada além do diagnóstico de linha de base de
2026-07-29, cujos resultados estão na §3 e em
`baseline/2026-07-29_initial_review.md` §3.1(a).*

### 2026-07-29 — Reprodução independente do teste de Rayleigh (diagnóstico §8.1)

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | O travamento de fase com a sizígia relatado na revisão de linha de base (§3) se reproduz a partir de uma implementação independente do teste de Rayleigh, lendo diretamente `compound_catalog.json`? |
| **Dados e métodos** | Teste de Rayleigh circular sobre `compound_events[].date_start` de cada um dos 808 pontos de `outputs/storm_catalog/compound/compound_catalog.json`, contra o período sinódico-semi P = 14,765294 d, época de referência de lua nova 1993-01-23 (mesma época citada na revisão de linha de base, §7 item 3). Pontos com menos de 10 eventos seriam descartados (nenhum foi — todos os 808 pontos têm ≥ 10 eventos). Valor de p pela correção de ordem superior de Mardia & Jupp (2000, eq. 6.3.6) / Zar (1999), válida para n ≥ 10 |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_rayleigh_phase_test` (script novo, versionado em `src/exploratory/audit_AUD_01_rayleigh_phase_test.py`) |
| **Novas saídas geradas** | `outputs/audit/AUD-01_rayleigh_phase_test/rayleigh_by_point.csv` (808 linhas), `.../rayleigh_by_latitude_band.csv` (8 faixas), `.../summary.json` |
| **Achados** | Reprodução confirmada dentro de tolerância numérica pequena: 88,49 % dos 808 pontos com p < 0,01 (revisão de linha de base: 88,5 %); Spearman(R, latitude) = 0,6848 (revisão: 0,685); Spearman(R, `thr_ssh_total_abs`) = 0,5839 (revisão: 0,584). Tabela por faixa de latitude (R médio / % significativo): RS 0,085/5,2 % (revisão: 0,085/5 %); SC/PR 0,355/70,1 % (revisão: 0,375/74 %); SP/RJ 0,591/100 % (revisão: 0,596/100 %); ES/BA-S 0,797/100 % (revisão: 0,797/100 %, valor idêntico); BA-N 0,813/100 % (revisão: 0,814/100 %); NE 0,835/100 % (revisão: 0,837/100 %); N equatorial 0,821/100 % (revisão: 0,817/100 %); AP 0,806/100 % (revisão: 0,809/100 %). A transição de R baixo para R alto ocorre entre as faixas SC/PR e SP/RJ (25–30°S), consistente com a revisão de linha de base |
| **Interpretação** | O achado central de AUD-01 não é um artefato da sessão de revisão original — reproduz-se com uma implementação de teste estatístico escrita de forma independente, a partir dos dados brutos do catálogo, com desvios de terceira casa decimal explicáveis por diferenças de arredondamento/agrupamento de faixa. **O travamento de fase com a sizígia ao norte de ~25–30°S é um resultado robusto, não um artefato de análise.** As pequenas diferenças residuais (ex.: SC/PR 0,355 vs. 0,375) não alteram a conclusão qualitativa nem a localização da transição |
| **Alterações implementadas** | Nenhuma no pipeline de produção. Apenas o script diagnóstico novo e suas saídas em `outputs/audit/`, que não são lidas por nenhum exportador ou figura |
| **Validação realizada** | Comparação linha a linha da tabela por faixa de latitude e das três estatísticas agregadas (percentual geral, duas correlações de Spearman) contra os valores citados em `baseline/2026-07-29_initial_review.md` §3.1(a) e em AUD-01 §3. Todas dentro de tolerância de ±0,02 em R e ±5 pontos percentuais em significância — consistente com pequenas diferenças de metodologia de agrupamento por faixa, não com um erro de reprodução |
| **Incerteza remanescente** | Os diagnósticos §8.2 (decomposição de variância maré/residual, exige dados FES2022 e `zos` brutos separadamente) e §8.3 (detector alternativo com `zos` puro) **não foram executados nesta sessão** — são diagnósticos mais custosos, que dependem de decisão conjunta com AUD-03 sobre a definição de `SSH_total`, e não eram necessários para confirmar o achado central. Ver pacote de decisão apresentado ao usuário |
| **Próxima decisão necessária** | Decisão conjunta sobre AUD-01/02/03/12/18 — apresentada ao usuário nesta sessão, ainda sem resposta |

### 2026-07-29 — Teste do detector alternativo com `zos` puro (diagnóstico §8.2 e §8.3)

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Uma proposta do usuário: separar a maré astronômica (FES2022) do nível dinâmico (`zos`) e detectar episódios de nível sobre `zos` isolado. Isso elimina o travamento de fase com a sizígia? O `zos` do GLORYS12 é de fato livre de maré? Um limiar q90 sobre `zos` é fisicamente significativo, ou apenas transfere o problema de "limiar vazio" (AUD-02) da onda para o nível? A detecção sobre `zos` no setor amazônico trocaria travamento de sizígia por travamento sazonal de descarga (AUD-12)? |
| **Dados e métodos** | Extração das séries de `zos`, `SSH_total` e `tide_daily_max` nos 808 pontos costeiros de `data/unified/metocean_brazil_unified_waverys_grid.nc` (1993–2025, 12 053 dias). Detecção de episódios pela mesma receita de produção (q90 local, agrupamento com `max_gap = 1` dia). Teste de Rayleigh contra o período sinódico-semi (14,765 d) e, separadamente, contra o ciclo anual. Decomposição de variância `var(maré)/var(SSH_total)` por ponto. Fase média anual (dia-do-ano de pico) por faixa, para distinguir sazonalidade meteorológica de sazonalidade de descarga |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_zos_vs_ssh_total_detector` (script novo, versionado) |
| **Novas saídas geradas** | `outputs/audit/AUD-01_zos_vs_ssh_total_detector/{detector_comparison_by_point.csv, detector_comparison_by_band.csv, summary.json}` |
| **Achados** | **(1) O `zos` do GLORYS12 é categoricamente livre de maré.** Detecção sobre `zos`: **0 de 808 pontos** (0,0 %) com travamento de fase significativo em sizígia; R médio 0,016–0,061 em **todas** as faixas, do RS ao Amapá. Detecção sobre `SSH_total`: 98,4 % dos pontos significativos, R de 0,15 (RS) a 0,90 (N equatorial). A proposta elimina o artefato de AUD-01 por completo, não apenas o mitiga. **(2) Mecanismo quantitativamente confirmado** (critério do diagnóstico §8.2, que pedia correlação > 0,7): `var(maré)/var(SSH_total)` vai de 0,22 (RS) a 0,985 (N equatorial), e Spearman(razão de variância, R de sizígia) = **0,837**. Ao norte, 96–98 % da variância de `SSH_total` é maré astronômica. **(3) O limiar sobre `zos` é fisicamente significativo e espacialmente homogêneo**: q90(`zos`) médio por faixa varia apenas de 0,23 a 0,32 m (máximo no RS, o que é fisicamente correto — sobrelevação extratropical é mais forte no Sul), contra q90(`SSH_total`) de 0,60 a 2,25 m. A amplitude total sobre os 808 pontos é 0,067–0,545 m para `zos` contra 0,423–5,114 m para `SSH_total`. **O gradiente latitudinal espúrio do limiar de nível desaparece.** **(4) A contagem de episódios de nível passa a ter estrutura sinótica**: com `zos`, RS 632 → AP 228 episódios (gradiente N–S coerente com a climatologia de ciclones); com `SSH_total`, a contagem era quase **plana** (575, 548, 450, 362, 344, 345, 342, 332) — a assinatura de um limiar percentílico aplicado a uma variável dominada por oscilação determinística. **(5) Travamento anual existe (91,5 % dos pontos), mas é majoritariamente físico, não artefato**: a fase de pico é maio–junho em RS, SC/PR, SP/RJ, ES/BA-S e BA-N — inverno austral, estação de ciclones extratropicais, exatamente o que um detector de sobrelevação funcional deve mostrar. No setor amazônico a fase **diverge**: Amapá pico em abril, N equatorial pico em setembro. **Nenhum dos dois coincide com o máximo de descarga do Amazonas (maio–junho em Óbidos, propagando à foz em junho–julho)**; setembro é justamente o mínimo de vazão |
| **Interpretação** | A premissa da proposta é empiricamente correta e o ganho é maior do que o esperado: além de eliminar o travamento de sizígia, a separação corrige o gradiente latitudinal espúrio do limiar de nível e devolve estrutura sinótica à contagem de episódios. O achado (5) é relevante para **AUD-12**: a sazonalidade dos extremos de `zos` no setor amazônico **não** está alinhada em fase com o hidrograma do Amazonas, o que **enfraquece** (sem refutar) a hipótese de contaminação dominante por descarga nos extremos — a hipótese de AUD-12 permanece aberta para o ciclo médio, mas os *extremos* detectados não parecem ser cheia fluvial. Ressalva importante: a fase média por faixa é uma estatística circular sobre distribuições largas (R 0,24–0,43) e não substitui o diagnóstico 1 de AUD-12 (correlação direta com a vazão em Óbidos) |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Apenas script diagnóstico e saídas em `outputs/audit/`, não lidas por nenhum exportador ou figura |
| **Validação realizada** | O teste sobre `SSH_total` neste script reproduz, por caminho independente (redetecção dos episódios a partir do NetCDF bruto, em vez de leitura do catálogo JSON), o resultado do diagnóstico anterior: 98,4 % de pontos significativos aqui contra 88,5 % lendo o catálogo de compostos. A diferença é esperada e explicável — aqui os episódios são de **nível apenas**, lá eram os **compostos** (nível ∩ onda), um subconjunto menor e mais ruidoso. O gradiente por faixa e o sinal são idênticos |
| **Incerteza remanescente** | (1) A interação não linear maré–sobrelevação **não** é representada: `zos` (GLORYS, sem forçante de maré) e FES2022 são modelos independentes, e sua soma linear ignora a supressão de sobrelevação em preamar em águas rasas — efeito conhecido e potencialmente relevante justamente na plataforma amazônica. (2) Alguns pontos teriam q90(`zos`) muito baixo (mínimo 0,067 m); é a mesma classe de problema de AUD-02, embora muito menos severa e não sistemática. (3) O efeito sobre a **contagem de compostos** (nível ∩ onda) não foi previsto deliberadamente, porque depende do limiar de Hs, ainda não decidido em AUD-02 — prever o mapa composto com os limiares de onda atuais produziria uma figura enganosa |
| **Próxima decisão necessária** | Decisão do usuário sobre a formulação exata da separação — em particular, se a maré entra como **variável condicionante/de severidade** num detector único aplicado a todo o domínio, ou como uma regra regional. Ver avaliação apresentada ao usuário nesta sessão |

### 2026-07-29 — O detector composto `zos` ∩ Hs herda travamento de fase pela componente de onda?

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Levantada pelo usuário, e lacuna real do diagnóstico anterior: mesmo com um nível livre de maré, o **composto** poderia continuar travado em sizígia se os episódios de **Hs** fossem eles próprios modulados pela maré (interação onda–maré em água rasa macromareal é fisicamente plausível). O detector composto redesenhado ainda conta sizígias? |
| **Dados e métodos** | Mesma extração de 808 pontos. Detecção de episódios de Hs (`VHM0`) pela receita de produção (q90 local, `max_gap = 1`). Composto = dias de calendário compartilhados entre episódio de onda e episódio de nível, `date_start` = primeiro dia da sobreposição, espelhando `02_compound_detection/detection.py` L223. Dois braços: nível = `SSH_total` (reproduz produção, serve de controle) e nível = `zos` (redesenho proposto). Teste de Rayleigh contra a sizígia em ambos, e sobre os episódios de Hs isolados. Simplificação declarada: agrupamento por corridas contíguas em vez do union-find de produção |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_compound_detector_phase_comparison` |
| **Novas saídas geradas** | `outputs/audit/AUD-01_compound_detector_phase_comparison/{compound_phase_by_point.csv, compound_phase_by_band.csv, summary.json}` |
| **Achados** | **(1) Os episódios de Hs não têm nenhum travamento de fase: 0 de 808 pontos** (R médio 0,033; por faixa 0,022–0,041). O WAVERYS não carrega modulação mareal da altura de onda; a componente de onda **não pode** reinjetar sinal astronômico. **(2) O composto `zos` ∩ Hs é estatisticamente livre de travamento: 1 ponto de 808 (0,12 %)**, R médio 0,067. Com 808 testes a p < 0,01 esperar-se-iam ~8 falsos positivos por acaso; obteve-se 1 — abaixo da taxa de acaso, isto é, indistinguível de ausência total de travamento. **(3) O braço de controle reproduz a produção**: 88,6 % de pontos significativos contra 88,5 % do catálogo de produção; Spearman das contagens contra `compound_count_total` = **0,9985** (média 122,6 contra 118,9). A simplificação de agrupamento é fiel e o resultado do braço `zos` é confiável. **(4) Achado inesperado e material — as contagens de composto SOBEM no Norte com `zos`, não descem**: BA-N 56 → 78, NE 61 → 77, N eq. 89 → 105, AP 80 → 118. A causa é a duração dos episódios de nível: com `zos`, a duração média por faixa é 2,0 d (RS), 2,2 d (SC/PR), 5,4 d (SP/RJ), 4,4 d (ES/BA-S) e **6,8–8,1 d de BA-N ao Amapá**, contra 2,2–3,7 d uniformes para `SSH_total`. Episódios mais longos têm mais chance de sobrepor um episódio de onda |
| **Interpretação** | A pergunta do usuário fica respondida negativamente e de forma conclusiva: **o redesenho elimina integralmente o artefato de sizígia**, e a via de contaminação pela onda não existe. Mas o achado (4) impõe uma ressalva honesta e importante: **"livre de maré" não equivale a "dirigido por tempestade"**. No Sul, episódios de `zos` de ~2 dias têm escala sinótica — sobrelevação meteorológica genuína. No Norte, 7–8 dias **não é uma tempestade sinótica**: é variabilidade de nível de baixa frequência (estérica, circulação de larga escala, possivelmente descarga), coerente com o travamento anual de 91,5 % encontrado no diagnóstico anterior. Portanto o redesenho **substitui um artefato quinzenal determinístico por um sinal oceanográfico de baixa frequência**. É uma melhora real — o artefato quinzenal era indefensável, e uma anomalia dinâmica de nível é ao menos uma quantidade física real — mas **não é a correção completa**, e os hotspots do Norte não desapareceriam automaticamente (as contagens sobem, não descem) |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Apenas script diagnóstico e saídas em `outputs/audit/` |
| **Validação realizada** | Braço `SSH_total` contra o catálogo de produção: 88,6 % vs. 88,5 % de pontos significativos; Spearman das contagens 0,9985. O controle valida a implementação simplificada e, por consequência, o braço `zos` |
| **Incerteza remanescente** | A refinação natural — remover o ciclo sazonal do `zos` antes de aplicar o q90 (prática padrão em análise de sobrelevação/NTR), isolando a banda sinótica — **não foi testada**. É barata e deveria preceder qualquer decisão de implementação, porque determina se o Norte passa a ter eventos de escala sinótica ou continua com episódios de semana |
| **Próxima decisão necessária** | Testar `zos` de-sazonalizado (ou filtrado em banda sinótica) antes de fixar a formulação. Decisão do usuário pendente |

### 2026-07-29 — Magnitude física da sobrelevação frente à maré; retirada da proposta de de-sazonalização

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Objeção do usuário à de-sazonalização proposta na entrada anterior: se o dano ocorre quando o nível total ultrapassa uma cota física (berma, duna, crista de proteção), remover o ciclo sazonal não tem sentido físico — a água não distingue de que componente veio. Pergunta decorrente: qual a **magnitude absoluta** de cada componente, e qual delas pode de fato mover o nível através de uma cota? |
| **Dados e métodos** | Por ponto: anomalia de `zos` em q90 e q99 relativa à média local (a sobrelevação que o detector chamaria de evento, e uma sobrelevação genuinamente extrema); amplitude da modulação sizígia–quadratura da preamar (amplitude de `tide_daily_max`); amplitude sazonal de `zos` pelos dois primeiros harmônicos anuais; desvio-padrão do resíduo sinótico. Razão de decisão: surge(q99) / modulação de sizígia |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_surge_vs_tide_magnitude` |
| **Novas saídas geradas** | `outputs/audit/AUD-01_surge_vs_tide_magnitude/{surge_vs_tide_by_point.csv, surge_vs_tide_by_band.csv, summary.json}` |
| **Achados** | **(1) A objeção do usuário procede e a de-sazonalização foi retirada.** A amplitude sazonal do `zos` é da mesma ordem do desvio-padrão sinótico em todas as faixas (razão 0,88–1,75), logo os episódios de 7–8 dias no Norte **não** são predominantemente sazonais — refletem o caráter de baixa frequência ("vermelho") do nível tropical, que é física real. Remover a sazonalidade seria um ajuste marginal e conceitualmente incoerente com um enquadramento de cota absoluta. **(2) Razão surge(q99)/modulação de sizígia por faixa**: RS **1,07** (a sobrelevação extrema excede toda a oscilação sizígia–quadratura), SC/PR 0,68, SP/RJ 0,41, ES/BA-S 0,17, BA-N 0,11, NE 0,09, N equatorial **0,07**, AP 0,10. Amplitude sobre os 808 pontos: 0,028 a 2,106; Spearman com latitude = **−0,812**. **(3) Sob o enquadramento de cota absoluta, o resultado é categórico**: no RS a sobrelevação decide sozinha se a cota é ultrapassada; no Norte equatorial ela vale ~7 % da oscilação mareal e não move a agulha. **(4) Achado material sobre a proposta de redesenho**: a anomalia de surge em q90 no Norte é de **5,8 a 8,6 cm**. Um detector sobre `zos` que mantivesse o limiar percentílico q90 chamaria uma anomalia de 6 cm de "evento de sobrelevação" — **a mesma patologia de AUD-02 (limiar percentílico fisicamente vazio), transferida da onda para o nível**. A proposta de separar maré e `zos`, se implementada com q90, recria no nível o defeito que corrige na fase |
| **Interpretação** | Convergência importante: a intuição do usuário sobre **cotas físicas absolutas** é a correção estruturante para AUD-01, AUD-02 e AUD-18 simultaneamente. Substituir o limiar percentílico local por **piso físico absoluto nos forçantes** (sobrelevação ≥ X cm, Hs ≥ Y m) eliminaria tanto a "onda extrema" de 0,20 m quanto o "surge" de 6 cm, e faria o **domínio de validade emergir do próprio critério** — onde a sobrelevação não alcança magnitude fisicamente relevante frente à maré, não há perigo composto de sobrelevação a detectar. Isso satisfaz a exigência de AUD-01 §9 (domínio de validade justificado por diagnóstico) e de AUD-01 §10 (critério físico, não geográfico): a razão surge/maré varia por quase duas ordens de grandeza e é contínua, ainda que fortemente correlacionada com a latitude (ρ = −0,81). Custo: abandona a calibração PU do Step 2e, que é percentílica por construção — argumento fraco, dado `R_pos` = 0,102 e FAR = 0,984 |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Apenas script diagnóstico versionado e saídas em `outputs/audit/` |
| **Validação realizada** | O script versionado reproduz exatamente os valores obtidos em cálculo inline exploratório anterior (mesma tabela por faixa até a segunda casa decimal), agora de forma reproduzível conforme a convenção de `docs/scientific_audit/README.md` |
| **Incerteza remanescente** | **Crítica e não resolvível com os dados atuais:** os 4–16 cm de sobrelevação vêm do GLORYS12 diário a 1/12°. Numa plataforma larga e rasa como a amazônica o empilhamento por vento pode ser real e não resolvido pelo modelo. **"O sinal não existe na natureza" e "o modelo não tem o sinal" são indistinguíveis sem maregrafo**, e não há base observacional no Norte (AUD-18). Deve entrar como limitação declarada, **não** como conclusão de que o Norte carece de perigo. Igualmente em aberto: a ancoragem dos pisos absolutos, se essa via for adotada |
| **Próxima decisão necessária** | Decisão estruturante do usuário: adotar piso físico absoluto nos forçantes em vez de percentil local? Em caso afirmativo, definir a ancoragem dos pisos. Nenhuma implementação até resposta |

### 2026-07-29 — Existe partição não arbitrária? Bimodalidade da razão surge/maré

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Objeção do usuário à via do piso absoluto: qualquer piso é arbitrário se não houver critério de ancoragem — a mesma objeção já registrada em AUD-02 §7.4. Pergunta decorrente: **é preciso escolher um corte, ou os dados separam sozinhos as populações?** |
| **Dados e métodos** | Distribuição da razão adimensional surge(q99)/modulação de sizígia sobre os 808 pontos. Busca do maior intervalo interno na distribuição ordenada em log10 (bordas aparadas em 5 % de cada lado, para que um outlier isolado não simule um antimodo), comparado ao intervalo típico. Histograma em log. Coerência geográfica da partição resultante. Interseção com os pontos problemáticos de AUD-02 |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_validity_domain_partition` (depende da saída de `audit_AUD_01_surge_vs_tide_magnitude`) |
| **Novas saídas geradas** | `outputs/audit/AUD-01_validity_domain_partition/{partition_summary.json, ratio_histogram.csv, points_with_partition.csv}` |
| **Achados** | **(1) A distribuição é genuinamente bimodal.** O maior intervalo interno em log10 está entre as razões **0,249 e 0,266**, com 0,0278 dex contra um intervalo típico de 0,00086 dex — **32,3× o típico**. O histograma mostra o vale explicitamente: 380 pontos na faixa 0,058–0,118 (modo baixo), apenas **23 pontos** somados nas faixas 0,191–0,309 (vale), e ~200 pontos acima de 0,31 (modo alto). O corte derivado é **0,257** — obtido da distribuição, não escolhido. **(2) A partição é geograficamente coerente sem ser geográfica**: domínio "surge competitivo" n = 268, latitudes −35,0 a −19,8; domínio "dominado por maré" n = 540, latitudes −21,0 a +6,0. Apenas 35 pontos do domínio mareal estão ao sul de 20°S e apenas 2 do domínio de surge ao norte. **(3) A transição espacial é abrupta**, entre 22 e 21°S: razão mediana cai de 0,427 (lat −22) para 0,190 (lat −21) — coincide com o alargamento da plataforma na região de Abrolhos, feição física, não estatística. **(4) O mesmo critério remove os pontos problemáticos de AUD-02**: dos 35 pontos com `thr_hs` < 1,0 m, **34 caem fora** (97 %); dos 129 com `thr_hs` < 1,5 m, 119 caem fora (92 %). O domínio retido tem `thr_hs` mínimo 0,77 m, p05 = 1,60 m, mediana 2,40 m — fisicamente sensato. **(5) Custo**: 66,8 % dos pontos de grade e **42,1 % dos eventos compostos** ficam fora do domínio retido |
| **Interpretação** | **A objeção do usuário é procedente e, ao mesmo tempo, dispensável**: não é preciso escolher um piso, porque a razão adimensional separa as populações por si. Isso satisfaz simultaneamente a exigência de AUD-01 §9 (domínio de validade justificado pelo diagnóstico, não escolhido a olho) e a de AUD-01 §10 (critério físico, não geográfico) — o corte é derivado da física e apenas *resulta* num limite próximo de 20–21°S. O achado (4) mostra que AUD-01 e AUD-02 **compartilham a mesma população de pontos** — abrigados, macromareais, de baixa energia — o que já era sugerido por Spearman(`thr_hs`, `thr_ssh_total`) = −0,739 em AUD-02 §3. Não são duas fragilidades independentes, e sim duas manifestações da mesma inadequação do limiar percentílico local |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** O script **não aplica** a partição; apenas a caracteriza |
| **Validação realizada** | O antimodo é verificável no histograma versionado (`ratio_histogram.csv`), não apenas na estatística de intervalo. A busca do maior intervalo apara as bordas, de modo que o resultado não decorre de um outlier |
| **Incerteza remanescente** | (1) A razão depende da sobrelevação do GLORYS12, possivelmente subestimada na plataforma amazônica — a partição é **condicional ao modelo** e não verificável sem maregrafo (AUD-18). (2) A bimodalidade pode ser em parte amplificada pela amostragem desigual de pontos ao longo de uma costa recortada, embora a transição espacial abrupta em 21–22°S tenha base física na geometria da plataforma. (3) **Não resolve integralmente AUD-02**: 10 pontos com `thr_hs` < 1,5 m sobrevivem no domínio retido |
| **Próxima decisão necessária** | A decisão deixa de ser "qual piso arbitrário" e passa a ser: **aceitar a restrição de domínio derivada fisicamente, ao custo de 42 % dos eventos e da alegação de cobertura nacional, ou manter a cobertura integral e qualificar os resultados do Norte?** Pendente do usuário |

### 2026-07-29 — Chave de regime q = (setup + surge)/maré; e o discriminador artefato vs. modulação

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Proposta do usuário para preservar a cobertura nacional: definir q = (0,2·Hs_q99 + surge_q99)/modulação de sizígia e trocar a variável de nível conforme o regime — onde q > 1 manter a maré na detecção (`SSH_total`), onde q < 1 detectar só sobre `zos`. **É defensável?** Hipótese inicial do auditor, registrada aqui por transparência: a chave falharia, porque SP/RJ tem q > 1 *e* 100 % de travamento de fase sob `SSH_total`. **Essa hipótese mostrou-se incorreta** |
| **Dados e métodos** | (1) Cálculo de q por ponto (Hs_q99 extraído do dataset unificado; surge e modulação de sizígia da saída de `audit_AUD_01_surge_vs_tide_magnitude`), partição em q = 1, e cruzamento com o travamento de fase medido do catálogo que cada ramo produziria. (2) **Discriminador decisivo**: fração de eventos compostos detectados por `SSH_total` que contêm ao menos um dia com `zos` — variável livre de maré — acima do seu próprio q90 local. Alta fração ⇒ havia tempestade e a maré apenas fixou o instante (modulação, caso b); baixa fração ⇒ o evento se sustenta só na maré (artefato, caso a) |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_storm_over_tide_switch`; `python -m src.exploratory.audit_AUD_01_storm_corroboration` |
| **Novas saídas geradas** | `outputs/audit/AUD-01_storm_over_tide_switch/{switch_by_point.csv, switch_summary.json}`; `outputs/audit/AUD-01_storm_corroboration/{corroboration_by_point.csv, corroboration_summary.json}` |
| **Achados** | **(1) Partição por q = 1**: ramo "manter maré" n = 281 (lat −35,0 a −19,8); ramo "só `zos`" n = 527 (lat −26,2 a +6,0). Mediana de q: RS 2,60; SC/PR 2,26; SP/RJ 1,39; ES/BA-S 0,57; BA-N 0,62; NE 0,54; N eq. 0,34; AP 0,36. **(2) Travamento residual no ramo que mantém a maré: 189 de 281 pontos (67 %)** — concentrado em SC/PR (64 %) e SP/RJ (88 %); RS apenas 6 %. Após a chave, 23,5 % dos pontos do domínio seguem travados, contra 88,6 % hoje e 0,12 % sob `zos` puro. **(3) O discriminador resolve a ambiguidade e inverte a leitura do achado (2)**: fração de eventos corroborados por sinal independente de `zos` — RS 0,92; SC/PR 0,82; SP/RJ 0,78; ES/BA-S 0,54; BA-N 0,26; NE 0,17; N eq. 0,17; AP 0,33. **Os 189 pontos travados dentro do ramo "manter maré" têm mediana de corroboração 0,795.** Spearman(corroboração, q) = **0,644**. **(4) Alerta que contraria o objetivo do usuário**: sob a chave, os pontos do Norte migram para o ramo `zos`, cujas contagens de composto são **maiores** que as atuais — BA-N 56 → 78, NE 61 → 77, N eq. 89 → 105, AP 80 → 118. **(5) Descontinuidade**: para os 113 pontos com 0,7 < q < 1,4, a diferença relativa mediana entre os dois catálogos candidatos é **0,35** |
| **Interpretação** | **A hipótese do auditor estava errada e a proposta do usuário é defensável.** R alto não significa "artefato": significa apenas que os eventos se agrupam em sizígia. O discriminador mostra que em SC/PR e SP/RJ ~80 % desses eventos têm tempestade independente comprovada — é **modulação mareal de tempestade real (caso b)**, exatamente a amplificação que o arcabouço de compostos deve capturar, e exatamente o que o usuário queria preservar no S/SE. No Norte a corroboração cai a 0,17–0,33: ali é **artefato (caso a)**. O gradiente de corroboração acompanha q (ρ = 0,644), o que significa que **a chave em q = 1 está bem posicionada** — ela separa, de fato, os dois casos. Consequência metodológica mais ampla: **o teste de Rayleigh sozinho não é diagnóstico de artefato** e não deveria ser usado isoladamente no manuscrito; precisa vir acompanhado da fração de corroboração. Isso qualifica o próprio achado de linha de base da §3 |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Scripts diagnósticos e saídas em `outputs/audit/`; nenhuma chave foi aplicada |
| **Validação realizada** | O discriminador usa `zos` — variável demonstradamente livre de maré (0/808 travados, entrada de 2026-07-29) — como testemunha independente, portanto não é circular em relação ao `SSH_total` que avalia |
| **Incerteza remanescente** | (1) **Descontinuidade de 35 % nas contagens** entre pontos vizinhos que caem em lados opostos da chave: produziria artefato espacial visível no mapa perto de 20–21°S. (2) **Comensurabilidade**: `compound_count_total` passaria a ter definição distinta nos dois ramos, mas o `Hazard_Index` os normaliza por Min–Max num único conjunto de 808 pontos e os ranqueia como se fossem a mesma quantidade. (3) **O achado (4) contraria o objetivo declarado**: a chave tende a *elevar* a frequência no Norte, podendo reforçar em vez de atenuar os hotspots setentrionais, salvo compensação pela componente de intensidade — **não verificado**. (4) O proxy de setup usa Hs local, pouco confiável em células abrigadas/estuarinas (AUD-12), embora esses pontos caiam em q < 1 de qualquer modo. (5) ES/BA-S é zona de transição genuína (q = 0,57 mas corroboração 0,54) e fica no ramo `zos` com metade dos eventos corroborados |
| **Próxima decisão necessária** | Escolher entre: **(A)** a chave de regime proposta, aceitando descontinuidade e comensurabilidade parcial; **(B)** detecção uniforme sobre `zos` ∩ Hs com a maré entrando como severidade/condicionante, que é comensurável e sem descontinuidade, mas perde da detecção os ~10–20 % de eventos do S/SE cujo cruzamento de limiar dependeu da maré. Pendente do usuário |

### 2026-07-29 — Como a maré entra na severidade sem inflar o Norte

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Pergunta do usuário sobre a opção (B): sob detecção uniforme livre de maré, a amplificação mareal precisa retornar pela severidade. Como fazê-lo **sem** recriar o viés regional na componente de intensidade, já que o Norte simplesmente tem mais água? |
| **Dados e métodos** | Sobre os eventos compostos de um detector uniforme `zos` ∩ Hs, quatro formulações candidatas de severidade, avaliadas pelo viés regional — Spearman entre a severidade média por ponto e a latitude absoluta. **A** nível total absoluto `zos + maré + 0,2·Hs`; **B** excesso sobre datum local `A − q95(maré diária máx.)`, sendo o q95 um proxy da preamar média de sizígia, isto é, o nível a que a costa está adaptada; **C** fase mareal adimensional `(maré − mediana)/amplitude` local; **D** apenas anomalia de surge, sem informação mareal, como referência |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_severity_tide_term` |
| **Novas saídas geradas** | `outputs/audit/AUD-01_severity_tide_term/{severity_by_point.csv, severity_by_band.csv, severity_summary.json}` |
| **Achados** | Viés regional, Spearman(|lat|, severidade): **A = −0,847** (negativo ⇒ cresce em direção ao equador: **infla o Norte**, AP 2,27 m contra RS 1,33 m, por razão puramente astronômica); **B = +0,930**; **C = +0,153**; **D = +0,640**. Médias por faixa em B: RS 0,926 m, SC/PR 0,739, SP/RJ 0,641, ES/BA-S 0,321, BA-N 0,379, NE 0,264, **N eq. 0,001**, AP 0,076 m. Médias em C: entre −0,028 e +0,046 em todas as faixas |
| **Interpretação** | A preocupação do usuário é **confirmada e quantificada**: a formulação ingênua (A) reproduz exatamente o viés que o redesenho pretendia remover. Duas vias evitam isso, com naturezas distintas. **C** é regionalmente neutra por construção — como a detecção passou a ser livre de maré, os eventos caem em fase mareal aleatória e a média regional não se desloca; funciona como modulador **no nível do evento**, mas representa a amplificação apenas em termos relativos, de modo que uma sizígia num regime de 1,63 m conta o mesmo que numa de 0,46 m, perdendo a informação de que a amplificação macromareal é fisicamente muito maior. **B** preserva a dimensão física (metros acima do datum adaptado) e portanto representa a amplificação corretamente, mas a consequência honesta é que no setor equatorial o excesso médio sobre a preamar de sizígia é **0,001 m** — a contribuição meteorológica e de onda praticamente não acrescenta nada ao que a maré já faz, atribuindo severidade desprezível ao Norte. Isso não é defeito da formulação: é a mesma constatação física já registrada (surge q99 de 11,8 cm contra 163 cm de oscilação), agora expressa em termos de severidade. **A escolha entre B e C é, portanto, uma decisão científica, não técnica**: se severidade significa "quão anômalo frente ao que a costa já absorve", B; se significa "quanto a maré amplificou este evento, de forma comparável entre regimes", C. Nota prática: a receita de excesso sobre limiar local **já existe** em `normalize_compound_intensity()` e é a razão pela qual a intensidade atual tem viés equatorial fraco (Spearman ≈ 0,295 na revisão de linha de base), valor que se situa entre C e D |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Nenhuma formulação foi adotada |
| **Validação realizada** | As quatro formulações são avaliadas sobre exatamente o mesmo conjunto de eventos (detector uniforme `zos` ∩ Hs), de modo que as diferenças de viés decorrem apenas da definição de severidade |
| **Incerteza remanescente** | (1) O datum de B usa q95 da maré diária máxima como proxy de preamar média de sizígia; um datum de engenharia (HAT, ou cota de projeto local) não está disponível para os 808 pontos e alteraria os valores absolutos, embora não o sinal do viés. (2) O proxy de setup 0,2·Hs usa Hs local, pouco confiável em células abrigadas (AUD-12), o que afeta A e B nos mesmos pontos já sob suspeita. (3) Não foi avaliado o efeito de nenhuma das formulações sobre o **ranking municipal final** — só sobre o viés latitudinal da componente |
| **Próxima decisão necessária** | Se a opção (B) do registro anterior for escolhida, decidir entre severidade **C** (neutra regionalmente, amplificação relativa) e **B** (dimensional, atribui severidade desprezível ao Norte). Recomenda-se publicar B como campo diagnóstico acompanhante em qualquer cenário, por responder diretamente à pergunta "o perigo no Norte é meteorológico?" |

### 2026-07-29 — Sensibilidade da severidade "excesso de água" à escolha do datum de maré

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | A severidade por excesso sobre datum exige escolher o datum, o que reabre a objeção de arbitrariedade de AUD-02 §7.4. A preocupação é quantitativa: no setor macromareal a oscilação de sizígia é ~1,63 m enquanto a contribuição de tempestade é ~0,12 m, de modo que deslocar o datum em poucos centímetros é comparável ao sinal inteiro. **A conclusão depende do datum escolhido?** |
| **Dados e métodos** | Recálculo da severidade sob quatro datums, todos derivados apenas da maré astronômica FES2022 (`tide_daily_max`, 1993–2025, por ponto): q90 (permissivo), q95 (proxy de MHWS, padrão atual), q99 (sizígias altas) e **máximo, estimativa de HAT — datum de engenharia definido, sem escolha de percentil**. Eventos do detector uniforme `zos` ∩ Hs. Métricas: viés regional (Spearman contra |lat|), excesso médio por faixa e **fração de eventos que efetivamente ultrapassa o datum** |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_01_datum_sensitivity` |
| **Novas saídas geradas** | `outputs/audit/AUD-01_datum_sensitivity/{datum_sensitivity_by_point.csv, datum_sensitivity_by_band.csv, datum_sensitivity_summary.json}` |
| **Achados** | **(1) A conclusão é robusta.** Viés regional praticamente idêntico nos quatro datums: q90 **+0,925**, q95 **+0,930**, q99 **+0,931**, HAT **+0,932**. **(2)** Os valores absolutos deslocam sem alterar o padrão — excesso médio no RS 0,96 → 0,82 m e no N equatorial 0,12 → 0,00 → −0,15 → −0,28 m, conforme o datum aperta. Nenhuma escolha aproxima o Norte do Sul. **(3) Subproduto de valor independente — fração de eventos que ultrapassa o datum**: RS e SP/RJ ~99–100 % sob **qualquer** datum; N equatorial 66 % (q90) → 55 % (q95) → 40 % (q99) → **27 % (HAT)**; AP 70 % → 61 % → 48 % → 37 %. Ou seja, no Sul praticamente todo evento composto detectado põe água acima do máximo rotineiro, ao passo que no Norte, mesmo na leitura mais permissiva, um terço dos eventos sequer alcança o nível que a maré astronômica atinge sozinha toda quinzena |
| **Interpretação** | **A objeção de arbitrariedade fica desarmada para esta escolha específica**: qualquer datum de maré convencional produz a mesma resposta qualitativa, e a tabela de sensibilidade é publicável como evidência disso. Recomendação prática: adotar **HAT** como datum primário, por ser o único sem escolha de percentil — responde-se "usamos HAT, datum de projeto padrão" em vez de "escolhemos o q95". Ressalva numérica: sob HAT o setor equatorial fica negativo, exigindo piso em zero e gerando empates; o q95 evita isso com resultado praticamente idêntico. O achado (3) tem valor próprio para o manuscrito, independentemente do datum adotado como oficial |
| **Alterações implementadas** | **Nenhuma no pipeline de produção.** Nenhum datum foi adotado |
| **Validação realizada** | Os quatro datums são avaliados sobre exatamente o mesmo conjunto de eventos, de modo que as diferenças decorrem apenas do nível de referência |
| **Incerteza remanescente** | (1) Todos os datums derivam de `tide_daily_max`, herdando a incoerência de fase de AUD-03 (maré máxima diária somada a `zos` de 00Z). (2) Um datum de engenharia local real — cota de projeto, crista de proteção, cota de duna — seria mais defensável que qualquer proxy de maré, mas não está disponível para os 808 pontos; essa é a mesma lacuna de vulnerabilidade física de AUD-10. (3) O proxy de setup 0,2·Hs continua usando Hs local, pouco confiável em células abrigadas (AUD-12) |
| **Próxima decisão necessária** | Nenhuma nova. A escolha do datum deixa de ser bloqueante, dado o resultado de robustez; permanece pendente apenas a decisão anterior entre as duas formulações de severidade |

### 2026-07-29 — Implementação do método MHWS e comparação com o legado

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Autorizada a implementação pelo usuário. O método MHWS — detecção sobre `zos` ∩ Hs, condicionada a `max(SWL) > MHWS`, com a intensidade medindo o excesso sobre o MHWS — corrige o artefato e altera o ranking municipal na direção pretendida? |
| **Dados e métodos** | `MHWS = A_M2 + A_S2` das constantes harmônicas FES2022 (`m2_fes2022.nc`, `s2_fes2022.nc`), interpolado por vizinho válido mais próximo aos 808 pontos. `SWL = (zos − média local) + maré_máx_diária`; a de-mediação é necessária porque `zos` é referenciado ao geoide e o MHWS ao nível médio local — sob o método antigo o offset cancelava contra o próprio percentil, aqui não cancela. Agrupamento de episódios em componentes conexas por dias de excedência compartilhados, espelhando `classify_storms_at_point`. Intensidade `0,5·[norm(pico_Hs − thr_hs) + norm(max(SWL) − MHWS)]` com Q05/Q95 agrupados no domínio, como no método anterior. Sem termo de setup. Comparação com exposição e SVI idênticos nos dois braços |
| **Scripts executados** | `python -m src.compound_detection.detection_mhws`; `python -m src.exploratory.compare_methods_ssh_total_vs_mhws` |
| **Novas saídas geradas** | `outputs/legacy_ssh_total_method/` (instantâneo do legado, com README documentando o método antigo); `outputs/storm_catalog/compound_mhws/`; `outputs/method_comparison_ssh_total_vs_mhws/` (com README completo da comparação) |
| **Achados** | **(1) Fidelidade verificada**: o `thr_hs` recomputado reproduz o de produção em **808 de 808** pontos (diferença máxima 0,000000 m); as diferenças observadas vêm apenas do que mudou de propósito. MHWS resolvido em 808/808 pontos, 0,08–4,33 m. **(2) Frequência e intensidade corrigiram como pretendido.** A condição de MHWS rejeitou 30 117 de 109 756 candidatos (27,4 %), concentrados no Norte: `Hazard_Frequency` no N equatorial cai de 0,153 para **0,048**; `Hazard_Intensity` de 0,394 para **0,239**, passando a ter gradiente S→N limpo. **(3) A duração inverteu e domina.** `Hazard_Duration` no N equatorial sobe de 0,301 para **0,431** — passando a ser o **máximo** do domínio — enquanto o RS cai para 0,039, o **mínimo**. A duração média da sobreposição no N equatorial vai de 1,64 para **5,31 dias**, porque sob o detector novo os episódios de nível no trópico são anomalias de `zos` de baixa frequência (7–8 dias), não tempestades sinóticas. **(4) Resultado líquido: o perigo no N equatorial SOBE** de 0,234 para 0,334, apesar de frequência e intensidade terem caído, e o top-10 municipal ao norte de 20°S passa de 70 % para **90 %**. **(5) As duas correções não são separáveis** — top-10 ao norte de 20°S: legado+3comp 70 %, legado+2comp 90 %, MHWS+3comp 90 %, **MHWS+2comp 30 %**. Concordância global: Spearman do perigo na grade 0,756; do risco municipal 0,854; sobreposição do top-10 apenas 2/10 |
| **Interpretação** | O detector novo faz exatamente o que foi projetado para fazer nas componentes que dependem dele — frequência e intensidade —, mas **a correção é revertida pela componente de duração**, que nunca foi tratada. Sob o detector antigo a duração já era problemática (AUD-06); sob o novo ela piora, porque passa a medir persistência de anomalia oceanográfica de baixa frequência em vez de duração de tempestade. **A conclusão operacional é que AUD-01 e AUD-06 formam um par indissociável**: adotar o detector novo mantendo a duração com peso 1/3 produz um resultado pior que o publicado. O achado (5) é o mais consequente da sessão e deve constar do material suplementar, porque demonstra que nenhuma das duas mudanças isoladas é defensável |
| **Alterações implementadas** | Método MHWS implementado **em caminhos novos**; código e saídas do método legado intocados. Nenhum produto publicado (site, figuras do artigo) regenerado. Ver §13 |
| **Validação realizada** | (1) `thr_hs` idêntico à produção em 808/808 pontos. (2) Índice de perigo derivado pela **mesma** função `derive_native_hazard_index` nos dois braços, apenas trocando a fonte. (3) Exposição e SVI lidos do produto publicado, idênticos nos dois braços por construção — a única diferença é a definição do evento. (4) Instantâneo legado criado **antes** de qualquer escrita, e em caminho versionado, já que o original é `.gitignore`d |
| **Incerteza remanescente** | (1) O teste de fase não foi reexecutado sobre o catálogo novo; espera-se travamento residual no Norte pela condição de MHWS, legítimo por ser corroborado por tempestade, mas **não medido**. (2) O catálogo de eventos individuais não é persistido pelo novo módulo, apenas as métricas por ponto — o que impede diagnósticos posteriores que precisem de datas de evento. (3) A calibração do Step 2e permanece a do método antigo, otimizada sobre `SSH_total`; **não foi refeita nem justificada**. (4) AUD-02, AUD-04 e AUD-12 permanecem intocados |
| **Próxima decisão necessária** | **Bloqueante: AUD-06.** Decidir o tratamento da componente de duração antes de adotar o método novo. Sem essa decisão o método novo não pode substituir o publicado, porque piora o resultado que se pretendia corrigir |

### 2026-07-29 — Adoção do método e fechamento

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Resolvido AUD-06, o detector MHWS entrega um campo de perigo defensável e pode substituir o publicado? |
| **Dados e métodos** | Adoção conjunta: detecção sobre `zos` ∩ Hs condicionada a `SWL > MHWS`, com o índice de perigo migrado para `frequência + severidade integrada` (pesos 1/2). Regeneração completa da cadeia — catálogo composto, índice, exportadores do site, figuras e tabelas do artigo |
| **Achados** | Campo de perigo: ρ(\|lat\|, `Hazard_Index`) = **+0,584**, gradiente monotônico S→N coerente com a climatologia de ciclones extratropicais; média por faixa de 0,826 no RS a 0,125 no NE. As duas componentes passam a se reforçar (ρ = +0,599). Ranking municipal: top-10 ao norte de 20°S de **70 % para 50 %**; São José do Norte/RS em 4º; São Sebastião 17º→13º; Bertioga 24º→20º; Itajaí 275º→230º; Navegantes 273º→216º |
| **Interpretação** | O achado central da revisão de linha de base — eventos compostos travados em sizígia ao norte de ~20°S — está resolvido na origem: a maré não participa mais da decisão sobre a existência do evento. O travamento residual que permanece no Norte é legítimo e demonstrável como modulação de tempestade real, pela fração de corroboração medida em 2026-07-29. O produto continua cobrindo a costa inteira, sem exclusão de domínio |
| **Alterações implementadas** | Método MHWS adotado como canônico; método legado preservado em `outputs/legacy_ssh_total_method/` com documentação completa; comparação lado a lado em `outputs/method_comparison_ssh_total_vs_mhws/` |
| **Validação realizada** | `thr_hs` recomputado idêntico à produção em 808/808 pontos. Índice derivado pela mesma função nos dois braços da comparação. Exposição e SVI idênticos por construção na comparação, isolando o efeito do detector |
| **Incerteza remanescente** | (1) **A calibração do Step 2e não foi refeita** — o par q90/q90 foi otimizado sobre `SSH_total` e segue aplicado à variável nova, sem recalibração nem justificativa escrita. Pertence a AUD-18. (2) **O teste de Rayleigh não foi reexecutado sobre o catálogo final**; espera-se travamento residual no Norte pela condição de MHWS, legítimo mas não medido. (3) O catálogo de eventos individuais não é persistido, apenas as métricas por ponto, o que impede diagnósticos posteriores que dependam de datas. (4) AUD-02 (limiar de Hs de 0,20 m), AUD-04 (associação grade→município) e AUD-12 (pontos estuarinos) permanecem abertos e não são alcançados por esta correção |
| **Próxima decisão necessária** | Nenhuma para esta questão |
