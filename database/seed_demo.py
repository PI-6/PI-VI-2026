"""Dados de demonstração para o BI: meses de histórico de atendimentos e uma agenda movimentada.

Uso (com o venv do backend ativo, a partir da raiz do projeto, DEPOIS do seed.py):
    python database/seed_demo.py            # cria os dados de demonstração
    python database/seed_demo.py --reset    # apaga a demonstração anterior e cria de novo
    python database/seed_demo.py --apagar   # só apaga a demonstração

Só para desenvolvimento e apresentação. NÃO usar em produção.

O que o script faz:
- Cria clientes fictícios (e-mail @demo.com.br, senha "Senha@123"). Tudo o que é da demonstração
  fica ligado a esses clientes, então --reset/--apagar não mexem nos dados do seed.py.
- Gera atendimentos desde 1º de janeiro do ano passado até hoje (assim o ano atual fica completo
  e dá para comparar com o ano anterior no Financeiro), e agendamentos para os próximos
  DIAS_A_FRENTE dias, com padrões de um salão real:
    * mais movimento na sexta e no sábado; picos em maio (Dia das Mães) e dezembro;
    * leve crescimento mês a mês (o salão ganhando clientes);
    * serviços com pesos diferentes (corte e manicure mais comuns que coloração);
    * clientes fiéis que voltam com frequência;
    * cerca de 6% de cancelamentos;
    * reajuste de preços há alguns meses (o BI usa o valor gravado em cada agendamento).
- Respeita as mesmas regras do backend: cada profissional só faz os próprios serviços, dentro do
  horário de trabalho, sem sobrepor outro agendamento nem bloqueio, e com pausa de almoço.
- Usa semente aleatória fixa: rodando no mesmo dia, o resultado é sempre o mesmo.

Não muda o MER nem cria tabela: só insere em usuarios e agendamentos.
"""
import argparse
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

PASSWORD = "Senha@123"
DEMO_EMAIL_DOMAIN = "demo.com.br"
RANDOM_SEED = 2026

DIAS_A_FRENTE = 14

SLOT_MINUTES = 30  # mesma grade de horários do backend (SLOT_MINUTES em appointment_service.py)
LUNCH = (time(12, 0), time(13, 0))  # ninguém atende no almoço

# Chance de cada horário livre virar atendimento, antes dos multiplicadores abaixo
BASE_OCCUPANCY = 0.42
FUTURE_OCCUPANCY = 0.30  # agenda futura um pouco mais vazia: ainda vai encher
CANCEL_RATE = 0.06
MONTHLY_GROWTH = 0.02  # +2% por mês de histórico

# 0 = segunda ... 6 = domingo (como no Python e na API)
WEEKDAY_FACTOR = {0: 0.7, 1: 0.8, 2: 0.85, 3: 0.95, 4: 1.2, 5: 1.35, 6: 0.6}
# Sazonalidade por mês (1 = janeiro)
MONTH_FACTOR = {1: 0.8, 2: 0.82, 3: 0.95, 4: 0.95, 5: 1.25, 6: 0.95,
                7: 0.85, 8: 0.95, 9: 1.0, 10: 1.05, 11: 1.1, 12: 1.35}
# Peso de cada serviço na escolha (serviço que não está aqui tem peso 1)
SERVICE_WEIGHT = {
    "Corte feminino": 3.0, "Corte masculino": 2.5, "Escova": 2.0, "Coloração": 1.0,
    "Manicure": 3.0, "Pedicure": 2.0, "Design de sobrancelha": 2.5, "Maquiagem": 0.8,
}
# Até este número de meses atrás, os preços eram 10% menores (reajuste)
MONTHS_BEFORE_PRICE_INCREASE = 4
OLD_PRICE_FACTOR = 0.90

CLIENT_NAMES = [
    "Larissa Campos", "Patrícia Nogueira", "Renata Bastos", "Gabriela Prado", "Juliana Teixeira",
    "Aline Moraes", "Vanessa Ribeiro", "Tatiane Lopes", "Bruna Carvalho", "Camila Andrade",
    "Daniela Freitas", "Elaine Pires", "Flávia Rezende", "Helena Duarte", "Isabela Gomes",
    "Karina Mendes", "Letícia Barros", "Mônica Cardoso", "Natália Rocha", "Priscila Vieira",
    "Roberta Farias", "Simone Costa", "Thaís Monteiro", "Viviane Araújo", "Beatriz Fonseca",
    "Rodrigo Martins", "Felipe Souza", "Gustavo Lima", "André Oliveira", "Marcelo Pereira",
    "Lucas Almeida", "Rafael Batista",
]


