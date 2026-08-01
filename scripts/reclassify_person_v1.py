# -*- coding: utf-8 -*-
"""按用户硬规则重分类：
   有人(真人/动漫角色/模特/装饰/拟人) -> 人物(单一类)
   无人 -> 15 个非人主题之一
   铁律：最终落非人类的，若检出含人 -> 强制改回 人物
   手动读的 200 条(reclass_map.json) 作为真值覆盖。
"""
import json, re, collections, os

ROOT = "C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54"
DATA = os.path.join(ROOT, "shuixian-prompts", "data")

# ---------- 人物判定（高召回：任何人的迹象都算） ----------
PERSON = [
    # 直称人
    r"人(?:物|像|物)?", r"女性", r"男性", r"女孩", r"男孩", r"女人", r"男人", r"少女", r"少年",
    r"青年", r"成人", r"儿童", r"婴儿", r"宝宝", r"小孩", r"宝宝", r"幼童", r"老(?:人|年|妪)",
    r"模特", r"主(?:播|角|持)", r"肖像", r"自拍", r"证件照", r"情侣", r"夫妻", r"夫妇", r"家庭",
    r"婚礼", r"新(?:郎|娘)", r"婚纱", r"全家福", r"写真", r"cosplay", r"coser",
    r"球(?:员|星)", r"歌(?:手|星)", r"明星", r"名(?:人|模)", r"网红", r"博主", r"up主",
    r"运动(?:员|员)", r"武(?:士|者)", r"骑(?:士|者)", r"法(?:师|者)", r"魔法少女", r"女(?:王|神|巫|侠|仆)",
    r"男(?:王|神|侠|仆)", r"公(?:主|主)", r"王子", r"皇(?:帝|后|族)", r"仙(?:女|子|侠)", r"剑客",
    r"侠客", r"道(?:长|士)", r"僧", r"佛", r"神话人物", r"历史(?:人物|人物)",
    r"妈(?:妈|咪)", r"爸(?:爸)", r"爷(?:爷)", r"奶(?:奶)", r"孩(?:子|童)", r"同(?:学|事|事)", r"朋(?:友|辈)",
    r"纳税人", r"消费(?:者|者)", r"用(?:户|人)", r"顾(?:客|客)",
    # 动漫 / 二次元 / 角色
    r"动漫", r"二次元", r"アニメ", r"anime", r"manga", r"まんが", r"动(?:漫|man)", r"日系动漫",
    r"3D动漫", r"动漫风格", r"动漫角色", r"动漫插画", r"动漫海报", r"动漫少女", r"动漫男", r"动漫风",
    r"二次元角色", r"二次元少女", r"VTuber", r"vtuber", r"虚拟主播", r"虚拟偶(?:像|像)",
    r"角(?:色|色设计|色设定|色参考|色插画|色头像|色海报|色立绘|色三视图|色线稿)",
    r"人(?:物|物关系|物设定|物设计|物参考|物头像|物卡|物插画|物海报|物立绘)图?",
    r"角?色?设定", r"立绘", r"机甲少女", r"机甲女", r"拟人",
    r"少(?:女|年)动漫", r"萌系", r"Q版", r"chibi", r"吉祥物(?:人)?",  # 拟人吉祥物算人
    # 解剖/外貌（在描绘语境下视为人）
    r"面(?:部|容|孔)", r"五(?:官|官)", r"肤(?:色|质)", r"发(?:色|型|丝|髻|辫)", r"眼(?:睛|眸|神)",
    r"嘴(?:唇)?", r"身(?:材|材比例|高|体)", r"表(?:情|情)", r"妆(?:容|容)", r"肖(?:像|像)",
    r"半身", r"全身", r"胸(?:部|像)?", r"大(?:头|头照)", r"侧脸", r"正脸", r"回眸", r"自拍",
    r"写实模(?:特|特)", r"摄影棚", r"棚拍", r"时尚大片", r"时尚杂志", r"时尚编辑",
    # 英文
    r"portrait", r"person", r"woman", r"man", r"girl", r"boy", r"character", r"model",
    r"selfie", r"cosplay", r"anime", r"manga", r"avatar", r"figure", r"face", r"heroine",
    r"protagonist", r"waifu", r"VTuber",
    # 特定人名/角色名（常见）
    r"杨贵妃", r"貂蝉", r"孙悟空", r"诸葛亮", r"织田信长", r"朱元璋", r"OpenAI",  # OpenAI 常作为人物/品牌出现，保守算人语境
    r"梅西", r"罗纳尔多", r"Ronaldo", r"Messi", r"Cristiano",
]
PERSON_RE = re.compile("|".join(PERSON), re.I)

