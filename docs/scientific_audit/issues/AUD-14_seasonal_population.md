# AUD-14 — População sazonal invisível: censo *de jure* contra 33 anos de registro metoceânico

| Campo | Valor |
|-------|-------|
| **ID** | AUD-14 |
| **Tipo** | `qualidade-dados` |
| **Componente** | exposição |
| **Etapa do fluxo** | Step 4.2 |
| **Afeta** | dados, interpretação, documentação |
| **Prioridade** | P2 |
| **Bloqueia publicação?** | Não — mas exige declaração explícita entre as limitações |
| **Status** | `aguardando-decisao` |
| **Desfecho** | — *(proposto: `limitacao-reconhecida`)* |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-05, AUD-08 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2, §8 item 14, §9.3 item 16 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-31 |

---

## 1. Problema

A exposição usa a população **residente** (*de jure*) do Censo 2022, contada num
único instante (31/07/2022). A população flutuante dos balneários — que em alguns
municípios do Sul e Sudeste multiplica a população presente por três ou mais no
verão — é invisível.

O viés é **sistemático e direcional**: subestima exatamente os municípios de
SC, PR, SP e RJ, que são os de maior perigo físico no domínio.

## 2. Por que importa cientificamente

A sazonalidade da população coincide parcialmente com a sazonalidade do perigo.
As ressacas do Atlântico Sul ocorrem preferencialmente no outono e inverno
austral, quando a população flutuante é menor — o que reduz o viés. Mas eventos
de verão existem, e o pico de população coincide com o período de maior uso da
orla, portanto de maior exposição de pessoas na faixa de praia.

A consequência prática: municípios como Balneário Camboriú, Bombinhas, Guarujá,
Ubatuba e Cabo Frio têm exposição efetiva bem acima da registrada, e todos estão
no setor de maior perigo. Isso agrava o problema documentado em AUD-05.

## 3. Evidência original

A limitação já está **corretamente reconhecida no código**, em
`src/04_risk_integration/municipal_exposure.py` L16–20:

> *"Two further limits are inherent to the inputs. The census counts residents on
> 2022-07-31, a single instant against 33 years of metocean record, and it counts
> them* de jure*: the seasonal population of the resort municipalities of the
> South and Southeast is invisible here."*

O que **não** existe:

- nenhuma quantificação do viés;
- nenhuma menção no `README.md`;
- nenhum uso de `dom_10km` (domicílios dentro de 10 km), que já está calculado em
  `municipal_exposure.csv` e é o caminho natural para estimar a população
  flutuante.

Dados disponíveis e não usados, de `outputs/exposure/municipal_exposure.csv`:

| coluna | conteúdo |
|---|---|
| `dom_municipality` | 13 714 191 domicílios no total dos 282 municípios |
| `dom_10km` | 11 396 273 domicílios dentro de 10 km |
| `dom_1km`, `dom_2km`, `dom_5km` | idem, demais bandas |

A razão `pop_10km / dom_10km` é 2,70 na média nacional do conjunto. Municípios com
razão anomalamente **baixa** são candidatos a alta fração de domicílios de uso
ocasional — um proxy imediato, calculável sem dado novo.

## 4. Localização exata

### Código

| Caminho | Elemento | Papel |
|---|---|---|
| `src/04_risk_integration/municipal_exposure.py` | L16–20 | Docstring que reconhece a limitação |
| `src/04_risk_integration/municipal_exposure.py` | `accumulate_tile()` L147 | Lê `TOTAL` e `TOTAL_DOM` da grade IBGE |
| `src/04_risk_integration/municipal_exposure.py` | L237 | Escreve as colunas `pop_*` e `dom_*` |
| `src/04_risk_integration/exposure_index.py` | `exposure_absolute()` L105 | Consome apenas `pop_10km` |
| `src/site/export_risk_index_data.py` | `EXPOSURE_FIELD` L68 | `pop_10km` |
| `src/01_data_preparation/acquisition/download_ibge_grade.py` | — | Aquisição da grade; ponto de entrada para variáveis adicionais |

### Dados

