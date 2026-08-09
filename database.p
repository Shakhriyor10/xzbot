import sqlite3
from datetime import datetime
from config import DB_NAME, OWNER_ID

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ads_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            group_link TEXT,
            report_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            added_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_activity (
            user_id INTEGER,
            full_name TEXT,
            username TEXT,
            msg_date TEXT,
            msg_count INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, msg_date)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE daily_activity ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            session_info TEXT,
            added_date TEXT
        )
    ''')
    conn.commit()

def save_user(user):
    username = user.username.lower() if user.username else None
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
        (user.id, username, user.full_name)
    )
    conn.commit()

def get_all_admins():
    cursor.execute("SELECT user_id FROM admins")
    db_admins = [row[0] for row in cursor.fetchall()]
    return list(set([OWNER_ID] + db_admins))

def add_group_message(user_id, full_name, username, is_admin):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO daily_activity (user_id, full_name, username, msg_date, msg_count, is_admin)
        VALUES (?, ?, ?, ?, 1, ?)
        ON CONFLICT(user_id, msg_date) DO UPDATE SET
            msg_count = msg_count + 1,
            full_name = excluded.full_name,
            username = excluded.username,
            is_admin = excluded.is_admin
    ''', (user_id, full_name, username, today, is_admin))
    conn.commit()

def get_top_active_by_role(is_admin, limit=5):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT full_name, username, msg_count 
        FROM daily_activity 
        WHERE msg_date = ? AND is_admin = ?
        ORDER BY msg_count DESC 
        LIMIT ?
    ''', (today, is_admin, limit))
    return cursor.fetchall()

