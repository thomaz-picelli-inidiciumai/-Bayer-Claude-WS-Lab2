"""Testes da Agenda de visitas (docs/specs/lab2-specs/agenda-de-visitas.md).

Relógio fixo pela fixture `client`: quarta-feira 04/11/2026 08:00. A semana corrente é
segunda 02/11 a sexta 06/11.

Verificação manual (não dá para provar por HTTP; anotar o resultado no PR):
- O pop-up "Agendar visita" abre pelo botão geral e pelo "+ Agendar" de cada dia (data preenchida),
  fecha com Esc, botão e clique no fundo.
- Validação no navegador impede o envio e mostra o mesmo pop-up de erros do servidor.
- Cancelar pede confirmação; o aviso de sucesso some sozinho em alguns segundos.
- Layout: cinco colunas em tela larga, três até 1100 px, uma coluna abaixo de 900 px.
"""

import re
from datetime import datetime

import duckdb
import pytest

from app.db import conexao

INSERT = "INSERT INTO visitas VALUES (?, ?, ?, ?, ?, ?)"


def dt(m, d, h=9, mi=0):
    return datetime(2026, m, d, h, mi)


@pytest.fixture()
def semana(client):
    """Semana de 02/11 a 06/11 com visitas conhecidas (representante 1, salvo indicação)."""
    with conexao() as con:
        con.execute("DELETE FROM visitas")
        con.executemany(INSERT, [
            (1, 1, 1, dt(11, 3, 14), "planejada", None),
            (2, 2, 1, dt(11, 3, 9), "planejada", None),
            (3, 3, 1, dt(11, 5, 10), "planejada", None),
            (4, 4, 1, dt(11, 5, 15), "cancelada", None),
            (5, 5, 2, dt(11, 4, 11), "planejada", None),      # outro representante
            (6, 6, 1, dt(11, 10, 9), "planejada", None),      # semana seguinte
            (7, 7, 1, dt(11, 2, 9), "realizada", "x" * 12),   # realizada não aparece
        ])
    return client


def dia(resposta, iso):
    achou = re.search(rf'<section[^>]*data-dia="{iso}".*?</section>', resposta.text, re.S)
    assert achou, f"dia {iso} não está na página"
    return achou.group(0)


def visitas_do_dia(resposta, iso):
    return [int(i) for i in re.findall(r'data-visita="(\d+)"', dia(resposta, iso))]


def agendar(client, **campos):
    dados = {"medico_id": "1", "data": "2026-11-05", "hora": "09:00", **campos}
    return client.post("/agenda/nova", data=dados, follow_redirects=False)


def total(banco):
    return banco("SELECT count(*) FROM visitas")[0][0]


# ---------- critério 1: semana e ordem ----------

def test_criterio_1_mostra_segunda_a_sexta_com_visitas_ordenadas_por_horario(semana):
    """Dado visitas planejadas, quando abro a agenda, então vejo a semana corrente (segunda a
    sexta) com as visitas de cada dia ordenadas por horário."""
    r = semana.get("/agenda")
    assert r.status_code == 200
    dias = re.findall(r'<section[^>]*data-dia="([\d-]+)"', r.text)
    assert dias == ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
    assert visitas_do_dia(r, "2026-11-03") == [2, 1]        # 09:00 antes de 14:00
    assert visitas_do_dia(r, "2026-11-05") == [3, 4]        # planejada 10:00 e cancelada 15:00
    for nome in ("Segunda", "Terça", "Quarta", "Quinta", "Sexta"):
        assert nome in r.text


def test_agenda_nao_mostra_outro_representante_realizadas_nem_outra_semana(semana):
    r = semana.get("/agenda")
    todas = re.findall(r'data-visita="(\d+)"', r.text)
    assert sorted(map(int, todas)) == [1, 2, 3, 4]


def test_dia_sem_visitas_mostra_sem_visitas(semana):
    r = semana.get("/agenda")
    assert "Sem visitas" in dia(r, "2026-11-06")
    assert "Sem visitas" in dia(r, "2026-11-04")
    assert "Sem visitas" not in dia(r, "2026-11-03")


def test_dia_de_hoje_e_destacado(semana):
    r = semana.get("/agenda")
    assert re.search(r'<section class="dia hoje"[^>]*data-dia="2026-11-04"', r.text)
    assert r.text.count("dia hoje") == 1


def test_horario_e_medico_aparecem_na_visita(semana, banco):
    r = semana.get("/agenda")
    nome = banco("SELECT nome FROM medicos WHERE id = 2")[0][0]
    assert "09:00" in dia(r, "2026-11-03") and nome in dia(r, "2026-11-03")


