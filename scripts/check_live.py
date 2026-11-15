"""Post-go-live gate: does the live site actually serve indexable responses?

Four checks, in the order plan 3.7 step 6 lists them:

  1. eleven URLs, no `X-Robots-Tag` on any of them
  2. dist/ has zero occurrences of `noindex` across every .html and _headers
  3. robots.txt has no site-wide `Disallow: /` and points at the apex sitemap
  4. every canonical still names the apex, and sitemap.xml still lists 10 apex locs

Check 5 (the www 301s) lives in scripts/check_www.py and is run separately.

    python scripts/check_live.py                 # against https://apocalab.com
    python scripts/check_live.py --host <host>   # against another host

Exit 1 if any assertion fails. `httpx` is not available here, and neither is a
working system resolver on this machine, so DNS falls back to AliDNS over HTTPS
before giving up — same shim as scripts/check_www.py.
"""

from __future__ import annotations

import json
import os
import re
import socket
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

HOST = "apocalab.com"
if "--host" in sys.argv:
    HOST = sys.argv[sys.argv.index("--host") + 1]

URLS = [
    "/",
    "/blast-radius/",
    "/nuclear-bomb-map/",
    "/methodology/",
    "/nuclear-winter/",
    "/nuclear-bomb-map/new-york/",
    "/nuclear-bomb-map/los-angeles/",
    "/nuclear-bomb-map/london/",
    "/nuclear-bomb-map/paris/",
    "/nuclear-bomb-map/tokyo/",
    "/sitemap.xml",
    "/robots.txt",
]

passes = 0
fails: list[str] = []
report: dict = {"host": HOST, "headers": [], "fails": []}


def check(cond: bool, label: str) -> bool:
    global passes
    if cond:
        passes += 1
    else:
        fails.append(label)
    return cond


# --------------------------------------------------------------------- DNS shim
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
_orig_gai = socket.getaddrinfo
_cache: dict[str, list[str]] = {}


def _resolve_via_doh(name: str) -> list[str]:
    if name in _cache:
        return _cache[name]
    ips: list[str] = []
    try:
        url = f"https://dns.alidns.com/resolve?name={name}&type=A"
        raw = _opener.open(
            urllib.request.Request(url, headers={"User-Agent": "apocalab-gate"}),
            timeout=20,
        ).read()
        ips = [a["data"] for a in (json.loads(raw).get("Answer") or []) if a.get("type") == 1]
    except Exception:
        ips = []
    _cache[name] = ips
    return ips


def _patched_gai(host, port, *a, **k):
    try:
        return _orig_gai(host, port, *a, **k)
    except socket.gaierror:
        pass
    name = host.decode() if isinstance(host, bytes) else str(host)
    ips = _resolve_via_doh(name)
    if ips:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0)) for ip in ips]
    return _orig_gai(host, port, *a, **k)


socket.getaddrinfo = _patched_gai


def fetch(path: str):
    """GET a path, return (status, headers, body). No redirect following."""
    ctx = ssl.create_default_context()
    conn = __import__("http.client", fromlist=["HTTPSConnection"]).HTTPSConnection(
        HOST, 443, timeout=25, context=ctx
    )
    try:
        conn.request(
            "GET",
            path,
            headers={
                "User-Agent": "apocalab-gate/1.0",
                "Accept": "*/*",
                "Cache-Control": "no-cache",
            },
        )
        r = conn.getresponse()
        body = r.read()
        return r.status, dict((k.lower(), v) for k, v in r.getheaders()), body
    finally:
        conn.close()


# ------------------------------------------------------- 1. the eleven headers
print(f"1. response headers on https://{HOST} — no X-Robots-Tag expected")
for path in URLS:
    try:
        status, headers, body = fetch(path)
    except Exception as exc:  # noqa: BLE001
        check(False, f"{path}: request failed ({exc})")
        report["headers"].append({"path": path, "error": str(exc)})
        print(f"   FAIL {path:42} request failed: {exc}")
        continue
    xrt = headers.get("x-robots-tag")
    row = {"path": path, "status": status, "x_robots_tag": xrt, "bytes": len(body)}
    report["headers"].append(row)
    check(status == 200, f"{path}: status {status}")
    check(xrt is None, f"{path}: still carries X-Robots-Tag: {xrt}")
    print(f"   {'PASS' if status == 200 and xrt is None else 'FAIL'} {path:42} {status}  X-Robots-Tag={xrt!r}")

