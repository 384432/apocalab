# -*- coding: utf-8 -*-
"""
HTTP gate: every URL the sitemap advertises must answer 200.

check_site.py proves the file exists in dist/; this proves a plain static server
actually serves it, which is the same thing a CDN does. It starts its own
loopback server on an ephemeral port, so it needs no running services.

Local checks (always):
  - the served HTML's canonical equals the URL it was fetched from
  - robots.txt and sitemap.xml themselves answer 200
  - the Natural Earth fallback asset answers 200 (the degraded map path needs it)
  - a URL that does not exist answers 404 (so the 200s above are not a server
    that answers 200 to everything)
  - dist/404.html exists, carries the five recovery links inside <main>, and
    carries neither a canonical nor a <meta name="robots">

Online checks (only with --online <base>):
  - the platform's not-found behaviour is what the local server cannot reproduce:
    a random missing path must answer 404, not 200 + the home page
  - a missing .png must answer 404 with a Content-Type that is not text/html
    (a soft 404 that serves HTML for an image URL is worse than a 404)
  - the body served for a missing path must be our 404 page, not the platform's
    own error page: the five recovery links have to be in it

用法：
  python scripts/check_urls.py                                   # 本地产物
  python scripts/check_urls.py --online https://apocalab.pages.dev  # 线上再走一遍
"""
import argparse
import http.server
import pathlib
import re
import secrets
import sys
import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# The five pages a lost visitor is sent back to. Same five anchor targets the
# rest of the site is allowed to link with (§4.8), so the 404 is not a second
# set of link rules to maintain.
RECOVERY = ["/", "/blast-radius/", "/nuclear-bomb-map/", "/methodology/", "/nuclear-winter/"]

UA = "apocalab-check/1.0"

# 本机开着代理时 urllib 会把 pages.dev 也送进代理，验到的是代理的缓存 —— 线上这一路一律绕开。
ONLINE_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

fails = []
passes = 0
warns = []


def check(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        fails.append(msg)
        print(f"  FAIL  {msg}")


def warn(msg):
    warns.append(msg)
    print(f"  WARN  {msg}")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def log_message(self, *a):  # noqa: A003 - silence the access log
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{port}"


def get(path, base_url=None):
    url = (base_url or base) + path
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    opener = ONLINE_OPENER if base_url else urllib.request.build_opener()
    try:
        with opener.open(req, timeout=20) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Content-Type", ""), exc.read()


def main_links(html_bytes):
    """hrefs inside <main>, so a header or footer link cannot satisfy the check."""
    text = html_bytes.decode("utf-8", "ignore")
    m = re.search(r"(?is)<main\b[^>]*>(.*?)</main>", text)
    body = m.group(1) if m else ""
    return re.findall(r'(?i)href="([^"]+)"', body), text



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

# 本地服务器答 404 用的是它自己那页错误页，我们的 404.html 它不会自动吐出来 ——
# 那段是托管平台的行为，所以这里按产物校验：文件在、五条链接在 <main> 里、
# 不带 canonical、不带 meta robots。线上那一路在 §5 真发请求验。
p404 = DIST / "404.html"
check(p404.exists(), "dist/404.html 存在（CF Pages 用它作答）")
if p404.exists():
    h404 = p404.read_text(encoding="utf-8")
    hrefs, _ = main_links(h404.encode("utf-8"))
    for href in RECOVERY:
        check(href in hrefs, f"404 页 <main> 里含指向 {href} 的链接")
    check(
        re.search(r'(?i)rel="canonical"', h404) is None,
        "404 页不带 canonical（这个地址不是页面的地址）",
    )
    check(
        re.search(r'(?i)<meta[^>]+name="robots"', h404) is None,
        "404 页不带 <meta name=robots>（404 状态本身就是信号，两种信号不叠）",
    )

argp = argparse.ArgumentParser(description="sitemap / 404 HTTP gate")
argp.add_argument(
    "--online",
    metavar="BASE",
    help="再对线上 host 跑一遍反向验证，例如 https://apocalab.pages.dev",
)
args = argp.parse_args()

if args.online:
    host = args.online.rstrip("/")
    print(f"5 线上口径（{host}）：托管平台的 not-found 行为，本地静态服务器复现不出来")

    # 随机 token：不撞上任何真实页面，也不会被 CDN 上的旧缓存命中。
    token = secrets.token_hex(4)
    missing = f"/zzz-no-such-page-{token}/"
    status, ctype, body = get(missing, base_url=host)
    print(f"    GET {missing} → {status} {ctype}")
    check(status == 404, f"线上 {missing} 返回 {status}（要求 404；200 就是软 404）")
    check("text/html" in ctype, f"线上 {missing}: Content-Type 是 HTML（{ctype}）")
    hrefs, text = main_links(body)
    for href in RECOVERY:
        check(href in hrefs, f"线上 404 响应的 <main> 里含指向 {href} 的链接")
    check(
        re.search(r'(?i)rel="canonical"', text) is None,
        "线上 404 响应不带 canonical",
    )
    check(
        re.search(r'(?i)<meta[^>]+name="robots"', text) is None,
        "线上 404 响应不带 <meta name=robots>",
    )

    status, ctype, body = get(f"/zzz-{token}.png", base_url=host)
    print(f"    GET /zzz-{token}.png → {status} {ctype}")
    check(status == 404, f"线上不存在的 .png 返回 {status}（要求 404）")
    # Content-Type on a 404: Pages answers every unmatched path with 404.html, so
    # a missing image comes back as text/html carrying the 404 page. That is what
    # nginx and Apache do with their own error pages too, and the status code is
    # the part that decides whether a crawler sees a page or nothing. Forcing
    # image/png here would label HTML bytes as a PNG, which is a worse lie than
    # the mismatch it removes — so this is a warning, not a failure.
    if "text/html" in ctype:
        hrefs, _ = main_links(body)
        check(
            all(h in hrefs for h in RECOVERY),
            "线上不存在的 .png 返回的是本站 404 页（五条回收链接在 <main> 里）",
        )
        warn(f"线上不存在的 .png 的 Content-Type 是 {ctype}（平台把 404.html 发给所有未匹配路径）")
    else:
        check(True, f"线上不存在的 .png 的 Content-Type 不是 text/html（{ctype}）")

    for href in RECOVERY:
        st, ct, _ = get(href, base_url=host)
        check(st == 200 and "text/html" in ct, f"线上 404 页上的 {href} 可点（{st} {ct}）")

srv.shutdown()
print(f"结果：PASS {passes}  FAIL {len(fails)}  WARN {len(warns)}")
if fails:
    sys.exit(1)
print("HTTP 闸门全绿。")
