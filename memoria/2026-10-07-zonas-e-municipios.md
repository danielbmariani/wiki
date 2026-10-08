---
autor: agente:claude-opus-5-5
data: 2026-10-07
fontes: [tse-eleitorado-local-votacao-2026]
status: rascunho
---

# Zonas e municípios: armadilhas dos dados do TSE

- `NR_ZONA` só é único dentro da UF. A chave é `SG_UF` + `NR_ZONA` (ID `SP-001`), e há lacunas na numeração.
- Zona ↔ município é muitos-para-muitos: muitas zonas cobrem vários municípios, e grandes cidades têm
  dezenas de zonas. A relação vem dos locais de votação (`dados/celulas.json`).
- O arquivo traz os dois turnos com as mesmas linhas; o pipeline usa só `NR_TURNO = 1`.
- `ZZ` (exterior) tem uma única zona (`ZZ-001`) e 186 "municípios" (cidades no exterior). Entra na busca,
  fica fora da colmeia (não há coordenadas).
- Coordenadas ausentes vêm como `-1`. O centroide da zona é a média dos locais ponderada pelo eleitorado.
- Encoding latin-1, separador `;`.
