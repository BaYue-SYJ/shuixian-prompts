#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水仙的AI提示词 —— YouMind(gpt-image-2) 全量抓取 + 可搜索画廊生成。

抓取每条提示词的：
  - 提示词文本 (translatedContent / content / description)
  - 原图      (media[0])
  - 缩略图    (mediaThumbnails[0])

产出（默认写入 shuixian-prompts/）：
  data/prompts.json            全部条目（缩略图做网格，原图做弹层）
  images/thumbs/<id>.<ext>     缩略图
  images/originals/<id>.<ext>  原图
  index.html                   可搜索画廊（关键词实时筛选 + 排序 + 懒加载 + 弹层）

用法：
  python download_shuixian.py                 # 全量下载并建站
  python download_shuixian.py --max-pages 1   # 试跑 1 页，验证原图/缩略图可下
  python download_shuixian.py --no-download   # 仅用已有 prompts.json 重建 index.html
  python download_shuixian.py --workers 24    # 调并发数
"""
import os
import sys
import json
import time
import re
import logging
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('shuixian')

# ---------- 配置 ----------
API_URL = "https://youmind.com/youmarketing-api/prompts"
REFERER = "https://youmind.com/zh-CN/gpt-image-2-prompts/explore?sortBy=views&sortOrder=desc"
MODEL = "gpt-image-2"
LOCALE = "zh-CN"
LIMIT = 100
MAX_RETRIES = 3                # 单页/单图失败重试次数
MAX_CONSECUTIVE_FAILURES = 12  # 连续整页失败达到此数才终止(容忍临时抖动)
FAILURE_BACKOFF = 30           # 整页失败后等待秒数再重试
WORKERS = 16                   # 图片并发下载线程数
REQUEST_INTERVAL = 0.2         # 翻页间隔秒

PROJECT_DIR = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts"
DATA_DIR = os.path.join(PROJECT_DIR, "data")
THUMB_DIR = os.path.join(PROJECT_DIR, "images", "thumbs")
ORIG_DIR = os.path.join(PROJECT_DIR, "images", "originals")

KNOWN_EXT = {'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'}


# ---------- 工具 ----------
def ext_from_url(u):
    if not u:
        return 'jpg'
    m = re.search(r'\.([a-zA-Z0-9]+)(?:[\?#]|$)', u.split('/')[-1])
    if m and m.group(1).lower() in KNOWN_EXT:
        return m.group(1).lower()
    return 'jpg'


def valid_image(path):
    try:
        with open(path, 'rb') as f:
            head = f.read(12)
    except Exception:
        return False
    if head[:3] == b'\xff\xd8\xff':
        return True
    if head[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return True
    if head[:4] == b'GIF8':
        return True
    return False


def download_image(url, out_path, referer=REFERER):
    """下载单张图到 out_path；已存在且有效则跳过。返回 (ok, skipped)。"""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0 and valid_image(out_path):
        return True, True
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36',
        'Referer': referer,
        'Accept': 'image/avif,image/webp,image/png,image/*,*/*;q=0.8',
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
            if not body:
                raise IOError("empty body")
            tmp = out_path + '.part'
            with open(tmp, 'wb') as f:
                f.write(body)
            if not valid_image(tmp):
                os.remove(tmp)
                raise IOError("not a valid image")
            os.replace(tmp, out_path)
            return True, False
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)
            else:
                log.warning("  图片下载失败 %s: %s", os.path.basename(out_path), e)
    return False, False


def fetch_page(payload, page):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        API_URL, data=data,
        headers={
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Referer': REFERER,
        },
        method='POST')
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
            else:
                log.error("  第 %d 页请求失败: %s", page, e)
    return None


def resolve_prompt(p):
    return (p.get('translatedContent') or p.get('content') or p.get('description') or '').strip()


def slug(s):
    s = re.sub(r'[^a-zA-Z0-9]', '_', str(s).strip().lower())
    return s.strip('_') or 'x'


# ---------- 抓取主逻辑 ----------
def scrape(max_pages=None, workers=WORKERS, no_download=False):
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(THUMB_DIR, exist_ok=True)
    os.makedirs(ORIG_DIR, exist_ok=True)

    if no_download:
        json_path = os.path.join(DATA_DIR, 'prompts.json')
        if not os.path.exists(json_path):
            log.error("未找到 %s，无法 --no-download 重建", json_path)
            return
        items = json.load(open(json_path, encoding='utf-8'))
        log.info("--no-download：直接用已有 %d 条重建 index.html", len(items))
        build_html(items)
        return

    payload = {
        'model': MODEL, 'limit': LIMIT, 'locale': LOCALE, 'q': '',
        'categories': '', 'campaign': None, 'filterMode': None,
        'searchMode': None, 'sortBy': 'views', 'sortOrder': 'desc',
    }

    all_items = []
    seen = set()
    page = 1
    consecutive = 0
    total = None

    while True:
        if max_pages and page > max_pages:
            log.info("已达 --max-pages %d，停止", max_pages)
            break
        payload['page'] = page
        data = fetch_page(payload, page)
        if data is None:
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                log.error("连续 %d 页失败，终止。已保存 %d 条", consecutive, len(all_items))
                break
            log.warning("第 %d 页失败，%ds 后重试同页", page, FAILURE_BACKOFF)
            time.sleep(FAILURE_BACKOFF)
            continue
        consecutive = 0
        if total is None:
            total = data.get('total')
            log.info("总提示词: %s, 总页数: %s", f"{total:,}" if total else '?', data.get('totalPages'))

        batch = data.get('prompts', []) or []

        # ---- 并发下载本页原图 + 缩略图 ----
        results = {}  # pid -> {'orig': path_or_'', 'thumb': path_or_''}
        with ThreadPoolExecutor(max_workers=workers) as ex:
            fut_map = {}
            for p in batch:
                pid = p.get('id')
                if pid in seen:
                    continue
                media = p.get('media', []) or []
                thumbs = p.get('mediaThumbnails', []) or []
                orig = media[0] if media else ''
                thumb = thumbs[0] if thumbs else ''
                if orig:
                    op = os.path.join(ORIG_DIR, f"{slug(pid)}.{ext_from_url(orig)}")
                    fut_map[ex.submit(download_image, orig, op)] = ('orig', pid)
                if thumb:
                    tp = os.path.join(THUMB_DIR, f"{slug(pid)}.{ext_from_url(thumb)}")
                    fut_map[ex.submit(download_image, thumb, tp)] = ('thumb', pid)
            for fut in as_completed(fut_map):
                kind, pid = fut_map[fut]
                ok, _ = fut.result()
                results.setdefault(pid, {})[kind] = ok

        # ---- 组装条目 ----
        for p in batch:
            pid = p.get('id')
            if pid in seen:
                continue
            seen.add(pid)
            media = p.get('media', []) or []
            thumbs = p.get('mediaThumbnails', []) or []
            orig_url = media[0] if media else ''
            thumb_url = thumbs[0] if thumbs else ''
            r = results.get(pid, {})
            # 浏览器可解析的相对路径（正斜杠）；下载失败则回退远程 URL
            rel_orig = f"images/originals/{slug(pid)}.{ext_from_url(orig_url)}"
            rel_thumb = f"images/thumbs/{slug(pid)}.{ext_from_url(thumb_url)}"
            orig_local = rel_orig if (orig_url and r.get('orig')) else orig_url
            thumb_local = rel_thumb if (thumb_url and r.get('thumb')) else (thumb_url or orig_local)
            author = p.get('author', {}) or {}
            item = {
                "id": pid,
                "title": p.get('title', '') or 'Untitled',
                "prompt": resolve_prompt(p),
                "thumb": thumb_local,
                "image": orig_local,
                "author": author.get('name', '') if isinstance(author, dict) else '',
                "likes": p.get('likes', 0) or 0,
                "resultsCount": p.get('resultsCount', 0) or 0,
                "slug": p.get('slug', '') or '',
            }
            all_items.append(item)

        log.info("第 %d 页: 本页 %d 条, 累计 %d", page, len(batch), len(all_items))
        if not data.get('hasMore'):
            break
        page += 1
        time.sleep(REQUEST_INTERVAL)

    # ---- 清理中断残留的 .part 临时文件 ----
    for d in (THUMB_DIR, ORIG_DIR):
        try:
            for fn in os.listdir(d):
                if fn.endswith('.part'):
                    os.remove(os.path.join(d, fn))
        except Exception:
            pass

    # ---- 写数据 ----
    json_path = os.path.join(DATA_DIR, 'prompts.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=1)
    log.info("已写入 %s (%d 条)", os.path.relpath(json_path, PROJECT_DIR), len(all_items))

    # ---- 建站 ----
    build_html(all_items)


# ---------- HTML 生成 ----------
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>水仙的AI提示词</title>
<style>
:root{
  --bg:#f5f6f8; --panel:#ffffff; --ink:#1a1a1a; --muted:#6b7280;
  --accent:#e94560; --line:#e5e7eb; --chip:#eef1f5;
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink)}
header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:14px 20px}
.h-wrap{max-width:1320px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.brand{font-size:20px;font-weight:700}
.brand small{color:var(--muted);font-weight:400;margin-left:8px;font-size:13px}
.search{flex:1;min-width:220px}
.search input{width:100%;padding:10px 14px;border:1px solid var(--line);border-radius:10px;font-size:15px;background:var(--panel)}
.sort select{padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--panel);font-size:14px}
.meta{color:var(--muted);font-size:13px;padding:10px 20px;max-width:1320px;margin:0 auto}
.grid{max-width:1320px;margin:0 auto;padding:8px 20px 60px;display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.10)}
.card .thumb{width:100%;aspect-ratio:1/1;object-fit:cover;display:block;background:var(--chip)}
.card .cap{padding:8px 10px;font-size:13px;line-height:1.4;color:var(--ink);height:42px;overflow:hidden}
.sentinel{height:1px}
.modal-mask{position:fixed;inset:0;background:rgba(15,18,25,.72);display:none;z-index:50;align-items:center;justify-content:center;padding:24px}
.modal-mask.show{display:flex}
.modal{background:var(--panel);border-radius:14px;max-width:1040px;width:100%;max-height:90vh;overflow:auto;display:flex;flex-direction:column}
.modal .top{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line)}
.modal .top h3{margin:0;font-size:16px;word-break:break-all}
.modal .close{cursor:pointer;border:none;background:var(--chip);border-radius:8px;padding:6px 12px;font-size:14px}
.modal .body{display:flex;gap:18px;padding:18px;flex-wrap:wrap}
.modal .imgwrap{flex:1 1 380px;min-width:280px}
.modal .imgwrap img{width:100%;border-radius:10px;display:block;background:var(--chip)}
.modal .info{flex:1 1 320px;min-width:260px}
.modal .prompt{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px;font-size:14px;line-height:1.7;max-height:320px;overflow:auto;word-break:break-word}
.modal .row{display:flex;gap:10px;align-items:center;margin:10px 0;color:var(--muted);font-size:13px;flex-wrap:wrap}
.copy{cursor:pointer;border:1px solid var(--accent);color:var(--accent);background:#fff;border-radius:8px;padding:6px 12px;font-size:13px}
.empty{text-align:center;color:var(--muted);padding:60px 20px}
</style>
</head>
<body>
<header><div class="h-wrap">
  <div class="brand">水仙的AI提示词<small>可搜索提示词原图库</small></div>
  <div class="search"><input id="q" placeholder="搜索标题 / 提示词 / 作者…"></div>
  <div class="sort"><select id="sort">
    <option value="default">默认顺序</option>
    <option value="likes">最多点赞</option>
    <option value="results">最多生成</option>
  </select></div>
</div></header>
<div class="meta" id="meta"></div>
<div class="grid" id="grid"></div>
<div class="sentinel" id="sentinel"></div>
<div class="empty" id="empty" style="display:none">没有匹配的提示词</div>

<div class="modal-mask" id="mask">
  <div class="modal">
    <div class="top"><h3 id="m-title"></h3><button class="close" id="m-close">关闭</button></div>
    <div class="body">
      <div class="imgwrap"><img id="m-img" alt=""></div>
      <div class="info">
        <div class="row" id="m-row"></div>
        <div class="prompt" id="m-prompt"></div>
        <div style="margin-top:12px"><button class="copy" id="m-copy">复制提示词</button></div>
      </div>
    </div>
  </div>
</div>

<script>
let ALL=[];
const grid=document.getElementById('grid');
const meta=document.getElementById('meta');
const emptyEl=document.getElementById('empty');
const q=document.getElementById('q');
const sortSel=document.getElementById('sort');
const sentinel=document.getElementById('sentinel');
let view=[];
let rendered=0;
const PAGE=60;
let current=null;

function fmt(n){ return (n||0).toLocaleString(); }

fetch('data/prompts.json').then(r=>r.json()).then(d=>{
  ALL=d;
  apply();
}).catch(e=>{
  meta.textContent='数据加载失败，请通过 HTTP 服务访问（不要用 file:// 直接打开）';
  console.error(e);
});

function matches(it){
  const s=q.value.trim().toLowerCase();
  if(!s) return true;
  return (it.title||'').toLowerCase().includes(s)
      || (it.prompt||'').toLowerCase().includes(s)
      || (it.author||'').toLowerCase().includes(s);
}
function apply(){
  let arr=ALL.filter(matches);
  const sv=sortSel.value;
  if(sv==='likes') arr.sort((a,b)=>(b.likes||0)-(a.likes||0));
  else if(sv==='results') arr.sort((a,b)=>(b.resultsCount||0)-(a.resultsCount||0));
  view=arr; rendered=0; grid.innerHTML=''; emptyEl.style.display='none';
  meta.textContent='共 '+fmt(ALL.length)+' 条提示词 · 匹配 '+fmt(view.length)+' 条';
  loadMore();
}
function loadMore(){
  const next=view.slice(rendered, rendered+PAGE);
  for(const it of next){
    const card=document.createElement('div');
    card.className='card';
    const img=document.createElement('img');
    img.className='thumb'; img.loading='lazy';
    img.src=it.thumb||it.image; img.alt=it.title||'';
    img.onerror=()=>{ img.src=it.image||''; };
    const cap=document.createElement('div');
    cap.className='cap'; cap.textContent=it.title||'(无标题)';
    card.appendChild(img); card.appendChild(cap);
    card.onclick=()=>openModal(it);
    grid.appendChild(card);
  }
  rendered+=next.length;
  emptyEl.style.display = (view.length===0) ? 'block' : 'none';
}
q.addEventListener('input', apply);
sortSel.addEventListener('change', apply);

const io=new IntersectionObserver(es=>{
  if(es[0].isIntersecting && rendered<view.length){ loadMore(); }
},{rootMargin:'500px'});
io.observe(sentinel);

const mask=document.getElementById('mask');
function openModal(it){
  current=it;
  document.getElementById('m-title').textContent=it.title||'(无标题)';
  const im=document.getElementById('m-img');
  im.src=it.image||it.thumb; im.onerror=()=>{ im.src=it.thumb||''; };
  document.getElementById('m-prompt').textContent=it.prompt||'(无提示词内容)';
  document.getElementById('m-row').textContent=
    '作者：'+(it.author||'未知')+'  ·  点赞：'+fmt(it.likes)+'  ·  生成数：'+fmt(it.resultsCount);
  mask.classList.add('show');
}
document.getElementById('m-close').onclick=()=>mask.classList.remove('show');
mask.onclick=e=>{ if(e.target===mask) mask.classList.remove('show'); };
document.getElementById('m-copy').onclick=()=>{
  if(current&&current.prompt){
    navigator.clipboard.writeText(current.prompt).then(()=>{
      const b=document.getElementById('m-copy'); const t=b.textContent;
      b.textContent='已复制 ✓'; setTimeout(()=>b.textContent=t,1500);
    });
  }
};
document.addEventListener('keydown',e=>{ if(e.key==='Escape') mask.classList.remove('show'); });
</script>
</body>
</html>
"""


def build_html(items):
    out = os.path.join(PROJECT_DIR, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    log.info("已生成 %s（%d 条）", os.path.relpath(out, PROJECT_DIR), len(items))


# ---------- 入口 ----------
if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=None, help='最多抓几页（试跑用）')
    ap.add_argument('--workers', type=int, default=WORKERS, help='图片并发下载线程数')
    ap.add_argument('--no-download', action='store_true', help='仅用已有 prompts.json 重建 index.html')
    args = ap.parse_args()
    scrape(max_pages=args.max_pages, workers=args.workers, no_download=args.no_download)
    log.info("🎉 完成！")
