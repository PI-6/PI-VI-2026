# Modelo de Dados (MER) — Time 12

Proposta inicial do modelo relacional, feita a partir de `docs/requisitos.md` e `docs/sprints.md`.
**Precisa da revisão do Eduardo** antes de ser considerada final (Seção 9 do relatório).

Convenções:
- Tabelas e colunas em português, no singular para colunas e plural para tabelas.
- Toda tabela tem `id` inteiro auto incremento como chave primária.
- Exclusões de usuários e serviços são lógicas (`ativo = 0`), para não perder o histórico
  de agendamentos usado pelo BI.

## Diagrama

As tabelas marcadas como *(Sprint N)* ainda não têm migration; entram quando a sprint começar.
Migrations aplicadas: `001` (usuários, serviços, profissionais, horários), `002` (agendamentos) e `003` (bloqueios).

```mermaid
erDiagram
    USUARIOS ||--o| PROFISSIONAIS : "é (se for da equipe)"
    PROFISSIONAIS ||--o{ PROFISSIONAL_SERVICOS : realiza
    SERVICOS ||--o{ PROFISSIONAL_SERVICOS : "é realizado por"
    PROFISSIONAIS ||--o{ HORARIOS_TRABALHO : trabalha
    USUARIOS ||--o{ AGENDAMENTOS : "agenda (cliente)"
    PROFISSIONAIS ||--o{ AGENDAMENTOS : atende
    SERVICOS ||--o{ AGENDAMENTOS : "é agendado"
    PROFISSIONAIS ||--o{ BLOQUEIOS : "bloqueia (pontual)"
    PROFISSIONAIS ||--o{ BLOQUEIOS_RECORRENTES : "bloqueia (toda semana)"
    USUARIOS ||--o{ BLOQUEIOS : "cria (equipe)"
    USUARIOS ||--o{ BLOQUEIOS_RECORRENTES : "cria (equipe)"

    USUARIOS {
        int id PK
        varchar nome
        char cpf UK "nulo para equipe"
        varchar telefone
        varchar email UK
        varchar senha_hash
        enum perfil "cliente, admin, gerente"
        tinyint ativo
    }
    PROFISSIONAIS {
        int id PK
        int usuario_id FK,UK
    }
    SERVICOS {
        int id PK
        varchar nome
        varchar descricao
        smallint duracao_minutos
        decimal preco
        tinyint ativo
    }
    PROFISSIONAL_SERVICOS {
        int profissional_id PK,FK
        int servico_id PK,FK
    }
    HORARIOS_TRABALHO {
        int id PK
        int profissional_id FK
        tinyint dia_semana "0=segunda ... 6=domingo"
        time hora_inicio
        time hora_fim
    }
    AGENDAMENTOS {
        int id PK
        int cliente_id FK
        int profissional_id FK
        int servico_id FK
        datetime inicio
        datetime fim
        decimal valor "preço no momento do agendamento"
        enum status "agendado, concluido, cancelado"
        datetime cancelado_em
        int cancelado_por FK "usuário que cancelou"
    }
    BLOQUEIOS {
        int id PK
        int profissional_id FK
        datetime inicio
        datetime fim
        varchar motivo
        int criado_por FK "usuário da equipe"
    }
    BLOQUEIOS_RECORRENTES {
        int id PK
        int profissional_id FK
        tinyint dia_semana "0=segunda ... 6=domingo"
        time hora_inicio
        time hora_fim
        date valido_de
        date valido_ate "nulo = sem data para acabar"
        varchar motivo
        int criado_por FK "usuário da equipe"
    }
    PRODUTOS {
        int id PK "sem sprint definida"
        varchar nome
        varchar descricao
        decimal quantidade
        decimal quantidade_minima
        decimal preco_unitario
        enum unidade "ml, g, l, un"
    }
```

## Decisões e justificativas

| Decisão | Por quê |
|---|---|
| Profissional é um usuário com perfil `admin` ou `gerente` + linha em `profissionais` | O RF08 diz que o gerente define o nível de acesso do profissional, então todo profissional faz login. A tabela separada garante que um agendamento só aponte para quem é da equipe. |
| Perfil como `ENUM` em `usuarios` | São só três perfis fixos e o gerente herda o admin; uma tabela de papéis seria complexidade sem ganho agora. |
| CPF e telefone só com dígitos e opcionais | Obrigatórios no cadastro do cliente (validado na API), mas funcionários podem ser cadastrados só com nome e e-mail. São dados pessoais (LGPD). |
| Um intervalo de trabalho por dia | Pausas (almoço, consulta médica) são feitas com `bloqueios`, como descrito na Sprint 3. |
| `agendamentos.valor` guarda o preço do dia | Se o preço do serviço mudar, a receita histórica do BI continua correta. |
| Bloqueios em duas tabelas: `bloqueios` (pontuais) e `bloqueios_recorrentes` (semanais) | Modelo do Eduardo (issue #19, migration 003). Cada tipo tem campos diferentes; separados, as colunas de data e hora são `NOT NULL` e as restrições ficam simples. O recorrente segue o padrão de `horarios_trabalho`: uma linha por dia da semana. |
| Recorrente com `valido_de` / `valido_ate` | Permite regras com período ("almoço às 12h só em novembro") e encerrar uma regra sem apagar a linha. `valido_ate` nulo = vale sem data para acabar. |
| Bloqueio removido é apagado (`DELETE`) | Bloqueio não entra na receita nem nos indicadores do BI, então não há histórico a preservar. |
| Cancelamento muda o `status` para `cancelado`, sem apagar a linha | Na tela, "Excluir agendamento" (RF06) marca como cancelado e grava quem cancelou e quando. A checagem de conflito e a lista de horários livres ignoram os cancelados, então o horário fica livre na hora. O BI conta só os `concluido` na receita e pode mostrar a taxa de cancelamento. |

## Pontos para o Eduardo revisar

1. Estoque (RF09) ainda não está em nenhuma sprint do `docs/sprints.md` (o Luiz vai incluir).
2. ~~Índice em `agendamentos (profissional_id, inicio)`~~: criado na migration 002, junto com `(cliente_id, inicio)`.
3. ~~Bloqueios (issue #19)~~: modelado pelo Eduardo na migration 003 (PR #60), com duas tabelas.