# ---------- critério 2: conflito ----------

def test_criterio_2_conflito_de_horario_e_recusado(semana, banco):
    """Dado visita planejada do mesmo representante no mesmo horário, quando adiciono, então a
    gravação é recusada com "Já existe uma visita neste horário"."""
    antes = total(banco)
    r = agendar(semana, medico_id="8", data="2026-11-05", hora="10:00")
    assert r.status_code == 422
    assert "Já existe uma visita neste horário" in r.text
    assert re.search(r'data-erro-de="hora"[^>]*>\s*Já existe uma visita neste horário', r.text)
    assert total(banco) == antes


def test_visita_de_outro_representante_no_mesmo_horario_nao_e_conflito(semana, banco):
    antes = total(banco)
    r = agendar(semana, medico_id="8", data="2026-11-04", hora="11:00")   # rep. 2 já tem 11:00
    assert r.status_code == 303
    assert total(banco) == antes + 1


# ---------- critério 3: canceladas ----------

def test_criterio_3_cancelada_aparece_riscada_e_nao_conta_como_conflito(semana, banco):
    """Dado uma visita cancelada, quando vejo a agenda, então ela aparece riscada e não conta
    como conflito."""
    r = semana.get("/agenda")
    cancelada = re.search(r'<li[^>]*data-visita="4"[^>]*>', r.text).group(0)
    assert "cancelada" in cancelada
    antes = total(banco)
    r = agendar(semana, medico_id="8", data="2026-11-05", hora="15:00")   # mesmo horário da cancelada
    assert r.status_code == 303
    assert total(banco) == antes + 1


# ---------- critério 4: navegação ----------

def test_criterio_4_navegacao_entre_semanas(semana):
    """Dado a navegação Semana anterior/próxima, quando clico, então a agenda muda de semana."""
    r = semana.get("/agenda", params={"semana": "2026-11-09"})
    dias = re.findall(r'<section[^>]*data-dia="([\d-]+)"', r.text)
    assert dias == ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"]
    assert visitas_do_dia(r, "2026-11-10") == [6]

    atual = semana.get("/agenda")
    anterior = re.search(r'href="([^"]*)"[^>]*>[^<]*Semana anterior', atual.text).group(1).replace("&amp;", "&")
    proxima = re.search(r'href="([^"]*)"[^>]*>[^<]*Próxima semana', atual.text).group(1).replace("&amp;", "&")
    assert anterior == "/agenda?semana=2026-10-26"
    assert proxima == "/agenda?semana=2026-11-09"
    assert re.search(r'href="/agenda"[^>]*>[^<]*Hoje', atual.text) or "semana=2026-11-02" in atual.text


def test_semana_com_qualquer_dia_mostra_a_mesma_semana(semana):
    for d in ("2026-11-02", "2026-11-04", "2026-11-06", "2026-11-07", "2026-11-08"):
        r = semana.get("/agenda", params={"semana": d})
        assert visitas_do_dia(r, "2026-11-03") == [2, 1], d


@pytest.mark.parametrize("valor", ["abc", "2026-13-45", "", "04/11/2026"], ids=["texto", "impossivel", "vazio", "br"])
def test_semana_invalida_mostra_a_semana_atual(semana, valor):
    r = semana.get("/agenda", params={"semana": valor})
    assert r.status_code == 200
    assert visitas_do_dia(r, "2026-11-03") == [2, 1]


# ---------- critério 5 e regras de data/hora ----------

def test_criterio_5_horario_no_passado_e_recusado(semana, banco):
    """Dado que adiciono uma visita no passado, então vejo "Escolha um horário futuro"."""
    antes = total(banco)
    for data, hora in (("2026-11-03", "10:00"), ("2026-11-04", "08:00")):   # ontem; hoje == agora
        r = agendar(semana, data=data, hora=hora)
        assert r.status_code == 422, (data, hora)
        assert "Escolha um horário futuro" in r.text
    assert total(banco) == antes


def test_hoje_mais_tarde_e_aceito(semana, banco):
    antes = total(banco)
    assert agendar(semana, data="2026-11-04", hora="08:30").status_code == 303
    assert total(banco) == antes + 1


@pytest.mark.parametrize("data", ["2026-11-07", "2026-11-08"], ids=["sabado", "domingo"])
def test_fim_de_semana_nao_e_dia_util(semana, banco, data):
    antes = total(banco)
    r = agendar(semana, data=data)
    assert r.status_code == 422
    assert re.search(r'data-erro-de="data"[^>]*>\s*Escolha um dia útil', r.text)
    assert total(banco) == antes


