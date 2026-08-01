#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分析全部提示词中出现频率最高的 30 个词（合并同义词）。"""
import json, re, os, collections

ROOT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
LOCAL_DATA = os.path.join(ROOT, "shuixian-prompts", "data")
DEPLOY_DATA = os.path.join(ROOT, "shuixian-deploy", "data")

# ---------- 加载全部提示词（去重） ----------
def load_json(p):
    with open(p, encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            print("LOAD FAIL", p, e)
            return []

files = []
for d in (LOCAL_DATA, DEPLOY_DATA):
    for name in os.listdir(d):
        if name.endswith(".json") and (
            name.startswith("prompts") or name == "prompts.json"
        ) and ".bak" not in name:
            files.append(os.path.join(d, name))

entries = {}
for f in files:
    arr = load_json(f)
    if isinstance(arr, list):
        for e in arr:
            if isinstance(e, dict) and "id" in e:
                entries.setdefault(e["id"], e)
print(f"数据文件: {len(files)}  去重后提示词总数: {len(entries)}")

# ---------- 清洗：抽出模板中的 default 真实文本 ----------
TPL = re.compile(r'\{argument[^}]*?default="([^"]*)"[^}]*\}', re.I)
BRACE = re.compile(r'\{[^}]*\}')

def clean_text(e):
    title = e.get("title", "") or ""
    prompt = e.get("prompt", "") or ""
    raw = title + "\n" + prompt
    raw = TPL.sub(lambda m: m.group(1), raw)   # 用 default 真实值替换模板
    raw = BRACE.sub(" ", raw)                  # 去掉残余 {} 内容
    return raw

# ---------- 中文分词 (jieba) ----------
import jieba
jieba.setLogLevel(20)

EN_TOK = re.compile(r"[A-Za-z][A-Za-z\-']*")

# ---------- 停用词 ----------
EN_STOP = set("""a an the and or of to in on for with at by from as is are was were be been being
this that these those it its it's i you he she they we my your his her their our your s t
into out up down off over under between among through during before after about above below
not no nor so than too very can will just also more most such other each any all both few
one two three new old using use used using per via de la le du des un une les au aux et
style styles high low top side make made making create created generating generate
image images picture photo photograph photos""".split())

CN_STOP = set("""的 了 和 与 及 或 在 是 我 你 他 她 它 们 这 那 这个 那个 这些 那些 有 也 都 就 而 等 中 上 下 里 个 之 其 为 以 对 于 与 把 被 让 给 从 到 并 但 因 因为 所以 如果 一个 一种 一样 不 无 没 又 再 很 更 最 着 过 吗 呢 吧 啊 啦 的 地 得 及 且 或 若 如 同 像 将 被 使 让 给 向 往 由 靠 用 把 拿 和 跟 与 及 或 但 然 后 则 即 亦 将 已 己 自 此 彼 某 各 该 每 任 何 些 多 少 大 小 前 后 左 右 内 外 全 半 整 完 整 一个 一种 一样 一起 一下 一种 部分""".split())

# 模板胶水词 / 量词 / 连接词（非内容词，剔除）
CN_FILLER = set("""一张 一位 以及 带有 采用 使用 左侧 右侧 上方 下方 中间 整体 局部 呈现 具有 通过 根据 例如 包括 主要 形成 营造 突出 体现 展现 描绘 塑造 刻画 展示 显示 进行 表现 组合 元素 特点 特点 风格为 风格是 的 是 为 与 和 以 在 上 下 中 内 外 用 将 把 被 让 给 向 往 由 靠 从 到 并 且 但 因 所以 如果 一种 一个 一样 一起 一下 同时 此外 另外 其中 整体 部分 方面""".split())

# ---------- 同义词合并表（相同意思 -> 规范词） ----------
SYN = {
    # 人物相关
    "woman": "女性/人物", "women": "女性/人物", "female": "女性/人物",
    "lady": "女性/人物", "girl": "女性/人物", "girls": "女性/人物",
    "man": "男性/人物", "men": "男性/人物", "male": "男性/人物",
    "boy": "男性/人物", "boys": "男性/人物",
    "person": "人物", "people": "人物", "character": "角色/人物",
    "characters": "角色/人物", "portrait": "人像", "portraits": "人像",
    "face": "脸/面部", "faces": "脸/面部",
    # 质量/细节/真实感
    "detailed": "精细/细节", "detail": "精细/细节", "details": "精细/细节",
    "intricate": "精细/细节",
    "realistic": "写实/真实感", "realism": "写实/真实感",
    "photorealistic": "写实/真实感", "photo realistic": "写实/真实感",
    "high": "高(质量/分辨率)", "quality": "高(质量/分辨率)",
    "hq": "高(质量/分辨率)",
    "resolution": "分辨率", "hd": "高清", "sharp": "清晰", "sharpness": "清晰",
    # 画面构成
    "background": "背景", "bg": "背景",
    "foreground": "前景", "scene": "场景", "scenes": "场景",
    "composition": "构图", "lighting": "光影/光照", "light": "光影/光照",
    "shadow": "阴影", "shadows": "阴影", "shadow s": "阴影",
    "color": "颜色/色彩", "colors": "颜色/色彩", "colour": "颜色/色彩",
    "colourful": "颜色/色彩", "colorful": "颜色/色彩",
    "white": "白色", "black": "黑色",
    # 风格/媒介
    "illustration": "插画", "illustrations": "插画", "illustrate": "插画",
    "design": "设计", "designs": "设计",
    "art": "艺术/美术", "artwork": "艺术/美术", "artworks": "艺术/美术",
    "anime": "动漫", "cartoon": "卡通", "manga": "漫画",
    "painting": "绘画", "paint": "绘画", "drawing": "绘画", "draw": "绘画",
    "3d": "3D", "render": "渲染", "rendering": "渲染", "cinematic": "电影感",
    "concept": "概念", "concept art": "概念",
    "ui": "界面/UI", "ux": "界面/UI", "interface": "界面/UI",
    "logo": "标志/Logo", "logos": "标志/Logo",
    "icon": "图标", "icons": "图标",
    "poster": "海报", "posters": "海报", "banner": "横幅",
    "photo": "照片/摄影", "photograph": "照片/摄影", "photography": "照片/摄影",
    "landscape": "风景", "portraits photography": "摄影",
    # 其他高频概念
    "cute": "可爱", "beautiful": "美丽", "elegant": "优雅",
    "mini": "迷你", "small": "小", "large": "大", "big": "大",
    "vintage": "复古", "retro": "复古", "modern": "现代", "futuristic": "未来感",
    "fantasy": "奇幻", "surreal": "超现实", "abstract": "抽象",
    "minimal": "极简", "minimalist": "极简", "simple": "简约",
    "soft": "柔和", "dark": "暗调", "bright": "明亮", "vibrant": "鲜艳",
    "texture": "纹理", "textures": "纹理", "pattern": "图案", "patterns": "图案",
    "nature": "自然", "animal": "动物", "animals": "动物",
    "food": "美食", "character design": "角色设计",
    "game": "游戏", "game ui": "游戏", "ui design": "界面/UI",
    "vector": "矢量", "flat": "扁平", "isometric": "等距/2.5D",
}

# 中文同义词
CN_SYN = {
    "女性": "女性/人物", "女人": "女性/人物", "女孩": "女性/人物", "女生": "女性/人物",
    "少女": "女性/人物", "美女": "美丽", "男子": "男性/人物", "男人": "男性/人物",
    "男性": "男性/人物", "男孩": "男性/人物", "男生": "男性/人物",
    "人物": "人物", "角色": "角色/人物", "人像": "人像", "肖像": "人像",
    "脸": "脸/面部", "面部": "脸/面部", "脸部": "脸/面部",
    "细节": "精细/细节", "精细": "精细/细节", "精致": "精细/细节",
    "写实": "写实/真实感", "真实": "写实/真实感", "真实感": "写实/真实感",
    "高质量": "高(质量/分辨率)", "品质": "高(质量/分辨率)", "高清": "高清",
    "清晰": "清晰", "分辨率": "分辨率", "背景": "背景", "前景": "前景",
    "场景": "场景", "构图": "构图", "光影": "光影/光照", "光照": "光影/光照",
    "光线": "光影/光照", "阴影": "阴影", "颜色": "颜色/色彩", "色彩": "颜色/色彩",
    "白色": "白色", "黑色": "黑色", "插画": "插画", "插图": "插画",
    "设计": "设计", "艺术": "艺术/美术", "美术": "艺术/美术",
    "动漫": "动漫", "动画": "动漫", "卡通": "卡通", "漫画": "漫画",
    "绘画": "绘画", "画": "绘画", "3d": "3D", "三维": "3D", "渲染": "渲染",
    "电影感": "电影感", "概念": "概念", "界面": "界面/UI", "ui": "界面/UI",
    "标志": "标志/Logo", "logo": "标志/Logo", "图标": "图标",
    "海报": "海报", "横幅": "横幅", "摄影": "照片/摄影", "照片": "照片/摄影",
    "风景": "风景", "可爱": "可爱", "美丽": "美丽", "漂亮": "美丽",
    "优雅": "优雅", "迷你": "迷你", "小": "小", "大": "大",
    "复古": "复古", "现代": "现代", "未来": "未来感", "未来感": "未来感",
    "奇幻": "奇幻", "超现实": "超现实", "抽象": "抽象", "极简": "极简",
    "简约": "简约", "简单": "简约", "柔和": "柔和", "暗": "暗调",
    "暗调": "暗调", "明亮": "明亮", "鲜艳": "鲜艳", "纹理": "纹理",
    "图案": "图案", "自然": "自然", "动物": "动物", "美食": "美食",
    "游戏": "游戏", "矢量": "矢量", "扁平": "扁平", "风格": "风格",
    "全身": "全身", "半身": "半身", "特写": "特写", "近景": "特写",
    "蓝色": "蓝色", "红色": "红色", "绿色": "绿色", "黄色": "黄色",
    "粉色": "粉色", "紫色": "紫色", "金色": "金色", "银色": "银色",
    "头发": "头发", "长发": "头发", "短发": "头发", "眼睛": "眼睛",
    "皮肤": "皮肤", "服装": "服装", "衣服": "服装", "裙子": "服装",
    "天空": "天空", "水": "水", "城市": "城市", "建筑": "建筑",
    "室内": "室内", "室外": "室外", "森林": "自然", "花": "花",
    "工作室": "工作室", "产品": "产品", "包装": "包装", "字体": "字体",
    "文字": "文字", "标题": "标题", "品牌": "品牌",
}

def canon(token, is_cn):
    if is_cn:
        return CN_SYN.get(token, token)
    # 英文：先小写
    t = token.lower()
    t = t.strip("-'")
    if not t:
        return None
    if t in SYN:
        return SYN[t]
    # 轻量复数归一（>=5 字母、以 s 结尾、非 ss 结尾）
    if len(t) >= 5 and t.endswith("s") and not t.endswith("ss"):
        sing = t[:-1]
        if sing in SYN:
            return SYN[sing]
    return t

# ---------- 统计 ----------
doc_freq = collections.Counter()      # 出现在多少条提示词中
occ_freq = collections.Counter()      # 总出现次数

for e in entries.values():
    text = clean_text(e)
    seen_in_doc = set()
    # 中文：jieba 切分
    for seg in jieba.cut(text):
        seg = seg.strip()
        if not seg:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]+", seg):   # 纯中文词
            if seg in CN_STOP or seg in CN_FILLER:
                continue
            if len(seg) < 2:                          # 剔除单字碎片(感/级/画…)
                continue
            c = canon(seg, True)
            if c and len(c) >= 2:
                occ_freq[c] += 1
                seen_in_doc.add(c)
        elif EN_TOK.fullmatch(seg):                  # 英文词
            c = canon(seg, False)
            if c is None:
                continue
            if c in EN_STOP:
                continue
            if len(c) < 2:
                continue
            occ_freq[c] += 1
            seen_in_doc.add(c)
        # 混合/数字/符号 跳过
    for c in seen_in_doc:
        doc_freq[c] += 1

