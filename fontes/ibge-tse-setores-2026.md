---
id: BR
autor: humano:pipeline
data: 2026-10-08
fontes: [ibge-tse-setores-2026]
status: revisado
---

# Setores censitários e votação por seção (IBGE e TSE)

- `malha`: https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/shp/BR/BR_setores_CD2022.zip — SHA-256 `86777db621ca40d23d19a0cb9fffa561246e3ab59dbc8cc3264da2f9cb4f0215`
- `locais-26`: https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip — SHA-256 `f75ed6866725b360a5ae2e7036e0d477944d45e36f6ccd86cd2d7ac57d7fff17`
- `locais-22`: https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/eleitorado_local_votacao_2022.zip — SHA-256 `6dc19c1ddb746cc067469e70ad5018f202334d97cd540edc8c9de3321e66da23`
- `votos-26`: https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2026_BR.zip — SHA-256 `2d42006d0f6c6e00bad83f5c23cd3d78cd3e3182dbc1ad6718222b6b132c23e1`
- `votos-22`: https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2022_BR.zip — SHA-256 `9353993de5cf03778aef44e01d4925e7ee105f5262491d344a2f0dbc956b0139`
- `detalhe-26`: https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2026.zip — SHA-256 `11a62c3a604e8b73fc328617b7688d2c635de1c76df02ba63b8f77879512f573`
- `detalhe-22`: https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip — SHA-256 `ad22c50b9e6d9dfb096a2170680a190f1734895ba89d8977b95fd63ca02c03da`

- **Licença:** dados abertos do IBGE e do TSE, uso livre com citação da fonte.
- **Método:** SPEC.md, seção 3.4, a partir de deltafolha/eleicoes-por-setores-censitarios.
- **Usado para:** `dados/setores.pmtiles`, `dados/setores/`, `dados/municipios/`, `dados/locais/`.
