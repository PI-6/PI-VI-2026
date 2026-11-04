"""Acesso à tabela de produtos do estoque (migration 004)."""
import db

SELECT_PRODUCT = """
    SELECT id, nome, descricao, quantidade, quantidade_minima, preco_unitario, unidade
      FROM produtos
"""


def list_all():
    return db.fetch_all(SELECT_PRODUCT + " ORDER BY nome")


def list_low_stock():
    """Produtos com quantidade <= quantidade mínima (estoque baixo)."""
    return db.fetch_all(SELECT_PRODUCT + " WHERE quantidade <= quantidade_minima ORDER BY nome")


def find_by_id(product_id):
    return db.fetch_one(SELECT_PRODUCT + " WHERE id = %s", (product_id,))


def find_by_name(nome):
    return db.fetch_one(SELECT_PRODUCT + " WHERE nome = %s", (nome,))


def create(product):
    return db.execute(
        """INSERT INTO produtos (nome, descricao, quantidade, quantidade_minima, preco_unitario, unidade)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (product["nome"], product["descricao"], product["quantidade"], product["quantidade_minima"],
         product["preco_unitario"], product["unidade"]),
    )


def update(product_id, product):
    db.execute(
        """UPDATE produtos
              SET nome = %s, descricao = %s, quantidade = %s, quantidade_minima = %s,
                  preco_unitario = %s, unidade = %s
            WHERE id = %s""",
        (product["nome"], product["descricao"], product["quantidade"], product["quantidade_minima"],
         product["preco_unitario"], product["unidade"], product_id),
    )
