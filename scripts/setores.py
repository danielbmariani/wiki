"""Estimativas eleitorais por setor censitário (Censo 2022) e tiles do mapa.

Uso:
    python scripts/setores.py [UF ...]

Baixa as fontes para .cache/fontes (ou $COLMEIA_CACHE) e escreve em dados/:
setores.pmtiles, setores/<UF>/<prefixo>.json, municipios/<UF>.json e locais/<UF>.json.
Método: SPEC.md, seção 3.4.
"""

import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from comum import DADOS, IBGE_UF, RAIZ, SETORES_IDS, UFS
from gerar_dados import titulo

CACHE = Path(os.environ.get("COLMEIA_CACHE", RAIZ / ".cache" / "fontes"))
TSE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
FONTES = {
    "malha": "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
             "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/"
             "shp/BR/BR_setores_CD2022.zip",
    "locais-26": f"{TSE}/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip",
    "locais-22": f"{TSE}/eleitorado_locais_votacao/eleitorado_local_votacao_2022.zip",
    "votos-26": f"{TSE}/votacao_secao/votacao_secao_2026_BR.zip",
    "votos-22": f"{TSE}/votacao_secao/votacao_secao_2022_BR.zip",
    "detalhe-26": f"{TSE}/detalhe_votacao_secao/detalhe_votacao_secao_2026.zip",
    "detalhe-22": f"{TSE}/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip",
}
ELEICOES = {"26": (2026, 1, 22), "22": (2022, 2, 22)}  # ano, turno, número do adversário
LULA = 13
CRS_METROS = "EPSG:5880"
FAIXA = 100.0
PESO_MIN = 50.0
FRACA = 2000.0
GRADE_LOCAL = 50.0
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_LOCAL_VOTACAO"]
UF_IBGE = {v: k for k, v in IBGE_UF.items()}


def baixar(nome):
    destino = CACHE / FONTES[nome].rsplit("/", 1)[1]
    if not destino.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        print(f"Baixando {FONTES[nome]}…", flush=True)
        parcial = destino.with_suffix(".parcial")
        urllib.request.urlretrieve(FONTES[nome], parcial)
        parcial.rename(destino)
    return destino


def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_csv_zip(zip_path, sufixo, colunas, filtro, chunk=2_000_000):
    z = zipfile.ZipFile(zip_path)
    csvs = [n for n in z.namelist() if n.endswith(".csv")]
    nome = next((n for n in csvs if n.endswith("_BRASIL.csv")), None) or next(n for n in csvs if n.endswith(sufixo))
    partes = []
    with z.open(nome) as f:
        texto = io.TextIOWrapper(f, encoding="latin-1", newline="")
        for parte in pd.read_csv(texto, sep=";", usecols=colunas, dtype=str, chunksize=chunk):
            partes.append(filtro(parte))
    return pd.concat(partes, ignore_index=True)


def normalizar_chave(df):
    for c in ["CD_MUNICIPIO", "NR_ZONA", "NR_LOCAL_VOTACAO"]:
        df[c] = df[c].astype(int)
    return df


