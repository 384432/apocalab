# apocalab.com

Nuclear weapon effects — transcribed, not modelled.

Every number on the site comes from *The Effects of Nuclear Weapons* (Glasstone & Dolan, 3rd ed.,
1977), a public-domain U.S. government publication, and every number carries the figure, equation
and **printed page** it came from. Nothing is fitted, simulated or estimated; the only arithmetic is
the cube-root scaling law the manual itself prints on p. 101.

## Run it

```bash
npm install
npm run build          # -> dist/  (pure static; runtime JS only in the panel switcher and on the map page)
npx http-server dist   # or any static server; ?city=tokyo&yield=1000&burst=ground works without one
```

## Gates

These scripts decide whether the site may ship. All exit non-zero on failure. The Python gates
print their own assertion counts — the number is never written down by hand, here or on a page.

```bash
python scripts/verify_calibration.py # 600 dpi figure calibration gate; must pass before any read-out (fails with exit 1 on any >1% deviation; --p115-y-grid-ft 200 reproduces the old 2.5x axis error and must abort)
python scripts/verify_data.py       # data layer (provenance, scaling, monotonicity)
python scripts/check_site.py        # built HTML (pages, JS-off, citations, canonical, sitemap, internal links, noindex mode, query-page rules); also matches the assertion count on /methodology/ against verify_data's real PASS count
python scripts/check_urls.py        # every sitemap URL answers 200 over real HTTP
python scripts/verify_pop_tiles.py  # tiles: sizes, decoded total, bin error, browser/script agreement
python scripts/read_neighbor_noses.py # re-reads the 10 / 15 / 20 / 30 psi noses behind the sign-off evidence
node   scripts/verify_map.mjs       #  browser: tiles, blocked tiles, shared URL, JS off, 390 px
node   scripts/verify_click.mjs     #  browser: click -> six rings + circle population, a-g
node   scripts/verify_weapons.mjs   #  browser: fifteen options, tabulated vs scaled rows, anchor, share URL, 0-f
```

The two figure-reading scripts need numpy + Pillow. The default isolated `python` does not ship
them, so both scripts bootstrap through `scripts/_imgdep.py`: if the packages are missing it
re-runs the same script under an interpreter that has them (set `APOCA_IMG_PY` to override),
passing stdout/stderr and the exit code straight through; a missing exit 1 from the gate still
arrives as exit 1. If no capable interpreter exists it exits 2 with the install commands, so an
environment problem (2) can never be mistaken for a failed calibration (1).

`check_site.py` and `check_urls.py` need `dist/` to exist first (`npm run build`). `check_urls.py`
starts its own loopback server, so it needs nothing running; `verify_map.mjs`, `verify_click.mjs`
and `verify_weapons.mjs` drive headless Chromium on `--remote-debugging-port=9333` against the
built site on `:4322`. Start that browser with an explicit `--window-size` (1400,900): the ring
pixel assertions are calibrated to a laid-out frame, and the default 800×600 window is too small
for them.

`check_site.py` also checks *which artifact* it is looking at, because the indexing rule differs by
deployment:

```bash
CF_PAGES_BRANCH=preview npm run build && python scripts/check_site.py --expect preview
CF_PAGES_BRANCH=main    npm run build && python scripts/check_site.py --expect main
```

`--expect` names the **branch** the artifact came from; what that branch should produce is read from
`SITE_LIVE` in `src/lib/site.ts`. While `SITE_LIVE = false`, both branches must produce `staged`
(noindex) and the flag makes no difference. With `SITE_LIVE = true`, `main` must produce a build with
no `noindex` anywhere and a preview must carry the header. Feeding a production artifact to
`--expect preview` fails on purpose.

Once deployed, the same two questions are asked over real HTTP:

```bash
# before go-live (SITE_LIVE = false): both environments were noindex
python scripts/check_online.py https://apocalab.pages.dev          --expect noindex
python scripts/check_online.py https://preview.apocalab.pages.dev  --expect noindex

# since 2026-11-16 (SITE_LIVE = true, domain live): production is indexable
python scripts/check_online.py https://apocalab.com                --expect indexed
python scripts/check_online.py https://apocalab.pages.dev          --expect indexed
python scripts/check_online.py https://preview.apocalab.pages.dev  --expect noindex
```

It checks the header (not just the file), the canonical on each page, `robots.txt`, the sitemap and
the `.geojson` MIME type, with proxies bypassed.

## Deploy — Cloudflare Pages, static, no adapter

This is a hard constraint, not a preference: the whole site rests on "readable with scripting off,
no server state, the CDN serves HTML". An adapter would make Pages run Functions and take all
three away.

