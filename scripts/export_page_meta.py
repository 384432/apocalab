# -*- coding: utf-8 -*-
"""Export the title / description / H1 of every built page as plain text.

The point is review without a browser: docs/page-meta.txt is one line per page,
read from dist/ (so it is the shipped text, not the source template), and a
second block carries the paragraphs that make claims about method — currently
the population convention sentence printed on each city page.

    python scripts/export_page_meta.py     (after npm run build)
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = ROOT / "docs" / "page-meta.txt"


def text_of(fragment):
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?s)<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment).replace("\xa0", " ")).strip()


def url_of(page):
    rel = page.parent.relative_to(DIST).as_posix()
    return "/" if rel == "." else f"/{rel}/"


pages = sorted(DIST.rglob("index.html"), key=lambda p: url_of(p))
if not pages:
    sys.exit("dist is empty — run npm run build first")

lines = []
conventions = []
for page in pages:
    src = page.read_text(encoding="utf-8")
    url = url_of(page)

    def pick(pattern):
        m = re.search(pattern, src, re.I | re.S)
        return text_of(m.group(1)) if m else "(missing)"

    title = pick(r"<title>(.*?)</title>")
    desc = pick(r'<meta\s+name="description"\s+content="(.*?)"')
    h1 = pick(r"<h1[^>]*>(.*?)</h1>")
    lines.append(f"{url}  |  Title: {title}  |  Description: {desc}  |  H1: {h1}")

    m = re.search(r'<p[^>]*id="population-convention"[^>]*>(.*?)</p>', src, re.I | re.S)
    if m:
        conventions.append(f"{url}\n  {text_of(m.group(1))}")

body = "\n".join(lines) + "\n"
if conventions:
    body += "\nPOPULATION CONVENTION (the sentence printed on the page)\n\n"
    body += "\n\n".join(conventions) + "\n"

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(body, encoding="utf-8")
print(f"{len(pages)} pages -> {OUT.relative_to(ROOT)}")
print(body)
