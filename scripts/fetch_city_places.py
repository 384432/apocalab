# -*- coding: utf-8 -*-
"""Pick 2-3 real, named places near each published city, from the GeoNames dump.

Why the dump and not the API: api.geonames.org needs a personal account (the
demo user is permanently over its credit limit), and a page that carries a
number we cannot reproduce is worse than a page with one fewer sentence. The
country dumps are the same data the API serves, are CC BY 4.0, and stay in the
gitignored work dir.

What a "place" is here: a feature the dump already names, within 10 km of the
GeoNames city point, from the classes that survive a sanity read of the text —
parks (P), water (H), spots and buildings (S), areas (L), hills (T). No roads
(R), no administrative divisions (A), no cells (L with a numeric name), because
those read as machine output rather than as a place in a city.

Selection, per city: prefer one park, one water feature and one landmark when
all three exist; otherwise the three nearest acceptable features at different
distances, so the page can talk about one place inside the 5 psi rings, one
between rings, and one out past the 1 psi ring.

Output: src/data/city-places.json. Re-run with --refresh to re-download a dump.

    python scripts/fetch_city_places.py
"""
import json
import math
import os
import pathlib
import re
import sys
import time
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITIES = ROOT / "src" / "data" / "cities.json"
OUT = ROOT / "src" / "data" / "city-places.json"
WORK = ROOT / ".tmp_handbook" / "geonames"

BASE = "https://download.geonames.org/export/dump/"
# One dump per country we need, rather than allCountries.zip (403 MB).
COUNTRIES = ["US", "GB", "FR", "JP"]

# GeoNames feature classes: which ones can appear on a city page.
OK_CLASS = {"P", "H", "S", "L", "T"}
# Codes that read as a place a person would name. Everything else in those
# classes is machine inventory (hotels, post offices, churches, bus stops) and
# has no business in a sentence about a city.
OK_CODE = {
    "PRK": "park", "GDN": "garden", "SQR": "square", "RES": "reserve",
    "PPLX": "district", "PPL": "district", "PPLL": "district",
    "LK": "lake", "PND": "lake", "RSV": "reservoir", "STM": "river",
    "CNL": "canal", "CHN": "river", "BAY": "bay", "SPNG": "spring",
    "ISL": "island", "HLL": "hill", "MT": "hill", "FRST": "wood",
    "BCH": "beach", "AREA": "area", "RGN": "area",
}
# Substrings that turn a name into a category: they describe a database entry,
# not a landmark.
BAD_NAME = re.compile(
    r"historical|hotel|motel|inn\b|post office|bureau de poste|station|"
    r"cemetery|parking|garage|mall\b|plaza hotel|school|library|university|"
    r"apartment|housing|projects|houses\b|tower\b|building",
    re.I,
)

MIN_KM, MAX_KM = 0.4, 10.0
PER_CITY = 3

