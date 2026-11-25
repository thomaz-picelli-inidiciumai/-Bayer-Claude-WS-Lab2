# Receitas de direções visuais

Use para **propor opções** na entrevista e como ponto de partida; os valores são sugestões, o usuário ajusta. Cada receita diz como preencher os tokens do contrato ([tokens.md](tokens.md)) e o que muda na estrutura. Marcas reais: sempre peça os hex oficiais ao usuário; as cores abaixo são aproximações genéricas "no espírito", não identidade oficial.

## A. "iPhone / Apple" (iOS claro)
Sensação: limpo, vidro fosco, cantos generosos, muito espaço, texto grande.
- Fundos: `--bg #f2f2f7`, `--card #ffffff`, `--surface-alt #f9f9fb`. Escuro: `--bg #000000` (iOS usa preto), `--card #1c1c1e`.
- Texto: `--text #000000` (ou `#1c1c1e`), `--text-weak #3c3c43`, `--text-muted #6c6c70` (o `#8e8e93` de iOS não passa AA sobre branco; avise).
- Marca (azul sistema): `--brand #007aff` → para texto/botão AA prefira `#0062cc`; estados: sucesso `#34c759`/texto `#1d7a38`, perigo `#ff3b30`/texto `#c4281e`, aviso `#ff9500`/texto `#8a5300`.
- Fonte: `-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, "Segoe UI", sans-serif` (a SF só existe em dispositivos Apple; fora deles cai em Segoe/Roboto, avise).
- Forma: `--radius 10px`, `--radius-lg 14px`, botões grandes `--radius-pill` ou 12px; `--control-h 44px`.
- Profundidade: sombras quase invisíveis, `--blur 20px` com cabeçalho/pop-up translúcidos (`backdrop-filter: saturate(180%) blur(var(--blur))` + fundo `color-mix` com transparência). Sem bordas pesadas; separadores de 0.5-1px em `--border`.
- Casca: título grande no topo de cada tela (`.page-header h1` ~28-34px, negrito); navegação como **barra de abas inferior** em telas estreitas (ícone + rótulo, fixa), e barra superior/translúcida no desktop. Listas como "grupos inset" (cartões de cantos grandes, linhas com separador).
- Movimento: curvas suaves (`cubic-bezier(.2,.8,.2,1)`), pop-up estilo "folha" subindo.
- Cuidado: não usar o logotipo nem o ícone da Apple; "estilo iOS" é só linguagem visual.

## B. Terminal (tela preta, letras verdes)
Sensação: retrô, técnico, monoespaçado, sem arredondar nada.
- Fundos: `--bg #000000` (ou `#050805`), `--card #0a0f0a`, bordas `#1f3d1f`.
- Texto: `--text #33ff66` (ou `#39ff14`), `--text-weak #2bd957`, `--text-muted #1f9e3f` (confira AA sobre preto: precisa ≥ 4.5; clareie se falhar).
- Marca/ênfase: verde claro `--brand #5dff8a`; texto sobre marca = preto `--text-on-brand #000`.
- Estados (cor sozinha não basta, tudo é verde!): perigo em vermelho/laranja `#ff5555`, aviso `#ffcc00`, **e** prefixos de texto `[ OK ]`, `[ERRO]`, `[AVISO]` via `::before`.
- Fonte: `"Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", monospace` em **tudo** (`--font-body` = `--font-heading` = mono); tamanho 14px+.
- Forma: `--radius 0`, `--radius-lg 0`, sem sombras (`--shadow-* none`), borda de 1px sólida; foco = contorno tracejado ou bloco invertido; cursor piscante opcional (`::after` com animação, desligado em `prefers-reduced-motion`).
- Casca: cabeçalho como linha de prompt (`usuario@bayviva:~$`) no lugar do logo (texto); navegação como lista de comandos `[home] [contas] [visitas]`; títulos em caixa alta ou prefixados com `> `. Tabelas com bordas de caracteres simples. Brilho (`text-shadow: 0 0 6px`) só como detalhe, nunca em texto pequeno.
- Cuidado: efeito de scanlines/CRT só se o usuário pedir (prejudica leitura).

## C. Identidade de uma marca (ex.: Bayer)
Sensação: corporativa, confiável, seguindo manual de marca.
- **Pergunte, não invente:** hex primários e secundários oficiais, fonte oficial (e se existe licença/arquivo), regra de uso do logo (área de respiro, versão sobre fundo escuro), tom de voz. Peça o arquivo do logo (SVG).
- Mapeamento: cor primária → `--brand`; derive `--brand-hover`, `--brand-dark`, `--brand-tint` por `color-mix`; cores secundárias → categorias (`--cat-*`) e gráficos; neutros da marca → `--bg`, `--border`, `--text`.
- Se a cor primária da marca não passa AA como texto sobre branco (comum com cores vibrantes), use-a em fundos/botões com texto da cor certa (branco ou escuro) e use uma variação mais escura para links e texto.
- Fonte oficial só se o usuário fornecer o arquivo e confirmar o direito de uso; senão, fonte de sistema com pesos e proporções parecidas e aviso.
- Casca: logo no cabeçalho (via arquivo do usuário), faixa/linha de marca na navegação, rodapé sóbrio se pedido. Tom formal e muito espaço em branco; raio pequeno (2-6px).
- Como o repositório é fictício, mantenha o nome do app e os dados fictícios; só a **aparência** muda.

## D. Corporativo clássico (tipo CRM de mercado)
Densidade compacta, cantos 2-4px, azul sóbrio, bordas finas, tabelas densas, tipografia 13px. É o caminho de volta ao "estilo Lightning" original.

## E. Escuro moderno (dev tools)
`--bg #0e1116`, `--card #161b22`, bordas `#30363d`, texto `#e6edf3`, marca azul/violeta clareada, sombras trocadas por borda, raio 6-8px, fonte de sistema + mono nos números, `color-scheme: dark`.

## F. Acessibilidade máxima (alto contraste)
Texto preto sobre branco (ou o inverso), bordas de 2px, foco de 3px, fonte 16px, `--control-h 48px`, sem transparências, sem depender de cor, cantos sutis. Bom como opção "para impressão e uso em campo, ao sol".

## G. Amigável / lúdico
Cores quentes e saturadas com neutros suaves, raio 14-20px e pílulas, ícones grandes, sombras coloridas leves, fonte arredondada **do sistema** se houver (`ui-rounded`, "Nunito" só local), movimento sutil de "quique" desligável.

## H. Editorial / sofisticado
Fundo off-white quente, texto quase preto, **serifada nos títulos** (Georgia/"Iowan Old Style"/Cambria) e sans no corpo, linhas finas no lugar de cartões, cor de marca usada com parcimônia, muito respiro.

## I. Brutalista
Bordas pretas de 2-3px, sombras duras sem desfoque (`4px 4px 0 var(--text)`), cores chapadas e vivas, raio 0, tipografia grande e pesada. Mantenha contraste e foco claros.

## Como combinar com a entrevista
- Mostre 2-3 receitas próximas do que o usuário descreveu, com uma linha de "como fica" cada uma, e deixe misturar ("A no desktop com cor da marca C").
- Quando o pedido for vago ("quero algo mais moderno"), ofereça D, E e A como três pontos de partida e peça escolha.
- Sempre registre em `docs/specs/design-system.md` qual receita foi base e o que foi ajustado.
