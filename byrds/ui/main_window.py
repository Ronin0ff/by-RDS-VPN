"""Main application window — composes sidebar + stacked pages."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from byrds import __brand__, __version__
from byrds.core.controller import AppController
from byrds.i18n import tr
from byrds.ui.pages import DashboardPage, LogsPage, ServersPage, SettingsPage
from byrds.ui.theme import PALETTE
from byrds.ui.widgets import Sidebar, TopBar

PAGE_INDEX = {"dashboard": 0, "servers": 1, "settings": 2, "logs": 3}


def make_app_icon() -> QIcon:
    """Generate a brand icon in-memory (pure Qt — avoids shipping an asset)."""
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

    size = QSize(64, 64)
    pixmap = QPixmap(size)
    pixmap.fill(QColor(PALETTE.surface_lowest))
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QColor(PALETTE.primary))
    p.setBrush(QColor(PALETTE.surface_mid))
    p.drawRoundedRect(4, 4, size.width() - 8, size.height() - 8, 10, 10)
    font = QFont("Space Grotesk", 18, QFont.Bold)
    p.setFont(font)
    p.setPen(QColor(PALETTE.primary))
    p.drawText(pixmap.rect(), Qt.AlignCenter, "RDS")
    p.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self.setWindowTitle(f"{__brand__} · v{__version__}")
        self.setMinimumSize(1100, 720)
        self.setWindowIcon(make_app_icon())

        root = QWidget()
        root.setObjectName("RootWidget")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.navigated.connect(self._on_nav)
        layout.addWidget(self._sidebar)

        # Right column: top bar + stacked pages
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._topbar = TopBar()
        right_layout.addWidget(self._topbar)

        self._stack = QStackedWidget()
        self._dashboard = DashboardPage(controller)
        self._dashboard.on_change_clicked(lambda: self._on_nav("servers"))
        self._servers = ServersPage(controller)
        self._settings = SettingsPage(controller)
        self._logs = LogsPage(controller)
        for page in (self._dashboard, self._servers, self._settings, self._logs):
            self._stack.addWidget(page)
        right_layout.addWidget(self._stack, 1)

        layout.addWidget(right, 1)
        self.setCentralWidget(root)

        # Tray icon
        self._tray = QSystemTrayIcon(self.windowIcon(), self)
        self._tray.setToolTip(__brand__)
        self._tray.activated.connect(self._on_tray_activated)
        self._build_tray_menu()
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.show()

        self._controller.state_changed.connect(self._on_state_changed)
        self._controller.error_raised.connect(self._on_error)
        self._on_state_changed(self._controller.state)

    # ------------------------------------------------------------------

    def _on_nav(self, page_id: str) -> None:
        if page_id == "help":
            QMessageBox.information(
                self,
                __brand__,
                f"{__brand__}\n"
                f"Version {__version__}\n\n"
                "Windows VPN client for VLESS / VMess / Trojan.\n"
                "Docs: https://github.com/Ronin0ff/by-RDS-VPN",
            )
            return
        idx = PAGE_INDEX.get(page_id)
        if idx is None:
            return
        self._stack.setCurrentIndex(idx)
        self._sidebar.select(page_id)

    def _on_state_changed(self, state: str) -> None:
        mapping = {
            "disconnected": "ready",
            "connecting": "connecting",
            "connected": "online",
            "error": "error",
        }
        self._topbar.set_state(mapping.get(state, "ready"))

    def _on_error(self, key: str) -> None:
        QMessageBox.warning(self, __brand__, tr(key))

    # ------------------------------------------------------------------
    # Tray
    # ------------------------------------------------------------------

    def _build_tray_menu(self) -> None:
        from PySide6.QtWidgets import QMenu

        menu = QMenu()
        show_action = QAction(tr("tray.show"), self)
        show_action.triggered.connect(self.showNormal)
        show_action.triggered.connect(self.activateWindow)
        connect_action = QAction(tr("tray.connect"), self)
        connect_action.triggered.connect(self._controller.connect)
        disconnect_action = QAction(tr("tray.disconnect"), self)
        disconnect_action.triggered.connect(self._controller.disconnect)
        quit_action = QAction(tr("tray.quit"), self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(connect_action)
        menu.addAction(disconnect_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)

    def _on_tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isHidden() or self.isMinimized():
                self.showNormal()
                self.activateWindow()
            else:
                self.hide()

    def _quit_app(self) -> None:
        from PySide6.QtWidgets import QApplication

        self._controller.shutdown()
        QApplication.quit()

    # ------------------------------------------------------------------

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if (
            event.type() == QEvent.WindowStateChange
            and self.isMinimized()
            and self._controller.settings.minimize_to_tray
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            self.hide()
        super().changeEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if (
            self._controller.settings.minimize_to_tray
            and QSystemTrayIcon.isSystemTrayAvailable()
        ):
            event.ignore()
            self.hide()
            return
        self._controller.shutdown()
        event.accept()
