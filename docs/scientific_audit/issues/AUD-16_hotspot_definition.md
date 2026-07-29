# AUD-16 — Ausência de definição operacional de "hotspot"; classes de intervalo igual arbitrárias

| Campo | Valor |
|-------|-------|
| **ID** | AUD-16 |
| **Tipo** | `risco-interpretacao` |
| **Componente** | integração |
| **Etapa do fluxo** | Step 4.4 / 4.5 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | P2 |
| **Bloqueia publicação?** | Não — mas "hotspot = top-10" não é um critério e será questionado |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | AUD-11 |
| **Bloqueia** | — |
| **Relacionado a** | AUD-05, AUD-07 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §2.1 (parágrafo final), §8 item 13, §9.1 lista de verificação |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

O objetivo declarado do trabalho é "identify priority hotspots for adaptation
planning". Não existe definição operacional de hotspot no repositório:

- as classes publicadas são **oito intervalos iguais** em [0, 1], fixados no
  código, sem relação com a distribuição observada;
- as tabelas do artigo usam simplesmente **"top-10"**, sem critério de corte,
  sem limiar percentílico, sem quebra natural, sem teste de significância.

## 2. Por que importa cientificamente

"Top-10" é uma escolha de apresentação, não um resultado. Um leitor não sabe se o
11º município é substancialmente diferente do 10º, ou se o corte é arbitrário. Os
dados mostram que é arbitrário: 80 municípios caem na classe (0,625; 0,750] e 65
na classe (0,500; 0,625] — a distribuição é unimodal e não tem quebra natural em
lugar nenhum próximo ao 10º colocado.

Consequências:

- a recomendação de política pública ("priorizar estes dez municípios") não tem
  base estatística;
- combinado com a instabilidade documentada em AUD-07 (o top-5 muda inteiramente
  sob agregação alternativa) e com a ancoragem de escala de AUD-11, o corte
  torna-se indefensável;
- classes de intervalo igual sobre um índice cuja escala é definida por Min–Max
  dão a impressão falsa de que os limites de classe têm significado absoluto.

## 3. Evidência original

### 3.1 Distribuição nas classes publicadas

`FIXED_BOUNDARIES["Risk_Hazard"]` = `[0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]`:

| classe | n de municípios |
|---|---|
| (0,000; 0,125] | 3 |
| (0,125; 0,250] | 10 |
| (0,250; 0,375] | 26 |
| (0,375; 0,500] | 47 |
| (0,500; 0,625] | 65 |
| (0,625; 0,750] | **80** |
| (0,750; 0,875] | 39 |
| (0,875; 1,000] | 10 |

Distribuição unimodal com moda na sexta classe. **Nenhuma quebra natural**
coincide com um limite de classe.

### 3.2 Estatísticas do índice

De `site/public/data/risk_index_metadata.json` → `numeric_stats`:

| campo | count | mín | máx | média | mediana |
|---|---|---|---|---|---|
| `Risk_Hazard` | 280 | 0,000 | 1,000 | 0,5876 | 0,6160 |
| `Risk_Hazard_raw` | 280 | 0,0924 | 0,7185 | 0,4603 | 0,4780 |

### 3.3 O corte de top-10 na prática

`outputs/article_figures/tables/top10_municipalities_by_integrated_risk.csv`:

| posição | município | `Risk_Hazard` |
|---|---|---|
| 1 | Icatu/MA | 1,000 |
| ... | | |
| 10 | Salvaterra/PA | 0,879 |

O 11º e o 12º (Vigia/PA 0,870 e Duque de Caxias/RJ 0,861) estão a 0,009 e 0,018
do 10º. **A diferença entre o 10º e o 11º é menor que o deslocamento de 0,043
induzido pela remoção de um único município** (AUD-11 §3.2). Ou seja, o corte de
top-10 é menos estável que o ruído de ancoragem da escala.

### 3.4 As classes do perigo têm o mesmo problema

