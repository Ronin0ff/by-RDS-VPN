"""Import proxy profiles from raw text, files, or HTTP(S) subscription URLs."""

from __future__ import annotations

import base64
import binascii
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx

from byrds.core.parsers import ParseError, Profile, parse_many, parse_uri

log = logging.getLogger(__name__)


def _decode_subscription(raw: str) -> str:
    """Subscription endpoints typically return a base64-encoded list of URIs."""
    candidate = raw.strip()
    if candidate.startswith(("vless://", "vmess://", "trojan://")):
        return candidate
    cleaned = "".join(candidate.split())
    cleaned += "=" * (-len(cleaned) % 4)
    try:
        decoded = base64.b64decode(cleaned).decode("utf-8", errors="strict")
        if any(scheme in decoded for scheme in ("vless://", "vmess://", "trojan://")):
            return decoded
    except (binascii.Error, UnicodeDecodeError):
        pass
    return candidate


def import_text(text: str) -> tuple[list[Profile], list[tuple[str, str]]]:
    """Parse all URIs from a multi-line blob (supports base64 subscription payloads)."""
    text = _decode_subscription(text)
    return parse_many(text)


def import_file(path: str | Path) -> tuple[list[Profile], list[tuple[str, str]]]:
    data = Path(path).read_text(encoding="utf-8")
    return import_text(data)


def import_single(uri: str) -> Profile:
    return parse_uri(uri)


def fetch_subscription(
    url: str, timeout: float = 15.0
) -> tuple[list[Profile], list[tuple[str, str]]]:
    """Download a subscription endpoint and parse its contents."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ParseError(f"invalid subscription URL scheme: {parsed.scheme!r}")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            res = client.get(url)
            res.raise_for_status()
            body = res.text
    except httpx.HTTPError as exc:
        raise ParseError(f"failed to fetch subscription: {exc}") from exc
    return import_text(body)
