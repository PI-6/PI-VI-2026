"""Regras de agendamento (RF04): disponibilidade (#11), criação (#12) e e-mail de confirmação (#26).
Também a agenda do dia da equipe e a exclusão (cancelamento) de agendamento (RF06).

A agenda é uma grade de horários de início a cada SLOT_MINUTES. Um horário só está
livre se o serviço inteiro couber nele: sem sobrepor outro agendamento nem um bloqueio
(#17) e sem passar do fim do expediente do profissional.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from errors import ConflictError, NotFoundError, ValidationError
from services import validators as v
from services.block_service import expand

# Decisão do time (19/10): horários de início a cada 30 minutos
SLOT_MINUTES = 30


def overlaps(start, end, busy):
    """True se o intervalo [start, end) encosta em algum intervalo ocupado."""
    return any(start < item["fim"] and end > item["inicio"] for item in busy)


class AppointmentService:
    def __init__(self, appointment_repository, professional_repository, catalog_repository,
                 block_repository=None, notifier=None, clock=datetime.now):
        self.appointments = appointment_repository
        self.professionals = professional_repository
        self.catalog = catalog_repository
        self.blocks = block_repository  # None = sem bloqueios (usado em alguns testes)
        self.notifier = notifier  # notifications.AppointmentNotifier; None = não envia e-mail
        self.clock = clock  # injetável para os testes não dependerem do dia de hoje

    def availability(self, professional_id, day_text, service_id_text):
        day, service_id = self._parse_query(day_text, service_id_text)
        professional, service = self._load(professional_id, service_id)
        duration = timedelta(minutes=service["duracao_minutos"])

        response = {
            "profissional_id": professional_id,
            "servico_id": service_id,
            "data": day.isoformat(),
            "duracao_minutos": service["duracao_minutos"],
            "horarios": [],
        }

        work = self._working_hours(professional, day)
        now = self.clock()
        if not work or day < now.date():
            return response  # dia de folga ou data que já passou

        day_start = datetime.combine(day, work["hora_inicio"])
        day_end = datetime.combine(day, work["hora_fim"])
        busy = self._busy(professional_id, day_start, day_end)

        start = day_start
        while start + duration <= day_end:  # o serviço precisa terminar dentro do expediente
            if start > now:  # horários de hoje que já passaram não aparecem
                status = "ocupado" if overlaps(start, start + duration, busy) else "livre"
                response["horarios"].append({"hora": start.strftime("%H:%M"), "status": status})
            start += timedelta(minutes=SLOT_MINUTES)
        return response

    def create(self, client, data):
        """Cria o agendamento do cliente logado. O cliente vem do token, nunca do corpo."""
        professional_id, service_id, day, start_time = self._parse_body(data)
        professional, service = self._load(professional_id, service_id)

        start = datetime.combine(day, start_time)
        end = start + timedelta(minutes=service["duracao_minutos"])
        self._ensure_bookable(professional, day, start, end)

        if overlaps(start, end, self._busy(professional_id, start, end)):
            raise ConflictError("Esse horário não está mais disponível. Escolha outro.")

        # O preço é copiado: se o serviço mudar de preço depois, a receita do BI não muda
        price = Decimal(str(service["preco"])).quantize(Decimal("0.01"))
        appointment_id = self.appointments.create_if_free(
            client["id"], professional_id, service_id, start, end, price
        )
        if appointment_id is None:  # outro cliente confirmou o mesmo horário no mesmo instante
            raise ConflictError("Esse horário não está mais disponível. Escolha outro.")

        appointment = {
            "id": appointment_id,
            "profissional": {"id": professional_id, "nome": professional["nome"]},
            "servico": {"id": service_id, "nome": service["nome"]},
            "data": day.isoformat(),
            "hora_inicio": start.strftime("%H:%M"),
            "hora_fim": end.strftime("%H:%M"),
            "valor": float(price),
            "status": "agendado",
        }
        # Só depois de gravado: se o e-mail falhar, o agendamento continua valendo.
        # O notifier envia em segundo plano, ao cliente e ao profissional.
        if self.notifier:
            self.notifier.appointment_confirmed(client, appointment, professional)
        return appointment

    def day_schedule(self, day_text, professional_id_text=None):
        """Agenda de um dia para a equipe (RF06): agendamentos ativos e bloqueios.

        Sem profissional_id, traz o salão inteiro; com ele, só a agenda daquela pessoa.
        """
        day, professional_id = self._parse_schedule_query(day_text, professional_id_text)
        if professional_id is not None and not self.professionals.find_active_by_id(professional_id):
            raise NotFoundError("Profissional não encontrado.")

        start = datetime.combine(day, time.min)
        end = start + timedelta(days=1)
        blocks = expand(self.blocks.list_between(start, end, professional_id), start, end) if self.blocks else []

        return {
            "data": day.isoformat(),
            "agendamentos": [{
                "id": row["id"],
                "hora_inicio": row["inicio"].strftime("%H:%M"),
                "hora_fim": row["fim"].strftime("%H:%M"),
                "status": row["status"],
                "valor": float(row["valor"]),
                "cliente": {"id": row["cliente_id"], "nome": row["cliente_nome"]},
                "profissional": {"id": row["profissional_id"], "nome": row["profissional_nome"]},
                "servico": {"id": row["servico_id"], "nome": row["servico_nome"]},
            } for row in self.appointments.list_day(start, end, professional_id)],
            "bloqueios": [{
                "id": block["id"],
                "tipo": block["tipo"],
                "motivo": block.get("motivo"),
                "profissional": {"id": block["profissional_id"], "nome": block.get("profissional_nome")},
                # Bloqueio de vários dias aparece recortado no dia consultado (00:00 a 24:00 no meio)
                "hora_inicio": max(block["inicio"], start).strftime("%H:%M"),
                "hora_fim": "24:00" if block["fim"] >= end else block["fim"].strftime("%H:%M"),
            } for block in sorted(blocks, key=lambda b: (b["inicio"], b.get("profissional_nome") or ""))],
        }

    def cancel(self, appointment_id, current_user):
        """Exclui um agendamento pela agenda (RF06): vira 'cancelado' e o horário fica livre.

        A linha não é apagada: o BI precisa do histórico e fica registrado quem cancelou e quando.
        """
        appointment = self.appointments.find_by_id(appointment_id)
        if not appointment:
            raise NotFoundError("Agendamento não encontrado.")
        if appointment["status"] == "cancelado":
            raise ConflictError("Este agendamento já foi cancelado.")
        if appointment["status"] == "concluido":
            raise ConflictError("Atendimento já concluído não pode ser excluído.")
        if not self.appointments.cancel(appointment_id, current_user["id"], self.clock()):
            # Outra pessoa mudou o status entre a leitura e o UPDATE
            raise ConflictError("Este agendamento acabou de ser alterado. Atualize a agenda.")

    def _ensure_bookable(self, professional, day, start, end):
        """Mesmas regras da disponibilidade: só se agenda o que a tela mostraria como livre."""
        if start <= self.clock():
            raise ValidationError("Esse horário já passou.")
        work = self._working_hours(professional, day)
        if not work:
            raise ValidationError("O profissional não trabalha nesse dia.")
        day_start = datetime.combine(day, work["hora_inicio"])
        day_end = datetime.combine(day, work["hora_fim"])
        if start < day_start or end > day_end:
            raise ValidationError("O serviço precisa começar e terminar dentro do expediente do profissional.")
        if (start - day_start) % timedelta(minutes=SLOT_MINUTES):
            raise ValidationError(f"Escolha um horário da agenda (de {SLOT_MINUTES} em {SLOT_MINUTES} minutos).")

    def _busy(self, professional_id, start, end):
        """Intervalos que tiram horários da agenda: agendamentos ativos e bloqueios.

        Para o cliente os dois são iguais ("ocupado", X vermelho na tela): ele não precisa
        saber se o horário é de outro cliente ou se a profissional está no almoço.
        """
        busy = list(self.appointments.list_busy_between(professional_id, start, end))
        if self.blocks:
            busy += expand(self.blocks.list_between(start, end, professional_id), start, end)
        return busy

    def _working_hours(self, professional, day):
        for item in professional["horarios"]:
            if item["dia_semana"] == day.weekday():  # 0 = segunda, igual ao banco
                return {"hora_inicio": v.parse_time(item["hora_inicio"]),
                        "hora_fim": v.parse_time(item["hora_fim"])}
        return None

    def _load(self, professional_id, service_id):
        professional = self.professionals.find_active_by_id(professional_id)
        if not professional:
            raise NotFoundError("Profissional não encontrado.")
        service = self.catalog.find_active_by_id(service_id)
        if not service:
            raise NotFoundError("Serviço não encontrado.")
        if service_id not in {s["id"] for s in professional["servicos"]}:
            raise ValidationError("Este profissional não realiza o serviço escolhido.")
        return professional, service

    @staticmethod
    def _parse_body(data):
        errors = {}
        ids = {}
        for field in ("profissional_id", "servico_id"):
            value = data.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                errors[field] = "Informe um id válido."
            ids[field] = value
        try:
            day = date.fromisoformat(data.get("data") or "")
        except (TypeError, ValueError):
            day = None
            errors["data"] = "Informe a data no formato AAAA-MM-DD."
        start_time = v.parse_time(data.get("hora"))
        if not start_time:
            errors["hora"] = "Informe o horário no formato HH:MM."
        if errors:
            raise ValidationError("Verifique os dados do agendamento.", errors)
        return ids["profissional_id"], ids["servico_id"], day, start_time

    @staticmethod
    def _parse_schedule_query(day_text, professional_id_text):
        errors = {}
        try:
            day = date.fromisoformat(day_text or "")
        except ValueError:
            day = None
            errors["data"] = "Informe a data no formato AAAA-MM-DD."
        professional_id = None
        if professional_id_text:
            try:
                professional_id = int(professional_id_text)
            except ValueError:
                errors["profissional_id"] = "Informe um id válido."
        if errors:
            raise ValidationError("Verifique os parâmetros da consulta.", errors)
        return day, professional_id

    @staticmethod
    def _parse_query(day_text, service_id_text):
        errors = {}
        try:
            day = date.fromisoformat(day_text or "")
        except ValueError:
            day = None
            errors["data"] = "Informe a data no formato AAAA-MM-DD."
        try:
            service_id = int(service_id_text or "")
        except ValueError:
            service_id = None
            errors["servico_id"] = "Informe o serviço (servico_id)."
        if errors:
            raise ValidationError("Verifique os parâmetros da consulta.", errors)
        return day, service_id
