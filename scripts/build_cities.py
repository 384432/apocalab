# -*- coding: utf-8 -*-
"""Build src/data/cities.json for the 20 preset metros.

Source: GeoNames cities15000 (CC BY 4.0). Coordinates are the gazetteer point for
each city — NOT an administrative centroid and NOT a population-weighted centroid.
That distinction matters: the 10 km population figure defined in D4 is measured
from this point, so the point has to be stable and citable, not eyeballed.

`reference_population` is GeoNames' city-proper population. It is kept only to
order the list and to sanity-check matches. It is NOT the "population within
10 km" figure and must never be printed on the site as one.
"""
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / ".tmp_handbook" / "cities15000.txt"
OUT = ROOT / "src" / "data" / "cities.json"

COUNTRY_NAME = {
    "US": "United States", "GB": "United Kingdom", "FR": "France", "JP": "Japan",
    "DE": "Germany", "AU": "Australia", "CA": "Canada", "MX": "Mexico",
    "BR": "Brazil", "IN": "India", "ZA": "South Africa",
}

# slug, display name, ISO country, accepted gazetteer names, admin1 code (optional)
TARGETS = [
    ("new-york",      "New York",      "US", ["New York", "New York City"], None),
    ("los-angeles",   "Los Angeles",   "US", ["Los Angeles"], None),
    ("chicago",       "Chicago",       "US", ["Chicago"], None),
    ("houston",       "Houston",       "US", ["Houston"], None),
    ("san-francisco", "San Francisco", "US", ["San Francisco"], None),
    ("washington-dc", "Washington, D.C.", "US", ["Washington", "Washington, D.C."], "DC"),
    ("miami",         "Miami",         "US", ["Miami"], None),
    ("seattle",       "Seattle",       "US", ["Seattle"], None),
    ("boston",        "Boston",        "US", ["Boston"], None),
    ("atlanta",       "Atlanta",       "US", ["Atlanta"], None),
    ("london",        "London",        "GB", ["London"], None),
    ("paris",         "Paris",         "FR", ["Paris"], None),
    ("tokyo",         "Tokyo",         "JP", ["Tokyo"], None),
    ("berlin",        "Berlin",        "DE", ["Berlin"], None),
    ("sydney",        "Sydney",        "AU", ["Sydney"], None),
    ("toronto",       "Toronto",       "CA", ["Toronto"], None),
    ("mexico-city",   "Mexico City",   "MX", ["Mexico City"], None),
    ("sao-paulo",     "São Paulo",     "BR", ["São Paulo", "Sao Paulo"], None),
    ("new-delhi",     "New Delhi",     "IN", ["New Delhi"], None),
    ("johannesburg",  "Johannesburg",  "ZA", ["Johannesburg"], None),
]

with open(SRC, encoding="utf-8") as f:
    rows = list(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE))

by_key = {}
for r in rows:
    if len(r) < 15:
        continue
    gid, name, ascii_name, _alt, lat, lon, _fc, _fcode, cc, _cc2, admin1 = r[:11]
    pop = int(r[14] or 0)
    for nm in {name.lower(), ascii_name.lower()}:
        # most populous match wins for each (name, country, admin1) key
        for key in ((nm, cc, admin1), (nm, cc, None)):
            cur = by_key.get(key)
            if cur is None or pop > cur["reference_population"]:
                by_key[key] = {
                    "geonameid": int(gid), "lat": float(lat), "lon": float(lon),
                    "admin1": admin1, "reference_population": pop,
                    "matched_name": name,
                }

cities, missing = [], []
for slug, display, cc, names, admin1 in TARGETS:
    hit = None
    for nm in names:
        hit = by_key.get((nm.lower(), cc, admin1))
        if hit:
            break
    if not hit:
        missing.append(f"{slug} ({cc})")
        continue
    cities.append({
        "slug": slug,
        "name": display,
        "country": cc,
        "country_name": COUNTRY_NAME[cc],
        "lat": round(hit["lat"], 4),
        "lon": round(hit["lon"], 4),
        "geonameid": hit["geonameid"],
        "gazetteer_name": hit["matched_name"],
        "reference_population": hit["reference_population"],
        "reference_population_note": "GeoNames city-proper population; reference only, never displayed as the 10 km figure",
    })

if missing:
    raise SystemExit(f"unmatched: {missing}")

doc = {
    "source": {
        "name": "GeoNames cities15000",
        "url": "https://download.geonames.org/export/dump/",
        "license": "CC BY 4.0",
        "retrieved": "2026-11-11",
        "note": "Coordinates are the gazetteer point for each city; the 10 km population radius is measured from this point.",
    },
    "count": len(cities),
    "cities": cities,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(f"wrote {OUT}  ({len(cities)} cities)")
print(f"{'slug':<15}{'geonameid':>10}{'lat':>10}{'lon':>10}{'ref pop':>12}  gazetteer")
for c in cities:
    print(f"{c['slug']:<15}{c['geonameid']:>10}{c['lat']:>10.4f}{c['lon']:>10.4f}"
          f"{c['reference_population']:>12,}  {c['gazetteer_name']}")
