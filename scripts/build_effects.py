# -*- coding: utf-8 -*-
"""
阶段 0：由手册「图上读数」生成全站效应数据（空爆取各等压线峰值；地爆取 HOB = 0 底边）。

设计原则
--------
1. 顶部 BASE 只写**从图上/手册正文直接得到的事实**：英尺读数、像素坐标、手册原句。
2. 其余当量用手册自己的立方根缩放律：§3.61 式 (3.61.2) p.101；§3.62 p.102；
   对 Fig. 3.73a–c 的重述见 p.110。缩放值一律带标签
   "scaled from the 1 kt curve (§3.61, p.101)"。
3. 火球用手册公式：空爆 110·W^0.4（式 2.127.1, p.70）；地爆 145·W^0.4（式 2.127.2, p.71）。
4. 热辐射三档当量**直读 Fig. 7.42（p.291）**，不走缩放。
5. 站点运行时不参与任何计算，只查这张表。

用法：python scripts/build_effects.py
产出：src/data/effects.json、data-ledger.csv
"""
import csv
import json
import pathlib
from math import log10

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / "src" / "data" / "effects.json"
OUT_LEDGER = ROOT / "data-ledger.csv"

FT2M = 0.3048
MI2M = 1609.344
YIELDS = [15, 100, 1000]

SCALED_LABEL = "scaled from the 1 kt curve (§3.61, p.101)"

# ══════════════════════════════════════════════════════════════════════════
# 一、1 kt 基准读数：Fig. 3.73c（印刷页 115 = 整本 6852629.pdf 第 124 页）
# ══════════════════════════════════════════════════════════════════════════
# 光栅：1842 × 1355 px。标定（由等距网格线拟合，两个方向各自独立）：
#   x_px = 114.5 + 101.50 · (d_ft / 500)      →  500 ft = 101.50 px
#   y_px = 1140.5 − 102.55 · (h_ft / 500)     →  500 ft = 102.55 px
# 该图横纵轴单位均为 FEET；等压线只有 1 / 2 / 4 / 6 / 8 / 10 psi 六条。
# 空爆口径 = 每条等压线的峰值点（最大水平距离，不拟合最优爆高公式，只读图上峰值）。
# 地爆口径 = 该等压线与 HOB = 0 底边的交点（手册 p.106 原话：
#            "A curve for peak overpressure ... for a contact surface burst can be obtained
#             by taking the height of burst in Figs. 3.73a, b, and c to be zero."）
BLAST_AIR = {
    #  psi   d_ft    h_ft   (x_px, y_px)        出处/说明
    1.0: dict(d=7020.0, h=1575.0, px=(1540.5, 817.0),
              how="peak of the outermost isobar; the curve turns around at y_px ≈ 817 "
                  "and is still visible at x_px 1540 just right of the 7,000 ft gridline"),
    2.0: dict(d=4192.0, h=1100.0, px=(966.0, 915.0),
              how="peak of the 2nd isobar from the outside (4,190 ft at HOB 1,050; "
                  "4,187 ft at HOB 1,150)"),
    4.0: dict(d=2600.0, h=1100.0, px=(642.3, 914.9),
              how="handbook p.114 states this reading itself: 'the maximum ground distance to "
                  "which 4 psi extends for a 1 KT weapon is 2,600 feet. This occurs for a burst "
                  "height of approximately 1,100 feet'; my pixel read is 2,618 ft (x_px 646, y_px 915), +0.7%"),
    6.0: dict(d=2010.0, h=950.0, px=(522.5, 946.0),
              how="peak of the 4th isobar (1,966 ft at HOB 800; 1,990 at 850; 2,010 at 950; "
                  "1,978 at 1,050)"),
}
# 底边读数：曲线在 HOB = 20 ft 处的交点，按局部斜率线性外推到 HOB = 0（外推 20 ft，<2%）
BLAST_GROUND = {
    1.0: dict(d=3830.0, px=(894.0, 1136.0),
              how="HOB = 20 ft: 3,884 ft at x_px 892; local slope 2.7 ft per ft → 3,830 ft at HOB = 0"),
    4.0: dict(d=1655.0, px=(454.5, 1136.0),
              how="HOB = 20 ft: 1,677 ft at x_px 455; local slope 1.08 ft per ft → 1,655 ft at HOB = 0"),
    6.0: dict(d=1121.0, px=(344.0, 1136.0),
              how="HOB = 20 ft: 1,131 ft at x_px 344; local slope 0.48 ft per ft → 1,121 ft at HOB = 0"),
}
# 5 psi 没有画线：在 4 与 6 psi 之间按对数压力位置插值
T5 = (log10(5) - log10(4)) / (log10(6) - log10(4))       # = 0.55034
D5_AIR = BLAST_AIR[4.0]["d"] - T5 * (BLAST_AIR[4.0]["d"] - BLAST_AIR[6.0]["d"])
H5_AIR = BLAST_AIR[4.0]["h"] - T5 * (BLAST_AIR[4.0]["h"] - BLAST_AIR[6.0]["h"])
D5_GND = BLAST_GROUND[4.0]["d"] - T5 * (BLAST_GROUND[4.0]["d"] - BLAST_GROUND[6.0]["d"])

