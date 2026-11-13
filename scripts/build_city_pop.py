# -*- coding: utf-8 -*-
"""Population inside each city's effect rings, from the WorldPop API.

Why an API and not a downloaded raster: WorldPop's own service does the
area-of-a-geodesic-circle integration on their gridded surface, so the number
is reproducible by anyone with the same circle — no resampling choices of mine
get baked in, and the dataset name comes back in the response rather than being
typed by hand.

What it asks for: /catchment calls per city, every radius the site uses, so the
rings are nested by construction (cumulative at each radius). The city figure is
the same call's cumulative at 10 km, not a second query through /population: two
different integrations of "10 km" differ by ~0.4% (a polygon approximates the
circle from outside or inside), and a page that shows both numbers would invite
exactly that comparison. One engine, one disc, one set of numbers.

The 10 km figure is still never derived from the effect rings (D4): it is a
separate radius in the same request, not a sum.

Output: src/data/city-pop.json, cached. Re-run with --refresh to re-fetch.

    python scripts/build_city_pop.py            # fetch what is missing
    python scripts/build_city_pop.py --refresh  # re-fetch every city

A failed call is fatal: a missing number must break the build, not turn into a
silently smaller page.
"""
import json
import math
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITIES = ROOT / "src" / "data" / "cities.json"
EFFECTS = ROOT / "src" / "data" / "effects.json"
OUT = ROOT / "src" / "data" / "city-pop.json"

API = "https://api.worldpop.org/v3"
YEAR = 2020
CITY_RADIUS_KM = 10.0
# One catchment per city, wide enough to hold the largest ring the site draws:
# 1 Mt 1 psi at 21.40 km. 10 km would cut that ring off, and a page that showed
# a "ring" count from a 10 km disc would be reporting the disc, not the ring.
# Every radius below is a cumulative inside this one catchment, so no ring is
# ever assembled by subtracting another one.
CATCH_RADIUS_KM = 25.0
RETRIES = 4

# The proxy on this machine would otherwise be asked to reach api.worldpop.org,
# and the response would be a proxy error page rather than JSON.
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def radii_from_effects():
    """Every radius the site draws, plus the catchment that has to contain them."""
    data = json.loads(EFFECTS.read_text(encoding="utf-8"))
    out = set()
    max_ring = 0.0
    for e in data["entries"]:
        if e["burst"] != "air":
            continue
        r = round(float(e["radius_km"]), 3)
        out.add(r)
        max_ring = max(max_ring, r)
    if CATCH_RADIUS_KM < max_ring:
        raise SystemExit(
            f"catch radius {CATCH_RADIUS_KM} km < largest ring {max_ring} km: "
            "the outer rings would be truncated by the catchment"
        )
    out.add(CITY_RADIUS_KM)
    out.add(CATCH_RADIUS_KM)
    return sorted(out)


def post(path, body):
    payload = json.dumps(body).encode("utf-8")
    last = None
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(
            API + path,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "apocalab-build/1.0"},
            method="POST",
        )
        try:
            with opener.open(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}: {exc.read()[:200].decode('utf-8', 'replace')}"
            if exc.code in (400, 413, 422):  # the request itself is wrong; retrying cannot help
                break
        except Exception as exc:  # noqa: BLE001 - network noise, retried below
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(2 * attempt)
    raise SystemExit(f"WorldPop {path} failed: {last}")


def per_km2_check(ring):
    """Sanity: the density in this band must not be absurdly higher than mean Earth.

    A wrong unit (m vs km) or a mis-scaled polygon shows up here as a number in
    the millions per km²; the API itself would still answer 200. The band is the
    one the API reports (from_km -> to_km), so this works for every chunk,
    including the ones that restart at 0.
    """
    from_km, to_km = ring["from_km"], ring["to_km"]
    area = math.pi * (to_km ** 2 - from_km ** 2)
    if area <= 0:
        raise SystemExit(f"radii not increasing: {from_km} -> {to_km}")
    density = ring["population"] / area
    if density > 400_000:
        raise SystemExit(f"implausible density {density:,.0f}/km² in band {from_km}-{to_km} km")
    return density


