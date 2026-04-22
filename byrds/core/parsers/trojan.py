"""Parser for ``trojan://`` URIs (TLS / REALITY)."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from byrds.core.parsers.base import ParseError, Profile, StreamSettings


def _first(qs: dict[str, list[str]], key: str, default: str = "") -> str:
    values = qs.get(key)
    if not values:
        return default
    return values[0]


def parse_trojan(uri: str) -> Profile:
    """Parse a Trojan URI::

        trojan://<password>@<host>:<port>?security=tls&sni=<sni>&type=tcp#<remark>
    """
    if not uri.startswith("trojan://"):
        raise ParseError("not a trojan:// URI")

    parts = urlsplit(uri)
    password = unquote(parts.username or "")
    if not password:
        raise ParseError("trojan URI missing password")
    if not parts.hostname:
        raise ParseError("trojan URI missing host")
    if parts.port is None:
        raise ParseError("trojan URI missing port")

    qs = parse_qs(parts.query, keep_blank_values=True)
    network = _first(qs, "type", "tcp").lower() or "tcp"
    if network == "h2":
        network = "http"

    # Trojan historically implies TLS; accept explicit overrides.
    security = _first(qs, "security", "tls").lower() or "tls"
    if security not in {"tls", "reality", "xtls", "none"}:
        security = "tls"

    alpn_raw = _first(qs, "alpn")
    alpn = [a for a in alpn_raw.split(",") if a] if alpn_raw else []

    stream = StreamSettings(
        network=network,  # type: ignore[arg-type]
        security=security,  # type: ignore[arg-type]
        sni=_first(qs, "sni") or _first(qs, "peer"),
        alpn=alpn,
        fingerprint=_first(qs, "fp"),
        allow_insecure=_first(qs, "allowInsecure", "0") in {"1", "true", "True"},
        public_key=_first(qs, "pbk"),
        short_id=_first(qs, "sid"),
        spider_x=unquote(_first(qs, "spx")),
        header_type=_first(qs, "headerType", "none"),
        host=_first(qs, "host"),
        path=unquote(_first(qs, "path")),
        service_name=unquote(_first(qs, "serviceName")),
        grpc_mode=_first(qs, "mode"),
    )

    remark = unquote(parts.fragment) if parts.fragment else ""

    return Profile(
        protocol="trojan",
        address=parts.hostname,
        port=parts.port,
        uuid_or_password=password,
        remark=remark,
        stream=stream,
        source_uri=uri,
    )
