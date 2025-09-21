import os
import asyncio
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl

from . import database
from . import webhook

app = FastAPI(title="ChatGPT Relay Server", version="0.1.0")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

# Get retention period from environment variable (default: 24 hours)
RETENTION_HOURS = int(os.getenv("RETENTION_HOURS", "24"))


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key from header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


class CreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to send to ChatGPT")
    webhook_url: Optional[HttpUrl] = Field(None, description="URL to receive webhook notifications when request completes")
    prompt_mode: Optional[str] = Field(None, description="Special prompt mode like 'search' or 'study' that types /sear or /stu before the prompt")


class RequestResponse(BaseModel):
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


class ClaimRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)


class CompletionPayload(BaseModel):
    response: str


class FailurePayload(BaseModel):
    error: str


async def periodic_cleanup():
    """Background task to periodically clean up old requests."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            deleted_count = database.cleanup_old_requests(RETENTION_HOURS)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old requests (retention: {RETENTION_HOURS}h)")
        except Exception as e:
            print(f"Error during periodic cleanup: {e}")


@app.on_event("startup")
async def startup() -> None:
    try:
        database.init_db()
        # Start background cleanup task
        asyncio.create_task(periodic_cleanup())
        print(f"Started periodic cleanup task (retention: {RETENTION_HOURS}h)")
    except ValueError as e:
        # Database not available yet, will retry on first request
        print(f"Database initialization deferred: {e}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin/database/requests")
def view_requests(
    limit: int = Query(10, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    api_key: str = Depends(verify_api_key)
) -> dict[str, list]:
    """
    View database requests (development/admin use only).
    Use with caution in production environments.
    """
    try:
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                # Build query with optional status filter
                query = "SELECT * FROM requests"
                params = []
                
                if status:
                    query += " WHERE status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                # Get column names
                columns = [desc[0] for desc in cur.description]
                
                # Convert to list of dictionaries
                records = []
                for row in rows:
                    record = dict(zip(columns, row))
                    # Convert datetime objects to strings
                    for key, value in record.items():
                        if hasattr(value, 'isoformat'):
                            record[key] = value.isoformat()
                    records.append(record)
                
                return {
                    "status": "success",
                    "count": len(records),
                    "records": records
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@app.get("/admin/database/stats")
def database_stats(api_key: str = Depends(verify_api_key)) -> dict[str, any]:
    """
    Get database statistics (development/admin use only).
    """
    try:
        with database.get_connection() as conn:
            with conn.cursor() as cur:
                # Get total counts by status
                cur.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM requests 
                    GROUP BY status
                """)
                status_counts = dict(cur.fetchall())
                
                # Get total records
                cur.execute("SELECT COUNT(*) FROM requests")
                total_count = cur.fetchone()[0]
                
                # Get oldest and newest records
                cur.execute("""
                    SELECT 
                        MIN(created_at) as oldest,
                        MAX(created_at) as newest
                    FROM requests
                """)
                oldest, newest = cur.fetchone()
                
                return {
                    "status": "success",
                    "total_requests": total_count,
                    "status_breakdown": status_counts,
                    "oldest_request": oldest.isoformat() if oldest else None,
                    "newest_request": newest.isoformat() if newest else None
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@app.post("/admin/cleanup")
def manual_cleanup(
    retention_hours: int = Query(RETENTION_HOURS, description="Hours to retain completed requests"),
    api_key: str = Depends(verify_api_key)
) -> dict[str, str]:
    """
    Manually trigger cleanup of old completed/failed requests.
    Useful for maintenance or testing purposes.
    """
    try:
        deleted_count = database.cleanup_old_requests(retention_hours)
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} requests older than {retention_hours} hours"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.post("/requests", response_model=RequestResponse, status_code=201)
def create_request(payload: CreateRequest, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    webhook_url = str(payload.webhook_url) if payload.webhook_url else None
    record = database.create_request(payload.prompt, webhook_url, payload.prompt_mode)
    return RequestResponse(**database.serialize(record))


@app.get("/requests/{request_id}", response_model=RequestResponse)
def read_request(
    request_id: int, 
    api_key: str = Depends(verify_api_key),
    delete_after_fetch: bool = Query(False, description="Delete the request from database after fetching")
) -> RequestResponse:
    try:
        record = database.get_request(request_id)
        response_data = RequestResponse(**database.serialize(record))
        
        # Delete the request if requested
        if delete_after_fetch:
            deleted = database.delete_request(request_id)
            if not deleted:
                # This shouldn't happen since we just fetched it, but handle gracefully
                print(f"Warning: Could not delete request {request_id} after fetch")
        
        return response_data
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/requests/{request_id}/fetch-and-delete", response_model=RequestResponse)
def fetch_and_delete_request(request_id: int, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    """
    Fetch the request response and immediately delete it from the database.
    This is a convenience endpoint that combines fetch and delete operations.
    """
    try:
        record = database.get_request(request_id)
        response_data = RequestResponse(**database.serialize(record))
        
        # Delete the request after fetching
        deleted = database.delete_request(request_id)
        if not deleted:
            # This shouldn't happen since we just fetched it, but handle gracefully
            raise HTTPException(status_code=500, detail=f"Could not delete request {request_id} after fetch")
        
        return response_data
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/worker/claim", response_model=RequestResponse, status_code=200)
def claim_request(payload: ClaimRequest, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    record = database.claim_next_request(payload.worker_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No pending requests")
    return RequestResponse(**database.serialize(record))


@app.post("/worker/{request_id}/complete", response_model=RequestResponse)
def complete_request(request_id: int, payload: CompletionPayload, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    try:
        record = database.complete_request(request_id, payload.response)
        # Schedule webhook delivery in background
        background_tasks.add_task(webhook.send_completion_webhook, request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RequestResponse(**database.serialize(record))


@app.post("/worker/{request_id}/fail", response_model=RequestResponse)
def fail_request(request_id: int, payload: FailurePayload, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    try:
        record = database.fail_request(request_id, payload.error)
        # Schedule webhook delivery in background
        background_tasks.add_task(webhook.send_failure_webhook, request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RequestResponse(**database.serialize(record))

