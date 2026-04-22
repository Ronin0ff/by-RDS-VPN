"""Connection log terminal page."""

from __future__ import annotations

import datetime as _dt

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from byrds.core.controller import AppController
from byrds.core.logs import LogEntry
from byrds.i18n import tr
from byrds.ui.theme import PALETTE

LEVEL_COLORS = {
    "INFO": PALETTE.primary,
    "WARN": PALETTE.warning,
    "OK": PALETTE.success,
    "READY": PALETTE.success,
    "ERROR": PALETTE.error,
}


class LogsPage(QWidget):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._session_id = _dt.datetime.now().strftime("RDS-%Y%m%d-%H%M%S")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel(tr("logs.title"))
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()
        self._clear_btn = QPushButton("🗑  " + tr("logs.clear"))
        self._clear_btn.clicked.connect(self._clear)
        self._export_btn = QPushButton("↓  " + tr("logs.export"))
        self._export_btn.setObjectName("PrimaryButton")
        self._export_btn.clicked.connect(self._export)
        header.addWidget(self._clear_btn)
        header.addWidget(self._export_btn)
        root.addLayout(header)

        status = QHBoxLayout()
        session_lbl = QLabel(tr("logs.session", id=self._session_id))
        session_lbl.setObjectName("CardSubtitle")
        live_lbl = QLabel("● " + tr("logs.live"))
        live_lbl.setStyleSheet(f"color: {PALETTE.primary}; font-weight: 700;")
        live_lbl.setAlignment(Qt.AlignRight)
        status.addWidget(session_lbl)
        status.addStretch()
        status.addWidget(live_lbl)
        root.addLayout(status)

        self._edit = QPlainTextEdit()
        self._edit.setReadOnly(True)
        self._edit.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background: {PALETTE.surface_mid};
                border: 1px solid {PALETTE.outline_variant};
                border-radius: 8px;
                padding: 14px;
                color: {PALETTE.on_surface};
                font-family: "Space Grotesk", monospace;
                font-size: 13px;
            }}
            """
        )
        root.addWidget(self._edit, 1)

        for entry in self._controller.log.snapshot():
            self._append(entry)
        self._controller.log_added.connect(self._append)

    # ------------------------------------------------------------------

    def _append(self, entry: LogEntry) -> None:
        cursor = self._edit.textCursor()
        cursor.movePosition(QTextCursor.End)

        ts_fmt = QTextCharFormat()
        ts_fmt.setForeground(QColor(PALETTE.outline))
        cursor.setCharFormat(ts_fmt)
        cursor.insertText(f"[{entry.timestamp:%Y-%m-%d %H:%M:%S}]   ")

        lvl_fmt = QTextCharFormat()
        lvl_fmt.setForeground(QColor(LEVEL_COLORS.get(entry.level, PALETTE.primary)))
        lvl_fmt.setFontWeight(700)
        cursor.setCharFormat(lvl_fmt)
        cursor.insertText(f"[{entry.level}]   ")

        msg_fmt = QTextCharFormat()
        msg_fmt.setForeground(QColor(PALETTE.on_surface))
        cursor.setCharFormat(msg_fmt)
        cursor.insertText(entry.message + "\n")

        self._edit.setTextCursor(cursor)
        self._edit.ensureCursorVisible()

    def _clear(self) -> None:
        self._edit.clear()
        self._controller.log.clear()

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("logs.export"),
            f"byrds-log-{self._session_id}.txt",
            "Text (*.txt);;All (*)",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._controller.log.export())
