"""Definições compartilhadas: IDs, caminhos, modelo dos quadros."""

import gzip
import json
import os
import re
import unicodedata
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
COLMEIA = Path(os.environ.get("COLMEIA_DIR", RAIZ.parent / "colmeia"))
DADOS = COLMEIA / "dados"
CELULAS = COLMEIA / "celulas"
GRUPOS = COLMEIA / "_data" / "grupos"

SECOES = ["Próximas ações", "Onde conversar", "Materiais", "Notas"]
DOMINIOS_GRUPOS = ["chat.whatsapp.com", "whatsapp.com/channel", "t.me"]

UFS = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins", "ZZ": "Exterior",
}

IBGE_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
SETORES_IDS = DADOS / "setores_ids.txt.gz"

RE_SETOR = re.compile(r"^(\d{2})\d{13}$")
RE_ZONA = re.compile(r"^([A-Z]{2})-(\d{3})$")
RE_MUNICIPIO = re.compile(r"^([A-Z]{2})-(\d{5})$")


def nivel(id_):
    if id_ == "BR":
        return "brasil"
    if id_ in UFS:
        return "uf"
    if RE_MUNICIPIO.match(id_):
        return "municipio"
    if RE_ZONA.match(id_):
        return "zona"
    m = RE_SETOR.match(id_)
    if m and m.group(1) in IBGE_UF:
        return "setor"
    return None


def caminho_relativo(id_):
    """Caminho do quadro relativo a celulas/ e _data/grupos/, sem extensão."""
    n = nivel(id_)
    if n == "brasil":
        return "BR"
    if n == "uf":
        return f"{id_}/index"
    if n == "setor":
        return f"{IBGE_UF[id_[:2]]}/setores/{id_}"
    uf, num = id_.split("-")
    return f"{uf}/{'municipios' if n == 'municipio' else 'zonas'}/{num}"


def caminho_quadro(id_):
    return CELULAS / f"{caminho_relativo(id_)}.md"


def caminho_grupos(id_):
    return GRUPOS / f"{caminho_relativo(id_)}.yml"


def id_do_caminho(caminho):
    """Inverso de caminho_relativo, a partir de 'celulas/SP/zonas/001.md' ou similar."""
    partes = Path(caminho).with_suffix("").parts
    for raiz in ("celulas", "grupos"):
        if raiz in partes:
            partes = partes[partes.index(raiz) + 1:]
            break
    if partes == ("BR",):
        return "BR"
    if len(partes) == 2 and partes[1] == "index":
        return partes[0]
    if len(partes) == 3 and partes[1] in ("municipios", "zonas"):
        return f"{partes[0]}-{partes[2]}"
    if len(partes) == 3 and partes[1] == "setores" and nivel(partes[2]) == "setor":
        return partes[2] if IBGE_UF[partes[2][:2]] == partes[0] else None
    return None


def carregar_celulas():
    with open(DADOS / "celulas.json", encoding="utf-8") as f:
        return json.load(f)


def carregar_setores():
    if not SETORES_IDS.exists():
        return set()
    with gzip.open(SETORES_IDS, "rt") as f:
        return {linha.strip() for linha in f if linha.strip()}


def ids_validos(celulas=None, setores=None):
    c = celulas or carregar_celulas()
    s = carregar_setores() if setores is None else setores
    return {"BR", *c["ufs"], *c["municipios"], *c["zonas"], *s}


def nome_celula(id_, celulas):
    n = nivel(id_)
    if n == "brasil":
        return "Brasil"
    if n == "uf":
        return UFS[id_]
    if n == "municipio":
        return f"{celulas['municipios'][id_]['n']} ({id_[:2]})"
    if n == "setor":
        return f"Setor {id_} ({IBGE_UF[id_[:2]]})"
    return f"Zona {id_[3:]} ({id_[:2]})"


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sem_acento.lower()).strip()


def ler_front_matter(texto):
    """Retorna (dict, corpo). Lança ValueError se o front matter for inválido."""
    if not texto.startswith("---\n"):
        raise ValueError("o arquivo precisa começar com front matter (---)")
    fim = texto.find("\n---\n", 4)
    if fim == -1:
        raise ValueError("front matter sem o '---' de fechamento")
    try:
        meta = yaml.safe_load(texto[4:fim]) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"front matter com YAML inválido: {e}") from e
    if not isinstance(meta, dict):
        raise ValueError("front matter precisa ser um conjunto de campos")
    return meta, texto[fim + 5:]


def escrever_front_matter(meta, corpo):
    cabecalho = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{cabecalho}\n---\n{corpo}"


def modelo_quadro(id_, celulas):
    meta = {"id": id_, "nivel": nivel(id_), "titulo": nome_celula(id_, celulas)}
    corpo = "".join(f"\n## {s}\n" for s in SECOES)
    return escrever_front_matter(meta, corpo)


def secoes_do_corpo(corpo):
    """Divide o corpo em {titulo: texto} pelos cabeçalhos '## '."""
    secoes, atual = {}, None
    for linha in corpo.splitlines():
        if linha.startswith("## "):
            atual = linha[3:].strip()
            secoes[atual] = []
        elif atual is not None:
            secoes[atual].append(linha)
    return {k: "\n".join(v).strip() for k, v in secoes.items()}
