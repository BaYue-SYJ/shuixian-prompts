# -*- coding: utf-8 -*-
"""
process_twitter_0728b.py — 2026-07-28 下午批量 twitter 提示词处理（1506 条新增）
仅处理「今日新增」（相对 backup_twitter_20260728_1004 的 926 条）。
三步：重分类（修正 server.py 子串误判，短英文词改词边界） / 清内容 / 重拟非中文标题。
用法：
  python scripts/process_twitter_0728b.py            # 空跑预览
  python scripts/process_twitter_0728b.py --apply     # 写入本地+部署
"""
import json, re, sys, os, shutil

R = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54"
BASE1004 = f"{R}/backup_twitter_20260728_1004/local/prompts-twitter.json"
LOCAL = f"{R}/shuixian-prompts/data/prompts-twitter.json"
DEPLOY = f"{R}/shuixian-deploy/data/prompts-twitter.json"

# ---------------- 分类：修正版 RULES（短英文词词边界匹配）----------------
RULES = [
    ('字体/排版/标题设计', ['字体','排版','标题设计','typography','艺术字','lettering','书法','字体设计','标题字','字库']),
    ('Logo/品牌/VI', ['视觉识别','商标','品牌设计','标志','logodesign']),  # 收窄：去掉裸 'logo'/'品牌'（incidental 误触）
    ('UI/App/网页/SaaS', ['界面','app','网页','dashboard','saas','小程序','软件','网站','设计系统','移动端','桌面','浏览器','ppt','幻灯片','仪表盘','终端','屏幕','ui']),
    ('产品/电商/包装', ['产品','电商','包装','购物','包装设计','产品渲染','详情页']),
    ('商业海报/广告/社媒', ['海报','广告','杂志','报纸','社交媒体','banner','branding','传单','名片','封面','营销','社媒','宣传','画册','campaign','lookbook']),
    ('摄影/电影感/写实场景', ['摄影','胶片','纪实','电影感','cinematic','镜头','photo','拍立得','写实','真实感','超写实','夜景','街拍','film']),
    ('头像/人像/写真', ['人像','肖像','自拍','头像','写真','portrait','面部','美女','帅哥','古风人物','女性','男性','少女','人物','男神','女神','girl','boy','child','kid','baby','people','model','lady','teen','woman','man']),
    ('插画/涂鸦/手绘风', ['插画','水彩','油画','扁平','手绘','治愈','illustration','绘本','矢量','噪点','厚涂','涂鸦','手绘风','国风']),
    ('漫画/故事板/分镜', ['漫画','故事板','分镜','manga','条漫','漫画分镜','四格']),
    ('3D/游戏/像素/等距', ['3d','c4d','blender','渲染','建模','render','oc渲染','游戏','像素','等距','像素风','游戏原画','游戏场景','voxel']),
    ('信息图/教育图解/图表', ['信息图','教育图解','图表','infographic','数据可视化','图解','示意','流程图']),
]

def _kw_match(kw, text):
    """ASCII 短词（<=3）用词边界；含数字的关键词(3d/c4d)只卡前边界；其余子串。"""
    if kw.isascii() and len(kw) <= 3:
        if any(ch.isdigit() for ch in kw):
            return re.search(r'(?<![a-z0-9])' + re.escape(kw), text) is not None
        return re.search(r'(?<![a-z0-9])' + re.escape(kw) + r'(?![a-z0-9])', text) is not None
    return kw.lower() in text

def classify(title, prompt):
    t = (title or "").lower(); p = (prompt or "").lower()
    best, bs = None, -1
    for cls, words in RULES:
        s = 0
        for w in words:
            wl = w.lower()
            if wl in t: s += 3
            elif _kw_match(wl, p): s += 1
        if s > bs:
            bs, best = s, cls
    return best if bs > 0 else "其他综合"

# ---------------- 内容清洗 ----------------
EMOJI = r"[\U0001F000-\U0001FAFF\u200D\u2600-\u27BF\uFE0F]"

