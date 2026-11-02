"""Bloqueios de horário do profissional (RF06; issues #17, #18 e #19).

Dois tipos:
- pontual: um período com data e hora (consulta médica, curso, folga). Pode durar mais de um dia.
- semanal: repete toda semana no mesmo dia e horário (almoço de toda terça, 12h às 13h).

Quem pode mexer: o admin só na própria agenda; o gerente em qualquer uma.
Um bloqueio não pode cair em cima de agendamento já marcado: a equipe cancela ou remarca
o cliente antes. Assim nenhum cliente fica com horário confirmado num período bloqueado.
"""
from datetime import date, datetime, timedelta

from errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from services import validators as v

BLOCK_TYPES = ("pontual", "semanal")
MAX_REASON_LENGTH = 120


def expand(blocks, start, end):
    """Transforma bloqueios em intervalos concretos {"inicio", "fim", ...} dentro de [start, end).

    O pontual já tem início e fim. O semanal vira um intervalo em cada dia do período que
    cai no dia da semana dele. O resultado vem ordenado pelo início.
    """
    intervals = []
    for block in blocks:
        if block["tipo"] == "pontual":
            candidates = [(block["inicio"], block["fim"])]
        else:
            candidates = []
            day = start.date()
            while day <= end.date():
                if day.weekday() == block["dia_semana"]:
                    candidates.append((datetime.combine(day, block["hora_inicio"]),
                                       datetime.combine(day, block["hora_fim"])))
                day += timedelta(days=1)
        for begin, finish in candidates:
            if begin < end and finish > start:
                intervals.append({**block, "inicio": begin, "fim": finish})
    return sorted(intervals, key=lambda item: item["inicio"])


def to_response(block):
    """Formato do bloqueio na API (o mesmo que o front envia para criar)."""
    body = {
        "id": block["id"],
        "profissional_id": block["profissional_id"],
        "tipo": block["tipo"],
        "motivo": block.get("motivo"),
    }
    if block["tipo"] == "pontual":
        body.update(
            data=block["inicio"].date().isoformat(),
            hora_inicio=block["inicio"].strftime("%H:%M"),
            data_fim=block["fim"].date().isoformat(),
            hora_fim=block["fim"].strftime("%H:%M"),
        )
    else:
        body.update(
            dia_semana=block["dia_semana"],
            hora_inicio=block["hora_inicio"].strftime("%H:%M"),
            hora_fim=block["hora_fim"].strftime("%H:%M"),
        )
    return body


class BlockService:
    def __init__(self, block_repository, professional_repository, clock=datetime.now):
        self.blocks = block_repository
        self.professionals = professional_repository
        self.clock = clock  # injetável para os testes não dependerem do dia de hoje

    def list_blocks(self, professional_id):
        """Bloqueios que ainda valem: os semanais e os pontuais que não terminaram."""
        self._get_professional(professional_id)
        return [to_response(b) for b in self.blocks.list_for_professional(professional_id, self.clock())]

    def create_block(self, professional_id, data, current_user):
        professional = self._get_professional(professional_id)
        self._ensure_can_manage(professional, current_user)

        block = self._validate(data)
        block.update(profissional_id=professional_id, criado_por=current_user["id"])

        block_id, conflicts = self.blocks.create_if_no_conflict(block, self.clock())
        if conflicts:
            raise ConflictError(
                "Já existem agendamentos nesse horário. Cancele ou remarque esses clientes antes de bloquear.",
                {"agendamentos": [{
                    "id": item["id"],
                    "data": item["inicio"].date().isoformat(),
                    "hora_inicio": item["inicio"].strftime("%H:%M"),
                    "hora_fim": item["fim"].strftime("%H:%M"),
                } for item in conflicts]},
            )
        return to_response({**block, "id": block_id})

    def delete_block(self, block_id, current_user):
        block = self.blocks.find_by_id(block_id)
        if not block:
            raise NotFoundError("Bloqueio não encontrado.")
        professional = self.professionals.find_active_by_id(block["profissional_id"])
        # Profissional desativado: só o gerente ainda mexe na agenda dele
        if professional:
            self._ensure_can_manage(professional, current_user)
        elif current_user["perfil"] != "gerente":
            raise ForbiddenError("Você só pode alterar bloqueios da sua própria agenda.")
        self.blocks.delete(block_id)

    def _get_professional(self, professional_id):
        professional = self.professionals.find_active_by_id(professional_id)
        if not professional:
            raise NotFoundError("Profissional não encontrado.")
        return professional

    @staticmethod
    def _ensure_can_manage(professional, current_user):
        if current_user["perfil"] == "gerente":
            return
        if professional["usuario_id"] != current_user["id"]:
            raise ForbiddenError("Você só pode alterar bloqueios da sua própria agenda.")

    def _validate(self, data):
        errors = {}
        kind = data.get("tipo")
        motivo = v.clean_text(data.get("motivo")) or None
        start_time = v.parse_time(data.get("hora_inicio"))
        end_time = v.parse_time(data.get("hora_fim"))

        if kind not in BLOCK_TYPES:
            errors["tipo"] = "O tipo deve ser pontual ou semanal."
        if motivo and len(motivo) > MAX_REASON_LENGTH:
            errors["motivo"] = f"Use no máximo {MAX_REASON_LENGTH} caracteres."
        if not start_time:
            errors["hora_inicio"] = "Informe o horário no formato HH:MM."
        if not end_time:
            errors["hora_fim"] = "Informe o horário no formato HH:MM."

        block = {"tipo": kind, "motivo": motivo}
        if kind == "pontual":
            self._validate_one_off(data, start_time, end_time, block, errors)
        elif kind == "semanal":
            self._validate_weekly(data, start_time, end_time, block, errors)

        if errors:
            raise ValidationError("Verifique os dados do bloqueio.", errors)
        return block

    def _validate_one_off(self, data, start_time, end_time, block, errors):
        start_day = self._parse_date(data.get("data"), "data", errors)
        # data_fim é opcional: sem ela, o bloqueio começa e termina no mesmo dia
        end_day = self._parse_date(data["data_fim"], "data_fim", errors) if data.get("data_fim") else start_day
        if not (start_day and end_day and start_time and end_time):
            return
        start = datetime.combine(start_day, start_time)
        end = datetime.combine(end_day, end_time)
        if end <= start:
            errors["hora_fim"] = "O fim do bloqueio deve ser depois do início."
        elif end <= self.clock():
            errors["data"] = "Esse período já passou."
        block.update(inicio=start, fim=end)

    @staticmethod
    def _validate_weekly(data, start_time, end_time, block, errors):
        day = data.get("dia_semana")
        if not isinstance(day, int) or isinstance(day, bool) or not 0 <= day <= 6:
            errors["dia_semana"] = "dia_semana deve ser de 0 (segunda) a 6 (domingo)."
        if start_time and end_time and end_time <= start_time:
            errors["hora_fim"] = "O fim do bloqueio deve ser depois do início."
        block.update(dia_semana=day, hora_inicio=start_time, hora_fim=end_time)

    @staticmethod
    def _parse_date(value, field, errors):
        try:
            return date.fromisoformat(value or "")
        except (TypeError, ValueError):
            errors[field] = "Informe a data no formato AAAA-MM-DD."
            return None