def locais(sufixo):
    """Locais de votação por eleição, com coordenadas e totais oficiais."""
    cache = CACHE / f"locais-{sufixo}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    ano, turno, adversario = ELEICOES[sufixo]

    cad = ler_csv_zip(
        baixar(f"locais-{sufixo}"), ".csv",
        CHAVE + ["NR_TURNO", "NM_LOCAL_VOTACAO", "NM_BAIRRO", "NR_LATITUDE", "NR_LONGITUDE"],
        lambda d: d[d.NR_TURNO == "1"].drop(columns="NR_TURNO").drop_duplicates(CHAVE),
    ).drop_duplicates(CHAVE)
    cad = normalizar_chave(cad)
    for c in ["NR_LATITUDE", "NR_LONGITUDE"]:
        cad[c] = pd.to_numeric(cad[c].str.replace(",", "."), errors="coerce")
    sem = (cad.NR_LATITUDE == -1) | (cad.NR_LONGITUDE == -1) | (cad.NR_LATITUDE == 0)
    cad.loc[sem, ["NR_LATITUDE", "NR_LONGITUDE"]] = np.nan

    def votos_filtro(d):
        d = d[(d.NR_TURNO == str(turno)) & (d.CD_CARGO == "1")]
        n = d.NR_VOTAVEL.astype(int)
        q = d.QT_VOTOS.astype(int)
        out = d[CHAVE].copy()
        out["lula"] = np.where(n == LULA, q, 0)
        out["adv"] = np.where(n == adversario, q, 0)
        out["validos"] = np.where(n < 95, q, 0)
        return out.groupby(CHAVE, as_index=False).sum()

    votos = ler_csv_zip(
        baixar(f"votos-{sufixo}"), ".csv",
        CHAVE + ["NR_TURNO", "CD_CARGO", "NR_VOTAVEL", "QT_VOTOS"], votos_filtro,
    ).groupby(CHAVE, as_index=False).sum()

    def detalhe_filtro(d):
        d = d[(d.NR_TURNO == str(turno)) & (d.CD_CARGO == "1")]
        out = d[CHAVE].copy()
        for c, n in [("QT_APTOS", "aptos"), ("QT_ABSTENCOES", "abst"),
                     ("QT_VOTOS_BRANCOS", "brancos"), ("QT_VOTOS_NULOS", "nulos")]:
            out[n] = d[c].astype(int)
        return out.groupby(CHAVE, as_index=False).sum()

    detalhe = ler_csv_zip(
        baixar(f"detalhe-{sufixo}"), "_BRASIL.csv",
        CHAVE + ["NR_TURNO", "CD_CARGO", "QT_APTOS", "QT_ABSTENCOES",
                 "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS"], detalhe_filtro,
    ).groupby(CHAVE, as_index=False).sum()

    df = votos.pipe(normalizar_chave).merge(detalhe.pipe(normalizar_chave), on=CHAVE, how="outer")
    df = df.merge(cad, on=CHAVE, how="left").fillna(
        {c: 0 for c in ["lula", "adv", "validos", "aptos", "abst", "brancos", "nulos"]})
    df = df[df.SG_UF != "ZZ"]
    df.to_parquet(cache)
    return df


def ler_malha(uf):
    destino = CACHE / "malha" / f"{uf}.parquet"
    if not destino.exists():
        particionar_malha()
    malha = gpd.read_parquet(destino)
    malha.geometry = shapely.make_valid(malha.geometry.values)
    return malha.to_crs(CRS_METROS)


def particionar_malha(lote=60_000):
    """Lê a malha nacional uma vez e grava um GeoParquet por UF."""
    import pyogrio
    caminho = f"/vsizip/{baixar('malha')}"
    total = pyogrio.read_info(caminho)["features"]
    partes = {}
    for inicio in range(0, total, lote):
        df = pyogrio.read_dataframe(
            caminho, skip_features=inicio, max_features=lote,
            columns=["CD_SETOR", "CD_UF", "CD_MUN", "NM_MUN", "NM_BAIRRO", "NM_DIST", "NM_SUBDIST"],
        )
        for cd_uf, parte in df.groupby("CD_UF"):
            partes.setdefault(IBGE_UF[cd_uf], []).append(parte.drop(columns="CD_UF"))
        print(f"malha: {min(inicio + lote, total)}/{total}", flush=True)
    (CACHE / "malha").mkdir(parents=True, exist_ok=True)
    for uf, lista in partes.items():
        g = pd.concat(lista, ignore_index=True)
        g["CD_SETOR"] = g.CD_SETOR.str[:15]
        g.to_parquet(CACHE / "malha" / f"{uf}.parquet")


