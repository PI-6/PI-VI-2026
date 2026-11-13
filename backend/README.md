# Backend — API do salão

API REST em Python com Flask, organizada em camadas:

```
routes/        recebe a requisição, lê o JSON e checa login/perfil
services/      regras de negócio (validações, permissões específicas)
repositories/  único lugar com SQL (MySQL)
tests/         testes dos serviços e das rotas, com repositórios em memória
```

## Como rodar

Pré-requisitos: Python 3.11+ e Docker (ou um MySQL 8 instalado).

```bash
# 1. Banco (na raiz do projeto)
docker compose up -d
cp .env.example .env            # ajuste se o seu MySQL for outro

# 2. Ambiente Python
cd backend
python -m venv venv
source venv/bin/activate         # no Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 3. Tabelas e dados de teste
python ../database/migrate.py
python ../database/seed.py
python ../database/seed_demo.py   # opcional: histórico para o BI (Financeiro) e agenda cheia

# 4. Subir a API em http://127.0.0.1:5000
python app.py
```

Testes e lint (dentro de `backend/`):

```bash
pytest
flake8
```

Usuários do seed (senha `Senha@123`): `mariana@salaobelle.com.br` (gerente),
`camila@salaobelle.com.br` (admin) e `ana.souza@gmail.com` (cliente).

## Autenticação

O login devolve um `token`. Nas rotas protegidas, envie o header:

```
Authorization: Bearer <token>
```

O token vale `TOKEN_EXPIRATION_HOURS` horas (padrão 8). O perfil é sempre conferido
no backend a cada requisição; o gerente tem acesso a tudo que o admin tem.

## Formato dos erros

```json
{ "erro": "Verifique os campos do cadastro.", "detalhes": { "cpf": "CPF inválido." } }
```

`detalhes` aparece em erros de validação (400), com a mensagem de cada campo, e no 409 de bloqueio,
com os agendamentos que impedem o bloqueio.
Status usados: 400 validação, 401 sem login, 403 sem permissão, 404 não encontrado, 409 conflito
(horário ocupado ou cadastro duplicado, inclusive quando duas requisições chegam ao mesmo tempo).

