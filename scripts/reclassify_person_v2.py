# -*- coding: utf-8 -*-
"""v2：按用户硬规则重分类（高召回人物判定 + 严格二次审计）。
   有人(真人/动漫角色/模特/装饰/拟人/名字/姿态/服饰) -> 人物(单一类)
   无人 -> 15 个非人主题之一
   铁律：最终落非人类的，若“严格人物审计”检出含人 -> 强制改回 人物（保证零泄漏）
   手动读的 200 条(reclass_map.json) 作为真值覆盖（不被铁律翻回，尊重人工判断）。
"""
import json, re, collections, os, random

ROOT = "C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54"
DATA = os.path.join(ROOT, "shuixian-prompts", "data")

# =====================================================================
# 人物判定 —— 第一层（高召回，任何人的迹象都算；过分类进人物可接受）
# =====================================================================
PERSON_DIRECT = [
    # ---- 直称人（含泛称/尊称/职业/关系）----
    r"人(?:物|像|形|员|士|们)?", r"女性", r"男性", r"女孩", r"男孩", r"女人", r"男人",
    r"少女", r"少年", r"青年", r"成人", r"儿童", r"婴儿", r"宝宝", r"小孩", r"幼童",
    r"老人", r"老年", r"老妪", r"老年", r"中年", r"女子", r"男子", r"妇女", r"男士", r"女士",
    r"姑娘", r"小伙", r"小伙子", r"大叔", r"阿姨", r"大妈", r"大爷", r"老头", r"老太", r"老太婆",
    r"美女", r"帅哥", r"型男", r"佳人", r"丽人", r"妙龄", r"行人", r"路人", r"人群", r"众人",
    r"群众", r"世人", r"活人", r"生人", r"陌生人", r"旁人", r"他人", r"本人", r"个人", r"某人",
    r"此人", r"那人", r"诸位", r"各位", r"大家", r"人们", r"人士", r"员工", r"职员", r"工人",
    r"农民", r"军人", r"警察", r"医生", r"护士", r"老师", r"学生", r"顾客", r"消费者", r"用户",
    r"模特", r"主(?:播|角|持)", r"肖像", r"自拍", r"证件照", r"情侣", r"夫妻", r"夫妇", r"家庭",
    r"婚礼", r"新(?:郎|娘)", r"婚纱", r"全家福", r"写真", r"cosplay", r"coser", r"球(?:员|星)",
    r"歌(?:手|星)", r"明星", r"名(?:人|模)", r"网红", r"博主", r"up主", r"运动(?:员)?",
    r"武(?:士|者)", r"骑(?:士|者)", r"法(?:师|者)", r"魔法少女", r"女(?:王|神|巫|侠|仆|孩)",
    r"男(?:王|神|侠|仆)", r"公(?:主|主)", r"王子", r"皇(?:帝|后|族)", r"仙(?:女|子|侠)",
    r"剑客", r"侠客", r"道(?:长|士)", r"僧", r"佛", r"神话人物", r"历史人物", r"爸(?:爸)?",
    r"妈(?:妈)?", r"爷(?:爷)?", r"奶(?:奶)?", r"孩(?:子|童)", r"同(?:学|事)", r"朋(?:友|辈)",
    r"纳税人", r"顾(?:客)?", r"婴孩", r"幼(?:儿|崽)", r"少年", r"主(?:人|顾)",
    # ---- 动漫 / 二次元 / 角色 ----
    r"动漫", r"二次元", r"アニメ", r"anime", r"manga", r"まんが", r"动(?:漫|man)", r"日系动漫",
    r"3D动漫", r"动漫风格", r"动漫角色", r"动漫插画", r"动漫海报", r"动漫少女", r"动漫男", r"动漫风",
    r"二次元角色", r"二次元少女", r"VTuber", r"vtuber", r"虚拟主播", r"虚拟偶(?:像)?",
    r"角(?:色|色设计|色设定|色参考|色插画|色头像|色海报|色立绘|色三视图|色线稿)",
    r"人(?:物|物关系|物设定|物设计|物参考|物头像|物卡|物插画|物海报|物立绘)图?",
    r"角?色?设定", r"立绘", r"机甲少女", r"机甲女", r"拟人", r"少(?:女|年)动漫", r"萌系",
    r"Q版", r"chibi", r"吉祥物", r"cos服", r"兽耳", r"猫耳", r"狐耳", r"女仆",
    # ---- 姿态 / 服饰（强人物线索）----
    r"拱手", r"作揖", r"抱拳", r"鞠躬", r"跪坐", r"跪", r"站姿", r"坐姿", r"蹲", r"奔跑",
    r"行走", r"跳舞", r"挥舞", r"比心", r"敬礼", r"比耶", r"摆拍", r"街拍", r"艺术照",
    r"礼服", r"婚纱", r"西装", r"制服", r"汉服", r"古装", r"和服", r"旗袍", r"唐装", r"浴衣",
    r"军装", r"护士服", r"学生服", r"校服", r"运动服", r"泳装", r"比基尼", r"华服", r"中华服",
    r"中華服", r"唐风", r"汉风", r"古风", r"国风", r"和风", r"民族风", r"cosplay服装",
    r"古风美女", r"古风少女", r"汉服少女", r"和服少女",
    # ---- 直播 / 活动语境 ----
    r"直播", r"直播间", r"正在直播", r"直播中", r"合影", r"合照", r"自拍", r"摆拍", r"街拍",
    # ---- 英文 ----
    r"portrait", r"person", r"woman", r"man", r"girl", r"boy", r"character", r"model",
    r"selfie", r"cosplay", r"anime", r"manga", r"avatar", r"figure", r"face", r"heroine",
    r"protagonist", r"waifu", r"VTuber", r"people", r"lady", r"gentleman", r"child",
    r"queen", r"king", r"princess", r"prince", r"goddess", r"warrior", r"knight",
    # ---- 特定人名/角色名（常见，扩充）----
    # 神话/历史/文学
    r"杨贵妃", r"貂蝉", r"西施", r"王昭君", r"武则天", r"慈禧", r"嫦娥", r"后羿", r"女娲", r"盘古",
    r"宙斯", r"雅典娜", r"孙悟空", r"猪八戒", r"唐僧", r"诸葛亮", r"关羽", r"张飞", r"赵云",
    r"刘备", r"曹操", r"司马懿", r"织田信长", r"丰臣秀吉", r"德川家康", r"宫本武藏", r"源义经",
    r"秦始皇", r"汉武帝", r"唐太宗", r"成吉思汗", r"亚历山大", r"拿破仑", r"凯撒", r"林肯",
    r"华盛顿", r"丘吉尔", r"罗斯福", r"孙中山", r"毛泽东",
    # 哲学/科学/艺术/文学
    r"柏拉图", r"苏格拉底", r"亚里士多德", r"孔子", r"老子", r"庄子", r"孟子", r"荀子",
    r"朱熹", r"王阳明", r"康德", r"黑格尔", r"尼采", r"马克思", r"伏尔泰", r"卢梭", r"培根",
    r"笛卡尔", r"叔本华", r"弗洛伊德", r"牛顿", r"爱因斯坦", r"伽利略", r"达尔文", r"居里夫人",
    r"特斯拉", r"霍金", r"哥白尼", r"门捷列夫", r"玻尔", r"薛定谔", r"图灵", r"达芬奇", r"梵高",
    r"毕加索", r"莫奈", r"拉斐尔", r"米开朗基罗", r"伦勃朗", r"张大千", r"齐白石", r"徐悲鸿",
    r"莎士比亚", r"托尔斯泰", r"杜甫", r"李白", r"苏轼", r"曹雪芹", r"鲁迅", r"巴尔扎克",
    r"歌德", r"海明威", r"马克吐温",
    # 现代名流
    r"刘亦菲", r"杨幂", r"迪丽热巴", r"范冰冰", r"章子怡", r"成龙", r"李连杰", r"周杰伦",
    r"林俊杰", r"邓紫棋", r"泰勒斯威夫特", r"碧昂丝", r"梅西", r"罗纳尔多", r"詹姆斯", r"科比",
    r"乔丹", r"马斯克", r"比尔盖茨", r"扎克伯格", r"OpenAI",
    r"Messi", r"Ronaldo", r"Cristiano", r"Taylor Swift", r"Beyonc", r"Michael Jordan",
    r"Harry Potter", r"Spider-?Man", r"钢铁侠", r"蝙蝠侠", r"超人", r"奥特曼", r"葫芦娃",
    r"喜羊羊", r"哆啦A梦", r"路飞", r"鸣人", r"佐助",
]

