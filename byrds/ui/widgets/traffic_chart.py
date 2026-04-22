"""Real-time traffic chart (downlink / uplink over last 60 s)."""

from __future__ import annotations

from collections import deque

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from byrds.i18n import tr
from byrds.ui.theme import PALETTE


class TrafficChart(QWidget):
    WINDOW = 60  # seconds

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CardLow")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel(tr("dashboard.realtime"))
        title.setObjectName("CardTitle")
        title.setStyleSheet("font-size: 14px;")
        self._ping_label = QLabel(tr("dashboard.ping_ms", ms=0))
        self._ping_label.setObjectName("CardSubtitle")
        self._ping_label.setAlignment(Qt.AlignRight)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._ping_label)
        root.addLayout(header)

        pg.setConfigOptions(antialias=True, foreground=PALETTE.on_surface_variant)
        self._plot = pg.PlotWidget()
        self._plot.setBackground(PALETTE.surface_mid)
        self._plot.showGrid(x=True, y=True, alpha=0.1)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setMenuEnabled(False)
        self._plot.hideButtons()
        self._plot.setYRange(0, 1, padding=0)
        self._plot.getAxis("bottom").setPen(pg.mkPen(PALETTE.outline_variant))
        self._plot.getAxis("left").setPen(pg.mkPen(PALETTE.outline_variant))
        root.addWidget(self._plot, 1)

        self._down = deque([0.0] * self.WINDOW, maxlen=self.WINDOW)
        self._up = deque([0.0] * self.WINDOW, maxlen=self.WINDOW)
        self._xs = list(range(-self.WINDOW + 1, 1))

        self._down_curve = self._plot.plot(
            self._xs,
            list(self._down),
            pen=pg.mkPen(PALETTE.primary, width=2),
            fillLevel=0,
            brush=(0, 219, 233, 40),
        )
        self._up_curve = self._plot.plot(
            self._xs,
            list(self._up),
            pen=pg.mkPen(PALETTE.success, width=2),
        )

    def push(self, down_mbps: float, up_mbps: float) -> None:
        self._down.append(max(down_mbps, 0.0))
        self._up.append(max(up_mbps, 0.0))
        ymax = max(1.0, max(self._down), max(self._up) * 1.2)
        self._plot.setYRange(0, ymax, padding=0)
        self._down_curve.setData(self._xs, list(self._down))
        self._up_curve.setData(self._xs, list(self._up))

    def set_ping(self, ms: int | None) -> None:
        self._ping_label.setText(tr("dashboard.ping_ms", ms=(ms or 0)))

    def reset(self) -> None:
        for _ in range(self.WINDOW):
            self._down.append(0.0)
            self._up.append(0.0)
        self._down_curve.setData(self._xs, list(self._down))
        self._up_curve.setData(self._xs, list(self._up))