# ---------- Geração (sem banco: dá para testar sem MySQL) ----------

def fake_cpf(rng):
    """CPF fictício com dígitos verificadores válidos (o cadastro valida o CPF)."""
    while True:
        digits = [rng.randint(0, 9) for _ in range(9)]
        if len(set(digits)) > 1:  # 111.111.111-11 e parecidos são inválidos
            break
    for size in (9, 10):
        total = sum(d * (size + 1 - i) for i, d in enumerate(digits[:size]))
        digits.append((total * 10 % 11) % 10)
    return "".join(map(str, digits))


def build_clients(rng):
    """Clientes da demonstração. Os primeiros da lista são os mais fiéis (voltam mais vezes)."""
    clients = []
    for position, name in enumerate(CLIENT_NAMES):
        login = name.lower().replace(" ", ".")
        for accented, plain in zip("áâãéêíóôõúç", "aaaeeiooouc"):
            login = login.replace(accented, plain)
        clients.append({
            "nome": name,
            "email": f"{login}@{DEMO_EMAIL_DOMAIN}",
            "cpf": fake_cpf(rng),
            "telefone": f"1998{rng.randint(1000000, 9999999)}",
            "peso": 1.0 / (1 + position * 0.15),  # fidelidade: cai devagar ao longo da lista
        })
    return clients


def _overlaps(start, end, intervals):
    return any(start < busy_end and end > busy_start for busy_start, busy_end in intervals)


def _demand(day, first_day):
    months_from_start = (day.year - first_day.year) * 12 + day.month - first_day.month
    growth = (1 + MONTHLY_GROWTH) ** months_from_start
    return WEEKDAY_FACTOR[day.weekday()] * MONTH_FACTOR[day.month] * growth


