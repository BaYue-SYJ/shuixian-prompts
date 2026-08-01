# -*- coding: utf-8 -*-
"""把 X 检查台「已收录」里被删除的帖子，从画廊数据中同步清除。

判定依据（最可靠）：
  帖子在检查台被删除时，server.py 会 rmtree 掉 D:/PromptHunter/gallery-dl/Twitter/<账号>/<推文ID>
  并 unmark collected.json。所以“已被删”= 画廊数据里存在、但其 gallery-dl 源文件夹已消失的条目。
  （与 collected.json 一致：gallery-dl 现存文件夹数 == collected.json 条数，可作交叉验证。）

动作：
  1) 从本地 & 部署的 prompts-twitter*.json 中移除这些条目（含 cat1/cat2）。
  2) 删除（移动到 trash 子目录，可恢复）shuixian-prompts/images/twitter 下对应图片。
  3) 复核 gallery-dl 源文件夹确已消失（若仍在，强删）。

用法：
  python purge_deleted_posts.py          # dry-run，打印将删除的清单
  python purge_deleted_posts.py --apply  # 真正执行（执行前自动备份数据文件）
"""
import os, json, sys, shutil, datetime, collections

GALLERY_DL = r"D:\PromptHunter\gallery-dl\Twitter"
ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
DATA_FILES = [
    "shuixian-prompts/data/prompts-twitter.json",
    "shuixian-deploy/data/prompts-twitter.json",
    "shuixian-prompts/data/prompts-twitter-cat1.json",
    "shuixian-deploy/data/prompts-twitter-cat1.json",
    "shuixian-prompts/data/prompts-twitter-cat2.json",
    "shuixian-deploy/data/prompts-twitter-cat2.json",
]
IMG_DIR = os.path.join(ROOT, "shuixian-prompts", "images", "twitter")
TRASH_DIR = os.path.join(IMG_DIR, "_deleted_trash")


def derive_tid(e):
    t = e.get("tweet")
    if t and str(t).strip():
        return str(t).strip()
    imgs = e.get("images") or []
    if imgs:
        base = os.path.basename(str(imgs[0]))
        name = base[:-4] if base.lower().endswith(".jpg") else base
        if name.isdigit() and len(name) >= 15:
            return name
    return None


def build_existing_tids():
    s = set()
    for acc in os.listdir(GALLERY_DL):
        adir = os.path.join(GALLERY_DL, acc)
        if not os.path.isdir(adir) or acc.startswith("__") or acc.endswith(".db"):
            continue
        for tid in os.listdir(adir):
            if os.path.isdir(os.path.join(adir, tid)) and tid.isdigit():
                s.add(tid)
    return s


def main():
    apply = "--apply" in sys.argv
    existing = build_existing_tids()
    print("gallery-dl 现存 tweet 文件夹数:", len(existing))

    # 收集每个文件里待删条目
    plan = {}  # filepath -> list of (index, entry)
    for p in DATA_FILES:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp, encoding="utf-8"))
        to_del = []
        for i, e in enumerate(d):
            if not isinstance(e, dict):
                continue
            tid = derive_tid(e)
            if not tid:
                continue
            if tid not in existing:
                to_del.append((i, e))
        if to_del:
            plan[fp] = to_del

    total = sum(len(v) for v in plan.values())
    print("待删除条目总数:", total)
    img_set = set()
    for fp, items in plan.items():
        acc = collections.Counter()
        for i, e in items:
            a = e.get("author") or e.get("account") or "?"
            acc[a] += 1
            for im in (e.get("images") or []):
                img_set.add(os.path.basename(str(im)))
        print(f"  {os.path.relpath(fp, ROOT)}: {len(items)} 条  按账号 {dict(acc)}")
    print("  涉及图片文件数:", len(img_set))

    if not apply:
        print("\n[dry-run] 未做任何修改。加 --apply 执行。")
        return

    # ---- 执行 ----
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # 1) 备份 + 写回数据文件
    for fp, items in plan.items():
        d = json.load(open(fp, encoding="utf-8"))
        idxs = sorted((i for i, _ in items), reverse=True)
        bak = fp + f".bak-del-{ts}"
        shutil.copy2(fp, bak)
        for i in idxs:
            del d[i]
        json.dump(d, open(fp, "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
        print(f"  [数据] 已更新 {os.path.relpath(fp, ROOT)} (备份 {os.path.basename(bak)})")

    # 2) 图片：仅删未被任何“保留条目”引用的（防误删共享图）
    remaining_imgs = set()
    for p in DATA_FILES:
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            continue
        for e in json.load(open(fp, encoding="utf-8")):
            if isinstance(e, dict):
                for im in (e.get("images") or []):
                    remaining_imgs.add(os.path.basename(str(im)))
    to_del_imgs = img_set - remaining_imgs
    if to_del_imgs:
        os.makedirs(TRASH_DIR, exist_ok=True)
        moved = 0
        for fn in to_del_imgs:
            src = os.path.join(IMG_DIR, fn)
            if os.path.exists(src):
                shutil.move(src, os.path.join(TRASH_DIR, fn))
                moved += 1
        print(f"  [图片] 移动 {moved} 张到回收目录 {os.path.relpath(TRASH_DIR, ROOT)}")

    # 3) 复核 gallery-dl 源文件夹确已消失（强删残留）
    deleted_tids = set()
    for fp, items in plan.items():
        for i, e in items:
            tid = derive_tid(e)
            if tid:
                deleted_tids.add(tid)
    still = 0
    for acc in os.listdir(GALLERY_DL):
        adir = os.path.join(GALLERY_DL, acc)
        if not os.path.isdir(adir) or acc.startswith("__") or acc.endswith(".db"):
            continue
        for tid in list(os.listdir(adir)):
            tdir = os.path.join(adir, tid)
            if os.path.isdir(tdir) and tid in deleted_tids:
                shutil.rmtree(tdir, ignore_errors=True)
                still += 1
    print(f"  [复核] 强删残留源文件夹: {still} 个")


if __name__ == "__main__":
    main()