- `data/raw/ibge/grade_estatistica_2022/grade_id*.zip` — 20 quadrantes; a grade
  carrega `TOTAL` e `TOTAL_DOM`. **A variável de domicílios de uso ocasional não
  está na grade estatística**; precisaria vir do agregado por setor censitário
  ou do SIDRA.
- `data/metadata/ibge_grade_estatistica_2022_download.json` — proveniência.

### Figuras afetadas

Indiretamente, todas as que exibem exposição ou risco.

## 5. Comportamento atual vs. comportamento pretendido

| | Descrição |
|---|---|
| **Implementado** | População residente em 31/07/2022 dentro de 10 km |
| **Pretendido/conceitual** | Pessoas presentes onde o perigo atua — o que, para um município balneário, varia por um fator grande ao longo do ano |

## 6. Divergência documentação ↔ implementação ↔ saídas

- A docstring do módulo reconhece a limitação com precisão. **Nenhuma divergência
  entre código e sua própria documentação.**
- O `README.md` §4.2 descreve a exposição sem mencionar a limitação, e o
  manuscrito ainda não a declara.
- A docstring diz explicitamente *"The manuscript must say so explicitly"* — uma
  obrigação registrada e ainda não cumprida.

## 7. Explicações alternativas plausíveis

1. **O viés pode ser irrelevante para o resultado.** Se a sazonalidade do perigo
   for anticorrelacionada com a da população (ressacas no inverno, turistas no
   verão), a exposição média anual efetiva pode estar próxima da residente.
   **Verificável** com os dados de sazonalidade já produzidos no submódulo 3.4.
2. **A população residente é a métrica correta para risco crônico.** Erosão,
   perda de patrimônio e deslocamento afetam residentes, não visitantes. Um índice
   de risco para planejamento de adaptação de longo prazo deve mesmo usar
   residentes.
3. **Um proxy de população flutuante introduz sua própria incerteza.** Domicílios
   de uso ocasional não são ocupados simultaneamente; qualquer fator de conversão
   é uma suposição.
4. **A comparabilidade nacional favorece a métrica residente.** É a única
   disponível de forma homogênea para os 282 municípios.

## 8. Diagnósticos propostos

1. **Sazonalidade cruzada** — comparar o ciclo mensal de eventos compostos
   (submódulo 3.4, `outputs/storm_catalog/seasonality/`) com a sazonalidade
   turística conhecida, por região. *Saída esperada:* saber se o viés atenua ou
   agrava a exposição efetiva.
2. **Proxy imediato de uso ocasional** — calcular `pop_10km / dom_10km` por
   município e identificar os que se desviam da razão nacional (2,70). Requer
   apenas o CSV existente.
3. **Obter a variável de domicílios de uso ocasional** do Censo 2022 via SIDRA
   para os 282 municípios, seguindo o padrão de proveniência de
   `~/.claude/rules/data_download_rules.md` (metadados em `data/metadata/`).
4. **Estimativa de sensibilidade** — recalcular `Exposure_Index` com
   `pop_10km + f · dom_uso_ocasional_10km` para f ∈ {2, 3, 4} pessoas por
   domicílio, e medir a mudança de posição dos balneários.
5. **Comparar com dados de população flutuante** publicados por prefeituras ou
   pela FecomércioSC para alguns municípios de referência, como aferição do proxy.

## 9. Critérios objetivos de resolução

- [x] O `README.md` §4.2 e o texto do manuscrito declaram explicitamente que a
      exposição é população **residente** *de jure* de 2022 e que a população
      flutuante não está representada — cumprindo a obrigação registrada na
      docstring de `municipal_exposure.py`. *README §4.2, bloco de citação; e
      §"Conceptual Framework", definição de exposição. Também no glossário do
      site e na página de metodologia do índice.*
- [x] A direção do viés está declarada: subestima os balneários do S/SE, que são
      os de maior perigo. *Declarada nos dois lugares, nomeando Balneário
      Camboriú, Bombinhas, Guarujá, Ubatuba e Cabo Frio, e dizendo que o risco
      desses municípios é um **limite inferior**.*
