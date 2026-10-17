# -*- coding: utf-8 -*-
"""[常备工具] 给现代版各页面注入 data-i18n / data-i18n-placeholder / data-i18n-title 标记。
按「元素内文 = 字典中文值」精确匹配，避免手改上百处出错。可重复执行（幂等）。"""
import os, re, glob

import os as _os
WS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))   # 项目根（tools/ 的上一层）

# ---------- key -> 中文原文（纯文本 / 含少量标记，必须与 HTML 中一致） ----------
P = [
    # 导航 / 通用
    ("nav_home", "首页"), ("nav_gallery", "画廊"), ("nav_categories", "分类"),
    ("nav_search", "搜索"), ("nav_favorites", "收藏"), ("nav_about", "关于"), ("nav_submit", "投稿"),
    ("brand_sub", "Prompt Garden · 提示词花园"),
    # 首页
    ("idx_h1", '把灵感种进<span class="hl">水仙</span>的<br class="hide-mobile">AI 提示词花园'),
    ("idx_cta_gallery", "开始逛画廊"), ("idx_cta_cats", "浏览全部分类"),
    ("idx_stat_prompts", "精选提示词"), ("idx_stat_majors", "大分类"), ("idx_stat_subs", "小分类"),
    ("idx_qr", "扫码关注公众号"),
    ("idx_cats_h2", "挑一个主题，慢慢逛"),
    ("idx_cats_p", "点开任意一栏，进入对应画廊；每一类都按风格聚合了上百条提示词。"),
    ("idx_more_cats", "查看分类总览"),
    ("idx_pick_eyebrow", "Editor's Pick"), ("idx_pick_h2", "每日精选"),
    ("idx_pick_p", "从各路主题里随机捞了几条，点开看详情；不喜欢这波，点「换一批」。"),
    ("idx_shuffle", "换一批"),
    ("idx_cta1_h3", "有好的提示词？投给我们"),
    ("idx_cta1_p", "你的作品会出现在水仙的花园里，被更多人看到、使用、喜欢。"),
    ("idx_cta1_btn", "立即投稿"),
    ("idx_cta2_h3", "喜欢这个花园？"),
    ("idx_cta2_p", "请作者喝杯咖啡，支持水仙持续更新更多精选提示词。"),
    ("idx_cta2_btn", "去赞赏"),
    # 画廊
    ("gal_eyebrow", "Gallery"), ("gal_h1", "提示词画廊"),
    ("gal_sub", "按大类、小类筛选，或用关键词搜索（支持拼音首字母，如 <b>sbpk</b> → 赛博朋克）；点卡片看完整提示词，心仪的收进合集。"),
    ("gal_all_cats", "全部分类"), ("gal_clear", "清除筛选"),
    ("gal_sort_latest", "最新"), ("gal_sort_hot", "最热"), ("gal_sort_random", "随机"),
    ("gal_more", "显示更多"),
    # 分类
    ("cat_eyebrow", "All Categories"), ("cat_h1", "分类总览"),
    # 搜索
    ("se_eyebrow", "Search"), ("se_h1", "搜你喜欢的那一句"), ("se_btn", "搜索"),
    ("se_recent", "最近搜索"), ("se_hot", "大家都在搜"), ("se_tags", "按标签逛"), ("se_none", "暂无"),
    ("se_sort_rel", "相关度"), ("se_empty", "没有匹配的提示词，换个关键词试试。"),
    # 详情
    ("de_back", "← 返回画廊"), ("de_related", "同类推荐"), ("de_more", "查看更多"),
    ("tip_detail_page", "提示：本页为灯箱详情的页面版；在画廊里点卡片可直接唤起全屏灯箱。"),
    # 关于
    ("ab_eyebrow", "About"), ("ab_h1", "关于水仙的提示词花园"),
    ("ab_sub", "一个慢慢长起来的中文 AI 图像提示词合集"),
    ("ab_lead", "「水仙的AI提示词」是一个持续收集、整理的中文 AI 图像生成提示词花园。我们把散落在各处的好句子按主题分门别类，让想出图的人能更快找到合适的那一句话。"),
    ("ab_h2_what", "我们做了什么"),
    ("ab_p_what", "提示词是和 AI 绘画模型沟通的语言。一句好的提示词，往往决定了出图的质量和风格。我们从大量实践里筛选出表达清晰、可复用、风格鲜明的提示词，并为每条标注了分类与预览图，方便你按场景检索。"),
    ("ab_li1", "<b>按主题聚合</b>：人物写真、动漫二次元、海报广告、插画艺术、产品电商、游戏、建筑空间、车辆机械 3D、随手拍、晓兰 等 12 大类。"),
    ("ab_li2", "<b>可直接复制</b>：点开任意卡片即可查看完整提示词，一键复制使用。"),
    ("ab_li3", "<b>本地收藏</b>：支持多画板收藏，无需登录，存在你自己的浏览器里。"),
    ("ab_h2_rights", "图片与版权"),
    ("ab_p_rights", "所有预览图托管于 Cloudflare R2 公共存储，仅用于提示词效果展示。提示词与图片版权归原作者所有，本站点仅作整理与展示，<b>仅供学习交流，请勿用于商业用途</b>。"),
    ("ab_h2_contact", "联系我们"),
    ("ab_p_contact", "想投稿好提示词、纠错、或者聊聊想法？欢迎通过以下方式找到我们："),
    ("ab_li_c1", '微信公众号：<b>水仙的AI提示词</b>（首页扫码关注）'),
    ("ab_li_c2", '投稿入口：<a href="submit.html">立即投稿</a>'),
    ("ab_li_c3", '支持作者：<a href="sponsor.html">赞赏一下</a>'),
    ("ab_footer", "© 2026 水仙的AI提示词 · 用 ❤ 与一点点蓝意做成"),
    # 赞赏
    ("sp_eyebrow", "Sponsor"), ("sp_h1", "请作者喝杯咖啡"),
    ("sp_sub", "你的支持，是水仙持续更新的动力 ☕"), ("sp_h2", "赞赏水仙 🌼"),
    ("sp_qr_cap", "微信扫一扫 · 赞赏作者"),
    ("sp_alt", '没有微信也没关系，欢迎在 <a href="about.html#contact">关于页</a> 找到我们，或去 <a href="submit.html">投稿</a> 用一条好提示词来支持——那同样是很暖的鼓励。'),
    # 投稿
    ("sb_eyebrow", "Submit"), ("sb_h1", "投稿好提示词"),
    ("sb_sub", "你的作品会出现在水仙的花园里，被更多人看到、使用、喜欢"),
    ("sb_h3_guide", "投稿须知"),
    ("sb_li1", "<b>内容</b>：一条完整的、出图效果好的中文（或中英混合）AI 图像提示词。"),
    ("sb_li2", "<b>格式</b>：建议附上分类（如「人物写真 / 电影感」）和 1–2 张效果预览图，方便我们归档展示。"),
    ("sb_li3", "<b>原创优先</b>：转载请注明来源；我们仅作整理展示，版权归原作者。"),
    ("sb_li4", "<b>审核</b>：我们会筛选表达清晰、可复用的提示词收录，不符合的恕不逐一回复。"),
    ("sb_h3_mail", "发送到投稿邮箱"),
    ("sb_p_mail", "把提示词 + 预览图发到下方邮箱，标题写「投稿 + 分类」即可。"),
    ("sb_tip", "没有邮箱也没关系，关注首页公众号「水仙的AI提示词」直接发消息给我们也行 🌿"),
    # 404
    ("nf_h1", "这朵水仙暂时没找到"), ("nf_p", "你访问的页面可能已被移动或从未存在。"),
    ("nf_home", "回到首页"), ("nf_gallery", "逛逛画廊"), ("nf_search", "去搜索"),
    # 收藏合集页（静态按钮）
    ("col_title", "我的收藏合集"),
    ("col_sub", "无需登录，全部保存在本机浏览器。可建多个合集分门别类，拖拽排序、跨合集移动、导出 JSON / Markdown / CSV，也能批量下载图片。"),
    ("col_new", "＋ 新建合集"),
    ("col_export_all", "导出全部"),
    ("col_export_cur", "导出当前合集"),
    ("col_import", "导入 JSON"),
    ("col_dl_all", "批量下载图片"),
    ("col_rename_full", "重命名合集"),
    ("col_dup", "复制合集"),
    ("col_clear", "清空合集"),
    ("col_del", "删除合集"),
    ("col_hint", "提示：拖动卡片可调整合集内顺序；卡片右上角的按钮可移出或移动到其他合集。"),
    ("col_empty", "这个合集还是空的，去画廊点 ❤ 收藏喜欢的提示词吧。"),
]
NORM = lambda s: re.sub(r"\s+", " ", s or "").strip()
TEXT2KEY = {}
for k, v in P:
    TEXT2KEY.setdefault(NORM(v), k)

