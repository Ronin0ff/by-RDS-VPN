"""Application entry-point for ``python -m byrds`` and PyInstaller ``byRDS.exe``."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from byrds import __brand__, __version__
from byrds.core.controller import AppController
from byrds.i18n import set_language, tr
from byrds.ui.main_window import MainWindow
from byrds.ui.theme import qss

LOG = logging.getLogger("byrds")


def _setup_logging() -> None:
    level = os.environ.get("BYRDS_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    _setup_logging()

    parser = argparse.ArgumentParser(prog=__brand__.replace(" ", "-"))
    parser.add_argument("--minimized", action="store_true", help="start hidden to tray")
    parser.add_argument("--version", action="version", version=f"{__brand__} {__version__}")
    args = parser.parse_args(argv)

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QCoreApplication.setOrganizationName("RDS")
    QCoreApplication.setApplicationName(__brand__)
    QCoreApplication.setApplicationVersion(__version__)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont("Space Grotesk", 10))
    app.setStyleSheet(qss())

    controller = AppController()
    set_language(controller.settings.language)

    window = MainWindow(controller)
    if not (args.minimized or controller.settings.start_minimized):
        window.show()
    else:
        LOG.info("starting minimized")

    # Optional auto-connect on launch
    if controller.settings.auto_connect and controller.active_profile:
        LOG.info("auto-connect to %s", controller.active_profile.short_label())
        controller.connect()

    LOG.info("%s %s started (UI language=%s)", __brand__, __version__, tr("app.brand"))
    try:
        return app.exec()
    finally:
        controller.shutdown()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
