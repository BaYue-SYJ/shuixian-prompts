# -*- coding: utf-8 -*-
"""reclassify_17cat_strict.py
严格版【17 类单标签重分类】—— 人物优先（零泄漏）。

判定：
  1) 命中 v3 高召回人物检测(含严格二次审计) -> 人物类；
     其中动漫信号强 -> 动漫/二次元人物，否则 -> 真人/写实人物。
  2) 未命中人物 -> 17cat 非人关键词优先级，最高分类；全不中 -> 其他/未归类。

尊重人工真值：
  - reclass_map.json（16 类时代的 200 条人工真值）：
      值 "人物"        -> 按信号拆成 真人/动漫
      值 "食物/饮品"   -> 映射到 产品/电商/包装
      其它非人值        -> 原样保留（用户在 16 类时代已逐条读过）
  - _person_overrides.json（8 条确认泄漏）-> 按信号拆成 真人/动漫
  - 人工真值/覆盖条目不被“严格审计”翻回（尊重人工判断），但会报告疑似含人的非人真值供复核。

本地+部署同步改写；并再生 categories.json。
用法：
  python scripts/reclassify_17cat_strict.py          # dry-run 打印分布+将改写数
  python scripts/reclassify_17cat_strict.py --apply  # 写回本地+部署 + 重生 categories.json
"""
import json, re, os, collections, glob, sys, importlib.util

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data")

# ---------- 复用 v3 的严格人物检测（零泄漏保证） ----------
_spec = importlib.util.spec_from_file_location(
    "rpv3", os.path.join(ROOT, "scripts", "reclassify_person_v3.py"))
rpv3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rpv3)
has_person = rpv3.has_person
has_person_strict = rpv3.has_person_strict

# ---------- 17 类展示顺序 ----------
CATEGORIES_17 = [
    "真人/写实人物", "动漫/二次元人物",
    "字体/排版/标题", "Logo/品牌/VI", "UI/App/网页/SaaS", "产品/电商/包装", "海报/广告/社媒",
    "插画/艺术/概念", "漫画/分镜/故事板", "信息图/教育图解", "3D/游戏/像素/等距",
    "建筑/室内/空间", "风景/自然", "动物/宠物", "车辆/机械/科幻", "抽象/纹理/背景", "其他/未归类",
]

# ---------- 清洗模板占位 ----------
TPL = re.compile(r'\{argument[^}]*?default="([^"]*)"[^}]*\}', re.I)
BRACE = re.compile(r'\{[^}]*\}')
def clean_text(e):
    raw = (e.get("title", "") or "") + "\n" + (e.get("prompt", "") or "")
    raw = TPL.sub(lambda m: m.group(1), raw)
    raw = BRACE.sub(" ", raw)
    return raw

# ---------- 真人 / 动漫 信号 ----------
ANIME_KW = ["动漫", "二次元", "动画", "漫画", "卡通", "日系插画", "赛璐璐", " anime", "anime ", "anime,",
            "manga", "cartoon", "cel shading", "吉卜力", "宫崎骏", "日漫", "comic style", "2d",
            "二次元风格", "插画风", "日式动", "acg", "galgame", "立绘", "二次元少女", "动漫风", "动画风",
            "anime style", "manga style", "2d illustration", "chibi", "q版", "二次元插画", "comic", "anime"]
REAL_KW = ["真人", "摄影", "写实", "照片", "胶片", "棚拍", "人像摄影", "realistic", "real photo",
           "photoreal", "photograph", "电影感", "live action", "real life", "portrait photo", "单反",
           "影棚", "光圈", "写真摄影", "纪实", "街拍", "时尚摄影", "real person", "cosplay 真人",
           "电影截图", "实拍", "人像写真", "影棚写真", "婚纱摄影", "汉服摄影", "和服"]
def person_kind(text):
    a = sum(1 for k in ANIME_KW if k in text)
    r = sum(1 for k in REAL_KW if k in text)
    return "动漫/二次元人物" if a > r else "真人/写实人物"

