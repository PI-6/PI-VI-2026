# Sistema de Agendamento e Gestão para Salão de Beleza

Projeto Integrador VI – Engenharia de Software
Pontifícia Universidade Católica de Campinas (PUC-Campinas)
**Orientadora:** Prof.ª Sílvia C. de Matos Soares
**Equipe:** Time 12

---

## 📋 Sobre o projeto

Sistema web de agendamento e gestão para pequenos negócios de prestação de serviços, com foco em um
salão de beleza. Tem duas frentes:

- **Área pública:** o cliente se cadastra, escolhe o serviço, o profissional, a data e o horário, e recebe
  a confirmação por e-mail.
- **Área interna:** o funcionário (admin) acompanha o próprio dia e a agenda do salão; o gerente também
  cuida de serviços, profissionais, estoque e do Financeiro, com dashboards de BI.

**BI (dashboards financeiros) é o componente de "tecnologia atual" do projeto.**

### Por quê
Pequenos negócios de serviço perdem tempo e clientes com agendamentos manuais, não têm visibilidade dos
horários livres e não têm dados para tomar decisões.

### Como
Agendamento online por profissional com checagem de conflito, bloqueio de horários, e-mails automáticos,
controle de estoque e indicadores financeiros calculados a partir dos atendimentos.

### O quê
Uma aplicação web (API REST em Python + MySQL + frontend em JavaScript) com três perfis de acesso:
**cliente**, **admin** (funcionário) e **gerente** (herda tudo do admin).

---

## 👥 Equipe

| Integrante | Papel |
|---|---|
| Luiz | Scrum Master |
| Airton | Front-end |
| Rafael | Back-end |
| Eduardo | Banco de Dados / Revisão de Documentação |
| Guilherme | Documentação |

---

## ⚙️ Funcionalidades

| Requisito | Funcionalidade | Quem usa |
|---|---|---|
| RF01 | Home pública com apresentação do salão | Todos |
| RF02 | Cadastro (nome completo, CPF, telefone, e-mail, senha, confirmar senha) | Cliente |
| RF03 | Login; e-mail do domínio do salão leva à área interna | Todos |
| RF04 | Agendamento em etapas: serviço → profissional → data/hora → confirmação, com e-mail ao cliente e ao profissional | Cliente |
| RF05 | Dashboard do funcionário: agenda de hoje, receita do dia e do mês, alerta de estoque baixo | Admin e gerente |
| RF06 | Agenda do dia, exclusão de agendamento e bloqueio de horários (pontual ou semanal) | Admin e gerente |
| RF07 | Cadastro de serviços | Gerente |
| RF08 | Cadastro de profissionais (serviços, horário de trabalho e nível de acesso) | Gerente |
| RF09 | Estoque de produtos com alerta de estoque baixo | Gerente |
| RF10 | Financeiro (BI): resumo por período, comparativo mensal, receita semanal, ranking de profissionais e serviços mais realizados | Gerente |

Regras de negócio principais:

- Horário ocupado ou bloqueado não pode ser agendado. O conflito é checado no backend e protegido no banco,
  inclusive quando dois clientes confirmam o mesmo horário ao mesmo tempo.
- Excluir um agendamento libera o horário na hora (o agendamento fica como `cancelado`, sem apagar o histórico).
- Estoque baixo: quantidade ≤ quantidade mínima.
- No BI, **atendimento realizado** é o agendamento não cancelado cujo horário já terminou. A receita usa o
  preço gravado no dia do agendamento.

> Notificações por WhatsApp (API da Twilio) estão previstas apenas como **trabalho futuro**.

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+ com Flask (API REST em JSON), em camadas: rotas → serviços → repositórios |
| Autenticação | Token assinado (itsdangerous) no header `Authorization: Bearer`; senhas com hash |
| Banco de dados | MySQL 8, com migrations em SQL puro |
| E-mail | SMTP (Mailpit para testes locais) |
| Frontend | HTML, CSS e JavaScript, consumindo a API por um cliente HTTP central (`frontend/js/api.js`) |
| Testes e qualidade | pytest e flake8 |
| Ambiente local | Docker Compose (MySQL + Mailpit) |
| Gestão | Scrum (6 sprints de 2 semanas) e GitHub Projects (Kanban) |

