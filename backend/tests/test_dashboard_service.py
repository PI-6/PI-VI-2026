"""Dashboard do funcionário (RF05, issue #69).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). Receita = atendimentos realizados
(não cancelados e já terminados), só os do funcionário logado.
"""
from datetime import datetime, timedelta

import pytest


def at(text):
    return datetime.fromisoformat(text)


@pytest.fixture
def camila(users, professionals):
    user = users.add(nome="Camila Ferreira", email="camila@salaobelle.com.br", senha="Senha@123", perfil="admin")
    return user, professionals.link(user["id"], [1])


@pytest.fixture
def juliana(users, professionals):
    user = users.add(nome="Juliana Rocha", email="juliana@salaobelle.com.br", senha="Senha@123", perfil="admin")
    return user, professionals.link(user["id"], [2])


@pytest.fixture
def ana(users):
    return users.add(nome="Ana Souza", email="ana@gmail.com", senha="Senha@123", perfil="cliente")


@pytest.fixture
def book(appointments, ana):
    def add(professional_id, start, valor, minutes=60, status="agendado", servico_id=1):
        begin = at(start)
        return appointments.add(professional_id, begin, begin + timedelta(minutes=minutes), status=status,
                                valor=valor, servico_id=servico_id, cliente_id=ana["id"])
    return add


def test_dashboard_of_the_logged_professional(dashboard_service, camila, juliana, ana, book):
    camila_user, camila_id = camila
    _, juliana_id = juliana
    book(camila_id, "2026-10-19T09:00", 90)                        # realizado
    book(camila_id, "2026-10-19T11:30", 90)                        # em andamento às 12h
    book(camila_id, "2026-10-19T15:00", 90)                        # a seguir
    book(camila_id, "2026-10-19T16:00", 90, status="cancelado")    # não aparece
    book(camila_id, "2026-10-05T10:00", 50)                        # outro dia do mês
    book(camila_id, "2026-09-30T10:00", 999)                       # mês anterior
    book(juliana_id, "2026-10-19T09:00", 35, servico_id=2)         # outra profissional

    result = dashboard_service.for_user(camila_user)

    assert result["data"] == "2026-10-19"
    assert result["profissional"] == {"id": camila_id, "nome": "Camila Ferreira"}
    assert result["agendamentos_hoje"] == {"total": 3, "realizados": 1, "a_seguir": 2}
    assert result["receita"] == {"dia": 90.0, "dia_prevista": 270.0, "mes": 140.0, "mes_atendimentos": 2}
    assert [(a["hora_inicio"], a["situacao"]) for a in result["agenda_hoje"]] == [
        ("09:00", "realizado"), ("11:30", "em_andamento"), ("15:00", "a_seguir")]
    assert result["agenda_hoje"][0]["cliente"] == {"id": ana["id"], "nome": "Ana Souza"}
    assert result["agenda_hoje"][0]["servico"] == {"id": 1, "nome": "Corte feminino"}


def test_dashboard_without_appointments(dashboard_service, camila):
    result = dashboard_service.for_user(camila[0])

    assert result["agendamentos_hoje"] == {"total": 0, "realizados": 0, "a_seguir": 0}
    assert result["receita"] == {"dia": 0.0, "dia_prevista": 0.0, "mes": 0.0, "mes_atendimentos": 0}
    assert result["agenda_hoje"] == []


def test_manager_who_does_not_attend_sees_only_stock_alert(dashboard_service, manager, products):
    products.add("Lixa de unha", 3, 20)

    result = dashboard_service.for_user(manager)

    assert result["profissional"] is None
    assert result["agenda_hoje"] == [] and result["receita"]["mes"] == 0.0
    assert result["estoque_baixo"]["total"] == 1


def test_stock_alert_has_at_most_three_products(dashboard_service, camila, products):
    for name, quantity in [("A", 5), ("B", 1), ("C", 0), ("D", 3), ("E", 50)]:
        products.add(name, quantity, 10)

    alert = dashboard_service.for_user(camila[0])["estoque_baixo"]

    assert alert["total"] == 4
    assert [p["nome"] for p in alert["produtos"]] == ["C", "B", "D"]
