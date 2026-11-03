"""Repositórios em memória para testar os serviços sem precisar do MySQL.

Têm as mesmas funções dos repositórios reais, mas guardam tudo em listas.
"""
from datetime import date

from werkzeug.security import generate_password_hash


class FakeUserRepository:
    def __init__(self):
        self.rows = []

    def add(self, **fields):
        user = {"id": len(self.rows) + 1, "cpf": None, "telefone": None, "ativo": 1, **fields}
        if "senha" in user:
            user["senha_hash"] = generate_password_hash(user.pop("senha"))
        self.rows.append(user)
        return user

    def find_by_id(self, user_id):
        return next((u for u in self.rows if u["id"] == user_id), None)

    def find_by_email(self, email):
        return next((u for u in self.rows if u["email"] == email), None)

    def find_by_cpf(self, cpf):
        return next((u for u in self.rows if u["cpf"] == cpf), None)

    def create_client(self, nome, cpf, telefone, email, senha_hash):
        user = self.add(nome=nome, cpf=cpf, telefone=telefone, email=email,
                        senha_hash=senha_hash, perfil="cliente")
        return user["id"]


class FakeCatalogRepository:
    def __init__(self):
        self.rows = []

    def add(self, nome, duracao_minutos=30, preco=50.0, descricao=None):
        row = {"id": len(self.rows) + 1, "nome": nome, "descricao": descricao,
               "duracao_minutos": duracao_minutos, "preco": preco, "ativo": 1}
        self.rows.append(row)
        return row["id"]

    def _active(self):
        return [r for r in self.rows if r["ativo"]]

    def list_active(self):
        return self._active()

    def find_active_by_id(self, service_id):
        return next((r for r in self._active() if r["id"] == service_id), None)

    def find_active_by_name(self, nome):
        return next((r for r in self._active() if r["nome"] == nome), None)

    def find_active_ids(self, service_ids):
        return {r["id"] for r in self._active() if r["id"] in service_ids}

    def create(self, nome, descricao, duracao_minutos, preco):
        return self.add(nome, duracao_minutos, float(preco), descricao)

    def update(self, service_id, nome, descricao, duracao_minutos, preco):
        row = self.find_active_by_id(service_id)
        row.update(nome=nome, descricao=descricao, duracao_minutos=duracao_minutos, preco=float(preco))

    def deactivate(self, service_id):
        self.find_active_by_id(service_id)["ativo"] = 0


class FakeProfessionalRepository:
    def __init__(self, users):
        self.users = users
        self.rows = []

    def _build(self, row):
        user = self.users.find_by_id(row["usuario_id"])
        if not user["ativo"]:
            return None
        return {"id": row["id"], "usuario_id": user["id"], "nome": user["nome"],
                "email": user["email"], "telefone": user["telefone"], "perfil": user["perfil"],
                "servicos": [{"id": i} for i in row["servicos"]],
                # Igual ao repositório real, que devolve os horários como "HH:MM"
                "horarios": [{**h, "hora_inicio": h["hora_inicio"].strftime("%H:%M"),
                              "hora_fim": h["hora_fim"].strftime("%H:%M")} for h in row["horarios"]]}

    def list_active(self):
        return [p for p in (self._build(r) for r in self.rows) if p]

    def find_active_by_id(self, professional_id):
        row = next((r for r in self.rows if r["id"] == professional_id), None)
        return self._build(row) if row else None

    def list_active_by_service(self, service_id):
        found = [p for p in self.list_active() if {"id": service_id} in p["servicos"]]
        return [{"id": p["id"], "nome": p["nome"]} for p in sorted(found, key=lambda p: p["nome"])]

    def link(self, user_id, service_ids=(), hours=()):
        """Transforma um usuário que já existe em profissional."""
        row = {"id": len(self.rows) + 1, "usuario_id": user_id,
               "servicos": list(service_ids), "horarios": list(hours)}
        self.rows.append(row)
        return row["id"]

    def create(self, user, service_ids, hours):
        created = self.users.add(**user)
        return self.link(created["id"], service_ids, hours)

    def update(self, professional_id, user, service_ids, hours):
        row = next(r for r in self.rows if r["id"] == professional_id)
        stored = self.users.find_by_id(row["usuario_id"])
        stored.update({k: val for k, val in user.items() if k != "senha_hash" or val})
        row.update(servicos=service_ids, horarios=hours)

    def deactivate(self, professional_id):
        row = next(r for r in self.rows if r["id"] == professional_id)
        self.users.find_by_id(row["usuario_id"])["ativo"] = 0


