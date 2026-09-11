#!/usr/bin/env python3
"""Probe curated remote iframe targets for content and frame policy."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]
CATALOG = SITE_ROOT / "catalog.json"
CURATION = SITE_ROOT / "vendor" / "curated-games.json"
PARENT_ORIGIN = "https://skeezers.org"
USER_AGENT = "Mozilla/5.0 (compatible; SkeezersEmbedProbe/2.0)"
BAD_CONTENT = (
    "domain for sale",
    "buy this domain",
    "domain parking",
    "in progress",
    "window.location='/lander",
    'window.location="/lander',
    "404 not found",
    "page not found",
    "access denied",
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class MetaPolicies(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.policies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("http-equiv", "").lower() == "content-security-policy":
            self.policies.append(values.get("content", ""))


def final_headers(raw: str) -> dict[str, str]:
    blocks = raw.replace("\r\n", "\n").strip().split("\n\n")
    for block in reversed(blocks):
        lines = block.splitlines()
        if lines and lines[0].startswith("HTTP/"):
            headers: dict[str, str] = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()
            return headers
    return {}


def _csp_frame_error(policy: str) -> str | None:
    directive = next(
        (part.strip().lower() for part in policy.split(";") if part.strip().lower().startswith("frame-ancestors")),
        "",
    )
    if not directive:
        return None
    sources = directive.split()[1:]
    allowed = {"*", "https:", PARENT_ORIGIN}
    if not any(source in allowed for source in sources):
        return directive
    return None


def frame_policy_error(headers: dict[str, str]) -> str | None:
    x_frame = headers.get("x-frame-options", "").lower()
    if "deny" in x_frame or "sameorigin" in x_frame:
        return f"X-Frame-Options={x_frame}"
    return _csp_frame_error(headers.get("content-security-policy", ""))


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", unescape(value).lower()).strip()


def content_error(body: bytes, expected_title: str = "") -> str | None:
    if len(body) < 300:
        return f"response body too small ({len(body)} bytes)"
    text = body.decode("utf-8", "replace")
    lower = text.lower()
    marker = next((item for item in BAD_CONTENT if item in lower), None)
    if marker:
        return f"bad content marker: {marker}"
    parser = MetaPolicies()
    parser.feed(text)
    for policy in parser.policies:
        error = _csp_frame_error(policy)
        if error:
            return f"meta CSP: {error}"
    if expected_title:
        match = TITLE_RE.search(text)
        actual = normalized(match.group(1)) if match else ""
        expected = normalized(expected_title)
        if not actual or expected not in actual:
            return f"title mismatch: expected {expected_title!r}, got {actual!r}"
    return None


def identity_error(body: bytes, expected_marker: str) -> str | None:
    if normalized(expected_marker) not in normalized(body.decode("utf-8", "replace")):
        return f"identity marker missing: {expected_marker!r}"
    return None


def remote_identity_error(manifest_item: dict) -> str | None:
    identity_url = manifest_item.get("identity_url")
    if not identity_url:
        return None
    result = subprocess.run(
        [
            "curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            "20",
            "--max-filesize",
            "1000000",
            "--user-agent",
            USER_AGENT,
            identity_url,
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        return result.stderr.decode("utf-8", "replace").strip() or "identity request failed"
    return identity_error(result.stdout, manifest_item["expected_identity_marker"])


def probe(game: dict, manifest_item: dict) -> dict:
    status = "000"
    last_error = "not attempted"
    for attempt in range(2):
        with tempfile.NamedTemporaryFile() as header_file, tempfile.NamedTemporaryFile() as body_file:
            result = subprocess.run(
                [
                    "curl",
                    "--location",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "20",
                    "--max-filesize",
                    "2000000",
                    "--user-agent",
                    USER_AGENT,
                    "--dump-header",
                    header_file.name,
                    "--output",
                    body_file.name,
                    "--write-out",
                    "%{http_code}",
                    game["url"],
                ],
                capture_output=True,
                text=True,
            )
            header_file.seek(0)
            headers = final_headers(header_file.read().decode("utf-8", "replace"))
            body_file.seek(0)
            body = body_file.read()
        status = result.stdout.strip() or "000"
        error = (
            frame_policy_error(headers)
            or content_error(body, manifest_item.get("expected_title", ""))
            or remote_identity_error(manifest_item)
        )
        if result.returncode in {0, 63} and status.startswith("2") and error is None:
            return {"id": game["id"], "status": status, "passed": True}
        last_error = error or result.stderr.strip() or f"HTTP {status}"
        if attempt == 0:
            time.sleep(1)
    return {"id": game["id"], "status": status, "passed": False, "error": last_error}


def main() -> None:
    games = json.loads(CATALOG.read_text())
    curation = json.loads(CURATION.read_text())
    manifest = {item["id"]: item for item in curation["games"]}
    targets = [game for game in games if game.get("embed") and game["source"] in {"Interstellar", "gogoat35"}]
    expected = [item for item in curation["games"] if item["verification"] != "self-contained-local-review"]
    if {game["id"] for game in targets} != {item["id"] for item in expected}:
        raise SystemExit("catalog remote embeds do not match curation manifest")
    with ThreadPoolExecutor(max_workers=12) as executor:
        results = list(executor.map(lambda game: probe(game, manifest[game["id"]]), targets))
    failures = [result for result in results if not result["passed"]]
    print(json.dumps({"result": "PASS" if not failures else "FAIL", "checked": len(results), "failures": failures}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
