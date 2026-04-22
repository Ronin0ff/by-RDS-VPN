"""In-memory ring buffer for Xray and application logs (used by the Logs page)."""

from __future__ import annotations

import datetime as _dt
import threading
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Literal

LogLevel = Literal["INFO", "WARN", "OK", "READY", "ERROR"]


@dataclass(slots=True)
class LogEntry:
    timestamp: _dt.datetime
    level: LogLevel
    message: str

    def format(self) -> str:
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}]  [{self.level}]  {self.message}"


class LogBuffer:
    """Thread-safe ring buffer with Qt-friendly listener interface."""

    def __init__(self, capacity: int = 2000) -> None:
        self._buf: deque[LogEntry] = deque(maxlen=capacity)
        self._lock = threading.RLock()
        self._listeners: list[Callable[[LogEntry], None]] = []

    def add(self, level: LogLevel, message: str) -> LogEntry:
        entry = LogEntry(_dt.datetime.now(), level, message)
        with self._lock:
            self._buf.append(entry)
            listeners = list(self._listeners)
        for cb in listeners:
            try:
                cb(entry)
            except Exception:  # noqa: BLE001 — listeners must never kill the sink
                pass
        return entry

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def snapshot(self) -> list[LogEntry]:
        with self._lock:
            return list(self._buf)

    def export(self) -> str:
        with self._lock:
            return "\n".join(e.format() for e in self._buf)

    def subscribe(self, callback: Callable[[LogEntry], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(callback)

        def _unsubscribe() -> None:
            with self._lock:
                if callback in self._listeners:
                    self._listeners.remove(callback)

        return _unsubscribe

    def __iter__(self) -> Iterator[LogEntry]:
        return iter(self.snapshot())
