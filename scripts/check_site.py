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
import json
import pathlib
import re
import sys

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
    "methodology": DIST / "methodology" / "index.html",
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

BANNED = [
    (r"\bdemo\b", "demo"),
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

print(f"结果：PASS {passes}  FAIL {len(fails)}")
if fails:
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("阶段 1 构建闸门全绿。")
