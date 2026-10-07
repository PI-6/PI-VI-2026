from werkzeug.security import check_password_hash, generate_password_hash

from errors import ConflictError, UnauthorizedError, ValidationError
from services import validators as v

MIN_PASSWORD_LENGTH = 6

# Quanto maior o nível, mais acesso. O gerente herda tudo do admin.
ROLE_LEVEL = {"cliente": 0, "admin": 1, "gerente": 2}


def has_role(user, minimum_role):
    return ROLE_LEVEL[user["perfil"]] >= ROLE_LEVEL[minimum_role]


def public_user(user):
    """Dados do usuário que podem ir para o front (sem hash de senha, CPF etc.)."""
    return {
        "id": user["id"],
        "nome": user["nome"],
        "email": user["email"],
        "perfil": user["perfil"],
    }


class AuthService:
    def __init__(self, user_repository, token_service, salon_domain):
        self.users = user_repository
        self.tokens = token_service
        self.salon_domain = salon_domain

    def register_client(self, data):
        nome = v.clean_text(data.get("nome"))
        cpf = v.only_digits(data.get("cpf"))
        telefone = v.only_digits(data.get("telefone"))
        email = v.clean_text(data.get("email")).lower()
        senha = data.get("senha") or ""
        confirmar_senha = data.get("confirmar_senha") or ""

        errors = {}
        if len(nome.split()) < 2:
            errors["nome"] = "Informe o nome completo."
        if not v.is_valid_cpf(cpf):
            errors["cpf"] = "CPF inválido."
        if not v.is_valid_phone(telefone):
            errors["telefone"] = "Telefone inválido. Use DDD + número."
        if not v.is_valid_email(email):
            errors["email"] = "E-mail inválido."
        elif v.email_domain(email) == self.salon_domain:
            # Contas da equipe são criadas pelo gerente, não pelo cadastro público
            errors["email"] = "Este domínio é reservado para a equipe do salão."
        if len(senha) < MIN_PASSWORD_LENGTH:
            errors["senha"] = f"A senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres."
        elif senha != confirmar_senha:
            errors["confirmar_senha"] = "As senhas não conferem."
        if errors:
            raise ValidationError("Verifique os campos do cadastro.", errors)

        if self.users.find_by_email(email):
            raise ConflictError("E-mail já cadastrado.")
        if self.users.find_by_cpf(cpf):
            raise ConflictError("CPF já cadastrado.")

        user_id = self.users.create_client(nome, cpf, telefone, email, generate_password_hash(senha))
        return {"id": user_id, "nome": nome, "email": email, "perfil": "cliente"}

    def login(self, email, senha):
        email = v.clean_text(email).lower()
        if not email or not senha:
            raise ValidationError("Informe e-mail e senha.")

        user = self.users.find_by_email(email)
        # Mesma mensagem para e-mail inexistente e senha errada, para não revelar quem tem conta
        if not user or not user["ativo"] or not check_password_hash(user["senha_hash"], senha):
            raise UnauthorizedError("E-mail ou senha inválidos.")

        return {
            "token": self.tokens.generate(user["id"]),
            "usuario": public_user(user),
            "area": self.area_for(user),
        }

    def area_for(self, user):
        # Regra do RF03: e-mail do domínio do salão vai para a área interna
        if v.email_domain(user["email"]) == self.salon_domain and has_role(user, "admin"):
            return "interna"
        return "cliente"

    def user_from_token(self, token):
        user_id = self.tokens.read_user_id(token)
        user = self.users.find_by_id(user_id)
        if not user or not user["ativo"]:
            raise UnauthorizedError("Usuário não encontrado ou desativado.")
        return user
