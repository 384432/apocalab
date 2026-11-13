# -*- coding: utf-8 -*-
"""Spot check: sum the 100 m WorldPop cells inside one ring, by hand.

This is not part of the build. It exists to answer one question the API cannot
answer for itself: does the number printed on a city page actually equal the sum
of the grid cells inside that circle? It re-adds the cells with numpy and
compares.

Needs rasterio + numpy, which are not build dependencies:

    python -m venv .venv && .venv/Scripts/pip install numpy rasterio

    python scripts/check_raster_sum.py paris 3.22
    python scripts/check_raster_sum.py new-york 0.1

The raster is the same WorldPop 100 m constrained UN-adjusted 2020 surface the
API integrates. The product path is the country file WorldPop publishes for a
download; the API names its release "R2025A", so a small difference is expected
and is reported rather than smoothed over.
"""
import json
import math
import os
import pathlib
import sys
import urllib.request

import numpy as np
import rasterio
from rasterio.windows import from_bounds

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".tmp_handbook" / "worldpop"

# Country file -> (iso3). Only the countries this site publishes.
ISO3 = {"new-york": "USA", "los-angeles": "USA", "london": "GBR",
        "paris": "FRA", "tokyo": "JPN"}
# 100 m constrained, UN-adjusted, 2020.
URL = ("https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/"
       "2020/BSGM/{iso3}/{iso3_l}_ppp_2020_UNadj_constrained.tif")


def fetch(iso3):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{iso3.lower()}_ppp_2020_UNadj_constrained.tif"
    if p.exists() and p.stat().st_size > 1_000_000:
        return p
    url = URL.format(iso3=iso3, iso3_l=iso3.lower())
    proxy = os.environ.get("WORLDPOP_PROXY")
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else \
               [urllib.request.ProxyHandler({})]
    req = urllib.request.Request(url, headers={"User-Agent": "apocalab-check/1.0"})
    with urllib.request.build_opener(*handlers).open(req, timeout=900) as r, open(p, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    print(f"downloaded {p.name}: {p.stat().st_size/1048576:.1f} MB")
    return p


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    h = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.minimum(1.0, np.sqrt(h)))


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "paris"
    radius = float(sys.argv[2]) if len(sys.argv) > 2 else 3.22
    cities = json.loads((ROOT / "src" / "data" / "cities.json").read_text(encoding="utf-8"))["cities"]
    city = next(c for c in cities if c["slug"] == slug)
    lat, lon = float(city["lat"]), float(city["lon"])

    path = fetch(ISO3[slug])
    pad = radius / 110.574 * 1.6
    with rasterio.open(path) as ds:
        win = from_bounds(lon - pad, lat - pad, lon + pad, lat + pad, ds.transform)
        arr = ds.read(1, window=win, boundless=True, fill_value=0)
        tr = ds.window_transform(win)
        print(f"grid: {arr.shape[0]}x{arr.shape[1]} cells, {tr.a:.8f} deg x {-tr.e:.8f} deg, "
              f"crs={ds.crs}")
        rows, cols = np.indices(arr.shape)
        cell_lon = tr.c + (cols + 0.5) * tr.a
        cell_lat = tr.f + (rows + 0.5) * tr.e
        d = haversine_km(lat, lon, cell_lat, cell_lon)
        inside = d <= radius
        vals = arr[inside].astype("float64")
        # WorldPop marks no-data with a large negative value; those cells are
        # ocean, outside the national boundary, or simply no settlement. Treat
        # them as zero people, and say how many there were rather than hiding it.
        nodata = ds.nodata if ds.nodata is not None else -99999.0
        holes = int((vals <= nodata / 2).sum())
        vals = np.clip(vals, 0, None)
        vals = np.where(vals > 1e6, 0, vals)  # a cell above 1e6 people is a sentinel
        n = int(inside.sum())
        total = float(vals.sum())
        print(f"cells inside {radius} km: {n}   no-data / empty cells: {holes}")
        print(f"sum: {total:,.0f} people")
        print(f"mean per cell: {vals.mean():.2f}   max cell: {vals.max():.1f}")
        dens = total / (math.pi * radius ** 2)
        print(f"implied density: {dens:,.0f}/km²  (mean per cell {vals.mean():.2f} "
              f"= {vals.mean()/0.01:,.0f}/km²)")

    data = json.loads((ROOT / "src" / "data" / "city-pop.json").read_text(encoding="utf-8"))
    page = data["cities"][slug]["ring_population"].get(f"{radius:.3f}")
    if page is not None:
        print(f"page figure: {page:,}   difference: {100*(total-page)/page:+.2f}%")


if __name__ == "__main__":
    main()
