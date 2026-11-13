"""Regras do Financeiro / BI (RF10).

Atendimento realizado = agendamento não cancelado cujo horário já terminou (decisão do time,
03/11). Agendamentos futuros e cancelados não entram em nenhum número daqui.

Os valores em dinheiro são somados como Decimal (sem erro de arredondamento) e só viram
float com 2 casas na resposta.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from errors import ValidationError

MONTH_NAMES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
MIN_YEAR, MAX_YEAR = 2000, 2100
PERIODS = ("semana", "mes", "ano")
WEEKDAY_NAMES = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")


def period_range(period, day):
    """Intervalo [início, fim) do período que contém o dia. A semana vai de segunda a domingo."""
    if period == "semana":
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=7)
    elif period == "mes":
        start = day.replace(day=1)
        end = date(day.year + 1, 1, 1) if day.month == 12 else date(day.year, day.month + 1, 1)
    else:
        start, end = date(day.year, 1, 1), date(day.year + 1, 1, 1)
    return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())


def period_info(period, start, end):
    """Cabeçalho comum das respostas por período (o fim mostrado é o último dia, inclusive)."""
    return {"periodo": period, "inicio": start.date().isoformat(),
            "fim": (end - timedelta(days=1)).date().isoformat()}


def to_decimal(value):
    """Decimal exato: o MySQL já devolve Decimal; float (ex.: nos testes) passa pela string."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def money(value):
    return float(to_decimal(value).quantize(Decimal("0.01")))


def variation(current, previous):
    """Variação percentual em relação ao anterior, com 1 casa. None quando o anterior é zero."""
    if not previous:
        return None
    current, previous = to_decimal(current), to_decimal(previous)
    return float(((current - previous) / previous * 100).quantize(Decimal("0.1")))


