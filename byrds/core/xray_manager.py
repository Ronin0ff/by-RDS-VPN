"""Manage the life-cycle of the bundled ``xray`` process."""

from __future__ import annotations

import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

LogCallback = Callable[[str, str], None]  # (level, message)


def _frozen_base_dir() -> Path | None:
    """Return the PyInstaller ``_MEIPASS`` directory if we are frozen."""
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else None


def locate_xray_binary() -> Path | None:
    """Find ``xray`` binary in vendor/, _MEIPASS/, or $PATH."""
    exe = "xray.exe" if sys.platform == "win32" else "xray"

    candidates: list[Path] = []
    frozen = _frozen_base_dir()
    if frozen:
        candidates.append(frozen / "vendor" / exe)
        candidates.append(frozen / exe)
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root / "vendor" / exe)

    path_entry = shutil.which(exe)
    if path_entry:
        candidates.append(Path(path_entry))

    for c in candidates:
        if c.is_file() and os.access(c, os.X_OK):
            return c
    return None


def geo_assets_dir() -> Path | None:
    """Directory containing ``geoip.dat`` / ``geosite.dat`` (set XRAY_LOCATION_ASSET)."""
    frozen = _frozen_base_dir()
    if frozen and (frozen / "vendor" / "geoip.dat").is_file():
        return frozen / "vendor"
    repo_vendor = Path(__file__).resolve().parents[2] / "vendor"
    if (repo_vendor / "geoip.dat").is_file():
        return repo_vendor
    return None


@dataclass(slots=True)
class XrayStatus:
    running: bool
    pid: int | None
    binary: Path | None
    version: str = ""
    last_error: str = ""


class XrayManager:
    """Start / stop / reload an external ``xray run -c config.json`` process."""

    def __init__(self, log_sink: LogCallback | None = None) -> None:
        self._log_sink = log_sink or (lambda level, msg: None)
        self._proc: subprocess.Popen[str] | None = None
        self._config_path: Path | None = None
        self._reader_thread: threading.Thread | None = None
        self._stop_reader = threading.Event()
        self._lock = threading.RLock()
        self.last_error: str = ""

    # -- public API --------------------------------------------------------

    def status(self) -> XrayStatus:
        with self._lock:
            binary = locate_xray_binary()
            running = self._proc is not None and self._proc.poll() is None
            pid = self._proc.pid if running and self._proc is not None else None
            return XrayStatus(
                running=running,
                pid=pid,
                binary=binary,
                version=self._query_version(binary) if binary else "",
                last_error=self.last_error,
            )

    def start(self, config: dict[str, Any]) -> None:
        """Start ``xray`` with the provided config; replaces any running instance."""
        with self._lock:
            self.stop()
            binary = locate_xray_binary()
            if binary is None:
                self.last_error = "xray binary not found (expected in vendor/xray[.exe])"
                self._log_sink("ERROR", self.last_error)
                raise FileNotFoundError(self.last_error)

            self._config_path = Path(tempfile.mkdtemp(prefix="byrds-")) / "config.json"
            self._config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            self._log_sink("INFO", f"wrote xray config -> {self._config_path}")

            env = os.environ.copy()
            assets = geo_assets_dir()
            if assets:
                env["XRAY_LOCATION_ASSET"] = str(assets)

            cmd = [str(binary), "run", "-c", str(self._config_path)]
            self._log_sink("INFO", f"starting {' '.join(cmd)}")
            try:
                self._proc = subprocess.Popen(  # noqa: S603 — trusted local binary
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                    creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0),
                )
            except OSError as exc:
                self.last_error = f"failed to spawn xray: {exc}"
                self._log_sink("ERROR", self.last_error)
                raise

            self._stop_reader.clear()
            self._reader_thread = threading.Thread(
                target=self._pump_output, name="xray-log", daemon=True
            )
            self._reader_thread.start()
            self._log_sink("READY", f"xray running (pid={self._proc.pid})")

    def stop(self) -> None:
        with self._lock:
            if self._proc is None:
                return
            if self._proc.poll() is None:
                try:
                    if sys.platform == "win32":
                        self._proc.terminate()
                    else:
                        self._proc.send_signal(signal.SIGTERM)
                    self._proc.wait(timeout=5)
                except (subprocess.TimeoutExpired, OSError):
                    try:
                        self._proc.kill()
                    except OSError:
                        pass
            self._stop_reader.set()
            self._proc = None
            if self._reader_thread:
                self._reader_thread.join(timeout=2)
                self._reader_thread = None
            if self._config_path and self._config_path.exists():
                try:
                    shutil.rmtree(self._config_path.parent, ignore_errors=True)
                except OSError:
                    pass
            self._config_path = None
            self._log_sink("INFO", "xray stopped")

    # -- internals ---------------------------------------------------------

    def _query_version(self, binary: Path) -> str:
        try:
            res = subprocess.run(  # noqa: S603
                [str(binary), "version"],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        for line in res.stdout.splitlines():
            if "Xray" in line or line.lower().startswith("xray"):
                return line.strip()
        return res.stdout.splitlines()[0].strip() if res.stdout else ""

    def _pump_output(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        stdout = self._proc.stdout
        while not self._stop_reader.is_set():
            line = stdout.readline()
            if not line:
                break
            line = line.rstrip()
            level = "INFO"
            up = line.lower()
            if "error" in up or "fatal" in up:
                level = "ERROR"
            elif "warn" in up:
                level = "WARN"
            elif "accepted" in up or "started" in up:
                level = "OK"
            self._log_sink(level, line)
        exit_code = self._proc.poll() if self._proc else None
        if exit_code not in (None, 0):
            self._log_sink("ERROR", f"xray exited with code {exit_code}")
        time.sleep(0.05)  # let caller observe final state