def _extract_from_json(p):
    try:
        d = json.loads(p)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    parts = []
    def grab(o, depth=0):
        if depth > 4: return
        if isinstance(o, str):
            s = o.strip()
            if 15 < len(s) < 400 and not s.startswith('http'):
                parts.append(s)
        elif isinstance(o, dict):
            for v in o.values(): grab(v, depth+1)
        elif isinstance(o, list):
            for v in o[:6]: grab(v, depth+1)
    grab(d)
    # 优先挑含视觉词的长句
    parts.sort(key=lambda s: -len(s))
    for s in parts:
        if re.search(r'portrait|woman|man|girl|boy|car|scene|character|animal|product|building|landscape|render|style', s, re.I):
            return s
    return parts[0] if parts else None

def clean(prompt):
    p = prompt or ""
    if p.strip().startswith("{"):
        ex = _extract_from_json(p)
        if ex:
            p = ex
    urls = re.findall(r'https?://\S+', p)
    body = re.sub(r'https?://\S+', ' ', p)
    # 去聊天/指令前缀
    body = re.sub(r'^\s*(let\'?s|i shared|which one|use the uploaded|please|pls|here(?:’| i)?s|this is|i made|my prompt|prompt below|below is).*?[:：]\s*', '', body, flags=re.I)
    body = re.sub(r'^\s*(let\'?s|i shared|which one|use the uploaded|please|pls)\b.*?[\n。]', ' ', body, flags=re.I)
    # 去 emoji + "Prompt:" 装饰标签（含 ZWJ 连接序列）
    body = re.sub(r'^' + EMOJI + r'*\s*prompt\s*:?', '', body, flags=re.I)
    body = re.sub(r'^\s*(---?prompt---?|--prompt---|----|prompt\s*:?)\s*$', '', body, flags=re.I|re.M)
    body = re.sub(r'prompt\s*:', ' ', body, flags=re.I)
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    if not body and urls:
        return urls[0]
    return body

# ---------------- 启发式中文标题 ----------------
SUBJECT = [
    ('女性', ['woman','women','girl','girls','lady','female','portrait','face','selfie']),
    ('男性', ['man','men','boy','boys','male','gentleman']),
    ('儿童', ['child','children','kid','kids','baby','babies','toddler']),
    ('情侣', ['couple','couples','lovers','wedding','bride','groom']),
    ('人物', ['people','person','crowd','group']),
    ('角色', ['character','characters','avatar','protagonist','hero','knight','warrior']),
    ('汽车', ['car','cars','automobile','vehicle','porsche','ferrari','tesla','bmw','automotive']),
    ('摩托车', ['motorcycle','bike','scooter']),
    ('建筑', ['building','architecture','architectural','skyscraper','interior','room','house']),
    ('美食', ['food','coffee','dish','meal','drink','cake','dessert','cuisine','restaurant']),
    ('花', ['flower','flowers','bloom','rose','botanical']),
    ('产品', ['product','packaging','bottle','device','gadget']),
    ('猫', ['cat','cats','kitten','feline']),
    ('狗', ['dog','dogs','puppy','canine']),
    ('动物', ['animal','animals','creature','fox','wolf','lion','tiger','horse','bird','dragon','bear','rabbit']),
    ('风景', ['landscape','nature','mountain','beach','ocean','forest','city','cityscape','scenery','sunset','sky']),
]
STYLE = [
    ('电影感', ['cinematic','film','film still','movie','drama']),
    ('复古', ['vintage','retro','nostalgic','old']),
    ('霓虹', ['neon','cyberpunk','synthwave','vaporwave']),
    ('赛博朋克', ['cyber','sci-fi','scifi','futuristic','tech']),
    ('3D', ['3d','c4d','blender','render','voxel','isometric','octane']),
    ('像素', ['pixel','8-bit','8bit']),
    ('极简', ['minimal','minimalist','clean','simple']),
    ('高级感', ['luxury','premium','high-end','elegant','sophisticated','refined']),
    ('时尚', ['fashion','editorial','vogue','haute']),
    ('街拍', ['street','urban','candid']),
    ('棚拍', ['studio','studio shot']),
    ('户外', ['outdoor','outside','nature']),
    ('夜景', ['night','nocturnal','dark']),
    ('梦幻', ['dreamy','ethereal','surreal','magical','fantasy','fairy']),
    ('水彩', ['watercolor','aquarelle']),
    ('油画', ['oil painting','renaissance']),
    ('二次元', ['anime','manga','waifu','otaku']),
    ('漫画', ['comic','graphic novel']),
    ('温馨', ['cozy','warm','soft','gentle']),
    ('哥特', ['gothic','dark fantasy']),
    ('国风', ['chinese style','oriental','ink','guofeng']),
    ('海报', ['poster','billboard','banner']),
    ('广告', ['advertisement','ad','commercial','campaign','branding']),
    ('插画', ['illustration','illustrated','concept art']),
]
CAT_HINT = {
    '字体/排版/标题设计': '字体设计',
    'Logo/品牌/VI': '标志/品牌设计',
    'UI/App/网页/SaaS': '界面设计',
    '产品/电商/包装': '产品渲染',
    '商业海报/广告/社媒': '海报设计',
    '摄影/电影感/写实场景': '摄影作品',
    '头像/人像/写真': '人像写真',
    '插画/涂鸦/手绘风': '插画作品',
    '漫画/故事板/分镜': '漫画分镜',
    '3D/游戏/像素/等距': '3D 渲染',
    '信息图/教育图解/图表': '信息图',
    '其他综合': 'AI 生成图片',
}

