"""Consultas agregadas do Financeiro / BI (RF10).

Atendimento realizado = agendamento não cancelado cujo horário já terminou (decisão do time,
03/11). Por isso toda consulta recebe `now`: o que ainda não aconteceu não entra na receita.
A receita usa agendamentos.valor, o preço gravado no dia do agendamento.

O período é sempre [start, end) pelo início do agendamento.
"""
import db

# Condição comum a todas as consultas: só atendimentos realizados no período
REALIZED = """
    a.status <> 'cancelado'
    AND a.fim <= %s
    AND a.inicio >= %s
    AND a.inicio < %s
"""


def monthly_totals(start, end, now):
    """Receita e atendimentos por mês: [{"ano", "mes", "receita", "atendimentos"}]. Meses vazios não vêm."""
    return db.fetch_all(
        """SELECT YEAR(a.inicio) AS ano, MONTH(a.inicio) AS mes,
                  SUM(a.valor) AS receita, COUNT(*) AS atendimentos
             FROM agendamentos a
            WHERE """ + REALIZED + """
            GROUP BY YEAR(a.inicio), MONTH(a.inicio)
            ORDER BY ano, mes""",
        (now, start, end),
    )
