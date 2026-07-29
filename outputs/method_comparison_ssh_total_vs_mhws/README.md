# Comparação de métodos — `SSH_total` (legado) × MHWS (novo)

Comparação lado a lado dos dois detectores de evento composto, com **exposição
e vulnerabilidade idênticas nos dois braços por construção**: os atributos
municipais vêm do mesmo produto publicado, de modo que a única coisa que difere
é a definição do evento composto.

Gerado por [`src/exploratory/compare_methods_ssh_total_vs_mhws.py`](../../src/exploratory/compare_methods_ssh_total_vs_mhws.py).
Nada aqui é publicado: os dados do site, as figuras do artigo e o instantâneo
legado permanecem intocados.

---

## 1. A diferença de método

| | Legado | Novo |
|---|---|---|
| Limiar de onda | q90 local de Hs | q90 local de Hs *(igual)* |
| Variável de nível | `SSH_total = zos + maré` | **`zos`** (livre de maré) |
| Condição adicional | — | **`max(SWL) > MHWS`** na sobreposição |
| Nível estático | — | `SWL = (zos − média(zos)) + maré` |
| Datum | — | `MHWS = A_M2 + A_S2` (FES2022) |
| Termo de nível na intensidade | `pico_SSH − thr_ssh` | `max(SWL) − MHWS` |
| Setup de onda | não usado | não usado |

Detalhes e justificativa: [`detection_mhws.py`](../../src/03_storm_catalog_generation/02_compound_detection/detection_mhws.py)
e [`AUD-01`](../../docs/scientific_audit/issues/AUD-01_compound_detector_tidal_phase_locking.md).

**Papéis da maré.** Ela deixa de decidir *se* houve evento e passa a decidir
*se a água chegou alto* e *quão grave foi*. É a separação entre forçante e
variável condicionante da tipologia de eventos compostos.

---

## 2. Verificação de fidelidade

O `thr_hs` recomputado pelo novo módulo reproduz **exatamente** o de produção
nos **808 de 808** pontos (diferença máxima 0,000000 m). A parte não alterada
do método é, portanto, idêntica, e as diferenças observadas vêm apenas do que
mudou de propósito.

MHWS resolvido em 808 de 808 pontos, faixa **0,08 a 4,33 m**.

---

## 3. O que aconteceu com cada componente

Média por faixa de latitude, componentes já normalizadas 0–1 na grade:

### Frequência — funcionou como pretendido

| | RS | SC/PR | SP/RJ | ES/BA-S | BA-N | NE | **N eq.** | AP |
|---|---|---|---|---|---|---|---|---|
| legado | 0,680 | 0,582 | 0,435 | 0,149 | 0,044 | 0,060 | **0,153** | 0,120 |
| novo | 0,740 | 0,650 | 0,465 | 0,200 | 0,057 | 0,050 | **0,048** | 0,117 |

A condição de MHWS rejeitou **30 117 de 109 756** candidatos (27,4 %),
concentrados no Norte: o setor equatorial cai de 86 para 25 eventos por ponto.

### Intensidade — funcionou como pretendido

| | RS | SC/PR | SP/RJ | ES/BA-S | BA-N | NE | N eq. | AP |
|---|---|---|---|---|---|---|---|---|
| legado | 0,784 | 0,499 | 0,446 | 0,428 | 0,439 | 0,302 | 0,394 | 0,445 |
| novo | **0,831** | 0,469 | 0,369 | 0,262 | 0,219 | 0,182 | **0,239** | 0,326 |

Passa a ter gradiente S→N limpo, como esperado de um forçante sinótico.

### Duração — **viés amplificado, e domina o resultado**

| | RS | SC/PR | SP/RJ | ES/BA-S | BA-N | NE | **N eq.** | AP |
|---|---|---|---|---|---|---|---|---|
| legado | 0,235 | 0,197 | 0,351 | 0,443 | 0,531 | 0,520 | 0,301 | 0,557 |
| novo | **0,039** | 0,036 | 0,140 | 0,127 | 0,236 | 0,323 | **0,431** | 0,273 |

