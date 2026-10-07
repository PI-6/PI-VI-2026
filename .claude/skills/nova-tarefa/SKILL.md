---
name: nova-tarefa
description: Inicia o trabalho em uma issue do GitHub do Time 12 seguindo o fluxo do time (branch, plano em etapas, validação e PR). Use quando pedirem para começar, implementar ou pegar uma issue.
---

# Começar uma tarefa a partir de uma issue

Argumento esperado: número da issue (ex.: `/nova-tarefa 14`).

1. Leia a issue com `gh issue view <N>`. Se não houver número, pergunte qual é.
2. Confira se a issue está no escopo de `docs/requisitos.md`. Se tocar algo fora (ex.: WhatsApp), pare e avise.
3. Atualize a base: `git checkout developer && git pull`.
4. Crie a branch: `git checkout -b feature/<N>-<nome-curto-em-kebab-case>`.
5. Proponha um plano em etapas. Para cada etapa, diga o que muda e como validar. Espere aprovação.
6. Implemente uma etapa por vez, valide e faça um commit pequeno em português.
7. No fim, rode testes e lint, faça push e abra o PR para `developer` com `gh pr create --base developer`,
   descrevendo o que mudou, como testar e incluindo `Closes #<N>`.
8. Lembre de mover o card para "In QA" no quadro.
