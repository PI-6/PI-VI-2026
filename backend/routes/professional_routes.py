from flask import Blueprint, g, jsonify

from routes.guards import role_required
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
