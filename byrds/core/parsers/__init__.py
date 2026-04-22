"""Profile URI parsers (VLESS / VMess / Trojan)."""

from __future__ import annotations

from byrds.core.parsers.base import ParseError, Profile
from byrds.core.parsers.trojan import parse_trojan
from byrds.core.parsers.vless import parse_vless
from byrds.core.parsers.vmess import parse_vmess


def parse_uri(uri: str) -> Profile:
    """Parse any supported proxy URI into a :class:`Profile`.

    Raises :class:`ParseError` if the scheme is not supported or the URI is malformed.
    """
    uri = uri.strip()
    if not uri:
        raise ParseError("empty URI")
    scheme = uri.split("://", 1)[0].lower()
    if scheme == "vless":
        return parse_vless(uri)
    if scheme == "vmess":
        return parse_vmess(uri)
    if scheme == "trojan":
        return parse_trojan(uri)
    raise ParseError(f"unsupported scheme: {scheme}")


def parse_many(text: str) -> tuple[list[Profile], list[tuple[str, str]]]:
    """Parse a multi-line blob of proxy URIs.

    Returns a tuple ``(profiles, errors)`` where ``errors`` is a list of ``(line, reason)``.
    """
    profiles: list[Profile] = []
    errors: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            profiles.append(parse_uri(line))
        except ParseError as exc:
            errors.append((line, str(exc)))
    return profiles, errors


__all__ = [
    "ParseError",
    "Profile",
    "parse_many",
    "parse_trojan",
    "parse_uri",
    "parse_vless",
    "parse_vmess",
]