# ---------- 需手工锚定的（含数字 / 只出现在属性里） ----------
MANUAL = [
    # 首页 hero 导语（数字随数据变化）
    ("index.html",
     '<p class="lead">5,430 条精选提示词，按主题分成了 12 大分类、79 个小类——人物、动漫、海报、插画、产品、游戏……慢慢逛，总有一句能帮你出图。</p>',
     '<p class="lead" data-i18n="idx_lead">5,430 条精选提示词，按主题分成了 12 大分类、79 个小类——人物、动漫、海报、插画、产品、游戏……慢慢逛，总有一句能帮你出图。</p>'),
    ("index.html", '<p class="eyebrow">12 大分类 · 79 小类</p>',
     '<p class="eyebrow" data-i18n="idx_cats_eyebrow">12 大分类 · 79 小类</p>'),
    ("index.html", '查看全部 5,430 条', '查看全部 5,430 条'),  # 由 data-i18n 处理下方 a 标签
    ("index.html", '<a class="btn btn-primary" href="gallery.html?cat=全部">查看全部 5,430 条',
     '<a class="btn btn-primary" href="gallery.html?cat=全部" data-i18n="idx_see_all">查看全部 5,430 条'),
    # 分类总览副标题（数字）
    ("categories.html", '<p class="sub">12 大分类、79 个小类，共 5,430 条提示词。点任意小类即可进入对应画廊。</p>',
     '<p class="sub" data-i18n="cat_sub">12 大分类、79 个小类，共 5,430 条提示词。点任意小类即可进入对应画廊。</p>'),
    # 赞赏正文（数字）
    ("sponsor.html", '<p>整理 5,430 条提示词、维护这个花园花了不少心思。如果它帮到了你，欢迎量力赞赏，让花园长得更久。</p>',
     '<p data-i18n="sp_p">整理 5,430 条提示词、维护这个花园花了不少心思。如果它帮到了你，欢迎量力赞赏，让花园长得更久。</p>'),
    # 输入框 placeholder
    ("gallery.html", '<input id="galSearch" type="text" placeholder="在结果里搜索…" autocomplete="off">',
     '<input id="galSearch" type="text" placeholder="在结果里搜索…" data-i18n-placeholder="gal_search_ph" autocomplete="off">'),
    ("search.html", '<input id="bigSearch" type="text" placeholder="试试「赛博朋克」「角色立绘」「电影感」，也支持拼音缩写 sbpk…" autocomplete="off">',
     '<input id="bigSearch" type="text" placeholder="试试「赛博朋克」「角色立绘」「电影感」，也支持拼音缩写 sbpk…" data-i18n-placeholder="se_ph" autocomplete="off">'),
    # 搜索页初始计数文案
    ("search.html", '<span class="count" id="resultCount">输入关键词开始搜索</span>',
     '<span class="count" id="resultCount" data-i18n="se_placeholder_count">输入关键词开始搜索</span>'),
    # 视图切换按钮的 title
    ("gallery.html", '<button data-view="masonry" class="active" title="瀑布流">',
     '<button data-view="masonry" class="active" title="瀑布流" data-i18n-title="gal_view_masonry">'),
    ("gallery.html", '<button data-view="uniform" title="列表">',
     '<button data-view="uniform" title="列表" data-i18n-title="gal_view_list">'),
    # 页头（header 组件）属性
    ("components/header.html", 'title="切换版本" aria-label="切换版本"',
     'title="切换版本" data-i18n-title="title_skin" aria-label="切换版本"'),
    ("components/header.html", 'id="themeBtn" title="切换主题" aria-label="切换主题"',
     'id="themeBtn" title="切换主题" data-i18n-title="title_theme" aria-label="切换主题"'),
    ("components/header.html", 'class="icon-btn" href="favorites.html" title="收藏" aria-label="收藏"',
     'class="icon-btn" href="favorites.html" title="收藏" data-i18n-title="title_fav" aria-label="收藏"'),
    # 收藏页空状态：外层 div 内还有 <div class="big">，不能整块替换，改为包一层 span
    ("favorites.html", '<div class="big">🌼</div>这个合集还是空的，去画廊点 ❤ 收藏喜欢的提示词吧。',
     '<div class="big">🌼</div><span data-i18n="col_empty">这个合集还是空的，去画廊点 ❤ 收藏喜欢的提示词吧。</span>'),
]