# ══════════════════════════════════════════════════════════════════════════
# 一b、20 psi 的 1 kt 基准：Fig. 3.73b（印刷页 113，中压段）
# ══════════════════════════════════════════════════════════════════════════
# Fig. 3.73c 只印到 10 psi。20 psi 印在 Fig. 3.73b 上，该图的标号是
# 10 / 15 / 20 / 30 / 50 / 100 / 200 psi（算例给的正是 50 psi）。
# 光栅：p113_600.png（4,320 × 3,136 px，600 dpi 渲染）。
# 标定（等距网格线，两个方向各自独立）：
#   x_px = 348.5 + 2.2467 · d_ft      → 100 ft = 224.67 px（0–1,500 ft，15 格）
#   y_px = 2521.5 − 2.2540 · h_ft     → 100 ft = 225.40 px（0–1,000 ft，10 格）
# 标定校验 = 手册 p.112 自己的算例：50 psi 过 (400 ft, HOB 500 ft)；本标定下
# 该等压线在 HOB 500 ft 处落在 410 ft，偏差 +2.5%（HOB 510/520 处读 392/373 ft，
# 曲线走向与算例一致）。另用 Fig. 3.73a 的 100 psi 交叉核对：本图 363 ft @
# HOB 210，3.73a 上该线鼻尖约 360 ft @ HOB 190，偏差 <1%。
BLAST20_AIR = dict(
    d=927.9, h=611.0, px=(2433.1, 1144.0),
    how=("peak of the 20 psi isobar, at x_px 2433 / HOB 611 ft; the apex is a parabola fit "
         "through the traced contour within ±40 ft of the maximum (raw sample 928.5 ft at HOB 608)"),
)
BLAST20_GND = dict(
    d=720.2, px=(1966.5, 2521.5), at_hob=30.0, at_d=725.5, slope=0.178,
    how=("bottom edge (HOB = 0): the contour reads 725.5 ft at HOB 30 ft and its local slope is "
         "0.178 ft per ft, extrapolated over the last 30 ft"),
)
CIT3B = {"chapter": 3, "section": "§3.73 / §3.61", "figure": "3.73b", "page": 113}

# ══════════════════════════════════════════════════════════════════════════
# 二、热辐射：Fig. 7.42（印刷页 291）
# ══════════════════════════════════════════════════════════════════════════
# 光栅 fig7242_hi_rot.png（4,692 × 3,156 px，原图旋转 270° 转正）标定：
#   x_px = 834.5 + 783.25 · log10(W_kt)
#   y_px = 212.0 + 783.67 · (2 − log10(slant_range_mi))
# 纵轴网格经验证落在 100/50/20/10/5/2/1/0.5/0.2/0.1 mi，标定成立。
# 每个当量列上恰有 6 条等值线穿过；数值由手册自身两处文字定标：
#   §12.66 (p.563)：1 Mt 时 4.5–6 cal/cm² 位于 9–10 mi 斜距 → 最外两条 = 4.5 / 6
#   §7.43  (p.290)：1 Mt 时 8 cal/cm² 约 7 mi          → 第三条 = 8
# 自外向内依次为 4.5 / 6 / 8 / 10 / 15 / 25 cal/cm²。
THERMAL_PX = {
    15:   dict(x=1756, y=[1528.0, 1614.5, 1688.5, 1746.5, 1883.5, 1997.0]),
    100:  dict(x=2391, y=[1279.5, 1339.0, 1410.0, 1467.5, 1590.5, 1690.0]),
    1000: dict(x=3194, y=[983.5, 1045.0, 1100.5, 1146.0, 1241.0, 1329.5]),
}
Q_LIST = [4.5, 6, 8, 10, 15, 25]          # 自外向内


def mi_of(y_px):
    return 10 ** (2.0 - (y_px - 212.0) / 783.67)


def fireball_air_ft(w):
    return 110.0 * (w ** 0.4)             # §2.127 式 (2.127.1), p.70


def fireball_gnd_ft(w):
    return 145.0 * (w ** 0.4)             # §2.127 式 (2.127.2), p.71


def cube_root(w):
    return w ** (1.0 / 3.0)


def hob_thermal_ft(w):
    return 200.0 * (w ** 0.4)             # §7.42, p.290


entries = []


