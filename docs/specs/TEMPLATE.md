# Template de spec

Copie este arquivo para `docs/specs/<tela>.md` e preencha todas as seções. Uma seção vazia é uma pergunta que o agente vai responder por conta própria.

## Objetivo e usuário
Quem usa e o que precisa conseguir fazer, em uma ou duas frases.

## Critérios de aceite
Numerados, no formato **Dado** (estado inicial), **quando** (ação), **então** (resultado que dá para observar). Cada critério deve virar um teste.

## Campos e validações
Tabela: campo, tipo, obrigatório, regra, placeholder e mensagem de erro.

## Interface (rotas e nomes de campo)
Rotas, métodos HTTP, nomes dos campos do formulário ou parâmetros e o que cada resposta devolve (status e mensagem). Sem isso não há como escrever o teste antes do código.

## Estados da tela
Vazio, carregando, erro e sucesso: o que o usuário vê em cada um.

## Dados e regras de negócio
Em quais tabelas e colunas gravar ou ler, valores permitidos e regras (por exemplo, "visita cancelada não conta como conflito").

## Fora de escopo
O que esta spec propositalmente não cobre.
