import sqlite3
from datetime import date

conn = sqlite3.connect("memory.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS dialogs (
    user_id INTEGER,
    role TEXT,
    content TEXT,
    created DATE DEFAULT CURRENT_DATE
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


def count_today_messages(user_id):
    today = str(date.today())
    cur.execute("""
        SELECT COUNT(*) FROM dialogs
        WHERE user_id=? AND role='user' AND created=?
    """, (user_id, today))
    return cur.fetchone()[0]
