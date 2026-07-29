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
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | AUD-01 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-02, AUD-03, AUD-04, AUD-15 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.1(e), §5, §8 item 10 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

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

- [ ] Existe uma classificação versionada de validade oceânica dos 808 pontos,
      com critério explícito e reproduzível.
- [ ] A hipótese de contaminação por descarga está **testada** — não apenas
      afirmada — pelo diagnóstico 1, com correlação reportada.
- [ ] Está decidido e justificado: manter os pontos estuarinos, excluí-los, ou
      marcá-los com ressalva no produto.
- [ ] Se mantidos, Macapá e Chaves têm interpretação explícita no manuscrito,
      declarando que seu perigo deriva de ponto estuarino e que o mecanismo
      dominante ali é mareal/fluvial.
- [ ] Se excluídos, os municípios órfãos foram reassociados (AUD-04) e o efeito
      no ranking está reportado.
- [ ] A validade do WAVERYS nos pontos de `thr_hs` < 1 m está avaliada (comum com
      AUD-02, diagnóstico 4).

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada. A contaminação permanece **hipótese
fundamentada** — a revisão de linha de base identificou a localização dos pontos
e os limiares anômalos, mas não testou o ciclo sazonal do `zos`.*
