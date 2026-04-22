# PyInstaller spec for the portable Windows `byRDS.exe`
# Usage:
#   python -m PyInstaller byrds.spec

# noqa: F821 — ``Analysis`` / ``PYZ`` / ``EXE`` / ``BUNDLE`` are injected by PyInstaller.
from pathlib import Path

import sys

project_root = Path.cwd()
vendor_dir = project_root / "vendor"

binaries = []
datas = [
    (str(project_root / "byrds" / "assets"), "byrds/assets"),
]
for asset_name in ("xray.exe", "geoip.dat", "geosite.dat"):
    src = vendor_dir / asset_name
    if src.exists():
        datas.append((str(src), "vendor"))

hiddenimports = [
    "byrds.ui.pages.dashboard",
    "byrds.ui.pages.servers",
    "byrds.ui.pages.settings",
    "byrds.ui.pages.logs",
]

a = Analysis(  # type: ignore[name-defined]  # noqa: F821
    ["byrds/__main__.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)  # type: ignore[name-defined]  # noqa: F821

exe = EXE(  # type: ignore[name-defined]  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="byRDS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