def has_cjk(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))

def gen_title(entry):
    title = entry.get("title") or ""
    if has_cjk(title) and not title.strip().startswith("{"):
        return None  # 保留可读中文标题
    prompt = clean(entry.get("prompt") or "")
    cat = entry.get("category") or "其他综合"
    text = (prompt or "").lower()
    # 收集命中（英文词用词边界，避免 cat→education 误判）
    def _hit(kws):
        return any(_kw_match(k.lower(), text) for k in kws)
    subj = next((cn for cn, kws in SUBJECT if _hit(kws)), None)
    styles = [cn for cn, kws in STYLE if _hit(kws)]
    sty = styles[0] if styles else ""
    # 组合
    if subj and sty:
        return f"{sty}{subj}"
    if subj and not sty:
        return f"{subj}{CAT_HINT.get(cat,'')}"
    if sty and not subj:
        return f"{sty}{CAT_HINT.get(cat,'作品')}"
    # 兜底：无主体/风格命中 → 直接用分类提示词（纯中文，避免中英混排）
    return CAT_HINT.get(cat, "AI 生成图片")

# ---------------- 主流程 ----------------
def main():
    apply = "--apply" in sys.argv
    base = json.load(open(BASE1004, encoding="utf-8"))
    loc = json.load(open(LOCAL, encoding="utf-8"))
    dep = json.load(open(DEPLOY, encoding="utf-8"))
    base_ids = {e["id"] for e in base}
    loc_map = {e["id"]: e for e in loc}
    new_ids = [i for i in loc_map if i not in base_ids]
    print(f"MODE: {'APPLY' if apply else 'DRY-RUN'} | new entries: {len(new_ids)}")

    cat_ch = tit_ch = con_ch = 0
    samples = []
    for i in new_ids:
        e = loc_map[i]
        o_cat = e.get("category")
        o_prompt = e.get("prompt") or ""
        o_title = e.get("title") or ""
        # 1) 重分类
        n_cat = classify(o_title, o_prompt)
        if n_cat != o_cat:
            cat_ch += 1
        # 2) 清内容
        n_prompt = clean(o_prompt)
        if n_prompt != o_prompt:
            con_ch += 1
        # 3) 重拟标题
        n_title = gen_title(e)
        title_changed = False
        if n_title is not None and n_title != o_title:
            tit_ch += 1
            title_changed = True
        if apply:
            e["category"] = n_cat
            e["prompt"] = n_prompt
            if n_title is not None:
                e["title"] = n_title
        if len(samples) < 50:
            samples.append((i, o_cat, n_cat, o_title, n_title if n_title is not None else "✓",
                            "清" if n_prompt != o_prompt else "✓"))

    print(f"changes -> category:{cat_ch} | title:{tit_ch} | content:{con_ch}")
    print("\n--- sample (id | old_cat->new_cat | old_title -> new_title | content) ---")
    for i, oc, nc, ot, nt, c in samples[:45]:
        print(f"#{i} | {oc}->{nc} | {ot[:38]!r} -> {nt!r} | {c}")

    if apply:
        # 本地与部署初始内容相同、应用相同变换，直接把处理后的 loc 写入两份
        json.dump(loc, open(LOCAL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        json.dump(loc, open(DEPLOY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("WROTE local + deploy (synced).")
        print("deploy synced. done.")

if __name__ == "__main__":
    main()
