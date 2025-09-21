#!/usr/bin/env python3
"""
Utility to connect to a running Chromium instance via the Chrome DevTools Protocol
and dump the active page's localStorage. Run Chrome with
"chrome --remote-debugging-port=9222 --user-data-dir=YOUR_PROFILE_DIR" first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import requests
except ImportError as exc:  # pragma: no cover
    print("Missing dependency 'requests'. Install it with 'pip install requests'.", file=sys.stderr)
    sys.exit(1)

try:
    import websocket
except ImportError as exc:  # pragma: no cover
    print(
        "Missing dependency 'websocket-client'. Install it with 'pip install websocket-client'.",
        file=sys.stderr,
    )
    sys.exit(1)

Target = Dict[str, Any]
LOCAL_STORAGE_SCRIPT = """(() => {
    const output = {};
    for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        try {
            output[key] = localStorage.getItem(key);
        } catch (err) {
            output[key] = null;
        }
    }
    return output;
})()"""


def fetch_targets(host: str, port: int, timeout: float) -> List[Target]:
    """Fetch the list of targets exposed by the remote debugging endpoint."""
    url = f"http://{host}:{port}/json"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError(f"Unexpected response when listing targets: {data!r}")
    return data


def print_targets(targets: List[Target]) -> None:
    """Pretty-print available targets for manual inspection."""
    for index, target in enumerate(targets):
        title = target.get("title", "<no title>")
        url = target.get("url", "<no url>")
        target_type = target.get("type", "page")
        print(f"[{index}] {target_type:>5} | {title} | {url}")


def choose_target(targets: List[Target], args: argparse.Namespace) -> Target:
    """Select a target based on CLI arguments, prompting if needed."""
    if args.index is not None:
        if args.index < 0 or args.index >= len(targets):
            raise ValueError(f"Index {args.index} out of range (0-{len(targets) - 1}).")
        return targets[args.index]

    matches = targets
    if args.filter:
        needle = args.filter.lower()
        matches = [
            target
            for target in matches
            if needle in target.get("url", "").lower() or needle in target.get("title", "").lower()
        ]
    if args.exact_url:
        matches = [target for target in matches if target.get("url") == args.exact_url]

    if not matches:
        raise ValueError("No targets matched the provided filters.")

    if len(matches) == 1 or args.pick_first or not sys.stdin.isatty():
        return matches[0]

    print("Multiple matching targets found:")
    for idx, target in enumerate(matches):
        title = target.get("title", "<no title>")
        url = target.get("url", "<no url>")
        print(f"  ({idx}) {title} | {url}")

    while True:
        selection = input("Select target index: ").strip()
        if not selection:
            continue
        try:
            chosen_index = int(selection)
        except ValueError:
            print("Please enter a numeric index.")
            continue
        if 0 <= chosen_index < len(matches):
            return matches[chosen_index]
        print(f"Index must be between 0 and {len(matches) - 1}.")


def call_cdp(ws: websocket.WebSocket, method: str, params: Dict[str, Any] | None, message_id: int) -> Dict[str, Any]:
    """Send a CDP command and wait for the matching response."""
    payload: Dict[str, Any] = {"id": message_id, "method": method}
    if params:
        payload["params"] = params
    ws.send(json.dumps(payload))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") != message_id:
            continue
        if "error" in data:
            error = data["error"]
            raise RuntimeError(f"CDP call {method} failed: {error}")
        return data.get("result", {})


def dump_local_storage(ws_url: str, timeout: float) -> Dict[str, Any]:
    """Connect to the target websocket and return the localStorage contents."""
    ws = websocket.create_connection(ws_url, timeout=timeout)
    message_id = 0
    try:
        message_id += 1
        call_cdp(ws, "Runtime.enable", None, message_id)
        message_id += 1
        result = call_cdp(
            ws,
            "Runtime.evaluate",
            {
                "expression": LOCAL_STORAGE_SCRIPT,
                "returnByValue": True,
                "awaitPromise": True,
            },
            message_id,
        )
        remote_obj = result.get("result", {})
        if "value" not in remote_obj:
            raise RuntimeError("CDP did not return a value for localStorage.")
        value = remote_obj["value"]
        if not isinstance(value, dict):
            raise RuntimeError(f"Unexpected value type returned: {type(value).__name__}")
        return value
    finally:
        ws.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dump localStorage from a Chromium tab using the Chrome DevTools Protocol.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "filter",
        nargs="?",
        help="Substring to match in the target tab URL or title (case-insensitive).",
    )
    parser.add_argument("--host", default="localhost", help="Remote debugging host.")
    parser.add_argument("--port", type=int, default=9222, help="Remote debugging port.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Network timeout in seconds.")
    parser.add_argument(
        "--exact-url",
        help="Match a tab whose URL exactly equals the provided string.",
    )
    parser.add_argument(
        "--index",
        type=int,
        help="Use the tab at this index from the full target list (overrides filters).",
    )
    parser.add_argument(
        "--pick-first",
        action="store_true",
        help="If multiple tabs match the filter, automatically choose the first.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available targets and exit without dumping localStorage.",
    )
    parser.add_argument(
        "--output",
        help="Write the JSON dump to this file instead of stdout.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON with indentation (only used when writing to stdout).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        targets = fetch_targets(args.host, args.port, args.timeout)
    except requests.exceptions.RequestException as exc:
        print(f"Failed to reach Chrome debugging endpoint: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.list:
        print_targets(targets)
        return 0

    try:
        target = choose_target(targets, args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        print("Selected target does not expose a webSocketDebuggerUrl.", file=sys.stderr)
        return 1

    try:
        storage = dump_local_storage(ws_url, args.timeout)
    except (websocket.WebSocketException, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Failed to dump localStorage: {exc}", file=sys.stderr)
        return 3

    serialized = json.dumps(storage, indent=2 if args.pretty and not args.output else None, sort_keys=True)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(serialized, encoding="utf-8")
        print(f"Wrote localStorage contents to {output_path}", file=sys.stderr)
    else:
        print(serialized)

    return 0


if __name__ == "__main__":
    sys.exit(main())
