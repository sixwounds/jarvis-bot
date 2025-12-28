import sqlite3
from datetime import date

conn = sqlite3.connect("stats.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS usage (
    user_id INTEGER,
    day TEXT,
    count INTEGER
)
""")
conn.commit()


def get_count(user_id: int) -> int:
    today = date.today().isoformat()
    cur.execute("SELECT count FROM usage WHERE user_id=? AND day=?", (user_id, today))
    row = cur.fetchone()
    return row[0] if row else 0


def inc_count(user_id: int):
    today = date.today().isoformat()
    cur.execute("SELECT count FROM usage WHERE user_id=? AND day=?", (user_id, today))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE usage SET count=count+1 WHERE user_id=? AND day=?", (user_id, today))
    else:
        cur.execute("INSERT INTO usage VALUES (?, ?, 1)", (user_id, today))
    conn.commit()


def reset_day():
    cur.execute("DELETE FROM usage")
    conn.commit()
