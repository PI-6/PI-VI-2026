# Sistema de Gestão para Pequenos Negócios de Prestação de Serviços

Projeto Integrador VI – Engenharia de Software
Pontifícia Universidade Católica de Campinas (PUC-Campinas)
**Orientadora:** Prof.ª Sílvia C. de Matos Soares
**Equipe:** Time 12

---

## 📋 Sobre o projeto

Sistema web de agendamento e gestão voltado para pequenos negócios de prestação de serviços (como barbearias e salões de beleza), permitindo que clientes agendem horários com profissionais específicos e que administradores acompanhem indicadores de desempenho do negócio.

### Por quê (Why)
Pequenos negócios de serviços frequentemente perdem tempo e clientes com agendamentos manuais, falta de visibilidade sobre horários disponíveis e ausência de dados para tomada de decisão.

### Como (How)
Um sistema simples, com agendamento por profissional, notificações automáticas por e-mail e um dashboard com indicadores financeiros e operacionais.

### O quê (What)
Uma plataforma web onde o cliente escolhe o profissional, visualiza a agenda dele e marca um horário; o profissional gerencia sua disponibilidade; e o administrador acompanha receita e atendimentos por meio de um dashboard.

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

## ⚙️ Funcionalidades principais

- Seleção de profissional pelo cliente, seguida da visualização da agenda individual daquele profissional
- Se o horário desejado não estiver disponível, o cliente deve escolher outro profissional (sem fila de espera ou realocação automática)
- Notificações automáticas por e-mail:
  - **Cliente:** data, hora, local e nome do profissional
  - **Administrador/profissional:** data, hora e nome do cliente
- Tela para o profissional bloquear manualmente horários em sua agenda
- Dashboard administrativo com:
  - Receita mensal comparada entre todos os meses
  - Clientes atendidos por profissional/mês
  - Receita semanal total

---

## 🛠️ Tecnologias

- **Linguagens:** Python, html css e JavaScript
- **Metodologia:** Scrum, com sprints de 2 semanas (Sprint 0 a Sprint 5)
- **Gestão de tarefas:** GitHub Projects (Kanban)
- **Formatação da documentação acadêmica:** ABNT
- **Banco de dados:** MySQL

> Este projeto também considera a integração de notificações via WhatsApp (API oficial da Twilio) como possível diferencial, atualmente posicionada como trabalho futuro na documentação acadêmica.

---

## 📁 Estrutura do repositório

```
Time12-SistemaGestao/
├── frontend/
├── backend/
├── database/
│   ├── migrations/
│   └── seeds/
├── docs/
│   ├── especificacao/
│   ├── apresentacoes/
│   └── diagramas/
├── .github/
│   └── ISSUE_TEMPLATE/
├── .gitignore
└── README.md
```

---

## 🗂️ Metodologia de trabalho

O projeto é conduzido em 6 sprints de 2 semanas cada (Sprint 0 a Sprint 5), organizadas em um board Kanban no GitHub Projects, com tickets vinculados a milestones e responsáveis definidos.

Fluxo do board:
`Backlog` → `To Do (Sprint atual)` → `In Progress` → `Em Revisão` → `Concluído`

---

## 📄 Documentação acadêmica

A documentação completa do projeto (especificação, requisitos funcionais e não funcionais, regras de negócio, backlog detalhado) segue as normas ABNT e está disponível em `docs/especificacao/Time 12.docx`.
