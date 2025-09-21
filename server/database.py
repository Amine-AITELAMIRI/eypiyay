import os
import psycopg2
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Dict, Generator, Optional

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")


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


def _row_to_record(row: tuple) -> RequestRecord:
    return RequestRecord(
        id=row[0],
        prompt=row[1],
        status=row[2],
        response=row[3],
        error=row[4],
        worker_id=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id SERIAL PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    response TEXT,
                    error TEXT,
                    worker_id TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.commit()


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def create_request(prompt: str) -> RequestRecord:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO requests (prompt, status) VALUES (%s, 'pending') RETURNING id",
                (prompt,),
            )
            request_id = cur.fetchone()[0]
            conn.commit()
            return get_request(request_id)


def get_request(request_id: int) -> RequestRecord:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM requests WHERE id = %s",
                (request_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError(f"Request {request_id} not found")
            return _row_to_record(row)


def claim_next_request(worker_id: str) -> Optional[RequestRecord]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute(
                "SELECT * FROM requests WHERE status = 'pending' ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED"
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("COMMIT")
                return None
            request_id = row[0]
            cur.execute(
                "UPDATE requests SET status = %s, worker_id = %s, updated_at = NOW() WHERE id = %s",
                ("processing", worker_id, request_id),
            )
            conn.commit()
            return get_request(request_id)



def complete_request(request_id: int, response: str) -> RequestRecord:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET status = %s, response = %s, error = NULL, updated_at = NOW() WHERE id = %s",
                ("completed", response, request_id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Request {request_id} not found")
            conn.commit()
    return get_request(request_id)


def fail_request(request_id: int, error: str) -> RequestRecord:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET status = %s, error = %s, updated_at = NOW() WHERE id = %s",
                ("failed", error, request_id),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Request {request_id} not found")
            conn.commit()
    return get_request(request_id)


def serialize(record: RequestRecord) -> Dict[str, Any]:
    return asdict(record)
