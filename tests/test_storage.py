"""Tests for the JSON-backed storage layer."""

from __future__ import annotations

from pathlib import Path

from byrds.core.parsers import parse_uri
from byrds.core.storage import Settings, Storage


def test_settings_roundtrip(tmp_path: Path) -> None:
    store = Storage(root=tmp_path)
    s = Settings(socks_port=20000, dns_mode="cloudflare", direct_domains=["example.com"])
    store.save_settings(s)
    loaded = store.load_settings()
    assert loaded.socks_port == 20000
    assert loaded.dns_mode == "cloudflare"
    assert loaded.direct_domains == ["example.com"]


def test_settings_ignores_unknown_keys(tmp_path: Path) -> None:
    store = Storage(root=tmp_path)
    (tmp_path / "settings.json").write_text(
        '{"socks_port": 30000, "unknown_future_field": true}', encoding="utf-8"
    )
    loaded = store.load_settings()
    assert loaded.socks_port == 30000
    # Defaults survive gracefully:
    assert loaded.http_port == Settings().http_port


def test_profiles_roundtrip(tmp_path: Path) -> None:
    store = Storage(root=tmp_path)
    profiles = [
        parse_uri(
            "vless://abc-1234@1.2.3.4:443?encryption=none&flow=xtls-rprx-vision"
            "&security=reality&sni=a.com&pbk=p&sid=1&type=tcp#node1"
        ),
        parse_uri("trojan://pwd@5.6.7.8:443?security=tls&sni=b.com&type=tcp#node2"),
    ]
    profiles[0].favorite = True
    profiles[0].last_ping_ms = 42
    store.save_profiles(profiles)

    loaded = store.load_profiles()
    assert len(loaded) == 2
    assert loaded[0].remark == "node1"
    assert loaded[0].favorite is True
    assert loaded[0].last_ping_ms == 42
    assert loaded[0].stream.security == "reality"
    assert loaded[1].protocol == "trojan"