class FakeAppointmentRepository:
    def __init__(self, users=None, catalog=None, professionals=None):
        self.rows = []
        # Usados só na agenda do dia, para preencher os nomes como o JOIN do repositório real
        self.users = users
        self.catalog = catalog
        self.professionals = professionals
        # Liga para simular outro cliente gravando o mesmo horário entre a checagem e o INSERT
        self.simulate_race = False

    def add(self, profissional_id, inicio, fim, status="agendado", **fields):
        row = {"id": len(self.rows) + 1, "profissional_id": profissional_id,
               "inicio": inicio, "fim": fim, "status": status, **fields}
        self.rows.append(row)
        return row["id"]

    def create_if_free(self, cliente_id, professional_id, service_id, inicio, fim, valor):
        if self.simulate_race or self.list_busy_between(professional_id, inicio, fim):
            return None
        return self.add(professional_id, inicio, fim, cliente_id=cliente_id, servico_id=service_id, valor=valor)

    def list_day(self, start, end, professional_id=None):
        rows = [r for r in self.rows if r["status"] != "cancelado" and r["inicio"] < end and r["fim"] > start
                and (professional_id is None or r["profissional_id"] == professional_id)]
        result = []
        for r in sorted(rows, key=lambda r: r["inicio"]):
            service = next(s for s in self.catalog.rows if s["id"] == r["servico_id"])
            professional = next(p for p in self.professionals.rows if p["id"] == r["profissional_id"])
            result.append({
                **r,
                "cliente_nome": self.users.find_by_id(r["cliente_id"])["nome"],
                "profissional_nome": self.users.find_by_id(professional["usuario_id"])["nome"],
                "servico_nome": service["nome"],
            })
        return result

    def find_by_id(self, appointment_id):
        return next((r for r in self.rows if r["id"] == appointment_id), None)

    def cancel(self, appointment_id, cancelled_by, cancelled_at):
        row = self.find_by_id(appointment_id)
        if not row or row["status"] != "agendado":
            return False
        row.update(status="cancelado", cancelado_por=cancelled_by, cancelado_em=cancelled_at)
        return True

    def list_busy_between(self, professional_id, start, end):
        return sorted(
            ({"inicio": r["inicio"], "fim": r["fim"]} for r in self.rows
             if r["profissional_id"] == professional_id and r["status"] != "cancelado"
             and r["inicio"] < end and r["fim"] > start),
            key=lambda r: r["inicio"],
        )


