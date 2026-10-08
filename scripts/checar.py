"""Checagens automáticas de todo PR.

Uso:
    python scripts/checar.py --raiz <pasta com os arquivos do PR> [--relatorio saida.md] arquivo...

Os arquivos são caminhos relativos ao repositório. A lista de IDs válidos vem de
dados/celulas.json da branch base (deste checkout), nunca do PR.
Sai com código 1 se houver erro. Imprime JSON com erros, rótulos e se o PR é só texto.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

from comum import (
    DOMINIOS_GRUPOS, SECOES, carregar_celulas, id_do_caminho, ids_validos, ler_front_matter,
    nivel, secoes_do_corpo,
)

RE_URL = re.compile(r"https?://[^\s)\]>\"']+")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_CPF = re.compile(r"(?<![\d/])\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?![\d/])")
RE_TELEFONE = re.compile(
    r"(?<![\d/])(?:\+?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?9?\d{4}[\s.-]?\d{4}(?![\d/])"
)
RE_CEP = re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)|\bCEP\b", re.IGNORECASE)
RE_HTML = re.compile(r"<\s*/?\s*[a-zA-Z!]")
RE_LINK_TELEFONE = re.compile(r"(wa\.me/|api\.whatsapp\.com/send|whatsapp://|tel:)", re.IGNORECASE)
RE_HASH = re.compile(r"\b[0-9a-f]{32,}\b")
RE_DATA = re.compile(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}h\d{0,2}\b")

STATUS_INTELIGENCIA = {"rascunho", "revisado", "descartado"}
PASTAS_INTELIGENCIA = ("memoria/", "analises/", "execucoes/", "fontes/")
RE_AUTOR = re.compile(r"^(agente|humano):[\w.\-]+$")


def dominio_de_grupo(url):
    p = urlparse(url)
    if p.scheme != "https":
        return False
    host = p.netloc.lower()
    if host == "chat.whatsapp.com" or host == "t.me":
        return len(p.path) > 1
    if host in ("whatsapp.com", "www.whatsapp.com"):
        return p.path.startswith("/channel/") and len(p.path) > len("/channel/")
    return False


def eh_link_de_grupo(url):
    host = urlparse(url).netloc.lower()
    return host in ("chat.whatsapp.com", "t.me", "telegram.me") or (
        host in ("whatsapp.com", "www.whatsapp.com") and "/channel" in url
    )


def dados_pessoais(texto):
    """Erros de dados pessoais. Datas e horários não contam como telefone."""
    erros = []
    if RE_LINK_TELEFONE.search(texto):
        erros.append("Há um link que abre conversa com um número de telefone (wa.me, tel:). "
                     "Use só links de grupos ou canais.")
    sem_urls = RE_HASH.sub(" ", RE_URL.sub(" ", texto))
    if RE_EMAIL.search(sem_urls):
        erros.append("Parece haver um e-mail. Não publique e-mails de pessoas.")
    sem_datas = RE_DATA.sub(" ", sem_urls)
    if RE_CPF.search(sem_datas):
        erros.append("Parece haver um CPF. Não publique documentos de pessoas.")
    elif RE_TELEFONE.search(sem_datas):
        erros.append("Parece haver um número de telefone. Não publique telefones; "
                     "para contato, use o link do grupo.")
    if RE_CEP.search(sem_urls):
        erros.append("Parece haver um CEP. Indique só o nome do lugar público "
                     "(praça, escola, feira), sem CEP.")
    return erros


def checar_quadro(caminho, texto, validos, celulas):
    erros = []
    try:
        meta, corpo = ler_front_matter(texto)
    except ValueError as e:
        return [f"Front matter inválido: {e}."]
    id_caminho = id_do_caminho(caminho)
    id_ = str(meta.get("id", ""))
    if not id_:
        erros.append("Falta o campo `id` no front matter.")
    elif id_ != id_caminho:
        erros.append(f"O `id` ({id_}) não corresponde ao caminho do arquivo ({id_caminho}).")
    elif id_ not in validos:
        erros.append(f"`{id_}` não é um código oficial do TSE conhecido.")
    elif meta.get("nivel") != nivel(id_):
        erros.append(f"O campo `nivel` deveria ser `{nivel(id_)}`.")
    if not meta.get("titulo"):
        erros.append("Falta o campo `titulo` no front matter.")
    extras = set(meta) - {"id", "nivel", "titulo", "atualizado"}
    if extras:
        erros.append(f"Campos não permitidos no front matter: {', '.join(sorted(extras))}.")
    if "atualizado" in meta:
        a = meta["atualizado"]
        if not isinstance(a, date):
            try:
                a = date.fromisoformat(str(a))
            except ValueError:
                a = None
        if a is None:
            erros.append("`atualizado` precisa ser uma data no formato AAAA-MM-DD.")
        elif a > date.today():
            erros.append("`atualizado` não pode ser uma data futura.")

    titulos = [l[3:].strip() for l in corpo.splitlines() if l.startswith("## ")]
    if titulos != SECOES:
        erros.append("O quadro precisa ter exatamente estas seções, nesta ordem: "
                     + ", ".join(f"`## {s}`" for s in SECOES) + ".")
    if re.search(r"^#{1}\s", corpo, re.MULTILINE):
        erros.append("Não use títulos de nível 1 (`# `) no quadro; use `###` dentro das seções.")
    if RE_HTML.search(corpo):
        erros.append("O quadro não pode conter HTML; use só Markdown.")
    for url in RE_URL.findall(corpo):
        if eh_link_de_grupo(url):
            erros.append(f"Links de grupos ({url}) ficam no arquivo de grupos, que só admins "
                         "aprovam. Use o formulário “Sugerir grupo”.")
    for secao, conteudo in secoes_do_corpo(corpo).items():
        if len(conteudo) > 5000:
            erros.append(f"A seção “{secao}” passou de 5.000 caracteres; resuma.")
    return erros + dados_pessoais(texto)


def checar_grupos(caminho, texto, validos):
    erros = []
    id_ = id_do_caminho(caminho)
    if not id_ or id_ not in validos:
        erros.append(f"O caminho não corresponde a uma célula oficial ({id_ or 'inválido'}).")
    try:
        dados = yaml.safe_load(texto)
    except yaml.YAMLError as e:
        return erros + [f"YAML inválido: {e}"]
    if not isinstance(dados, dict) or set(dados) != {"grupos"} or not isinstance(dados["grupos"], list):
        return erros + ["O arquivo deve ter só a chave `grupos:` com uma lista de grupos."]
    for i, g in enumerate(dados["grupos"], 1):
        if not isinstance(g, dict) or set(g) - {"nome", "link"} or not g.get("link") or not g.get("nome"):
            erros.append(f"Grupo {i}: precisa ter só `nome` e `link`.")
            continue
        if not dominio_de_grupo(str(g["link"])):
            erros.append(f"Grupo {i}: link fora dos domínios permitidos "
                         f"({', '.join(DOMINIOS_GRUPOS)}), ou sem https.")
        if len(str(g["nome"])) > 80:
            erros.append(f"Grupo {i}: nome com mais de 80 caracteres.")
        erros += [f"Grupo {i}: {e}" for e in dados_pessoais(str(g["nome"]))]
    return erros


def checar_inteligencia(caminho, texto, validos):
    if Path(caminho).name == "README.md":
        return dados_pessoais(texto)
    erros = []
    try:
        meta, _ = ler_front_matter(texto)
    except ValueError as e:
        return [f"Front matter inválido: {e}."]
    partes = Path(caminho).parts
    em_memoria = "memoria" in partes
    id_ = meta.get("id")
    if id_ is None and not em_memoria:
        erros.append("Falta o campo `id` (célula ou nível).")
    elif id_ is not None and str(id_) not in validos:
        erros.append(f"`{id_}` não é um código oficial conhecido.")
    if "analises" in partes:
        pasta = partes[partes.index("analises") + 1] if len(partes) > partes.index("analises") + 2 else None
        if pasta != str(id_):
            erros.append("Análises ficam em `analises/<ID>/`, com o mesmo `id` do front matter.")
    if not RE_AUTOR.match(str(meta.get("autor", ""))):
        erros.append("`autor` deve ser `agente:<modelo>` ou `humano:<usuario-github>`.")
    if not meta.get("data"):
        erros.append("Falta o campo `data`.")
    if not isinstance(meta.get("fontes", []), list):
        erros.append("`fontes` deve ser uma lista.")
    if meta.get("status") not in STATUS_INTELIGENCIA:
        erros.append("`status` deve ser rascunho, revisado ou descartado.")
    return erros + dados_pessoais(texto)


def rotulo_celula(id_):
    return {"brasil": "brasil", "uf": f"uf:{id_}", "municipio": f"municipio:{id_}",
            "zona": f"zona:{id_}", "setor": f"setor:{id_}"}[nivel(id_)]


def checar(raiz, arquivos, celulas=None):
    celulas = celulas or carregar_celulas()
    validos = ids_validos(celulas)
    erros, rotulos = {}, set()
    somente_texto = bool(arquivos)
    for arq in arquivos:
        caminho = Path(raiz) / arq
        e_quadro = arq.startswith("celulas/") and arq.endswith(".md")
        if not e_quadro:
            somente_texto = False
        if not caminho.exists():
            continue
        if not (e_quadro or arq.startswith("_data/grupos/") or
                (arq.startswith(PASTAS_INTELIGENCIA) and arq.endswith(".md")) or arq == "recursos.md"):
            continue
        texto = caminho.read_text(encoding="utf-8")
        if e_quadro:
            lista = checar_quadro(arq, texto, validos, celulas)
        elif arq.startswith("_data/grupos/") and arq.endswith((".yml", ".yaml")):
            lista = checar_grupos(arq, texto, validos)
            rotulos.add("grupo")
        elif arq.startswith("_data/grupos/"):
            lista = ["Em `_data/grupos/` só entram arquivos `.yml`."]
        elif arq.startswith(PASTAS_INTELIGENCIA) and arq.endswith(".md"):
            lista = checar_inteligencia(arq, texto, validos)
            if "autor: agente:" in texto:
                rotulos.add("agente")
        elif arq == "recursos.md":
            lista = dados_pessoais(texto)
        else:
            continue
        id_ = id_do_caminho(arq) if arq.startswith(("celulas/", "_data/grupos/")) else None
        if id_ and id_ in validos:
            rotulos.add(rotulo_celula(id_))
            rotulos.add(f"nivel:{nivel(id_)}")
        if lista:
            erros[arq] = lista
    if somente_texto:
        rotulos.add("texto")
    return {"erros": erros, "rotulos": sorted(rotulos), "somente_texto": somente_texto}


def relatorio(resultado):
    if not resultado["erros"]:
        return "✅ **Checagens da Colmeia: tudo certo.**\n"
    linhas = ["❌ **Checagens da Colmeia: esta sugestão precisa de ajustes.**", ""]
    for arq, erros in resultado["erros"].items():
        linhas.append(f"**`{arq}`**")
        linhas += [f"- {e}" for e in erros]
        linhas.append("")
    linhas.append("Corrija os pontos acima e as checagens rodam de novo. "
                  "Dúvidas? Veja o [guia de contribuição]"
                  f"(https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'colmeiabrasil/colmeia')}"
                  "/blob/main/CONTRIBUTING.md).")
    return "\n".join(linhas) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", default=".")
    ap.add_argument("--relatorio")
    ap.add_argument("arquivos", nargs="*")
    args = ap.parse_args()
    resultado = checar(args.raiz, args.arquivos)
    if args.relatorio:
        Path(args.relatorio).write_text(relatorio(resultado), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False))
    sys.exit(1 if resultado["erros"] else 0)


if __name__ == "__main__":
    main()