# ---------- 非人 关键词 ----------
CAT_KEYWORDS = {
    "字体/排版/标题": ["字体", "font", "排版", "typography", "标题", "文字设计", "lettering", "艺术字", "字效", "标语", "slogan", "海报字体", "标题字", "字形", "文字", "艺术字"],
    "Logo/品牌/VI": ["logo", "标志", "品牌", "brand", "vi", "视觉识别", "emblem", "商标", "企业形象", "logomark", "字母标", "图形标", "徽标"],
    "UI/App/网页/SaaS": ["ui", "界面", "网页", "website", "web", "saas", "dashboard", "仪表盘", "手机界面", "应用界面", "app", "后台", "落地页", "landing", "官网", "操作界面", "移动端", "pc端", "弹窗", "导航栏", "按钮", "app界面"],
    "产品/电商/包装": ["产品图", "电商", "包装", "packaging", "瓶", "bottle", "商品", "product", "礼盒", "标签设计", "电商主图", "详情页", "三维产品", "产品渲染", "瓶身", "罐", "包装盒", "产品展示", "包装设计", "食物", "美食", "蛋糕", "咖啡", "饮料", "餐饮", "food", "coffee", "cake", "dessert", "drink", "meal", "burger", "pizza", "零食"],
    "海报/广告/社媒": ["海报", "poster", "广告", "advertis", "营销", "社媒", "social media", "banner", "宣传", "促销", "小红书", "公众号", "招贴", "封面图", "活动海报", "主视觉", "kv", "视觉海报", "促销图"],
    "漫画/分镜/故事板": ["漫画", "comic", "manga", "故事板", "storyboard", "分镜", "四格", "条漫", "手绘漫画", "连环画", "绘本", "卡通角色", "q版", "卡通"],
    "信息图/教育图解": ["信息图", "infographic", "图表", "chart", "数据", "教育", "图解", "diagram", "流程图", "时间轴", "思维导图", "统计", "可视化", "数据图", "知识点", "课程"],
    "3D/游戏/像素/等距": ["3d", "游戏", "game", "像素", "pixel", "等距", "isometric", "建模", "render", "模型", "voxel", "低多边形", "low poly", "游戏角色", "游戏场景", "二次元游戏", "像素风", "体素", "游戏ui"],
    "插画/艺术/概念": ["插画", "illustration", "涂鸦", "doodle", "手绘", "装饰画", "矢量插画", "扁平插画", "水彩", "艺术插画", "art print", "国风插画", "治愈插画", "壁纸", "wallpaper", "背景图", "概念艺术", "concept art", "绘本风", "板绘", "二次元插画", "油画", "painting", "艺术", "抽象艺术"],
    "建筑/室内/空间": ["建筑", "室内", "房间", "城堡", "城市", "街道", "店铺", "咖啡馆", "教堂", "寺庙", "家居", "空间", "卧室", "客厅", "interior", "building", "city", "room", "architecture", "cafe", "shop", "建筑摄影", "室内设计", "场景设计"],
    "风景/自然": ["风景", "风光", "山水", "自然", "森林", "海", "天空", "日落", "日出", "雪山", "草原", "湖泊", "星空", "极光", "沙漠", "花海", "田园", "风光摄影", "风景摄影", "landscape", "nature", "mountain", "ocean", "sunset", "scenery", "forest", "极光"],
    "动物/宠物": ["猫", "狗", "动物", "鸟", "马", "龙", "老虎", "狮子", "宠物", "鱼", "狐狸", "狼", "兔子", "cat", "dog", "animal", "dragon", "bird", "furry", "kitty", "puppy", "宠物摄影"],
    "车辆/机械/科幻": ["车", "汽车", "机甲", "机器人", "飞船", "武器", "机械", "载具", "vehicle", "car", "robot", "mecha", "sci-fi", "spaceship", "weapon", "armor", "机甲", "科幻", "赛车"],
    "抽象/纹理/背景": ["纹理", "背景", "图案", "材质", "渐变", "wallpaper", "texture", "pattern", "background", "无缝", "底纹", "抽象背景", "几何"],
}
NONPERSON_PRIORITY = ["字体/排版/标题", "Logo/品牌/VI", "UI/App/网页/SaaS", "产品/电商/包装", "海报/广告/社媒",
                      "漫画/分镜/故事板", "信息图/教育图解", "3D/游戏/像素/等距", "插画/艺术/概念",
                      "建筑/室内/空间", "风景/自然", "动物/宠物", "车辆/机械/科幻", "抽象/纹理/背景"]

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

