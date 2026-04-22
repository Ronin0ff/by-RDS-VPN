"""Left-hand primary navigation (Dashboard / Servers / Settings / Logs)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from byrds import __version__
from byrds.i18n import tr


class Sidebar(QWidget):
    navigated = Signal(str)  # page id: "dashboard" | "servers" | "settings" | "logs" | "help"

    WIDTH = 240
    PAGES = [
        ("dashboard", "■ ", "nav.dashboard"),
        ("servers", "▤ ", "nav.servers"),
        ("settings", "⚙ ", "nav.settings"),
        ("logs", "≡ ", "nav.logs"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.WIDTH)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 24, 0, 24)
        root.setSpacing(0)

        # Brand block
        brand_box = QVBoxLayout()
        brand_box.setContentsMargins(24, 0, 24, 24)
        brand_box.setSpacing(2)
        brand = QLabel(tr("app.brand"))
        brand.setObjectName("BrandLabel")
        version = QLabel(f"V {__version__}")
        version.setObjectName("VersionLabel")
        brand_box.addWidget(brand)
        brand_box.addWidget(version)
        root.addLayout(brand_box)

        # Nav buttons
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}
        for page_id, icon, key in self.PAGES:
            btn = QPushButton(f"{icon}{tr(key)}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, p=page_id: self.navigated.emit(p))
            self._group.addButton(btn)
            self._buttons[page_id] = btn
            root.addWidget(btn)

        root.addStretch()

        # Footer
        footer = QFrame()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(0)
        help_btn = QPushButton(f"?  {tr('nav.help')}")
        help_btn.setObjectName("NavButton")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(lambda: self.navigated.emit("help"))
        footer_layout.addWidget(help_btn)
        root.addWidget(footer)

        # Default page
        self.select("dashboard")

    def select(self, page_id: str) -> None:
        btn = self._buttons.get(page_id)
        if btn is not None and not btn.isChecked():
            btn.setChecked(True)
