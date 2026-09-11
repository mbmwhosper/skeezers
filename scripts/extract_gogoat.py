#!/usr/bin/env python3
"""Extract runnable gogoat game documents from captured Google Sites wrappers."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE_ROOT = Path(__file__).resolve().parents[1]
GOGOAT_ROOT = SITE_ROOT / "games" / "gogoat"
CURATION_PATH = SITE_ROOT / "vendor" / "curated-games.json"


class EmbeddedCodeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.documents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "data-code" and value:
                self.documents.append(value)


def standalone_document(fragment: str) -> str:
    fragment = fragment.strip()
    if "<html" in fragment.lower():
        document = fragment
    else:
        document = (
            "<!doctype html>\n"
            '<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>html,body{width:100%;height:100%;margin:0;overflow:hidden}</style>'
            f"</head><body>{fragment}</body></html>\n"
        )
    return "\n".join(line.rstrip() for line in document.splitlines()) + "\n"


def main() -> None:
    extracted = 0
    already_standalone = 0
    normalized = 0
    curation = json.loads(CURATION_PATH.read_text())
    local_pages = {
        Path(unquote(urlsplit(item["url"]).path)).name
        for item in curation["games"]
        if item["source"] == "gogoat35" and item["verification"] == "self-contained-local-review"
    }
    for page_name in sorted(local_pages):
        page = GOGOAT_ROOT / page_name
        source = page.read_text(errors="replace")
        if "_docs_flag_initialData" not in source:
            already_standalone += 1
            clean = standalone_document(source)
            if clean != source:
                page.write_text(clean)
                normalized += 1
            continue
        parser = EmbeddedCodeParser()
        parser.feed(source)
        if len(parser.documents) != 1:
            raise SystemExit(f"Expected one embedded document in {page.name}, found {len(parser.documents)}")
        page.write_text(standalone_document(parser.documents[0]))
        extracted += 1
    print(
        {
            "extracted": extracted,
            "already_standalone": already_standalone,
            "normalized": normalized,
        }
    )


if __name__ == "__main__":
    main()
