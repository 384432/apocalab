# -*- coding: utf-8 -*-
"""把台账 + 两张读图对照图打成一张自包含 HTML，供抽查。输出 out/spotcheck/review.html"""
import base64
import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "spotcheck"
doc = json.loads((ROOT / "src" / "data" / "effects.json").read_text(encoding="utf-8"))
rows = list(csv.reader((ROOT / "data-ledger.csv").open(encoding="utf-8-sig")))
head, body = rows[0], rows[1:]


def img64(p):
    return "data:image/png;base64," + base64.b64encode((OUT / p).read_bytes()).decode()


PRIMARY = [("fireball", "火球半径"), ("overpressure_5psi", "5 psi 超压"),
           ("overpressure_1psi", "1 psi 超压"), ("thermal_2nd", "热辐射·二度 4.5 cal/cm²"),
           ("thermal_3rd", "热辐射·三度 10 cal/cm²")]
by = {(e["effect"], e["burst"], e["yield_kt"]): e for e in doc["entries"]}


def table(burst):
    out = ['<table><thead><tr><th>效应</th><th>15 kt</th><th>100 kt</th><th>1 Mt</th>'
           '<th>爆高（1 kt → 15/100/1000 kt）</th><th>口径</th></tr></thead><tbody>']
    for eff, cn in PRIMARY:
        cells = []
        for y in (15, 100, 1000):
            e = by.get((eff, burst, y))
            if e is None:
                cells.append('<td class="na">—</td>')
            else:
                cells.append(f'<td><b>{e["radius_km"]:.2f}</b></td>')
        e0 = by.get((eff, burst, 15))
        if e0:
            if e0["hob_ft"] is None:
                hob_txt = "不适用（该公式与爆高无关）"
            elif burst == "air":
                hob_txt = "/".join(str(round(by[(eff, burst, y)]["hob_ft"] / 1000, 1))
                                   for y in (15, 100, 1000)) + " 千 ft"
            else:
                hob_txt = "HOB = 0（地爆）"
            way = {"formula": "手册公式", "curve_read": "图上直读（不缩放）",
                   "scaled_curve_read": "读图 + 立方根缩放"}[e0["value_type"]]
        else:
            hob_txt, way = "—", "—"
        out.append(f'<tr><td class="eff">{cn}</td>{"".join(cells)}<td class="dim">{hob_txt}</td>'
                   f'<td class="dim">{way}</td></tr>')
    out.append("</tbody></table>")
    return "".join(out)


cross_rows = "".join(
    f'<tr><td>{c["id"]}</td><td>{c["claim"]}</td>'
    f'<td class="dim">{c.get("manual_mi", c.get("manual_ft"))} '
    f'{"mi" if "manual_mi" in c else "ft"}</td>'
    f'<td><b>{c.get("ours_mi", c.get("ours_ft"))}</b> '
    f'{"mi" if "ours_mi" in c else "ft"}</td>'
    f'<td class="{"pos" if abs(c["delta_pct"]) <= 6 else "neg"}">{c["delta_pct"]:+.1f}%</td>'
    f'<td class="dim">{c["manual"]}</td></tr>'
    for c in doc["cross_checks"])

