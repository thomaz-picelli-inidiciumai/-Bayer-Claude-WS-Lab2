"""BayViva: CRM fictício para representantes da indústria farmacêutica.

Estado da base: login, home e contas (médicos) prontos.
Registrar visita, painel e agenda são construídos nos Labs 1 e 2.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import quote, unquote, urlencode

import duckdb
import jinja2
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.routing import NoMatchFound

from app import regras, relogio
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


# ---------------------------------------------------------------------------
# Registrar visita (docs/specs/lab2-specs/registrar-visita.md)
# ---------------------------------------------------------------------------

REPRESENTANTE_ID = 1  # usuário logado (fixo na base)
ROTULOS_VISITA = {"medico_id": "Médico", "data_hora": "Data e hora", "notas": "Notas"}


class VisitaDuplicada(Exception):
    """Já existe visita realizada do mesmo médico no mesmo instante."""


def _lista_de_medicos() -> list[tuple[int, str]]:
    with conexao(somente_leitura=True) as con:
        return con.execute("SELECT id, nome FROM medicos ORDER BY nome").fetchall()


def _gravar_visita(valores: dict) -> tuple:
    """Grava a visita numa transação e a lê de volta; só então confirma (COMMIT).

    Levanta VisitaDuplicada ou duckdb.Error. Nada fica gravado quando levanta.
    """
    with conexao() as con:
        con.execute("BEGIN TRANSACTION")
        try:
            repetida = con.execute(
                "SELECT 1 FROM visitas WHERE medico_id = ? AND data_hora = ? AND status = 'realizada' LIMIT 1",
                [valores["medico_id"], valores["data_hora"]],
            ).fetchone()
            if repetida:
                raise VisitaDuplicada()
            novo_id = con.execute("SELECT coalesce(max(id), 0) + 1 FROM visitas").fetchone()[0]
            esperado = (novo_id, valores["medico_id"], REPRESENTANTE_ID, valores["data_hora"], "realizada", valores["notas"])
            con.execute("INSERT INTO visitas VALUES (?, ?, ?, ?, ?, ?)", list(esperado))
            gravado = con.execute(
                "SELECT id, medico_id, representante_id, data_hora, status, notas FROM visitas WHERE id = ?",
                [novo_id],
            ).fetchone()
            if gravado is None or tuple(gravado) != esperado:
                raise duckdb.Error("A visita não foi confirmada no banco")
            con.execute("COMMIT")
            return gravado
        except BaseException:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            raise


def _tela_visita(request: Request, medicos, digitado: dict, erros: dict, status_code: int = 200,
                 sucesso: dict | None = None, falha: str | None = None):
    agora = relogio.agora()
    return templates.TemplateResponse(
        request,
        "visita_nova.html",
        contexto(
            request, ativo="visitas", medicos=medicos, v=digitado, erros=erros, rotulos=ROTULOS_VISITA,
            sucesso=sucesso, falha=falha, agora_iso=agora.isoformat(timespec="seconds"),
            agora_input=agora.strftime("%Y-%m-%dT%H:%M"),
        ),
        status_code=status_code,
    )


VISITA_EM_BRANCO = {"medico_id": None, "data_hora": "", "notas": ""}


@app.get("/visitas/nova")
def visitas_nova(request: Request, medico_id: str = ""):
    try:
        medicos = _lista_de_medicos()
    except duckdb.Error:
        return _tela_visita(request, [], VISITA_EM_BRANCO, {}, 500, falha=regras.MSG_FALHA_GRAVAR)
    escolhido = regras.inteiro(medico_id)
    if escolhido not in {m[0] for m in medicos}:
        escolhido = None
    return _tela_visita(request, medicos, {**VISITA_EM_BRANCO, "medico_id": escolhido}, {})


@app.post("/visitas/nova")
def visitas_registrar(
    request: Request,
    medico_id: str = Form(""),
    data_hora: str = Form(""),
    notas: str = Form(""),
):
    try:
        medicos = _lista_de_medicos()
    except duckdb.Error:
        digitado = {"medico_id": None, "data_hora": data_hora, "notas": notas}
        return _tela_visita(request, [], digitado, {}, 500, falha=regras.MSG_FALHA_GRAVAR)

    ids = {m[0] for m in medicos}
    valores, erros = regras.validar_registro(medico_id, data_hora, notas, ids, relogio.agora())
    digitado = {"medico_id": valores["medico_id"], "data_hora": data_hora.strip(), "notas": notas}

    if not erros:
        try:
            _gravar_visita(valores)
        except VisitaDuplicada:
            erros["data_hora"] = regras.MSG_DUPLICADA
        except duckdb.Error:
            return _tela_visita(request, medicos, digitado, {}, 500, falha=regras.MSG_FALHA_GRAVAR)
        else:
            nome = dict(medicos)[valores["medico_id"]]
            quando = valores["data_hora"].strftime("%d/%m/%Y às %H:%M")
            return _tela_visita(request, medicos, VISITA_EM_BRANCO, {}, 200, sucesso={"medico": nome, "quando": quando})

    return _tela_visita(request, medicos, digitado, erros, 422)


# ---------------------------------------------------------------------------
# Painel de médicos (docs/specs/lab2-specs/painel-de-medicos.md)
# ---------------------------------------------------------------------------

PAINEL_POR_PAGINA = 20
PAINEL_DIAS_ATENCAO = 30   # até 30 dias: verde
PAINEL_DIAS_CRITICO = 90   # acima de 90 dias (ou nunca): vermelho

ULTIMA_VISITA_SQL = (
    "LEFT JOIN (SELECT medico_id, max(data_hora) AS ultima FROM visitas "
    "WHERE status = 'realizada' GROUP BY medico_id) u ON u.medico_id = m.id"
)


def _like_literal(texto: str) -> str:
    """Escapa % _ \\ para a busca por parte do nome tratar tudo como texto comum."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _selo_dias(dias: int | None) -> tuple[str, str, str]:
    """(classe do selo, texto do selo, texto da coluna 'há N dias')."""
    if dias is None:
        return "critico", "Sem visita", "—"
    if dias == 0:
        texto = "hoje"
    elif dias == 1:
        texto = "há 1 dia"
    else:
        texto = f"há {dias} dias"
    if dias <= PAINEL_DIAS_ATENCAO:
        return "ok", texto, texto
    if dias <= PAINEL_DIAS_CRITICO:
        return "atencao", texto, texto
    return "critico", texto, texto


