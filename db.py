import sqlite3
from threading import Lock
from datetime import datetime
import time

lock = Lock()
conn = sqlite3.connect("dialog.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS dialog (user_id INTEGER, role TEXT, content TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS daily (user_id INTEGER PRIMARY KEY, count INTEGER, day TEXT)")
conn.commit()


def get_dialog(uid):
    with lock:
        cur.execute("SELECT role, content FROM dialog WHERE user_id=?", (uid,))
        return [{"role": r, "content": c} for r, c in cur.fetchall()]


def add_message(uid, role, content):
    with lock:
        cur.execute("INSERT INTO dialog VALUES (?, ?, ?)", (uid, role, content))
        conn.commit()


def reset_dialog(uid):
    with lock:
        cur.execute("DELETE FROM dialog WHERE user_id=?", (uid,))
        conn.commit()


def get_today_count(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    with lock:
        cur.execute("SELECT count FROM daily WHERE user_id=? AND day=?", (uid, today))
        row = cur.fetchone()
        return row[0] if row else 0


def inc_today_count(uid):
    today = datetime.now().strftime("%Y-%m-%d")
    with lock:
        cur.execute("SELECT count FROM daily WHERE user_id=? AND day=?", (uid, today))
        if cur.fetchone():
            cur.execute("UPDATE daily SET count=count+1 WHERE user_id=?", (uid,))
        else:
            cur.execute("INSERT INTO daily VALUES (?, ?, ?)", (uid, 1, today))
        conn.commit()


def daily_reset_loop():
    while True:
        today = datetime.now().strftime("%Y-%m-%d")
        with lock:
            cur.execute("DELETE FROM daily WHERE day!=?", (today,))
            conn.commit()
        time.sleep(3600)
