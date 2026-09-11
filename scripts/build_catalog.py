#!/usr/bin/env python3
"""Build Skeezers' catalog from the authorized source repositories."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

SITE_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = SITE_ROOT / "vendor"
CURATION_PATH = VENDOR_ROOT / "curated-games.json"


def slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "game"


def gogoat_games(approved: dict[str, dict]) -> list[dict]:
    root = SITE_ROOT / "games" / "gogoat"
    ignored = {"index.html", "Home.html"}
    games = []
    for page in sorted(root.glob("*.html"), key=lambda item: item.name.lower()):
        if page.name in ignored:
            continue
        title = page.stem.strip()
        game_id = f"gogoat-{slug(title)}"
        item = approved.get(game_id)
        if item is None:
            continue
        local = item["verification"] == "self-contained-local-review"
        game = {
            "id": game_id,
            "title": title,
            "description": (
                "Self-contained game page recovered from gogoat35."
                if local
                else "Curated game originally listed by gogoat35."
            ),
            "category": "Games",
            "tags": [],
            "source": "gogoat35",
            "url": f"games/gogoat/{quote(page.name)}" if local else item["url"],
            "image": "",
            "local": local,
        }
        if not local:
            game["embed"] = True
        games.append(game)
    return games


def interstellar_games() -> list[dict]:
    source = VENDOR_ROOT / "interstellar-games.json"
    games = []
    for index, item in enumerate(json.loads(source.read_text())):
        title = str(item.get("name", "")).strip()
        target = str(item.get("link", "")).strip()
        if not title or not target or title.startswith("!"):
            continue
        if target.startswith("/"):
            target = "https://gointerstellar.app" + target
        image = str(item.get("image") or "").strip()
        if image.lower() in {"none", "null", "/icons/none", "/icons/null"}:
            image = ""
        if image.startswith("/icons/"):
            image = "assets/interstellar/" + image.rsplit("/", 1)[-1]
        categories = [str(x) for x in item.get("categories", []) if str(x).lower() != "all"]
        games.append(
            {
                "id": f"interstellar-{slug(title)}-{index}",
                "title": title,
                "description": "Game listed by the Interstellar game catalog.",
                "category": categories[0] if categories else "Games",
                "tags": categories[1:],
                "source": "Interstellar",
                "url": target,
                "image": image,
                "local": False,
                "embed": True,
            }
        )
    return games


def radon_games() -> list[dict]:
    source = VENDOR_ROOT / "radon-games.json"
    games = []
    for item in json.loads(source.read_text()):
        game_type = item["type"]
        target = f"https://cdn.radon.games/{game_type}.html?id={quote(item['id'])}"
        if game_type == "emulator":
            target += f"&emu={quote(item['emulator'])}"
        games.append(
            {
                "id": f"radon-{item['id']}",
                "title": item["title"],
                "description": item.get("description", ""),
                "category": game_type.capitalize(),
                "tags": item.get("tags", []),
                "source": "Radon Games",
                "url": target,
                "image": f"https://cdn.radon.games/images/{quote(item['id'])}.png?h=180&w=320",
                "local": False,
            }
        )
    return games


def leereilly_games() -> list[dict]:
    text = (VENDOR_ROOT / "leereilly-games.md").read_text()
    browser_games = text.split("# Browser-Based", 1)[1].split("# Native", 1)[0]
    category = "Browser"
    games = []
    for line in browser_games.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            category = heading.group(1).strip()
            continue
        title_match = re.match(r"^\* \[([^]]+)]\((https?://[^)]+)\)", line)
        play_match = re.search(
            r"\[Play it now!?\]\((https?://[^)]+)\)", line, re.IGNORECASE
        )
        if not title_match or not play_match:
            continue
        title, repository = title_match.groups()
        remainder = line[title_match.end() :]
        description = re.split(r"\[Play it now!?\]", remainder, maxsplit=1, flags=re.IGNORECASE)[0]
        description = re.sub(r"^\s*[-–—]\s*", "", description).strip()
        games.append(
            {
                "id": f"games-on-github-{slug(title)}-{len(games)}",
                "title": title,
                "description": description,
                "category": category,
                "tags": ["open source"],
                "source": "Games on GitHub",
                "url": play_match.group(1),
                "image": "",
                "local": False,
                "repository": repository,
            }
        )
    return games


def special_games() -> list[dict]:
    return [
        {
            "id": "nettleweb-library",
            "title": "NettleWeb Game Library",
            "description": "Open the game library supplied by the NettleWeb project.",
            "category": "Library",
            "tags": ["html5", "flash", "dos"],
            "source": "NettleWeb",
            "url": "https://nettleweb.com/",
            "image": "",
            "local": False,
        },
    ]


def main() -> None:
    curation = json.loads(CURATION_PATH.read_text())
    approved = {item["id"]: item for item in curation["games"]}
    candidates = gogoat_games(approved) + interstellar_games()
    curated = []
    for game in candidates:
        item = approved.get(game["id"])
        if item is None:
            continue
        if item["source"] != game["source"] or item["url"] != game["url"]:
            raise ValueError(f"curated game drifted: {game['id']}")
        curated.append(game)
    missing = sorted(set(approved) - {game["id"] for game in curated})
    if missing:
        raise ValueError(f"curated games missing from sources: {missing}")
    games = special_games() + curated + radon_games() + leereilly_games()
    output = SITE_ROOT / "catalog.json"
    output.write_text(json.dumps(games, indent=2, ensure_ascii=False) + "\n")
    counts: dict[str, int] = {}
    for game in games:
        counts[game["source"]] = counts.get(game["source"], 0) + 1
    print(json.dumps({"total": len(games), "sources": counts, "output": str(output)}))


if __name__ == "__main__":
    main()
