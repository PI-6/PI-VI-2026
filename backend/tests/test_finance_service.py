"""Financeiro / BI (RF10).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). Atendimento realizado = agendamento
não cancelado cujo horário já terminou (decisão do time, 03/11).
"""
from datetime import datetime, timedelta

import pytest

from errors import ValidationError


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
