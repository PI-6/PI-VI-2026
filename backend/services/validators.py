"""Funções de validação usadas pelos serviços."""
import re
from datetime import datetime

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def only_digits(value):
    return re.sub(r"\D", "", value or "")


def clean_text(value):
    return value.strip() if isinstance(value, str) else ""


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email or ""))


def email_domain(email):
    return email.rsplit("@", 1)[-1].lower() if "@" in email else ""


def is_valid_phone(phone_digits):
    # DDD + 8 dígitos (fixo) ou DDD + 9 dígitos (celular)
    return len(phone_digits) in (10, 11)


def is_valid_cpf(cpf_digits):
    if len(cpf_digits) != 11 or cpf_digits == cpf_digits[0] * 11:
        return False

    # Os dois últimos dígitos são verificadores, calculados a partir dos anteriores
    for position in (9, 10):
        total = sum(int(cpf_digits[i]) * (position + 1 - i) for i in range(position))
        check_digit = (total * 10) % 11 % 10
        if check_digit != int(cpf_digits[position]):
            return False
    return True


def parse_time(value):
    """Converte "HH:MM" em datetime.time, ou devolve None se o formato for inválido."""
    try:
        return datetime.strptime(value, "%H:%M").time()
    except (TypeError, ValueError):
        return None
