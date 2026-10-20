"""E-mail de confirmação do agendamento (issues #23, #24 e #26).

"Agora" é segunda, 19/10/2026, 12h. A profissional trabalha terça (20/10) das 9h às 18h.
"""
import logging
import smtplib
from datetime import date

import pytest

from errors import ConflictError
from notifications import templates
from notifications.appointment_notifier import AppointmentNotifier
from notifications.email_sender import ConsoleEmailSender, SmtpEmailSender, build_message, build_sender
from tests.conftest import DOMAIN, SALON
from tests.fakes import FakeEmailSender

CLIENT = {"id": 50, "nome": "Ana Paula Souza", "email": "ana.souza@gmail.com", "perfil": "cliente"}

APPOINTMENT = {
    "id": 8,
    "profissional": {"id": 2, "nome": "Camila Ferreira"},
    "servico": {"id": 1, "nome": "Corte feminino"},
    "data": "2026-10-20",
    "hora_inicio": "10:00",
    "hora_fim": "11:00",
    "valor": 1290.5,
    "status": "agendado",
}


@pytest.fixture
def professional_id(professional_service):
    return professional_service.create_professional({
        "nome": "Camila Ferreira", "email": f"camila@{DOMAIN}", "senha": "camila123", "perfil": "admin",
        "servicos": [1, 2], "horarios": [{"dia_semana": 1, "hora_inicio": "09:00", "hora_fim": "18:00"}],
    })["id"]


def booking(professional_id, **changes):
    return {"profissional_id": professional_id, "servico_id": 1, "data": "2026-10-20", "hora": "10:00", **changes}


# --- Template (#24) ---------------------------------------------------------

def test_date_and_money_are_formatted_in_portuguese():
    assert templates.format_date_long(date(2026, 10, 20)) == "terça-feira, 20 de outubro de 2026"
    assert templates.format_date_long(date(2026, 3, 1)) == "domingo, 1 de março de 2026"
    assert templates.format_money(1290.5) == "R$ 1.290,50"


def test_client_email_has_date_time_place_and_professional():
    subject, text, html = templates.client_confirmation(CLIENT["nome"], APPOINTMENT, SALON)

    assert subject == "Agendamento confirmado: Corte feminino em 20/10/2026 às 10:00"
    for content in (text, html):
        assert "terça-feira, 20 de outubro de 2026" in content
        assert "10:00 às 11:00" in content
        assert "Rua das Flores, 123 - Cambuí, Campinas - SP" in content
        assert "Camila Ferreira" in content
        assert "Corte feminino" in content
        assert "R$ 1.290,50" in content
    assert "Olá, Ana!" in text  # só o primeiro nome
    assert "google.com/maps/search" in html


def test_client_email_escapes_html():
    appointment = {**APPOINTMENT, "servico": {"id": 1, "nome": "<script>alert(1)</script>"}}
    _, _, html = templates.client_confirmation("Ana", appointment, SALON)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_email_without_phone_asks_to_reply():
    _, text, _ = templates.client_confirmation("Ana", APPOINTMENT, {**SALON, "telefone": ""})
    assert "Responda este e-mail" in text


# --- Disparo na confirmação (#26) -------------------------------------------

def test_booking_sends_confirmation_to_the_client(appointment_service, email_sender, professional_id):
    created = appointment_service.create(CLIENT, booking(professional_id))

    assert len(email_sender.sent) == 1
    sent = email_sender.sent[0]
    assert sent["to"] == "ana.souza@gmail.com"
    assert "20/10/2026 às 10:00" in sent["subject"]
    assert "Camila Ferreira" in sent["text"] and SALON["endereco"] in sent["text"]
    assert created["status"] == "agendado"


def test_no_email_when_the_slot_is_taken(appointment_service, email_sender, professional_id):
    appointment_service.create(CLIENT, booking(professional_id))
    with pytest.raises(ConflictError):
        appointment_service.create(CLIENT, booking(professional_id, hora="10:30"))
    assert len(email_sender.sent) == 1  # só o primeiro agendamento gerou e-mail


def test_smtp_failure_does_not_cancel_the_booking(appointment_service, appointments, professional_id, caplog):
    appointment_service.notifier = AppointmentNotifier(FakeEmailSender(fail=True), SALON)

    with caplog.at_level(logging.ERROR):
        created = appointment_service.create(CLIENT, booking(professional_id))

    assert created["id"] and len(appointments.rows) == 1
    assert "Falha ao enviar confirmação do agendamento" in caplog.text
    assert "ana.souza@gmail.com" not in caplog.text  # e-mail do cliente fora do log (LGPD)


def test_client_without_email_is_skipped(notifier, email_sender):
    assert notifier.appointment_confirmed({"id": 1, "nome": "Ana"}, APPOINTMENT) is False
    assert email_sender.sent == []


# --- Envio por SMTP (#23) ---------------------------------------------------

def test_message_has_text_and_html_parts():
    message = build_message("Salão Belle", "contato@salaobelle.com.br", "ana@gmail.com",
                            "Assunto", "texto", "<p>html</p>")
    assert message["From"] == "Salão Belle <contato@salaobelle.com.br>"
    assert [part.get_content_type() for part in message.iter_parts()] == ["text/plain", "text/html"]


def test_smtp_sender_uses_starttls_and_login(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            calls.append(("quit",))

        def starttls(self, context):
            calls.append(("starttls",))

        def login(self, user, password):
            calls.append(("login", user))

        def send_message(self, message):
            calls.append(("send", message["To"]))

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    sender = SmtpEmailSender("smtp.gmail.com", 587, "salao@gmail.com", "senha-de-app", "starttls",
                             "Salão Belle", "salao@gmail.com")
    sender.send("ana@gmail.com", "Assunto", "texto")

    assert calls == [("connect", "smtp.gmail.com", 587, 10), ("starttls",), ("login", "salao@gmail.com"),
                     ("send", "ana@gmail.com"), ("quit",)]


def test_invalid_security_mode_is_refused():
    with pytest.raises(ValueError):
        SmtpEmailSender("host", 25, "", "", "tls", "Salão", "a@b.com")


def test_without_smtp_host_the_api_only_logs():
    class Config:
        SMTP_HOST = ""

    assert isinstance(build_sender(Config), ConsoleEmailSender)
