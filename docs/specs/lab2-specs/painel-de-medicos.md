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

## Fora de escopo
Metas, alertas, exportação, múltiplos representantes.
