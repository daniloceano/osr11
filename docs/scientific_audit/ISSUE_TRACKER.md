# Rastreador central da auditoria científica — OSR11

**Última atualização:** 2026-07-31
**Origem:** [`baseline/2026-07-29_initial_review.md`](baseline/2026-07-29_initial_review.md)
**Questões abertas:** 1 de 18 (AUD-05) · **em investigação:** 3 (AUD-08, AUD-09, AUD-17) · **aguardando decisão:** 0 · **resolvidas:** 14 (AUD-01, AUD-02, AUD-03, AUD-04, AUD-06, AUD-07, AUD-10, AUD-11, AUD-12, AUD-13, AUD-14, AUD-15, AUD-16, AUD-18) · **arquivadas:** 0

> ### Nota de sessão de 2026-07-30 — histórica, não é o estado atual
>
> *Os contadores desta nota valiam quando ela foi escrita. O estado corrente está
> na linha de contadores acima e na tabela mestra da §2; as notas de sessão
> seguintes registram o que mudou desde então.*
>
> **Sete questões foram resolvidas.** AUD-01 e AUD-06 em conjunto (método do
> perigo); AUD-04 por reenquadramento — a associação município↔ponto é
> julgamento de especialista, e foi arquivada como dado de entrada versionado
> sem alterar nenhum valor. AUD-17 teve seis de seus oito itens corrigidos (correção puramente
> documental, sem efeito em nenhum valor numérico publicado — ver seu registro,
> §14).
>
> **AUD-01 e AUD-06 foram resolvidas em conjunto**, por serem indissociáveis:
> nenhuma das duas correções isoladas é defensável. O método adotado usa a maré
> como **variável condicionante** em vez de forçante, e o índice de perigo passou
> de três para **duas componentes** — `frequência + severidade integrada`.
> O método legado está preservado em `outputs/legacy_ssh_total_method/` e a
> comparação em `outputs/method_comparison_ssh_total_vs_mhws/`.
> **Site e figuras do artigo foram regenerados.**
>
> Resultado: gradiente de perigo coerente (ρ com \|latitude\| = +0,58), as duas
> componentes passam a se reforçar (ρ = +0,60, era −0,55), e o top-10 municipal
> ao norte de 20°S cai de **70 % para 50 %**. Dois critérios de aceitação de
> AUD-06 permanecem não verificados, registrados no próprio registro.
>
> AUD-03, AUD-10 e AUD-14 foram encerradas como `limitacao-reconhecida` por
> decisão do pesquisador em 2026-07-31. As seis questões com status literal
> `aberto` e as cinco em investigação permanecem sem desfecho final.
>
> Relatório para coautores: [`reports/2026-07-30_relatorio_auditoria_perigo.md`](reports/2026-07-30_relatorio_auditoria_perigo.md).

---

