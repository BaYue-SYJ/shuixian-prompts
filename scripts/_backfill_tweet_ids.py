#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补全 twitter json 旧条目的 tweet 字段（备份后写入本地+部署两份）。

方法（按优先级）：
  1) 从 image 文件名提取 15+ 位数字（tweet id 命名的新数据）
  2) collected.json 已知映射（图片文件名 -> tweet id）
  3) 哈希匹配 gallery-dl 原图（you1873118 + DracoVibeCoding）
  4) 遍历顺序兜底（复现 integrate_twitter.py：账号顺序 + 文件夹字母序 + 连续编号）
校验：tweet 为 15+ 数字、且 (author,tweet) 唯一；冲突则跳过。
"""
import os, hashlib, json, re, shutil, datetime

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
TW = r"D:\PromptHunter\gallery-dl\Twitter"
LOCAL = os.path.join(ROOT, "shuixian-prompts", "images", "twitter")
LOCAL_JSON = os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter.json")
DEPLOY_JSON = os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter.json")
ORIG_ACCOUNTS = ["you1873118", "DracoVibeCoding"]
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# 1) gallery-dl 原图哈希索引（仅原始两个账号）
index = {}
for acc in ORIG_ACCOUNTS:
    base = os.path.join(TW, acc)
    if not os.path.isdir(base):
        continue
    for tid in os.listdir(base):
        folder = os.path.join(base, tid)
        if not os.path.isdir(folder) or not tid.isdigit():
            continue
        imgs = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXTS))
        for i, fn in enumerate(imgs):
            h = md5(os.path.join(folder, fn))
            index.setdefault(h, []).append((acc, tid, i))

# 2) 遍历顺序映射（复现 integrate_twitter.py）
order = {}
counter = 30000
for acc in ORIG_ACCOUNTS:
    base = os.path.join(TW, acc)
    if not os.path.isdir(base):
        continue
    for tid in sorted(os.listdir(base)):
        folder = os.path.join(base, tid)
        if not os.path.isdir(folder) or not tid.isdigit():
            continue
        imgs = sorted(f for f in os.listdir(folder) if f.lower().endswith(IMG_EXTS))
        if not imgs:
            continue
        order[counter] = (acc, tid)
        counter += len(imgs)

# 3) collected.json 已知映射
cj = r"D:\PromptHunter\collected.json"
collected = json.load(open(cj, encoding="utf-8")) if os.path.exists(cj) else {}
collected_by_img = {}
for key, info in collected.items():
    tid = key.split("/", 1)[1] if "/" in key else ""
    for p in (info.get("images") or []):
        collected_by_img[os.path.basename(p)] = tid


def fill_tweet(x, used):
    if isinstance(x.get("tweet"), str) and re.search(r"\d{15,}", x["tweet"]):
        return False  # 已有合法 tweet
    iid = x.get("id")
    author = x.get("author")
    img_rel = x.get("image") or (x.get("images") or [""])[0]
    base_img = os.path.basename(img_rel)
    p = os.path.join(LOCAL, base_img)
    tid = None
    # 1) image 文件名
    m = re.search(r"(\d{15,})\.jpg$", base_img)
    if m:
        tid = m.group(1)
    # 2) collected 映射
    if not tid and base_img in collected_by_img and collected_by_img[base_img].isdigit():
        tid = collected_by_img[base_img]
    # 3) 哈希
    if not tid and os.path.exists(p):
        h = md5(p)
        hits = [hh for hh in index.get(h, []) if hh[0] == author]
        if hits:
            tid = hits[0][1]
    # 4) 遍历顺序兜底
    if not tid:
        ot = order.get(iid, (None, None))[1]
        if ot:
            tid = ot
    if tid and tid.isdigit() and len(tid) >= 15 and (author, tid) not in used:
        x["tweet"] = tid
        used.add((author, tid))
        return True
    return False


def process(path, label):
    d = json.load(open(path, encoding="utf-8"))
    used = set()
    filled = skip = 0
    for x in d:
        if fill_tweet(x, used):
            filled += 1
        else:
            skip += 1
    # 备份
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = path + f".bak-backfill-{ts}"
    shutil.copy2(path, bak)
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"[{label}] 补全 {filled} 条, 跳过 {skip} 条; 备份 -> {bak}")
    return d


if __name__ == "__main__":
    process(LOCAL_JSON, "本地版")
    process(DEPLOY_JSON, "部署版")
