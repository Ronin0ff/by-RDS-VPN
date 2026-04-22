"""Large "metric card" widget showing a label + big number."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class MetricCard(QFrame):
    def __init__(self, icon: str, title: str, unit: str = "MB/s", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("CardLow")
        self.setMinimumHeight(140)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(6)
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("LabelCaps")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("CardTitle")
        title_lbl.setStyleSheet("font-size: 14px;")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        root.addLayout(header)

        root.addStretch()

        bottom = QHBoxLayout()
        bottom.setSpacing(6)
        bottom.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        self._value = QLabel("0.00")
        self._value.setObjectName("BigMetricDim")
        self._value.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        self._unit = QLabel(unit)
        self._unit.setObjectName("CardSubtitle")
        self._unit.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        bottom.addStretch()
        bottom.addWidget(self._value)
        bottom.addWidget(self._unit)
        root.addLayout(bottom)

    def setValue(self, value: float, active: bool = False) -> None:  # noqa: N802
        self._value.setText(f"{value:.2f}")
        self._value.setObjectName("BigMetric" if active else "BigMetricDim")
        self._value.style().unpolish(self._value)
        self._value.style().polish(self._value)
