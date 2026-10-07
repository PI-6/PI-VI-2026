from flask import current_app, request

from errors import ValidationError


def services():
    """Serviços (camada de regras) montados no create_app."""
    return current_app.extensions["services"]


def json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Envie os dados em JSON.")
    return data
