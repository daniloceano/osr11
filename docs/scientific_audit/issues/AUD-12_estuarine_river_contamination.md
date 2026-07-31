# AUD-12 — Contaminação estuarina e fluvial dos pontos de grade do estuário amazônico

| Campo | Valor |
|-------|-------|
| **ID** | AUD-12 |
| **Tipo** | `qualidade-dados` |
| **Componente** | perigo |
| **Etapa do fluxo** | Step 2a (seleção de pontos costeiros) → Step 3.1/3.2 |
| **Afeta** | dados, interpretação, saídas |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim, salvo qualificação — dois municípios do top-10 de risco dependem desses pontos |
| **Status** | `resolvido` |
| **Desfecho** | `resultado-validado-mantido` |
| **Depende de** | AUD-01 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-02, AUD-03, AUD-04, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.1(e), §5, §8 item 10 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 |

---

## 1. Problema

Pontos de grade situados **dentro do estuário amazônico** entram no catálogo de
perigo como se fossem pontos oceânicos costeiros. Nessas células:

- o `zos` do GLORYS12 carrega o ciclo sazonal de descarga do Amazonas, não apenas
  a sobrelevação meteorológica;
- o modelo global não resolve a dinâmica de canal, a pororoca, nem a estratificação
  salina do estuário;
- o WAVERYS não é válido em águas interiores estreitas, o que se reflete em
  limiares de Hs de 0,20 a 0,51 m.

Dois municípios do **top-10 de risco** — Macapá/AP (4º) e Chaves/PA (8º) —
recebem seu perigo de pontos assim.

## 2. Por que importa cientificamente

Se o `zos` nesses pontos é dominado pelo hidrograma do Amazonas, então:

- os "extremos de nível" detectados coincidem com a cheia sazonal (março–junho),
  não com eventos de tempestade;
- combinados com o travamento de sizígia (AUD-01) e com limiares de onda
  irrisórios (AUD-02), os "eventos compostos" ali não têm nenhuma das três
  propriedades que o trabalho declara medir;
- a inundação real nesses municípios é fluvial e mareal, não composta
  onda–sobrelevação. Atribuí-la ao mecanismo estudado é um erro de atribuição
  causal que aparecerá no top-10 do artigo.

## 3. Evidência original

De `outputs/storm_catalog/compound/compound_metrics.csv` e
`site/public/data/risk_index_municipalities.geojson`:

| Município | Ponto de grade | Localização | `thr_hs_abs` (m) | `thr_ssh_total_abs` (m) | `compound_count_total` | `mean_compound_intensity_norm` |
|---|---|---|---|---|---|---|
| **Macapá/AP** | (0,8; −50,2) | Dentro do estuário amazônico, canal norte | **0,51** | 3,381 | 118 | 0,3548 |
| **Chaves/PA** | (0,0; −50,4) | Foz do Amazonas / norte de Marajó | **0,24** | 2,338 | 127 | **0,2027** |
| Salvaterra/PA | (−0,8; −48,4) | Baía de Marajó | 0,72 | 2,970 | 86 | 0,3437 |
| Vigia/PA | (−1,4; −48,6) | Baía do Guajará | **0,20** | 2,917 | 100 | 0,3218 |
| Colares/PA | (−1,4; −48,6) | idem (mesmo ponto) | 0,20 | 2,917 | 100 | 0,3218 |

Indicadores adicionais:

- O **mínimo global** de `mean_compound_intensity_norm` (0,1691) está em
  (0,4; −50,0) — dentro do estuário. A normalização por excesso sobre o limiar
  local está funcionando (AUD-02 §7.2) e sinaliza que esses pontos têm eventos
  fracos.
- O **máximo global** de `mean_overlap_duration` (2,51 d) está em (3,4; −50,8) —
  offshore do Amapá, na pluma amazônica.
- Vigia/PA está a **61,1 km** do ponto que recebe (AUD-04).
- Chaves/PA tem área de 12 568 km² com 19 848 habitantes, e recebe
  `SVI_Coast_2022` = **100,000** (o máximo absoluto) — ou seja, seu lugar no
  top-10 é conduzido por SVI, com o perigo apenas viabilizando o produto
  geométrico.

