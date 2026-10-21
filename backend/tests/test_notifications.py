"""E-mails do agendamento: cliente e profissional (issues #23, #24, #25 e #26).

"Agora" é segunda, 19/10/2026, 12h. A profissional trabalha terça (20/10) das 9h às 18h.
"""
import logging
import smtplib
import threading
from datetime import date

import pytest

from errors import ConflictError
from notifications import templates
from notifications.appointment_notifier import AppointmentNotifier, run_now
from notifications.email_sender import ConsoleEmailSender, SmtpEmailSender, build_message, build_sender
from tests.conftest import DOMAIN, SALON
from tests.fakes import FakeEmailSender

CLIENT = {"id": 50, "nome": "Ana Paula Souza", "email": "ana.souza@gmail.com", "perfil": "cliente"}
PROFESSIONAL = {"id": 2, "nome": "Camila Ferreira", "email": f"camila@{DOMAIN}"}

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


def test_professional_email_has_client_date_and_time():
    subject, text, html = templates.professional_notification("Camila Ferreira", CLIENT["nome"], APPOINTMENT, SALON)

    assert subject == "Novo agendamento: Ana Paula Souza em 20/10/2026 às 10:00"
    for content in (text, html):
        assert "Ana Paula Souza" in content
        assert "terça-feira, 20 de outubro de 2026" in content
        assert "10:00 às 11:00" in content
        assert "Corte feminino" in content
    assert "Olá, Camila!" in text


def test_professional_email_has_no_client_contact_data():
    """Minimização (LGPD): o profissional recebe só o nome do cliente."""
    _, text, html = templates.professional_notification("Camila", CLIENT["nome"], APPOINTMENT, SALON)
    for content in (text, html):
        assert CLIENT["email"] not in content
        assert "R$" not in content  # o valor fica no painel, não no aviso


def test_professional_email_escapes_html():
    _, _, html = templates.professional_notification("Camila", "<b>Ana</b>", APPOINTMENT, SALON)
    assert "<b>Ana</b>" not in html and "&lt;b&gt;Ana&lt;/b&gt;" in html


def test_templates_live_in_separate_files():
    """O texto do e-mail é editável sem mexer no código Python."""
    names = {path.name for path in templates.TEMPLATES_DIR.iterdir()}
    assert {"cliente.html", "cliente.txt", "profissional.html", "profissional.txt"} <= names


# --- Disparo na confirmação (#25 e #26) -------------------------------------

def test_booking_emails_the_client_and_the_professional(appointment_service, email_sender, professional_id):
    created = appointment_service.create(CLIENT, booking(professional_id))

    assert [mail["to"] for mail in email_sender.sent] == ["ana.souza@gmail.com", f"camila@{DOMAIN}"]
    to_client, to_professional = email_sender.sent
    assert "20/10/2026 às 10:00" in to_client["subject"]
    assert "Camila Ferreira" in to_client["text"] and SALON["endereco"] in to_client["text"]
    assert to_professional["subject"].startswith("Novo agendamento: Ana Paula Souza")
    assert created["status"] == "agendado"


def test_no_email_when_the_slot_is_taken(appointment_service, email_sender, professional_id):
    appointment_service.create(CLIENT, booking(professional_id))
    with pytest.raises(ConflictError):
        appointment_service.create(CLIENT, booking(professional_id, hora="10:30"))
    assert len(email_sender.sent) == 2  # só o primeiro agendamento gerou e-mails (cliente e profissional)


def test_smtp_failure_does_not_cancel_the_booking(appointment_service, appointments, professional_id, caplog):
    appointment_service.notifier = AppointmentNotifier(FakeEmailSender(fail=True), SALON, run=run_now)

    with caplog.at_level(logging.ERROR):
        created = appointment_service.create(CLIENT, booking(professional_id))

    assert created["id"] and len(appointments.rows) == 1
    assert "Falha ao enviar e-mail ao cliente do agendamento" in caplog.text
    assert "Falha ao enviar e-mail ao profissional do agendamento" in caplog.text
    assert "ana.souza@gmail.com" not in caplog.text  # e-mails fora do log (LGPD)
    assert f"camila@{DOMAIN}" not in caplog.text


def test_professional_failure_does_not_block_the_client_email():
    class FailsForStaff(FakeEmailSender):
        def send(self, to, subject, text, html=None):
            if to.endswith(DOMAIN):
                raise ConnectionRefusedError("SMTP recusou")
            super().send(to, subject, text, html)

    sender = FailsForStaff()
    result = AppointmentNotifier(sender, SALON, run=run_now).send_confirmation(CLIENT, APPOINTMENT, PROFESSIONAL)

    assert result == {"cliente": True, "profissional": False}
    assert [mail["to"] for mail in sender.sent] == ["ana.souza@gmail.com"]


def test_recipient_without_email_is_skipped(notifier, email_sender):
    result = notifier.send_confirmation({"id": 1, "nome": "Ana"}, APPOINTMENT, {"nome": "Camila"})
    assert result == {"cliente": False, "profissional": False}
    assert email_sender.sent == []


def test_booking_does_not_wait_for_the_email(appointment_service, professional_id):
    """Com o envio em segundo plano, a API responde antes de o SMTP terminar."""
    release, finished = threading.Event(), threading.Event()

    class SlowSender(FakeEmailSender):
        def send(self, to, subject, text, html=None):
            release.wait(timeout=5)  # simula um SMTP lento
            super().send(to, subject, text, html)
            if len(self.sent) == 2:
                finished.set()

    sender = SlowSender()
    appointment_service.notifier = AppointmentNotifier(sender, SALON)  # padrão: segundo plano

    created = appointment_service.create(CLIENT, booking(professional_id))

    assert created["status"] == "agendado" and sender.sent == []  # respondeu sem esperar o e-mail
    release.set()
    assert finished.wait(timeout=5)
    assert {mail["to"] for mail in sender.sent} == {"ana.souza@gmail.com", f"camila@{DOMAIN}"}


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
