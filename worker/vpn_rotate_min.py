#!/usr/bin/env python3
"""
Minimal VPN rotation utility for NordVPN.
Handles disconnecting and reconnecting to ensure a fresh IP address.
"""

from __future__ import annotations

import subprocess
import time
import json
from typing import Optional, Dict, Any, List


def _run(cmd: List[str], timeout: int = 20) -> subprocess.CompletedProcess:
    """Run a command with timeout and capture output."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _parse_status(text: str) -> Dict[str, Any]:
    """Parse nordvpn status output into a dictionary."""
    info = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = [s.strip() for s in line.split(":", 1)]
            info[k.lower().replace(" ", "_")] = v
    return info


def _status() -> Dict[str, Any]:
    """Get current NordVPN status."""
    try:
        cp = _run(["nordvpn", "status"], timeout=5)
        return _parse_status(cp.stdout)
    except Exception:
        return {}


def _wait_connected(max_wait_s: float = 20.0) -> Dict[str, Any]:
    """Wait for VPN to reach connected state."""
    deadline = time.time() + max_wait_s
    last = {}
    while time.time() < deadline:
        last = _status()
        if "connected" in last.get("status", "").lower():
            return last
        time.sleep(0.5)
    return last


def rotate(
    region: Optional[str] = None,
    require_new: bool = True,
    max_retries: int = 2,
    connect_timeout_s: int = 20,
) -> Dict[str, Any]:
    """
    Disconnects and connects to the fastest server (or fastest in `region`).
    No IP checks; uses NordVPN status only.
    If `require_new` is True, it tries to avoid reconnecting to the same hostname
    (up to `max_retries` extra attempts).

    Args:
        region: Optional region to connect to (e.g., "france", "united_states")
        require_new: If True, ensure we connect to a different server than before
        max_retries: Maximum retry attempts if connection fails or same server
        connect_timeout_s: Seconds to wait for connection to establish

    Returns:
        dict with ok, status, server, country, city, technology, protocol, retries
    """
    result: Dict[str, Any] = {"ok": False, "retries": 0}

    # Snapshot current server (if any) to avoid reconnecting to the same one
    before = _status()
    before_server = (
        before.get("hostname")
        or before.get("current_server")
        or before.get("server")
        or ""
    )

    # Quick disconnect (ignore errors)
    try:
        _run(["nordvpn", "d"], timeout=5)
    except Exception:
        pass

    attempts = 0
    new_status: Dict[str, Any] = {}

    while True:
        # Connect fastest (optionally within region)
        cmd = ["nordvpn", "c"]
        if region:
            cmd.append(region)
        _run(cmd, timeout=15)

        # Wait until connected (fast polling)
        new_status = _wait_connected(max_wait_s=connect_timeout_s)

        # Check if we're connected
        if "connected" not in (new_status.get("status", "").lower()):
            attempts += 1
            if attempts > max_retries:
                break
            # try again
            try:
                _run(["nordvpn", "d"], timeout=5)
            except Exception:
                pass
            continue

        # If we must ensure a different server, compare hostnames
        if require_new:
            new_server = (
                new_status.get("hostname")
                or new_status.get("current_server")
                or new_status.get("server")
                or ""
            )
            if before_server and new_server and new_server == before_server:
                attempts += 1
                if attempts > max_retries:
                    break
                # Try another server
                try:
                    _run(["nordvpn", "d"], timeout=5)
                except Exception:
                    pass
                time.sleep(0.5)
                continue

        # Success
        break

    result.update({
        "ok": "connected" in new_status.get("status", "").lower(),
        "status": new_status.get("status"),
        "server": new_status.get("hostname")
                  or new_status.get("current_server")
                  or new_status.get("server"),
        "country": new_status.get("country"),
        "city": new_status.get("city"),
        "technology": new_status.get("technology"),
        "protocol": new_status.get("protocol"),
        "retries": attempts,
    })

    if not result["ok"]:
        result["error"] = "Failed to confirm connected status quickly."

    return result


if __name__ == "__main__":
    import sys
    # Usage:
    #   python3 vpn_rotate_min.py
    #   python3 vpn_rotate_min.py france
    region = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(rotate(region=region), ensure_ascii=False))

