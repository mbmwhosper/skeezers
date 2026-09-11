#!/usr/bin/env python3
"""Create a Cloudflare Pages bundle from redistributable catalog assets."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = SITE_ROOT / "dist-cloudflare"
MAX_ASSET_BYTES = 25 * 1024 * 1024
ROOT_FILES = (
    "_headers",
    "app.js",
    "icon.svg",
    "index.html",
    "manifest.webmanifest",
    "styles.css",
    "sw.js",
    "third-party.html",
)


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()

    for name in ROOT_FILES:
        shutil.copy2(SITE_ROOT / name, OUTPUT / name)
    shutil.copytree(SITE_ROOT / "assets", OUTPUT / "assets")
    shutil.copytree(SITE_ROOT / "third_party", OUTPUT / "third_party")

    catalog = json.loads((SITE_ROOT / "catalog.json").read_text())
    gogoat_output = OUTPUT / "games" / "gogoat"
    gogoat_output.mkdir(parents=True)
    for game in catalog:
        if game["source"] != "gogoat35" or not game["local"]:
            continue
        relative = Path(unquote(urlsplit(game["url"]).path))
        if relative.parent != Path("games/gogoat"):
            raise ValueError(f"unsafe local gogoat path: {game['id']}")
        shutil.copy2(SITE_ROOT / relative, gogoat_output / relative.name)
    (OUTPUT / "catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"
    )

    files = [path for path in OUTPUT.rglob("*") if path.is_file()]
    oversized = [path for path in files if path.stat().st_size > MAX_ASSET_BYTES]
    if oversized:
        names = ", ".join(str(path.relative_to(OUTPUT)) for path in oversized)
        raise SystemExit(f"Cloudflare's 25 MiB asset limit exceeded by: {names}")

    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "files": len(files),
                "games": len(catalog),
                "largest_asset_bytes": max(path.stat().st_size for path in files),
                "authorized_gogoat_games_included": True,
            }
        )
    )


if __name__ == "__main__":
    main()