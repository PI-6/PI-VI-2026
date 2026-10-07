"""Regras do cadastro de serviços do salão (RF07)."""
from decimal import Decimal, InvalidOperation

from errors import ConflictError, NotFoundError, ValidationError
from services import validators as v

MAX_DURATION_MINUTES = 8 * 60


class CatalogService:
    def __init__(self, catalog_repository):
        self.catalog = catalog_repository

    def list_services(self):
        return self.catalog.list_active()

    def get_service(self, service_id):
        service = self.catalog.find_active_by_id(service_id)
        if not service:
            raise NotFoundError("Serviço não encontrado.")
        return service

    def create_service(self, data):
        fields = self._validate(data)
        self._ensure_unique_name(fields["nome"])
        service_id = self.catalog.create(**fields)
        return self.catalog.find_active_by_id(service_id)

    def update_service(self, service_id, data):
        self.get_service(service_id)
        fields = self._validate(data)
        self._ensure_unique_name(fields["nome"], ignore_id=service_id)
        self.catalog.update(service_id, **fields)
        return self.catalog.find_active_by_id(service_id)

    def delete_service(self, service_id):
        self.get_service(service_id)
        # Exclusão lógica: agendamentos antigos continuam apontando para o serviço
        self.catalog.deactivate(service_id)

    def _ensure_unique_name(self, nome, ignore_id=None):
        existing = self.catalog.find_active_by_name(nome)
        if existing and existing["id"] != ignore_id:
            raise ConflictError("Já existe um serviço com esse nome.")

    def _validate(self, data):
        nome = v.clean_text(data.get("nome"))
        descricao = v.clean_text(data.get("descricao")) or None
        duracao = data.get("duracao_minutos")
        preco = data.get("preco")

        errors = {}
        if not 2 <= len(nome) <= 100:
            errors["nome"] = "Informe um nome entre 2 e 100 caracteres."
        if descricao and len(descricao) > 500:
            errors["descricao"] = "A descrição pode ter no máximo 500 caracteres."

        # bool é subclasse de int no Python, por isso a checagem extra
        if not isinstance(duracao, int) or isinstance(duracao, bool) \
                or not 1 <= duracao <= MAX_DURATION_MINUTES:
            errors["duracao_minutos"] = f"Informe a duração em minutos (1 a {MAX_DURATION_MINUTES})."

        try:
            preco = Decimal(str(preco)).quantize(Decimal("0.01"))
            if preco < 0 or preco >= Decimal("100000"):
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors["preco"] = "Informe um preço válido (ex.: 59.90)."

        if errors:
            raise ValidationError("Verifique os dados do serviço.", errors)
        return {"nome": nome, "descricao": descricao, "duracao_minutos": duracao, "preco": preco}
