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

Four scripts decide whether the site may ship. All exit non-zero on failure.

```bash
python scripts/verify_data.py   # 354 checks on the data layer (provenance, scaling, monotonicity)
python scripts/check_site.py    # 674 checks on the built HTML (pages, JS-off, citations, canonical, sitemap, internal links, noindex mode, query-page rules)
python scripts/check_urls.py    #  30 checks over real HTTP: every sitemap URL answers 200
node   scripts/verify_map.mjs   #  browser: tiles, blocked tiles, shared URL, JS off, 390 px
```

`check_site.py` and `check_urls.py` need `dist/` to exist first (`npm run build`). `check_urls.py`
starts its own loopback server, so it needs nothing running; `verify_map.mjs` drives headless
Chromium on `--remote-debugging-port=9333` against the built site on `:4322`.

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
# while SITE_LIVE = false, both environments must be noindex
python scripts/check_online.py https://apocalab.pages.dev          --expect noindex
python scripts/check_online.py https://preview.apocalab.pages.dev  --expect noindex

# after the domain points here and SITE_LIVE = true
python scripts/check_online.py https://apocalab.pages.dev          --expect indexed
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

**`SITE_LIVE` is `false` right now.** Every page carries `rel=canonical` pointing at
`apocalab.com`; until that domain answers, an indexable `*.pages.dev` copy would be what Google
indexes, and the day the domain goes live the same pages would exist at two hostnames. So production
is noindexed too, and the sitemap is generated but not submitted.

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
| `scripts/build_effects.py` | the 24 transcribed values → `src/data/effects.json` + `data-ledger.csv` |
| `scripts/verify_data.py` | provenance, unit chain, cube-root recomputation, monotonicity |
| `scripts/build_cities.py` | GeoNames cities15000 → `src/data/cities.json` (20 gazetteer points) |
| `scripts/build_city_pop.py` | WorldPop API → `src/data/city-pop.json`: people inside every radius the site draws, per city (cached; `--refresh` to refetch) |
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

Two things are stated on the page rather than hidden: the 1 Mt burst heights (10,174 ft / 15,750 ft)
sit outside Fig. 3.73c's stated 5,000 ft homogeneous-atmosphere assumption, and the contour labels on
Fig. 7.42 had to be identified from the manual's prose because the scan has no text layer. Both are
in `/methodology/`.
