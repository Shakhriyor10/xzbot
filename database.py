import sqlite3
from datetime import datetime

from config import DB_NAME


def upgrade_admins_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(admins)")
    columns = {row[1] for row in cursor.fetchall()}

    if "region" not in columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN region TEXT")

    if "birth_date" not in columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN birth_date TEXT")

    if "phone" not in columns:
        cursor.execute("ALTER TABLE admins ADD COLUMN phone TEXT")

    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Adminlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT
        )
    """)
    
    # 3. Shikoyatlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            username TEXT,
            complaint_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 4. Reklamalar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ads_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            username TEXT,
            group_name TEXT,
            group_link TEXT,
            created_at DATE DEFAULT CURRENT_DATE
        )
    """)

    # 5. Guruh faolligi jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            group_id INTEGER,
            full_name TEXT,
            username TEXT,
            message_count INTEGER DEFAULT 1,
            created_at DATE DEFAULT CURRENT_DATE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connected_accounts (
            owner_user_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            username TEXT NOT NULL DEFAULT '',
            display_name TEXT NOT NULL DEFAULT '',
            session_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (owner_user_id, account_id),
            UNIQUE (session_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_texts (
            owner_user_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            text_content TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (owner_user_id, account_id),
            FOREIGN KEY (owner_user_id, account_id)
                REFERENCES connected_accounts(owner_user_id, account_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_api_credentials (
            owner_user_id INTEGER PRIMARY KEY,
            api_id INTEGER NOT NULL,
            encrypted_api_hash TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    upgrade_admins_table()



# 👤 --- FOYDALANUVCHILAR FUNKSIYALARI --- 👤

def save_user(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, full_name, username)
        VALUES (?, ?, ?)
    """, (user.id, user.full_name, user.username or ""))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


# 🛠 --- ADMINLAR FUNKSIYALARI --- 🛠

def add_admin_to_db(admin_id, full_name="", username="", region="", birth_date="", phone=""):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO admins (admin_id, full_name, username, region, birth_date, phone) VALUES (?, ?, ?, ?, ?, ?)", (admin_id, full_name, username, region, birth_date, phone))
    conn.commit()
    conn.close()

def remove_admin_from_db(admin_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE admin_id = ?", (admin_id,))
    conn.commit()
    conn.close()

def get_all_admins():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT admin_id FROM admins")
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

def get_admins_with_names():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT admin_id, full_name, username, region, birth_date, phone FROM admins")
    admins = cursor.fetchall()
    conn.close()
    return admins

# ⚠️ --- SHIKOYAT FUNKSIYALARI --- ⚠️

def save_admin_complaint(user_id, full_name, username, text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints (user_id, full_name, username, complaint_text)
        VALUES (?, ?, ?, ?)
    """, (user_id, full_name, username, text))
    conn.commit()
    conn.close()


# 📩 --- REKLAMA FUNKSIYALARI --- 📩

def save_ad_submission(user_id, full_name, username, group_name, group_link):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ads_history (user_id, full_name, username, group_name, group_link, created_at)
        VALUES (?, ?, ?, ?, ?, DATE('now', 'localtime'))
    """, (user_id, full_name, username, group_name, group_link))
    conn.commit()
    conn.close()

def get_today_ads():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT group_name, group_link, COUNT(*) 
        FROM ads_history 
        WHERE created_at = DATE('now', 'localtime')
        GROUP BY group_name
        ORDER BY COUNT(*) DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_ads_stat():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ads_history")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT group_name) FROM ads_history")
    total_groups = cursor.fetchone()[0]

    conn.close()
    return total_count, total_groups


# 📊 --- GURUH FAOLLIGI FUNKSIYALARI --- 📊


def log_group_message(user_id, group_id, full_name, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT id
        FROM group_activity
        WHERE user_id = ?
          AND group_id = ?
          AND created_at = ?
    """, (user_id, group_id, today))

    row = cursor.fetchone()

    if row:
        cursor.execute("""
            UPDATE group_activity
            SET message_count = message_count + 1,
                full_name = ?,
                username = ?
            WHERE id = ?
        """, (
            full_name,
            username,
            row[0]
        ))
    else:
        cursor.execute("""
            INSERT INTO group_activity
            (
                user_id,
                group_id,
                full_name,
                username,
                message_count,
                created_at
            )
            VALUES (?, ?, ?, ?, 1, ?)
        """, (
            user_id,
            group_id,
            full_name,
            username,
            today
        ))

    conn.commit()
    conn.close()


# ============================================================
# 📅 BUGUNGI ODDIY FOYDALANUVCHILAR
# ============================================================

def get_top_daily_active(
    group_id=None,
    limit=5,
    exclude_user_ids=None
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    exclude_user_ids = exclude_user_ids or []

    if group_id is not None:
        params = [group_id, today]

        query = """
            SELECT
                user_id,
                full_name,
                username,
                SUM(message_count) AS total
            FROM group_activity
            WHERE group_id = ?
              AND created_at = ?
        """

        if exclude_user_ids:
            placeholders = ",".join(
                "?" for _ in exclude_user_ids
            )
            query += f"""
              AND user_id NOT IN ({placeholders})
            """
            params.extend(exclude_user_ids)

        query += """
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """

        params.append(limit)

        cursor.execute(query, params)

    else:
        params = [today]

        query = """
            SELECT
                user_id,
                full_name,
                username,
                SUM(message_count) AS total
            FROM group_activity
            WHERE created_at = ?
        """

        if exclude_user_ids:
            placeholders = ",".join(
                "?" for _ in exclude_user_ids
            )
            query += f"""
              AND user_id NOT IN ({placeholders})
            """
            params.extend(exclude_user_ids)

        query += """
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """

        params.append(limit)

        cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    return rows


# ============================================================
# 📆 OYLIK ODDIY FOYDALANUVCHILAR
# ============================================================

def get_top_monthly_active(
    group_id=None,
    limit=5,
    exclude_user_ids=None
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    month_start = datetime.now().strftime("%Y-%m-01")

    exclude_user_ids = exclude_user_ids or []

    if group_id is not None:
        params = [group_id, month_start]

        query = """
            SELECT
                user_id,
                full_name,
                username,
                SUM(message_count) AS total
            FROM group_activity
            WHERE group_id = ?
              AND created_at >= ?
        """

        if exclude_user_ids:
            placeholders = ",".join(
                "?" for _ in exclude_user_ids
            )
            query += f"""
              AND user_id NOT IN ({placeholders})
            """
            params.extend(exclude_user_ids)

        query += """
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """

        params.append(limit)

        cursor.execute(query, params)

    else:
        params = [month_start]

        query = """
            SELECT
                user_id,
                full_name,
                username,
                SUM(message_count) AS total
            FROM group_activity
            WHERE created_at >= ?
        """

        if exclude_user_ids:
            placeholders = ",".join(
                "?" for _ in exclude_user_ids
            )
            query += f"""
              AND user_id NOT IN ({placeholders})
            """
            params.extend(exclude_user_ids)

        query += """
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
        """

        params.append(limit)

        cursor.execute(query, params)

    rows = cursor.fetchall()

    conn.close()

    return rows


# ============================================================
# 👑 GURUH ADMINLARI AKTIVLIGI
# ============================================================

def get_group_admin_activity(
    group_id,
    admin_ids,
    monthly=False
):
    if not admin_ids:
        return []

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    placeholders = ",".join(
        "?" for _ in admin_ids
    )

    if monthly:
        date_condition = "created_at >= ?"
        date_value = datetime.now().strftime("%Y-%m-01")
    else:
        date_condition = "created_at = ?"
        date_value = datetime.now().strftime("%Y-%m-%d")

    query = f"""
        SELECT
            user_id,
            full_name,
            username,
            SUM(message_count) AS total
        FROM group_activity
        WHERE group_id = ?
          AND user_id IN ({placeholders})
          AND {date_condition}
        GROUP BY user_id
        ORDER BY total DESC
    """

    params = [
        group_id,
        *admin_ids,
        date_value
    ]

    cursor.execute(query, params)

    rows = cursor.fetchall()

    # Bazada hali yozuvi yo'q adminlar ham chiqishi kerak.
    found = {
        row[0]: row
        for row in rows
    }

    result = list(rows)

    for admin_id in admin_ids:
        if admin_id not in found:
            try:
                cursor.execute("""
                    SELECT full_name, username
                    FROM users
                    WHERE user_id = ?
                """, (admin_id,))

                user = cursor.fetchone()

                if user:
                    full_name, username = user
                else:
                    full_name = f"ID: {admin_id}"
                    username = ""

            except Exception:
                full_name = f"ID: {admin_id}"
                username = ""

            result.append((
                admin_id,
                full_name,
                username,
                0
            ))

    result.sort(
        key=lambda x: x[3],
        reverse=True
    )

    conn.close()

    return result


# ============================================================
# 📆 ESKI FUNKSIYALAR — MOSLIK UCHUN
# ============================================================

def get_top_weekly_active(limit=5):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            full_name,
            username,
            SUM(message_count) AS total
        FROM group_activity
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_top_active_by_role(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            full_name,
            username,
            SUM(message_count) AS total
        FROM group_activity
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows


# 🔄 --- ALIASLAR (ESKI IMPORTLAR XATOLIK BERMASLIGI UCHUN) --- 🔄
add_group_message = log_group_message

# ============================================================

# ============================================================
# 📊 REKLAMA GURUHLARI — TOP 10
# ============================================================

def get_top_ad_groups(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT group_name, group_link, COUNT(*) AS cnt
        FROM ads_history
        GROUP BY group_name, group_link
        ORDER BY cnt DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# 👥 REKLAMA KELGAN GURUHLAR
# ============================================================

def get_ad_groups(limit=50):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT group_name, group_link, MAX(created_at) AS last_date
        FROM ads_history
        GROUP BY group_name, group_link
        ORDER BY last_date DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# CONNECTED TELEGRAM ACCOUNTS
# ============================================================

def save_connected_account(
    owner_user_id,
    account_id,
    username,
    display_name,
    session_name,
):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO connected_accounts (
                owner_user_id, account_id, username, display_name, session_name
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(owner_user_id, account_id) DO UPDATE SET
                username = excluded.username,
                display_name = excluded.display_name,
                session_name = excluded.session_name
        """, (
            int(owner_user_id),
            int(account_id),
            username or "",
            display_name or "",
            session_name,
        ))


def get_connected_accounts(owner_user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
            SELECT account_id, username, display_name, session_name
            FROM connected_accounts
            WHERE owner_user_id = ?
            ORDER BY created_at, account_id
        """, (int(owner_user_id),)).fetchall()


def get_connected_account(owner_user_id, account_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
            SELECT account_id, username, display_name, session_name
            FROM connected_accounts
            WHERE owner_user_id = ? AND account_id = ?
        """, (int(owner_user_id), int(account_id))).fetchone()


def save_account_api_credentials(owner_user_id, api_id, encrypted_api_hash):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO account_api_credentials (
                owner_user_id, api_id, encrypted_api_hash
            ) VALUES (?, ?, ?)
            ON CONFLICT(owner_user_id) DO UPDATE SET
                api_id = excluded.api_id,
                encrypted_api_hash = excluded.encrypted_api_hash,
                updated_at = CURRENT_TIMESTAMP
        """, (int(owner_user_id), int(api_id), encrypted_api_hash))


def get_account_api_credentials(owner_user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
            SELECT api_id, encrypted_api_hash
            FROM account_api_credentials
            WHERE owner_user_id = ?
        """, (int(owner_user_id),)).fetchone()


def save_account_text(owner_user_id, account_id, text_content):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT INTO account_texts (owner_user_id, account_id, text_content)
            VALUES (?, ?, ?)
            ON CONFLICT(owner_user_id, account_id) DO UPDATE SET
                text_content = excluded.text_content,
                updated_at = CURRENT_TIMESTAMP
        """, (int(owner_user_id), int(account_id), text_content))


def get_account_text(owner_user_id, account_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("""
            SELECT text_content
            FROM account_texts
            WHERE owner_user_id = ? AND account_id = ?
        """, (int(owner_user_id), int(account_id))).fetchone()
    return row[0] if row else None


def delete_account_text(owner_user_id, account_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute("""
            DELETE FROM account_texts
            WHERE owner_user_id = ? AND account_id = ?
        """, (int(owner_user_id), int(account_id)))
        return cursor.rowcount > 0


def get_account_ad_groups(limit=50):
    """Return stable row IDs for the existing advertisement group history."""
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
            SELECT MAX(rowid), group_name, group_link, MAX(created_at)
            FROM ads_history
            GROUP BY group_name, group_link
            ORDER BY MAX(created_at) DESC
            LIMIT ?
        """, (int(limit),)).fetchall()


def get_account_ad_group(row_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("""
            SELECT group_name, group_link
            FROM ads_history
            WHERE rowid = ?
        """, (int(row_id),)).fetchone()

# ============================================================
# 👤 ADMIN MA'LUMOTLARI UCHUN YANGI USTUNLAR
# ============================================================

