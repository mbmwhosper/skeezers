#!/usr/bin/env python3
"""Verify source and Cloudflare bundles for Skeezers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_ROOT = Path(__file__).resolve().parents[1]
DIST_ROOT = SITE_ROOT / "dist-cloudflare"
MAX_CLOUDFLARE_ASSET_BYTES = 25 * 1024 * 1024
REQUIRED_GAME_FIELDS = {
    "id",
    "title",
    "description",
    "category",
    "tags",
    "source",
    "url",
    "image",
    "local",
}


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "poster", "data"):
            if values.get(key):
                self.references.append(str(values[key]))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_catalog(root: Path, expected_total: int, terraria_expected: bool) -> list[dict]:
    games = json.loads((root / "catalog.json").read_text())
    require(len(games) == expected_total, f"{root.name}: expected {expected_total} games")
    require(len({game["id"] for game in games}) == len(games), f"{root.name}: duplicate IDs")
    for game in games:
        require(REQUIRED_GAME_FIELDS <= game.keys(), f"{root.name}: missing fields in {game.get('id')}")
        parsed = urlsplit(game["url"])
        scheme = parsed.scheme.lower()
        if game["local"]:
            require(not scheme and not parsed.netloc, f"local game must use a relative URL: {game['id']}")
            target = (root / unquote(urlsplit(game["url"]).path)).resolve()
            require(target.is_relative_to(root.resolve()), f"path escape in {game['id']}")
            require(target.is_file(), f"missing local game {game['url']}")
        else:
            require(scheme in {"http", "https"}, f"unsafe remote URL in {game['id']}")
        if game["image"]:
            image = urlsplit(game["image"])
            require(image.scheme.lower() in {"", "http", "https"}, f"unsafe image URL in {game['id']}")
        require(not game["description"].startswith("* ["), f"raw markdown description in {game['id']}")
    has_terraria = any(game["id"] == "terraria-wasm" for game in games)
    require(has_terraria is terraria_expected, f"{root.name}: unexpected Terraria state")
    return games


def verify_html_references(root: Path) -> int:
    checked = 0
    for page in root.rglob("*.html"):
        parser = References()
        parser.feed(page.read_text(errors="replace"))
        for reference in parser.references:
            if reference.startswith(("#", "data:", "http:", "https:", "//", "javascript:", "mailto:", "about:", "blob:")):
                continue
            target = (page.parent / unquote(urlsplit(reference).path)).resolve()
            require(target.exists(), f"{page.relative_to(root)}: missing {reference}")
            checked += 1
    return checked


def main() -> None:
    node = shutil.which("node")
    node_checked = node is not None and os.access(node, os.X_OK)
    if node is not None and node_checked:
        subprocess.run([node, "--check", "app.js"], cwd=SITE_ROOT, check=True)
        subprocess.run([node, "--check", "sw.js"], cwd=SITE_ROOT, check=True)
    subprocess.run(["python3", "-m", "py_compile", "scripts/build_catalog.py"], cwd=SITE_ROOT, check=True)
    subprocess.run(["python3", "-m", "py_compile", "scripts/build_cloudflare.py"], cwd=SITE_ROOT, check=True)
    subprocess.run(["python3", "scripts/build_catalog.py"], cwd=SITE_ROOT, check=True)
    subprocess.run(["python3", "scripts/build_cloudflare.py"], cwd=SITE_ROOT, check=True)

    source_games = verify_catalog(SITE_ROOT, expected_total=803, terraria_expected=True)
    dist_games = verify_catalog(DIST_ROOT, expected_total=802, terraria_expected=False)
    require(sum(game["local"] for game in source_games) == 58, "source local-game count")
    require(sum(game["local"] for game in dist_games) == 57, "dist local-game count")

    files = [path for path in DIST_ROOT.rglob("*") if path.is_file()]
    require(bool(files), "Cloudflare bundle is empty")
    largest = max(path.stat().st_size for path in files)
    require(largest <= MAX_CLOUDFLARE_ASSET_BYTES, "Cloudflare asset exceeds 25 MiB")
    require(not (DIST_ROOT / "games" / "terraria").exists(), "Terraria leaked into Cloudflare bundle")
    require((DIST_ROOT / "games" / "gogoat").is_dir(), "authorized gogoat files missing")
    require((DIST_ROOT / "third_party" / "licenses" / "INTERSTELLAR-ASSETS-GPL-3.0.txt").is_file(), "Interstellar license missing")
    require((DIST_ROOT / "third_party" / "licenses" / "RADON-GAMES-AGPL-3.0.txt").is_file(), "Radon license missing")

    headers = (SITE_ROOT / "_headers").read_text()
    global_block = headers.split("\n/\n", 1)[0]
    require("Content-Security-Policy" not in global_block, "global CSP would break inline games")
    require("/index.html\n  Content-Security-Policy:" in headers, "launcher CSP missing")
    launcher = (SITE_ROOT / "index.html").read_text()
    require('sandbox="allow-scripts ' in launcher, "game iframe sandbox missing")

    checked_refs = verify_html_references(SITE_ROOT)
    source_counts = Counter(game["source"] for game in source_games)
    print(
        json.dumps(
            {
                "result": "PASS",
                "source_games": len(source_games),
                "cloudflare_games": len(dist_games),
                "source_counts": dict(sorted(source_counts.items())),
                "html_references_checked": checked_refs,
                "cloudflare_files": len(files),
                "largest_cloudflare_asset_bytes": largest,
                "initial_render_limit": 96,
                "javascript_syntax_checked": node_checked,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
