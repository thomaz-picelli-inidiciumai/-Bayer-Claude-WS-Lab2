# Design system: tema "Terminal fósforo verde"

Status: **aprovada e implementada** (a fonte da verdade dos valores é o `:root` de `app/static/style.css`; além dos tokens abaixo existem `--bg-login`, `--hero-*`, `--text-on-cat`, `--radius-md/chip/round`, `--shadow-toast`, `--prompt-text`, `--menu-*`, `--title-prefix` e `--rotulo-*`). Gerada por `/redesenhar-visual`. Receita-base: B (Terminal), em `.claude/skills/redesenhar-visual/estilos.md`.

## 1. Objetivo
Trocar toda a aparência do BayViva para um terminal de fósforo verde sobre preto, sem alterar comportamento, rotas, nomes de campo, `id`, `data-*`, mensagens ou regras. Muda só a camada visual.

## 2. Decisões da entrevista
| Tema | Decisão |
|---|---|
| Direção | Terminal, texto verde sobre preto |
| Verde de base | Fósforo clássico `#33ff66` |
| Tema | Somente escuro (impressão sai em preto sobre branco) |
| Estados | Cores + prefixos de texto `[ OK ]`, `[ERRO]`, `[AVISO]` |
| Casca | Moderada: prompt no cabeçalho, menu `[home]`, títulos com `> ` |
| Efeitos | Brilho sutil só em títulos grandes (sem cursor piscante, sem scanlines) |
| Cantos / sombras | Retos (0), sem sombras, borda sólida de 1px |
| Tipografia | Monoespaçada em tudo, 14px base |
| Densidade | Confortável (`--control-h` 36px; 44px em tela estreita) |
| Logo | Símbolo atual em `currentColor` + nome em texto |
| Acessibilidade | WCAG AA (padrão) |
| Itens assumidos pelo padrão | Navegação continua como abas no topo; movimento sutil e desligado em `prefers-reduced-motion` |

## 3. Tokens (valores finais)
**Fundos:** `--bg #000000`, `--card #0a110a`, `--surface-alt #0f1a0f`, `--surface-input #050a05`, `--overlay #000000cc`.
**Texto:** `--text #33ff66`, `--text-weak #2ee05c`, `--text-muted #22b24a`, `--text-on-brand #000000`, `--text-link #5dff8a`.
**Bordas:** `--border #1f4d2a`, `--border-strong #2f8a45`.
**Marca:** `--brand #5dff8a`, `--brand-hover #8dffaa`, `--brand-dark #2ee05c`, `--brand-tint #0d2a14`, `--brand-tint-border #1f6b34`.
**Estados:** `--success #33ff66` / tint `#0d2a14` / texto `#5dff8a`; `--danger #ff5555` / tint `#2a0d0d` / texto `#ff7b7b`; `--warn #ffcc00` / tint `#2a2205` / texto `#ffd633`; `--info #5fafff`.
**Foco:** `--focus #00e5ff` (ciano, para não se confundir com o verde), `--focus-ring: 0 0 0 2px var(--focus)`.
**Categorias** (texto preto sobre elas): `--cat-conta #5fafff`, `--cat-visita #ffaf5f`, `--cat-insight #ffd75f`, `--cat-painel #5fffd7`, `--cat-agenda #ff87d7`.
**Tipografia:** `--font-body`/`--font-heading`/`--font-mono`: `"Cascadia Mono", Consolas, Menlo, "DejaVu Sans Mono", monospace`. Escala `--fs-xs 12px`, `--fs-sm 13px`, `--fs-base 14px`, `--fs-md 16px`, `--fs-lg 18px`, `--fs-xl 22px`, `--fs-2xl 28px`.
**Forma e profundidade:** `--radius-sm 0`, `--radius 0`, `--radius-lg 0`, `--radius-pill 0`; `--shadow-1/2/3: none`; `--blur 0`; `--glow: 0 0 6px #33ff6688` (só em `h1`/título de página).
**Densidade e movimento:** `--control-h 36px`, `--control-h-sm 28px`, `--control-h-lg 44px`, `--pad 16px`, `--gap 12px`, `--dur-fast .08s`, `--dur .15s`.
**Casca:** `--header-bg #000000`, `--nav-bg #000000`, `--nav-accent-w 2px`, `--logo-color var(--brand)`. `color-scheme: dark`.

## 4. Regras de uso
- Verde `--brand` para ação principal, link e item ativo; `--text` para leitura corrida; `--text-muted` só para rótulos secundários.
- Estado nunca só por cor: `.selo.ok::before` `[ OK ]`, `.selo.critico::before` `[ERRO]`, `.selo.atencao::before` `[AVISO]`; avisos, toasts e pop-ups já têm ícone ✓ / ! e ganham o rótulo em texto. Os textos de interface não mudam; os prefixos são decorativos (`::before`) e não entram nos testes.
- Casca por CSS, sem trocar texto de template: `.logo::after` `@vendas:~$`, `.menu a::before/::after` `[` `]`, `h1::before` `> `.
- Brilho (`--glow`) só em títulos ≥ 20px, nunca em texto pequeno.
- Ícones de objeto (`.icone.*`) usam as `--cat-*` com glifo preto.
- Impressão: `@media print` com fundo branco e texto preto.

## 5. Escopo: telas cobertas
`login`, `home`, `contas`, `ficha`, `visita_nova`, `painel`, `agenda`, `em_construcao`, mais a casca (`base.html`, `_ui.html`, `_simbolo.html`) e `app/static/style.css`.
Ajustes estruturais previstos: mover o `style=` inline de `ficha.html` para classe; trocar o ícone de busca em data-URI por máscara CSS que usa `currentColor`; `_simbolo.html` já usa `currentColor` (sem mudança de markup).

## 6. Critérios de aceite
1. Nenhuma cor literal (`#hex`, `rgb(`, `rgba(`) fora do `:root` em `style.css`, nos templates e em `app.js`; nenhum `style=` inline.
2. Todos os pares texto/fundo da seção 3 passam em AA. Relatório da checagem, lido direto do CSS final: 63 pares, 0 falhas; o menor é `borda de campo/cartão` 4.41:1 (mín. 3.0) e o menor de texto é `texto suave/fundo tintado` 5.55:1 (mín. 4.5).
3. As 8 telas abrem sem erro (200) e usam só tokens.
4. `pytest` passa **sem alterar nenhum teste**.
5. Foco por teclado visível (ciano) em botões, links, campos e pop-ups.
6. Em ~390px: a tabela vira cartões, alvos de toque ≥ 44px e não há rolagem horizontal da página.
7. Em `prefers-reduced-motion`, nenhuma animação.
8. Conferência visual feita nas telas, em desktop e celular (por captura se houver navegador, senão listada para conferência manual).

## 7. Fora de escopo
Banco, `db/seed.py`, rotas, regras de validação, textos de interface, novos componentes ou funcionalidades, fontes ou bibliotecas externas, logotipos de terceiros.

## 8. Riscos conhecidos
- Verde saturado sobre preto cansa em leitura longa: por isso texto de corpo em `#33ff66`/`#2ee05c` (não verde puro `#00ff00`), sem brilho em texto pequeno e fonte ≥ 13px.
- Conteúdo gerado por `::before`/`::after` (prompt, colchetes, `> `, `[ OK ]`) pode ser lido por leitores de tela; é aceitável por ser curto, e a decisão é revisável.
- Cascadia Mono/Consolas existem no Windows; em outros sistemas cai em Menlo/DejaVu/monospace.
