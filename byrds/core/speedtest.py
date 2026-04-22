"""HTTP download speed test through the local SOCKS5 proxy."""

from __future__ import annotations

import logging
import time

import httpx

log = logging.getLogger(__name__)

# Cloudflare’s built-in endpoint for speed testing. Returns a stream of zeros.
DEFAULT_URL = "https://speed.cloudflare.com/__down?bytes=25000000"  # 25 MB


def measure_download_mbps(
    proxy_url: str,
    url: str = DEFAULT_URL,
    budget_seconds: float = 8.0,
) -> float:
    """Download ``url`` through ``proxy_url`` and return observed speed in Mbps.

    ``proxy_url`` is an httpx proxy string, e.g. ``socks5://127.0.0.1:10808`` or
    ``http://127.0.0.1:10809``. Aborts after ``budget_seconds``.
    """
    transport_kwargs: dict = {"proxy": proxy_url} if proxy_url else {}
    total_bytes = 0
    start = time.perf_counter()
    try:
        with httpx.Client(timeout=budget_seconds + 2, verify=True, **transport_kwargs) as client:
            with client.stream("GET", url) as r:
                r.raise_for_status()
                for chunk in r.iter_bytes(chunk_size=64 * 1024):
                    total_bytes += len(chunk)
                    if time.perf_counter() - start >= budget_seconds:
                        break
    except httpx.HTTPError as exc:
        log.debug("speedtest via %s failed: %s", proxy_url, exc)
        return 0.0

    elapsed = max(time.perf_counter() - start, 1e-6)
    mbps = (total_bytes * 8) / (elapsed * 1_000_000)
    return round(mbps, 2)
