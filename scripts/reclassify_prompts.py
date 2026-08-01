#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【改写数据】按新分类重写各画廊数据文件的 category 字段。
规则（与设计稿 analyze_categories.py 完全一致）：
  - 含「人相关」词语(标题+正文) -> 人物
  - 其余 -> 保留原 category（缺省 其他综合）
对每个文件：先把原文件复制为 <name>.bak-reclass-<ts> 再覆盖写回。
"""
import json, re, os, shutil, collections, datetime

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"

# 与 analyze_categories.py 完全一致的「人相关」关键词
PERSON = [
    r'人物', r'女孩', r'男孩', r'男人', r'女人', r'女性', r'男性',
    r'儿童', r'婴儿', r'少年', r'青年', r'中年', r'老年', r'老人', r'孕妇', r'孕妈',
    r'情侣', r'夫妻', r'一家人', r'家庭照', r'全家福',
    r'自拍', r'肖像', r'证件照', r'写真', r'cosplay', r'模特', r'角色',
    r'少女', r'萝莉', r'正太', r'御姐', r'帅哥', r'美女', r'靓女', r'型男',
    r'人脸', r'头像', r'半身', r'全身', r'群像', r'人群', r'群众',
    r'婚纱', r'汉服', r'和服', r'妆容', r'五官', r'表情',
    r'\bgirl\b', r'\bgirls\b', r'\bboy\b', r'\bboys\b',
    r'\bwoman\b', r'\bwomen\b', r'\bman\b', r'\bmen\b',
    r'\bperson\b', r'\bpeople\b', r'\bportrait\b', r'\bportraits\b',
    r'\bselfie\b', r'\bchild\b', r'\bchildren\b', r'\bbaby\b', r'\bkid\b', r'\bkids\b',
    r'\bmodel\b', r'\bmodels\b', r'\bcosplay\b',
    r'\bcharacter\b', r'\bbride\b', r'\bgroom\b', r'\bcrowd\b',
    r'\bheroine\b', r'\bhero\b', r'\bfemale\b', r'\bmale\b',
    r'\blady\b', r'\bgentleman\b', r'\bavatar\b', r'\bwaifu\b', r'\bhusbando\b',
    r'\bfamily\b',
]
PERSON_RE = re.compile("|".join(PERSON), re.IGNORECASE)

def is_person(text):
    return bool(PERSON_RE.search(text or ""))

# 需要重写的文件（本地单文件 + 部署拆分文件 + 两端 twitter 文件）
TARGETS = [
    "shuixian-prompts/data/prompts.json",
    "shuixian-prompts/data/prompts-twitter.json",
    "shuixian-prompts/data/prompts-twitter-cat1.json",
    "shuixian-prompts/data/prompts-twitter-cat2.json",
    "shuixian-deploy/data/prompts.part1.json",
    "shuixian-deploy/data/prompts.part2.json",
    "shuixian-deploy/data/prompts.part3.json",
    "shuixian-deploy/data/prompts-twitter.json",
    "shuixian-deploy/data/prompts-twitter-cat1.json",
    "shuixian-deploy/data/prompts-twitter-cat2.json",
]

def reclassify_file(rel):
    fp = os.path.join(ROOT, rel)
    d = json.load(open(fp, encoding="utf-8"))
    if not isinstance(d, list):
        print(f"  [跳过] {rel}: 非 list 类型"); return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = fp + f".bak-reclass-{ts}"
    shutil.copy2(fp, bak)
    before = collections.Counter()
    after = collections.Counter()
    empty_prompt = 0
    changed = 0
    for e in d:
        if not isinstance(e, dict):
            continue
        title = str(e.get("title", "") or "")
        prompt = str(e.get("prompt", "") or e.get("content", "") or "")
        if not prompt.strip() and not str(e.get("content", "")).strip():
            empty_prompt += 1
        old = e.get("category", "") or "其他综合"
        before[old] += 1
        if is_person(title + "\n" + prompt):
            new = "人物"
        else:
            new = old
        if new != old:
            changed += 1
        e["category"] = new
        after[new] += 1
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
    return dict(file=rel, total=len(d), changed=changed, empty_prompt=empty_prompt,
                before=before, after=after, bak=bak)

def main():
    grand_before = collections.Counter()
    grand_after = collections.Counter()
    print(f"待处理文件: {len(TARGETS)}")
    for rel in TARGETS:
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            print(f"  [缺失] {rel}"); continue
        r = reclassify_file(rel)
        if not r:
            continue
        grand_before.update(r["before"])
        grand_after.update(r["after"])
        print(f"\n● {r['file']}  总 {r['total']} | 改 {r['changed']} | 空prompt {r['empty_prompt']}")
        print(f"    备份: {os.path.basename(r['bak'])}")
        # 仅展示变动的类目
        diff = {k: r["after"][k] - r["before"].get(k, 0) for k in set(r["after"]) | set(r["before"])}
        diff = {k: v for k, v in diff.items() if v != 0}
        print(f"    变动类目: {diff}")

    print("\n========== 全量汇总（所有文件合计）==========")
    print(f"  总条目: {sum(grand_after.values())}")
    print(f"  分类数: {len(grand_after)}")
    for k, v in grand_after.most_common():
        print(f"    {k}: {v}")

if __name__ == "__main__":
    main()
