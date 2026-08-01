# -*- coding: utf-8 -*-
"""处理 2026-07-28 新增的 twitter 提示词：重分类 + 清内容 + 重拟差标题。

范围：仅处理相对 backup_twitter_20260727_1240/prompts-twitter.json（12:40, 841 条）
      新增的 85 条真实图片提示词。
      - 不动 107 条旧“画廊”损坏占位条目
      - 不动 10 条“每日一词”文案帖（本次新增无此类）
      - 不动主库 prompts.json / prompts.partN.json
      - 不动 07-27 已处理的 173 条（账号映射已移除，避免回退那 26 条映射结果）
本地(shuixian-prompts)与部署(shuixian-deploy)两端同步改写。
改前已备份至 backup_twitter_20260728_1004/。
"""
import json, re, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
LOCAL_TW  = os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter.json")
DEPLOY_TW = os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter.json")
BAK       = os.path.join(ROOT, "backup_twitter_20260727_1240", "prompts-twitter.json")
DRY = "--apply" not in sys.argv

RULES = [
    ('字体/排版/标题设计', ['字体','排版','标题设计','typography','艺术字','lettering','书法','字体设计','标题字','字库']),
    ('Logo/品牌/VI', ['logo','品牌','视觉识别','商标','品牌设计','标志','logodesign']),  # 已去掉裸 'vi'（会误中 youvibe）
    ('UI/App/网页/SaaS', ['界面','app','网页','dashboard','saas','小程序','软件','网站','原型','设计系统','移动端','手机','桌面','浏览器','ppt','幻灯片','仪表盘','终端','屏幕','ui']),
    ('产品/电商/包装', ['产品','电商','包装','商品','购物','包装设计','产品渲染','详情页']),
    ('商业海报/广告/社媒', ['海报','广告','杂志','报纸','社交媒体','banner','branding','传单','名片','封面','营销','社媒','宣传','画册']),
    ('摄影/电影感/写实场景', ['摄影','胶片','纪实','电影感','cinematic','镜头','photo','拍立得','写实','真实感','超写实','夜景','街拍']),
    ('头像/人像/写真', ['人像','肖像','自拍','头像','写真','portrait','面部','美女','帅哥','古风人物','女性','男性','少女','人物','男神','女神','beauty','model','studio','woman','girl']),
    ('插画/涂鸦/手绘风', ['插画','水彩','油画','扁平','手绘','治愈','illustration','绘本','矢量','噪点','厚涂','涂鸦','手绘风','国风']),
    ('漫画/故事板/分镜', ['漫画','故事板','分镜','manga','条漫','漫画分镜','四格']),
    ('3D/游戏/像素/等距', ['3d','c4d','blender','渲染','建模','render','oc渲染','游戏','像素','等距','像素风','游戏原画','游戏场景','voxel']),
    ('信息图/教育图解/图表', ['信息图','教育图解','图表','infographic','数据可视化','图解','示意','流程图']),
]

# 明显错分桶（人像/摄影内容被误归到此类的，必须纠正）
MISBUCKET = {'Logo/品牌/VI', 'UI/App/网页/SaaS'}

def kw_match(kw, text):
    """长度<=3 的英文关键词用边界匹配，避免 'app' 误中 'happy'、'ui' 误中 'youvibe'。"""
    if kw.isascii() and len(kw) <= 3:
        if any(ch.isdigit() for ch in kw):
            pat = r'(?<![a-z0-9])' + re.escape(kw)          # 3d/c4d：只卡前边界
        else:
            pat = r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])'
        return re.search(pat, text, re.I) is not None
    return kw.lower() in text.lower()

def classify(title, prompt):
    t = (title or "").lower(); p = (prompt or "").lower(); best_cls = None; bs = -1
    for cls, words in RULES:
        s = 0
        for w in words:
            wl = w.lower()
            if kw_match(wl, t): s += 3
            elif kw_match(wl, p): s += 1
        if s > bs: bs, best_cls = s, cls
    return best_cls if bs > 0 else "其他综合"

def clean(p):
    p = p or ""
    urls = re.findall(r'https?://\S+', p)
    body = re.sub(r'https?://\S+', ' ', p)
    # 去掉 emoji + “Prompt:” 装饰标签（含 ZWJ 连接序列如 🏴‍☠️ / 🧚‍♀️；在话题标签之后也能清）
    body = re.sub(r'[\U0001F000-\U0001FAFF\u200D\u2600-\u27BF\uFE0F]*\s*prompt\s*:?', '', body, flags=re.I)
    body = re.sub(r'^\s*(---?prompt---?|--prompt---|----)\s*$', '', body, flags=re.I|re.M)
    # 去掉英文聊天前缀 / 泛泛标题
    body = re.sub(
        r'^(let\'?s dance together\.?|which one you prefer\??:|check prompt|i shared my prompt here|prompt is here|today\'?s portrait[^\n]*|i feel so hot today\.?|today is so hot|try me[^\n]*|now i need to play[^\n]*|random shot and i feel it is good\.?|get idea from here\.?|after party portrait\.?|this is the new qwen[^\n]*|portrait by[^\n]*|tired|imperfection|portrait\.?|a new happy hour portrait\.?)\s*[\n:：]?\s*',
        '', body, flags=re.I)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    real = body and (len(body) > 40 or ',' in body or
                     re.search(r'vertical|iphone|photorealistic|9:16|portrait|ccd|flash|studio|model|film|china|korean|japanese|fantasy|xianxia|古风|人像|摄影|写真|手机|画面|女生|女性|少女', body, re.I))
    if real:
        return body
    if urls:
        return urls[0]          # URL-only 条目：保留分享链接，避免 prompt 变空
    return (p or "").strip()

