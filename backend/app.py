import logging
from types import SimpleNamespace

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import Config
from errors import AppError
from routes import auth_routes, catalog_routes, professional_routes

HTTP_MESSAGES = {
    404: "Recurso não encontrado.",
    405: "Método não permitido para esta rota.",
    415: "Envie os dados em JSON.",
}


def build_services(config):
    """Liga cada serviço aos repositórios reais (MySQL)."""
    # Import aqui dentro para os testes conseguirem criar o app sem precisar do banco
    from repositories import catalog_repository, professional_repository, user_repository
    from services.auth_service import AuthService
    from services.catalog_service import CatalogService
    from services.professional_service import ProfessionalService
    from services.token_service import TokenService

    tokens = TokenService(config.SECRET_KEY, config.TOKEN_EXPIRATION_HOURS)
    return SimpleNamespace(
        auth=AuthService(user_repository, tokens, config.SALON_EMAIL_DOMAIN),
        catalog=CatalogService(catalog_repository),
        professionals=ProfessionalService(
            professional_repository, user_repository, catalog_repository, config.SALON_EMAIL_DOMAIN
        ),
    )


def create_app(services=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False  # mantém acentos legíveis nas respostas
    CORS(app)

    app.extensions["services"] = services or build_services(Config)

    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(catalog_routes.bp)
    app.register_blueprint(professional_routes.bp)

    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        # 404 de rota inexistente, 405 de método errado etc. também em JSON
        return jsonify({"erro": HTTP_MESSAGES.get(error.code, error.description)}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Loga só o tipo do erro e o traceback; nunca o corpo da requisição (pode ter CPF/telefone)
        logging.exception("Erro inesperado: %s", type(error).__name__)
        return jsonify({"erro": "Erro interno no servidor."}), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