def classify_auto(e):
    """自动分类（无人工覆盖时）。"""
    text = clean_text(e)
    if has_person(e) or has_person_strict(e):
        return person_kind(text)
    best_cat, best_score = None, 0
    for cat in NONPERSON_PRIORITY:
        n = len(set(m.group(0).lower() for m in CAT_REGEX[cat].finditer(text)))
        if n > best_score:
            best_score, best_cat = n, cat
    return best_cat or "其他/未归类"

# ---------- 人工真值 ----------
def load_json(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as ex:
        print("LOAD FAIL", p, ex)
        return {}

manual_raw = load_json(os.path.join(ROOT, "reclass_map.json"))
manual = {}
for k, v in manual_raw.items():
    ik = int(k)
    if v == "人物":
        manual[ik] = None          # None 标记：按信号拆 真人/动漫
    elif v == "食物/饮品":
        manual[ik] = "产品/电商/包装"
    else:
        manual[ik] = v
overrides = {int(k): None for k in load_json(os.path.join(ROOT, "_person_overrides.json"))}

PERSON_CLASSES = ("真人/写实人物", "动漫/二次元人物")

APPLY = "--apply" in sys.argv
data_files = []
for d in (LOCAL_DATA, DEPLOY_DATA):
    for p in glob.glob(os.path.join(d, "prompts*.json")):
        if ".bak" not in p:
            data_files.append(p)

dist = collections.Counter()
total = 0
changed_total = 0
flipped = []              # 自动翻回人物的 id
manual_leak = []          # 人工真值标非人、但严格审计含人（不自动翻回，供复核）
for p in data_files:
    arr = load_json(p)
    if not isinstance(arr, list):
        continue
    changed = 0
    for e in arr:
        if not isinstance(e, dict) or "id" not in e:
            continue
        i = e["id"]
        if i in overrides:
            cat = person_kind(clean_text(e))         # 覆盖 人物 -> 拆信号（优先于人工真值）
        elif i in manual:
            mc = manual[i]
            if mc is None:
                cat = person_kind(clean_text(e))     # 人工 人物 -> 拆信号
            else:
                cat = mc
                if cat not in PERSON_CLASSES and has_person_strict(e):
                    manual_leak.append((i, cat, p))
        else:
            cat = classify_auto(e)
        # 硬规则：最终非人但严格审计含人 -> 翻回人物（不翻人工真值/覆盖）
        if cat not in PERSON_CLASSES:
            if has_person_strict(e):
                cat = person_kind(clean_text(e))
                if i not in manual and i not in overrides:
                    flipped.append(i)
        if e.get("category") != cat:
            e["category"] = cat
            changed += 1
        dist[cat] += 1
        total += 1
    if APPLY:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(arr, f, ensure_ascii=False, indent=1)
    print(f"{os.path.relpath(p, ROOT):48s} 条数={len(arr):5d}  {'改写' if APPLY else '待改'}={changed}")
    changed_total += changed

print(f"\n总条目(含两端重复计数): {total}   本次{'改写' if APPLY else '将改写'}={changed_total}")
print(f"严格审计自动翻回人物(非人工覆盖): {len(flipped)}")
if manual_leak:
    print("\n⚠ 人工真值标为非人、但严格审计疑似含人的条目（不自动翻回，请复核）：")
    for i, c, p in manual_leak:
        print(f"   [{c}] {i}  @ {os.path.relpath(p, ROOT)}")

print("\n=== 17 类分布 ===")
for c in CATEGORIES_17:
    n = dist.get(c, 0)
    print(f"{c:18s} {n:6d}  {round(n/total*100,1) if total else 0}%")
oob = [c for c in dist if c not in CATEGORIES_17]
if oob:
    print("\n!! 越界类目(不在17类内):", oob)

if APPLY:
    for d in (LOCAL_DATA, DEPLOY_DATA):
        cat_path = os.path.join(d, "categories.json")
        cnt = collections.Counter()
        for p in glob.glob(os.path.join(d, "prompts*.json")):
            if ".bak" in p:
                continue
            a = load_json(p)
            if isinstance(a, list):
                for e in a:
                    if isinstance(e, dict):
                        cnt[e.get("category", "其他/未归类")] += 1
        tot = sum(cnt.values())
        obj = {"total": tot, "categories": [
            {"category": c, "count": cnt.get(c, 0), "pct": round(cnt.get(c, 0) / tot * 100, 1)}
            for c in CATEGORIES_17 if cnt.get(c, 0) > 0
        ]}
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        print(f"\n重生 {os.path.relpath(cat_path, ROOT)}: total={tot}")
