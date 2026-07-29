# AUD-07 — Instabilidade do ranking sob escolhas alternativas de agregação do perigo

| Campo | Valor |
|-------|-------|
| **ID** | AUD-07 |
| **Tipo** | `analise-sensibilidade` |
| **Componente** | perigo → integração |
| **Etapa do fluxo** | Step 4.4 |
| **Afeta** | interpretação, saídas, documentação |
| **Prioridade** | **P0** |
| **Bloqueia publicação?** | **Sim** — o top-5 do resultado principal não é robusto e não pode ser apresentado sem esta tabela |
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-06, AUD-11, AUD-13, AUD-16 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §1 (preocupação 4), §9.1 itens 4 e 5, §10 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

---

## 1. Problema

O ranking municipal de risco publicado **não sobrevive** a escolhas alternativas
razoáveis da agregação do perigo. Trocando apenas a definição de `Hazard_Index`
para "frequência apenas", o ρ de Spearman com o índice publicado cai para
**0,384** e o top-5 muda integralmente — de municípios do Maranhão e do Amapá
para São Sebastião, São José do Norte, Magé, Guarujá e Guaraqueçaba.

Esta questão **não pede uma correção**: pede que a instabilidade seja medida,
publicada e discutida. Um ranking instável ainda pode ser publicado — desde que a
instabilidade seja declarada.

## 2. Por que importa cientificamente

O principal resultado do trabalho, tal como apresentado nas tabelas do artigo, é
uma lista ordenada de municípios prioritários. Se essa lista depende de uma
escolha metodológica sem justificativa física forte (média aritmética de três
componentes Min–Max, pesos iguais), então:

- a ordenação específica dentro do top-10 não tem significado defensável;
- um revisor que refizer o cálculo com outra agregação obterá outra lista e
  concluirá que o resultado é arbitrário;
- a recomendação de política pública derivada da lista é frágil.

A solução científica correta não é escolher a agregação que produz o resultado
preferido, mas **publicar a tabela de sensibilidade ao lado do resultado**.

## 3. Evidência original

Todos os testes foram executados sobre
`site/public/data/risk_index_municipalities.geojson` (280 municípios com perigo)
e `outputs/storm_catalog/compound/compound_metrics.csv` (808 pontos).

### 3.1 Sensibilidade da agregação, no nível do risco integrado

ρ = Spearman com o `Risk_Hazard` publicado; sobreposição de top-20 e top-10:

| Variante | ρ | top-20 | top-10 | top-5 resultante |
|---|---|---|---|---|
| **implementado** (geométrico H,E,V) | 1,000 | 20/20 | 10/10 | Icatu, Turiaçu, Apicum-Açu, Macapá, Axixá |
| **perigo = só frequência** | **0,384** | 6/20 | 4/10 | **São Sebastião, S. José do Norte, Magé, Guarujá, Guaraqueçaba** |
| perigo = frequência + intensidade | 0,816 | 12/20 | 4/10 | Apicum-Açu, Icatu, Turiaçu, Cururupu, Axixá |
| perigo = média geométrica de F,D,I | 0,883 | 18/20 | 7/10 | Icatu, Macapá, Magé, Maricá, Saquarema |
| componentes normalizadas por posto | 0,967 | 17/20 | 6/10 | Icatu, Macapá, Axixá, Chaves, Vigia |
| média aritmética de H,E,V | 0,934 | 11/20 | 6/10 | Icatu, Maricá, São Sebastião, Saquarema, S. Gonçalo |
| exposição por posto de `pop_10km` | 0,773 | 10/20 | 6/10 | Magé, Macapá, Turiaçu, D. de Caxias, Maricá |
| sem exposição (H × V) | 0,803 | 9/20 | 5/10 | Calçoene, Turiaçu, Icatu, C. Mendes, Bacuri |
| sem renormalização municipal do perigo | 1,000 | 20/20 | 10/10 | idêntico (Min–Max é monotônico) |
| sem piso de recorte (piso 1e-6) | 1,000 | 20/20 | 10/10 | idêntico |

### 3.2 Sensibilidade da agregação, no nível do perigo (808 pontos)

