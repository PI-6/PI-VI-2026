"""Conexão com o MySQL.

Só os módulos de backend/repositories/ devem importar este arquivo.
"""
from contextlib import contextmanager
from urllib.parse import unquote, urlparse

import mysql.connector

from config import Config
from errors import ConflictError

IntegrityError = mysql.connector.IntegrityError
DUPLICATE_ENTRY = 1062  # código do MySQL para violação de UNIQUE


def connect(database_url=None):
    url = database_url or Config.DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL não configurada. Veja o .env.example.")

    parts = urlparse(url)
    return mysql.connector.connect(
        host=parts.hostname,
        port=parts.port or 3306,
        user=unquote(parts.username or ""),
        password=unquote(parts.password or ""),
        database=parts.path.lstrip("/"),
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )


@contextmanager
def transaction():
    """Abre uma conexão, entrega um cursor e faz commit no final.

    Se der qualquer erro no meio, desfaz tudo (rollback). Assim, operações
    que mexem em várias tabelas (ex.: cadastrar profissional + serviços +
    horários) nunca ficam pela metade.
    """
    conn = connect()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except IntegrityError as error:
        conn.rollback()
        # Duas requisições ao mesmo tempo podem passar pela checagem do serviço (ex.: mesmo
        # e-mail no cadastro); o UNIQUE do banco barra a segunda, e aqui isso vira 409, não 500.
        if error.errno == DUPLICATE_ENTRY:
            raise ConflictError("Já existe um cadastro com esses dados.") from error
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def placeholders(values):
    """Gera "%s, %s, %s" para usar em cláusulas IN.

    Só os marcadores são montados na string; os valores continuam indo
    separados como parâmetros, então não há risco de SQL injection.
    """
    return ", ".join(["%s"] * len(values))


def fetch_one(sql, params=()):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def fetch_all(sql, params=()):
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def execute(sql, params=()):
    """Executa INSERT/UPDATE/DELETE e devolve o id gerado (quando houver)."""
    with transaction() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid
