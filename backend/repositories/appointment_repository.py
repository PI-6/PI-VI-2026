"""Acesso à tabela de agendamentos."""
import db


def list_busy_between(professional_id, start, end):
    """Intervalos que ocupam a agenda do profissional entre start e end.

    Cancelados não entram: cancelar libera o horário. Concluídos entram, porque
    o horário já passou ou foi usado.
    """
    return db.fetch_all(
        """SELECT inicio, fim
             FROM agendamentos
            WHERE profissional_id = %s
              AND status <> 'cancelado'
              AND inicio < %s
              AND fim > %s
            ORDER BY inicio""",
        (professional_id, end, start),
    )