def main():
    refresh = "--refresh" in sys.argv
    cities = json.loads(CITIES.read_text(encoding="utf-8"))["cities"]
    radii = radii_from_effects()
    print(f"radii ({len(radii)}): {radii}")

    cache = {"cities": {}}
    if OUT.exists() and not refresh:
        cache = json.loads(OUT.read_text(encoding="utf-8"))
        if cache.get("radii_km") != radii:
            print("radii changed -> refetching every city")
            cache = {"cities": {}}

    source = None
    for i, city in enumerate(cities, 1):
        slug = city["slug"]
        if slug in cache["cities"] and not refresh:
            print(f"  [{i:2d}/{len(cities)}] {slug}: cached")
            continue

        # /catchment accepts at most 10 radii per call: two calls, merged.
        # `cumulative` is an absolute count within the radius, so merging is exact.
        cumulative = {}
        for chunk_start in range(0, len(radii), 10):
            chunk = radii[chunk_start:chunk_start + 10]
            catch = post("/catchment", {
                "points": [{"id": slug, "lon": city["lon"], "lat": city["lat"]}],
                "radii_km": chunk,
                "year": YEAR,
            })
            for ring in catch["points"][0]["rings"]:
                per_km2_check(ring)
                cumulative[f'{ring["to_km"]:.3f}'] = round(ring["cumulative"])

        # The dataset name is only reported by /population, so it is recorded
        # once, here, rather than typed into the source.
        if source is None:
            probe = post("/population", {
                "geojson": circle_geojson(city["lat"], city["lon"], CITY_RADIUS_KM),
                "year": YEAR,
            })
            source = probe["data_source"]
        cache["cities"][slug] = {
            "geonameid": city["geonameid"],
            "data_year": catch.get("data_year", YEAR),
            # Per-record, not only global: a page must be able to prove that the
            # 21.40 km ring it prints came from a catchment wide enough to hold it.
            "catchRadiusKm": CATCH_RADIUS_KM,
            "city_pop_10km": cumulative[f"{CITY_RADIUS_KM:.3f}"],
            "ring_population": cumulative,
        }
        print(f"  [{i:2d}/{len(cities)}] {slug}: 10 km {cache['cities'][slug]['city_pop_10km']:,}"
              f"  5 psi@100kt {cumulative['3.220']:,}")

    # One dataset name for the whole file: the API returns it per response, and a
    # mixed version would mean the figures are not comparable.
    cache["source"] = {
        "name": source,
        "api": API + "/catchment",
        "year": YEAR,
        "radius_km": CITY_RADIUS_KM,
        "catch_radius_km": CATCH_RADIUS_KM,
        "retrieved": time.strftime("%Y-%m-%d"),
        "license": "CC BY 4.0",
        "note": (
            "People inside a geodesic disc of the given radius around the "
            "GeoNames city point, integrated by WorldPop on their gridded surface. "
            "Every radius on a city page — fireball, 5 psi, 1 psi, both thermal "
            f"contours — is the cumulative inside one {CATCH_RADIUS_KM:g} km catchment, "
            "so no ring is ever built by subtracting another ring, and the widest "
            "ring (1 Mt 1 psi, 21.40 km) still sits inside the catchment. "
            "city_pop_10km is the cumulative at 10 km from that same catchment; it is "
            "never built by summing effect rings. The grid cell is 100 m, not the "
            "1 km of D4: this is the resolution the WorldPop API serves, and it is "
            "printed on the page beside the number."
        ),
    }
    cache["radii_km"] = radii
    cache["cities"] = {c["slug"]: cache["cities"][c["slug"]] for c in cities if c["slug"] in cache["cities"]}

    OUT.write_text(json.dumps(cache, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(cache['cities'])} cities, {cache['source']['name']})")


def circle_geojson(lat, lon, radius_km, n=96):
    """A geodesic circle, approximated by a 96-gon in degree space.

    The error is in the corners: a 96-gon inscribes the circle, so the polygon
    area is 0.07% under the true area. WorldPop integrates the polygon, not the
    circle, and reports the polygon's own area_km2 — that is why the area is
    printed and stored beside the number.
    """
    pts = []
    dlat = radius_km / 110.574
    dlon = radius_km / (111.320 * math.cos(math.radians(lat)))
    for i in range(n):
        b = 2 * math.pi * i / n
        pts.append([round(lon + dlon * math.cos(b), 5), round(lat + dlat * math.sin(b), 5)])
    pts.append(pts[0])
    return {"type": "Polygon", "coordinates": [pts]}


if __name__ == "__main__":
    main()
