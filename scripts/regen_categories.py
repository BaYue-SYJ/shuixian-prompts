#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据当前数据文件重新生成 categories.json（不改动 category 字段）"""
import json, os, collections

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"

for name, base in [("本地", os.path.join(ROOT, "shuixian-prompts", "data")),
                   ("部署", os.path.join(ROOT, "shuixian-deploy", "data"))]:
    cnt = collections.Counter()
    total = 0
    for nm in os.listdir(base):
        if nm.startswith("prompts") and nm.endswith(".json") and ".bak" not in nm:
            with open(os.path.join(base, nm), "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                continue
            for e in data:
                if isinstance(e, dict) and "id" in e:
                    total += 1
                    cat = e.get("category")
                    if isinstance(cat, list):
                        for c in cat:
                            cnt[c] += 1
                    elif cat:
                        cnt[cat] += 1
                    else:
                        cnt["其他综合"] += 1
    categories = []
    for cat, n in cnt.most_common():
        categories.append({"category": cat, "count": n, "percentage": round(n / total * 100, 1)})
    out = {"total": total, "categories": categories}
    out_path = os.path.join(base, "categories.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"{name} categories.json 已生成: total={total}, 类数={len(categories)}")
