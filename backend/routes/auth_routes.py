from flask import Blueprint, g, jsonify

from routes.guards import login_required
from routes.helpers import json_body, services
from services.auth_service import public_user

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.get("/teste")
def health_check():
    return jsonify({"mensagem": "Conexão bem-sucedida! O Front e o Back estão conversando."})


@bp.post("/cadastro")
def register():
    user = services().auth.register_client(json_body())
    return jsonify({"mensagem": "Cadastro realizado com sucesso.", "usuario": user}), 201


@bp.post("/login")
def login():
    data = json_body()
    return jsonify(services().auth.login(data.get("email"), data.get("senha")))


@bp.get("/me")
@login_required
def me():
    user = g.current_user
    return jsonify({"usuario": public_user(user), "area": services().auth.area_for(user)})
