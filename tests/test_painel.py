"""Testes do Painel de médicos (docs/specs/lab2-specs/painel-de-medicos.md).

Relógio fixo pela fixture `client`: quarta-feira 04/11/2026 08:00.

Verificação manual (não dá para provar por HTTP; anotar o resultado no PR):
- Layout em 360, 768 e 1440 px: sem rolagem horizontal; abaixo de 720 px cada médico vira cartão.
- Selos de urgência legíveis (contraste) e cartões de resumo alinhados.
"""

import re
from datetime import datetime

import duckdb
import pytest

from app.db import conexao


def ids(resposta):
    return [int(i) for i in re.findall(r'<tr[^>]*data-medico="(\d+)"', resposta.text)]


def linha(resposta, medico_id):
    achou = re.search(rf'<tr[^>]*data-medico="{medico_id}"[^>]*>.*?</tr>', resposta.text, re.S)
    assert achou, f"médico {medico_id} não está na página"
    return achou.group(0)


def cartao(resposta, nome):
    achou = re.search(rf'data-resumo="{nome}"[^>]*>\s*<span class="valor">(\d+)<', resposta.text)
    assert achou, f"cartão {nome} não encontrado"
    return int(achou.group(1))


@pytest.fixture()
def carteira(client):
    """Quatro médicos com visitas conhecidas (hoje = 04/11/2026):

    1: realizadas 01/06 e 20/10          -> última 20/10, há 15 dias (verde)
    2: realizada 01/07 (de outro rep.)   -> há 126 dias (vermelho)
    3: só cancelada                      -> sem visita realizada
    4: realizada 15/09, cancelada 25/10, planejada 10/11 -> última 15/09, há 50 dias (âmbar)
    """
    with conexao() as con:
        con.execute("DELETE FROM visitas")
        con.execute("DELETE FROM medicos WHERE id > 4")
        con.executemany("INSERT INTO visitas VALUES (?, ?, ?, ?, ?, ?)", [
            (1, 1, 1, datetime(2026, 6, 1, 10), "realizada", "x" * 12),
            (2, 1, 1, datetime(2026, 10, 20, 9), "realizada", "x" * 12),
            (3, 2, 3, datetime(2026, 7, 1, 9), "realizada", "x" * 12),
            (4, 4, 1, datetime(2026, 9, 15, 9), "realizada", "x" * 12),
            (5, 4, 1, datetime(2026, 10, 25, 9), "cancelada", None),
            (6, 4, 1, datetime(2026, 11, 10, 9), "planejada", None),
            (7, 3, 1, datetime(2026, 10, 30, 9), "cancelada", None),
        ])
    return client


# ---------- critérios de aceite ----------

def test_criterio_1_ordem_da_mais_antiga_para_a_mais_recente_e_sem_visita_primeiro(carteira, banco):
    """Dado médicos com visitas realizadas, quando abro o painel, então a lista vai da última
    visita mais antiga para a mais recente; quem nunca teve visita vem primeiro."""
    r = carteira.get("/painel")
    assert r.status_code == 200
    assert ids(r) == [3, 2, 4, 1]


def test_criterio_2_canceladas_e_planejadas_sao_ignoradas(carteira):
    """Dado visitas canceladas ou planejadas, quando calculo a última visita, então elas são ignoradas."""
    r = carteira.get("/painel")
    assert "Sem visita" in linha(r, 3)                      # só tinha cancelada
    assert "15/09/2026" in linha(r, 4)                      # ignora cancelada 25/10 e planejada 10/11
    assert "25/10/2026" not in r.text and "10/11/2026" not in r.text


def test_ultima_visita_considera_qualquer_representante(carteira):
    assert "01/07/2026" in linha(carteira.get("/painel"), 2)


def test_colunas_data_e_dias(carteira):
    r = carteira.get("/painel")
    assert "20/10/2026" in linha(r, 1) and "há 15 dias" in linha(r, 1)
    assert "01/07/2026" in linha(r, 2) and "há 126 dias" in linha(r, 2)
    assert "há 50 dias" in linha(r, 4)


def test_visita_de_hoje_e_de_ontem(carteira):
    with conexao() as con:
        con.execute("INSERT INTO visitas VALUES (50, 1, 1, TIMESTAMP '2026-11-04 07:00:00', 'realizada', NULL)")
        con.execute("INSERT INTO visitas VALUES (51, 2, 1, TIMESTAMP '2026-11-03 07:00:00', 'realizada', NULL)")
    r = carteira.get("/painel")
    assert "hoje" in linha(r, 1)
    assert "há 1 dia" in linha(r, 2) and "há 1 dias" not in linha(r, 2)


