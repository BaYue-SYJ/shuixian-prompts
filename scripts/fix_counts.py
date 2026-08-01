"""方案3 收尾：把 merge 遗留的错数字改回正确值（纯离线，不重抓网络）。

- 6 个 Excel 分类页 hero 三数字（提示词条目 / 配图数量 / 总库占比）→ Excel 真实值
- index.html 的 6 张 Excel 卡片（提示词 / 占比）→ Excel 真实值
- index.html 头部三统计 + header-sub + footer 文案 → 全站合并值（6 Excel + YouMind）
- YouMind 卡片的 13,496 保持不动
复用 youmind_scraper 里已验证的 replace_class_nums / atomic_write_text。
"""
import os, json, re, sys
sys.path.insert(0, r"C:\Users\lianxiang\Downloads")
import youmind_scraper as ym  # 有 __main__ 守卫，import 安全

P = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\style-gallery"
BUCKETS = ["01_anime", "02_scifi", "03_art", "04_design", "05_fashion", "06_other"]

YOUMIND_PROMPTS = 13496
YOUMIND_IMGS = 13480

# 真实 Excel 数据
counts, imgs = {}, {}
for b in BUCKETS:
    items = json.load(open(os.path.join(P, "data", b + ".json"), encoding="utf-8"))
    counts[b] = len(items)
    d = os.path.join(P, "images", b)
    n = len([f for f in os.listdir(d) if f.startswith("img_")]) if os.path.isdir(d) else 0
    imgs[b] = n

EXCEL_TOTAL = sum(counts.values())
EXCEL_IMG = sum(imgs.values())
COMBINED_P = EXCEL_TOTAL + YOUMIND_PROMPTS
COMBINED_I = EXCEL_IMG + YOUMIND_IMGS
print(f"Excel 总条数={EXCEL_TOTAL:,}  总图={EXCEL_IMG:,}  | 合并后 条={COMBINED_P:,} 图={COMBINED_I:,}")

# 1) 6 个分类页
for b in BUCKETS:
    cnt, imc = counts[b], imgs[b]
    pct = cnt / EXCEL_TOTAL * 100
    path = os.path.join(P, b + ".html")
    html = open(path, encoding="utf-8").read()
    html = ym.replace_class_nums(html, "stat-num", [cnt, imc, f"{pct:.1f}%"])
    ym.atomic_write_text(path, html)
    print(f"  {b}.html -> 条目 {cnt:,} / 配图 {imc:,} / 占比 {pct:.1f}%")

# 2) index.html
idx = os.path.join(P, "index.html")
html = open(idx, encoding="utf-8").read()

# 6 张 Excel 卡片：每卡 (提示词, 占比) + YouMind 卡(13,496) 保持
card_vals = []
for b in BUCKETS:
    pct = counts[b] / EXCEL_TOTAL * 100
    card_vals.extend([counts[b], f"{pct:.1f}%"])
card_vals.append(YOUMIND_PROMPTS)  # YouMind 卡，原样保留
html = ym.replace_class_nums(html, "card-meta-num", card_vals)

# 头部三统计
html = ym.replace_class_nums(html, "header-stat-num", [COMBINED_P, COMBINED_I, 7])

# 文案
html = re.sub(r"6 大视觉类别 · 13,496 条提示词",
              f"7 大视觉类别 · {COMBINED_P:,} 条提示词", html)
html = re.sub(r"13,496 entries · 6 categories",
              f"{COMBINED_P:,} entries · 7 categories", html)
ym.atomic_write_text(idx, html)
print(f"  index.html -> 头部 {COMBINED_P:,} / {COMBINED_I:,} / 7 ; Excel 卡片已修正; YouMind 卡保留 13,496")
print("DONE")
