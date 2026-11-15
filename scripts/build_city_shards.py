"""Build the 27 lazy-loaded gazetteer shards (plan §15).

Input : .tmp_handbook/cities15000.txt  (34,214 rows, 19 tab-separated columns, no header)
Output: public/data/cities/<key>.json   (a-z + "other"; compact arrays, UTF-8, no spaces)

Row shape: [geonameid, name, asciiname, latitude, longitude, population, admin1, country]

Two rules are fixed in plan §15 and this script must not drift from them:

  * The bucket key is the first character of **asciiname** (the pure-ASCII name),
    uppercased; anything outside A-Z goes to `other`. Not `name` — `Łódź` and
    `Ålesund` start with letters that would fall into `other` and become
    unreachable from an English keyboard.
  * Row order inside a shard is the source file's order, never sorted: the byte
    and gzip figures recorded in §15 were measured in this order, and sorting on
    disk would make them unreproducible. The client sorts matched candidates by
    population at match time.

Deviation from either rule is a plan change, not an implementation detail.

Run: python scripts/build_city_shards.py
"""

import gzip
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, ".tmp_handbook", "cities15000.txt")
OUT = os.path.join(ROOT, "public", "data", "cities")

KEYS = [chr(c) for c in range(ord("a"), ord("z") + 1)] + ["other"]

# §15 baseline, measured on exactly this shape. If these drift, the plan's numbers
# are describing something that is no longer shipped.
BASELINE_ROWS = 34214
BASELINE_RAW = 2348515
BASELINE_GZIP = 886209


def bucket_key(asciiname: str) -> str:
    if not asciiname:
        return "other"
    ch = asciiname[0].upper()
    return ch.lower() if "A" <= ch <= "Z" else "other"


def main() -> int:
    rows = []
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            c = line.split("\t")
            rows.append([
                int(c[0]),            # geonameid
                c[1],                 # name
                c[2],                 # asciiname
                float(c[4]),          # latitude
                float(c[5]),          # longitude
                int(c[14] or 0),      # population
                c[10],                # admin1
                c[8],                 # country code
            ])

    if len(rows) != BASELINE_ROWS:
        print(f"FAIL 源文件 {len(rows)} 行，§15 基线是 {BASELINE_ROWS} 行", file=sys.stderr)
        return 1

    buckets = OrderedDict((k, []) for k in KEYS)
    for row in rows:
        buckets[bucket_key(row[2])].append(row)

    placed = sum(len(v) for v in buckets.values())
    if placed != len(rows):
        print(f"FAIL 分桶只放下 {placed} / {len(rows)} 行", file=sys.stderr)
        return 1
    empty = [k for k, v in buckets.items() if not v]
    if empty:
        print(f"FAIL 空桶 {empty}：客户端会去取一个 404", file=sys.stderr)
        return 1

    os.makedirs(OUT, exist_ok=True)
    total_raw = total_gz = 0
    print(f"{'file':10} {'rows':>6} {'bytes':>9} {'gzip':>8}")
    for key, rs in buckets.items():
        blob = json.dumps(rs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        path = os.path.join(OUT, f"{key}.json")
        with open(path, "wb") as fh:
            fh.write(blob)
        gz = len(gzip.compress(blob, compresslevel=9, mtime=0))
        total_raw += len(blob)
        total_gz += gz
        print(f"{key + '.json':10} {len(rs):6d} {len(blob):9d} {gz:8d}")

    whole = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    whole_gz = len(gzip.compress(whole, compresslevel=9, mtime=0))
    print(f"{'SUM':10} {placed:6d} {total_raw:9d} {total_gz:8d}")
    print(f"{'one file':10} {placed:6d} {len(whole):9d} {whole_gz:8d}")

    # The one-file numbers are what §15 quotes; the per-file sum is the price of
    # sharding (each file pays for its own gzip dictionary).
    print(f"\n单文件 {len(whole)} / gzip {whole_gz}  vs §15 基线 {BASELINE_RAW} / {BASELINE_GZIP}")
    if len(whole) != BASELINE_RAW or whole_gz != BASELINE_GZIP:
        print("FAIL 与 §15 基线不一致：行序或字段变了，先查清再改数", file=sys.stderr)
        return 1
    print(f"逐桶求和 {total_raw} / gzip {total_gz}（比单文件 +{total_gz - whole_gz} 字节）")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
