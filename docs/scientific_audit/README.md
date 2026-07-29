# Auditoria científica do OSR11 — guia do fluxo de trabalho

Este diretório converte a revisão científica independente dos resultados de
risco costeiro em um **fluxo de auditoria rastreável e incremental**, no qual
cada fragilidade pode ser investigada de forma isolada, por sessões de trabalho
distintas, sem que seja necessário reler a revisão inteira.

---

## Estrutura

```
docs/scientific_audit/
├── README.md                          # este guia
├── ISSUE_TRACKER.md                   # rastreador central — comece por aqui
├── ISSUE_TEMPLATE.md                  # gabarito para novas questões
├── baseline/
│   ├── README.md                      # regra de imutabilidade
│   └── 2026-07-29_initial_review.md   # revisão original preservada
└── issues/
    ├── AUD-01_*.md … AUD-18_*.md      # um registro por questão acionável
    └── archive/                       # questões fundidas ou substituídas
```

---

## Os três níveis, e o que cada um responde

| Nível | Documento | Responde |
|-------|-----------|----------|
| Histórico | `baseline/` | *O que foi encontrado, e quando?* — imutável |
| Situação | `ISSUE_TRACKER.md` | *Onde estamos agora, e o que bloqueia a submissão?* |
| Trabalho | `issues/AUD-NN_*.md` | *O que exatamente investigar, com que evidência e sob que critério de aceitação?* |

O registro de linha de base **nunca** é editado. O rastreador é atualizado a
cada mudança de situação de uma questão. Os registros de questão acumulam
histórico cronológico.

---

## Sistema de identificadores

`AUD-NN`, com dois dígitos, atribuído sequencialmente na ordem de criação.

O identificador é **opaco e permanente**: não codifica prioridade, componente
nem situação, porque todos esses atributos mudam ao longo da investigação e o
identificador não pode mudar — ele é citado em commits, mensagens e no
manuscrito. Uma questão fundida em outra mantém seu arquivo, movido para
`issues/archive/`, com situação `arquivado` e o campo **Desfecho** preenchido.

Nome de arquivo: `AUD-NN_<slug_snake_case_em_ingles>.md`, seguindo a convenção
de nomes em inglês já adotada por todo o repositório para caminhos e
identificadores. O **conteúdo** é em português.

---

## Vocabulário controlado

### Tipo (`Tipo`)

| Valor | Significado |
|-------|-------------|
| `erro-implementacao` | O código não faz o que a metodologia declara. Confirmado por inspeção ou execução |
| `fragilidade-metodologica` | O código faz o que foi declarado, mas a escolha metodológica é questionável |
| `lacuna-validacao` | Falta evidência independente para sustentar ou refutar um resultado |
| `risco-interpretacao` | O resultado pode ser lido como algo que não é |
| `qualidade-dados` | Limitação da entrada, não da análise |
| `analise-sensibilidade` | Teste de robustez ainda não executado ou não publicado |
| `inconsistencia-documental` | Documentação, código e saídas discordam entre si |
| `melhoria-opcional` | Aprimoraria o trabalho, mas não afeta a defensabilidade |

### Prioridade (`Prioridade`)

| Valor | Significado |
|-------|-------------|
| `P0` | **Bloqueia a publicação.** O resultado não pode ser apresentado sem resolução ou sem uma qualificação explícita no manuscrito |
| `P1` | Exige resolução **ou** justificativa explícita e documentada antes da submissão |
| `P2` | Recomendado antes da submissão; a ausência enfraquece a resposta a revisores |
| `P3` | Melhoria opcional; pode ficar para trabalho futuro |

### Situação (`Status`)

| Valor | Significado |
|-------|-------------|
| `aberto` | Registrado, ainda não investigado |
| `em-investigacao` | Alguma sessão está produzindo diagnósticos |
| `aguardando-decisao` | Diagnósticos concluídos; falta uma decisão científica humana |
| `bloqueado` | Depende de outra questão ainda não resolvida |
| `resolvido` | Fechado com um desfecho registrado e critérios de aceitação satisfeitos |
| `arquivado` | Fundido em outra questão ou tornado obsoleto |

### Desfecho (`Desfecho`) — preenchido apenas no fechamento

| Valor | Significado |
|-------|-------------|
| `erro-confirmado-corrigido` | Havia um erro de implementação; foi corrigido e validado |
| `metodologia-alterada` | A escolha metodológica foi mudada deliberadamente |
| `resultado-validado-mantido` | O resultado suspeito foi examinado e **mantido**, com justificativa |
| `mitigado-parcialmente` | A preocupação foi reduzida, mas não eliminada |
| `limitacao-reconhecida` | Permanece como limitação declarada no manuscrito |
| `substituido-ou-fundido` | Absorvido por outra questão |
| `sem-acao-necessaria` | O exame mostrou que não havia problema |

> **Um resultado inesperado não é, por si só, um erro.** O objetivo da auditoria
> é decidir se os resultados são **defensáveis**, não forçá-los a concordar com a
> literatura prévia ou com a expectativa do analista. `resultado-validado-mantido`
> é um desfecho tão legítimo quanto `erro-confirmado-corrigido`.

---

## Como trabalhar uma questão

1. **Ler apenas o registro da questão.** Ele é autocontido por construção. Se
   depender fortemente de outra, a dependência está declarada — leia a
   dependência, não a revisão inteira.
2. **Mudar a situação** para `em-investigacao` no registro e no rastreador.
3. **Executar os diagnósticos propostos** (seção 8 do registro). Escrever
   scripts novos em `src/exploratory/`, seguindo a convenção existente:

   ```
   src/exploratory/audit_AUD_NN_<slug>.py   →   outputs/audit/AUD-NN_<slug>/
   ```

   Isso estende o padrão já usado por `src/exploratory/make_exploratory_*.py` →
   `outputs/exploratory_*/`.
4. **Registrar uma entrada no Histórico de investigação** (seção 14), usando o
   gabarito. Uma entrada por sessão, em ordem cronológica, nunca sobrescrevendo
   entradas anteriores.
5. **Confrontar os critérios de aceitação** (seção 9) explicitamente, item a
   item. Um item não verificado permanece não verificado.
6. **Fechar apenas quando todos os critérios estiverem satisfeitos**, preencher
   o **Desfecho**, e atualizar o rastreador.

### Regra de fechamento

> **Uma alteração de código, por si só, não é evidência de que a questão foi
> resolvida.** O fechamento exige demonstração — diagnóstico reproduzido,
> comparação antes/depois, produtos a jusante regenerados sem nova
> inconsistência — registrada no histórico da questão.

---

## Rastreabilidade de versionamento

Cada registro tem uma tabela **Rastreabilidade de versionamento** (seção 13),
preenchida à medida que houver trabalho real. Não se registram hashes de commit
inventados nem se afirma que um código foi alterado quando não foi.

Convenção sugerida para mensagens de commit ligadas à auditoria:

```
<tipo>(AUD-NN): <descrição>
```

Ramos, quando usados: `audit/AUD-NN-<slug>`.

---

## Manutenção incremental

- Uma questão nova recebe o próximo `AUD-NN` livre e uma linha no rastreador.
- Uma questão fundida vai para `issues/archive/` com `Status: arquivado` e
  `Desfecho: substituido-ou-fundido`, e a linha do rastreador é movida para a
  tabela de arquivadas — **nunca apagada**.
- O rastreador é o único lugar onde a situação agregada é mantida; os registros
  individuais mantêm o detalhe.
- Uma nova rodada de revisão externa gera um **novo** arquivo em `baseline/`,
  não uma edição do anterior.
