# -*- coding: utf-8 -*-
"""
阶段 1 构建闸门。/blast-radius/ 的四条上线标准（plan §4.2）在这里逐条判定。

G-a 关 JS 能读完整表   —— 24 个值全部是静态文本；无可执行 <script>
G-b 每格带印刷页码     —— p. 115 / p. 291 / p. 70 / p. 71 出现次数不低于格子数
G-c 5 psi 每行带插值   —— "interpolated between 4 and 6 psi contours" ≥ 6
G-d 1 Mt 带爆高边界    —— "5,000 ft" 与 "10,174 ft" 出现在同一段落内

另外三条全站约束：免责恰一行、禁词（词边界）、无占位残渣。

阶段 3 追加：
16  _headers 按 CF_PAGES_BRANCH 条件生成 —— 生产（main）整份产物不许出现 noindex，
    预览必须带 X-Robots-Tag: noindex；两种模式各自反向断言一次。
17  内链四页闭环 —— 出链恰好覆盖其余三页、入链 ≥ 2、锚文本固定、全部落在正文 <p> 里。
18  地图页正文 —— ≥ 700 词、4–6 个 H2、每节都有具体数字与印刷页码。
19  承诺台账 —— title 里的 “N Cities” 必须在 plan.md 的 PROMISE-LEDGER 里有一条带到期日的行，
    过期未兑现即失败。

用法：python scripts/check_site.py [--expect main|preview] [--branch main]
     不带参数时按环境变量 CF_PAGES_BRANCH 推断，未设置即按预览产物验收。
"""
import datetime
import html
import itertools
import json
import os
import pathlib
import re
import sys
import urllib.parse
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


CITY_SLUGS = ["new-york", "los-angeles", "london", "tokyo", "paris"]
# 闭环是这四页之间的契约；城市页是从地图页分出去的叶子，只汇入、不参与闭环。
CORE = ["index", "blast-radius", "nuclear-bomb-map", "methodology"]
# 城市页（模板复制）走唯一性断言；其余非核心页走各自的小节断言。
CITY = CITY_SLUGS

PAGES = {
    "index": DIST / "index.html",
    "blast-radius": DIST / "blast-radius" / "index.html",
    "nuclear-bomb-map": DIST / "nuclear-bomb-map" / "index.html",
    "methodology": DIST / "methodology" / "index.html",
    "nuclear-winter": DIST / "nuclear-winter" / "index.html",
    # City pages are published by slug (PUBLISHED_CITY_SLUGS in src/lib/cities.ts).
    # Each one added here must also be added to CANONICAL and to sitemap
    # expectations, or section 13 fails.
    **{s: DIST / "nuclear-bomb-map" / s / "index.html" for s in CITY_SLUGS},
}

