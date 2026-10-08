"""Gera dados/ a partir do arquivo de locais de votação do TSE.

Uso:
    python scripts/gerar_dados.py [caminho/para/eleitorado_local_votacao_2026.zip]

Sem argumento, baixa o arquivo do portal de dados abertos do TSE.
"""

import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

from colmeia import layout_hexagonal
from comum import DADOS, RAIZ, UFS

URL_TSE = (
    "https://cdn.tse.jus.br/estatistica/sead/odsele/eleitorado_locais_votacao/"
    "eleitorado_local_votacao_2026.zip"
)
FONTE_ID = "tse-eleitorado-local-votacao-2026"
URL_MALHA = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
)

ROMANOS = re.compile(r"^(i{2,3}|iv|vi{1,3}|ix|xi{0,3}|xx)$")
MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "a", "o"}


def titulo(texto):
    palavras = texto.strip().lower().split()
    saida = []
    for i, p in enumerate(palavras):
        if ROMANOS.match(p):
            saida.append(p.upper())
        elif i > 0 and p in MINUSCULAS:
            saida.append(p)
        elif p.startswith("d'") and len(p) > 2:
            saida.append("d'" + p[2:].capitalize())
        else:
            saida.append("-".join(s.capitalize() for s in p.split("-")))
    return " ".join(saida)


def coordenada(valor):
    try:
        v = float(valor.replace(",", "."))
    except ValueError:
        return None
    return None if v == -1 else v


def abrir_csv(zip_path):
    z = zipfile.ZipFile(zip_path)
    nome = next(n for n in z.namelist() if n.endswith("_BRASIL.csv"))
    return io.TextIOWrapper(z.open(nome), encoding="latin-1", newline="")


def ler_tse(zip_path):
    zonas = defaultdict(lambda: {"m": set(), "e": 0, "locais": {}})
    municipios = {}
    for row in csv.DictReader(abrir_csv(zip_path), delimiter=";"):
        if row["NR_TURNO"] != "1":
            continue
        uf = row["SG_UF"]
        zid = f"{uf}-{int(row['NR_ZONA']):03d}"
        mid = f"{uf}-{row['CD_MUNICIPIO']}"
        municipios.setdefault(mid, titulo(row["NM_MUNICIPIO"]))
        zona = zonas[zid]
        zona["m"].add(mid)
        eleitores = int(row["QT_ELEITOR_SECAO"] or 0)
        zona["e"] += eleitores
        local = zona["locais"].setdefault(row["NR_LOCAL_VOTACAO"], {
            "nome": titulo(row["NM_LOCAL_VOTACAO"]),
            "bairro": titulo(row["NM_BAIRRO"]),
            "m": mid,
            "lat": coordenada(row["NR_LATITUDE"]),
            "lon": coordenada(row["NR_LONGITUDE"]),
            "e": 0,
        })
        local["e"] += eleitores
    return zonas, municipios


def centroide(locais):
    pontos = [(l["lat"], l["lon"], max(l["e"], 1)) for l in locais if l["lat"] and l["lon"]]
    if not pontos:
        return None
    peso = sum(p[2] for p in pontos)
    return (
        sum(p[0] * p[2] for p in pontos) / peso,
        sum(p[1] * p[2] for p in pontos) / peso,
    )


def escrever_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def main():
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path("/tmp/eleitorado_local_votacao_2026.zip")
        print(f"Baixando {URL_TSE}…")
        urllib.request.urlretrieve(URL_TSE, zip_path)

    sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zonas, nomes_municipios = ler_tse(zip_path)

    municipios = {mid: {"n": nome, "z": []} for mid, nome in nomes_municipios.items()}
    celulas_zonas, centroides = {}, {}
    for zid in sorted(zonas):
        z = zonas[zid]
        celulas_zonas[zid] = {"m": sorted(z["m"]), "e": z["e"], "l": len(z["locais"])}
        for mid in z["m"]:
            municipios[mid]["z"].append(zid)
        c = centroide(z["locais"].values())
        if c and not zid.startswith("ZZ"):
            centroides[zid] = c

    ufs = {}
    for uf, nome in UFS.items():
        ufs[uf] = {
            "n": nome,
            "z": sum(1 for z in celulas_zonas if z.startswith(uf + "-")),
            "m": sum(1 for m in municipios if m.startswith(uf + "-")),
        }

    escrever_json(DADOS / "celulas.json", {
        "fonte": FONTE_ID,
        "ufs": ufs,
        "municipios": municipios,
        "zonas": celulas_zonas,
    })

    for uf in UFS:
        zids = [z for z in celulas_zonas if z.startswith(uf + "-")]
        mids = sorted(m for m in municipios if m.startswith(uf + "-"))
        zi, mi = {z: i for i, z in enumerate(zids)}, {m: i for i, m in enumerate(mids)}
        locais = []
        for zid in zids:
            for l in zonas[zid]["locais"].values():
                locais.append([l["nome"], l["bairro"], mi[l["m"]], zi[zid]])
        locais.sort()
        escrever_json(DADOS / "busca" / f"{uf}.json", {"m": mids, "z": zids, "l": locais})

    with urllib.request.urlopen(URL_MALHA) as r:
        bruto = r.read()
    malha = json.loads(gzip.decompress(bruto) if bruto[:2] == b"\x1f\x8b" else bruto)
    escrever_json(DADOS / "colmeia.json", layout_hexagonal(centroides, malha, tamanho=0.12))

    ficha = RAIZ / "fontes" / f"{FONTE_ID}.md"
    ficha.write_text(f"""---
id: BR
autor: humano:pipeline
data: {date.today().isoformat()}
fontes: [{FONTE_ID}]
status: revisado
---

# Eleitorado por local de votação 2026 (TSE)

- **Origem:** {URL_TSE}
- **Arquivo:** `eleitorado_local_votacao_2026_BRASIL.csv` (dentro do zip), turno 1
- **SHA-256 do zip:** `{sha256}`
- **Licença:** dados abertos do TSE (Portal de Dados Abertos, uso livre com citação da fonte)
- **Usado para:** `dados/celulas.json`, `dados/busca/*.json`, `dados/colmeia.json`
- **Contorno das UFs:** malha do IBGE, qualidade mínima ({URL_MALHA})

Totais: {len(celulas_zonas)} zonas, {len(municipios)} municípios
({sum(1 for m in municipios if m.startswith('ZZ-'))} no exterior),
{sum(len(z['locais']) for z in zonas.values())} locais de votação.
""", encoding="utf-8")

    print(f"{len(celulas_zonas)} zonas, {len(municipios)} municípios, "
          f"{len(centroides)} zonas na colmeia")


if __name__ == "__main__":
    main()
