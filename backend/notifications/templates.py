"""Textos dos e-mails (issues #24 e #25).

O texto e o visual ficam em arquivos separados em `email_templates/`, renderizados com
Jinja2 (que já vem com o Flask, então não há dependência nova). Assim dá para mudar o
e-mail sem mexer na lógica. Este módulo só prepara os dados que os templates usam.

Cada função devolve (assunto, texto puro, html). O HTML usa só tabelas e estilos inline,
porque Gmail e Outlook ignoram <style> e CSS moderno.
"""
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

WEEKDAYS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")
MONTHS = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro")

# Mesma paleta do protótipo: rosé, dourado e neutros
COLORS = {
    "rose": "#b76e79",
    "dourado": "#c9a227",
    "texto": "#3a3a3a",
    "suave": "#7a7a7a",
    "fundo": "#f7f1ee",
}

TEMPLATES_DIR = Path(__file__).parent / "email_templates"

# Autoescape só nos .html: nome de cliente ou serviço com "<script>" vira texto, não código.
# StrictUndefined faz um campo esquecido no template dar erro nos testes, em vez de sair vazio.
_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def format_date_long(day):
    """date(2026, 10, 20) -> 'terça-feira, 20 de outubro de 2026' (sem depender do locale do servidor)."""
    return f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}"


def format_money(value):
    """90.0 -> 'R$ 90,00'."""
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def maps_link(address):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"


def first_name(full_name, fallback):
    return (full_name or "").split(" ")[0] or fallback


def _render(name, context):
    """Renderiza o par <name>.txt e <name>.html com o mesmo contexto."""
    context = {"cores": COLORS, **context}
    text = _env.get_template(f"{name}.txt").render(context)
    html = _env.get_template(f"{name}.html").render(context)
    return text, html


def client_confirmation(client_name, appointment, salon):
    """E-mail ao cliente com data, horário, local e profissional (#24).

    appointment: o dicionário que o AppointmentService.create devolve.
    salon: {"nome", "endereco", "telefone"} vindos do .env.
    """
    day = date.fromisoformat(appointment["data"])
    address = salon["endereco"]
    phone = salon.get("telefone") or ""

    subject = (f"Agendamento confirmado: {appointment['servico']['nome']} "
               f"em {day.strftime('%d/%m/%Y')} às {appointment['hora_inicio']}")
    text, html = _render("cliente", {
        "salao": salon,
        "primeiro_nome": first_name(client_name, "cliente"),
        "detalhes": [
            ("Serviço", appointment["servico"]["nome"]),
            ("Profissional", appointment["profissional"]["nome"]),
            ("Data", format_date_long(day)),
            ("Horário", f"{appointment['hora_inicio']} às {appointment['hora_fim']}"),
            ("Local", address),
            ("Valor", format_money(appointment["valor"])),
        ],
        "link_mapa": maps_link(address),
        "contato": (f"Precisa remarcar ou cancelar? Fale com a gente pelo {phone}." if phone
                    else "Precisa remarcar ou cancelar? Responda este e-mail."),
    })
    return subject, text, html


def professional_notification(professional_name, client_name, appointment, salon):
    """Aviso de novo agendamento ao profissional, com data, horário e nome do cliente (#25).

    Só o nome do cliente: CPF, telefone e e-mail dele não vão no e-mail (LGPD, minimização).
    """
    day = date.fromisoformat(appointment["data"])
    client = client_name or "Cliente"

    subject = f"Novo agendamento: {client} em {day.strftime('%d/%m/%Y')} às {appointment['hora_inicio']}"
    text, html = _render("profissional", {
        "salao": salon,
        "primeiro_nome": first_name(professional_name, "equipe"),
        "detalhes": [
            ("Cliente", client),
            ("Serviço", appointment["servico"]["nome"]),
            ("Data", format_date_long(day)),
            ("Horário", f"{appointment['hora_inicio']} às {appointment['hora_fim']}"),
        ],
    })
    return subject, text, html
