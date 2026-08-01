#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把全部提示词重标为【单标签】：每条提示词只归入 12 类中的唯一一类（互斥）。
category 字段写回「字符串」（非数组）。
优先级（越靠前越优先，命中即按其归类）：
  字体/排版/标题设计 > 信息图/教育图解/图表 > Logo/品牌/VI > UI/App/网页/SaaS >
  产品/电商/包装 > 漫画/故事板/分镜 > 3D/游戏/像素/等距 > 插画/涂鸦/手绘风 >
  商业海报/广告/社媒 > 头像/人像/写真 > 摄影/电影感/写实场景 >
  (以上 11 个使用场景都未命中时) 全部人像(含人关键词) > 其他综合(兜底)
"""
import json, re, os, collections, glob

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data")

# ---------- 加载 ----------
def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("LOAD FAIL", p, e); return []
def save_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

# ---------- 清洗模板占位 ----------
TPL = re.compile(r'\{argument[^}]*?default="([^"]*)"[^}]*\}', re.I)
BRACE = re.compile(r'\{[^}]*\}')
def clean_text(e):
    raw = (e.get("title","") or "") + "\n" + (e.get("prompt","") or "")
    raw = TPL.sub(lambda m: m.group(1), raw)
    raw = BRACE.sub(" ", raw)
    return raw

# ---------- 11 个使用场景关键词（同 classify_scenario.py） ----------
CAT_KEYWORDS = {
 "商业海报/广告/社媒": ["海报","poster","广告","advertis","营销","社媒","social media","banner","宣传","促销","小红书","公众号","招贴","封面图","活动海报","主视觉","kv","视觉海报","促销图"],
 "UI/App/网页/SaaS": ["ui","界面","网页","website","web","saas","dashboard","仪表盘","手机界面","应用界面","app","后台","落地页","landing","官网","操作界面","移动端","pc端","弹窗","导航栏","按钮","app界面"],
 "产品/电商/包装": ["产品图","电商","包装","packaging","瓶","bottle","商品","product","礼盒","标签设计","电商主图","详情页","三维产品","产品渲染","瓶身","罐","包装盒","产品展示","包装设计"],
 "头像/人像/写真": ["头像","写真","美颜","证件照","自拍","婚纱","汉服","和服","cosplay","半身","全身","人像","portrait","avatar","beauty","selfie","headshot","妆容","个人写真","艺术照","人脸","人物"],
 "Logo/品牌/VI": ["logo","标志","品牌","brand","vi","视觉识别","emblem","商标","企业形象","logomark","字母标","图形标","徽标"],
 "摄影/电影感/写实场景": ["摄影","photograph","photo","胶片","电影感","cinematic","纪实","街拍","风光","夜景","实拍","场景照","人像摄影","风景摄影","电影海报","film","写实","场景"],
 "信息图/教育图解/图表": ["信息图","infographic","图表","chart","数据","教育","图解","diagram","流程图","时间轴","思维导图","统计","可视化","数据图","知识点","课程","信息图"],
 "漫画/故事板/分镜": ["漫画","comic","manga","故事板","storyboard","分镜","四格","条漫","手绘漫画","连环画","绘本","卡通角色","q版","卡通"],
 "3D/游戏/像素/等距": ["3d","游戏","game","像素","pixel","等距","isometric","建模","render","模型","voxel","低多边形","low poly","游戏角色","游戏场景","二次元游戏","像素风","体素","游戏ui"],
 "插画/涂鸦/手绘风": ["插画","illustration","涂鸦","doodle","手绘","装饰画","矢量插画","扁平插画","水彩","艺术插画","art print","国风插画","治愈插画","壁纸","wallpaper","背景图","概念艺术","concept art","绘本风","板绘","二次元插画"],
 "字体/排版/标题设计": ["字体","font","排版","typography","标题","文字设计","lettering","艺术字","字效","标语","slogan","海报字体","标题字","字形","文字","艺术字"],
}
# 单标签优先级（最具体/最具定义性的类目在前）
PRIORITY = ["字体/排版/标题设计","信息图/教育图解/图表","Logo/品牌/VI","UI/App/网页/SaaS",
            "产品/电商/包装","漫画/故事板/分镜","3D/游戏/像素/等距","插画/涂鸦/手绘风",
            "商业海报/广告/社媒","头像/人像/写真","摄影/电影感/写实场景"]

CAT_REGEX = {}
for cat, kws in CAT_KEYWORDS.items():
    parts = []
    for k in kws:
        if re.fullmatch(r"[a-zA-Z][a-zA-Z/ ]*", k):
            for w in k.replace("/", " ").strip().split():
                parts.append(r"\b" + re.escape(w) + r"\b")
        else:
            parts.append(re.escape(k))
    CAT_REGEX[cat] = re.compile("|".join(parts), re.I)

PERSON_KW = ["人物","女孩","男孩","男人","女人","女性","男性","儿童","婴儿","少年","青年","老年","孕妇","情侣","自拍","肖像","证件照","写真","cosplay","模特","角色","少女","萝莉","正太","御姐","帅哥","美女","人脸","头像","半身","全身","群像","人群","婚纱","汉服","和服","妆容","五官","表情","头发","长发","短发","发丝","侧脸","正脸",
             "girl","girls","boy","boys","woman","women","man","men","person","people","persons","portrait","selfie","child","children","baby","kid","character","characters","cosplay","bride","crowd","hero","heroine","female","male","lady","ladies","gentleman","avatar","avatars","husbando","family"]
PERSON_RE = re.compile("|".join(
    [r"\b"+re.escape(w)+r"\b" if re.fullmatch(r"[a-zA-Z]+",w) else re.escape(w) for w in PERSON_KW]), re.I)

# ---------- 「画图展示」：prompt 只是工具/模型名（不是真实提示词） ----------
MODEL_RE = re.compile(r"(gpt[-\s]?image[-\s]?\w*|chatgpt|midjourney|dall[-\s]?\w*|flux\w*|stable\s*diffusion|sd[-\s]?\w*|sora\w*|imagen\w*|gemini\w*|seedream\w*|krea\w*|recraft\w*|ideogram\w*|kling\w*|grok\w*|veo\w*|nanogpt|nano\s*banana|leonardo\w*|playground\w*|runway\w*|pika\w*|hedra\w*|liblib\w*|即梦|可灵|通义\s*万相|豆包|海艺|秒画|星流|画宇宙|堆友|炉米|灵积)", re.I)
STOP_RE = re.compile(r"\b(prompt|in|alt|the|a|an|of|to|using|use|with|for|image|img|gen|generate|via|by|this|that|my|your|on|at|is|are)\b", re.I)
_PARENS = re.compile(r"^\([^()]{1,45}\)$")
def is_showcase(e):
    """prompt 字段几乎只是模型/工具名（如 'GPT-Image-2'、'(GPT-Image-2)'、'GPT-Image-2 prompt in ALT'），不是真实提示词。"""
    raw = (e.get("prompt","") or "")
    if _PARENS.fullmatch(raw.strip()):
        return True
    t = raw.strip()
    if len(t) > 50:
        return False
    if not MODEL_RE.search(t):
        return False
    s = MODEL_RE.sub("", t); s = STOP_RE.sub("", s); s = re.sub(r"[\W_]+", "", s)
    return len(s) <= 10

def classify_single(text):
    """返回唯一一个类目字符串。"""
    best_cat, best_score = None, 0
    for cat in PRIORITY:                       # PRIORITY 即从高到低
        n = len(set(m.group(0).lower() for m in CAT_REGEX[cat].finditer(text)))
        if n > best_score:
            best_score, best_cat = n, cat
    if best_cat:
        return best_cat
    if PERSON_RE.search(text):
        return "全部人像"
    return "其他综合"

# ---------- 重标所有数据文件 ----------
data_files = []
for d in (LOCAL_DATA, DEPLOY_DATA):
    for p in glob.glob(os.path.join(d, "prompts*.json")):
        if ".bak" not in p:
            data_files.append(p)

dist = collections.Counter()
total = 0
for p in data_files:
    arr = load_json(p)
    if not isinstance(arr, list):
        continue
    changed = 0
    for e in arr:
        if not isinstance(e, dict) or "id" not in e:
            continue
        cat = "画图展示" if is_showcase(e) else classify_single(clean_text(e))
        if e.get("category") != cat:
            e["category"] = cat
            changed += 1
        dist[cat] += 1
        total += 1
    save_json(p, arr)
    print(f"{os.path.relpath(p, ROOT):48s} 条数={len(arr):5d}  本次改写={changed}")

print(f"\n总条目(含两端重复计数): {total}   去重后类别合计={sum(dist.values())}")
print("\n=== 单标签 12 类(+其他综合) 分布 ===")
# 展示顺序：11 使用场景按 PRIORITY，再 全部人像，再 其他综合
order = PRIORITY + ["全部人像", "其他综合", "画图展示"]
for c in order:
    n = dist.get(c, 0)
    print(f"{c:22s} {n:6d}  {round(n/total*100,1)}%")

# ---------- 重生 categories.json（本地+部署，单标签口径） ----------
for d in (LOCAL_DATA, DEPLOY_DATA):
    cat_path = os.path.join(d, "categories.json")
    local = d == LOCAL_DATA
    # categories.json 用本地全部做统计（两端内容一致）
    cnt = collections.Counter()
    allf = glob.glob(os.path.join(d, "prompts*.json"))
    for p in allf:
        if ".bak" in p: continue
        a = load_json(p)
        if isinstance(a, list):
            for e in a:
                if isinstance(e, dict):
                    cnt[e.get("category","其他综合")] += 1
    tot = sum(cnt.values())
    obj = {"total": tot, "categories": [
        {"category": c, "count": cnt.get(c,0), "pct": round(cnt.get(c,0)/tot*100,1)}
        for c in order if cnt.get(c,0) > 0
    ]}
    save_json(cat_path, obj)
    print(f"\n重生 {os.path.relpath(cat_path, ROOT)}: total={tot}")
