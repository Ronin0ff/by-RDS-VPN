"""Register the app to start with Windows via HKCU\\...\\Run."""

from __future__ import annotations

import logging
import os
import sys

log = logging.getLogger(__name__)

APP_ID = "byRDS-VPN"


def is_supported() -> bool:
    return sys.platform == "win32"


def _exe_command() -> str:  # pragma: no cover (platform-dependent)
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'
    return f'"{sys.executable}" -m byrds --minimized'


def set_autostart(enabled: bool) -> bool:  # pragma: no cover (Windows only)
    if not is_supported():
        log.info("autostart not supported on %s — noop", sys.platform)
        return False
    import winreg  # type: ignore[import-not-found]

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            if enabled:
                winreg.SetValueEx(key, APP_ID, 0, winreg.REG_SZ, _exe_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_ID)
                except FileNotFoundError:
                    pass
    except OSError as exc:
        log.error("autostart toggle failed: %s", exc)
        return False
    return True


def is_autostart_enabled() -> bool:  # pragma: no cover
    if not is_supported():
        return False
    import winreg  # type: ignore[import-not-found]

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_ID)
            return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        log.error("autostart probe failed: %s", exc)
        return False


# Silence unused-import linters when stubs run on non-Windows.
_ = os
