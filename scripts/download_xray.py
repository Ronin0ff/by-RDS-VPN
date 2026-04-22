#!/usr/bin/env python3
"""Download the Xray-core release + geo assets into ``vendor/``.

Used by GitHub Actions to assemble a Windows portable .exe.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

RELEASE_API = "https://api.github.com/repos/XTLS/Xray-core/releases/latest"


ASSET_NAME = {
    "windows-x86_64": "Xray-windows-64.zip",
    "windows-x86_32": "Xray-windows-32.zip",
    "linux-x86_64": "Xray-linux-64.zip",
    "macos-x86_64": "Xray-macos-64.zip",
    "macos-arm64": "Xray-macos-arm64-v8a.zip",
}


def _http_get(url: str, accept: str = "application/octet-stream") -> bytes:
    headers = {"User-Agent": "byrds-vpn/0.1", "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} for {url}", file=sys.stderr)
        raise


def download_xray(platform_key: str, target: Path) -> None:
    name = ASSET_NAME[platform_key]
    print("-> Fetching latest Xray-core release metadata from GitHub...")
    meta = json.loads(_http_get(RELEASE_API, accept="application/vnd.github+json"))
    asset = next((a for a in meta.get("assets", []) if a.get("name") == name), None)
    if asset is None:
        raise SystemExit(f"release asset {name!r} not found in latest release")

    print(f"-> Downloading {name} (size={asset['size']:,} bytes)...")
    blob = _http_get(asset["browser_download_url"])
    target.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for member in z.namelist():
            if member.endswith(("/", "\\")):
                continue
            out_name = Path(member).name
            if out_name.lower() in {"xray.exe", "xray", "geoip.dat", "geosite.dat"}:
                dst = target / out_name
                dst.write_bytes(z.read(member))
                if sys.platform != "win32" and out_name == "xray":
                    dst.chmod(0o755)
                print(f"  [ok] {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Xray-core binaries.")
    parser.add_argument(
        "--platform",
        default="windows-x86_64",
        choices=sorted(ASSET_NAME.keys()),
    )
    parser.add_argument(
        "--target",
        default=str(Path(__file__).resolve().parents[1] / "vendor"),
    )
    args = parser.parse_args()
    download_xray(args.platform, Path(args.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
