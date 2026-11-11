# apocalab.com — 项目长期约定

## 数据规则（不可协商）

- 唯一数据源：《The Effects of Nuclear Weapons》3rd ed. 1977（公有领域）。任何数字必须能落到
  「章 / 图号或公式号 / **印刷页**」。PDF 页 ≠ 印刷页，引用一律用印刷页。
- 两套 PDF 偏移量不要混用：整本 `EoNW/6852629.pdf` 里第 3 章 = 印刷页 + 9；分章 `eonw_3.pdf` = +79。
- 数值只允许三种来源：手册公式直算、图上直读、手册自己写的立方根缩放。**不允许本站拟合**。
- 缩放值必须带固定标签 `scaled from the 1 kt curve (§3.61, p.101)`，且 JSON 里留 1 kt 基准 +
  像素坐标，任何人能复算。
- 5 psi 没有印线，必须写 `interpolated between 4 and 6 psi contours, at X ft`，页面与台账都要有。
- 热辐射三档直读 Fig. 7.42（p.291），不走缩放。该图**无文字层**，等值线标号由 §12.66(p.563) +
  §7.43(p.290) 反推为 4.5/6/8/10/15/25 —— 这件事必须写在 methodology，不能假装是读出来的。
- 地爆只给超压与火球（火球 145·W^0.4，p.71；空爆 110·W^0.4，p.70，**禁止混搭**），热辐射不做地爆，
  页面上要明写「不是漏了」。

## 页面规则

- 全站禁词：`education demo` / `prototype` / `demo` / `simulation model` / `our estimate`。
  校验用词边界（`demolish`/`demographic` 含 demo 子串）。
- 免责：每页**恰一行**，放 footer，只有一个 `<p>`。不做首屏条、不做副标题。
- 表格页必须 JS off 可读；每格带印刷页码。JSON-LD 是唯一允许的 `<script>`。
- 顺序：数据 → 骨架 → `/blast-radius/` 上线 → 地图。地图圈由自绘 Canvas 画，且
  `dragRotate:false / touchPitch:false / maxPitch:0`。

## 工程

- Astro 5 静态，`site=https://apocalab.com`，零运行时 JS。
- 本机装 node 包**先写 `.npmrc` 走 registry.npmmirror.com**，否则走代理会 ECONNRESET。
- 构建后必跑：`python scripts/verify_data.py`（354 项）+ `python scripts/check_site.py`（96 项）。
- `.tmp_handbook/`（PDF + 读图脚本）永不提交。
