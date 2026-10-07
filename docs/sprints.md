# Backlog de Sprints — Time 12
## Sistema de Gestão para Pequenos Negócios de Prestação de Serviços

**Papéis da equipe:**
- **Airton (FE)** — Front-end
- **Rafael (BE)** — Back-end
- **Eduardo (DB)** — Banco de Dados + Revisão de Documentação
- **Guilherme (DOC)** — Documentação
- **Luiz (SM)** — Scrum Master (acompanhamento de entregas, prazos e reuniões)

> Sugestão de uso: criar um board Kanban no GitHub Projects com colunas **Backlog / A Fazer / Em Progresso / Em Revisão / Concluído**, e criar uma *Issue* para cada linha das tabelas abaixo, com label do responsável e da sprint.

---

## Sprint 0 — Planejamento, Modelagem e Protótipos (2 semanas)

**Objetivo:** fechar requisitos, desenhar o banco de dados e produzir os protótipos de tela.

| Tarefa | Responsável |
|---|---|
| Levantar e validar com orientadora o tema de tecnologia atual (BI) | Guilherme (DOC) |
| Finalizar Requisitos Funcionais (incluir RF15 — bloqueio de horário pelo profissional) | Guilherme (DOC) |
| Redigir Requisitos Não Funcionais (desempenho, segurança, usabilidade, disponibilidade) | Guilherme (DOC) |
| Modelar o MER do banco de dados (clientes, profissionais, agendamentos, bloqueios, serviços) | Eduardo (DB) |
| Revisar consistência entre requisitos funcionais e modelo de dados | Eduardo (DB) |
| Criar protótipos de telas (Figma/XD): tela pública de agendamento | Airton (FE) |
| Criar protótipos de telas: painel admin, agenda do profissional, dashboards | Airton (FE) |
| Definir arquitetura geral e stack (frontend, backend, banco, cloud) | Rafael (BE) |
| Criar repositório GitHub, estrutura de pastas e board Kanban | Luiz (SM) |
| Definir critérios de pronto (Definition of Done) para as sprints seguintes | Luiz (SM) |
| Agendar validação dos protótipos com representante da comunidade externa | Luiz (SM) |

---

## Sprint 1 — Setup Técnico e Backend Base (2 semanas)

**Objetivo:** infraestrutura pronta, autenticação e cadastros básicos funcionando.

| Tarefa | Responsável |
|---|---|
| Configurar projeto frontend (framework, rotas, layout base) | Airton (FE) |
| Criar componentes de UI reutilizáveis (botões, inputs, cards) | Airton (FE) |
| Configurar projeto backend (framework, estrutura de camadas) | Rafael (BE) |
| Implementar autenticação (login admin/profissional) | Rafael (BE) |
| Implementar CRUD de profissionais e serviços | Rafael (BE) |
| Criar banco de dados físico a partir do MER (migrations) | Eduardo (DB) |
| Popular banco com dados de teste (seed) | Eduardo (DB) |
| Revisar Seção 1–2 do documento (Introdução, Objetivos) conforme decisões técnicas | Guilherme (DOC) |
| Fazer daily/checkpoint semanal e atualizar status no Kanban | Luiz (SM) |
| Cobrar entrega dos protótipos validados junto à comunidade externa | Luiz (SM) |

---

## Sprint 2 — Agendamento (Fluxo do Cliente) (2 semanas)

**Objetivo:** cliente consegue escolher profissional, ver disponibilidade e agendar.

| Tarefa | Responsável |
|---|---|
| Tela pública: seleção de profissional | Airton (FE) |
| Tela pública: calendário de disponibilidade do profissional escolhido | Airton (FE) |
| Tela pública: formulário de confirmação de agendamento | Airton (FE) |
| Endpoint: listar profissionais disponíveis | Rafael (BE) |
| Endpoint: consultar horários livres de um profissional | Rafael (BE) |
| Endpoint: criar agendamento (validando conflito de horário) | Rafael (BE) |
| Otimizar queries de disponibilidade (índices por profissional/data) | Eduardo (DB) |
| Testar integridade dos dados de agendamento (sem overlap de horários) | Eduardo (DB) |
| Atualizar Seção 5.1 (Requisitos Funcionais) com o que já foi implementado | Guilherme (DOC) |
| Revisar se a Seção 5.3 pendente já pode ser fechada com a definição de BI | Guilherme (DOC) |
| Verificar aderência das entregas ao escopo definido na Sprint 0 | Luiz (SM) |

---

## Sprint 3 — Painel Admin + Bloqueio de Horários + Notificações (2 semanas)