def mapear_municipios(malha, pontos):
    """Município do TSE → município do IBGE, pelo polígono onde caem (ou de que mais se aproximam) os locais."""
    perto = gpd.sjoin_nearest(pontos[["CD_MUNICIPIO", "geometry"]], malha[["CD_MUN", "geometry"]])
    perto = perto[~perto.index.duplicated()]
    return perto.groupby("CD_MUNICIPIO").CD_MUN.agg(lambda s: s.mode().iat[0]).to_dict()


def ligar(setores, pontos):
    """Para cada setor, os locais da faixa de 100 m mais próxima (método 3.4)."""
    arvore = shapely.STRtree(pontos.geometry.values)
    geoms = setores.geometry.values
    idx_s, idx_p = arvore.query_nearest(geoms, return_distance=False, all_matches=False)
    perto = np.full(len(geoms), np.inf)
    perto[idx_s] = shapely.distance(geoms[idx_s], pontos.geometry.values[idx_p])
    limite = (np.floor(perto / FAIXA) + 1) * FAIXA
    s, p = arvore.query(geoms, predicate="dwithin", distance=limite)
    centro = shapely.centroid(geoms)
    pares = pd.DataFrame({
        "s": s, "p": p,
        "dist_c": shapely.distance(centro[s], pontos.geometry.values[p]),
    })
    pares["peso"] = 1.0 / np.maximum(pares.dist_c, PESO_MIN)
    return pares, perto


def estimar(pares, pontos, n_setores):
    cols = ["lula", "adv", "validos", "aptos", "abst", "brancos", "nulos"]
    v = pontos[cols].to_numpy(float)[pares.p.values] * pares.peso.values[:, None]
    soma = np.zeros((n_setores, len(cols)))
    np.add.at(soma, pares.s.values, v)
    return pd.DataFrame(soma, columns=cols)


def indicadores(t):
    with np.errstate(divide="ignore", invalid="ignore"):
        lula = 100 * t.lula / t.validos
        adv = 100 * t.adv / t.validos
        abst = 100 * t.abst / t.aptos
        bn = 100 * (t.brancos + t.nulos) / (t.aptos - t.abst)
        margem = np.abs(t.lula - t.adv)
        espaco = (t.abst + t.brancos + t.nulos) / np.where(margem > 0, margem, np.nan)
    return pd.DataFrame({"lula": lula, "adv": adv, "abst": abst, "bn": bn, "espaco": espaco})


def arred(x, casas=1):
    return None if x is None or not np.isfinite(x) else round(float(x), casas)


def grade(geoms):
    return set(zip(np.round(shapely.get_x(geoms) / GRADE_LOCAL).astype(int),
                   np.round(shapely.get_y(geoms) / GRADE_LOCAL).astype(int)))


