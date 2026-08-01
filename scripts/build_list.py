# -*- coding: utf-8 -*-
"""生成部署版轻量 list 数据文件（方法①）。

读取 shuixian-deploy/data 下的完整数据（prompts.part1/2/3.json + twitter 文件），
每条只保留画廊/分类/搜索需要的字段，去掉完整 prompt 正文，并预计算 themes/styles/person，
使首屏只需下载约 3MB（而非 25MB）。

输出：
  data/list.part1.json / list.part2.json / list.part3.json   （主库轻量版，与 prompts.partN 对应）
  data/list-twitter.json
完整 prompts.part*.json / prompts-twitter*.json 保留不动（供灯箱/复制按需加载）。
"""
import json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shuixian-deploy", "data")
ROOT = os.path.abspath(ROOT)

THEMES = ["人像","UI","3D","插画","摄影","海报","漫画","字体"]
STYLES = ["写实","赛博","水彩","胶片","霓虹","极简","复古","日系"]
THEME_RULES = {
    "人像": r"人像|头像|少女|女性|女孩|男生|男孩|男人|女人|人物|portrait|face|selfie",
    "UI":   r"UI|界面|网页|app|dashboard|图标|icon|saas",
    "3D":   r"3D|三维|等距|isometric|blender|c4d|产品|电商|包装",
    "插画": r"插画|illustration|手绘|涂鸦|painting|水彩|油画",
    "摄影": r"摄影|photography|胶片|写实|photo|街拍|电影感",
    "海报": r"海报|poster|广告|banner|社媒|电商",
    "漫画": r"漫画|manga|anime|分镜|storyboard|二次元",
    "字体": r"字体|typography|标题|文字|logo|品牌|vi",
}
STYLE_RULES = {
    "写实": r"写实|photorealistic|realistic|照片|摄影|电影感",
    "赛博": r"赛博|cyberpunk",
    "水彩": r"水彩|watercolor",
    "胶片": r"胶片|film",
    "霓虹": r"霓虹|neon",
    "极简": r"极简|minimalist|简约|clean",
    "复古": r"复古|vintage|怀旧|oldschool",
    "日系": r"日系|日式|japanese|anime|宫崎骏",
}
THEME_RE = {k: re.compile(v, re.I) for k, v in THEME_RULES.items()}
STYLE_RE = {k: re.compile(v, re.I) for k, v in STYLE_RULES.items()}

def slim(e):
    text = ((e.get("title") or "") + " " + (e.get("prompt") or "")).lower()
    themes = [t for t in THEMES if THEME_RE[t].search(text)]
    styles = [s for s in STYLES if STYLE_RE[s].search(text)]
    cat = e.get("category") or ""
    person = ("人像" in text) or ("人像" in cat) or ("头像" in cat)
    out = {
        "id": e.get("id"),
        "title": e.get("title") or "",
        "category": cat,
        "image": e.get("image") or "",
        "images": e.get("images") or [],
        "likes": e.get("likes") or 0,
        "tweet": e.get("tweet"),
        "themes": themes,
        "styles": styles,
        "person": person,
    }
    return out

def dump(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def main():
    # 主库：沿用 prompts.part1/2/3 的分块，输出对应 list.partN
    total = 0
    for i in (1, 2, 3):
        src = os.path.join(ROOT, f"prompts.part{i}.json")
        dst = os.path.join(ROOT, f"list.part{i}.json")
        data = json.load(open(src, encoding="utf-8"))
        slimmed = [slim(e) for e in data]
        dump(dst, slimmed)
        total += len(slimmed)
        print(f"list.part{i}.json: {len(slimmed)} 条 -> {dst}")
    # twitter 系列（cat1/cat2 旧拆分已合并进 prompts-twitter.json 并删除，不再生成）
    for src_name, dst_name in [
        ("prompts-twitter.json", "list-twitter.json"),
    ]:
        src = os.path.join(ROOT, src_name)
        if not os.path.exists(src):
            continue
        dst = os.path.join(ROOT, dst_name)
        data = json.load(open(src, encoding="utf-8"))
        slimmed = [slim(e) for e in data]
        dump(dst, slimmed)
        total += len(slimmed)
        print(f"{dst_name}: {len(slimmed)} 条 -> {dst}")
    print("合计轻量条目:", total)

if __name__ == "__main__":
    main()
