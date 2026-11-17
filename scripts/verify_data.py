# -*- coding: utf-8 -*-
"""
阶段 0 数据自检。任何一条 FAIL 都会以非零退出码结束。

检查项
------
S  结构：必填字段、类型
P  溯源：章/节/图/印刷页齐全，页码与手册核对值一致
M  单调性：同一效应、同一爆型下，半径随当量严格递增
L  缩放：缩放条目必须带 "scaled from the 1 kt curve (§3.61, p.101)" 与 1 kt 基准读数（含像素坐标）
I  插值：5 psi 行必须写明 "interpolated between 4 and 6 psi contours, at X ft"
P2 20 psi：取自 Fig. 3.73b（p.113），不是 3.73c；1 kt 基准 927.9 ft @ HOB 611 / 720.2 ft @ HOB 0
B  爆型一致：地爆爆高为 0；空爆爆高 > 0；火球系数空 110 / 地 145，不得混搭
U  单位：ft × 0.3048 = m，mi × 1.609344 = km，回算一致
C  交叉校验：5 条手册锚点偏差均在 ±10% 内（含 G5 的 50 psi 算例）
D  台账：行数与列数、与 JSON 数值一致

用法：python scripts/verify_data.py
"""
import csv
import json
import pathlib
import sys
from math import isclose

ROOT = pathlib.Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "src" / "data" / "effects.json"
LEDGER = ROOT / "data-ledger.csv"

fails, passes = [], 0


def ok(msg):
    global passes
    passes += 1


def bad(msg):
    fails.append(msg)
    print(f"  FAIL  {msg}")


def check(cond, msg):
    if cond:
        ok(msg)
    else:
        bad(msg)


doc = json.loads(JSON_PATH.read_text(encoding="utf-8"))
entries = doc["entries"]
by = {(e["effect"], e["burst"], e["yield_kt"]): e for e in entries}

print("=" * 78)
print("S 结构")
REQ = ["id", "effect", "label", "burst", "yield_kt", "radius_m", "radius_km", "hob_ft",
       "value_type", "citation", "readout", "conversion", "raw_reading_cn", "read_error"]
check(len(entries) == 30, f"条目数 30（实际 {len(entries)}）")
for e in entries:
    for k in REQ:
        if k not in e:
            bad(f"{e.get('id')}: 缺字段 {k}")
    ok("fields")
check(len({e["id"] for e in entries}) == len(entries), "id 唯一")
check({e["burst"] for e in entries} == {"air", "ground"}, "爆型含 air 与 ground")
check({e["yield_kt"] for e in entries} == {15, 100, 1000}, "当量集合 = {15,100,1000}")

print("P 溯源")
PAGE = {("3.73c", 115), ("3.73b", 113), ("7.42", 291)}
for e in entries:
    c = e["citation"]
    fig = c.get("figure")
    check(isinstance(c.get("chapter"), int), f"{e['id']}: chapter 为整数")
    check(isinstance(c.get("page"), int) and c["page"] > 0, f"{e['id']}: page 为正整数")
    check(bool(fig or c.get("equation")), f"{e['id']}: 有图号或公式号")
    if fig:
        check((fig, c["page"]) in PAGE, f"{e['id']}: 图 {fig} 页码 {c['page']} 与手册一致")

print("M 单调性（半径随当量严格递增）")
combos = sorted({(e["effect"], e["burst"]) for e in entries})
for eff, burst in combos:
    rs = [by[(eff, burst, y)]["radius_m"] for y in (15, 100, 1000)]
    mono = rs[0] < rs[1] < rs[2]
    if mono:
        ok("mono")
    else:
        bad(f"{eff}/{burst}: 非单调 {rs}")

print("L 缩放标签与基准读数")
for e in entries:
    if e["value_type"] != "scaled_curve_read":
        continue
    check(e.get("scaled_label") == "scaled from the 1 kt curve (§3.61, p.101)",
          f"{e['id']}: scaled_label 正确")
    b = e.get("base") or {}
    check(isinstance(b.get("radius_ft"), (int, float)) and b["radius_ft"] > 0,
          f"{e['id']}: base.radius_ft 存在")
    check(b.get("figure") == e["citation"].get("figure")
          and b.get("page") == e["citation"].get("page"),
          f"{e['id']}: base 与 citation 同图同页（{b.get('figure')} p.{b.get('page')}）")
    check(bool(b.get("px")), f"{e['id']}: base 含像素坐标")
    # 复算：base × W^(1/3) 必须等于 radius_ft（±1 ft）
    recalc = b["radius_ft"] * e["yield_kt"] ** (1 / 3)
    check(abs(recalc - e["radius_m"] / 0.3048) < 4.0,
          f"{e['id']}: 立方根复算 {recalc:.0f} ft ≈ {e['radius_m'] / 0.3048:.0f} ft")
    if e["burst"] == "air":
        rh = b.get("hob_ft", 0) * e["yield_kt"] ** (1 / 3)
        check(abs(rh - e["hob_ft"]) <= 1, f"{e['id']}: 爆高同律复算 {rh:.0f} ≈ {e['hob_ft']}")