## Endpoints

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/api/teste` | público | Verifica se a API está no ar |
| POST | `/api/cadastro` | público | Cadastro de cliente |
| POST | `/api/login` | público | Login (cliente ou equipe) |
| GET | `/api/me` | logado | Dados do usuário do token |
| GET | `/api/servicos` | público | Lista serviços ativos |
| GET | `/api/servicos/<id>` | público | Detalhe de um serviço |
| GET | `/api/servicos/<id>/profissionais` | logado | Profissionais que realizam o serviço (só id e nome) |
| POST | `/api/servicos` | gerente | Cria serviço |
| PUT | `/api/servicos/<id>` | gerente | Edita serviço |
| DELETE | `/api/servicos/<id>` | gerente | Exclui serviço (exclusão lógica) |
| GET | `/api/profissionais` | admin | Lista profissionais com serviços e horários |
| GET | `/api/profissionais/<id>` | admin | Detalhe de um profissional |
| GET | `/api/profissionais/<id>/disponibilidade` | logado | Horários livres e ocupados de um dia para um serviço |
| POST | `/api/agendamentos` | cliente | Cria um agendamento para o cliente logado |
| GET | `/api/agendamentos?data=AAAA-MM-DD` | admin | Agenda do dia: agendamentos e bloqueios (filtro `profissional_id`) |
| DELETE | `/api/agendamentos/<id>` | admin | Exclui (cancela) um agendamento e libera o horário |
| GET | `/api/profissionais/<id>/bloqueios` | admin | Bloqueios que ainda valem de um profissional |
| POST | `/api/profissionais/<id>/bloqueios` | admin* | Cria bloqueio pontual ou semanal |
| DELETE | `/api/bloqueios/<tipo>/<id>` | admin* | Remove um bloqueio (`tipo`: `pontual` ou `semanal`) |
| GET | `/api/financeiro/receita-mensal?ano=AAAA` | gerente | Receita mês a mês do ano, com variação |
| GET | `/api/financeiro/atendimentos-por-profissional` | gerente | Ranking de profissionais no período |
| GET | `/api/financeiro/receita-semanal?data=AAAA-MM-DD` | gerente | Receita da semana, dia a dia |
| GET | `/api/financeiro/servicos` | gerente | Serviços mais realizados no período (pizza) |
| GET | `/api/financeiro/resumo` | gerente | Receita, atendimentos e série do período (barras) |
| GET | `/api/produtos` | gerente | Lista produtos do estoque (`?estoque_baixo=1` filtra) |
| GET | `/api/produtos/<id>` | gerente | Detalhe de um produto |
| POST | `/api/produtos` | gerente | Cadastra produto |
| PUT | `/api/produtos/<id>` | gerente | Edita produto |
| GET | `/api/dashboard` | admin | Dashboard do funcionário logado (agenda, receita e estoque baixo) |
| POST | `/api/profissionais` | gerente | Cria profissional (e o login dele) |
| PUT | `/api/profissionais/<id>` | gerente | Edita profissional |
| DELETE | `/api/profissionais/<id>` | gerente | Desativa profissional |

\* O admin só cria e remove bloqueios da **própria** agenda; o gerente, de qualquer profissional.

### Cadastro — `POST /api/cadastro`

```json
{
  "nome": "Ana Paula Souza",
  "cpf": "529.982.247-25",
  "telefone": "(19) 99123-4567",
  "email": "ana.souza@gmail.com",
  "senha": "segredo1",
  "confirmar_senha": "segredo1"
}
```

CPF e telefone podem vir com ou sem máscara. E-mails do domínio do salão são recusados
aqui, porque contas da equipe são criadas pelo gerente.

### Login — `POST /api/login`

Envio: `{ "email": "...", "senha": "..." }`. Resposta:

```json
{
  "token": "eyJpZCI6MX0...",
  "area": "interna",
  "usuario": { "id": 1, "nome": "Mariana Duarte", "email": "mariana@salaobelle.com.br", "perfil": "gerente" }
}
```

`area` é `"interna"` para e-mails do domínio do salão (`SALON_EMAIL_DOMAIN`) e `"cliente"`
para os demais. O front usa esse campo e o `perfil` para decidir para onde redirecionar.

### Serviço — `POST` e `PUT /api/servicos`

```json
{ "nome": "Hidratação", "descricao": "Hidratação capilar", "duracao_minutos": 40, "preco": 69.90 }
```

### Profissionais de um serviço — `GET /api/servicos/<id>/profissionais`

Usada na etapa 2 do agendamento: depois de escolher o serviço, o cliente vê quem o realiza.
Qualquer usuário logado pode chamar (cliente, admin ou gerente). Resposta:

```json
[
  { "id": 2, "nome": "Camila Ferreira" },
  { "id": 1, "nome": "Mariana Duarte" }
]
```

- Traz só profissionais ativos, em ordem alfabética.
- Devolve apenas `id` e `nome`. E-mail e telefone da equipe ficam em `GET /api/profissionais`, restrita à equipe.
- Serviço inexistente ou excluído: `404`.

### Disponibilidade — `GET /api/profissionais/<id>/disponibilidade?data=AAAA-MM-DD&servico_id=N`

Usada na etapa 3 do agendamento. Qualquer usuário logado pode chamar. Resposta:

```json
{
  "profissional_id": 2,
  "servico_id": 1,
  "data": "2026-10-20",
  "duracao_minutos": 60,
  "horarios": [
    { "hora": "09:00", "status": "livre" },
    { "hora": "09:30", "status": "ocupado" }
  ]
}
```

Regras (`services/appointment_service.py`):

- Horários de início a cada 30 minutos (`SLOT_MINUTES`), a partir do início do expediente do dia.
- Um horário só aparece se o serviço inteiro terminar até o fim do expediente.
- `ocupado` = o intervalo do serviço sobrepõe outro agendamento ou um bloqueio. Cancelados não ocupam.
  Para o cliente, horário de outro cliente e horário bloqueado aparecem igual (`ocupado`).
- Dia de folga ou data passada: `horarios` vem vazio. Hoje: só horários que ainda não começaram.
- `data` ou `servico_id` inválidos: `400`, com `detalhes`. Profissional ou serviço inexistente: `404`.
  Profissional que não faz o serviço: `400`.

### Agendamento — `POST /api/agendamentos`

Etapa 4 do agendamento (confirmação). Só o **cliente** usa esta rota; admin e gerente recebem `403`.
O cliente é sempre o usuário do token, nunca um campo do corpo.

```json
{ "profissional_id": 2, "servico_id": 1, "data": "2026-10-20", "hora": "10:00" }
```

Resposta `201`:

```json
{
  "id": 8,
  "profissional": { "id": 2, "nome": "Camila Ferreira" },
  "servico": { "id": 1, "nome": "Corte feminino" },
  "data": "2026-10-20",
  "hora_inicio": "10:00",
  "hora_fim": "11:00",
  "valor": 90.0,
  "status": "agendado"
}
```

- Valem as mesmas regras da disponibilidade: horário da grade de 30 min, no futuro, dentro do expediente,
  o serviço precisa terminar até o fim do expediente e o profissional precisa realizar o serviço (`400`).
- Horário sobreposto a outro agendamento ou a um bloqueio: `409`. A gravação trava a agenda do profissional
  (`SELECT ... FOR UPDATE`) e confere o conflito de novo, então dois clientes no mesmo instante (ou um cliente
  e alguém da equipe bloqueando o horário) não conseguem o mesmo horário.
- `valor` é o preço do serviço no momento: mudar o preço depois não altera agendamentos já feitos.
- Depois de gravar, a API envia **e-mails ao cliente e ao profissional**, em segundo plano (veja abaixo).
  Se o envio falhar, o agendamento continua valendo e a resposta continua `201`; a falha fica no log.

### Agenda do dia — `GET /api/agendamentos?data=AAAA-MM-DD&profissional_id=N`

Tela de Agenda (RF06). Admin e gerente veem o salão inteiro; `profissional_id` é opcional e filtra uma
pessoa. Resposta:

```json
{
  "data": "2026-10-20",
  "agendamentos": [
    {
      "id": 8, "hora_inicio": "10:00", "hora_fim": "11:00", "status": "agendado", "valor": 90.0,
      "cliente": { "id": 3, "nome": "Ana Paula Souza" },
      "profissional": { "id": 2, "nome": "Camila Ferreira" },
      "servico": { "id": 1, "nome": "Corte feminino" }
    }
  ],
  "bloqueios": [
    {
      "id": 1, "tipo": "semanal", "motivo": "Almoço",
      "profissional": { "id": 2, "nome": "Camila Ferreira" },
      "hora_inicio": "12:00", "hora_fim": "13:00"
    }
  ]
}
```

- Agendamentos cancelados não aparecem (excluir libera o horário). Concluídos aparecem.
- Do cliente vem só o nome (LGPD: a agenda não precisa de CPF, e-mail ou telefone).
- Bloqueio de vários dias aparece recortado no dia consultado: no meio do período, `00:00` a `24:00`.
- `data` ou `profissional_id` inválidos: `400`. Profissional inexistente: `404`.

### Excluir agendamento — `DELETE /api/agendamentos/<id>`

Cancelamento de última hora pela equipe (RF06). Resposta `204`.

- A linha não é apagada: o `status` vira `cancelado` e ficam gravados `cancelado_por` e `cancelado_em`.
  O horário volta a aparecer como `livre` na hora.
- Só agendamento com status `agendado` pode ser excluído. Já cancelado ou concluído: `409`.
- O cliente **não** usa esta rota (`403`) e não recebe e-mail de cancelamento (não está nos requisitos).

### Bloqueios — `POST /api/profissionais/<id>/bloqueios`

Tira um intervalo da agenda do profissional: ninguém agenda ali e o horário aparece como `ocupado`.

Pontual (consulta médica, curso, folga). `data_fim` é opcional; sem ela, termina no mesmo dia:

```json
{ "tipo": "pontual", "data": "2026-10-27", "hora_inicio": "14:00", "hora_fim": "16:00", "motivo": "Consulta médica" }
```

Semanal (repete toda semana; `dia_semana`: 0 = segunda ... 6 = domingo). `valido_de` e `valido_ate` são
opcionais: sem `valido_de`, a regra começa hoje; sem `valido_ate`, não tem data para acabar.

```json
{ "tipo": "semanal", "dia_semana": 1, "hora_inicio": "12:00", "hora_fim": "13:00", "motivo": "Almoço",
  "valido_de": "2026-11-03", "valido_ate": "2026-11-30" }
