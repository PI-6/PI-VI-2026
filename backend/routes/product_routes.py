"""Estoque (RF09). Menu exclusivo do gerente; o admin vê só o alerta no Dashboard."""
from flask import Blueprint, jsonify, request

from routes.guards import role_required
from routes.helpers import json_body, services

bp = Blueprint("products", __name__, url_prefix="/api/produtos")


# ?estoque_baixo=1 traz só os produtos com quantidade <= quantidade mínima
@bp.get("")
@role_required("gerente")
def list_products():
    low_stock_only = request.args.get("estoque_baixo", "").lower() in ("1", "true", "sim")
    return jsonify(services().products.list_products(low_stock_only))


@bp.get("/<int:product_id>")
@role_required("gerente")
def get_product(product_id):
    return jsonify(services().products.get_product(product_id))


@bp.post("")
@role_required("gerente")
def create_product():
    return jsonify(services().products.create_product(json_body())), 201


# PUT substitui o cadastro inteiro: envie todos os campos
@bp.put("/<int:product_id>")
@role_required("gerente")
def update_product(product_id):
    return jsonify(services().products.update_product(product_id, json_body()))
