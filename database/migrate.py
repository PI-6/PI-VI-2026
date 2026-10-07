"""Aplica as migrations de database/migrations/ em ordem.

Uso (com o venv do backend ativo, a partir da raiz do projeto):
    python database/migrate.py

Cada arquivo .sql roda uma única vez; o controle fica na tabela schema_migrations.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from db import connect  # noqa: E402

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def split_statements(sql):
    # Tira os comentários "--" antes de dividir, porque eles podem conter ";".
    # Nossos arquivos não têm ";" nem "--" dentro de textos, então isso é suficiente.
    without_comments = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    return [stmt.strip() for stmt in without_comments.split(";") if stmt.strip()]


def main():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
               versao VARCHAR(100) PRIMARY KEY,
               aplicada_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
           )"""
    )
    cursor.execute("SELECT versao FROM schema_migrations")
    applied = {row[0] for row in cursor.fetchall()}

    pending = [f for f in sorted(MIGRATIONS_DIR.glob("*.sql")) if f.name not in applied]
    if not pending:
        print("Banco já está atualizado.")

    for file in pending:
        print(f"Aplicando {file.name}...")
        # Obs.: no MySQL, CREATE/ALTER TABLE fazem commit implícito, então se uma
        # migration falhar no meio é preciso corrigir o banco na mão antes de rodar de novo.
        for statement in split_statements(file.read_text(encoding="utf-8")):
            cursor.execute(statement)
        cursor.execute("INSERT INTO schema_migrations (versao) VALUES (%s)", (file.name,))
        conn.commit()

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