- [x] O diagnóstico 1 foi executado, e a relação entre a sazonalidade do perigo e
      a da população está reportada. *Executado sobre o produto 3.4 regenerado
      em 2026-07-31: os eventos compostos no Sul/Sudeste concentram-se em outono
      e inverno austral (MAM+JJA: RS 84,6 %, SC/PR 84,3 %, SP/RJ 87,2 %), e o
      verão — pico da população flutuante — responde por apenas 3,1–8,0 %. A
      sazonalidade do perigo é **anticorrelacionada** com a da população, o que
      **atenua** o viés anual. Ver §14.*
- [x] Existe pelo menos uma estimativa de sensibilidade (diagnóstico 4), **ou**
      está registrado por que a variável de uso ocasional não pôde ser obtida.
      *Registrado, com a razão: a Grade Estatística do IBGE carrega apenas
      `TOTAL` e `TOTAL_DOM`; a categoria de uso ocasional existe por setor
      censitário no SIDRA e exigiria nova aquisição com proveniência própria.
      O proxy alternativo proposto pela §8 (diagnóstico 2) **foi tentado e
      rejeitado** — ver §14, achado (b).*
- [x] Se um proxy for adotado, sua proveniência está registrada em
      `data/metadata/` e o fator de conversão está justificado.
      *Não se aplica: **nenhum proxy foi adotado** e nenhum fator de conversão
      foi aplicado. Nada foi inventado.*
- [x] Existe texto de limitação pronto para o manuscrito.
      *`README.md` → "Declared limitations for the manuscript", terceiro
      parágrafo.*

## 10. Riscos de alteração prematura

- **Adotar um fator de conversão arbitrário** (pessoas por domicílio de uso
  ocasional) introduz uma suposição não verificável em uma camada hoje sólida e
  bem documentada.
- **Inflar a exposição dos balneários** move Balneário Camboriú e Itajaí para
  cima no ranking, o que "resolve" AUD-05 pela via errada — por ajuste de
  parâmetro, não por correção de mecanismo. Deve ser resistido.
- A exposição residente é hoje uma das camadas mais defensáveis do trabalho;
  alterá-la sem necessidade troca solidez por incerteza.

## 11. Condições sob as quais o resultado atual pode ser mantido

Muito provável que a métrica residente seja mantida. Basta que:

1. A limitação seja declarada no README e no manuscrito, com a direção do viés;
2. Uma estimativa de sensibilidade seja apresentada, ainda que grosseira, para
   mostrar a ordem de grandeza do efeito;
3. Fique claro que o índice mede risco a **residentes**, não a visitantes nem a
   ativos turísticos.

Desfecho esperado: `limitacao-reconhecida`.

## 12. Produtos a jusante que exigiriam regeneração

Se apenas houver declaração: nenhum.

Se um proxy for incorporado:

```bash
python -m src.risk_integration.municipal_exposure
python -m src.site.export_risk_index_data
python -m src.figures_article.make_article_hazard_vulnerability_risk_multiplot
python -m src.figures_article.make_article_top10_municipality_tables
```

## 13. Rastreabilidade de versionamento

| Data | Commit | Ramo | Arquivos alterados | Natureza |
|------|--------|------|--------------------|----------|
| 2026-07-31 | *(não commitado)* | `main` | `src/exploratory/audit_AUD_14_seasonal_population.py` (novo), `README.md` (§4.2, §Conceptual Framework, limitações do manuscrito), `site/content/project.ts`, `site/content/methodology.ts` | Diagnóstico + declaração. **Nenhum proxy adotado; nenhum valor numérico publicado alterado** |

## 14. Histórico de investigação

*A limitação está reconhecida na docstring de `municipal_exposure.py` desde a
implementação do módulo, sem quantificação.*

### 2026-07-31 — A sazonalidade do perigo atenua o viés; o proxy proposto não funciona

