#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确识别 434 条 residual：区分 twitter(可删) 与 YouMind 主库(保留)，并导出删除清单。"""
import json, re, os, collections

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data")

def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("LOAD FAIL", p, e); return []

# ---- 收集文件，标记是否 twitter 文件 ----
twitter_files, main_files = [], []
for d in (LOCAL_DATA, DEPLOY_DATA):
    for name in os.listdir(d):
        if not name.endswith(".json") or ".bak" in name or name.startswith("categories"):
            continue
        if name.startswith("prompts-twitter"):
            twitter_files.append(os.path.join(d, name))
        elif name in ("prompts.json",) or name.startswith("prompts.part"):
            main_files.append(os.path.join(d, name))

# 每 id 记录：首次出现的完整 dict、来源文件集合、是否为 twitter 来源
entry_by_id = {}
sources = collections.defaultdict(set)
is_tw_src = collections.defaultdict(bool)
for f in twitter_files + main_files:
    arr = load_json(f)
    if not isinstance(arr, list): continue
    tw = f in set(twitter_files)
    for e in arr:
        if not isinstance(e, dict) or "id" not in e: continue
        i = e["id"]
        if i not in entry_by_id:
            entry_by_id[i] = e
        sources[i].add(f)
        if tw:
            is_tw_src[i] = True

# ---- 多标签分类器（与 classify_scenario.py 同口径） ----
TPL = re.compile(r'\{argument[^}]*?default="([^"]*)"[^}]*\}', re.I)
BRACE = re.compile(r'\{[^}]*\}')
def clean_text(e):
    raw = (e.get("title","") or "") + "\n" + (e.get("prompt","") or "")
    raw = TPL.sub(lambda m: m.group(1), raw); raw = BRACE.sub(" ", raw)
    return raw

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

def classify(text):
    cats = set()
    for cat, rgx in CAT_REGEX.items():
        if rgx.search(text): cats.add(cat)
    return cats, bool(PERSON_RE.search(text))

# ---- 找 residual ----
residual = []          # 全 residual
tw_delete = []         # twitter 来源 → 可删
ym_keep = []           # YouMind 主库来源 → 保留
for i, e in entry_by_id.items():
    cats, person = classify(clean_text(e))
    if not cats and not person:
        rec = {"id": i, "title": e.get("title",""), "author": e.get("author",""),
               "image": e.get("image",""), "images": e.get("images",[]),
               "tw_src": is_tw_src[i]}
        residual.append(rec)
        if is_tw_src[i]:
            tw_delete.append(rec)
        else:
            ym_keep.append(rec)

print(f"总条目: {len(entry_by_id)}")
print(f"residual 总数: {len(residual)}")
print(f"  ├ twitter 来源(可删): {len(tw_delete)}")
print(f"  └ YouMind 主库来源(保留): {len(ym_keep)}")

# 导出 twitter 删除清单（含 tweet id）
def tweet_ids_of(rec):
    ids = []
    paths = []
    if rec["image"]: paths.append(rec["image"])
    if rec["images"]: paths.extend(rec["images"])
    for p in paths:
        m = re.search(r"(\d{15,})\.jpg$", str(p), re.I)
        if m: ids.append(m.group(1))
    return sorted(set(ids)), paths

for rec in tw_delete:
    tids, paths = tweet_ids_of(rec)
    rec["tweet_ids"] = tids
    rec["img_paths"] = paths

out = os.path.join(ROOT, "scripts", "_residual_twitter_delete.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(tw_delete, f, ensure_ascii=False, indent=1)
print("twitter 删除清单 ->", out)

# 抽查 YouMind 保留项，确认是真实提示词
print("\n--- YouMind 主库 residual(保留) 抽样，确认非闲聊 ---")
for rec in ym_keep[:8]:
    print("  id=%s | %s" % (rec["id"], rec["title"][:50]))
