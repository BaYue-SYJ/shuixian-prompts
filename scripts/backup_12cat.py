#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改前备份：本地与部署的数据文件 + 两个 index.html -> 带时间戳目录。"""
import os, shutil, datetime

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
dest = os.path.join(ROOT, "scripts", f"backup_12cat_{ts}")
os.makedirs(dest, exist_ok=True)

items = [
    os.path.join(ROOT, "shuixian-prompts", "data", "prompts.json"),
    os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter.json"),
    os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter-cat1.json"),
    os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter-cat2.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts.part1.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts.part2.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts.part3.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter-cat1.json"),
    os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter-cat2.json"),
    os.path.join(ROOT, "shuixian-prompts", "index.html"),
    os.path.join(ROOT, "shuixian-deploy", "index.html"),
]
n = 0
for p in items:
    if os.path.exists(p):
        shutil.copy2(p, dest)
        n += 1
        print("backup:", os.path.relpath(p, ROOT))
    else:
        print("MISS :", os.path.relpath(p, ROOT))
print(f"\n共备份 {n} 个文件 -> {dest}")
