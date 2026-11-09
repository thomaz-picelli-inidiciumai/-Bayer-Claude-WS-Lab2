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
- `GET /agenda?semana=AAAA-MM-DD`: mostra segunda a sexta da semana que contém essa data; sem o parâmetro, a semana atual.
- `POST /agenda/nova`: campos `medico_id`, `data` (`AAAA-MM-DD`) e `hora` (`HH:MM`). Sucesso: 303 para `/agenda?semana=<data>`. Erro de validação ou conflito: 422, nada é gravado.

## Estados da tela
- **Vazio:** dia sem visitas mostra "Sem visitas".
- **Sucesso:** visita aparece no dia correto sem recarregar a semana errada.
- **Erro:** mensagens por campo.

## Dados e regras
- Gravar em `visitas` com status `planejada`, `notas` vazio.
- Horário único no fuso America/Sao_Paulo; `data_hora` armazenada sem fuso, nesse horário local.
- Duração fixa de 30 minutos.

## Fora de escopo
Fusos múltiplos, recorrência, sincronização com calendário externo, arrastar e soltar.