def generate(professionals, services, clients, busy, first_day, last_day, now, rng):
    """Gera os agendamentos de first_day até last_day (inclusive).

    professionals: [{"id", "servicos": [ids], "horarios": {dia_semana: (hora_inicio, hora_fim)}}]
    services: {id: {"nome", "duracao_minutos", "preco"}}
    clients: [{"id", "peso"}]
    busy: {profissional_id: [(inicio, fim), ...]} com agendamentos e bloqueios que já existem
    Devolve dicts no formato da tabela agendamentos (sem id).
    """
    price_change = date(now.year, now.month, 1)
    for _ in range(MONTHS_BEFORE_PRICE_INCREASE):
        price_change = (price_change - timedelta(days=1)).replace(day=1)

    client_weights = [c["peso"] for c in clients]
    rows = []
    day = first_day
    while day <= last_day:
        future = datetime.combine(day, time(23, 59)) > now
        occupancy = (FUTURE_OCCUPANCY if future else BASE_OCCUPANCY) * _demand(day, first_day)

        for prof in professionals:
            hours = prof["horarios"].get(day.weekday())
            if not hours or not prof["servicos"]:
                continue
            taken = list(busy.get(prof["id"], []))
            lunch = (datetime.combine(day, LUNCH[0]), datetime.combine(day, LUNCH[1]))
            taken.append(lunch)

            offered = [services[s] | {"id": s} for s in prof["servicos"] if s in services]
            weights = [SERVICE_WEIGHT.get(s["nome"], 1.0) for s in offered]

            slot = datetime.combine(day, hours[0])
            day_end = datetime.combine(day, hours[1])
            while slot < day_end:
                if rng.random() >= occupancy:
                    slot += timedelta(minutes=SLOT_MINUTES)
                    continue
                service = rng.choices(offered, weights)[0]
                end = slot + timedelta(minutes=service["duracao_minutos"])
                if end > day_end or _overlaps(slot, end, taken):
                    slot += timedelta(minutes=SLOT_MINUTES)
                    continue

                client = rng.choices(clients, client_weights)[0]
                price = service["preco"] * (OLD_PRICE_FACTOR if day < price_change else 1)
                cancelled = rng.random() < CANCEL_RATE
                if cancelled:
                    status = "cancelado"
                elif end <= now:
                    status = "concluido"
                else:
                    status = "agendado"
                rows.append({
                    "cliente_id": client["id"], "profissional_id": prof["id"], "servico_id": service["id"],
                    "inicio": slot, "fim": end, "valor": round(price, 2), "status": status,
                    # Cancelado pelo próprio cliente, um pouco antes do horário
                    "cancelado_em": min(slot - timedelta(hours=rng.randint(2, 48)), now) if cancelled else None,
                    "cancelado_por": client["id"] if cancelled else None,
                })
                if not cancelled:  # cancelado libera o horário, como no sistema
                    taken.append((slot, end))
                # Próximo horário de início na grade de 30 min depois do fim deste
                minutes = -(-service["duracao_minutos"] // SLOT_MINUTES) * SLOT_MINUTES
                slot += timedelta(minutes=minutes)
        day += timedelta(days=1)
    return rows


def first_day_of_history(today):
    """1º de janeiro do ano passado: o ano atual fica completo e o anterior serve de comparação."""
    return date(today.year - 1, 1, 1)


# ---------- Banco ----------

def _as_time(value):
    # O conector do MySQL devolve colunas TIME como timedelta
    if isinstance(value, timedelta):
        return (datetime.min + value).time()
    return value


def load_professionals(cursor):
    cursor.execute(
        "SELECT p.id FROM profissionais p JOIN usuarios u ON u.id = p.usuario_id WHERE u.ativo = 1 ORDER BY p.id"
    )
    professionals = {row[0]: {"id": row[0], "servicos": [], "horarios": {}} for row in cursor.fetchall()}
    cursor.execute(
        "SELECT ps.profissional_id, ps.servico_id FROM profissional_servicos ps"
        " JOIN servicos s ON s.id = ps.servico_id AND s.ativo = 1"
    )
    for prof_id, service_id in cursor.fetchall():
        if prof_id in professionals:
            professionals[prof_id]["servicos"].append(service_id)
    cursor.execute("SELECT profissional_id, dia_semana, hora_inicio, hora_fim FROM horarios_trabalho")
    for prof_id, weekday, start, end in cursor.fetchall():
        if prof_id in professionals:
            professionals[prof_id]["horarios"][weekday] = (_as_time(start), _as_time(end))
    return list(professionals.values())


def load_services(cursor):
    cursor.execute("SELECT id, nome, duracao_minutos, preco FROM servicos WHERE ativo = 1")
    return {row[0]: {"nome": row[1], "duracao_minutos": int(row[2]), "preco": float(row[3])}
            for row in cursor.fetchall()}


def load_busy(cursor, first_day, last_day):
    """Agendamentos e bloqueios que já existem no período, por profissional."""
    start = datetime.combine(first_day, time.min)
    end = datetime.combine(last_day + timedelta(days=1), time.min)
    busy = {}
    cursor.execute(
        "SELECT profissional_id, inicio, fim FROM agendamentos"
        " WHERE status <> 'cancelado' AND inicio < %s AND fim > %s",
        (end, start),
    )
    for prof_id, begin, finish in cursor.fetchall():
        busy.setdefault(prof_id, []).append((begin, finish))
    cursor.execute("SELECT profissional_id, inicio, fim FROM bloqueios WHERE inicio < %s AND fim > %s", (end, start))
    for prof_id, begin, finish in cursor.fetchall():
        busy.setdefault(prof_id, []).append((begin, finish))

    # Bloqueios semanais viram um intervalo em cada dia em que valem
    cursor.execute(
        "SELECT profissional_id, dia_semana, hora_inicio, hora_fim, valido_de, valido_ate FROM bloqueios_recorrentes"
    )
    for prof_id, weekday, block_start, block_end, valid_from, valid_until in cursor.fetchall():
        day = max(first_day, valid_from)
        last = min(last_day, valid_until) if valid_until else last_day
        while day <= last:
            if day.weekday() == weekday:
                busy.setdefault(prof_id, []).append(
                    (datetime.combine(day, _as_time(block_start)), datetime.combine(day, _as_time(block_end)))
                )
            day += timedelta(days=1)
    return busy


def delete_demo(cursor):
    pattern = f"%@{DEMO_EMAIL_DOMAIN}"
    cursor.execute(
        "DELETE a FROM agendamentos a JOIN usuarios u ON u.id = a.cliente_id WHERE u.email LIKE %s", (pattern,)
    )
    appointments = cursor.rowcount
    cursor.execute("DELETE FROM usuarios WHERE email LIKE %s AND perfil = 'cliente'", (pattern,))
    return appointments, cursor.rowcount


def create_clients(cursor, clients):
    from werkzeug.security import generate_password_hash

    password_hash = generate_password_hash(PASSWORD)
    for client in clients:
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (client["email"],))
        row = cursor.fetchone()
        if row:
            client["id"] = row[0]
            continue
        cursor.execute(
            "INSERT INTO usuarios (nome, cpf, telefone, email, senha_hash, perfil)"
            " VALUES (%s, %s, %s, %s, %s, 'cliente')",
            (client["nome"], client["cpf"], client["telefone"], client["email"], password_hash),
        )
        client["id"] = cursor.lastrowid


