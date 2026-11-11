# -*- coding: utf-8 -*-
"""把 plan.md 渲染成一个可公网分享的静态单页（深色、可读、带目录）。"""
import re
import html
import datetime
import pathlib

import markdown

ROOT = pathlib.Path(r"E:\CODEX\Web\apocalab.com")
SRC = ROOT / "plan.md"
OUT_DIR = ROOT / "plan-site"
OUT_DIR.mkdir(exist_ok=True)

md_text = SRC.read_text(encoding="utf-8")

# 去掉首行的 H1，页面头部单独渲染
md_text = re.sub(r"\A#\s.*\n", "", md_text)

md = markdown.Markdown(
    extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list", "nl2br"],
    extension_configs={"toc": {"permalink": False, "toc_depth": "2-2"}},
)
body = md.convert(md_text)
toc_html = md.toc
toc_html = re.sub(r'<div class="toc">\s*<ul>', '<ul class="toc-list">', toc_html)
toc_html = toc_html.replace("</div>", "").strip()

# 表格加横向滚动容器
body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")

# 待办清单
body = body.replace("<li>[ ] ", '<li class="todo">')

# 代码块语言标签
body = re.sub(r'<pre><code class="language-(\w+)">', r'<pre data-lang="\1"><code>', body)

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>apocalab.com — 实施计划 v1</title>
<style>
  :root {{
    --bg: #0B0E13;
    --panel: #11161e;
    --panel-2: #0f141b;
    --line: #1e2632;
    --line-soft: #171e28;
    --fg: #dfe6f0;
    --fg-dim: #9aa7b8;
    --fg-faint: #6b7788;
    --accent: #ff6a2b;
    --accent-soft: rgba(255,106,43,.12);
    --warn: #f0b429;
    --ok: #37c98b;
  }}
  * {{ box-sizing: border-box; }}
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg);
    font: 16px/1.75 -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
    font-feature-settings: "tnum" 0;
  }}
  a {{ color: #7fb3ff; text-decoration: none; border-bottom: 1px solid rgba(127,179,255,.25); }}
  a:hover {{ border-bottom-color: #7fb3ff; }}

  .top {{
    border-bottom: 1px solid var(--line);
    background: linear-gradient(180deg, #0e131a 0%, #0B0E13 100%);
    padding: 44px 24px 30px;
  }}
  .top-inner {{ max-width: 980px; margin: 0 auto; }}
  .eyebrow {{
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 12px; letter-spacing: .14em; text-transform: uppercase;
    color: var(--accent); font-weight: 600;
  }}
  .dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--accent); }}
  h1.title {{ font-size: clamp(26px, 4.4vw, 40px); line-height: 1.2; margin: 14px 0 10px; letter-spacing: -.01em; }}
  .sub {{ color: var(--fg-dim); font-size: 15px; margin: 0; max-width: 720px; }}
  .meta {{ margin-top: 18px; display: flex; flex-wrap: wrap; gap: 8px; }}
  .chip {{
    font-size: 12.5px; color: var(--fg-dim); background: var(--panel);
    border: 1px solid var(--line); border-radius: 999px; padding: 4px 11px;
  }}
  .chip b {{ color: var(--fg); font-weight: 600; }}

  .layout {{ max-width: 1180px; margin: 0 auto; padding: 0 24px 100px; }}
  .grid {{ display: grid; grid-template-columns: 1fr; gap: 40px; }}
  @media (min-width: 1080px) {{
    .grid {{ grid-template-columns: 232px minmax(0, 1fr); gap: 56px; }}
    nav.toc {{ position: sticky; top: 28px; align-self: start; max-height: calc(100vh - 56px); overflow-y: auto; }}
  }}
  nav.toc {{ display: none; padding-top: 44px; }}
  @media (min-width: 1080px) {{ nav.toc {{ display: block; }} }}
  nav.toc .toc-title {{ font-size: 11.5px; letter-spacing: .14em; text-transform: uppercase; color: var(--fg-faint); margin-bottom: 12px; }}
  ul.toc-list {{ list-style: none; margin: 0; padding: 0; border-left: 1px solid var(--line); }}
  ul.toc-list li {{ margin: 0; }}
  ul.toc-list a {{
    display: block; padding: 5px 0 5px 14px; font-size: 13.5px; line-height: 1.45;
    color: var(--fg-dim); border: 0; border-left: 2px solid transparent; margin-left: -1px;
  }}
  ul.toc-list a:hover {{ color: var(--fg); border-left-color: var(--accent); }}
  ul.toc-list ul {{ display: none; }}

  main {{ padding-top: 40px; max-width: 880px; }}
  h2 {{
    font-size: 22px; line-height: 1.35; margin: 52px 0 16px; padding-top: 22px;
    border-top: 1px solid var(--line-soft); letter-spacing: -.005em;
  }}
  h2:first-of-type {{ margin-top: 0; border-top: 0; padding-top: 0; }}
  h3 {{ font-size: 17px; margin: 32px 0 10px; color: #cfe0f5; }}
  p {{ margin: 12px 0; }}
  strong {{ color: #fff; font-weight: 650; }}
  hr {{ border: 0; border-top: 1px solid var(--line); margin: 40px 0; }}
  blockquote {{
    margin: 18px 0; padding: 12px 16px; background: var(--accent-soft);
    border-left: 2px solid var(--accent); border-radius: 0 6px 6px 0; color: #f0d9cd;
  }}
  blockquote p {{ margin: 4px 0; }}
  ul, ol {{ padding-left: 22px; }}
  li {{ margin: 6px 0; }}
  li.todo {{ list-style: none; position: relative; padding-left: 2px; }}
  li.todo::before {{
    content: ""; position: absolute; left: -18px; top: 7px; width: 11px; height: 11px;
    border: 1px solid #46536a; border-radius: 3px;
  }}
  code {{
    font: 13.5px/1.5 "JetBrains Mono", "Cascadia Code", Consolas, monospace;
    background: #161d27; border: 1px solid var(--line); border-radius: 4px;
    padding: 1.5px 5px; color: #ffc9ad;
  }}
  pre {{
    position: relative; background: var(--panel-2); border: 1px solid var(--line);
    border-radius: 8px; padding: 16px 18px; overflow-x: auto; margin: 18px 0;
  }}
  pre code {{ background: none; border: 0; padding: 0; color: #c7d3e2; font-size: 13px; }}
  pre[data-lang]::before {{
    content: attr(data-lang); position: absolute; top: 8px; right: 12px;
    font-size: 10.5px; letter-spacing: .1em; text-transform: uppercase; color: var(--fg-faint);
  }}
  .table-wrap {{
    overflow-x: auto; margin: 18px 0; border: 1px solid var(--line);
    border-radius: 8px; background: var(--panel-2);
  }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; min-width: 560px; }}
  th, td {{ padding: 9px 13px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line-soft); }}
  th {{ background: #141b24; color: #cfe0f5; font-weight: 600; white-space: nowrap; font-size: 12.5px; letter-spacing: .02em; }}
  tbody tr:last-child td {{ border-bottom: 0; }}
  tbody tr:hover td {{ background: rgba(255,255,255,.015); }}
  td code {{ font-size: 12.5px; }}

  footer {{
    border-top: 1px solid var(--line); margin-top: 60px; padding: 28px 24px 60px;
    color: var(--fg-faint); font-size: 12.5px; text-align: center;
  }}
  @media print {{
    body {{ background: #fff; color: #111; }}
    nav.toc, .top {{ display: none; }}
    pre, .table-wrap {{ border-color: #ccc; }}
  }}
</style>
</head>
<body>

<header class="top">
  <div class="top-inner">
    <div class="eyebrow"><span class="dot"></span>apocalab.com &nbsp;/&nbsp; implementation plan</div>
    <h1 class="title">核武器效应公开数据站 —— 实施计划 v1</h1>
    <p class="sub">技术方案、数据来源与页码落实、页面规格、开发顺序、风险清单。第一步只交计划，不含代码。</p>
    <div class="meta">
      <span class="chip">版本 <b>v1 · 待裁决</b></span>
      <span class="chip">输出日期 <b>{now}</b></span>
      <span class="chip">数据源 <b>Glasstone &amp; Dolan, 1977（公有领域）</b></span>
      <span class="chip">工时 <b>70–85 h</b></span>
    </div>
  </div>
</header>

<div class="layout">
  <div class="grid">
    <nav class="toc">
      <div class="toc-title">目录</div>
      {toc}
    </nav>
    <main>
{body}
    </main>
  </div>
</div>

<footer>apocalab.com · 实施计划 v1 · 本文档为内部方案，未对外发布</footer>
</body>
</html>
""".format(now=now, toc=toc_html, body=body)

(OUT_DIR / "index.html").write_text(PAGE, encoding="utf-8")
print("written:", OUT_DIR / "index.html", (OUT_DIR / "index.html").stat().st_size, "bytes")