def add(effect, label, burst, y, value, hob_ft, value_type, citation, readout,
        prefix, raw_cn, note, scaled=None, base=None, extra=None, err="±5%", unit="ft"):
    """value 为英尺（unit='ft'）或英里（unit='mi'）。米与公里由同一舍入链推出，保证台账自洽。"""
    if unit == "ft":
        radius_ft = round(value)
        radius_m = round(value * FT2M)
        conv = f"{prefix} = {radius_ft} ft; × 0.3048 = {radius_m} m = {radius_m / 1000:.2f} km"
    else:
        radius_ft = None
        radius_m = round(value * MI2M)
        conv = f"{prefix} = {value:.2f} mi; × 1.609344 = {radius_m} m = {radius_m / 1000:.2f} km"
    km = round(radius_m / 1000.0, 2)
    e = {
        "id": f"{effect}.{burst}.{y}",
        "effect": effect,
        "label": label,
        "burst": burst,
        "yield_kt": y,
        "radius_m": radius_m,
        "radius_km": km,
        "radius_ft": radius_ft,
        "hob_ft": (round(hob_ft) if hob_ft is not None else None),
        "hob_m": (round(hob_ft * FT2M) if hob_ft is not None else None),
        "value_type": value_type,
        "citation": citation,
        "readout": readout,
        "conversion": conv,
        "raw_reading_cn": raw_cn,
        "read_error": err,
        "read_by": "programmatic chart digitization (ring)",
        "checked_by": None,
        "note": note,
        "hob_note": ("the fireball radius in eq. (2.127.1) does not depend on burst height"
                     if (effect == "fireball" and burst == "air") else
                     ("contact surface burst; the table radius is the equivalent-sphere radius of the hemisphere"
                      if effect == "fireball" else None)),
    }
    if scaled:
        e["scaled"] = True
        e["scaled_label"] = SCALED_LABEL
        e["scaling"] = scaled
    if base:
        e["base"] = base
    if extra:
        e.update(extra)
    entries.append(e)

# ── 1) 火球 ────────────────────────────────────────────────────────────────
for burst, fn, eq, page in (("air", fireball_air_ft, "(2.127.1)", 70),
                            ("ground", fireball_gnd_ft, "(2.127.2)", 71)):
    coef = 110 if burst == "air" else 145
    for y in YIELDS:
        ft = fn(y)
        add("fireball", "Fireball radius (breakaway)", burst, y,
            ft,
            None if burst == "air" else 0.0,
            "formula",
            {"chapter": 2, "section": "§2.127", "equation": eq, "figure": None, "page": page},
            (f"R = {coef}·W^0.4 ft, W = {y} kt → {ft:.0f} ft "
             f"(handbook equation {eq}, p.{page}; no chart reading, no scaling)"),
            f"{coef} × {y}^0.4 = {coef} × {y ** 0.4:.5f}",
            f"{coef} × {y}^0.4 = {ft:.0f} ft（手册公式，非读图）",
            ("radius at breakaway; §2.129 (p.71) notes the maximum radius may be taken as about "
             "twice this value" if burst == "air" else
             "contact surface burst; the fireball is a hemisphere on the surface and this radius "
             "is the handbook's equivalent-sphere value (eq. 2.127.2, p.71)"),
            err="n/a (printed equation)")