# The one address each page is allowed to claim as its own. Written out in full
# rather than derived, so a change in astro.config.mjs cannot silently pass.
CANONICAL = {
    "index": "https://apocalab.com/",
    "blast-radius": "https://apocalab.com/blast-radius/",
    "nuclear-bomb-map": "https://apocalab.com/nuclear-bomb-map/",
    "methodology": "https://apocalab.com/methodology/",
    "nuclear-winter": "https://apocalab.com/nuclear-winter/",
    **{s: f"https://apocalab.com/nuclear-bomb-map/{s}/" for s in CITY_SLUGS},
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
# 闭环四页之间不许抢词。
CORE_TITLES = {
    n: title_map[n]
    for n in ("index", "blast-radius", "nuclear-bomb-map", "methodology")
    if n in title_map
}
for a, b in itertools.combinations(sorted(CORE_TITLES), 2):
    n, s = common_run(CORE_TITLES[a], CORE_TITLES[b])
    check(n <= 3, f"title {a} 与 {b} 最长共同词串 {n} 词（“{s}”），要求 ≤ 3")

# 城市页是一个模板复制出来的，彼此必然共用「Nuclear Bomb Effects on」这类骨架，
# 所以它们之间不比词串 —— 比的是唯一性：标题里有没有这个城市名，以及有没有两页
# 输出了一模一样的标题。对核心页仍然按 ≤3 词要求。
city_raw = json.loads((ROOT / "src" / "data" / "cities.json").read_text(encoding="utf-8"))["cities"]
name_of = {c["slug"]: c["name"].lower() for c in city_raw}
city_titles = {n: t for n, t in title_map.items() if n in CITY}
check(len(set(city_titles.values())) == len(city_titles),
      f"城市页 title 互不重复（{len(city_titles)} 页，{len(set(city_titles.values()))} 个不同标题）")
for n, t in city_titles.items():
    city_name = name_of.get(n, n.replace("-", " "))
    check(city_name in t, f"{n}: title 里出现城市名 “{city_name}”")
    # 城市名是这些页面唯一合法的差异来源，所以比对时先把它摘掉：
    # 摘掉之后剩下的骨架不许和核心页共用超过 3 个连续词。
    # 现在剩下的是 ": 15 kt to 1 mt"，与 /blast-radius/ 的 "15 kt, 100 kt, 1 mt"
    # 只共用 2 个词；再往这边加词就会撞上，撞上就改模板，不要改这条断言。
    stripped = t.replace(city_name, " ")
    for core, ct in CORE_TITLES.items():
        run, frag = common_run(stripped, ct)
        check(run <= 3, f"title {n} 去掉城市名后与 {core} 最长共同词串 {run} 词（“{frag}”），要求 ≤ 3")
        full, ffrag = common_run(t, ct)
        check(full <= 4, f"title {n} 与 {core} 最长共同词串 {full} 词（“{ffrag}”），要求 ≤ 4（城市名占 1 词）")

# 查询页是独立成篇的内容页，和核心页也要错开词，但不必互相比较骨架。
for q in [n for n in title_map if n in CANONICAL and n not in CORE and n not in CITY]:
    for core, ct in CORE_TITLES.items():
        run, frag = common_run(title_map[q], ct)
        check(run <= 3, f"title {q} 与 {core} 最长共同词串 {run} 词（“{frag}”），要求 ≤ 3")

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

print("16 Cloudflare Pages 产物契约（noindex 条件生效）")


def arg_value(flag, default=None):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


# Which artifact is on the floor. Default comes from the same variable the
# generator used, so a production build checked without flags still fails
# loudly instead of being read as a preview.
BRANCH = arg_value("--branch", os.environ.get("CF_PAGES_BRANCH", "") or "")
EXPECT = arg_value("--expect", "main" if BRANCH == "main" else "preview")
check(EXPECT in ("main", "preview"), f"--expect 只能是 main 或 preview（实际 {EXPECT!r}）")
print(f"     产物模式：{EXPECT}（CF_PAGES_BRANCH={BRANCH or 'unset'}）")


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


# ---- SITE_LIVE：唯一开关，从 site.ts 读，不在这里写 ----------------
# 这里必须读「真值来源」，而不是自己假设。断言的目的不是证明某个模式存在，
# 而是证明产物和那一个布尔值一致 —— 上线当天只改 site.ts，闸门自动跟着变。
site_src = (ROOT / "src" / "lib" / "site.ts").read_text(encoding="utf-8")
live_decls = re.findall(
    r"export const SITE_LIVE\s*(?::\s*boolean\s*)?=\s*(true|false)\s*;", site_src
)
check(len(live_decls) == 1,
      f"site.ts 里 SITE_LIVE 恰好声明一次（实际 {len(live_decls)} 次）")
SITE_LIVE = (live_decls[0] == "true") if live_decls else False

gen_src = (ROOT / "scripts" / "gen_headers.mjs").read_text(encoding="utf-8")
check("readSiteLive" in gen_src and "site.ts" in gen_src,
      "gen_headers.mjs 从 src/lib/site.ts 读 SITE_LIVE")
check(not re.search(r"(?m)^\s*export const SITE_LIVE", gen_src),
      "gen_headers.mjs 不自己定义 SITE_LIVE（唯一定义在 site.ts）")

# One source of truth: the generator. A leftover static copy in public/ would be
# copied over dist/ and silently win on a platform that copies public/ last.
check(not (ROOT / "public" / "_headers").exists(),
      "public/_headers 不存在（唯一来源是 scripts/gen_headers.mjs）")
check((ROOT / "scripts" / "gen_headers.mjs").exists(), "scripts/gen_headers.mjs 存在")
cfg_src = (ROOT / "astro.config.mjs").read_text(encoding="utf-8")
check("writeHeaders" in cfg_src and "astro:build:done" in cfg_src,
      "astro.config.mjs 在 astro:build:done 里生成 _headers")

# 期望模式由两件事决定：SITE_LIVE 与「这次是哪个分支构建的」。
if not SITE_LIVE:
    EXPECTED_MODE = "staged"          # 域名没上线：生产和预览都不许收录
else:
    EXPECTED_MODE = "production" if EXPECT == "main" else "preview"
EXPECT_NOINDEX = EXPECTED_MODE != "production"
print(f"     SITE_LIVE={SITE_LIVE}  产物模式={EXPECTED_MODE}  noindex={EXPECT_NOINDEX}")

hdr_path = DIST / "_headers"
check(hdr_path.exists(), "dist/_headers 存在（Pages 只认这个文件名）")
rules = []
if hdr_path.exists():
    hdr = hdr_path.read_text(encoding="utf-8")
    hdr_low = hdr.lower()
    rules = parse_headers(hdr)
    check(bool(rules), "_headers 至少一条规则")
    check("disallow" not in hdr_low, "_headers 里不塞 robots 指令（那是 robots.txt 的活）")

    # 生成器把决定写进了产物本身，所以产物可以自证是哪种模式。
    m_mode = re.search(r"(?m)^#\s*mode:\s*(\S+)\s*$", hdr)
    check(m_mode is not None and m_mode.group(1) == EXPECTED_MODE,
          f"_headers 自报模式 {EXPECTED_MODE}（实际 {m_mode.group(1) if m_mode else None}）")
    m_live = re.search(r"(?m)^#\s*site-live:\s*(true|false)\s*$", hdr)
    check(m_live is not None and (m_live.group(1) == "true") == SITE_LIVE,
          f"_headers 自报 site-live={str(SITE_LIVE).lower()}（实际 {m_live.group(1) if m_live else None}）")

    geo = next((r for r in rules if "geojson" in r["path"]), None)
    check(
        geo is not None
        and any(h.lower().startswith("content-type:") and "application/json" in h.lower()
                for h in geo["headers"]),
        "_headers 给 .geojson 指定 application/json（Pages 对未知扩展名默认 octet-stream）",
    )

    if EXPECT_NOINDEX:
        check(rules[0]["path"] == "/*", f"noindex 模式第一条规则作用于 /*（实际 {rules[:1]}）")
        if rules:
            check(
                any(h.lower().startswith("x-robots-tag:") and "noindex" in h.lower()
                    for h in rules[0]["headers"]),
                f"{EXPECTED_MODE} 构建给全部页面加 X-Robots-Tag: noindex",
            )
    else:
        # 生产：整份 _headers 不许出现 noindex，连注释里也不许。
        check("noindex" not in hdr_low, "生产构建的 _headers 不含 noindex 字样")
        check("x-robots-tag" not in hdr_low, "生产构建的 _headers 不写 X-Robots-Tag")
        check(not any(r["path"] == "/*" and r["headers"] for r in rules),
              "生产构建没有作用于 /* 的头规则")

# HTML 侧：收录开关只有 _headers 一条路。谁把 <meta name="robots" content="noindex">
# 写进模板，两种模式都会翻车 —— 生产多一条隐形 noindex，或预览以为有头其实没生效。
htmls = sorted(DIST.rglob("*.html"))
check(len(htmls) >= len(PAGES), f"dist 里有 {len(htmls)} 个 HTML（页面 {len(PAGES)} 个）")
meta_robots = [
    p.relative_to(DIST).as_posix()
    for p in htmls
    if re.search(r'name="robots"', p.read_text(encoding="utf-8", errors="replace"), re.I)
]
check(not meta_robots, f"没有页面用 meta robots（命中 {meta_robots[:3]}）")
if not EXPECT_NOINDEX:
    dirty = [
        p.relative_to(DIST).as_posix()
        for p in htmls
        if "noindex" in p.read_text(encoding="utf-8", errors="replace").lower()
    ]
    check(not dirty, f"生产产物 HTML 里没有 noindex（命中 {dirty[:3]}）")
else:
    check(len(htmls) >= 4, "预览产物四页齐全")

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

print("17 内链：四页闭环 + 城市页汇入")

# 锚文本固定。改这里就是改契约，所以要连 plan §4 一起改。
ANCHOR = {
    "/": "nuke simulator",
    "/blast-radius/": "nuclear bomb blast radius",
    "/nuclear-bomb-map/": "nuclear bomb map",
    "/methodology/": "where these numbers come from",
}
PAGE_PATH = {
    "index": "/",
    "blast-radius": "/blast-radius/",
    "nuclear-bomb-map": "/nuclear-bomb-map/",
    "methodology": "/methodology/",
    "nuclear-winter": "/nuclear-winter/",
    **{s: f"/nuclear-bomb-map/{s}/" for s in CITY_SLUGS},
}
QUERY = [n for n in PAGE_PATH if n not in CORE and n not in CITY]
CITY_PATHS = {PAGE_PATH[n] for n in CITY}


def anchors_in(region):
    """Every <a> in a fragment, as (href, anchor text, raw attrs)."""
    out = []
    for attrs, inner in re.findall(r"(?is)<a\b([^>]*)>(.*?)</a>", region):
        m = re.search(r'href="([^"]*)"', attrs)
        out.append((m.group(1) if m else None, text_of(inner).strip(), attrs))
    return out


link_map = {}
main_region = {}
for name, body in raw.items():
    m = re.search(r"(?is)<main\b[^>]*>(.*?)</main>", body)
    check(m is not None, f"{name}: 有 <main>")
    region = m.group(1) if m else ""
    main_region[name] = region
    own = PAGE_PATH[name]

    links = [(h, a, at) for h, a, at in anchors_in(region) if h and h.startswith("/")]
    link_map[name] = links

    known = set(ANCHOR) | CITY_PATHS
    for h, a, at in links:
        check(h in known, f"{name}: 内链目标 {h} 是站内已知页面")
        check(h != own, f"{name}: 不给自己加内链（{h}）")
        check("nofollow" not in at.lower(), f"{name}: → {h} 的链接没有 nofollow")
        check("onclick" not in at.lower(), f"{name}: → {h} 的链接不是 JS 跳转")
        # 锚文本只在四个核心目标上锁死；城市页链接的锚文本由页面自己写，但必须
        # 是描述性的（不是 click here / learn more）。
        if h in ANCHOR:
            check(a.lower() == ANCHOR[h],
                  f"{name}: → {h} 的锚文本是 “{ANCHOR[h]}”（实际 “{a}”）")
        check(a.lower() not in ("click here", "learn more", "read more", "here"),
              f"{name}: → {h} 的锚文本不是 “{a}”")

    # 正文段落：所有页面内链都必须落在某个 <p> 里，不许堆在页脚或导航。
    in_p = []
    for blk in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", region):
        in_p += [(h, a) for h, a, _ in anchors_in(blk) if h and h.startswith("/")]
    check(len(in_p) == len(links),
          f"{name}: {len(links)} 条内链全部在正文 <p> 里（段内 {len(in_p)} 条）")

    got = {h for h, _, _ in links}
    if name in CORE:
        wanted = set(ANCHOR) - {own}
        check(wanted <= got, f"{name}: 出链覆盖其余三页（缺 {sorted(wanted - got)}）")
        check(len(links) >= 3, f"{name}: 出链 {len(links)} 条 ≥ 3")
    else:
        # 城市页：至少 3 条回核心页，且 /blast-radius/ 与 /nuclear-bomb-map/ 都得到。
        to_core = got & set(ANCHOR)
        check(len(to_core) >= 3, f"{name}: 回核心页的内链 {len(to_core)} 条 ≥ 3")
        check({"/blast-radius/", "/nuclear-bomb-map/"} <= to_core,
              f"{name}: 同时回到 blast-radius 与 map（实际 {sorted(to_core)}）")

for name in CORE:
    own = PAGE_PATH[name]
    src = [s for s, ls in link_map.items() if own in {h for h, _, _ in ls}]
    check(len(src) >= 2, f"{name}: 入链 {len(src)} 条 ≥ 2（来自 {src}）")

# 城市页不是孤岛。地图页链全部已发布城市，每页再链其余各页 —— 一页只有 sitemap
# 一条发现路径，等于把它的收录押在爬虫愿意走 sitemap 上。
CITY_NAME = {
    c["slug"]: c["name"]
    for c in json.loads((ROOT / "src" / "data" / "cities.json").read_text(encoding="utf-8"))["cities"]
}
CITY_ANCHOR = {f"/nuclear-bomb-map/{s}/": f"nuclear bomb effects on {CITY_NAME[s]}"
               for s in CITY_SLUGS}

# 锚文本只有一种写法：nuclear bomb effects on {City}。页面自己另起一套就会让这套
# 互链变成「五个不同锚文本指向同一个模板」。
for name, links in link_map.items():
    for h, a, _ in links:
        if h in CITY_ANCHOR:
            check(a.strip().lower() == CITY_ANCHOR[h].lower(),
                  f"{name}: → {h} 的锚文本是 “{CITY_ANCHOR[h]}”（实际 “{a}”）")

for slug in CITY_SLUGS:
    own = f"/nuclear-bomb-map/{slug}/"
    src_core = [s for s in CORE if own in {h for h, _, _ in link_map[s]}]
    src_city = [s for s in CITY if s != slug and own in {h for h, _, _ in link_map[s]}]
    total = len(src_core) + len(src_city)
    check("nuclear-bomb-map" in src_core, f"{slug}: 地图页正文链到它")
    check(len(src_city) == len(CITY) - 1,
          f"{slug}: 其余 {len(CITY) - 1} 个城市页都链到它（实际 {len(src_city)}）")
    check(total >= 4, f"{slug}: 入链 {total} 条 ≥ 4")

# 一层就够：城市页只链兄弟，不链兄弟的兄弟，也不按大洲分组。出链数恰好是已发布
# 城市数减一，多挂一条就是第二层。
for name in CITY:
    n = len([h for h, _, _ in link_map[name]
             if h in CITY_PATHS and h != PAGE_PATH[name]])
    check(n == len(CITY) - 1, f"{name}: 到其它城市页的出链 {n} 条（恰好 {len(CITY) - 1}）")

# 闭环：四页互为入链出链，没有孤岛，也没有指到站外的假内链。
check(set(link_map) == set(PAGE_PATH), "17: 内链矩阵覆盖四页与已发布城市页")

print("18 地图页正文")
mtxt = text_of(main_region["nuclear-bomb-map"])
wcount = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", mtxt))
check(wcount >= 700, f"map: 正文 {wcount} 词 ≥ 700")

# 两样东西不是「文章小节」：地图控件的标题 <h2 id="map-title">（随选城变化，
# 是控件的标签不是段落标题）和 <figure> 内部内容。先摘掉再切段，
# 否则 H2 计数与第一节词数都会偏。
article = raw["nuclear-bomb-map"]
article = re.sub(r'(?is)<h2[^>]*\bid="map-title"[^>]*>.*?</h2>', " ", article)
article = re.sub(r"(?is)<figure\b.*?</figure>", " ", article)
h2s = re.findall(r"(?is)<h2\b[^>]*>(.*?)</h2>", article)
check(4 <= len(h2s) <= 6, f"map: 文章 H2 小节 {len(h2s)} 个（要求 4–6）")
sections = re.split(r"(?is)<h2\b[^>]*>", article)[1:]
for i, sec in enumerate(sections, 1):
    title = text_of(re.split(r"(?is)</h2>", sec)[0])
    # 章节正文 = 该节内的正文段落；页脚注（class 含 small）是页面级说明，不算进小节词数。
    paras = [
        p for p in re.findall(r"(?is)<p\b([^>]*)>(.*?)</p>", sec)
        if "small" not in p[0].lower()
    ]
    body_txt = " ".join(text_of(p[1]) for p in paras)
    check(any(re.search(r"\d", text_of(p[1])) for p in paras),
          f"map 第 {i} 节 “{title}” 含具体数字")
    check(any(re.search(r"p\.\s?\d{2,3}", text_of(p[1])) for p in paras),
          f"map 第 {i} 节 “{title}” 带印刷页码")
    wc = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", body_txt))
    check(100 <= wc <= 155, f"map 第 {i} 节 “{title}” {wc} 词（目标 100–150，闸门 155）")

print("19 承诺台账（title 里的数字必须有到期日）")

plan_txt = (ROOT / "plan.md").read_text(encoding="utf-8")
ledger = re.search(r"(?s)<!--\s*PROMISE-LEDGER\s*(.*?)-->", plan_txt)
check(ledger is not None, "plan.md 有 PROMISE-LEDGER 块")

promises = []
if ledger:
    for line in ledger.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        check(len(parts) == 5, f"承诺行应为 5 段：{line!r}")
        if len(parts) == 5:
            promises.append(parts)

today = datetime.date.today()
for pid, text, where, deadline, rule in promises:
    due = datetime.date.fromisoformat(deadline)
    mrule = re.match(r"dist:(.+?)>=(\d+)$", rule)
    count, need = 0, 0
    if mrule:
        count = len(list(DIST.glob(mrule.group(1))))
        need = int(mrule.group(2))
    if today > due:
        check(count >= need,
              f"承诺 {pid}（{text}）{deadline} 已到期：{count}/{need} 兑现")
    else:
        print(f"     承诺 {pid}: “{text}” 截止 {deadline}（剩 {(due - today).days} 天），"
              f"当前 {count}/{need}，位置 {where}")

# title 一旦承诺数字，就必须在台账里有一行；否则到期没人会记得删。
# 反方向也断言：地图页的 title 现在不许再出现城市数量（v1.6 已撤回那个承诺）。
claim = re.search(r"(\d+)\s+(Cities|city pages|city)", title_map.get("nuclear-bomb-map", ""))
check(claim is None,
      f"map: title 里不写城市数量（实际出现 “{claim.group(0) if claim else ''}”）")
for name, t in title_map.items():
    c = re.search(r"(\d+)\s+Cities", t)
    if c:
        check(any(text.strip().lower() == f"{c.group(1)} cities".lower() for _, text, *_ in promises),
              f"{name}: title 承诺 “{c.group(1)} Cities”，台账里有对应行")

print("20 首月查询页（页一上线就套用硬要求）")

# 清单来自 plan.md §4.10。这里刻意硬编码而不是去解析 plan 的表格：
# 表格会被人重排，而「哪 13 页、每页多少月搜」是已经复核过的事实。
QUERY_PAGES = {
    "/nuclear-winter/": 9900,
    "/neutron-bomb/": 8100,
    "/hydrogen-bomb-vs-atomic-bomb/": 8100,
    "/fallout-map/": 4400,
    "/tsar-bomba/": 2400,
    "/thermal-radiation/": 1900,
    "/hiroshima/": 1600,
    "/how-to-survive-a-nuclear-blast/": 1300,
    "/overpressure/": 1000,
    "/nuclear-strike-map/": 720,
    "/nuclear-weapon-effects/": 720,
    "/blast-wave/": 590,
    "/nuclear-bomb-crater/": 480,
}
check(len(QUERY_PAGES) == 13, f"查询页清单 13 条（实际 {len(QUERY_PAGES)}）")

# 反方向：dist 里出现的页面，必须在 CANONICAL 里登记过。一个页面被构建出来、
# 却没有登记，就等于绕过 sitemap / canonical / 收录开关的所有断言 —— 那是偷偷加页。
listed_paths = {urllib.parse.urlparse(u).path for u in CANONICAL.values()}
built_paths = set()
for page in DIST.rglob("index.html"):
    rel = page.parent.relative_to(DIST).as_posix()
    built_paths.add("/" if rel == "." else f"/{rel}/")
stray = sorted(built_paths - listed_paths)
check(not stray, f"dist 里没有未登记的页面（{stray[:4]}）")

live = []
for path in QUERY_PAGES:
    page = DIST / path.strip("/") / "index.html"
    if not page.exists():
        continue
    live.append(path)
    html_ = page.read_text(encoding="utf-8")
    m = re.search(r"(?is)<main\b[^>]*>(.*?)</main>", html_)
    check(m is not None, f"{path}: 有 <main>")
    region = m.group(1) if m else ""
    wc = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", text_of(region)))
    check(wc >= 700, f"{path}: 正文 {wc} 词 ≥ 700")

    article = re.sub(r"(?is)<figure\b.*?</figure>", " ", region)
    h2s = re.findall(r"(?is)<h2\b[^>]*>(.*?)</h2>", article)
    check(4 <= len(h2s) <= 6, f"{path}: H2 {len(h2s)} 个（要求 4–6）")
    for i, sec in enumerate(re.split(r"(?is)<h2\b[^>]*>", article)[1:], 1):
        sec_title = text_of(re.split(r"(?is)</h2>", sec)[0])
        paras = [
            x for x in re.findall(r"(?is)<p\b([^>]*)>(.*?)</p>", sec)
            if "small" not in x[0].lower()
        ]
        body_txt = " ".join(text_of(x[1]) for x in paras)
        check(bool(re.search(r"\d", body_txt)), f"{path} 第 {i} 节 “{sec_title}” 含具体数字")
        has_page = bool(re.search(r"p\.\s?\d{2,3}", body_txt))
        has_study = bool(re.search(r"\((?:Turco|Robock|Toon|Coupe)\s+\d{4}\)", body_txt))
        if path == "/nuclear-winter/":
            # 这一页引的是已发表的气候模型研究，不是手册：页码只对手册那一节有意义。
            # 所以每节要么带 (作者 年份)，要么带印刷页码 —— 二者必居其一，不许都没有。
            check(has_study or has_page,
                  f"{path} 第 {i} 节 “{sec_title}” 带 (作者 年份) 或印刷页码")
        else:
            check(has_page, f"{path} 第 {i} 节 “{sec_title}” 带印刷页码")
        n = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.-]*", body_txt))
        check(100 <= n <= 155, f"{path} 第 {i} 节 “{sec_title}” {n} 词（目标 100–150）")

    links = [(h, a, at) for h, a, at in anchors_in(region) if h and h.startswith("/")]
    for h, a, at in links:
        if h in ANCHOR:
            check(a.lower() == ANCHOR[h], f"{path}: → {h} 的锚文本是 “{ANCHOR[h]}”（实际 “{a}”）")
        check("nofollow" not in at.lower(), f"{path}: → {h} 没有 nofollow")
    core = {h for h, _, _ in links} & set(ANCHOR)
    check(len(core) >= 3, f"{path}: 回核心页内链 {len(core)} 条 ≥ 3")
    check({"/blast-radius/", "/nuclear-bomb-map/"} <= core,
          f"{path}: 同时回到 blast-radius 与 map（实际 {sorted(core)}）")

