# -*- coding: utf-8 -*-
"""Download GeoNames cities15000 dump (CC BY 4.0) once, into the gitignored work dir."""
import pathlib
import urllib.request
import zipfile
import os

OUT = pathlib.Path(__file__).resolve().parent.parent / ".tmp_handbook"
OUT.mkdir(exist_ok=True)
zip_path = OUT / "cities15000.zip"
url = "https://download.geonames.org/export/dump/cities15000.zip"

def good_zip(p: pathlib.Path) -> bool:
    if not p.exists() or p.stat().st_size < 1_000_000:
        return False
    try:
        with zipfile.ZipFile(p) as z:
            return "cities15000.txt" in z.namelist()
    except zipfile.BadZipFile:
        return False


if not good_zip(zip_path):
    # a truncated download from an earlier run must not be reused
    if zip_path.exists():
        zip_path.unlink()
    req = urllib.request.Request(url, headers={"User-Agent": "apocalab-build/0.1"})
    with urllib.request.urlopen(req, timeout=180) as r, open(zip_path, "wb") as f:
        f.write(r.read())
    print("downloaded", zip_path.stat().st_size, "bytes")
else:
    print("cached", zip_path.stat().st_size, "bytes")

txt = OUT / "cities15000.txt"
if not txt.exists():
    with zipfile.ZipFile(zip_path) as z:
        z.extract("cities15000.txt", OUT)
print("txt", txt.stat().st_size, "bytes")
