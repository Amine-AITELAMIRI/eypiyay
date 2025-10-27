#!/usr/bin/env python3
"""Background worker that polls the relay server and forwards prompts to ChatGPT."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import websocket

import cdp_send_prompt as bookmarklet

logger = logging.getLogger(__name__)

# Import VPN rotation module (optional dependency)
try:
    # Try relative import first (when run as module: python -m worker.cdp_worker)
    from . import vpn_rotate_min
    VPN_AVAILABLE = True
except ImportError:
    try:
        # Try direct import (when run as script: python cdp_worker.py)
        import vpn_rotate_min
        VPN_AVAILABLE = True
    except ImportError:
        VPN_AVAILABLE = False
        logger.warning("vpn_rotate_min module not available, VPN rotation will be disabled")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ChatGPT relay worker")
    parser.add_argument("server", help="Base URL of the relay server, e.g. http://localhost:8000")
    parser.add_argument("worker_id", help="Identifier for this worker instance")
    parser.add_argument("api_key", help="API key for authentication")
    parser.add_argument("filter", nargs="?", help="Substring to match in the target tab URL/title")
    parser.add_argument("--script", default="bookmarklet.js", help="Path to the bookmarklet script")
    parser.add_argument("--host", default="localhost", help="Chrome remote debugging host")
    parser.add_argument("--port", type=int, default=9222, help="Chrome remote debugging port")
    parser.add_argument("--timeout", type=float, default=5.0, help="CDP network timeout")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Seconds to wait before re-polling when idle")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("--pick-first", action="store_true", help="Automatically use the first matching tab")
    parser.add_argument("--index", type=int, help="Force a specific tab index")
    parser.add_argument("--exact-url", help="Select tab whose URL matches exactly")
    parser.add_argument("--chatgpt-url", default="https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project", help="ChatGPT URL to navigate to for each request")
    parser.add_argument("--vpn-rotate", action="store_true", help="Enable VPN rotation for search mode requests (requires NordVPN)")
    parser.add_argument("--vpn-region", help="Optional VPN region to prefer (e.g., 'france', 'united_states')")
    parser.add_argument("--vpn-max-retries", type=int, default=2, help="Maximum retry attempts for VPN connection")
    return parser.parse_args()


def cdp_evaluate(send, expression: str, return_by_value: bool = True, await_promise: bool = False) -> Dict[str, Any]:
    params = {"expression": expression}
    if return_by_value:
        params["returnByValue"] = True
    if await_promise:
        params["awaitPromise"] = True
    result = send("Runtime.evaluate", params)
    return result.get("result", {})


def get_saved_files(send) -> List[str]:
    result = cdp_evaluate(
        send,
        """(() => {
        try {
            return JSON.parse(localStorage.getItem('chatgpt-files') || '[]');
        } catch (err) {
            return [];
        }
    })()""",
    )
    return result.get("value", []) if isinstance(result.get("value"), list) else []


def get_file_content(send, key: str) -> Optional[str]:
    result = cdp_evaluate(
        send,
        f"localStorage.getItem({json.dumps(key)})",
    )
    return result.get("value")


def wait_for_new_file(send, previous: List[str]) -> Optional[str]:
    previous_set = set(previous)
    while True:
        current = get_saved_files(send)
        if current:
            for name in current:
                if name not in previous_set:
                    return name
        time.sleep(1.0)


def normalize_url_for_comparison(url: str) -> str:
    """
    Normalize URL for comparison by removing trailing slashes and sorting query parameters.
    This helps determine if two URLs are effectively the same.
    """
    from urllib.parse import urlparse, parse_qs, urlencode
    
    parsed = urlparse(url.rstrip('/'))
    
    # Sort query parameters for consistent comparison
    query_params = parse_qs(parsed.query)
    sorted_query = urlencode(sorted(query_params.items()), doseq=True)
    
    # Reconstruct normalized URL
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if sorted_query:
        normalized += f"?{sorted_query}"
    
    return normalized


def get_current_page_url(send) -> str:
    """Get the current page URL via CDP"""
    try:
        result = cdp_evaluate(send, "window.location.href")
        return result.get("value", "")
    except Exception as e:
        logger.warning(f"Failed to get current page URL: {e}")
        return ""


def modify_chatgpt_url(send, model_mode: str, chatgpt_url: str, follow_up_chat_url: Optional[str] = None) -> None:
    """
    Navigate to ChatGPT URL - either follow-up chat or default URL with model parameter.
    Optimized to skip navigation if already on the target page (only for follow-ups).
    When follow_up_chat_url is null, always navigates to ensure a NEW chat is created.
    
    Args:
        send: CDP send function
        model_mode: Model mode (auto, thinking, instant)
        chatgpt_url: Default configured ChatGPT URL
        follow_up_chat_url: Optional URL of existing chat to continue (None means new chat)
    """
    # Determine target URL
    if follow_up_chat_url:
        base_url = follow_up_chat_url.rstrip('/')
        
        # Add model parameter to follow-up URL if model_mode is specified
        if model_mode:
            # Check if URL already has query parameters
            separator = '&' if '?' in base_url else '?'
            target_url = f"{base_url}{separator}model=gpt-5-{model_mode}"
        else:
            target_url = base_url
        
        url_type = "follow-up chat"
        is_follow_up = True
    else:
        # Use the configured ChatGPT URL for new conversations
        base_url = chatgpt_url.rstrip('/')
        
        # Add model parameter if model_mode is specified
        if model_mode:
            target_url = f"{base_url}?model=gpt-5-{model_mode}"
        else:
            target_url = base_url
        
        url_type = "new chat"
        is_follow_up = False
    
    # Only optimize navigation for follow-ups
    # For new chats (follow_up_chat_url is None), always navigate to ensure fresh conversation
    if is_follow_up:
        # Get current page URL and check if navigation is needed
        current_url = get_current_page_url(send)
        
        # Normalize URLs for comparison
        normalized_current = normalize_url_for_comparison(current_url) if current_url else ""
        normalized_target = normalize_url_for_comparison(target_url)
        
        # Skip navigation if already on the target page (only for follow-ups)
        if normalized_current == normalized_target:
            logger.info(f"Already on target page ({url_type}), skipping navigation: {target_url}")
            return
    
    # Navigate to the URL
    logger.info(f"Navigating to {url_type}: {target_url}")
    send("Page.navigate", {"url": target_url})
    
    # Wait for page to load
    time.sleep(3)


def fetch_and_encode_image(image_url: str) -> Optional[str]:
    """Fetch an image URL and convert it to base64 data URI"""
    try:
        # If already a data URI, return as-is
        if image_url.startswith('data:'):
            logger.info("Image is already a data URI, using as-is")
            return image_url
        
        # Fetch the image
        logger.info(f"Fetching image from {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Get content type
        content_type = response.headers.get('Content-Type', 'image/png')
        
        # Encode to base64
        encoded = base64.b64encode(response.content).decode('utf-8')
        data_uri = f"data:{content_type};base64,{encoded}"
        
        logger.info(f"Successfully converted image to base64 ({len(encoded)} bytes)")
        return data_uri
        
    except Exception as e:
        logger.error(f"Failed to fetch and encode image: {e}")
        return None


def rotate_vpn_if_needed(prompt_mode: Optional[str], vpn_enabled: bool, vpn_region: Optional[str] = None, vpn_max_retries: int = 2) -> None:
    """
    Rotate VPN connection if prompt_mode is 'search' and VPN rotation is enabled.
    
    Args:
        prompt_mode: The prompt mode (e.g., 'search', 'study')
        vpn_enabled: Whether VPN rotation is enabled via command-line flag
        vpn_region: Optional region to prefer for VPN connection
        vpn_max_retries: Maximum retry attempts for VPN connection
    """
    # Skip if VPN rotation is not enabled
    if not vpn_enabled:
        return
    
    # Skip if not in search mode
    if prompt_mode != "search":
        logger.debug(f"Skipping VPN rotation for prompt_mode={prompt_mode}")
        return
    
    # Check if VPN module is available
    if not VPN_AVAILABLE:
        logger.warning("VPN rotation requested but vpn_rotate_min module is not available")
        return
    
    logger.info("Search mode detected, rotating VPN to get fresh IP address...")
    
    try:
        result = vpn_rotate_min.rotate(
            region=vpn_region,
            require_new=True,
            max_retries=vpn_max_retries,
            connect_timeout_s=20,
        )
        
        if result["ok"]:
            logger.info(
                f"VPN rotation successful! Connected to: {result.get('server')} "
                f"({result.get('country')}, {result.get('city')}) "
                f"[{result.get('protocol')}] (retries: {result.get('retries', 0)})"
            )
        else:
            logger.warning(
                f"VPN rotation failed: {result.get('error', 'Unknown error')}. "
                f"Continuing with current connection (retries: {result.get('retries', 0)})"
            )
    except Exception as e:
        logger.error(f"Unexpected error during VPN rotation: {e}. Continuing with current connection")
        # Don't raise - continue with the request even if VPN rotation fails


def run_prompt(
    ws_url: str, 
    script: str, 
    job: Dict[str, Any], 
    timeout: float, 
    chatgpt_url: str,
    vpn_enabled: bool = False,
    vpn_region: Optional[str] = None,
    vpn_max_retries: int = 2,
) -> Dict[str, Any]:
    # Rotate VPN before running the prompt if needed (for search mode)
    prompt_mode = job.get("prompt_mode")
    rotate_vpn_if_needed(prompt_mode, vpn_enabled, vpn_region, vpn_max_retries)
    
    ws = websocket.create_connection(ws_url, timeout=timeout)
    message_id = 0

    def send(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        nonlocal message_id
        message_id += 1
        return bookmarklet.call_cdp(ws, method, params, message_id)

    try:
        send("Runtime.enable")
        saved_before = get_saved_files(send)

        # Handle navigation - either to follow-up chat or new chat
        model_mode = job.get("model_mode")
        follow_up_chat_url = job.get("follow_up_chat_url")
        
        # Always navigate to ensure we're on the correct page
        # - If follow_up_chat_url is provided: navigate to that specific chat
        # - If follow_up_chat_url is null: navigate to chatgpt_url to start a new chat
        modify_chatgpt_url(send, model_mode, chatgpt_url, follow_up_chat_url)
        # Wait a bit longer for page to fully stabilize after navigation
        time.sleep(2)

        # Convert image URL to base64 BEFORE setting window variables
        # This ensures the page is fully loaded when we set the image
        converted_image = None
        image_url = job.get("image_url")
        if image_url:
            # Convert external URLs to base64 to avoid CSP violations in ChatGPT
            converted_image = fetch_and_encode_image(image_url)
            if not converted_image:
                logger.warning(f"Failed to convert image, skipping image upload")

        # Now set all window variables after page is stable
        prompt = job["prompt"]
        send("Runtime.evaluate", {"expression": f"window.__chatgptBookmarkletPrompt = {json.dumps(prompt)};"})
        
        # Set prompt mode if available in the job
        prompt_mode = job.get("prompt_mode")
        if prompt_mode:
            send("Runtime.evaluate", {"expression": f"window.__chatgptBookmarkletPromptMode = {json.dumps(prompt_mode)};"})
        
        # Set image URL if we successfully converted it
        if converted_image:
            send("Runtime.evaluate", {"expression": f"window.__chatgptBookmarkletImageUrl = {json.dumps(converted_image)};"})
            logger.info("Image URL set in window, bookmarklet will upload it")

        send(
            "Runtime.evaluate",
            {
                "expression": script,
                "awaitPromise": True,
            },
        )

        new_file = wait_for_new_file(send, saved_before)
        if not new_file:
            raise RuntimeError("Timed out waiting for bookmarklet to persist response")

        content = get_file_content(send, new_file)
        if not content:
            raise RuntimeError(f"LocalStorage entry {new_file} not found")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to parse JSON in {new_file}: {exc}") from exc

        return payload
    finally:
        ws.close()


def resolve_target(args: argparse.Namespace) -> Dict[str, Any]:
    targets = bookmarklet.fetch_targets(args.host, args.port, args.timeout)
    if args.index is not None:
        args_for_selection = argparse.Namespace(index=args.index, filter=None, exact_url=None, pick_first=True)
    else:
        args_for_selection = argparse.Namespace(
            index=None,
            filter=args.filter,
            exact_url=args.exact_url,
            pick_first=True,
        )
    target = bookmarklet.choose_target(targets, args_for_selection)
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        raise RuntimeError("Selected tab does not expose webSocketDebuggerUrl")
    return {"target": target, "ws_url": ws_url}


def claim_request(server: str, worker_id: str, api_key: str) -> Optional[Dict[str, Any]]:
    headers = {"X-API-Key": api_key}
    response = requests.post(f"{server.rstrip('/')}/worker/claim", json={"worker_id": worker_id}, headers=headers)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def post_completion(server: str, request_id: int, result: Dict[str, Any], api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    
    # Extract chat_url from result if available
    chat_url = result.get("url")
    
    payload = {
        "response": json.dumps(result)
    }
    
    # Include chat_url if present
    if chat_url:
        payload["chat_url"] = chat_url
    
    response = requests.post(
        f"{server.rstrip('/')}/worker/{request_id}/complete",
        json=payload,
        headers=headers,
    )
    response.raise_for_status()


def post_failure(server: str, request_id: int, message: str, api_key: str) -> None:
    headers = {"X-API-Key": api_key}
    response = requests.post(
        f"{server.rstrip('/')}/worker/{request_id}/fail",
        json={"error": message},
        headers=headers,
    )
    response.raise_for_status()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s [%(levelname)s] %(message)s")

    script_path = Path(args.script)
    if not script_path.exists():
        logger.error("Bookmarklet script not found at %s", script_path)
        return 1
    script = bookmarklet.load_bookmarklet(script_path)

    try:
        target_info = resolve_target(args)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to resolve target tab: %s", exc)
        return 1

    ws_url = target_info["ws_url"]
    logger.info("Worker %s targeting %s", args.worker_id, target_info["target"].get("url"))

    while True:
        try:
            job = claim_request(args.server, args.worker_id, args.api_key)
        except requests.RequestException as exc:
            logger.error("Server communication error: %s", exc)
            time.sleep(args.poll_interval)
            continue

        if job is None:
            logger.debug("No work available. Sleeping for %.1fs", args.poll_interval)
            time.sleep(args.poll_interval)
            continue

        request_id = job["id"]
        prompt = job["prompt"]
        logger.info("Processing request %s", request_id)

        try:
            result = run_prompt(
                ws_url, 
                script, 
                job, 
                args.timeout, 
                args.chatgpt_url,
                vpn_enabled=args.vpn_rotate,
                vpn_region=args.vpn_region,
                vpn_max_retries=args.vpn_max_retries,
            )
        except Exception as exc:
            logger.error("Prompt %s failed: %s", request_id, exc)
            try:
                post_failure(args.server, request_id, str(exc), args.api_key)
            except requests.RequestException as post_exc:
                logger.error("Failed to report failure for %s: %s", request_id, post_exc)
            continue

        try:
            post_completion(args.server, request_id, result, args.api_key)
            logger.info("Request %s completed", request_id)
        except requests.RequestException as exc:
            logger.error("Failed to report completion for %s: %s", request_id, exc)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


