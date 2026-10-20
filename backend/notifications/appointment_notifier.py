"""Disparo dos e-mails de agendamento (issue #26).

Regra: o e-mail é consequência do agendamento, não condição. Se o SMTP falhar, o
agendamento já está gravado e o cliente recebe a resposta de sucesso normalmente;
a falha fica registrada no log para a equipe verificar (base para a #27).
"""
import logging

from notifications import templates

logger = logging.getLogger(__name__)


class AppointmentNotifier:
    def __init__(self, sender, salon):
        self.sender = sender
        self.salon = salon  # {"nome", "endereco", "telefone"}

    def appointment_confirmed(self, client, appointment):
        """Envia a confirmação ao cliente. Devolve True se o envio deu certo."""
        email = client.get("email")
        if not email:
            logger.warning("Agendamento %s sem e-mail do cliente; confirmação não enviada.", appointment["id"])
            return False
        try:
            subject, text, html = templates.client_confirmation(client.get("nome"), appointment, self.salon)
            self.sender.send(email, subject, text, html)
        except Exception as error:  # noqa: BLE001 - qualquer falha de envio não pode derrubar o agendamento
            # Só o id e o tipo do erro: nada de e-mail, CPF ou telefone no log (LGPD)
            logger.error("Falha ao enviar confirmação do agendamento %s: %s", appointment["id"], type(error).__name__)
            return False
        logger.info("Confirmação do agendamento %s enviada ao cliente.", appointment["id"])
        return True
