# Arquitetura do Sistema — Time 12
## Sistema de Agendamento e Gestão para Salão de Beleza

Este documento descreve a arquitetura planejada e serve de base para a Seção 10 (Arquitetura e Tecnologias) do relatório `Time 12.docx`.

---

## 1. Visão geral (contexto do sistema)

O sistema tem duas superfícies, uma área pública para o cliente e uma área interna para o admin (funcionário) e o gerente. As duas conversam com a mesma API em Python, que acessa um banco MySQL.

```mermaid
flowchart LR
    C["Cliente"] --> FE
    A["Admin (funcionário)"] --> FE
    G["Gerente"] --> FE

    subgraph FE["Frontend: React + HTML/CSS/JavaScript"]
        PUB["Área pública"]
        INT["Área interna"]
    end

    FE -->|"HTTPS / JSON (API REST)"| BE

    subgraph BE["Backend: Python"]
        API["API REST"]
    end

    BE -->|"SQL"| DB[("MySQL")]
    BE -->|"SMTP"| MAIL["Servidor de e-mail"]
    BE -.->|"futuro"| WPP["Twilio (WhatsApp)"]

    style WPP stroke-dasharray: 5 5
```

A linha tracejada indica a integração futura com WhatsApp via Twilio. Ela está prevista apenas em Trabalhos Futuros (Seção 15) e não é um compromisso de sprint.

---

## 2. Frontend (React)

```mermaid
flowchart TD
    APP["App React: rotas e controle de acesso"]

    APP --> PUB
    APP --> INT

    subgraph PUB["Área pública (cliente)"]
        HOME["Home"]
        CAD["Cadastro"]
        LOG["Login"]
        AG["Fluxo de agendamento:<br/>serviço, profissional, data/hora, confirmação"]
    end

    subgraph INT["Área interna (rotas protegidas)"]
        direction TB
        subgraph ADM["Admin"]
            DASH["Dashboard do funcionário"]
            AGE["Agenda (calendário diário)"]
        end
        subgraph GER["Gerente: tudo do admin, mais"]
            SERV["Serviços"]
            PROF["Profissionais"]
            EST["Estoque"]
            FIN["Financeiro"]
        end
    end
```

- **Home:** presente na área pública, mas ainda sem tarefa no backlog.
- **Rotas protegidas:** o React verifica o nível de acesso (cliente, admin ou gerente) antes de exibir cada tela. A validação real fica sempre no backend.
- **Menu lateral:** varia por perfil. O admin vê Dashboard e Agenda. O gerente vê esses dois e também Serviços, Profissionais, Estoque e Financeiro.

---

## 3. Backend (Python) em camadas

O backend segue o padrão em camadas com *Repository pattern*, para que a regra de negócio nunca acesse o banco diretamente.

```mermaid
flowchart TD
    REQ["Requisição HTTP"] --> R["Camada de rotas/controllers: validação de entrada e autorização por perfil"]
    R --> S["Camada de serviços: regras de negócio"]
    S --> REPO["Camada de repositórios: único ponto de acesso ao banco"]
    REPO --> DB[("MySQL")]
    S --> NOT["Módulo de notificações: e-mail"]
```

| Camada | Responsabilidade | Exemplo neste projeto |
|---|---|---|
| Rotas/controllers | Receber a requisição, validar os dados e checar o nível de acesso | Rota de criar agendamento só aceita usuário autenticado |
| Serviços | Aplicar as regras de negócio | Impedir agendamento em horário ocupado ou bloqueado |
| Repositórios | Executar as consultas SQL | Buscar horários livres de um profissional |
| Notificações | Enviar e-mails | Confirmação ao cliente e ao admin/profissional |

### Módulos do backend

