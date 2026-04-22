"""Build Xray-core JSON config from a :class:`Profile` + :class:`Settings`.

Only the subset of Xray features we actually expose in the UI is modelled here —
it is intentionally conservative, because Xray rejects unknown keys in strict mode.
"""

from __future__ import annotations

import logging
from typing import Any

from byrds.core.parsers.base import Profile, StreamSettings
from byrds.core.storage import Settings

log = logging.getLogger(__name__)


DNS_PROFILES: dict[str, list[str]] = {
    "cloudflare": ["https://1.1.1.1/dns-query", "https://1.0.0.1/dns-query"],
    "adguard": ["https://dns.adguard-dns.com/dns-query"],
    "google": ["https://dns.google/dns-query"],
}


def build_stream_settings(stream: StreamSettings) -> dict[str, Any]:
    """Convert internal StreamSettings into Xray ``streamSettings`` block."""
    net = stream.network

    result: dict[str, Any] = {
        "network": "http" if net == "h2" else net,
        "security": stream.security if stream.security != "none" else "none",
    }

    if stream.security == "tls":
        tls: dict[str, Any] = {}
        if stream.sni:
            tls["serverName"] = stream.sni
        if stream.alpn:
            tls["alpn"] = stream.alpn
        if stream.allow_insecure:
            tls["allowInsecure"] = True
        if stream.fingerprint:
            tls["fingerprint"] = stream.fingerprint
        result["tlsSettings"] = tls
    elif stream.security == "reality":
        reality: dict[str, Any] = {
            "fingerprint": stream.fingerprint or "chrome",
            "serverName": stream.sni,
            "publicKey": stream.public_key,
            "shortId": stream.short_id,
            "spiderX": stream.spider_x,
        }
        result["realitySettings"] = {k: v for k, v in reality.items() if v}

    if net == "tcp":
        header = {"type": stream.header_type or "none"}
        if stream.host and stream.header_type == "http":
            header["request"] = {"headers": {"Host": [stream.host]}}
        result["tcpSettings"] = {"header": header}
    elif net == "ws":
        ws: dict[str, Any] = {"path": stream.path or "/"}
        if stream.host:
            ws["headers"] = {"Host": stream.host}
        result["wsSettings"] = ws
    elif net == "http":
        h2: dict[str, Any] = {}
        if stream.path:
            h2["path"] = stream.path
        if stream.host:
            h2["host"] = [stream.host]
        result["httpSettings"] = h2
    elif net == "grpc":
        grpc: dict[str, Any] = {"serviceName": stream.service_name or stream.path or ""}
        if stream.grpc_mode == "multi":
            grpc["multiMode"] = True
        result["grpcSettings"] = grpc

    return result


def _vless_outbound(profile: Profile) -> dict[str, Any]:
    user: dict[str, Any] = {
        "id": profile.uuid_or_password,
        "encryption": profile.encryption or "none",
    }
    if profile.flow:
        user["flow"] = profile.flow
    return {
        "protocol": "vless",
        "settings": {
            "vnext": [
                {
                    "address": profile.address,
                    "port": profile.port,
                    "users": [user],
                }
            ]
        },
        "streamSettings": build_stream_settings(profile.stream),
        "tag": "proxy",
    }


def _vmess_outbound(profile: Profile) -> dict[str, Any]:
    return {
        "protocol": "vmess",
        "settings": {
            "vnext": [
                {
                    "address": profile.address,
                    "port": profile.port,
                    "users": [
                        {
                            "id": profile.uuid_or_password,
                            "alterId": profile.alter_id,
                            "security": profile.security_cipher or "auto",
                        }
                    ],
                }
            ]
        },
        "streamSettings": build_stream_settings(profile.stream),
        "tag": "proxy",
    }


def _trojan_outbound(profile: Profile) -> dict[str, Any]:
    return {
        "protocol": "trojan",
        "settings": {
            "servers": [
                {
                    "address": profile.address,
                    "port": profile.port,
                    "password": profile.uuid_or_password,
                }
            ]
        },
        "streamSettings": build_stream_settings(profile.stream),
        "tag": "proxy",
    }


