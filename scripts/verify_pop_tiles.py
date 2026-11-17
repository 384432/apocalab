# -*- coding: utf-8 -*-
"""Gate for the population tiles, and the independent check on the browser sum.

Two jobs, both of them about the same claim — "the number the map prints came
from these tiles, and it is the same number this script gets":

  1. tiles: count, per-file size, decoded total, worst-case bin error, no cell
     above the top bin, and the coverage of the world the source actually has.
  2. agreement: re-sum the rings at the very coordinates the click gate landed
     on, with the same arithmetic the browser uses, and compare. If the two
     disagree, one of them is wrong and the map is guessing.

Also prints, for the 20 tabulated cities, how far the 1 km tile surface sits from
the 100 m API figure. That gap is expected — different surface, different
release — and it is reported rather than tuned away, because a snapped click
uses the table and a click 6 km away uses the tiles.

    python scripts/verify_pop_tiles.py
"""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
META = ROOT / "src" / "data" / "pop-meta.json"
TILES = ROOT / "public" / "data" / "pop"
CITY_POP = ROOT / "src" / "data" / "city-pop.json"
CITY_LIST = ROOT / "src" / "data" / "cities.json"
GATE = ROOT / "click-gate.json"
OUT = ROOT / "pop-gate.json"

KM_LAT = 110.574
KM_LON = 111.32
SLICES = 48

passes = []
fails = []


def check(ok, label):
    (passes if ok else fails).append(label)


def load_tiles(meta):
    per = meta["grid"]["cells_per_tile"]
    n = meta["grid"]["tiles"]
    files = sorted(TILES.glob("*.bin"))
    check(len(files) == n, f"瓦片文件 {len(files)} 个 = 元数据 {n} 个")
    check(len(files) == 36 * 18, f"瓦片数 {len(files)} = 36×18")
    bad = [f.name for f in files if f.stat().st_size != per * per]
    check(not bad, f"每个瓦片 {per*per:,} 字节（例外 {len(bad)}）")
    tiles = {}
    for f in files:
        tiles[f.stem] = f.read_bytes()
    return tiles


def decode(meta, code):
    if code == 0:
        return 0.0
    b = meta["bins"]
    return b["floor"] * math.pow(b["ratio"], code - 0.5)


def code_at(meta, tiles, ci, cj):
    per = meta["grid"]["cells_per_tile"]
    tx, ty = ci // per, cj // per
    t = tiles.get(f"x{tx:02d}y{ty:02d}")
    if t is None:
        return -1
    col, row = ci - tx * per, cj - ty * per
    if not (0 <= col < per and 0 <= row < per):
        return -1
    return t[row * per + col]


def overlap(x0, x1, y0, y1, r, cell_area):
    lo, hi = max(x0, -r), min(x1, r)
    bot, top = max(y0, -r), min(y1, r)
    if hi <= lo or top <= bot or cell_area <= 0:
        return 0.0
    dy = (top - bot) / SLICES
    area = 0.0
    for i in range(SLICES):
        y = bot + (i + 0.5) * dy
        half = math.sqrt(max(0.0, r * r - y * y))
        l, rr = max(lo, -half), min(hi, half)
        if rr > l:
            area += (rr - l) * dy
    return min(1.0, area / cell_area)


def sum_inside(meta, tiles, lat, lon, radius):
    """The exact arithmetic of src/scripts/bomb-map.ts sumInside()."""
    g = meta["grid"]
    cell = g["cell_deg"]
    km_lon = KM_LON * max(0.02, math.cos(math.radians(max(-89.0, min(89.0, lat)))))
    d_lat = radius / KM_LAT
    d_lon = radius / km_lon
    ci0 = math.floor((lon - d_lon + 180) / cell)
    ci1 = math.floor((lon + d_lon + 180) / cell)
    cj0 = math.floor((90 - (lat + d_lat)) / cell)
    cj1 = math.floor((90 - (lat - d_lat)) / cell)
    cell_w = cell * km_lon
    cell_h = cell * KM_LAT
    cell_area = cell_w * cell_h
    total = 0.0
    for cj in range(cj0, cj1 + 1):
        y1 = (90 - cj * cell - lat) * KM_LAT
        y0 = y1 - cell_h
        for ci in range(ci0, ci1 + 1):
            code = code_at(meta, tiles, ci, cj)
            if code <= 0:
                continue
            x0 = (ci * cell - 180 - lon) * km_lon
            total += decode(meta, code) * overlap(x0, x0 + cell_w, y0, y1, radius, cell_area)
    return total


