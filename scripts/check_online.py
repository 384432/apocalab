# -*- coding: utf-8 -*-
"""线上断言：把 check_site.py 里能在线验的那几条，在真实 HTTP 上再验一遍。

用法：
    python scripts/check_online.py https://apocalab.pages.dev --expect noindex      # SITE_LIVE=false 期间
    python scripts/check_online.py https://apocalab.pages.dev --expect indexed      # 域名上线之后

--expect indexed  → 不许有任何 X-Robots-Tag: noindex，HTML 里也不许有 meta robots noindex
--expect noindex  → 每个页面都必须带 X-Robots-Tag: noindex

期望值由 src/lib/site.ts 的 SITE_LIVE 决定，不由「这是不是生产地址」决定：
SITE_LIVE=false 时生产也必须 noindex，因为 canonical 指向的域名还没上线。

代理一律绕过：本机开着代理时，urllib 会把 pages.dev 也送进代理，验到的是代理的缓存。
"""
import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
CANON = "https://apocalab.com"
PAGES = [
    "/",
    "/blast-radius/",
    "/nuclear-bomb-map/",
    "/nuclear-bomb-map/new-york/",
    "/methodology/",
]

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

fails = []
passes = 0


def check(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        fails.append(msg)
        print("  FAIL ", msg)


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", "apocalab-check/1.0")
    try:
        with opener.open(req, timeout=45) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


ap = argparse.ArgumentParser()
ap.add_argument("base")
ap.add_argument("--expect", choices=["indexed", "noindex"], default="indexed")
args = ap.parse_args()
base = args.base.rstrip("/")

print(f"base={base}  expect={args.expect}")

print("1 四页可达 + canonical")
for path in PAGES:
    url = base + path
    status, hdr, body = fetch(url)
    check(status == 200, f"{path}: HTTP {status}")
    if status != 200:
        continue
    html = body.decode("utf-8", "replace")
    can = re.search(r'(?is)<link\s+rel="canonical"\s+href="([^"]+)"', html)
    check(can is not None, f"{path}: 有 canonical")
    if can:
        want = CANON + path
        check(can.group(1) == want, f"{path}: canonical 指向 {want}（实际 {can.group(1)}）")
        check("pages.dev" not in can.group(1), f"{path}: canonical 不含 pages.dev")

print("2 收录开关")
for path in PAGES:
    status, hdr, body = fetch(base + path)
    if status != 200:
        continue
    tag = " ".join(v for k, v in hdr.items() if k.lower() == "x-robots-tag")
    if args.expect == "noindex":
        check("noindex" in tag.lower(), f"{path}: 带 X-Robots-Tag: noindex（实际 {tag!r}）")
    else:
        check("noindex" not in tag.lower(), f"{path}: 没有 X-Robots-Tag: noindex（实际 {tag!r}）")
        check('name="robots"' not in body.decode("utf-8", "replace").lower(),
              f"{path}: HTML 里没有 meta robots")

print("3 sitemap / robots")
status, hdr, body = fetch(base + "/sitemap.xml")
check(status == 200, f"sitemap.xml: HTTP {status}")
locs = []
if status == 200:
    root = ET.fromstring(body.decode("utf-8"))
    locs = [e.text.strip() for e in root.findall("s:url/s:loc", NS)]
    check(len(locs) == len(PAGES), f"sitemap: {len(locs)} 条（页面 {len(PAGES)} 个）")
    check(set(locs) == {CANON + p for p in PAGES}, f"sitemap: 与四页一一对应（实际 {locs}）")

status, hdr, body = fetch(base + "/robots.txt")
check(status == 200, f"robots.txt: HTTP {status}")
if status == 200:
    lines = [x.strip() for x in body.decode("utf-8").strip().splitlines()]
    check(lines == ["User-agent: *", "Allow: /", "Sitemap: https://apocalab.com/sitemap.xml"],
          f"robots.txt: 三行内容正确（实际 {lines}）")

print("4 静态资源头")
status, hdr, body = fetch(base + "/ne_110m_land.geojson")
check(status == 200, f"geojson: HTTP {status}")
ctype = " ".join(v for k, v in hdr.items() if k.lower() == "content-type")
check("application/json" in ctype.lower(), f"geojson: Content-Type 是 json（实际 {ctype!r}）")
check(body[:1] == b"{", "geojson: 返回的是 JSON 而不是错误页")

print(f"结果：PASS {passes}  FAIL {len(fails)}")
sys.exit(1 if fails else 0)