@pytest.mark.parametrize("hora,aceita", [
    ("08:00", True), ("18:00", True), ("12:30", True),
    ("07:30", False), ("18:30", False), ("08:15", False), ("", False), ("9", False),
])
def test_grade_de_horarios(semana, banco, hora, aceita):
    antes = total(banco)
    r = agendar(semana, data="2026-11-06", hora=hora)
    assert r.status_code == (303 if aceita else 422)
    assert total(banco) == antes + (1 if aceita else 0)
    if not aceita:
        assert "Escolha um horário entre 08:00 e 18:00, de 30 em 30 minutos" in r.text


@pytest.mark.parametrize("campo,valor,mensagem", [
    ("medico_id", "", "Selecione um médico"),
    ("medico_id", "9999", "Selecione um médico"),
    ("data", "", "Informe a data"),
    ("data", "31/12/2026", "Informe a data"),
], ids=["sem-medico", "medico-inexistente", "sem-data", "data-formato-br"])
def test_campos_obrigatorios(semana, banco, campo, valor, mensagem):
    antes = total(banco)
    r = agendar(semana, **{campo: valor})
    assert r.status_code == 422
    assert re.search(rf'data-erro-de="{campo}"[^>]*>\s*{re.escape(mensagem)}', r.text)
    assert total(banco) == antes


# ---------- gravação e sucesso ----------

def test_sucesso_grava_planejada_e_redireciona_para_a_semana_da_data(semana, banco):
    antes = total(banco)
    maior_id = banco("SELECT max(id) FROM visitas")[0][0]
    r = agendar(semana, medico_id="8", data="2026-11-13", hora="09:30")
    assert r.status_code == 303
    assert r.headers["location"] == "/agenda?semana=2026-11-13"
    assert total(banco) == antes + 1
    linha = banco("SELECT id, medico_id, representante_id, status, notas, strftime(data_hora, '%Y-%m-%d %H:%M') "
                  "FROM visitas ORDER BY id DESC LIMIT 1")[0]
    assert linha[:4] == (maior_id + 1, 8, 1, "planejada")
    assert not linha[4]                      # notas vazias
    assert linha[5] == "2026-11-13 09:30"


def test_visita_nova_aparece_no_dia_certo_sem_cair_na_semana_errada(semana):
    r = agendar(semana, medico_id="8", data="2026-11-13", hora="09:30")
    pagina = semana.get(r.headers["location"])
    assert re.findall(r'<section[^>]*data-dia="([\d-]+)"', pagina.text)[0] == "2026-11-09"
    assert "09:30" in dia(pagina, "2026-11-13")


def test_aviso_de_sucesso_aparece_uma_unica_vez(semana):
    r = agendar(semana, medico_id="8", data="2026-11-05", hora="09:00")
    primeira = semana.get(r.headers["location"])
    assert "Visita agendada para 05/11 às 09:00" in primeira.text
    segunda = semana.get(r.headers["location"])
    assert "Visita agendada para" not in segunda.text


def test_sucesso_sem_cookie_nao_mostra_aviso(semana):
    assert "Visita agendada para" not in semana.get("/agenda").text


def test_redirecionamento_respeita_prefixo_de_proxy(semana, monkeypatch):
    monkeypatch.setenv("BAYVIVA_ROOT_PATH", "/proxy/8000")
    r = agendar(semana)
    assert r.status_code == 303
    assert r.headers["location"] == "/proxy/8000/agenda?semana=2026-11-05"
    pagina = semana.get("/agenda")
    assert 'action="/proxy/8000/agenda/nova"' in pagina.text


# ---------- erros: tela ----------

def test_erro_mostra_a_semana_certa_o_popup_aberto_e_mantem_os_dados(semana):
    r = agendar(semana, medico_id="", data="2026-11-13", hora="08:15")
    assert r.status_code == 422
    assert 'data-dia="2026-11-13"' in r.text                      # semana da data enviada
    abertura = re.search(r'<dialog id="dlg-agendar"[^>]*>', r.text).group(0)
    assert " open" in abertura and "data-modal" in abertura
    assert 'value="2026-11-13"' in r.text
    assert "Selecione um médico" in r.text
    assert "Escolha um horário entre 08:00 e 18:00" in r.text
    assert " open" in re.search(r'<dialog id="dlg-erros"[^>]*>', r.text).group(0)


def test_erro_com_data_invalida_mantem_a_semana_enviada_no_formulario(semana):
    r = semana.post("/agenda/nova", data={"medico_id": "1", "data": "", "hora": "09:00", "semana": "2026-11-09"})
    assert r.status_code == 422
    assert 'data-dia="2026-11-10"' in r.text


