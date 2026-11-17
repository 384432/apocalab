# -*- coding: utf-8 -*-
"""Build the population tiles the map reads when you click a point.

Input: the WorldPop 2020 1 km country rasters (scripts/fetch_worldpop_1km.py).
Output: public/data/pop/x{lon}y{lat}.bin — 10 deg x 10 deg tiles, one byte per
cell — plus src/data/pop-meta.json, which is the only description of the
encoding and is baked into the page island so a click never fetches it.

Grid, in one paragraph because every number below depends on it:

  source   30 arc-seconds, WorldPop 2020 1 km unadjusted, per country
  cell     1/24 deg = 5 source cells per side. 1/24 deg is 4.63 km at the
           equator and 2.32 km at 60 deg — a lat/lon grid cannot be 5 km
           everywhere, so the cell is defined in degrees and the ground size is
           reported, not assumed. 10 deg / (1/24) = 240 cells per tile edge.
  tile     10 deg x 10 deg, west to east, north to south, one byte per cell.

Aggregation is a cell-centre assignment, not an area average: every source cell
lands in exactly one tile cell, so the global sum is conserved and the build can
assert it. Quantisation is logarithmic, 255 intervals from 0.5 to 400,000 people
per cell, reconstructing at the geometric midpoint; the worst-case relative
error is sqrt(ratio) - 1, printed by this script and asserted below 3%.

Nothing here touches the site's tabulated city figures. Those come from the
WorldPop API at 100 m (scripts/build_city_pop.py) and stay bit-identical; this
script exists for the points that have no tabulated figure.

    python scripts/build_pop_tiles.py            # build + verify
    python scripts/build_pop_tiles.py --dry-run  # aggregate, print, write nothing
"""
import json
import math
import pathlib
import sys

import numpy as np
import rasterio

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / ".tmp_handbook" / "worldpop1k"
MANIFEST = SRC / "manifest.json"
OUT = ROOT / "public" / "data" / "pop"
META = ROOT / "src" / "data" / "pop-meta.json"

CELL_DEG = 1.0 / 24.0
TILE_DEG = 10.0
NX = int(360 / CELL_DEG)          # 8640 cells around
NY = int(180 / CELL_DEG)          # 4320 cells pole to pole
PER_TILE = int(TILE_DEG / CELL_DEG)  # 240

FLOOR = 1.0           # below one person a cell is empty (level 0)
TOP = 3000000.0       # the largest cell in the data is ~1.3 million; this is headroom
LEVELS = 255          # levels 1..255; level 0 means "no people"
RATIO = (TOP / FLOOR) ** (1.0 / LEVELS)

SOURCE = {
    "name": "WorldPop 2020 1 km UN-adjusted (Global_2000_2020_1km, 2020)",
    "url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/",
    "license": "CC BY 4.0",
    "year": 2020,
    "resolution_deg": 1.0 / 120.0,
    "note": (
        "Same product family as the tabulated city figures (WorldPop, 2020 "
        "estimates) but the downloadable 1 km release, not the API's 100 m "
        "R2025A surface. Aggregated to 1/24 deg cells; see /methodology/."
    ),
}


def manifest_files():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ok = [r for r in data["files"] if r["status"] in ("ok", "cached")]
    missing = [r["iso3"] for r in data["files"] if r["status"] == "absent"]
    return ok, missing


def aggregate(files, acc):
    """Add every country raster into the global cell accumulator."""
    rows_done = 0
    for rec in files:
        path = SRC / (rec["iso3"].lower() + ".tif")
        if not path.exists():
            print(f"  !! {rec['iso3']}: manifest says {rec['status']} but {path.name} is gone")
            continue
        with rasterio.open(path) as ds:
            a = ds.transform
            if abs(a.a - 1.0 / 120.0) > 1e-9 or abs(-a.e - 1.0 / 120.0) > 1e-9:
                raise SystemExit(
                    f"{path.name}: unexpected pixel size {a.a:.10f} x {-a.e:.10f}, "
                    "the cell-centre assignment assumes 30 arc-seconds"
                )
            nod = ds.nodata if ds.nodata is not None else -99999.0
            step = 1024
            for r0 in range(0, ds.height, step):
                h = min(step, ds.height - r0)
                block = ds.read(1, window=((r0, r0 + h), (0, ds.width))).astype(np.float64)
                valid = block > max(0.0, nod)
                if not valid.any():
                    continue
                rr, cc = np.nonzero(valid)
                vals = block[rr, cc]
                lon = a.c + (cc + 0.5) * a.a
                lat = a.f + (r0 + rr + 0.5) * a.e
                ci = np.floor((lon + 180.0) / CELL_DEG).astype(np.int32)
                ri = np.floor((90.0 - lat) / CELL_DEG).astype(np.int32)
                np.clip(ci, 0, NX - 1, out=ci)
                np.clip(ri, 0, NY - 1, out=ri)
                idx = ri.astype(np.int64) * NX + ci
                acc += np.bincount(idx, weights=vals, minlength=NX * NY).reshape(NY, NX).astype(
                    np.float64
                )
            rows_done += 1
            if rows_done % 25 == 0:
                print(f"  {rows_done}/{len(files)} countries, "
                      f"running total {acc.sum()/1e9:.4f} billion", flush=True)