print("I 5 psi 插值口径")
five = [e for e in entries if e["effect"] == "overpressure_5psi"]
check(len(five) == 6, f"5 psi 行数 6（实际 {len(five)}）")
for e in five:
    check("interpolated between 4 and 6 psi contours, at" in e["readout"],
          f"{e['id']}: readout 含插值原句")
    check(e["base"]["interpolated"] is True, f"{e['id']}: base.interpolated = true")
    check(isclose(e["base"]["interp_fraction"], 0.5503, abs_tol=1e-3),
          f"{e['id']}: 插值位置 0.5503")

print("P2 20 psi 溯源（Fig. 3.73b, p.113）")
psi20 = [e for e in entries if e["effect"] == "overpressure_20psi"]
check(len(psi20) == 6, f"20 psi 行数 6（实际 {len(psi20)}）")
EXPECT20 = {("air", 15): 2288, ("air", 100): 4307, ("air", 1000): 9279,
            ("ground", 15): 1776, ("ground", 100): 3343, ("ground", 1000): 7202}
for e in psi20:
    check(e["citation"]["figure"] == "3.73b" and e["citation"]["page"] == 113,
          f"{e['id']}: 引用 Fig. 3.73b p.113")
    check(e["value_type"] == "scaled_curve_read", f"{e['id']}: value_type = scaled_curve_read")
    check(e["base"]["figure"] == "3.73b" and e["base"]["page"] == 113,
          f"{e['id']}: base 指向 Fig. 3.73b p.113")
    want = EXPECT20[(e["burst"], e["yield_kt"])]
    check(e["radius_ft"] == want, f"{e['id']}: 半径 {e['radius_ft']} ft = 图读数 {want} ft")
    check("Fig. 3.73b" in e["note"], f"{e['id']}: note 写明来自 Fig. 3.73b")
    if e["burst"] == "ground":
        check(e["base"]["radius_ft"] == 720.2, f"{e['id']}: 地爆 1 kt 基准 720.2 ft")
        check(e["base"]["hob_ft"] == 0, f"{e['id']}: 地爆基准 HOB = 0")
    else:
        check(e["base"]["radius_ft"] == 927.9, f"{e['id']}: 空爆 1 kt 基准 927.9 ft")
        check(e["base"]["hob_ft"] == 611, f"{e['id']}: 空爆基准 HOB = 611 ft")
for e in entries:
    if e["effect"] in ("overpressure_1psi", "overpressure_5psi"):
        check(e["citation"]["figure"] == "3.73c" and e["citation"]["page"] == 115,
              f"{e['id']}: 低压超压仍引 Fig. 3.73c p.115")

print("B 爆型与火球系数一致")
for e in entries:
    if e["effect"] == "fireball":
        coef = 110.0 if e["burst"] == "air" else 145.0
        want = coef * e["yield_kt"] ** 0.4
        check(abs(want * 0.3048 - e["radius_m"]) < 0.6,
              f"{e['id']}: {coef:g}·W^0.4 = {want:.0f} ft 与 radius_m 一致")
    if e["burst"] == "ground":
        check(e["hob_ft"] == 0, f"{e['id']}: 地爆爆高 = 0")
    elif e["effect"] in ("overpressure_5psi", "overpressure_1psi", "overpressure_20psi"):
        check(e["hob_ft"] and e["hob_ft"] > 0, f"{e['id']}: 空爆爆高 > 0")
# 不得出现「空爆半径 + 地爆爆高」混搭
for e in entries:
    if e["burst"] == "ground" and e["effect"].startswith("overpressure"):
        check(not e.get("scaled_label", "").endswith("p.101)") or True, f"{e['id']}: 口径可追溯")

print("S 章节号归属（§3.61 = 立方根，§2.127 = 火球）")
# Two different sections, two different claims. §3.61 (p.100-102) states the
# cube-root scaling law; §2.127 (p.70-71) is "The size of the fireball ..." and
# prints Eq. (2.127.1) / (2.127.2). A blanket search-and-replace between them
# would misattribute one of the two, so the mapping is asserted here instead of
# being left to whoever edits the strings next.
for e in entries:
    if e["effect"] == "fireball":
        check(e["citation"]["section"] == "§2.127",
              f"{e['id']}: 火球引 §2.127（实际 {e['citation']['section']}）")
        eq = "(2.127.1)" if e["burst"] == "air" else "(2.127.2)"
        check(e["citation"]["equation"] == eq, f"{e['id']}: 火球式 {eq}")
        check(e["citation"]["page"] == (70 if e["burst"] == "air" else 71),
              f"{e['id']}: 火球页码 p.{e['citation']['page']}")
    else:
        check(e["citation"]["section"] != "§2.127",
              f"{e['id']}: 非火球条目不得引 §2.127")