| Setting | Value |
|---|---|
| Project | `apocalab` — Git-connected to `384432/apocalab` |
| Build command | `npm run build` |
| Output directory | `dist` |
| Node | 20+ |
| Adapter | none — `astro.config.mjs` stays `output: 'static'` |
| Production | `https://apocalab.pages.dev`, branch `main` |
| Preview | `https://preview.apocalab.pages.dev` (branch `preview`) and one URL per deployment |

`wrangler.toml` carries `pages_build_output_dir = "./dist"` so a manual
`wrangler pages deploy` cannot upload the repository root.

`dist/_headers` is **generated at the end of every build** by `scripts/gen_headers.mjs`, not copied
from `public/`. Whether the deploy may be indexed depends on the environment, and that is only known
while building:

| `SITE_LIVE` | `CF_PAGES_BRANCH` | mode | `_headers` |
|---|---|---|---|
| `false` | `main` | **staged** | `X-Robots-Tag: noindex` on `/*` |
| `false` | anything else / unset | staged | same |
| `true` | `main` | production | no `X-Robots-Tag` at all — `robots.txt` and `sitemap.xml` invite crawlers in |
| `true` | anything else / unset | preview | `X-Robots-Tag: noindex` on `/*` |

**`SITE_LIVE` is `true` as of 2026-11-16 06:05 CST (22:05 UTC).** It was `false` before that, and the
reason is worth keeping: every page carries `rel=canonical` pointing at `apocalab.com`; while that
domain did not answer, an indexable `*.pages.dev` copy would have been what Google indexed, and the
day the domain went live the same pages would have existed at two hostnames. So production was
noindexed too and the sitemap was generated but not submitted. With the domain live and both hosts
serving the same build, `apocalab.pages.dev` loses the header along with the apex and is consolidated
by `rel=canonical` — deliberately not given a `noindex` of its own, because Pages `_headers` match on
path only, so a blanket rule for it would also blank the main domain.

Going live is one boolean, in `src/lib/site.ts`:

```ts
export const SITE_LIVE = true;
```

`gen_headers.mjs` reads that value out of the file (it does not keep a copy) and refuses to build if
the declaration is missing or appears twice. `check_site.py` reads the same value to decide what the
artifact should look like, so flipping the flag cannot leave the gate behind. `SITE_ENV=production`
still forces the `main` rule when you want to reproduce that artifact locally.
The gate asserts both directions: a production artifact may not contain the word `noindex` in
`_headers` **or** in any HTML file, and a preview artifact must carry the header. It also fails if a
static `public/_headers` ever comes back — a leftover copy would win or lose depending on copy order,
which is worse than having none.

The same generated file pins the MIME type of `ne_110m_land.geojson`, which Pages would otherwise
serve as `application/octet-stream`.

## Internal links

Four core pages, one closed loop. Anchor text is fixed (changing it is a contract change, and
`check_site.py` §17 fails the build):

| Destination | Anchor text |
|---|---|
| `/blast-radius/` | `nuclear bomb blast radius` |
| `/nuclear-bomb-map/` | `nuclear bomb map` |
| `/` | `nuke simulator` |
| `/methodology/` | `where these numbers come from` |

Every core page links to the other three from inside body paragraphs — not from the footer, not only
from the nav — with no `rel="nofollow"` and no JS routing.

City pages (`/nuclear-bomb-map/{city}/`) are leaves: each one links back to at least three core
pages, always including `/blast-radius/` and `/nuclear-bomb-map/`, with the same fixed anchor text.
They do not join the loop, so adding cities cannot break it.

## Pipeline

