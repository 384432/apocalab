# apocalab.com

Nuclear weapon effects — transcribed, not modelled.

Every number on the site comes from *The Effects of Nuclear Weapons* (Glasstone & Dolan, 3rd ed.,
1977), a public-domain U.S. government publication, and every number carries the figure, equation
and **printed page** it came from. Nothing is fitted, simulated or estimated; the only arithmetic is
the cube-root scaling law the manual itself prints on p. 101.

## Run it

```bash
npm install
npm run build          # -> dist/  (pure static, zero runtime JS except the panel switcher)
npx http-server dist   # or any static server; ?city=tokyo&yield=1000&burst=ground works without one
```

## Gates

Two scripts decide whether the site may ship. Both exit non-zero on failure.

```bash
python scripts/verify_data.py   # 354 checks on the data layer (provenance, scaling, monotonicity)
python scripts/check_site.py    # 264 checks on the built HTML (pages, JS-off, citations, URL state)
```

`check_site.py` needs `dist/` to exist first.

## Pipeline

| script | what it does |
|---|---|
| `scripts/build_effects.py` | the 24 transcribed values → `src/data/effects.json` + `data-ledger.csv` |
| `scripts/verify_data.py` | provenance, unit chain, cube-root recomputation, monotonicity |
| `scripts/build_cities.py` | GeoNames cities15000 → `src/data/cities.json` (20 gazetteer points) |
| `scripts/fetch_geonames.py` | one-time download of the GeoNames dump into the gitignored work dir |
| `scripts/check_site.py` | the build gate: citations, JS-off reading, interpolation labels, URL state |
| `scripts/measure_switch.mjs` | drives headless Chromium to time a yield switch (gate: < 300 ms) |
| `scripts/verify_switch.mjs` | same browser, asserts the numbers actually change |
| `scripts/verify_share_url.mjs` | cold-loads a shared `?city=&yield=&burst=` URL |
| `scripts/verify_js_off.mjs` | disables scripting, asserts the default state is still readable |
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
