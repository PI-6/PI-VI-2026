---
paths:
  - "backend/**/*"
  - "database/**/*"
---

# Regras do backend (Python) e do banco (MySQL)

- Camadas: `routes/` (entrada, validação, autorização) → `services/` (regras) → `repositories/` (SQL).
- Uma rota nunca importa um repositório diretamente; sempre passa por um serviço.
- Repositórios recebem e devolvem dados simples (dicts ou dataclasses), sem regra de negócio.
- SQL sempre parametrizado. Nada de montar consulta com f-string ou concatenação.
- Toda rota interna verifica o perfil (cliente, admin, gerente) antes de executar.
- Respostas da API em JSON com status HTTP coerente (400 validação, 401 sem login, 403 sem permissão, 404, 409 conflito de horário).
- Conflito de agendamento é checado no serviço e protegido no banco (restrição ou transação), para evitar dois clientes no mesmo horário.
- E-mails só pelo módulo `notifications/`; os serviços chamam esse módulo, nunca o SMTP direto.
- Mudanças de schema só por migration em `database/`, seguindo o MER do Eduardo. Avise se a tarefa exigir mudar o MER.
- Não escolha framework, ORM ou biblioteca de migration sem confirmar com o time (decisão do Rafael).
- Toda regra de negócio nova ganha teste unitário no serviço.
