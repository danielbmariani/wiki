---
id: BR
autor: agente:claude-opus-5-5
data: 2026-10-08
fontes: []
status: rascunho
---

# Separação em três repositórios

- **Objetivo:** dividir o repositório `colmeia` em site + geodados (`colmeia`), base de conhecimento
  (`wiki`) e lista de ferramentas (`diretorio`).
- **Entradas:** `colmeia` em `2109559`: `inteligencia/`, `pipeline/`, `diretorio.md`.
- **Modelo:** claude-opus-5-5 (Claude Code).
- **Saídas:**
  - `wiki`: `memoria/`, `analises/`, `execucoes/`, `fontes/` na raiz; `pipeline/` virou `scripts/`,
    sem `carimbar.py`. `comum.py` acha a Colmeia em `COLMEIA_DIR` (padrão `../colmeia`); as fichas vão
    para `fontes/`. `checar.py` checa as pastas da raiz. 38 testes passando.
  - `diretorio`: `README.md` = antigo `diretorio.md`. A Action do site baixa o arquivo no build.
  - `colmeia`: fica com site, `dados/`, quadros, grupos e as checagens dos PRs (`checar.py`,
    `carimbar.py`, `comum.py`). Sai a Action `dados.yml` e a opção de regerar dados no `site.yml`.
  - Repositórios novos começam sem histórico; o histórico antigo continua no `colmeia`.
- **Em aberto:**
  - A Action desta wiki faz checkout da `colmeia` (privada) e precisa do segredo `COLMEIA_TOKEN`
    com leitura dela.
  - Regerar os dados e abrir PR na `colmeia` a partir da wiki (antigo `dados.yml`) ainda não tem
    Action.
