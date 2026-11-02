"""Acesso à tabela de bloqueios de horário (migration 003).

Devolve os horários já como datetime.time (o conector do MySQL entrega colunas TIME
como timedelta), para o serviço não precisar saber disso.
"""
from datetime import datetime, timedelta

import db

# Trecho fixo, sem nenhum valor vindo de fora; os filtros são sempre parâmetros (%s)
SELECT_BLOCK = """
    SELECT b.id, b.profissional_id, u.nome AS profissional_nome, b.tipo, b.inicio, b.fim,
           b.dia_semana, b.hora_inicio, b.hora_fim, b.motivo
      FROM bloqueios b
      JOIN profissionais p ON p.id = b.profissional_id
      JOIN usuarios u ON u.id = p.usuario_id
"""


def _to_time(value):
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    return value


def _normalize(row):
    if row:
        row["hora_inicio"] = _to_time(row["hora_inicio"])
        row["hora_fim"] = _to_time(row["hora_fim"])
    return row


def find_by_id(block_id):
    return _normalize(db.fetch_one(SELECT_BLOCK + " WHERE b.id = %s", (block_id,)))


def list_for_professional(professional_id, since):
    """Bloqueios que ainda valem: todos os semanais e os pontuais que terminam depois de `since`."""
    rows = db.fetch_all(
        SELECT_BLOCK + """
             WHERE b.profissional_id = %s
               AND (b.tipo = 'semanal' OR b.fim > %s)
             ORDER BY b.tipo, b.inicio, b.dia_semana, b.hora_inicio""",
        (professional_id, since),
    )
    return [_normalize(row) for row in rows]


def list_between(start, end, professional_id=None):
    """Pontuais que encostam em [start, end) e todos os semanais, de profissionais ativos.

    Os semanais vêm inteiros porque quem sabe em quais dias do período eles caem é o
    serviço (block_service.expand). Com professional_id, só os daquele profissional.
    """
    sql = SELECT_BLOCK + """
               WHERE u.ativo = 1
                 AND (b.tipo = 'semanal' OR (b.inicio < %s AND b.fim > %s))"""
    params = [end, start]
    if professional_id is not None:
        sql += " AND b.profissional_id = %s"
        params.append(professional_id)
    return [_normalize(row) for row in db.fetch_all(sql + " ORDER BY u.nome", tuple(params))]


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
            # WEEKDAY() do MySQL também usa 0 = segunda, igual ao Python e a horarios_trabalho
            cursor.execute(
                base + " AND WEEKDAY(inicio) = %s AND TIME(inicio) < %s AND TIME(fim) > %s ORDER BY inicio",
                (block["profissional_id"], now, block["dia_semana"], block["hora_fim"], block["hora_inicio"]),
            )
        conflicts = cursor.fetchall()
        if conflicts:
            return None, conflicts

        cursor.execute(
            """INSERT INTO bloqueios (profissional_id, tipo, inicio, fim, dia_semana, hora_inicio, hora_fim,
                                      motivo, criado_por)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (block["profissional_id"], block["tipo"], block.get("inicio"), block.get("fim"),
             block.get("dia_semana"), block.get("hora_inicio"), block.get("hora_fim"),
             block["motivo"], block["criado_por"]),
        )
        return cursor.lastrowid, []


def delete(block_id):
    db.execute("DELETE FROM bloqueios WHERE id = %s", (block_id,))