| Módulo | Função |
|---|---|
| Autenticação e acesso | Cadastro, login por e-mail e senha, redirecionamento por domínio do salão, três níveis de acesso |
| Serviços e profissionais | CRUD, vínculo profissional↔serviço, horário de trabalho, nível de acesso |
| Agendamentos | Listar horários (livre/ocupado), criar agendamento, excluir para liberar o horário |
| Bloqueios | Bloquear e desbloquear horários do profissional |
| Estoque | CRUD de produtos e alerta de estoque baixo |
| Financeiro e BI | Faturamento por semana/mês/ano, ranking de funcionários, serviços mais realizados, comparativo mensal |
| Notificações | E-mail de confirmação (data, hora, endereço do salão, nome do profissional) |

---

## 4. Fluxo principal: agendamento do cliente

```mermaid
sequenceDiagram
    actor Cli as Cliente
    participant FE as Frontend React
    participant API as API Python
    participant DB as MySQL
    participant Mail as Servidor de e-mail

    Cli->>FE: Escolhe o serviço
    FE->>API: Listar profissionais do serviço
    API->>DB: Consulta profissionais vinculados
    DB-->>API: Profissionais
    API-->>FE: Lista filtrada
    Cli->>FE: Escolhe o profissional
    FE->>API: Consultar horários
    API->>DB: Horários, agendamentos e bloqueios
    DB-->>API: Status de cada horário
    API-->>FE: Livre ou ocupado (X vermelho)
    Cli->>FE: Escolhe data e hora
    FE-->>Cli: Tela de confirmação (confirmar ou alterar)
    Cli->>FE: Confirma
    FE->>API: Criar agendamento
    API->>DB: Valida conflito e grava
    API->>Mail: E-mail ao cliente e ao profissional
    API-->>FE: Agendamento confirmado
```

---

## 5. Controle de acesso

```mermaid
flowchart TD
    L["Login com e-mail e senha"] --> D{"Domínio do e-mail é o do salão?"}
    D -->|"Não"| CLI["Cliente: área pública e seus agendamentos"]
    D -->|"Sim"| N{"Nível de acesso"}
    N -->|"Admin"| ADM["Dashboard e Agenda"]
    N -->|"Gerente"| GER["Dashboard, Agenda, Serviços, Profissionais, Estoque e Financeiro"]
```

---

## 6. Tecnologias

| Camada | Tecnologia | Observação |
|---|---|---|
| Frontend | React, HTML, CSS e JavaScript | Gráficos do Dashboard e do Financeiro via biblioteca de gráficos (a definir) |
| Protótipos | Figma/XD | Print no relatório, mais o link |
| Backend | Python + Flask | Login por token assinado (itsdangerous); camadas rota → serviço → repositório |
| Banco de dados | MySQL 8 | Modelo relacional em `docs/mer.md`; migrations em SQL puro |
| E-mail | SMTP | Notificações de confirmação |
| WhatsApp | Twilio | Apenas Trabalhos Futuros |
| Versionamento | GitHub (organização PI-6) | `main` ← `developer` ← `feature/{n-issue}-{nome}` |
| Gestão | GitHub Projects (Kanban) e Scrum | Seis sprints de duas semanas |
| Hospedagem/cloud | A definir | Ainda sem decisão registrada |

---

## 7. Estrutura de pastas sugerida do repositório

```
/
├── frontend/              # React
│   └── src/
│       ├── pages/         # home, cadastro, login, agendamento, admin, gerente
│       ├── components/    # botões, inputs, cards, gráficos
│       └── routes/        # rotas protegidas por perfil
├── backend/               # Python
│   ├── routes/            # controllers
│   ├── services/          # regras de negócio
│   ├── repositories/      # acesso ao banco
│   └── notifications/     # e-mail
├── database/              # migrations e seeds
├── docs/                  # documentação
├── CONTRIBUTING.md
└── README.md
```

---

## 8. Pontos em aberto

- Biblioteca de gráficos do frontend. (Backend: Flask, definido.)
- Hospedagem/cloud, citada na Sprint 0, ainda sem decisão.
- Tarefas da página Home, que ainda não estão no backlog.
