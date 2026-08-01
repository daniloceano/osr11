# AUD-09 — SVI_Coast_2022: dois indicadores com direcionalidade invertida; o índice é um eixo de pobreza, não de suscetibilidade costeira

| Campo | Valor |
|-------|-------|
| **ID** | AUD-09 |
| **Tipo** | `fragilidade-metodologica` |
| **Componente** | vulnerabilidade |
| **Etapa do fluxo** | Step 4.3 |
| **Afeta** | dados, interpretação, saídas, documentação |
| **Prioridade** | P1 |
| **Bloqueia publicação?** | Sim — satisfeito: cargas publicadas, inversão discutida, escalas separadas e lacuna externa declarada |
| **Status** | `resolvido` |
| **Desfecho** | `resultado-validado-mantido` — nenhum indicador está invertido, o SVI não foi recalculado, e o que restava era de escala e de nomenclatura |
| **Depende de** | — |
| **Bloqueia** | AUD-05, AUD-11 |
| **Relacionado a** | AUD-10, AUD-13 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.3, §8 item 7, §9.2 item 11 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 (verificação das escalas e fechamento) |

---

> ### Nota de leitura — duas escalas, e o registro as confunde
>
> **O que entra no risco** é `Vulnerability_CDF_PC1 = Φ(PC1/sd(PC1))`, faixa
> 0,0122–0,9948, **sem âncora exata**.
>
> **O que é publicado como camada** é `SVI_Coast_2022`, o Min–Max 0–100 do mesmo
> PC1, preservado por rastreabilidade — e **ainda com Balneário Camboriú em
> 0,0000 e Chaves/PA em 100,0000**, impresso como `100.000` na tabela do artigo.
>
> Os números de alternativas de escala da §9 e da §14 (posto percentílico
> ρ = 0,958 no risco, deslocamento 108) são do pipeline **anterior**, com piso e
> Min–Max final. Remedidos: **ρ = 0,991**, deslocamento 66. Ver §3-bis.
>
> Fechada como `resultado-validado-mantido` por decisão do pesquisador em
> 2026-07-31, que também decidiu **não buscar material externo** — a comparação
> com Lima et al. (2024) fica como lacuna declarada.

## 1. Problema

O `SVI_Coast_2022` é construído por PCA sobre dez indicadores padronizados, com o
sinal do PC1 ajustado **globalmente**. Dois dos dez indicadores entram no índice
com carga **oposta à sua direção conceitual**:

- `pop_rent` (proporção em domicílio não próprio): r = **−0,765** com o SVI —
  mais locatários resulta em **menor** vulnerabilidade;
- `pop_agevul` (proporção em faixas etárias vulneráveis, < 9 e 60+): r = **−0,323**.

Além disso, o índice correlaciona r = **+0,944** com `pop_poverty`: funcionalmente
ele é um eixo de pobreza, saneamento e ruralidade, não uma medida de
suscetibilidade a inundação costeira.

Há ainda um artefato de escala: **Balneário Camboriú recebe SVI = 0,000
exatamente**, por ser o mínimo do Min–Max.

## 2. Por que importa cientificamente

1. **A interpretação declarada não corresponde ao conteúdo.** O `README.md`
   §"Conceptual Framework" define vulnerabilidade como suscetibilidade física e
   social. O índice implementado mede o gradiente de desenvolvimento Norte–Sul do
   Brasil — real e importante, mas não específico do perigo costeiro. Isso explica
   por que o top-10 de risco migra do Sudeste (perigo) para o Maranhão (SVI).
2. **A inversão de sinal será questionada.** Um revisor de vulnerabilidade social
   perguntará por que insegurança de posse (locação) e população idosa reduzem a
   vulnerabilidade. A resposta — que na estrutura urbana brasileira essas
   variáveis se concentram em municípios mais ricos, e a PCA captura o eixo
   dominante — é defensável, mas precisa estar escrita.
3. **O SVI = 0,000 exato** propaga-se ao produto final: é a âncora inferior da
   escala de `Risk_Hazard` (ver AUD-11) e o mecanismo terminal da reprovação de
   Balneário Camboriú (ver AUD-05).

## 3. Evidência original

De `site/public/data/risk_index_municipalities.geojson` (282 municípios):

### 3.1 Direcionalidade dos dez indicadores

