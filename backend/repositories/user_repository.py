import db


def find_by_id(user_id):
    return db.fetch_one(
        "SELECT id, nome, cpf, telefone, email, perfil, ativo FROM usuarios WHERE id = %s",
        (user_id,),
    )


def find_by_email(email):
    # Única consulta que traz o hash da senha: só o login precisa dele
    return db.fetch_one(
        "SELECT id, nome, cpf, telefone, email, perfil, ativo, senha_hash FROM usuarios WHERE email = %s",
        (email,),
    )


def find_by_cpf(cpf):
    return db.fetch_one(
        "SELECT id, nome, cpf, telefone, email, perfil, ativo FROM usuarios WHERE cpf = %s",
        (cpf,),
    )


def create_client(nome, cpf, telefone, email, senha_hash):
    return db.execute(
        "INSERT INTO usuarios (nome, cpf, telefone, email, senha_hash, perfil)"
        " VALUES (%s, %s, %s, %s, %s, 'cliente')",
        (nome, cpf, telefone, email, senha_hash),
    )