def test_criterio_3_filtro_por_especialidade(client):
    """Dado a lista, quando filtro por especialidade, então só vejo os médicos correspondentes."""
    with conexao() as con:
        con.execute("UPDATE medicos SET especialidade = 'Clínica Geral' WHERE id IN (5, 6)")
    r = client.get("/painel", params={"especialidade": "Clínica Geral"})
    assert sorted(ids(r)) == [5, 6]
    r = client.get("/painel", params={"especialidade": ""})
    assert len(ids(r)) == 20  # vazio = todas


def test_filtro_de_especialidade_lista_valores_existentes_e_todas(client):
    with conexao() as con:
        con.execute("UPDATE medicos SET especialidade = 'Clínica Geral' WHERE id = 5")
    r = client.get("/painel")
    opcoes = re.findall(r'<option value="([^"]*)"', re.search(r'<select[^>]*name="especialidade".*?</select>', r.text, re.S).group(0))
    assert opcoes == ["", "Cardiologia", "Clínica Geral"]
    assert ">Todas<" in r.text


def test_criterio_3_busca_por_parte_do_nome_sem_diferenciar_caixa(client, banco):
    nomes = banco("SELECT id, nome FROM medicos")
    esperado = {i for i, n in nomes if "almeida" in n.lower()}
    assert 0 < len(esperado) <= 20
    for texto in ("almeida", "ALMEIDA", "  AlMeIdA "):
        assert set(ids(client.get("/painel", params={"q": texto}))) == esperado


def test_busca_e_filtro_juntos(client, banco):
    with conexao() as con:
        con.execute("UPDATE medicos SET especialidade = 'Clínica Geral' WHERE id = 5")
    nome5 = banco("SELECT nome FROM medicos WHERE id = 5")[0][0]
    r = client.get("/painel", params={"especialidade": "Clínica Geral", "q": nome5[4:9]})
    assert ids(r) == [5]
    r = client.get("/painel", params={"especialidade": "Cardiologia", "q": nome5})
    assert ids(r) == []


def test_estado_vazio_com_filtros_sem_resultado(client):
    r = client.get("/painel", params={"q": "zzzz"})
    assert r.status_code == 200
    assert "Nenhum médico encontrado para os filtros aplicados" in r.text
    r = client.get("/painel", params={"especialidade": "Inexistente"})
    assert "Nenhum médico encontrado para os filtros aplicados" in r.text


def test_busca_com_aspas_e_percentual_nao_quebra(client):
    for q in ("'; DROP TABLE medicos; --", "%", "_", '"'):
        assert client.get("/painel", params={"q": q}).status_code == 200
    assert client.get("/contas").text.count('href="/contas/') == 50


def test_criterio_4_vinte_por_pagina_com_anterior_e_proxima(client):
    """Dado mais de 20 médicos, quando abro o painel, então vejo 20 por página com Anterior/Próxima."""
    p1, p2, p3 = (client.get("/painel", params={"pagina": n}) for n in (1, 2, 3))
    assert (len(ids(p1)), len(ids(p2)), len(ids(p3))) == (20, 20, 10)
    assert len(set(ids(p1)) | set(ids(p2)) | set(ids(p3))) == 50   # sem repetir nem faltar
    assert "Próxima" in p1.text and "Anterior" in p1.text
    assert re.search(r'btn[^"]*desativado[^>]*>\s*Anterior', p1.text)       # primeira: sem anterior
    assert re.search(r'href="[^"]*pagina=2[^"]*"[^>]*>\s*Próxima', p1.text)
    assert re.search(r'href="[^"]*pagina=1[^"]*"[^>]*>\s*Anterior', p2.text)
    assert re.search(r'btn[^"]*desativado[^>]*>\s*Próxima', p3.text)        # última: sem próxima
    assert "Mostrando 21–40 de 50 médicos" in p2.text


@pytest.mark.parametrize("valor", ["abc", "0", "-3", "", "1.5"], ids=["texto", "zero", "negativo", "vazio", "decimal"])
def test_pagina_invalida_volta_para_a_primeira(client, valor):
    assert ids(client.get("/painel", params={"pagina": valor})) == ids(client.get("/painel"))


def test_pagina_alem_da_ultima_mostra_a_ultima(client):
    assert ids(client.get("/painel", params={"pagina": 99})) == ids(client.get("/painel", params={"pagina": 3}))


def test_links_de_pagina_preservam_os_filtros(client):
    r = client.get("/painel", params={"q": "dr", "especialidade": "Cardiologia"})
    link = re.search(r'href="([^"]*)"[^>]*>\s*Próxima', r.text).group(1).replace("&amp;", "&")
    assert "pagina=2" in link and "q=dr" in link and "especialidade=Cardiologia" in link


