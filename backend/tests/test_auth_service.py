import pytest

from errors import ConflictError, UnauthorizedError, ValidationError
from tests.conftest import DOMAIN

VALID_CLIENT = {
    "nome": "Ana Paula Souza",
    "cpf": "529.982.247-25",
    "telefone": "(19) 99123-4567",
    "email": "Ana.Souza@gmail.com",
    "senha": "segredo1",
    "confirmar_senha": "segredo1",
}


def test_register_client_saves_clean_data_and_hashed_password(auth_service, users):
    created = auth_service.register_client(VALID_CLIENT)

    saved = users.find_by_id(created["id"])
    assert saved["cpf"] == "52998224725"
    assert saved["telefone"] == "19991234567"
    assert saved["email"] == "ana.souza@gmail.com"
    assert saved["perfil"] == "cliente"
    assert saved["senha_hash"] != "segredo1"


def test_register_client_returns_all_field_errors(auth_service):
    with pytest.raises(ValidationError) as exc:
        auth_service.register_client({"nome": "Ana", "cpf": "111", "telefone": "1",
                                      "email": "x", "senha": "123"})
    assert set(exc.value.details) == {"nome", "cpf", "telefone", "email", "senha"}


def test_register_client_requires_matching_passwords(auth_service):
    with pytest.raises(ValidationError) as exc:
        auth_service.register_client({**VALID_CLIENT, "confirmar_senha": "outra123"})
    assert "confirmar_senha" in exc.value.details


def test_register_client_blocks_salon_domain(auth_service):
    with pytest.raises(ValidationError) as exc:
        auth_service.register_client({**VALID_CLIENT, "email": f"ana@{DOMAIN}"})
    assert "email" in exc.value.details


def test_register_client_rejects_duplicate_email_and_cpf(auth_service):
    auth_service.register_client(VALID_CLIENT)

    with pytest.raises(ConflictError, match="E-mail"):
        auth_service.register_client({**VALID_CLIENT, "cpf": "11144477735"})
    with pytest.raises(ConflictError, match="CPF"):
        auth_service.register_client({**VALID_CLIENT, "email": "outra@gmail.com"})


def test_login_client_goes_to_client_area(auth_service):
    auth_service.register_client(VALID_CLIENT)

    result = auth_service.login("ana.souza@gmail.com", "segredo1")

    assert result["area"] == "cliente"
    assert result["usuario"]["perfil"] == "cliente"
    assert "senha_hash" not in result["usuario"]
    assert result["token"]


def test_login_salon_email_goes_to_internal_area(auth_service, manager):
    result = auth_service.login(f"MARIANA@{DOMAIN}", "Senha@123")
    assert result["area"] == "interna"


@pytest.mark.parametrize("email,senha", [
    ("ana.souza@gmail.com", "senha-errada"),
    ("ninguem@gmail.com", "segredo1"),
])
def test_login_with_wrong_credentials(auth_service, email, senha):
    auth_service.register_client(VALID_CLIENT)
    with pytest.raises(UnauthorizedError, match="E-mail ou senha inválidos"):
        auth_service.login(email, senha)


def test_login_blocks_inactive_user(auth_service, manager):
    manager["ativo"] = 0
    with pytest.raises(UnauthorizedError):
        auth_service.login(f"mariana@{DOMAIN}", "Senha@123")


def test_token_identifies_the_user(auth_service, manager):
    token = auth_service.login(f"mariana@{DOMAIN}", "Senha@123")["token"]
    assert auth_service.user_from_token(token)["id"] == manager["id"]


def test_tampered_token_is_rejected(auth_service, manager):
    token = auth_service.login(f"mariana@{DOMAIN}", "Senha@123")["token"]
    with pytest.raises(UnauthorizedError):
        auth_service.user_from_token(token[:-2] + "xx")
