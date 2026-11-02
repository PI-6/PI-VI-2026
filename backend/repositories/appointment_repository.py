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
    ao mesmo tempo (ou a equipe pode bloquear o horário enquanto o cliente confirma).
    Por isso, dentro de uma única transação:
    1. trava a linha do profissional (FOR UPDATE): a segunda requisição espera a primeira terminar;
    2. confere de novo se há sobreposição com agendamentos e bloqueios, agora vendo o que a
       primeira gravou;
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
        # Bloqueio pontual que encosta no intervalo, ou semanal no mesmo dia da semana e faixa de horário.
        # O agendamento cabe dentro de um expediente, então começa e termina no mesmo dia.
        cursor.execute(
            """SELECT COUNT(*) AS total
                 FROM bloqueios
                WHERE profissional_id = %s
                  AND ((tipo = 'pontual' AND inicio < %s AND fim > %s)
                       OR (tipo = 'semanal' AND dia_semana = %s AND hora_inicio < %s AND hora_fim > %s))""",
            (professional_id, fim, inicio, inicio.weekday(), fim.time(), inicio.time()),
        )
        if cursor.fetchone()["total"]:
            return None
        cursor.execute(
            "INSERT INTO agendamentos (cliente_id, profissional_id, servico_id, inicio, fim, valor)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (cliente_id, professional_id, service_id, inicio, fim, valor),
        )
        return cursor.lastrowid


def list_day(start, end, professional_id=None):
    """Agendamentos ativos (não cancelados) em [start, end), com os nomes para a agenda da equipe.

    Do cliente vai só o nome: a agenda não precisa de CPF, e-mail ou telefone (LGPD).
    """
    sql = """SELECT a.id, a.inicio, a.fim, a.valor, a.status,
                    a.cliente_id, c.nome AS cliente_nome,
                    a.profissional_id, up.nome AS profissional_nome,
                    a.servico_id, s.nome AS servico_nome
               FROM agendamentos a
               JOIN usuarios c ON c.id = a.cliente_id
               JOIN profissionais p ON p.id = a.profissional_id
               JOIN usuarios up ON up.id = p.usuario_id
               JOIN servicos s ON s.id = a.servico_id
              WHERE a.status <> 'cancelado'
                AND a.inicio < %s
                AND a.fim > %s"""
    params = [end, start]
    if professional_id is not None:
        sql += " AND a.profissional_id = %s"
        params.append(professional_id)
    return db.fetch_all(sql + " ORDER BY a.inicio, up.nome", tuple(params))


def find_by_id(appointment_id):
    return db.fetch_one(
        "SELECT id, cliente_id, profissional_id, servico_id, inicio, fim, status FROM agendamentos WHERE id = %s",
        (appointment_id,),
    )


def cancel(appointment_id, cancelled_by, cancelled_at):
    """Marca como cancelado só se ainda estiver 'agendado'; devolve True se mudou.

    O WHERE com status = 'agendado' evita que dois cliques (ou duas pessoas da equipe)
    cancelem o mesmo agendamento duas vezes e sobrescrevam quem cancelou primeiro.
    """
    with db.transaction() as cursor:
        cursor.execute(
            """UPDATE agendamentos
                  SET status = 'cancelado', cancelado_em = %s, cancelado_por = %s
                WHERE id = %s AND status = 'agendado'""",
            (cancelled_at, cancelled_by, appointment_id),
        )
        return cursor.rowcount == 1