# 仅在“描绘图像”语境下才算人的解剖词（避免产品手、食物特写误判）
ANAT_CTX = re.compile(r"模特|角色|摄影|肖像|写真|自拍|人像|人物|动漫|二次元|插画|立绘|主角|半身|全身|时尚|证件|婚|情侣|家庭|女孩|男孩|女性|男性|少女|少年|女人|男人|cosplay|anime|character|portrait|person|woman|man|girl|boy|model", re.I)

def has_person(t):
    if PERSON_RE.search(t):
        return True
    # 解剖词需配合人物语境
    for kw in [r"面(?:部|容|孔)", r"五(?:官|官)", r"肤(?:色|质)", r"发(?:色|型|丝)", r"眼(?:睛|眸)", r"身(?:材|高)", r"妆", r"肖?", r"半身", r"全身", r"胸", r"侧脸", r"回眸"]:
        if re.search(kw, t) and ANAT_CTX.search(t):
            return True
    return False

# ---------- 非人主题（优先级从高到低） ----------
TOPICS = [
    ("食物/饮品", re.compile(r"美食|餐饮|菜(?:品|系|肴|谱)?|料理|食谱|饮(?:品|料)|咖啡|茶(?:饮|叶)?|酒(?:类|店|吧)?|蛋糕|甜品|甜点|汉堡|薯条|薯片|披萨|寿司|拉面|面(?:条|食)?|米(?:饭|线)?|汤|零(?:食|食)|包装食品|烧烤|烧烤|烹(?:饪|调)|水果|果汁|奶茶|冰淇淋|可丽饼|月饼|粽(?:子)?|火锅|小吃|牛(?:奶|排)|鸡(?:肉|腿)|海鲜|面包", re.I)),
    ("Logo/品牌/VI", re.compile(r"logo|标志|品牌|商标|\bvi\b|标识|吉祥物|品牌视觉|企业形象|门(?:店|头)|品脾|brand|视觉识别|ip设计|vi设计|logo设计", re.I)),
    ("UI/App/网页/SaaS", re.compile(r"\bui\b|app|界面|网页|网站|落地页|dashboard|saas|幻灯片|幻灯|截图|终端|设计系统|原型图|直播间界面|着陆页|官网|web|手机界面|app界面|软件界面|wikiHow|landing", re.I)),
    ("字体/排版/标题", re.compile(r"字体|排版|标题|书法|字帖|手写|字母|衬线|无衬线|试卷|笔(?:记|迹)|文档|名(?:片|称)|教材|课本|杂志(?:排版|内页)?|海报字体|字体样本|字(?:体)?样张|标(?:题)?字", re.I)),
    ("插画/艺术/概念", re.compile(r"插画|艺术|绘画|涂鸦|手绘|水彩|油画|版(?:画|绘)|概念艺术|壁画|绘(?:本|画)|扁平插画|装饰艺术|图标|艺术(?:图|作品)|画(?:作|风)|速写|素描|钢(?:笔|笔画)|蜡笔|色(?:彩|铅)|民(?:间艺术|艺)|浮世绘|绘本|插画风格|art|illustration|painting|doodle|sketch", re.I)),
    ("3D/游戏/像素/等距", re.compile(r"\b3d\b|游戏|像素|等距|纸雕|微缩|手办|沙盘|等轴测|体素|voxel|像素风|游戏截图|game|rpg|开放世界|卡牌|机甲(?![少少女女])", re.I)),
    ("建筑/室内/空间", re.compile(r"建筑|室内|房间|卧(?:室|房)|客(?:厅|房)|办公(?:室|空间)|房产|别墅|公寓|平面(?:图|图)|空间|城市(?:规划|设计)|景观模型|房(?:子|产)|装(?:修|饰)|家居|橱窗|展(?:厅|台)|门店(?:设计)?|建筑效果|室内设计|architecture|interior|floor plan", re.I)),
    ("风景/自然", re.compile(r"风景|自然|山水|天空|日落|日出|晚霞|海(?:景|边|滩|洋)?|山(?:脉|景|峰)?|森林|雪(?:景|山)?|花(?:海|田|园)?|植(?:物|被)|城市天际线|旅行|风光|夜景|星空|星(?:空|云)|云海|峡湾|湖泊|河(?:流|畔)?|公(?:园|路)|自(?:然|驾)|landscape|nature|cityscape|skyline", re.I)),
    ("动物/宠物", re.compile(r"动物|宠物|猫|狗|鸟|鱼|兽|野生|生物|恐龙|熊猫|企鹅|水獭|虎|狮|象|熊|兔|马|鹿|狐|狼|鲸|鲨|昆虫|爬(?:行)?动物| Creature|animal|pet|cat|dog|bird", re.I)),
    ("车辆/机械/科幻", re.compile(r"汽(?:车|车)|车辆|载具|机(?:甲|器人|械)|飞船|飞机|火车|机械|科幻|未来城市|太空|太空|赛(?:车|博)|超(?:跑|车)|坦(?:克|克)|无人机|摩托|自行车|car|vehicle|mecha|robot|spaceship|sci-?fi", re.I)),
    ("漫画/分镜/故事板", re.compile(r"漫画|分镜|故事板|漫画页面|分格|漫画风|comic|manga page|storyboard|四格", re.I)),
    ("信息图/教育图解", re.compile(r"信息图|教育|图解|科普|地图|数据可视化|时间线|思维导图|教程|课件|医学|科(?:普|学)|知识|图鉴|拆解|示意|图表|infographic|diagram|map|courseware|教科书", re.I)),
    ("抽象/纹理/背景", re.compile(r"抽象|纹理|图案|背景|渐变|壁纸|几何|流体|噪点|纯色|极简(?:抽象|纹理)|色块|abstract|texture|pattern|wallpaper|gradient", re.I)),
    ("海报/广告/社媒", re.compile(r"海报|广告|社媒|banner|传单|缩略图|宣传|营销|促销|封面|活动|电影海报|联名|招贴|poster|ad|social|thumbnail|cover|flyer", re.I)),
]