> ### Sessão de 2026-07-31 — AUD-03, 09, 10, 12, 14, 15, 17
>
> Sete questões trabalhadas. **Nenhum valor numérico publicado foi alterado**, e
> nenhuma correção metodológica foi necessária: os quatro diagnósticos
> quantitativos executados confirmaram os produtos ou reduziram o escopo da
> preocupação.
>
> **AUD-12 fechada** como `resultado-validado-mantido`, por decisão do
> pesquisador em 2026-07-31: manter todos os pontos, sem filtro, com as
> incertezas de escala das fontes declaradas de forma geral e a modelagem de
> alta resolução em grade não estruturada recomendada como trabalho futuro.
> AUD-03, AUD-10 e AUD-14 foram posteriormente aprovadas e fechadas como
> `limitacao-reconhecida`; AUD-09 permanece em investigação com dois critérios
> não verificados.
>
> **Correção registrada:** a primeira versão desta sessão afirmou que Fernando
> de Noronha estava fora do escopo por não haver ponto de grade apropriado.
> **Falso** — há 19 pontos sobre o arquipélago, limiares oceânicos normais, o
> mais próximo a 1,5 km, todos com 100 % dos candidatos rejeitados pelo portão.
> As duas ausências são lacuna de associação e as duas são recuperáveis.
> Corrigido em AUD-15 §9, §14 e no `README.md`.
>
> - **AUD-09 — não há indicador invertido.** Os dez indicadores foram rastreados
>   até suas consultas ao SIDRA e submetidos a teste de reversão contra âncoras
>   de posição indisputada; **todos passaram**. A inversão global do sinal do PC1
>   **não disparou** (correlação média +0,468). As duas cargas negativas —
>   `pop_rent` −0,338 e `pop_agevul` −0,137 — são resultados empíricos legítimos.
>   Impor direção por inversão de sinal antes do PCA é um **no-op matemático**
>   (ρ = 1,000). **O SVI não foi recalculado**, e o sinal não foi escolhido para
>   reproduzir ranking algum. O que resta é de nomenclatura: r = +0,940 com
>   pobreza — é um eixo de privação material.
> - **AUD-12 — dissolvida pela mudança de método, não por exclusão.** O portão
>   HAT esvaziou os pontos questionados: Macapá 118 → **1** evento, Chaves
>   127 → **7**, Salvaterra 86 → **0**, Vigia/Colares 100 → **2**. Macapá caiu do
>   4º para o **172º** lugar do risco; Chaves do 8º para o **94º**. A
>   contaminação por descarga **não se sustenta**: o acoplamento com o oceano
>   aberto na banda sinótica é 0,827 nos pontos questionados contra 0,833 nos
>   vizinhos. O filtro de `max(Hₛ) < 0,5 m` é **vazio** — o mínimo do domínio é
>   0,54 m. **Recomendação: nenhum filtro.**
> - **AUD-15 — uma categoria nova e maior.** Os números antigos conferem (282
>   entregues, 280 com risco, ausentes Fernando de Noronha e Içara), mas o
>   portão HAT criou **83 municípios cujo ponto não aceitou nenhum evento**,
>   com `Hazard_Index_mun` exatamente 0, ocupando as posições **191–280**. Fica
>   em `em-investigacao`: vários critérios seguem não verificados.
> - **AUD-03 — a limitação é maior no Sul, não no Norte.** Erro de fase mediano
>   de 1,2 cm/dia, mas ≈1 cm no Norte macromareal contra **5–10 cm no Sul
>   micromareal** — o inverso do que a revisão de linha de base previa. É ruído,
>   não viés. O limiar de detecção **não é mais afetado**, só o portão e a
>   severidade.
> - **AUD-17 — seis inconsistências novas (#9–#14)**, todas criadas pela
>   melhoria do método. A mais grave: README e site afirmavam que os Steps 3.1 e
>   3.3–3.8 liam catálogos `SSH_total` superseded, o que é **falso** desde
>   `eee6142`. A #14 marcou os diretórios de saída de esquema antigo e revelou
>   que `outputs/storm_catalog/compound/` está **misturado** — catálogo corrente
>   (16 768 eventos) ao lado de sumário legado (96 031). Corrigidas as
>   inequívocas; **checklist de rechecagem** criada na §15 do registro.
>   Permanece `em-investigacao`.
>
> ### Decisão estrutural de 2026-07-31 — fim da cadeia de Min–Max
>
> O pesquisador decidiu **substituir toda normalização ancorada na amostra por
> escalas de âncora fixa e remover o piso de 0,01**. Registro canônico em
> **AUD-11 §14**; referências cruzadas em AUD-09 (escala do SVI), AUD-15 (piso)
> e AUD-08 (banda de exposição, ainda em decisão).
>
> - **SVI**: Min–Max 0–100 → **Φ(PC1/sd)**. ρ = 1,0000 com o atual (monótona),
>   sem âncora exata. O SVI **não é recalculado**, só reescalado.
> - **Perigo**: frequência com baliza fixa de **3 eventos/ano** (nenhum ponto
>   satura; máximo observado 98 de 99) e severidade usada como está (máximo
>   0,948). Zero natural preservado nas duas.
> - **Piso e Min–Max final removidos**: perigo nulo ⇒ risco nulo. **84
>   municípios com risco exatamente zero**; risco passa a ocupar 0 – 0,59.
> - **Exige regenerar todos os produtos municipais e as figuras do artigo.**
>
> - **Exposição** (AUD-08 §14, decidido 2026-07-31): deixa de usar banda única.
>   Passa à **população efetiva**, média ponderada das bandas cumulativas de 1,
>   5 e 10 km com pesos decrescentes. Como as bandas são aninhadas, isso gera
>   decaimento por distância automático, com peso efetivo por anel
>   **1,00 / 0,50 / 0,20** no esquema recomendado. **Nenhum município fica com
>   exposição zero** — contra 14 sob `pop_1km` puro, que suprimia Itaboraí/RJ
>   (223 mil hab., perigo 0,63) e Paulo Lopes/SC por artefato da grade do IBGE
>   (1 km em área rural). Identidade útil: ponderar o numerador já pondera a
>   população relativa (`pop_ef/P ≡ Σwᵢ·(popᵢ/P)`, erro 2e-16), de modo que um
>   único conjunto de pesos serve aos dois termos.
>
> Efeito conjunto de tudo: ρ = 0,954 · deslocamento mediano 17 posições ·
> top-10 6/10 · **84 municípios em zero exato** · risco 0 – 0,570.
>
> **Falta apenas confirmar os pesos exatos** antes da implementação.
>
> **A implementação não foi feita nesta sessão**, por instrução do pesquisador.
> O prompt pronto está em
> [`reports/2026-07-31_prompt_implementacao_normalizacao.md`](reports/2026-07-31_prompt_implementacao_normalizacao.md).
>
> **O build do site não foi executado** — não há Node.js no ambiente. As
> alterações passaram por verificação estrutural, não por compilação.

> ### Sessão de 2026-07-31 (cont.) — AUD-13 fechada; quatro registros descrevem produto superseded
>
> **AUD-13 fechada** como `resultado-validado-mantido`, por decisão do
> pesquisador. Nenhum valor publicado alterado, nenhuma mudança de fórmula.
> Diagnóstico versionado em `src/exploratory/audit_AUD_13_component_contributions.py`
> → `outputs/audit/AUD-13_component_contributions/`.
>
> A questão **mudou de objeto** e o registro foi reescrito contra o produto
> vigente (§3-bis nova; §9 refeita, com os critérios de 2026-07-29 anotados um a
> um — dois **anulados** por se tornarem insatisfazíveis, um **sem objeto**).
> Nada foi apagado.
>
> - **O índice integrado é, operacionalmente, o índice de perigo.** O perigo
>   responde por **84,7 %** da variância de log(risco) (era 51,0 %); removendo-o
>   da fórmula, ρ = **+0,092** contra o ranking publicado. A causa não é a
>   álgebra: o portão HAT tornou o campo de perigo quase binário, e a média
>   geométrica pondera pela dispersão logarítmica.
> - **O cancelamento trocou de par.** E × V — objeto declarado da questão —
>   comprime a variância em 9 %; **H × V comprime por um fator de 3**. E as duas
>   anticorrelações têm naturezas distintas: E × V é fato social, H × V é a
>   interseção de um gradiente físico com um socioeconômico.
> - **A correlação marginal vulnerabilidade × risco trocou de sinal**, de +0,297
>   para **−0,372**, com a parcial em **+0,790**. É supressão, não
>   degenerescência — e precisa estar dito, ou o mapa é lido como
>   "vulnerabilidade reduz risco".
> - **A inversão perigo → risco desapareceu**: top-20 do risco 20/20 no S/SE,
>   contra 15/20 no N/NE. O resultado que a §2 do registro chamava de "o mais
>   importante do trabalho" não existe mais.
> - **Mecanismo, novo e indispensável:** o HAT médio vai de **0,49 m** (35–28°S)
>   a **2,61 m** (2°S–7°N), enquanto o forçante enfraquece na mesma direção.
>   208 dos 808 pontos sem evento aceito; AL 15/15, SE 7/7, CE 18/20, PE 12/13
>   em perigo zero. Aceito como resultado — o perigo se concentra onde a
>   vulnerabilidade é menor — **com a ressalva declarada** de que parte da
>   magnitude da anticorrelação é produzida pela geografia do portão.
>
> **Alerta de manutenção:** AUD-05, AUD-07 e AUD-16 continuam com toda a
> evidência da §3 medida sobre o produto de 2026-07-29. Em AUD-07, a
> instabilidade que motivou o P0 caiu de ρ = 0,384 para **0,940** e migrou para
> o eixo da agregação (aritmética contra geométrica: 0,934 → **0,550**). Em
> AUD-16, as classes cartográficas **já foram alteradas** no código
> (`FIXED_BOUNDARIES["Risk_Hazard"]`) e existe hoje uma quebra natural real — a
> massa de 84 municípios em zero exato. Nenhum dos três pode ser julgado pelos
> critérios que carrega.

> ### Sessão de 2026-07-31 (cont.) — AUD-02 fechada como limitação reconhecida
>
> **AUD-02 fechada** como `limitacao-reconhecida`, por decisão do pesquisador.
> Nenhum piso, nenhum filtro de ponto, nenhum reprocessamento de catálogo,
> nenhum valor numérico alterado. Diagnóstico em
> `src/exploratory/audit_AUD_02_threshold_exposure.py` →
> `outputs/audit/AUD-02_threshold_exposure/`.
>
> **O alvo da questão mudou e não encolheu.** O portão HAT **não** esvaziou os
> pontos de limiar baixo — os 256 abaixo de 1,5 m ainda carregam **17,2 %** de
> todos os eventos aceitos. O que mudou é quem eles alimentam: os hotspots do
> Norte que a §3 do registro nomeia estão em risco zero e saíram por outra via,
> e quem depende de limiar baixo hoje é **o topo do ranking**.
>
> - **161 de 280** municípios publicados vêm de pontos com `thr_hs` < 1,5 m;
>   **44** de pontos abaixo de 1,0 m.
> - **8 dos 20 primeiros**, incluindo o **1º** — São José do Norte/RS, com
>   **1,20 m**, onde o q90 mediano do RS é 2,48 m — e o **4º**, Mangaratiba/RJ,
>   com **0,78 m**, ponto dentro da Baía de Sepetiba.
> - **Todos os 20 primeiros** vêm de pontos abaixo de **2,0 m**.
> - Por estado: mediana **0,90 m no MA** (24 de 33 municípios abaixo de 1,0 m)
>   contra 1,71 m no RS.
>
> **Duas indisponibilidades demonstradas sustentam o desfecho.** O piso não é
> derivável aqui: a calibração PU não determina o eixo da onda (seis melhores
> pares dentro de 1 % do score, cobrindo q50–q80), e a âncora externa natural —
> setup/runup a partir de Hₛ — exige declividade de face de praia, camada física
> que **AUD-10 já fechou como ausente**. E os pontos abrigados não são
> filtráveis: a orientação da linha de costa abriga pontos que não estão em baía
> alguma, e o WAVERYS é driver de larga escala **mesmo nos pontos expostos**.
>
> **O desfecho exigiu três coisas, todas feitas:** renomear a quantidade para
> *local Hₛ exceedance* onde o texto descreve o que o detector seleciona
> (README §2e e glossário, `site/content/project.ts`, `site/components/Hero.tsx`);
> publicar a tabela de limiares por setor e por estado como suplementar; e
> **declarar com número** a exposição do topo do ranking. O título do projeto foi
> mantido — descreve o fenômeno de interesse, não a quantidade detectada.
>
> **Trabalho futuro nomeado:** wave setup calculado diretamente de Hₛ substituiria
> o percentil por um limiar de significado físico local e resolveria piso e
> abrigo de uma vez. Depende da camada física de AUD-10.
>
> **Consequência para AUD-05:** o agrupamento duvidoso do topo deixou de ser o do
> Norte e passou a ser **as baías abrigadas do RJ** — Magé 3º, Mangaratiba 4º. A
> §3.3 de AUD-05 ainda lista Chaves, Macapá e os municípios do MA, todos hoje em
> risco zero.
>
> **O build do site não foi executado** — não há Node.js neste ambiente. As
> edições de `.ts`/`.tsx` passaram por verificação estrutural, não por compilação.

> ### Sessão de 2026-07-31 (cont.) — AUD-07 fechada; o bootstrap teve de ser redesenhado
>
> **AUD-07 fechada** como `resultado-validado-mantido`. Nenhum valor numérico
> alterado — só a legenda da tabela de top-10 do artigo. Diagnóstico em
> `src/exploratory/audit_AUD_07_aggregation_sensitivity.py` →
> `outputs/audit/AUD-07_aggregation_sensitivity/`.
>
> - **A instabilidade que motivou o P0 evaporou.** "Só frequência" foi de
>   ρ = **0,384 para 0,940**; "só severidade" 0,974. E a varredura de peso
>   frequência↔severidade dá **ρ ≥ 0,94 em toda a faixa** — a ponderação igual é
>   praticamente indiferente, não uma convenção injustificada.
> - **A instabilidade remanescente está na forma funcional**, não nas
>   componentes: média aritmética 0,551, componentes por posto percentílico
>   0,638. São as únicas variantes que movem o resultado.
> - **O bootstrap do §8.2 tornou-se degenerado e teve de ser trocado.**
>   Reamostrar municípios mede **exatamente 0,0** de deslocamento de posto em 200
>   sorteios: com âncoras fixas (AUD-11) o valor de um município não depende da
>   amostra. Substituído por bootstrap sobre os **33 anos de registro**, com
>   validação de que o sorteio-identidade reproduz o produto publicado.
> - **O topo é firme, o meio não é interpretável.** Posições 1, 2 e 3
>   degeneradas; largura mediana do IC de 90 % de **4,5** posições no top-10 e
>   **45** na faixa 101–196. **Oito municípios têm intervalo cobrindo a posição
>   10** — "top-10" é corte de apresentação, não classe estatística.
> - **Achado novo, não previsto por nenhum critério: eventos únicos.** **94 dos
>   196** municípios com risco positivo têm menos de dez eventos aceitos e **90**
>   têm menos de cinco. O primeiro deles é o **21º** — Guimarães/MA, com **um
>   evento em 33 anos**. A causa é a assimetria entre as componentes: a
>   frequência é ancorada em 99 eventos (um evento vale 0,010) enquanto a
>   severidade é uma **média condicional que não escala com raridade** (um dia
>   moderado devolve 0,283). No bootstrap, 94 municípios caem a zero em alguns
>   sorteios — 34 % para Guimarães, Alcântara, Raposa e Icatu —, restando apenas
>   **102 dos 280 robustamente não nulos**.
>
> **Decisão do pesquisador: declarar, não corrigir.** A correção da assimetria
> não é óbvia, e escolhê-la depois de ver quais municípios ela remove seria
> seleção de resultado; além disso reabriria AUD-13 e obrigaria a regenerar toda
> a cadeia municipal. Fica como trabalho futuro, com o diagnóstico versionado.
>
> **Anotado em AUD-15 e AUD-16**, que herdam a instabilidade da fronteira
> zero/não-zero. A §3 de AUD-16 foi marcada como desatualizada: a premissa
> "distribuição unimodal sem quebra natural" caiu — os 84 zeros exatos **são**
> uma quebra natural, e as classes cartográficas já haviam sido alteradas no
> código.

> ### Sessão de 2026-07-31 (cont.) — AUD-16 fechada: não existem hotspots discretos
>
> **AUD-16 fechada** como `resultado-validado-mantido`. Nenhum valor publicado
> nem classe cartográfica alterada. Diagnóstico em
> `src/exploratory/audit_AUD_16_hotspot_definition.py` →
> `outputs/audit/AUD-16_hotspot_definition/`.
>
> A questão nasceu porque "hotspot = top-10" não é critério. A medição mostrou
> que o problema era mais fundo: **não existe a coisa que o critério deveria
> delimitar.**
>
> - **Teste de unimodalidade de Silverman**: rejeita sobre os 280 (p = **0,002**)
>   e **não** rejeita sobre os 196 com risco positivo (p = **0,556**). A
>   bimodalidade está inteiramente na massa em zero, não num agrupamento de alto
>   risco. Fisher–Jenks confirma: GVF sobe suavemente de 0,678 (k=2) a 0,974
>   (k=8), **sem cotovelo**.
> - **A única quebra genuína é o zero**, e ela é uma declaração sobre o registro
>   — nenhum evento aceito em 1993–2025 —, não a classe mais baixa de um
>   gradiente.
> - **A rota Getis-Ord do §8.3 está indisponível**, e agora com número:
>   **32,6 %** dos 650 pares de vizinhança compartilham o mesmo ponto de grade
>   (178 pontos para 280 municípios, até 9 por ponto), logo têm perigo idêntico
>   por construção. Gi\* mediria a geometria da associação. Resultado negativo,
>   não pendência.
> - **A definição defensável vem do intervalo, não do valor**: município cujo IC
>   de 90 % permanece dentro das N primeiras posições sob reamostragem dos 33
>   anos. **7 a N = 10, 14 a N = 20.** Nenhum município fora do top-N publicado é
>   robustamente top-N — a lista não perde ninguém, apenas contém 3 membros que
>   não se sustentam no top-10.
> - **A objeção às classes de intervalo igual caiu**: AUD-11 removeu o Min–Max, a
>   escala tem âncora fixa e os limites valem igual na próxima regeneração. Jenks
>   foi comparado e recusado — recolocaria os limites a cada regeneração e não tem
>   *k* preferencial.
>
> `diptest`, `jenkspy` e `libpysal` não existem neste ambiente; os três
> procedimentos foram implementados no próprio script, em vez de acrescentar
> dependências a um repositório de artigo.
>
> **Não feito, e declarado:** figura de KDE; e a definição por intervalo não foi
> levada às figuras nem ao site como camada — continua sendo texto, não símbolo
> no mapa.

> ### Sessão de 2026-07-31 (cont.) — AUD-18 fechada; resta **uma** questão aberta
>
> **AUD-18 fechada** como `limitacao-reconhecida`. Nenhuma alteração de método,
> de escopo geográfico ou de valor publicado. Nenhum script novo — a questão não
> tem cálculo, e emitir tabela fixa por script daria aparência de diagnóstico a
> um levantamento bibliográfico.
>
> - **Dois números do registro caducaram.** `R_pos` = 0,102 é do par q90/q90
>   superseded; no par vigente **q70/q99** vale **0,1905** (H = 28, M = 119,
>   U = 831) — o detector quase dobrou o recall em SC. E o "ótimo de borda" da
>   §3.3 **já foi testado** em 2026-07-30: a grade foi a q95/q99 e o ótimo migrou,
>   mas pelo eixo do **nível**, não pelo da onda.
> - **A busca por base regional no N/NE dá negativo qualificado.** Não existe
>   equivalente aos 147 pares município×data de SC, logo **recalibração regional
>   continua impossível**. Mas três fontes servem parcialmente e ficam nomeadas:
>   *Panorama da Erosão Costeira no Brasil* (Muehe, org., MMA, 2018), com capítulo
>   por estado, que diz **onde** a costa recua e não **quando** houve evento;
>   a análise datada de ressacas em Fortaleza/CE (Paula et al., 2015), que cobre
>   **um** município; e as redes maregráficas **GLOSS-Brasil** (CHM/Marinha) e
>   **RMPG** (IBGE), com estações no N/NE, que validariam a **componente de
>   nível** e **nunca foram usadas**.
> - **A distinção que o manuscrito precisa fazer**: "não dá para recalibrar fora
>   de SC" é verdade; "não dá para verificar nada" seria falso e mais cômodo. A
>   comparação com marégrafos é tratável hoje, com dado público, e fecharia também
>   a lacuna de AUD-03.
> - **O domínio de validade não é recorte geográfico.** AUD-01 caracterizou a
>   partição por razão surge/maré (bimodal, antimodo em 0,257, intervalo 32× o
>   típico) e **deliberadamente não a aplicou**, porque o portão HAT elimina a
>   patologia por construção. O que se declara, portanto, é que **o mesmo detector
>   significa físicas diferentes ao longo da costa**, com a razão variando por
>   quase duas ordens de grandeza.
>
> **Ressalva registrada:** o reconhecimento **não é exaustivo** e o conteúdo das
> fontes **não foi verificado** — apenas existência, escopo e natureza. Registros
> de capitania e de autoridade portuária não foram procurados.
>
> **Resta uma única questão aberta: AUD-05**, a suíte de casos conhecidos, que é
> terminal e depende de sete questões — todas hoje resolvidas ou em investigação
> com decisão tomada.

> ### Sessão de 2026-07-31 (cont.) — AUD-15 fechada; duas afirmações do registro refutadas
>
> **AUD-15 fechada** como `limitacao-reconhecida`. Diagnóstico em
> `src/exploratory/audit_AUD_15_sea_frontage.py` →
> `outputs/audit/AUD-15_sea_frontage/`. Nenhum município excluído, nenhum valor
> numérico alterado.
>
> - **Içara/SC não é lacuna recuperável — a ausência está correta.** Está a
>   **4,0 km da costa, sem frente de mar**, e os **três** vizinhos dela dentro do
>   conjunto ficam entre ela e o mar (Araranguá 7,12 km de frente, Jaguaruna
>   15,90 km, Balneário Rincão a 0,23 km da linha). A razão é datável:
>   **Balneário Rincão foi desmembrado de Içara** pela Lei Estadual 12.668/2003,
>   instalado em 2013, levando o litoral. Um município sem frente de mar não tem
>   ponto oceânico próprio — a associação não falhou, não havia o que associar.
>   **A dependência de AUD-04 e a pendência com Karine deixam de existir.**
> - **Santa Rita/MA foi mal julgada.** A §2 dizia "provavelmente não é costeiro
>   em nenhum sentido útil"; tem **1,98 km de frente de mar**. O problema é
>   exposição (4 residentes) e associação (ponto a 77 km), não pertencimento.
> - **O critério de pertencimento deixou de ser desconhecido.** O conjunto tem
>   **exatamente uma** exceção à frente de mar, e ela é defeito datável da lista
>   herdada: Lima et al. reportam 281 e **não incluem Balneário Rincão**, logo a
>   lista parece anteceder o desmembramento — carrega o pai sem litoral e perde o
>   filho com a costa. Continua **não reconstruível** a partir do repositório.
> - **A classificação de frente de mar sai como triagem.** A Natural Earth 10 m
>   devolve interseção zero para 25 municípios quase todos costeiros — Olinda,
>   Itajaí, Navegantes —, todos a menos de 0,7 km da linha. Só o caso a uma ordem
>   de grandeza fora da banda é decidível.
> - **Classe própria para o zero na figura do artigo**, por decisão do
>   pesquisador: baliza `1e-6` no painel D do multiplot, **mantendo o verde** e
>   rotulando apenas `0`, sem texto explicativo na legenda. Resolve o conflito
>   entre a exigência de AUD-11 (categoria própria) e o commit `4db5001` (que a
>   desligara), atendendo à exigência sem impor o cinza. O site e a figura de
>   zooms **já** isolavam o zero; o multiplot era o que faltava.
>
> **Divergência deixada em aberto:** a figura de zooms rotula a mesma classe como
> "No accepted event", texto que o pesquisador dispensou no multiplot. Não
> unificado por conta própria — é escolha de apresentação.
>
> **Resta uma única questão aberta: AUD-05**, e nenhuma questão P2 em aberto.

> ### Sessão de 2026-07-31 (cont.) — AUD-11 fechada: a decisão não cumpriu tudo o que prometeu
>
> **AUD-11 fechada** como `mitigado-parcialmente` — não `metodologia-alterada`, e
> a distinção é o achado. Diagnóstico em
> `src/exploratory/audit_AUD_11_scale_anchoring.py` →
> `outputs/audit/AUD-11_scale_anchoring/`. Nenhum valor publicado alterado.
>
> A entrada de decisão de AUD-11 afirma que, com âncoras fixas, "nenhum valor
> publicado passará a depender de qual município ou qual ponto está no conjunto".
> **Verdade para perigo e exposição; falso para a vulnerabilidade**:
> `V = Φ(PC1/sd(PC1))` estima `sd(PC1)` **da amostra entregue**.
>
> - **No nível do município a melhoria é grande e real.** Leave-one-out
>   recalculando `sd` dentro de cada subamostra: pior caso **Chaves/PA**, que
>   desloca qualquer outro em no máximo **0,0036** e nenhum posto em mais de
>   **3**. Contra **0,0945** sob Min–Max — **redução de 26×**.
> - **No nível de domínio a dependência é material.** Excluir AP+PA+MA muda
>   `sd(PC1)` em −16,6 % (ρ = 0,991); excluir **todo o N/NE** muda em **−57,5 %**
>   e reordena os 104 restantes a **ρ = 0,696**, com deslocamento de até 0,292.
> - **Nenhum município em 1,000** (máximo 0,566) e os **84 em 0,000 são
>   substantivos**. O esquema de Min–Max, por contraste, produz um município em
>   1,000 **por construção**.
> - **Comparação dos quatro esquemas**: âncoras fixas (adotado) · Min–Max
>   ρ = 0,998 mas com âncoras exatas · posto percentílico ρ = 0,638 · z-score
>   truncado ρ = 0,592. As âncoras fixas são o único esquema testado que preserva
>   a magnitude **e** dispensa a ancoragem em indivíduos.
> - **Declarado** em `README.md` §4.4 e no campo
>   `integrated_risk_formula.interpretation` dos metadados publicados: o índice é
>   de **priorização relativa**, condicional ao domínio de 282 municípios, e
>   qualquer análise de subconjunto tem de **recalcular a escala**, não fatiar
>   estes valores.
>
> **Correção a um registro anterior.** A §3-bis.1 de AUD-07 afirmava que "com
> âncoras fixas, o valor de um município não depende da amostra", apoiada num
> bootstrap que devolveu 0,0. Aquele bootstrap reamostrava **valores publicados
> sem recalcular `sd(PC1)`** — demonstrava uma tautologia. Corrigido no registro.
> A conclusão de AUD-07 sobre o **desenho** do bootstrap continua válida.
>
> **Resta apenas AUD-05**, mais AUD-08, AUD-09 e AUD-17 em investigação.

Vocabulário controlado de `Tipo`, `Prioridade`, `Status` e `Desfecho`:
ver [`README.md`](README.md).

---

## 1. Situação por prioridade

| Prioridade | Total | aberto | em-investigação | aguardando-decisão | resolvido |
|---|---|---|---|---|---|
| **P0 — bloqueia publicação** | 6 | 1 | 0 | 0 | **5** |
| **P1 — resolver ou justificar** | 9 | 0 | 3 | 0 | **6** |
| **P2 — recomendado** | 3 | 0 | 0 | 0 | **3** |
| **P3 — opcional** | 0 | — | — | — | — |
| **Total** | **18** | **1** | **3** | **0** | **14** |

---

## 2. Tabela mestra

| ID | Título | Tipo | Componente | Etapa | Afeta | Prio | Bloqueia publicação? | Status | Desfecho | Depende de | Registro |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **AUD-01** | Eventos compostos travados em fase com a sizígia ao norte de ~20°S | fragilidade-metodologica | perigo | 3.2 (orig. 2e) | dados, interp., saídas, doc. | **P0** | **Sim** | `resolvido` | `metodologia-alterada` | **06** | [AUD-01](issues/AUD-01_compound_detector_tidal_phase_locking.md) |
| **AUD-02** | Limiar de onda é percentil local: mede raridade, não severidade; **8 dos 20 primeiros abaixo de 1,5 m** | fragilidade-metodologica | perigo | 2e → 3.1/3.2 | dados, interp., saídas, doc. | **P0** | Sim — satisfeito por qualificação explícita | `resolvido` | `limitacao-reconhecida` | — | [AUD-02](issues/AUD-02_hs_threshold_transfer.md) |
| **AUD-03** | Incoerência de fase no nível somado (zos 00Z + maré máx. diária) | qualidade-dados | perigo | 2c → portão HAT / severidade | doc., interp. | P1 | Não | `resolvido` | `limitacao-reconhecida` | — | [AUD-03](issues/AUD-03_ssh_total_phase_coherence.md) |
| **AUD-04** | Transferência grade → município: regra não reproduzível e suporte inadequado | **erro-implementacao** | perigo → integração | 4.1 | código, dados, interp., saídas, doc. | **P0** | **Sim** | `resolvido` | `limitacao-reconhecida` | — | [AUD-04](issues/AUD-04_grid_to_municipality_transfer.md) |
| **AUD-05** | Validação contra casos costeiros conhecidos (suíte de aceitação) | lacuna-validacao | integração | 4.4 | interp., saídas | **P0** | **Sim** | `aberto` | — | 01, 02, 04, 06, 08, 09, 11 | [AUD-05](issues/AUD-05_known_case_validation.md) |
| **AUD-06** | Duração: faixa trivial (1,26–2,51 d) amplificada a peso 1/3 | fragilidade-metodologica | perigo | 3.2 → 4.4 | código, interp., saídas | **P0** | **Sim** | `resolvido` | `metodologia-alterada` | 01 | [AUD-06](issues/AUD-06_duration_component_validity.md) |
| **AUD-07** | Ranking robusto no topo e à ponderação; **não interpretável abaixo da posição ~20** — 94 municípios com < 10 eventos | analise-sensibilidade | perigo → integração | 4.4 | interp., saídas, doc. | **P0** | Sim — satisfeito por publicação da sensibilidade e dos ICs | `resolvido` | `resultado-validado-mantido` | — | [AUD-07](issues/AUD-07_hazard_aggregation_stability.md) |
| **AUD-08** | Exposição: saturação do termo relativo e MAUP; **população efetiva implementada** | fragilidade-metodologica | exposição | 4.2 → 4.4 | código, interp., saídas | P1 | Sim, salvo qualificação | `em-investigacao` | — | — | [AUD-08](issues/AUD-08_exposure_spatial_support.md) |
| **AUD-09** | SVI: duas cargas negativas do PC1 — **sem erro de codificação**; CDF implementada | fragilidade-metodologica | vulnerabilidade | 4.3 | interp., doc. | P1 | Sim, salvo qualificação | `em-investigacao` | — | **11** | [AUD-09](issues/AUD-09_svi_directionality.md) |
| **AUD-10** | Camada de vulnerabilidade física ausente, apesar de declarada | inconsistencia-documental | vulnerabilidade | 4.3 | interp., doc. | P1 | Sim, salvo qualificação | `resolvido` | `limitacao-reconhecida` | — | [AUD-10](issues/AUD-10_physical_vulnerability_missing.md) |
| **AUD-11** | Ancoragem amostral **reduzida 26×, não eliminada**: `sd(PC1)` continua da amostra e é material em escala de domínio | risco-interpretacao | integração | 4.4 | código, interp., saídas, doc. | P1 | Sim — satisfeito por declaração | `resolvido` | `mitigado-parcialmente` | — | [AUD-11](issues/AUD-11_minmax_chain_and_sample_anchoring.md) |
| **AUD-12** | Contaminação estuarina e fluvial no estuário amazônico | qualidade-dados | perigo | 2a → 3.1/3.2 | dados, interp., saídas | P1 | Não — top-10 já não depende desses pontos | `resolvido` | `resultado-validado-mantido` | 01 | [AUD-12](issues/AUD-12_estuarine_river_contamination.md) |
| **AUD-13** | Índice integrado: conduzido pelo perigo (84,7 %); cancelamento dominante passou a ser H × V | analise-sensibilidade | integração | 4.4 | interp., saídas, doc. | P1 | Sim, salvo qualificação | `resolvido` | `resultado-validado-mantido` | 01, 02 | [AUD-13](issues/AUD-13_integrated_index_behaviour.md) |
| **AUD-14** | População sazonal invisível (censo *de jure*) | qualidade-dados | exposição | 4.2 | interp., doc. | P2 | Não | `resolvido` | `limitacao-reconhecida` | — | [AUD-14](issues/AUD-14_seasonal_population.md) |
| **AUD-15** | Cobertura: **Içara não tem frente de mar** — ausência correta; 4 degenerados, 83 sem perigo aceito, fronteira de zero instável | qualidade-dados | integração | 4.1/4.2/4.4 | dados, interp., saídas, doc. | P2 | Não | `resolvido` | `limitacao-reconhecida` | — | [AUD-15](issues/AUD-15_sample_coverage.md) |
| **AUD-16** | **Não existem hotspots discretos** (Silverman p = 0,56 nos positivos); definição adotada é por intervalo de posto | risco-interpretacao | integração | 4.4/4.5 | interp., saídas, doc. | P2 | Não | `resolvido` | `resultado-validado-mantido` | 11 | [AUD-16](issues/AUD-16_hotspot_definition.md) |
| **AUD-17** | Quatorze inconsistências documentação ↔ código ↔ saídas (8 originais + 6 de 2026-07-31) | **inconsistencia-documental** | transversal | 3 + 4 + README + site | doc., saídas | P1 | Sim, salvo correção | `em-investigacao` | — | 09, 12 | [AUD-17](issues/AUD-17_documentation_code_consistency.md) |
| **AUD-18** | Calibração é 100 % catarinense; busca por base no N/NE dá **negativo qualificado** — não é irremediável, é não explorada | lacuna-validacao | transversal | 2d/2e → 3 → 4 | dados, interp., doc. | P1 | Sim — satisfeito por declaração | `resolvido` | `limitacao-reconhecida` | — | [AUD-18](issues/AUD-18_independent_validation_gap.md) |

---

## 3. Grafo de dependências

```
AUD-01 (sizígia) ────┬──► AUD-05 (validação de casos)
AUD-02 (limiar Hs) ──┤        ▲
AUD-04 (associação) ─┤        │
AUD-06 (duração) ────┤        │
AUD-08 (exposição) ──┤        │
AUD-09 (SVI) ────────┤        │
AUD-11 (Min–Max) ────┴────────┘

AUD-01 ◄──► AUD-06   PAR INDISSOCIÁVEL (demonstrado em 2026-07-29):
                     nenhuma das duas correções isoladas é defensável.
                     top-10 ao N de 20°S — legado+3comp 70 % · legado+2comp 90 %
                                         · MHWS+3comp   90 % · MHWS+2comp   30 %

AUD-01 ──► AUD-12 (contaminação estuarina)
AUD-01, AUD-02 ──► AUD-13 (comportamento do índice)
                   As tres fecharam em 2026-07-31. A dependencia AUD-02 -> AUD-13
                   foi resolvida por DECLARACAO, nao por remocao: com
                   rho(perigo, risco) = 0,893 o indice propaga integralmente o
                   criterio percentilico de onda, que agora e uma limitacao
                   declarada. Se um piso fisico for adotado no futuro (rota do
                   wave setup), AUD-13 tem de ser remedida por inteiro (§3-bis).
AUD-11 ──► AUD-16 (definição de hotspot)

Acrescentadas em 2026-07-31:
AUD-11 ──► AUD-09  (âncoras exatas do Min–Max: a alternativa por posto
                    percentílico NÃO é neutra no risco, ρ = 0,958)
AUD-04 ──► AUD-15  (Içara continua sem associação)
AUD-09, AUD-12 ──► AUD-17  (podem ainda mexer em produtos; a checklist de
                    rechecagem está em AUD-17 §15)

Sem dependências (podem começar imediatamente):
  AUD-01, AUD-02, AUD-03, AUD-04, AUD-06, AUD-07,
  AUD-08, AUD-09, AUD-10, AUD-11, AUD-14, AUD-15,
  AUD-17, AUD-18
```

**AUD-05 é terminal**: não tem correção própria; é a suíte de aceitação que
fecha quando as sete questões das quais depende fecharem.

---

## 4. Agrupamento por natureza do problema

| Natureza | Questões |
|---|---|
| **Erro de implementação confirmado** | AUD-04 (regra documentada não se reproduz), AUD-17 (afirmações falsas no código e nos metadados publicados) |
| **Fragilidade metodológica** | AUD-01, AUD-02, AUD-03, AUD-06, AUD-08, AUD-09 |
| **Lacuna de validação** | AUD-05, AUD-18 |
| **Risco de interpretação** | AUD-11, AUD-16 |
| **Qualidade de dados** | AUD-12, AUD-14, AUD-15 |
| **Análise de sensibilidade pendente** | AUD-07, AUD-13 |
| **Inconsistência documental** | AUD-10, AUD-17 |
| **Melhoria opcional** | *nenhuma registrada como questão autônoma — ver §7* |

---

## 5. Agrupamento por componente do risco

| Componente | Questões |
|---|---|
| **Perigo** | AUD-01, AUD-02, AUD-03, AUD-06, AUD-12 |
| **Exposição** | AUD-08, AUD-14 |
| **Vulnerabilidade** | AUD-09, AUD-10 |
| **Integração** | AUD-05, AUD-07, AUD-11, AUD-13, AUD-15, AUD-16 |
| **Transversal** | AUD-17, AUD-18 |

---

## 6. Ordem de trabalho recomendada

A ordem abaixo respeita as dependências e concentra os reprocessamentos caros
(catálogos do Step 3) em uma única execução.

| Onda | Questões | Racional |
|---|---|---|
| **1 — sem custo de reprocessamento** | AUD-17, AUD-07, AUD-13, AUD-11 | Correção documental e consolidação de diagnósticos já executados. Nenhuma depende de decisão científica pendente; AUD-17 pode fechar integralmente |
| **2 — decisões sobre o detector** | AUD-01, AUD-02, AUD-03, AUD-12, AUD-18 | Todas tocam o catálogo do Step 3. **Decidir as cinco em conjunto e reprocessar uma única vez** |
| **3 — camadas municipais** | AUD-04, AUD-06, AUD-08, AUD-09, AUD-15 | Posteriores ao Step 3; exigem apenas reexecutar o exportador e as figuras |
| **4 — enquadramento e escopo** | AUD-10, AUD-14, AUD-16 | Predominantemente documentais; dependem do método final |
| **5 — aceitação** | AUD-05 | Fecha por último, verificando o produto resultante |

---

## 7. Achados da revisão **não** convertidos em questão autônoma

Registrados aqui para que a rastreabilidade fique completa e nenhum achado se
perca por omissão.

| Achado da revisão | Onde foi absorvido | Por quê |
|---|---|---|
| Pontos fortes (§1): rastreabilidade do código, estrutura espacial correta da frequência, normalização de intensidade por excesso local, média geométrica conjuntiva, SVI reprodutível | Citados como evidência dentro de AUD-02 §7.2, AUD-09 §3.5, AUD-13 §7.3 | Não são fragilidades. Preservados no registro de linha de base e usados como contra-argumento nas questões relevantes |
| Reconstrução da metodologia implementada (§2.1) | `baseline/…` §2.1; replicada por partes nas §4 de cada questão | É contexto, não problema acionável |
| Anomalia de `pop_house` pré-normalizado | AUD-17 §3, item adicional | Já auditado em 2026-07-28 e demonstrado inócuo para o índice; pendência apenas de coerência entre coluna publicada e definição no manuscrito |
| Pseudo-replicação espacial (178 pontos para 280 municípios) | AUD-04 §2 e §3; consequência tratada em AUD-16 §10 | É uma consequência direta da associação, não um problema independente |
| Casos Campos dos Goytacazes e Linhares (§6.2) | AUD-08 §3.2 (causa) e AUD-05 §3.1 (teste) | Mesmo mecanismo do MAUP da exposição; separá-los duplicaria contexto |
| Subestimação de Osório e Santa Vitória do Palmar (§6.3) | AUD-13 §7 (compensação E × V) | Manifestação do cancelamento estrutural, já rastreado |
| Subestimação de Recife/Olinda/Jaboatão (§6.4) | AUD-18 §3.5 | É uma lacuna de validação (não há base regional para decidir se está certo), não uma fragilidade de método |
| Melhoria opcional: setor censitário costeiro como unidade (§9.3 item 15) | AUD-08 §8.5 e §10 | Alternativa de suporte espacial dentro da questão de exposição; não é problema autônomo |
| Melhoria opcional: sensibilidade `mean` vs. `p95` (§9.3 item 17) | AUD-06 §8.2 | Diagnóstico dentro da questão da duração |
| Melhoria opcional: estimar população sazonal (§9.3 item 16) | AUD-14 §8.3–8.4 | Diagnóstico dentro da questão da população sazonal |
| Lista de verificação pré-submissão (§9.1 lista final) | Distribuída pelos critérios de resolução (§9) das questões correspondentes | Cada item tem dono; manter uma segunda lista criaria duas fontes de verdade |

Nenhum achado da revisão de linha de base foi descartado.

### Achado novo, posterior à revisão de linha de base

| Achado | Onde foi registrado | Quando |
|---|---|---|
| O mapa de estrutura do `README.md` (L480–485, L496–499) aponta módulos do Step 3 e do Step 4 em diretórios onde eles não estão | AUD-17 §3 item **#8** | 2026-07-29, durante a criação desta estrutura. Induziu erro real de referência, corrigido em AUD-02 §4 e AUD-03 §4 |
| Documentação e site descreviam os Steps 3.1 e 3.3–3.8 como lendo catálogos `SSH_total` superseded, o que deixou de ser verdade com o commit `eee6142` | AUD-17 §3 item **#9** | 2026-07-31. A regeneração do Step 3 **criou** a inconsistência ao corrigir a ciência |
| Resíduo extenso do Hazard Index de três componentes e da fórmula de risco de duas componentes, sobrevivendo em sete arquivos do site e do `src/` depois de corrigidos no README em 2026-07-29 | AUD-17 §3 itens **#10** e **#11** | 2026-07-31 |
| `outputs/storm_catalog/compound/` é **misturado**, não legado: catálogo corrente de 16 768 eventos ao lado de sumário legado que reporta 96 031, sem distinção | AUD-17 §9 item **#14** | 2026-07-31 |
| 83 municípios com `Hazard_Index_mun` exatamente 0, por associação a ponto sem evento aceito — categoria de cobertura que o método anterior não podia produzir | AUD-15 §14 e §9, critério novo | 2026-07-31 |
| O erro de fase do nível somado é ~10× maior no Sul micromareal que no Norte macromareal — o inverso do que a revisão de linha de base previa | AUD-03 §14 | 2026-07-31 |
| O portão HAT é monotônico em latitude — HAT médio de 0,49 m a 2,61 m do RS ao AP — e produz o gradiente de perigo por um mecanismo de maré independente do clima de tempestades | AUD-13 §3-bis.8 | 2026-07-31 |
| A correlação marginal entre vulnerabilidade e risco é negativa (−0,372) com parcial +0,790: supressão induzida pela anticorrelação perigo–vulnerabilidade | AUD-13 §3-bis.3 e §3-bis.4 | 2026-07-31 |
| A escolha entre média geométrica e aritmética deixou de ser quase neutra (ρ 0,934) e passou a determinar o resultado (ρ 0,550) | AUD-13 §3-bis.5; consequência para AUD-07 | 2026-07-31 |
| O bootstrap por município perdeu o objeto: com âncoras fixas, reamostrar municípios desloca postos em exatamente 0,0 | AUD-07 §3-bis.1 | 2026-07-31 |
| 94 dos 196 municípios com risco positivo têm menos de dez eventos aceitos; o 21º do país tem **um**. A severidade é média condicional e não escala com raridade | AUD-07 §3-bis.4 | 2026-07-31 |
| A fronteira zero/não-zero é amostralmente instável: só 102 dos 280 municípios são robustamente não nulos | AUD-07 §3-bis.4; declarado em AUD-15 | 2026-07-31 |
| Içara/SC não tem frente de mar desde o desmembramento de Balneário Rincão (2003/2013): sua ausência do produto está correta, não é falha de associação | AUD-15 §3-bis.3 | 2026-07-31 |
| Santa Rita/MA tem 1,98 km de frente de mar — é costeira por critério geométrico, contra o que o registro supunha | AUD-15 §3-bis.4 | 2026-07-31 |
| Não existem hotspots discretos: entre os 196 municípios com evento aceito a distribuição é unimodal (Silverman p = 0,56) e o Fisher–Jenks não tem cotovelo | AUD-16 §3-bis.1 | 2026-07-31 |
| Getis-Ord Gi\* é inviável neste produto: 32,6 % dos pares de vizinhança compartilham ponto de grade e têm perigo idêntico por construção | AUD-16 §3-bis.3 | 2026-07-31 |

---

## 8. Como atualizar este rastreador

1. Ao mudar a situação de uma questão, atualize **a linha da tabela mestra** e o
   cabeçalho do registro correspondente. As duas devem sempre concordar.
2. Ao fechar uma questão, preencha **Desfecho** nos dois lugares e atualize os
   contadores da §1 e do cabeçalho.
3. Ao arquivar, mova a linha para a §9 e o arquivo para `issues/archive/`.
   **Nunca apague uma linha.**
4. Ao criar uma questão nova, use o próximo `AUD-NN` livre, copie
   [`ISSUE_TEMPLATE.md`](ISSUE_TEMPLATE.md), e acrescente linha na tabela mestra,
   nos agrupamentos das §4 e §5, e no grafo da §3 se houver dependência.
5. **Não marque nada como `resolvido` sem que todos os critérios de aceitação da
   §9 do registro estejam verificados e o histórico da §14 documente a
   verificação.** Alteração de código não é evidência de resolução.

---

## 9. Questões arquivadas

*Nenhuma.*

| ID | Título | Desfecho | Absorvida por | Data |
|---|---|---|---|---|
| — | — | — | — | — |
