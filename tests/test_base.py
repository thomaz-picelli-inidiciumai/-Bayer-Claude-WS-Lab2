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


def test_home_tem_icone_para_cada_tela_das_specs(client):
    r = client.get("/home")
    for titulo in ("Registrar visita", "Painel de médicos", "Agenda de visitas"):
        assert titulo in r.text
    # as três telas já existem: os ícones levam às rotas reais, não a "em construção"
    assert '<a class="tile" href="/visitas/nova">' in r.text
    assert '<a class="tile" href="/painel">' in r.text
    assert '<a class="tile" href="/agenda">' in r.text
    for tela in ("visitas", "painel", "agenda"):
        assert f"/em-construcao/{tela}" not in r.text
    # as extensões continuam em construção
    assert '<a class="tile" href="/em-construcao/insight">' in r.text
    assert '<a class="tile" href="/em-construcao/nova-conta">' in r.text


def test_home_icone_aponta_para_a_rota_real_quando_ela_existe(client, monkeypatch):
    """O ícone se liga sozinho quando existe uma função de rota com o nome indicado em ATALHOS."""
    import app.main as main

    atalhos = [{**a, "rota": "insight_teste"} if a["slug"] == "insight" else a for a in main.ATALHOS]
    monkeypatch.setattr(main, "ATALHOS", atalhos)
    assert '<a class="tile" href="/em-construcao/insight">' in client.get("/home").text

    def insight_teste():
        return "ok"

    main.app.add_api_route("/insight-teste", insight_teste, name="insight_teste")
    try:
        r = client.get("/home")
        assert '<a class="tile" href="/insight-teste">' in r.text
        assert '<a class="tile" href="/em-construcao/insight">' not in r.text
    finally:
        main.app.router.routes.pop()


def test_home_icone_respeita_prefixo_de_proxy(client):
    r = client.get("/home", headers={"X-Forwarded-Prefix": "/proxy/8001"})
    assert 'href="/proxy/8001/agenda"' in r.text
    assert 'href="/proxy/8001/visitas/nova"' in r.text
    assert 'href="/proxy/8001/em-construcao/insight"' in r.text


def test_menu_superior_leva_as_telas_reais(client):
    r = client.get("/home")
    for caminho in ("/visitas/nova", "/painel", "/agenda"):
        assert f'<a href="{caminho}" class=' in r.text