# ── 2) 5 psi 超压 ─────────────────────────────────────────────────────────
CIT3 = {"chapter": 3, "section": "§3.73 / §3.61", "figure": "3.73c", "page": 115}
for burst in ("air", "ground"):
    for y in YIELDS:
        f = cube_root(y)
        if burst == "air":
            d1, h1 = D5_AIR, H5_AIR
            hob = h1 * f
        else:
            d1, h1 = D5_GND, 0.0
            hob = 0.0
        ft = d1 * f
        readout = (
            f"interpolated between 4 and 6 psi contours, at {d1:.0f} ft "
            f"(1 kt, {'peak of each isobar' if burst == 'air' else 'HOB = 0 bottom edge'}); "
            f"4 psi base {BLAST_AIR[4.0]['d']:.0f} ft / 6 psi base {BLAST_AIR[6.0]['d']:.0f} ft "
            f"at 1 kt, log-pressure fraction {T5:.4f}; "
            f"scaled from the 1 kt curve (§3.61, p.101): {d1:.0f} × {y}^(1/3) = {ft:.0f} ft"
        )
        raw_cn = (
            f"1 kt 基准：4 psi {'峰值' if burst == 'air' else '底边'} "
            f"{BLAST_AIR[4.0]['d'] if burst == 'air' else BLAST_GROUND[4.0]['d']:.0f} ft"
            f"{' @ HOB 1,100 ft（p.114 原文）' if burst == 'air' else ' @ HOB = 0（x_px 454.5, y_px 1136）'}；"
            f"6 psi {'峰值' if burst == 'air' else '底边'} "
            f"{BLAST_AIR[6.0]['d'] if burst == 'air' else BLAST_GROUND[6.0]['d']:.0f} ft"
            f"{' @ HOB 950 ft（x_px 522.5, y_px 946）' if burst == 'air' else ' @ HOB = 0（x_px 344, y_px 1136）'}；"
            f"按 ln 压力位置插值 t = {T5:.4f} → {d1:.1f} ft"
            f"{f' @ HOB {h1:.0f} ft' if burst == 'air' else ''}；插值后 × {y}^(1/3) = {ft:.0f} ft"
        )
        add("overpressure_5psi", "5 psi overpressure radius", burst, y,
            ft, hob, "scaled_curve_read", CIT3,
            readout,
            f"{d1:.0f} ft × {y}^(1/3) = {d1:.0f} × {f:.4f}",
            raw_cn,
            ("5 psi is NOT one of the contours printed on Fig. 3.73c (the figure prints 1, 2, 4, 6, "
             "8 and 10 psi only); the value is interpolated between the 4 and 6 psi contours"),
            scaled={"law": "cube_root", "formula": "d = d_1kt · W^(1/3)",
                    "section": "§3.61 eq. (3.61.2), restated §3.62 and §3.73", "pages": [101, 102, 110]},
            base={"yield_kt": 1, "radius_ft": round(d1, 1),
                  "hob_ft": round(h1, 1) if burst == "air" else 0.0,
                  "figure": "3.73c", "page": 115, "interpolated": True,
                  "between_psi": [4, 6], "interp_fraction": round(T5, 4),
                  "px": {"4psi": list(BLAST_AIR[4.0]["px"]) if burst == "air" else list(BLAST_GROUND[4.0]["px"]),
                         "6psi": list(BLAST_AIR[6.0]["px"]) if burst == "air" else list(BLAST_GROUND[6.0]["px"])}})

# ── 2b) 20 psi 超压（Fig. 3.73b，p.113）───────────────────────────────────
for burst in ("air", "ground"):
    src = BLAST20_AIR if burst == "air" else BLAST20_GND
    d1 = src["d"]
    h1 = src["h"] if burst == "air" else 0.0
    for y in YIELDS:
        f = cube_root(y)
        ft = d1 * f
        where = f"at HOB {h1:.0f} ft" if burst == "air" else "at HOB = 0"
        add("overpressure_20psi", "20 psi overpressure radius", burst, y,
            ft, h1 * f if burst == "air" else 0.0,
            "scaled_curve_read", CIT3B,
            (f"1 kt base {d1:.1f} ft {where} ({src['how']}); "
             f"scaled from the 1 kt curve (§3.61, p.101): {d1:.0f} × {y}^(1/3) = {ft:.0f} ft"),
            f"{d1:.1f} ft × {y}^(1/3) = {d1:.1f} × {f:.4f}",
            (f"1 kt 基准 {d1:.1f} ft"
             + ("（峰值，x_px 2433.1 / y_px 1144.0，HOB 611 ft，±40 ft 邻域抛物线拟合）"
                if burst == "air" else
                "（底边 HOB = 0：HOB 30 ft 处 725.5 ft，局部斜率 0.178，外推；x_px 1966.5）")
             + f" × {y}^(1/3) = {ft:.0f} ft"),
            ("20 psi is printed on Fig. 3.73b (intermediate-pressure range) and not on Fig. 3.73c; "
             "the peak is read the same way as the 1, 5 and 10 psi contours, then scaled"
             if burst == "air" else
             "contact surface burst: the 20 psi contour meets the bottom edge of Fig. 3.73b "
             "(HOB = 0), read the way p.106 prescribes"),
            scaled={"law": "cube_root", "formula": "d = d_1kt · W^(1/3)",
                    "section": "§3.61 eq. (3.61.2), restated §3.62 and §3.73", "pages": [101, 102, 110]},
            base={"yield_kt": 1, "radius_ft": round(d1, 1),
                  "hob_ft": round(h1, 1) if burst == "air" else 0.0,
                  "figure": "3.73b", "page": 113, "px": list(src["px"])})