# --------------------------------------------------------------- 2. dist scan
print("\n2. dist/ — zero occurrences of noindex")
scanned = 0
hits: list[tuple[str, int]] = []
for dirpath, _dirnames, filenames in os.walk(DIST):
    for name in filenames:
        if not (name.endswith(".html") or name == "_headers"):
            continue
        p = Path(dirpath) / name
        text = p.read_text(encoding="utf-8", errors="replace")
        scanned += 1
        n = len(re.findall(r"noindex", text, re.I))
        if n:
            hits.append((str(p.relative_to(ROOT)), n))
total = sum(n for _, n in hits)
check(total == 0, f"dist: {total} noindex occurrence(s) in {len(hits)} file(s)")
print(f"   files scanned {scanned}, occurrences {total}")
for p, n in hits:
    print(f"   FAIL {p}  x{n}")
report["dist"] = {"files": scanned, "noindex": total, "hits": hits}

# ----------------------------------------------------------------- 3. robots
print("\n3. robots.txt")
try:
    st, _h, body = fetch("/robots.txt")
    robots = body.decode("utf-8", errors="replace")
except Exception as exc:  # noqa: BLE001
    robots = ""
    print(f"   FAIL could not fetch robots.txt: {exc}")
    check(False, "robots.txt unreachable")
site_wide = re.search(r"(?im)^\s*Disallow:\s*/\s*$", robots)
check(site_wide is None, "robots.txt: site-wide Disallow: / present")
check(
    f"Sitemap: https://{HOST}/sitemap.xml" in robots or "Sitemap: https://apocalab.com/sitemap.xml" in robots,
    "robots.txt: sitemap does not point at the apex",
)
print(f"   site-wide Disallow: {bool(site_wide)}")
for line in robots.strip().splitlines():
    print(f"   | {line}")
report["robots"] = robots

# ------------------------------------------------- 4. canonical + sitemap locs
print("\n4. canonical and sitemap")
canon: list[tuple[str, str | None]] = []
for p in sorted(DIST.rglob("*.html")):
    text = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<link rel="canonical" href="([^"]*)"', text)
    canon.append((str(p.relative_to(ROOT)), m.group(1) if m else None))
for rel, href in canon:
    if rel.endswith("404.html"):
        check(href is None, f"404.html carries a canonical: {href}")
        print(f"   {rel:46} canonical={href} (none by design)")
        continue
    ok = href is not None and href.startswith("https://apocalab.com/")
    check(ok, f"{rel}: canonical is {href!r}")
    print(f"   {'PASS' if ok else 'FAIL'} {rel:46} {href}")

locs: list[str] = []
try:
    _st, _h, body = fetch("/sitemap.xml")
    locs = re.findall(r"<loc>(.*?)</loc>", body.decode("utf-8", errors="replace"))
except Exception as exc:  # noqa: BLE001
    print(f"   FAIL could not fetch sitemap.xml: {exc}")
check(len(locs) == 10, f"sitemap: {len(locs)} locs, expected 10")
check(all(l.startswith("https://apocalab.com/") for l in locs), "sitemap: a loc is not on the apex")
print(f"   sitemap locs: {len(locs)}")
for l in locs:
    print(f"   | {l}")
report["canonical"] = canon
report["sitemap"] = locs

# ------------------------------------------------------------------- verdict
report["passes"] = passes
report["fails"] = fails
(ROOT / "live-gate.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n结果：PASS {passes}  FAIL {len(fails)}")
for f in fails:
    print(f"  FAIL {f}")
sys.exit(1 if fails else 0)