def main():
    meta = json.loads(META.read_text(encoding="utf-8"))
    if meta.get("partial"):
        print("!! this meta was built with --partial-ok: coverage is not global")
    tiles = load_tiles(meta)
    per = meta["grid"]["cells_per_tile"]

    total = 0.0
    peak = 0
    for t in tiles.values():
        for code in t:
            if code:
                total += decode(meta, code)
                if code > peak:
                    peak = code
    b = meta["bins"]
    top_code_value = b["floor"] * math.pow(b["ratio"], 254 - 0.5)
    check(peak <= 254, f"最高档 {peak} ≤ 254（未触顶）")
    check(abs(total - meta["totals"]["people_after_quantisation"]) < 1.0,
          f"解码总量 {total:,.0f} = 元数据 {meta['totals']['people_after_quantisation']:,.0f}")
    check(b["max_relative_error"] < 0.03,
          f"档位最大相对误差 {100*b['max_relative_error']:.3f}% < 3%")
    check(abs(math.sqrt(b["ratio"]) - 1 - b["max_relative_error"]) < 5e-4,
          "误差界与档位比值自洽（sqrt(ratio)-1）")
    print(f"tiles {len(tiles)} · people {total:,.0f} · top code {peak} "
          f"({top_code_value:,.0f}) · bin step {100*(b['ratio']-1):.2f}%")

    # ---- the two surfaces, city by city: how far apart are they?
    # Not an equality test and never will be: the tiles are 4.63 km cells of the
    # downloadable release, the table is 100 m of the API release. What is
    # asserted is that the resolvable rings — those wider than a cell — stay in
    # the same league, and that the sub-cell rings are reported as the shares of
    # a cell they are, not hidden.
    cities = json.loads(CITY_LIST.read_text(encoding="utf-8"))["cities"]
    pop = json.loads(CITY_POP.read_text(encoding="utf-8"))["cities"]
    gaps = []
    for c in cities:
        rec = pop.get(c["slug"])
        if not rec:
            continue
        for key, table_value in sorted(rec["ring_population"].items(), key=lambda kv: float(kv[0])):
            r = float(key)
            if r >= 25 or not table_value:
                continue
            mine = sum_inside(meta, tiles, float(c["lat"]), float(c["lon"]), r)
            gaps.append((c["slug"], r, table_value, mine, 100 * (mine - table_value) / table_value))
    wide = [g for g in gaps if g[1] >= 5.0]
    narrow = [g for g in gaps if g[1] < 5.0]
    worst = max(wide, key=lambda g: abs(g[4]))
    print(f"20 城 · 环 ≥ 5 km（可分辨）：{len(wide)} 档，平均差 {sum(g[4] for g in wide)/len(wide):+.1f}%，"
          f"最大 {worst[4]:+.1f}%（{worst[0]} @ {worst[1]} km：表 {worst[2]:,} / 瓦片 {worst[3]:,.0f}）")
    if narrow:
        nw = max(narrow, key=lambda g: abs(g[4]))
        print(f"20 城 · 环 < 5 km（小于一格，只能按格内密度折算）：{len(narrow)} 档，"
              f"最大 {nw[4]:+.1f}%（{nw[0]} @ {nw[1]} km：表 {nw[2]:,} / 瓦片 {nw[3]:,.0f}）")
    check(all(abs(g[4]) < 60 for g in wide),
          f"可分辨环里没有量级错误（最大 {worst[4]:+.1f}%）")

    # ---- agreement with the browser, at the coordinates the gate clicked
    agreement = []
    if GATE.exists():
        gate = json.loads(GATE.read_text(encoding="utf-8"))

        def node_at(*path):
            cur = gate
            for key in path:
                cur = cur.get(key) if isinstance(cur, dict) else None
                if cur is None:
                    return None
            return cur if isinstance(cur, dict) else None

        cases = [
            ("a", node_at("a", "out", "after")),
            ("b", node_at("b", "out", "after")),
            ("c-ocean", node_at("c", "ocean", "out", "after")),
            ("c-desert", node_at("c", "desert", "out", "after")),
            ("g-touch", node_at("g", "touch", "out", "after")),
        ]
        for name, node in cases:
            if not node:
                continue
            centre = node.get("centre")
            vals = (node.get("pop") or {}).get("vals")
            kind = (node.get("pop") or {}).get("kind")
            if not centre or not vals or kind != "tiles":
                continue
            for key, shown in vals.items():
                mine = sum_inside(meta, tiles, centre["lat"], centre["lon"], float(key))
                agreement.append((name, key, shown, round(mine), shown - round(mine)))
        bad = [a for a in agreement if a[4] != 0]
        for name, key, shown, mine, delta in agreement:
            print(f"  {name:9s} {key} km  浏览器 {shown:>10,}  脚本 {mine:>10,}  Δ {delta}")
        check(not bad, f"浏览器与脚本逐档一致（{len(agreement)} 档，{len(bad)} 档不同）")
    else:
        print("click-gate.json 不在，跳过浏览器一致性对比")

    result = {"pass": len(passes), "fail": len(fails), "problems": fails,
              "people": total, "bins": {"floor": b["floor"], "top": b["top"],
                                        "levels": b["levels"], "ratio": b["ratio"],
                                        "max_relative_error": b["max_relative_error"]},
              "surface_gap_pct": {
                  "wide_mean": sum(g[4] for g in wide) / len(wide),
                  "wide_worst": worst[4], "wide_worst_at": f"{worst[0]} {worst[1]} km",
                  "narrow_worst": (max(abs(g[4]) for g in narrow) if narrow else None),
              },
              "agreement": [{"case": a[0], "km": a[1], "browser": a[2], "script": a[3]} for a in agreement]}
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"\n结果：PASS {len(passes)}  FAIL {len(fails)}")
    for f in fails:
        print("  FAIL", f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
