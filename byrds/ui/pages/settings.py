"""Settings / Routing page."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from byrds.core.controller import AppController
from byrds.core.storage import Settings
from byrds.i18n import set_language, tr


class _Card(QFrame):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 18, 20, 18)
        self._layout.setSpacing(12)
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        self._layout.addWidget(title_label)

    def add(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)


class SettingsPage(QWidget):
    def __init__(self, controller: AppController, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel(tr("settings.title"))
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_general(), tr("settings.tab_general"))
        self._tabs.addTab(self._build_routing(), tr("settings.tab_routing"))
        root.addWidget(self._tabs, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        self._reset_btn = QPushButton(tr("settings.reset"))
        self._reset_btn.clicked.connect(self._reset)
        self._apply_btn = QPushButton(tr("settings.apply"))
        self._apply_btn.setObjectName("PrimaryButton")
        self._apply_btn.clicked.connect(self._apply)
        footer.addWidget(self._reset_btn)
        footer.addWidget(self._apply_btn)
        root.addLayout(footer)

        self._load_from_settings()

    # ------------------------------------------------------------------
    # Build tabs
    # ------------------------------------------------------------------

    def _build_general(self) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(0, 16, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Behaviour card
        behaviour = _Card("Behaviour")
        self._autostart = QCheckBox(tr("settings.autostart"))
        self._tray = QCheckBox(tr("settings.tray"))
        self._auto_connect = QCheckBox(tr("settings.auto_connect"))
        self._auto_reconnect = QCheckBox(tr("settings.auto_reconnect"))
        self._system_proxy = QCheckBox(tr("settings.system_proxy"))
        self._allow_lan = QCheckBox(tr("settings.allow_lan"))
        for w in (
            self._autostart,
            self._tray,
            self._auto_connect,
            self._auto_reconnect,
            self._system_proxy,
            self._allow_lan,
        ):
            behaviour.add(w)
        grid.addWidget(behaviour, 0, 0)

        # Network card
        network = _Card("Network")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)

        self._socks_port = QSpinBox()
        self._socks_port.setRange(1024, 65535)
        form.addRow(tr("settings.socks_port"), self._socks_port)

        self._http_port = QSpinBox()
        self._http_port.setRange(1024, 65535)
        form.addRow(tr("settings.http_port"), self._http_port)

        self._dns = QComboBox()
        self._dns.addItems(["system", "cloudflare", "adguard", "google", "custom"])
        form.addRow(tr("settings.dns"), self._dns)

        self._language = QComboBox()
        self._language.addItem("Русский", "ru")
        self._language.addItem("English", "en")
        form.addRow(tr("settings.language"), self._language)
        network.add_layout(form)
        grid.addWidget(network, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(1, 1)
        return page

    def _build_routing(self) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        grid.setContentsMargins(0, 16, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Global rules card
        global_card = _Card(tr("settings.global_rules"))
        self._kill_switch = QCheckBox(tr("settings.kill_switch"))
        ks_desc = QLabel(tr("settings.kill_switch_desc"))
        ks_desc.setObjectName("CardSubtitle")
        self._mux = QCheckBox(tr("settings.mux"))
        mx_desc = QLabel(tr("settings.mux_desc"))
        mx_desc.setObjectName("CardSubtitle")
        for w in (self._kill_switch, ks_desc, self._mux, mx_desc):
            global_card.add(w)
        grid.addWidget(global_card, 0, 0)

        # Direct domains card
        direct_card = _Card(tr("settings.direct_domains"))
        hint = QLabel(tr("settings.direct_domains_hint"))
        hint.setObjectName("CardSubtitle")
        hint.setWordWrap(True)
        direct_card.add(hint)
        self._direct_list = QListWidget()
        direct_card.add(self._direct_list)

        add_row = QHBoxLayout()
        add_btn = QPushButton(tr("settings.add"))
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._add_direct_domain)
        del_btn = QPushButton("×")
        del_btn.setObjectName("IconOnly")
        del_btn.clicked.connect(self._remove_direct_domain)
        add_row.addStretch()
        add_row.addWidget(del_btn)
        add_row.addWidget(add_btn)
        direct_card.add_layout(add_row)
        grid.addWidget(direct_card, 1, 0)

        # Split tunnel card
        split_card = _Card(tr("settings.split_tunnel"))
        self._split_list = QListWidget()
        split_card.add(self._split_list)

        split_row = QHBoxLayout()
        browse_btn = QPushButton(tr("settings.browse_app"))
        browse_btn.clicked.connect(self._browse_app)
        split_row.addStretch()
        split_row.addWidget(browse_btn)
        split_card.add_layout(split_row)
        grid.addWidget(split_card, 0, 1, 2, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return page

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def _load_from_settings(self) -> None:
        s = self._controller.settings
        self._autostart.setChecked(s.autostart)
        self._tray.setChecked(s.minimize_to_tray)
        self._auto_connect.setChecked(s.auto_connect)
        self._auto_reconnect.setChecked(s.auto_reconnect)
        self._system_proxy.setChecked(s.system_proxy_on_connect)
        self._allow_lan.setChecked(s.allow_lan)
        self._socks_port.setValue(s.socks_port)
        self._http_port.setValue(s.http_port)
        idx = self._dns.findText(s.dns_mode)
        if idx >= 0:
            self._dns.setCurrentIndex(idx)
        lang_idx = self._language.findData(s.language)
        if lang_idx >= 0:
            self._language.setCurrentIndex(lang_idx)
        self._kill_switch.setChecked(s.enable_kill_switch)
        self._mux.setChecked(s.enable_mux)

        self._direct_list.clear()
        self._direct_list.addItems(list(s.direct_domains))
        self._split_list.clear()
        for entry in s.split_tunnel_apps:
            self._split_list.addItem(
                f"{entry.get('name', '')}  [{entry.get('mode', 'proxy')}]  — {entry.get('path', '')}"
            )

    def _add_direct_domain(self) -> None:
        text, ok = QInputDialog.getText(self, "Add domain", "Domain (supports *.example):")
        if ok and text.strip():
            self._direct_list.addItem(text.strip())

    def _remove_direct_domain(self) -> None:
        for item in self._direct_list.selectedItems():
            self._direct_list.takeItem(self._direct_list.row(item))

    def _browse_app(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self, tr("settings.browse_app"), "", "Executables (*.exe *.app);;All (*)"
        )
        if not path:
            return
        mode, ok = QInputDialog.getItem(
            self, "Mode", "Mode:", ["proxy", "bypass", "direct"], 0, False
        )
        if not ok:
            return
        name = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        self._split_list.addItem(f"{name}  [{mode}]  — {path}")

    def _apply(self) -> None:
        s = self._controller.settings
        s.autostart = self._autostart.isChecked()
        s.minimize_to_tray = self._tray.isChecked()
        s.auto_connect = self._auto_connect.isChecked()
        s.auto_reconnect = self._auto_reconnect.isChecked()
        s.system_proxy_on_connect = self._system_proxy.isChecked()
        s.allow_lan = self._allow_lan.isChecked()
        s.socks_port = self._socks_port.value()
        s.http_port = self._http_port.value()
        s.dns_mode = self._dns.currentText()
        s.language = self._language.currentData() or "ru"
        s.enable_kill_switch = self._kill_switch.isChecked()
        s.enable_mux = self._mux.isChecked()

        s.direct_domains = [
            self._direct_list.item(i).text() for i in range(self._direct_list.count())
        ]

        split: list[dict] = []
        for i in range(self._split_list.count()):
            text = self._split_list.item(i).text()
            # "name  [mode]  — path"
            try:
                name, rest = text.split("  [", 1)
                mode, rest = rest.split("]  — ", 1)
                split.append({"name": name.strip(), "mode": mode.strip(), "path": rest.strip()})
            except ValueError:
                continue
        s.split_tunnel_apps = split

        self._controller.save_settings()
        self._controller.apply_system_settings()
        set_language(s.language)

    def _reset(self) -> None:
        self._controller.settings = Settings()
        self._controller.save_settings()
        self._load_from_settings()
