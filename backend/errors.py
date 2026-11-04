"""Erros de negócio que a API sabe transformar em resposta HTTP.

Os serviços lançam essas exceções e o app.py converte em JSON com o status certo,
assim nenhuma regra de negócio precisa conhecer o Flask.
"""


class AppError(Exception):
    status_code = 400

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self):
        body = {"erro": self.message}
        if self.details:
            body["detalhes"] = self.details
        return body


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
