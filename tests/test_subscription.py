"""Tests for subscription decoding / importing."""

from __future__ import annotations

import base64

from byrds.core.subscription import import_text


def test_import_plain_text_multiline() -> None:
    blob = (
        "vless://abc-1234@1.1.1.1:443?encryption=none&flow=xtls-rprx-vision"
        "&security=reality&sni=a.com&pbk=p&sid=1&type=tcp#n1\n"
        "trojan://pwd@2.2.2.2:443?security=tls&sni=b.com&type=tcp#n2\n"
    )
    profs, errors = import_text(blob)
    assert not errors
    assert len(profs) == 2
    assert profs[0].protocol == "vless"
    assert profs[1].protocol == "trojan"


def test_import_base64_subscription_payload() -> None:
    plain = (
        "vless://abc-1234@1.1.1.1:443?encryption=none&flow=xtls-rprx-vision"
        "&security=reality&sni=a.com&pbk=p&sid=1&type=tcp#n1\n"
        "trojan://pwd@2.2.2.2:443?security=tls&sni=b.com&type=tcp#n2\n"
    )
    encoded = base64.b64encode(plain.encode("utf-8")).decode("ascii")
    profs, errors = import_text(encoded)
    assert not errors
    assert [p.protocol for p in profs] == ["vless", "trojan"]