FILES = ["components/header.html"] + [os.path.basename(p) for p in sorted(glob.glob(os.path.join(WS, "*.html")))]

# 允许承载 data-i18n 的标签（div 只匹配 class 白名单）
TAGS = ["h1", "h2", "h3", "p", "li", "option", "button", "span", "label", "a", "div", "small", "strong", "title"]

rx = re.compile(r"<(" + "|".join(TAGS) + r")(\s[^>]*)?>(.*?)</\1>", re.S | re.I)

rx_cache = {}

def inject(path):
    src = open(path, encoding="utf-8").read()
    out = src
    inserts = []  # (pos, text)
    # 逐个标签类型独立扫描整个文件：
    # 若用一条大正则一次扫，外层元素（如 <div>）会先消耗掉内层 <a>/<span> 的区域，
    # 导致内层再也匹配不到（这是上一版的 bug）。
    for tag in TAGS:
        rx = rx_cache.get(tag)
        if rx is None:
            rx = re.compile(r"<(" + tag + r")(\s[^>]*)?>(.*?)</" + tag + r">", re.S | re.I)
            rx_cache[tag] = rx
        for m in rx.finditer(src):
            attrs = m.group(2) or ""
            inner = m.group(3)
            if "data-i18n" in attrs:
                continue
            if tag == "div" and "<div" in inner.lower():
                continue
            key = TEXT2KEY.get(NORM(inner))
            if not key:
                continue
            pos = m.start() + 1 + len(m.group(1))
            inserts.append((pos, ' data-i18n="%s"' % key))
    # 去重（同一位置只插一次）
    seen = set()
    uniq = []
    for pos, txt in inserts:
        if pos in seen:
            continue
        seen.add(pos)
        uniq.append((pos, txt))
    for pos, txt in sorted(uniq, key=lambda x: -x[0]):
        out = out[:pos] + txt + out[pos:]
    changed = out != src
    if changed:
        open(path, "w", encoding="utf-8").write(out)
    return changed, len(uniq)

