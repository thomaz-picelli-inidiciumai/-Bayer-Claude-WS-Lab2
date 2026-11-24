# Spec: Painel de médicos a visitar

## Objetivo e usuário
Mostrar ao representante a carteira priorizada pelo tempo desde a última visita realizada, para decidir quem visitar primeiro.

## Critérios de aceite
1. **Dado** médicos com visitas `realizadas`, **quando** abro o painel, **então** a lista vem ordenada da última visita mais antiga para a mais recente; médicos sem nenhuma visita aparecem primeiro.
2. **Dado** visitas `canceladas` ou `planejadas`, **quando** calculo a última visita, **então** elas são ignoradas.
3. **Dado** a lista, **quando** filtro por especialidade ou busco por nome (parte do texto, sem diferenciar maiúsculas), **então** só vejo os médicos correspondentes.
4. **Dado** mais de 20 médicos, **quando** abro o painel, **então** vejo 20 por página com navegação Anterior/Próxima.
5. **Dado** uma visita recém registrada, **quando** volto ao painel, **então** o médico desce na lista.

## Campos e colunas
Nome (link para a ficha), especialidade, data da última visita (dd/mm/aaaa) e "há N dias". Filtro de especialidade com a lista de valores existentes em `medicos` mais "Todas". Busca por nome com placeholder "Buscar por nome".

## Interface (rotas e nomes de campo)
`GET /painel` (a função da rota se chama `painel`; é por esse nome que o ícone da home passa a apontar para a tela) com parâmetros opcionais na URL: `especialidade` (valor exato; vazio ou ausente = todas), `q` (parte do nome) e `pagina` (inteiro a partir de 1; inválido volta para 1).

## Estados da tela
- **Vazio:** "Nenhum médico encontrado para os filtros aplicados".
- **Erro de banco:** "Não foi possível carregar o painel. Tente novamente."

## Dados e regras
`medicos` com `LEFT JOIN` na última `visitas.data_hora` com status `realizada`. Dias desde a visita contados a partir da data atual do app.

## Critérios de aceite adicionais (experiência e robustez)
6. **Dado** o painel aberto, **quando** vejo o topo da tela, **então** há três cartões de resumo sobre a carteira inteira (sem considerar filtros): total de médicos, médicos sem nenhuma visita realizada e médicos sem visita realizada há mais de 90 dias (inclui os que nunca tiveram).
7. **Dado** a coluna "há N dias", **quando** vejo cada linha, **então** há um selo: verde até 30 dias, âmbar de 31 a 90, vermelho acima de 90 dias ou "Sem visita".
8. **Dado** `pagina` maior que a última página, **quando** abro o painel, **então** vejo a última página.
9. **Dado** cada linha do painel, **quando** clico em "Registrar visita", **então** vou para `/visitas/nova?medico_id=<id>` com o médico selecionado.
10. **Dado** uma falha do banco, **quando** abro o painel, **então** a resposta é 500 com "Não foi possível carregar o painel. Tente novamente." e um botão "Tentar novamente".

## Decisões de detalhe (resposta ao /checar-spec)
- A "última visita" considera visitas `realizada` de qualquer representante (a carteira é todos os médicos).
- A busca por nome ignora maiúsculas, mas diferencia acentos; os espaços nas pontas de `q` são removidos.
- Visita feita hoje mostra "hoje" em vez de "há 0 dias"; 1 dia mostra "há 1 dia".
- `especialidade` que não existe em `medicos` resulta no estado vazio, sem ignorar o filtro.
- "Hoje" vem de America/Sao_Paulo.

## Experiência
- Filtros em formulário `GET` (especialidade, busca por nome e botão "Limpar"), que funciona sem JavaScript; os links de página preservam os filtros.
- Layout em largura total. Abaixo de 720 px cada médico vira um cartão empilhado; a paginação continua alcançável com o polegar.
- Ordem do desempate: nome em ordem alfabética.
- Rodapé da tabela: "Mostrando X–Y de Z médicos".

## Fora de escopo
Metas, alertas, exportação, múltiplos representantes.
