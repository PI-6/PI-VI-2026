import db


def _format_time(value):
    # O conector do MySQL devolve colunas TIME como timedelta
    total_minutes = int(value.total_seconds()) // 60
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _load_details(cursor, professionals):
    """Completa cada profissional com seus serviços e horários de trabalho."""
    if not professionals:
        return professionals

    ids = tuple(p["id"] for p in professionals)
    by_id = {p["id"]: {**p, "servicos": [], "horarios": []} for p in professionals}

    cursor.execute(
        """SELECT ps.profissional_id, s.id, s.nome
             FROM profissional_servicos ps
             JOIN servicos s ON s.id = ps.servico_id AND s.ativo = 1
            WHERE ps.profissional_id IN (""" + db.placeholders(ids) + """)
            ORDER BY s.nome""",
        ids,
    )
    for row in cursor.fetchall():
        by_id[row["profissional_id"]]["servicos"].append({"id": row["id"], "nome": row["nome"]})

    cursor.execute(
        """SELECT profissional_id, dia_semana, hora_inicio, hora_fim
             FROM horarios_trabalho
            WHERE profissional_id IN (""" + db.placeholders(ids) + """)
            ORDER BY dia_semana""",
        ids,
    )
    for row in cursor.fetchall():
        by_id[row["profissional_id"]]["horarios"].append({
            "dia_semana": row["dia_semana"],
            "hora_inicio": _format_time(row["hora_inicio"]),
            "hora_fim": _format_time(row["hora_fim"]),
        })

    return list(by_id.values())


SELECT_PROFESSIONAL = """
    SELECT p.id, u.id AS usuario_id, u.nome, u.email, u.telefone, u.perfil
      FROM profissionais p
      JOIN usuarios u ON u.id = p.usuario_id
     WHERE u.ativo = 1
"""


def list_active():
    with db.transaction() as cursor:
        cursor.execute(SELECT_PROFESSIONAL + " ORDER BY u.nome")
        return _load_details(cursor, cursor.fetchall())


def find_active_by_id(professional_id):
    with db.transaction() as cursor:
        cursor.execute(SELECT_PROFESSIONAL + " AND p.id = %s", (professional_id,))
        row = cursor.fetchone()
        return _load_details(cursor, [row])[0] if row else None


def _replace_services_and_hours(cursor, professional_id, service_ids, hours):
    # Mais simples apagar e inserir de novo do que calcular a diferença
    cursor.execute("DELETE FROM profissional_servicos WHERE profissional_id = %s", (professional_id,))
    cursor.execute("DELETE FROM horarios_trabalho WHERE profissional_id = %s", (professional_id,))

    if service_ids:
        cursor.executemany(
            "INSERT INTO profissional_servicos (profissional_id, servico_id) VALUES (%s, %s)",
            [(professional_id, service_id) for service_id in service_ids],
        )
    if hours:
        cursor.executemany(
            "INSERT INTO horarios_trabalho (profissional_id, dia_semana, hora_inicio, hora_fim)"
            " VALUES (%s, %s, %s, %s)",
            [(professional_id, h["dia_semana"], h["hora_inicio"], h["hora_fim"]) for h in hours],
        )


def create(user, service_ids, hours):
    """Cria usuário + profissional + serviços + horários numa única transação."""
    with db.transaction() as cursor:
        cursor.execute(
            "INSERT INTO usuarios (nome, cpf, telefone, email, senha_hash, perfil)"
            " VALUES (%s, %s, %s, %s, %s, %s)",
            (user["nome"], user["cpf"], user["telefone"], user["email"], user["senha_hash"], user["perfil"]),
        )
        cursor.execute("INSERT INTO profissionais (usuario_id) VALUES (%s)", (cursor.lastrowid,))
        professional_id = cursor.lastrowid
        _replace_services_and_hours(cursor, professional_id, service_ids, hours)
        return professional_id


def update(professional_id, user, service_ids, hours):
    with db.transaction() as cursor:
        cursor.execute(
            """UPDATE usuarios u
                 JOIN profissionais p ON p.usuario_id = u.id
                  SET u.nome = %s, u.cpf = %s, u.telefone = %s, u.email = %s, u.perfil = %s
                WHERE p.id = %s""",
            (user["nome"], user["cpf"], user["telefone"], user["email"], user["perfil"], professional_id),
        )
        # Senha só muda quando o gerente informar uma nova
        if user.get("senha_hash"):
            cursor.execute(
                """UPDATE usuarios u JOIN profissionais p ON p.usuario_id = u.id
                      SET u.senha_hash = %s WHERE p.id = %s""",
                (user["senha_hash"], professional_id),
            )
        _replace_services_and_hours(cursor, professional_id, service_ids, hours)


def deactivate(professional_id):
    # Desativa o usuário: some das listagens e não consegue mais fazer login
    db.execute(
        "UPDATE usuarios u JOIN profissionais p ON p.usuario_id = u.id SET u.ativo = 0 WHERE p.id = %s",
        (professional_id,),
    )
