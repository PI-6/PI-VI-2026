"""Testes do gerador de dados de demonstração (database/seed_demo.py), sem precisar do MySQL."""
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from services import validators as v

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "database"))
import seed_demo  # noqa: E402

NOW = datetime(2026, 11, 13, 12, 0)
SERVICES = {
    1: {"nome": "Corte feminino", "duracao_minutos": 60, "preco": 90.0},
    2: {"nome": "Manicure", "duracao_minutos": 40, "preco": 35.0},
    3: {"nome": "Coloração", "duracao_minutos": 120, "preco": 180.0},
}
WORK = {day: (time(9, 0), time(18, 0)) for day in (1, 2, 3, 4, 5)}  # terça a sábado
PROFESSIONALS = [
    {"id": 1, "servicos": [1, 3], "horarios": WORK},
    {"id": 2, "servicos": [2], "horarios": WORK},
]
# Já ocupado: um agendamento do seed e um bloqueio de consulta médica
BUSY = {1: [(datetime(2026, 11, 17, 14, 0), datetime(2026, 11, 17, 16, 0))]}


def generate(seed=1, busy=None):
    rng = random.Random(seed)
    clients = seed_demo.build_clients(rng)
    for i, client in enumerate(clients, start=1):
        client["id"] = 100 + i
    first_day = seed_demo.first_day_of_history(NOW.date())
    last_day = NOW.date() + timedelta(days=14)
    return seed_demo.generate(PROFESSIONALS, SERVICES, clients, busy or BUSY, first_day, last_day, NOW, rng)


@pytest.fixture(scope="module")
def rows():
    return generate()


def active(rows):
    return [r for r in rows if r["status"] != "cancelado"]


def test_history_starts_in_january_of_last_year_and_goes_two_weeks_ahead(rows):
    assert min(r["inicio"] for r in rows).date() >= date(2025, 1, 1)
    assert min(r["inicio"] for r in rows).date() < date(2025, 1, 8)
    assert max(r["inicio"] for r in rows).date() > NOW.date() + timedelta(days=7)


def test_volume_is_enough_for_the_charts(rows):
    realized = [r for r in active(rows) if r["fim"] <= NOW]
    assert len(realized) > 2000
    months = {(r["inicio"].year, r["inicio"].month) for r in realized}
    assert len(months) == 23  # jan/2025 a nov/2026


def test_no_overlap_between_appointments_or_with_what_was_busy(rows):
    for prof in PROFESSIONALS:
        mine = sorted((r["inicio"], r["fim"]) for r in active(rows) if r["profissional_id"] == prof["id"])
        for (_, end), (next_start, _) in zip(mine, mine[1:]):
            assert end <= next_start
        for start, end in mine:
            for busy_start, busy_end in BUSY.get(prof["id"], []):
                assert not (start < busy_end and end > busy_start)


def test_respects_working_hours_lunch_grid_and_services(rows):
    by_id = {p["id"]: p for p in PROFESSIONALS}
    for r in rows:
        prof = by_id[r["profissional_id"]]
        assert r["servico_id"] in prof["servicos"]
        hours = prof["horarios"][r["inicio"].weekday()]
        assert hours[0] <= r["inicio"].time() and r["fim"].time() <= hours[1]
        assert r["fim"] - r["inicio"] == timedelta(minutes=SERVICES[r["servico_id"]]["duracao_minutos"])
        assert r["inicio"].minute in (0, 30)
        lunch_start = datetime.combine(r["inicio"].date(), time(12, 0))
        assert not (r["inicio"] < lunch_start + timedelta(hours=1) and r["fim"] > lunch_start)


def test_status_follows_the_clock(rows):
    for r in rows:
        if r["status"] == "concluido":
            assert r["fim"] <= NOW
        elif r["status"] == "agendado":
            assert r["fim"] > NOW
        else:
            assert r["cancelado_por"] == r["cliente_id"] and r["cancelado_em"] <= NOW
    cancel_rate = sum(r["status"] == "cancelado" for r in rows) / len(rows)
    assert 0.03 < cancel_rate < 0.10


def test_friday_and_saturday_are_busier_than_tuesday(rows):
    def per_day(weekday):
        days = {r["inicio"].date() for r in rows if r["inicio"].weekday() == weekday}
        return sum(1 for r in active(rows) if r["inicio"].weekday() == weekday) / len(days)
    assert per_day(5) > per_day(1)
    assert per_day(4) > per_day(1)


def test_mothers_day_peak_in_may(rows):
    def revenue(month):
        return sum(r["valor"] for r in active(rows)
                   if r["inicio"].year == 2026 and r["inicio"].month == month and r["fim"] <= NOW)
    assert revenue(5) > revenue(4) and revenue(5) > revenue(6)


def test_december_is_the_best_month_of_last_year(rows):
    def revenue(month):
        return sum(r["valor"] for r in active(rows) if r["inicio"].year == 2025 and r["inicio"].month == month)
    assert revenue(12) == max(revenue(m) for m in range(1, 13))


def test_old_prices_are_lower_than_current(rows):
    old = {r["valor"] for r in rows if r["servico_id"] == 1 and r["inicio"].date() < date(2026, 7, 1)}  # reajuste
    new = {r["valor"] for r in rows if r["servico_id"] == 1 and r["inicio"].date() >= date(2026, 7, 1)}
    assert old == {81.0} and new == {90.0}


def test_same_seed_gives_the_same_data():
    assert generate(seed=7) == generate(seed=7)


def test_clients_have_valid_cpf_phone_and_demo_email():
    clients = seed_demo.build_clients(random.Random(3))
    assert len({c["cpf"] for c in clients}) == len(clients)
    for client in clients:
        assert v.is_valid_cpf(client["cpf"])
        assert v.is_valid_phone(client["telefone"])
        assert v.is_valid_email(client["email"]) and client["email"].endswith("@demo.com.br")