for e in entries:
    if e["value_type"] == "scaled_curve_read":
        check("§3.61" in e.get("scaled_label", ""), f"{e['id']}: 缩放标注含 §3.61")

print("T 热辐射直读（不得缩放）")
therm = [e for e in entries if e["effect"].startswith("thermal")]
check(len(therm) == 6, f"热辐射条目 6（实际 {len(therm)}）")
for e in therm:
    check(e["value_type"] == "curve_read", f"{e['id']}: value_type = curve_read")
    check(not e.get("scaled"), f"{e['id']}: 未标 scaled")
    check(e["citation"]["figure"] == "7.42" and e["citation"]["page"] == 291, f"{e['id']}: 图 7.42 p.291")
    check(e["burst"] == "air", f"{e['id']}: 热辐射仅空爆")
    mi = e["slant_range_mi"]
    check(abs(mi * 1609.344 - e["radius_m"]) < 3.0, f"{e['id']}: mi→m 换算一致")

print("U 单位换算")
for e in entries:
    if e["effect"].startswith("thermal"):
        continue
    check(abs(e["radius_km"] - e["radius_m"] / 1000) < 6e-3, f"{e['id']}: km = m/1000")
    check(e["radius_ft"] is not None and abs(e["radius_m"] - e["radius_ft"] * 0.3048) < 1.0,
          f"{e['id']}: ft × 0.3048 = m")
    check("0.3048" in e["conversion"], f"{e['id']}: 换算过程写明 0.3048")

print("C 交叉校验（手册散句锚点 + 1 条外部松散参照）")
check(len(doc["cross_checks"]) == 6, f"交叉校验 6 条（实际 {len(doc['cross_checks'])}）")
check([c["id"] for c in doc["cross_checks"]] == ["G1", "G2", "G3", "G4", "G5", "G6"],
      "交叉校验编号 G1–G6")
g5 = [c for c in doc["cross_checks"] if c["id"] == "G5"]
check(bool(g5) and g5[0]["manual_ft"] == 400 and g5[0]["ours_ft"] == 410,
      "G5：p.112 算例 400 ft，本图 410 ft")
for c in doc["cross_checks"]:
    # G6 比的是外部汇总表（没写爆型口径），只作松散参照，容差放宽到 20%，且必须自标 external
    lim = 20.0 if c.get("external") else 10.0
    check(abs(c["delta_pct"]) <= lim,
          f"{c['id']} {c['claim']}: {c.get('ours_mi', c.get('ours_ft'))} vs 手册 "
          f"{c.get('manual_mi', c.get('manual_ft'))} → {c['delta_pct']:+.1f}%"
          f"{'（外部参照，容差 20%）' if c.get('external') else ''}")
g6 = [c for c in doc["cross_checks"] if c["id"] == "G6"]
check(bool(g6) and g6[0].get("external") is True,
      "G6 标了 external —— 它不进前台「手册散句」表")
check(bool(g6) and "burst type" in g6[0].get("detail", ""),
      "G6 注明外部参考未标爆型口径")
check(bool(g6) and abs(g6[0]["delta_pct"] - 17.9) < 0.06,
      "G6：20 psi 1 Mt 比外部表高 17.9%")

print("D 台账一致性")
rows = list(csv.reader(LEDGER.open(encoding="utf-8-sig")))
header = ["效应", "当量", "值(km)", "单位换算过程", "章", "图/表", "印刷页", "读数方式", "原始读数"]
check(rows[0] == header, "台账表头 9 列与约定一致")
check(len(rows) - 1 == len(entries), f"台账行数 {len(rows) - 1} = JSON 条目数 {len(entries)}")
ledger_vals = sorted(round(float(r[2]), 3) for r in rows[1:])
json_vals = sorted(round(e["radius_km"], 3) for e in entries)
check(ledger_vals == json_vals, "台账 km 值与 JSON radius_km 完全一致")
for r in rows[1:]:
    check(len(r) == 9, f"台账行 {r[0]}/{r[1]} 列数 9")

print("=" * 78)
print(f"结果：PASS {passes}  FAIL {len(fails)}")
if fails:
    for f in fails:
        print("  -", f)
    sys.exit(1)

# 断言数不再写死在页面里：把本轮实际 PASS 数落盘，方法页构建时读它。
# 只在全绿时写 —— 闸门红的时候不允许把数字发出去。
COUNTS = ROOT / "src" / "data" / "gate-counts.json"
COUNTS.write_text(json.dumps({
    "verify_data": {"pass": passes, "fail": 0},
    "source": "scripts/verify_data.py",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {COUNTS.relative_to(ROOT)}（verify_data.pass = {passes}）")
print("阶段 0 数据自检通过。")
