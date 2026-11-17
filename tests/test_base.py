"""Testes de exemplo da base: login, home e contas."""


def test_raiz_redireciona_para_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "/login"


def test_login_tem_botao_entrar(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Entrar" in r.text


def test_home_mostra_atalhos(client):
    r = client.get("/home")
    assert r.status_code == 200
    for texto in ("Registrar visita", "Registrar insight", "Nova conta"):
        assert texto in r.text


def test_contas_lista_50_medicos(client):
    r = client.get("/contas")
    assert r.status_code == 200
    assert r.text.count('href="/contas/') == 50


def test_ficha_do_medico(client):
    r = client.get("/contas/1")
    assert r.status_code == 200
    assert "BV-0001" in r.text
    assert "Cardiologia" in r.text


def test_ficha_inexistente_retorna_404(client):
    assert client.get("/contas/9999").status_code == 404


def test_seed_e_deterministico(tmp_path):
    import duckdb
    import seed

    dados = []
    for nome in ("a.duckdb", "b.duckdb"):
        p = tmp_path / nome
        seed.criar(p)
        con = duckdb.connect(str(p))
        dados.append(con.execute("SELECT count(*), sum(medico_id) FROM visitas").fetchall())
        con.close()
    assert dados[0] == dados[1]


def test_links_com_prefixo_de_proxy_por_variavel(client, monkeypatch):
    monkeypatch.setenv("BAYVIVA_ROOT_PATH", "/proxy/8000")
    r = client.get("/login", follow_redirects=False)
    assert "/proxy/8000/static/style.css" in r.text
    assert 'href="/proxy/8000/home"' in r.text
    r = client.get("/contas")
    assert 'action="/proxy/8000/contas"' in r.text
    assert 'href="/proxy/8000/contas/1"' in r.text
    r = client.get("/", follow_redirects=False)
    assert r.headers["location"] == "/proxy/8000/login"


def test_links_com_prefixo_de_proxy_por_header(client):
    r = client.get("/home", headers={"X-Forwarded-Prefix": "/proxy/8001/"})
    assert "/proxy/8001/static/style.css" in r.text
    assert 'href="/proxy/8001/contas"' in r.text


def test_sem_prefixo_links_continuam_na_raiz(client):
    r = client.get("/home")
    assert 'href="/static/style.css"' in r.text
    assert 'href="/contas"' in r.text


def test_proxy_que_nao_remove_o_prefixo(client, monkeypatch):
    monkeypatch.setenv("BAYVIVA_ROOT_PATH", "/proxy/8000")
    assert client.get("/proxy/8000/home").status_code == 200
    assert client.get("/proxy/8000/static/style.css").status_code == 200
    assert client.get("/home").status_code == 200
