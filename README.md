# Wiki da Colmeia

Base de conhecimento reproduzível e checável coletivamente: memória, análises, fontes e os scripts
que geram os dados do mapa da [Colmeia](https://github.com/colmeiabrasil/colmeia).

- `memoria/`: fatos e decisões duráveis (um arquivo por fato).
- `analises/<ID>/`: análises por célula ou nível.
- `execucoes/`: registro de cada execução de agente.
- `fontes/`: fichas das fontes de dados (origem, data, hash, licença).
- `scripts/`: pipeline IBGE + TSE e checagens.

Regras e formato em [`AGENTS.md`](AGENTS.md).

## Reproduzir os dados

Os scripts escrevem em `dados/` de um checkout da Colmeia ao lado deste repositório
(`../colmeia`, ou o caminho em `COLMEIA_DIR`) e registram as fichas em `fontes/`.

```bash
git clone https://github.com/colmeiabrasil/colmeia ../colmeia
pip install -r scripts/requirements.txt
python scripts/gerar_dados.py              # TSE: UFs, municípios, zonas, locais
python scripts/setores.py [UF ...]         # IBGE + TSE: estimativas por setor e tiles (precisa de tippecanoe)
python -m pytest scripts/testes -q
python scripts/checar.py memoria/*.md      # mesma checagem do CI
```
