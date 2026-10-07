"""Repositórios em memória para testar os serviços sem precisar do MySQL.

Têm as mesmas funções dos repositórios reais, mas guardam tudo em listas.
"""
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
                "servicos": [{"id": i} for i in row["servicos"]], "horarios": row["horarios"]}

    def list_active(self):
        return [p for p in (self._build(r) for r in self.rows) if p]

    def find_active_by_id(self, professional_id):
        row = next((r for r in self.rows if r["id"] == professional_id), None)
        return self._build(row) if row else None

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
