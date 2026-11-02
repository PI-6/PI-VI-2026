"""Bloqueios de horário (issues #17, #18 e #19).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). A profissional Camila (admin) trabalha
terça (20/10) das 9h às 18h e sábado das 8h às 12h. Serviço 1 = 60 min.
"""
from datetime import datetime, time

import pytest

from errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from services.block_service import expand
from tests.conftest import DOMAIN

TUESDAY = "2026-10-20"


@pytest.fixture
def camila(professional_service):
    return professional_service.create_professional({
        "nome": "Camila Ferreira", "email": f"camila@{DOMAIN}", "senha": "camila123", "perfil": "admin",
        "servicos": [1, 2],
        "horarios": [
            {"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"},
            {"dia_semana": 5, "hora_inicio": "08:00", "hora_fim": "12:00"},
        ],
    })


@pytest.fixture
def camila_user(users, camila):
    return users.find_by_id(camila["usuario_id"])


@pytest.fixture
def other_admin(users):
    return users.add(nome="Juliana Rocha", email=f"juliana@{DOMAIN}", senha="Senha@123", perfil="admin")


def at(hhmm, day=TUESDAY):
    return datetime.fromisoformat(f"{day}T{hhmm}")


def lunch(**changes):
    return {"tipo": "semanal", "dia_semana": 1, "hora_inicio": "12:00", "hora_fim": "13:00",
            "motivo": "Almoço", **changes}


def doctor(**changes):
    return {"tipo": "pontual", "data": TUESDAY, "hora_inicio": "14:00", "hora_fim": "16:00",
            "motivo": "Consulta médica", **changes}


# --- criar (#17) ---------------------------------------------------------------------------

def test_admin_blocks_own_agenda_once(block_service, camila, camila_user):
    block = block_service.create_block(camila["id"], doctor(), camila_user)

    assert block == {
        "id": 1, "profissional_id": camila["id"], "tipo": "pontual", "motivo": "Consulta médica",
        "data": TUESDAY, "hora_inicio": "14:00", "data_fim": TUESDAY, "hora_fim": "16:00",
    }


def test_admin_blocks_weekly_lunch(block_service, camila, camila_user, blocks):
    block = block_service.create_block(camila["id"], lunch(), camila_user)

    assert block["tipo"] == "semanal" and block["dia_semana"] == 1
    assert (block["hora_inicio"], block["hora_fim"]) == ("12:00", "13:00")
    assert blocks.rows[0]["criado_por"] == camila_user["id"]


def test_one_off_block_can_span_several_days(block_service, camila, camila_user):
    block = block_service.create_block(
        camila["id"], doctor(data="2026-10-27", data_fim="2026-10-31", hora_inicio="08:00", hora_fim="18:00",
                             motivo="Férias"), camila_user)

    assert (block["data"], block["data_fim"]) == ("2026-10-27", "2026-10-31")


def test_manager_blocks_any_agenda(block_service, camila, manager):
    assert block_service.create_block(camila["id"], lunch(), manager)["id"] == 1


def test_admin_cannot_block_someone_else(block_service, camila, other_admin):
    with pytest.raises(ForbiddenError):
        block_service.create_block(camila["id"], lunch(), other_admin)


def test_block_for_unknown_professional(block_service, manager):
    with pytest.raises(NotFoundError):
        block_service.create_block(99, lunch(), manager)


@pytest.mark.parametrize("changes, field", [
    ({"tipo": "almoço"}, "tipo"),
    ({"hora_inicio": "12h"}, "hora_inicio"),
    ({"hora_fim": "11:00"}, "hora_fim"),
    ({"dia_semana": 7}, "dia_semana"),
    ({"dia_semana": True}, "dia_semana"),
    ({"motivo": "x" * 121}, "motivo"),
])
def test_invalid_weekly_block(block_service, camila, manager, changes, field):
    with pytest.raises(ValidationError) as error:
        block_service.create_block(camila["id"], lunch(**changes), manager)
    assert field in error.value.details


@pytest.mark.parametrize("changes, field", [
    ({"data": "20/10/2026"}, "data"),
    ({"data_fim": "amanhã"}, "data_fim"),
    ({"hora_fim": "14:00"}, "hora_fim"),
    ({"data_fim": "2026-10-19"}, "hora_fim"),  # termina antes de começar
    ({"data": "2026-10-19", "hora_inicio": "09:00", "hora_fim": "11:00"}, "data"),  # já passou
])
def test_invalid_one_off_block(block_service, camila, manager, changes, field):
    with pytest.raises(ValidationError) as error:
        block_service.create_block(camila["id"], doctor(**changes), manager)
    assert field in error.value.details


