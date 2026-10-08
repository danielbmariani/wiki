---
id: BR
autor: agente:claude-fable-5
data: 2026-10-08
fontes: [mariani-voto-renda-2026]
status: rascunho
---

# Voto e renda por setor censitário e área de ponderação (Daniel Mariani)

Estimativas de voto (2022 T1 e T2; 2026 T1) por setor censitário e por
área de ponderação do Censo 2022, com renda, demografia e religião do
IBGE. Pipeline de Daniel Mariani; método do
deltafolha/eleicoes-por-setores-censitarios, estendido (geolocalização
complementada por CNEFE, auditoria contra boletins de urna, Censo 2022 e
nível área de ponderação). Cópia em `dados/mariani/` da Colmeia; portal
canônico com CSVs por UF: https://dados-eleicoes.danielmariani.com.br

- `setores`: https://dados-eleicoes.danielmariani.com.br/dados/setores_eleicao_renda.parquet — SHA-256 `41612b59c22b76cf47c7648467423b88bb5fe320cf8569febdcbfc8c5d68d722` (468.099 linhas)
- `apond`: https://dados-eleicoes.danielmariani.com.br/dados/apond_completo.parquet — SHA-256 `9a38a275fc4d5bda21c722d4a09729498d91957eb492f828b8daac9c1dc9b0c7` (14.270 linhas)
- `apond-csv`: https://dados-eleicoes.danielmariani.com.br/dados/apond_completo.csv — SHA-256 `92784723502329ac6250847be7ca3abfb000e039f43d40ed78819c26ee42e930`
- `setor-apond`: https://dados-eleicoes.danielmariani.com.br/dados/setor_apond.csv.gz — SHA-256 `66e3acb273cfa3338b923ccb258a9023cf722e07b0ecd1582f99351491e940a8` (correspondência 468.097 setores → 14.406 áreas)
- `malha-apond`: https://s831wlcouwnuetu4.public.blob.vercel-storage.com/apond_malha_2022.gpkg — SHA-256 `37b38f932bfd5080a91e84e76410248485c8274aeff9814752b65f5f4fafdaf6` (GeoPackage, 395 MB, dissolve da malha de setores 2022; o IBGE não publica essa geometria)
- `dicionario`: https://dados-eleicoes.danielmariani.com.br/dados/dicionario_dados.csv — descrição de todas as colunas

- **Licença:** CC BY 4.0 — citar "Daniel Mariani, dados-eleicoes.danielmariani.com.br, 2026; dados TSE e IBGE (Censo 2022)".
- **Método e auditoria:** https://dados-eleicoes.danielmariani.com.br/metodologia (zero divergências entre boletins de urna e votação por seção em 749 milhões de votos; 2022 reproduz o resultado oficial).
- **Usado para:** `dados/mariani/` na Colmeia; cruzamentos de voto com renda per capita, religião e classe por área de ponderação.