**Ainda não foi feito:** nenhuma análise do ciclo sazonal do `zos` nesses pontos,
nem comparação com o hidrograma do Amazonas. A contaminação é **hipótese
fundamentada**, não fato demonstrado.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/02_threshold_calibration/01_exploratory_data_analysis/coastal.py` | seleção de pontos costeiros | Onde os 808 pontos foram definidos, via linha de costa Natural Earth |
| `src/02_threshold_calibration/01_exploratory_data_analysis/main.py` | orquestrador do Step 2a | — |
| `src/03_storm_catalog_generation/shared/catalog_utils.py` | `build_grid_index()` | Indexação dos pontos no Step 3 |
| `src/exploratory/longterm_mean_zos_map.py` | — | **Já existe**: mapa de `zos` médio de longo prazo, útil para detectar o gradiente estuarino |
| `src/exploratory/make_exploratory_zos_mean_coastal_band_map.py` | — | Mapa de `zos` médio na faixa costeira |
| `src/exploratory/article_fig03_zos_hatched.py` | — | Figura de `zos` com hachura |

### Dados e saídas

- `outputs/exploratory_zos_mean_coastal_band_map/` e
  `outputs/exploratory_fig03_zos_hatched_points/` — saídas existentes que já
  tocam neste problema.
- `outputs/article_figures/supplementary_temporal_mean_zos_within_200km_coast.png`
  — figura suplementar já produzida.
- `data/external/ana_bho/` — base hidrográfica ottocodificada da ANA, **já
  presente no repositório**; fonte natural para delimitar domínios estuarinos e
  identificar desembocaduras.

### Figuras afetadas

- `outputs/article_figures/supplementary_integrated_risk_zooms.png` — painel B
  (PA a PI) é inteiramente o setor afetado.
- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.*`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Todo ponto de grade selecionado pela proximidade à linha de costa Natural Earth entra no catálogo, sem filtro de validade oceânica |
| **Pretendido/conceitual** | Pontos que representem o forçante **oceânico** costeiro: onda de mar aberto e nível de plataforma |

## 6. Divergência documentação ↔ implementação ↔ saídas

O `README.md` §2a descreve a seleção como "Coastal grid-point selection via
Natural Earth coastline", sem critério de validade oceanográfica. Não há
divergência entre documentação e código; a lacuna é a **ausência de um critério
de exclusão** para águas interiores.

## 7. Explicações alternativas plausíveis

1. **A contaminação pode ser pequena.** O `zos` do GLORYS12 é uma anomalia de
   nível; o modelo pode representar razoavelmente o efeito estérico e barotrópico
   da descarga sem que isso domine a variância no ponto. **Verificável.**
2. **A normalização por excesso sobre o limiar local já mitiga o problema.**
   Chaves tem intensidade 0,203, quase o mínimo do domínio — o método está
   sinalizando corretamente que os eventos ali são fracos. O que não é mitigado é
   a **frequência**.
3. **Os pontos podem ser oceanograficamente válidos.** A plataforma amazônica é
   ampla e rasa; pontos a 0,8°N e 50,2°W podem estar em água aberta da plataforma
   interna, não em canal estuarino. Verificável com batimetria.
4. **A inundação nesses municípios é real.** Macapá e Chaves de fato sofrem
   inundação costeira. O problema é de **atribuição de mecanismo**, não de
   existência do risco. Isso pode ser resolvido por reenquadramento (ver AUD-01
   §7.1).
5. **A descarga fluvial é um co-fator legítimo de inundação composta.** A
   literatura de compostos costeiros (Zscheischler et al. 2020, já citado no
   código) inclui explicitamente descarga fluvial + nível do mar como um tipo de
   evento composto. Se o trabalho quisesse capturar isso, teria de fazê-lo
   deliberadamente, com uma variável de vazão.

## 8. Diagnósticos propostos

1. **Ciclo sazonal do `zos`** nos pontos suspeitos, comparado com pontos de
   plataforma aberta na mesma latitude e com o hidrograma do Amazonas (dados da
   ANA, estação Óbidos). *Saída esperada:* se o `zos` tiver máximo em maio–junho e
   correlação alta com a vazão, a contaminação está demonstrada.