| Indicador | r com SVI | ρ com SVI | Direção conceitual | Coerente? |
|---|---|---|---|---|
| `pop_poverty` | **+0,944** | +0,944 | ↑ vulnerabilidade | ✓ |
| `pop_illiterate` | +0,832 | +0,853 | ↑ | ✓ |
| `pop_house` | +0,825 | +0,830 | ↑ | ✓ |
| `pop_nogarbage` | +0,783 | +0,805 | ↑ | ✓ |
| `pop_nonwhite` | +0,779 | +0,820 | ↑ | ✓ |
| `pop_nosewage` | +0,720 | +0,741 | ↑ | ✓ |
| `pop_nowater` | +0,569 | +0,586 | ↑ | ✓ |
| `pop_nopaving` | +0,342 | +0,363 | ↑ | ✓ (fraco) |
| `pop_agevul` | **−0,323** | −0,252 | ↑ | ✗ **invertido** |
| `pop_rent` | **−0,765** | −0,756 | ↑ | ✗ **invertido** |

### 3.2 Redundância

- |r| médio fora da diagonal entre os dez indicadores: **0,433**.
- Bloco de saneamento (`nowater`, `nosewage`, `nogarbage`, `nopaving`):
  r interno 0,215 a 0,459 — quatro dos dez indicadores medem a mesma dimensão
  latente de infraestrutura, o que constitui **contagem múltipla parcial**.
- Menores |r| médios: `pop_agevul` 0,230 e `pop_nopaving` 0,241 — os dois
  indicadores menos integrados ao eixo dominante.

### 3.3 Efeitos de escala

| relação | ρ (Spearman) |
|---|---|
| SVI × log₁₀(`pop_municipality`) | **−0,494** |
| SVI × `Exposure_Index` | **−0,588** |
| SVI × `Risk_Hazard` | +0,297 |
| SVI × `Risk_Hazard` (parcial, controlando H e E) | **+0,795** |

### 3.4 Extremos

| Maiores SVI | valor | pop. municipal |
|---|---|---|
| Chaves/PA | **100,000** | 19 848 |
| Santo Amaro do Maranhão/MA | 93,237 | 13 561 |
| Icatu/MA | 91,702 | 24 618 |
| Primeira Cruz/MA | 91,288 | 13 521 |
| Paulino Neves/MA | 91,100 | 17 355 |

| Menores SVI | valor | pop. municipal |
|---|---|---|
| **Balneário Camboriú/SC** | **0,000** | 136 326 |
| Santos/SP | 8,687 | 418 360 |
| Florianópolis/SC | 10,154 | 536 876 |
| Niterói/RJ | 11,667 | 480 647 |
| São José/SC | 11,762 | 271 013 |

### 3.5 Reprodutibilidade — o que **está** correto

Auditoria registrada em `src/04_risk_integration/external_svi/README.md`
(2026-07-28): recomputar PC1 e o SVI a partir das dez variáveis entregues
reproduz os valores publicados **exatamente** (r = +1,000000, max|Δ| = 0,0000).
PC1 explica **50,5 %** da variância dos dez indicadores padronizados. Esta
questão **não** é sobre erro de cálculo.

---

## 3-bis. As duas escalas, e o custo das alternativas (2026-07-31)

Gerada por `src/exploratory/audit_AUD_09_scale_alternatives.py` →
`outputs/audit/AUD-09_scale_alternatives/`.

### 3-bis.1 Âncoras exatas: onde acabaram e onde continuam

| | escala | faixa | em 0 exato | em 1 / 100 exato |
|---|---|---|---|---|
| **Entra no risco** | `Φ(PC1/sd(PC1))` | 0,0122 – 0,9948 | **0** | **0** |
| **Publicado como camada** | `SVI_Coast_2022` (Min–Max 0–100) | 0,0000 – 100,0000 | **1** (Balneário Camboriú/SC) | **1** (Chaves/PA) |

O critério 6 exigia que nenhum município recebesse âncora exata por artefato de
Min–Max. **No caminho do risco isso foi atingido.** Na camada publicada não, e
por escolha deliberada: o SVI entregue foi preservado sem recálculo, por
proveniência — ele é produto de coautora externa. O que faltava não era corrigir,
era **declarar a distinção**, porque a âncora é visível ao leitor: a camada de
mapa vai de 0 a 100 e a primeira linha de
`outputs/article_figures/tables/top10_municipalities_by_svi.csv` imprime
`100.000`.

### 3-bis.2 As alternativas ficaram **menos** consequentes, não mais

Efeito de trocar a escala de vulnerabilidade, sobre o risco publicado:

