"""Disponibilidade do profissional (issue #11).

"Agora" é segunda, 19/10/2026, 12h (NOW no conftest). A profissional de teste trabalha
terça (20/10) das 9h às 18h e sábado das 8h às 12h. Serviço 1 = 60 min, serviço 2 = 40 min.
"""
from datetime import datetime

import pytest

from errors import ConflictError, NotFoundError, ValidationError
from tests.conftest import DOMAIN

TUESDAY = "2026-10-20"


@pytest.fixture
def professional_id(professional_service):
    return professional_service.create_professional({
        "nome": "Camila Ferreira", "email": f"camila@{DOMAIN}", "senha": "camila123", "perfil": "admin",
        "servicos": [1, 2],
        "horarios": [
            {"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"},
            {"dia_semana": 5, "hora_inicio": "08:00", "hora_fim": "12:00"},
        ],
    })["id"]


def at(hhmm, day=TUESDAY):
    return datetime.fromisoformat(f"{day}T{hhmm}")


def slots(result):
    return {item["hora"]: item["status"] for item in result["horarios"]}


def test_free_day_has_slots_every_30_minutes(appointment_service, professional_id):
    result = appointment_service.availability(professional_id, TUESDAY, "1")

    hours = [item["hora"] for item in result["horarios"]]
    assert hours[:3] == ["09:00", "09:30", "10:00"]
    assert hours[-1] == "17:00"  # 60 min: o último início que termina até 18h
    assert len(hours) == 17
    assert set(slots(result).values()) == {"livre"}
    assert result["duracao_minutos"] == 60 and result["data"] == TUESDAY


def test_service_must_end_before_closing_time(appointment_service, professional_id, professionals, catalog):
    long_service = catalog.add("Coloração", duracao_minutos=180, preco=180.0)
    # o serviço novo precisa estar entre os que a profissional faz
    professionals.rows[0]["servicos"].append(long_service)

    hours = [item["hora"] for item in appointment_service.availability(
        professional_id, TUESDAY, str(long_service))["horarios"]]
    assert hours[-1] == "15:00"  # 15h + 3h = 18h; 15h30 passaria do expediente


def test_appointment_blocks_every_overlapping_start(appointment_service, appointments, professional_id):
    appointments.add(professional_id, at("10:00"), at("11:00"))

    result = slots(appointment_service.availability(professional_id, TUESDAY, "1"))
    assert result["09:00"] == "livre"     # 9h-10h termina quando o outro começa
    assert result["09:30"] == "ocupado"   # 9h30-10h30 sobrepõe
    assert result["10:00"] == "ocupado"
    assert result["10:30"] == "ocupado"
    assert result["11:00"] == "livre"     # começa quando o outro termina


def test_cancelled_appointment_frees_the_slot(appointment_service, appointments, professional_id):
    appointments.add(professional_id, at("10:00"), at("11:00"), status="cancelado")

    assert slots(appointment_service.availability(professional_id, TUESDAY, "1"))["10:00"] == "livre"


def test_other_professionals_appointments_do_not_count(appointment_service, appointments, professional_id):
    appointments.add(professional_id + 1, at("10:00"), at("11:00"))

    assert slots(appointment_service.availability(professional_id, TUESDAY, "1"))["10:00"] == "livre"


def test_day_off_returns_no_slots(appointment_service, professional_id):
    # 26/10/2026 é segunda, dia em que a profissional não trabalha
    assert appointment_service.availability(professional_id, "2026-10-26", "1")["horarios"] == []


def test_past_date_returns_no_slots(appointment_service, professional_id):
    assert appointment_service.availability(professional_id, "2026-10-13", "1")["horarios"] == []


def test_today_hides_slots_that_already_started(appointment_service, professional_id):
    appointment_service.clock = lambda: at("10:10")

    hours = [item["hora"] for item in appointment_service.availability(professional_id, TUESDAY, "1")["horarios"]]
    assert hours[0] == "10:30"


@pytest.mark.parametrize("day,service,field", [
    ("20/10/2026", "1", "data"),
    ("", "1", "data"),
    (None, "1", "data"),
    (TUESDAY, "corte", "servico_id"),
    (TUESDAY, None, "servico_id"),
])
def test_invalid_query_parameters(appointment_service, professional_id, day, service, field):
    with pytest.raises(ValidationError) as error:
        appointment_service.availability(professional_id, day, service)
    assert field in error.value.details


def test_unknown_professional_or_service(appointment_service, professional_id):
    with pytest.raises(NotFoundError):
        appointment_service.availability(99, TUESDAY, "1")
    with pytest.raises(NotFoundError):
        appointment_service.availability(professional_id, TUESDAY, "99")