def encode(arr):
    """1 byte per cell: 0 = empty, 1..255 = log bins from FLOOR to TOP."""
    out = np.zeros(arr.shape, dtype=np.uint8)
    nz = arr >= FLOOR
    if nz.any():
        lvl = np.floor(np.log(arr[nz] / FLOOR) / math.log(RATIO)).astype(np.int64) + 1
        np.clip(lvl, 1, LEVELS, out=lvl)
        out[nz] = lvl.astype(np.uint8)
    return out


def decode(codes):
    """Rebuild people per cell at the geometric midpoint of each bin."""
    vals = np.zeros(codes.shape, dtype=np.float64)
    nz = codes > 0
    if nz.any():
        c = codes[nz].astype(np.float64)
        # bin i covers FLOOR*RATIO^(i-1) .. FLOOR*RATIO^i, level 0 is exactly 0
        vals[nz] = FLOOR * np.power(RATIO, c - 0.5)
    return vals


def main():
    dry = "--dry-run" in sys.argv
    # A partial run exists only to smoke-test the client before every country
    # has arrived. It marks the meta so a partial build cannot be mistaken for
    # the real one: the final build has no flag and no `partial` key.
    partial = "--partial-ok" in sys.argv
    files, missing = manifest_files()
    print(f"{len(files)} country rasters, {len(missing)} with no 1 km file "
          f"({', '.join(missing[:12])}{' …' if len(missing) > 12 else ''})")

    acc = np.zeros((NY, NX), dtype=np.float64)
    aggregate(files, acc)

    total = acc.sum()
    print(f"aggregated total: {total:,.0f} people over {int((acc > 0).sum()):,} cells")
    if not 6.5e9 < total < 9.5e9 and not partial:
        raise SystemExit(
            f"total {total:,.0f} is not a plausible world population — a country file "
            "is missing or misread; refusing to write tiles"
        )

    # Quantisation error, measured on the real cell values, not assumed.
    codes = encode(acc)
    back = decode(codes)
    nz = acc >= FLOOR
    err = np.abs(back[nz] - acc[nz]) / acc[nz]
    clipped = int((acc > TOP).sum())
    print(f"quantisation: max relative error {100*err.max():.3f}%, "
          f"mean {100*err.mean():.3f}%, cells > {TOP:,.0f}: {clipped}")
    print(f"largest cell: {acc.max():,.0f} people")
    if clipped:
        raise SystemExit(
            f"{clipped} cells hold more than the top bin ({TOP:,.0f}); widening the "
            "range would push the bin step past the 3% budget — re-size the bins, "
            "do not clip"
        )
    if err.max() >= 0.03:
        raise SystemExit(f"quantisation error {100*err.max():.2f}% exceeds the 3% budget")
    print(f"sum after quantisation: {back.sum():,.0f} ({100*(back.sum()-total)/total:+.3f}%)")

    if dry:
        print("dry run: nothing written")
        return

    OUT.mkdir(parents=True, exist_ok=True)

    # The tile grid is fixed at 36×18 names, so every rebuild overwrites the same
    # 648 files. Deleting them first is pointless and, on Windows, it trips the
    # bulk-delete guard at 50 files. Write first, then drop only the names this
    # build did not produce (normally none — that is the case a grid change would
    # show up in).
    written = 0
    names = set()
    for ty in range(NY // PER_TILE):
        for tx in range(NX // PER_TILE):
            block = codes[ty * PER_TILE:(ty + 1) * PER_TILE, tx * PER_TILE:(tx + 1) * PER_TILE]
            name = f"x{tx:02d}y{ty:02d}.bin"
            block.tofile(OUT / name)
            names.add(name)
            written += 1
    stray = sorted(p.name for p in OUT.glob("*.bin") if p.name not in names)
    for name in stray:
        (OUT / name).unlink()
    if stray:
        print(f"removed {len(stray)} stale tiles: {' '.join(stray[:10])}")
    size = sum(p.stat().st_size for p in OUT.glob("*.bin"))
    print(f"wrote {written} tiles, {size:,} bytes total "
          f"({size/1e6:.1f} MB, {PER_TILE*PER_TILE:,} bytes each)")

    meta = {
        "source": SOURCE,
        "grid": {
            "cell_deg": CELL_DEG,
            "cell_km_equator": CELL_DEG * 111.319,
            "cells_per_tile": PER_TILE,
            "tile_deg": TILE_DEG,
            "tiles": written,
            "origin": "x00y00 is 180 W .. 170 W, 90 N .. 80 N; y increases southward",
            "order": "row-major, north to south, west to east, one byte per cell",
        },
        "bins": {
            "floor": FLOOR,
            "top": TOP,
            "levels": LEVELS,
            "ratio": RATIO,
            "decode": "level 0 = 0 people; level i>0 = floor * ratio^(i-0.5)",
            "max_relative_error": float(err.max()),
        },
        "totals": {
            "people_before_quantisation": float(total),
            "people_after_quantisation": float(back.sum()),
            "cells_with_people": int((acc > 0).sum()),
            "cells_clipped_at_top": clipped,
        },
        "built": "python scripts/build_pop_tiles.py",
    }
    if partial:
        meta["partial"] = True
        meta["built"] += " --partial-ok"
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {META.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