| escala | ρ com `V` | **ρ no risco** | top-20 | desloc. máx | 0 exatos | 1 exatos |
|---|---|---|---|---|---|---|
| **`Φ(PC1/sd)` — publicada** | 1,000 | 1,000 | 20/20 | 1 | 0 | 0 |
| posto percentílico do PC1 | 1,000 | **0,991** | 19/20 | 66 | 0 | **1** |
| aditivo, direção imposta | 0,941 | **0,978** | 14/20 | 76 | 0 | 0 |
| Min–Max do PC1 (o SVI/100 original) | 1,000 | 0,976 | 18/20 | 50 | **1** | **1** |

Os números do registro são do pipeline anterior, com piso de 0,01 e Min–Max
final: posto percentílico dava **ρ = 0,958** no risco e deslocamento de **108**
posições. Hoje dá **0,991** e **66**. A afirmação da §14 de que a alternativa
"**não é neutra**, portanto a escolha depende de AUD-11" continua verdadeira em
espécie, mas o custo caiu pela metade — a remoção do piso e do Min–Max final
tornou o produto **menos** sensível à escala da vulnerabilidade.

As três escalas derivadas de PC1 têm ρ = 1,000 entre si na **ordenação da
vulnerabilidade** — são transformações monótonas do mesmo componente — e diferem
no **risco** apenas porque a média geométrica é não linear. Só o índice aditivo
com direção imposta muda a própria ordenação (ρ = 0,941), e ainda assim custa
menos no risco (0,978) do que custava antes (0,941).

> **Nota de precisão.** A escala publicada devolve deslocamento máximo de **1**
> posição contra ela mesma, não 0: o `Risk_Hazard` do GeoJSON é arredondado a
> seis casas, e o recálculo desempata um par quase idêntico. É ruído de
> arredondamento, não discrepância.

### 3-bis.3 A comparação externa não será feita

O critério 7 pedia comparação com o SVI-Coast de Lima et al. (2024) **ou** o
registro de por que não foi possível. O pesquisador decidiu em 2026-07-31 **não
buscar material externo**. A referência é do censo de **2010**, não está no
repositório, e obtê-la exige o material suplementar do artigo.

