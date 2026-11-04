"""Quem entrega o e-mail (issue #23).

Usa só a biblioteca padrão do Python (smtplib + email), então não há dependência nova.

- SmtpEmailSender: envia de verdade por SMTP (Gmail, Outlook, Mailpit local etc.).
- ConsoleEmailSender: usado quando SMTP_HOST não está configurado. Não envia nada,
  só registra no log que o e-mail "sairia", para o time conseguir rodar a API sem SMTP.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

logger = logging.getLogger(__name__)

SECURITY_MODES = ("starttls", "ssl", "none")


def build_message(sender_name, sender_email, to, subject, text, html=None):
    message = EmailMessage()
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = to
    message["Subject"] = subject
    message["Message-ID"] = make_msgid(domain=sender_email.partition("@")[2] or None)
    message.set_content(text)  # versão em texto puro, para clientes de e-mail sem HTML
    if html:
        message.add_alternative(html, subtype="html")
    return message


class SmtpEmailSender:
    def __init__(self, host, port, user, password, security, sender_name, sender_email, timeout=10):
        if security not in SECURITY_MODES:
            raise ValueError(f"SMTP_SECURITY deve ser um destes: {', '.join(SECURITY_MODES)}")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.security = security
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.timeout = timeout  # sem timeout, um SMTP fora do ar travaria a requisição do cliente

    def send(self, to, subject, text, html=None):
        message = build_message(self.sender_name, self.sender_email, to, subject, text, html)
        context = ssl.create_default_context()
        if self.security == "ssl":
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=context)
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
        with server:
            if self.security == "starttls":
                server.starttls(context=context)
            if self.user:
                server.login(self.user, self.password)
            server.send_message(message)


class ConsoleEmailSender:
    def send(self, to, subject, text, html=None):
        logger.info("SMTP não configurado: e-mail '%s' não foi enviado (veja SMTP_HOST no .env).", subject)


def build_sender(config):
    if not config.SMTP_HOST:
        return ConsoleEmailSender()
    return SmtpEmailSender(
        host=config.SMTP_HOST,
        port=config.SMTP_PORT,
        user=config.SMTP_USER,
        password=config.SMTP_PASSWORD,
        security=config.SMTP_SECURITY,
        sender_name=config.SALON_NAME,
        sender_email=config.MAIL_FROM,
    )
