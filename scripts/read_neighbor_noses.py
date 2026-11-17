# -*- coding: utf-8 -*-
"""同图邻线检查：读 Fig. 3.73b（p.113）上 15 / 20 / 30 psi 三条等压线的鼻尖。

方法与 10 psi 鼻尖完全同一套（列扫 + 竖直行程）：在窗口内从右往左扫列，第一个出现
连续 ≥40 px 竖直行程的列就是这条曲线的最外侧点；鼻尖 HOB 取该行程的竖直中心。

窗口是逐条定的，右边界压在印刷标号（"15" / "20" / "30"）与下一条竖直网格线之间：
  * 竖直网格线是实线，行程贯穿整个窗口，比曲线更"长"，所以窗口右界必须收在
    目标曲线外侧、下一条网格线内侧，否则扫到的会是网格。
  * 印刷标号是实心笔画，也会形成长行程，所以窗口上下界要躲开标号所在的高度。
自检：20 psi 用同一流程重读，必须复现已签核的 928.0 ft。

两条判据（plan §22）：
  a 单调：d(15) > d(20) > d(30)，且峰值高度随 psi 升高而下移（HOB 递减）
  b 插值：t = ln(20/15)/ln(30/15)，用 15 与 30 插 20；主判据 ln d 插值、旁证 d 线性插值，
    门槛都是 ≤5%，但两条线分开报不合并

用法：python scripts/read_neighbor_noses.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _imgdep  # noqa: E402  缺 numpy/Pillow 时自动换解释器重跑

_imgdep.ensure()

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG = ROOT / ".tmp_handbook" / "p113_600.png"
GATE = ROOT / "scripts" / "verify_calibration.py"

X0, PXF, Y0, PYF = 348.5, 2.2467, 2521.5, 2.2540     # 图框锚，与已签核数据同一套
X0_LABEL, PXF_LABEL = 360.68, 2.2545                 # 轴标锚，verify_calibration A1 拟合值
INK = 120
SIGNED_20, SIGNED_20_HOB = 928.0, 612.0
MINLEN = 40                                          # 与 10 psi 同一门槛（≈18 ft）


def gate() -> None:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        sys.exit("标定闸门未通过，拒绝读图。")
    tail = [l for l in r.stdout.splitlines() if l.startswith("结果")]
    print("标定闸门：" + (tail[0] if tail else "通过"))


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


def col_runs(mask, x, y0, y1, minlen=MINLEN):
    col = mask[y0:y1, x]
    idx = np.flatnonzero(col)
    segs = []
    if len(idx):
        s = p = idx[0]
        for i in idx[1:]:
            if i - p <= 2:
                p = i
            else:
                segs.append((s, p))
                s = p = i
        segs.append((s, p))
    return [(s, e) for s, e in segs if e - s + 1 >= minlen]


def nose(mask, h_lo, h_hi, d_lo, d_hi):
    y0 = int(round(Y0 - h_hi * PYF))
    y1 = int(round(Y0 - h_lo * PYF))
    for x in range(int(X0 + d_hi * PXF), int(X0 + d_lo * PXF), -1):
        rs = col_runs(mask, x, y0, y1)
        if rs:
            s, e = max(rs, key=lambda r: r[1] - r[0])
            hob = (Y0 - (y0 + (s + e) / 2.0)) / PYF
            span = (e - s + 1) / PYF
            return x, (x - X0) / PXF, hob, span
    return None


def row_at(mask, hob, d_lo, d_hi, maxw=20):
    """某一行窗口内所有墨迹簇的 d（含该处的网格线），用来核对「是不是同一条线」。"""
    y = int(round(Y0 - hob * PYF))
    xa, xb = int(X0 + d_lo * PXF), int(X0 + d_hi * PXF)
    cnt = mask[y - 2:y + 3, xa:xb].sum(axis=0)
    out = []
    for s, e in groups(np.flatnonzero(cnt >= 2), 3):
        if e - s + 1 > maxw:
            continue
        w = cnt[s:e + 1].astype(float)
        c = float((np.arange(s, e + 1) * w).sum() / w.sum())
        out.append(round((c + xa - X0) / PXF, 1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    gate()
    a = np.asarray(Image.open(FIG).convert("L")).astype(np.uint8)
    mask = a < INK

    plan = [
        ("15 psi", 600, 700, 1100, 1210, 0),
        ("20 psi", 570, 660, 840, 935, 0),
        ("30 psi", 460, 580, 590, 650, 0),
    ]
    out = {}
    for name, h_lo, h_hi, d_lo, d_hi, probe in plan:
        got = nose(mask, h_lo, h_hi, d_lo, d_hi)
        if not got:
            sys.exit(f"{name}：窗口 HOB {h_lo}..{h_hi} / d {d_lo}..{d_hi} 内没有长行程。")
        x, d, hob, span = got
        d_lab = (x - X0_LABEL) / PXF_LABEL
        probes = {h: row_at(mask, h, d_lo, d_hi)
                  for h in (int(round(hob)) - 40, int(round(hob)) + 20)}
        out[name] = dict(window=[h_lo, h_hi, d_lo, d_hi], x_px=x,
                         d_frame=round(d, 1), d_label=round(d_lab, 1),
                         hob=round(float(hob), 1), run_span_ft=round(float(span), 1),
                         crossings_at={str(k): v for k, v in probes.items()})
        print("\n%s  （窗口 HOB %d..%d, d %d..%d）" % (name, h_lo, h_hi, d_lo, d_hi))
        print("   鼻尖 x_px=%7.1f  d(图框锚)=%7.1f ft  d(轴标锚)=%7.1f ft  HOB=%5.1f ft"
              % (x, d, d_lab, hob))
        print("   该列竖直行程 %.0f ft" % span)
        for k, v in probes.items():
            print("   同线核对（鼻尖前后各一行）HOB %d 全部交点：%s" % (k, v))

    d15, h15 = out["15 psi"]["d_frame"], out["15 psi"]["hob"]
    d20, h20 = out["20 psi"]["d_frame"], out["20 psi"]["hob"]
    d30, h30 = out["30 psi"]["d_frame"], out["30 psi"]["hob"]

    print("\n" + "=" * 92)
    print("判据 a（单调）")
    a1, a2 = d15 > d20 > d30, h15 > h20 > h30
    print("   d：  %.1f > %.1f > %.1f  → %s" % (d15, d20, d30, "PASS" if a1 else "FAIL"))
    print("   HOB：%.1f > %.1f > %.1f（psi 越高峰越低）→ %s"
          % (h15, h20, h30, "PASS" if a2 else "FAIL"))
    print("   自检：20 psi 复现 %.1f @ HOB %.0f，已签核 %.1f @ HOB %.0f，差 %+.2f%%"
          % (d20, h20, SIGNED_20, SIGNED_20_HOB, (d20 - SIGNED_20) / SIGNED_20 * 100))

    print("判据 b（插值，判据取 ≤5%）")
    t = math.log(20 / 15) / math.log(30 / 15)
    lg = math.exp(math.log(d15) + t * (math.log(d30) - math.log(d15)))
    lin = d15 + t * (d30 - d15)
    e_lg = (d20 - lg) / lg * 100
    e_lin = (d20 - lin) / lin * 100
    print("   t = ln(20/15)/ln(30/15) = %.5f" % t)
    print("   主判据 ln d 插值：预测 %7.1f，实测 %7.1f，相对误差 %+.2f%%" % (lg, d20, e_lg))
    print("   旁证 d 线性插值：预测 %7.1f，实测 %7.1f，相对误差 %+.2f%%" % (lin, d20, e_lin))
    b_ok = abs(e_lg) <= 5.0 and abs(e_lin) <= 5.0
    print("   两条线分开报不合并（门槛都是 ≤5%%，余量看各自误差）→ %s" % ("PASS" if b_ok else "FAIL"))

    verdict = "signed" if (a1 and a2 and b_ok) else "unsigned"
    print("\nverdict = %s（a=%s  b=%s）" % (verdict, a1 and a2, b_ok))

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(dict(
            figure="p113_600.png", anchor_frame=[X0, PXF, Y0, PYF],
            anchor_label=[X0_LABEL, PXF_LABEL], minlen_px=MINLEN, noses=out,
            criterion_a=dict(monotone_d=bool(a1), monotone_hob=bool(a2)),
            criterion_b=dict(t=round(t, 5), ln_pred=round(lg, 1), d_pred=round(lin, 1),
                             err_ln_pct=round(e_lg, 2), err_d_pct=round(e_lin, 2), ok=bool(b_ok)),
            signed_20_reproduced=round(d20, 1), verdict=verdict),
            ensure_ascii=False, indent=2), encoding="utf-8")
        print("wrote", args.json)
    return 0 if verdict == "signed" else 1


if __name__ == "__main__":
    sys.exit(main())
