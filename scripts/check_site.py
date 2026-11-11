# -*- coding: utf-8 -*-
"""
阶段 1 构建闸门。/blast-radius/ 的四条上线标准（plan §4.2）在这里逐条判定。

G-a 关 JS 能读完整表   —— 24 个值全部是静态文本；无可执行 <script>
G-b 每格带印刷页码     —— p. 115 / p. 291 / p. 70 / p. 71 出现次数不低于格子数
G-c 5 psi 每行带插值   —— "interpolated between 4 and 6 psi contours" ≥ 6
G-d 1 Mt 带爆高边界    —— "5,000 ft" 与 "10,174 ft" 出现在同一段落内

另外三条全站约束：免责恰一行、禁词（词边界）、无占位残渣。

用法：python scripts/check_site.py     （先跑 astro build）
"""
import html
import itertools
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
JSON_PATH = ROOT / "src" / "data" / "effects.json"

fails = []
passes = 0


def check(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        fails.append(msg)
        print(f"  FAIL  {msg}")


def text_of(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = html.unescape(h).replace("\xa0", " ")
    return re.sub(r"\s+", " ", h)


def paragraphs(h):
    return [text_of(p) for p in re.split(r"(?i)</p>", h)]


def citation_line(e):
    """Mirror of citationLine() in src/lib/effects.ts."""
    c = e["citation"]
    if c.get("figure"):
        return f"Ch. {c['chapter']} · Fig. {c['figure']} · p. {c['page']}"
    eq = c.get("equation") or ""
    label = f"Eq. {eq}" if eq.startswith("(") else (eq or "Eq.")
    return f"{label} · p. {c['page']}"


PAGES = {
    "index": DIST / "index.html",
    "blast-radius": DIST / "blast-radius" / "index.html",
    "nuclear-bomb-map": DIST / "nuclear-bomb-map" / "index.html",
    "methodology": DIST / "methodology" / "index.html",
}

# The one address each page is allowed to claim as its own. Written out in full
# rather than derived, so a change in astro.config.mjs cannot silently pass.
CANONICAL = {
    "index": "https://apocalab.com/",
    "blast-radius": "https://apocalab.com/blast-radius/",
    "nuclear-bomb-map": "https://apocalab.com/nuclear-bomb-map/",
    "methodology": "https://apocalab.com/methodology/",
}

print("0 产物存在")
for name, p in PAGES.items():
    check(p.exists(), f"{name}: {p.relative_to(ROOT)} 存在")

if fails:
    print("\n构建产物缺失，先跑 astro build。")
    sys.exit(1)

raw = {k: p.read_text(encoding="utf-8") for k, p in PAGES.items()}
txt = {k: text_of(v) for k, v in raw.items()}

data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
entries = data["entries"]

# ---------------------------------------------------------------- 全站约束
print("1 全站约束")

DISCLAIMER = "Not a prediction for any specific event."
for name, body in txt.items():
    check(body.count(DISCLAIMER) == 1, f"{name}: 免责句恰出现 1 次（实际 {body.count(DISCLAIMER)}）")

# 标题与描述的长度：超过 ~158 字符的 description 在结果页会被截断，等于白写
for name, body in raw.items():
    mt = re.search(r"(?is)<title>(.*?)</title>", body)
    md = re.search(r'(?is)<meta name="description" content="(.*?)"', body)
    mh = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", body)
    check(mt is not None, f"{name}: 有 <title>")
    check(md is not None, f"{name}: 有 meta description")
    check(mh is not None, f"{name}: 有 <h1>")
    if mt:
        t = text_of(mt.group(1))
        check(len(t) <= 65, f"{name}: title 长度 {len(t)} ≤ 65")
    if md:
        d = text_of(md.group(1))
        check(len(d) <= 158, f"{name}: description 长度 {len(d)} ≤ 158")
        check(len(d) >= 110, f"{name}: description 长度 {len(d)} ≥ 110（别写太薄）")
    if mt and mh:
        check(text_of(mt.group(1)) != text_of(mh.group(1)), f"{name}: title 与 H1 不同")

BANNED = [    (r"\bdemo\b", "demo"),
    (r"\bprototype\b", "prototype"),
    (r"education\s+demo", "education demo"),
    (r"simulation\s+model", "simulation model"),
    (r"our\s+estimate", "our estimate"),
]
for name, body in txt.items():
    low = body.lower()
    for pat, label in BANNED:
        check(not re.search(pat, low), f"{name}: 无禁词 “{label}”")

RESIDUE = ["lorem", "ipsum", "TODO", "FIXME", "undefined", "[object Object]"]
for name, body in raw.items():
    for token in RESIDUE:
        check(token not in body, f"{name}: 无占位残渣 “{token}”")

# 免责必须在 <footer> 里，且 footer 只有一个 <p>
for name, body in raw.items():
    m = re.search(r"(?is)<footer\b.*?</footer>", body)
    check(m is not None, f"{name}: 有 footer 元素")
    if m:
        check(m.group(0).count("<p") == 1, f"{name}: footer 内恰一个 <p>")

# ---------------------------------------------------------------- G-a
print("2 G-a 关 JS 读得到完整表")
br = raw["blast-radius"]

scripts = re.findall(r"(?is)<script\b[^>]*>", br)
executable = [s for s in scripts if "application/ld+json" not in s]
check(not executable, f"blast-radius: 无可执行 <script>（发现 {len(executable)} 个：{executable[:2]}）")
check(len(scripts) == 1, f"blast-radius: 只有 1 个 <script>，且是 JSON-LD（实际 {len(scripts)}）")

brtxt = txt["blast-radius"]
for e in entries:
    v = f"{e['radius_km']:.2f} km"
    check(v in brtxt, f"blast-radius: {e['id']} 的值 “{v}” 是静态文本")

check("<table" in br and br.count("<table") >= 3, "blast-radius: 至少 3 张语义化表格")
check(br.count("<script") == br.count("application/ld+json"), "blast-radius: 没有内联脚本")

# ---------------------------------------------------------------- G-b
print("3 G-b 每格带印刷页码")
counts = {
    "p. 115": (brtxt.count("p. 115"), 12),   # 5 psi + 1 psi，空爆 3 + 地爆 3，各两行
    "p. 291": (brtxt.count("p. 291"), 6),    # 热辐射 6 格
    "p. 70": (brtxt.count("p. 70"), 3),      # 空爆火球 3 格
    "p. 71": (brtxt.count("p. 71"), 3),      # 地爆火球 3 格
}
for label, (got, want) in counts.items():
    check(got >= want, f"blast-radius: “{label}” 出现 {got} 次（要求 ≥ {want}）")

# ---------------------------------------------------------------- G-c
print("4 G-c 5 psi 插值标注")
n_interp = brtxt.count("interpolated between 4 and 6 psi contours")
check(n_interp >= 6, f"blast-radius: 插值句出现 {n_interp} 次（要求 ≥ 6）")
for ft in ("2,275 ft", "1,361 ft"):
    check(ft in brtxt, f"blast-radius: 插值位置写明 {ft}")

# ---------------------------------------------------------------- G-d
print("5 G-d 1 Mt 爆高边界")
hit = [p for p in paragraphs(br) if "5,000 ft" in p and "10,174 ft" in p]
check(bool(hit), "blast-radius: “5,000 ft” 与 “10,174 ft” 在同一段落内")
if hit:
    check("15,750 ft" in hit[0], "该段落同时给出 1 psi 的 15,750 ft")
    check("3.61" in hit[0], "该段落点明仍按 §3.61 缩放")

mb = txt["methodology"]
check("5,000 ft" in mb, "methodology: 写明 5,000 ft 假设边界")
check("10,174 ft" in mb and "15,750 ft" in mb, "methodology: 给出两档越界爆高")
check("read as an upper bound" in mb or "edge of what this chart supports" in mb,
      "methodology: 说明该档应读作上限/边界值")

# ---------------------------------------------------------------- 其余硬要求
print("6 热辐射标定与地爆口径")
check("no text layer" in brtxt or "no text layer" in mb, "methodology: 写明 Fig. 7.42 扫描件无文字层")
check("12.66" in mb and "7.43" in mb, "methodology: 标定依据引用 §12.66 与 §7.43")
check("4.5, 6, 8, 10, 15, 25" in mb, "methodology: 给出自外向内的等值线次序")
check("deliberately absent" in brtxt, "blast-radius: 明写地爆不给热辐射")
check("read directly off Fig. 7.42, not scaled" in brtxt, "blast-radius: 热辐射标注为直读")
check(brtxt.count("read directly off Fig. 7.42, not scaled") >= 6, "blast-radius: 6 个热辐射格全标直读")
check("scaled from the 1 kt curve (§3.61, p.101)" in brtxt, "blast-radius: 缩放标签原文")
check(brtxt.count("scaled from the 1 kt curve (§3.61, p.101)") >= 12,
      "blast-radius: 12 个缩放格全带标签")
check("contact burst" in brtxt, "blast-radius: 地爆口径写明")
check("2.127.2" in brtxt, "blast-radius: 地爆火球引用式 (2.127.2)，未与空爆混搭")

print("7 阶段 2 首页默认态（SSR）")
idx = raw["index"]
idxtxt = txt["index"]
check("New York" in idxtxt, "index: 默认城市 New York 出现在静态文本里")
check("100 kt" in idxtxt, "index: 默认当量 100 kt 出现在静态文本里")
check("Air burst" in idxtxt, "index: 默认爆型 Air burst 出现在静态文本里")
for km in ("0.21", "3.22", "9.93", "6.99", "4.02"):
    check(re.search(rf"{re.escape(km)}\s*km", idxtxt) is not None,
          f"index: 默认态 {km} km 是静态文本")
check(idxtxt.count("p. 115") >= 2, "index: 5 psi 与 1 psi 两行各带 p. 115")
check(idxtxt.count("p. 291") >= 2, "index: 两行热辐射各带 p. 291")
check("p. 70" in idxtxt, "index: 火球带 p. 70")
check("ring centre" in idxtxt, "index: 写明 ring centre")

print("8 阶段 2 数据岛（JSON）")
m = re.search(r'(?is)<script type="application/json" id="apoca-island">(.*?)</script>', idx)
check(m is not None, "index: 存在 id=apoca-island 的 JSON 岛")
island = json.loads(m.group(1)) if m else {}
check(island.get("default") == {"city": "new-york", "yield": 100, "burst": "air"},
      f"index: 岛内默认态是 New York/100/air（实际 {island.get('default')}）")
check(len(island.get("cities", [])) == 20, f"index: 岛内含 20 个城市（实际 {len(island.get('cities', []))}）")
check(island.get("yields") == [15, 100, 1000], "index: 岛内含三档当量")

by_key = {(e["effect"], e["burst"], e["yield_kt"]): e for e in entries}
for burst in ("air", "ground"):
    for y in (15, 100, 1000):
        rows = island.get("combos", {}).get(burst, {}).get(str(y))
        check(rows is not None and len(rows) == 5, f"index: 岛内 combos.{burst}.{y} 有 5 行")
        if not rows:
            continue
        for row in rows:
            e = by_key.get((row["id"], burst, y))
            if row["absent"]:
                check(e is None, f"index: {burst}/{y}/{row['id']} 标 absent 时确实没有数据")
                continue
            check(e is not None, f"index: {burst}/{y}/{row['id']} 在 effects.json 中存在")
            if not e:
                continue
            check(row["km"] == f"{e['radius_km']:.2f}",
                  f"index: 岛内 {burst}/{y}/{row['id']} 的 km 与 JSON 一致（{row['km']} vs {e['radius_km']:.2f}）")
            check(row["src"] == citation_line(e),
                  f"index: 岛内 {burst}/{y}/{row['id']} 的出处与 JSON 一致")
            check(bool(row["tags"]), f"index: {burst}/{y}/{row['id']} 至少一个口径标签")
            check(abs(row["r"] - e["radius_km"]) < 1e-9,
                  f"index: 岛内 {burst}/{y}/{row['id']} 的环半径 = km")

check(len(island.get("scales", {})) == 6, "index: 岛内 6 组绘图比例")
check(len(island.get("bars", {})) == 6, "index: 岛内 6 组比例尺")

print("9 阶段 2 脚本与 URL 状态")
scripts = re.findall(r"(?is)<script\b[^>]*>", idx)
executable = [s for s in scripts if "application/ld+json" not in s and "application/json" not in s]
check(len(executable) == 1, f"index: 恰 1 个可执行 script（实际 {len(executable)}）")
check(all("src=" not in s for s in executable), "index: 没有外链脚本，无额外请求")
check(len(scripts) == 3, f"index: 共 3 个 script（FAQ JSON-LD + 数据岛 + 内联脚本），实际 {len(scripts)}")
check(not re.search(r"\bfetch\s*\(|XMLHttpRequest", idx), "index: 脚本里没有网络请求")
for token in ("URLSearchParams", "replaceState", "city", "yield", "burst"):
    check(token in idx, f"index: 脚本处理 URL 状态（含 {token}）")
for name in ('name="city"', 'name="yield"', 'name="burst"'):
    check(name in idx, f"index: 控件有 {name}")
check("no-js" not in idx, "index: 没有残留的 no-js 分支")

print("10 阶段 2 关 JS 回退")
check("class=\"fallback\"" in idx, "index: 有关 JS 回退段落")
cands = list((DIST / "_astro").glob("*.css"))
check(bool(cands), "dist: 有构建后的 CSS")
if cands:
    css = " ".join(p.read_text(encoding="utf-8") for p in cands)
    check(".js .controls" in css, "CSS: 控件默认隐藏、脚本运行后才显示")
    check(".js .fallback" in css, "CSS: 回退段落在脚本运行后隐藏")

print("11 阶段 2 不承诺尚未上线的功能")
head_txt = " ".join([
    re.search(r"(?is)<title>(.*?)</title>", idx).group(1),
    re.search(r'(?is)<meta name="description" content="(.*?)"', idx).group(1),
    re.search(r"(?is)<h1[^>]*>(.*?)</h1>", idx).group(1),
])
head_plain = text_of(head_txt).lower()
check("population" not in head_plain,
      "index: title/description/h1 不出现 population（人口层还没上线）")

print("12 canonical 绝对地址")
for name, body in raw.items():
    links = re.findall(r'(?is)<link\s+rel="canonical"\s+href="([^"]+)"', body)
    check(len(links) == 1, f"{name}: 恰一个 canonical（实际 {len(links)}）")
    if not links:
        continue
    url = links[0]
    check(url == CANONICAL[name], f"{name}: canonical 指向自己（{url}）")
    check(url.startswith("https://apocalab.com/"), f"{name}: canonical 是 https 绝对地址")
    check(url.endswith("/"), f"{name}: canonical 以斜杠结尾")
    check("?" not in url and "#" not in url, f"{name}: canonical 不含 query 或锚点")

print("13 sitemap 与 robots")
sm_path = DIST / "sitemap.xml"
check(sm_path.exists(), "dist/sitemap.xml 存在")
locs = []
if sm_path.exists():
    sm = sm_path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(sm)
        locs = [e.text.strip() for e in root.findall("s:url/s:loc", NS)]
        check(True, "sitemap: 是合法 XML")
    except Exception as exc:  # noqa: BLE001
        check(False, f"sitemap: 解析失败 {exc}")
    check(len(locs) == len(CANONICAL), f"sitemap: 列出 {len(locs)} 个 URL（页面数 {len(CANONICAL)}）")
    check(set(locs) == set(CANONICAL.values()), "sitemap: 与被构建的页面集合一致（不多不少）")
    for loc in locs:
        check(
            loc.startswith("https://apocalab.com/") and loc.endswith("/"),
            f"sitemap: {loc} 是 https 绝对地址且带斜杠",
        )
        rel = loc[len("https://apocalab.com/"):]
        target = (DIST / rel / "index.html") if rel else (DIST / "index.html")
        check(target.exists(), f"sitemap: {loc} 解析到构建产物（静态托管即 200）")

rob_path = DIST / "robots.txt"
check(rob_path.exists(), "dist/robots.txt 存在")
if rob_path.exists():
    lines = [ln.strip() for ln in rob_path.read_text(encoding="utf-8").strip().splitlines()]
    check(
        lines == ["User-agent: *", "Allow: /", "Sitemap: https://apocalab.com/sitemap.xml"],
        f"robots.txt: 恰三行且内容正确（实际 {lines}）",
    )

print("14 四页标题不互相抢词")
title_map = {}
for name, body in raw.items():
    m = re.search(r"(?is)<title>(.*?)</title>", body)
    title_map[name] = text_of(m.group(1)).lower() if m else ""


def common_run(a, b):
    """Longest run of consecutive words present in both titles."""
    A = re.findall(r"[a-z0-9.]+", a)
    B = re.findall(r"[a-z0-9.]+", b)
    for n in range(min(len(A), len(B)), 1, -1):
        sa = {" ".join(A[i:i + n]) for i in range(len(A) - n + 1)}
        sb = {" ".join(B[i:i + n]) for i in range(len(B) - n + 1)}
        hit = sa & sb
        if hit:
            return n, sorted(hit)[0]
    return 0, ""


check("blast radius" not in title_map.get("index", "x"), "index: title 不出现 blast radius")
check("nuke simulator" in title_map.get("index", ""), "index: title 的主词是 nuke simulator")
check("nuclear bomb blast radius" in title_map.get("blast-radius", ""),
      "blast-radius: title 的主词是 nuclear bomb blast radius")
for a, b in itertools.combinations(sorted(title_map), 2):
    n, s = common_run(title_map[a], title_map[b])
    check(n <= 3, f"title {a} 与 {b} 最长共同词串 {n} 词（“{s}”），要求 ≤ 3")

print("15 地图页（/nuclear-bomb-map/）")
mp = raw["nuclear-bomb-map"]
mt = txt["nuclear-bomb-map"]
check('id="map-rings"' in mp, "map: 自绘半径圈 canvas 存在")
check('id="map-fallback"' in mp, "map: 备用轮廓 canvas 存在")
check('id="map-frame"' in mp and 'data-mode="pending"' in mp, "map: frame 带 data-mode 供断言")
check(mp.count('class="map-ro"') == 5, f"map: 读数列 5 行（实际 {mp.count('class=\"map-ro\"')}）")
check("OpenFreeMap" in mt and "OpenStreetMap" in mt, "map: 底图署名")
check("Natural Earth" in mt, "map: 备用轮廓署名（公有领域）")

for eff in ("fireball", "overpressure_5psi", "overpressure_1psi", "thermal_2nd", "thermal_3rd"):
    e = next(x for x in entries if x["effect"] == eff and x["burst"] == "air" and x["yield_kt"] == 100)
    check(f"{e['radius_km']:.2f}" in mt, f"map: 默认态 {eff} 的 {e['radius_km']:.2f} km 是静态文本")
    check(citation_line(e) in mt, f"map: 默认态 {eff} 带出处 {citation_line(e)}")

m2 = re.search(r'(?is)<script type="application/json" id="apoca-map-island">(.*?)</script>', mp)
check(m2 is not None, "map: 存在 apoca-map-island")
island2 = json.loads(m2.group(1)) if m2 else {}
mcities = island2.get("cities", [])
check(len(mcities) == 20, f"map: 岛内含 20 个城市（实际 {len(mcities)}）")
check(all("lat" in c and "lon" in c for c in mcities), "map: 岛内城市带经纬度")
for burst in ("air", "ground"):
    for y in (15, 100, 1000):
        rows = island2.get("combos", {}).get(burst, {}).get(str(y))
        check(rows is not None and len(rows) == 5, f"map: 岛内 combos.{burst}.{y} 有 5 行")
        for row in rows or []:
            e = by_key.get((row["id"], burst, y))
            if row["absent"]:
                check(e is None, f"map: {burst}/{y}/{row['id']} 标 absent 时确实没有数据")
                continue
            check(e is not None, f"map: {burst}/{y}/{row['id']} 在 effects.json 中存在")
            if e:
                check(row["km"] == f"{e['radius_km']:.2f}",
                      f"map: 岛内 {burst}/{y}/{row['id']} 的 km 与 JSON 一致")

mscripts = re.findall(r"(?is)<script\b[^>]*>", mp)
mods = [s for s in mscripts if 'type="module"' in s]
check(len(mods) == 1, f"map: 一个模块脚本（实际 {len(mods)}）")
check(not any("maplibre" in s for s in mscripts if "src=" in s),
      "map: MapLibre 不在 HTML 里静态引用（必须是运行时动态 import）")
for name in ("index", "blast-radius", "methodology"):
    check("maplibre" not in raw[name].lower(), f"{name}: 不加载地图库")
check("<svg" in raw["index"] and 'class="rings"' in raw["index"],
      "index: 首页的 SVG 真比例圆环保留，没有被地图替换")

chunks = sorted((DIST / "_astro").glob("BombMap*.js"))
check(bool(chunks), "dist: 有地图脚本 chunk")
if chunks:
    js = "".join(p.read_text(encoding="utf-8") for p in chunks)
    for token in ("dragRotate", "touchPitch", "pitchWithRotate", "maxPitch", "disableRotation"):
        check(token in js, f"map: 构建产物里带旋转/俯仰锁定 {token}")

print("16 Cloudflare Pages 产物契约")


def parse_headers(text):
    """_headers is: a path line at column 0, then indented headers, repeat."""
    out = []
    cur = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[:1].isspace():
            cur = {"path": raw.strip(), "headers": []}
            out.append(cur)
        elif cur is not None:
            cur["headers"].append(raw.strip())
    return out


hdr_path = DIST / "_headers"
check(hdr_path.exists(), "dist/_headers 存在（Pages 只认这个文件名）")
rules = []
if hdr_path.exists():
    hdr = hdr_path.read_text(encoding="utf-8")
    rules = parse_headers(hdr)
    check(bool(rules) and rules[0]["path"] == "/*", f"_headers 第一条规则作用于 /*（实际 {rules[:1]}）")
    if rules:
        check(
            any(h.lower().startswith("x-robots-tag:") and "noindex" in h.lower()
                for h in rules[0]["headers"]),
            "_headers 给全部预览页加 noindex",
        )
    check("disallow" not in hdr.lower(), "_headers 里不塞 robots 指令（那是 robots.txt 的活）")
    geo = next((r for r in rules if "geojson" in r["path"]), None)
    check(
        geo is not None
        and any(h.lower().startswith("content-type:") and "application/json" in h.lower()
                for h in geo["headers"]),
        "_headers 给 .geojson 指定 application/json（Pages 对未知扩展名默认 octet-stream）",
    )

cfg = (ROOT / "astro.config.mjs").read_text(encoding="utf-8")
check(not re.search(r"(?m)^\s*adapter\s*:", cfg), "astro.config.mjs 没有 adapter（纯静态，Pages 不跑函数）")
check("@astrojs/" not in cfg, "astro.config.mjs 不引任何 @astrojs/* 适配器包")
check("output: 'static'" in cfg or 'output: "static"' in cfg, "astro.config.mjs 是 output: 'static'")
check(not (DIST / "functions").exists(), "dist 里没有 functions/（预览环境不执行任何服务端代码）")

wr = ROOT / "wrangler.toml"
check(wr.exists(), "wrangler.toml 存在")
if wr.exists():
    check('pages_build_output_dir = "./dist"' in wr.read_text(encoding="utf-8"),
          "wrangler.toml 的 pages_build_output_dir 指向 dist")

print(f"结果：PASS {passes}  FAIL {len(fails)}")
if fails:
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("阶段 1 构建闸门全绿。")
