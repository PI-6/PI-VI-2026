"""Financeiro / BI (RF10).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). Atendimento realizado = agendamento
não cancelado cujo horário já terminou (decisão do time, 03/11).
"""
from datetime import date, datetime, timedelta

import pytest

from errors import ValidationError
from services.finance_service import period_range


def at(text):
    return datetime.fromisoformat(text)


@pytest.fixture
def book(appointments):
    """Atalho para criar agendamentos de 1 hora direto no repositório em memória."""
    def add(start, valor, status="agendado", profissional_id=1, servico_id=1, cliente_id=10):
        begin = at(start)
        return appointments.add(profissional_id, begin, begin + timedelta(hours=1), status=status,
                                valor=valor, servico_id=servico_id, cliente_id=cliente_id)
    return add


# --- receita mensal comparada (#30) --------------------------------------------------------

def test_monthly_revenue_has_twelve_months_with_zeros(finance_service):
    result = finance_service.monthly_revenue("2026")

    assert result["ano"] == 2026
    assert [m["mes"] for m in result["meses"]] == list(range(1, 13))
    assert result["meses"][0] == {"mes": 1, "nome": "jan", "receita": 0.0, "atendimentos": 0,
                                  "situacao": "fechado", "variacao_percentual": None}
    assert result["total"] == {"receita": 0.0, "atendimentos": 0}


def test_monthly_revenue_sums_realized_appointments(finance_service, book):
    book("2026-09-10T10:00", 90)
    book("2026-09-11T10:00", 35.5)
    book("2026-10-05T14:00", 60)

    months = finance_service.monthly_revenue("2026")["meses"]

    assert (months[8]["receita"], months[8]["atendimentos"]) == (125.5, 2)
    assert (months[9]["receita"], months[9]["atendimentos"]) == (60.0, 1)


def test_cancelled_and_not_finished_appointments_do_not_count(finance_service, book):
    book("2026-10-05T14:00", 60, status="cancelado")
    book("2026-10-19T11:30", 90)   # termina 12h30: ainda em andamento às 12h
    book("2026-10-20T10:00", 90)   # amanhã
    book("2026-10-19T11:00", 50)   # termina exatamente às 12h: conta
    book("2026-10-12T10:00", 40, status="concluido")

    october = finance_service.monthly_revenue("2026")["meses"][9]

    assert (october["receita"], october["atendimentos"]) == (90.0, 2)


def test_variation_compares_with_previous_month(finance_service, book):
    book("2025-12-10T10:00", 100)
    book("2026-01-10T10:00", 150)
    book("2026-02-10T10:00", 75)

    months = finance_service.monthly_revenue("2026")["meses"]

    assert months[0]["variacao_percentual"] == 50.0     # janeiro x dezembro do ano anterior
    assert months[1]["variacao_percentual"] == -50.0
    assert months[2]["variacao_percentual"] == -100.0   # março sem movimento
    assert months[3]["variacao_percentual"] is None     # abril: o anterior foi zero


def test_month_status_and_future_months_without_variation(finance_service, book):
    book("2026-09-10T10:00", 100)

    months = finance_service.monthly_revenue("2026")["meses"]

    assert [m["situacao"] for m in months[8:]] == ["fechado", "em_andamento", "futuro", "futuro"]
    assert months[10]["variacao_percentual"] is None


def test_monthly_revenue_defaults_to_current_year(finance_service):
    assert finance_service.monthly_revenue()["ano"] == 2026
    assert finance_service.monthly_revenue("")["ano"] == 2026


def test_total_of_the_year(finance_service, book):
    book("2025-12-10T10:00", 999)   # ano anterior: só entra na comparação
    book("2026-03-10T10:00", 10.1)
    book("2026-03-11T10:00", 20.2)

    assert finance_service.monthly_revenue("2026")["total"] == {"receita": 30.3, "atendimentos": 2}


@pytest.mark.parametrize("year", ["dois mil", "1999", "2101", "2026.5"])
def test_invalid_year(finance_service, year):
    with pytest.raises(ValidationError) as error:
        finance_service.monthly_revenue(year)
    assert "ano" in error.value.details


# --- período (semana, mês, ano) ------------------------------------------------------------

@pytest.mark.parametrize("period, day, start, end", [
    ("semana", "2026-10-21", "2026-10-19", "2026-10-26"),   # quarta: segunda a domingo
    ("semana", "2026-10-19", "2026-10-19", "2026-10-26"),   # a própria segunda
    ("semana", "2026-11-01", "2026-10-26", "2026-11-02"),   # domingo: semana que vira o mês
    ("mes", "2026-10-21", "2026-10-01", "2026-11-01"),
    ("mes", "2026-12-15", "2026-12-01", "2027-01-01"),
    ("ano", "2026-10-21", "2026-01-01", "2027-01-01"),
])
def test_period_range(period, day, start, end):
    assert period_range(period, date.fromisoformat(day)) == (at(f"{start}T00:00"), at(f"{end}T00:00"))


