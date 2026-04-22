"""Toggle Windows system-wide HTTP/SOCKS proxy settings.

On non-Windows platforms, all calls are no-ops.
"""

from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)


def is_supported() -> bool:
    return sys.platform == "win32"


def set_windows_proxy(host: str, port: int) -> None:  # pragma: no cover (Windows only)
    """Enable Internet Settings proxy via HKCU registry and notify WinInet."""
    if not is_supported():
        log.info("system proxy not supported on %s — noop", sys.platform)
        return
    import winreg  # type: ignore[import-not-found]

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(
                key,
                "ProxyServer",
                0,
                winreg.REG_SZ,
                f"{host}:{port}",
            )
            winreg.SetValueEx(
                key,
                "ProxyOverride",
                0,
                winreg.REG_SZ,
                "localhost;127.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;"
                "172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;"
                "172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;"
                "192.168.*;<local>",
            )
    except OSError as exc:
        log.error("failed to set Windows proxy: %s", exc)
        return

    _refresh_wininet()
    log.info("Windows proxy -> %s:%s enabled", host, port)


def clear_windows_proxy() -> None:  # pragma: no cover (Windows only)
    if not is_supported():
        return
    import winreg  # type: ignore[import-not-found]

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    except OSError as exc:
        log.error("failed to clear Windows proxy: %s", exc)
        return

    _refresh_wininet()
    log.info("Windows proxy disabled")


def _refresh_wininet() -> None:  # pragma: no cover
    import ctypes

    internet_option_settings_changed = 39
    internet_option_refresh = 37
    wininet = ctypes.windll.Wininet  # type: ignore[attr-defined]
    wininet.InternetSetOptionW(0, internet_option_settings_changed, 0, 0)
    wininet.InternetSetOptionW(0, internet_option_refresh, 0, 0)
