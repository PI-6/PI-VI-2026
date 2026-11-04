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


def by_professional(start, end, now):
    """Atendimentos, clientes distintos e receita por profissional, do que mais atendeu ao que menos.

    Profissional desativado continua aparecendo se atendeu no período (o histórico não some).
    """
    return db.fetch_all(
        """SELECT a.profissional_id AS id, u.nome,
                  COUNT(*) AS atendimentos, COUNT(DISTINCT a.cliente_id) AS clientes, SUM(a.valor) AS receita
             FROM agendamentos a
             JOIN profissionais p ON p.id = a.profissional_id
             JOIN usuarios u ON u.id = p.usuario_id
            WHERE """ + REALIZED + """
            GROUP BY a.profissional_id, u.nome
            ORDER BY atendimentos DESC, receita DESC, u.nome""",
        (now, start, end),
    )


def daily_totals(start, end, now):
    """Receita e atendimentos por dia: [{"dia": date, "receita", "atendimentos"}]. Dias vazios não vêm."""
    return db.fetch_all(
        """SELECT DATE(a.inicio) AS dia, SUM(a.valor) AS receita, COUNT(*) AS atendimentos
             FROM agendamentos a
            WHERE """ + REALIZED + """
            GROUP BY DATE(a.inicio)
            ORDER BY dia""",
        (now, start, end),
    )


def by_service(start, end, now):
    """Atendimentos e receita por serviço, do mais realizado ao menos realizado.

    Serviço excluído (ativo = 0) continua aparecendo se foi realizado no período.
    """
    return db.fetch_all(
        """SELECT s.id, s.nome, COUNT(*) AS atendimentos, SUM(a.valor) AS receita
             FROM agendamentos a
             JOIN servicos s ON s.id = a.servico_id
            WHERE """ + REALIZED + """
            GROUP BY s.id, s.nome
            ORDER BY atendimentos DESC, receita DESC, s.nome""",
        (now, start, end),
    )
