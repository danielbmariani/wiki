# Instruções para agentes

Antes de trabalhar, leia este arquivo e tudo em `memoria/`. O desenho do site e dos dados está no
`SPEC.md` da [Colmeia](https://github.com/colmeiabrasil/colmeia).

## Regras

- **Só por Pull Request.** Nunca faça push direto na branch principal.
- **Identifique-se.** Todo arquivo que você criar leva `autor: agente:<modelo>`
  (ex.: `agente:claude-opus-5-5`) e `status: rascunho`. Só humanos mudam o status para `revisado`.
- **Nenhum dado pessoal.** Nada de nomes de pessoas, telefones, e-mails, CPF, CEP ou endereços
  de pessoas. Só dados agregados e lugares públicos. Nada de perfilamento individual.
- **IDs oficiais:** setor censitário do IBGE `355030805000001` (a célula); do TSE `BR`, `SP`,
  `SP-71072` (município), `SP-001` (zona). Listas válidas: `dados/setores_ids.txt.gz` e
  `dados/celulas.json` da Colmeia.
- **Reproduzível:** toda análise cita as fontes (`fontes/`) e, se usou código, o script em `scripts/`.
- Rode `python scripts/checar.py <arquivos>` antes de abrir o PR. É a mesma checagem do CI.

## Onde escrever

```
memoria/        um fato ou decisão durável por arquivo, útil para execuções futuras
analises/<ID>/  análises por célula ou nível: analises/SP-001/2026-10-20-abstencao.md
execucoes/      um registro por execução: AAAA-MM-DD-<assunto>.md
fontes/         fichas de dados: origem, data, hash, licença
scripts/        código que gera dados e análises
```

Front matter obrigatório (o `id` é opcional em `memoria/`):

```yaml
---
id: SP-001
autor: agente:claude-opus-5-5
data: 2026-10-20
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho      # rascunho | revisado | descartado
---
```

Toda execução registra: objetivo, entradas, modelo, saídas e o que ficou em aberto.
Se aprendeu algo que vale para a próxima execução (armadilha dos dados, convenção, decisão),
proponha um arquivo em `memoria/`.
