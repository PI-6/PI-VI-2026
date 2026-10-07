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
Status usados: 400 validação, 401 sem login, 403 sem permissão, 404 não encontrado, 409 conflito.

## Endpoints (Sprint 1)

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/api/teste` | público | Verifica se a API está no ar |
| POST | `/api/cadastro` | público | Cadastro de cliente |
| POST | `/api/login` | público | Login (cliente ou equipe) |
| GET | `/api/me` | logado | Dados do usuário do token |
| GET | `/api/servicos` | público | Lista serviços ativos |
| GET | `/api/servicos/<id>` | público | Detalhe de um serviço |
| POST | `/api/servicos` | gerente | Cria serviço |
| PUT | `/api/servicos/<id>` | gerente | Edita serviço |
| DELETE | `/api/servicos/<id>` | gerente | Exclui serviço (exclusão lógica) |
| GET | `/api/profissionais` | admin | Lista profissionais com serviços e horários |
| GET | `/api/profissionais/<id>` | admin | Detalhe de um profissional |
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
