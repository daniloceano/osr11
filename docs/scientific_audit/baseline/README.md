# `baseline/` — Registros de linha de base da auditoria

Este diretório guarda **revisões científicas completas, preservadas sem
alteração**, que servem de referência histórica para a auditoria.

## Regra de imutabilidade

Arquivos deste diretório **não são editados após a criação**. Eles registram o
que era sabido, medido e concluído em uma data específica. Corrigir, atualizar
ou reinterpretar um registro de linha de base destruiria a capacidade de mostrar
a um revisor, editor ou colaborador *o que foi encontrado* e *o que foi feito a
respeito*.

Se uma afirmação de um registro de linha de base for posteriormente refutada,
isso é documentado no registro de questão correspondente
(`../issues/AUD-*.md`, seção **Histórico de investigação**), nunca alterando o
registro de linha de base.

Correções de forma são aceitáveis apenas quando necessárias para que o Markdown
continue legível (níveis de cabeçalho, escape de caracteres). Qualquer correção
de forma aplicada deve ser declarada no cabeçalho do próprio arquivo.

## Convenção de nomes

```
YYYY-MM-DD_<slug em inglês>.md
```

## Registros existentes

| Arquivo | Data | Escopo | Questões derivadas |
|---------|------|--------|--------------------|
| `2026-07-29_initial_review.md` | 2026-07-29 | Revisão científica e metodológica independente da cadeia perigo → exposição → vulnerabilidade → risco (Steps 2 a 4), com diagnósticos quantitativos sobre `outputs/` e `site/public/data/` | AUD-01 a AUD-18 |

## Como citar um registro de linha de base

Nos registros de questão, use o formato:

```
baseline/2026-07-29_initial_review.md §3.1(a)
```

com a seção da revisão, não o número de linha — os números de linha mudam se o
Markdown for reprocessado, as seções não.
