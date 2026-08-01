#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline test of merge mode: copy REAL style-gallery pages to temp, run merge patch, verify."""
import os, sys, json, shutil, re, time
sys.path.insert(0, r"C:\Users\lianxiang\Downloads")
import youmind_scraper as ym

SRC = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\style-gallery"
TMP = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\scripts\merge_test_" + time.strftime("%H%M%S")
os.makedirs(os.path.join(TMP, "data"), exist_ok=True)
os.makedirs(os.path.join(TMP, "images"), exist_ok=True)

# Copy the REAL 6 pages + index.html
for fn in ["index.html", "01_anime.html", "02_scifi.html", "03_art.html",
           "04_design.html", "05_fashion.html", "06_other.html"]:
    shutil.copy2(os.path.join(SRC, fn), os.path.join(TMP, fn))

# Synthetic merge data keyed by the 6 buckets (simulating YouMind-mapped)
cat_items = {
    "01_anime": [{"id": "a1", "title": "t", "prompt": "p", "image": "images/01_anime/ym_a1.jpg"}],
    "02_scifi": [{"id": "s1", "title": "t", "prompt": "p", "image": "images/02_scifi/ym_s1.jpg"}],
    "03_art": [],
    "04_design": [{"id": "d1", "title": "t", "prompt": "p", "image": "images/04_design/ym_d1.jpg"},
                  {"id": "d2", "title": "t", "prompt": "p", "image": "images/04_design/ym_d2.jpg"},
                  {"id": "d3", "title": "t", "prompt": "p", "image": "images/04_design/ym_d3.jpg"}],
    "05_fashion": [],
    "06_other": [{"id": "o1", "title": "t", "prompt": "p", "image": "images/06_other/ym_o1.jpg"}],
}
cat_img_count = {"01_anime": 1, "02_scifi": 1, "03_art": 0, "04_design": 3, "05_fashion": 0, "06_other": 1}
cat_counter = {k: len(v) for k, v in cat_items.items()}

print("== run merge build ==")
ym.build_web_project(TMP, cat_items, cat_img_count, cat_counter, merge=True)

print("\n== verify data files ==")
for b in ["01_anime", "02_scifi", "03_art", "04_design", "05_fashion", "06_other"]:
    p = os.path.join(TMP, "data", f"{b}.json")
    n = len(json.load(open(p, encoding="utf-8"))) if os.path.exists(p) else "MISSING"
    print(f"  {b}.json: {n} items")

print("\n== verify index.html numbers ==")
html = open(os.path.join(TMP, "index.html"), encoding="utf-8").read()
print("  header-stat-num values:", re.findall(r'header-stat-num">([\d,\.]+)<', html))
print("  card-meta-num values:", re.findall(r'card-meta-num">([\d,\.]+)<', html))
print("  footer entries:", re.findall(r'(\d[\d,]*)\s+entries', html))
print("  still has old 13,387?:", "13,387" in html)

print("\n== verify 01_anime.html hero ==")
h1 = open(os.path.join(TMP, "01_anime.html"), encoding="utf-8").read()
print("  stat-num values:", re.findall(r'stat-num">([\d,\.]+)<', h1))
print("  footer:", re.findall(r'共 ([\d,]+) 条', h1))
print("  openGalleryBtn present:", 'id="openGalleryBtn"' in h1)
print("  gallery-overlay.js present:", 'src="gallery-overlay.js"' in h1)
print("  data-category:", re.findall(r'data-category="([^"]+)"', h1))

print("\n== verify 03_art.html (zero bucket) ==")
h3 = open(os.path.join(TMP, "03_art.html"), encoding="utf-8").read()
print("  stat-num values:", re.findall(r'stat-num">([\d,\.]+)<', h3))

print("\n== backup dir ==")
bk = os.path.join(TMP, "data", "_backup_excel")
print("  backup exists:", os.path.isdir(bk), "| files:", sorted(os.listdir(bk)) if os.path.isdir(bk) else [])

for fn in ["index.html", "01_anime.html"]:
    t = open(os.path.join(TMP, fn), encoding="utf-8").read()
    print(f"  {fn}: <body>={t.count('<body')} </body>={t.count('</body>')} <div>={t.count('<div')} </div>={t.count('</div>')}")

print("\nMERGE_TEST_OK ; TMP=", TMP)
