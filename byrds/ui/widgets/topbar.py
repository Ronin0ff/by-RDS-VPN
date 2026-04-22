"""Slim top-bar with SECURE / status indicator (matches mockup)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from byrds.i18n import tr
from byrds.ui.theme import PALETTE


class StatusDot(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = PALETTE.outline_variant

    def set_color(self, hex_color: str) -> None:
        self._color = hex_color
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(self._color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(0, 0, 9, 9)


class TopBar(QWidget):
    HEIGHT = 48

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TopBar")
        self.setFixedHeight(self.HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        self._status_text = QLabel(tr("topbar.system_ready"))
        self._status_text.setObjectName("CardSubtitle")
        self._dot = StatusDot()

        layout.addWidget(self._dot)
        layout.addWidget(self._status_text)
        layout.addStretch()

        secure = QLabel(tr("topbar.secure"))
        secure.setObjectName("TopBarLabel")
        layout.addWidget(secure)

    def set_state(self, state: str) -> None:
        """state: 'ready' | 'connecting' | 'online' | 'error'."""
        mapping = {
            "ready": (PALETTE.outline_variant, tr("topbar.system_ready")),
            "connecting": (PALETTE.warning, tr("topbar.system_busy")),
            "online": (PALETTE.primary, tr("topbar.system_online")),
            "error": (PALETTE.error, tr("topbar.system_error")),
        }
        color, text = mapping.get(state, mapping["ready"])
        self._dot.set_color(color)
        self._status_text.setText(text)