`FIXED_BOUNDARIES` aplica os mesmos oito intervalos iguais a `Hazard_Index`,
`Hazard_Frequency`, `Hazard_Duration`, `Hazard_Intensity` e — em escala 0–100 —
a `SVI_Coast_2022`.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/site/export_risk_index_data.py` | `FIXED_BOUNDARIES` L461–468 | Oito intervalos iguais para seis camadas |
| `src/site/export_risk_index_data.py` | `_nice_boundaries()` L236–270 | Limites arredondados para camadas sem limites fixos |
| `src/site/export_risk_index_data.py` | `_current_available_layers()` L471–493 | Aplica os limites e as cores |
| `src/04_risk_integration/palettes.py` | `risk_colors()` | Paleta discreta compartilhada |
| `src/figures_article/make_article_top10_municipality_tables.py` | — | Gera as tabelas de top-10 |
| `src/04_risk_integration/coastal_projection.py` | — | Camadas costeiras usam as mesmas classes discretas |

### Saídas

- `site/public/data/risk_index_metadata.json` → `available_layers[].boundaries`
- `site/public/data/coastal_hazard_metadata.json` → limites de classe por camada
- `outputs/article_figures/tables/top10_municipalities_by_{integrated_risk,hazard,svi}.{csv,tex}`

### Figuras afetadas

Todas as figuras com legenda discreta:
`hazard_vulnerability_risk_multiplot.png`,
`supplementary_integrated_risk_zooms.png`,
`coastal_hazard_index_components.png`.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Oito intervalos iguais fixos; "hotspot" = os dez primeiros da lista ordenada |
| **Pretendido** | Um critério declarado que responda: *a partir de que valor um município é hotspot, e por quê?* |

## 6. Divergência documentação ↔ implementação ↔ saídas

- O `README.md` menciona "priority hotspots" no Objetivo Geral, no Objetivo
  Específico 7 e no resumo, **sem nunca definir o termo**.
- As legendas das tabelas de artigo dizem "Top 10 Brazilian coastal
  municipalities by normalized integrated compound-risk index" — o que é
  descritivamente honesto, mas o texto do manuscrito provavelmente usará
  "hotspot".
- Código e saídas concordam. A lacuna é conceitual e documental.

## 7. Explicações alternativas plausíveis

1. **"Top-10" é uma convenção de apresentação aceitável** em trabalhos de
   priorização, desde que apresentado como tal e não como classe estatística.
2. **Intervalos iguais são a escolha cartográfica padrão** para índices
   normalizados 0–1 e têm a vantagem de serem imediatamente legíveis. Quebras
   naturais (Jenks) mudam a cada regeneração, o que prejudica a comparabilidade
   entre figuras.
3. **A ausência de quebra natural pode ser o resultado.** Se o risco costeiro
   brasileiro varia continuamente, sem agrupamentos, então **não existem
   hotspots discretos** — e essa é uma conclusão científica legítima e
   interessante, que o trabalho poderia afirmar.
4. **Um critério percentílico é igualmente arbitrário.** Escolher o decil
   superior não é mais fundamentado que escolher os dez primeiros; apenas
   escala com o tamanho do conjunto.

## 8. Diagnósticos propostos

1. **Testar a existência de agrupamentos** na distribuição de `Risk_Hazard`:
   estimativa de densidade por kernel, teste de unimodalidade (dip de Hartigan),
   e classificação por quebras naturais de Jenks com número de classes variável.
   *Saída esperada:* determinar se existem hotspots discretos ou se a distribuição
   é contínua.
2. **Sensibilidade ao corte**: para N ∈ {5, 10, 15, 20, 30, 50} e para os
   percentis 90, 95, 99, listar os municípios selecionados e medir a estabilidade
   sob as variantes de agregação de AUD-07.
3. **Autocorrelação espacial**: aplicar Getis-Ord Gi* ou LISA sobre
   `Risk_Hazard` com a matriz de vizinhança municipal, o que dá uma definição de
   hotspot **estatisticamente fundamentada** — agrupamentos espaciais
   significativos, não apenas valores altos. *Esta é a definição padrão de
   "hotspot" na literatura de análise espacial e é a rota recomendada.*
   **Atenção:** a pseudo-replicação de AUD-04 (178 pontos para 280 municípios)
   inflaciona artificialmente a autocorrelação e precisa ser considerada.
4. **Combinar com os intervalos de confiança** do bootstrap de AUD-07: definir
   hotspot como município cujo limite inferior do intervalo de confiança excede
   um limiar.
5. **Comparar intervalos iguais, quantis e Jenks** quanto ao mapa resultante.

## 9. Critérios objetivos de resolução

- [ ] Existe um teste de unimodalidade/agrupamento da distribuição de
      `Risk_Hazard`, com resultado reportado.
- [ ] Existe uma definição operacional de "hotspot" declarada no manuscrito, com
      justificativa — seja percentílica, seja por autocorrelação espacial, seja
      por intervalo de confiança.
- [ ] Se a distribuição for contínua e sem agrupamentos, o manuscrito **afirma
      isso** em vez de impor um corte, e apresenta o resultado como gradiente de
      prioridade.
- [ ] A sensibilidade ao corte está reportada: quais municípios entram e saem
      conforme N ou o percentil.
- [ ] As classes cartográficas estão justificadas, ou substituídas por classes
      derivadas da distribuição.
- [ ] Nenhuma afirmação do tipo "os dez principais hotspots são X" aparece sem
      referência à instabilidade documentada em AUD-07.

## 10. Riscos de alteração prematura

- **Adotar Jenks** faz os limites de classe mudarem a cada regeneração dos dados,
  quebrando a comparabilidade entre versões das figuras — problema real num
  projeto em que os dados ainda vão mudar por AUD-01/02/04.
- **Adotar Getis-Ord Gi\*** antes de resolver AUD-04 produz agrupamentos
  artificiais, porque municípios que compartilham ponto de grade têm perigo
  idêntico por construção — a autocorrelação medida seria em parte um artefato de
  pseudo-replicação.
- **Mudar o corte para produzir uma lista mais plausível** é seleção de resultado.

## 11. Condições sob as quais o resultado atual pode ser mantido

Aceitável manter intervalos iguais e top-10, se:

1. O termo "hotspot" for substituído por "municípios de maior índice" onde não
   houver critério estatístico;
2. A sensibilidade ao corte for reportada;
3. As classes forem declaradas como escolha cartográfica, não como categorias de
   risco;
4. AUD-07 fornecer os intervalos de confiança que contextualizam a lista.

## 12. Produtos a jusante que exigiriam regeneração

Se as classes mudarem:

```bash
python -m src.site.export_risk_index_data
python -m src.site.export_coastal_hazard_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.figures_article.make_article_coastal_hazard_components_map
python -m src.figures_article.make_article_top10_municipality_tables
```

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada além da contagem de classes do diagnóstico de
linha de base de 2026-07-29.*
