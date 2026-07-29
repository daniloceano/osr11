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
| **Status** | `aberto` |
| **Desfecho** | — |
| **Depende de** | — |
| **Bloqueia** | — |
| **Relacionado a** | AUD-05, AUD-08 |
| **Origem** | `baseline/2026-07-29_initial_review.md` §3.2, §8 item 14, §9.3 item 16 |
| **Criado em** | 2026-07-29 |
| **Última atualização** | 2026-07-29 |

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

- [ ] O `README.md` §4.2 e o manuscrito declaram explicitamente que a exposição é
      população **residente** *de jure* de 2022 e que a população flutuante não
      está representada — cumprindo a obrigação registrada na docstring.
- [ ] A direção do viés está declarada: subestima os balneários do S/SE, que são
      os de maior perigo.
- [ ] O diagnóstico 1 foi executado, e a relação entre a sazonalidade do perigo e
      a da população está reportada.
- [ ] Existe pelo menos uma estimativa de sensibilidade (diagnóstico 4), ou está
      registrado por que a variável de uso ocasional não pôde ser obtida.
- [ ] Se um proxy for adotado, sua proveniência está registrada em
      `data/metadata/` e o fator de conversão está justificado.

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
| — | — | — | — | *nenhuma alteração até o momento* |

## 14. Histórico de investigação

*Nenhuma investigação registrada. A limitação está reconhecida desde a
implementação do módulo, sem quantificação.*