# --- ranking de profissionais (#31) --------------------------------------------------------

@pytest.fixture
def staff(users, professionals):
    """Camila (id 1) e Juliana (id 2)."""
    camila = professionals.link(users.add(nome="Camila Ferreira", email="camila@x.com", perfil="admin")["id"])
    juliana = professionals.link(users.add(nome="Juliana Rocha", email="juliana@x.com", perfil="admin")["id"])
    return camila, juliana


def test_ranking_orders_by_appointments(finance_service, book, staff):
    camila, juliana = staff
    book("2026-10-05T10:00", 90, profissional_id=camila, cliente_id=10)
    book("2026-10-06T10:00", 35, profissional_id=juliana, cliente_id=10)
    book("2026-10-07T10:00", 35, profissional_id=juliana, cliente_id=10)   # mesma cliente de novo
    book("2026-10-08T10:00", 40, profissional_id=juliana, cliente_id=11)

    result = finance_service.professional_ranking("mes", "2026-10-15")

    assert (result["periodo"], result["inicio"], result["fim"]) == ("mes", "2026-10-01", "2026-10-31")
    assert result["profissionais"] == [
        {"posicao": 1, "id": juliana, "nome": "Juliana Rocha", "atendimentos": 3, "clientes": 2, "receita": 110.0},
        {"posicao": 2, "id": camila, "nome": "Camila Ferreira", "atendimentos": 1, "clientes": 1, "receita": 90.0},
    ]


def test_ranking_tie_is_broken_by_revenue(finance_service, book, staff):
    camila, juliana = staff
    book("2026-10-05T10:00", 35, profissional_id=juliana)
    book("2026-10-06T10:00", 90, profissional_id=camila)

    names = [p["nome"] for p in finance_service.professional_ranking("mes", "2026-10-15")["profissionais"]]
    assert names == ["Camila Ferreira", "Juliana Rocha"]


def test_ranking_respects_the_period(finance_service, book, staff):
    camila, _ = staff
    book("2026-09-30T10:00", 90, profissional_id=camila)   # mês anterior
    book("2026-10-13T10:00", 90, profissional_id=camila)   # semana anterior
    book("2026-10-19T09:00", 90, profissional_id=camila)   # esta semana, já terminou

    assert finance_service.professional_ranking("semana")["profissionais"][0]["atendimentos"] == 1
    assert finance_service.professional_ranking("mes")["profissionais"][0]["atendimentos"] == 2
    assert finance_service.professional_ranking("ano")["profissionais"][0]["atendimentos"] == 3


def test_ranking_defaults_to_current_month(finance_service):
    result = finance_service.professional_ranking()

    assert (result["periodo"], result["inicio"], result["fim"]) == ("mes", "2026-10-01", "2026-10-31")
    assert result["profissionais"] == []


@pytest.mark.parametrize("period, day, field", [
    ("dia", None, "periodo"),
    ("mes", "15/10/2026", "data"),
    ("mes", "1999-01-01", "data"),
])
def test_ranking_invalid_query(finance_service, period, day, field):
    with pytest.raises(ValidationError) as error:
        finance_service.professional_ranking(period, day)
    assert field in error.value.details


# --- receita semanal (#32) -----------------------------------------------------------------

def test_weekly_revenue_has_seven_days(finance_service, book):
    book("2026-10-13T10:00", 50)    # terça da semana anterior
    book("2026-10-14T10:00", 50)
    book("2026-10-19T09:00", 90)    # segunda (hoje), já terminou
    book("2026-10-19T10:00", 35.5)
    book("2026-10-20T10:00", 90)    # amanhã: ainda não aconteceu

    result = finance_service.weekly_revenue()

    assert (result["inicio"], result["fim"]) == ("2026-10-19", "2026-10-25")
    assert (result["receita"], result["atendimentos"]) == (125.5, 2)
    assert [d["dia_semana"] for d in result["dias"]] == ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    assert result["dias"][0] == {"data": "2026-10-19", "dia_semana": "seg", "receita": 125.5, "atendimentos": 2}
    assert result["dias"][1]["receita"] == 0.0
    assert result["semana_anterior"] == {"receita": 100.0, "variacao_percentual": 25.5}


def test_weekly_revenue_of_another_week(finance_service, book):
    book("2026-10-14T10:00", 50)

    result = finance_service.weekly_revenue("2026-10-18")   # domingo: semana de 12 a 18

    assert (result["inicio"], result["fim"], result["receita"]) == ("2026-10-12", "2026-10-18", 50.0)
    assert result["semana_anterior"] == {"receita": 0.0, "variacao_percentual": None}


def test_weekly_revenue_invalid_date(finance_service):
    with pytest.raises(ValidationError) as error:
        finance_service.weekly_revenue("ontem")
    assert "data" in error.value.details
