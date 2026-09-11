# Skeezers

A clean game launcher built from the repositories authorized for `skeezers.org`.

## Included sources

- `gogoat35/gogoat35.github.io`: 2 self-contained local pages and 27 curated HTTPS game targets
- `UseInterstellar/Interstellar-Assets`: game catalog and icons
- `Radon-Games/Radon-Games`: game metadata and official CDN launch URLs
- `leereilly/games`: playable browser-game links from its curated open-source list
- `nettleweb/nettleweb`: NettleWeb library entry

The original six hand-written placeholder games are not used by the launcher. They are preserved separately at `/home/man/skeezers-original-prototype`.

## Rebuild the catalog

```sh
python3 scripts/extract_gogoat.py
python3 scripts/build_catalog.py
```

The extractor converts imported gogoat Google Sites captures into the standalone game HTML stored inside each capture. It is idempotent, so already-extracted pages are left unchanged.

## Local preview

Use an unused port; do not assume port 8080 is available.

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8765/`.

## Verification

```sh
python3 scripts/build_cloudflare.py
python3 scripts/verify.py
node scripts/test_app.js
node scripts/test_local_games.js
python3 scripts/test_probe.py
python3 scripts/probe_curated.py
```

`vendor/curated-games.json` is fail closed: only listed Interstellar and gogoat IDs with the exact reviewed URL enter the public catalog. New or changed upstream entries remain quarantined until reviewed.

`probe_curated.py` is the network-dependent check for every curated remote Interstellar and gogoat embed. It rejects unreachable responses, parked/error content, unexpected page titles, and frame-blocking HTTP or meta CSP policies. The offline verifier deliberately remains deterministic.

Interstellar and gogoat games open inside the Skeezers player. Remote frames receive scripts, forms, pointer lock, and their own origin, but not popup, download, or modal privileges. Local frames omit `allow-same-origin`. Third-party hosts remain capable of changing availability or refusing embedding; the player keeps an always-visible direct-open fallback.

## Cloudflare Pages deployment

Build the deployable directory with:

```sh
python3 scripts/build_cloudflare.py
```

Configure Cloudflare Pages to use `python3 scripts/build_cloudflare.py` as the build command and `dist-cloudflare` as the output directory.

The public bundle includes the gogoat35 pages under the redistribution permission confirmed by the Skeezers operator.

The included `_headers` file applies a strict content security policy to the launcher while leaving the self-contained game pages free to run their inline game code.

See `THIRD_PARTY.md` for source and license details. The top-level MIT license covers only the original Skeezers launcher and build scripts, not third-party catalogs, artwork, or game code.