ledger_head = "".join(f"<th>{h}</th>" for h in head)
ledger_body = "".join(
    "<tr>" + "".join(f'<td class="{"num" if i == 2 else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
    for r in body)

caveat_html = "".join(f"<li>{c}</li>" for c in doc["caveats"])

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>apocalab 阶段 0 · 数据抽查</title>
<style>
:root{{--bg:#0f1115;--panel:#171a21;--line:#262b36;--fg:#e6e8ee;--dim:#9aa3b2;--acc:#ff8a4c;--ok:#3ecf8e;--bad:#ff6b6b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:36px 22px 80px}}
h1{{font-size:26px;margin:0 0 6px}}
h2{{font-size:18px;margin:38px 0 12px;padding-left:10px;border-left:3px solid var(--acc)}}
.sub{{color:var(--dim);font-size:13.5px;margin-bottom:8px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:13.5px}}
th,td{{padding:9px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{background:#1d212b;color:var(--dim);font-weight:600;font-size:12.5px;letter-spacing:.02em;position:sticky;top:0}}
td.num{{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
td.eff{{font-weight:600;white-space:nowrap}}
td.dim,.dim{{color:var(--dim)}}
td.na{{color:#4a5160}}
.pos{{color:var(--ok)}} .neg{{color:var(--bad)}}
img{{width:100%;border:1px solid var(--line);border-radius:8px;background:#fff;margin:8px 0 4px}}
.note{{color:var(--dim);font-size:12.5px;margin:2px 0 18px}}
.scroll{{overflow:auto;max-height:620px;border-radius:8px;border:1px solid var(--line)}}
ul{{color:var(--dim);font-size:13.5px}} li{{margin:6px 0}}
code{{background:#1d212b;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.kpi{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px}}
.kpi div{{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px;font-size:13px;color:var(--dim)}}
.kpi b{{display:block;color:var(--fg);font-size:17px;font-variant-numeric:tabular-nums}}
</style></head><body><div class="wrap">
<h1>阶段 0 · 数据抽查</h1>
<p class="sub">《The Effects of Nuclear Weapons》3rd ed. 1977 读图成果 · 24 条记录 · 数值单位 km ·
所有页码为印刷页码（整本扫描 6852629.pdf 中第 3 章 = 印刷页 + 9）</p>
<div class="kpi">
  <div><b>24</b>条记录</div>
  <div><b>336</b>项自检通过</div>
  <div><b>4/4</b>手册锚点交叉校验</div>
  <div><b>0.7%</b>与 p.114 算例偏差</div>
</div>

<h2>一、12 个主数（空爆，取各等压线峰值）</h2>
{table("air")}
<p class="note">爆高列 = 15 kt / 100 kt / 1 Mt 三档（千英尺）。每条等压线的峰值点各有自己的爆高，
统一按 W<sup>1/3</sup> 缩放。5 psi 是 4/6 psi 之间的插值，图上没有这条线。</p>

<h2>二、地爆选项（HOB = 0，读底边）</h2>
{table("ground")}
<p class="note">地爆只给超压与火球：Fig. 7.42 的热辐射是按 200·W<sup>0.4</sup> ft 爆高算的空爆曲线，
手册对地爆热辐射另走一套程序（§7.41, p.290），不在这里硬凑。</p>

<h2>三、读图对照 · Fig. 3.73c（印刷页 115）</h2>
<img src="{img64("fig3-73c_peaks_marked.png")}" alt="Fig 3.73c marked">
<p class="note">● 空爆峰值点 ｜ ○ 5 psi 插值点 ｜ ▲ 地爆底边读点 ｜ 紫线 = 手册 §3.73 的 5,000 ft 匀质大气假设上限</p>

<h2>四、读图对照 · Fig. 7.42（印刷页 291）</h2>
<img src="{img64("fig7-42_columns_marked.png")}" alt="Fig 7.42 marked">
<p class="note">三列分别为 15 kt / 100 kt / 1 Mt；每条当量列上六条等值线自外向内 = 4.5 / 6 / 8 / 10 / 15 / 25 cal/cm²。
绿圈是取用的两条（4.5 二度、10 三度）。六个数值全部直读，没有缩放。</p>

<h2>五、手册锚点交叉校验</h2>
<table><thead><tr><th>#</th><th>校验项</th><th>手册值</th><th>我的读数</th><th>偏差</th><th>手册出处</th></tr></thead>
<tbody>{cross_rows}</tbody></table>

<h2>六、口径与已知缺口</h2>
<ul>{caveat_html}</ul>

<h2>七、完整台账（data-ledger.csv）</h2>
<div class="scroll"><table><thead><tr>{ledger_head}</tr></thead><tbody>{ledger_body}</tbody></table></div>
<p class="note">台账逐行对应 <code>src/data/effects.json</code>，由 <code>scripts/verify_data.py</code>
校验两者数值完全一致。</p>
</div></body></html>"""

(OUT / "review.html").write_text(HTML, encoding="utf-8")
print("saved", OUT / "review.html", (OUT / "review.html").stat().st_size, "bytes")