def processar_uf(uf, base, saida_geo, saida_mun_geo):
    malha = ler_malha(uf)
    malha = malha[~malha.geometry.is_empty & malha.geometry.notna()].reset_index(drop=True)
    print(f"{uf}: {len(malha)} setores", flush=True)

    por_eleicao = {}
    mapa_mun = {}
    for suf in ELEICOES:
        lv = base[suf]
        lv = lv[(lv.SG_UF == uf)].reset_index(drop=True)
        com = lv.dropna(subset=["NR_LATITUDE", "NR_LONGITUDE"])
        pontos = gpd.GeoDataFrame(
            com, geometry=gpd.points_from_xy(com.NR_LONGITUDE, com.NR_LATITUDE), crs="EPSG:4326",
        ).to_crs(CRS_METROS)
        if suf == "26":
            mapa_mun = mapear_municipios(malha, pontos)
        else:
            novos = {k: v for k, v in mapear_municipios(malha, pontos).items() if k not in mapa_mun}
            mapa_mun.update(novos)
        lv["CD_MUN"] = lv.CD_MUNICIPIO.map(mapa_mun)
        pontos["CD_MUN"] = pontos.CD_MUNICIPIO.map(mapa_mun)
        por_eleicao[suf] = (lv, pontos.reset_index(drop=True))

    resultados = {suf: [] for suf in ELEICOES}
    ligacoes = {suf: [] for suf in ELEICOES}
    for cd_mun, setores in malha.groupby("CD_MUN"):
        for suf, (_, pontos) in por_eleicao.items():
            pts = pontos[pontos.CD_MUN == cd_mun].reset_index()
            if pts.empty:
                continue
            pares, perto = ligar(setores, pts)
            est = estimar(pares, pts, len(setores))
            est.index = setores.index
            est["dist"] = perto
            est["n"] = np.bincount(pares.s.values, minlength=len(setores))
            resultados[suf].append(est)
            pares = pares.assign(setor=setores.index.values[pares.s.values],
                                 local=pts["index"].values[pares.p.values])
            ligacoes[suf].append(pares[["setor", "local", "dist_c"]])

    est = {suf: pd.concat(r).reindex(malha.index) if r else None for suf, r in resultados.items()}
    lig = {suf: pd.concat(l) if l else pd.DataFrame(columns=["setor", "local", "dist_c"])
           for suf, l in ligacoes.items()}
    ind = {suf: indicadores(e) if e is not None else None for suf, e in est.items()}

    comparavel = np.zeros(len(malha), bool)
    if all(e is not None for e in est.values()):
        g26 = por_eleicao["26"][1].geometry.values
        g22 = por_eleicao["22"][1].geometry.values
        l26 = lig["26"].groupby("setor").local.apply(list)
        l22 = lig["22"].groupby("setor").local.apply(list)
        for s in l26.index.intersection(l22.index):
            a, b = grade(g26[l26[s]]), grade(g22[l22[s]])
            comparavel[s] = len(a & b) / max(len(a), len(b)) >= 0.5

    vizinhos = {}
    arvore = shapely.STRtree(malha.geometry.values)
    a, b = arvore.query(malha.geometry.values, predicate="intersects")
    for i, j in zip(a, b):
        if i != j:
            vizinhos.setdefault(i, []).append(j)

    lv26, pts26 = por_eleicao["26"]
    pts26_4326 = pts26.to_crs("EPSG:4326")
    locais_uf = [
        [titulo(r.NM_LOCAL_VOTACAO), titulo(r.NM_BAIRRO or ""), round(g.y, 5), round(g.x, 5),
         f"{uf}-{r.CD_MUNICIPIO:05d}", f"{uf}-{r.NR_ZONA:03d}"]
        for r, g in zip(pts26.itertuples(), pts26_4326.geometry)
    ]
    escrever(DADOS / "locais" / f"{uf}.json", locais_uf)
    l26 = lig["26"].groupby("setor").local.apply(lambda s: sorted(set(map(int, s))))

    i26, i22 = ind["26"], ind["22"]
    e26 = est["26"]
    feicoes = []
    painel = {}
    centros = shapely.get_coordinates(shapely.point_on_surface(malha.to_crs("EPSG:4326").geometry.values))
    for k, r in enumerate(malha.itertuples()):
        dist = e26.dist.iat[k] if e26 is not None else np.inf
        qualidade = 0 if not np.isfinite(dist) else (1 if dist > FRACA else 2)
        props = {"id": r.CD_SETOR, "q": qualidade}
        if qualidade:
            lula, adv = i26.lula.iat[k], i26.adv.iat[k]
            props.update({
                "l26": arred(lula), "f26": arred(adv),
                "v": "l" if lula > adv else "f" if adv > lula else "e",
                "pv": arred(max(lula, adv)),
                "esp": arred(i26.espaco.iat[k], 2),
                "ab": arred(i26.abst.iat[k]), "bn": arred(i26.bn.iat[k]),
            })
            if i22 is not None and np.isfinite(i22.lula.iat[k]):
                props["l22"] = arred(i22.lula.iat[k])
                if comparavel[k]:
                    props["d"] = arred(lula - i22.lula.iat[k])
        feicoes.append(props)
        painel.setdefault(r.CD_SETOR[:11], {})[r.CD_SETOR] = {
            "b": next((x for x in (r.NM_BAIRRO, r.NM_SUBDIST, r.NM_DIST) if isinstance(x, str) and x), ""),
            "m": r.CD_MUN,
            "c": [round(centros[k][0], 5), round(centros[k][1], 5)],
            "dist": None if not np.isfinite(dist) else int(dist),
            "lv": l26.get(k, []),
            "viz": [malha.CD_SETOR.iat[j] for j in vizinhos.get(k, [])],
        }

    geo = malha[["geometry"]].to_crs("EPSG:4326").copy()
    geo.geometry = shapely.make_valid(shapely.set_precision(geo.geometry.values, 1e-6))
    with open(saida_geo, "w", encoding="utf-8") as f:
        for props, g in zip(feicoes, geo.geometry.values):
            f.write(json.dumps({"type": "Feature", "properties": props, "tippecanoe": {"minzoom": 10},
                                "geometry": shapely.geometry.mapping(g)},
                               ensure_ascii=False, separators=(",", ":")) + "\n")

    for prefixo, setores in painel.items():
        escrever(DADOS / "setores" / uf / f"{prefixo}.json", setores)

    municipios = municipios_uf(uf, malha, por_eleicao, feicoes, mapa_mun)
    escrever(DADOS / "municipios" / f"{uf}.json", municipios)
    contornos = malha[["CD_MUN", "geometry"]].copy()
    contornos.geometry = shapely.make_valid(shapely.set_precision(contornos.geometry.values, 1.0))
    contornos = contornos.dissolve("CD_MUN").to_crs("EPSG:4326")
    contornos.geometry = shapely.simplify(contornos.geometry.values, 0.001)
    with open(saida_mun_geo, "w", encoding="utf-8") as f:
        for cd, g in zip(contornos.index, contornos.geometry.values):
            m = municipios[cd]
            props = {"id": cd, "nome": m["n"], "uf": uf, "l26": m.get("l26"),
                     "f26": m.get("f26"), "l22": m.get("l22")}
            if m.get("esp") is not None:
                props["esp"] = m["esp"]
            if m.get("l26") is not None:
                props["v"] = "l" if m["l26"] > m["f26"] else "f"
                props["pv"] = max(m["l26"], m["f26"])
                if m.get("l22") is not None:
                    props["d"] = round(m["l26"] - m["l22"], 1)
            f.write(json.dumps({"type": "Feature", "properties": props, "tippecanoe": {"maxzoom": 10},
                                "geometry": shapely.geometry.mapping(g)},
                               ensure_ascii=False, separators=(",", ":")) + "\n")
    return municipios


