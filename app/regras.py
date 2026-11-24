"""Regras de validação das telas de visitas, sem banco e sem HTTP.

As mesmas mensagens são repetidas em app/static/app.js (validação no navegador);
tests/test_regras.py confere que as duas listas não se afastam.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

# Mensagens (textos definidos nas specs de docs/specs/lab2-specs/)
MSG_MEDICO = "Selecione um médico"
MSG_DATA_HORA_VAZIA = "Informe a data e a hora da visita"
MSG_DATA_HORA_FUTURA = "A data da visita não pode estar no futuro"
MSG_NOTAS_TAMANHO = "Informe de 10 a 1000 caracteres"
MSG_NOTAS_PII = "Remova dados pessoais das notas"
MSG_DUPLICADA = "Esta visita já foi registrada"
MSG_DATA_VAZIA = "Informe a data"
MSG_DIA_UTIL = "Escolha um dia útil"
MSG_HORA_GRADE = "Escolha um horário entre 08:00 e 18:00, de 30 em 30 minutos"
MSG_HORARIO_FUTURO = "Escolha um horário futuro"
MSG_CONFLITO = "Já existe uma visita neste horário"
MSG_FALHA_GRAVAR = "Não foi possível salvar. Nada foi gravado. Tente novamente."
MSG_FALHA_PAINEL = "Não foi possível carregar o painel. Tente novamente."
MSG_FALHA_AGENDA = "Não foi possível carregar a agenda. Tente novamente."

NOTAS_MIN = 10
NOTAS_MAX = 1000

_TELEFONE = re.compile(r"\d(?:[\s\-()]*\d){7,}")


def inteiro(texto) -> int | None:
    """Converte para int ou devolve None (qualquer texto que não seja inteiro)."""
    try:
        return int(str(texto).strip())
    except (TypeError, ValueError):
        return None


def parse_data_hora(texto) -> datetime | None:
    """Aceita AAAA-MM-DDTHH:MM (input datetime-local), com ou sem segundos."""
    texto = (texto or "").strip()
    for formato in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def parse_data(texto) -> date | None:
    try:
        return datetime.strptime((texto or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def grade_de_horarios() -> list[str]:
    """08:00 a 18:00 (inclusive), de 30 em 30 minutos: 21 horários."""
    return [f"{m // 60:02d}:{m % 60:02d}" for m in range(8 * 60, 18 * 60 + 1, 30)]


def tem_dado_pessoal(texto: str) -> bool:
    """E-mail = qualquer '@'; telefone = 8 ou mais dígitos (com espaços, hífens ou parênteses)."""
    return "@" in texto or bool(_TELEFONE.search(texto))


def eh_dia_util(dia: date) -> bool:
    return dia.weekday() < 5


def segunda_da_semana(dia: date) -> date:
    return dia - timedelta(days=dia.weekday())


def validar_registro(medico_id, data_hora, notas, medicos_validos: set[int], agora: datetime):
    """Valida o formulário de registrar visita.

    Devolve (valores, erros). `erros` é um dict campo -> mensagem (uma por campo).
    """
    erros: dict[str, str] = {}

    medico = inteiro(medico_id)
    if medico is None or medico not in medicos_validos:
        erros["medico_id"] = MSG_MEDICO
        medico = None

    momento = parse_data_hora(data_hora)
    if momento is None:
        erros["data_hora"] = MSG_DATA_HORA_VAZIA
    elif momento > agora:
        erros["data_hora"] = MSG_DATA_HORA_FUTURA

    texto = (notas or "").strip()
    if not NOTAS_MIN <= len(texto) <= NOTAS_MAX:
        erros["notas"] = MSG_NOTAS_TAMANHO
    elif tem_dado_pessoal(texto):
        erros["notas"] = MSG_NOTAS_PII

    return {"medico_id": medico, "data_hora": momento, "notas": texto}, erros


def validar_agendamento(medico_id, data, hora, medicos_validos: set[int], agora: datetime):
    """Valida o formulário da agenda (sem a checagem de conflito, que usa o banco)."""
    erros: dict[str, str] = {}

    medico = inteiro(medico_id)
    if medico is None or medico not in medicos_validos:
        erros["medico_id"] = MSG_MEDICO
        medico = None

    dia = parse_data(data)
    if dia is None:
        erros["data"] = MSG_DATA_VAZIA
    elif not eh_dia_util(dia):
        erros["data"] = MSG_DIA_UTIL

    hora = (hora or "").strip()
    if hora not in grade_de_horarios():
        erros["hora"] = MSG_HORA_GRADE

    momento = None
    if "data" not in erros and "hora" not in erros:
        momento = datetime.combine(dia, datetime.strptime(hora, "%H:%M").time())
        if momento <= agora:
            erros["hora"] = MSG_HORARIO_FUTURO

    return {"medico_id": medico, "data": dia, "hora": hora, "data_hora": momento}, erros
