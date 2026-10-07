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

```mermaid
erDiagram
    USUARIOS ||--o| PROFISSIONAIS : "é (se for da equipe)"
    PROFISSIONAIS ||--o{ PROFISSIONAL_SERVICOS : realiza
    SERVICOS ||--o{ PROFISSIONAL_SERVICOS : "é realizado por"
    PROFISSIONAIS ||--o{ HORARIOS_TRABALHO : trabalha
    USUARIOS ||--o{ AGENDAMENTOS : "agenda (cliente)"
    PROFISSIONAIS ||--o{ AGENDAMENTOS : atende
    SERVICOS ||--o{ AGENDAMENTOS : "é agendado"
    PROFISSIONAIS ||--o{ BLOQUEIOS : bloqueia

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
        int cliente_id FK "Sprint 2"
        int profissional_id FK
        int servico_id FK
        datetime inicio
        datetime fim
        decimal valor "preço no momento do agendamento"
        enum status "agendado, concluido, cancelado"
    }
    BLOQUEIOS {
        int id PK
        int profissional_id FK "Sprint 3"
        datetime inicio
        datetime fim
        varchar motivo
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
| `agendamentos.status` em vez de apagar a linha | Excluir um agendamento libera o horário (RF06), mas manter a linha como `cancelado` ajuda nos relatórios. A regra exata fica para a Sprint 2/3. |

## Pontos para o Eduardo revisar

1. Estoque (RF09) não aparece em nenhuma sprint do `docs/sprints.md`. Em qual sprint entra?
2. Agendamento cancelado: apagar a linha ou mudar o status? (impacta o BI)
3. Precisamos de índice em `agendamentos (profissional_id, inicio)` na Sprint 2 (tarefa de otimização).