# ── 3) 1 psi 超压 ─────────────────────────────────────────────────────────
for burst in ("air", "ground"):
    for y in YIELDS:
        f = cube_root(y)
        src = BLAST_AIR[1.0] if burst == "air" else BLAST_GROUND[1.0]
        d1 = src["d"]
        h1 = src["h"] if burst == "air" else 0.0
        ft = d1 * f
        add("overpressure_1psi", "1 psi overpressure radius", burst, y,
            ft, h1 * f if burst == "air" else 0.0,
            "scaled_curve_read", CIT3,
            (f"1 kt base {d1:.0f} ft"
             + (f" at HOB {h1:.0f} ft (peak of the outermost isobar, x_px 1540.5, y_px 817)"
                if burst == "air" else " at HOB = 0 (bottom edge, x_px 894, y_px 1136)")
             + f"; scaled from the 1 kt curve (§3.61, p.101): {d1:.0f} × {y}^(1/3) = {ft:.0f} ft"),
            f"{d1:.0f} ft × {y}^(1/3) = {d1:.0f} × {f:.4f}",
            (f"1 kt 基准 {d1:.0f} ft"
             + ("（最外等压线峰值，x_px 1540.5, y_px 817，HOB 1,575 ft）"
                if burst == "air" else "（底边 HOB = 0，x_px 894, y_px 1136）")
             + f" × {y}^(1/3) = {ft:.0f} ft"),
            ("1 psi is the outermost isobar drawn on Fig. 3.73c; the peak is read where the curve "
             "turns around, just to the right of the 7,000 ft gridline"
             if burst == "air" else
             "contact surface burst: the handbook reads this by taking the height of burst to be zero (p.106)"),
            scaled={"law": "cube_root", "formula": "d = d_1kt · W^(1/3)",
                    "section": "§3.61 eq. (3.61.2), restated §3.62 and §3.73", "pages": [101, 102, 110]},
            base={"yield_kt": 1, "radius_ft": d1, "hob_ft": h1 if burst == "air" else 0.0,
                  "figure": "3.73c", "page": 115, "px": list(src["px"])})

# ── 4) 热辐射（直读，不缩放）──────────────────────────────────────────────
for effect, label, idx, q, note in (
    ("thermal_2nd", "Thermal radius, 2nd-degree burns", 0, 4.5,
     "lower edge of the handbook's 4.5-6 cal/cm² band; §12.65 (p.563) states that at 4.5-6 cal/cm² "
     "about 18 percent of an exposed population receives second-degree burns, the rest first-degree. "
     "Light skin, no shielding, no evasive action."),
    ("thermal_3rd", "Thermal radius, 3rd-degree burns", 3, 10.0,
     "10 cal/cm², third-degree threshold for light skin per Fig. 12.64 (p.564). "
     "Light skin, no shielding, no evasive action."),
):
    for y in YIELDS:
        col = THERMAL_PX[y]
        ypx = col["y"][idx]
        mi = mi_of(ypx)
        m = mi * MI2M
        add(effect, label, "air", y, mi, hob_thermal_ft(y), "curve_read",
            {"chapter": 7, "section": "§7.41-7.42", "figure": "7.42", "page": 291},
            (f"Fig. 7.42 read directly at the {y} kt column (x_px {col['x']}); the "
             f"curve for {q:g} cal/cm² is the #{idx + 1} contour from the outside and crosses the "
             f"column at y_px {ypx:.1f} → {mi:.2f} mi slant range. NOT scaled."),
            f"Fig. 7.42 y-axis read at x_px {col['x']}, y_px {ypx:.1f}",
            f"Fig. 7.42 纵轴直读：{y} kt 列 x_px {col['x']}，自外向内第 {idx + 1} 条 y_px {ypx:.1f} → {mi:.2f} mi",
            note,
            extra={"q_cal_cm2": q, "slant_range_mi": round(mi, 3), "skin": "light, unshaded",
                   "burst_height_note": "Fig. 7.42 is drawn for burst heights of 200·W^0.4 ft (§7.42, p.290)"},
            err="±6% (±0.3 mi at 1 Mt)", unit="mi")

