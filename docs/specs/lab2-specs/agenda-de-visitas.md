# Spec: Agenda de visitas

## Objetivo e usuário
Permitir que o representante veja e planeje suas visitas por dia na semana.

## Critérios de aceite
1. **Dado** visitas `planejadas`, **quando** abro a agenda, **então** vejo a semana corrente (segunda a sexta) com as visitas de cada dia ordenadas por horário.
2. **Dado** que adiciono uma visita em um horário, **quando** já existe visita `planejada` do mesmo representante no mesmo horário, **então** a gravação é recusada com "Já existe uma visita neste horário".
3. **Dado** uma visita `cancelada`, **quando** vejo a agenda, **então** ela aparece riscada e não conta como conflito.
4. **Dado** a navegação Semana anterior/próxima, **quando** clico, **então** a agenda muda de semana.
5. **Dado** que adiciono uma visita no passado, **então** vejo "Escolha um horário futuro".

## Campos e validações
Médico (obrigatório, lista), data (obrigatória, dia útil), hora (obrigatória, de 08:00 a 18:00 em intervalos de 30 min). Mensagens de erro ao lado do campo.

## Interface (rotas e nomes de campo)
- `GET /agenda?semana=AAAA-MM-DD`: mostra segunda a sexta da semana que contém essa data; sem o parâmetro, a semana atual. A função da rota se chama `agenda` (é por esse nome que o ícone da home passa a apontar para a tela).
- `POST /agenda/nova`: campos `medico_id`, `data` (`AAAA-MM-DD`) e `hora` (`HH:MM`). Sucesso: 303 para `/agenda?semana=<data>`. Erro de validação ou conflito: 422, nada é gravado.

## Estados da tela
- **Vazio:** dia sem visitas mostra "Sem visitas".
- **Sucesso:** visita aparece no dia correto sem recarregar a semana errada.
- **Erro:** mensagens por campo.

## Dados e regras
- Gravar em `visitas` com status `planejada`, `notas` vazio.
- Horário único no fuso America/Sao_Paulo; `data_hora` armazenada sem fuso, nesse horário local.
- Duração fixa de 30 minutos.

## Critérios de aceite adicionais (experiência e robustez)
6. **Dado** uma data de fim de semana, **quando** tento adicionar, **então** vejo "Escolha um dia útil" e nada é gravado (422).
7. **Dado** uma hora fora da grade (antes de 08:00, depois de 18:00 ou fora dos intervalos de 30 minutos), **quando** tento adicionar, **então** vejo "Escolha um horário entre 08:00 e 18:00, de 30 em 30 minutos" (422). O horário 18:00 é aceito.
8. **Dado** uma data de hoje com hora que já passou, **quando** tento adicionar, **então** vejo "Escolha um horário futuro". "Futuro" é estritamente maior que o momento atual.
9. **Dado** uma visita adicionada com sucesso, **quando** a agenda recarrega (303), **então** vejo uma mensagem "Visita agendada para <dd/mm> às <HH:MM>" uma única vez (não reaparece ao recarregar a página).
10. **Dado** uma visita `planejada` do representante 1, **quando** clico em "Cancelar" e confirmo, **então** `POST /agenda/{id}/cancelar` muda o status para `cancelada`, responde 303 para a semana da visita e a visita aparece riscada. Visita inexistente, de outro representante ou que não esteja `planejada` responde 404 e nada muda.
11. **Dado** uma falha do banco ao gravar, **quando** tento adicionar ou cancelar, **então** a resposta é 500, nada é gravado e vejo "Não foi possível salvar. Nada foi gravado. Tente novamente."
12. **Dado** `semana` inválida (texto que não é data), **quando** abro a agenda, **então** vejo a semana atual.

## Dados e regras adicionais
- A agenda mostra apenas visitas do representante 1, com status `planejada` ou `cancelada`. Visitas `realizada` não aparecem.
- A verificação de conflito e a gravação ocorrem na mesma transação.
- O conflito considera só visitas `planejada` do mesmo representante e o mesmo `data_hora`.

## Decisões de detalhe (resposta ao /checar-spec)
- Dia útil é segunda a sexta; feriados não são considerados.
- Validação nesta ordem, uma mensagem por campo: médico ("Selecione um médico"); data vazia ou inválida ("Informe a data"), fim de semana ("Escolha um dia útil"); hora vazia ou fora da grade (mensagem do critério 7); depois, só se data e hora forem válidas, passado ("Escolha um horário futuro") e conflito ("Já existe uma visita neste horário").
- "Escolha um horário futuro" e "Já existe uma visita neste horário" aparecem junto do campo Hora.
- A semana é a civil (segunda a domingo) que contém a data de `semana`; a tela mostra segunda a sexta dela. Sábado e domingo pertencem à semana que acabou de passar.
- "Hoje" é a data de America/Sao_Paulo; se hoje for fim de semana, a "semana atual" é essa mesma semana civil.

## Experiência
- Em tela larga, cinco colunas (segunda a sexta) com o dia de hoje destacado; abaixo de 900 px os dias empilham.
- O formulário "Nova visita" abre em pop-up, pelo botão geral ou pelo "+ Agendar" de cada dia (que preenche a data). Hora é uma lista com os 21 horários da grade; data tem `min` igual a hoje.
- Em caso de erro (422) a semana certa é exibida, o pop-up abre de novo com os dados mantidos, as mensagens junto de cada campo e um resumo.
- Cancelar pede confirmação em pop-up.
- A mensagem de sucesso usa um cookie de aviso de uso único, para não alterar o `Location` do 303.
- Navegação "Semana anterior", "Hoje" e "Próxima semana" com o intervalo da semana no título.

## Fora de escopo
Fusos múltiplos, recorrência, sincronização com calendário externo, arrastar e soltar.
