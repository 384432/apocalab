# -*- coding: utf-8 -*-
"""读图前的标定闸门。

任何脚本在用 p113_600.png / p115_600.png 取数之前，必须先跑这个文件；四个断言
任一偏差超过 1%，立刻以非零退出码中止。它只验标定，不读数据、不改任何文件。

四条断言
--------
A1  p113 x：手册 p.112 算例「地面距离 400 ft、爆高 500 ft 处为 50 psi」→
    在 HOB 500 行读到 50 psi 曲线的横坐标，必须落在 400 ft ±1%。
    用轴标数字拟合出的原点（X0_LABEL）；图框原点（X0_FRAME = 348.5）的读数一并打印，
    因为两者差 6–8 ft，正是 plan §22 记录的那处系统偏移。
A2  p113 y：左侧 6 个轴标数字中心间距 = 2 个网格格高，且轴域 0–1000 ft →
    每格 100 ft；由标签反推的 PYF 必须在 2.2540 的 ±1% 内。
A3  p115 x：已签核的 1 psi 接触爆底边 3830 ft（effects.json）→
    底边交点读数必须在 3830 ±1%。
A4  p115 y：左侧 6 个轴标中心间距 487.4 px = 1000 ft，网格每格 500 ft。

注释里记着两轮踩过的错，改这个文件之前先读它们
------------------------------------------------
* 2026-11-18（p115 纵轴，错 2.5 倍）：把「244 px = 200 ft/格」当成 p115 的纵轴标定
  （PYF 1.22），而实测轴标间距 487.4 px = 1000 ft、每格 500 ft（PYF 0.4874）。
  后果：HOB 被放大约 2.5 倍，那一轮 p115 的 HOB 500 行读数（1,233 ft，plan §20.3）实际取的是
  HOB≈1240 处，数值无效（plan §21.2 保留原数字并标注作废原因）。
  **注意 1,310.1 ft 不是 p115 的值**：它属于 p113（Fig. 3.73b），作废原因是判据变更（原读法
  取 HOB 500 行，新判据改为读鼻尖 1,467.3 ft；p113 纵轴标定两轮均正确，A2 偏差 0.188%）。
  两者作废原因不同：p113 是判据换位置，p115 是标定错。
  A4 就是为了不再犯这个错：它把「轴标间距 ↔ 网格格高 ↔ 每格 ft」三者绑在一起，
  一旦有人再按 200 ft/格 去算，PYF 立刻差 150%，脚本当场中止。
* 2026-11-18（p113 x，6–8 ft 系统偏移）：p113 底部的 x 轴标数字中心比图框/网格整体右移
  14.3 px（约 6.4 ft），且右端偏移到 20 px（约 9 ft），即标签锚与图框锚之间存在一个
  小比例差 + 常数偏。此前一律用图框锚 348.5，导致 50 psi 算例读成 404.9 ft（+1.2%），
  而标签锚读成 397.9 ft（−0.5%）。A1 用标签锚判定，同时打印图框锚读数，两者都进记录。

用法
----
    python scripts/verify_calibration.py            # 正常校验
    python scripts/verify_calibration.py --json out.json
    python scripts/verify_calibration.py --p115-y-grid-ft 200   # 故意复现旧错，必须中止
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _imgdep  # noqa: E402  默认解释器可能没有 numpy/Pillow，缺包时自动换解释器重跑

_imgdep.ensure()

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGDIR = ROOT / ".tmp_handbook"
P113 = FIGDIR / "p113_600.png"
P115 = FIGDIR / "p115_600.png"

# 图框锚（历史值，读数仍以它为准，便于与已签核数据对账）
P113_X0, P113_PXF = 348.5, 2.2467
P113_Y0, P113_PYF = 2521.5, 2.2540
P115_X0, P115_PXF = 272.5, 0.4840
P115_Y0, P115_PYF = 2715.5, 0.4874

# 轴标间距的实测基线（2026-11-18 复核）
P113_LABEL_PX = 450.0     # 6 个轴标、200 ft 一档
P115_LABEL_PX = 487.4     # 6 个轴标、1000 ft 一档

TOL = 0.01                # 1%
INK = 120                 # 二值阈值，与各读图脚本一致


def load(path: pathlib.Path) -> np.ndarray:
    if not path.exists():
        sys.exit(f"缺图：{path}。没有 600 dpi 渲染就无法校验标定，中止。")
    return np.asarray(Image.open(path).convert("L")).astype(np.uint8) < INK


def groups(idx, gap):
    out = []
    if len(idx) == 0:
        return out
    s = p = idx[0]
    for i in idx[1:]:
        if i - p <= gap:
            p = i
        else:
            out.append((s, p))
            s = p = i
    out.append((s, p))
    return out


def clusters(mask, axis, lo, hi, gap, min_span):
    """axis=1 按列聚（返回 x 中心），axis=0 按行聚（返回 y 中心）。"""
    prof = mask.sum(axis=0) if axis == 1 else mask.sum(axis=1)
    idx = np.flatnonzero(prof[lo:hi] > 0) + lo
    res = []
    for s, e in groups(idx, gap):
        if e - s + 1 < min_span:
            continue
        w = prof[s:e + 1].astype(float)
        c = float((np.arange(s, e + 1) * w).sum() / w.sum())
        res.append(c)
    return res


def grid_lines(mask, axis, lo, hi, fill=0.25):
    """找出贯穿图区的网格线位置。

    axis=1（竖线）：lo..hi 是**行带**，按列求填充率 —— 竖线在行带上才连成一条。
    axis=0（横线）：lo..hi 是**列带**，按行求填充率 —— 横线在列带上才连成一条。
    """
    if axis == 1:
        band = mask[lo:hi, :]
        prof = band.sum(axis=0) / band.shape[0]
    else:
        band = mask[:, lo:hi]
        prof = band.sum(axis=1) / band.shape[1]
    peaks = [i for i in range(2, len(prof) - 2)
             if prof[i] > fill and prof[i] >= prof[i - 1] and prof[i] >= prof[i + 1]]
    merged = []
    for p in peaks:
        if merged and p - merged[-1][-1] <= 6:
            merged[-1].append(p)
        else:
            merged.append([p])
    return [float(np.mean(g)) for g in merged]


def row_crossings(mask, y, x0, x1, band=2, thr=2, gap=3):
    """在一行（±band）内所有墨迹簇的中心像素与宽度。"""
    seg = mask[y - band:y + band + 1, x0:x1]
    cnt = seg.sum(axis=0)
    out = []
    for s, e in groups(np.flatnonzero(cnt >= thr), gap):
        w = cnt[s:e + 1].astype(float)
        c = float((np.arange(s, e + 1) * w).sum() / w.sum())
        out.append((c + x0, e - s + 1))
    return out


def lsq(pairs):
    """最小二乘 y = a + b·x，返回 (a, b, max|resid|)。"""
    xs = np.array([p[0] for p in pairs], float)
    ys = np.array([p[1] for p in pairs], float)
    b, a = np.polyfit(xs, ys, 1)
    resid = float(np.max(np.abs(ys - (a + b * xs))))
    return float(a), float(b), resid


class Result:
    def __init__(self):
        self.rows = []
        self.failed = False

    def check(self, name, measured, expected, dev, tol=TOL, note=""):
        good = abs(dev) <= tol
        if not good:
            self.failed = True
        self.rows.append(dict(assertion=name, measured=measured, expected=expected,
                              deviation_pct=round(dev * 100, 3), tol_pct=tol * 100,
                              ok=good, note=note))
        print("  %s  %-52s %12s  vs %-12s %+7.3f%%  (容差 %.1f%%)%s"
              % ("PASS" if good else "FAIL", name, measured, expected,
                 dev * 100, tol * 100, ("  " + note) if note else ""))
        return good


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--p113-y-grid-ft", type=float, default=100.0,
                    help="p113 纵向每格 ft（实测 100）")
    ap.add_argument("--p115-y-grid-ft", type=float, default=500.0,
                    help="p115 纵向每格 ft（实测 500；传 200 可复现旧错）")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    R = Result()
    m113 = load(P113)
    m115 = load(P115)

    print("=" * 100)
    print("A1  p113 x：手册算例 50 psi @ (400 ft, HOB 500)")
    # x 轴标：底部数字行带。p113 的数字在 y 2555..2625
    lab_x = clusters(m113[2555:2625, :], axis=1, lo=300, hi=3620, gap=28, min_span=20)
    if len(lab_x) < 6:
        sys.exit(f"A1 中止：p113 底部只识别到 {len(lab_x)} 个轴标，无法定标。")
    # 前 6 个标签对应 0/200/400/600/800/1000（更远的簇会混进轴标题）
    six = lab_x[:6]
    a, b, resid = lsq([(i * 200.0, c) for i, c in enumerate(six)])
    x0_label = a
    pxf_label = b
    print("     轴标 x 中心：%s" % ", ".join("%.1f" % v for v in six))
    print("     拟合：x = %.2f + %.4f·d   （残差 ≤ %.1f px）" % (x0_label, pxf_label, resid))

    y500 = int(round(P113_Y0 - 500 * P113_PYF))
    # HOB 500 行被 500 那条横网格压住，取相邻两行读同一条近竖直曲线再平均
    picks = []
    for hob in (490, 510):
        yy = int(round(P113_Y0 - hob * P113_PYF))
        for c, w in row_crossings(m113, yy, int(P113_X0), int(P113_X0 + 460 * P113_PXF)):
            d_frame = (c - P113_X0) / P113_PXF
            if 395.0 <= d_frame <= 415.0 and w <= 12:
                picks.append(c)
                break
    if not picks:
        sys.exit("A1 中止：HOB 490/510 两行都没找到 50 psi 曲线。")
    x50 = float(np.mean(picks))
    d_label = (x50 - x0_label) / pxf_label
    d_frame = (x50 - P113_X0) / P113_PXF
    print("     50 psi 曲线像素 x = %.1f（HOB 490/510 各一次：%s）"
          % (x50, ", ".join("%.1f" % p for p in picks)))
    print("     轴标锚读数 %.1f ft / 图框锚读数 %.1f ft（已知系统偏移 %+.1f ft）"
          % (d_label, d_frame, d_frame - d_label))
    R.check("A1 p113 x: 50 psi @ HOB 500 → 400 ft（轴标锚）", round(d_label, 1), 400.0,
            (d_label - 400.0) / 400.0)
    R.check("A1b p113 x: 图框锚偏差（已知 +1~2%，只作护栏）", round(d_frame, 1), 400.0,
            (d_frame - 400.0) / 400.0, tol=0.03,
            note="plan §22 记录的 6–8 ft 偏移")

    print("A2  p113 y：轴标间距 ↔ 网格格高")
    yl = clusters(m113[:, 200:330], axis=0, lo=200, hi=2560, gap=12, min_span=20)
    yl = [y for y in yl if y > 240]
    print("     轴标 y 中心：%s" % ", ".join("%.1f" % v for v in yl))
    if len(yl) != 6:
        sys.exit(f"A2 中止：p113 左侧轴标应为 6 个，实测 {len(yl)} 个。")
    lsq_a, lsq_b, lsq_r = lsq([(i * 200.0, c) for i, c in enumerate(sorted(yl))])
    label_px = abs(lsq_b) * 200.0
    print("     轴标间距 %.1f px（拟合 200 ft/档，残差 ≤ %.1f px）" % (label_px, lsq_r))
    R.check("A2a p113 y: 轴标间距 / 实测基线 450.0 px", round(label_px, 1), P113_LABEL_PX,
            (label_px - P113_LABEL_PX) / P113_LABEL_PX)
    grows = grid_lines(m113, axis=0, lo=400, hi=3600, fill=0.25)
    grows = [y for y in grows if 280 < y < 2508]
    dg = np.diff(sorted(grows))
    dg = dg[(dg > 180) & (dg < 280)]
    grid_px = float(np.median(dg))
    print("     横网格 %d 条，格高中位数 %.1f px（间距样本 %s）"
          % (len(grows), grid_px, ", ".join("%.0f" % v for v in dg)))
    R.check("A2b p113 y: 轴标间距 = 2 × 格高",
            round(label_px / grid_px, 3), 2.0, (label_px / grid_px - 2.0) / 2.0)
    pyf_meas = label_px / 200.0
    R.check("A2c p113 y: PYF（标签反推）vs 2.2540", round(pyf_meas, 4), P113_PYF,
            (pyf_meas - P113_PYF) / P113_PYF)
    cell_ft = grid_px / pyf_meas
    R.check("A2d p113 y: 每格 ft vs 声明值 %.0f" % args.p113_y_grid_ft,
            round(cell_ft, 1), args.p113_y_grid_ft,
            (cell_ft - args.p113_y_grid_ft) / args.p113_y_grid_ft)

    print("A3  p115 x：已签核的 1 psi 接触爆底边 3830 ft")
    # 1 psi 曲线在底边是斜的（每升高 1 ft 右移约 2.7 ft），已签核值是把 h=15..40
    # 四点外推到 HOB=0 得到的，所以这里也外推，不能直接取某一行。
    pts = []
    for hob in (15, 20, 25, 30, 35, 40):
        yy = int(round(P115_Y0 - hob * P115_PYF))
        cand = [c for c, w in row_crossings(m115, yy, 285, 3885)
                if 3600.0 <= (c - P115_X0) / P115_PXF <= 4000.0]
        if cand:
            pts.append((float(hob), (max(cand) - P115_X0) / P115_PXF))
    if len(pts) < 4:
        sys.exit("A3 中止：底边找到的 1 psi 交点少于 4 个，无法外推到 HOB=0。")
    slope, icept = np.polyfit([p[0] for p in pts], [p[1] for p in pts], 1)
    hero = float(icept)
    print("     h→0 外推：h=15..40 六点 %s，斜率 %.2f ft/ft"
          % (", ".join("%.0f" % p[1] for p in pts), slope))
    R.check("A3 p115 x: 1 psi 底边 → 3830 ft", round(hero, 1), 3830.0,
            (hero - 3830.0) / 3830.0)

    print("A4  p115 y：轴标间距 ↔ 网格格高（旧错就死在这一条）")
    yl5 = clusters(m115[:, 150:262], axis=0, lo=200, hi=2760, gap=12, min_span=20)
    yl5 = [y for y in yl5 if y > 240]
    print("     轴标 y 中心：%s" % ", ".join("%.1f" % v for v in yl5))
    if len(yl5) != 6:
        sys.exit(f"A4 中止：p115 左侧轴标应为 6 个，实测 {len(yl5)} 个。")
    a5, b5, r5 = lsq([(i * 1000.0, c) for i, c in enumerate(sorted(yl5))])
    label_px5 = abs(b5) * 1000.0
    print("     轴标间距 %.1f px = 1000 ft（拟合残差 ≤ %.1f px）" % (label_px5, r5))
    R.check("A4a p115 y: 轴标间距 / 实测基线 487.4 px", round(label_px5, 1), P115_LABEL_PX,
            (label_px5 - P115_LABEL_PX) / P115_LABEL_PX)
    gcol = grid_lines(m115, axis=0, lo=300, hi=3800, fill=0.25)
    gcol = [y for y in gcol if 200 < y < 2760]
    d5 = np.diff(sorted(gcol))
    d5 = d5[(d5 > 180) & (d5 < 320)]
    grid_px5 = float(np.median(d5))
    print("     横网格 %d 条，格高中位数 %.1f px" % (len(gcol), grid_px5))
    R.check("A4b p115 y: 轴标间距 = 2 × 格高",
            round(label_px5 / grid_px5, 3), 2.0,
            (label_px5 / grid_px5 - 2.0) / 2.0)
    pyf5 = label_px5 / 1000.0
    R.check("A4c p115 y: PYF（标签反推）vs 0.4874", round(pyf5, 4), P115_PYF,
            (pyf5 - P115_PYF) / P115_PYF)
    cell5 = grid_px5 / pyf5
    R.check("A4d p115 y: 每格 ft vs 声明值 %.0f" % args.p115_y_grid_ft,
            round(cell5, 1), args.p115_y_grid_ft,
            (cell5 - args.p115_y_grid_ft) / args.p115_y_grid_ft,
            note="传 --p115-y-grid-ft 200 就是 2026-11-18 那个 2.5 倍错")

    print("=" * 100)
    bad = [r for r in R.rows if not r["ok"]]
    print("结果：PASS %d  FAIL %d" % (len(R.rows) - len(bad), len(bad)))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(dict(
            figure_dir=str(FIGDIR), tol_pct=TOL * 100,
            anchors=dict(p113_frame=[P113_X0, P113_PXF, P113_Y0, P113_PYF],
                         p113_label=[round(x0_label, 2), round(pxf_label, 4)],
                         p115_frame=[P115_X0, P115_PXF, P115_Y0, P115_PYF]),
            assertions=R.rows, ok=not R.failed), ensure_ascii=False, indent=2),
            encoding="utf-8")
        print("wrote", args.json)
    if R.failed:
        print("标定未通过 —— 不许用它取任何数。")
        for r in bad:
            print("  FAIL %s：实测 %s，应为 %s，偏差 %+.3f%%"
                  % (r["assertion"], r["measured"], r["expected"], r["deviation_pct"]))
        return 1
    print("标定通过，可以读图。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