**Não é uma inversão:** a duração cai em **79 % dos 808 pontos** (635 de 808).
O que muda é o *contraste*. O Sul colapsa ao piso da escala normalizada
(0,216 → 0,037) enquanto o setor equatorial se mantém (0,429 → 0,352), de modo
que a razão Norte/Sul passa de **2,0×** para **9,4×**. A duração já favorecia o
Norte no método legado; o método novo amplifica esse viés. A duração média da
sobreposição no N equatorial vai de 1,64 para **5,31 dias**.

**Causa física.** Sob o detector novo, os episódios de nível no trópico são
anomalias de `zos` de baixa frequência, com 7–8 dias de duração, não
tempestades sinóticas. A sobreposição herda essa persistência. A componente
mede persistência de estado oceanográfico, não duração de tempestade.

### Índice de perigo resultante

| | RS | SC/PR | SP/RJ | ES/BA-S | BA-N | NE | **N eq.** | AP |
|---|---|---|---|---|---|---|---|---|
| legado | 0,722 | 0,480 | 0,454 | 0,332 | 0,329 | 0,253 | **0,234** | 0,391 |
| novo | 0,831 | 0,578 | 0,477 | 0,262 | 0,219 | 0,243 | **0,334** | 0,333 |

O setor equatorial **sobe** de 0,234 para 0,334, apesar de frequência e
intensidade terem caído — porque é a única faixa em que a duração sobe
(0,301 → 0,431), enquanto o Sul, que deveria dominar, tem sua duração colapsada
ao piso da escala.

---

## 4. O achado central: as duas correções não são separáveis

Percentual do top-10 de risco municipal situado ao norte de 20°S:

| | 3 componentes (F+D+I) | 2 componentes (F+I) |
|---|---|---|
| **Legado** (`SSH_total`) | 70 % | 90 % |
| **Novo** (MHWS) | **90 %** | **30 %** |

- Corrigir só o detector **piora** (70 % → 90 %);
- Remover só a duração do método antigo **piora** (70 % → 90 %);
- **As duas juntas resolvem** (70 % → 30 %).

Top-5 sob cada combinação:

| Combinação | Top-5 |
|---|---|
| legado, 3 comp *(publicado)* | Icatu/MA, Turiaçu/MA, Apicum-Açu/MA, Macapá/AP, Axixá/MA |
| novo, 3 comp | Apicum-Açu/MA, Cururupu/MA, Augusto Corrêa/PA, Turiaçu/MA, Cajueiro da Praia/PI |
| **novo, 2 comp** | **São José do Norte/RS, Apicum-Açu/MA, Guaraqueçaba/PR, Chaves/PA, Turiaçu/MA** |

**Consequência prática: a correção do detector está condicionada à resolução de
[AUD-06](../../docs/scientific_audit/issues/AUD-06_duration_component_validity.md).**
Adotar o detector novo mantendo a duração com peso 1/3 não apenas dilui a
correção — ela é revertida.

---

## 5. Concordância global entre os métodos

| | Spearman |
|---|---|
| `Hazard_Index` na grade (808 pontos) | 0,756 |
| `Risk_Hazard` municipal (280 municípios) | 0,854 |
| Sobreposição do top-10 | 2 de 10 |
| Sobreposição do top-20 | 8 de 20 |

Correlação global alta com sobreposição de topo baixa: o método muda pouco o
ordenamento geral e muito **quem está no topo** — que é justamente o resultado
que o artigo reporta.

---

## 6. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `hazard_by_point.csv` | componentes e índice de perigo dos dois métodos, 808 pontos |
| `risk_by_municipality.csv` | risco, posição e variação de posição por município |
| `comparison_summary.json` | estatísticas agregadas, top-10 de cada braço, maiores subidas e quedas, variantes de agregação |

---

## 7. O que este exercício **não** resolve

- **AUD-06** (duração) — agora o problema dominante, ver §4;
- **AUD-02** (limiar de Hs) — `thr_hs` continua 0,20 m em Vigia; a condição de
  MHWS filtra parte desses eventos mas não corrige o limiar de onda;
- **AUD-04** (associação grade → município) — intocado;
- **AUD-12** (pontos estuarinos) — intocado;
- **AUD-03** — mitigado, não eliminado: a soma `zos(00Z) + maré máx. diária`
  deixa de governar a detecção, mas sobrevive na condição e na intensidade.

---

**Gerado em:** 2026-07-29