class FakeBlockRepository:
    """Bloqueios em memória, em duas listas como as duas tabelas reais (ids independentes).

    Recebe os agendamentos para checar conflito, como o SQL real.
    """

    def __init__(self, appointments, professionals):
        self.appointments = appointments
        self.professionals = professionals
        self.tables = {"pontual": [], "semanal": []}

    @property
    def rows(self):
        return self.tables["pontual"] + self.tables["semanal"]

    def add(self, profissional_id, tipo="pontual", motivo=None, criado_por=1, **fields):
        table = self.tables[tipo]
        row = {"id": len(table) + 1, "profissional_id": profissional_id, "tipo": tipo,
               "motivo": motivo, "criado_por": criado_por, **fields}
        if tipo == "semanal":
            row.setdefault("valido_de", date(2026, 1, 1))  # nos testes, já valendo antes de "agora"
            row.setdefault("valido_ate", None)
        table.append(row)
        return row["id"]

    def _with_name(self, row):
        professional = self.professionals.find_active_by_id(row["profissional_id"])
        return {**row, "profissional_nome": professional["nome"] if professional else None}

    def find_by_id(self, kind, block_id):
        row = next((r for r in self.tables[kind] if r["id"] == block_id), None)
        return self._with_name(row) if row else None

    def list_for_professional(self, professional_id, since):
        return [self._with_name(r) for r in self.rows if r["profissional_id"] == professional_id and (
            r["fim"] > since if r["tipo"] == "pontual"
            else r["valido_ate"] is None or r["valido_ate"] >= since.date())]

    def list_between(self, start, end, professional_id=None):
        def overlaps(r):
            if r["tipo"] == "pontual":
                return r["inicio"] < end and r["fim"] > start
            return r["valido_de"] <= end.date() and (r["valido_ate"] is None or r["valido_ate"] >= start.date())
        return [self._with_name(r) for r in self.rows
                if (professional_id is None or r["profissional_id"] == professional_id)
                and self.professionals.find_active_by_id(r["profissional_id"]) and overlaps(r)]

    def create_if_no_conflict(self, block, now):
        active = [r for r in self.appointments.rows
                  if r["profissional_id"] == block["profissional_id"] and r["status"] != "cancelado"
                  and r["fim"] > now]
        if block["tipo"] == "pontual":
            conflicts = [r for r in active if r["inicio"] < block["fim"] and r["fim"] > block["inicio"]]
        else:
            conflicts = [r for r in active if r["inicio"].weekday() == block["dia_semana"]
                         and r["inicio"].time() < block["hora_fim"] and r["fim"].time() > block["hora_inicio"]
                         and r["inicio"].date() >= block["valido_de"]
                         and (block["valido_ate"] is None or r["inicio"].date() <= block["valido_ate"])]
        if conflicts:
            return None, sorted(conflicts, key=lambda r: r["inicio"])
        return self.add(**{k: val for k, val in block.items() if k != "id"}), []

    def delete(self, kind, block_id):
        self.tables[kind] = [r for r in self.tables[kind] if r["id"] != block_id]


class FakeFinanceRepository:
    """Agregações do Financeiro calculadas em Python sobre os agendamentos em memória.

    Mesma regra do SQL real: realizado = não cancelado e já terminado (fim <= now).
    """

    def __init__(self, appointments, professionals, users, catalog):
        self.appointments = appointments
        self.professionals = professionals
        self.users = users
        self.catalog = catalog

    def _realized(self, start, end, now):
        return [r for r in self.appointments.rows
                if r["status"] != "cancelado" and r["fim"] <= now and start <= r["inicio"] < end]

    def monthly_totals(self, start, end, now):
        groups = {}
        for r in self._realized(start, end, now):
            key = (r["inicio"].year, r["inicio"].month)
            group = groups.setdefault(key, {"ano": key[0], "mes": key[1], "receita": 0, "atendimentos": 0})
            group["receita"] += r["valor"]
            group["atendimentos"] += 1
        return [groups[key] for key in sorted(groups)]

    def _professional_name(self, professional_id):
        professional = next(p for p in self.professionals.rows if p["id"] == professional_id)
        return self.users.find_by_id(professional["usuario_id"])["nome"]

    def by_professional(self, start, end, now):
        groups = {}
        for r in self._realized(start, end, now):
            group = groups.setdefault(r["profissional_id"], {
                "id": r["profissional_id"], "nome": self._professional_name(r["profissional_id"]),
                "atendimentos": 0, "clientes": set(), "receita": 0})
            group["atendimentos"] += 1
            group["clientes"].add(r["cliente_id"])
            group["receita"] += r["valor"]
        rows = [{**g, "clientes": len(g["clientes"])} for g in groups.values()]
        return sorted(rows, key=lambda g: (-g["atendimentos"], -g["receita"], g["nome"]))


class FakeEmailSender:
    """Guarda os e-mails em vez de enviar. Com fail=True simula o SMTP fora do ar."""

    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    def send(self, to, subject, text, html=None):
        if self.fail:
            raise ConnectionRefusedError("SMTP fora do ar")
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html})
