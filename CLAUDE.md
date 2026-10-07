# Time 12 — Sistema de Agendamento e Gestão para Salão de Beleza

Projeto Integrador VI (Engenharia de Software, PUC-Campinas). Sistema web com duas frentes:
área pública para o cliente agendar e área interna para admin (funcionário) e gerente.
BI (dashboards financeiros) é o componente de "tecnologia atual" do projeto.

Contexto detalhado (leia quando a tarefa tocar o assunto):
- Arquitetura e diagramas: @docs/arquitetura.md
- Requisitos funcionais e telas: @docs/requisitos.md

## Idioma
- Responda sempre em português do Brasil.
- Código (variáveis, funções, classes) em inglês; textos de interface, mensagens de commit e comentários em português.

## Equipe e responsáveis
- Airton: frontend · Rafael: backend · Eduardo: banco de dados (MER) e revisão de docs
- Guilherme: documentação · Luiz: Scrum Master
- Decisões de cada área são do responsável. Se a tarefa exigir uma decisão dessas, pergunte antes.

## Stack (decidida — não trocar sem avisar)
- Frontend: React com JavaScript (não TypeScript), HTML e CSS. Componentes funcionais com hooks.
- Backend: Python, API REST com JSON. **Framework ainda não definido (decisão do Rafael):
  não escolha nem instale um framework sem perguntar.**
- Banco: MySQL, modelo relacional conforme o MER do Eduardo em `database/`.
- E-mail: SMTP para confirmações de agendamento.
- Biblioteca de gráficos e hospedagem: ainda não definidas. Pergunte antes de escolher.

## Estrutura do repositório
```
frontend/src/pages/        telas (home, cadastro, login, agendamento, admin, gerente)
frontend/src/components/   componentes reutilizáveis (botões, inputs, cards, tabelas, modais, gráficos)
frontend/src/routes/       rotas protegidas por perfil
backend/routes/            controllers: validação de entrada e autorização
backend/services/          regras de negócio
backend/repositories/      único ponto de acesso ao banco
backend/notifications/     envio de e-mail
database/                  migrations e seeds
docs/                      documentação
```

## Regras de arquitetura
- Backend em camadas: rota → serviço → repositório → MySQL.
- Só `backend/repositories/` executa SQL. Serviços e rotas nunca acessam o banco direto.
- Regras de negócio ficam em `backend/services/`, nunca nas rotas nem no frontend.
- Toda autorização é validada no backend. A checagem de perfil no React é só para exibir telas.
- O frontend acessa o backend apenas pela API, por um módulo de cliente HTTP centralizado.

## Regras de negócio essenciais
- Três perfis: cliente, admin, gerente. O gerente herda tudo do admin.
- Login com e-mail do domínio do salão leva à área interna; demais e-mails, à área do cliente.
- Cadastro, nesta ordem: nome completo, CPF, telefone, e-mail, senha, confirmar senha.
- Agendamento: serviço → profissional (filtrado pelo serviço) → data/hora → confirmação.
- Horário ocupado ou bloqueado não pode ser agendado; a validação de conflito é no backend.
- Excluir um agendamento libera o horário.
- Estoque baixo: produto com quantidade ≤ quantidade mínima.

## Fora de escopo
- WhatsApp via Twilio é **trabalho futuro**. Não implemente, não crie stubs, não adicione dependências.
- Não implemente nada que não esteja em `docs/requisitos.md` ou na issue em andamento sem perguntar.

## Fluxo Git (obrigatório)
- Toda tarefa parte de uma issue do GitHub Projects.
- Branch: `feature/{numero-da-issue}-{nome-curto}`, criada a partir de `developer`.
- PR sempre para `developer`, com `Closes #N` na descrição.
- Nunca faça commit ou push direto em `main` ou `developer`.
- Merge de `developer` para `main` só no fim da sprint, feito pelo time.
- Commits pequenos e descritivos em português.

## Como trabalhar
1. Antes de codar, leia a issue e proponha um plano em etapas, cada uma com uma forma de validar.
2. Explique o porquê das escolhas técnicas, não só a solução.
3. Quando faltar informação, pergunte. Se precisar supor, diga qual é a suposição.
4. Implemente uma etapa por vez e valide (rodar, testar, mostrar o resultado) antes da próxima.
5. Ao terminar, rode os testes e o lint e só então sugira o PR.

## Comandos
<!-- Atualizar quando o setup de cada parte estiver pronto. -->
- Frontend: `cd frontend && npm install && npm run dev` · testes: `npm test`
- Backend: a definir junto com o framework.
- Banco: a definir junto com as migrations.

## Segurança e dados (LGPD)
- Senhas sempre com hash (nunca texto puro). CPF e telefone são dados pessoais: não registrar em logs.
- Credenciais (banco, SMTP) só em `.env`, que fica no `.gitignore`. Mantenha um `.env.example` atualizado.
- Consultas SQL sempre parametrizadas.
