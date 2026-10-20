from datetime import datetime

import pytest

from services.appointment_service import AppointmentService
from services.auth_service import AuthService
from services.catalog_service import CatalogService
from services.professional_service import ProfessionalService
from services.token_service import TokenService
from tests.fakes import (
    FakeAppointmentRepository, FakeCatalogRepository, FakeProfessionalRepository, FakeUserRepository
)

DOMAIN = "salaobelle.com.br"

# "Agora" nos testes: segunda-feira, 19/10/2026, 12h
NOW = datetime(2026, 10, 19, 12, 0)


@pytest.fixture
def users():
    return FakeUserRepository()


@pytest.fixture
def catalog():
    repo = FakeCatalogRepository()
    repo.add("Corte feminino", 60, 90.0)
    repo.add("Manicure", 40, 35.0)
    return repo


@pytest.fixture
def professionals(users):
    return FakeProfessionalRepository(users)


@pytest.fixture
def tokens():
    return TokenService("chave-de-teste", expiration_hours=1)


@pytest.fixture
def auth_service(users, tokens):
    return AuthService(users, tokens, DOMAIN)


@pytest.fixture
def catalog_service(catalog):
    return CatalogService(catalog)


@pytest.fixture
def professional_service(professionals, users, catalog):
    return ProfessionalService(professionals, users, catalog, DOMAIN)


@pytest.fixture
def manager(users):
    return users.add(nome="Mariana Duarte", email=f"mariana@{DOMAIN}", senha="Senha@123", perfil="gerente")


@pytest.fixture
def appointments():
    return FakeAppointmentRepository()


@pytest.fixture
def appointment_service(appointments, professionals, catalog):
    return AppointmentService(appointments, professionals, catalog, clock=lambda: NOW)