**Objetivo:** admin/profissional gerencia a própria agenda e o sistema envia e-mails automáticos.

| Tarefa | Responsável |
|---|---|
| Tela admin: painel de horários do dia do profissional | Airton (FE) |
| Tela admin: ação de bloquear horário (almoço, consulta médica, etc.) | Airton (FE) |
| Tela admin: listagem/gestão dos agendamentos recebidos | Airton (FE) |
| Endpoint: bloquear/desbloquear horário do profissional | Rafael (BE) |
| Endpoint: impedir agendamento em horário bloqueado | Rafael (BE) |
| Implementar envio de e-mail ao ADMIN/profissional na confirmação (data, hora, nome do cliente) | Rafael (BE) |
| Implementar envio de e-mail ao CLIENTE na confirmação (data, hora, endereço, nome do profissional) | Rafael (BE) |
| Criar tabela de "bloqueios de horário" no banco | Eduardo (DB) |
| Validar regra: horário bloqueado não pode ser sobrescrito por agendamento | Eduardo (DB) |
| Documentar RF de bloqueio de horário e RF de notificação por e-mail (cliente e admin) | Guilherme (DOC) |
| Revisar documento completo até a Seção 5 (Requisitos) | Guilherme (DOC) |
| Testar manualmente o fluxo ponta a ponta (agendar → bloquear → e-mails) e reportar bugs no Kanban | Luiz (SM) |

---

## Sprint 4 — Dashboards / BI (2 semanas)

**Objetivo:** painel de indicadores para o admin.

| Tarefa | Responsável |
|---|---|
| Endpoint: fluxo de dinheiro recebido por mês, comparando com os demais meses do ano | Rafael (BE) |
| Endpoint: quantidade de clientes atendidos por funcionário/mês | Rafael (BE) |
| Endpoint: dinheiro recebido por semana | Rafael (BE) |
| Componente de gráfico: fluxo mensal comparativo | Airton (FE) |
| Componente de gráfico: atendimentos por funcionário | Airton (FE) |
| Componente de gráfico: faturamento semanal | Airton (FE) |
| Tela de dashboards (layout consolidado dos 3 gráficos) | Airton (FE) |
| Validar performance das queries de agregação com volume maior de dados de teste | Eduardo (DB) |
| Conferir se os cálculos batem com os dados semeados no banco | Eduardo (DB) |
| Redigir Seção 4 (Fundamentação Teórica sobre BI) e Seção 11 (Descrição da solução de BI) | Guilherme (DOC) |
| Cobrar entrega dos 3 gráficos até a metade da sprint (checkpoint de risco) | Luiz (SM) |

---

## Sprint 5 — Testes, Validação e Fechamento da Documentação (2 semanas)

**Objetivo:** sistema estabilizado, documento ABNT completo, aceite da comunidade externa.

| Tarefa | Responsável |
|---|---|
| Ajustes finais de UI/responsividade em todas as telas | Airton (FE) |
| Correção de bugs apontados nos testes | Rafael (BE) |
| Revisão final da estrutura do banco e scripts de migração | Eduardo (DB) |
| Executar bateria de testes funcionais (Seção 12 — Testes e Validação) | Eduardo (DB) |
| Escrever Seção 9 (Modelo de Dados/MER), Seção 10 (Arquitetura e Tecnologias) | Guilherme (DOC) |
| Escrever Seção 13 (Gestão do Projeto — Backlog, Sprints planejadas x reais) | Guilherme (DOC) |
| Escrever Seções 14–16 (Resultados, Ética/Privacidade, Conclusão, Termo de Aceite) | Guilherme (DOC) |
| Revisão ortográfica e formatação ABNT do documento `Time 12.docx` completo | Eduardo (DB) |
| Coletar aceite formal da comunidade externa | Luiz (SM) |
| Organizar gravação do vídeo do sistema em funcionamento | Luiz (SM) |
| Organizar montagem dos slides finais e do banner | Luiz (SM) |

---

## Observações para o Kanban do GitHub

- Sugestão de labels: `sprint-0` a `sprint-5`, `Airton`, `Rafael`, `Eduardo`, `Guilherme`, `Luiz`.
- Cada linha das tabelas pode virar uma *Issue* individual, atribuída à pessoa responsável (via *Assignee* do GitHub) e associada à Milestone da sprint correspondente — isso permite que a professora acompanhe o progresso de cada integrante ao longo do tempo.
- Luiz, como Scrum Master, pode manter uma Issue fixa por sprint como "checklist mestre" linkando todas as outras.