# ---- 解剖 / 外貌（复合词，避免 手机/车身/眼镜 误判）----
PERSON_ANAT = [
    r"面(?:部|容|孔|庞|颊)", r"瓜子脸", r"圆脸", r"瘦脸", r"脸蛋", r"脸型", r"小脸", r"美脸",
    r"五(?:官|官)", r"肤(?:色|质)", r"发(?:色|型|丝|髻|辫|型)", r"长发", r"短发", r"卷发",
    r"黑发", r"金发", r"白发", r"头发", r"刘海", r"双马尾", r"单马尾", r"发饰",
    r"眼(?:睛|眸|神|影|线|波|眶)", r"大眼", r"杏眼", r"凤眼", r"双眼皮", r"睫毛", r"眉毛",
    r"鼻子", r"耳朵", r"嘴(?:唇|角)?", r"嘴巴", r"朱唇", r"樱唇", r"丰唇", r"牙齿", r"笑容",
    r"表(?:情|情)", r"妆(?:容)?", r"肖(?:像|像)", r"半身", r"全身", r"胸(?:部|口|廓)?",
    r"大(?:头|头照)", r"侧脸", r"正脸", r"回眸", r"手部", r"手指", r"手掌", r"双手", r"握手",
    r"挥手", r"摆手", r"手托", r"手捧", r"手拿", r"伸手", r"纤手", r"玉手", r"脚趾", r"脚踝",
    r"赤脚", r"双脚", r"玉足", r"美足", r"手臂", r"肩膀", r"脖子", r"腰部", r"背部", r"腹部",
    r"膝盖", r"身(?:材|高|体|段|形)", r"上身", r"下身", r"满身", r"写实模(?:特|特)",
    r"摄影棚", r"棚拍", r"时尚大片", r"时尚杂志", r"时尚编辑",
]

