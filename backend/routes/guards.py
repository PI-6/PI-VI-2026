"""Decorators de autenticação e autorização das rotas.

Uso:
    @login_required            -> qualquer usuário logado
    @role_required("admin")    -> admin ou gerente (o gerente herda o admin)
    @role_required("gerente")  -> só gerente

O usuário logado fica disponível em flask.g.current_user.
"""
from functools import wraps

from flask import g, request

from errors import ForbiddenError, UnauthorizedError
from routes.helpers import services
from services.auth_service import has_role


def _authenticate():
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Faça login para continuar.")
    g.current_user = services().auth.user_from_token(token.strip())


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        _authenticate()
        return view(*args, **kwargs)
    return wrapper


def role_required(minimum_role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            _authenticate()
            if not has_role(g.current_user, minimum_role):
                raise ForbiddenError("Você não tem permissão para acessar este recurso.")
            return view(*args, **kwargs)
        return wrapper
    return decorator
