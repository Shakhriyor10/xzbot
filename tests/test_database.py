import sqlite3
from types import SimpleNamespace

import database


def test_database_initialization_and_admin_roundtrip(tmp_path, monkeypatch):
    db_path = tmp_path / "bot.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))

    database.init_db()
    database.add_admin_to_db(42, "Admin", "admin", "Toshkent", "01.01.2000", "+998")

    assert database.get_all_admins() == [42]
    assert database.get_admins_with_names() == [
        (42, "Admin", "admin", "Toshkent", "01.01.2000", "+998")
    ]

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert {"users", "admins", "complaints", "ads_history", "group_activity"} <= tables


def test_user_ad_and_activity_flows(tmp_path, monkeypatch):
    db_path = tmp_path / "bot.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.init_db()

    database.save_user(SimpleNamespace(id=7, full_name="User", username="user"))
    database.save_ad_submission(7, "User", "user", "Group", "https://t.me/group")
    database.log_group_message(7, -1001, "User", "user")
    database.log_group_message(7, -1001, "User", "user")

    assert database.get_all_users() == [7]
    assert database.get_all_ads_stat() == (1, 1)
    assert database.get_top_ad_groups() == [("Group", "https://t.me/group", 1)]
    assert database.get_top_daily_active(group_id=-1001) == [(7, "User", "user", 2)]
