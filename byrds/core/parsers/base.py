"""Common types for proxy URI parsers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

Protocol = Literal["vless", "vmess", "trojan"]
Network = Literal["tcp", "kcp", "ws", "http", "h2", "grpc", "quic"]
Security = Literal["none", "tls", "reality", "xtls"]


class ParseError(ValueError):
    """Raised when a proxy URI cannot be parsed."""


@dataclass(slots=True)
class StreamSettings:
    """Transport-layer settings for a single outbound."""

    network: Network = "tcp"
    security: Security = "none"
    # TLS
    sni: str = ""
    alpn: list[str] = field(default_factory=list)
    fingerprint: str = ""  # fp=chrome/firefox/...
    allow_insecure: bool = False
    # REALITY
    public_key: str = ""       # pbk
    short_id: str = ""         # sid
    spider_x: str = ""         # spx
    # Transport specifics
    header_type: str = "none"  # tcp header type (for obfuscation)
    host: str = ""             # Host header (ws/h2) or obfs host
    path: str = ""             # ws/h2 path
    service_name: str = ""     # grpc
    grpc_mode: str = ""        # "multi" / "gun"


@dataclass(slots=True)
class Profile:
    """A single server profile parsed from a proxy URI."""

    # Core
    protocol: Protocol
    address: str
    port: int
    uuid_or_password: str  # uuid for vless/vmess, password for trojan
    remark: str = ""

    # VLESS-specific
    encryption: str = "none"
    flow: str = ""

    # VMess-specific
    alter_id: int = 0
    security_cipher: str = "auto"  # scy / aes-128-gcm / chacha20-poly1305 / auto / none

    # Transport / TLS
    stream: StreamSettings = field(default_factory=StreamSettings)

    # Bookkeeping
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source_uri: str = ""
    group: str = ""           # country / subscription name
    favorite: bool = False
    last_ping_ms: int | None = None
    last_speed_mbps: float | None = None

    @property
    def endpoint(self) -> str:
        return f"{self.address}:{self.port}"

    def short_label(self) -> str:
        return self.remark or f"{self.protocol}://{self.endpoint}"
