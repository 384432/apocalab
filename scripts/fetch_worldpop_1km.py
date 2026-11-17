# -*- coding: utf-8 -*-
"""Download the WorldPop 2020 1 km per-country rasters.

Why these files: every population figure this site prints comes from WorldPop
(the API integrates their 100 m surface). A clicked-point estimate has to come
from the same product family, or one word would cover two unrelated population
sources. WorldPop publishes no global mosaic, so the 1 km 2020 country files are
the smallest complete download.

URLs are built directly instead of listing each country directory: the listing
costs a full round trip per country and the file name pattern is uniform
(`{iso}_ppp_2020_1km_Aggregated.tif`). A 404 is recorded as `absent`, because a
handful of territories publish no 1 km file.

    python scripts/fetch_worldpop_1km.py             # fetch what is missing
    python scripts/fetch_worldpop_1km.py --status    # print the manifest summary

Range resume is *attempted* but the host ignores it: measured on 2026-11-17,
`Range: bytes=2000000-` on RUS answered **200 with the whole body**, never 206.
So a stalled file restarts from zero, and the only lever that works is a long
per-read timeout (900 s) plus few enough parallel connections that the host keeps
answering — 10 workers make it return 503 for whichever country starts last.

Manifest: .tmp_handbook/worldpop1k/manifest.json — status, bytes, url per ISO3.
"""
import concurrent.futures as futures
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / ".tmp_handbook" / "worldpop1k"
MANIFEST = DEST / "manifest.json"
UA = {"User-Agent": "apocalab-tiles/1.0"}
# The sandbox proxy turns these requests into proxy errors and caps them at the
# same rate anyway; a direct connection is what worked for the country probes.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
ROW = re.compile(r'<a href="([^"?][^"]*)">[^<]*</a>')
# 10 workers is what triggers the 503s: the host starts refusing every new
# connection once the parallel count climbs, and the failures land on whichever
# country happens to start last. Three at a time is slower per file but it is the
# only setting observed to keep answering.
WORKERS = 3
RETRIES = 6
# 300 s was not enough for the three biggest files (RUS is ~70 MB at ~0.25 MB/s):
# the read timed out mid-transfer, the `.part` was thrown away, and the next
# attempt started from zero — it could never finish. Attempts now resume from
# the bytes already on disk, so the limit only has to cover one stall.
TIMEOUT = 900


def list_isos():
    req = urllib.request.Request(BASE, headers=UA)
    with OPENER.open(req, timeout=120) as r:
        html = r.read().decode("utf-8", "replace")
    return sorted({m.group(1).strip("/") for m in ROW.finditer(html)
                   if m.group(1).endswith("/") and len(m.group(1).strip("/")) == 3})


def url_for(iso):
    return f"{BASE}{iso}/{iso.lower()}_ppp_2020_1km_Aggregated.tif"


def fetch(iso):
    dest = DEST / (iso.lower() + ".tif")
    if dest.exists() and dest.stat().st_size > 1024:
        return {"iso3": iso, "status": "cached", "bytes": dest.stat().st_size, "url": url_for(iso)}
    url = url_for(iso)
    part = dest.with_suffix(".part")
    last = ""
    for attempt in range(RETRIES):
        have = part.stat().st_size if part.exists() else 0
        headers = dict(UA)
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            req = urllib.request.Request(url, headers=headers)
            with OPENER.open(req, timeout=TIMEOUT) as r:
                if have and getattr(r, "status", None) != 206:
                    # Range refused: restart rather than append a second copy.
                    have = 0
                with open(part, "ab" if have else "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
            got = part.stat().st_size
            if got < 1024:
                part.unlink()
                return {"iso3": iso, "status": "absent", "url": url}
            part.replace(dest)
            return {"iso3": iso, "status": "ok", "bytes": got, "url": url}
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                if part.exists():
                    part.unlink()
                return {"iso3": iso, "status": "absent", "url": url}
            if exc.code == 416 and part.exists() and part.stat().st_size > 1024:
                # The part already holds the whole file.
                part.replace(dest)
                return {"iso3": iso, "status": "ok", "bytes": dest.stat().st_size, "url": url}
            last = f"{exc.code}"
            if exc.code in (429, 503, 502, 504):
                # Back off hard: this is the host refusing load, not a missing file.
                time.sleep(20 + attempt * 25)
                continue
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        # The partial file stays: that is what makes the next attempt a resume.
        time.sleep(5 + attempt * 5)
    kept = part.stat().st_size if part.exists() else 0
    return {"iso3": iso, "status": f"error: {last}", "url": url, "partial": kept}


def summarise(records):
    ok = [r for r in records if r["status"] in ("ok", "cached")]
    print(f"files: {len(ok)}  bytes: {sum(r.get('bytes', 0) for r in ok)/1e6:.1f} MB")
    for key in ("absent", "error"):
        bad = [r for r in records if r["status"].startswith(key)]
        print(f"{key}: {len(bad)} {' '.join(r['iso3'] for r in bad[:25])}")


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    if "--status" in sys.argv:
        summarise(json.loads(MANIFEST.read_text(encoding="utf-8"))["files"])
        return

    isos = list_isos()
    print(f"{len(isos)} countries", flush=True)
    done = []
    t0 = time.time()
    with futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        todo = [iso for iso in isos
                if not (DEST / (iso.lower() + ".tif")).exists()]
        fut = {pool.submit(fetch, iso): iso for iso in todo}
        for i, f in enumerate(futures.as_completed(fut), 1):
            rec = f.result()
            done.append(rec)
            moved = sum(r.get("bytes", 0) for r in done) / 1e6
            rate = moved / max(1e-9, time.time() - t0)
            print(f"[{i}/{len(todo)}] {rec['iso3']} {rec['status']} "
                  f"{rec.get('bytes', 0)/1e6:.1f} MB · {moved:.0f} MB · {rate:.2f} MB/s",
                  flush=True)
            MANIFEST.write_text(json.dumps({"files": done}, indent=1), encoding="utf-8")

    cached = [{"iso3": iso, "status": "cached",
               "bytes": (DEST / (iso.lower() + ".tif")).stat().st_size,
               "url": url_for(iso)}
              for iso in isos if (DEST / (iso.lower() + ".tif")).exists()
              and iso not in {r["iso3"] for r in done}]
    MANIFEST.write_text(json.dumps({"files": sorted(done + cached, key=lambda r: r["iso3"])},
                                   indent=1), encoding="utf-8")
    summarise(done + cached)


if __name__ == "__main__":
    main()