def topic_class(t):
    for name, rx in TOPICS:
        if rx.search(t):
            return name
    return "其他/未归类"

def classify(e):
    t = e.get("prompt", "") or e.get("title", "")
    t = " ".join(t.split())
    if has_person(t):
        return "人物"
    return topic_class(t)

# ---------- 载入数据 + 手动真值 + 计算 ----------
def load_all():
    out = []
    for fn in ("prompts.json", "prompts-twitter.json"):
        a = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
        for e in a:
            out.append(e)
    return out

data = load_all()
manual = {int(k): v for k, v in json.load(open(os.path.join(ROOT, "reclass_map.json"), encoding="utf-8")).items()}

full = {}
flipped = []  # 铁律校验翻回人物的
for e in data:
    i = e["id"]
    if i in manual:
        c = manual[i]
    else:
        c = classify(e)
    # 铁律：非人类但若含人 -> 人物
    if c != "人物":
        t = " ".join((e.get("prompt", "") or e.get("title", "")).split())
        if has_person(t):
            c = "人物"
            if i not in manual:
                flipped.append(i)
    full[i] = c

# 统计
cnt = collections.Counter(full.values())
print("总条数:", len(full))
print("手动覆盖:", len(manual), " 铁律翻回人物:", len(flipped))
print("分布:")
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v} ({v*100//len(full)}%)")

# 保存完整映射（int id -> class）
json.dump({str(k): v for k, v in full.items()}, open(os.path.join(ROOT, "reclass_full.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("\n已写 reclass_full.json")

# 抽样：每类展示 2 条非人样本供核对（看是否误判）
import random
random.seed(3)
byclass = collections.defaultdict(list)
for e in data:
    byclass[full[e["id"]]].append(e)
print("\n=== 非人类抽样（每类2条，核对是否误含人）===")
for cls in ["Logo/品牌/VI","海报/广告/社媒","产品/电商/包装","食物/饮品","UI/App/网页/SaaS","字体/排版/标题","插画/艺术/概念","3D/游戏/像素/等距","建筑/室内/空间","风景/自然","动物/宠物","车辆/机械/科幻","漫画/分镜/故事板","信息图/教育图解","抽象/纹理/背景","其他/未归类"]:
    samp = random.sample(byclass[cls], min(2, len(byclass[cls])))
    for e in samp:
        t = " ".join((e.get("prompt","") or e.get("title","")).split())[:90]
        print(f"  [{cls}] {e['id']}: {t}")
PY = None
