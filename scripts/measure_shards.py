"""Measure the per-bucket payload size of the GeoNames gazetteer (plan §15 step 0).

Reads .tmp_handbook/cities15000.txt (34,214 rows, 19 tab-separated columns, no header)
and answers three questions with real bytes, no estimates:

  A. How many buckets does the first letter of `asciiname` actually produce, and how
     big is each one (uncompressed + gzip) when only the seven search fields survive?
  B. Does dropping the duplicated `asciiname` (name == asciiname on 27,089 rows)
     save more than 100 KB after gzip, on the whole file and summed per bucket?
  C. What does the whole file weigh, both as one blob and as the sum of its buckets?

Nothing here ships. The output is pasted into plan.md and this script stays as the
reproducible record. Run: python scripts/measure_shards.py
"""

import gzip
import json
import os
import sys
from collections import defaultdict

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   ".tmp_handbook", "cities15000.txt")

FIELDS = ["geonameid", "name", "asciiname", "latitude", "longitude", "population",
          "admin1", "country"]


def gz(b):
    return len(gzip.compress(b, compresslevel=9, mtime=0))


def load():
    rows = []
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            c = line.split("\t")
            rows.append({
                "geonameid": int(c[0]),
                "name": c[1],
                "asciiname": c[2],
                # float() not round(): this is the encoding the §15 baseline
                # (2,348,515 B / 886,209 B) was measured on, so the per-bucket
                # numbers stay directly comparable with it.
                "latitude": float(c[4]),
                "longitude": float(c[5]),
                "population": int(c[14] or 0),
                "admin1": c[10],
                "country": c[8],
            })
    return rows


def flat(row, merge=None):
    """Compact array. merge: None = as-is, 'null' = null when duplicates name,
    'empty' = empty string when duplicates name, 'split' handled by caller."""
    a = row["asciiname"]
    if merge == "null" and a == row["name"]:
        a = None
    elif merge == "empty" and a == row["name"]:
        a = ""
    return [row["geonameid"], row["name"], a, row["latitude"], row["longitude"],
            row["population"], row["admin1"], row["country"]]


def dump(seq):
    return json.dumps(seq, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def bucket_key(row):
    a = row["asciiname"]
    if not a:
        return ""
    ch = a[0].upper()
    return ch if ("A" <= ch <= "Z") else ch


def main():
    rows = load()
    print(f"rows loaded: {len(rows)}")
    uniq = defaultdict(int)
    for r in rows:
        uniq[bucket_key(r)] += 1
    print(f"raw first-char buckets: {len(uniq)}")
    print("bucket row counts: " + ", ".join(
        f"{k or '<empty>'}={uniq[k]}" for k in sorted(uniq)))

    # --- A. per-bucket sizes, current shape -------------------------------------
    buckets = defaultdict(list)
    for r in rows:
        buckets[bucket_key(r)].append(r)

    print("\n--- A. per bucket (7 search fields, compact arrays) ---")
    print(f"{'bucket':8} {'rows':>6} {'raw B':>10} {'gzip B':>9}")
    per = []
    for k in sorted(buckets):
        blob = dump([flat(r) for r in buckets[k]])
        per.append((k, len(buckets[k]), len(blob), gz(blob)))
    for k, n, raw, g in sorted(per, key=lambda x: -x[3]):
        print(f"{k or '<empty>':8} {n:6d} {raw:10d} {g:9d}")
    tot_raw = sum(x[2] for x in per)
    tot_gz = sum(x[3] for x in per)
    print(f"{'TOTAL':8} {len(rows):6d} {tot_raw:10d} {tot_gz:9d}  (sum of buckets)")
    gzs = sorted(x[3] for x in per)
    print(f"median bucket gzip: {gzs[len(gzs) // 2]}  min {gzs[0]}  max {gzs[-1]}")

    whole = dump([flat(r) for r in rows])
    print(f"whole file as one blob: raw {len(whole)}  gzip {gz(whole)}")

    # --- B. duplicate-name variants --------------------------------------------
    print("\n--- B. name == asciiname dropped ---")
    same = sum(1 for r in rows if r["name"] == r["asciiname"])
    print(f"identical rows: {same} / {len(rows)} ({same / len(rows) * 100:.1f}%)")

    variants = {}
    for mode in (None, "null", "empty"):
        blob = dump([flat(r, mode) for r in rows])
        variants[mode] = (len(blob), gz(blob))
        label = mode or "as-is"
        print(f"whole  {label:6}: raw {len(blob):9d}  gzip {gz(blob):9d}")

    # 'split': rows lose the asciiname slot entirely, the 7,125 rows that really
    # differ hang off a sparse {row_index: asciiname} map. The most favourable
    # shape for the merge idea, so the verdict is not won by a bad encoding.
    def split_blob(seq):
        data = [[r[0], r[1], r[3], r[4], r[5], r[6], r[7]] for r in seq]
        extra = {str(i): r[2] for i, r in enumerate(seq) if r[2] != r[1]}
        return dump([data, extra])

    blob = split_blob([flat(r) for r in rows])
    variants["split"] = (len(blob), gz(blob))
    print(f"whole  split : raw {len(blob):9d}  gzip {gz(blob):9d}")

    # per-bucket sums, which is what the shards actually ship
    for mode in (None, "null", "empty"):
        s_raw = s_gz = 0
        for k in sorted(buckets):
            blob = dump([flat(r, mode) for r in buckets[k]])
            s_raw += len(blob)
            s_gz += gz(blob)
        variants[f"sum-{mode}"] = (s_raw, s_gz)
        print(f"shards {mode or 'as-is':6}: raw {s_raw:9d}  gzip {s_gz:9d}")

    s_raw = s_gz = 0
    for k in sorted(buckets):
        blob = split_blob([flat(r) for r in buckets[k]])
        s_raw += len(blob)
        s_gz += gz(blob)
    variants["sum-split"] = (s_raw, s_gz)
    print(f"shards {'split':6}: raw {s_raw:9d}  gzip {s_gz:9d}")

    base = variants["sum-None"][1]
    print(f"\ndelta vs current shape (shards, gzip):")
    for key in ("sum-null", "sum-empty", "sum-split"):
        print(f"  {key:10}: {base - variants[key][1]:+d} B saved")
    base_w = variants[None][1]
    for key in ("null", "empty", "split"):
        print(f"  {key:10}: {base_w - variants[key][1]:+d} B saved (whole file)")

    # --- C. what the top three buckets cost on the wire ------------------------
    print("\n--- C. top three buckets ---")
    for k, n, raw, g in sorted(per, key=lambda x: -x[3])[:3]:
        print(f"{k}: {n} rows, {raw} B raw, {g} B gzip, gzip/row {g / n:.1f} B")


if __name__ == "__main__":
    sys.exit(main())