def test_formulario_traz_grade_de_21_horarios_medicos_e_marcacoes(semana, banco):
    r = semana.get("/agenda")
    horas = re.findall(r'<option value="(\d\d:\d\d)"', r.text)
    assert len(horas) == 21 and horas[0] == "08:00" and horas[-1] == "18:00"
    assert 'data-valida="agenda"' in r.text and "data-enviar" in r.text
    assert 'action="/agenda/nova"' in r.text and 'min="2026-11-04"' in r.text
    assert len(re.findall(r'<option value="\d+"[^>]*>Dr\.', r.text)) == 50
    assert r.text.count("data-abrir=") >= 6        # botão geral + "+ Agendar" dos 5 dias
    assert "dlg-agendar" in r.text and " open" not in re.search(r'<dialog id="dlg-agendar"[^>]*>', r.text).group(0)


# ---------- cancelar ----------

def test_cancelar_muda_status_e_redireciona(semana, banco):
    antes = total(banco)
    r = semana.post("/agenda/3/cancelar", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/agenda?semana=2026-11-05"
    assert banco("SELECT status FROM visitas WHERE id = 3")[0][0] == "cancelada"
    assert total(banco) == antes
    pagina = semana.get(r.headers["location"])
    assert "Visita cancelada" in pagina.text
    assert "cancelada" in re.search(r'<li[^>]*data-visita="3"[^>]*>', pagina.text).group(0)


def test_cancelar_libera_o_horario(semana, banco):
    semana.post("/agenda/3/cancelar", follow_redirects=False)
    assert agendar(semana, medico_id="8", data="2026-11-05", hora="10:00").status_code == 303


@pytest.mark.parametrize("visita_id", ["9999", "5", "4", "7", "abc"], ids=["inexistente", "outro-rep", "ja-cancelada", "realizada", "texto"])
def test_cancelar_visita_invalida_responde_404_e_nada_muda(semana, banco, visita_id):
    antes = banco("SELECT id, status FROM visitas ORDER BY id")
    r = semana.post(f"/agenda/{visita_id}/cancelar", follow_redirects=False)
    assert r.status_code == 404
    assert banco("SELECT id, status FROM visitas ORDER BY id") == antes


def test_botao_cancelar_so_nas_planejadas_e_ha_confirmacao(semana):
    r = semana.get("/agenda")
    assert 'id="dlg-cancelar"' in r.text
    assert 'data-acao="/agenda/3/cancelar"' in r.text
    assert 'data-acao="/agenda/4/cancelar"' not in r.text      # cancelada não tem botão


# ---------- falhas do banco ----------

def _banco_sem_escrita(monkeypatch):
    import app.main as main

    original = main.conexao

    def com_falha(somente_leitura=False):
        if not somente_leitura:
            raise duckdb.IOException("falha simulada de gravação")
        return original(somente_leitura=True)

    monkeypatch.setattr(main, "conexao", com_falha)


def test_falha_ao_agendar_nao_grava_e_avisa(semana, banco, monkeypatch):
    antes = total(banco)
    _banco_sem_escrita(monkeypatch)
    r = agendar(semana, medico_id="8", data="2026-11-05", hora="09:00")
    assert r.status_code == 500
    assert "Não foi possível salvar. Nada foi gravado. Tente novamente." in r.text
    assert 'id="dlg-falha"' in r.text
    assert total(banco) == antes


def test_falha_ao_cancelar_nao_muda_o_status(semana, banco, monkeypatch):
    _banco_sem_escrita(monkeypatch)
    r = semana.post("/agenda/3/cancelar", follow_redirects=False)
    assert r.status_code == 500
    assert "Não foi possível salvar. Nada foi gravado. Tente novamente." in r.text
    assert banco("SELECT status FROM visitas WHERE id = 3")[0][0] == "planejada"


def test_falha_do_banco_ao_ler_a_agenda_nao_derruba_a_tela(semana, monkeypatch):
    import app.main as main

    def quebrado(somente_leitura=False):
        raise duckdb.IOException("falha simulada")

    monkeypatch.setattr(main, "conexao", quebrado)
    r = semana.get("/agenda")
    assert r.status_code == 500
    assert "Não foi possível carregar a agenda. Tente novamente." in r.text


# ---------- integração com a home e o menu ----------

def test_home_e_menu_apontam_para_a_agenda(client):
    home = client.get("/home").text
    assert '<a class="tile" href="/agenda">' in home
    assert 'href="/agenda"' in home
