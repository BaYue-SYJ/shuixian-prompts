# -*- coding: utf-8 -*-
"""把 raw 截图拼成「线上 | 本地」对照图，并在差异处画红框 + 编号。"""
import io
import os
import json
from PIL import Image, ImageDraw, ImageFont

OUT = r"C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\reports\20261028-compare"
RAW = os.path.join(OUT, "raw")
PAIR = os.path.join(OUT, "pairs")
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTB = r"C:\Windows\Fonts\msyhbd.ttc"
RED = (214, 40, 40)
LABEL_BG = (22, 48, 47)
LABEL_FG = (255, 255, 255)

MARK_W = 680          # 单侧最大宽
MARK_H = 880          # 单侧最大高
GAP = 18
PAD = 22
BAR = 38

TITLES = {
    "01-hero-cta": ("① 首页 CTA：只剩「开始逛画廊」", "浏览全部分类按钮已删除"),
    "02-hero-stats": ("② 首页统计：6,011 / 13 大分类", "线上 5,452 / 12 大分类"),
    "03-hero-lead": ("③ 首页导语数字", "条数与分类数同步更新"),
    "04-footer": ("④ 页脚「浏览」栏：全部分类 / 搜索 已删", "线上有 4 个链接，本地 2 个"),
    "05-rail": ("⑤ 画廊左栏：新增「多图」「New欧美」", "线上只有 12 大类"),
    "06-card": ("⑥ 卡片左下角「多图 · N」角标", "线上没有角标（本地取自多图分类）"),
    "07-detail": ("⑦ 详情页：动作条/备注删除 + 正文不再撑高", "线上右列被长提示词拉到 2 倍高"),
    "08-categories": ("⑧ 分类页已下线", "线上 200，本地 404"),
}

CIRCLED = "①②③④⑤⑥⑦⑧⑨"


def font(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz)


def load(p):
    return Image.open(p).convert("RGB")


def main():
    os.makedirs(PAIR, exist_ok=True)
    meta = json.load(io.open(os.path.join(OUT, "rects.json"), encoding="utf-8"))
    index = []

    for item_id, (title, sub) in TITLES.items():
        sides = {}
        for side in ("live", "local"):
            info = meta.get(side, {}).get(item_id)
            if not info or "file" not in info:
                continue
            sides[side] = (load(os.path.join(OUT, info["file"])), info)
        if len(sides) < 2:
            print("skip", item_id, list(sides))
            continue

        # 各自缩放：只缩小不放大（截图本身已是 2x），保证文字清晰
        sized = {}
        for k, v in sides.items():
            img = v[0]
            sc = min(1.0, MARK_W / img.width, MARK_H / img.height)
            sized[k] = (img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.LANCZOS), v[1], sc)
        wl, hl = sized["live"][0].size
        wr, hr = sized["local"][0].size
        body_h = max(hl, hr)

        W = PAD * 2 + wl + GAP + wr
        H = PAD + BAR + body_h + PAD
        canvas = Image.new("RGB", (W, H), (247, 246, 243))
        d = ImageDraw.Draw(canvas)

        for i, (side, label) in enumerate((("live", "线上 prompt.qqsrc.com  ·  ?v=17"),
                                          ("local", "本地 127.0.0.1:8140  ·  ?v=27"))):
            x = PAD if i == 0 else PAD + wl + GAP
            img, info, sc = sized[side]
            # 标签条
            d.rectangle([x, PAD, x + img.width, PAD + BAR], fill=LABEL_BG)
            d.text((x + 12, PAD + 9), label, font=font(17, True), fill=LABEL_FG)
            canvas.paste(img, (x, PAD + BAR))
            # 红框 + 编号
            # 截图是 deviceScaleFactor=2，元素坐标是 CSS px，画框要乘 2
            K = 2
            for k, m in enumerate(info.get("marks", [])[:9]):
                mx = x + m["x"] * sc * K
                my = PAD + BAR + m["y"] * sc * K
                mw = max(8, m["w"] * sc * K)
                mh = max(8, m["h"] * sc * K)
                d.rectangle([mx - 2, my - 2, mx + mw + 2, my + mh + 2], outline=RED, width=3)
                # 编号放到框左外侧，避免压住框里的文字
                bx, by = (mx - 22 if mx - 22 > 8 else mx + 22), my + 12
                r = 14
                d.ellipse([bx - r, by - r, bx + r, by + r], fill=RED)
                ch = CIRCLED[k] if k < len(CIRCLED) else str(k + 1)
                f = font(19, True)
                tw = d.textlength(ch, font=f)
                d.text((bx - tw / 2, by - 11), ch, font=f, fill=(255, 255, 255))

        out = os.path.join(PAIR, item_id + ".png")
        canvas.save(out, optimize=True)
        index.append({"id": item_id, "file": "pairs/" + item_id + ".png", "title": title, "sub": sub,
                      "size": canvas.size})
        print("pair", item_id, canvas.size)

    json.dump(index, io.open(os.path.join(OUT, "pairs.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