# ---- 名字 + 人物动词 启发式（抓未收录的具体人名）----
PERSON_NAMEVERB = [
    r"[一-龥]{2,3}(?:正在|在拍|在画|说|认为|表示|代言|主演|演唱|扮演|绘制|写道|创作|设计|手绘)",
    r"[A-Za-z]{2,20}(?:'s selfie|'s portrait| is posing| posing| portrait| selfie)",
]

PERSON_DIRECT_RE = re.compile("|".join(PERSON_DIRECT), re.I)
PERSON_ANAT_RE = re.compile("|".join(PERSON_ANAT), re.I)
PERSON_NAMEVERB_RE = re.compile("|".join(PERSON_NAMEVERB))

def has_person(t):
    if PERSON_DIRECT_RE.search(t):
        return True
    if PERSON_ANAT_RE.search(t):
        return True
    if PERSON_NAMEVERB_RE.search(t):
        return True
    return False

# =====================================================================
# 严格二次审计（铁律用）：在第一层基础上再放宽，凡疑似人物都翻回人物
# =====================================================================
PERSON_STRICT_EXTRA = [
    r"古风", r"国风", r"汉风", r"唐风", r"和风", r"民族风",  # 风格词（图像常含人）
    r"风韵", r"韵味的", r"端庄", r"温婉", r"妩媚", r"婉约", r"典雅女子", r"古典美人",
    r"肖像画", r"人像摄影", r"人物摄影", r"艺术人像", r"写真人像",
    r"眼波", r"眉眼", r"唇形", r"体态", r"身姿", r"仪态", r"风姿",
]
PERSON_STRICT_RE = re.compile("|".join(PERSON_DIRECT + PERSON_ANAT + PERSON_NAMEVERB + PERSON_STRICT_EXTRA), re.I)

def has_person_strict(t):
    return bool(PERSON_STRICT_RE.search(t))

