import json, os, sys

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY = os.path.join(ROOT, "shuixian-deploy", "data")

MAIN = "prompts-twitter.json"
CAT1 = "prompts-twitter-cat1.json"
CAT2 = "prompts-twitter-cat2.json"

# 唯一需要规整的非标准旧分类
REMAP = {"全部人像": "头像/人像/写真"}

APPLY = "--apply" in sys.argv

def load(p):
    return json.load(open(p, encoding="utf-8"))

def save(p, obj):
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

def merge_one(target_paths, src_paths):
    results = []
    for base in target_paths:
        main = load(base[MAIN])
        main_ids = set(e["id"] for e in main)
        added = []
        for sp in src_paths:
            for e in load(sp):
                if e["id"] in main_ids:
                    print(f"  SKIP dup id {e['id']} in {os.path.basename(base[MAIN])}")
                    continue
                # 规整旧分类
                if e.get("category") in REMAP:
                    e["category"] = REMAP[e["category"]]
                main.append(e)
                added.append(e["id"])
        results.append((base[MAIN], added))
        if APPLY:
            save(base[MAIN], main)
    return results

targets = [
    {MAIN: os.path.join(LOCAL, MAIN), CAT1: os.path.join(LOCAL, CAT1), CAT2: os.path.join(LOCAL, CAT2)},
    {MAIN: os.path.join(DEPLOY, MAIN), CAT1: os.path.join(DEPLOY, CAT1), CAT2: os.path.join(DEPLOY, CAT2)},
]

src_local = [os.path.join(LOCAL, CAT1), os.path.join(LOCAL, CAT2)]
src_deploy = [os.path.join(DEPLOY, CAT1), os.path.join(DEPLOY, CAT2)]

for t in targets:
    print(f"\n=== {os.path.dirname(os.path.dirname(t[MAIN]))} ===")
    res = merge_one([t], src_local if "shuixian-prompts" in t[MAIN] else src_deploy)
    for name, added in res:
        print(f"  {os.path.basename(name)}: +{len(added)} -> {added}")

if APPLY:
    # 清空 cat1/cat2 源文件，避免重复死数据
    for p in [os.path.join(LOCAL, CAT1), os.path.join(LOCAL, CAT2),
              os.path.join(DEPLOY, CAT1), os.path.join(DEPLOY, CAT2)]:
        save(p, [])
    print("\n[APPLY] cat1/cat2 source files emptied to [].")
else:
    print("\n[DRY-RUN] no files changed. Re-run with --apply to write.")
