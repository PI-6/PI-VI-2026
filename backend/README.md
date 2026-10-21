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

`detalhes` só aparece em erros de validação (400), com a mensagem de cada campo.
Status usados: 400 validação, 401 sem login, 403 sem permissão, 404 não encontrado, 409 conflito
(horário ocupado ou cadastro duplicado, inclusive quando duas requisições chegam ao mesmo tempo).

## Endpoints (Sprint 1)

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
| POST | `/api/profissionais` | gerente | Cria profissional (e o login dele) |
| PUT | `/api/profissionais/<id>` | gerente | Edita profissional |
| DELETE | `/api/profissionais/<id>` | gerente | Desativa profissional |

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
- `ocupado` = o intervalo do serviço sobrepõe outro agendamento. Cancelados não ocupam. Bloqueios entram na Sprint 3.
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
- Horário sobreposto a outro agendamento: `409`. A gravação trava a agenda do profissional
  (`SELECT ... FOR UPDATE`) e confere o conflito de novo, então dois clientes no mesmo instante não
  conseguem o mesmo horário.
- `valor` é o preço do serviço no momento: mudar o preço depois não altera agendamentos já feitos.
- Depois de gravar, a API envia **e-mails ao cliente e ao profissional**, em segundo plano (veja abaixo).
  Se o envio falhar, o agendamento continua valendo e a resposta continua `201`; a falha fica no log.

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
