"""Regras do cadastro de profissionais (RF08).

Todo profissional é também um usuário da equipe: faz login com o e-mail do salão
e tem nível de acesso admin ou gerente.
"""
from werkzeug.security import generate_password_hash

from errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from services import validators as v
from services.auth_service import MIN_PASSWORD_LENGTH

STAFF_ROLES = ("admin", "gerente")


class ProfessionalService:
    def __init__(self, professional_repository, user_repository, catalog_repository, salon_domain):
        self.professionals = professional_repository
        self.users = user_repository
        self.catalog = catalog_repository
        self.salon_domain = salon_domain

    def list_professionals(self):
        return self.professionals.list_active()

    def get_professional(self, professional_id):
        professional = self.professionals.find_active_by_id(professional_id)
        if not professional:
            raise NotFoundError("Profissional não encontrado.")
        return professional

    def create_professional(self, data):
        user, service_ids, hours = self._validate(data, password_required=True)
        self._ensure_unique(user)
        professional_id = self.professionals.create(user, service_ids, hours)
        return self.professionals.find_active_by_id(professional_id)

    def update_professional(self, professional_id, data, current_user):
        current = self.get_professional(professional_id)
        user, service_ids, hours = self._validate(data, password_required=False)

        # Evita que o gerente tire o próprio acesso e fique sem ninguém para gerenciar
        if current["usuario_id"] == current_user["id"] and user["perfil"] != "gerente":
            raise ForbiddenError("Você não pode remover o seu próprio acesso de gerente.")

        self._ensure_unique(user, ignore_user_id=current["usuario_id"])
        self.professionals.update(professional_id, user, service_ids, hours)
        return self.professionals.find_active_by_id(professional_id)

    def delete_professional(self, professional_id, current_user):
        professional = self.get_professional(professional_id)
        if professional["usuario_id"] == current_user["id"]:
            raise ForbiddenError("Você não pode excluir o seu próprio cadastro.")
        self.professionals.deactivate(professional_id)

    def _ensure_unique(self, user, ignore_user_id=None):
        same_email = self.users.find_by_email(user["email"])
        if same_email and same_email["id"] != ignore_user_id:
            raise ConflictError("E-mail já cadastrado.")
        if user["cpf"]:
            same_cpf = self.users.find_by_cpf(user["cpf"])
            if same_cpf and same_cpf["id"] != ignore_user_id:
                raise ConflictError("CPF já cadastrado.")

    def _validate(self, data, password_required):
        nome = v.clean_text(data.get("nome"))
        email = v.clean_text(data.get("email")).lower()
        telefone = v.only_digits(data.get("telefone")) or None
        cpf = v.only_digits(data.get("cpf")) or None
        senha = data.get("senha") or ""
        perfil = data.get("perfil")

        errors = {}
        if len(nome.split()) < 2:
            errors["nome"] = "Informe o nome completo."
        if not v.is_valid_email(email):
            errors["email"] = "E-mail inválido."
        elif v.email_domain(email) != self.salon_domain:
            errors["email"] = f"Profissionais usam o e-mail do salão (@{self.salon_domain})."
        if telefone and not v.is_valid_phone(telefone):
            errors["telefone"] = "Telefone inválido. Use DDD + número."
        if cpf and not v.is_valid_cpf(cpf):
            errors["cpf"] = "CPF inválido."
        if perfil not in STAFF_ROLES:
            errors["perfil"] = "O nível de acesso deve ser admin ou gerente."
        if password_required or senha:
            if len(senha) < MIN_PASSWORD_LENGTH:
                errors["senha"] = f"A senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres."

        service_ids = self._validate_service_ids(data.get("servicos"), errors)
        hours = self._validate_hours(data.get("horarios"), errors)

        if errors:
            raise ValidationError("Verifique os dados do profissional.", errors)

        user = {
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "cpf": cpf,
            "perfil": perfil,
            "senha_hash": generate_password_hash(senha) if senha else None,
        }
        return user, service_ids, hours

    def _validate_service_ids(self, value, errors):
        if not isinstance(value, list) or not value:
            errors["servicos"] = "Selecione pelo menos um serviço."
            return []
        if not all(isinstance(i, int) and not isinstance(i, bool) for i in value):
            errors["servicos"] = "Lista de serviços inválida."
            return []

        service_ids = sorted(set(value))
        missing = set(service_ids) - self.catalog.find_active_ids(service_ids)
        if missing:
            errors["servicos"] = f"Serviços não encontrados: {sorted(missing)}."
        return service_ids

    def _validate_hours(self, value, errors):
        if not isinstance(value, list) or not value:
            errors["horarios"] = "Informe pelo menos um dia de trabalho."
            return []

        hours, days_seen = [], set()
        for item in value:
            item = item if isinstance(item, dict) else {}
            day = item.get("dia_semana")
            start = v.parse_time(item.get("hora_inicio"))
            end = v.parse_time(item.get("hora_fim"))

            if not isinstance(day, int) or isinstance(day, bool) or not 0 <= day <= 6:
                errors["horarios"] = "dia_semana deve ser de 0 (segunda) a 6 (domingo)."
            elif day in days_seen:
                errors["horarios"] = "Cada dia da semana só pode aparecer uma vez."
            elif not start or not end:
                errors["horarios"] = "Use o formato HH:MM nos horários."
            elif end <= start:
                errors["horarios"] = "O horário de fim deve ser depois do início."
            else:
                days_seen.add(day)
                hours.append({"dia_semana": day, "hora_inicio": start, "hora_fim": end})
                continue
            break  # já achou um erro, não precisa olhar o resto
        return hours
