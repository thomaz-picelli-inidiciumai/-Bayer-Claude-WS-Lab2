"""Guarda do design system (docs/specs/design-system.md): lê o CSS e os templates, sem subir o app."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = (RAIZ / "app" / "static" / "style.css").read_text(encoding="utf-8")
TEMPLATES = sorted((RAIZ / "app" / "templates").glob("*.html"))
JS = (RAIZ / "app" / "static" / "app.js").read_text(encoding="utf-8")


def _blocos_raiz(css: str) -> list[tuple[int, int]]:
    """Intervalos (início, fim) dos blocos `:root { ... }`, inclusive o dentro de @media print."""
    intervalos = []
    for m in re.finditer(r":root\s*\{", css):
        profundidade, i = 1, m.end()
        while profundidade and i < len(css):
            profundidade += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        intervalos.append((m.start(), i))
    return intervalos


def _fora_da_raiz(css: str) -> str:
    texto, ultimo = [], 0
    for ini, fim in _blocos_raiz(css):
        texto.append(css[ultimo:ini])
        ultimo = fim
    texto.append(css[ultimo:])
    return "".join(texto)


def _bloco_media_celular(css: str) -> str:
    """Conteúdo dos @media (max-width: 720px) do arquivo, concatenados."""
    partes = []
    for m in re.finditer(r"@media \(max-width: 720px\)\s*\{", css):
        profundidade, i = 1, m.end()
        while profundidade and i < len(css):
            profundidade += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        partes.append(css[m.end():i - 1])
    return "\n".join(partes)


def test_nenhuma_cor_literal_fora_da_raiz():
    achados = re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", _fora_da_raiz(CSS))
    assert achados == [], f"cor literal fora do :root: {achados[:5]}"


def test_templates_e_js_sem_cor_literal_nem_estilo_inline():
    for caminho in TEMPLATES:
        texto = caminho.read_text(encoding="utf-8")
        assert not re.search(r"\bstyle=|<style", texto), f"estilo inline em {caminho.name}"
        assert not re.search(r"#[0-9a-fA-F]{6}\b", texto), f"cor literal em {caminho.name}"
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", JS), "cor literal em app.js"


def test_campos_com_16px_no_celular():
    celular = _bloco_media_celular(CSS)
    regra = re.search(r"input[^{}]*select[^{}]*textarea[^{}]*\{([^}]*)\}", celular)
    assert regra, "falta regra de input/select/textarea no @media de celular"
    assert re.search(r"font-size:\s*16px", regra.group(1))


def test_nenhum_texto_menor_que_12px():
    menores = [int(n) for n in re.findall(r"font-size:\s*(\d+)px", CSS) if int(n) < 12]
    assert menores == [], f"font-size abaixo de 12px: {menores}"


def test_estado_pressionado_toque_rapido_e_quebra_de_texto_longo():
    assert re.search(r"\.btn[^{,]*:active[^{]*\{[^}]*color:\s*var\(--bg\)", CSS), "falta estado pressionado em .btn"
    assert re.search(r"touch-action:\s*manipulation", CSS)
    assert re.search(r"overflow-wrap:\s*anywhere", CSS)
