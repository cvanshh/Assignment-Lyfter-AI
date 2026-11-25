import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import settings

def _path() -> str:
    u = settings.database_url
    return u.split("sqlite:///", 1)[1] if u.startswith("sqlite:///") else u

@contextmanager
def conn():
    c = sqlite3.connect(_path(), timeout=10)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init_db() -> None:
    d = os.path.dirname(_path())
    if d:
        os.makedirs(d, exist_ok=True)
    with conn() as c:
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT, created_at TEXT NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id)")
        c.execute("CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, system_prompt TEXT)")

def ping() -> bool:
    try:
        with conn() as c:
            c.execute("SELECT 1")
        return True
    except Exception:
        return False

def history(sid: str) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT role, content, metadata FROM messages WHERE session_id=? ORDER BY id", (sid,)).fetchall()
    out = []
    for r in rows:
        m = {"role": r["role"], "content": r["content"]}
        if r["metadata"]:
            m["metadata"] = json.loads(r["metadata"])
        out.append(m)
    return out

def get_system_prompt(sid: str) -> str | None:
    with conn() as c:
        r = c.execute("SELECT system_prompt FROM sessions WHERE session_id=?", (sid,)).fetchone()
    return r["system_prompt"] if r else None

def save_turn(sid: str, system_prompt: str | None, user: str, reply: str, meta: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with conn() as c:  # one transaction: a turn is stored fully or not at all
        if system_prompt:
            c.execute("INSERT INTO sessions(session_id, system_prompt) VALUES(?,?) "
                      "ON CONFLICT(session_id) DO UPDATE SET system_prompt=excluded.system_prompt", (sid, system_prompt))
        c.execute("INSERT INTO messages(session_id, role, content, metadata, created_at) VALUES(?,?,?,?,?)",
                  (sid, "user", user, None, now))
        c.execute("INSERT INTO messages(session_id, role, content, metadata, created_at) VALUES(?,?,?,?,?)",
                  (sid, "assistant", reply, json.dumps(meta), now))
