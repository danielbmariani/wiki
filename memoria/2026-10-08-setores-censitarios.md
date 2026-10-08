---
autor: agente:claude-opus-5-5
data: 2026-10-08
fontes: [ibge-tse-setores-2026]
status: rascunho
---

# Setores censitários: armadilhas dos dados

- Malha `BR_setores_CD2022.zip` (IBGE): 468.099 setores, `CD_SETOR` com 15 dígitos, SIRGAS 2000
  (EPSG:4674). Ler com filtro `where` no zip leva ~2 min por UF; `setores.py` lê a malha uma vez e grava
  um GeoParquet por UF em `.cache/fontes/malha/`.
- `NM_BAIRRO` vem vazio na maior parte do país; o painel cai para subdistrito e distrito.
- `eleitorado_local_votacao_2026.zip` tem um CSV por UF **e** `_BRASIL.csv`: pegar o `_BRASIL`,
  senão a leitura pega só a primeira UF e quase nenhum local ganha coordenada.
- Coordenadas do TSE usam vírgula e às vezes vêm como `,6057` ou `-,1160`; `-1` significa sem coordenada.
  Sem coordenada: 1,8% dos locais em 2026 e 8,2% em 2022.
- `votacao_secao_<ano>_BR.zip` traz só presidente e já tem `NR_LOCAL_VOTACAO`; `detalhe_votacao_secao`
  traz aptos, abstenções, brancos e nulos por seção e cargo (presidente = `CD_CARGO` 1) no `_BRASIL.csv`.
- Totais conferidos sem o exterior: 2022 T2 Lula 60.193.094 × Bolsonaro 58.061.090; 2026 T1
  Lula 53.722.151 × Flávio 55.960.603.
- Município TSE → IBGE: o pipeline associa pelo setor mais próximo de cada local de votação
  (moda por município), sem tabela externa.
- O repositório de referência (deltafolha) não tem licença: seguimos o método, não copiamos código.
- Tiles: um PMTiles com camadas `municipios` (z0–10) e `setores` (z10–12, overzoom no navegador),
  `-S4`, 225 MB no país. Com setores a partir de z8, tiles de SP chegavam a 1 MB e o mapa travava;
  a partir de z10 o maior tile tem 371 KB e o p95 fica em 21 KB.
- Pipeline nacional: ~30 min numa máquina de 20 núcleos (SP sozinho, 103 mil setores, ~5 min); saída
  total ~350 MB (PMTiles + 122 MB de painéis por subdistrito, maior arquivo 620 KB).
- "Espaço para conversar" (abstenção + brancos + nulos ≥ diferença) vale para quase todo setor urbano:
  em Maceió, 1.597 de 1.620. A rampa de cor diferencia, mas a contagem do chamado à ação diz pouco.