def test_block_over_booked_client_is_refused(block_service, appointments, camila, camila_user):
    appointment_id = appointments.add(camila["id"], at("15:00"), at("16:00"), cliente_id=5)

    with pytest.raises(ConflictError) as error:
        block_service.create_block(camila["id"], doctor(), camila_user)
    assert error.value.details == {"agendamentos": [
        {"id": appointment_id, "data": TUESDAY, "hora_inicio": "15:00", "hora_fim": "16:00"},
    ]}


def test_weekly_block_over_future_booking_is_refused(block_service, appointments, camila, camila_user):
    # Terça da semana seguinte, 12h30: cai no almoço semanal de terça
    appointments.add(camila["id"], at("12:30", "2026-10-27"), at("13:30", "2026-10-27"))

    with pytest.raises(ConflictError):
        block_service.create_block(camila["id"], lunch(), camila_user)


def test_cancelled_or_past_bookings_do_not_stop_a_block(block_service, appointments, camila, camila_user):
    appointments.add(camila["id"], at("14:00"), at("15:00"), status="cancelado")
    # Terça passada (13/10), já concluído: não impede o almoço semanal daqui para frente
    appointments.add(camila["id"], at("12:00", "2026-10-13"), at("13:00", "2026-10-13"), status="concluido")

    assert block_service.create_block(camila["id"], doctor(), camila_user)["id"] == 1
    assert block_service.create_block(camila["id"], lunch(), camila_user)["id"] == 2


# --- listar --------------------------------------------------------------------------------

def test_list_shows_weekly_and_upcoming_one_off_blocks(block_service, blocks, camila, camila_user):
    blocks.add(camila["id"], "pontual", inicio=at("09:00", "2026-10-13"), fim=at("10:00", "2026-10-13"))
    block_service.create_block(camila["id"], lunch(), camila_user)
    block_service.create_block(camila["id"], doctor(), camila_user)

    listed = block_service.list_blocks(camila["id"])

    assert {b["tipo"] for b in listed} == {"semanal", "pontual"}
    assert len(listed) == 2  # o pontual que já passou não aparece


def test_list_for_unknown_professional(block_service):
    with pytest.raises(NotFoundError):
        block_service.list_blocks(99)


# --- remover (#18) -------------------------------------------------------------------------

def test_admin_removes_own_block(block_service, blocks, camila, camila_user):
    block_id = block_service.create_block(camila["id"], lunch(), camila_user)["id"]

    block_service.delete_block(block_id, camila_user)

    assert blocks.rows == []


def test_admin_cannot_remove_someone_elses_block(block_service, camila, camila_user, other_admin):
    block_id = block_service.create_block(camila["id"], lunch(), camila_user)["id"]

    with pytest.raises(ForbiddenError):
        block_service.delete_block(block_id, other_admin)


def test_manager_removes_any_block(block_service, blocks, camila, camila_user, manager):
    block_id = block_service.create_block(camila["id"], lunch(), camila_user)["id"]

    block_service.delete_block(block_id, manager)

    assert blocks.rows == []


def test_only_manager_removes_block_of_inactive_professional(
        block_service, professional_service, blocks, camila, camila_user, manager):
    block_id = block_service.create_block(camila["id"], lunch(), camila_user)["id"]
    professional_service.delete_professional(camila["id"], manager)

    with pytest.raises(ForbiddenError):
        block_service.delete_block(block_id, {**camila_user, "perfil": "admin", "id": 999})
    block_service.delete_block(block_id, manager)
    assert blocks.rows == []


def test_remove_unknown_block(block_service, manager):
    with pytest.raises(NotFoundError):
        block_service.delete_block(99, manager)


# --- expand --------------------------------------------------------------------------------

def test_expand_repeats_weekly_block_on_matching_days():
    weekly = {"id": 1, "tipo": "semanal", "dia_semana": 1, "hora_inicio": time(12), "hora_fim": time(13)}

    result = expand([weekly], at("00:00", "2026-10-19"), at("00:00", "2026-11-02"))

    assert [(r["inicio"], r["fim"]) for r in result] == [
        (at("12:00", "2026-10-20"), at("13:00", "2026-10-20")),
        (at("12:00", "2026-10-27"), at("13:00", "2026-10-27")),
    ]


def test_expand_keeps_only_intervals_inside_the_period():
    one_off = {"id": 1, "tipo": "pontual", "inicio": at("08:00"), "fim": at("09:00")}
    weekly = {"id": 2, "tipo": "semanal", "dia_semana": 1, "hora_inicio": time(12), "hora_fim": time(13)}

    result = expand([one_off, weekly], at("09:00"), at("12:00"))

    assert result == []  # um termina quando o período começa; o outro começa quando ele termina
