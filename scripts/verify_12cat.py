#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证：文件合法性、本地==部署 一致性、已删 106 条不残留、12 类分布。"""
import json, os, collections

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LD = os.path.join(ROOT, "shuixian-prompts", "data")
DD = os.path.join(ROOT, "shuixian-deploy", "data")

del_ids = set(r["id"] for r in json.load(open(os.path.join(ROOT,"scripts","_residual_twitter_delete.json"),encoding="utf-8")))

def load_files(data_dir):
    out = {}
    for n in os.listdir(data_dir):
        if n.endswith(".json") and ".bak" not in n and (n=="prompts.json" or n.startswith("prompts.part") or n.startswith("prompts-twitter")):
            p = os.path.join(data_dir, n)
            try:
                a = json.load(open(p, encoding="utf-8"))
            except Exception as e:
                return None, f"JSON解析失败 {n}: {e}"
            if isinstance(a, list):
                out[n] = a
    return out, None

ld, err1 = load_files(LD)
dd, err2 = load_files(DD)
print("本地文件读取:", "OK" if not err1 else err1)
print("部署文件读取:", "OK" if not err2 else err2)

def union(files):
    by_id = {}
    for arr in files.values():
        for e in arr:
            if isinstance(e, dict) and "id" in e:
                by_id.setdefault(e["id"], e)
    return by_id

lu = union(ld); du = union(dd)
print(f"\n本地去重条数: {len(lu)}   部署去重条数: {len(du)}")
print("本地==部署 条数:", "一致 ✅" if len(lu)==len(du) else "不一致 ❌")

# 已删 106 是否残留
miss_local = [i for i in del_ids if i in lu]
miss_deploy = [i for i in del_ids if i in du]
print(f"已删条目本地残留: {len(miss_local)}   部署残留: {len(miss_deploy)}  {'✅' if not miss_local and not miss_deploy else '❌'}")

# 12 类分布对比
def dist(by_id):
    c = collections.Counter()
    for e in by_id.values():
        for x in (e.get("category") or []):
            c[x]+=1
    return c
lc, dc = dist(lu), dist(du)
print("\n12 类分布(本地 vs 部署):")
twelve = ["商业海报/广告/社媒","UI/App/网页/SaaS","产品/电商/包装","头像/人像/写真","Logo/品牌/VI","摄影/电影感/写实场景","信息图/教育图解/图表","漫画/故事板/分镜","3D/游戏/像素/等距","插画/涂鸦/手绘风","字体/排版/标题设计","全部人像"]
for t in twelve:
    same = "✅" if lc.get(t)==dc.get(t) else "❌"
    print(f"  {t:22s} 本地 {lc.get(t,0):6d}  部署 {dc.get(t,0):6d}  {same}")
# 空类目
print(f"  空类目(仅全部): 本地 {lc.get('',0)}  部署 {dc.get('',0)}")

# categories.json
for name,d in (("本地",LD),("部署",DD)):
    c = json.load(open(os.path.join(d,"categories.json"),encoding="utf-8"))
    print(f"\ncategories.json({name}) total={c['total']} 类数={len(c['categories'])}")

# 抽查 category 字段类型
sample = next(iter(lu.values()))
print("\n样例 entry.category 类型:", type(sample.get("category")).__name__, "值:", sample.get("category"))
