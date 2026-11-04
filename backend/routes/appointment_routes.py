from flask import Blueprint, g, jsonify, request

from routes.guards import client_required, role_required
from routes.helpers import json_body, services

bp = Blueprint("appointments", __name__, url_prefix="/api/agendamentos")


# Etapa 4 do agendamento: o cliente confirma. A equipe não agenda por esta rota.
@bp.post("")
@client_required
def create_appointment():
    return jsonify(services().appointments.create(g.current_user, json_body())), 201


# Agenda do dia (RF06): ?data=AAAA-MM-DD e, se quiser, &profissional_id=N
@bp.get("")
@role_required("admin")
def day_schedule():
    return jsonify(services().appointments.day_schedule(
        request.args.get("data"), request.args.get("profissional_id")
    ))


# Excluir agendamento pela agenda (RF06): vira cancelado e libera o horário
@bp.delete("/<int:appointment_id>")
@role_required("admin")
def cancel_appointment(appointment_id):
    services().appointments.cancel(appointment_id, g.current_user)
    return "", 204
