import sqlite3

import database
from account_credentials import AccountCredentialStore


def test_api_hash_is_encrypted_and_can_be_restored(tmp_path, monkeypatch):
    db_path = tmp_path / "credentials.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.init_db()

    store = AccountCredentialStore()
    store.directory = tmp_path / "sessions"
    store.key_path = store.directory / ".credentials.key"
    api_hash = "0123456789abcdef0123456789abcdef"

    store.save(100, 12345, api_hash)
    assert store.get(100) == (12345, api_hash)

    with sqlite3.connect(db_path) as connection:
        encrypted = connection.execute(
            "SELECT encrypted_api_hash FROM account_api_credentials"
        ).fetchone()[0]
    assert encrypted != api_hash
    assert api_hash not in encrypted
