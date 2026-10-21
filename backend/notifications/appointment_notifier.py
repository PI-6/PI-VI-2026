"""Disparo dos e-mails de agendamento (issues #25 e #26).

Regras:
- O e-mail é consequência do agendamento, não condição. Se o SMTP falhar, o agendamento
  já está gravado e o cliente recebe a resposta de sucesso normalmente; a falha fica no
  log para a equipe verificar (base para a #27).
- O envio acontece em segundo plano: a API responde ao cliente logo depois de gravar, sem
  esperar o servidor de e-mail, que pode levar alguns segundos.
- Cada destinatário é independente: se o e-mail do profissional falhar, o do cliente sai.
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from notifications import templates

logger = logging.getLogger(__name__)

# Poucas threads bastam: o envio é rápido e só acontece quando alguém agenda.
# Criado só no primeiro uso, para os testes (que enviam na hora) não abrirem threads.
_executor = None


def run_in_background(job):
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="email")
    _executor.submit(job)


def run_now(job):
    """Executa na hora. Usado nos testes, para conferir os e-mails logo após o agendamento."""
    job()


class AppointmentNotifier:
    def __init__(self, sender, salon, run=run_in_background):
        self.sender = sender
        self.salon = salon  # {"nome", "endereco", "telefone"}
        self.run = run

    def appointment_confirmed(self, client, appointment, professional=None):
        """Agenda o envio ao cliente e ao profissional e volta na hora, sem esperar o SMTP."""
        # Cópias: o envio roda em outra thread e não pode ver mudanças feitas depois nesses dicts
        client, appointment, professional = dict(client), dict(appointment), dict(professional or {})
        self.run(lambda: self.send_confirmation(client, appointment, professional))

    def send_confirmation(self, client, appointment, professional):
        """Envia os dois e-mails. Devolve quais deram certo: {"cliente": bool, "profissional": bool}."""
        return {
            "cliente": self._deliver(
                "cliente", appointment["id"], client.get("email"),
                lambda: templates.client_confirmation(client.get("nome"), appointment, self.salon),
            ),
            "profissional": self._deliver(
                "profissional", appointment["id"], professional.get("email"),
                lambda: templates.professional_notification(
                    professional.get("nome"), client.get("nome"), appointment, self.salon
                ),
            ),
        }

    def _deliver(self, recipient, appointment_id, email, build):
        if not email:
            logger.warning("Agendamento %s sem e-mail do %s; aviso não enviado.", appointment_id, recipient)
            return False
        try:
            subject, text, html = build()
            self.sender.send(email, subject, text, html)
        except Exception as error:  # noqa: BLE001 - qualquer falha de envio não pode derrubar o agendamento
            # Só o id e o tipo do erro: nada de e-mail, CPF ou telefone no log (LGPD)
            logger.error("Falha ao enviar e-mail ao %s do agendamento %s: %s",
                         recipient, appointment_id, type(error).__name__)
            return False
        logger.info("E-mail do agendamento %s enviado ao %s.", appointment_id, recipient)
        return True
