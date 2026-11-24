"""Testes da tela Registrar visita (docs/specs/lab2-specs/registrar-visita.md).

Relógio fixo pela fixture `client`: quarta-feira 04/11/2026 08:00 (America/Sao_Paulo).

Verificação manual (não dá para provar por HTTP; anotar o resultado no PR):
- Critério 4: ao clicar em Salvar o botão fica desabilitado com "Salvando…" e um segundo
  clique não envia de novo.
- Critério 9: com campo inválido, o navegador não envia, mostra as mesmas mensagens e o
  mesmo pop-up do servidor, e o foco vai para o primeiro campo com erro.
- Layout: duas colunas a partir de 900 px, uma coluna abaixo; sem rolagem horizontal em 360 px.
- Pop-up: fecha com Esc, com o botão e com clique no fundo; foco preso dentro dele.
"""

import re

import duckdb
import pytest

OK = {"medico_id": "1", "data_hora": "2026-11-03T10:00", "notas": "Conversa util sobre o protocolo."}


def postar(client, **campos):
    return client.post("/visitas/nova", data={**OK, **campos})


def total(banco):
    return banco("SELECT count(*) FROM visitas")[0][0]


# ---------- tela (GET) ----------

def test_formulario_abre_com_os_campos_da_spec(client):
    r = client.get("/visitas/nova")
    assert r.status_code == 200
    for trecho in ('name="medico_id"', 'name="data_hora"', 'name="notas"', 'type="datetime-local"',
                   "Selecione um médico", "Resuma o que foi discutido (mín. 10 caracteres)"):
        assert trecho in r.text
    assert "Visita registrada com sucesso" not in r.text


def test_medicos_em_ordem_alfabetica(client, banco):
    r = client.get("/visitas/nova")
    nomes = re.findall(r'<option value="\d+"[^>]*>([^<]+)</option>', r.text)
    esperado = [n for (n,) in banco("SELECT nome FROM medicos ORDER BY nome")]
    assert nomes == esperado
    assert len(nomes) == 50


def test_formulario_tem_marcacoes_para_o_javascript(client):
    """Contrato de marcação (não prova o clique do critério 4: isso é verificação manual)."""
    r = client.get("/visitas/nova")
    assert 'data-valida="visita"' in r.text
    assert "data-enviar" in r.text
    assert 'data-agora="2026-11-04T08:00:00"' in r.text
    assert 'max="2026-11-04T08:00"' in r.text


def test_links_do_formulario_respeitam_prefixo_de_proxy(client, monkeypatch):
    monkeypatch.setenv("BAYVIVA_ROOT_PATH", "/proxy/8000")
    r = client.get("/visitas/nova")
    assert 'action="/proxy/8000/visitas/nova"' in r.text
    assert "/proxy/8000/static/app.js" in r.text


# ---------- critério 1 ----------

def test_criterio_1_grava_visita_e_mostra_sucesso(client, banco):
    """Dado o formulário preenchido com dados válidos, quando clico em Salvar, então uma linha
    é gravada em visitas (realizada, representante 1) e vejo "Visita registrada com sucesso"."""
    antes = total(banco)
    maior_id = banco("SELECT max(id) FROM visitas")[0][0]

    r = postar(client)

    assert r.status_code == 200
    assert "Visita registrada com sucesso" in r.text
    assert total(banco) == antes + 1
    linha = banco(
        "SELECT id, medico_id, representante_id, status, notas, strftime(data_hora, '%Y-%m-%dT%H:%M') "
        "FROM visitas ORDER BY id DESC LIMIT 1"
    )[0]
    assert linha == (maior_id + 1, 1, 1, "realizada", OK["notas"], "2026-11-03T10:00")


def test_criterio_1_sucesso_abre_popup_com_resumo_e_link_para_painel(client):
    r = postar(client, medico_id="2")
    assert 'id="dlg-sucesso"' in r.text
    assert "Ver painel" in r.text
    assert 'href="/painel"' in r.text
    assert "03/11/2026" in r.text and "10:00" in r.text


def test_criterio_1_formulario_volta_limpo_apos_sucesso(client):
    r = postar(client, notas="Texto que nao deve voltar ao formulario.")
    corpo_textarea = re.search(r"<textarea[^>]*>(.*?)</textarea>", r.text, re.S).group(1)
    assert corpo_textarea.strip() == ""
    assert not re.search(r'<option value="\d+" selected', r.text)


