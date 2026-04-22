"""Large round on/off button that sits at the centre of the Dashboard."""

from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton

from byrds.ui.theme import PALETTE


class PowerButton(QAbstractButton):
    """A tactile square-with-rounded-corners power toggle (matches the mockup)."""

    stateChanged = Signal(bool)

    _SIZE = 180

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(self._SIZE, self._SIZE)
        self._busy = False
        self.toggled.connect(self.stateChanged.emit)

    def setBusy(self, busy: bool) -> None:
        self._busy = busy
        self.setEnabled(not busy)
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._SIZE, self._SIZE)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = QRect(6, 6, self._SIZE - 12, self._SIZE - 12)
        if self.isChecked():
            accent = QColor(PALETTE.primary)
            bg = QColor(PALETTE.surface_mid)
        elif self._busy:
            accent = QColor(PALETTE.warning)
            bg = QColor(PALETTE.surface_low)
        else:
            accent = QColor(PALETTE.outline)
            bg = QColor(PALETTE.surface_low)

        p.setBrush(bg)
        pen = QPen(accent, 1.5)
        p.setPen(pen)
        p.drawRoundedRect(rect, 18, 18)

        # glow when active
        if self.isChecked():
            glow_pen = QPen(QColor(0, 219, 233, 70), 8)
            p.setPen(glow_pen)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), 20, 20)

        # power glyph
        centre = rect.center()
        radius = 28
        pen = QPen(accent, 3)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(
            centre.x() - radius,
            centre.y() - radius + 4,
            radius * 2,
            radius * 2,
            40 * 16,
            260 * 16,
        )
        p.drawLine(centre.x(), centre.y() - radius + 2, centre.x(), centre.y() + 4)
