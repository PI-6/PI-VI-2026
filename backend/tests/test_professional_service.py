import pytest

from errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from tests.conftest import DOMAIN


def new_professional(**changes):
    data = {
        "nome": "Camila Ferreira",
        "email": f"camila@{DOMAIN}",
        "telefone": "19 98888-7777",
        "senha": "camila123",
        "perfil": "admin",
        "servicos": [1, 2],
        "horarios": [
            {"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"},
            {"dia_semana": 5, "hora_inicio": "08:00", "hora_fim": "12:00"},
        ],
    }
    data.update(changes)
    return data


def test_create_professional(professional_service, users):
    created = professional_service.create_professional(new_professional())

    assert created["perfil"] == "admin"
    assert created["telefone"] == "19988887777"
    assert [s["id"] for s in created["servicos"]] == [1, 2]
    assert users.find_by_email(f"camila@{DOMAIN}")["senha_hash"] != "camila123"


def test_professional_needs_salon_email(professional_service):
    with pytest.raises(ValidationError) as exc:
        professional_service.create_professional(new_professional(email="camila@gmail.com"))
    assert "email" in exc.value.details


def test_professional_cannot_be_client(professional_service):
    with pytest.raises(ValidationError) as exc:
        professional_service.create_professional(new_professional(perfil="cliente"))
    assert "perfil" in exc.value.details


def test_professional_services_must_exist(professional_service):
    with pytest.raises(ValidationError) as exc:
        professional_service.create_professional(new_professional(servicos=[1, 99]))
    assert "99" in exc.value.details["servicos"]


@pytest.mark.parametrize("hours", [
    [],
    [{"dia_semana": 7, "hora_inicio": "09:00", "hora_fim": "18:00"}],
    [{"dia_semana": 1, "hora_inicio": "18:00", "hora_fim": "09:00"}],
    [{"dia_semana": 1, "hora_inicio": "9h", "hora_fim": "18:00"}],
    [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "12:00"},
     {"dia_semana": 1, "hora_inicio": "13:00", "hora_fim": "18:00"}],
])
def test_invalid_work_hours(professional_service, hours):
    with pytest.raises(ValidationError) as exc:
        professional_service.create_professional(new_professional(horarios=hours))
    assert "horarios" in exc.value.details


def test_create_requires_password(professional_service):
    with pytest.raises(ValidationError) as exc:
        professional_service.create_professional(new_professional(senha=""))
    assert "senha" in exc.value.details


def test_duplicate_email(professional_service, manager):
    with pytest.raises(ConflictError):
        professional_service.create_professional(new_professional(email=manager["email"]))


def test_update_without_password_keeps_old_one(professional_service, users, manager):
    created = professional_service.create_professional(new_professional())
    old_hash = users.find_by_email(f"camila@{DOMAIN}")["senha_hash"]

    professional_service.update_professional(
        created["id"], new_professional(senha="", perfil="gerente"), manager
    )

    user = users.find_by_email(f"camila@{DOMAIN}")
    assert user["perfil"] == "gerente"
    assert user["senha_hash"] == old_hash


def test_manager_cannot_remove_own_access(professional_service, professionals, manager):
    own_id = professionals.link(manager["id"], [1])

    with pytest.raises(ForbiddenError):
        professional_service.update_professional(
            own_id, new_professional(email=manager["email"], perfil="admin"), manager
        )
    with pytest.raises(ForbiddenError):
        professional_service.delete_professional(own_id, manager)


def test_delete_professional(professional_service, manager):
    created = professional_service.create_professional(new_professional())

    professional_service.delete_professional(created["id"], manager)

    assert professional_service.list_professionals() == []
    with pytest.raises(NotFoundError):
        professional_service.get_professional(created["id"])
