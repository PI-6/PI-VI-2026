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


def create_if_free(cliente_id, professional_id, service_id, inicio, fim, valor):
    """Grava o agendamento só se o intervalo continuar livre; devolve o id ou None.

    O serviço já checou o conflito, mas dois clientes podem confirmar o mesmo horário
    ao mesmo tempo. Por isso, dentro de uma única transação:
    1. trava a linha do profissional (FOR UPDATE): a segunda requisição espera a primeira terminar;
    2. confere de novo se há sobreposição, agora vendo o que a primeira gravou;
    3. só então insere.
    """
    with db.transaction() as cursor:
        cursor.execute("SELECT id FROM profissionais WHERE id = %s FOR UPDATE", (professional_id,))
        cursor.fetchone()  # o conector do MySQL exige ler o resultado antes do próximo comando
        cursor.execute(
            """SELECT COUNT(*) AS total
                 FROM agendamentos
                WHERE profissional_id = %s
                  AND status <> 'cancelado'
                  AND inicio < %s
                  AND fim > %s""",
            (professional_id, fim, inicio),
        )
        if cursor.fetchone()["total"]:
            return None
        cursor.execute(
            "INSERT INTO agendamentos (cliente_id, profissional_id, servico_id, inicio, fim, valor)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (cliente_id, professional_id, service_id, inicio, fim, valor),
        )
        return cursor.lastrowid
