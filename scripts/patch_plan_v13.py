# -*- coding: utf-8 -*-
"""plan.md v1.2 -> v1.3

两条本轮定下的硬约束入正文：
  A) og:image 必须是构建期生成的 PNG 1200x630，不许 SVG，不许运行时渲染
  B) 首页 title 在人口层上线前不得出现 population（标题不许承诺页面上没有的东西）
"""
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent.parent / "plan.md"
text = P.read_text(encoding="utf-8")
n0 = len(text)


def rep(old, new, want=1):
    global text
    n = text.count(old)
    if n != want:
        print(f"[ABORT] expected {want}, got {n}: {old[:70]!r}")
        sys.exit(1)
    text = text.replace(old, new)
    print(f"  ok  {old[:56]!r}")


# ── 版本头 ──────────────────────────────────────────────────────────────────
rep(
    "> 版本：**v1.2（2026-11-11 修订）**。",
    "> 版本：**v1.3（2026-11-11 修订）**。",
)

rep(
    "**v1.2 相对 v1.1 改了什么**（只列会改变行为的）：",
    """**v1.3 相对 v1.2 改了什么**（只列会改变行为的）：

1. **og:image 升级为硬约束**：必须是构建期生成的 **PNG 1200×630**。SVG 一律不接受——分享卡片在微信、Slack、X、iMessage 里对 SVG 的支持都不一致，一张"在浏览器里能看"的 SVG 等于一张在群里不显示的卡片。这条写进 §3.5 并加进 §5 的构建断言。
2. **标题不许承诺页面上没有的东西**：人口层在阶段 4 才上线，首页 title 在它上线前不出现 `population`。上线后按 §4.1 原文恢复。

**v1.2 相对 v1.1 改了什么**（只列会改变行为的）：""",
)

# ── §3.5 硬约束 ─────────────────────────────────────────────────────────────
rep(
    """- 构建后加一条断言脚本：任一页面 `og:title !== title` 或 `og:image` 以 `.svg` 结尾 → 构建失败。""",
    """- 构建后加一条断言脚本，以下任一条命中即**构建失败**（不是警告）：
  1. 任一页面 `og:title !== title`；
  2. 任一 `og:image` 以 `.svg` 结尾，或返回的 `content-type` 不是 `image/png`；
  3. 任一 `og:image` 的像素尺寸不是 1200×630（用 Pillow 打开实际校验，不信文件名）；
  4. 任一 `og:image` 不是以 `https://apocalab.com/` 开头的绝对 URL。

**为什么 PNG 是硬约束，不是偏好**：SVG 的分发链路不受我们控制。微信、Slack、X、iMessage 的抓取器对 SVG 的支持互不一致，多数直接不渲染；而它们的缓存一旦存了空图，改回来要等缓存过期。一张 1200×630 的 PNG 是这些抓取器唯一共同支持的格式。所以**分享图在构建期光栅化**，浏览器能力不参与这件事——这与站点其余部分"能用 HTML/CSS 就不上图"的原则不冲突，因为分享卡片根本不经过我们的 CSS。

**同理，也不接受运行时渲染的分享图**（Canvas 截图、`satori` 之类按请求生成）：分享卡片是抓取器拉的，它不执行我们的脚本。图必须在 `astro build` 之前就存在于 `public/og/`。""",
)

# ── §5 清单 ─────────────────────────────────────────────────────────────────
rep(
    "- [ ] og:image = 1200×630 PNG，构建期生成；og:title 与 title 同源",
    """- [ ] og:image **必须是构建期生成的 PNG，尺寸实测 1200×630**（Pillow 打开量，不看文件名）；**SVG 一律不允许**；`og:title` 与 `title` 同源；绝对 URL；`og:image:width/height` 显式写出
- [ ] title / description / H1 不得出现页面上还没有的功能词（当前：`population` 在人口层上线前禁用）""",
)

# ── R15 ────────────────────────────────────────────────────────────────────
rep(
    "| R15 | og 图需离线底图 | 3.5 | 无瓦片服务器可用 | Natural Earth 110m（公有领域）光栅化，不需要任何地图 API |",
    "| R15 | og 图需离线底图 | 3.5 | 无瓦片服务器可用 | Natural Earth 110m（公有领域）在构建期光栅化进 PNG，不需要任何地图 API；**输出必须是 PNG 1200×630，SVG 不接受**（SVG 在微信/Slack/X 的抓取器里不渲染） |",
)

# ── §4.1 标题与已上线状态对齐 ───────────────────────────────────────────────
rep(
    """### 4.1 `/` — 主词 `nuke simulator`
- Title: `Nuke Simulator: Blast Radius and Population for Any City`""",
    """### 4.1 `/` — 主词 `nuke simulator`
- Title（阶段 2 已上线）: `Nuke Simulator: Blast Radius for Any City, 15 kt to 1 Mt`
- Title（人口层上线后恢复）: `Nuke Simulator: Blast Radius and Population for Any City`""",
)

rep(
    "- H1: `Pick a point, pick a yield — this nuke simulator draws the rings to scale`",
    "- H1（阶段 2 已上线）: `Pick a city, pick a yield — the rings are drawn to scale from the manual`",
)

P.write_text(text, encoding="utf-8")
print(f"OK  {n0} -> {len(text)} chars")
