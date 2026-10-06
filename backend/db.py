import os
import sqlite3
from urllib.parse import urlparse, unquote

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Erros de "valor duplicado" nos dois bancos
IntegrityErrors = (mysql.connector.IntegrityError, sqlite3.IntegrityError)


def _usa_mysql():
    return bool(os.getenv("DATABASE_URL"))


def _conectar():
    url = os.getenv("DATABASE_URL")
    if url:
        p = urlparse(url)
        return mysql.connector.connect(
            host=p.hostname,
            port=p.port or 3306,
            user=unquote(p.username or ""),
            password=unquote(p.password or ""),
            database=p.path.lstrip("/"),
        )

    # Sem DATABASE_URL: banco local temporário, só para desenvolvimento
    caminho = os.path.join(os.path.dirname(__file__), "dev.db")
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'cliente'
        )"""
    )
    return conn


def buscar_um(sql, params=()):
    conn = _conectar()
    try:
        if _usa_mysql():
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            resultado = cur.fetchone()
            cur.close()
            return resultado
        cur = conn.execute(sql.replace("%s", "?"), params)
        linha = cur.fetchone()
        return dict(linha) if linha else None
    finally:
        conn.close()


def executar(sql, params=()):
    conn = _conectar()
    try:
        if _usa_mysql():
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            cur.close()
        else:
            conn.execute(sql.replace("%s", "?"), params)
            conn.commit()
    finally:
        conn.close()