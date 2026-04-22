"""Servers page — list profiles grouped by country, with ping/speed tests."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from byrds.core.controller import AppController
from byrds.core.parsers import ParseError
from byrds.core.parsers.base import Profile
from byrds.core.ping import ping_many
from byrds.core.subscription import (
    fetch_subscription,
    import_file,
    import_single,
    import_text,
)
from byrds.i18n import tr

log = logging.getLogger(__name__)


COLUMNS = ["", "Name", "Protocol", "Address", "Ping", "Speed"]


class _PingWorker(QThread):
    done = Signal(dict)

    def __init__(self, profiles: list[Profile]) -> None:
        super().__init__()
        self._profiles = profiles

    def run(self) -> None:
        self.done.emit(ping_many(self._profiles))


class ServersPage(QWidget):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._ping_worker: _PingWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel(tr("servers.title"))
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText(tr("servers.search"))
        self._search.setFixedWidth(260)
        self._search.textChanged.connect(self._refresh_table)
        header.addWidget(self._search)

        self._test_btn = QPushButton("⚡ " + tr("servers.test_all"))
        self._test_btn.clicked.connect(self._ping_all)
        header.addWidget(self._test_btn)

        self._import_btn = QPushButton("↓ " + tr("servers.import"))
        self._import_btn.setObjectName("PrimaryButton")
        self._import_btn.clicked.connect(self._show_import_menu)
        header.addWidget(self._import_btn)

        root.addLayout(header)

        # Count
        self._count_label = QLabel()
        self._count_label.setObjectName("CardSubtitle")
        root.addWidget(self._count_label)

        # Table
        self._table = QTableWidget(0, len(COLUMNS))
        self._table.setHorizontalHeaderLabels(COLUMNS)
        self._table.verticalHeader().hide()
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context)
        self._table.doubleClicked.connect(lambda _: self._activate_selected())
        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(False)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 6):
            header_view.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        root.addWidget(self._table, 1)

        # Footer help
        footer = QFrame()
        footer.setObjectName("CardLow")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(18, 14, 18, 14)
        tip = QLabel(
            "TIP: импорт из <b>.txt</b>, вставка <b>vless://…</b> или HTTP(S) подписка. "
            "Двойной клик — выбрать узел активным."
        )
        tip.setObjectName("CardSubtitle")
        tip.setWordWrap(True)
        footer_layout.addWidget(tip)
        root.addWidget(footer)

        self._controller.profiles_changed.connect(self._refresh_table)
        self._refresh_table()

    # ----- helpers --------------------------------------------------------

    def _current_profiles(self) -> list[Profile]:
        query = self._search.text().strip().lower()
        profs = self._controller.profiles
        if query:
            profs = [
                p
                for p in profs
                if query in (p.remark or "").lower()
                or query in p.address.lower()
                or query in p.protocol
            ]
        return profs

    def _refresh_table(self) -> None:
        profs = self._current_profiles()
        self._count_label.setText(tr("servers.count", n=len(self._controller.profiles)))
        self._table.setRowCount(len(profs))
        active_id = (
            self._controller.active_profile.id if self._controller.active_profile else ""
        )
        for row, p in enumerate(profs):
            bullet = "●" if p.id == active_id else ("★" if p.favorite else "○")
            items = [
                QTableWidgetItem(bullet),
                QTableWidgetItem(p.remark or p.short_label()),
                QTableWidgetItem(p.protocol),
                QTableWidgetItem(f"{p.address}:{p.port}"),
                QTableWidgetItem("—" if p.last_ping_ms is None else f"{p.last_ping_ms} ms"),
                QTableWidgetItem(
                    "—"
                    if p.last_speed_mbps is None
                    else f"{p.last_speed_mbps:.1f} Mbps"
                ),
            ]
            items[0].setTextAlignment(Qt.AlignCenter)
            items[0].setData(Qt.UserRole, p.id)
            for col, it in enumerate(items):
                self._table.setItem(row, col, it)

    def _selected_profile(self) -> Profile | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if item is None:
            return None
        pid = item.data(Qt.UserRole)
        return next((p for p in self._controller.profiles if p.id == pid), None)

    def _activate_selected(self) -> None:
        prof = self._selected_profile()
        if prof is None:
            return
        self._controller.set_active_profile(prof.id)
        self._refresh_table()

    def _on_context(self, pos) -> None:
        prof = self._selected_profile()
        if prof is None:
            return
        menu = QMenu(self)
        act_activate = menu.addAction("Make active")
        act_fav = menu.addAction("Toggle favorite")
        menu.addSeparator()
        act_delete = menu.addAction(tr("servers.delete"))
        chosen = menu.exec(self._table.viewport().mapToGlobal(pos))
        if chosen == act_activate:
            self._activate_selected()
        elif chosen == act_fav:
            prof.favorite = not prof.favorite
            self._controller.save_profiles()
            self._refresh_table()
        elif chosen == act_delete:
            self._controller.remove_profile(prof.id)

    def _show_import_menu(self) -> None:
        menu = QMenu(self)
        act_paste = menu.addAction(tr("servers.import_text"))
        act_file = menu.addAction(tr("servers.import_file"))
        act_sub = menu.addAction(tr("servers.import_subscription"))
        chosen = menu.exec(
            self._import_btn.mapToGlobal(self._import_btn.rect().bottomLeft())
        )
        if chosen == act_paste:
            self._import_paste()
        elif chosen == act_file:
            self._import_file()
        elif chosen == act_sub:
            self._import_subscription()

    def _import_paste(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, tr("servers.import_text"), "URI:", ""
        )
        if not ok or not text.strip():
            return
        try:
            if "\n" not in text.strip():
                profs = [import_single(text.strip())]
                errors: list[tuple[str, str]] = []
            else:
                profs, errors = import_text(text)
        except ParseError as exc:
            QMessageBox.critical(self, "Import", f"Parse error: {exc}")
            return
        added = self._controller.add_profiles(profs)
        self._report_import(added, errors)

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("servers.import_file"), "", "Text (*.txt);;All (*)"
        )
        if not path:
            return
        profs, errors = import_file(Path(path))
        added = self._controller.add_profiles(profs)
        self._report_import(added, errors)

    def _import_subscription(self) -> None:
        url, ok = QInputDialog.getText(
            self, tr("servers.import_subscription"), "https://...", text="https://"
        )
        if not ok or not url.strip():
            return

        def _task() -> object:
            return fetch_subscription(url.strip())

        def _cb(result) -> None:
            if isinstance(result, Exception):
                QMessageBox.critical(self, "Subscription", str(result))
                return
            profs, errors = result
            added = self._controller.add_profiles(profs)
            self._report_import(added, errors)

        self._controller.run_async(_task, _cb)

    def _report_import(self, added: int, errors: list[tuple[str, str]]) -> None:
        msg = f"Added {added} profile(s)."
        if errors:
            msg += f"\n{len(errors)} failed to parse:\n" + "\n".join(
                f"- {reason}" for _, reason in errors[:5]
            )
        QMessageBox.information(self, "Import", msg)

    # ----- ping -----------------------------------------------------------

    def _ping_all(self) -> None:
        if self._ping_worker is not None and self._ping_worker.isRunning():
            return
        profs = self._current_profiles()
        if not profs:
            return
        self._test_btn.setEnabled(False)
        worker = _PingWorker(profs)
        worker.done.connect(lambda results: self._apply_ping_results(results, profs))
        worker.finished.connect(lambda: self._test_btn.setEnabled(True))
        self._ping_worker = worker
        worker.start()

    def _apply_ping_results(
        self, results: dict[str, int | None], profs: list[Profile]
    ) -> None:
        for p in profs:
            p.last_ping_ms = results.get(p.id)
        self._controller.save_profiles()
        self._refresh_table()