def _url_painel(request: Request, especialidade: str, q: str, pagina: int) -> str:
    params = {k: v for k, v in (("especialidade", especialidade), ("q", q)) if v}
    params["pagina"] = pagina
    return rota(request, "painel") + "?" + urlencode(params)


@app.get("/painel")
def painel(request: Request, especialidade: str = "", q: str = "", pagina: str = "1"):
    especialidade, q = especialidade.strip(), q.strip()
    hoje = relogio.hoje()

    condicoes, params = [], []
    if especialidade:
        condicoes.append("m.especialidade = ?")
        params.append(especialidade)
    if q:
        condicoes.append("lower(m.nome) LIKE ? ESCAPE '\\'")
        params.append(f"%{_like_literal(q.lower())}%")
    onde = (" WHERE " + " AND ".join(condicoes)) if condicoes else ""

    try:
        with conexao(somente_leitura=True) as con:
            especialidades = [r[0] for r in con.execute("SELECT DISTINCT especialidade FROM medicos ORDER BY 1").fetchall()]
            total_carteira, sem_visita, mais_90 = con.execute(
                "SELECT count(*), count(*) FILTER (WHERE u.ultima IS NULL), "
                "count(*) FILTER (WHERE u.ultima IS NULL OR CAST(u.ultima AS DATE) < ?) "
                f"FROM medicos m {ULTIMA_VISITA_SQL}",
                [hoje - timedelta(days=PAINEL_DIAS_CRITICO)],
            ).fetchone()
            total = con.execute(f"SELECT count(*) FROM medicos m{onde}", params).fetchone()[0]
            paginas = max(1, -(-total // PAINEL_POR_PAGINA))
            numero = regras.inteiro(pagina)
            numero = 1 if numero is None or numero < 1 else min(numero, paginas)
            linhas = con.execute(
                f"SELECT m.id, m.nome, m.especialidade, u.ultima FROM medicos m {ULTIMA_VISITA_SQL}{onde} "
                "ORDER BY u.ultima ASC NULLS FIRST, m.nome LIMIT ? OFFSET ?",
                [*params, PAINEL_POR_PAGINA, (numero - 1) * PAINEL_POR_PAGINA],
            ).fetchall()
    except duckdb.Error:
        return templates.TemplateResponse(
            request, "painel.html",
            contexto(request, ativo="painel", erro=regras.MSG_FALHA_PAINEL), status_code=500,
        )

    medicos = []
    for mid, nome, esp, ultima in linhas:
        dias = (hoje - ultima.date()).days if ultima else None
        classe, selo, texto = _selo_dias(dias)
        medicos.append({
            "id": mid, "nome": nome, "especialidade": esp,
            "ultima": ultima.strftime("%d/%m/%Y") if ultima else "—",
            "dias": texto, "classe": classe, "selo": selo,
        })

    primeiro = (numero - 1) * PAINEL_POR_PAGINA + 1
    return templates.TemplateResponse(request, "painel.html", contexto(
        request, ativo="painel", erro=None, medicos=medicos, especialidades=especialidades,
        especialidade=especialidade, q=q, total=total, numero=numero, paginas=paginas,
        de=primeiro, ate=primeiro + len(medicos) - 1,
        resumo={"total": total_carteira, "sem_visita": sem_visita, "mais_90": mais_90},
        url_anterior=_url_painel(request, especialidade, q, numero - 1) if numero > 1 else None,
        url_proxima=_url_painel(request, especialidade, q, numero + 1) if numero < paginas else None,
        rotulo_filtros=bool(especialidade or q),
    ))


# ---------------------------------------------------------------------------
# Agenda de visitas (docs/specs/lab2-specs/agenda-de-visitas.md)
# ---------------------------------------------------------------------------

DIAS_DA_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
COOKIE_AVISO = "bayviva_aviso"
ROTULOS_AGENDA = {"medico_id": "Médico", "data": "Data", "hora": "Hora"}


class HorarioOcupado(Exception):
    """Já existe visita planejada do representante neste horário."""


class VisitaNaoCancelavel(Exception):
    """Visita inexistente, de outro representante ou que não está planejada."""


def _semana_de(texto) -> date:
    """Segunda-feira da semana civil que contém `texto` (AAAA-MM-DD); inválido = semana atual."""
    return regras.segunda_da_semana(regras.parse_data(texto) or relogio.hoje())


def _visitas_da_semana(segunda: date) -> list[tuple]:
    inicio = datetime.combine(segunda, time.min)
    with conexao(somente_leitura=True) as con:
        return con.execute(
            "SELECT v.id, v.data_hora, v.status, m.nome FROM visitas v JOIN medicos m ON m.id = v.medico_id "
            "WHERE v.representante_id = ? AND v.status IN ('planejada', 'cancelada') "
            "AND v.data_hora >= ? AND v.data_hora < ? ORDER BY v.data_hora, v.id",
            [REPRESENTANTE_ID, inicio, inicio + timedelta(days=7)],
        ).fetchall()


def _agendar(valores: dict) -> None:
    """Confere conflito e grava na mesma transação; lê de volta antes do COMMIT."""
    with conexao() as con:
        con.execute("BEGIN TRANSACTION")
        try:
            ocupado = con.execute(
                "SELECT 1 FROM visitas WHERE representante_id = ? AND status = 'planejada' AND data_hora = ? LIMIT 1",
                [REPRESENTANTE_ID, valores["data_hora"]],
            ).fetchone()
            if ocupado:
                raise HorarioOcupado()
            novo_id = con.execute("SELECT coalesce(max(id), 0) + 1 FROM visitas").fetchone()[0]
            esperado = (novo_id, valores["medico_id"], REPRESENTANTE_ID, valores["data_hora"], "planejada", None)
            con.execute("INSERT INTO visitas VALUES (?, ?, ?, ?, ?, ?)", list(esperado))
            gravado = con.execute(
                "SELECT id, medico_id, representante_id, data_hora, status, notas FROM visitas WHERE id = ?", [novo_id]
            ).fetchone()
            if gravado is None or tuple(gravado) != esperado:
                raise duckdb.Error("A visita não foi confirmada no banco")
            con.execute("COMMIT")
        except BaseException:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            raise


def _cancelar(visita_id: int) -> date:
    """Muda a visita planejada do representante para `cancelada`; devolve o dia dela."""
    with conexao() as con:
        con.execute("BEGIN TRANSACTION")
        try:
            achada = con.execute(
                "SELECT data_hora FROM visitas WHERE id = ? AND representante_id = ? AND status = 'planejada'",
                [visita_id, REPRESENTANTE_ID],
            ).fetchone()
            if achada is None:
                raise VisitaNaoCancelavel()
            con.execute("UPDATE visitas SET status = 'cancelada' WHERE id = ?", [visita_id])
            depois = con.execute("SELECT status FROM visitas WHERE id = ?", [visita_id]).fetchone()
            if depois is None or depois[0] != "cancelada":
                raise duckdb.Error("O cancelamento não foi confirmado no banco")
            con.execute("COMMIT")
            return achada[0].date()
        except BaseException:
            try:
                con.execute("ROLLBACK")
            except duckdb.Error:
                pass
            raise


def _aviso_e_cookie(resposta, mensagem: str | None = None):
    """Aviso de uso único: grava o cookie no redirect e apaga depois de lido."""
    if mensagem:
        resposta.set_cookie(COOKIE_AVISO, quote(mensagem), max_age=60, httponly=True, samesite="lax", path="/")
    else:
        resposta.delete_cookie(COOKIE_AVISO, path="/")


def _tela_agenda(request: Request, segunda: date, digitado: dict | None = None, erros: dict | None = None,
                 status_code: int = 200, falha: str | None = None, aviso: str | None = None):
    hoje = relogio.hoje()
    erro_leitura = None
    try:
        visitas = _visitas_da_semana(segunda)
        medicos = _lista_de_medicos()
    except duckdb.Error:
        visitas, medicos, erro_leitura = [], [], regras.MSG_FALHA_AGENDA
        status_code = 500

    dias = []
    for i, nome in enumerate(DIAS_DA_SEMANA):
        d = segunda + timedelta(days=i)
        dias.append({
            "data": d, "iso": d.isoformat(), "nome": nome, "curto": d.strftime("%d/%m"), "hoje": d == hoje,
            "visitas": [
                {"id": vid, "hora": quando.strftime("%H:%M"), "medico": medico, "status": status,
                 "resumo": f"{quando:%d/%m} às {quando:%H:%M}, {medico}"}
                for vid, quando, status, medico in visitas if quando.date() == d
            ],
        })

    sexta = segunda + timedelta(days=4)
    resposta = templates.TemplateResponse(
        request, "agenda.html",
        contexto(
            request, ativo="agenda", dias=dias, medicos=medicos, horas=regras.grade_de_horarios(),
            titulo_semana=f"{segunda:%d/%m} a {sexta:%d/%m/%Y}", semana_iso=segunda.isoformat(),
            url_anterior=rota(request, "agenda") + "?" + urlencode({"semana": (segunda - timedelta(days=7)).isoformat()}),
            url_proxima=rota(request, "agenda") + "?" + urlencode({"semana": (segunda + timedelta(days=7)).isoformat()}),
            hoje_iso=hoje.isoformat(), v=digitado or {"medico_id": None, "data": "", "hora": ""}, erros=erros or {},
            rotulos=ROTULOS_AGENDA, falha=falha or erro_leitura, aviso=aviso, erro_leitura=erro_leitura,
            agora_iso=relogio.agora().isoformat(timespec="seconds"),
        ),
        status_code=status_code,
    )
    return resposta


@app.get("/agenda")
def agenda(request: Request, semana: str = ""):
    aviso = request.cookies.get(COOKIE_AVISO)
    resposta = _tela_agenda(request, _semana_de(semana), aviso=unquote(aviso) if aviso else None)
    if aviso:
        _aviso_e_cookie(resposta)
    return resposta


@app.post("/agenda/nova")
def agenda_nova(
    request: Request,
    medico_id: str = Form(""),
    data: str = Form(""),
    hora: str = Form(""),
    semana: str = Form(""),
):
    # Semana exibida se houver erro: a da data enviada, senão a do campo oculto, senão a atual.
    segunda = regras.segunda_da_semana(regras.parse_data(data)) if regras.parse_data(data) else _semana_de(semana)
    try:
        medicos = {m[0] for m in _lista_de_medicos()}
    except duckdb.Error:
        return _tela_agenda(request, segunda, {"medico_id": regras.inteiro(medico_id), "data": data, "hora": hora},
                            {}, 500, falha=regras.MSG_FALHA_GRAVAR)

    valores, erros = regras.validar_agendamento(medico_id, data, hora, medicos, relogio.agora())
    digitado = {"medico_id": valores["medico_id"], "data": data.strip(), "hora": hora.strip()}

    if not erros:
        try:
            _agendar(valores)
        except HorarioOcupado:
            erros["hora"] = regras.MSG_CONFLITO
        except duckdb.Error:
            return _tela_agenda(request, segunda, digitado, {}, 500, falha=regras.MSG_FALHA_GRAVAR)
        else:
            destino = rota(request, "agenda") + "?" + urlencode({"semana": valores["data"].isoformat()})
            resposta = RedirectResponse(destino, status_code=303)
            quando = valores["data_hora"]
            _aviso_e_cookie(resposta, f"Visita agendada para {quando:%d/%m} às {quando:%H:%M}")
            return resposta

    return _tela_agenda(request, segunda, digitado, erros, 422)


@app.post("/agenda/{visita_id}/cancelar")
def agenda_cancelar(request: Request, visita_id: str):
    numero = regras.inteiro(visita_id)
    if numero is None:
        raise HTTPException(status_code=404, detail="Visita não encontrada")
    try:
        dia = _cancelar(numero)
    except VisitaNaoCancelavel:
        raise HTTPException(status_code=404, detail="Visita não encontrada")
    except duckdb.Error:
        return _tela_agenda(request, _semana_de(""), status_code=500, falha=regras.MSG_FALHA_GRAVAR)
    destino = rota(request, "agenda") + "?" + urlencode({"semana": dia.isoformat()})
    resposta = RedirectResponse(destino, status_code=303)
    _aviso_e_cookie(resposta, "Visita cancelada")
    return resposta


@app.get("/em-construcao/{nome}")
def em_construcao(request: Request, nome: str):
    """Destino dos itens de menu e atalhos ainda não implementados."""
    return templates.TemplateResponse(
        request, "em_construcao.html", contexto(request, ativo=nome, nome=nome)
    )
