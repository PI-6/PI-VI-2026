"""Testes das rotas: autenticação, permissões e formato das respostas."""
from types import SimpleNamespace

import pytest

from app import create_app
from tests.conftest import DOMAIN


@pytest.fixture
def client(auth_service, catalog_service, professional_service, appointment_service, users):
    users.add(nome="Mariana Duarte", email=f"mariana@{DOMAIN}", senha="Senha@123", perfil="gerente")
    users.add(nome="Camila Ferreira", email=f"camila@{DOMAIN}", senha="Senha@123", perfil="admin")
    users.add(nome="Ana Souza", email="ana@gmail.com", senha="Senha@123", perfil="cliente")

    app = create_app(SimpleNamespace(
        auth=auth_service, catalog=catalog_service, professionals=professional_service,
        appointments=appointment_service,
    ))
    return app.test_client()


def auth_header(client, email):
    response = client.post("/api/login", json={"email": email, "senha": "Senha@123"})
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


def test_login_returns_token_and_area(client):
    response = client.post("/api/login", json={"email": f"camila@{DOMAIN}", "senha": "Senha@123"})
    assert response.status_code == 200
    assert response.get_json()["area"] == "interna"


def test_register_returns_201(client):
    response = client.post("/api/cadastro", json={
        "nome": "Carlos Alves", "cpf": "11144477735", "telefone": "19998765432",
        "email": "carlos@gmail.com", "senha": "segredo1", "confirmar_senha": "segredo1",
    })
    assert response.status_code == 201


def test_validation_error_format(client):
    response = client.post("/api/cadastro", json={})
    body = response.get_json()
    assert response.status_code == 400
    assert body["erro"] and "cpf" in body["detalhes"]


def test_body_must_be_json(client):
    assert client.post("/api/login", data="texto").status_code == 400


def test_me_requires_login(client):
    assert client.get("/api/me").status_code == 401
    assert client.get("/api/me", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_services_list_is_public(client):
    response = client.get("/api/servicos")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


@pytest.mark.parametrize("email,expected_status", [
    ("ana@gmail.com", 403),
    (f"camila@{DOMAIN}", 403),
    (f"mariana@{DOMAIN}", 201),
])
def test_only_manager_creates_services(client, email, expected_status):
    response = client.post(
        "/api/servicos",
        json={"nome": "Escova", "duracao_minutos": 45, "preco": 60},
        headers=auth_header(client, email),
    )
    assert response.status_code == expected_status


def test_admin_can_list_professionals_but_client_cannot(client):
    assert client.get("/api/profissionais", headers=auth_header(client, f"camila@{DOMAIN}")).status_code == 200
    assert client.get("/api/profissionais", headers=auth_header(client, "ana@gmail.com")).status_code == 403


def test_professionals_by_service_requires_login(client):
    assert client.get("/api/servicos/1/profissionais").status_code == 401


@pytest.mark.parametrize("email", ["ana@gmail.com", f"camila@{DOMAIN}", f"mariana@{DOMAIN}"])
def test_any_logged_user_lists_professionals_by_service(client, email):
    response = client.get("/api/servicos/1/profissionais", headers=auth_header(client, email))
    assert response.status_code == 200
    assert response.get_json() == []


def test_client_sees_only_id_and_name_of_professionals(client):
    manager = auth_header(client, f"mariana@{DOMAIN}")
    created = client.post("/api/profissionais", headers=manager, json={
        "nome": "Juliana Rocha", "email": f"juliana@{DOMAIN}", "telefone": "19977776666",
        "senha": "juliana123", "perfil": "admin", "servicos": [1],
        "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"}],
    })
    assert created.status_code == 201

    response = client.get("/api/servicos/1/profissionais", headers=auth_header(client, "ana@gmail.com"))
    assert response.get_json() == [{"id": 1, "nome": "Juliana Rocha"}]
    assert client.get("/api/servicos/2/profissionais", headers=manager).get_json() == []


def test_professionals_by_unknown_service_returns_404(client):
    response = client.get("/api/servicos/99/profissionais", headers=auth_header(client, "ana@gmail.com"))
    assert response.status_code == 404


def test_availability_requires_login(client):
    assert client.get("/api/profissionais/1/disponibilidade?data=2026-10-20&servico_id=1").status_code == 401


def test_client_sees_availability(client):
    manager = auth_header(client, f"mariana@{DOMAIN}")
    created = client.post("/api/profissionais", headers=manager, json={
        "nome": "Juliana Rocha", "email": f"juliana@{DOMAIN}", "senha": "juliana123", "perfil": "admin",
        "servicos": [1], "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "12:00"}],
    }).get_json()

    response = client.get(
        f"/api/profissionais/{created['id']}/disponibilidade?data=2026-10-20&servico_id=1",
        headers=auth_header(client, "ana@gmail.com"),
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["horarios"][0] == {"hora": "09:00", "status": "livre"}
    assert body["horarios"][-1]["hora"] == "11:00"


def test_availability_with_invalid_date_returns_400(client):
    response = client.get("/api/profissionais/1/disponibilidade?data=amanha&servico_id=1",
                          headers=auth_header(client, "ana@gmail.com"))
    assert response.status_code == 400
    assert "data" in response.get_json()["detalhes"]


def _create_juliana(client):
    return client.post("/api/profissionais", headers=auth_header(client, f"mariana@{DOMAIN}"), json={
        "nome": "Juliana Rocha", "email": f"juliana@{DOMAIN}", "senha": "juliana123", "perfil": "admin",
        "servicos": [1], "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "12:00"}],
    }).get_json()["id"]


def test_booking_requires_login(client):
    assert client.post("/api/agendamentos", json={}).status_code == 401


@pytest.mark.parametrize("email", [f"camila@{DOMAIN}", f"mariana@{DOMAIN}"])
def test_staff_cannot_book_through_the_site(client, email):
    response = client.post("/api/agendamentos", json={}, headers=auth_header(client, email))
    assert response.status_code == 403


def test_client_books_and_second_booking_conflicts(client):
    booking = {"profissional_id": _create_juliana(client), "servico_id": 1, "data": "2026-10-20", "hora": "10:00"}
    headers = auth_header(client, "ana@gmail.com")

    first = client.post("/api/agendamentos", json=booking, headers=headers)
    assert first.status_code == 201
    assert first.get_json()["hora_fim"] == "11:00"

    second = client.post("/api/agendamentos", json={**booking, "hora": "10:30"}, headers=headers)
    assert second.status_code == 409


def test_delete_service_returns_204(client):
    headers = auth_header(client, f"mariana@{DOMAIN}")
    assert client.delete("/api/servicos/1", headers=headers).status_code == 204
    assert client.get("/api/servicos/1").status_code == 404


def test_unknown_route_returns_json(client):
    response = client.get("/api/nao-existe")
    assert response.status_code == 404
    assert response.get_json()["erro"] == "Recurso não encontrado."