2. **Classificação de validade oceânica de todos os 808 pontos**: distância à
   costa, profundidade, distância à desembocadura mais próxima (usando
   `data/external/ana_bho/`), e largura do corpo d'água. Produzir uma máscara de
   pontos "oceânicos", "estuarinos" e "interiores".
3. **Recalcular o `Hazard_Index` excluindo os pontos estuarinos** e medir o efeito
   no ranking municipal — quais municípios perdem perigo, e para que ponto
   passariam a ser associados (interage com AUD-04).
4. **Verificar a validade do WAVERYS** nesses pontos: fração de células vizinhas
   com dado válido, e comparação de `thr_hs_abs` com o clima de ondas offshore da
   plataforma Pará-Maranhão.
5. **Reutilizar as figuras existentes** (`longterm_mean_zos_map.py`,
   `make_exploratory_zos_mean_coastal_band_map.py`) para inspecionar o gradiente
   de `zos` médio entre estuário e plataforma.

## 9. Critérios objetivos de resolução

- [x] Existe uma classificação versionada de validade oceânica dos 808 pontos,
      com critério explícito e reproduzível.
      *`outputs/audit/AUD-12_estuarine_contamination/point_diagnostics.csv` —
      808 linhas com máximo, q70, q90 e q99 de Hₛ, q99 de `zos`, HAT, elevação
      do fundo (ETOPO 2022), fração de variância sazonal do `zos`, e acoplamento
      com o oceano aberto (bruto e sem ciclo anual). Reprodutível pelo script
      nomeado na §14. É a base quantitativa da classificação; **não** foi
      convertida em máscara categórica, porque nenhum corte se justificou.*
- [x] A hipótese de contaminação por descarga está **testada** — não apenas
      afirmada — com correlação reportada. *Testada e **não sustentada**: ver
      §14. A correlação de anomalia com o oceano aberto nos seis pontos
      questionados é 0,758–0,929 (mediana 0,827), indistinguível dos outros 197
      pontos ao norte de 2° S (mediana 0,833).*
- [x] Está decidido e justificado: manter os pontos estuarinos, excluí-los, ou
      marcá-los com ressalva no produto. **Decidido pelo pesquisador em
      2026-07-31: manter todos os pontos, sem filtro e sem ressalva por
      município.** Justificativa registrada na §14, entrada de decisão.
- [x] ~~Se mantidos, Macapá e Chaves têm interpretação explícita no
      manuscrito~~ — **critério dispensado deliberadamente pelo pesquisador em
      2026-07-31**, e substituído. A razão está registrada na §14: dadas as
      incertezas de escala espacial das fontes (GLORYS12, WAVERYS, ETOPO) e as
      demais incertezas do encadeamento, vieses pontuais são esperados e não
      justificam parágrafo dedicado a municípios individuais. Em lugar disso o
      manuscrito trará (a) a declaração geral de incerteza de escala e (b) a
      recomendação de trabalho futuro com modelagem de alta resolução em grade
      não estruturada. **Este critério não foi satisfeito; foi retirado, com
      justificativa e autoria registradas.**
- [x] Se excluídos, os municípios órfãos foram reassociados (AUD-04) e o efeito
      no ranking está reportado. *Não se aplica sob a recomendação de manter. O
      efeito de cada exclusão candidata **está** reportado (§14), incluindo os
      municípios que ficariam órfãos.*
- [ ] A validade do WAVERYS nos pontos de `thr_hs` < 1 m está avaliada (comum com
      AUD-02, diagnóstico 4). *Parcial: os percentis e o máximo de Hₛ estão
      medidos em todos os 808 pontos, e nenhum tem `max(Hₛ) < 0,5 m`. Uma
      avaliação da **validade do modelo de ondas** em si (fração de células
      vizinhas válidas, comparação com o clima de ondas offshore) não foi feita
      e permanece com AUD-02.*

## 10. Riscos de alteração prematura

