#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【仅分析，不改任何画廊文件】
把 14,584 条提示词重新归类：
  - 含「人相关」词语的提示词 -> 人物 类别
  - 其余 -> 沿用现有主题类目（被抽走人物的从原类目扣除）
输出：分类数 + 每类条数 + 人物类来源分布 + 标题可读性抽样。
"""
import json, re, collections, os

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
FILES = [
    ("主库YouMind", os.path.join(ROOT, "shuixian-prompts/data/prompts.json")),
    ("X推特画廊",  os.path.join(ROOT, "shuixian-prompts/data/prompts-twitter.json")),
    ("X分类cat1",  os.path.join(ROOT, "shuixian-prompts/data/prompts-twitter-cat1.json")),
    ("X分类cat2",  os.path.join(ROOT, "shuixian-prompts/data/prompts-twitter-cat2.json")),
]

# 「人相关」关键词（中文用复合词避免误伤 人工智能/机器人/人生；英文带词边界）
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

def load_all():
    items = []
    for src, fp in FILES:
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            print("  跳过", fp, e); continue
        for e in d:
            if not isinstance(e, dict):
                continue
            title = str(e.get("title", "") or "")
            prompt = str(e.get("prompt", "") or e.get("content", "") or "")
            cat = e.get("category", "") or "其他综合"
            items.append((src, title, prompt, cat))
    return items

def main():
    items = load_all()
    print(f"载入总条数: {len(items)}")

    # 1) 人物判定
    person_items = [it for it in items if is_person(it[1] + "\n" + it[2])]
    non_person = [it for it in items if not is_person(it[1] + "\n" + it[2])]
    print(f"含「人相关」词语 -> 人物: {len(person_items)}")
    print(f"其余(非人物) : {len(non_person)}")

    # 2) 重新归类：人物 + 其余沿用现有主题（人像写真基本全被抽走）
    newcat = collections.Counter()
    person_from = collections.Counter()
    for src, title, prompt, cat in items:
        if is_person(title + "\n" + prompt):
            newcat["人物"] += 1
            person_from[cat] += 1
        else:
            newcat[cat if cat else "其他综合"] += 1

    print("\n========== 重新整理后的分类（每条仅归入一类）==========")
    print(f"总分类数: {len(newcat)}")
    for k, v in newcat.most_common():
        print(f"  {k}: {v}")

    print("\n========== 「人物」类别的来源（原类目分布）==========")
    for k, v in person_from.most_common():
        print(f"  原[{k}] -> 人物: {v}")

    # 3) 标题可读性抽样
    print("\n========== 标题可读性抽样（说明「标题不可读」现象）==========")
    has_cjk = re.compile(r'[\u4e00-\u9fff]')
    short = [it for it in items if len(it[1].strip()) <= 3]
    no_cjk = [it for it in items if not has_cjk.search(it[1])]
    print(f"  标题≤3字(过短/像文件名): {len(short)} 条")
    print(f"  标题不含中文(纯英文/符号): {len(no_cjk)} 条")
    print("  纯英文标题样本:")
    for it in no_cjk[:12]:
        print("    -", repr(it[1][:60]))
    print("  过短标题样本:")
    for it in short[:12]:
        print("    -", repr(it[1][:30]))

if __name__ == "__main__":
    main()
