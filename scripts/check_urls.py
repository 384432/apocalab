# -*- coding: utf-8 -*-
"""
HTTP gate: every URL the sitemap advertises must answer 200.

check_site.py proves the file exists in dist/; this proves a plain static server
actually serves it, which is the same thing a CDN does. It starts its own
loopback server on an ephemeral port, so it needs no running services.

Also checks:
  - the served HTML's canonical equals the URL it was fetched from
  - robots.txt and sitemap.xml themselves answer 200
  - the Natural Earth fallback asset answers 200 (the degraded map path needs it)
  - a URL that does not exist answers 404 (so the 200s above are not a server
    that answers 200 to everything)

用法：python scripts/check_urls.py
"""
import http.server
import pathlib
import re
import sys
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

fails = []
passes = 0


def check(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        fails.append(msg)
        print(f"  FAIL  {msg}")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def log_message(self, *a):  # noqa: A003 - silence the access log
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"


def get(path):
    req = urllib.request.Request(base + path, headers={"User-Agent": "apocalab-gate/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


print("1 sitemap 里每个 URL")
sm = (DIST / "sitemap.xml").read_bytes()
locs = [e.text.strip() for e in ET.fromstring(sm).findall("s:url/s:loc", NS)]
check(bool(locs), "sitemap.xml 至少列出一个 URL")

for loc in locs:
    check(loc.startswith("https://apocalab.com"), f"{loc}: 是站点绝对地址")
    path = loc[len("https://apocalab.com"):] or "/"
    status, ctype, body = get(path)
    check(status == 200, f"{path}: HTTP {status}（要求 200）")
    check("text/html" in ctype, f"{path}: Content-Type 是 HTML（{ctype}）")
    heads = re.findall(r'(?is)<link\s+rel="canonical"\s+href="([^"]+)"', body.decode("utf-8", "ignore"))
    check(heads == [loc], f"{path}: 返回页面的 canonical 等于该 URL（{heads}）")
    check(len(body) > 4000, f"{path}: 响应体非空（{len(body)} bytes）")

print("2 站点级文件")
for path, kind in (("/robots.txt", "text/plain"), ("/sitemap.xml", "xml")):
    status, ctype, body = get(path)
    check(status == 200, f"{path}: HTTP {status}（要求 200）")
    check(kind in ctype, f"{path}: Content-Type 含 {kind}（{ctype}）")

print("3 降级路径需要的静态资源")
status, ctype, body = get("/ne_110m_land.geojson")
check(status == 200, f"/ne_110m_land.geojson: HTTP {status}（要求 200）")
# python's mimetypes has no .geojson entry, and neither does Cloudflare Pages:
# the real Content-Type comes from public/_headers, which check_site.py asserts.
# What matters here is that the bytes are served, not the label the test server
# happens to pick.
check(
    "json" in ctype or "octet-stream" in ctype,
    f"/ne_110m_land.geojson: Content-Type {ctype}（本地服务器无 .geojson 映射，属预期）",
)
check(body[:1] == b"{", f"/ne_110m_land.geojson: 响应体是 JSON 对象（首字节 {body[:1]!r}）")
check(len(body) > 80_000, f"/ne_110m_land.geojson: 体积 {len(body)} bytes（不是空壳）")

print("4 反向验证：不存在的路径必须 404")
status, _, _ = get("/this-page-does-not-exist/")
check(status == 404, f"不存在的路径返回 {status}（要求 404，否则上面的 200 不算数）")

srv.shutdown()
print(f"结果：PASS {passes}  FAIL {len(fails)}")
if fails:
    sys.exit(1)
print("HTTP 闸门全绿。")