- **Excluir pontos estuarinos** deixa municípios sem associação de perigo e força
  reassociação; a interação com AUD-04 precisa ser resolvida junto.
- **Excluir pontos com base no resultado que produzem** é seleção. O critério de
  exclusão deve ser geográfico e físico, definido antes de ver o efeito.
- Alguns desses pontos podem ser os **únicos** disponíveis para municípios do
  estuário; excluí-los equivale a excluir os municípios do estudo, o que é uma
  decisão de escopo, não técnica (ver AUD-15).

## 11. Condições sob as quais o resultado atual pode ser mantido

Os pontos podem ser mantidos se:

1. O diagnóstico 1 mostrar que a contaminação por descarga é pequena
   (ex.: correlação `zos` × vazão abaixo de 0,3);
2. O manuscrito declarar que os municípios do estuário amazônico recebem perigo
   de pontos estuarinos, com as limitações do GLORYS12 e do WAVERYS ali;
3. AUD-01 e AUD-02 tiverem desfecho compatível — os três problemas coexistem
   nesses pontos e resolver apenas um não os torna defensáveis.

## 12. Produtos a jusante que exigiriam regeneração

Se pontos forem excluídos, é preciso reprocessar a partir do catálogo:

```bash
python -m src.03_storm_catalog_generation.hazard_characterization --module all
python -m src.site.export_coastal_hazard_data
python -m src.site.export_risk_index_data
# figuras: cadeia de AUD-04 §12
```

Se apenas houver classificação e declaração: apenas produtos novos em
`outputs/audit/AUD-12_*/`.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(não commitado)* | `main` | `src/exploratory/audit_AUD_12_estuarine_contamination.py` (novo) | Diagnóstico. **Nenhum ponto excluído; nenhum valor numérico publicado alterado** |
| 2026-07-31 | *(não commitado)* | `main` | este registro; `ISSUE_TRACKER.md` | Registro da decisão de manter sem filtro e do desfecho `resultado-validado-mantido` |

## 14. Histórico de investigação