# For the five published cities the places are chosen by hand and then verified
# against the dump by name: an automatic "nearest park" pick produces entries
# like a post office branch, which is a real record and a useless sentence.
# Every name below was found in the country dump at the distance the page
# prints; the script re-finds it, and if a name is not there it falls back to
# the automatic pick instead of inventing one.
CURATED = {
    "new-york": ["Brooklyn Heights", "Hudson River", "Central Park"],
    "los-angeles": ["Little Tokyo", "Echo Park", "Griffith Park"],
    "london": ["Covent Garden", "The Serpentine", "Regent's Park"],
    "paris": ["Jardin du Luxembourg", "Champs-Elysees", "Bois de Boulogne"],
    "tokyo": ["Kabukicho", "Shinjuku Gyoen", "Sumida Gawa"],
}
# A curated place may sit just outside the automatic 10 km window; the catchment
# is 25 km, so anything inside it is still counted from the same request.
CURATED_MAX_KM = 14.0

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def download(code):
    """Country dump, cached in .tmp_handbook/geonames/.

    GEONAMES_PROXY=https://... is honoured because download.geonames.org is
    throttled to a few kB/s on a direct connection from this machine while the
    local proxy gets the same file at line speed. This affects fetching only:
    the file is a static dump, and the checksum is the size.
    """
    global opener
    proxy = os.environ.get("GEONAMES_PROXY")
    if proxy:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    WORK.mkdir(parents=True, exist_ok=True)
    txt = WORK / f"{code}.txt"
    if txt.exists() and txt.stat().st_size > 100_000:
        print(f"  {code}: cached {txt.stat().st_size/1048576:.1f} MB")
        return txt
    z = WORK / f"{code}.zip"
    if not z.exists() or z.stat().st_size < 100_000:
        req = urllib.request.Request(BASE + f"{code}.zip",
                                     headers={"User-Agent": "apocalab-build/1.0"})
        t0 = time.time()
        with opener.open(req, timeout=600) as r, open(z, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        print(f"  {code}: downloaded {z.stat().st_size/1048576:.1f} MB "
              f"in {time.time()-t0:.0f}s")
    with zipfile.ZipFile(z) as zf:
        zf.extractall(WORK)
    return txt


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def usable(name, fclass, fcode):
    if fclass not in OK_CLASS:
        return False
    if fcode not in OK_CODE:
        return False
    if not name or not name.strip():
        return False
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'’()-]{2,34}", name):
        return False
    if re.search(r"\d", name) or BAD_NAME.search(name):
        return False
    if name.lower() in {"unknown", "unnamed", "locality"}:
        return False
    return True


def kind(fclass, fcode):
    return OK_CODE.get(fcode, "place")


def cardinal(lat1, lon1, lat2, lon2):
    """Compass direction of the place from the city point, 8 points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    b = (math.degrees(math.atan2(y, x)) + 360) % 360
    return ["north", "north-east", "east", "south-east",
            "south", "south-west", "west", "north-west"][int((b + 22.5) % 360 // 45)]


def candidates(city, rows):
    lat, lon = float(city["lat"]), float(city["lon"])
    out = []
    for row in rows:
        # geonameid, name, asciiname, alternatenames, lat, lon, fclass, fcode,
        # country, cc2, admin1..., population, elevation, dem, tz, modified
        try:
            gid, name, ascii_name, lat_s, lon_s = row[0], row[1], row[2], row[4], row[5]
            fclass, fcode = row[6], row[7]
            pop = int(row[14] or 0)
        except (IndexError, ValueError):
            continue
        if gid == str(city["geonameid"]):
            continue
        if not usable(ascii_name, fclass, fcode):
            continue
        d = haversine_km(lat, lon, float(lat_s), float(lon_s))
        if not (MIN_KM <= d <= MAX_KM):
            continue
        out.append({
            "geonameid": int(gid),
            "name": ascii_name,
            "kind": kind(fclass, fcode),
            "fclass": fclass,
            "fcode": fcode,
            "lat": round(float(lat_s), 5),
            "lon": round(float(lon_s), 5),
            "distance_km": round(d, 2),
            "bearing": cardinal(lat, lon, float(lat_s), float(lon_s)),
            "population": pop,
        })
    return out


def curated(slug, rows, city):
    """Look up the hand-picked names; return [] if any of them is missing."""
    names = CURATED.get(slug)
    if not names:
        return []
    lat, lon = float(city["lat"]), float(city["lon"])
    found = []
    for want in names:
        best = None
        for row in rows:
            try:
                ascii_name, lat_s, lon_s = row[2], row[4], row[5]
                fclass, fcode = row[6], row[7]
                gid = row[0]
            except IndexError:
                continue
            if ascii_name.lower() != want.lower():
                continue
            d = haversine_km(lat, lon, float(lat_s), float(lon_s))
            if d > CURATED_MAX_KM:
                continue
            # Prefer the entry that is a mapped feature (park, water) over the
            # same name used for a neighbourhood polygon.
            rank = 0 if fclass in {"L", "H"} else 1
            if best is None or (rank, d) < (best[0], best[1]):
                best = (rank, d, {
                    "geonameid": int(gid),
                    "name": ascii_name,
                    "kind": kind(fclass, fcode),
                    "fclass": fclass,
                    "fcode": fcode,
                    "lat": round(float(lat_s), 5),
                    "lon": round(float(lon_s), 5),
                    "distance_km": round(d, 2),
                    "bearing": cardinal(lat, lon, float(lat_s), float(lon_s)),
                    "curated": True,
                })
        if best is None:
            print(f"  !! curated place not found: {want} — falling back to automatic pick")
            return []
        found.append(best[2])
    return found


def pick(cands):
    """One park, one water feature, one district where they exist; then fill.

    The point is that each page carries three sentences that could only be
    written about that city. Three parks would satisfy "three places" and still
    be a template, so the kinds are drawn from different groups.
    """
    groups = {
        "park": [c for c in cands if c["fcode"] in {"PRK", "GDN", "SQR", "FRST", "RES"}],
        "water": [c for c in cands if c["fclass"] == "H"],
        "district": [c for c in cands if c["fcode"] in {"PPLX", "PPL", "PPLL", "AREA", "RGN"}],
        "other": cands,
    }
    chosen, seen = [], set()
    for keys in (("park",), ("water",), ("district",), ("other",)):
        pool = [c for k in keys for c in groups[k]]
        pool.sort(key=lambda c: (abs(c["distance_km"] - 3.0), c["distance_km"]))
        for c in pool:
            if c["geonameid"] in seen:
                continue
            if any(abs(c["distance_km"] - x["distance_km"]) < 0.6 for x in chosen):
                continue
            chosen.append(c)
            seen.add(c["geonameid"])
            break
        if len(chosen) == PER_CITY:
            break
    return sorted(chosen[:PER_CITY], key=lambda c: c["distance_km"])


def main():
    refresh = "--refresh" in sys.argv
    if refresh:
        for f in list(WORK.glob("*.zip")) + list(WORK.glob("*.txt")):
            f.unlink()
    cities = json.loads(CITIES.read_text(encoding="utf-8"))["cities"]
    out = {}
    for code in COUNTRIES:
        print(f"{code}")
        txt = download(code)
        rows = txt.read_text(encoding="utf-8", errors="replace").splitlines()
        rows = [r.split("\t") for r in rows]
        print(f"  {len(rows)} rows")
        for city in [c for c in cities if c.get("country") == code]:
            picked = curated(city["slug"], rows, city)
            if not picked:
                cands = candidates(city, rows)
                picked = pick(cands)
            if len(picked) < 2:
                raise SystemExit(f"{city['slug']}: only {len(picked)} places, refusing to write a thin page")
            out[city["slug"]] = picked
            print(f"  {city['slug']}: " + ", ".join(
                f"{p['name']} ({p['kind']}, {p['distance_km']} km {p['bearing']})" for p in picked))
    OUT.write_text(json.dumps({"places": out}, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(out)} cities)")


if __name__ == "__main__":
    main()