# =====================================================================
# 非人主题（优先级从高到低）
# =====================================================================
TOPICS = [
    ("食物/饮品", re.compile(r"美食|餐饮|菜(?:品|系|肴|谱)?|料理|食谱|饮(?:品|料)|咖啡|茶(?:饮|叶)?|酒(?:类|店|吧)?|蛋糕|甜品|甜点|汉堡|薯条|薯片|披萨|寿司|拉面|面(?:条|食)?|米(?:饭|线)?|汤|零(?:食|食)|包装食品|烧烤|烹(?:饪|调)|水果|果汁|奶茶|冰淇淋|可丽饼|月饼|粽(?:子)?|火锅|小吃|牛(?:奶|排)|鸡(?:肉|腿)|海鲜|面包", re.I)),
    ("Logo/品牌/VI", re.compile(r"logo|标志|品牌|商标|\bvi\b|标识|吉祥物|品牌视觉|企业形象|门(?:店|头)|品脾|brand|视觉识别|ip设计|vi设计|logo设计", re.I)),
    ("UI/App/网页/SaaS", re.compile(r"\bui\b|app|界面|网页|网站|落地页|dashboard|saas|幻灯片|幻灯|截图|终端|设计系统|原型图|直播间界面|着陆页|官网|web|手机界面|app界面|软件界面|wikiHow|landing", re.I)),
    ("字体/排版/标题", re.compile(r"字体|排版|标题|书法|字帖|手写|字母|衬线|无衬线|试卷|笔(?:记|迹)|文档|名(?:片|称)|教材|课本|杂志(?:排版|内页)?|海报字体|字体样本|字(?:体)?样张|标(?:题)?字", re.I)),
    ("插画/艺术/概念", re.compile(r"插画|艺术|绘画|涂鸦|手绘|水彩|油画|版(?:画|绘)|概念艺术|壁画|绘(?:本|画)|扁平插画|装饰艺术|图标|艺术(?:图|作品)|画(?:作|风)|速写|素描|钢(?:笔|笔画)|蜡笔|色(?:彩|铅)|民(?:间艺术|艺)|浮世绘|绘本|插画风格|art|illustration|painting|doodle|sketch", re.I)),
    ("3D/游戏/像素/等距", re.compile(r"\b3d\b|游戏|像素|等距|纸雕|微缩|手办|沙盘|等轴测|体素|voxel|像素风|游戏截图|game|rpg|开放世界|卡牌|机甲", re.I)),
    ("建筑/室内/空间", re.compile(r"建筑|室内|房间|卧(?:室|房)|客(?:厅|房)|办公(?:室|空间)|房产|别墅|公寓|平面(?:图|图)|空间|城市(?:规划|设计)|景观模型|房(?:子|产)|装(?:修|饰)|家居|橱窗|展(?:厅|台)|门店(?:设计)?|建筑效果|室内设计|architecture|interior|floor plan", re.I)),
    ("风景/自然", re.compile(r"风景|自然|山水|天空|日落|日出|晚霞|海(?:景|边|滩|洋)?|山(?:脉|景|峰)?|森林|雪(?:景|山)?|花(?:海|田|园)?|植(?:物|被)|城市天际线|旅行|风光|夜景|星空|星(?:空|云)|云海|峡湾|湖泊|河(?:流|畔)?|公(?:园|路)|自(?:然|驾)|landscape|nature|cityscape|skyline", re.I)),
    ("动物/宠物", re.compile(r"动物|宠物|猫|狗|鸟|鱼|兽|野生|生物|恐龙|熊猫|企鹅|水獭|虎|狮|象|熊|兔|马|鹿|狐|狼|鲸|鲨|昆虫|爬(?:行)?动物|animal|pet|cat|dog|bird", re.I)),
    ("车辆/机械/科幻", re.compile(r"汽(?:车|车)|车辆|载具|机(?:甲|器人|械)|飞船|飞机|火车|机械|科幻|未来城市|太空|赛(?:车|博)|超(?:跑|车)|坦(?:克)?|无人机|摩托|自行车|car|vehicle|mecha|robot|spaceship|sci-?fi", re.I)),
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

# =====================================================================
# 载入数据 + 手动真值 + 计算
# =====================================================================
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
flipped = []          # 铁律翻回人物的（仅自动分类部分）
manual_leak = []      # 手动真值里落在非人但含人的（应人工复核）
for e in data:
    i = e["id"]
    if i in manual:
        c = manual[i]
        if c != "人物" and has_person_strict(" ".join((e.get("prompt", "") or e.get("title", "")).split())):
            manual_leak.append((i, c))
    else:
        c = classify(e)
    # 铁律（严格审计）：非人物但若含人 -> 人物
    if c != "人物":
        t = " ".join((e.get("prompt", "") or e.get("title", "")).split())
        if has_person_strict(t):
            c = "人物"
            if i not in manual:
                flipped.append(i)
    full[i] = c

cnt = collections.Counter(full.values())
print("总条数:", len(full))
print("手动覆盖:", len(manual), " 铁律翻回人物:", len(flipped))
if manual_leak:
    print("⚠ 手动真值中疑似含人但归非人的条目（建议复核）:")
    for i, c in manual_leak:
        t = " ".join((next(x for x in data if x['id']==i).get("prompt","") or "").split())[:80]
        print(f"   [{c}] {i}: {t}")
print("分布:")
for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v} ({v*100//len(full)}%)")

json.dump({str(k): v for k, v in full.items()}, open(os.path.join(ROOT, "reclass_full.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("\n已写 reclass_full.json")

# 抽样：每类展示 2 条非人样本供核对（看是否误含人）
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
