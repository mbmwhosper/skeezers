# Skeezers

A clean game launcher built from the repositories authorized for `skeezers.org`.

## Included sources

- `gogoat35/gogoat35.github.io`: locally copied game pages
- `MercuryWorkshop/terraria-wasm`: locally hosted release build
- `UseInterstellar/Interstellar-Assets`: game catalog and icons
- `Radon-Games/Radon-Games`: game metadata and official CDN launch URLs
- `leereilly/games`: playable browser-game links from its curated open-source list
- `nettleweb/nettleweb`: NettleWeb library entry

The original six hand-written placeholder games are not used by the launcher. They are preserved separately at `/home/man/skeezers-original-prototype`.

## Rebuild the catalog

```sh
python3 scripts/build_catalog.py
```

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
```

The repository-backed pages in the local development copy open inside the Skeezers player. Catalog entries that point to third-party sites open in a new tab and remain dependent on those sites being online.

## Cloudflare Pages deployment

Build the deployable directory with:

```sh
python3 scripts/build_cloudflare.py
```

Configure Cloudflare Pages to use `python3 scripts/build_cloudflare.py` as the build command and `dist-cloudflare` as the output directory.

The public bundle includes the gogoat35 pages under the redistribution permission confirmed by the Skeezers operator. Terraria's WebAssembly runtime is about 95 MiB, above Cloudflare Pages' 25 MiB per-asset limit, so Terraria remains available only in the local development copy. Its exclusion is technical rather than a permissions assumption.

The included `_headers` file applies a strict content security policy to the launcher while leaving the self-contained game pages free to run their inline game code.

See `THIRD_PARTY.md` for source and license details. The top-level MIT license covers only the original Skeezers launcher and build scripts, not third-party catalogs, artwork, or game code.
