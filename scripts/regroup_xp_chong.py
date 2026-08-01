#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge the per-image xp-chong entries into one entry per prompt (multi-image).

Each image was stored as a separate entry during initial integration. This
script groups them by the source post ID embedded in `slug`
(e.g. "deepblueaix-2072329409089208523-29462" -> group "2072329409089208523")
and merges each group into a single entry carrying `thumbs`/`images` arrays.
"""
import json
from collections import defaultdict
from pathlib import Path

PROJECT = Path(r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts")

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save(p, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

def main():
    data_path = PROJECT / "data" / "prompts.json"
    data = load(data_path)
    old_max = max(d["id"] for d in data)
    print("total before:", len(data), "max id:", old_max)

    old_entries = [d for d in data if d["id"] < 29462]
    new_entries = [d for d in data if d["id"] >= 29462]
    print("old:", len(old_entries), "new(image) entries:", len(new_entries))

    # group new entries by slug middle token (source group id)
    groups = defaultdict(list)
    for d in new_entries:
        parts = d["slug"].split("-")
        gid = parts[1] if len(parts) >= 3 and parts[1].isdigit() else str(d["id"])
        groups[gid].append(d)

    merged = []
    for gid in sorted(groups.keys(), key=lambda g: int(g) if g.isdigit() else 0):
        items = sorted(groups[gid], key=lambda x: x["id"])
        first = items[0]
        thumbs = [i["thumb"] for i in items]
        images = [i["image"] for i in items]
        entry = {
            "id": first["id"],
            "title": first.get("title", ""),
            "prompt": first.get("prompt", ""),
            "category": first.get("category", "其他综合"),
            "author": first.get("author", ""),
            "thumb": first["thumb"],
            "image": first["image"],
            "thumbs": thumbs,
            "images": images,
            "multi": len(items) > 1,
            "likes": 0,
            "resultsCount": 0,
            "slug": first.get("slug", ""),
        }
        merged.append(entry)
    print("merged prompts:", len(merged))

    # keep ordering: old entries first, merged appended (already highest ids)
    new_data = old_entries + merged
    save(data_path, new_data)
    print("total after:", len(new_data))

    # regenerate categories.json
    cats = {}
    for d in new_data:
        c = d.get("category", "其他综合")
        cats[c] = cats.get(c, 0) + 1
    total = len(new_data)
    existing_order = ["平面设计","人像写真","摄影纪实","动漫二次元","UI与界面","动物自然","风景建筑","游戏影视","插画艺术","3D与产品","科幻未来","文字Logo","美食料理","其他综合"]
    ordered = [c for c in existing_order if c in cats]
    for c in sorted(cats.keys()):
        if c not in ordered:
            ordered.append(c)
    categories = [{"category": c, "count": cats[c], "pct": round(cats[c]/total*100, 1)} for c in ordered]
    save(PROJECT / "data" / "categories.json", {"total": total, "categories": categories})
    print("categories.json updated. new cats:")
    for c in categories:
        if c["category"] in ("DeepBlueAIX","GrayNoteLab","listudio"):
            print("  ", c["category"], c["count"])

if __name__ == "__main__":
    main()