OUTBOUND_BUILDERS = {
    "vless": _vless_outbound,
    "vmess": _vmess_outbound,
    "trojan": _trojan_outbound,
}


def _mux(settings: Settings) -> dict[str, Any]:
    return {"enabled": settings.enable_mux, "concurrency": settings.mux_concurrency}


def _inbounds(settings: Settings) -> list[dict[str, Any]]:
    listen = "0.0.0.0" if settings.allow_lan else "127.0.0.1"
    return [
        {
            "tag": "socks",
            "listen": listen,
            "port": settings.socks_port,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
        },
        {
            "tag": "http",
            "listen": listen,
            "port": settings.http_port,
            "protocol": "http",
            "settings": {"allowTransparent": False},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
    ]


def _dns(settings: Settings) -> dict[str, Any]:
    if settings.dns_mode == "system":
        return {"servers": ["localhost"]}
    if settings.dns_mode == "custom":
        return {"servers": list(settings.custom_dns)}
    servers = DNS_PROFILES.get(settings.dns_mode)
    if not servers:
        log.warning("unknown DNS mode %r, falling back to system", settings.dns_mode)
        return {"servers": ["localhost"]}
    return {"servers": list(servers)}


def _routing(settings: Settings) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []

    if settings.block_domains:
        rules.append(
            {
                "type": "field",
                "outboundTag": "block",
                "domain": list(settings.block_domains),
            }
        )

    direct_domains = list(settings.direct_domains) + [
        f"geosite:{s}" for s in settings.geosite_direct
    ]
    if direct_domains:
        rules.append({"type": "field", "outboundTag": "direct", "domain": direct_domains})

    if settings.direct_ips:
        rules.append({"type": "field", "outboundTag": "direct", "ip": list(settings.direct_ips)})

    proxy_domains = list(settings.proxy_domains) + [
        f"geosite:{s}" for s in settings.geosite_proxy
    ]
    if proxy_domains:
        rules.append({"type": "field", "outboundTag": "proxy", "domain": proxy_domains})

    # Default: everything else through proxy (matches a typical VPN client's expectation).
    rules.append({"type": "field", "outboundTag": "proxy", "port": "0-65535"})

    return {"domainStrategy": "IPIfNonMatch", "rules": rules}


def build_xray_config(profile: Profile, settings: Settings) -> dict[str, Any]:
    """Create a complete Xray JSON configuration."""
    builder = OUTBOUND_BUILDERS.get(profile.protocol)
    if builder is None:
        raise ValueError(f"unsupported protocol: {profile.protocol}")

    outbound = builder(profile)
    xtls_flow = profile.protocol == "vless" and profile.flow
    if settings.enable_mux and profile.protocol in {"vless", "vmess", "trojan"} and not xtls_flow:
        outbound["mux"] = _mux(settings)

    config: dict[str, Any] = {
        "log": {"loglevel": "info"},
        "dns": _dns(settings),
        "inbounds": _inbounds(settings),
        "outbounds": [
            outbound,
            {"protocol": "freedom", "tag": "direct"},
            {"protocol": "blackhole", "tag": "block"},
        ],
        "routing": _routing(settings),
        "policy": {
            "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
            "system": {
                "statsInboundUplink": True,
                "statsInboundDownlink": True,
                "statsOutboundUplink": True,
                "statsOutboundDownlink": True,
            },
        },
        "stats": {},
        "api": {"tag": "api", "services": ["StatsService"]},
    }

    # Expose stats API on a local-only inbound so the GUI can query uplink/downlink.
    config["inbounds"].append(
        {
            "tag": "api",
            "listen": "127.0.0.1",
            "port": settings.api_port,
            "protocol": "dokodemo-door",
            "settings": {"address": "127.0.0.1"},
        }
    )
    # Ensure the `api` inbound is only routed to the `api` outbound.
    config["routing"]["rules"].insert(
        0, {"type": "field", "inboundTag": ["api"], "outboundTag": "api"}
    )

    return config
