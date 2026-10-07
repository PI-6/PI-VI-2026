---
paths:
  - "frontend/**/*"
---

# Regras do frontend (React)

- Componentes funcionais com hooks. Nada de class components.
- Um componente por arquivo, nome em PascalCase (`ServiceCard.jsx`).
- Antes de criar um componente, verifique se já existe um reutilizável em `src/components/`.
- Componentes reutilizáveis esperados: botão, input, card, tabela, modal de confirmação de exclusão, stepper.
- Toda exclusão (agendamento, serviço, profissional, produto) pede confirmação em modal.
- Chamadas HTTP somente pelo cliente central de API (`src/services/api.js`). Componentes não chamam `fetch` direto.
- Enquanto um endpoint não existir, use mock no cliente de API (mesmo formato de resposta), nunca dados fixos dentro do componente.
- Rotas internas protegidas por perfil em `src/routes/`.
  Menu do admin: Dashboard, Agenda. Menu do gerente: Dashboard, Agenda, Serviços, Profissionais, Estoque, Financeiro (nesta ordem).
- Layout responsivo (desktop e mobile). Paleta clean em tons neutros/rosé com dourado.
- Textos de interface em português do Brasil.
