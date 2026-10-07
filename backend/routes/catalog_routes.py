from flask import Blueprint, jsonify

from routes.guards import role_required
from routes.helpers import json_body, services

bp = Blueprint("catalog", __name__, url_prefix="/api/servicos")


# Listagem é pública: o cliente escolhe o serviço antes de agendar
@bp.get("")
def list_services():
    return jsonify(services().catalog.list_services())


@bp.get("/<int:service_id>")
def get_service(service_id):
    return jsonify(services().catalog.get_service(service_id))


@bp.post("")
@role_required("gerente")
def create_service():
    return jsonify(services().catalog.create_service(json_body())), 201


@bp.put("/<int:service_id>")
@role_required("gerente")
def update_service(service_id):
    return jsonify(services().catalog.update_service(service_id, json_body()))


@bp.delete("/<int:service_id>")
@role_required("gerente")
def delete_service(service_id):
    services().catalog.delete_service(service_id)
    return "", 204
