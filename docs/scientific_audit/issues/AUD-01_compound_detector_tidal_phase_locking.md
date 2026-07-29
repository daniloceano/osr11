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
| **Status** | `em-investigacao` |
| **Desfecho** | — |
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
- [ ] A razão `var(maré)/var(SSH_total)` está calculada por ponto e sua relação
      com R está quantificada (correlação e gráfico de dispersão).
- [ ] Está definido e documentado um **domínio de validade** explícito do
      detector composto — seja por latitude, seja por um critério físico
      (ex.: amplitude de maré, razão de variâncias) — com o limiar justificado
      pelo diagnóstico, não escolhido a olho.
- [ ] Uma das três decisões está tomada, documentada e implementada:
      (a) restringir a análise composta ao domínio validado;
      (b) adotar um detector de nível baseado em anomalia não-maré;
      (c) manter o detector atual e **renomear/reenquadrar** a quantidade no
      manuscrito, com o diagnóstico de fase publicado como material suplementar.
- [ ] Se (c) for a escolha, o manuscrito contém uma declaração explícita de que
      a coocorrência ao norte de ~20°S é modulada pelo ciclo de sizígia, e a
      figura de diagnóstico está incluída.
- [ ] Os produtos a jusante da §12 estão regenerados e verificados, ou está
      registrado por escrito que nenhuma regeneração é necessária e por quê.

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
| — | — | — | — | *nenhuma alteração até o momento* |

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