print(f"     查询页已上线 {len(live)}/{len(QUERY_PAGES)}")

print("21 人口查询半径：25 km catchment 必须覆盖最大环")

popdata = json.loads((ROOT / "src" / "data" / "city-pop.json").read_text(encoding="utf-8"))
air_max = max(float(e["radius_km"]) for e in entries if e["burst"] == "air")
air_max_txt = f"{air_max:.2f}".rstrip("0").rstrip(".")
catch_km = float(popdata["source"].get("catch_radius_km") or 0)
check(catch_km >= air_max,
      f"city-pop source.catch_radius_km {catch_km} km ≥ 最大环 {air_max:.2f} km")
check("100 m" in popdata["source"]["name"],
      f"city-pop 数据集写明 100 m（实际 “{popdata['source']['name']}”）")
check(f"{catch_km:g} km catchment" in popdata["source"]["note"],
      "city-pop source.note 写明查询半径")

for slug, rec in popdata["cities"].items():
    cr = rec.get("catchRadiusKm")
    check(cr is not None, f"city-pop {slug}: 每条记录带 catchRadiusKm")
    if cr is not None:
        check(float(cr) >= air_max,
              f"city-pop {slug}: catchRadiusKm {cr} ≥ 最大环 {air_max:.2f}")
    check(f"{air_max:.3f}" in rec["ring_population"],
          f"city-pop {slug}: 最大环 {air_max:.3f} km 这一档真的抓到了")
    check(f"{catch_km:.3f}" in rec["ring_population"],
          f"city-pop {slug}: catchment {catch_km:.3f} km 这一档在数据里")

