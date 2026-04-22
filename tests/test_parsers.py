"""Integration-style tests for URI parsers against the real ``vless.txt`` sample."""

from __future__ import annotations

from pathlib import Path

import pytest

from byrds.core.parsers import ParseError, parse_many, parse_uri

SAMPLE = Path(__file__).parent / "data" / "vless_sample.txt"


def test_sample_file_exists() -> None:
    assert SAMPLE.is_file(), "vless_sample.txt must be checked in"
    assert SAMPLE.stat().st_size > 1000


def test_parse_all_sample_links_successfully() -> None:
    text = SAMPLE.read_text(encoding="utf-8")
    profiles, errors = parse_many(text)

    if errors:
        formatted = "\n".join(f"- {reason!s}: {line[:120]}" for line, reason in errors[:5])
        pytest.fail(
            f"Expected all {len(profiles) + len(errors)} sample links to parse, "
            f"got {len(errors)} failure(s):\n{formatted}"
        )
    assert len(profiles) >= 30, f"sample should contain many profiles, got {len(profiles)}"


def test_parse_vless_reality() -> None:
    uri = (
        "vless://5458507c-40e7-4883-baa2-3c33e31fb790@45.38.143.119:443"
        "?encryption=none&flow=xtls-rprx-vision&security=reality"
        "&sni=sosok.vk.com&fp=chrome&pbk=HkLK62c3szw51gYtORRnPlO0v6kxOSd_aCd0J4rTKzo"
        "&sid=1a&spx=%2FbBBGcl2EmHhtque&type=tcp&headerType=none#test-node"
    )
    prof = parse_uri(uri)
    assert prof.protocol == "vless"
    assert prof.address == "45.38.143.119"
    assert prof.port == 443
    assert prof.uuid_or_password == "5458507c-40e7-4883-baa2-3c33e31fb790"
    assert prof.flow == "xtls-rprx-vision"
    assert prof.encryption == "none"
    assert prof.stream.security == "reality"
    assert prof.stream.sni == "sosok.vk.com"
    assert prof.stream.fingerprint == "chrome"
    assert prof.stream.public_key.startswith("HkLK62c3sz")
    assert prof.stream.short_id == "1a"
    assert prof.stream.spider_x == "/bBBGcl2EmHhtque"
    assert prof.remark == "test-node"


def test_parse_vmess_tls() -> None:
    # Minimal vmess with TLS + tcp
    uri = (
        "vmess://eyJ2IjoiMiIsInBzIjoiVGVzdE5vZGUiLCJhZGQiOiIxLjIuMy40IiwicG9ydCI6IjQ0MyIs"
        "ImlkIjoiZDY5NTEwMjYtN2QwMy00ZWQ4LWEzMzEtZDRlNTI1YzA2ZGY0IiwiYWlkIjoiMCIsInNjeSI6"
        "ImF1dG8iLCJuZXQiOiJ0Y3AiLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoi"
        "dGxzIiwic25pIjoiZXhhbXBsZS5jb20iLCJhbHBuIjoiaDIsaHR0cC8xLjEiLCJmcCI6ImNocm9tZSJ9"
    )
    prof = parse_uri(uri)
    assert prof.protocol == "vmess"
    assert prof.address == "1.2.3.4"
    assert prof.port == 443
    assert prof.uuid_or_password == "d6951026-7d03-4ed8-a331-d4e525c06df4"
    assert prof.remark == "TestNode"
    assert prof.alter_id == 0
    assert prof.security_cipher == "auto"
    assert prof.stream.security == "tls"
    assert prof.stream.sni == "example.com"
    assert prof.stream.alpn == ["h2", "http/1.1"]
    assert prof.stream.fingerprint == "chrome"


def test_parse_trojan_reality() -> None:
    uri = (
        "trojan://secret_password@example.com:443"
        "?security=reality&sni=www.oracle.com&fp=chrome"
        "&pbk=iWS4FTE_lzNt1y5qy_zVexOBpNPtkR62vARC5jA7PAA&sid=309f&spx=%2F"
        "&type=tcp&headerType=none#Trojan-Test"
    )
    prof = parse_uri(uri)
    assert prof.protocol == "trojan"
    assert prof.address == "example.com"
    assert prof.port == 443
    assert prof.uuid_or_password == "secret_password"
    assert prof.stream.security == "reality"
    assert prof.stream.sni == "www.oracle.com"
    assert prof.stream.public_key.endswith("PAA")
    assert prof.remark == "Trojan-Test"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "http://example.com",
        "vless://",
        "vless://onlyuuid@",
        "vmess://not_base64!!!",
        "trojan://password@host",  # missing port
    ],
)
def test_invalid_uris_raise_parse_error(bad: str) -> None:
    with pytest.raises(ParseError):
        parse_uri(bad)
