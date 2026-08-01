import json, os
from collections import Counter

base = r'C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-prompts'
data_path = os.path.join(base, 'data', 'prompts.json')
d = json.load(open(data_path, encoding='utf-8'))

RULES = [
    ('UI与界面', ['ui', 'app', '界面', '终端', '屏幕', '原型', '设计系统', 'ppt', '幻灯片',
                  '浏览器', '网页', '桌面', '仪表盘', 'dashboard', '移动端', '手机', '小程序', '网站', '软件']),
    ('文字Logo', ['logo', '字体', 'typography', '招牌', '艺术字', 'lettering', '排版设计', '书法']),
    ('3D与产品', ['3d', 'c4d', 'blender', '渲染', '产品', '包装', '建模', 'render', 'oc渲染']),
    ('动漫二次元', ['anime', '动漫', '二次元', 'manga', '漫画', '日系', '萌系', '赛璐璐', 'galgame']),
    ('科幻未来', ['赛博朋克', 'cyberpunk', '科幻', '太空', '宇宙', '机械', '机器人', '星际', '未来城市', '废土', '机甲']),
    ('美食料理', ['美食', '食物', '料理', '咖啡', '甜点', '蛋糕', '饮品']),
    ('动物自然', ['猫', '狗', '动物', '植物', '花卉', '花', '鸟', '森林', '宠物', '野生动物', '海洋生物']),
    ('平面设计', ['海报', '广告', '杂志', '报纸', '社交媒体', 'banner', '品牌', 'branding', '传单', '名片', '封面', '排版']),
    ('风景建筑', ['风景', '山水', '建筑', '城市', '室内', '景观', '园林', '街道', '小镇', '天空', '海洋', '雪山', '庭院']),
    ('插画艺术', ['插画', '水彩', '油画', '扁平', '手绘', '治愈', 'illustration', '绘本', '矢量', '噪点', '厚涂']),
    ('摄影纪实', ['摄影', '胶片', '纪实', '电影感', 'cinematic', '镜头', 'photo', '拍立得']),
    ('游戏影视', ['游戏', '影视', '电影', '关卡', '场景', '世界观', 'cg', '游戏原画']),
    ('人像写真', ['人像', '肖像', '自拍', '头像', '写真', 'portrait', '面部', '美女', '帅哥', '古风人物']),
]


def classify(it):
    title = (it.get('title') or '').lower()
    prompt = (it.get('prompt') or '').lower()
    best = None
    best_score = -1
    for cls, words in RULES:
        score = 0
        for w in words:
            wl = w.lower()
            if wl in title:
                score += 3
            elif wl in prompt:
                score += 1
        if score > best_score:
            best_score = score
            best = cls
    return best if best_score > 0 else '其他综合'


cnt = Counter()
for it in d:
    c = classify(it)
    it['category'] = c
    cnt[c] += 1

n = len(d)
json.dump(d, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
stats = [{'category': c, 'count': v, 'pct': round(v / n * 100, 1)}
         for c, v in sorted(cnt.items(), key=lambda x: -x[1])]
json.dump({'total': n, 'categories': stats},
          open(os.path.join(base, 'data', 'categories.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)

d2 = json.load(open(data_path, encoding='utf-8'))
print(f"写回校验: 条目 {len(d2)}, 含 category 字段: {all('category' in x for x in d2)}\n")
print(f"总 {n} 条分类完成:\n")
for s in stats:
    bar = '#' * int(s['pct'] / 1.5)
    print(f"{s['category']:8s}: {s['count']:6d}  ({s['pct']:4.1f}%) {bar}")
