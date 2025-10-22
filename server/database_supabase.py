"""
Supabase-based database implementation using REST API
This is a modern alternative to direct PostgreSQL connections
"""
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
from supabase import create_client, Client
from datetime import datetime

# Get Supabase credentials from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hizcmicfsbirljnfaogr.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Can be anon or service_role key

# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY environment variable is required")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


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
    model_mode: Optional[str]
    image_url: Optional[str]
    created_at: str
    updated_at: str


def _row_to_record(row: Dict[str, Any]) -> RequestRecord:
    """Convert Supabase row to RequestRecord"""
    return RequestRecord(
        id=row['id'],
        prompt=row['prompt'],
        status=row['status'],
        response=row.get('response'),
        error=row.get('error'),
        worker_id=row.get('worker_id'),
        webhook_url=row.get('webhook_url'),
        webhook_delivered=row.get('webhook_delivered', False),
        prompt_mode=row.get('prompt_mode'),
        model_mode=row.get('model_mode'),
        image_url=row.get('image_url'),
        created_at=row['created_at'],
        updated_at=row['updated_at'],
    )


def init_db() -> None:
    """
    Initialize database schema
    Note: With Supabase, you typically create tables via the dashboard or SQL editor
    This function checks if the table exists
    """
    try:
        supabase = get_supabase()
        # Try to fetch one record to check if table exists
        supabase.table('requests').select('id').limit(1).execute()
        print("✅ Connected to Supabase - 'requests' table exists")
    except Exception as e:
        print(f"⚠️ Supabase connection issue: {e}")
        print("📝 Please create the 'requests' table in Supabase dashboard")
        print("   See SUPABASE_MIGRATION_GUIDE.md for SQL schema")
        raise


def create_request(
    prompt: str, 
    webhook_url: Optional[str] = None, 
    prompt_mode: Optional[str] = None, 
    model_mode: Optional[str] = None,
    image_url: Optional[str] = None
) -> RequestRecord:
    """Create a new request"""
    supabase = get_supabase()
    
    data = {
        'prompt': prompt,
        'status': 'pending',
        'webhook_url': webhook_url,
        'prompt_mode': prompt_mode,
        'model_mode': model_mode,
        'image_url': image_url,
        'webhook_delivered': False
    }
    
    result = supabase.table('requests').insert(data).execute()
    return _row_to_record(result.data[0])


def get_request(request_id: int) -> RequestRecord:
    """Get a request by ID"""
    supabase = get_supabase()
    
    result = supabase.table('requests').select('*').eq('id', request_id).execute()
    
    if not result.data:
        raise KeyError(f"Request {request_id} not found")
    
    return _row_to_record(result.data[0])


def claim_next_request(worker_id: str) -> Optional[RequestRecord]:
    """Claim the next pending request"""
    supabase = get_supabase()
    
    # Get oldest pending request
    result = supabase.table('requests')\
        .select('*')\
        .eq('status', 'pending')\
        .order('created_at')\
        .limit(1)\
        .execute()
    
    if not result.data:
        return None
    
    request = result.data[0]
    request_id = request['id']
    
    # Update to processing
    update_result = supabase.table('requests')\
        .update({
            'status': 'processing',
            'worker_id': worker_id,
            'updated_at': datetime.utcnow().isoformat()
        })\
        .eq('id', request_id)\
        .execute()
    
    return _row_to_record(update_result.data[0])


def complete_request(request_id: int, response: str) -> RequestRecord:
    """Mark a request as completed"""
    supabase = get_supabase()
    
    result = supabase.table('requests')\
        .update({
            'status': 'completed',
            'response': response,
            'error': None,
            'updated_at': datetime.utcnow().isoformat()
        })\
        .eq('id', request_id)\
        .execute()
    
    if not result.data:
        raise KeyError(f"Request {request_id} not found")
    
    return _row_to_record(result.data[0])


def fail_request(request_id: int, error: str) -> RequestRecord:
    """Mark a request as failed"""
    supabase = get_supabase()
    
    result = supabase.table('requests')\
        .update({
            'status': 'failed',
            'error': error,
            'updated_at': datetime.utcnow().isoformat()
        })\
        .eq('id', request_id)\
        .execute()
    
    if not result.data:
        raise KeyError(f"Request {request_id} not found")
    
    return _row_to_record(result.data[0])


def mark_webhook_delivered(request_id: int) -> None:
    """Mark webhook as delivered"""
    supabase = get_supabase()
    
    supabase.table('requests')\
        .update({
            'webhook_delivered': True,
            'updated_at': datetime.utcnow().isoformat()
        })\
        .eq('id', request_id)\
        .execute()


def delete_request(request_id: int) -> bool:
    """Delete a request"""
    supabase = get_supabase()
    
    result = supabase.table('requests')\
        .delete()\
        .eq('id', request_id)\
        .execute()
    
    return len(result.data) > 0


def cleanup_old_requests(retention_hours: int = 24) -> int:
    """Clean up old completed/failed requests"""
    supabase = get_supabase()
    
    # Calculate cutoff time
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(hours=retention_hours)).isoformat()
    
    # Delete old completed/failed requests
    result = supabase.table('requests')\
        .delete()\
        .in_('status', ['completed', 'failed'])\
        .lt('updated_at', cutoff)\
        .execute()
    
    return len(result.data) if result.data else 0


def get_all_requests(limit: int = 10, status: Optional[str] = None):
    """Get all requests with optional status filter"""
    supabase = get_supabase()
    
    query = supabase.table('requests').select('*').order('created_at', desc=True).limit(limit)
    
    if status:
        query = query.eq('status', status)
    
    result = query.execute()
    return result.data


def get_stats():
    """Get database statistics"""
    supabase = get_supabase()
    
    # Get all requests
    all_requests = supabase.table('requests').select('status,created_at').execute()
    
    if not all_requests.data:
        return {
            'total_requests': 0,
            'status_breakdown': {},
            'oldest_request': None,
            'newest_request': None
        }
    
    # Calculate stats
    status_breakdown = {}
    for req in all_requests.data:
        status = req['status']
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    created_times = [req['created_at'] for req in all_requests.data]
    
    return {
        'total_requests': len(all_requests.data),
        'status_breakdown': status_breakdown,
        'oldest_request': min(created_times) if created_times else None,
        'newest_request': max(created_times) if created_times else None
    }


def serialize(record: RequestRecord) -> Dict[str, Any]:
    """Serialize RequestRecord to dict"""
    return asdict(record)

