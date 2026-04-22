"""Tests for the Xray config builder — validates the JSON structure we feed Xray."""

from __future__ import annotations

import pytest

from byrds.core.config_builder import build_xray_config
from byrds.core.parsers import parse_uri
from byrds.core.storage import Settings


@pytest.fixture
def default_settings() -> Settings:
    return Settings()


def test_build_vless_reality_config(default_settings: Settings) -> None:
    uri = (
        "vless://5458507c-40e7-4883-baa2-3c33e31fb790@45.38.143.119:443"
        "?encryption=none&flow=xtls-rprx-vision&security=reality"
        "&sni=sosok.vk.com&fp=chrome&pbk=HkLK62c3sz"
        "&sid=1a&spx=%2F&type=tcp&headerType=none#node"
    )
    profile = parse_uri(uri)
    cfg = build_xray_config(profile, default_settings)

    # Inbounds: socks + http + api (api injected automatically)
    inbound_tags = {ib["tag"] for ib in cfg["inbounds"]}
    assert "socks" in inbound_tags
    assert "http" in inbound_tags
    assert "api" in inbound_tags

    # Outbound protocol
    proxy = next(ob for ob in cfg["outbounds"] if ob["tag"] == "proxy")
    assert proxy["protocol"] == "vless"
    assert proxy["settings"]["vnext"][0]["address"] == "45.38.143.119"
    assert proxy["settings"]["vnext"][0]["users"][0]["flow"] == "xtls-rprx-vision"
    assert proxy["streamSettings"]["security"] == "reality"
    assert proxy["streamSettings"]["realitySettings"]["publicKey"] == "HkLK62c3sz"


def test_build_vmess_tls(default_settings: Settings) -> None:
    uri = (
        "vmess://eyJ2IjoiMiIsInBzIjoiVGVzdE5vZGUiLCJhZGQiOiIxLjIuMy40IiwicG9ydCI6IjQ0MyIs"
        "ImlkIjoiZDY5NTEwMjYtN2QwMy00ZWQ4LWEzMzEtZDRlNTI1YzA2ZGY0IiwiYWlkIjoiMCIsInNjeSI6"
        "ImF1dG8iLCJuZXQiOiJ0Y3AiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoi"
        "dGxzIiwic25pIjoiZXhhbXBsZS5jb20iLCJhbHBuIjoiaDIsaHR0cC8xLjEiLCJmcCI6ImNocm9tZSJ9"
    )
    cfg = build_xray_config(parse_uri(uri), default_settings)
    proxy = next(ob for ob in cfg["outbounds"] if ob["tag"] == "proxy")
    assert proxy["protocol"] == "vmess"
    tls = proxy["streamSettings"]["tlsSettings"]
    assert tls["serverName"] == "example.com"
    assert tls["alpn"] == ["h2", "http/1.1"]


def test_routing_direct_and_block_rules() -> None:
    uri = (
        "trojan://password@example.com:443?security=tls&sni=example.com"
        "&type=tcp#t"
    )
    settings = Settings(
        direct_domains=["bank.example", "localhost"],
        block_domains=["ads.example"],
        proxy_domains=["geosite:netflix"],
    )
    cfg = build_xray_config(parse_uri(uri), settings)

    outbound_tags = {ob["tag"] for ob in cfg["outbounds"]}
    assert outbound_tags == {"proxy", "direct", "block"}

    rules = cfg["routing"]["rules"]
    block_rule = next(r for r in rules if r.get("outboundTag") == "block")
    assert "ads.example" in block_rule["domain"]

    direct_rules = [r for r in rules if r.get("outboundTag") == "direct"]
    domain_rule = next(r for r in direct_rules if "domain" in r)
    assert "bank.example" in domain_rule["domain"]

    # Default catch-all through proxy must be the last rule.
    assert rules[-1]["outboundTag"] == "proxy"


def test_mux_disabled_with_xtls_flow() -> None:
    uri = (
        "vless://abc@example.com:443?encryption=none&flow=xtls-rprx-vision"
        "&security=reality&sni=a.com&pbk=p&sid=1&type=tcp#t"
    )
    settings = Settings(enable_mux=True)
    cfg = build_xray_config(parse_uri(uri), settings)
    proxy = next(ob for ob in cfg["outbounds"] if ob["tag"] == "proxy")
    assert "mux" not in proxy, "MUX must not be applied with XTLS flow"


def test_dns_modes() -> None:
    uri = "trojan://pwd@example.com:443?security=tls&sni=example.com&type=tcp#t"
    prof = parse_uri(uri)

    assert build_xray_config(prof, Settings(dns_mode="system"))["dns"] == {
        "servers": ["localhost"]
    }
    cfg_cf = build_xray_config(prof, Settings(dns_mode="cloudflare"))
    assert any("1.1.1.1" in s or "1.0.0.1" in s for s in cfg_cf["dns"]["servers"])

    cfg_custom = build_xray_config(
        prof, Settings(dns_mode="custom", custom_dns=["9.9.9.9"])
    )
    assert cfg_custom["dns"]["servers"] == ["9.9.9.9"]
