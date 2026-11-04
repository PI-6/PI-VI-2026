"""Regras do Financeiro / BI (RF10).

Atendimento realizado = agendamento não cancelado cujo horário já terminou (decisão do time,
03/11). Agendamentos futuros e cancelados não entram em nenhum número daqui.

Os valores em dinheiro são somados como Decimal (sem erro de arredondamento) e só viram
float com 2 casas na resposta.
"""
from datetime import date, datetime
from decimal import Decimal

from errors import ValidationError

MONTH_NAMES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
MIN_YEAR, MAX_YEAR = 2000, 2100


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
