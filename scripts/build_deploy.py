#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 Cloudflare Pages（手动拖拽部署）构建部署包：
- 拆分 26MB 的 prompts.json 为多个 <25MB 的 part 文件（拖拽单文件上限 25MiB）
- 生成 R2 版 index.html：图片走可配置的 R2 公共域名（IMG_BASE），数据并发加载多个 part
- 拖拽包不含图片（缩略图+原图全部走 R2），文件数控制在 1000 以内
"""
import json, os, shutil

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
SRC = os.path.join(ROOT, "shuixian-prompts")
DEPLOY = os.path.join(ROOT, "shuixian-deploy")

# ---------- 1. 拆分数据 ----------
data_path = os.path.join(SRC, "data", "prompts.json")
all_items = json.load(open(data_path, encoding="utf-8"))
n = len(all_items)
PARTS = 3  # 26.3MB / 3 ≈ 8.8MB，远低于 25MB 上限
chunk = (n + PARTS - 1) // PARTS

os.makedirs(os.path.join(DEPLOY, "data"), exist_ok=True)
part_files = []
for i in range(PARTS):
    seg = all_items[i * chunk:(i + 1) * chunk]
    p = os.path.join(DEPLOY, "data", f"prompts.part{i+1}.json")
    json.dump(seg, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    part_files.append(p)
    print(f"part{i+1}: {len(seg)} 条 -> {os.path.getsize(p)/1024/1024:.2f} MB")

# categories.json
shutil.copy(os.path.join(SRC, "data", "categories.json"),
            os.path.join(DEPLOY, "data", "categories.json"))

# 二维码（小文件，随 Pages 一起部署）
os.makedirs(os.path.join(DEPLOY, "images"), exist_ok=True)
shutil.copy(os.path.join(SRC, "images", "wechat-qr.jpg"),
            os.path.join(DEPLOY, "images", "wechat-qr.jpg"))

# ---------- 2. 改写 index.html ----------
html = open(os.path.join(SRC, "index.html"), encoding="utf-8").read()

# (a) 增加 IMG_BASE 与 DATA_PARTS 常量
html = html.replace(
    "const CHUNK = 48;",
    'const CHUNK = 48;\n'
    '// ===== Cloudflare R2 图片域名（部署前务必修改）=====\n'
    '// 改成你的 R2 公共访问域名，例如 "https://shuixian-r2.r2.dev" 或自定义域名 "https://cdn.example.com"\n'
    '// 留空 "" 则使用相对路径（仅本地测试用，拖拽部署到 Pages 必须填写）\n'
    'const IMG_BASE = "https://<YOUR-BUCKET>.r2.dev";\n'
    'const DATA_PARTS = ' + json.dumps([f"data/prompts.part{i+1}.json" for i in range(PARTS)], ensure_ascii=False) + ";"
)

# (b) 卡片缩略图：拼 R2 完整地址 + 加载失败回退占位图
html = html.replace(
    '    const img = document.createElement(\'img\');\n'
    '    img.className="thumb"; img.dataset.src=d.thumb; img.alt=d.title||"";\n'
    '    img.loading="lazy";\n'
    '    io.observe(img);',
    '    const img = document.createElement(\'img\');\n'
    '    img.className="thumb"; img.dataset.src=(IMG_BASE?IMG_BASE+"/":"")+d.thumb; img.alt=d.title||"";\n'
    '    img.loading="lazy";\n'
    '    img.onerror=function(){this.onerror=null;this.src=PH;};\n'
    '    io.observe(img);'
)

# (c) 灯箱原图：走 R2 + 失败回退
html = html.replace(
    '  const src = (d.image && d.image.trim()) ? d.image : (d.thumb||"");\n'
    '  img.src = src || PH;',
    '  const src = (d.image && d.image.trim()) ? d.image : (d.thumb||"");\n'
    '  const full = src ? (IMG_BASE?IMG_BASE+"/":"")+src : "";\n'
    '  img.src = full || PH;\n'
    '  img.onerror=function(){this.onerror=null;this.src=PH;};'
)
html = html.replace(
    '  if(src){ link.href = src; link.style.display="inline"; } else { link.style.display="none"; }',
    '  if(full){ link.href = full; link.style.display="inline"; } else { link.style.display="none"; }'
)

# (d) 启动：并发加载多个 part
html = html.replace(
    "fetch('data/prompts.json')\n"
    "  .then(r=>r.json())\n"
    "  .then(data=>{\n"
    "    ALL = data;\n"
    "    renderChips();\n"
    "    resetAndRender();\n"
    "  })\n"
    "  .catch(err=>{\n"
    "    loadingEl.textContent = \"数据加载失败：\" + err.message + \"（请通过本地服务器 http://localhost:8090 打开本页）\";\n"
    "  });",
    "Promise.all(DATA_PARTS.map(u=>fetch(u).then(r=>r.json())))\n"
    "  .then(parts=>{\n"
    "    ALL = parts.flat();\n"
    "    renderChips();\n"
    "    resetAndRender();\n"
    "  })\n"
    "  .catch(err=>{\n"
    "    loadingEl.textContent = \"数据加载失败：\" + err.message;\n"
    "  });"
)

open(os.path.join(DEPLOY, "index.html"), "w", encoding="utf-8").write(html)
print("index.html (R2 版) 已生成")

# ---------- 3. 校验 ----------
files = []
for dp, _, fnames in os.walk(DEPLOY):
    for f in fnames:
        fp = os.path.join(dp, f)
        files.append((fp, os.path.getsize(fp)))
print(f"\n部署包文件数: {len(files)} (拖拽上限 1000)")
over = [f for f, s in files if s > 25*1024*1024]
print(f"超 25MB 文件: {len(over)}")
print("部署包总体积: %.1f MB" % (sum(s for _, s in files)/1024/1024))
print("目录:", DEPLOY)
