"""
Webhook delivery functionality for ChatGPT relay API
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import httpx
from . import database

logger = logging.getLogger(__name__)


async def deliver_webhook(webhook_url: str, payload: Dict[str, Any], request_id: int) -> bool:
    """
    Deliver webhook payload to the specified URL with retry logic
    
    Args:
        webhook_url: The URL to deliver the webhook to
        payload: The data to send in the webhook
        request_id: The request ID for tracking
        
    Returns:
        bool: True if delivery was successful, False otherwise
    """
    max_retries = 3
    retry_delays = [1, 5, 15]  # seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "ChatGPT-Relay-API/1.0"
                    }
                )
                
                # Consider 2xx status codes as successful
                if 200 <= response.status_code < 300:
                    logger.info(f"Webhook delivered successfully to {webhook_url} for request {request_id}")
                    database.mark_webhook_delivered(request_id)
                    return True
                else:
                    logger.warning(
                        f"Webhook delivery failed with status {response.status_code} "
                        f"for request {request_id}, attempt {attempt + 1}"
                    )
                    
        except httpx.TimeoutException:
            logger.warning(f"Webhook delivery timeout for request {request_id}, attempt {attempt + 1}")
        except httpx.RequestError as e:
            logger.warning(f"Webhook delivery error for request {request_id}, attempt {attempt + 1}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during webhook delivery for request {request_id}: {e}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delays[attempt])
    
    logger.error(f"Webhook delivery failed after {max_retries} attempts for request {request_id}")
    return False


def create_webhook_payload(request_record: database.RequestRecord) -> Dict[str, Any]:
    """
    Create webhook payload from request record
    
    Args:
        request_record: The request record to create payload from
        
    Returns:
        Dict containing webhook payload
    """
    payload = {
        "request_id": request_record.id,
        "status": request_record.status,
        "prompt": request_record.prompt,
        "timestamp": request_record.updated_at,
        "worker_id": request_record.worker_id,
    }
    
    if request_record.status == "completed":
        payload["response"] = request_record.response
    elif request_record.status == "failed":
        payload["error"] = request_record.error
    
    return payload


async def send_completion_webhook(request_id: int) -> None:
    """
    Send webhook notification for a completed request
    
    Args:
        request_id: The ID of the completed request
    """
    try:
        request_record = database.get_request(request_id)
        
        if not request_record.webhook_url:
            logger.debug(f"No webhook URL configured for request {request_id}")
            return
        
        if request_record.webhook_delivered:
            logger.debug(f"Webhook already delivered for request {request_id}")
            return
        
        payload = create_webhook_payload(request_record)
        
        # Deliver webhook asynchronously
        await deliver_webhook(request_record.webhook_url, payload, request_id)
        
    except Exception as e:
        logger.error(f"Error sending completion webhook for request {request_id}: {e}")


async def send_failure_webhook(request_id: int) -> None:
    """
    Send webhook notification for a failed request
    
    Args:
        request_id: The ID of the failed request
    """
    try:
        request_record = database.get_request(request_id)
        
        if not request_record.webhook_url:
            logger.debug(f"No webhook URL configured for request {request_id}")
            return
        
        if request_record.webhook_delivered:
            logger.debug(f"Webhook already delivered for request {request_id}")
            return
        
        payload = create_webhook_payload(request_record)
        
        # Deliver webhook asynchronously
        await deliver_webhook(request_record.webhook_url, payload, request_id)
        
    except Exception as e:
        logger.error(f"Error sending failure webhook for request {request_id}: {e}")