def test_inactive_professional_is_not_found(appointment_service, professional_service, professional_id, manager):
    professional_service.delete_professional(professional_id, manager)

    with pytest.raises(NotFoundError):
        appointment_service.availability(professional_id, TUESDAY, "1")


def test_professional_must_perform_the_service(appointment_service, professional_id, catalog):
    other = catalog.add("Maquiagem", duracao_minutos=60)

    with pytest.raises(ValidationError):
        appointment_service.availability(professional_id, TUESDAY, str(other))


# ---------- Criação de agendamento (issue #12) ----------

CLIENT = {"id": 50, "nome": "Ana Souza", "perfil": "cliente"}


def booking(professional_id, **changes):
    data = {"profissional_id": professional_id, "servico_id": 1, "data": TUESDAY, "hora": "10:00"}
    data.update(changes)
    return data


def test_create_appointment(appointment_service, appointments, professional_id):
    created = appointment_service.create(CLIENT, booking(professional_id))

    assert created["hora_inicio"] == "10:00" and created["hora_fim"] == "11:00"
    assert created["profissional"]["nome"] == "Camila Ferreira"
    assert created["servico"]["nome"] == "Corte feminino"
    assert created["status"] == "agendado"
    saved = appointments.rows[0]
    assert saved["cliente_id"] == CLIENT["id"]  # o cliente vem do token, não do corpo
    assert saved["fim"] == at("11:00")


def test_price_is_copied_to_the_appointment(appointment_service, appointments, catalog, professional_id):
    appointment_service.create(CLIENT, booking(professional_id))
    catalog.update(1, "Corte feminino", None, 60, 120.0)  # o gerente aumenta o preço depois

    assert appointments.rows[0]["valor"] == 90  # o agendamento continua com o preço do dia


def test_new_appointment_shows_as_busy(appointment_service, professional_id):
    appointment_service.create(CLIENT, booking(professional_id))

    assert slots(appointment_service.availability(professional_id, TUESDAY, "1"))["10:00"] == "ocupado"


@pytest.mark.parametrize("hora", ["10:00", "09:30", "10:30"])
def test_overlapping_appointment_is_refused(appointment_service, appointments, professional_id, hora):
    appointments.add(professional_id, at("10:00"), at("11:00"))

    with pytest.raises(ConflictError):
        appointment_service.create(CLIENT, booking(professional_id, hora=hora))


def test_back_to_back_appointments_are_allowed(appointment_service, appointments, professional_id):
    appointments.add(professional_id, at("10:00"), at("11:00"))

    assert appointment_service.create(CLIENT, booking(professional_id, hora="11:00"))["hora_inicio"] == "11:00"


def test_cancelled_slot_can_be_booked_again(appointment_service, appointments, professional_id):
    appointments.add(professional_id, at("10:00"), at("11:00"), status="cancelado")

    assert appointment_service.create(CLIENT, booking(professional_id))["status"] == "agendado"


def test_simultaneous_booking_is_refused(appointment_service, appointments, professional_id):
    # A checagem do serviço passou, mas outro cliente gravou o horário antes do INSERT
    appointments.simulate_race = True

    with pytest.raises(ConflictError):
        appointment_service.create(CLIENT, booking(professional_id))


@pytest.mark.parametrize("changes,message", [
    ({"hora": "08:30"}, "expediente"),                            # antes de abrir
    ({"hora": "17:30"}, "expediente"),                            # 60 min passaria das 18h
    ({"hora": "10:15"}, "agenda"),                                # fora da grade de 30 min
    ({"data": "2026-10-26"}, "não trabalha"),                     # segunda: folga
    ({"data": "2026-10-19", "hora": "11:00"}, "já passou"),       # hoje, antes das 12h
    ({"data": "2026-10-13"}, "já passou"),                        # data passada
])
def test_unbookable_times_are_refused(appointment_service, professional_id, changes, message):
    with pytest.raises(ValidationError, match=message):
        appointment_service.create(CLIENT, booking(professional_id, **changes))


@pytest.mark.parametrize("field,value", [
    ("profissional_id", "2"),
    ("servico_id", None),
    ("data", "20/10/2026"),
    ("hora", "10h"),
])
def test_invalid_booking_body(appointment_service, professional_id, field, value):
    with pytest.raises(ValidationError) as error:
        appointment_service.create(CLIENT, booking(professional_id, **{field: value}))
    assert field in error.value.details


def test_booking_service_the_professional_does_not_perform(appointment_service, professional_id, catalog):
    other = catalog.add("Maquiagem", duracao_minutos=60)

    with pytest.raises(ValidationError):
        appointment_service.create(CLIENT, booking(professional_id, servico_id=other))


def test_booking_unknown_professional(appointment_service):
    with pytest.raises(NotFoundError):
        appointment_service.create(CLIENT, booking(99))
