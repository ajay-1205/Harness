import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "state.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()


def create_session() -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO sessions (started_at) VALUES (?)",
        (datetime.now().isoformat(),),
    )
    conn.commit()
    session_id = cur.lastrowid
    conn.close()
    return session_id


def log_message(session_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_recent_history(session_id: int, limit: int = 10) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """SELECT role, content FROM messages
           WHERE session_id = ?
           ORDER BY id DESC LIMIT ?""",
        (session_id, limit),
    ).fetchall()
    conn.close()
    rows.reverse()  # DESC for the LIMIT, then flip back to chronological order
    return [{"role": r, "content": c} for r, c in rows]


if __name__ == "__main__":
    init_db()

    sid = create_session()
    print(f"[created session] {sid}")

    log_message(sid, "user", "What is 47 times 12, minus 6?")
    log_message(sid, "assistant", "That's 558.")
    log_message(sid, "user", "Now divide that by 4.")
    log_message(sid, "assistant", "558 divided by 4 is 139.5.")

    print("\n[recent history for this session]")
    for msg in get_recent_history(sid, limit=10):
        print(f"  {msg['role']:10s}: {msg['content']}")


    sid2 = create_session()
    log_message(sid2, "user", "Unrelated question from a different session.")
    print(f"\n[session {sid2} history -- should NOT contain the math messages]")
    for msg in get_recent_history(sid2, limit=10):
        print(f"  {msg['role']:10s}: {msg['content']}")
