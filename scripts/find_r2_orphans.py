#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 R2 上 images/twitter* 前缀的对象，与画廊数据实际引用的图片做差集，找出孤儿图。
用法：
  python find_r2_orphans.py --write scripts/_delete_keys.txt
  （不带 --write 只打印统计；带 --write 额外把孤儿 key 落盘，供 delete_r2_req.py 使用）
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upload_r2_req import list_objects_v2

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"

def referenced_basenames():
    """画廊数据里所有 twitter 图片引用的文件名（basename）。"""
    bases = set()
    files = [
        "shuixian-prompts/data/prompts-twitter.json",
        "shuixian-prompts/data/prompts-twitter-cat1.json",
        "shuixian-prompts/data/prompts-twitter-cat2.json",
    ]
    for rel in files:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for e in d:
            if not isinstance(e, dict):
                continue
            for im in (e.get("images") or []):
                fn = str(im)
                base = os.path.basename(fn)
                if base:
                    bases.add(base)
    return bases

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", default=None, help="把孤儿 key 写入此文件")
    args = ap.parse_args()

    account = os.environ["R2_ACCOUNT_ID"]
    bucket = os.environ["R2_BUCKET"]
    access = os.environ["R2_ACCESS_KEY"]
    secret = os.environ["R2_SECRET_KEY"]

    print("🔍 列举 R2 上 images/twitter 前缀对象...")
    r2_keys = list_objects_v2(account, bucket, access, secret, "images/twitter")
    print(f"   R2 twitter 对象总数: {len(r2_keys)}")

    ref = referenced_basenames()
    print(f"   画廊数据引用图片文件名数: {len(ref)}")

    orphans = []
    for k in r2_keys:
        base = os.path.basename(k)
        if base not in ref:
            orphans.append(k)
    orphans.sort()

    print(f"\n=== 孤儿图（R2 存在但画廊不再引用）: {len(orphans)} ===")
    # 按文件夹分组统计
    import collections
    by_dir = collections.Counter(k[:k.rfind("/")] for k in orphans)
    for d, c in sorted(by_dir.items()):
        print(f"   {d}: {c}")

    if args.write:
        with open(args.write, "w", encoding="utf-8") as f:
            for k in orphans:
                f.write(k + "\n")
        print(f"\n✅ 已写入 {len(orphans)} 个孤儿 key 到 {args.write}")
    else:
        # 打印前 30 个样本
        for k in orphans[:30]:
            print("   ", k)
        if len(orphans) > 30:
            print(f"   ... 其余 {len(orphans)-30} 个省略")

if __name__ == "__main__":
    main()
