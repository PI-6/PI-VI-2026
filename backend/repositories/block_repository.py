"""Acesso às tabelas de bloqueio (migration 003, modelo do Eduardo).

- `bloqueios`: pontuais, com inicio e fim (DATETIME).
- `bloqueios_recorrentes`: semanais, com dia_semana, hora_inicio/hora_fim (TIME) e a validade
  valido_de/valido_ate (DATE; valido_ate nulo = sem data para acabar).

Para o serviço, os dois chegam no mesmo formato de dict, com "tipo" = "pontual" ou "semanal".
Os horários já vêm como datetime.time (o conector do MySQL entrega TIME como timedelta).
"""
from datetime import datetime, timedelta

import db

# Trechos fixos, sem nenhum valor vindo de fora; os filtros são sempre parâmetros (%s)
SELECT_ONE_OFF = """
    SELECT 'pontual' AS tipo, b.id, b.profissional_id, u.nome AS profissional_nome,
           b.inicio, b.fim, b.motivo
      FROM bloqueios b
      JOIN profissionais p ON p.id = b.profissional_id
      JOIN usuarios u ON u.id = p.usuario_id
"""

SELECT_WEEKLY = """
    SELECT 'semanal' AS tipo, r.id, r.profissional_id, u.nome AS profissional_nome,
           r.dia_semana, r.hora_inicio, r.hora_fim, r.valido_de, r.valido_ate, r.motivo
      FROM bloqueios_recorrentes r
      JOIN profissionais p ON p.id = r.profissional_id
      JOIN usuarios u ON u.id = p.usuario_id
"""

# Consultas completas por tipo: escolhe-se a consulta pronta, sem montar SQL com o tipo
FIND_BY_ID = {
    "pontual": SELECT_ONE_OFF + " WHERE b.id = %s",
    "semanal": SELECT_WEEKLY + " WHERE r.id = %s",
}
DELETE_BY_ID = {
    "pontual": "DELETE FROM bloqueios WHERE id = %s",
    "semanal": "DELETE FROM bloqueios_recorrentes WHERE id = %s",
}


def _to_time(value):
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    return value


def _normalize(row):
    if row and row["tipo"] == "semanal":
        row["hora_inicio"] = _to_time(row["hora_inicio"])
        row["hora_fim"] = _to_time(row["hora_fim"])
    return row


def find_by_id(kind, block_id):
    return _normalize(db.fetch_one(FIND_BY_ID[kind], (block_id,)))


def list_for_professional(professional_id, since):
    """Bloqueios que ainda valem: pontuais que terminam depois de `since` e semanais não expirados."""
    one_off = db.fetch_all(
        SELECT_ONE_OFF + " WHERE b.profissional_id = %s AND b.fim > %s ORDER BY b.inicio",
        (professional_id, since),
    )
    weekly = db.fetch_all(
        SELECT_WEEKLY + """ WHERE r.profissional_id = %s
                              AND (r.valido_ate IS NULL OR r.valido_ate >= %s)
                            ORDER BY r.dia_semana, r.hora_inicio""",
        (professional_id, since.date()),
    )
    return [_normalize(row) for row in one_off + weekly]


def list_between(start, end, professional_id=None):
    """Bloqueios que podem encostar em [start, end), de profissionais ativos.

    Pontuais: os que sobrepõem o período. Semanais: os que valem em algum dia do período;
    quem sabe em quais dias eles caem é o serviço (block_service.expand).
    Com professional_id, só os daquele profissional.
    """
    one_off_sql = SELECT_ONE_OFF + " WHERE u.ativo = 1 AND b.inicio < %s AND b.fim > %s"
    one_off_params = [end, start]
    weekly_sql = SELECT_WEEKLY + """ WHERE u.ativo = 1
                                       AND r.valido_de <= %s
                                       AND (r.valido_ate IS NULL OR r.valido_ate >= %s)"""
    weekly_params = [end.date(), start.date()]
    if professional_id is not None:
        one_off_sql += " AND b.profissional_id = %s"
        one_off_params.append(professional_id)
        weekly_sql += " AND r.profissional_id = %s"
        weekly_params.append(professional_id)

    rows = db.fetch_all(one_off_sql, tuple(one_off_params)) + db.fetch_all(weekly_sql, tuple(weekly_params))
    return [_normalize(row) for row in rows]


def create_if_no_conflict(block, now):
    """Grava o bloqueio só se não houver agendamento ativo no intervalo; devolve (id, conflitos).

    Mesma ideia do agendamento (appointment_repository.create_if_free): trava a linha do
    profissional para que um cliente não confirme um horário enquanto ele está sendo bloqueado.
    Só contam agendamentos não cancelados que ainda não terminaram.
    """
    with db.transaction() as cursor:
        cursor.execute("SELECT id FROM profissionais WHERE id = %s FOR UPDATE", (block["profissional_id"],))
        cursor.fetchone()  # o conector do MySQL exige ler o resultado antes do próximo comando

        base = """SELECT id, inicio, fim
                    FROM agendamentos
                   WHERE profissional_id = %s
                     AND status <> 'cancelado'
                     AND fim > %s"""
        if block["tipo"] == "pontual":
            cursor.execute(
                base + " AND inicio < %s AND fim > %s ORDER BY inicio",
                (block["profissional_id"], now, block["fim"], block["inicio"]),
            )
        else:
            # WEEKDAY() do MySQL também usa 0 = segunda, igual ao Python e a dia_semana.
            # Só os agendamentos dentro da validade da regra contam.
            cursor.execute(
                base + """ AND WEEKDAY(inicio) = %s AND TIME(inicio) < %s AND TIME(fim) > %s
                           AND DATE(inicio) >= %s AND (%s IS NULL OR DATE(inicio) <= %s)
                         ORDER BY inicio""",
                (block["profissional_id"], now, block["dia_semana"], block["hora_fim"], block["hora_inicio"],
                 block["valido_de"], block["valido_ate"], block["valido_ate"]),
            )
        conflicts = cursor.fetchall()
        if conflicts:
            return None, conflicts

        if block["tipo"] == "pontual":
            cursor.execute(
                "INSERT INTO bloqueios (profissional_id, inicio, fim, motivo, criado_por)"
                " VALUES (%s, %s, %s, %s, %s)",
                (block["profissional_id"], block["inicio"], block["fim"], block["motivo"], block["criado_por"]),
            )
        else:
            cursor.execute(
                """INSERT INTO bloqueios_recorrentes
                       (profissional_id, dia_semana, hora_inicio, hora_fim, valido_de, valido_ate, motivo, criado_por)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (block["profissional_id"], block["dia_semana"], block["hora_inicio"], block["hora_fim"],
                 block["valido_de"], block["valido_ate"], block["motivo"], block["criado_por"]),
            )
        return cursor.lastrowid, []


def delete(kind, block_id):
    db.execute(DELETE_BY_ID[kind], (block_id,))