def test_notas_sao_gravadas_sem_espacos_nas_pontas(client, banco):
    postar(client, notas="   Texto com espacos nas pontas.   ")
    assert banco("SELECT notas FROM visitas ORDER BY id DESC LIMIT 1")[0][0] == "Texto com espacos nas pontas."


# ---------- critério 2 ----------

@pytest.mark.parametrize("campo,mensagem", [
    ("medico_id", "Selecione um médico"),
    ("data_hora", "Informe a data e a hora da visita"),
    ("notas", "Informe de 10 a 1000 caracteres"),
], ids=["medico", "data_hora", "notas"])
def test_criterio_2_campo_obrigatorio_vazio_nao_grava(client, banco, campo, mensagem):
    """Dado campo obrigatório vazio, quando clico em Salvar, então nada é gravado e vejo o erro
    ao lado do campo."""
    antes = total(banco)
    r = postar(client, **{campo: ""})
    assert r.status_code == 422
    assert total(banco) == antes
    assert "Visita registrada com sucesso" not in r.text
    junto = re.search(rf'data-erro-de="{campo}"[^>]*>([^<]*)<', r.text)
    assert junto and junto.group(1).strip() == mensagem


def test_criterio_2_erros_aparecem_no_popup_e_dados_sao_mantidos(client):
    r = postar(client, medico_id="3", data_hora="", notas="curta")
    assert r.status_code == 422
    popup = re.search(r'<dialog id="dlg-erros"[^>]*>', r.text).group(0)
    assert " open" in popup and "data-modal" in popup
    assert "Data e hora:" in r.text and "Notas:" in r.text
    assert 'value="3" selected' in r.text
    assert ">curta</textarea>" in r.text
    assert 'id="dlg-sucesso"' not in r.text


def test_sucesso_nao_tem_popup_de_erro_aberto(client):
    r = postar(client)
    assert " open" not in re.search(r'<dialog id="dlg-erros"[^>]*>', r.text).group(0)


# ---------- critério 3 (depende do painel) ----------

def test_criterio_3_ultima_visita_no_painel(client):
    """Dado uma visita salva e o painel construído, quando abro o painel, então a "última
    visita" do médico mostra essa data."""
    r = postar(client, medico_id="1", data_hora="2026-11-04T07:30")
    assert r.status_code == 200
    # a visita mais recente de todas leva o médico para o fim da lista (última página)
    painel = client.get("/painel", params={"pagina": 3})
    assert painel.status_code == 200
    linha = re.search(r'<tr[^>]*data-medico="1"[^>]*>.*?</tr>', painel.text, re.S)
    assert linha and "04/11/2026" in linha.group(0)


# ---------- regras dos campos ----------

def test_data_hora_futura_e_recusada_e_igual_ao_agora_e_aceita(client, banco):
    antes = total(banco)
    r = postar(client, data_hora="2026-11-04T08:01")
    assert r.status_code == 422
    assert "A data da visita não pode estar no futuro" in r.text
    assert total(banco) == antes

    r = postar(client, data_hora="2026-11-04T08:00")
    assert r.status_code == 200
    assert total(banco) == antes + 1


@pytest.mark.parametrize("tamanho,aceita", [(9, False), (10, True), (1000, True), (1001, False)])
def test_limites_das_notas(client, banco, tamanho, aceita):
    antes = total(banco)
    r = postar(client, notas="a" * tamanho)
    assert r.status_code == (200 if aceita else 422)
    assert total(banco) == antes + (1 if aceita else 0)
    if not aceita:
        assert "Informe de 10 a 1000 caracteres" in r.text


@pytest.mark.parametrize("notas", [
    "Falar com ana@example.com na semana que vem",
    "Ligar para 11 98765-4321 depois do almoco",
    "Telefone (11) 9876-5432 do consultorio",
    "Numero 12345678 anotado errado",
], ids=["email", "telefone-hifen", "telefone-parenteses", "oito-digitos"])
def test_notas_com_dado_pessoal_sao_recusadas(client, banco, notas):
    antes = total(banco)
    r = postar(client, notas=notas)
    assert r.status_code == 422
    assert "Remova dados pessoais das notas" in r.text
    assert total(banco) == antes


def test_sete_digitos_nao_sao_telefone(client):
    assert postar(client, notas="Protocolo 1234567 revisado hoje").status_code == 200


