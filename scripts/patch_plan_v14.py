# -*- coding: utf-8 -*-
"""
plan.md v1.3 -> v1.4

1. Adds §3.7: Cloudflare Pages is the delivery target, static only, no adapter,
   noindex on previews. This is the constraint that was in the brief and that my
   v1 plan dropped on the floor.
2. Replaces the §3.1 directory sketch with the tree that actually exists.
3. Corrects §3.2 / §3.6 to what was built (mercator.ts not projection.ts, 7 s
   upgrade window instead of a 4 s cliff, 138 KB geojson, +285 KB MapLibre).
"""
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent.parent / "plan.md"
text = P.read_text(encoding="utf-8")
edits = 0


def sub(old, new, count=1):
    global text, edits
    got = text.count(old)
    assert got == count, f"expected {count} hit(s), found {got}: {old[:70]!r}"
    text = text.replace(old, new, count)
    edits += 1


sub(
    "> 版本：**v1.3（2026-11-11 修订）**。阶段 0 数据层已通过抽检，阶段 1 骨架与 `/blast-radius/` 已上线，阶段 2 首页与查表已上线；第 8 节 5 个决策点已全部裁决，正文按裁决结果改过。",
    "> 版本：**v1.4（2026-11-11 修订）**。阶段 0 数据层已通过抽检，阶段 1 骨架与 `/blast-radius/`、阶段 2 首页与查表、阶段 3 `/nuclear-bomb-map/` 均已交付；交付形态自 v1.4 起锁定为 **Cloudflare Pages 静态站**（§3.7）。第 8 节 5 个决策点已全部裁决，正文按裁决结果改过。",
)

sub(
    "**v1.3 相对 v1.2 改了什么**（只列会改变行为的）：",
    """**v1.4 相对 v1.3 改了什么**（只列会改变行为的）：

1. **交付形态写回 Cloudflare Pages（§3.7）**。v1.0–v1.3 的计划里**根本没有部署一节**——这是漏项，不是取舍。结果阶段 2 我用平台自带托管交了一版预览，偏离了最初就定死的 Cloudflare Pages。现在补齐：`dist/` 静态产出、`output: 'static'`、不装 adapter、预览期 `_headers` 加 `noindex`、正式域名上线时删掉该行。
2. **§3.1 目录树改成真实结构**，不再写不存在的文件名。
3. **修正 §3.2 / §3.6 的三处实测偏差**：投影文件叫 `mercator.ts`；降级不是「4 s 超时悬崖」（降级层首帧就在，瓦片只是升级，窗口 7 s）；MapLibre 分块是 +285 KB gzip 而不是 +260 KB。
4. **三页 title / H1 重写并把分工写死（§4.1–4.3）**：`/` 主词 `nuke simulator`、`/blast-radius/` 主词 `nuclear bomb blast radius`、`/methodology/` 主词 `how nuclear blast radius is calculated`。首页 title 里不再出现 `blast radius`——两页打同一个词是自己在跟自己抢。四条 title 之间任意两页的最长共同词串不得超过 3 个词，`check_site.py` 断言。

**v1.3 相对 v1.2 改了什么**（只列会改变行为的）：""",
)

# ---- §3.1 the tree
sub(
    "  components/   ResultPanel / EffectTable / MapShell / Citation / SiteNav / Footnote\n"
    "  islands/      MapExplorer.ts        ← 唯一 hydrate 的组件\n"
    "  lib/          effects.ts / projection.ts / urlState.ts / population.ts / citation.ts\n"
    "  data/         effects.json / cities.json / fallout-cases.json / copy/\n"
    "scripts/        build_population.py / build_og.py / verify_data.py / build_ledger.py\n"
    "public/data/    cities-search-*.json / pop/<slug>.bin",
    "  components/   ResultPanel.astro（首页面板）/ RadiusCell.astro（表格单元格）/ BombMap.astro\n"
    "  lib/          effects.ts / panel.ts / island.ts / cities.ts / mercator.ts / site.ts\n"
    "  scripts/      bomb-map.ts           ← 全站唯一在浏览器里跑的地图脚本（动态 import MapLibre）\n"
    "  data/         effects.json / cities.json\n"
    "scripts/        build_effects.py / build_cities.py / verify_data.py / check_site.py / check_urls.py\n"
    "public/         ne_110m_land.geojson / favicon.svg / _headers / robots.txt",
)

# ---- §3.2 accuracy
sub(
    "由 `projection.ts` 自己算墨卡托投影，监听 `map.on('move')` 重绘。",
    "由 `lib/mercator.ts` 自己算墨卡托投影，监听 `map.on('move')` 重绘。",
)

sub(
    "- `map` 初始化失败 / style 加载超时 4s / 连续瓦片错误 → `basemap` 换成降级层，`rings` 照常，右下角一行 `Basemap unavailable — radii are still to scale.`。**不会出现永久的 Loading map。**",
    "- **降级层首帧就在，不是超时才出现**：HTML 一渲染完就先画轮廓 + 圈，瓦片只是在它之上淡入。所以「打不开」这件事不存在——只有「有没有真实底图」的区别。触发降级的条件只有两条：MapLibre 初始化抛错（含无 WebGL），或 7 s 内没跑完 `load`；style 就位之后的单张瓦片 / 字形 404 不算失败（MapLibre 会为单个资源报 error，圈不受影响）。降级时地图左下角出现一行 `Basemap unavailable — radii are still to scale.`",
)

sub(
    "自托管 Natural Earth 110m 陆地轮廓（公有领域，约 120 KB，随站打包 `public/geo/ne110m-land.json`）",
    "自托管 Natural Earth 110m 陆地轮廓（公有领域，138 KB 原始 / 约 40 KB gzip，随站打包 `public/ne_110m_land.geojson`）",
)

