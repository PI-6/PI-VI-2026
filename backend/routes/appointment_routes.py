from flask import Blueprint, g, jsonify

from routes.guards import client_required
from routes.helpers import json_body, services

bp = Blueprint("appointments", __name__, url_prefix="/api/agendamentos")


# Etapa 4 do agendamento: o cliente confirma. A equipe não agenda por esta rota.
@bp.post("")
@client_required
def create_appointment():
    return jsonify(services().appointments.create(g.current_user, json_body())), 201
