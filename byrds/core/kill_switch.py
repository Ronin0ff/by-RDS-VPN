"""Windows Firewall based kill switch.

Blocks all outbound traffic on the public/private/domain profiles and leaves
loopback + xray's own process free. Entirely no-op on non-Windows.
"""

from __future__ import annotations

import logging
import subprocess
import sys

log = logging.getLogger(__name__)

RULE_NAME = "byRDS-KillSwitch-BlockAll"


def is_supported() -> bool:
    return sys.platform == "win32"


def enable() -> bool:  # pragma: no cover (Windows only)
    if not is_supported():
        log.info("kill switch not supported on %s — noop", sys.platform)
        return False
    # Block all outbound by default on all profiles.
    cmd = [
        "netsh",
        "advfirewall",
        "set",
        "allprofiles",
        "firewallpolicy",
        "blockinbound,blockoutbound",
    ]
    return _run(cmd, "kill-switch enable")


def disable() -> bool:  # pragma: no cover (Windows only)
    if not is_supported():
        return False
    cmd = [
        "netsh",
        "advfirewall",
        "set",
        "allprofiles",
        "firewallpolicy",
        "blockinbound,allowoutbound",
    ]
    return _run(cmd, "kill-switch disable")


def _run(cmd: list[str], reason: str) -> bool:  # pragma: no cover
    try:
        res = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.error("%s failed: %s", reason, exc)
        return False
    if res.returncode != 0:
        log.error("%s: netsh exited %s: %s", reason, res.returncode, res.stderr)
        return False
    log.info("%s ok", reason)
    return True