### 2026-07-31 — Reavaliação sob o método vigente: o diagnóstico anterior não se transfere

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | O diagnóstico de 2026-07-29 foi feito sobre o detector `SSH_total` a q90/q90, sem portão HAT. O método mudou nos três pontos. Os pontos questionados ainda contribuem eventos, perigo e posição municipal? A contaminação por descarga se sustenta? Algum filtro de exclusão se justifica? |
| **Dados e métodos** | `outputs/storm_catalog/compound_hat/compound_metrics_hat.csv` (808 pontos, método vigente), `outputs/legacy_ssh_total_method/hazard/compound_metrics.csv` (legado, para o antes/depois), `data/unified/metocean_brazil_unified_waverys_grid.nc` (séries brutas), `data/external/etopo2022/` (batimetria), `site/public/data/risk_index_municipalities.geojson` (associação e ranking). Teste de contaminação: como não há dado de vazão da ANA no repositório, a hipótese foi testada pelo **acoplamento com o oceano aberto** — correlação da série de `zos` do ponto com a de uma célula offshore na mesma latitude (2° a leste; para os pontos da costa norte, onde leste é terra, referência ao norte), calculada na série bruta e depois de remover o ciclo anual médio, isolando a banda sinótica onde vive a sobrelevação meteorológica. Cinco cenários de exclusão avaliados como sensibilidade, com o risco municipal reconstruído do zero em cada um |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_12_estuarine_contamination` |
| **Novas saídas geradas** | `outputs/audit/AUD-12_estuarine_contamination/{point_diagnostics.csv, suspect_points.csv, low_wave_points.csv, municipal_dependence.csv, sensitivity_scenarios.csv, diagnosis_summary.json}` |
| **Achados** | (a) **A reconstrução do risco municipal confere com o publicado**: ρ = 1,000, max\|Δ\| = 3,4e-06, 280/280 municípios — as comparações abaixo são confiáveis. (b) **O portão HAT esvaziou os pontos questionados.** Contagem de eventos, legado → vigente: Macapá (0,8; −50,2) **118 → 1** (66 de 67 candidatos rejeitados); Chaves (0,0; −50,4) **127 → 7** (50 de 57 rejeitados); Salvaterra (−0,8; −48,4) **86 → 0** (28 de 28 rejeitados); Vigia/Colares (−1,4; −48,6) **100 → 2**; (0,4; −50,0) **147 → 3**; (3,4; −50,8) **59 → 1**. (c) **O top-10 já não depende deles.** Macapá era 4º e agora é **172º**; Chaves era 8º e agora é **94º**; Salvaterra 192º, Vigia 185º, Colares 188º. Nenhum município servido por ponto estuarino está entre os 50 primeiros. (d) **A contaminação por descarga não se sustenta na banda sinótica.** Correlação de anomalia com o oceano aberto: 0,758 (Macapá), 0,834 (Chaves), 0,893 (Salvaterra), 0,929 (Vigia/Colares), 0,786, 0,819 — mediana **0,827**, contra **0,833** nos outros 197 pontos ao norte de 2° S. Os pontos questionados são estatisticamente indistinguíveis dos vizinhos. A fração de variância sazonal do `zos` é 0,09–0,23 neles, **abaixo** da mediana 0,237 dos vizinhos. (e) **O teste do mês de pico não discrimina** e foi descartado: a fração de pontos cujo `zos` médio culmina em abril–junho é 0,37 no Norte e **1,00 ao sul de 25° S**, onde o Amazonas não tem influência — o ciclo estérico do Atlântico Sul também culmina no outono austral. (f) **O filtro de `max(Hₛ) < 0,5 m` é vazio no produto atual**: o mínimo de `max(Hₛ)` no domínio é **0,54 m**; **zero** pontos, zero eventos, zero municípios. O valor de 0,5 m do registro original vinha do **limiar** q90 do método superseded, não do máximo. (g) Aplicado à estatística que de fato varia, o filtro custa mais do que corrige: `q99(Hₛ) < 0,5 m` remove 8 pontos, 29 eventos e **silencia Chaves, Colares e Vigia**; `thr_hs(q70) < 0,5 m` remove 11 pontos, 31 eventos e silencia também Macapá. Todos os pontos removidos **têm** eventos aceitos pelo portão HAT — seriam falsos negativos, não artefatos. (h) Nenhum cenário muda o ranking: ρ = 1,000 e top-10 10/10 em todos, inclusive excluindo o Norte inteiro (203 pontos), que só desloca a mediana em 14 posições ao deixar 33 municípios órfãos |
| **Interpretação** | O problema que AUD-12 registrou foi **dissolvido pela mudança de método**, não por exclusão de pontos. O mecanismo era: `SSH_total` no q90 detectava a sizígia como extremo de nível, o que dava a esses pontos centenas de "eventos compostos" sem tempestade; o limiar de onda irrisório não filtrava nada. Com o nível segmentado em `zos` livre de maré e o portão exigindo `max(SWL) > HAT`, 95–100 % desses candidatos são rejeitados, e os municípios do estuário caíram do top-10 para a metade inferior do ranking. **Recomendação: não aplicar nenhum filtro.** O corte de 0,5 m não tem justificativa física (é vazio na estatística para a qual foi proposto), não tem estabilidade espacial verificável (não seleciona nada), e nas variantes em que morde ele remove pontos que carregam perigo detectado, silenciando quatro municípios sem alterar o ranking — ou seja, só custa cobertura. Excluir pontos com base no resultado que produzem também seria seleção, o que a §10 deste registro já advertia |
| **Alterações implementadas** | Nenhuma. Nenhum ponto excluído, nenhum produto regenerado |
| **Validação realizada** | (1) Reconstrução do risco municipal conferida contra o publicado (ρ = 1,000, max\|Δ\| = 3,4e-06, 280/280). (2) Bug de chave corrigido durante a sessão: o ponto da foz do Amazonas tem latitude −7,4e-13, que arredondava para a string `-0.0` e não casava com `0.0` do arquivo municipal, deixando Chaves espúriamente órfão; corrigido somando 0,0 para colapsar o zero negativo. (3) Denominador de comparação de ranking trocado pela reconstrução do próprio script, para que os deslocamentos não carreguem artefato de desempate |
| **Incerteza remanescente** | (1) **Sem dado de vazão.** O teste de contaminação é indireto: mede acoplamento com o oceano aberto, não correlação com o hidrograma do Amazonas. A série da estação de Óbidos (ANA) tornaria o teste direto e exigiria nova aquisição com proveniência. (2) A referência offshore usa deslocamento fixo de 2° (ou norte, quando leste é terra), o que não é uma definição de "plataforma aberta" e tem linha de base fortemente latitudinal — a comparação só é válida **dentro** do setor norte, que é como foi usada. (3) A elevação do fundo do ETOPO no ponto de Macapá é **+9,1 m**, isto é, a célula de grade cai sobre o que o ETOPO resolve como terra no complexo de ilhas do estuário; o WAVERYS ali tem dado, mas a representatividade da célula é questionável. Não é motivo suficiente para excluir um ponto que hoje contribui **um** evento, mas fica registrado. (4) A validade do WAVERYS em si nesses pontos não foi avaliada — permanece com AUD-02 |
| **Próxima decisão necessária** | Do pesquisador: registrar a decisão de **manter os pontos sem filtro**, e escrever a interpretação de Macapá e Chaves no manuscrito. Com essas duas, AUD-12 pode fechar como `resultado-validado-mantido` — o desfecho é que a preocupação foi testada e **superada pela mudança de método**, sem nova exclusão |


### 2026-07-31 — Decisão do pesquisador: manter sem filtro; fechamento

| Campo | Conteúdo |
|-------|----------|
| **Decisão** | **Manter todos os 808 pontos, sem nenhum filtro de exclusão.** Nenhum ponto estuarino é removido, nenhum recebe ressalva individual no produto |
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31, sobre os diagnósticos da entrada anterior |
| **Justificativa registrada** | Duas partes. A primeira é o diagnóstico: o portão HAT já esvaziou os pontos questionados (Macapá 118 → 1 evento, Chaves 127 → 7, Salvaterra 86 → 0), o top-10 deixou de depender deles (Macapá 4º → 172º, Chaves 8º → 94º), e a hipótese de contaminação por descarga não se sustentou (acoplamento sinótico com o oceano aberto 0,827 nos questionados contra 0,833 nos vizinhos). A segunda é de enquadramento, e é do pesquisador: **dadas as incertezas de escala espacial das fontes — GLORYS12 a 1/12°, WAVERYS a ~0,2°, ETOPO 2022 — e as demais incertezas acumuladas na cadeia, é esperado que o produto tenha vieses pontuais.** Isso é uma propriedade de um índice regional construído sobre reanálises globais, não um defeito a ser corrigido caso a caso. Aplicar um filtro para remover pontos incômodos seria seleção, e nesta base custaria cobertura sem alterar o ranking (ρ = 1,000 em todos os cenários testados) |
| **Consequência para o manuscrito** | Não haverá parágrafo dedicado a Macapá ou Chaves. Em seu lugar: (a) a declaração geral de que a resolução das fontes limita a representatividade célula a célula, sobretudo em corpos d'água interiores e recortes costeiros estreitos; (b) a recomendação de **trabalho futuro com modelagem de alta resolução em grade não estruturada**, que é a via adequada para resolver estuário, canal e zona de arrebentação — e não um filtro sobre a grade atual |
| **Critério retirado** | O item 4 da §9 exigia interpretação explícita de Macapá e Chaves no manuscrito. Foi **dispensado**, não satisfeito, pela justificativa acima. Fica registrado como retirada deliberada e não como critério cumprido |
| **Critério que permanece aberto e migra** | A validade do WAVERYS nos pontos de `thr_hs` < 1 m (item 6 da §9) não foi avaliada. É comum com **AUD-02**, diagnóstico 4, e segue lá; não bloqueia esta questão, cujo objeto era a contaminação estuarina |
| **Desfecho** | `resultado-validado-mantido`. A preocupação foi testada, não confirmada, e superada pela mudança de método (AUD-01) — sem nova exclusão. Nenhum ponto removido, nenhum produto regenerado, nenhum valor alterado |
