# Requisitos funcionais — Time 12

Fonte: protótipo definido para o Base44 e instruções gerais do projeto.
Perfis: **Cliente**, **Admin** (funcionário) e **Gerente** (herda tudo do Admin).

## Área pública (cliente)

### RF01 — Home (sem login)
- Hero com imagem do salão e botão em destaque "Faça seu agendamento", que leva a Login/Cadastro.
- Texto institucional sobre o salão.
- Rodapé com endereço, e-mail e telefone do salão.
- Obs.: ainda sem tarefa no backlog.

### RF02 — Cadastro
- Campos, nesta ordem exata: Nome completo, CPF, Telefone, E-mail, Senha, Confirmar senha.
- Validar CPF, formato de e-mail e senha igual à confirmação.

### RF03 — Login
- E-mail e senha.
- Se o domínio do e-mail for o do salão (ex.: `@salao.com`), redirecionar para a área interna, conforme o nível de acesso. Caso contrário, área do cliente.

### RF04 — Agendamento (cliente logado, em etapas)
1. Escolher o serviço.
2. Escolher o profissional: lista filtrada pelos profissionais que realizam aquele serviço.
3. Escolher data e horário: horários ocupados ou bloqueados aparecem com X vermelho / "indisponível" e não podem ser selecionados.
4. Confirmação: resumo (serviço, profissional, data, horário) com botões "Confirmar" e "Alterar".
- Ao confirmar: mensagem de sucesso e e-mail ao cliente (e ao profissional) com data, horário, endereço do salão e nome do profissional.

## Área interna — Admin

Menu lateral fixo, nesta ordem: Dashboard, Agenda.

### RF05 — Dashboard
- Agendamentos do dia do funcionário logado.
- Receita do dia e receita do mês.
- Alerta de estoque baixo (até 3 produtos em destaque).
- Agenda de hoje (lista resumida).

### RF06 — Agenda
- Calendário para escolher um dia e ver todos os serviços agendados.
- Excluir agendamento (ex.: cancelamento de última hora), com confirmação, liberando o horário.
- Bloquear e desbloquear horários do profissional.

## Área interna — Gerente (tudo do Admin, mais)

Menu: Dashboard, Agenda, Serviços, Profissionais, Estoque, Financeiro.

### RF07 — Serviços
- Listar, adicionar, editar e excluir serviços.

### RF08 — Profissionais
- Listar, adicionar, editar e excluir profissionais.
- Definir: serviços que realiza, horário de trabalho e nível de acesso (Admin ou Gerente).

### RF09 — Estoque
- Listar, adicionar e editar produtos.
- Campos: nome, descrição, quantidade em estoque, quantidade mínima (gatilho do alerta), preço por unidade, unidade de medida (ml, gramas, litros, unidade).

### RF10 — Financeiro (BI)
- Filtro por período: semana, mês ou ano.
- Receita total do período e quantidade de atendimentos.
- Ranking de funcionários por número de serviços realizados.
- Gráfico de pizza com os serviços mais realizados.
- Gráfico de barras com a receita ao longo do período.
- Comparativo mensal.

## Requisitos não funcionais (resumo)
- Responsivo (desktop e mobile); visual clean em tons neutros/rosé e dourado.
- Componentes reutilizáveis; toda exclusão com modal de confirmação.
- Senhas com hash; dados pessoais (CPF, telefone) tratados conforme a LGPD.
- Autorização sempre validada no backend.

## Fora de escopo (trabalhos futuros)
- Notificações por WhatsApp via Twilio.
