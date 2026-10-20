"""Popula o banco com dados de teste para desenvolvimento.

Uso (com o venv do backend ativo, a partir da raiz do projeto):
    python database/seed.py

Pode rodar mais de uma vez: quem já existe (pelo e-mail ou nome) é pulado.
Todos os usuários de teste usam a senha "Senha@123". NÃO usar em produção.
"""
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from werkzeug.security import generate_password_hash  # noqa: E402

from config import Config  # noqa: E402
from db import connect  # noqa: E402

PASSWORD = "Senha@123"
DOMAIN = Config.SALON_EMAIL_DOMAIN

SERVICES = [
    # nome, descrição, duração (min), preço
    ("Corte feminino", "Corte com lavagem e finalização", 60, 90.00),
    ("Corte masculino", "Corte na tesoura ou máquina", 30, 50.00),
    ("Escova", "Escova modeladora", 45, 60.00),
    ("Coloração", "Coloração completa da raiz às pontas", 120, 180.00),
    ("Manicure", "Cutilagem e esmaltação das mãos", 40, 35.00),
    ("Pedicure", "Cutilagem e esmaltação dos pés", 50, 40.00),
    ("Design de sobrancelha", "Design com pinça e linha", 30, 45.00),
    ("Maquiagem", "Maquiagem social", 60, 120.00),
]

# nome, e-mail (sem domínio), perfil, serviços que realiza
STAFF = [
    ("Mariana Duarte", "mariana", "gerente", ["Corte feminino", "Escova", "Coloração"]),
    ("Camila Ferreira", "camila", "admin", ["Corte feminino", "Corte masculino", "Escova"]),
    ("Juliana Rocha", "juliana", "admin", ["Manicure", "Pedicure"]),
    ("Beatriz Lima", "beatriz", "admin", ["Design de sobrancelha", "Maquiagem"]),
]

# Terça a sábado, das 9h às 18h (0 = segunda, como no Python)
WORK_DAYS = [1, 2, 3, 4, 5]
WORK_START, WORK_END = time(9, 0), time(18, 0)

CLIENTS = [
    ("Ana Paula Souza", "52998224725", "19991234567", "ana.souza@gmail.com"),
    ("Carlos Henrique Alves", "11144477735", "19998765432", "carlos.alves@hotmail.com"),
    ("Fernanda Martins", "93541134780", "19987654321", "fernanda.martins@outlook.com"),
]

# Agendamentos de exemplo, com datas relativas ao dia em que o seed roda, para sempre haver
# horários ocupados nos próximos dias. Dia útil +1 = próximo dia de trabalho; -1 = o último que passou.
# cliente (e-mail), profissional (login), serviço, dia útil, hora, status
APPOINTMENTS = [
    ("fernanda.martins@outlook.com", "mariana", "Coloração", 1, "09:00", "agendado"),
    ("ana.souza@gmail.com", "camila", "Corte feminino", 1, "10:00", "agendado"),
    ("fernanda.martins@outlook.com", "camila", "Escova", 1, "11:00", "cancelado"),
    ("carlos.alves@hotmail.com", "camila", "Corte masculino", 1, "14:00", "agendado"),
    ("ana.souza@gmail.com", "juliana", "Manicure", 2, "15:30", "agendado"),
    ("carlos.alves@hotmail.com", "camila", "Corte masculino", -1, "16:00", "concluido"),
    ("ana.souza@gmail.com", "mariana", "Coloração", -2, "13:00", "concluido"),
]


def work_day(offset, today=None):
    """N-ésimo dia de trabalho depois de hoje (offset > 0) ou antes de hoje (offset < 0)."""
    day = today or date.today()
    step = 1 if offset > 0 else -1
    remaining = abs(offset)
    while remaining:
        day += timedelta(days=step)
        if day.weekday() in WORK_DAYS:
            remaining -= 1
    return day


def find_id(cursor, sql, params):
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return row[0] if row else None


def main():
    conn = connect()
    cursor = conn.cursor()
    password_hash = generate_password_hash(PASSWORD)

    service_ids = {}
    for name, description, duration, price in SERVICES:
        service_id = find_id(cursor, "SELECT id FROM servicos WHERE nome = %s", (name,))
        if service_id is None:
            cursor.execute(
                "INSERT INTO servicos (nome, descricao, duracao_minutos, preco) VALUES (%s, %s, %s, %s)",
                (name, description, duration, price),
            )
            service_id = cursor.lastrowid
        service_ids[name] = service_id

    for name, login, role, services in STAFF:
        email = f"{login}@{DOMAIN}"
        if find_id(cursor, "SELECT id FROM usuarios WHERE email = %s", (email,)):
            continue
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (%s, %s, %s, %s)",
            (name, email, password_hash, role),
        )
        cursor.execute("INSERT INTO profissionais (usuario_id) VALUES (%s)", (cursor.lastrowid,))
        professional_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO profissional_servicos (profissional_id, servico_id) VALUES (%s, %s)",
            [(professional_id, service_ids[s]) for s in services],
        )
        cursor.executemany(
            "INSERT INTO horarios_trabalho (profissional_id, dia_semana, hora_inicio, hora_fim)"
            " VALUES (%s, %s, %s, %s)",
            [(professional_id, day, WORK_START, WORK_END) for day in WORK_DAYS],
        )

    for name, cpf, phone, email in CLIENTS:
        if find_id(cursor, "SELECT id FROM usuarios WHERE email = %s", (email,)):
            continue
        cursor.execute(
            "INSERT INTO usuarios (nome, cpf, telefone, email, senha_hash, perfil)"
            " VALUES (%s, %s, %s, %s, %s, 'cliente')",
            (name, cpf, phone, email, password_hash),
        )

    seed_appointments(cursor, service_ids)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Seed concluído. Senha de todos os usuários de teste: {PASSWORD}")
    print(f"Gerente: mariana@{DOMAIN} | Admin: camila@{DOMAIN} | Cliente: ana.souza@gmail.com")


def seed_appointments(cursor, service_ids):
    cursor.execute("SELECT COUNT(*) FROM agendamentos")
    if cursor.fetchone()[0]:
        print("Agendamentos já existem; pulando essa parte.")
        return

    services = {name: (duration, price) for name, _, duration, price in SERVICES}
    for client_email, login, service, offset, start, status in APPOINTMENTS:
        client_id = find_id(cursor, "SELECT id FROM usuarios WHERE email = %s", (client_email,))
        professional_id = find_id(
            cursor,
            "SELECT p.id FROM profissionais p JOIN usuarios u ON u.id = p.usuario_id WHERE u.email = %s",
            (f"{login}@{DOMAIN}",),
        )
        duration, price = services[service]
        begin = datetime.combine(work_day(offset), datetime.strptime(start, "%H:%M").time())
        cancelled = status == "cancelado"
        cursor.execute(
            "INSERT INTO agendamentos (cliente_id, profissional_id, servico_id, inicio, fim, valor, status,"
            " cancelado_em, cancelado_por) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (client_id, professional_id, service_ids[service], begin, begin + timedelta(minutes=duration),
             price, status, datetime.now() if cancelled else None, client_id if cancelled else None),
        )


if __name__ == "__main__":
    main()
