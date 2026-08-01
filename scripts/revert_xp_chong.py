#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revert xp-chong integration: drop the 3 categories + their data, restore
the originally-deployed version. Also dumps the R2 object keys to delete."""
import json, os, shutil
from pathlib import Path
from collections import OrderedDict

ROOT = Path(r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54")
PROJ = ROOT / "shuixian-prompts"
DEP = ROOT / "shuixian-deploy"

ORIG_CATEGORIES = ["全部","平面设计","人像写真","摄影纪实","动漫二次元","UI与界面","动物自然","风景建筑","游戏影视","插画艺术","3D与产品","科幻未来","文字Logo","美食料理","其他综合"]

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
def save(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

# ---- capture R2 keys to delete (from current merged data) ----
data = load(PROJ / "data" / "prompts.json")
new = [d for d in data if d["id"] >= 29462]
keys = set()
for d in new:
    for p in (d.get("thumbs") or [d.get("thumb")]) + (d.get("images") or [d.get("image")]):
        if p:
            keys.add(p)
KEY_FILE = ROOT / "scripts" / "_delete_keys.txt"
with open(KEY_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(sorted(keys)))
print("R2 keys to delete:", len(keys))

# ---- revert data ----
reverted = [d for d in data if d["id"] < 29462]
save(PROJ / "data" / "prompts.json", reverted)
print("prompts.json reverted:", len(data), "->", len(reverted))

# ---- categories.json ----
cats = {}
for d in reverted:
    c = d.get("category", "其他综合")
    cats[c] = cats.get(c, 0) + 1
total = len(reverted)
ordered = [c for c in ORIG_CATEGORIES if c in cats]
for c in sorted(cats.keys()):
    if c not in ordered:
        ordered.append(c)
categories = [{"category": c, "count": cats[c], "pct": round(cats[c]/total*100, 1)} for c in ordered]
save(PROJ / "data" / "categories.json", {"total": total, "categories": categories})
shutil.copy(PROJ / "data" / "categories.json", DEP / "data" / "categories.json")
print("categories restored:", [c["category"] for c in categories])

# ---- revert CATEGORIES array in both index.html ----
arr = "const CATEGORIES = [" + ",".join(f'"{c}"' for c in ORIG_CATEGORIES) + "];"
for html in [PROJ / "index.html", DEP / "index.html"]:
    txt = html.read_text(encoding="utf-8")
    txt = __import__("re").sub(r'const CATEGORIES = \[[^\]]+\];', arr, txt)
    html.write_text(txt, encoding="utf-8")
    print("CATEGORIES reverted in", html.name)

# ---- regenerate deploy part files ----
n = len(reverted)
part_size = (n + 2) // 3
parts = [reverted[i:i+part_size] for i in range(0, n, part_size)]
while len(parts) < 3:
    parts.append([])
parts = parts[:3]
for i, part in enumerate(parts, 1):
    p = DEP / "data" / f"prompts.part{i}.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(part, f, ensure_ascii=False, separators=(",", ":"))
    print(f"part{i}: {len(part)} entries, {os.path.getsize(p)/1024/1024:.2f} MB")
print("DONE revert")