# ---- BubbleBrain 28 条“差标题”用手写中文标题替换；其余保留原标题 ----
# 有真实 prompt 正文 → 由正文提炼；仅分享链接/聊天（无正文）→ 中性“生成图片”标题
TITLE_MAP = {
    32184: "AI 生成图片",
    32185: "Y2K 灰发时尚编辑人像",
    32186: "唐风古装 俏皮人像",
    32187: "韩系 CCD 楼梯间人像",
    32188: "韩系胶片 甜美人像",
    32189: "电影感 暗调近景人像",
    32190: "仙侠古风 梦幻人像",
    32191: "CCD 夜店舞池人像",
    32192: "百叶窗前 时尚编辑人像",
    32193: "工作室 情绪感人像",
    32194: "Qwen 3.0 生成图片",
    32195: "Y2K 夜店人像",
    32196: "AI 生成图片",
    32197: "夜店欢乐时光 人像",
    32198: "日系晨光 私房人像",
    32199: "GPT Image2 生成图片",
    32200: "日系柔焦 室内人像",
    32201: "CCD 柔焦 慵懒人像",
    32202: "韩系 Y2K 夜店人像",
    32203: "AI 生成图片",
    32204: "AI 生成图片",
    32205: "AI 生成图片",
    32206: "AI 生成图片",
    32207: "暗调骨相 氛围人像",
    32208: "Kimi K3 生成图片",
    32209: "AI 生成图片",
    32210: "韩系偶像 天台人像",
    32211: "仙侠暗黑 古风人像",
    32261: "夏日泳池 比基尼写真",   # DeepBlueAIX：标题原为 emoji+Prompt，无中文
}

def has_cn(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s or ""))

def process(path):
    data = json.load(open(path, encoding="utf-8"))
    bak_ids = {e.get("id") for e in json.load(open(BAK, encoding="utf-8"))}
    scope = [e for e in data if e.get("id") not in bak_ids]
    n_cat = n_prompt = n_title = 0
    plan = []
    for e in scope:
        i = e["id"]; cur_cat = e.get("category") or ""; cur_prompt = e.get("prompt") or ""; cur_title = e.get("title") or ""
        sug = classify(cur_title, cur_prompt)
        # 重分类策略：明显错分桶(Logo/UI)→按关键词纠正；正常类不向下降级到“其他综合”
        if sug != cur_cat:
            if cur_cat in MISBUCKET:
                new_cat = sug
            elif sug == "其他综合":
                new_cat = cur_cat          # 不降级
            else:
                new_cat = sug
        else:
            new_cat = cur_cat
        cp = clean(cur_prompt)
        new_title = cur_title
        if i in TITLE_MAP:
            new_title = TITLE_MAP[i]
        elif not has_cn(cur_title):
            new_title = "AI 生成图片"
        d = {}
        if new_cat != cur_cat:
            d["cat"] = f"{cur_cat}→{new_cat}"; n_cat += 1
        if cp != cur_prompt:
            d["prompt"] = "clean"; n_prompt += 1
        if new_title != cur_title:
            d["title"] = f"{cur_title!r}→{new_title!r}"; n_title += 1
        if d:
            plan.append((i, e.get("author"), d))
        if not DRY:
            if "cat" in d: e["category"] = new_cat
            if "prompt" in d: e["prompt"] = cp
            if "title" in d: e["title"] = new_title
    if not DRY:
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return len(scope), n_cat, n_prompt, n_title, plan

if __name__ == "__main__":
    mode = "DRY-RUN (不写入)" if DRY else "APPLY (已写入)"
    print("MODE:", mode)
    for name, p in (("本地", LOCAL_TW), ("部署", DEPLOY_TW)):
        tot, c, pr, ti, plan = process(p)
        print(f"\n[{name}] 范围 {tot} 条 | 改分类 {c} | 清内容 {pr} | 重拟标题 {ti} -> {os.path.basename(p)}")
        for i, auth, d in plan:
            print(f"  #{i} [{auth}] " + " | ".join(f"{k}:{v}" for k, v in d.items()))
