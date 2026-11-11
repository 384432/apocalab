# -*- coding: utf-8 -*-
"""Replace the mangled phase-2 memory block with a clean one.

The first attempt passed this text through `python -c "..."`, where backticks were
evaluated by the shell and every `code span` was replaced with empty output. This
script rewrites the block from an anchor.
"""
import pathlib

P = pathlib.Path(__file__).resolve().parent.parent / ".workbuddy" / "memory" / "2026-11-11.md"
text = P.read_text(encoding="utf-8")
anchor = "## 阶段 2（2026-11-11 下午）"
i = text.find(anchor)
if i < 0:
    raise SystemExit("anchor not found — nothing to replace")
head = text[:i].rstrip() + "\n"

block = """## 阶段 2（2026-11-11 下午）

### plan.md v1.2 回滚 + v1.3 追加

林更正：城市页 80 是我记错了口径 —— 80 是**首月总页量**，城市页固定 **20 个**。

- v1.2：删掉「城市页扩到 80 页」整段（-16h）与那个阶段；工时回 70–85h；§6.1 重写成
  「80 = 核心 8 + 城市 20 + 武器 12 + 约 40 个有独立搜索量的灾害/查询页，靠页面类型补齐」。
  **不许说「压缩」** —— 那是本来就不该有的工时。
- v1.3：① og:image 升级为**硬约束**：构建期生成的 PNG 1200×630，SVG 一律不接受，
  也不许运行时渲染（分享卡片由抓取器拉取，它不执行我们的脚本）；② 标题不许承诺页面上
  没有的功能 —— 人口层上线前首页 title 不出现 population。
- 两个 patch 脚本都带命中断言，命中数不对就整体不写盘：
  `scripts/patch_plan_v12.py`、`scripts/patch_plan_v13.py`。
- 备份链：`plan.v1.0.bak.md` → `plan.v1.1.bak.md` → `plan.v1.2.bak.md`（`*.bak.md` 已 gitignore）。

### 已上线

- 公网：https://apocalab.app.workbuddy.host/?sharecode=MGFRWEMR3E
  （应用名「核武器效应数据站」，locator `wbapp_gFR2qf0cBDy3D2VBx9ny4J`，与 plan 那个应用分开）
- 仓库：https://github.com/384432/apocalab （private，gh 账号 384432）
- 部署姿势：`astro build` → 复制 `dist/` 到 `.deploy/` → `workbuddy_sites_deploy(language=static)`。
  **不能直接指 `dist`：部署工具会把 dist 当构建产物排除，上传成空站。**
- 同目录重复部署要带 `appId`（从 `.workbuddy/applications.yaml` 的 locator 取），否则会要求选择应用。

### 新增文件

```
src/lib/cities.ts                20 城类型化访问（GeoNames 坐标，非行政中心）
src/lib/panel.ts                 面板所有字符串的唯一来源（SSR 与数据岛共用，防漂移）
src/components/ResultPanel.astro SSR 默认态 + SVG 真比例圆 + JSON 岛 + 内联切换脚本
src/data/cities.json             20 城 slug/经纬度/geonameid（build_cities.py 生成）
scripts/fetch_geonames.py        下载 cities15000（校验大小 + zip 可打开，不只看存在）
scripts/build_cities.py          GeoNames → cities.json（20 城全部按国别 + admin1 对上）
scripts/measure_switch.mjs       切当量耗时（CDP 实测）
scripts/verify_switch.mjs        切换是否真的改了数值（防「很快但没动」）
scripts/verify_share_url.mjs     冷启 `?city=&yield=&burst=` 还原状态
scripts/verify_js_off.mjs        关 JS 后首屏是否仍在 HTML
scripts/verify_layout.mjs        390 / 1280 宽度溢出与圆几何
```

### 浏览器实测（无头 Chromium + CDP，本机现成）

- 二进制：`%LOCALAPPDATA%\\ms-playwright\\chromium-1248\\chrome-win64\\chrome.exe`，
  起 `--remote-debugging-port=9333`；Node 22 自带 WebSocket，**不需要装 playwright 包**。
- **切当量**：同步 DOM 工作 0.4–1.1 ms，到下一帧 7.4–33.9 ms（门槛 300 ms，余量两个数量级）。
- **关 JS**：`?city=new-york&yield=100` 五个数与出处仍在 HTML；控件 `display:none`；回退段落可见。
- **已知边界**：关 JS 时其他组合（如 `?city=tokyo&yield=1000`）不会还原 —— 静态站没法按 query
  生成变体。已在回退段落里写明并指向 `/blast-radius/`，没有假装支持。
- 布局：390 / 1265 px 均 0 横向溢出，SVG 312 / 283 px。

### 闸门

- `verify_data.py` 354 项；`check_site.py` **285 项**（新增 11 节：阶段 2 默认态、
  数据岛与 effects.json 逐条比对、脚本数 = 3 且无网络请求、URL 参数、关 JS 回退、
  标题不得承诺未上线功能、title ≤ 65 / description 110–158 / title ≠ H1）。
- 自查发现并修掉：三页 description 原本 197 / 170 / 192 字符，结果页会截断 → 改到 150 / 144 / 141。

### 三维度标题口径（本轮产出，后续页沿用）

- `/`：Nuke Simulator: Blast Radius for Any City, 15 kt to 1 Mt
- `/blast-radius/`：Nuclear Bomb Blast Radius, 15 kt to 1 Mt — Table With Sources
- `/methodology/`：Methodology — How the Blast Radius Numbers Were Obtained

### 坑（本项目专属）

- **别用 `python -c "..."` 发长中文**：双引号里的反引号被 shell 当命令替换，
  `` `code` `` 静默变空，退出码还是 0。写记忆/文档一律先 Write 一个 `.py` 再执行。
- 临时输出别落在仓库根：调试用的 `g1.txt` / `st.txt` 被 `git add -A` 吃进暂存。
  已加 `/*.txt` 忽略。
- GeoNames zip 第一次下载被工具超时打断，留下 0 字节文件；脚本 `exists()` 直接复用了坏文件。
  下载器必须校验（大小 + zipfile 能打开）。
"""

P.write_text(head + block, encoding="utf-8")
print("rewritten:", len(head + block), "chars")
