"""Geração e leitura do token de login.

Usamos o itsdangerous (já vem junto com o Flask) para assinar o id do usuário.
Funciona como um JWT simples: o front guarda o token e manda no header
Authorization: Bearer <token>. Se alguém alterar o conteúdo, a assinatura não bate.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from errors import UnauthorizedError


class TokenService:
    def __init__(self, secret_key, expiration_hours):
        if not secret_key:
            raise RuntimeError("SECRET_KEY não configurada. Veja o .env.example.")
        self._serializer = URLSafeTimedSerializer(secret_key, salt="login")
        self._max_age = expiration_hours * 3600

    def generate(self, user_id):
        return self._serializer.dumps({"id": user_id})

    def read_user_id(self, token):
        try:
            data = self._serializer.loads(token, max_age=self._max_age)
        except SignatureExpired:
            raise UnauthorizedError("Sua sessão expirou. Faça login novamente.")
        except BadSignature:
            raise UnauthorizedError("Token inválido.")
        return data["id"]