@pytest.mark.parametrize("valor", ["9999", "abc", "0"], ids=["inexistente", "texto", "zero"])
def test_medico_inexistente_e_recusado(client, banco, valor):
    antes = total(banco)
    r = postar(client, medico_id=valor)
    assert r.status_code == 422
    assert "Selecione um médico" in r.text
    assert total(banco) == antes


def test_varios_erros_juntos_nao_gravam_nada(client, banco):
    antes = total(banco)
    r = postar(client, medico_id="", data_hora="", notas="")
    assert r.status_code == 422
    for msg in ("Selecione um médico", "Informe a data e a hora da visita", "Informe de 10 a 1000 caracteres"):
        assert msg in r.text
    assert total(banco) == antes


# ---------- visita duplicada ----------

def test_visita_duplicada_e_recusada(client, banco):
    antes = total(banco)
    assert postar(client).status_code == 200
    r = postar(client, notas="Outro texto qualquer valido.")
    assert r.status_code == 422
    assert "Esta visita já foi registrada" in r.text
    assert re.search(r'data-erro-de="data_hora"[^>]*>\s*Esta visita já foi registrada', r.text)
    assert total(banco) == antes + 1


def test_mesma_hora_de_outro_medico_nao_e_duplicada(client, banco):
    antes = total(banco)
    assert postar(client, medico_id="1").status_code == 200
    assert postar(client, medico_id="2").status_code == 200
    assert total(banco) == antes + 2


def test_visita_cancelada_nao_conta_como_duplicada(client, banco):
    from app.db import conexao

    with conexao() as con:
        con.execute(
            "INSERT INTO visitas VALUES (999999, 1, 1, TIMESTAMP '2026-11-03 10:00:00', 'cancelada', NULL)"
        )
    assert postar(client).status_code == 200


# ---------- médico pré-selecionado ----------

def test_medico_id_na_url_preseleciona(client):
    r = client.get("/visitas/nova?medico_id=7")
    assert 'value="7" selected' in r.text


@pytest.mark.parametrize("valor", ["9999", "abc", ""], ids=["inexistente", "texto", "vazio"])
def test_medico_id_invalido_na_url_e_ignorado(client, valor):
    r = client.get(f"/visitas/nova?medico_id={valor}")
    assert r.status_code == 200
    assert not re.search(r'<option value="\d+" selected', r.text)


# ---------- falha de gravação ----------

def _quebrar_gravacao(monkeypatch):
    """Faz toda conexão de escrita do app falhar, como um disco cheio ou banco travado."""
    import app.main as main

    original = main.conexao

    def com_falha(somente_leitura=False):
        if not somente_leitura:
            raise duckdb.IOException("falha simulada de gravação")
        return original(somente_leitura=True)

    monkeypatch.setattr(main, "conexao", com_falha)


def test_falha_do_banco_nao_grava_e_avisa(client, banco, monkeypatch):
    """Dado erro do banco ao gravar, então 500, pop-up de falha e dados mantidos."""
    antes = total(banco)
    _quebrar_gravacao(monkeypatch)
    r = postar(client, notas="Texto que precisa continuar na tela.")
    assert r.status_code == 500
    assert "Não foi possível salvar. Nada foi gravado. Tente novamente." in r.text
    assert 'id="dlg-falha"' in r.text
    assert "Visita registrada com sucesso" not in r.text
    assert ">Texto que precisa continuar na tela.</textarea>" in r.text
    assert total(banco) == antes


def test_falha_ao_gravar_tambem_nao_deixa_visita_pela_metade(client, banco, monkeypatch):
    import app.main as main

    class ConexaoQueFalhaNoInsert:
        def __init__(self, real):
            self.real = real

        def execute(self, sql, *a, **k):
            if sql.lstrip().upper().startswith("INSERT"):
                raise duckdb.Error("falha no INSERT")
            return self.real.execute(sql, *a, **k)

        def close(self):
            self.real.close()

    original = main.conexao
    from contextlib import contextmanager

    @contextmanager
    def com_falha(somente_leitura=False):
        with original(somente_leitura=somente_leitura) as con:
            yield con if somente_leitura else ConexaoQueFalhaNoInsert(con)

    monkeypatch.setattr(main, "conexao", com_falha)
    antes = total(banco)
    r = postar(client)
    assert r.status_code == 500
    assert total(banco) == antes
