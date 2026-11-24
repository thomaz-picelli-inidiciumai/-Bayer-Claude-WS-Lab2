"""Regras puras de validação e relógio (sem HTTP, sem banco)."""

from datetime import date, datetime
from pathlib import Path

import pytest

from app import regras, relogio

AGORA = datetime(2026, 11, 4, 8, 0)  # quarta-feira
MEDICOS = {1, 2, 3}


# ---------- relógio ----------

def test_agora_usa_override(monkeypatch):
    monkeypatch.setenv("BAYVIVA_AGORA", "2026-11-04T08:00")
    assert relogio.agora() == AGORA
    assert relogio.hoje() == date(2026, 11, 4)


def test_agora_ignora_override_invalido(monkeypatch):
    monkeypatch.setenv("BAYVIVA_AGORA", "ontem")
    assert isinstance(relogio.agora(), datetime)
    assert relogio.agora().tzinfo is None


def test_agora_sem_override_e_horario_de_sao_paulo(monkeypatch):
    monkeypatch.delenv("BAYVIVA_AGORA", raising=False)
    from zoneinfo import ZoneInfo

    esperado = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
    assert abs((relogio.agora() - esperado).total_seconds()) < 5


# ---------- dados pessoais ----------

@pytest.mark.parametrize("texto", [
    "falar com ana@x.com", "contato @ana", "ligar 11987654321", "ligar 1198765-4321",
    "tel (11) 9876 5432", "tel 1 2 3 4 5 6 7 8",
])
def test_detecta_dado_pessoal(texto):
    assert regras.tem_dado_pessoal(texto)


@pytest.mark.parametrize("texto", [
    "protocolo 1234567 revisado", "dose de 10 mg, 20 mg e 30 mg", "visita sem pendencias",
])
def test_nao_marca_texto_comum(texto):
    assert not regras.tem_dado_pessoal(texto)


# ---------- registrar visita ----------

def _valida(**kw):
    base = {"medico_id": "1", "data_hora": "2026-11-03T10:00", "notas": "Conversa util sobre o tema."}
    base.update(kw)
    return regras.validar_registro(base["medico_id"], base["data_hora"], base["notas"], MEDICOS, AGORA)


def test_registro_valido_nao_tem_erros():
    valores, erros = _valida()
    assert erros == {}
    assert valores["medico_id"] == 1
    assert valores["data_hora"] == datetime(2026, 11, 3, 10, 0)


def test_data_hora_igual_ao_agora_e_aceita_e_um_minuto_depois_nao():
    assert _valida(data_hora="2026-11-04T08:00")[1] == {}
    assert _valida(data_hora="2026-11-04T08:01")[1] == {"data_hora": regras.MSG_DATA_HORA_FUTURA}


@pytest.mark.parametrize("valor", ["", "   ", "amanha", "2026-13-40T10:00"])
def test_data_hora_vazia_ou_invalida(valor):
    assert _valida(data_hora=valor)[1] == {"data_hora": regras.MSG_DATA_HORA_VAZIA}


@pytest.mark.parametrize("valor", ["", "x", "99", "1.5"])
def test_medico_invalido(valor):
    assert _valida(medico_id=valor)[1] == {"medico_id": regras.MSG_MEDICO}


@pytest.mark.parametrize("tamanho,ok", [(9, False), (10, True), (1000, True), (1001, False)])
def test_limites_das_notas(tamanho, ok):
    erros = _valida(notas="a" * tamanho)[1]
    assert (erros == {}) is ok
    if not ok:
        assert erros == {"notas": regras.MSG_NOTAS_TAMANHO}


def test_notas_sao_aparadas_antes_de_contar():
    assert _valida(notas="   abc   ")[1] == {"notas": regras.MSG_NOTAS_TAMANHO}
    assert _valida(notas="  " + "a" * 10 + "  ")[0]["notas"] == "a" * 10


def test_notas_com_email_ou_telefone():
    assert _valida(notas="Falar com ana@example.com depois")[1] == {"notas": regras.MSG_NOTAS_PII}
    assert _valida(notas="Ligar para 11 98765-4321 amanha")[1] == {"notas": regras.MSG_NOTAS_PII}


def test_um_erro_por_campo_tamanho_vence_dado_pessoal():
    assert _valida(notas="a@b")[1] == {"notas": regras.MSG_NOTAS_TAMANHO}


# ---------- agenda ----------

def _agenda(medico="1", data="2026-11-05", hora="09:00"):
    return regras.validar_agendamento(medico, data, hora, MEDICOS, AGORA)


def test_agendamento_valido():
    valores, erros = _agenda()
    assert erros == {}
    assert valores["data_hora"] == datetime(2026, 11, 5, 9, 0)


def test_grade_tem_21_horarios_de_8_a_18():
    grade = regras.grade_de_horarios()
    assert len(grade) == 21
    assert grade[0] == "08:00" and grade[-1] == "18:00"


@pytest.mark.parametrize("hora,ok", [
    ("08:00", True), ("18:00", True), ("12:30", True),
    ("07:30", False), ("18:30", False), ("08:15", False), ("", False), ("9", False),
])
def test_grade_de_horarios(hora, ok):
    erros = _agenda(hora=hora)[1]
    assert (erros == {}) is ok
    if not ok:
        assert erros == {"hora": regras.MSG_HORA_GRADE}


def test_fim_de_semana_nao_e_dia_util():
    assert _agenda(data="2026-11-07")[1] == {"data": regras.MSG_DIA_UTIL}  # sábado
    assert _agenda(data="2026-11-08")[1] == {"data": regras.MSG_DIA_UTIL}  # domingo


def test_data_vazia_ou_invalida():
    assert _agenda(data="")[1] == {"data": regras.MSG_DATA_VAZIA}
    assert _agenda(data="31/12/2026")[1] == {"data": regras.MSG_DATA_VAZIA}


def test_horario_passado_ou_igual_ao_agora_e_recusado():
    assert _agenda(data="2026-11-04", hora="08:00")[1] == {"hora": regras.MSG_HORARIO_FUTURO}
    assert _agenda(data="2026-11-03", hora="10:00")[1] == {"hora": regras.MSG_HORARIO_FUTURO}
    assert _agenda(data="2026-11-04", hora="08:30")[1] == {}


def test_passado_so_e_checado_com_data_e_hora_validas():
    # fim de semana no passado: só o erro de dia útil, sem "horário futuro"
    assert _agenda(data="2026-11-01", hora="10:00")[1] == {"data": regras.MSG_DIA_UTIL}


def test_semana_comeca_na_segunda():
    assert regras.segunda_da_semana(date(2026, 11, 4)) == date(2026, 11, 2)
    assert regras.segunda_da_semana(date(2026, 11, 8)) == date(2026, 11, 2)  # domingo
    assert regras.segunda_da_semana(date(2026, 11, 2)) == date(2026, 11, 2)


# ---------- mensagens do navegador x servidor ----------

def test_mensagens_do_js_batem_com_as_do_servidor():
    js = (Path(__file__).resolve().parent.parent / "app" / "static" / "app.js").read_text(encoding="utf-8")
    for nome in (
        "MSG_MEDICO", "MSG_DATA_HORA_VAZIA", "MSG_DATA_HORA_FUTURA", "MSG_NOTAS_TAMANHO",
        "MSG_NOTAS_PII", "MSG_DATA_VAZIA", "MSG_DIA_UTIL", "MSG_HORA_GRADE", "MSG_HORARIO_FUTURO",
    ):
        assert getattr(regras, nome) in js, f"{nome} não aparece em app.js"
