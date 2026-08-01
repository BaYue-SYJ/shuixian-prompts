#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Twitter (gallery-dl) 两个账号的图文整合进「水仙的AI提示词」项目。

- 扫描 D:\\PromptHunter\\gallery-dl\\Twitter\\{account}\\{tweetId}\\ 下每个推文
- 解析 txt：作者 / 用户名 / 时间 + 标题 + prompt(提示词) 正文
- 把图片复制到 shuixian-prompts\\images\\twitter\\<imgid>.jpg（连续编号，从 30000 起）
- 生成 entry：id / title / prompt / thumb / image / images[] / author / category
  * 一个推文 = 一条 entry；多图用 images[] 数组（与本地画廊多图画廊一致）
- 写出 shuixian-prompts\\data\\prompts-twitter.json 与 shuixian-deploy\\data\\prompts-twitter.json（内容相同）
- 不动原来的 prompts.json / parts，也不动 images\\thumbs|originals

R2 上传由 upload_r2_req.py 单独处理（镜像 images/twitter 前缀）。
"""
import os, json, shutil, re

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
TW_SRC = r"D:\PromptHunter\gallery-dl\Twitter"
LOCAL_IMG = os.path.join(ROOT, "shuixian-prompts", "images", "twitter")
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter.json")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter.json")

# 处理顺序（决定 ID 分配）：you1873118 在前，DracoVibeCoding 在后
# 与 HTML 中 chips 顺序一致：…其他综合, 超写实人像, 二次元少女
ACCOUNTS = ["you1873118", "DracoVibeCoding"]
# 账号 -> 分类（已按内容重命名；重跑时不要回退成账号名）
CATEGORY_MAP = {"you1873118": "超写实人像", "DracoVibeCoding": "二次元少女"}
START_ID = 30000

HEADER_RE = re.compile(r"^(作者|用户名|时间)\s*[:：]\s*(.*)$")
# 提示词标记：可带「图一 / 图1」等前缀，分隔符支持 : ： ;
MARKER_RE = re.compile(r"^(图[一二三四123456789]?\s*)?(提示词|prompt)\s*[:：;]")
# Twitter 文本页脚（时间戳 / 浏览量 / 中点），从末尾剔除
FOOTER_RE = re.compile(
    r"""^\s*·\s*$                                  # 单独的中点
       | ·\s*\d{4}\s*年                            # 带年份的时间戳
       | ^[\d,]+\s*(查看|次查看|回复|转发|赞|喜欢|书签|引用)?\s*$  # 数字+统计词
       | ^\s*查看\s*$                              # 单独“查看”
    """,
    re.VERBOSE,
)


def _is_footer(line):
    s = line.strip()
    return bool(s) and bool(FOOTER_RE.search(s))


def _find_title(pre_lines):
    for ln in pre_lines:
        s = ln.strip()
        if not s or HEADER_RE.match(s):
            continue
        return s
    return ""


def parse_txt(path):
    """返回 (author, title, content)。

    提取优先级：
      1) 命中「提示词/prompt」标记（可带图N前缀、可同/下行）——取标记后内容为提示词；
      2) 无标记——标题取首个非空非表头行，其后全部正文视为提示词；
      3) 仍为空——兜底把整段 txt（含用户名/作者）放入提示词。
    末尾的 Twitter 页脚（时间戳、浏览量、中点）会被剔除。
    """
    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    author = ""
    for ln in lines:
        s = ln.strip()
        m = HEADER_RE.match(s)
        if m and m.group(1) == "作者":
            author = m.group(2).strip()
            break

    # 1) 有标记
    marker_idx = None
    for i, ln in enumerate(lines):
        if MARKER_RE.match(ln.strip()):
            marker_idx = i
            break
    if marker_idx is not None:
        s = lines[marker_idx].strip()
        same = s[MARKER_RE.match(s).end():].strip()
        body = []
        if same:
            body.append(same)
        for ln in lines[marker_idx + 1:]:
            st = ln.strip()
            if _is_footer(st):  # 遇到页脚即停止收集
                break
            body.append(st)
        content = "\n".join(body).strip()
        title = _find_title(lines[:marker_idx])
        if not title:
            title = author or "未命名"
        return author, title, content

    # 2) 无标记：标题 + 其后正文
    title = ""
    rest_start = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or HEADER_RE.match(s):
            continue
        title = s
        rest_start = i + 1
        break
    rest = []
    if rest_start is not None:
        for ln in lines[rest_start:]:
            st = ln.strip()
            if _is_footer(st):  # 遇到页脚即停止收集
                break
            rest.append(st)
    content = "\n".join(rest).strip()

    # 仅有标题/说明、无独立正文：把标题本身当作提示词（避免回退到带用户名的整段原文）
    if not content and title:
        content = title.strip()
    # 3) 仍为空：兜底把整段原文（含用户名/作者）放入提示词
    if not content:
        content = raw.strip()
    if not title:
        title = author or "未命名"
    return author, title, content


def collect_images(folder):
    """返回按数字排序的图片绝对路径列表。"""
    imgs = []
    for fn in os.listdir(folder):
        if fn.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            m = re.match(r"(\d+)", fn)
            key = int(m.group(1)) if m else 1e9
            imgs.append((key, os.path.join(folder, fn)))
    imgs.sort(key=lambda x: x[0])
    return [p for _, p in imgs]


def main():
    os.makedirs(LOCAL_IMG, exist_ok=True)
    entries = []
    counter = START_ID
    stats = {}
    for account in ACCOUNTS:
        base = os.path.join(TW_SRC, account)
        if not os.path.isdir(base):
            print("跳过不存在的账号目录:", base)
            continue
        tweet_dirs = sorted(
            d for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d))
        )
        n_tweets = 0
        n_images = 0
        for tid in tweet_dirs:
            folder = os.path.join(base, tid)
            imgs = collect_images(folder)
            if not imgs:
                continue  # 无图则不建条目
            txts = [f for f in os.listdir(folder) if f.lower().endswith(".txt")]
            author = account
            title = ""
            content = ""
            if txts:
                author, title, content = parse_txt(os.path.join(folder, txts[0]))
            ids = list(range(counter, counter + len(imgs)))
            # 复制图片
            img_paths = []
            for src, iid in zip(imgs, ids):
                dst = os.path.join(LOCAL_IMG, f"{iid}.jpg")
                shutil.copyfile(src, dst)
                img_paths.append(f"images/twitter/{iid}.jpg")
            first = ids[0]
            entry = {
                "id": first,
                "title": title,
                "prompt": content,
                "thumb": img_paths[0],
                "image": img_paths[0],
                "images": img_paths,
                "author": author,
                "likes": 0,
                "resultsCount": 0,
                "slug": f"tw-{first}",
                "category": CATEGORY_MAP.get(account, account),
            }
            entries.append(entry)
            counter += len(imgs)
            n_tweets += 1
            n_images += len(imgs)
        stats[account] = (n_tweets, n_images, counter - START_ID)
        print(f"[{account}] 推文 {n_tweets} 条, 图片 {n_images} 张")

    with open(LOCAL_DATA, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    with open(DEPLOY_DATA, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)

    total_tweets = sum(v[0] for v in stats.values())
    total_images = sum(v[1] for v in stats.values())
    empty_prompt = sum(1 for e in entries if not e.get("prompt"))
    print(f"提示词为空: {empty_prompt} / {len(entries)}")
    print(f"\n合计：{total_tweets} 条推文, {total_images} 张图片")
    print(f"entry 数 = {len(entries)}，本地图片目录: {LOCAL_IMG}")
    print(f"写出: {LOCAL_DATA}")
    print(f"写出: {DEPLOY_DATA}")


if __name__ == "__main__":
    main()