def insert_appointments(cursor, rows):
    cursor.executemany(
        "INSERT INTO agendamentos (cliente_id, profissional_id, servico_id, inicio, fim, valor, status,"
        " cancelado_em, cancelado_por) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        [(r["cliente_id"], r["profissional_id"], r["servico_id"], r["inicio"], r["fim"], r["valor"],
          r["status"], r["cancelado_em"], r["cancelado_por"]) for r in rows],
    )


def summary(rows, now):
    realized = [r for r in rows if r["status"] != "cancelado" and r["fim"] <= now]
    by_month = {}
    for r in realized:
        key = r["inicio"].strftime("%m/%Y")
        by_month[key] = by_month.get(key, 0) + r["valor"]
    lines = [f"  {month}: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
             for month, total in sorted(by_month.items(), key=lambda kv: kv[0][3:] + kv[0][:2])]
    future = sum(1 for r in rows if r["status"] == "agendado")
    cancelled = sum(1 for r in rows if r["status"] == "cancelado")
    return (f"{len(rows)} agendamentos: {len(realized)} realizados, {future} futuros, {cancelled} cancelados.\n"
            "Receita realizada por mês:\n" + "\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Dados de demonstração para o BI.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--reset", action="store_true", help="apaga a demonstração anterior e cria de novo")
    group.add_argument("--apagar", action="store_true", help="só apaga a demonstração")
    args = parser.parse_args()

    from db import connect  # aqui dentro para os testes importarem o gerador sem o conector do MySQL

    conn = connect()
    cursor = conn.cursor()
    try:
        if args.reset or args.apagar:
            appointments, clients = delete_demo(cursor)
            print(f"Demonstração anterior apagada: {appointments} agendamentos e {clients} clientes.")
            if args.apagar:
                conn.commit()
                return

        cursor.execute(
            "SELECT COUNT(*) FROM agendamentos a JOIN usuarios u ON u.id = a.cliente_id WHERE u.email LIKE %s",
            (f"%@{DEMO_EMAIL_DOMAIN}",),
        )
        if cursor.fetchone()[0]:
            print("Os dados de demonstração já existem. Use --reset para gerar de novo.")
            return

        professionals = load_professionals(cursor)
        services = load_services(cursor)
        if not professionals or not services:
            print("Nenhum profissional ou serviço no banco. Rode antes: python database/seed.py")
            return

        now = datetime.now().replace(second=0, microsecond=0)
        today = now.date()
        first_day = first_day_of_history(today)
        last_day = today + timedelta(days=DIAS_A_FRENTE)

        rng = random.Random(f"{RANDOM_SEED}-{today.isoformat()}")
        clients = build_clients(rng)
        create_clients(cursor, clients)
        busy = load_busy(cursor, first_day, last_day)
        rows = generate(professionals, services, clients, busy, first_day, last_day, now, rng)
        insert_appointments(cursor, rows)
        conn.commit()

        print(f"Demonstração criada de {first_day:%d/%m/%Y} a {last_day:%d/%m/%Y}.")
        print(summary(rows, now))
        print(f"Clientes da demonstração: {len(clients)} (e-mail @{DEMO_EMAIL_DOMAIN}, senha {PASSWORD}).")
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
