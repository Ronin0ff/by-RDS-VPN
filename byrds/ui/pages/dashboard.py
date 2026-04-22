"""Main Dashboard page — mirrors the ``dashboard_by_rds`` mockup."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from byrds.core.controller import AppController
from byrds.i18n import tr
from byrds.ui.widgets.metric_card import MetricCard
from byrds.ui.widgets.power_button import PowerButton
from byrds.ui.widgets.traffic_chart import TrafficChart


class DashboardPage(QWidget):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header row (title + status text)
        header = QHBoxLayout()
        title = QLabel(tr("dashboard.title"))
        title.setObjectName("SectionTitle")
        self._state_label = QLabel("● " + tr("topbar.system_ready"))
        self._state_label.setObjectName("CardSubtitle")
        self._state_label.setAlignment(Qt.AlignRight)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._state_label)
        root.addLayout(header)

        # Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # Left: big power toggle card
        power_card = QFrame()
        power_card.setObjectName("Card")
        power_layout = QVBoxLayout(power_card)
        power_layout.setContentsMargins(32, 32, 32, 32)
        power_layout.setSpacing(8)

        top_meta = QHBoxLayout()
        caps = QLabel(tr("dashboard.target_ip"))
        caps.setObjectName("LabelCaps")
        self._target_ip = QLabel("—")
        self._target_ip.setObjectName("MonoData")
        top_meta.addWidget(caps)
        top_meta.addSpacing(10)
        top_meta.addWidget(self._target_ip)
        top_meta.addStretch()
        power_layout.addLayout(top_meta)

        power_layout.addStretch()
        self._power = PowerButton()
        self._power.clicked.connect(lambda _checked: self._controller.toggle())
        power_wrap = QHBoxLayout()
        power_wrap.addStretch()
        power_wrap.addWidget(self._power)
        power_wrap.addStretch()
        power_layout.addLayout(power_wrap)

        self._big_state = QLabel(tr("dashboard.disconnected"))
        self._big_state.setAlignment(Qt.AlignCenter)
        self._big_state.setStyleSheet(
            "font-size: 20px; font-weight: 500; color: #DAE3F1; margin-top: 18px;"
        )
        power_layout.addWidget(self._big_state)

        self._hint = QLabel(tr("dashboard.press"))
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setObjectName("CardSubtitle")
        power_layout.addWidget(self._hint)
        power_layout.addStretch()

        grid.addWidget(power_card, 0, 0, 3, 1)

        # Right column: Selected node
        self._node_card = QFrame()
        self._node_card.setObjectName("Card")
        node_layout = QVBoxLayout(self._node_card)
        node_layout.setContentsMargins(20, 18, 20, 18)
        top = QHBoxLayout()
        nc = QLabel(tr("dashboard.selected_node"))
        nc.setObjectName("CardTitle")
        nc.setStyleSheet("font-size: 14px;")
        self._change_btn = QPushButton(tr("dashboard.change"))
        top.addWidget(nc)
        top.addStretch()
        top.addWidget(self._change_btn)
        node_layout.addLayout(top)

        self._node_name = QLabel(tr("dashboard.no_node"))
        self._node_name.setObjectName("CardTitle")
        self._node_addr = QLabel("—")
        self._node_addr.setObjectName("CardSubtitle")
        node_layout.addSpacing(4)
        node_layout.addWidget(self._node_name)
        node_layout.addWidget(self._node_addr)
        node_layout.addStretch()
        grid.addWidget(self._node_card, 0, 1, 1, 2)

        self._down_card = MetricCard("⇣", tr("dashboard.downlink"))
        self._up_card = MetricCard("⇡", tr("dashboard.uplink"))
        grid.addWidget(self._down_card, 1, 1)
        grid.addWidget(self._up_card, 1, 2)

        self._chart = TrafficChart()
        grid.addWidget(self._chart, 2, 1, 1, 2)

        grid.setColumnStretch(0, 7)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 3)
        grid.setRowStretch(2, 1)
        root.addLayout(grid, 1)

        # Wire up controller signals
        self._controller.state_changed.connect(self._on_state_changed)
        self._controller.metrics_sampled.connect(self._on_metrics)
        self._controller.profiles_changed.connect(self._refresh_node)
        self._controller.settings_changed.connect(self._refresh_node)
        self._refresh_node()
        self._on_state_changed(self._controller.state)

    # ------------------------------------------------------------------

    def on_change_clicked(self, handler) -> None:
        self._change_btn.clicked.connect(handler)

    def _on_state_changed(self, state: str) -> None:
        mapping = {
            "disconnected": (
                tr("dashboard.disconnected"),
                tr("dashboard.press"),
                "● " + tr("topbar.system_ready"),
                False,
            ),
            "connecting": (
                tr("topbar.system_busy"),
                "…",
                "● " + tr("topbar.system_busy"),
                True,
            ),
            "connected": (
                tr("dashboard.connected"),
                tr("dashboard.release"),
                "● " + tr("topbar.system_online"),
                False,
            ),
            "error": (
                tr("topbar.system_error"),
                "",
                "● " + tr("topbar.system_error"),
                False,
            ),
        }
        big, hint, status, busy = mapping[state]
        self._big_state.setText(big)
        self._hint.setText(hint)
        self._state_label.setText(status)
        self._power.blockSignals(True)
        self._power.setChecked(state == "connected")
        self._power.blockSignals(False)
        self._power.setBusy(busy)

    def _refresh_node(self) -> None:
        prof = self._controller.active_profile
        if prof is None:
            self._node_name.setText(tr("dashboard.no_node"))
            self._node_addr.setText("—")
            self._target_ip.setText("—")
        else:
            self._node_name.setText(prof.remark or prof.short_label())
            self._node_addr.setText(f"{prof.address}:{prof.port} · {prof.protocol}")
            self._target_ip.setText(prof.address)

    def _on_metrics(self, down: float, up: float, ping: int) -> None:
        self._down_card.setValue(down, active=self._controller.state == "connected")
        self._up_card.setValue(up, active=self._controller.state == "connected")
        self._chart.push(down, up)
        self._chart.set_ping(ping if ping > 0 else None)