```

Resposta `201`: o bloqueio no mesmo formato, com `id` e `profissional_id`. O pontual sempre traz `data_fim`;
o semanal sempre traz `valido_de` e `valido_ate` (`null` quando não tem fim).

No banco, cada tipo fica numa tabela (`bloqueios` e `bloqueios_recorrentes`, migration 003 do Eduardo),
então **os ids se repetem entre os tipos**: um bloqueio é identificado por `tipo` + `id`.

- Quem pode: o admin só na própria agenda; o gerente em qualquer uma (`403` caso contrário).
- `motivo` é opcional (até 150 caracteres). Fim antes do início, `valido_ate` antes de `valido_de` ou período
  que já passou: `400`.
- Se houver agendamento ativo no intervalo (no semanal, em qualquer semana dentro da validade), a resposta
  é `409` e lista esses agendamentos em `detalhes.agendamentos` (`id`, `data`, `hora_inicio`, `hora_fim`).
  A equipe cancela ou remarca o cliente e depois bloqueia. Assim ninguém fica com horário confirmado num
  período bloqueado.
- `GET /api/profissionais/<id>/bloqueios` lista os pontuais que ainda não terminaram e os semanais que não
  expiraram.
- `DELETE /api/bloqueios/<tipo>/<id>` remove (apaga a linha; bloqueio não entra no BI). Responde `204`.
- Na disponibilidade e na agenda do dia, um semanal só conta nos dias entre `valido_de` e `valido_ate`.
## Financeiro / BI (RF10)

Rotas em `/api/financeiro`, só para o **gerente** (admin e cliente recebem `403`).

**O que conta como atendimento realizado** (decisão do time, 03/11): agendamento **não cancelado cujo
horário já terminou** (`fim` até agora). Agendamentos futuros e em andamento não entram; cancelados nunca
entram. A receita usa o `valor` gravado no agendamento (preço do dia), não o preço atual do serviço.

### Receita mensal comparada — `GET /api/financeiro/receita-mensal?ano=AAAA`

Issue #30. Sem `ano`, usa o ano atual. Resposta:

```json
{
  "ano": 2026,
  "meses": [
    { "mes": 9,  "nome": "set", "receita": 4320.0, "atendimentos": 51, "situacao": "fechado",      "variacao_percentual": 12.5 },
    { "mes": 10, "nome": "out", "receita": 3100.0, "atendimentos": 38, "situacao": "em_andamento", "variacao_percentual": -28.2 },
    { "mes": 11, "nome": "nov", "receita": 0.0,    "atendimentos": 0,  "situacao": "futuro",       "variacao_percentual": null }
  ],
  "total": { "receita": 7420.0, "atendimentos": 89 }
}
```

- Sempre vêm os 12 meses, com zero nos meses sem movimento (o gráfico não fica com buracos).
- `variacao_percentual`: em relação ao mês anterior (janeiro compara com dezembro do ano anterior).
  É `null` quando o mês anterior teve receita zero ou quando o mês ainda não começou.
- `situacao`: `fechado`, `em_andamento` (número parcial, o mês atual) ou `futuro`.
- `ano` fora de 2000–2100 ou não numérico: `400`.

### Filtro por período (`periodo` e `data`)

As rotas por período recebem `?periodo=semana|mes|ano&data=AAAA-MM-DD`. O período é o que **contém** a data
(sem `data`, hoje). A semana vai de **segunda a domingo**. Toda resposta por período começa com:

```json
{ "periodo": "semana", "inicio": "2026-10-19", "fim": "2026-10-25" }
```

`fim` é o último dia do período, inclusive. `periodo` diferente de semana/mes/ano ou `data` inválida: `400`.

### Ranking de profissionais — `GET /api/financeiro/atendimentos-por-profissional?periodo=mes&data=AAAA-MM-DD`

Issue #31. Sem `periodo`, usa o mês. Resposta:

```json
{
  "periodo": "mes", "inicio": "2026-10-01", "fim": "2026-10-31",
  "profissionais": [
    { "posicao": 1, "id": 3, "nome": "Juliana Rocha",   "atendimentos": 42, "clientes": 30, "receita": 1580.0 },
    { "posicao": 2, "id": 2, "nome": "Camila Ferreira", "atendimentos": 37, "clientes": 33, "receita": 2890.0 }
  ]
}
```

- Ordem: mais atendimentos primeiro; empate decidido pela receita e depois pelo nome.
- `clientes` = clientes diferentes atendidos (quem voltou duas vezes conta uma).
- Só aparece quem teve atendimento no período. Profissional desativado continua aparecendo se atendeu.

### Receita semanal — `GET /api/financeiro/receita-semanal?data=AAAA-MM-DD`

Issue #32. Semana de segunda a domingo que contém a data (sem `data`, a semana atual). Resposta:

```json
{
  "periodo": "semana", "inicio": "2026-10-19", "fim": "2026-10-25",
  "receita": 1250.5, "atendimentos": 17,
  "dias": [
    { "data": "2026-10-19", "dia_semana": "seg", "receita": 0.0,   "atendimentos": 0 },
    { "data": "2026-10-20", "dia_semana": "ter", "receita": 410.0, "atendimentos": 6 }
  ],
  "semana_anterior": { "receita": 1000.0, "variacao_percentual": 25.1 }
}
```

- `dias` sempre traz os 7 dias, com zero nos dias sem atendimento.
- Na semana atual, os números são parciais: só entra o que já terminou.
- `semana_anterior.variacao_percentual` é `null` quando a semana anterior teve receita zero.

### Serviços mais realizados — `GET /api/financeiro/servicos?periodo=mes&data=AAAA-MM-DD`

Issue #61 (gráfico de pizza do RF10). Sem `periodo`, usa o mês. Resposta:

```json
{
  "periodo": "mes", "inicio": "2026-10-01", "fim": "2026-10-31",
  "total_atendimentos": 79,
  "servicos": [
    { "id": 5, "nome": "Manicure",       "atendimentos": 31, "receita": 1085.0, "percentual": 39.2 },
    { "id": 1, "nome": "Corte feminino", "atendimentos": 22, "receita": 1980.0, "percentual": 27.8 }
  ]
}
```

- Ordem: mais atendimentos primeiro (empate: receita, depois nome).
- `percentual` = fatia do serviço no total de atendimentos, com 1 casa (a soma pode dar 99,9 ou 100,1
  por arredondamento).
- Serviço excluído continua aparecendo se foi realizado no período.

### Resumo do período — `GET /api/financeiro/resumo?periodo=mes&data=AAAA-MM-DD`

Issue #62: cards do topo do Financeiro e gráfico de barras da receita ao longo do período.
Sem `periodo`, usa o mês. Resposta:

```json
{
  "periodo": "mes", "inicio": "2026-10-01", "fim": "2026-10-31",
  "receita": 3100.0, "atendimentos": 38, "ticket_medio": 81.58,
  "periodo_anterior": {
    "periodo": "mes", "inicio": "2026-09-01", "fim": "2026-09-30",
    "receita": 4320.0, "atendimentos": 51, "variacao_percentual": -28.2
  },
  "serie": [
    { "rotulo": "01/10", "inicio": "2026-10-01", "receita": 150.0, "atendimentos": 2 },
    { "rotulo": "02/10", "inicio": "2026-10-02", "receita": 0.0,   "atendimentos": 0 }
  ]
}
```

- `serie`: um ponto por dia na semana (`rotulo` = `seg` ... `dom`) e no mês (`rotulo` = `dd/mm`);
  um ponto por mês no ano (`rotulo` = `jan` ... `dez`). Sempre todos os pontos, com zero onde não houve
  movimento. A soma da série é a `receita` do período.
- `ticket_medio` = receita ÷ atendimentos; `null` sem atendimentos.
- `periodo_anterior` é a semana, o mês ou o ano anterior **inteiro**. No período atual os números são
  parciais (só o que já terminou), então a variação de um mês em andamento tende a ser negativa.
- `variacao_percentual` é `null` quando o período anterior teve receita zero.

## Dashboard (RF05) — `GET /api/dashboard`

Tela inicial da área interna, para admin e gerente. Mostra os **dados do funcionário logado** (como no
protótipo): a agenda e a receita são só dos atendimentos dele. O total do salão fica no Financeiro do
gerente. O alerta de estoque baixo é do salão inteiro. Resposta:

```json
{
  "data": "2026-11-03",
  "profissional": { "id": 2, "nome": "Camila Ferreira" },
  "agendamentos_hoje": { "total": 3, "realizados": 1, "a_seguir": 2 },
  "receita": { "dia": 90.0, "dia_prevista": 270.0, "mes": 1840.0, "mes_atendimentos": 21 },
  "agenda_hoje": [
    {
      "id": 31, "hora_inicio": "09:00", "hora_fim": "10:00", "situacao": "realizado",
      "cliente": { "id": 7, "nome": "Ana Paula Souza" },
      "servico": { "id": 1, "nome": "Corte feminino" }
    }
  ],
  "estoque_baixo": {
    "total": 2,
    "produtos": [
      { "id": 6, "nome": "Lixa de unha", "quantidade": 3, "quantidade_minima": 20, "unidade": "un" }
    ]
  }
}
```

- **Receita** segue a regra do Financeiro: só entra o que já terminou e não foi cancelado. `dia_prevista`
  soma também os atendimentos que ainda vão acontecer hoje (o card não fica zerado de manhã). `mes` vai do
  dia 1 até agora.
- `agenda_hoje`: em ordem de horário, sem cancelados; só o nome do cliente (LGPD). `situacao` é
  `realizado`, `em_andamento` ou `a_seguir`. `a_seguir` em `agendamentos_hoje` conta também os em andamento.
- `estoque_baixo`: até 3 produtos, os mais críticos primeiro (menor quantidade em relação ao mínimo;
  zerados no topo). `total` diz quantos produtos estão em estoque baixo no total.
- Usuário da equipe sem cadastro de profissional (ex.: gerente que não atende): `profissional` vem `null`,
  agenda vazia e receitas zeradas; o alerta de estoque aparece normalmente.

## Estoque (RF09)

Rotas em `/api/produtos`, só para o **gerente**. O admin vê apenas o alerta de estoque baixo no Dashboard.
Não há exclusão de produto: o RF09 pede listar, adicionar e editar (`DELETE` responde `405`).

### Produto — `POST` e `PUT /api/produtos`

```json
{
  "nome": "Água oxigenada 30 vol", "descricao": "Revelador para coloração",
  "quantidade": 0.5, "quantidade_minima": 1, "preco_unitario": 28.0, "unidade": "l"
}
```

Resposta (`201` no `POST`, `200` no `PUT` e nos `GET`), também usada em cada item da listagem:

```json
{
  "id": 5, "nome": "Água oxigenada 30 vol", "descricao": "Revelador para coloração",
  "quantidade": 0.5, "quantidade_minima": 1.0, "preco_unitario": 28.0, "unidade": "l",
  "estoque_baixo": true
}
```

- `unidade`: `ml`, `g` (gramas), `l` (litros) ou `un` (unidade).
- `quantidade` e `quantidade_minima`: números ≥ 0 com até 3 casas decimais. Em `un`, só inteiros (e a
  resposta vem sem casas: `12`, não `12.0`). Aceita número ou texto com ponto ou vírgula (`"0,5"`).
- `preco_unitario`: ≥ 0, até 2 casas decimais.
- **Estoque baixo**: `quantidade` ≤ `quantidade_minima` (`estoque_baixo: true`).
- Nome repetido: `409`. `PUT` substitui o cadastro inteiro, então envie todos os campos.
- `GET /api/produtos` lista em ordem alfabética; `?estoque_baixo=1` traz só os de estoque baixo.

## E-mails do agendamento

Código em `notifications/` (o serviço de agendamento só chama o `AppointmentNotifier`, nunca o SMTP direto):

```
notifications/email_sender.py          envio por SMTP (biblioteca padrão do Python, sem dependência nova)
notifications/templates.py             prepara os dados e renderiza os templates com Jinja2
notifications/email_templates/         texto e visual dos e-mails, um par .html/.txt por destinatário
notifications/appointment_notifier.py  dispara os e-mails em segundo plano e registra falhas
```

| Destinatário | Templates | Conteúdo |
|---|---|---|
| Cliente (#24) | `cliente.html` / `cliente.txt` | serviço, profissional, data por extenso, horário de início e fim, endereço com link "Como chegar" e valor |
| Profissional (#25) | `profissional.html` / `profissional.txt` | nome do cliente, serviço, data e horário |

- **Templates em arquivos separados:** para mudar o texto ou o visual de um e-mail, edite o arquivo em
  `email_templates/`, sem mexer no Python. O Jinja2 já vem com o Flask. Os campos ficam entre chaves
  duplas (`{{ primeiro_nome }}`), e o HTML é escapado automaticamente.
- **Segundo plano:** a API responde ao cliente assim que grava o agendamento; os e-mails saem numa
  thread separada (`ThreadPoolExecutor`, da biblioteca padrão), então um SMTP lento não atrasa a tela de
  confirmação. Nos testes o envio é imediato (`run=run_now`) para conferir os e-mails na hora.
- **Destinatários independentes:** se o e-mail do profissional falhar, o do cliente sai mesmo assim.
- **LGPD:** o profissional recebe só o nome do cliente (sem CPF, telefone ou e-mail), e o log registra
  apenas o id do agendamento e o tipo do erro.

Os dados do salão vêm do `.env` (`SALON_NAME`, `SALON_ADDRESS`, `SALON_PHONE`).

Para testar localmente, o `docker compose up -d` também sobe o **Mailpit**: com as configurações SMTP
do `.env.example`, todo e-mail enviado pela API aparece em http://localhost:8025, sem sair para a internet.
Com `SMTP_HOST` vazio a API não envia nada e só registra no log.

### Profissional — `POST` e `PUT /api/profissionais`

```json
{
  "nome": "Camila Ferreira",
  "email": "camila@salaobelle.com.br",
  "telefone": "19988887777",
  "senha": "camila123",
  "perfil": "admin",
  "servicos": [1, 2],
  "horarios": [
    { "dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00" },
    { "dia_semana": 5, "hora_inicio": "08:00", "hora_fim": "12:00" }
  ]
}
```

- `perfil`: `admin` ou `gerente`. `email` precisa ser do domínio do salão.
- `dia_semana`: 0 = segunda ... 6 = domingo (um intervalo por dia).
- `senha` é obrigatória ao criar; no `PUT`, se vier vazia, a senha atual é mantida.
- `PUT` substitui o cadastro inteiro (inclusive serviços e horários), então envie todos os campos.
- O gerente não pode excluir nem tirar o próprio acesso de gerente.