def municipios_uf(uf, malha, por_eleicao, feicoes, mapa_mun):
    tse_por_ibge = {}
    for tse, ibge in mapa_mun.items():
        tse_por_ibge.setdefault(ibge, []).append(f"{uf}-{tse:05d}")
    limites = malha[["CD_MUN"]].join(malha.to_crs("EPSG:4326").bounds)
    caixas = limites.groupby("CD_MUN").agg(minx=("minx", "min"), miny=("miny", "min"),
                                          maxx=("maxx", "max"), maxy=("maxy", "max"))
    espaco = pd.Series([f.get("esp") for f in feicoes], index=malha.CD_MUN.values)
    out = {}
    for cd, nome in malha.groupby("CD_MUN").NM_MUN.first().items():
        b = caixas.loc[cd]
        m = {"n": nome, "tse": sorted(tse_por_ibge.get(cd, [])),
             "bb": [round(b.minx, 4), round(b.miny, 4), round(b.maxx, 4), round(b.maxy, 4)]}
        esp = espaco.loc[[cd]]
        m["setores"] = int(len(esp))
        m["com_espaco"] = int((esp.dropna() >= 1).sum())
        for suf, (lv, _) in por_eleicao.items():
            t = lv[lv.CD_MUN == cd][["lula", "adv", "validos", "aptos", "abst",
                                     "brancos", "nulos"]].sum()
            if t.validos:
                i = indicadores(pd.DataFrame([t])).iloc[0]
                m[f"l{suf}"] = arred(i.lula)
                m[f"f{suf}"] = arred(i.adv)
                if suf == "26":
                    m["esp"] = arred(i.espaco, 2)
                    m["ab"] = arred(i.abst)
                    m["bn"] = arred(i.bn)
        out[cd] = m
    return out