Fica como **lacuna declarada de validação externa da camada de vulnerabilidade** —
a mesma natureza da lacuna de AUD-18 para o detector, e declarada pelo mesmo
padrão: nomeada, não omitida.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/external_svi/build_svi_coast_2022.py` | script completo | Produziu o SVI. **Externo, não executável a partir do repositório** — monta Google Drive, usa `!pip`, lê planilhas de `/content/drive/MyDrive/OSR11/` |
| `src/04_risk_integration/external_svi/README.md` | auditoria de 2026-07-28 | Registro de reprodutibilidade e da anomalia de `pop_house` |
| `src/site/export_risk_index_data.py` | `SOURCE_LAYER_SPECS` L91–99 | Única quantidade lida do shapefile entregue |
| `src/site/export_risk_index_data.py` | L517 | `svi_fraction = SVI_Coast_2022 / 100` |
| `src/site/export_risk_index_data.py` | L576–579 | Aplicação do piso `CLIP_FLOOR` = 0,01 antes do produto |

### Dados e saídas

- `outputs/risk_index/risk_index.shp` — fonte externa; carrega `SVI_Coast_2022`
  (truncado no DBF para `SVI_Coast_`), `PC1` e os dez indicadores.
- `site/public/data/risk_index_municipalities.geojson` — dez indicadores
  disponíveis nas propriedades, permitindo toda a análise sem o shapefile.

### Figuras e tabelas afetadas

- `outputs/article_figures/hazard_vulnerability_risk_multiplot.png` (painel SVI)
- `outputs/article_figures/tables/top10_municipalities_by_svi.*`

### Anomalia já documentada (não é esta questão)

`pop_house` é publicado **pré-normalizado** (Min–Max 0–1), enquanto o manuscrito
o define como residentes por domicílio (2,40–4,45). A auditoria de 2026-07-28
demonstrou que isso é **inócuo para o índice** (Min–Max e z-score são ambos
afins; matrizes padronizadas idênticas a 5,7e-15) mas **real para a tabela
publicada**. Rastreado em AUD-17.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | z-score dos dez indicadores → PCA → PC1 → inversão global de sinal se a correlação média com as entradas for negativa → Min–Max 0–100 |
| **Pretendido/conceitual** | Índice em que valores altos representem consistentemente maior suscetibilidade a impactos costeiros |

A PCA não impõe direção aos indicadores individuais: extrai o eixo de maior
variância. A inversão global garante que o **eixo** aponte na direção certa, não
que cada indicador contribua na direção certa.

## 6. Divergência documentação ↔ implementação ↔ saídas

- `README.md` §4.3 lista os dez indicadores com descrições que implicam direção
  positiva de vulnerabilidade para todos (ex.: "Proportion in non-owned housing",
  "Proportion in vulnerable age groups"). O índice trata dois deles em direção
  oposta. A tabela do README não é falsa, mas é enganosa sem a nota de cargas.
- `README.md` §4.3 não reporta as cargas do PC1 nem a variância explicada
  (50,5 %), ambas disponíveis.
- Implementação e saídas concordam.

## 7. Explicações alternativas plausíveis

1. **A inversão é um resultado empírico legítimo do Brasil costeiro.** Locação e
   envelhecimento se concentram nos balneários ricos do Sul/Sudeste; a PCA
   corretamente identifica que, neste conjunto, essas variáveis marcam o polo de
   **baixa** vulnerabilidade. Forçar a direção conceitual seria impor uma teoria
   contra o dado.
2. **A metodologia segue a referência declarada.** O SVI-Coast de Lima et al.
   (2024, *Nat. Hazards*, DOI 10.1007/s11069-023-06246-w) usa a mesma abordagem
   PCA para 281 municípios costeiros brasileiros. Reproduzir a metodologia de
   referência é defensável; divergir dela exige justificativa.
3. **Um índice de pobreza pode ser exatamente o que se quer.** Se a hipótese é
   que a capacidade de resposta a desastres costeiros é limitada primariamente
   por privação material, um eixo de pobreza é o indicador correto. O problema
   seria apenas de nomenclatura.
4. **A correlação negativa com o tamanho da população pode ser real.** Municípios
   maiores têm melhor infraestrutura per capita no Brasil; ρ = −0,494 é um fato,
   não um artefato.
5. **O SVI = 0 de Balneário Camboriú pode ser inofensivo** se o piso de 0,01
   estiver funcionando. Contra-argumento: ele ainda é a âncora da escala final
   (AUD-11).

## 8. Diagnósticos propostos

1. **Publicar as cargas do PC1** por indicador, com sinal e magnitude, e a
   variância explicada por PC1 e PC2. Extraível dos dez indicadores presentes no
   GeoJSON — não requer o script externo.
2. **Construir um índice aditivo com direcionalidade imposta** (z-score de cada
   indicador, sinal fixado conceitualmente, média simples) e comparar com o PC1:
   ρ de Spearman, mudança de posição por município, efeito no ranking de risco.
   *Saída esperada:* saber quanto da estrutura do SVI depende da inversão.
3. **Testar a remoção de `pop_rent` e `pop_agevul`**: recomputar PCA com oito
   indicadores; medir ρ com o SVI atual e a variância explicada.
4. **Testar o tratamento da redundância do bloco de saneamento**: agregar os
   quatro indicadores em um único fator antes da PCA, ou aplicar ponderação
   inversa à redundância; comparar.
5. **Substituir o Min–Max final por posto percentílico ou balizas fixas**, de modo
   que nenhum município receba 0 ou 100 exatos. Medir o efeito sobre
   `Risk_Hazard` (interage com AUD-11).
6. **Comparar com o SVI-Coast publicado** de Lima et al. (2024), baseado no censo
   de 2010, para os municípios em comum: ρ de Spearman entre os dois índices.
   Serve como validação externa da camada.

## 9. Critérios objetivos de resolução

- [x] As cargas do PC1 por indicador, os sinais e a variância explicada estão
      publicados. *`README.md` §4.3, tabela completa das dez cargas; PC1 50,5 %,
      PC2 16,5 %. Tabela auditável em
      `outputs/audit/AUD-09_svi_directionality/pc_loadings.csv` e
      `indicator_directionality.csv`.*
- [x] Está discutido explicitamente que `pop_rent` e `pop_agevul` entram
      com sinal oposto à sua interpretação conceitual, e por quê.
      *`README.md` §4.3, bloco de citação; e §14 abaixo. Os dois são cargas
      negativas legítimas do PCA, **não** erros de codificação: os dez
      indicadores passaram no teste de reversão.*
- [x] Está declarado que o `SVI_Coast_2022` é dominado por privação
      material (r = +0,940 com pobreza) e **não** contém suscetibilidade física
      (ver AUD-10). *`README.md` §4.3 e o parágrafo AUD-09 das limitações do
      manuscrito.*
- [x] Existe comparação quantificada entre o PC1 e ao menos um índice
      alternativo com direcionalidade imposta, com o efeito no ranking de risco
      medido. *Quatro alternativas medidas — ver §14. A que impõe direção por
      soma aditiva dá ρ = 0,941 com o publicado e muda o top-10 de risco de
      10/10 para 6/10.*
- [x] A redundância entre indicadores está quantificada e discutida.
      *|r| médio fora da diagonal entre os dez: **0,424**; dentro do bloco de
      saneamento: **0,377**. Declarado em `README.md` → limitações.*
- [x] Nenhum município recebe SVI exatamente 0 ou 100 por artefato de Min–Max,
      **ou** está demonstrado que o piso de 0,01 neutraliza completamente o efeito
      no produto final (**requer AUD-11**). **Satisfeito no caminho do risco;
      persiste, declaradamente, na camada publicada.** *AUD-11 fechou e o piso
      deixou de existir. **`Vulnerability_CDF_PC1`, que é o que entra no risco,
      não tem âncora exata**: faixa 0,0122–0,9948, zero municípios em 0 ou 1.
      **`SVI_Coast_2022`, preservado por rastreabilidade, continua em 0–100 e
      ainda põe Balneário Camboriú em 0,0000 e Chaves/PA em 100,0000** — visível
      na camada de mapa e impresso como `100.000` na primeira linha de
      `top10_municipalities_by_svi.csv`. É escolha deliberada de proveniência, e
      está declarada como tal no `README.md`, com a distinção entre as duas
      escalas explicitada. `outputs/audit/AUD-09_scale_alternatives/`.*
- [x] Existe comparação com o SVI-Coast de referência (Lima et al. 2024), ou está
      registrado por que não foi possível. **Registrado por que não foi feita, e
      não será.** *O índice de referência é do censo de 2010, não está no
      repositório, e obtê-lo exige o material suplementar do artigo. O
      pesquisador decidiu em 2026-07-31 **não buscar material externo**. Fica
      como lacuna declarada de validação externa da camada de vulnerabilidade, no
      `README.md` e no parágrafo de limitação — não como pendência aberta.*

## 10. Riscos de alteração prematura

- **Recompor o SVI dentro deste repositório** rompe a autoria e a proveniência da
  camada, produzida por Karine Bastos Leal (INPE). Qualquer alteração deve ser
  acordada com a autora; a auditoria existente foi deliberadamente conduzida sem
  modificar o produto entregue.
- **Impor direcionalidade** afasta o índice da metodologia de referência
  (Lima et al. 2024) e exige justificar a divergência.
- **Remover indicadores** reduz a comparabilidade com o índice publicado de
  referência, que usa dez variáveis.
- O SVI é a camada **mais** reprodutível do trabalho. Alterá-la sem necessidade
  troca uma força por uma incerteza.

## 11. Condições sob as quais o resultado atual pode ser mantido

Muito provável que o SVI seja mantido como está. Basta que:

1. As cargas do PC1 sejam publicadas;
2. A inversão de `pop_rent` e `pop_agevul` seja discutida;
3. O índice seja nomeado e interpretado pelo que é — vulnerabilidade **social**
   dominada por privação material — e não como suscetibilidade costeira;
4. AUD-10 declare explicitamente a ausência da camada física;
5. AUD-11 resolva o problema da âncora de escala.

## 12. Produtos a jusante que exigiriam regeneração

Somente se o SVI mudar:

```bash
# o SVI vem do shapefile externo; alterá-lo exige nova entrega ou
# reimplementação dentro do repositório, e então:
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
python -m src.figures_article.make_article_supplementary_integrated_risk_zooms
```

Se apenas as cargas forem publicadas: nenhum produto muda.

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(a commitar)* | `main` | **Novos:** `src/exploratory/audit_AUD_09_scale_alternatives.py`, `outputs/audit/AUD-09_scale_alternatives/`. **Alterados:** este registro (§3-bis, §9, §13, §14 e nota de leitura), `README.md` (parágrafo de limitação de AUD-09 reescrito), `docs/scientific_audit/ISSUE_TRACKER.md` | Verificação das escalas + declaração. **O SVI não foi tocado; nenhum valor numérico publicado alterado** |
| 2026-07-31 | *(não commitado)* | `main` | `src/exploratory/audit_AUD_09_svi_directionality.py` (novo), `README.md` (§4.3 reescrita com as cargas; limitações do manuscrito), `site/content/*.ts` e páginas do site (enquadramento social, contagem 281→282) | Diagnóstico + documentação. **O SVI não foi alterado; nenhum valor numérico publicado mudou** |

## 14. Histórico de investigação

*A auditoria de reprodutibilidade do SVI de 2026-07-28 está registrada em
`src/04_risk_integration/external_svi/README.md` e não é repetida aqui. Os
diagnósticos de direcionalidade da §3 vêm da revisão de linha de base de
2026-07-29.*

### 2026-07-31 — Auditoria de direcionalidade: nenhum indicador está invertido

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Há indicador codificado na direção errada? Se não, as cargas negativas do PC1 são defensáveis? Distinguir as quatro coisas que a palavra "invertido" confunde: (1) coluna codificada ao contrário; (2) carga negativa legítima do PCA; (3) inversão arbitrária do sinal global do componente; (4) diferença entre pobreza e suscetibilidade costeira |
| **Dados e métodos** | Os dez indicadores das propriedades de `site/public/data/risk_index_municipalities.geojson` (282 municípios) — o GeoJSON os carrega, logo nada depende do script externo do Colab. Reprodução do pipeline entregue: `StandardScaler` → PCA → PC1 → inversão global do sinal se a correlação média com as entradas for negativa → Min–Max 0–100. Cada coluna foi rastreada até sua consulta ao SIDRA em `src/04_risk_integration/external_svi/build_svi_coast_2022.py` e submetida a um **teste de reversão**: uma coluna invertida (`x` publicado onde `1−x` era pretendido) não pode ser detectada por correlação, porque a reversão inverte exatamente o sinal sob suspeita; ela é detectada lendo o valor em municípios cuja posição real não está em disputa. Âncoras: Balneário Camboriú (menor privação do conjunto) e Chaves/PA (maior) |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_09_svi_directionality` |
| **Novas saídas geradas** | `outputs/audit/AUD-09_svi_directionality/{indicator_directionality.csv, pc_loadings.csv, alternative_indices.csv, largest_rank_changes.csv, diagnosis_summary.json}` |
| **Achados** | (a) **Reprodução exata**: r = 1,000000 com o publicado, max\|Δ\| = 5,9e-05 (arredondamento do GeoJSON), ρ = 1,000. PC1 explica **50,5 %**, PC2 **16,5 %**. (b) **A inversão global do sinal NÃO disparou**: a correlação média de PC1 com as entradas saiu **+0,468**, positiva, de modo que o `if corr_media < 0` do script externo nunca executou. O caso (3) não se aplica. (c) **Nenhum dos dez indicadores falha no teste de reversão.** `pop_rent` = 1 − (próprio de morador / total) vale 0,503 em Balneário Camboriú e 0,098 em Chaves — coerente com a realidade, ao passo que uma coluna invertida daria 90 % de domicílios não próprios no estuário amazônico, o que é falso. `pop_agevul` fica em 0,19–0,41, a faixa correta para 0–9 mais 60+; invertida estaria em 0,59–0,81. Verificações pontuais confirmam os demais: `pop_illiterate` 1,4 % em Florianópolis contra 19,1 % em Chaves; `pop_nonwhite` 21 % em Balneário Camboriú contra 84 % em Salvador; `pop_nowater` 0,9 % em Santos contra 96 % em Santo Amaro do Maranhão. **O caso (1) não se aplica: não há erro a corrigir e o SVI não foi recalculado.** (d) As duas cargas negativas são o caso (2), e têm explicação física: não-propriedade é traço de afluência urbana no Brasil (aluguel e segunda residência concentram-se nos balneários ricos do Sul, ocupação própria autoconstruída domina o litoral pobre), e `pop_agevul` soma duas caudas etárias que se movem em sentidos opostos com a renda, de modo que a soma é quase plana ao longo do gradiente. (e) **Impor direção por inversão de sinal antes do PCA é um no-op matemático**: refletir uma entrada apenas reflete sua carga e devolve componente idêntico — ρ = 1,000, deslocamento máximo de posto 0. (f) O caso (4) é real e é o achado que resta: r = +0,940 com pobreza, ρ = −0,491 com log da população — é um eixo de **privação material**, não de suscetibilidade costeira |
| **Interpretação** | Não houve erro. A questão migra de "corrigir um indicador invertido" para "nomear e interpretar o índice pelo que ele é". As alternativas foram medidas em vez de assumidas: índice aditivo com direção imposta ρ = 0,941 (top-10 de risco 6/10, deslocamento máximo 111 posições); PCA sem `pop_rent` e `pop_agevul` ρ = 0,994 (top-10 10/10); reescala por posto percentílico ρ = 0,958 no risco (deslocamento máximo 108). Nenhuma delas foi adotada: o SVI é a camada mais reprodutível do trabalho, foi produzida por coautora externa, e alterá-la para satisfazer uma expectativa conceitual seria impor teoria contra o dado. **O sinal do PC1 não foi escolhido para reproduzir o ranking anterior — ele nem chegou a ser invertido.** |
| **Alterações implementadas** | Nenhuma no SVI nem em qualquer produto numérico. `README.md` §4.3 reescrita para publicar as dez cargas, a variância explicada, o fato de a inversão global não ter disparado, e a natureza do índice; parágrafo de limitação para o manuscrito; enquadramento social corrigido no site |
| **Validação realizada** | A reprodução independente do índice a partir das dez colunas publicadas confirma o pipeline entregue a 5,9e-05. O efeito de cada alternativa foi propagado até o `Risk_Hazard` reconstruído com a mesma fórmula do exportador (piso 0,01, média geométrica, Min–Max municipal) |
| **Incerteza remanescente** | (1) **Sem comparação com o SVI-Coast de Lima et al. (2024)** — o índice de referência é do censo de 2010 e não está no repositório. (2) As âncoras exatas de Min–Max (0 e 100) persistem e interagem com AUD-11; a alternativa por posto percentílico **não é neutra** no risco final (ρ = 0,958), portanto a escolha não pode ser feita dentro de AUD-09. (3) A redundância está quantificada mas não tratada: quatro dos dez indicadores medem saneamento, o que é contagem múltipla parcial de uma mesma dimensão latente. (4) `pop_house` continua publicado pré-normalizado, divergindo da definição do manuscrito — pendência de AUD-17, não desta questão |
| **Próxima decisão necessária** | Duas, ambas do pesquisador: (a) tentar ou dispensar a comparação com Lima et al. (2024); (b) decidir, junto com AUD-11, se as âncoras exatas de Min–Max são aceitáveis. Enquanto as duas estiverem abertas a questão **não pode** fechar |


### 2026-07-31 — DECISÃO: escala do SVI passa a ser a CDF normal do PC1

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | Substituir o Min–Max 0–100 do PC1 por **Φ(PC1 / sd(PC1))**, a CDF normal padrão do componente padronizado. Registro canônico da decisão, com a tabela completa das camadas afetadas: **AUD-11 §14**, entrada de 2026-07-31 |
| **Por que resolve o critério pendente** | O critério 6 da §9 exigia que nenhum município recebesse 0 ou 100 exatos por artefato de Min–Max. A CDF entrega faixa observada **0,0122–0,9948**, sem âncora exata, e a escala deixa de depender de Balneário Camboriú e de Chaves. Sendo **monótona**, ρ = **1,0000** com o SVI publicado: **a ordenação dos 282 municípios não muda** e a auditoria de direcionalidade desta questão permanece integralmente válida — as cargas do PC1, a variância explicada e os sinais são os mesmos |
| **O que NÃO muda** | O PCA, as dez variáveis, as cargas, o sinal do componente. **O SVI não é recalculado**, apenas reescalado. Nenhuma conclusão da entrada de 2026-07-31 sobre direcionalidade é afetada |
| **Documentação exigida** | O pesquisador pediu que a mudança fique **muito bem documentada**. O mínimo: (a) `README.md` §4.3 explicando por que o PC1 não tem escala natural (média 0, sd 2,247, faixa −5,06 a +5,75, 48 % negativo) e por que a CDF foi escolhida em vez de Min–Max ou posto percentílico; (b) docstring do módulo que implementar; (c) `risk_index_metadata.json` com a fórmula e a razão; (d) página do site correspondente; (e) parágrafo no manuscrito |
| **Critério que continua aberto** | A comparação com o SVI-Coast de Lima et al. (2024) permanece não realizada. AUD-09 **não fecha** por causa dela |

### 2026-07-31 — Verificação das escalas e fechamento

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | Depois do fechamento de AUD-11, algum município ainda recebe âncora exata por artefato de escala? E quanto custam hoje as alternativas de escala da vulnerabilidade, medidas contra o produto atual em vez do superseded? |
| **Dados e métodos** | `site/public/data/risk_index_municipalities.geojson` (282 entregues, 280 com risco) e `outputs/article_figures/tables/top10_municipalities_by_svi.csv`. Quatro escalas de vulnerabilidade construídas sobre os 282 e alinhadas por código IBGE aos 280 com risco — o script **levanta erro** se o alinhamento deixar qualquer NaN. Risco recomposto com `H` e `E` fixos |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_09_scale_alternatives` |
| **Novas saídas geradas** | `outputs/audit/AUD-09_scale_alternatives/{vulnerability_scale_alternatives.csv, exact_anchor_audit.json, summary.json}` |
| **Achados** | (a) **O critério 6 estava sendo julgado sobre a escala errada.** O que entra no risco é `Φ(PC1/sd)`, faixa 0,0122–0,9948, **zero âncoras exatas** — critério atingido. O que continua com 0,0000 e 100,0000 é `SVI_Coast_2022`, a camada preservada por rastreabilidade, e isso é **visível ao leitor**: a tabela do artigo imprime `100.000` na primeira linha. (b) **As alternativas ficaram menos consequentes, não mais.** Posto percentílico: **ρ = 0,991** no risco, contra 0,958 sob o pipeline anterior; deslocamento máximo 66, contra 108. Aditivo com direção imposta: **0,978**, contra 0,941. Min–Max do PC1: 0,976, e **reintroduz** uma âncora em 0 e outra em 1. (c) As três escalas derivadas de PC1 têm ρ = 1,000 entre si na ordenação da vulnerabilidade — são monótonas do mesmo componente — e só divergem no risco porque a média geométrica é não linear |
| **Interpretação** | A remoção do piso e do Min–Max final (AUD-11) tornou o produto **menos** sensível à escala da vulnerabilidade, e não mais. Isso reforça o desfecho já indicado pela auditoria de direcionalidade: não há erro a corrigir, o SVI não deve ser recalculado, e a escolha de escala é de segunda ordem. O que faltava era **separar duas coisas que o registro tratava como uma**: a escala que entra no risco, hoje sem âncora, e a escala publicada como camada, que mantém as âncoras por proveniência. Declarar essa distinção é o que fecha o critério, porque o leitor vê as duas |
| **Alterações implementadas** | Script novo. Parágrafo de limitação de AUD-09 no `README.md` reescrito para separar as duas escalas, reportar o custo das alternativas e declarar a lacuna externa. **Nenhum valor numérico publicado alterado; o SVI não foi tocado** |
| **Validação realizada** | O alinhamento por código IBGE é verificado por asserção. A escala publicada reproduz o risco publicado com deslocamento máximo de 1 posição, atribuível ao arredondamento a seis casas do GeoJSON |
| **Incerteza remanescente** | (1) **Sem comparação com Lima et al. (2024)** — decisão de não buscar material externo. (2) A redundância entre os dez indicadores continua **quantificada mas não tratada**: quatro medem saneamento. (3) `pop_house` continua publicado pré-normalizado, divergindo da definição do manuscrito — pendência de **AUD-17** |
| **Próxima decisão necessária** | Nenhuma |

### 2026-07-31 — DECISÃO: fechar como `resultado-validado-mantido`

| Campo | Conteúdo |
|-------|----------|
| **Quem decidiu** | Danilo Couto de Souza (PI), 2026-07-31 |
| **Decisão** | Fechar. **Não buscar material externo** — a comparação com Lima et al. (2024) fica como lacuna declarada de validação externa da camada de vulnerabilidade, nomeada no `README.md`, e não como pendência aberta |
| **Por que `resultado-validado-mantido`** | A questão nasceu como "dois indicadores estão invertidos". A auditoria de direcionalidade demonstrou que **não há indicador invertido**, que a inversão global do sinal do PC1 **nunca disparou**, e que impor direção antes do PCA é um no-op matemático. O SVI **não foi recalculado** em momento algum. O que restou — nomenclatura, escala e âncoras — foi declarado, não corrigido |
| **O que fica declarado** | (1) O índice é um eixo de **privação material** (r = +0,940 com pobreza), não de suscetibilidade costeira. (2) `pop_rent` e `pop_agevul` entram com carga negativa, e isso é resultado empírico legítimo. (3) As duas escalas são distintas, e a publicada mantém âncoras exatas por proveniência. (4) A validação externa não foi feita |
| **O que o desfecho NÃO cobre** | (1) A redundância do bloco de saneamento, quantificada e não tratada. (2) `pop_house` pré-normalizado — **AUD-17**. (3) A suíte de casos conhecidos — **AUD-05** |
