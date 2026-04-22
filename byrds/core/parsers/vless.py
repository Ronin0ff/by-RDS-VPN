"""Parser for ``vless://`` URIs (VLESS + REALITY / XTLS / TLS / WS / gRPC / TCP)."""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlsplit

from byrds.core.parsers.base import ParseError, Profile, StreamSettings


def _first(qs: dict[str, list[str]], key: str, default: str = "") -> str:
    values = qs.get(key)
    if not values:
        return default
    return values[0]


def parse_vless(uri: str) -> Profile:
    """Parse a standard VLESS URI (see `v2rayN`/`Nekoray` conventions).

    Example::

        vless://<uuid>@<host>:<port>?encryption=none&flow=xtls-rprx-vision
            &security=reality&sni=sosok.vk.com&fp=chrome
            &pbk=<pbk>&sid=<sid>&spx=%2F&type=tcp#<remark>
    """
    if not uri.startswith("vless://"):
        raise ParseError("not a vless:// URI")

    parts = urlsplit(uri)
    if not parts.username:
        raise ParseError("vless URI missing UUID (user-info)")
    if not parts.hostname:
        raise ParseError("vless URI missing host")
    if parts.port is None:
        raise ParseError("vless URI missing port")

    qs = parse_qs(parts.query, keep_blank_values=True)
    network = _first(qs, "type", "tcp").lower() or "tcp"
    if network == "h2":
        network = "http"

    security = _first(qs, "security", "none").lower() or "none"
    if security not in {"none", "tls", "reality", "xtls"}:
        security = "none"

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
        protocol="vless",
        address=parts.hostname,
        port=parts.port,
        uuid_or_password=parts.username,
        remark=remark,
        encryption=_first(qs, "encryption", "none") or "none",
        flow=_first(qs, "flow"),
        stream=stream,
        source_uri=uri,
    )
