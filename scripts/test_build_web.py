#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline test of build_web_project() using a synthetic dataset (no network)."""
import os, sys, json, time
sys.path.insert(0, r"C:\Users\lianxiang\Downloads")
import youmind_scraper as ym

TEST_DIR = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\scripts\web_test_" + time.strftime("%H%M%S")
os.makedirs(os.path.join(TEST_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(TEST_DIR, "images"), exist_ok=True)
# Minimal index.html to test section injection
with open(os.path.join(TEST_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write('<html><body><div class="footer">foot</div></body></html>\n')

# Synthetic categories + items (simulating YouMind structure)
cat_items = {
    "anime-manga": [
        {"id": "a1", "title": "动漫少女", "prompt": "anime girl, ...", "image": "images/youmind/anime_manga/img_a1.jpg", "author": "x", "likes": 10, "resultsCount": 3, "slug": "s1", "categories": ["anime-manga"]},
        {"id": "a2", "title": "机甲", "prompt": "mecha, ...", "image": "images/youmind/anime_manga/img_a2.png", "author": "y", "likes": 5, "resultsCount": 1, "slug": "s2", "categories": ["anime-manga"]},
    ],
    "cyberpunk-sci-fi": [
        {"id": "c1", "title": "霓虹都市", "prompt": "cyberpunk city, ...", "image": "images/youmind/cyberpunk_sci_fi/img_c1.jpg", "author": "z", "likes": 8, "resultsCount": 2, "slug": "s3", "categories": ["cyberpunk-sci-fi"]},
    ],
}
cat_img_count = {"anime-manga": 2, "cyberpunk-sci-fi": 1}
cat_counter = {"anime-manga": 2, "cyberpunk-sci-fi": 1}

print("== build_web_project (add mode) ==")
ym.build_web_project(TEST_DIR, cat_items, cat_img_count, cat_counter, merge=False)

print("\n== verify outputs ==")
data_youmind = os.path.join(TEST_DIR, "data", "youmind")
print("data/youmind files:", sorted(os.listdir(data_youmind)))
for fn in sorted(os.listdir(data_youmind)):
    with open(os.path.join(data_youmind, fn), encoding="utf-8") as f:
        arr = json.load(f)
    print(f"  {fn}: {len(arr)} items; first image={arr[0]['image']}; keys={list(arr[0].keys())}")

# Verify youmind.html + category pages exist
for p in ["youmind.html", "youmind_anime_manga.html", "youmind_cyberpunk_sci_fi.html"]:
    path = os.path.join(TEST_DIR, p)
    print(f"{p}: exists={os.path.exists(path)} size={os.path.getsize(path) if os.path.exists(path) else 0}")

# Verify index.html injection
with open(os.path.join(TEST_DIR, "index.html"), encoding="utf-8") as f:
    idx = f.read()
print("index.html has YOUMIND_SECTION_START:", "YOUMIND_SECTION_START" in idx)
print("index.html links to youmind.html:", 'href="youmind.html"' in idx)

# Verify category page data-category
with open(os.path.join(TEST_DIR, "youmind_anime_manga.html"), encoding="utf-8") as f:
    cp = f.read()
print("anime page data-category:", 'data-category="youmind/anime_manga"' in cp)
print("anime page loads gallery-overlay.js:", 'src="gallery-overlay.js"' in cp)

print("\n== re-run to test idempotent injection (no duplicate section) ==")
ym.build_web_project(TEST_DIR, cat_items, cat_img_count, cat_counter, merge=False)
with open(os.path.join(TEST_DIR, "index.html"), encoding="utf-8") as f:
    idx2 = f.read()
print("YOUMIND_SECTION_START count:", idx2.count("YOUMIND_SECTION_START"), "(expected 1)")

print("\n== merge mode test (writes data/<bucket>.json) ==")
ym.build_web_project(TEST_DIR, cat_items, cat_img_count, cat_counter, merge=True)
print("data/ root files:", sorted(os.listdir(os.path.join(TEST_DIR, "data"))))
print("data/01_anime.json exists:", os.path.exists(os.path.join(TEST_DIR, "data", "01_anime.json")))

print("\nALL_OK")