# ---- §3.6 budget accuracy
sub(
    "| 地图可见 | < 2 s（4G） | MapLibre 在 `requestIdleCallback` 后动态 `import()`；不阻塞首屏 |",
    "| 地图可见 | < 2 s（4G） | 首帧就是自绘轮廓 + 圈；MapLibre 动态 `import()` 后台升级，不阻塞首帧 |",
)
sub(
    "| JS 总量 | 首屏 < 40 KB，地图就绪后 +260 KB | 代码分割；`cities-search` 分片按需 |",
    "| JS 总量 | 首屏 < 40 KB，地图就绪后 +285 KB（gzip） | 代码分割；MapLibre 只在 `/nuclear-bomb-map/` 上按需加载 |",
)
sub(
    "| 降级 | 4 s 超时必定落到可用状态 | style 超时 + tile error 计数 |",
    "| 降级 | 可用状态在首帧即成立，不依赖任何网络请求 | 轮廓 + 圈先画；瓦片升级窗口 7 s |",
)

# ---- §4.1–4.3 titles, now that the three pages stop competing for one phrase
sub(
    "- Title（阶段 2 已上线）: `Nuke Simulator: Blast Radius for Any City, 15 kt to 1 Mt`\n"
    "- Title（人口层上线后恢复）: `Nuke Simulator: Blast Radius and Population for Any City`\n"
    "- H1（阶段 2 已上线）: `Pick a city, pick a yield — the rings are drawn to scale from the manual`",
    "- Title: `Nuke Simulator: What a Nuclear Bomb Would Do to Any City`（**不出现 `blast radius`**——那是 `/blast-radius/` 的词）\n"
    "- H1: `Nuke Simulator — see what a nuclear bomb would do to any city`\n"
    "- 人口层上线后：title 不变（主词已锁定 `nuke simulator`），只在 description 里加 10 km 人口；标题不跟着功能改，避免每次改版都丢一次相关性。",
)

sub(
    "- Title: `Nuclear Bomb Blast Radius, 15 kt to 1 Mt — Table With Sources`\n"
    "- H1: `Every nuclear bomb blast radius in this table points to a page in the 1977 manual`",
    "- Title: `Nuclear Bomb Blast Radius Table: 15 kt, 100 kt, 1 Mt`\n"
    "- H1: `Nuclear Bomb Blast Radius, with the printed page behind every number`",
)

sub(
    "- Title: `Nuclear Bomb Map — Drop a Pin Anywhere and See the Rings`\n"
    "- H1: `A nuclear bomb map with real scale, not a cartoon`\n"
    "- 与首页共用岛屿组件，差异在默认视角（世界 zoom 2）与文案侧重「地图」而非「模拟器」。\n"
    "- 导航一级项，首页与城市页都链过来。",
    "- Title: `Nuclear Bomb Map: Blast Rings on Real Ground, 20 Cities`\n"
    "- H1: `Nuclear Bomb Map — the rings on the ground, not on a chart`\n"
    "- 与首页共用 `lib/island.ts` + `panelRows()`，所以同一个组合在两页不可能显示不同的数；但**首页保留 SVG 真比例圆环，不用地图替换**——SVG 关 JS 也看得见，地图看不见，两者不是替代关系。\n"
    "- 默认视角 = 按该城最大半径自动 fit（16:9 画幅里外圈占短边 40%），不是固定世界 zoom：世界视图看不出任何一圈的相对大小。\n"
    "- 导航一级项，首页与城市页都链过来。",
)

# ---- §3.7 new section
sub(
    "## 4. 页面清单与逐页规格",
    """### 3.7 部署（Cloudflare Pages，静态，零适配器）

**这是硬约束，不是可选项。** 站点只以 Cloudflare Pages 的形式交付，理由不是偏好：整站的成立条件是「关掉 JS 也能读、没有服务端状态、CDN 直接吐 HTML」，一旦接了 adapter，Pages 就会去跑 Functions，这三个前提同时失效。

- **构建**：`npm run build`（即 `astro build`）→ `dist/`。`astro.config.mjs` 保持 `output: 'static'`，不装 `@astrojs/cloudflare` 或任何 adapter。`check_site.py` 断言配置里没有 `adapter:`、没有 `@astrojs/*`、`dist/` 里没有 `functions/`。
- **Pages 项目设置**：构建命令 `npm run build`，输出目录 `dist`，Node 20+。仓库根的 `wrangler.toml` 用 `pages_build_output_dir = "./dist"` 兜底，手工 `wrangler pages deploy` 也不会把仓库根当成产物。
- **预览期禁收录**：`public/_headers` 给 `/*` 加 `X-Robots-Tag: noindex`，避免 `*.pages.dev` 被搜成重复内容。**正式域名指向 Pages 之后必须删掉这一行**，否则生产页也带 noindex，整站从搜索结果里消失。`check_site.py` 断言这行在场，删文件就是构建失败，不会「顺手忘了」。
- **`_headers` 还负责 `.geojson` 的 MIME**：Pages 对未知扩展名默认 `application/octet-stream`，降级轮廓那条路径要它明确是 `application/json`。
- **交付物只有两种**：Cloudflare Pages 的预览链接（`*.pages.dev`，带 noindex）与正式域名 `apocalab.com`。平台自带的托管预览链接不再作为交付物，也不写进任何文档。

---

## 4. 页面清单与逐页规格""",
)

P.write_text(text, encoding="utf-8")
print(f"v1.4 applied, {edits} replacements")
print("bytes:", len(text))
if "3.7 部署" not in text:
    sys.exit(1)