| script | what it does |
|---|---|
| `scripts/build_effects.py` | the 30 transcribed values → `src/data/effects.json` + `data-ledger.csv` |
| `scripts/verify_data.py` | provenance, unit chain, cube-root recomputation, monotonicity |
| `scripts/build_cities.py` | GeoNames cities15000 → `src/data/cities.json` (20 gazetteer points) |
| `scripts/build_city_pop.py` | WorldPop API → `src/data/city-pop.json`: people inside every radius the site draws, per city (cached; `--refresh` to refetch) |
| `scripts/fetch_worldpop_1km.py` | downloads the WorldPop 2020 1 km country rasters into the gitignored work dir (249 directories, ~690 MB). 3 workers: 10 makes the host answer 503. The host ignores `Range` (200, never 206), so a stalled file restarts — the long read timeout is the only lever |
| `scripts/build_pop_tiles.py` | aggregates those rasters to 1/24° cells → `public/data/pop/*.bin` (648 tiles of 57,600 bytes) + `src/data/pop-meta.json` (the only description of the encoding) |
| `scripts/build_weapon_radii.py` | the twelve weapon presets → `src/data/weapon-radii.json` (six radii per preset) and `weapon-ledger.csv` (one row per preset × effect × burst, carrying `source_url` and — where the cited page prints a range rather than a point value — `yield_note`). Three paths: fireball from Eq. (2.127.1)/(2.127.2), the three overpressure rings by the cube-root law off the 100 kt table, the two thermal rings read off Fig. 7.42 at each preset's own column. Self-tests the 18 known contour points and the 100 kt anchor. The preset list itself — `src/data/weapons.json`, carrying the yield, the country, the year, one sentence, the source URL and the source's own wording — is hand-maintained and is the input, not the output |
| `scripts/verify_pop_tiles.py` | tile gate: file sizes, decoded total, worst-case bin error, and script-vs-browser agreement at the coordinates the click gate landed on |
| `scripts/fetch_geonames.py` | one-time download of the GeoNames dump into the gitignored work dir |
| `scripts/check_site.py` | the build gate: citations, JS-off reading, interpolation labels, URL state, canonical, sitemap, `_headers` mode, internal-link loop, map-page prose, promise ledger |
| `scripts/gen_headers.mjs` | writes `dist/_headers` from `SITE_LIVE` + `CF_PAGES_BRANCH` (staged/preview: `noindex`; production: no robots header) |
| `scripts/check_online.py` | the same two questions over real HTTP: header, canonical, robots, sitemap, geojson MIME |
| `scripts/check_urls.py` | serves `dist/` on a loopback port and fetches every sitemap URL: 200, canonical round-trip, 404 sanity |
| `scripts/measure_switch.mjs` | drives headless Chromium to time a yield switch (gate: < 300 ms) |
| `scripts/verify_switch.mjs` | same browser, asserts the numbers actually change |
| `scripts/verify_share_url.mjs` | cold-loads a shared `?city=&yield=&burst=` URL |
| `scripts/verify_js_off.mjs` | disables scripting, asserts the default state is still readable |
| `scripts/verify_layout.mjs` | overflow and ring geometry at 390 and 1265 px |
| `scripts/verify_map.mjs` | four map states (tiles / tiles blocked / shared URL / scripting off) plus a 390 px pass |
| `scripts/verify_click.mjs` | click gate a–g: six rings at any point, snapped city figures, ocean and desert, unchanged URL, ≤4 tile requests, forced 404, touch tap |
| `scripts/verify_weapons.mjs` | preset gate 0–f: the default page is New York at a fitted zoom (not a clicked point at 0°N 0°E), fifteen options, six numbers for each, tabulated rows to the digit, scaled rows against `weapon-radii.json`, the two class lines swapping, the 100 kt anchor, JS off, a shared `?w=&b=&lat=&lon=` URL, unchanged canonical, unchanged sitemap |
| `scripts/build_review_page.py` | one page with the ledger and the marked-up source figures |
| `scripts/patch_plan_v1*.py` | the plan revisions, one script per version, every edit asserted |

The browser scripts need a Chromium on `--remote-debugging-port=9333` and the built site on
`:4322`; they are development instruments, not part of the build.

## Conventions

- **A number that cannot be traced to a figure, equation and printed page does not go on the site.**
- No word from the banned list (`demo`, `prototype`, `education demo`, `simulation model`,
  `our estimate`) anywhere in rendered text. `check_site.py` fails the build if one appears.
- Exactly one line of disclaimer, at the bottom of every page, never in the hero.
- The site must stay readable with scripting off. The homepage's default state is server-rendered;
  the control bar only exists once the inline script has run.
- Titles never promise a feature the page does not have.

## Where the manual stops

Two things are stated on the page rather than hidden: the 1 Mt burst heights (6,110 ft / 10,174 ft /
15,750 ft) sit outside Fig. 3.73's stated 5,000 ft homogeneous-atmosphere assumption, and the
contour labels on Fig. 7.42 had to be identified from the manual's prose because the scan has no
text layer. Both are in `/methodology/`.

The 20 psi contour is printed on Fig. 3.73b (p. 113), not on Fig. 3.73c, whose labels stop at
10 psi. That row cites its own panel, is calibrated against the manual's p. 112 worked example
(50 psi at 400 ft ground distance, read here at 410 ft, +2.5%) and cross-checked against the
100 psi contour on Fig. 3.73a (<1% apart). Its six values carry no sign-off yet and are starred
until that re-read happens.