---

## 🚀 Como rodar localmente

Pré-requisitos: **Python 3.11+** e **Docker** (ou um MySQL 8 instalado).

```bash
# 1. Banco de dados e caixa de e-mail de testes (na raiz do projeto)
docker compose up -d
cp .env.example .env            # ajuste se o seu MySQL for outro

# 2. Ambiente Python
cd backend
python -m venv venv
source venv/bin/activate        # no Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 3. Tabelas e dados de teste
python ../database/migrate.py
python ../database/seed.py

# 4. API em http://127.0.0.1:5000
python app.py
```

Para abrir o frontend, sirva a pasta `frontend/` (em outro terminal):

```bash
cd frontend
python -m http.server 5500      # acesse http://127.0.0.1:5500
```

Os e-mails enviados pela API aparecem no Mailpit, em http://localhost:8025.

### Usuários de teste (senha `Senha@123`)

| Perfil | E-mail |
|---|---|
| Gerente | `mariana@salaobelle.com.br` |
| Admin | `camila@salaobelle.com.br` |
| Cliente | `ana.souza@gmail.com` |

### Testes e lint

```bash
cd backend
pytest
flake8
```

---

## 📁 Estrutura do repositório

```
/
├── backend/
│   ├── routes/            # entrada da API: validação e autorização por perfil
│   ├── services/          # regras de negócio
│   ├── repositories/      # único ponto de acesso ao MySQL
│   ├── notifications/     # envio de e-mail e templates
│   ├── tests/             # testes dos serviços e das rotas
│   └── README.md          # todos os endpoints, com exemplos
├── database/
│   ├── migrations/        # 001 a 004, em SQL puro
│   ├── migrate.py         # aplica as migrations pendentes
│   └── seed.py            # dados de teste
├── frontend/              # páginas HTML, CSS e JavaScript
├── docs/
│   ├── arquitetura.md     # arquitetura e diagramas
│   ├── mer.md             # modelo de dados (MER) e decisões
│   ├── requisitos.md      # requisitos funcionais e não funcionais
│   └── sprints.md         # backlog por sprint
├── docker-compose.yml     # MySQL + Mailpit para desenvolvimento
├── .env.example           # modelo das variáveis de ambiente
└── README.md
```

---

## 📚 Documentação técnica

| Documento | Conteúdo |
|---|---|
| [`backend/README.md`](backend/README.md) | Como rodar a API, formato dos erros e todos os endpoints com exemplos de requisição e resposta |
| [`docs/requisitos.md`](docs/requisitos.md) | Requisitos funcionais (RF01–RF10) e não funcionais |
| [`docs/arquitetura.md`](docs/arquitetura.md) | Arquitetura em camadas, fluxos e controle de acesso |
| [`docs/mer.md`](docs/mer.md) | Diagrama do banco e justificativa das decisões de modelagem |
| [`docs/sprints.md`](docs/sprints.md) | Planejamento das sprints e responsáveis |

---

## 🗂️ Metodologia de trabalho

O projeto segue Scrum, com 6 sprints de 2 semanas (Sprint 0 a Sprint 5), organizadas no GitHub Projects.
Cada tarefa é uma issue ligada à milestone da sprint e a um responsável.

Fluxo do board: `Todo` → `In Progress` → `In QA` → `Done`

Fluxo de branches:

- Cada issue ganha uma branch `feature/{número-da-issue}-{nome-curto}`, criada a partir de `developer`.
- A entrega volta para a `developer` por Pull Request, com `Closes #N` na descrição.
- A `developer` vai para a `main` no fim de cada sprint, pelo time.

---

## 📄 Documentação acadêmica

O relatório do projeto (especificação, requisitos, modelo de dados, arquitetura, solução de BI, testes e
gestão) segue as normas ABNT e é entregue no arquivo `Time 12.docx`.
