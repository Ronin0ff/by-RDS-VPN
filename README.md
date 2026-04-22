# by RDS — Windows VPN Client

Профессиональный Windows VPN-клиент с поддержкой протоколов **VLESS** (+ REALITY, XTLS-Vision, WS, gRPC), **VMess** и **Trojan** на базе [Xray-core](https://github.com/XTLS/Xray-core).

![by RDS](docs/dashboard_preview.png)

## Возможности

- **Протоколы:** VLESS (REALITY / XTLS / WS / gRPC / TCP), VMess (base64), Trojan (TLS / REALITY)
- **Импорт:** вставка ссылок, импорт `.txt`-файла, подписки (HTTP/HTTPS URL, base64)
- **Серверы:** группировка по странам, TCP-ping, speed-test через прокси, поиск и избранное
- **Маршрутизация:**
  - Kill Switch (Windows Firewall rules)
  - MUX (multiplexing)
  - Direct Domains (whitelist / bypass)
  - Proxy Domains (force through VPN)
  - Block Domains (чёрный список)
  - Geosite-наборы (RU / CN / private)
  - Application Split Tunneling (proxy / bypass / direct per-process)
- **Настройки:** DNS (system / Cloudflare / AdGuard / custom DoH), локальные SOCKS+HTTP порты, автозапуск Windows, hotkeys
- **Аналитика:** real-time график трафика, ping history, session journal, Logs-терминал с экспортом
- **UI:** тёмная тема, фирменный акцент `#00DBE9`, Space Grotesk + Inter, иконка в трее

## Сборка portable `.exe`

CI собирает артефакт автоматически через GitHub Actions (`.github/workflows/windows-build.yml`).
Вручную на Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
python scripts/download_xray.py         # скачивает xray.exe + geo*.dat в vendor/
pyinstaller byrds.spec                  # собирает dist/byRDS.exe
```

## Разработка (Linux/macOS — без запуска VPN)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest                                  # тесты парсеров, config-builder
ruff check .
python -m byrds                         # запуск UI (Qt)
```

На Linux/macOS функции Windows-specific (system proxy, autostart, kill switch) автоматически отключаются — UI и парсеры полностью работают для отладки.

## Структура

```
byrds/
├── app.py, __main__.py        # точка входа
├── core/
│   ├── parsers/               # vless / vmess / trojan URI → Profile
│   ├── config_builder.py      # Profile + Settings → Xray JSON
│   ├── xray_manager.py        # subprocess, hot-reload, rotate logs
│   ├── stats.py, ping.py, speedtest.py
│   ├── system_proxy.py, kill_switch.py, autostart.py
│   ├── subscription.py, storage.py, router.py
│   └── logs.py
├── ui/                        # PySide6 Dashboard / Servers / Settings / Logs
└── i18n/                      # RU / EN

tests/                         # pytest + sample vless.txt (40 URI)
scripts/download_xray.py       # CI helper
.github/workflows/             # ci.yml, windows-build.yml
byrds.spec                     # PyInstaller (onefile)
```

## Лицензия

MIT. См. [LICENSE](LICENSE).

---

by RDS · 2026
