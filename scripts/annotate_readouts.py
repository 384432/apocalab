# -*- coding: utf-8 -*-
"""
生成「读图对照图」：把 build_effects.py 用到的每个 1 kt 基准读数画回原图上，
方便人工抽查。输出到 out/spotcheck/。

标记含义
--------
● 实心圆 = 空爆峰值点（各等压线的最大水平距离）
○ 空心圆 = 5 psi 插值点（图上没有这条线）
▲ 三角   = 地爆读点（等压线与 HOB = 0 底边交点，取 HOB ≈ 20 ft 处再外推）

用法：python scripts/annotate_readouts.py
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
TMP = ROOT / ".tmp_handbook"
OUT = ROOT / "out" / "spotcheck"
OUT.mkdir(parents=True, exist_ok=True)

FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]

# Fig. 3.73c 标定
X0, XST = 114.5, 101.50
Y0, YST = 1140.5, 102.55


def px(d_ft, h_ft=0.0):
    return (X0 + XST * d_ft / 500.0, Y0 - YST * h_ft / 500.0)


def font(size):
    for p in FONT_PATHS:
        if pathlib.Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


RED = (200, 30, 30)
BLUE = (0, 100, 200)
GREEN = (0, 130, 70)

# (psi 标签, d_ft, h_ft, 说明)
PEAKS = [
    ("1 psi peak", 7020.0, 1575.0, "7,020 ft @ HOB 1,575"),
    ("2 psi peak", 4192.0, 1100.0, "4,192 ft @ HOB 1,100"),
    ("4 psi peak", 2600.0, 1100.0, "2,600 ft @ HOB 1,100  (§ p.114)"),
    ("6 psi peak", 2010.0, 950.0, "2,010 ft @ HOB 950"),
]
INTERP_PEAK = (2275.0, 1017.0, "5 psi interp\n2,275 ft @ HOB 1,017")
GROUND = [
    ("1 psi", 3830.0, "3,830 ft @ HOB 0"),
    ("4 psi", 1655.0, "1,655 ft"),
    ("6 psi", 1121.0, "1,121 ft"),
]
INTERP_GROUND = (1361.0, "5 psi interp 1,361 ft")


def fig_373c():
    im = Image.open(TMP / "fig_3_73c.png").convert("RGB")
    dr = ImageDraw.Draw(im)
    f = font(26)
    fs = font(22)

    # 峰值点
    for name, d, h, label in PEAKS:
        x, y = px(d, h)
        dr.line([(x, y), (x, y - 70)], fill=RED, width=3)
        dr.ellipse([x - 9, y - 9, x + 9, y + 9], fill=RED, outline=(255, 255, 255), width=2)
        tw = dr.textlength(label, font=fs)
        dr.rectangle([x - 6, y - 106, x + tw + 10, y - 72], fill=(255, 255, 255))
        dr.text((x, y - 102), label, font=fs, fill=RED)
    # 5 psi 插值峰值
    d5, h5, lab = INTERP_PEAK
    x, y = px(d5, h5)
    dr.ellipse([x - 11, y - 11, x + 11, y + 11], outline=BLUE, width=4)
    dr.line([(x, y + 14), (x - 40, y + 120)], fill=BLUE, width=2)
    dr.text((x - 150, y + 124), lab, font=fs, fill=BLUE)

    # 底边读点
    for name, d, label in GROUND:
        x, y = px(d, 0)
        y = 1134
        dr.polygon([(x, y - 13), (x - 11, y + 7), (x + 11, y + 7)], fill=GREEN)
        dr.line([(x, y + 8), (x, 1105)], fill=GREEN, width=2)
        dr.text((x - 34, 1092), label, font=fs, fill=GREEN)
    x, _ = px(INTERP_GROUND[0], 0)
    dr.polygon([(x, 1121), (x - 11, 1141), (x + 11, 1141)], outline=GREEN, width=3)
    dr.text((x - 40, 1152), INTERP_GROUND[1], font=fs, fill=GREEN)

    # 5,000 ft 爆高上限线（§3.73 匀质大气假设边界），提示 1 Mt 外推
    y5k = Y0 - YST * 5000 / 500
    dr.line([(120, y5k), (1630, y5k)], fill=(150, 60, 180), width=2)
    dr.text((126, y5k + 4), "HOB 5,000 ft — §3.73 homogeneous-atmosphere limit",
            font=fs, fill=(150, 60, 180))

    dr.text((126, 128), "Fig. 3.73c (printed p.115) — 1 kt, peak overpressure on the ground",
            font=f, fill=(20, 20, 20))

    crop = im.crop((95, 100, 1700, 1190))
    out = OUT / "fig3-73c_peaks_marked.png"
    crop.save(out)
    print("saved", out, crop.size)


# ── 图 7.42 ────────────────────────────────────────────────────────────────
THERMAL = {
    "15 kt": {"x": 1756, "y": [1528.0, 1614.5, 1688.5, 1746.5, 1883.5, 1997.0]},
    "100 kt": {"x": 2391, "y": [1279.5, 1339.0, 1410.0, 1467.5, 1590.5, 1690.0]},
    "1 Mt": {"x": 3194, "y": [983.5, 1045.0, 1100.5, 1146.0, 1241.0, 1329.5]},
}
QLAB = ["4.5", "6", "8", "10", "15", "25"]


def mi_of(y_px):
    return 10 ** (2 - (y_px - 212.0) / 783.67)


def fig_742():
    im = Image.open(TMP / "fig7242_hi_rot.png").convert("RGB")
    dr = ImageDraw.Draw(im)
    f, f2 = font(30), font(26)
    for name, col in THERMAL.items():
        x = col["x"]
        dr.line([(x, 330), (x, 2350)], fill=(210, 40, 40), width=3)
        dr.text((x - 40, 280), name, font=f, fill=(190, 20, 20))
        for i, y in enumerate(col["y"]):
            mi = mi_of(y)
            used = i in (0, 3)
            c = GREEN if used else (145, 145, 145)
            r = 15 if used else 8
            dr.ellipse([x - r, y - r, x + r, y + r],
                       outline=c, width=4 if used else 2)
            tag = f"{mi:.2f} mi"
            if used:
                tag += f"  = {QLAB[i]} cal/cm2 *"
            dr.text((x + 26, y - 15), tag, font=f2, fill=c)
    dr.text((1500, 2360),
            "* 4.5 and 10 cal/cm2 are the rows used in the data table (2nd- and 3rd-degree burns)",
            font=font(24), fill=GREEN)
    box = (1450, 250, 3790, 2420)
    crop = im.crop(box)
    out = OUT / "fig7-42_columns_marked.png"
    crop.save(out)
    print("saved", out, crop.size)


fig_373c()
fig_742()