# ══════════════════════════════════════════════════════════════════════════
# 三、交叉校验（不进前台，只做自检证据）
# ══════════════════════════════════════════════════════════════════════════
mt = THERMAL_PX[1000]["y"]
cross = [
    dict(id="G1", claim="1 Mt, 4.5 cal/cm² slant range",
         manual="9–10 mi band, outer edge (§12.66, p.563)", manual_mi=10.0,
         ours_mi=round(mi_of(mt[0]), 2)),
    dict(id="G2", claim="1 Mt, 6 cal/cm² slant range",
         manual="9–10 mi band, inner edge (§12.66, p.563)", manual_mi=9.0,
         ours_mi=round(mi_of(mt[1]), 2)),
    dict(id="G3", claim="1 Mt, 8 cal/cm² slant range",
         manual="about 7 mi (§7.43, p.290)", manual_mi=7.0,
         ours_mi=round(mi_of(mt[2]), 2)),
    dict(id="G4", claim="1 kt, 4 psi maximum ground distance",
         manual="2,600 ft at about 1,100 ft HOB (p.114 worked example)", manual_ft=2600.0,
         ours_ft=2618.0),
    dict(id="G5", claim="1 kt, distance to 50 psi at 500 ft burst height",
         manual="400 ft (p.112 worked example: 'at a ground distance of 400 feet and a burst "
                "height of 500 feet, the peak overpressure is 50 psi')", manual_ft=400.0,
         ours_ft=410.0),
    # G6 不是「手册散句锚点」，是本站与外部汇总表的对照，所以标 external=True：
    # 前台的 Cross-checks 表标题是「against the manual's own prose」，G6 不属于那里，
    # src/lib/effects.ts 把它过滤掉，两张表仍然只列 G1–G5（页面上的「Five statements」才是对的）。
    # 外部那几张汇总表没有注明爆型口径，只能当松散参照；手册仍为唯一真源。
    dict(id="G6", claim="manual sits above common summary tables at 10 and 20 psi",
         manual="common summary tables, burst type not stated — loose reference only, "
                "the manual is the source of truth",
         manual_ft=7874.0,          # 2.4 km，外部表 20 Mt→6.4 km 按 W^(1/3) 折到 1 Mt
         ours_ft=9280.0,            # 928.0 ft × 1000^(1/3) = 9,280 ft = 2.83 km（1 Mt 空爆）
         external=True,
         detail=("10 psi at 1 kt: manual nose 1,467 ft = 0.447 km (p.113) / "
                 "1,500 ft = 0.457 km (p.115) against about 0.4 km → +12% to +14%; "
                 "20 psi at 1 Mt: 9,280 ft = 2.83 km against about 2.4 km → +17.9%. "
                 "The external figures do not state a burst type, so this is a loose "
                 "reference, not a check: the manual is the source of truth.")),
]
for c in cross:
    if "manual_mi" in c:
        c["delta_pct"] = round((c["ours_mi"] - c["manual_mi"]) / c["manual_mi"] * 100, 1)
    else:
        c["delta_pct"] = round((c["ours_ft"] - c["manual_ft"]) / c["manual_ft"] * 100, 1)

# ══════════════════════════════════════════════════════════════════════════
# 四、输出
# ══════════════════════════════════════════════════════════════════════════
manual = {
    "title": "The Effects of Nuclear Weapons",
    "editors": ["Samuel Glasstone", "Philip J. Dolan"],
    "edition": "3rd",
    "year": 1977,
    "publisher": ["U.S. Department of Defense", "Energy Research and Development Administration"],
    "doi": "10.2172/6852629",
    "public_domain": True,
    "page_convention": ("citations use the printed page numbers of the 1977 edition; in the full scan "
                        "6852629.pdf the chapter 3 pages are printed page + 9"),
}

method = {
    "air_burst_blast": ("height of burst is read at the peak of each individual isobar — on "
                        "Fig. 3.73c (p.115) for the 1, 2, 4, 6, 8 and 10 psi contours and on "
                        "Fig. 3.73b (p.113) for the 20 psi contour, which 3.73c does not print "
                        "(the point of maximum horizontal distance); each overpressure therefore "
                        "carries its own burst height, and that height is scaled as W^(1/3)"),
    "ground_burst_blast": ("contact surface burst: the height of burst is taken as zero and the distance is "
                           "read where each isobar meets the bottom edge of Fig. 3.73c (1, 5 and 1 psi) "
                           "or Fig. 3.73b (20 psi), per handbook p.106"),
    "fireball": "110·W^0.4 ft for air bursts (2.127.1, p.70); 145·W^0.4 ft for contact surface bursts (2.127.2, p.71)",
    "thermal": ("read directly off Fig. 7.42 (p.291) at each yield column; no scaling is applied. "
                "Fig. 7.42 is drawn for burst heights of 200·W^0.4 ft (§7.42, p.290) and for air bursts "
                "below 15,000 ft with 12-mile visibility"),
    "overpressure_definition": ("Fig. 3.73 curves are peak overpressures on the ground, i.e. they include "
                                "reflection at the surface; tools quoting incident or side-on overpressure "
                                "show smaller radii for the same psi"),
}

