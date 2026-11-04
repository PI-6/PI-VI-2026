"""Financeiro / BI (RF10). Menu exclusivo do gerente."""
from flask import Blueprint, jsonify, request

from routes.guards import role_required
from routes.helpers import services

bp = Blueprint("finance", __name__, url_prefix="/api/financeiro")


# Receita mês a mês do ano, com a variação em relação ao mês anterior (#30)
@bp.get("/receita-mensal")
@role_required("gerente")
def monthly_revenue():
    return jsonify(services().finance.monthly_revenue(request.args.get("ano")))


# Ranking de profissionais no período (#31): ?periodo=semana|mes|ano&data=AAAA-MM-DD
@bp.get("/atendimentos-por-profissional")
@role_required("gerente")
def professional_ranking():
    return jsonify(services().finance.professional_ranking(request.args.get("periodo"), request.args.get("data")))