ρ com o `Hazard_Index` implementado:

| variante | ρ |
|---|---|
| só frequência | 0,594 |
| só duração | 0,110 |
| só intensidade | 0,871 |
| frequência + intensidade | 0,881 |
| média geométrica F, D, I | 0,896 |
| componentes por posto | 0,967 |
| taxa anual (`compound_count_annual_mean`) | 0,594 |

### 3.3 Deixar-uma-componente-de-fora, no risco integrado

| componente removida | ρ com o publicado | sobreposição de top-20 |
|---|---|---|
| perigo | **0,554** | 10/20 |
| exposição | 0,803 | 9/20 |
| vulnerabilidade | 0,741 | 5/20 |

### 3.4 Amplificação pela segunda normalização

`Hazard_Index_raw` ∈ [0,1468; 0,7278]; o Min–Max final multiplica o contraste por
**1,72×**. Ver AUD-11.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/hazard_index.py` | `derive_native_hazard_index()` L75–171 | Única implementação da agregação do perigo |
| `src/04_risk_integration/hazard_index.py` | L117–120 | `mean(axis=1, skipna=False)` seguido de `_minmax` |
| `src/04_risk_integration/hazard_index.py` | `component_weights` L145–149 | Pesos declarados nos metadados |
| `src/site/export_risk_index_data.py` | L576–583 | Média geométrica das três componentes |
| `src/exploratory/make_exploratory_hazard_index_comparison.py` | — | **Já existe** um comparador entre a definição antiga (só contagem) e a atual; é a base natural para estender a comparação |
| `src/exploratory/make_exploratory_risk_with_exposure.py` | — | Comparador de variantes de risco com exposição |
| `src/exploratory/make_exploratory_exposure_normalization.py` | — | Comparador de normalizações de exposição |

### Dados e saídas

- `outputs/exploratory_hazard_index_comparison/` — saídas existentes.
- `outputs/exploratory_exposure/exposure_normalization_summary.json` e
  `risk_with_exposure_summary.json` — comparações já feitas.
- `site/public/data/risk_index_metadata.json` → `native_hazard_index`,
  `hazard_index_normalization`, `integrated_risk_formula`.

### Figuras e tabelas afetadas

- `outputs/article_figures/tables/top10_municipalities_by_integrated_risk.*` — o
  produto diretamente instável.
- `outputs/article_figures/tables/top10_municipalities_by_hazard.*`
- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png`

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | Média aritmética equiponderada de três componentes Min–Max, seguida de novo Min–Max. Nenhuma análise de sensibilidade publicada |
| **Pretendido** | Uma escolha de agregação justificada, acompanhada de tabela de sensibilidade e de intervalos de confiança sobre as posições |

## 6. Divergência documentação ↔ implementação ↔ saídas

Não há divergência: documentação, código e saídas concordam. A lacuna é a
**ausência** de análise de sensibilidade publicada, apesar de o repositório já
conter três scripts exploratórios que fazem comparações parciais
(`make_exploratory_hazard_index_comparison.py`,
`make_exploratory_risk_with_exposure.py`,
`make_exploratory_exposure_normalization.py`). Esses resultados nunca foram
consolidados em produto de artigo.

## 7. Explicações alternativas plausíveis

1. **A instabilidade pode ser esperada e aceitável.** Índices compostos são
   notoriamente sensíveis a escolhas de agregação; a literatura de indicadores
   (INFORM, IPCC) reconhece isso. O padrão da área é publicar a sensibilidade,
   não eliminá-la.
2. **A variante "só frequência" pode não ser uma alternativa razoável.** Se a
   frequência isolada é conceitualmente inferior ao índice multimétrico, o ρ =
   0,384 é irrelevante. Contra-argumento: a frequência é a componente mais
   fisicamente interpretável e a única com estrutura espacial sinótica limpa.
3. **Boa parte da instabilidade pode vir de AUD-01/AUD-02**, não da agregação: se
   o perigo do Norte for corrigido, as variantes podem convergir. **Este é o teste
   decisivo** e deve ser refeito após a resolução daquelas questões.
