import database


def test_connected_account_and_text_roundtrip(tmp_path, monkeypatch):
    db_path = tmp_path / "accounts.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.init_db()

    database.save_connected_account(10, 20, "alice", "Alice", "session_10_20")
    assert database.get_connected_accounts(10) == [
        (20, "alice", "Alice", "session_10_20")
    ]

    database.save_account_text(10, 20, "Forwarded text")
    assert database.get_account_text(10, 20) == "Forwarded text"
    assert database.delete_account_text(10, 20) is True
    assert database.get_account_text(10, 20) is None


def test_account_ad_groups_have_stable_row_ids(tmp_path, monkeypatch):
    db_path = tmp_path / "groups.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.init_db()
    database.save_ad_submission(1, "User", "user", "Group", "https://t.me/group")

    row_id, name, link, _date = database.get_account_ad_groups()[0]
    assert name == "Group"
    assert link == "https://t.me/group"
    assert database.get_account_ad_group(row_id) == ("Group", "https://t.me/group")
