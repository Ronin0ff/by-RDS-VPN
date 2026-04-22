"""Persistent application storage (settings + profiles)."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

from byrds.core.parsers.base import Profile, StreamSettings

log = logging.getLogger(__name__)


def app_data_dir() -> Path:
    """Return per-user writable directory for config / logs."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "byRDS"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "byRDS"
    xdg = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(xdg) / "byRDS"


@dataclass(slots=True)
class Settings:
    """User-tunable application settings."""

    # Network
    socks_port: int = 10808
    http_port: int = 10809
    api_port: int = 10085
    allow_lan: bool = False

    # DNS
    dns_mode: str = "system"  # system / cloudflare / adguard / custom
    custom_dns: list[str] = field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])

    # Routing
    enable_kill_switch: bool = False
    enable_mux: bool = False
    mux_concurrency: int = 8
    system_proxy_on_connect: bool = True
    tun_mode: bool = False  # future: wintun TUN mode

    # Routing rules
    direct_domains: list[str] = field(default_factory=lambda: ["localhost", "*.local"])
    proxy_domains: list[str] = field(default_factory=list)
    block_domains: list[str] = field(default_factory=list)
    direct_ips: list[str] = field(default_factory=lambda: ["geoip:private"])
    geosite_direct: list[str] = field(default_factory=list)
    geosite_proxy: list[str] = field(default_factory=list)
    split_tunnel_apps: list[dict[str, str]] = field(default_factory=list)
    # each entry: {"name": "firefox", "path": "C:/...", "mode": "proxy|bypass|direct"}

    # Behaviour
    autostart: bool = False
    minimize_to_tray: bool = True
    start_minimized: bool = False
    auto_connect: bool = False
    auto_reconnect: bool = True
    language: str = "ru"  # ru / en
    theme: str = "dark"

    # Last-known state
    active_profile_id: str = ""
    last_window_geometry: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        kwargs: dict[str, Any] = {}
        for f in fields(cls):
            if f.name in data:
                kwargs[f.name] = data[f.name]
        return cls(**kwargs)


def _profile_to_dict(p: Profile) -> dict[str, Any]:
    d = asdict(p)
    # StreamSettings is a dataclass too; asdict handles nested dataclasses.
    return d


def _profile_from_dict(d: dict[str, Any]) -> Profile:
    stream_data = d.get("stream") or {}
    stream = StreamSettings(
        **{k: v for k, v in stream_data.items() if k in {f.name for f in fields(StreamSettings)}}
    )
    prof_kwargs = {k: v for k, v in d.items() if k in {f.name for f in fields(Profile)}}
    prof_kwargs["stream"] = stream
    return Profile(**prof_kwargs)


class Storage:
    """Simple JSON-file backed storage for settings and profiles."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or app_data_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.root / "settings.json"
        self.profiles_path = self.root / "profiles.json"
        self.logs_path = self.root / "logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)

    # --- settings ---
    def load_settings(self) -> Settings:
        if not self.settings_path.exists():
            return Settings()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            return Settings.from_dict(data)
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("failed to read settings.json (%s); using defaults", exc)
            return Settings()

    def save_settings(self, settings: Settings) -> None:
        self._atomic_write(self.settings_path, settings.to_dict())

    # --- profiles ---
    def load_profiles(self) -> list[Profile]:
        if not self.profiles_path.exists():
            return []
        try:
            raw = json.loads(self.profiles_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("failed to read profiles.json (%s); starting empty", exc)
            return []
        out: list[Profile] = []
        for item in raw:
            try:
                out.append(_profile_from_dict(item))
            except (TypeError, KeyError) as exc:
                log.warning("skipping malformed profile %r: %s", item.get("id"), exc)
        return out

    def save_profiles(self, profiles: list[Profile]) -> None:
        self._atomic_write(self.profiles_path, [_profile_to_dict(p) for p in profiles])

    def _atomic_write(self, path: Path, data: Any) -> None:
        if is_dataclass(data):
            data = asdict(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp_name = tmp.name
        os.replace(tmp_name, path)
