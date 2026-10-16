# 临时：用 Pillow 给截图加红框编号 + 通俗图注
import json, os
from PIL import Image, ImageDraw, ImageFont

TOOLS = 'C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54/shuixian-unified-0920/tools'
_data_path = os.path.join(TOOLS, '_shot_fixes.json')
data = json.load(open(_data_path)) if os.path.exists(_data_path) else None

# 找一个能渲染中文的字体
FONT = None
for p in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf', 'C:/Windows/Fonts/msyhbd.ttc']:
    if os.path.exists(p):
        FONT = p; break
if not FONT:
    FONT = 'C:/Windows/Fonts/arial.ttf'

f_badge = ImageFont.truetype(FONT, 26, index=0)
f_legend = ImageFont.truetype(FONT, 22, index=0)

RED = (229, 52, 52, 255)

def clamp(v, lo, hi):
    v = int(v); lo = int(lo); hi = int(hi)
    return max(lo, min(hi, v))

def annotate(shot, boxes, legend, out, legend_pos='bottom'):
    # boxes: [(num, x, y, w, h), ...]  legend_pos: 'bottom' | 'top'
    img = Image.open(shot).convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for num, x, y, w, h in boxes:
        x1, y1 = clamp(x, 2, W-2), clamp(y, 2, H-2)
        x2, y2 = clamp(x+w, 2, W-2), clamp(y+h, 2, H-2)
        od.rectangle([x1, y1, x2, y2], outline=RED, width=4)
        r = 17
        od.ellipse([x1, y1-r, x1+2*r, y1+r], fill=RED)
    img = Image.alpha_composite(img, ov).convert('RGB')
    d = ImageDraw.Draw(img)
    # 编号文字（白）
    for num, x, y, w, h in boxes:
        x1 = clamp(x, 2, W-2); y1 = clamp(y, 2, H-2)
        d.text((x1+5, y1-15), str(num), fill=(255, 255, 255), font=f_badge)
    # 图注条（bottom / top / append）
    lh = 32
    bar_h = 16 + lh*len(legend)
    if legend_pos == 'append':
        canvas = Image.new('RGB', (W, H + bar_h), (18, 18, 18))
        canvas.paste(img, (0, 0))
        img = canvas; d = ImageDraw.Draw(img); by = H
    else:
        by = H - bar_h if legend_pos == 'bottom' else 0
        d.rectangle([0, by, W, by+bar_h], fill=(18, 18, 18))
    ty = by + 8
    for num, txt in legend:
        d.ellipse([14, ty+2, 14+22, ty+24], fill=(229, 52, 52))
        d.text((20, ty+2), str(num), fill=(255, 255, 255), font=f_badge)
        d.text((46, ty+2), txt, fill=(255, 255, 255), font=f_legend)
        ty += lh
    img.save(out)
    print('saved', out, img.size)

# ---------- 首页：Issue 1 ----------
if data:
    z = data['index']['zaCard']
# 把「杂项」文字框扩成卡片范围
zx, zy, zw, zh = z['x']-34, z['y']-22, z['w']+68, z['h']+52
annotate(
    os.path.join(TOOLS, '_shot_index.png'),
    [(1, zx, zy, zw, zh)],
    [(1, '首页「挑一个主题」：原来的「其他/未归类」改成了「杂项」，更清爽')],
    os.path.join(TOOLS, '_annot_index.png'),
)

# ---------- 画廊：Issue 2/3/4 ----------
g = data['gallery']
sortSel = g['sortSel']; facetOn = g['facetOn']; grid = g['grid']
# grid 框裁到可视区域
gx, gy, gw, gh = grid['x'], grid['y'], grid['w'], min(grid['h'], 1080-grid['y'])
def t(d): return (d['x'], d['y'], d['w'], d['h'])
annotate(
    os.path.join(TOOLS, '_shot_gallery.png'),
    [(2, *t(sortSel)), (3, *t(facetOn)), (4, gx, gy, gw, gh)],
    [
        (2, '画廊默认排序：随机（下拉框显示「随机」）'),
        (3, '左侧筛选：每组只选一个，选新的自动取消旧的（高亮项）'),
        (4, '卡片均分 4 列，点「显示更多」新卡会横向铺满每一列'),
    ],
    os.path.join(TOOLS, '_annot_gallery.png'),
)

# ---------- 灯箱：v16 两项交互（一并列入说明）----------
lb = json.load(open(os.path.join(TOOLS, '_shot_lb.json')))
def tlb(d): return (d['x'], d['y'], d['w'], d['h'])
annotate(
    os.path.join(TOOLS, '_shot_lb.png'),
    [(5, *tlb(lb['dice'])), (6, *tlb(lb['prev'])), (6, *tlb(lb['next'])), (6, *tlb(lb['count']))],
    [
        (5, '灯箱打开后，右下角 🎲 骰子也能点（不再被遮罩盖住）；灯箱内另有一枚「换一个 🎲」'),
        (6, '左右大箭头 + 底部位置计数，上一页 / 下一页看得清、点得到'),
    ],
    os.path.join(TOOLS, '_annot_lb.png'),
    legend_pos='append',
)