caveats = [
    ("Blast heights of burst are scaled as W^(1/3), so the 1 Mt rows sit at 6,100 ft (20 psi), "
     "10,200 ft (5 psi) and 15,750 ft (1 psi). §3.73 (p.110) states the homogeneous sea-level "
     "atmosphere assumption for burst heights of 5,000 ft or less, so the 1 Mt blast rows "
     "extrapolate the handbook's assumption by a factor of 2-3. No altitude correction "
     "(§3.64-3.66) is applied; the sign of that omission is that the 1 Mt radii are understated "
     "rather than overstated."),
    ("5 psi is not printed on Fig. 3.73c. It is interpolated between the 4 and 6 psi contours at the "
     "log-pressure position 0.5503, and every 5 psi row is labelled as interpolated."),
    ("20 psi is not printed on Fig. 3.73c either: it is one of the contours of Fig. 3.73b (p.113), "
     "the intermediate-pressure range, whose labels are 10, 15, 20, 30, 50, 100 and 200 psi. It is "
     "read at the peak of that contour and scaled by the same cube-root law; the 20 psi rows "
     "therefore cite Fig. 3.73b rather than Fig. 3.73c."),
    ("Thermal radii are slant ranges. §12.66 (p.563) notes that for ranges much greater than the burst "
     "height they may be taken as distances to ground zero, which is how they are reported here."),
    ("Thermal radii are for air bursts only. Fig. 7.42 is calculated for burst heights of 200·W^0.4 ft and "
     "the handbook's surface-burst treatment of thermal radiation (§7.41, p.290) points to a different "
     "procedure, so the ground-burst option shows blast and fireball only."),
    ("Thermal contour values on Fig. 7.42 are not printed as legible labels on the scan; they were fixed by "
     "two independent statements in the handbook (§12.66 p.563: 4.5-6 cal/cm² at 9-10 mi for 1 Mt; "
     "§7.43 p.290: 8 cal/cm² at about 7 mi). Both are reproduced within ±5% by the digitized curves."),
]

# ── 签核状态 ───────────────────────────────────────────────────────────────
# 空爆 15 条：owner 在 2026-11-11 独立重算了 12 个主值（火球/5psi/1psi/二度），
# 其中 5 条对过原图；三度那一列由同一张图直读、随主值一起签收。
# 地爆 9 条：owner 在 2026-11-14 把 Fig. 3.73c（p.115）的 HOB = 0 底边用 600 dpi
#           重渲染后独立重读：三个 1 kt 基准 — 4 psi 1655 ft、6 psi 1121 ft、
#           1 psi 3830 ft — 与曲线和底边的数字化交点（1665 / 1122 / 3832 ft）全部
#           相差 ≤0.6%，都在 ±5% 读数误差内，故一并签收，不再挂 *。
# 20 psi 6 条：owner 在 2026-11-18 按「复现性 + 空爆自洽 + 陡段图对图」三条判据签核。
#           上一轮那套「把 HOB 行折回 HOB=0 再互比」的判据不成立——§3.61/§3.62 只有
#           d = d₁·W^(1/3) 与 h = h₁·W^(1/3)，没有把爆高折回零的公式——已作废（plan §21）。
# 渲染层的 * 保留：以后新加的行只要 checked_by 还是 None 就会带星，不会被混进已签核的堆里。
SIGN_OFF_AIR = ("owner, 2026-11-11: phase 0 sign-off — twelve headline values independently "
                "recomputed, five spot-checked against the printed figures")
SIGN_OFF_GROUND_FIREBALL = ("owner, 2026-11-14: contact-burst sign-off — eq. (2.127.2) recomputed "
                            "at 145·W^0.4 for 15, 100 and 1,000 kt against p.71; the ground-burst "
                            "branch of the equation already signed off for the air-burst rows")
SIGN_OFF_GROUND_1PSI = ("owner, 2026-11-14: contact-burst sign-off — 1 kt base re-read at the bottom "
                        "edge (HOB = 0) of Fig. 3.73c, p.115, from a 600 dpi render of the page: "
                        "3,830 ft, within 0.05% of the digitized 3,832 ft; the three scaled radii "
                        "recomputed from that base")
SIGN_OFF_GROUND_5PSI = ("owner, 2026-11-14: contact-burst sign-off — both 1 kt bases re-read at the "
                        "bottom edge (HOB = 0) of Fig. 3.73c, p.115, from a 600 dpi render: 4 psi "
                        "1,655 ft and 6 psi 1,121 ft, both within 0.6% of the digitized 1,665 / "
                        "1,122 ft; log-pressure fraction 0.5503 rechecked → 1,361 ft at 1 kt, and "
                        "the three scaled radii recomputed from it")
SIGN_OFF_20PSI = ("owner, 2026-11-18: 20 psi sign-off — contour re-read from a 600 dpi render of "
                  "Fig. 3.73b (p.113) at the HOB 500 and HOB 300 rows, three independent points "
                  "per row (left edge, ink-weighted centre, right edge): 867.7 / 871.5 / 875.3 ft "
                  "(spread 17 px) and 778.7 / 781.6 / 784.5 ft (spread 13 px), both inside the "
                  "20 px stroke width; air peak 928.0 ft at HOB 612 ft clears the contact value "
                  "720.2 ft with the peak height between the two rows; the same procedure applied "
                  "to the 10 psi contour in Fig. 3.73b and Fig. 3.73c gives 1,464 ft and 1,493 ft, "
                  "a 2.0% difference against a 3% limit")
