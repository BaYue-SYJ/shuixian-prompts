#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
扫描 D:\PromptHunter\gallery-dl\Twitter 下的推文文件夹，
解析每条推文的 txt 元数据 + 图片，生成自包含本地预览页（数据内联，图片走同源 http 服务）。
仅用于本地预览，不整合进主画廊。
"""
import os, re, json, html

ROOT = r"D:\PromptHunter\gallery-dl\Twitter"
OUT_HTML = r"D:\PromptHunter\gallery-dl\__twitter_preview.html"
WEB_PREFIX = "Twitter"  # 相对 http 服务根目录(gallery-dl)的路径前缀

HEADER_RE = re.compile(r"^\s*(作者|用户名|时间)\s*[:：]\s*(.*)$")
MARKER_RE = re.compile(r"^\s*(prompt|提示词)\s*[:：]\s*$")
TIME_RE = re.compile(r"^\s*时间\s*[:：]")

def parse_txt(path):
    meta = {"author": "", "username": "", "time": "", "title": "", "prompt": ""}
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return meta
    lines = text.split("\n")
    # 头部键值
    for ln in lines:
        m = HEADER_RE.match(ln)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if k == "作者": meta["author"] = v
            elif k == "用户名": meta["username"] = v
            elif k == "时间": meta["time"] = v
    # 标记行位置
    marker_idx = None
    for i, ln in enumerate(lines):
        if MARKER_RE.match(ln):
            marker_idx = i
            break
    # 时间行之后、标记行之前 = 标题区
    start = 0
    for i, ln in enumerate(lines):
        if TIME_RE.match(ln):
            start = i + 1
            break
    if marker_idx is not None:
        body = lines[start:marker_idx]
        meta["prompt"] = "\n".join(lines[marker_idx + 1:]).strip()
    else:
        rest = [l for l in lines[start:] if l.strip() != ""]
        body = rest[:1]
        meta["prompt"] = "\n".join(rest[1:]).strip()
    # 清理标题前后空行
    bt = [l for l in body]
    while bt and bt[0].strip() == "":
        bt.pop(0)
    while bt and bt[-1].strip() == "":
        bt.pop()
    meta["title"] = "\n".join(bt).strip()
    return meta

def collect():
    tweets = []
    for account in sorted(os.listdir(ROOT)):
        adir = os.path.join(ROOT, account)
        if not os.path.isdir(adir):
            continue
        for tid in sorted(os.listdir(adir)):
            tdir = os.path.join(adir, tid)
            if not os.path.isdir(tdir):
                continue
            imgs = [f for f in sorted(os.listdir(tdir))
                    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))]
            txt = os.path.join(tdir, tid + ".txt")
            meta = parse_txt(txt) if os.path.exists(txt) else {}
            tweets.append({
                "account": account,
                "tweetId": tid,
                "author": meta.get("author", ""),
                "username": meta.get("username", ""),
                "time": meta.get("time", ""),
                "title": meta.get("title", ""),
                "prompt": meta.get("prompt", ""),
                "images": [f"{WEB_PREFIX}/{account}/{tid}/{f}" for f in imgs],
            })
    return tweets

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Twitter 提示词预览</title>
<style>
:root{--blue:#2C8CAB;--blue-soft:#E3F4F8;--bg:#F7F7F7;--white:#fff;--ink:#111;--ink-2:#4A4A4A;--gray:#6B6B6B;--gray-2:#9AA0A6;--line:#EBEBEB;--shadow:0 1px 8px rgba(123,174,191,.10)}
*{box-sizing:border-box}
body{margin:0;font-family:"Noto Sans SC",-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased}
.site-header{position:sticky;top:0;z-index:30;background:var(--white);border-bottom:1px solid var(--line)}
.header-inner{max-width:1440px;margin:0 auto;padding:14px 48px;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.brand{font-size:20px;font-weight:700}
.brand small{color:var(--gray);font-weight:400;font-size:13px;margin-left:8px}
.search-bar{flex:1;min-width:240px;max-width:520px;height:46px;padding:0 18px;border-radius:23px;background:var(--bg);border:1px solid var(--line);display:flex;align-items:center;gap:10px}
.search-bar input{flex:1;border:none;outline:none;font-size:15px;background:transparent;color:var(--ink)}
.count{color:var(--gray);font-size:14px}
main{max-width:1440px;margin:0 auto;padding:28px 48px 64px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px}
.card{background:var(--white);border:1px solid var(--line);border-radius:16px;overflow:hidden;padding:12px;display:flex;flex-direction:column;gap:10px;cursor:pointer;transition:.18s}
.card:hover{transform:translateY(-3px);box-shadow:var(--shadow)}
.card .thumb{width:100%;height:200px;border-radius:12px;object-fit:cover;display:block;background:#eef2f4}
.card .thumb-ph{width:100%;height:200px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#eaf4f7,#dfeef2);color:var(--gray-2);font-size:13px}
.card .cap{font-size:15px;font-weight:500;line-height:1.4;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.card .sub{font-size:12px;color:var(--gray);display:flex;justify-content:space-between;gap:8px}
.card{position:relative}
.badge{position:absolute;top:20px;right:20px;z-index:2;display:inline-flex;align-items:center;gap:4px;background:rgba(14,20,25,.62);color:#fff;font-size:12px;font-weight:600;line-height:1;padding:5px 9px;border-radius:999px;pointer-events:none}
.empty{padding:60px 0;text-align:center;color:var(--gray-2)}
/* lightbox */
.mask{position:fixed;inset:0;background:#0E1419;display:none;z-index:60;align-items:center;justify-content:center;padding:24px}
.mask.show{display:flex}
.lightbox{width:1040px;max-width:100%;max-height:90vh;height:640px;background:var(--white);border-radius:20px;overflow:hidden;display:flex}
.lb-img{width:520px;flex:none;background:#0E1419;display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative}
.lb-img img{max-width:100%;max-height:100%;object-fit:contain}
.lb-nav{position:absolute;top:50%;transform:translateY(-50%);width:42px;height:42px;border-radius:50%;border:none;cursor:pointer;background:rgba(255,255,255,.85);color:#111;font-size:26px;line-height:1;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 14px rgba(0,0,0,.25);opacity:.92;user-select:none}
.lb-nav:hover{background:#fff;opacity:1}
.lb-prev{left:14px}.lb-next{right:14px}
.lb-count{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);background:rgba(14,20,25,.62);color:#fff;font-size:13px;font-weight:600;padding:5px 12px;border-radius:999px;pointer-events:none}
.lb-body{flex:1;padding:32px;display:flex;flex-direction:column;gap:14px;overflow:auto}
.lb-top{display:flex;align-items:center;justify-content:space-between}
.lb-close{width:24px;height:24px;cursor:pointer}
.lb-title{font-size:22px;font-weight:700;line-height:1.3}
.lb-meta{font-size:13px;color:var(--gray)}
.prompt-lbl{font-family:"DM Sans",sans-serif;font-size:12px;font-weight:500;color:var(--blue);letter-spacing:1px}
.prompt-txt{font-size:14px;line-height:1.65;color:#333;white-space:pre-wrap;word-break:break-word}
.lb-actions{display:flex;align-items:center;gap:16px;margin-top:auto}
.copy-btn{display:inline-flex;align-items:center;padding:11px 18px;border-radius:10px;background:var(--blue);color:#fff;font-size:14px;font-weight:500;border:none;cursor:pointer}
.toast{position:fixed;left:50%;bottom:40px;transform:translateX(-50%) translateY(20px);background:rgba(17,17,17,.92);color:#fff;padding:10px 20px;border-radius:10px;font-size:14px;opacity:0;pointer-events:none;transition:.25s;z-index:80}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
@media(max-width:768px){.header-inner{padding:12px 20px}.lightbox{flex-direction:column;height:auto;max-height:92vh}.lb-img{width:100%;height:260px}.lb-body{padding:20px}.main{padding:20px}}
</style>
</head>
<body>
<header class="site-header"><div class="header-inner">
  <div class="brand">Twitter 提示词预览<small id="total"></small></div>
  <div class="search-bar"><input id="search" type="text" placeholder="搜索标题 / 作者 / 提示词…" autocomplete="off"></div>
  <div class="count" id="count"></div>
</div></header>
<main>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">没有匹配的内容</div>
</main>
<div class="mask" id="mask"><div class="lightbox">
  <div class="lb-img"><img id="lbImg" src="" alt="">
    <button class="lb-nav lb-prev" id="lbPrev">‹</button>
    <button class="lb-nav lb-next" id="lbNext">›</button>
    <div class="lb-count" id="lbCount"></div>
  </div>
  <div class="lb-body">
    <div class="lb-top"><span class="lb-meta" id="lbMeta"></span>
      <svg class="lb-close" id="lbClose" viewBox="0 0 24 24" fill="none"><path d="M6 6L18 18M18 6L6 18" stroke="#6B6B6B" stroke-width="2" stroke-linecap="round"/></svg></div>
    <div class="lb-title" id="lbTitle"></div>
    <div class="prompt-lbl">PROMPT</div>
    <div class="prompt-txt" id="lbPrompt"></div>
    <div class="lb-actions"><button class="copy-btn" id="copyBtn">复制提示词</button></div>
  </div>
</div></div>
<div class="toast" id="toast">已复制</div>
<script>
const TWEETS = __TWEETS_JSON__;
const PH = "data:image/svg+xml;utf8,"+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#eaf4f7"/><text x="50%" y="52%" font-size="14" fill="#9AA0A6" text-anchor="middle" font-family="sans-serif">暂无预览</text></svg>');
const grid=document.getElementById('grid'), emptyEl=document.getElementById('empty');
let rendered=0, state={q:""};
document.getElementById('total').textContent=" · "+TWEETS.length+" 条";
const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){const i=e.target;if(i.dataset.src){i.src=i.dataset.src;i.removeAttribute('data-src');}io.unobserve(i);}});},{rootMargin:"300px"});
function getList(){const q=state.q.trim().toLowerCase();if(!q)return TWEETS;return TWEETS.filter(t=>(t.title||"").toLowerCase().includes(q)||(t.author||"").toLowerCase().includes(q)||(t.username||"").toLowerCase().includes(q)||(t.prompt||"").toLowerCase().includes(q));}
function makeCard(t){const card=document.createElement('div');card.className='card';const thumb=document.createElement('div');
  if(t.images&&t.images.length){const img=document.createElement('img');img.className='thumb';img.dataset.src=t.images[0];img.alt=t.title||'';img.loading='lazy';img.onerror=function(){this.onerror=null;this.src=PH;};io.observe(img);thumb.appendChild(img);}
  else{const ph=document.createElement('div');ph.className='thumb-ph';ph.textContent='暂无图';thumb.appendChild(ph);}
  const n=t.images?t.images.length:0;
  if(n>1){const b=document.createElement('div');b.className='badge';b.textContent=n;b.appendChild(document.createTextNode(''));thumb.appendChild(b);}
  const cap=document.createElement('div');cap.className='cap';cap.textContent=t.title||'(未命名)';
  const sub=document.createElement('div');sub.className='sub';
  const a=document.createElement('span');a.textContent='@'+(t.username||t.author||'未知');
  const c=document.createElement('span');c.textContent=(t.images?t.images.length:0)+' 图';
  sub.appendChild(a);sub.appendChild(c);
  card.appendChild(thumb);card.appendChild(cap);card.appendChild(sub);
  card.onclick=()=>openLightbox(t);return card;}
function render(){const list=getList();grid.innerHTML='';rendered=0;
  document.getElementById('count').textContent='显示 '+list.length+' / '+TWEETS.length;
  if(list.length===0){emptyEl.style.display='block';return;}emptyEl.style.display='none';
  list.forEach(t=>grid.appendChild(makeCard(t)));}
const searchInput=document.getElementById('search');let timer=null;
searchInput.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{state.q=searchInput.value;render();},200);});
// lightbox
const mask=document.getElementById('mask');let lbList=[],lbIndex=0,lbCur=null;
function openLightbox(t){lbCur=t;lbList=t.images&&t.images.length?t.images.slice():[];lbIndex=0;renderLb();
  document.getElementById('lbTitle').textContent=t.title||'(未命名)';
  document.getElementById('lbMeta').textContent='@'+(t.username||t.author||'?')+' · '+(t.time||'')+' · '+(t.account||'');
  document.getElementById('lbPrompt').textContent=t.prompt||'(暂无提示词内容)';
  mask.classList.add('show');document.body.style.overflow='hidden';}
function renderLb(){const img=document.getElementById('lbImg');const src=lbList[lbIndex]||'';img.src=src||PH;img.onerror=function(){this.onerror=null;this.src=PH;};
  const prev=document.getElementById('lbPrev'),next=document.getElementById('lbNext'),cnt=document.getElementById('lbCount');
  if(lbList.length>1){prev.style.display='flex';next.style.display='flex';cnt.textContent=(lbIndex+1)+' / '+lbList.length;}else{prev.style.display='none';next.style.display='none';cnt.textContent='';}}
function lbPrev(){if(lbIndex>0){lbIndex--;renderLb();}}
function lbNext(){if(lbIndex<lbList.length-1){lbIndex++;renderLb();}}
function closeLightbox(){mask.classList.remove('show');document.body.style.overflow='';}
document.getElementById('lbClose').onclick=closeLightbox;
document.getElementById('lbPrev').onclick=e=>{e.stopPropagation();lbPrev();};
document.getElementById('lbNext').onclick=e=>{e.stopPropagation();lbNext();};
mask.addEventListener('click',e=>{if(e.target===mask)closeLightbox();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLightbox();else if(mask.classList.contains('show')){if(e.key==='ArrowLeft')lbPrev();else if(e.key==='ArrowRight')lbNext();}});
(function(){const box=document.getElementById('lbImg');let x0=null;box.addEventListener('touchstart',e=>{x0=e.touches[0].clientX;},{passive:true});box.addEventListener('touchend',e=>{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40){if(dx<0)lbNext();else lbPrev();}x0=null;},{passive:true});})();
const toast=document.getElementById('toast');
document.getElementById('copyBtn').onclick=()=>{const txt=document.getElementById('lbPrompt').textContent;navigator.clipboard.writeText(txt).then(()=>{toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1400);}).catch(()=>{const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();document.execCommand('copy');document.body.removeChild(ta);toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1400);});};
render();
</script>
</body>
</html>
"""

def main():
    tweets = collect()
    # 统计
    n_img = sum(len(t["images"]) for t in tweets)
    multi = sum(1 for t in tweets if len(t["images"]) > 1)
    print(f"推文文件夹: {len(tweets)}  图片: {n_img}  多图推文: {multi}")
    data_json = json.dumps(tweets, ensure_ascii=False).replace("</", "<\\/")
    out = TEMPLATE.replace("__TWEETS_JSON__", data_json)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(out)
    print("预览页已生成:", OUT_HTML, "大小:", len(out), "字节")

if __name__ == "__main__":
    main()
