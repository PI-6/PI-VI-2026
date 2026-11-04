"""Dashboard da área interna (RF05): admin e gerente."""
from flask import Blueprint, g, jsonify

from routes.guards import role_required
from routes.helpers import services

bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


# Dados do funcionário logado: agenda e receita de hoje e do mês, mais o alerta de estoque baixo
@bp.get("")
@role_required("admin")
def dashboard():
    return jsonify(services().dashboard.for_user(g.current_user))