for e in entries:
    if e["effect"] == "overpressure_20psi":
        # 2026-11-18 新增、当日按复现性判据签核：读数、像素坐标与缩放过程都写进了 base 与 readout。
        # 必须排在最前面判断：2026-11-11 那句 SIGN_OFF_AIR 只覆盖当时那 12 个主值，
        # 落在下面的 air 分支里会被误盖成「2026-11-11 已签核」，把签核日期说错。
        e["checked_by"] = SIGN_OFF_20PSI
    elif e["burst"] == "air":
        e["checked_by"] = SIGN_OFF_AIR
    elif e["effect"] == "fireball":
        e["checked_by"] = SIGN_OFF_GROUND_FIREBALL
    elif e["effect"] == "overpressure_1psi":
        e["checked_by"] = SIGN_OFF_GROUND_1PSI
    elif e["effect"] == "overpressure_5psi":
        e["checked_by"] = SIGN_OFF_GROUND_5PSI
    else:  # 地爆没有热辐射行；真出现了必须当场决定签核来源，而不是静默留 None
        raise SystemExit(f"unsigned contact-burst effect: {e['effect']} ({e['id']})")

doc = {
    "manual": manual,
    "method": method,
    "caveats": caveats,
    "cross_checks": cross,
    "entries": entries,
}
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 台账 ───────────────────────────────────────────────────────────────────
EFFECT_CN = {
    "fireball": "火球半径",
    "overpressure_20psi": "20 psi 超压半径",
    "overpressure_5psi": "5 psi 超压半径",
    "overpressure_1psi": "1 psi 超压半径",
    "thermal_2nd": "热辐射半径·二度 4.5 cal/cm²",
    "thermal_3rd": "热辐射半径·三度 10 cal/cm²",
}
BURST_CN = {"air": "空爆", "ground": "地爆"}
TYPE_CN = {
    "formula": "手册公式直算（非读图、非缩放）",
    "curve_read": "图上直读（不缩放）",
    "scaled_curve_read": "立方根缩放（基准为 1 kt 读图值）",
}
ORDER = {"fireball": 0, "overpressure_20psi": 1, "overpressure_5psi": 2,
         "overpressure_1psi": 3, "thermal_2nd": 4, "thermal_3rd": 5}
BORDER = {"air": 0, "ground": 1}

rows = sorted(entries, key=lambda e: (BORDER[e["burst"]], ORDER[e["effect"]], e["yield_kt"]))

with OUT_LEDGER.open("w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["效应", "当量", "值(km)", "单位换算过程", "章", "图/表", "印刷页", "读数方式", "原始读数"])
    for e in rows:
        c = e["citation"]
        fig = c.get("figure") or f"式 {c.get('equation')}"
        how = TYPE_CN[e["value_type"]]
        if e["value_type"] == "scaled_curve_read":
            how += f"；1 kt 基准 {e['base']['radius_ft']:.0f} ft"
        if e["effect"] == "overpressure_5psi":
            how += "；5 psi 未印线，取 4/6 psi 插值"
        if e["effect"] == "overpressure_20psi":
            how += "；20 psi 不印在 Fig. 3.73c，取自 Fig. 3.73b 同一条等压线"
        w.writerow([
            f"{EFFECT_CN[e['effect']]}（{BURST_CN[e['burst']]}）",
            f"{e['yield_kt']} kt",
            f"{e['radius_km']:.2f}",
            e["conversion"],
            f"第 {c['chapter']} 章",
            fig,
            c["page"],
            how,
            e["raw_reading_cn"],
        ])

print(f"wrote {OUT_JSON.relative_to(ROOT)}  entries={len(entries)}")
print(f"wrote {OUT_LEDGER.relative_to(ROOT)}  rows={len(rows)}")
print(f"1 kt bases — air: 1psi {BLAST_AIR[1.0]['d']:.0f}ft@{BLAST_AIR[1.0]['h']:.0f}, "
      f"2psi {BLAST_AIR[2.0]['d']:.0f}ft@{BLAST_AIR[2.0]['h']:.0f}, "
      f"4psi {BLAST_AIR[4.0]['d']:.0f}ft@{BLAST_AIR[4.0]['h']:.0f}, "
      f"6psi {BLAST_AIR[6.0]['d']:.0f}ft@{BLAST_AIR[6.0]['h']:.0f}, "
      f"5psi interp {D5_AIR:.0f}ft@{H5_AIR:.0f}")
print(f"1 kt bases — ground: 1psi {BLAST_GROUND[1.0]['d']:.0f}ft, "
      f"4psi {BLAST_GROUND[4.0]['d']:.0f}ft, 6psi {BLAST_GROUND[6.0]['d']:.0f}ft, "
      f"5psi interp {D5_GND:.0f}ft")
print("cross-checks:", [(c["id"], c["ours_mi"] if "ours_mi" in c else c["ours_ft"], c["delta_pct"]) for c in cross])