class FinanceService:
    def __init__(self, finance_repository, clock=datetime.now):
        self.finance = finance_repository
        self.clock = clock  # injetável para os testes não dependerem do dia de hoje

    def monthly_revenue(self, year_text=None):
        """Receita mês a mês de um ano, comparando cada mês com o anterior (#30).

        Traz os 12 meses, inclusive os sem movimento (com zero), para o gráfico não ter buracos.
        Janeiro é comparado com dezembro do ano anterior.
        """
        now = self.clock()
        year = self._parse_year(year_text, now.year)

        rows = self.finance.monthly_totals(datetime(year - 1, 12, 1), datetime(year + 1, 1, 1), now)
        by_month = {(row["ano"], row["mes"]): row for row in rows}

        months, total = [], Decimal(0)
        previous = to_decimal(by_month.get((year - 1, 12), {}).get("receita"))
        for month in range(1, 13):
            row = by_month.get((year, month), {})
            revenue = to_decimal(row.get("receita"))
            status = self._month_status(year, month, now.date())
            months.append({
                "mes": month,
                "nome": MONTH_NAMES[month - 1],
                "receita": money(revenue),
                "atendimentos": int(row.get("atendimentos") or 0),
                "situacao": status,
                # Mês que ainda não começou não tem comparação: daria sempre -100%
                "variacao_percentual": None if status == "futuro" else variation(revenue, previous),
            })
            previous = revenue
            total += revenue

        return {
            "ano": year,
            "meses": months,
            "total": {
                "receita": money(total),
                "atendimentos": sum(m["atendimentos"] for m in months),
            },
        }

    def professional_ranking(self, period_text=None, day_text=None):
        """Ranking de profissionais por atendimentos realizados no período (#31 e RF10).

        Traz também os clientes distintos atendidos e a receita gerada por cada um.
        """
        period, start, end = self._parse_period(period_text, day_text, default_period="mes")
        rows = self.finance.by_professional(start, end, self.clock())
        return {
            **period_info(period, start, end),
            "profissionais": [{
                "posicao": position,
                "id": row["id"],
                "nome": row["nome"],
                "atendimentos": int(row["atendimentos"]),
                "clientes": int(row["clientes"]),
                "receita": money(row["receita"]),
            } for position, row in enumerate(rows, start=1)],
        }

    def summary(self, period_text=None, day_text=None):
        """Resumo do período para o topo do Financeiro e o gráfico de barras (#62 e RF10).

        Receita, atendimentos e ticket médio do período, comparação com o período anterior
        (semana, mês ou ano anterior inteiro) e a série: um ponto por dia na semana e no mês,
        um por mês no ano. A série sempre traz todos os pontos, com zero onde não houve movimento.
        """
        period, start, end = self._parse_period(period_text, day_text, default_period="mes")
        previous_start, previous_end = period_range(period, (start - timedelta(days=1)).date())
        now = self.clock()

        if period == "ano":
            rows = self.finance.monthly_totals(previous_start, end, now)
            buckets = [(date(start.year, m, 1), MONTH_NAMES[m - 1]) for m in range(1, 13)]
            totals = {date(row["ano"], row["mes"], 1): row for row in rows}
        else:
            rows = self.finance.daily_totals(previous_start, end, now)
            days = [(start + timedelta(days=i)).date() for i in range((end - start).days)]
            # Na semana o rótulo é o dia da semana; no mês, o dia/mês
            buckets = [(day, WEEKDAY_NAMES[day.weekday()] if period == "semana" else day.strftime("%d/%m"))
                       for day in days]
            totals = {row["dia"]: row for row in rows}

        series, revenue, count = [], Decimal(0), 0
        for bucket_start, label in buckets:
            row = totals.get(bucket_start, {})
            value, quantity = to_decimal(row.get("receita")), int(row.get("atendimentos") or 0)
            series.append({"rotulo": label, "inicio": bucket_start.isoformat(),
                           "receita": money(value), "atendimentos": quantity})
            revenue += value
            count += quantity

        previous_revenue, previous_count = Decimal(0), 0
        for key, row in totals.items():
            if previous_start.date() <= key < start.date():
                previous_revenue += to_decimal(row["receita"])
                previous_count += int(row["atendimentos"])

        return {
            **period_info(period, start, end),
            "receita": money(revenue),
            "atendimentos": count,
            "ticket_medio": money(revenue / count) if count else None,
            "periodo_anterior": {
                **period_info(period, previous_start, previous_end),
                "receita": money(previous_revenue),
                "atendimentos": previous_count,
                "variacao_percentual": variation(revenue, previous_revenue),
            },
            "serie": series,
        }

    def top_services(self, period_text=None, day_text=None):
        """Serviços mais realizados no período, para o gráfico de pizza (#61 e RF10).

        `percentual` é a fatia de cada serviço no total de atendimentos (a pizza é por quantidade).
        """
        period, start, end = self._parse_period(period_text, day_text, default_period="mes")
        rows = self.finance.by_service(start, end, self.clock())
        total = sum(int(row["atendimentos"]) for row in rows)
        return {
            **period_info(period, start, end),
            "total_atendimentos": total,
            "servicos": [{
                "id": row["id"],
                "nome": row["nome"],
                "atendimentos": int(row["atendimentos"]),
                "receita": money(row["receita"]),
                "percentual": float((Decimal(int(row["atendimentos"])) / total * 100).quantize(Decimal("0.1"))),
            } for row in rows],
        }

    def weekly_revenue(self, day_text=None):
        """Receita da semana (segunda a domingo) que contém a data, dia a dia (#32).

        Compara o total com a semana anterior inteira. Sem data, a semana atual.
        """
        _, start, end = self._parse_period("semana", day_text, default_period="semana")
        previous_start = start - timedelta(days=7)
        rows = self.finance.daily_totals(previous_start, end, self.clock())
        by_day = {row["dia"]: row for row in rows}

        days, total, total_count = [], Decimal(0), 0
        for offset in range(7):
            day = (start + timedelta(days=offset)).date()
            row = by_day.get(day, {})
            revenue = to_decimal(row.get("receita"))
            count = int(row.get("atendimentos") or 0)
            days.append({"data": day.isoformat(), "dia_semana": WEEKDAY_NAMES[offset],
                         "receita": money(revenue), "atendimentos": count})
            total += revenue
            total_count += count

        previous_total = sum((to_decimal(row["receita"]) for row in rows
                              if row["dia"] < start.date()), Decimal(0))
        return {
            **period_info("semana", start, end),
            "receita": money(total),
            "atendimentos": total_count,
            "dias": days,
            "semana_anterior": {"receita": money(previous_total),
                                "variacao_percentual": variation(total, previous_total)},
        }

    def _parse_period(self, period_text, day_text, default_period):
        """Lê ?periodo=semana|mes|ano&data=AAAA-MM-DD (data padrão: hoje) e devolve o intervalo."""
        errors = {}
        period = period_text or default_period
        if period not in PERIODS:
            errors["periodo"] = "O período deve ser semana, mes ou ano."
        day = self.clock().date()
        if day_text:
            try:
                day = date.fromisoformat(day_text)
            except ValueError:
                errors["data"] = "Informe a data no formato AAAA-MM-DD."
        if not errors and not MIN_YEAR <= day.year < MAX_YEAR:
            errors["data"] = f"Informe uma data entre {MIN_YEAR} e {MAX_YEAR - 1}."
        if errors:
            raise ValidationError("Verifique os parâmetros da consulta.", errors)
        return (period, *period_range(period, day))

    @staticmethod
    def _month_status(year, month, today):
        """fechado = já terminou; em_andamento = mês atual (número parcial); futuro = ainda não começou."""
        first_day = date(year, month, 1)
        if (year, month) == (today.year, today.month):
            return "em_andamento"
        return "futuro" if first_day > today else "fechado"

    @staticmethod
    def _parse_year(value, default):
        if value in (None, ""):
            return default
        try:
            year = int(value)
        except (TypeError, ValueError):
            year = None
        if year is None or not MIN_YEAR <= year <= MAX_YEAR:
            raise ValidationError("Verifique os parâmetros da consulta.",
                                  {"ano": f"Informe um ano entre {MIN_YEAR} e {MAX_YEAR}."})
        return year
