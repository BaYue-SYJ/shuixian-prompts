# -*- coding: utf-8 -*-
"""处理今天(2026-07-27)新增的 twitter 提示词：重分类 + 清内容 + 重拟差标题。

范围：仅处理相对 backup_twitter16/data_20260727_095928/prompts-twitter.local.bak
      新增的 183 条中、属于“真实图片提示词”的 173 条。
      - 不动 107 条旧“画廊”损坏占位条目
      - 不动 10 条“每日一词”文案帖（无 prompt、标题已可读）
      - 不动主库 prompts.json / prompts.partN.json
本地(shuixian-prompts)与部署(shuixian-deploy)两端同步改写。
改前已备份至 backup_twitter_20260727_1240/。
"""
import json, re, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
LOCAL_TW = os.path.join(ROOT, "shuixian-prompts", "data", "prompts-twitter.json")
DEPLOY_TW = os.path.join(ROOT, "shuixian-deploy", "data", "prompts-twitter.json")
BAK = os.path.join(ROOT, "backup_twitter16", "data_20260727_095928", "prompts-twitter.local.bak")
RULES = [
    ('字体/排版/标题设计', ['字体','排版','标题设计','typography','艺术字','lettering','书法','字体设计','标题字','字库']),
    ('Logo/品牌/VI', ['logo','品牌','vi','视觉识别','商标','品牌设计','标志','logodesign']),
    ('UI/App/网页/SaaS', ['ui','app','界面','终端','屏幕','原型','设计系统','ppt','幻灯片','浏览器','网页','桌面','仪表盘','dashboard','移动端','手机','小程序','网站','软件','saas']),
    ('产品/电商/包装', ['产品','电商','包装','商品','购物','包装设计','产品渲染','详情页']),
    ('商业海报/广告/社媒', ['海报','广告','杂志','报纸','社交媒体','banner','branding','传单','名片','封面','营销','社媒','宣传','画册']),
    ('摄影/电影感/写实场景', ['摄影','胶片','纪实','电影感','cinematic','镜头','photo','拍立得','写实','真实感','超写实','夜景','街拍']),
    ('头像/人像/写真', ['人像','肖像','自拍','头像','写真','portrait','面部','美女','帅哥','古风人物','女性','男性','少女','人物','男神','女神']),
    ('插画/涂鸦/手绘风', ['插画','水彩','油画','扁平','手绘','治愈','illustration','绘本','矢量','噪点','厚涂','涂鸦','手绘风','国风']),
    ('漫画/故事板/分镜', ['漫画','故事板','分镜','manga','条漫','漫画分镜','四格']),
    ('3D/游戏/像素/等距', ['3d','c4d','blender','渲染','建模','render','oc渲染','游戏','像素','等距','像素风','游戏原画','游戏场景','voxel']),
    ('信息图/教育图解/图表', ['信息图','教育图解','图表','infographic','数据可视化','图解','示意','流程图']),
]

def classify(title, prompt, account=None):
    t = (title or "").lower(); p = (prompt or "").lower(); best_cls = None; bs = -1
    for cls, words in RULES:
        s = 0
        for w in words:
            wl = w.lower()
            if wl in t: s += 3
            elif wl in p: s += 1
        if s > bs: bs, best_cls = s, cls
    return best_cls if bs > 0 else "其他综合"

def clean(p):
    p = p or ""
    p = re.sub(r'^请使用下面的prompt生成\d*张独立的图片（注意，不是collage多张图片到一张图片，而是\d*张独立图片）：\s*', '', p, flags=re.I)
    p = re.sub(r'图[二三四五六七八九]提示词[:：]\s*', '', p)
    p = re.sub(r'(正向提示词|负向提示词|反向提示词|主体描述|场景设定|镜头美学|服装和姿态|构图建议)[:：]\s*', '', p)
    p = re.sub(r'^(create a |generate a )[^\n:：]{0,60}[:：]\s*', '', p, flags=re.I)
    p = re.sub(r'https?://\S+', '', p)
    p = re.sub(r'(no watermark|no readable text|no logo|no visible brand logos|no visible text|no readable words)', '', p, flags=re.I)
    p = re.sub(r'constraints:\s*', '', p, flags=re.I)
    p = re.sub(r'\n{3,}', '\n\n', p).strip()
    return p

# ---- 仅这 18 条“差标题”用手写 AI 标题替换（其余保留原标题）----
BAD_TITLES = {
    32044: "ChatGPT Image2 地铁站青春人像",
    32045: "课堂偷亲 青春人像",
    32046: "真人 × 涂鸦影子 双重人格人像",
    32047: "邻家女孩 数字标注风人像",
    32048: "报纸朋克 复古人像",
    32049: "多情绪 胶片人像组图",
    32050: "Y2K朋克摇滚 杂志人像",
    32051: "报纸印花 朋克人像",
    32053: "烧报纸 氛围感人像",
    32054: "眼神叙事 情绪人像",
    32055: "羽毛蕾丝 高定时尚人像",
    32056: "羽毛主题 杂志写真",
    32057: "赛博暗黑 婚纱剑姬写真",
    32058: "若即若离 情绪人像",
    32059: "黑白光影 意境人像",
    32060: "旧杂志叙事 相亲往事人像",
    32061: "陶艺工作室 生活感人像",
    32062: "陶艺少女 恋爱眼神人像",
}

def is_textpost(e):
    t = e.get("title") or ""
    return ("每日一词" in t) or ("AIGC每日一词" in t) or (not (e.get("prompt") or "").strip())

def process(path):
    data = json.load(open(path, encoding="utf-8"))
    bak_ids = {e.get("id") for e in json.load(open(BAK, encoding="utf-8"))}
    real_ids = {e.get("id") for e in data
                if e.get("id") not in bak_ids and not is_textpost(e)}
    n_cat = n_prompt = n_title = 0
    for e in data:
        if e.get("id") not in real_ids:
            continue
        nc = classify(e.get("title"), e.get("prompt"), e.get("author"))
        if nc != (e.get("category") or ""):
            e["category"] = nc; n_cat += 1
        cp = clean(e.get("prompt"))
        if cp != (e.get("prompt") or ""):
            e["prompt"] = cp; n_prompt += 1
        if e.get("id") in BAD_TITLES:
            e["title"] = BAD_TITLES[e["id"]]; n_title += 1
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    return len(real_ids), n_cat, n_prompt, n_title

if __name__ == "__main__":
    for name, p in (("本地", LOCAL_TW), ("部署", DEPLOY_TW)):
        tot, c, pr, ti = process(p)
        print(f"[{name}] 处理真实新增 {tot} 条 | 改分类 {c} | 清内容 {pr} | 重拟标题 {ti} -> {os.path.basename(p)}")
