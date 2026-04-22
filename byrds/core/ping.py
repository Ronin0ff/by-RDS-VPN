"""TCP connect-time latency measurement for proxy endpoints."""

from __future__ import annotations

import logging
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from byrds.core.parsers.base import Profile

log = logging.getLogger(__name__)


def tcp_ping(host: str, port: int, timeout: float = 3.0) -> int:
    """Open a TCP connection and return handshake RTT in milliseconds.

    Raises ``OSError`` on failure.
    """
    start = time.perf_counter()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
    return int((time.perf_counter() - start) * 1000)


def ping_profile(profile: Profile, timeout: float = 3.0) -> int | None:
    """Return ping in ms, or ``None`` on failure."""
    try:
        return tcp_ping(profile.address, profile.port, timeout=timeout)
    except OSError as exc:
        log.debug("ping failed for %s:%s — %s", profile.address, profile.port, exc)
        return None


def ping_many(
    profiles: list[Profile],
    timeout: float = 3.0,
    workers: int = 50,
) -> dict[str, int | None]:
    """Ping many profiles in parallel. Returns mapping ``profile.id -> ms | None``."""
    if not profiles:
        return {}
    results: dict[str, int | None] = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_id = {ex.submit(ping_profile, p, timeout): p.id for p in profiles}
        for fut in as_completed(future_to_id):
            pid = future_to_id[fut]
            try:
                results[pid] = fut.result()
            except (OSError, RuntimeError) as exc:
                log.debug("ping worker error: %s", exc)
                results[pid] = None
    return results
