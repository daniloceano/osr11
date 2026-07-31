# Prompt de implementação — remoção da cadeia de Min–Max (AUD-11, AUD-09, AUD-15, AUD-08)

**Preparado em 2026-07-31.** Entregar a um agente numa sessão nova. A decisão
científica já está tomada e registrada; esta sessão é de **implementação e
regeneração**, não de reabertura do método.

> **Todas as decisões estruturais estão tomadas.** Resta apenas confirmar os
> pesos numéricos da exposição — ver "Confirmação pendente" no fim. Se o
> pesquisador não se manifestar, use o esquema recomendado (A) e **declare** que
> foi o padrão adotado.

---

## Prompt

Trabalhe no repositório OSR11 implementando a decisão de normalização registrada
em `docs/scientific_audit/issues/AUD-11_minmax_chain_and_sample_anchoring.md`
§14, entrada de 2026-07-31, com as referências cruzadas em AUD-09, AUD-15 e
AUD-08.

**Leia primeiro, integralmente:**

- `docs/scientific_audit/README.md` — vocabulário controlado e regra de fechamento
- `docs/scientific_audit/ISSUE_TRACKER.md`
- `docs/scientific_audit/issues/AUD-11_*.md` §14 — **a decisão canônica**
- `docs/scientific_audit/issues/AUD-09_*.md` §14 — escala do SVI
- `docs/scientific_audit/issues/AUD-15_*.md` §14 — remoção do piso
- `docs/scientific_audit/issues/AUD-08_*.md` §14 — banda de exposição
- `src/04_risk_integration/hazard_index.py`, `exposure_index.py`
- `src/site/export_risk_index_data.py`

**Não reabra a decisão.** Ela foi tomada sobre diagnósticos quantitativos e está
justificada nos registros. Se encontrar evidência que a contradiga, **pare e
relate** em vez de improvisar uma alternativa.

### O que implementar

**1 · Perigo — `src/04_risk_integration/hazard_index.py`**

Substituir a cadeia de Min–Max por escalas de âncora fixa:

```
Hazard_Frequency = min(compound_count_total / 99.0, 1.0)
Hazard_Severity  = min(mean_integrated_severity / 1.0, 1.0)
Hazard_Index     = (Hazard_Frequency + Hazard_Severity) / 2
```

- `99` = 3 eventos/ano × 33 anos. Definir como constante nomeada, com o
  raciocínio no docstring: baliza fixa, não vinda da amostra; máximo observado
  no domínio é 98, portanto **nenhum ponto satura**.
- A severidade já é adimensional e não negativa; a baliza 1,0 equivale a um dia
  de critério pleno no excesso diário máximo do domínio. Máximo observado 0,948.
- **Remover o segundo Min–Max** (`Hazard_Index = _minmax(Hazard_Index_raw)`).
- **Preservar o zero natural**: pontos sem evento devem sair com 0,0 exato, não
  NaN. Hoje `mean_integrated_severity` é NaN em alguns pontos sem evento —
  tratar como 0.
- Manter `_minmax` no módulo apenas se algo mais o usar; caso contrário remover,
  não deixar código morto.

**2 · Vulnerabilidade — o SVI passa a ser reescalado no repositório**

Hoje o `SVI_Coast_2022` chega pronto no shapefile externo, já em 0–100. A nova
escala precisa ser aplicada a partir do `PC1`, que **já está publicado** nas
propriedades do GeoJSON e no shapefile.

```
V = Φ(PC1 / sd(PC1))        # CDF normal padrão, scipy.stats.norm.cdf
```

- `sd` com `ddof=0`, sobre os 282 municípios.
- **Verificar antes de usar**: recomputar o PC1 a partir dos dez indicadores
  (z-score → PCA → PC1, com a inversão global de sinal se a correlação média
  com as entradas for negativa) e conferir contra a coluna `PC1` entregue. Devem
  bater. Se não baterem, **pare e relate**.
- **Verificação obrigatória**: ρ de Spearman entre `V` e o `SVI_Coast_2022/100`
  atual deve ser **exatamente 1,0000** — a transformação é monótona. Se não for,
  há erro na implementação.
- Publicar `V` como campo novo, mantendo `SVI_Coast_2022` no produto para
  auditoria. Nomeie o campo novo de forma inequívoca.

