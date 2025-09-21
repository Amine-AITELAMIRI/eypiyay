import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Generator, Optional

DB_PATH = Path(__file__).resolve().parent / "server.db"


@dataclass
class RequestRecord:
    id: int
    prompt: str
    status: str
    response: Optional[str]
    error: Optional[str]
    worker_id: Optional[str]
    created_at: str
    updated_at: str


def _row_to_record(row: sqlite3.Row) -> RequestRecord:
    return RequestRecord(
        id=row["id"],
        prompt=row["prompt"],
        status=row["status"],
        response=row["response"],
        error=row["error"],
        worker_id=row["worker_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                response TEXT,
                error TEXT,
                worker_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_request(prompt: str) -> RequestRecord:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO requests (prompt, status) VALUES (?, 'pending')",
            (prompt,),
        )
        request_id = cur.lastrowid
        conn.commit()
        return get_request(request_id)


def get_request(request_id: int) -> RequestRecord:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM requests WHERE id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Request {request_id} not found")
        return _row_to_record(row)


def claim_next_request(worker_id: str) -> Optional[RequestRecord]:
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM requests WHERE status = 'pending' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return None
        request_id = row["id"]
        conn.execute(
            "UPDATE requests SET status = ?, worker_id = ?, updated_at = datetime('now') WHERE id = ?",
            ("processing", worker_id, request_id),
        )
        conn.commit()
        return get_request(request_id)



def complete_request(request_id: int, response: str) -> RequestRecord:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE requests SET status = ?, response = ?, error = NULL, updated_at = datetime('now') WHERE id = ?",
            ("completed", response, request_id),
        )
        if cur.rowcount == 0:
            raise KeyError(f"Request {request_id} not found")
        conn.commit()
    return get_request(request_id)


def fail_request(request_id: int, error: str) -> RequestRecord:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE requests SET status = ?, error = ?, updated_at = datetime('now') WHERE id = ?",
            ("failed", error, request_id),
        )
        if cur.rowcount == 0:
            raise KeyError(f"Request {request_id} not found")
        conn.commit()
    return get_request(request_id)


def serialize(record: RequestRecord) -> Dict[str, Any]:
    return asdict(record)