total = len(entries)
print(f"\n=== 按「出现条数」(文档频率) 排名 Top 30 ===")
rows = []
for term, cnt in doc_freq.most_common(30):
    pct = cnt / total * 100
    rows.append((term, cnt, round(pct, 1), occ_freq[term]))

# 输出 markdown 表格
md = ["# 提示词高频词 Top 30（合并同义词）", "",
      f"- 分析提示词总数：**{total}** 条（本地版 + 部署版去重）",
      "- 统计口径：①「出现在多少条提示词中」(文档频率) 为主排序；②「总出现次数」为辅",
      "- 已剔除模板 `{argument ...}` 占位语法，仅统计真实提示词内容",
      "- 已剔除中文模板胶水词（一张/一位/以及/带有/采用/使用/左侧…）与单字碎片，避免模板噪声",
      "- 中英文同义词已归并（如 woman/girl/女性→女性/人物；realistic/写实→写实/真实感）",
      "",
      "| 排名 | 词（合并同义） | 出现条数 | 占比 | 总出现次数 |",
      "|----|----|----|----|----|"]
for i, (term, cnt, pct, occ) in enumerate(rows, 1):
    md.append(f"| {i} | {term} | {cnt} | {pct}% | {occ} |")
md.append("")
out = os.path.join(ROOT, "prompt_wordfreq_top30.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("\n".join(md))
print("\n写入:", out)
