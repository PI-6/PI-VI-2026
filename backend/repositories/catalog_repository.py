"""Acesso à tabela de serviços do salão (corte, manicure...).

Usamos o nome "catalog" para não confundir com a pasta services/, que é a camada de regras.
"""
import db


def _to_dict(row):
    if row is None:
        return None
    # DECIMAL vem do MySQL como Decimal, que não é serializável direto para JSON
    return {**row, "preco": float(row["preco"])}


def list_active():
    rows = db.fetch_all(
        "SELECT id, nome, descricao, duracao_minutos, preco FROM servicos WHERE ativo = 1 ORDER BY nome"
    )
    return [_to_dict(row) for row in rows]


def find_active_by_id(service_id):
    row = db.fetch_one(
        "SELECT id, nome, descricao, duracao_minutos, preco FROM servicos WHERE id = %s AND ativo = 1",
        (service_id,),
    )
    return _to_dict(row)


def find_active_by_name(nome):
    row = db.fetch_one(
        "SELECT id, nome, descricao, duracao_minutos, preco FROM servicos WHERE nome = %s AND ativo = 1",
        (nome,),
    )
    return _to_dict(row)


def find_active_ids(service_ids):
    """Dentre os ids informados, devolve só os que existem e estão ativos."""
    if not service_ids:
        return set()
    rows = db.fetch_all(
        "SELECT id FROM servicos WHERE ativo = 1 AND id IN (" + db.placeholders(service_ids) + ")",
        tuple(service_ids),
    )
    return {row["id"] for row in rows}


def create(nome, descricao, duracao_minutos, preco):
    return db.execute(
        "INSERT INTO servicos (nome, descricao, duracao_minutos, preco) VALUES (%s, %s, %s, %s)",
        (nome, descricao, duracao_minutos, preco),
    )


def update(service_id, nome, descricao, duracao_minutos, preco):
    db.execute(
        "UPDATE servicos SET nome = %s, descricao = %s, duracao_minutos = %s, preco = %s"
        " WHERE id = %s",
        (nome, descricao, duracao_minutos, preco, service_id),
    )


def deactivate(service_id):
    db.execute("UPDATE servicos SET ativo = 0 WHERE id = %s", (service_id,))
