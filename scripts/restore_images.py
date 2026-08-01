#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""恢复图片与 gallery-dl 源文件夹。
1) 把 _deleted_trash 中当前 prompts-twitter.json 仍引用的缺失图片移回 images/twitter。
2) 从备份恢复 31 条已删「八人」条目的 gallery-dl/Twitter/<账号>/<推文ID>/ 源文件夹。
"""
import argparse, json, os, shutil
from pathlib import Path

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL = os.path.join(ROOT, "shuixian-prompts")
TWITTER_JSON = os.path.join(LOCAL, "data", "prompts-twitter.json")
TRASH = os.path.join(LOCAL, "images", "twitter", "_deleted_trash")
IMG_DIR = os.path.join(LOCAL, "images", "twitter")
BACKUP_TWITTER = os.path.join(ROOT, "scripts", "backup_12cat_20260725_132953", "prompts-twitter.json")
GALLERY_BASE = r"D:\PromptHunter\gallery-dl\Twitter"

BAREN_IDS = [
    31389, 31392, 31396, 31400, 31404, 31408, 31412, 31416, 31420, 31424,
    31428, 31432, 31436, 31440, 31444, 31448, 31452, 31456, 31460, 31464,
    31468, 31472, 31476, 31480, 31488, 31504, 31508, 31512, 31516, 31520, 31524,
]


def restore_current_images(dry=True):
    data = json.load(open(TWITTER_JSON, encoding="utf-8"))
    trash_files = {f.name: f for f in Path(TRASH).glob("*")} if os.path.isdir(TRASH) else {}
    moved = 0
    moved_names = []
    for e in data:
        for rel in [e.get("thumb")] + e.get("images", []):
            if not rel:
                continue
            name = os.path.basename(rel)
            dst = os.path.join(IMG_DIR, name)
            if os.path.exists(dst):
                continue
            src = trash_files.get(name)
            if src and src.exists():
                print(f"{'[DRY]' if dry else ''} 恢复项目图: {name}")
                if not dry:
                    shutil.move(str(src), dst)
                moved += 1
                moved_names.append(name)
    return moved, moved_names


def restore_gallery_dl_sources(dry=True):
    backup = json.load(open(BACKUP_TWITTER, encoding="utf-8"))
    by_id = {e["id"]: e for e in backup}
    trash_files = {f.name: f for f in Path(TRASH).glob("*")} if os.path.isdir(TRASH) else {}
    restored_folders = 0
    copied = 0
    for iid in BAREN_IDS:
        e = by_id.get(iid)
        if not e:
            print(f"[!] 备份中找不到 id={iid}")
            continue
        tweet = str(e.get("tweet") or "")
        account = e.get("author") or "DracoVibeCoding"  # 空 author 的 6 条与 Draco 同主题/时间段
        if not tweet:
            print(f"[!] id={iid} 无 tweet 字段，跳过")
            continue
        folder = os.path.join(GALLERY_BASE, account, tweet)
        print(f"{'[DRY]' if dry else ''} 恢复源文件夹: {folder}")
        if not dry:
            os.makedirs(folder, exist_ok=True)
        restored_folders += 1
        # 把 entry-id 与 tweet-id 两种命名的图都拷回去
        src_candidates = set()
        for rel in [e.get("thumb")] + e.get("images", []):
            if rel:
                src_candidates.add(os.path.basename(rel))
        for name in list(src_candidates):
            # 也尝试 tweet-id 前缀（_1, _2...）
            if name.startswith(f"{iid}."):
                stem = name.split(".", 1)[0]
                for n, f in trash_files.items():
                    if n == f"{tweet}.jpg" or n.startswith(f"{tweet}_"):
                        src_candidates.add(n)
        for n in list(src_candidates):
            for tf in trash_files:
                if tf == n:
                    src_candidates.add(tf)
        # 真正复制
        for name in src_candidates:
            src = trash_files.get(name)
            if not src or not src.exists():
                continue
            dst = os.path.join(folder, name)
            print(f"{'[DRY]' if dry else ''}   拷入: {name}")
            if not dry:
                shutil.copy2(str(src), dst)
            copied += 1
    return restored_folders, copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry = not args.apply

    print(f"{'DRY-RUN' if dry else 'APPLY'} 恢复开始\n")

    # 先恢复 gallery-dl 源文件夹（从 trash 复制，不删除），
    # 再移动项目图，避免同一张图被移走后源文件夹复制不到。
    m2, copied = restore_gallery_dl_sources(dry=dry)
    print(f"\ngallery-dl 源文件夹恢复: {m2} 个，拷入 {copied} 张图")

    m1, names1 = restore_current_images(dry=dry)
    print(f"\n项目图恢复: {m1} 张")

    print("\n完成。")


if __name__ == "__main__":
    main()
