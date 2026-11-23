"""BayViva: CRM fictício para representantes da indústria farmacêutica.

Estado da base: login, home e contas (médicos) prontos.
Registrar visita, painel e agenda são construídos nos Labs 1 e 2.
"""

from __future__ import annotations

import os
from pathlib import Path

import jinja2
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.routing import NoMatchFound

from app.db import conexao

BASE = Path(__file__).resolve().parent
app = FastAPI(title="BayViva")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


def prefixo(request: Request) -> str:
    """Prefixo de caminho quando o app roda atrás de um proxy (ex.: /proxy/8000).

    Vem do header X-Forwarded-Prefix ou de BAYVIVA_ROOT_PATH; vazio em execução local.
    O host nunca entra: só o caminho, para funcionar em qualquer URL de participante.
    """
    valor = request.headers.get("x-forwarded-prefix") or os.environ.get("BAYVIVA_ROOT_PATH", "")
    valor = valor.strip().strip("/")
    return f"/{valor}" if valor else ""


def rota(request: Request, destino: str, /, **params) -> str:
    """Caminho (sem host) da rota `destino`, já com o prefixo do proxy."""
    return prefixo(request) + str(request.app.url_path_for(destino, **params))


@jinja2.pass_context
def _rota_template(ctx, destino: str, /, **params) -> str:
    return rota(ctx["request"], destino, **params)


templates.env.globals["rota"] = _rota_template

# Login sem senha: o botão Entrar leva ao usuário de demonstração.
USUARIO_DEMO = {"nome": "Rep. Demonstração", "iniciais": "RD"}


def contexto(request: Request, **extra):
    return {"request": request, "usuario": USUARIO_DEMO, **extra}


# Ícones da home. Para uma tela nova, acrescente uma linha aqui:
#   slug   : nome usado enquanto a tela está em construção (/em-construcao/<slug>)
#   rota   : nome da função da rota real; quando ela existir, o ícone passa a levar a ela
#   cor    : classe CSS do ícone (ver .icone.* em style.css)
ATALHOS = [
    {"slug": "visitas", "rota": "visitas_nova", "letra": "V", "cor": "visita",
     "titulo": "Registrar visita", "desc": "Grave o resultado de uma visita a um médico."},
    {"slug": "painel", "rota": "painel", "letra": "P", "cor": "painel",
     "titulo": "Painel de médicos", "desc": "Veja a carteira e as visitas de cada médico."},
    {"slug": "agenda", "rota": "agenda", "letra": "A", "cor": "agenda",
     "titulo": "Agenda de visitas", "desc": "Consulte as visitas planejadas."},
    {"slug": "insight", "rota": None, "letra": "I", "cor": "insight",
     "titulo": "Registrar insight", "desc": "Anote uma percepção de campo."},
    {"slug": "nova-conta", "rota": None, "letra": "C", "cor": "conta",
     "titulo": "Nova conta", "desc": "Cadastre um novo médico."},
]


def atalhos_da_home(request: Request) -> list[dict]:
    """ATALHOS com o link já resolvido: rota real se existir, senão 'em construção'."""
    resultado = []
    for a in ATALHOS:
        try:
            if not a["rota"]:
                raise NoMatchFound(a["slug"], {})
            link = rota(request, a["rota"])
        except NoMatchFound:
            link = rota(request, "em_construcao", nome=a["slug"])
        resultado.append({**a, "link": link})
    return resultado


@app.middleware("http")
async def aceitar_prefixo_do_proxy(request: Request, call_next):
    """Se o proxy não remover o prefixo, remove aqui antes do roteamento."""
    base = prefixo(request)
    caminho = request.scope["path"]
    if base and (caminho == base or caminho.startswith(base + "/")):
        request.scope["path"] = caminho[len(base):] or "/"
    return await call_next(request)


@app.get("/")
def raiz(request: Request):
    return RedirectResponse(rota(request, "login"))


@app.get("/login")
def login(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse(
        request, "home.html", contexto(request, ativo="home", atalhos=atalhos_da_home(request))
    )


@app.get("/contas")
def contas(request: Request, q: str = ""):
    sql = "SELECT id, nome, especialidade, cidade, estado FROM medicos"
    params: list = []
    if q.strip():
        sql += " WHERE lower(nome) LIKE ?"
        params.append(f"%{q.strip().lower()}%")
    sql += " ORDER BY id"
    with conexao(somente_leitura=True) as con:
        medicos = con.execute(sql, params).fetchall()
    return templates.TemplateResponse(
        request, "contas.html", contexto(request, ativo="contas", medicos=medicos, q=q)
    )


@app.get("/contas/{medico_id}")
def ficha(request: Request, medico_id: int):
    with conexao(somente_leitura=True) as con:
        cur = con.execute("SELECT * FROM medicos WHERE id = ?", [medico_id])
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Médico não encontrado")
        medico = dict(zip([d[0] for d in cur.description], row))
    medico["interesses"] = medico["interesses"].split("; ")
    return templates.TemplateResponse(
        request, "ficha.html", contexto(request, ativo="contas", m=medico)
    )


@app.get("/em-construcao/{nome}")
def em_construcao(request: Request, nome: str):
    """Destino dos itens de menu e atalhos ainda não implementados."""
    return templates.TemplateResponse(
        request, "em_construcao.html", contexto(request, ativo=nome, nome=nome)
    )
