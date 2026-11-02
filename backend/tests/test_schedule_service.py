"""Agenda do dia e exclusão de agendamento pela equipe (RF06).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). A profissional Camila trabalha
terça (20/10) das 9h às 18h. Serviço 1 = Corte feminino, 60 min, R$ 90.
"""
from datetime import datetime, time

import pytest

from errors import ConflictError, NotFoundError, ValidationError
from tests.conftest import DOMAIN, NOW

TUESDAY = "2026-10-20"


@pytest.fixture
def camila_id(professional_service):
    return professional_service.create_professional({
        "nome": "Camila Ferreira", "email": f"camila@{DOMAIN}", "senha": "camila123", "perfil": "admin",
        "servicos": [1, 2], "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"}],
    })["id"]


@pytest.fixture
def juliana_id(professional_service):
    return professional_service.create_professional({
        "nome": "Juliana Rocha", "email": f"juliana@{DOMAIN}", "senha": "juliana123", "perfil": "admin",
        "servicos": [2], "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"}],
    })["id"]


@pytest.fixture
def ana(users):
    return users.add(nome="Ana Souza", email="ana@gmail.com", senha="Senha@123", perfil="cliente")


def at(hhmm, day=TUESDAY):
    return datetime.fromisoformat(f"{day}T{hhmm}")


def book(appointment_service, client, professional_id, hora, servico_id=1):
    return appointment_service.create(client, {
        "profissional_id": professional_id, "servico_id": servico_id, "data": TUESDAY, "hora": hora,
    })


# --- agenda do dia -------------------------------------------------------------------------

def test_schedule_lists_the_day_for_the_whole_salon(appointment_service, camila_id, juliana_id, ana):
    book(appointment_service, ana, juliana_id, "09:00", servico_id=2)
    book(appointment_service, ana, camila_id, "10:00")

    result = appointment_service.day_schedule(TUESDAY)

    assert result["data"] == TUESDAY
    assert result["agendamentos"][1] == {
        "id": 2, "hora_inicio": "10:00", "hora_fim": "11:00", "status": "agendado", "valor": 90.0,
        "cliente": {"id": ana["id"], "nome": "Ana Souza"},
        "profissional": {"id": camila_id, "nome": "Camila Ferreira"},
        "servico": {"id": 1, "nome": "Corte feminino"},
    }
    assert [a["hora_inicio"] for a in result["agendamentos"]] == ["09:00", "10:00"]


def test_schedule_filters_by_professional(appointment_service, camila_id, juliana_id, ana):
    book(appointment_service, ana, juliana_id, "09:00", servico_id=2)
    book(appointment_service, ana, camila_id, "10:00")

    result = appointment_service.day_schedule(TUESDAY, str(camila_id))

    assert [a["profissional"]["id"] for a in result["agendamentos"]] == [camila_id]


def test_schedule_hides_cancelled_and_other_days(appointment_service, appointments, camila_id, ana):
    appointments.add(camila_id, at("11:00"), at("12:00"), status="cancelado",
                     cliente_id=ana["id"], servico_id=1, valor=90)
    appointments.add(camila_id, at("11:00", "2026-10-27"), at("12:00", "2026-10-27"),
                     cliente_id=ana["id"], servico_id=1, valor=90)

    assert appointment_service.day_schedule(TUESDAY)["agendamentos"] == []


def test_schedule_shows_blocks_of_the_day(appointment_service, blocks, camila_id, juliana_id):
    blocks.add(camila_id, "semanal", motivo="Almoço", dia_semana=1, hora_inicio=time(12), hora_fim=time(13))
    # Férias da Juliana de domingo a quarta: na terça aparece o dia inteiro
    blocks.add(juliana_id, "pontual", motivo="Férias", inicio=at("08:00", "2026-10-18"), fim=at("18:00", "2026-10-21"))
    blocks.add(camila_id, "semanal", dia_semana=3, hora_inicio=time(12), hora_fim=time(13))  # quinta: fora

    result = appointment_service.day_schedule(TUESDAY)

    assert result["bloqueios"] == [
        {"id": 2, "tipo": "pontual", "motivo": "Férias", "profissional": {"id": juliana_id, "nome": "Juliana Rocha"},
         "hora_inicio": "00:00", "hora_fim": "24:00"},
        {"id": 1, "tipo": "semanal", "motivo": "Almoço", "profissional": {"id": camila_id, "nome": "Camila Ferreira"},
         "hora_inicio": "12:00", "hora_fim": "13:00"},
    ]


@pytest.mark.parametrize("day, professional, field", [
    ("20/10/2026", None, "data"),
    (None, None, "data"),
    (TUESDAY, "camila", "profissional_id"),
])
def test_schedule_invalid_query(appointment_service, day, professional, field):
    with pytest.raises(ValidationError) as error:
        appointment_service.day_schedule(day, professional)
    assert field in error.value.details


def test_schedule_unknown_professional(appointment_service):
    with pytest.raises(NotFoundError):
        appointment_service.day_schedule(TUESDAY, "99")


# --- excluir agendamento -------------------------------------------------------------------

def test_cancel_frees_the_slot_and_records_who(appointment_service, appointments, camila_id, ana, manager):
    appointment_id = book(appointment_service, ana, camila_id, "10:00")["id"]

    appointment_service.cancel(appointment_id, manager)

    row = appointments.rows[0]
    assert (row["status"], row["cancelado_por"], row["cancelado_em"]) == ("cancelado", manager["id"], NOW)
    slots = appointment_service.availability(camila_id, TUESDAY, "1")["horarios"]
    assert {s["hora"]: s["status"] for s in slots}["10:00"] == "livre"
    # e outro cliente consegue agendar no mesmo horário
    assert book(appointment_service, ana, camila_id, "10:00")["status"] == "agendado"


@pytest.mark.parametrize("status, message", [
    ("cancelado", "já foi cancelado"),
    ("concluido", "concluído"),
])
def test_cancel_only_scheduled(appointment_service, appointments, camila_id, manager, status, message):
    appointment_id = appointments.add(camila_id, at("10:00"), at("11:00"), status=status)

    with pytest.raises(ConflictError, match=message):
        appointment_service.cancel(appointment_id, manager)


def test_cancel_unknown_appointment(appointment_service, manager):
    with pytest.raises(NotFoundError):
        appointment_service.cancel(99, manager)


def test_cancel_race_is_reported(appointment_service, appointments, camila_id, manager):
    appointment_id = appointments.add(camila_id, at("10:00"), at("11:00"))
    appointments.cancel = lambda *args: False  # outra pessoa cancelou entre a leitura e o UPDATE

    with pytest.raises(ConflictError, match="acabou de ser alterado"):
        appointment_service.cancel(appointment_id, manager)