total = 0
for f in FILES:
    fp = os.path.join(WS, f)
    if not os.path.exists(fp):
        continue
    ch, n = inject(fp)
    print(("  %-22s +%d 处 data-i18n" % (f, n)) if ch else ("  %-22s 无变化" % f))
    total += n

print("\n-- 手工锚定 --")
for f, old, new in MANUAL:
    if old == new:
        continue
    fp = os.path.join(WS, f)
    s = open(fp, encoding="utf-8").read()
    if new in s and old != new:
        print("   已存在  ", f)
        continue
    if old not in s:
        print("   !! 未找到 ", f, "|", old[:60])
        continue
    open(fp, "w", encoding="utf-8").write(s.replace(old, new, 1))
    print("   已注入  ", f, "|", old[:48])

print("\n合计注入 %d 处 data-i18n" % total)

# ---------- 校验 ----------
print("\n-- 校验：统计各页 data-i18n 数量 --")
for f in FILES:
    fp = os.path.join(WS, f)
    if not os.path.exists(fp):
        continue
    s = open(fp, encoding="utf-8").read()
    print("  %-24s %d 个 data-i18n, %d 个 placeholder/title" % (
        f, s.count("data-i18n="), s.count("data-i18n-placeholder=") + s.count("data-i18n-title=")))
