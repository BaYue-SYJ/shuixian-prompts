"""方案3 离线重组: 保留原 Excel 六类, 把 YouMind 原图作为第 7 个分区(YouMind 原图库)。
不重新抓网络——YouMind 数据已在被覆盖的 data/<bucket>.json 中, 原图已在 images/<bucket>/ym_*.jpg。
流程:
  1. 读回 YouMind 版 data (当前 data/<bucket>.json 是被覆盖版)
  2. 从 _backup_excel 恢复 Excel 六类 data/*.json
  3. 把 ym_*.jpg 移动到 images/youmind/<slug>/
  4. 调 build_web_project(merge=False) 生成 data/youmind + youmind.html + 分类页 + 注入 index
"""
import sys, os, json, shutil

sys.path.insert(0, r"C:\Users\lianxiang\Downloads")
import youmind_scraper as ym

PROJECT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\style-gallery"
BACKUP = os.path.join(PROJECT, "data", "_backup_excel")
BUCKETS = ["01_anime", "02_scifi", "03_art", "04_design", "05_fashion", "06_other"]

# 友好中文显示名
ym.CATEGORY_DISPLAY.update({
    "01_anime": "动漫影视", "02_scifi": "科幻游戏", "03_art": "绘画艺术",
    "04_design": "商业设计", "05_fashion": "写实时尚", "06_other": "其他综合",
})

# 1) 先读 YouMind 版 data (此时 data/<bucket>.json 还是被覆盖版)
youmind_raw = {}
for b in BUCKETS:
    p = os.path.join(PROJECT, "data", b + ".json")
    youmind_raw[b] = json.load(open(p, encoding="utf-8"))
print("已读 YouMind 版数据:", {b: len(youmind_raw[b]) for b in BUCKETS})

# 2) 恢复 Excel 六类 data/*.json (原图 img_*.jpg 仍在 images/<bucket>/)
for b in BUCKETS:
    shutil.copy2(os.path.join(BACKUP, b + ".json"),
                 os.path.join(PROJECT, "data", b + ".json"))
print("已恢复 Excel 六类 data/*.json")

# 3) 移动 YouMind 原图 -> images/youmind/<slug>/
cat_items, cat_img_count, cat_counter = {}, {}, {}
for b in BUCKETS:
    slug = ym.slugify(b)
    items = youmind_raw[b]
    cat_dir = os.path.join(PROJECT, "images", "youmind", slug)
    os.makedirs(cat_dir, exist_ok=True)
    new_items, local = [], 0
    for it in items:
        img = it.get("image", "")
        pid = it.get("id")
        if img.startswith("images/") and pid is not None:
            old_abs = os.path.join(PROJECT, img)
            ext = ym.ext_from_url(img) or "jpg"
            new_rel = f"images/youmind/{slug}/img_{ym.slugify(str(pid))}.{ext}"
            new_abs = os.path.join(PROJECT, new_rel)
            if os.path.exists(old_abs):
                if not os.path.exists(new_abs):
                    shutil.move(old_abs, new_abs)
                it["image"] = new_rel
                local += 1
        new_items.append(it)
    cat_items[slug] = new_items
    cat_img_count[slug] = local
    cat_counter[slug] = len(new_items)
print("已移动 YouMind 原图, 本地图计数:", cat_img_count)

# 4) add 模式构建网页 (写 data/youmind + youmind.html + 分类页 + 注入 index)
ym.build_web_project(PROJECT, cat_items, cat_img_count, cat_counter, merge=False)
print("ADD 重组完成")
