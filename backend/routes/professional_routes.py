from flask import Blueprint, g, jsonify, request

from routes.guards import login_required, role_required
from routes.helpers import json_body, services

bp = Blueprint("professionals", __name__, url_prefix="/api/profissionais")


# O admin também consulta (ex.: agenda e bloqueios), mas só o gerente altera
@bp.get("")
@role_required("admin")
def list_professionals():
    return jsonify(services().professionals.list_professionals())


@bp.get("/<int:professional_id>")
@role_required("admin")
def get_professional(professional_id):
    return jsonify(services().professionals.get_professional(professional_id))


# Etapa 3 do agendamento: qualquer usuário logado vê os horários livres e ocupados
@bp.get("/<int:professional_id>/disponibilidade")
@login_required
def availability(professional_id):
    return jsonify(services().appointments.availability(
        professional_id, request.args.get("data"), request.args.get("servico_id")
    ))


@bp.post("")
@role_required("gerente")
def create_professional():
    return jsonify(services().professionals.create_professional(json_body())), 201


@bp.put("/<int:professional_id>")
@role_required("gerente")
def update_professional(professional_id):
    professional = services().professionals.update_professional(
        professional_id, json_body(), g.current_user
    )
    return jsonify(professional)


@bp.delete("/<int:professional_id>")
@role_required("gerente")
def delete_professional(professional_id):
    services().professionals.delete_professional(professional_id, g.current_user)
    return "", 204