# 页面上两个半径都要出现：只写 10 km 会让「环内人口」看起来像是从一个装不下
# 那个环的查询里来的。
sentence_tail = f"rings up to {air_max_txt} km counted from the same {catch_km:g} km catchment"
for slug in CITY_SLUGS:
    check(sentence_tail in txt[slug], f"{slug}: 人口口径句同时写两个半径（找 “{sentence_tail}”）")
    check(f"within 10 km of" in txt[slug], f"{slug}: 人口口径句保留 10 km 城市圆")

print("22 /nuclear-winter/ 的引文纪律")

NW = DIST / "nuclear-winter" / "index.html"
if NW.exists():
    nwtxt = text_of(NW.read_text(encoding="utf-8"))
    DECL = ("These are published model studies, not figures from the 1977 manual. "
            "Nothing on this page is our own calculation.")
    check(DECL in nwtxt, "nuclear-winter: 顶部声明原文出现")
    for cite in ("Turco 1983", "Robock 2007", "Toon 2019", "Coupe 2019"):
        check(nwtxt.count(f"({cite})") >= 1, f"nuclear-winter: 正文里每条数字后跟 ({cite})")
    check("Chapter 9" in nwtxt or "Ch. 9" in nwtxt, "nuclear-winter: 手册第 9 章单独一节")
    check(bool(re.search(r"p\.\s?\d{2,3}", nwtxt)), "nuclear-winter: 手册那一节带印刷页码")
    # 手册数字与模型数字不许进同一张表。
    for table in re.findall(r"(?is)<table\b.*?</table>", NW.read_text(encoding="utf-8")):
        tt = text_of(table)
        check(not (re.search(r"\((?:Turco|Robock|Toon|Coupe)\s+\d{4}\)", tt)
                   and re.search(r"p\.\s?\d{2,3}", tt)),
              "nuclear-winter: 没有一张表同时出现模型引文与手册页码")