**3 · Exposição — `src/04_risk_integration/exposure_index.py`**

A **fórmula** de `exposure_absolute` e `exposure_relative` não muda; muda a
quantidade a que se aplicam. A exposição deixa de usar uma banda única e passa a
usar uma **população efetiva** — decisão de AUD-08 §14, 2026-07-31:

```
pop_efetiva = w1·pop_1km + w5·pop_5km + w10·pop_10km        (Σw = 1)

Exposure_absolute = clip[(log10(pop_efetiva) − 2) / (6 − 2), 0, 1]
Exposure_relative = pop_efetiva / pop_municipality
Exposure_Index    = √(Exposure_absolute × Exposure_relative)
```

Pesos recomendados: **w1 = 0,50 · w5 = 0,30 · w10 = 0,20**.

**O que documentar no docstring, porque é o ponto que um revisor vai questionar:**
as bandas são **cumulativas e aninhadas** (`pop_1km ⊂ pop_5km ⊂ pop_10km`,
verificado sem violações nos 282). Uma pessoa a 0,5 km é contada nos três
termos; uma a 7 km, só no terceiro. A ponderação portanto gera decaimento por
distância automaticamente, e o peso efetivo por pessoa é:

| Anel | Peso efetivo |
|---|---|
| 0–1 km | `w1+w5+w10` = **1,00** |
| 1–5 km | `w5+w10` = **0,50** |
| 5–10 km | `w10` = **0,20** |

É por esses pesos de anel que a escolha deve ser explicada — eles dizem quanto
vale uma pessoa a cada distância.

**Identidade que a implementação deve usar e comentar:**

```
pop_efetiva / P  ≡  w1·(pop_1km/P) + w5·(pop_5km/P) + w10·(pop_10km/P)
```

Ponderar o numerador **já é** ponderar a fração relativa (verificado:
`max|diff| = 2,22e-16`). Calcule `pop_efetiva` **uma vez** e use nos dois
termos. Não implemente duas ponderações separadas.

**Verificações obrigatórias:**

- `pop_efetiva ≤ pop_10km` em todos os municípios (garantido por Σw = 1 com
  bandas aninhadas). Se falhar, há erro.
- **Nenhum município com `pop_efetiva` = 0.** Sob os pesos recomendados são
  zero, contra 14 sob `pop_1km` puro. Se aparecer algum, **pare e relate**.
- Casos de controle, sob os pesos recomendados:

| Município | pop_1km | pop_5km | pop_10km | pop_efetiva | Exposure_Index |
|---|---|---|---|---|---|
| Itaboraí/RJ | 0 | 0 | 29 916 | **5 983** | 0,109 |
| Paulo Lopes/SC | 0 | 658 | 8 316 | **1 861** | 0,255 |

Ambos têm perigo ≈ 0,63 e núcleo urbano recuado: devem **degradar**, nunca
zerar.

**4 · Integração — `src/site/export_risk_index_data.py`**

```
Risk_Hazard = (Hazard_Index_mun × Exposure_Index × V) ** (1/3)
```

- **Remover `CLIP_FLOOR`** e todos os seus usos.
- **Remover a renormalização municipal do perigo** (`Hazard_Index_mun` deixa de
  ser um Min–Max sobre os municípios; passa a ser o valor transferido direto).
- **Remover o Min–Max final** do risco. O risco passa a ocupar ~0–0,57.
- Atualizar `risk_index_metadata.json`: fórmula, balizas, ausência de piso,
  ausência de Min–Max, e a razão de cada escolha.

### Documentação exigida

O pesquisador pediu explicitamente que a mudança do SVI fique **muito bem
documentada**. Mínimo, em todos estes lugares:

- `README.md` §4.3 — por que o PC1 **não** tem escala natural (média 0,
  sd 2,247, faixa −5,06 a +5,75, **48 % dos municípios negativos**), e por que a
  CDF normal foi preferida a Min–Max e a posto percentílico;
- `README.md` §4.4 — a fórmula nova inteira, com as balizas e sua justificativa;
- `README.md` → "Declared limitations for the manuscript" — parágrafo novo: o
  índice deixou de depender da amostra, **mas continua relativo a balizas
  escolhidas**; não é medida absoluta de dano esperado;
