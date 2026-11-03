"""Estoque (RF09, issue #68). Estoque baixo = quantidade <= quantidade mínima."""
from decimal import Decimal

import pytest

from errors import ConflictError, NotFoundError, ValidationError


def shampoo(**changes):
    return {"nome": "Shampoo hidratante", "descricao": "Uso no lavatório", "quantidade": 4500,
            "quantidade_minima": 1000, "preco_unitario": 0.08, "unidade": "ml", **changes}


# --- criar e editar ------------------------------------------------------------------------

def test_create_product(product_service, products):
    created = product_service.create_product(shampoo())

    assert created == {"id": 1, "nome": "Shampoo hidratante", "descricao": "Uso no lavatório",
                       "quantidade": 4500.0, "quantidade_minima": 1000.0, "preco_unitario": 0.08,
                       "unidade": "ml", "estoque_baixo": False}
    # No banco os números vão como Decimal, sem erro de arredondamento
    assert products.rows[0]["preco_unitario"] == Decimal("0.08")


def test_fractional_quantity_and_text_numbers(product_service):
    created = product_service.create_product(shampoo(unidade="l", quantidade="0,5", quantidade_minima="1.25"))

    assert (created["quantidade"], created["quantidade_minima"], created["estoque_baixo"]) == (0.5, 1.25, True)


def test_unit_products_have_integer_quantities(product_service):
    created = product_service.create_product(shampoo(nome="Esmalte", unidade="un", quantidade=12,
                                                     quantidade_minima=4))
    assert (created["quantidade"], created["quantidade_minima"]) == (12, 4)

    with pytest.raises(ValidationError) as error:
        product_service.create_product(shampoo(nome="Lixa", unidade="un", quantidade=2.5))
    assert "quantidade" in error.value.details


def test_quantity_equal_to_minimum_is_low_stock(product_service):
    assert product_service.create_product(shampoo(quantidade=1000))["estoque_baixo"] is True


def test_update_product(product_service):
    product_id = product_service.create_product(shampoo())["id"]

    updated = product_service.update_product(product_id, shampoo(quantidade=800, descricao=""))

    assert (updated["quantidade"], updated["descricao"], updated["estoque_baixo"]) == (800.0, None, True)


def test_duplicate_name_is_refused(product_service):
    product_service.create_product(shampoo())
    other_id = product_service.create_product(shampoo(nome="Condicionador"))["id"]

    with pytest.raises(ConflictError):
        product_service.create_product(shampoo())
    with pytest.raises(ConflictError):
        product_service.update_product(other_id, shampoo())


def test_update_can_keep_its_own_name(product_service):
    product_id = product_service.create_product(shampoo())["id"]

    assert product_service.update_product(product_id, shampoo(quantidade=10))["nome"] == "Shampoo hidratante"


def test_unknown_product(product_service):
    with pytest.raises(NotFoundError):
        product_service.get_product(99)
    with pytest.raises(NotFoundError):
        product_service.update_product(99, shampoo())


@pytest.mark.parametrize("changes, field", [
    ({"nome": "  "}, "nome"),
    ({"nome": "x" * 121}, "nome"),
    ({"descricao": "x" * 501}, "descricao"),
    ({"unidade": "kg"}, "unidade"),
    ({"quantidade": -1}, "quantidade"),
    ({"quantidade": "muito"}, "quantidade"),
    ({"quantidade": None}, "quantidade"),
    ({"quantidade": True}, "quantidade"),
    ({"quantidade": "NaN"}, "quantidade"),
    ({"quantidade": 10_000_000}, "quantidade"),
    ({"quantidade": 1.2345}, "quantidade"),
    ({"quantidade_minima": -5}, "quantidade_minima"),
    ({"preco_unitario": 9.999}, "preco_unitario"),
    ({"preco_unitario": ""}, "preco_unitario"),
])
def test_invalid_product(product_service, changes, field):
    with pytest.raises(ValidationError) as error:
        product_service.create_product(shampoo(**changes))
    assert field in error.value.details


# --- listar e alerta -----------------------------------------------------------------------

@pytest.fixture
def stock(products):
    products.add("Shampoo", 4500, 1000, "ml")
    products.add("Lixa de unha", 3, 20, "un")        # 15% do mínimo
    products.add("Água oxigenada", 0.5, 1, "l")      # 50% do mínimo
    products.add("Esmalte", 0, 0, "un")              # zerado, sem mínimo definido
    products.add("Pó descolorante", 240, 250, "g")   # 96% do mínimo
    return products


def test_list_is_alphabetical_with_low_stock_flag(product_service, stock):
    listed = product_service.list_products()

    assert [p["nome"] for p in listed] == ["Água oxigenada", "Esmalte", "Lixa de unha", "Pó descolorante", "Shampoo"]
    assert [p["estoque_baixo"] for p in listed] == [True, True, True, True, False]


def test_list_only_low_stock(product_service, stock):
    assert "Shampoo" not in [p["nome"] for p in product_service.list_products(low_stock_only=True)]


def test_alert_shows_the_three_most_critical(product_service, stock):
    alert = product_service.low_stock_alert()

    assert alert["total"] == 4
    assert [p["nome"] for p in alert["produtos"]] == ["Esmalte", "Lixa de unha", "Água oxigenada"]
    assert alert["produtos"][1] == {"id": 2, "nome": "Lixa de unha", "quantidade": 3, "quantidade_minima": 20,
                                    "unidade": "un"}


def test_alert_without_low_stock(product_service, products):
    products.add("Shampoo", 4500, 1000, "ml")

    assert product_service.low_stock_alert() == {"total": 0, "produtos": []}
