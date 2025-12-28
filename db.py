import sqlite3
import time
from datetime import datetime, timedelta

conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS dialogs (
    user_id INTEGER,
    role TEXT,
    content TEXT,
    created TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS daily_limits (
    user_id INTEGER PRIMARY KEY,
    count INTEGER DEFAULT 0,
    day TEXT
)
""")
conn.commit()


def get_dialog(user_id):
    cur.execute("SELECT role, content FROM dialogs WHERE user_id=?", (user_id,))
    return [{"role": r, "content": c} for r, c in cur.fetchall()]


def add_message(user_id, role, content):
    cur.execute(
        "INSERT INTO dialogs (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()


def reset_dialog(user_id):
    cur.execute("DELETE FROM dialogs WHERE user_id=?", (user_id,))
    conn.commit()


def get_today_count(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT count, day FROM daily_limits WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row or row[1] != today:
        cur.execute(
            "REPLACE INTO daily_limits (user_id, count, day) VALUES (?, 0, ?)",
            (user_id, today)
        )
        conn.commit()
        return 0

    return row[0]


def inc_today_count(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    count = get_today_count(user_id) + 1
    cur.execute(
        "REPLACE INTO daily_limits (user_id, count, day) VALUES (?, ?, ?)",
        (user_id, count, today)
    )
    conn.commit()


def reset_all_limits():
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("UPDATE daily_limits SET count=0, day=?", (today,))
    conn.commit()


def daily_reset_loop():
    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time.sleep((tomorrow - now).total_seconds())
        reset_all_limits()
