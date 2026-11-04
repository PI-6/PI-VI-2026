"""Dashboard da área interna (RF05, issue #69).

Mostra os dados do **funcionário logado** (prompt do protótipo: "Dados do funcionário logado"):
os agendamentos e a agenda de hoje, e a receita do dia e do mês dos atendimentos dele.
O total do salão continua só no Financeiro do gerente. O alerta de estoque baixo é do salão.

Receita segue a regra do BI (decisão do time, 03/11): atendimento realizado = não cancelado e
com horário já terminado. A "receita prevista do dia" soma também o que ainda vai acontecer hoje,
para o card não ficar zerado de manhã.
"""
from datetime import datetime, time, timedelta

from services.finance_service import money, period_range, to_decimal


def situation(appointment, now):
    if appointment["fim"] <= now:
        return "realizado"
    if appointment["inicio"] <= now:
        return "em_andamento"
    return "a_seguir"


class DashboardService:
    def __init__(self, appointment_repository, professional_repository, finance_repository, product_service,
                 clock=datetime.now):
        self.appointments = appointment_repository
        self.professionals = professional_repository
        self.finance = finance_repository
        self.products = product_service
        self.clock = clock  # injetável para os testes não dependerem do dia de hoje

    def for_user(self, current_user):
        now = self.clock()
        today = now.date()
        professional = self.professionals.find_active_by_user_id(current_user["id"])

        body = {
            "data": today.isoformat(),
            "profissional": {"id": professional["id"], "nome": professional["nome"]} if professional else None,
            "estoque_baixo": self.products.low_stock_alert(limit=3),
        }
        # Gerente que não atende (sem cadastro de profissional): só o alerta de estoque tem dado
        if not professional:
            body.update(agendamentos_hoje={"total": 0, "realizados": 0, "a_seguir": 0},
                        receita={"dia": 0.0, "dia_prevista": 0.0, "mes": 0.0, "mes_atendimentos": 0},
                        agenda_hoje=[])
            return body

        day_start = datetime.combine(today, time.min)
        rows = self.appointments.list_day(day_start, day_start + timedelta(days=1), professional["id"])
        agenda = [{
            "id": row["id"],
            "hora_inicio": row["inicio"].strftime("%H:%M"),
            "hora_fim": row["fim"].strftime("%H:%M"),
            "cliente": {"id": row["cliente_id"], "nome": row["cliente_nome"]},
            "servico": {"id": row["servico_id"], "nome": row["servico_nome"]},
            "situacao": situation(row, now),
        } for row in rows]

        realized_today = sum((to_decimal(r["valor"]) for r in rows if r["fim"] <= now), to_decimal(0))
        expected_today = sum((to_decimal(r["valor"]) for r in rows), to_decimal(0))
        month = self.finance.professional_totals(professional["id"], *period_range("mes", today), now)

        body.update(
            agendamentos_hoje={
                "total": len(agenda),
                "realizados": sum(1 for item in agenda if item["situacao"] == "realizado"),
                "a_seguir": sum(1 for item in agenda if item["situacao"] != "realizado"),
            },
            receita={
                "dia": money(realized_today),
                "dia_prevista": money(expected_today),
                "mes": money(month["receita"]),
                "mes_atendimentos": int(month["atendimentos"]),
            },
            agenda_hoje=agenda,
        )
        return body