- docstrings dos três módulos alterados;
- `risk_index_metadata.json`;
- páginas do site: `methodology/hazard-index`, `results/risk-integration`,
  `content/{methodology,results,project}.ts`;
- registros AUD-09, AUD-11, AUD-15, AUD-08 §13 e §14, com o antes/depois medido.

### Rotulagem do risco zero — não é detalhe cosmético

Com o piso removido, ~84 municípios ficam com risco **exatamente zero**. Isso
significa **"nenhum evento composto atendeu aos critérios em 1993–2025"**, e não
impossibilidade física — são 33 anos de amostra finita.

- Mapas: **categoria própria** na legenda, não a cor mais clara de um gradiente.
- Texto: use a formulação acima, nunca "sem risco".
- Os municípios em zero **empatam**; a ordenação interna deles desaparece, o que
  é o comportamento pretendido e deve ser dito.

### Regeneração e comparação antes/depois

Regenerar, nesta ordem:

```bash
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
python -m src.site.export_coastal_hazard_data
```

Produzir em `outputs/audit/AUD-11_normalization_change/` uma comparação
antes/depois com, no mínimo: ρ de Spearman do ranking; deslocamento mediano e
máximo de posto; composição do top-10; contagem de municípios em zero exato e a
causa de cada um (perigo ou exposição); faixa do risco; e os 20 municípios que
mais se movem, com a razão.

**Valores esperados** (simulação de 2026-07-31, esquema completo com os pesos
recomendados — teste de sanidade, não gabarito):

| | valor |
|---|---|
| ρ com o ranking publicado | 0,954 |
| Deslocamento mediano | 17 posições |
| Top-10 preservado | 6/10 |
| Municípios em zero exato | 84 (**todos por perigo nulo; nenhum por exposição**) |
| Faixa do risco | 0,000 – 0,570 |

Se a sua implementação divergir muito disto, **pare e investigue** antes de
seguir. Em particular, **qualquer município zerado por exposição é erro.**

### Regras da sessão

- **Não faça commit nem push sem autorização.**
- Preserve alterações preexistentes; não use comandos destrutivos.
- Não renomeie nem remova os arquivos de saída legados — estão marcados por
  README sob AUD-17 §14 item #14, e são lidos por diagnósticos de comparação.
- **Não existe Node.js neste ambiente**; o build do site não roda aqui. Faça a
  verificação estrutural dos arquivos `.ts`/`.tsx` editados e **declare** que o
  build não foi executado.
- Marque uma questão como resolvida apenas com todos os critérios de aceitação
  verificados um a um. AUD-09 e AUD-15 **continuam abertas** por outros
  critérios, mesmo depois desta implementação.

---

## Confirmação pendente — pesos da exposição

A **estrutura** está decidida: média ponderada das bandas de 1, 5 e 10 km com
pesos decrescentes (AUD-08 §14). Falta confirmar os números. Todos os esquemas
abaixo eliminam os zeros de exposição; diferem na agressividade do decaimento.

| Esquema | w1 / w5 / w10 | Pesos de anel | ρ | Desloc. mediano | Top-10 |
|---|---|---|---|---|---|
| **A — recomendado** | 0,50 / 0,30 / 0,20 | **1,00 / 0,50 / 0,20** | 0,954 | 17 | 6/10 |
| B | 0,60 / 0,30 / 0,10 | 1,00 / 0,40 / 0,10 | 0,948 | 20 | 6/10 |
| C | 0,50 / 0,33 / 0,17 | 1,00 / 0,50 / 0,17 | 0,952 | 18 | 6/10 |
| D | 0,77 / 0,15 / 0,08 | 1,00 / 0,23 / 0,08 | 0,943 | 22 | 4/10 |

**A** é a recomendação: os pesos de anel são legíveis em uma frase — *uma pessoa
na primeira faixa vale uma; entre 1 e 5 km vale meia; entre 5 e 10 km vale um
quinto* — o decaimento é monótono e nítido, e é o menor custo em movimentação de
ranking entre os esquemas com decaimento real.

Na ausência de manifestação, **use A e declare** que foi o padrão adotado, em
vez de parar a implementação.