def test_criterio_5_medico_com_visita_nova_desce_na_lista(client):
    """Dado uma visita recém registrada, quando volto ao painel, então o médico desce na lista."""
    primeiro = ids(client.get("/painel"))[0]
    r = client.post("/visitas/nova", data={
        "medico_id": str(primeiro), "data_hora": "2026-11-04T07:30", "notas": "Visita para testar a ordem do painel.",
    })
    assert r.status_code == 200
    depois = ids(client.get("/painel"))
    assert primeiro not in depois
    ultima = ids(client.get("/painel", params={"pagina": 3}))
    assert ultima[-1] == primeiro      # a visita mais recente de todas fica no fim


# ---------- extras da spec emendada ----------

def test_cartoes_de_resumo(carteira):
    r = carteira.get("/painel")
    assert cartao(r, "total") == 4
    assert cartao(r, "sem-visita") == 1          # médico 3
    assert cartao(r, "mais-90-dias") == 2        # médico 3 (nunca) e médico 2 (126 dias)


def test_cartoes_ignoram_os_filtros(carteira):
    r = carteira.get("/painel", params={"q": "zzzz"})
    assert cartao(r, "total") == 4


def test_selos_de_urgencia(carteira):
    r = carteira.get("/painel")
    assert "selo ok" in linha(r, 1)           # 15 dias
    assert "selo atencao" in linha(r, 4)      # 50 dias
    assert "selo critico" in linha(r, 2)      # 126 dias
    assert "selo critico" in linha(r, 3)      # nunca visitado


def test_limites_dos_selos(carteira):
    with conexao() as con:
        con.execute("DELETE FROM visitas")
        con.executemany("INSERT INTO visitas VALUES (?, ?, 1, ?, 'realizada', NULL)", [
            (1, 1, datetime(2026, 10, 5, 9)),    # 30 dias
            (2, 2, datetime(2026, 10, 4, 9)),    # 31 dias
            (3, 3, datetime(2026, 8, 6, 9)),     # 90 dias
            (4, 4, datetime(2026, 8, 5, 9)),     # 91 dias
        ])
    r = carteira.get("/painel")
    assert "selo ok" in linha(r, 1)
    assert "selo atencao" in linha(r, 2)
    assert "selo atencao" in linha(r, 3)
    assert "selo critico" in linha(r, 4)


def test_linha_tem_link_para_ficha_e_botao_registrar_visita(carteira):
    r = carteira.get("/painel")
    assert 'href="/contas/1"' in linha(r, 1)
    assert 'href="/visitas/nova?medico_id=1"' in linha(r, 1)
    assert "Registrar visita" in linha(r, 1)


def test_botao_registrar_visita_leva_ao_medico_selecionado(client):
    r = client.get("/visitas/nova?medico_id=7")
    assert 'value="7" selected' in r.text


def test_formulario_de_filtros_e_get_e_tem_placeholder(client):
    r = client.get("/painel")
    form = re.search(r'<form[^>]*class="[^"]*filtros[^"]*"[^>]*>', r.text).group(0)
    assert 'method="get"' in form and 'action="/painel"' in form
    assert 'placeholder="Buscar por nome"' in r.text
    assert 'name="q"' in r.text and 'name="especialidade"' in r.text


def test_filtros_digitados_continuam_nos_campos(client):
    r = client.get("/painel", params={"q": "silva", "especialidade": "Cardiologia"})
    assert 'value="silva"' in r.text
    assert re.search(r'<option value="Cardiologia" selected', r.text)


def test_criterio_10_erro_de_banco_mostra_mensagem_e_tentar_novamente(client, monkeypatch):
    import app.main as main

    def quebrado(somente_leitura=False):
        raise duckdb.IOException("falha simulada")

    monkeypatch.setattr(main, "conexao", quebrado)
    r = client.get("/painel")
    assert r.status_code == 500
    assert "Não foi possível carregar o painel. Tente novamente." in r.text
    assert "Tentar novamente" in r.text
    assert 'href="/painel"' in r.text


def test_painel_com_prefixo_de_proxy(client, monkeypatch):
    monkeypatch.setenv("BAYVIVA_ROOT_PATH", "/proxy/8000")
    r = client.get("/painel")
    assert 'action="/proxy/8000/painel"' in r.text
    assert 'href="/proxy/8000/contas/' in r.text
    assert 'href="/proxy/8000/visitas/nova?medico_id=' in r.text


def test_menu_e_home_apontam_para_o_painel(client):
    assert 'href="/painel"' in client.get("/home").text
    assert '<a class="tile" href="/painel">' in client.get("/home").text