def escrever(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, separators=(",", ":"))


def tiles(geo_setores, geo_municipios, saida):
    tippecanoe = shutil.which("tippecanoe") or os.environ.get("TIPPECANOE")
    if not tippecanoe:
        sys.exit("tippecanoe não encontrado (instale ou defina TIPPECANOE)")
    subprocess.run([
        tippecanoe, "-o", str(saida), "--force", "-Z0", "-z12", "-S4",
        "-L", json.dumps({"file": str(geo_municipios), "layer": "municipios",
                          "description": "municípios"}),
        "-L", json.dumps({"file": str(geo_setores), "layer": "setores"}),
        "--coalesce-smallest-as-needed", "--maximum-tile-bytes=400000", "--read-parallel", "-P", "--quiet",
        "--attribution", "IBGE (Censo 2022), TSE",
    ], check=True)


def ficha():
    linhas = "\n".join(f"- `{n}`: {u} — SHA-256 `{sha256(baixar(n))}`" for n, u in FONTES.items())
    caminho = RAIZ / "fontes" / "ibge-tse-setores-2026.md"
    caminho.write_text(f"""---
id: BR
autor: humano:pipeline
data: {date.today().isoformat()}
fontes: [ibge-tse-setores-2026]
status: revisado
---

# Setores censitários e votação por seção (IBGE e TSE)

{linhas}

- **Licença:** dados abertos do IBGE e do TSE, uso livre com citação da fonte.
- **Método:** SPEC.md, seção 3.4, a partir de deltafolha/eleicoes-por-setores-censitarios.
- **Usado para:** `dados/setores.pmtiles`, `dados/setores/`, `dados/municipios/`, `dados/locais/`.
""", encoding="utf-8")


def main():
    ufs = sys.argv[1:] or [u for u in UFS if u != "ZZ"]
    base = {suf: locais(suf) for suf in ELEICOES}
    tmp = CACHE / "geo"
    tmp.mkdir(parents=True, exist_ok=True)
    indice, ids = [], []
    for uf in ufs:
        geo_s, geo_m = tmp / f"setores-{uf}.geojsonl", tmp / f"municipios-{uf}.geojsonl"
        pronto = DADOS / "municipios" / f"{uf}.json"
        if not (geo_s.exists() and geo_m.exists() and pronto.exists()):
            for g in (geo_s, geo_m, pronto):
                g.unlink(missing_ok=True)
            processar_uf(uf, base, geo_s, geo_m)
        with open(pronto, encoding="utf-8") as f:
            indice += [[cd, m["n"], uf, m["bb"]] for cd, m in json.load(f).items()]
        ids += sorted(pd.read_parquet(CACHE / "malha" / f"{uf}.parquet", columns=["CD_SETOR"]).CD_SETOR)
    escrever(DADOS / "municipios.json", sorted(indice, key=lambda x: x[0]))
    with gzip.open(SETORES_IDS, "wt") as f:
        f.write("\n".join(sorted(ids)) + "\n")
    juntos_s, juntos_m = tmp / "setores.geojsonl", tmp / "municipios.geojsonl"
    for destino, padrao in ((juntos_s, "setores-*.geojsonl"), (juntos_m, "municipios-*.geojsonl")):
        with open(destino, "wb") as saida:
            for parte in sorted(tmp.glob(padrao)):
                if parte.stem.split("-", 1)[1] in ufs:
                    with open(parte, "rb") as entrada:
                        shutil.copyfileobj(entrada, saida)
    tiles(juntos_s, juntos_m, DADOS / "setores.pmtiles")
    ficha()
    print(f"{len(indice)} municípios em {len(ufs)} UFs")


if __name__ == "__main__":
    main()
