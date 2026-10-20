"""Textos dos e-mails (issue #24).

Cada template devolve (assunto, texto puro, html). O HTML usa só tabelas e estilos
inline, porque Gmail e Outlook ignoram <style> e CSS moderno.
"""
from datetime import date
from html import escape
from urllib.parse import quote_plus

WEEKDAYS = ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo")
MONTHS = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro")

# Mesma paleta do protótipo: rosé, dourado e neutros
ROSE = "#b76e79"
GOLD = "#c9a227"
TEXT = "#3a3a3a"
MUTED = "#7a7a7a"
BACKGROUND = "#f7f1ee"


def format_date_long(day):
    """date(2026, 10, 20) -> 'terça-feira, 20 de outubro de 2026' (sem depender do locale do servidor)."""
    return f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}"


def format_money(value):
    """90.0 -> 'R$ 90,00'."""
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def maps_link(address):
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"


def client_confirmation(client_name, appointment, salon):
    """E-mail ao cliente com data, horário, local e profissional (RF04).

    appointment: o dicionário que o AppointmentService.create devolve.
    salon: {"nome", "endereco", "telefone"} vindos do .env.
    """
    day = date.fromisoformat(appointment["data"])
    when = format_date_long(day)
    time_range = f"{appointment['hora_inicio']} às {appointment['hora_fim']}"
    first_name = (client_name or "").split(" ")[0] or "cliente"
    service = appointment["servico"]["nome"]
    professional = appointment["profissional"]["nome"]
    price = format_money(appointment["valor"])
    address = salon["endereco"]
    phone = salon.get("telefone") or ""

    subject = f"Agendamento confirmado: {service} em {day.strftime('%d/%m/%Y')} às {appointment['hora_inicio']}"

    contact_line = f"Precisa remarcar ou cancelar? Fale com a gente pelo {phone}." if phone \
        else "Precisa remarcar ou cancelar? Responda este e-mail."
    text = "\n".join([
        f"Olá, {first_name}!",
        "",
        f"Seu agendamento no {salon['nome']} está confirmado.",
        "",
        f"Serviço: {service}",
        f"Profissional: {professional}",
        f"Data: {when}",
        f"Horário: {time_range}",
        f"Local: {address}",
        f"Valor: {price}",
        "",
        f"Como chegar: {maps_link(address)}",
        "",
        "Chegue com 10 minutos de antecedência.",
        contact_line,
        "",
        f"Até breve!\n{salon['nome']}",
    ])

    rows = [
        ("Serviço", service),
        ("Profissional", professional),
        ("Data", when),
        ("Horário", time_range),
        ("Local", address),
        ("Valor", price),
    ]
    rows_html = "".join(
        f'<tr><td style="padding:10px 0;color:{MUTED};font-size:14px;width:120px;vertical-align:top;">'
        f'{escape(label)}</td>'
        f'<td style="padding:10px 0;color:{TEXT};font-size:15px;font-weight:bold;">'
        f'{escape(value)}</td></tr>'
        for label, value in rows
    )
    salon_name = escape(salon["nome"])
    html = f"""<!doctype html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background:{BACKGROUND};font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background:{BACKGROUND};padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;">
        <tr><td style="background:{ROSE};padding:24px;text-align:center;">
          <div style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">{salon_name}</div>
          <div style="color:#ffffff;font-size:14px;margin-top:6px;">Agendamento confirmado ✔</div>
        </td></tr>
        <tr><td style="padding:28px 28px 8px;">
          <p style="margin:0 0 12px;color:{TEXT};font-size:16px;">Olá, {escape(first_name)}!</p>
          <p style="margin:0 0 20px;color:{TEXT};font-size:15px;">
            Seu horário está reservado. Confira os detalhes:
          </p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="border-top:2px solid {GOLD};border-bottom:2px solid {GOLD};">
            {rows_html}
          </table>
        </td></tr>
        <tr><td style="padding:20px 28px;text-align:center;">
          <a href="{escape(maps_link(address))}"
             style="display:inline-block;background:{GOLD};color:#ffffff;text-decoration:none;
                    padding:12px 24px;border-radius:24px;font-size:15px;font-weight:bold;">Como chegar</a>
        </td></tr>
        <tr><td style="padding:0 28px 28px;color:{MUTED};font-size:13px;line-height:1.5;">
          Chegue com 10 minutos de antecedência.<br>{escape(contact_line)}
        </td></tr>
        <tr><td style="background:{BACKGROUND};padding:16px;text-align:center;color:{MUTED};font-size:12px;">
          {salon_name} · {escape(address)}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    return subject, text, html