else:
    print("     /nuclear-winter/ 未构建，跳过引文纪律（§20 会在它上线后套用硬要求）")

print("23 /methodology/ 的人口节：页面只有一套口径")

# 这一节曾经写着「人口还没有发布」和「WorldPop 1 km 格网」，而五个城市页早已印了
# 人口、用的是 100 m 的 R2025A。页面说假话比没有这一节更糟，所以逐条钉住。
meth_html = raw["methodology"]
meth_txt = txt["methodology"]
check("1 km grid" not in meth_txt, "methodology 全页不再出现 “1 km grid”")
check("No population figure is published" not in meth_txt,
      "methodology 不再声称人口尚未发布")

m = re.search(r'(?is)<h2[^>]*id="population"[^>]*>(.*?)(?=<h2\b|</main>)', meth_html)
check(m is not None, 'methodology: 有 id="population" 的 H2 一节')
if m:
    sect = text_of(m.group(1))
    check("100 m" in sect, "methodology 人口节写明 100 m 栅格")
    check("1 km" not in sect, "methodology 人口节里没有 “1 km”")
    check(popdata["source"]["name"] in sect,
          f"methodology 人口节写明 release 名（{popdata['source']['name']}）")
    check(str(popdata["source"]["year"]) in sect, "methodology 人口节写明 2020 估算")
    check(popdata["source"]["api"] in sect, "methodology 人口节写明 API 端点")
    check(popdata["source"]["retrieved"] in sect, "methodology 人口节写明抓取日期")
    check(str(popdata["source"]["radius_km"]).rstrip("0").rstrip(".") + " km" in sect,
          "methodology 人口节保留 10 km 城市圆")
    check(f"{catch_km:g} km" in sect, f"methodology 人口节写明查询半径 {catch_km:g} km")
    check(f"{air_max:.2f} km" in sect, f"methodology 人口节写明最大环 {air_max:.2f} km")
    check("catchment" in sect, "methodology 人口节写明所有半径共用一份 catchment")
    check("subtract" in sect, "methodology 人口节写明不做环减环")

    # 版本差必须带着两个实测数字，光说「有差异」等于没说。
    paris_api = popdata["cities"]["paris"]["ring_population"]["3.220"]
    gap = 100 * (831462 - paris_api) / paris_api
    check(f"{paris_api:,}" in sect, f"methodology 人口节写出 API 实测值 {paris_api:,}")
    check("831,462" in sect, "methodology 人口节写出 GeoTIFF 实测值 831,462")
    check(f"{gap:.1f}%" in sect, f"methodology 人口节写出 {gap:.1f}% 版本差")

print(f"结果：PASS {passes}  FAIL {len(fails)}")
if fails:
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("阶段 3 构建闸门全绿。")
