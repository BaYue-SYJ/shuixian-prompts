#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按「使用场景」12 类（多标签）重新统计全部提示词（仅分析，不改代码）。
一条提示词可同时归入它符合的所有分类；12 类 = 11 个使用场景 + 全部人像。"""
import json, re, os, collections

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data")

# ---------- 加载 + 去重 ----------
def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("LOAD FAIL", p, e); return []

files = []
for d in (LOCAL_DATA, DEPLOY_DATA):
    for name in os.listdir(d):
        if name.endswith(".json") and name.startswith("prompts") and ".bak" not in name:
            files.append(os.path.join(d, name))

entries = {}
for f in files:
    arr = load_json(f)
    if isinstance(arr, list):
        for e in arr:
            if isinstance(e, dict) and "id" in e:
                entries.setdefault(e["id"], e)
print(f"数据文件:{len(files)}  去重后提示词总数:{len(entries)}")

# ---------- 清洗模板占位 ----------
TPL = re.compile(r'\{argument[^}]*?default="([^"]*)"[^}]*\}', re.I)
BRACE = re.compile(r'\{[^}]*\}')
def clean_text(e):
    raw = (e.get("title","") or "") + "\n" + (e.get("prompt","") or "")
    raw = TPL.sub(lambda m: m.group(1), raw)
    raw = BRACE.sub(" ", raw)
    return raw

# ---------- 11 个使用场景 + 同义词关键词 ----------
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

# 同义词归并正则
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

# 全部人像（跨类，沿用人物口径，剔除 model）
PERSON_KW = ["人物","女孩","男孩","男人","女人","女性","男性","儿童","婴儿","少年","青年","老年","孕妇","情侣","自拍","肖像","证件照","写真","cosplay","模特","角色","少女","萝莉","正太","御姐","帅哥","美女","人脸","头像","半身","全身","群像","人群","婚纱","汉服","和服","妆容","五官","表情","头发","长发","短发","发丝","侧脸","正脸",
             "girl","girls","boy","boys","woman","women","man","men","person","people","persons","portrait","selfie","child","children","baby","kid","character","characters","cosplay","bride","crowd","hero","heroine","female","male","lady","ladies","gentleman","avatar","avatars","husbando","family"]
PERSON_RE = re.compile("|".join(
    [r"\b"+re.escape(w)+r"\b" if re.fullmatch(r"[a-zA-Z]+",w) else re.escape(w) for w in PERSON_KW]), re.I)

def classify_multi(text):
    """多标签：返回 (命中的使用场景集合, 是否含人物)。"""
    cats = set()
    for cat, rgx in CAT_REGEX.items():
        if rgx.search(text):
            cats.add(cat)
    is_person = bool(PERSON_RE.search(text))
    return cats, is_person

# ---------- 统计（多标签） ----------
cat_count = collections.Counter()
person_count = 0
covered = 0
residual = []
for e in entries.values():
    text = clean_text(e)
    cats, is_person = classify_multi(text)
    if is_person:
        cat_count["全部人像"] += 1
    for c in cats:
        cat_count[c] += 1
    if cats or is_person:
        covered += 1
    else:
        residual.append(e.get("title",""))

total = len(entries)

# ---------- 输出 ----------
order_cats = [c for c in CAT_KEYWORDS] + ["全部人像"]
rows = []
for c in order_cats:
    n = cat_count.get(c,0)
    rows.append((c, n, round(n/total*100,1)))

md = ["# 使用场景 12 类 提示词分布（多标签）", "",
      f"- 分析提示词总数：**{total}** 条（本地版 + 部署版去重）",
      "- **多标签**：一条提示词可同时归入它符合的所有分类（如「电影感人像海报」同时计入 商业海报 / 头像人像 / 摄影 / 全部人像）",
      "- 方法：中英文关键词匹配（同义词合并），命中即计入，不做单选",
      "- 「全部人像」为独立一类（含人物/角色等关键词，已剔除 model），与其余 11 类可重叠",
      f"- **并集覆盖率**：{covered}/{total} = {round(covered/total*100,1)}%（至少有 1 个类目命中的提示词占比）",
      "",
      "| 排名 | 分类 | 提示词数 | 占比(相对总数) |",
      "|----|----|----|----|"]
for i,(c,n,p) in enumerate(rows,1):
    md.append(f"| {i} | {c} | {n} | {p}% |")
md.append("")
md.append(f"> 注：因多标签，上表各「占比」之和会 **大于 100%**（一条提示词被重复计数）。")
md.append(f"> 全部人像单独 = {person_count} 条（{round(person_count/total*100,1)}%）。")
if residual:
    md.append("")
    md.append(f"## 未命中任何类目的提示词（{len(residual)} 条）")
    md.append("")
    md.append("、".join(residual[:50]))
out = os.path.join(ROOT, "prompt_scenario_analysis.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("\n=== 12 类（多标签）===")
for c,n,p in rows:
    print(f"{c:22s} {n:6d}  {p}%")
print(f"\n并集覆盖: {covered}/{total} = {round(covered/total*100,1)}%")
print(f"未命中: {len(residual)} 条")
if residual:
    print("样例:", "、".join(residual[:15]))
print("写入:", out)
