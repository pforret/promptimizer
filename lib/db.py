import sqlite3
from pathlib import Path

DB_PATH = Path("database/db.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS invocations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_topic    TEXT NOT NULL,
    prompt_name     TEXT NOT NULL,
    prompt_version  TEXT NOT NULL DEFAULT '1',
    full_prompt     TEXT NOT NULL,
    system_prompt   TEXT,
    system_version  TEXT,
    model_id        TEXT NOT NULL,
    model_name      TEXT,
    temperature     REAL DEFAULT 1.0,
    max_tokens      INTEGER,
    response_format TEXT,
    response_schema TEXT,
    full_response   TEXT,
    prompt_tokens   INTEGER,
    completion_tokens INTEGER,
    total_tokens    INTEGER,
    cost_usd        REAL,
    latency_ms      INTEGER,
    generation_id   TEXT,
    media_files     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT NOT NULL DEFAULT 'success',
    error_message   TEXT
);
CREATE INDEX IF NOT EXISTS idx_invocations_prompt ON invocations(prompt_topic, prompt_name);
CREATE INDEX IF NOT EXISTS idx_invocations_model ON invocations(model_id);
CREATE INDEX IF NOT EXISTS idx_invocations_created ON invocations(created_at);
"""


def get_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    # Migrate: add columns if missing (for existing DBs)
    existing = {row[1] for row in conn.execute("PRAGMA table_info(invocations)").fetchall()}
    if "system_prompt" not in existing:
        conn.execute("ALTER TABLE invocations ADD COLUMN system_prompt TEXT")
    if "system_version" not in existing:
        conn.execute("ALTER TABLE invocations ADD COLUMN system_version TEXT")
    return conn


def recreate_db(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS invocations")
    conn.executescript(_SCHEMA)


def insert_invocation(conn: sqlite3.Connection, **kwargs) -> int:
    cols = [
        "prompt_topic", "prompt_name", "prompt_version", "full_prompt",
        "system_prompt", "system_version",
        "model_id", "model_name", "temperature", "max_tokens",
        "response_format", "response_schema", "full_response",
        "prompt_tokens", "completion_tokens", "total_tokens",
        "cost_usd", "latency_ms", "generation_id", "media_files",
        "status", "error_message",
    ]
    present = {k: v for k, v in kwargs.items() if k in cols}
    keys = list(present.keys())
    placeholders = ", ".join("?" for _ in keys)
    sql = f"INSERT INTO invocations ({', '.join(keys)}) VALUES ({placeholders})"
    cur = conn.execute(sql, list(present.values()))
    conn.commit()
    return cur.lastrowid


def get_invocation(conn: sqlite3.Connection, inv_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM invocations WHERE id = ?", (inv_id,)).fetchone()
    return dict(row) if row else None


def list_invocations(
    conn: sqlite3.Connection,
    prompt_topic: str | None = None,
    prompt_name: str | None = None,
    model_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    sql = "SELECT * FROM invocations WHERE 1=1"
    params: list = []
    if prompt_topic:
        sql += " AND prompt_topic = ?"
        params.append(prompt_topic)
    if prompt_name:
        sql += " AND prompt_name LIKE ?"
        params.append(f"%{prompt_name}%")
    if model_id:
        sql += " AND model_id = ?"
        params.append(model_id)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def update_cost(conn: sqlite3.Connection, inv_id: int, cost_usd: float) -> None:
    conn.execute("UPDATE invocations SET cost_usd = ? WHERE id = ?", (cost_usd, inv_id))
    conn.commit()


def delete_invocation(conn: sqlite3.Connection, inv_id: int) -> bool:
    cur = conn.execute("DELETE FROM invocations WHERE id = ?", (inv_id,))
    conn.commit()
    return cur.rowcount > 0


def get_stats(conn: sqlite3.Connection) -> dict:
    row = conn.execute("""
        SELECT
            COUNT(*) as total_runs,
            SUM(cost_usd) as total_cost,
            SUM(total_tokens) as total_tokens,
            COUNT(DISTINCT model_id) as unique_models,
            COUNT(DISTINCT prompt_topic || '/' || prompt_name) as unique_prompts
        FROM invocations WHERE status = 'success'
    """).fetchone()
    return dict(row)
