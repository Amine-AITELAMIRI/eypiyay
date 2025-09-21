import os
import psycopg
import psycopg.errors
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any, Dict, Generator, Optional

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")


@dataclass
class RequestRecord:
    id: int
    prompt: str
    status: str
    response: Optional[str]
    error: Optional[str]
    worker_id: Optional[str]
    webhook_url: Optional[str]
    webhook_delivered: bool
    prompt_mode: Optional[str]
    created_at: str
    updated_at: str


def _row_to_record(row: tuple) -> RequestRecord:
    # Convert datetime objects to ISO format strings
    created_at = row[6].isoformat() if hasattr(row[6], 'isoformat') else str(row[6])
    updated_at = row[7].isoformat() if hasattr(row[7], 'isoformat') else str(row[7])
    
    return RequestRecord(
        id=row[0],
        prompt=row[1],
        status=row[2],
        response=row[3],
        error=row[4],
        worker_id=row[5],
        webhook_url=row[8],  # Added by migration at position 8
        webhook_delivered=row[9],  # Added by migration at position 9
        prompt_mode=row[10],  # Added by migration at position 10
        created_at=created_at,
        updated_at=updated_at,
    )


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create table if it doesn't exist
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
            
            # Add webhook_url column if it doesn't exist (migration)
            try:
                cur.execute("ALTER TABLE requests ADD COLUMN webhook_url TEXT")
                conn.commit()
            except psycopg.errors.DuplicateColumn:
                conn.rollback()  # Rollback the failed transaction
                pass  # Column already exists
            
            # Add webhook_delivered column if it doesn't exist (migration)
            try:
                cur.execute("ALTER TABLE requests ADD COLUMN webhook_delivered BOOLEAN NOT NULL DEFAULT FALSE")
                conn.commit()
            except psycopg.errors.DuplicateColumn:
                conn.rollback()  # Rollback the failed transaction
                pass  # Column already exists
            
            # Add prompt_mode column if it doesn't exist (migration)
            try:
                cur.execute("ALTER TABLE requests ADD COLUMN prompt_mode TEXT")
                conn.commit()
            except psycopg.errors.DuplicateColumn:
                conn.rollback()  # Rollback the failed transaction
                pass  # Column already exists


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def create_request(prompt: str, webhook_url: Optional[str] = None, prompt_mode: Optional[str] = None) -> RequestRecord:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO requests (prompt, status, webhook_url, prompt_mode) VALUES (%s, 'pending', %s, %s) RETURNING id",
                (prompt, webhook_url, prompt_mode),
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


def mark_webhook_delivered(request_id: int) -> None:
    """Mark webhook as delivered for a request"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET webhook_delivered = TRUE, updated_at = NOW() WHERE id = %s",
                (request_id,),
            )
            conn.commit()


def delete_request(request_id: int) -> bool:
    """
    Delete a request record from the database
    
    Args:
        request_id: The ID of the request to delete
        
    Returns:
        bool: True if the request was deleted, False if it wasn't found
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM requests WHERE id = %s",
                (request_id,),
            )
            deleted_count = cur.rowcount
            conn.commit()
            return deleted_count > 0


def cleanup_old_requests(retention_hours: int = 24) -> int:
    """
    Clean up completed requests older than the specified retention period.
    This is useful for automatic maintenance to prevent database bloat.
    
    Args:
        retention_hours: Number of hours to retain completed requests (default: 24)
        
    Returns:
        int: Number of requests deleted
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM requests 
                WHERE status IN ('completed', 'failed') 
                AND updated_at < NOW() - INTERVAL '%s hours'
                """,
                (retention_hours,),
            )
            deleted_count = cur.rowcount
            conn.commit()
            return deleted_count


def serialize(record: RequestRecord) -> Dict[str, Any]:
    return asdict(record)
