"""db.transaction: violação de UNIQUE vira 409 em vez de erro 500."""
import pytest

import db
from errors import ConflictError


class FakeConnection:
    def __init__(self, error):
        self.error = error
        self.rolled_back = False

    def cursor(self, dictionary=False):
        return self

    def execute(self, sql, params=()):
        raise self.error

    def commit(self):
        pass

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def run_with(error):
    connection = FakeConnection(error)
    original, db.connect = db.connect, lambda *args, **kwargs: connection
    try:
        with db.transaction() as cursor:
            cursor.execute("INSERT ...")
    finally:
        db.connect = original
        assert connection.rolled_back


def test_duplicate_entry_becomes_conflict():
    error = db.IntegrityError("Duplicate entry")
    error.errno = db.DUPLICATE_ENTRY
    with pytest.raises(ConflictError):
        run_with(error)


def test_other_integrity_errors_are_not_hidden():
    error = db.IntegrityError("Cannot add or update a child row")
    error.errno = 1452
    with pytest.raises(db.IntegrityError):
        run_with(error)
