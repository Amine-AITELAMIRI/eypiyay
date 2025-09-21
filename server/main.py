import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from . import database

app = FastAPI(title="ChatGPT Relay Server", version="0.1.0")

# Get API key from environment variable
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key from header."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


class CreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to send to ChatGPT")


class RequestResponse(BaseModel):
    id: int
    prompt: str
    status: str
    response: Optional[str]
    error: Optional[str]
    worker_id: Optional[str]
    created_at: str
    updated_at: str


class ClaimRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)


class CompletionPayload(BaseModel):
    response: str


class FailurePayload(BaseModel):
    error: str


@app.on_event("startup")
def startup() -> None:
    try:
        database.init_db()
    except ValueError as e:
        # Database not available yet, will retry on first request
        print(f"Database initialization deferred: {e}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/requests", response_model=RequestResponse, status_code=201)
def create_request(payload: CreateRequest, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    record = database.create_request(payload.prompt)
    return RequestResponse(**database.serialize(record))


@app.get("/requests/{request_id}", response_model=RequestResponse)
def read_request(request_id: int, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    try:
        record = database.get_request(request_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RequestResponse(**database.serialize(record))


@app.post("/worker/claim", response_model=RequestResponse, status_code=200)
def claim_request(payload: ClaimRequest, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    record = database.claim_next_request(payload.worker_id)
    if record is None:
        raise HTTPException(status_code=404, detail="No pending requests")
    return RequestResponse(**database.serialize(record))


@app.post("/worker/{request_id}/complete", response_model=RequestResponse)
def complete_request(request_id: int, payload: CompletionPayload, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    try:
        record = database.complete_request(request_id, payload.response)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RequestResponse(**database.serialize(record))


@app.post("/worker/{request_id}/fail", response_model=RequestResponse)
def fail_request(request_id: int, payload: FailurePayload, api_key: str = Depends(verify_api_key)) -> RequestResponse:
    try:
        record = database.fail_request(request_id, payload.error)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RequestResponse(**database.serialize(record))

