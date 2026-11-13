import pytest

from errors import ConflictError, NotFoundError, ValidationError

NEW_SERVICE = {"nome": "Hidratação", "descricao": "Hidratação capilar", "duracao_minutos": 40, "preco": "69.90"}


def test_create_service(catalog_service):
    created = catalog_service.create_service(NEW_SERVICE)
    assert created["nome"] == "Hidratação"
    assert created["preco"] == 69.9


def test_create_service_with_duplicate_name(catalog_service):
    with pytest.raises(ConflictError):
        catalog_service.create_service({**NEW_SERVICE, "nome": "Manicure"})


@pytest.mark.parametrize("field,value", [
    ("nome", "H"),
    ("duracao_minutos", 0),
    ("duracao_minutos", "40"),
    ("duracao_minutos", True),
    ("preco", -1),
    ("preco", "abc"),
    ("preco", None),
])
def test_create_service_validation(catalog_service, field, value):
    with pytest.raises(ValidationError) as exc:
        catalog_service.create_service({**NEW_SERVICE, field: value})
    assert field in exc.value.details


def test_update_service_keeps_own_name(catalog_service):
    updated = catalog_service.update_service(1, {"nome": "Corte feminino", "duracao_minutos": 75, "preco": 100})
    assert updated["duracao_minutos"] == 75


def test_update_missing_service(catalog_service):
    with pytest.raises(NotFoundError):
        catalog_service.update_service(99, NEW_SERVICE)


def test_deleted_service_disappears_from_list(catalog_service):
    catalog_service.delete_service(2)

    assert [s["nome"] for s in catalog_service.list_services()] == ["Corte feminino"]
    with pytest.raises(NotFoundError):
        catalog_service.get_service(2)
