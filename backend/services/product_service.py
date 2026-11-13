"""Estoque do salão (RF09, issue #68).

- Estoque baixo: quantidade <= quantidade mínima. A quantidade mínima é o gatilho do alerta.
- Unidades: ml, g (gramas), l (litros) e un (unidade). Em "un" a quantidade é sempre inteira;
  nas outras pode ter até 3 casas decimais (ex.: 0,5 l).
- O RF09 pede listar, adicionar e editar; não há exclusão de produto.
"""
from decimal import Decimal, InvalidOperation

from errors import ConflictError, NotFoundError, ValidationError
from services import validators as v

UNITS = ("ml", "g", "l", "un")
MAX_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 500
# Limites das colunas DECIMAL(10,3) e DECIMAL(10,2)
MAX_QUANTITY = Decimal("9999999.999")
MAX_PRICE = Decimal("99999999.99")


def is_low_stock(product):
    return Decimal(str(product["quantidade"])) <= Decimal(str(product["quantidade_minima"]))


def _number(value, unit):
    value = Decimal(str(value))
    if unit == "un":
        return int(value)
    return float(value)


def to_response(product):
    unit = product["unidade"]
    return {
        "id": product["id"],
        "nome": product["nome"],
        "descricao": product["descricao"],
        "quantidade": _number(product["quantidade"], unit),
        "quantidade_minima": _number(product["quantidade_minima"], unit),
        "preco_unitario": float(Decimal(str(product["preco_unitario"])).quantize(Decimal("0.01"))),
        "unidade": unit,
        "estoque_baixo": is_low_stock(product),
    }


def criticality(product):
    """Quanto menor, mais crítico: quantidade em relação ao mínimo (zerado vem primeiro)."""
    minimum = Decimal(str(product["quantidade_minima"]))
    quantity = Decimal(str(product["quantidade"]))
    return Decimal(0) if not minimum else quantity / minimum


class ProductService:
    def __init__(self, product_repository):
        self.products = product_repository

    def list_products(self, low_stock_only=False):
        rows = self.products.list_low_stock() if low_stock_only else self.products.list_all()
        return [to_response(row) for row in rows]

    def get_product(self, product_id):
        product = self.products.find_by_id(product_id)
        if not product:
            raise NotFoundError("Produto não encontrado.")
        return to_response(product)

    def create_product(self, data):
        product = self._validate(data)
        self._ensure_unique_name(product["nome"])
        return self.get_product(self.products.create(product))

    def update_product(self, product_id, data):
        self.get_product(product_id)
        product = self._validate(data)
        self._ensure_unique_name(product["nome"], ignore_id=product_id)
        self.products.update(product_id, product)
        return self.get_product(product_id)

    def low_stock_alert(self, limit=3):
        """Alerta do Dashboard (RF05): os `limit` produtos mais críticos e o total em estoque baixo."""
        rows = sorted(self.products.list_low_stock(), key=lambda p: (criticality(p), p["nome"]))
        return {
            "total": len(rows),
            "produtos": [{key: item[key] for key in ("id", "nome", "quantidade", "quantidade_minima", "unidade")}
                         for item in (to_response(row) for row in rows[:limit])],
        }

    def _ensure_unique_name(self, nome, ignore_id=None):
        same = self.products.find_by_name(nome)
        if same and same["id"] != ignore_id:
            raise ConflictError("Já existe um produto com esse nome.")

    def _validate(self, data):
        errors = {}
        nome = v.clean_text(data.get("nome"))
        descricao = v.clean_text(data.get("descricao")) or None
        unidade = data.get("unidade")

        if not nome:
            errors["nome"] = "Informe o nome do produto."
        elif len(nome) > MAX_NAME_LENGTH:
            errors["nome"] = f"Use no máximo {MAX_NAME_LENGTH} caracteres."
        if descricao and len(descricao) > MAX_DESCRIPTION_LENGTH:
            errors["descricao"] = f"Use no máximo {MAX_DESCRIPTION_LENGTH} caracteres."
        if unidade not in UNITS:
            errors["unidade"] = "A unidade deve ser ml, g, l ou un."

        quantidade = self._quantity(data.get("quantidade"), unidade, "quantidade", errors)
        minima = self._quantity(data.get("quantidade_minima"), unidade, "quantidade_minima", errors)
        preco = self._decimal(data.get("preco_unitario"), "preco_unitario", errors, places=2, maximum=MAX_PRICE)

        if errors:
            raise ValidationError("Verifique os dados do produto.", errors)
        return {"nome": nome, "descricao": descricao, "quantidade": quantidade,
                "quantidade_minima": minima, "preco_unitario": preco, "unidade": unidade}

    def _quantity(self, value, unit, field, errors):
        number = self._decimal(value, field, errors, places=3, maximum=MAX_QUANTITY)
        if number is not None and unit == "un" and number != number.to_integral_value():
            errors[field] = "Produto em unidade (un) só aceita quantidade inteira."
        return number

    @staticmethod
    def _decimal(value, field, errors, places, maximum):
        """Número >= 0 com até `places` casas. Aceita número ou texto ("12.5" ou "12,5")."""
        if isinstance(value, bool) or value is None or value == "":
            errors[field] = "Informe um número."
            return None
        try:
            number = Decimal(str(value).strip().replace(",", "."))
        except InvalidOperation:
            errors[field] = "Informe um número."
            return None
        if not number.is_finite():
            errors[field] = "Informe um número."
        elif number < 0:
            errors[field] = "O valor não pode ser negativo."
        elif number > maximum:
            errors[field] = f"O valor máximo é {maximum}."
        elif number != number.quantize(Decimal(1).scaleb(-places)):
            errors[field] = f"Use no máximo {places} casas decimais."
        else:
            return number
        return None