| Campo | Conteúdo |
|-------|----------|
| **Pergunta testada** | A sazonalidade do perigo agrava ou atenua a invisibilidade da população flutuante? E é possível sinalizar os municípios de alta ocupação ocasional sem dado novo? |
| **Dados e métodos** | (1) `outputs/storm_catalog/seasonality/seasonality_summary.csv`, o produto do Step 3.4 **regenerado em 2026-07-31** sobre os catálogos `zos` — os números antigos não valeriam. Share de eventos compostos aceitos por estação austral, agregado por faixa de latitude. (2) `outputs/exposure/municipal_exposure.csv`: razão residentes por domicílio ocupado dentro de 10 km, o proxy que a §8 propunha como diagnóstico 2. Nenhuma estimativa de população sazonal foi construída |
| **Scripts executados** | `python -m src.exploratory.audit_AUD_14_seasonal_population` |
| **Novas saídas geradas** | `outputs/audit/AUD-14_seasonal_population/{hazard_seasonality_by_region.csv, occasional_use_proxy.csv, diagnosis_summary.json}` |
| **Achados** | (a) **O perigo é de outono e inverno, e o turismo é de verão.** Share de eventos compostos em DJF: RS 8,0 %, SC/PR 5,4 %, SP/RJ 3,1 %, ES/BA-S 0,7 %, N/NE 4,4 %. O grosso cai em MAM+JJA: 84,6 % no RS, 84,3 % em SC/PR, 87,2 % em SP/RJ. A exposição efetiva média anual está, portanto, muito mais perto da residente do que o pico de verão sugeriria — o viés existe mas é **atenuado**, não amplificado. (b) **O proxy do diagnóstico 2 não funciona, e a razão é definicional.** O IBGE conta domicílios **ocupados**, de modo que os de uso ocasional já estão fora do denominador tanto quanto do numerador; a razão mede tamanho de família, não estoque habitacional sobre população residente, e não pode detectar segunda residência. Os balneários nomeados confirmam: Balneário Camboriú 2,41, Cabo Frio 2,71, Ubatuba 2,73, Bombinhas 2,74, Guarujá 2,89, contra 2,71 do conjunto — em torno da média, não abaixo dela. Diagnóstico 2 fica registrado como **tentado e rejeitado** |
| **Interpretação** | A limitação é da base e permanece, mas duas coisas mudaram em relação ao registro original. A primeira é que sua magnitude efetiva é menor do que se supunha, porque as ressacas do Atlântico Sul não coincidem com a alta temporada — isso é um argumento científico a favor da métrica residente, não uma desculpa. A segunda é que o caminho barato que o próprio registro propunha para sinalizar os balneários está fechado por definição da variável. Nenhuma estimativa sazonal foi inventada: inflar a exposição dos balneários moveria Balneário Camboriú e Itajaí para cima no ranking e "resolveria" AUD-05 por ajuste de parâmetro em vez de correção de mecanismo, exatamente o que a §10 deste registro adverte |
| **Alterações implementadas** | Nenhuma na camada de exposição. Declaração da limitação com a direção do viés em `README.md` §4.2 e §"Conceptual Framework", no glossário do site, na página de metodologia do índice, e um parágrafo pronto para o manuscrito |
| **Validação realizada** | O cruzamento entre exposição e produto municipal foi refeito **por código IBGE** depois que a primeira versão, unindo por nome, duplicou linhas — existem duas "Santa Rita" no conjunto, em MA e PB. Uma asserção no script agora falha se o merge duplicar |
| **Incerteza remanescente** | (1) A sazonalidade turística real não foi medida — assumiu-se o padrão conhecido de alta temporada em DJF, sem dado de ocupação. (2) A contagem de domicílios de uso ocasional continua **não obtida**; sem ela não há estimativa de sensibilidade quantitativa, apenas o argumento de atenuação sazonal. (3) O argumento sazonal é de média anual: um evento de verão em um balneário lotado continua tendo exposição efetiva muito acima da registrada, e isso não é capturado por nenhum índice de média |
| **Próxima decisão necessária** | Confirmar o fechamento como `limitacao-reconhecida`. Se o pesquisador quiser a estimativa de sensibilidade, ela exige uma aquisição SIDRA nova (domicílios de uso ocasional por município) com registro de proveniência — decisão de escopo, não técnica |