4. **As posições podem ser estatisticamente indistinguíveis.** Se o intervalo de
   confiança das posições for largo, "Icatu é 1º e Turiaçu é 2º" nunca teve
   significado, e a instabilidade entre variantes é apenas a manifestação disso.

## 8. Diagnósticos propostos

1. **Consolidar as tabelas §3.1 a §3.3 em um produto versionado** —
   `src/exploratory/audit_AUD_07_aggregation_sensitivity.py` →
   `outputs/audit/AUD-07_aggregation_sensitivity/` — com CSV, figura e JSON de
   resumo, aproveitando os três scripts exploratórios existentes.
2. **Bootstrap das posições**: reamostrar municípios com reposição (n = 1000),
   recalcular todas as normalizações dentro de cada reamostra, e produzir
   intervalo de confiança de 90 % para a posição de cada município.
   *Saída esperada:* saber se o top-10 é distinguível do top-30.
3. **Matriz de concordância entre variantes**: ρ de Spearman de todas as
   variantes contra todas, e índice de estabilidade de top-N para
   N ∈ {5, 10, 20, 50}.
4. **Análise de sensibilidade de pesos**: varrer os pesos das três componentes do
   perigo num simplex e mapear a região de pesos em que o top-5 permanece estável.
5. **Repetir §3.1 após AUD-01 e AUD-02** para verificar se a instabilidade
   diminui quando o perigo do Norte é corrigido.

## 9. Critérios objetivos de resolução

- [ ] A tabela de sensibilidade da agregação (§3.1) está versionada, gerada por
      script reproduzível, e incluída no material suplementar do manuscrito.
- [ ] A tabela de deixar-uma-componente-de-fora (§3.3) está versionada e incluída.
- [ ] Existe intervalo de confiança por bootstrap para a posição de cada
      município do top-20, e o manuscrito **não** afirma ordenação dentro de
      faixas estatisticamente indistinguíveis.
- [ ] A escolha da agregação está justificada por um critério declarado antes de
      observar o resultado (conceitual, ou consistência com um referencial como
      INFORM/IPCC), e não pela lista de municípios que produz.
- [ ] Se o ρ da variante "só frequência" permanecer abaixo de 0,6 após AUD-01 e
      AUD-02, o manuscrito declara explicitamente que a ordenação específica não é
      robusta e apresenta o resultado como faixas de prioridade, não como ranking.
- [ ] Nenhuma tabela de top-10 é publicada sem referência cruzada à tabela de
      sensibilidade.

## 10. Riscos de alteração prematura

- **Escolher a agregação depois de ver os rankings** é seleção de resultado. O
  critério deve ser fixado e declarado antes.
- **Substituir Min–Max por posto** (ρ = 0,967 no risco) parece atraente, mas
  destrói a informação de magnitude: dois municípios com perigo muito diferente
  ficam separados por uma posição. Interage com AUD-11 e deve ser decidido em
  conjunto.
- Executar esta análise **antes** de AUD-01, AUD-02, AUD-04 e AUD-06 produz uma
  tabela que terá de ser refeita. Recomenda-se produzir a infraestrutura agora e
  reexecutá-la ao final.

## 11. Condições sob as quais o resultado atual pode ser mantido

O ranking atual pode ser publicado se:

1. A tabela de sensibilidade acompanhá-lo, com a variante "só frequência"
   incluída, sem omissão;
2. Os intervalos de confiança por bootstrap forem apresentados;
3. O texto apresentar o resultado como **faixas de prioridade** em vez de
   ordenação estrita, quando as faixas se sobrepuserem;
4. A escolha da média aritmética equiponderada for justificada explicitamente.

## 12. Produtos a jusante que exigiriam regeneração

Se apenas a análise for adicionada: nenhum produto existente muda; são criados
novos em `outputs/audit/AUD-07_aggregation_sensitivity/`.

Se a agregação for alterada: cadeia de AUD-06 §12 (do exportador às figuras;
catálogos não precisam ser reprocessados).

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Os resultados da §3 foram produzidos no diagnóstico de linha de base de
2026-07-29, com scripts ad hoc não versionados. Consolidá-los em script
versionado é o diagnóstico 1.*
