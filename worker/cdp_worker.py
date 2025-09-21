#!/usr/bin/env python3
"""Background worker that polls the relay server and forwards prompts to ChatGPT."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import websocket

import cdp_send_prompt as bookmarklet

logger = logging.getLogger(__name__)


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
    parser.add_argument("--response-timeout", type=float, default=120.0, help="Seconds to wait for ChatGPT response")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Seconds to wait before re-polling when idle")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("--pick-first", action="store_true", help="Automatically use the first matching tab")
    parser.add_argument("--index", type=int, help="Force a specific tab index")
    parser.add_argument("--exact-url", help="Select tab whose URL matches exactly")
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


def wait_for_new_file(send, previous: List[str], timeout: float) -> Optional[str]:
    deadline = time.time() + timeout
    previous_set = set(previous)
    while time.time() < deadline:
        current = get_saved_files(send)
        if current:
            for name in current:
                if name not in previous_set:
                    return name
        time.sleep(1.0)
    return None


def modify_chatgpt_url(send, model_mode: str) -> None:
    """Modify the ChatGPT URL to use the project URL with model parameter"""
    # The project URL template
    project_url = "https://chatgpt.com/g/g-p-68d04e772ef881918e915068fbe126e4-api-auto/project"
    
    # Add model parameter
    target_url = f"{project_url}?model=gpt-5-{model_mode}"
    
    logger.info(f"Navigating to project URL with model: {target_url}")
    
    # Navigate to the new URL
    send("Page.navigate", {"url": target_url})
    
    # Wait for page to load
    time.sleep(3)


def run_prompt(ws_url: str, script: str, job: Dict[str, Any], timeout: float, response_timeout: float) -> Dict[str, Any]:
    ws = websocket.create_connection(ws_url, timeout=timeout)
    message_id = 0

    def send(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        nonlocal message_id
        message_id += 1
        return bookmarklet.call_cdp(ws, method, params, message_id)

    try:
        send("Runtime.enable")
        saved_before = get_saved_files(send)

        # Handle model mode by modifying URL if specified
        model_mode = job.get("model_mode")
        if model_mode:
            modify_chatgpt_url(send, model_mode)

        prompt = job["prompt"]
        send("Runtime.evaluate", {"expression": f"window.__chatgptBookmarkletPrompt = {json.dumps(prompt)};"})
        
        # Set prompt mode if available in the job
        prompt_mode = job.get("prompt_mode")
        if prompt_mode:
            send("Runtime.evaluate", {"expression": f"window.__chatgptBookmarkletPromptMode = {json.dumps(prompt_mode)};"})

        send(
            "Runtime.evaluate",
            {
                "expression": script,
                "awaitPromise": True,
            },
        )

        new_file = wait_for_new_file(send, saved_before, response_timeout)
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
    response = requests.post(
        f"{server.rstrip('/')}/worker/{request_id}/complete",
        json={"response": json.dumps(result)},
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
            result = run_prompt(ws_url, script, job, args.timeout, args.response_timeout)
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


