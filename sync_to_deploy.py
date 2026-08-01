# -*- coding: utf-8 -*-
"""sync_to_deploy.py —— 本地版(shuixian-prompts) → 部署版(shuixian-deploy) 安全同步脚本

为什么需要它：
  部署版在本地版基础上做了若干「仅部署需要」的优化（R2 远程图、轻量 list 首屏、
  完整数据懒加载、HTML preconnect）。直接用本地版整目录覆盖部署版会把这些优化冲掉，
  导致线上图 404、首屏变慢。本脚本在「复制本地改动」的同时，自动把这些优化重新打回去。

它做了什么（顺序）：
  1) 整文件复制「两边本就一致」的文件：classify.js / css / components / 分类统计 /
     twitter 完整数据 / manifest。
  2) 复制 4 个 HTML，并在 <head> 补回 R2 的 preconnect（幂等）。
  3) 复制 5 个带优化的 JS（base/gallery/home/favorites），再用一组幂等补丁把部署优化
     重新注入（IMG_BASE、list 模式、ensureFull 懒加载、isPerson、fullOf、preconnect 等）。
     任何补丁锚点找不到时只告警、不破坏文件。
  4) 用本地 prompts.json 重新切分 prompts.part1/2/3.json，并调用 build_list.py 重新生成
     轻量 list.*.json，保证数据两端一致。
  5) 全程不动 images/（绝不把本地 3.6GB 原图拷回部署版）、不动 _headers / README.md。

用法：
  python sync_to_deploy.py            # 真正执行
  python sync_to_deploy.py --dry-run  # 只打印将要做什么，不写文件
  python sync_to_deploy.py --no-data  # 跳过数据重新生成（仅同步前端代码）
"""
import os, sys, json, shutil, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.join(ROOT, "shuixian-prompts")
DEPLOY = os.path.join(ROOT, "shuixian-deploy")
DATA_L = os.path.join(LOCAL, "data")
DATA_D = os.path.join(DEPLOY, "data")
PY = r"C:\Users\lianxiang\.workbuddy\binaries\python\versions\3.13.12\python.exe"
R2 = "https://r2.qqsrc.com"

DRY = "--dry-run" in sys.argv
NO_DATA = "--no-data" in sys.argv

log_lines = []
def log(msg):
    print(msg); log_lines.append(msg)
def warn(msg):
    print("  ⚠ " + msg); log_lines.append("WARN: " + msg)

# ---------- 1) 安全整文件复制（两边本就一致 / 纯数据） ----------
SAFE_FILES = [
    "js/classify.js",
    "css/base.css",
    "components/header.html",
    "components/footer.html",
    "components/lightbox.html",
    "components/modals.html",
    "data/categories.json",
    "data/twitter_manifest.json",
    "data/prompts-twitter.json",
]

# ---------- 2) HTML（复制 + 补 R2 preconnect） ----------
HTML_FILES = ["index.html", "gallery.html", "classify.html", "favorites.html"]
HTML_PRECONNECT_PATCH = {
    "marker": "r2.qqsrc.com",
    "find": '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
    "replace": '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
               '  <link rel="preconnect" href="https://r2.qqsrc.com" crossorigin>\n'
               '  <link rel="dns-prefetch" href="https://r2.qqsrc.com">',
}

# ---------- 3) 受保护的 JS（复制 + 部署优化补丁） ----------
PROTECTED_JS = ["js/base.js", "js/gallery.js", "js/home.js", "js/favorites.js"]

BASE_PATCHES = [
    {  # IMG_BASE 指向 R2
        "name": "base.IMG_BASE→R2",
        "marker": 'const IMG_BASE = "https://r2.qqsrc.com";',
        "find": '  const IMG_BASE = "";',
        "replace": '  const IMG_BASE = "https://r2.qqsrc.com";',
    },
    {  # USE_LIST / DETAIL 状态变量
        "name": "base.USE_LIST状态",
        "marker": "let USE_LIST = false;",
        "find": "  let timer = null;",
        "replace": "  let timer = null;\n\n"
                   "  // 轻量列表模式（部署版）：首屏只加载 list 文件，完整 prompt 后台/按需加载\n"
                   "  let USE_LIST = false;\n"
                   "  let fullLoaded = false;\n"
                   "  let fullPromise = null;\n"
                   "  const DETAIL = {};",
    },
    {  # getTags 优先用预计算 themes/styles
        "name": "base.getTags预计算",
        "marker": "let themes, styles;",
        "find": '    const text = ((d.title||"") + " " + (d.prompt||"")).toLowerCase();\n'
                 '    const themes = THEMES.filter(t => TAG_RULES.themes[t].test(text));\n'
                 '    const styles = STYLES.filter(s => TAG_RULES.styles[s].test(text));',
        "replace": "    let themes, styles;\n"
                   "    if(Array.isArray(d.themes) && Array.isArray(d.styles)){ themes = d.themes; styles = d.styles; }\n"
                   "    else {\n"
                   '      const text = ((d.title||"") + " " + (d.prompt||"")).toLowerCase();\n'
                   "      themes = THEMES.filter(t => TAG_RULES.themes[t].test(text));\n"
                   "      styles = STYLES.filter(s => TAG_RULES.styles[s].test(text));\n"
                   "    }",
    },
    {  # isPerson 共享函数
        "name": "base.isPerson函数",
        "marker": "function isPerson(d){",
        "find": "  // ---------- 数据 ----------\n",
        "replace": "  // 是否「全部人像」：优先用列表预计算标志，回退到完整规则（兼容本地版）\n"
                   "  function isPerson(d){\n"
                   '    if(typeof d.person === \'boolean\') return d.person;\n'
                   '    return ((d.title||"")+(d.prompt||"")).toLowerCase().includes("人像") || (d.category||"").includes("人像") || (d.category||"").includes("头像");\n'
                   "  }\n"
                   "  // ---------- 数据 ----------\n",
    },
    {  # loadData 改 list 优先 + ensureFull + fullOf
        "name": "base.loadData→list模式",
        "marker": "const LIST_PARTS =",
        "find": '  // 兼容两种数据源：部署版用拆分文件 prompts.part1/2/3.json，本地版用单文件 prompts.json\n'
                '  const DATA_PARTS = ["data/prompts.part1.json","data/prompts.part2.json","data/prompts.part3.json"];\n'
                "  async function loadData(){\n"
                "    let main;\n"
                "    try {\n"
                "      const rp = await fetch('data/prompts.part1.json');\n"
                "      if(rp.ok){\n"
                "        const parts = await Promise.all(DATA_PARTS.map(u => fetch(u).then(x => x.json())));\n"
                "        main = [].concat(...parts);\n"
                "      } else {\n"
                '        main = await (await fetch(\'data/prompts.json\')).json();\n'
                "      }\n"
                "    } catch(e){\n"
                '      main = await (await fetch(\'data/prompts.json\')).json();\n'
                "    }\n"
                '    const m = await fetch(\'data/twitter_manifest.json\').then(r => r.json()).catch(() => ({ files:["prompts-twitter.json"] }));\n'
                '    const tws = await Promise.all(m.files.map(f => fetch(\'data/\'+f).then(r => r.json()).catch(() => [])));\n'
                "    ALL = main.concat(...tws);\n"
                "  }",
        "replace": "  // 兼容两种数据源：部署版优先用轻量 list 文件（首屏快），本地版用完整 prompts.json\n"
                   '  const LIST_PARTS = ["data/list.part1.json","data/list.part2.json","data/list.part3.json"];\n'
                   '  const FULL_PARTS = ["data/prompts.part1.json","data/prompts.part2.json","data/prompts.part3.json"];\n'
                   "  async function loadData(){\n"
                   "    // 1) 轻量列表优先（部署版）：一次性拉齐 list.part1/2/3（共 ~3.2MB，远小于完整 25MB）\n"
                   "    //    注意：必须 await 全部 part，不能把 part2/3 放后台再 ALL=... 赋值——否则后台完成时\n"
                   "    //    会覆盖 twitter 已合并的结果，造成数据丢失（已踩坑：首屏只拿到 ~5166 条）。\n"
                   "    let main = null;\n"
                   "    try {\n"
                   "      const rp = await fetch(LIST_PARTS[0]);\n"
                   "      if(rp.ok){\n"
                   "        USE_LIST = true;\n"
                   "        const parts = await Promise.all(LIST_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));\n"
                   "        main = [].concat(...parts);\n"
                   "      }\n"
                   "    } catch(e){ main = null; }\n"
                   "    if(!main){\n"
                   "      // 回退：本地版完整数据（无 list 文件）\n"
                   '      try { main = await (await fetch(\'data/prompts.json\')).json(); }\n'
                   "      catch(e){ main = []; }\n"
                   "      main.forEach(e => { DETAIL[tagKey(e)] = e; });  // 本地版直接建完整索引\n"
                   "      fullLoaded = true;\n"
                   "    }\n"
                   "    // 2) twitter 列表（优先 list 版，回退完整版）\n"
                   '    const m = await fetch(\'data/twitter_manifest.json\').then(r => r.json()).catch(() => ({ files:["prompts-twitter.json"] }));\n'
                   "    const tws = [];\n"
                   "    for(const f of m.files){\n"
                   "      const listName = 'data/list-' + f.replace(/^prompts-/, '');\n"
                   "      let arr = await fetch(listName).then(r => r.ok ? r.json() : null).catch(() => null);\n"
                   "      if(!arr) arr = await fetch('data/'+f).then(r => r.json()).catch(() => []);\n"
                   "      if(arr && arr.length) tws.push(arr);\n"
                   "    }\n"
                   "    ALL = main.concat(...tws);\n"
                   "    // 注意：完整数据（25MB）不在此自动加载，改为灯箱/复制首次使用时按需加载（ensureFull），\n"
                   "    // 避免占用带宽拖慢图片加载；重复访问时已被浏览器缓存。\n"
                   "  }\n\n"
                   "  // 按需/后台加载完整数据，填充 DETAIL 索引，供灯箱与复制取完整 prompt\n"
                   "  function ensureFull(){\n"
                   "    if(fullLoaded) return Promise.resolve();\n"
                   "    if(fullPromise) return fullPromise;\n"
                   "    fullPromise = (async () => {\n"
                   "      let full = [];\n"
                   "      try {\n"
                   "        const rp = await fetch(FULL_PARTS[0]);\n"
                   "        if(rp.ok){\n"
                   "          const parts = await Promise.all(FULL_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));\n"
                   "          full = [].concat(...parts);\n"
                   "        } else {\n"
                   '          full = await (await fetch(\'data/prompts.json\')).json();\n'
                   "        }\n"
                   "      } catch(e){ full = []; }\n"
                   '      const m = await fetch(\'data/twitter_manifest.json\').then(r => r.json()).catch(() => ({ files:["prompts-twitter.json"] }));\n'
                   "      const tws = await Promise.all(m.files.map(f => fetch('data/'+f).then(r => r.json()).catch(() => [])));\n"
                   "      full = full.concat(...tws);\n"
                   "      full.forEach(e => { DETAIL[tagKey(e)] = e; });\n"
                   "      fullLoaded = true;\n"
                   "    })();\n"
                   "    return fullPromise;\n"
                   "  }\n"
                   "  // 取完整条目（含 prompt）；列表模式下若尚未加载则退回轻量条目\n"
                   "  function fullOf(d){ return DETAIL[tagKey(d)] || d; }",
    },
    {  # addFav 存完整条目
        "name": "base.addFav→fullOf",
        "marker": "item: fullOf(d)",
        "find": "  function addFav(d, boardId){ favData.items[d.id] = { boardId: boardId || 'default', item:d }; saveFav(); }",
        "replace": "  function addFav(d, boardId){ favData.items[d.id] = { boardId: boardId || 'default', item: fullOf(d) }; saveFav(); }",
    },
    {  # openLightbox 改 async + 加载中占位
        "name": "base.openLightbox→async",
        "marker": "let lbEntry = null;",
        "find": "  function openLightbox(d){\n"
                "    lbList = (d.images && d.images.length) ? d.images.slice() : [d.image || d.thumb];\n"
                "    lbIndex = 0;\n"
                "    renderLb();\n"
                '    document.getElementById(\'lbTitle\').textContent = d.title || "(未命名)";\n'
                '    document.getElementById(\'lbPrompt\').textContent = d.prompt || "(暂无提示词内容)";',
        "replace": "  let lbEntry = null;\n"
                   "  async function openLightbox(d){\n"
                   "    lbEntry = d;\n"
                   "    const f = fullOf(d);\n"
                   "    lbList = (f.images && f.images.length) ? f.images.slice() : [f.image || f.thumb];\n"
                   "    lbIndex = 0;\n"
                   "    renderLb();\n"
                   '    document.getElementById(\'lbTitle\').textContent = f.title || "(未命名)";\n'
                   '    document.getElementById(\'lbPrompt\').textContent = (f.prompt != null) ? f.prompt : "(加载中…)";\n'
                   "    if(f.prompt == null){\n"
                   "      // 列表模式下完整 prompt 尚未加载，等后台加载完再补齐\n"
                   "      await ensureFull();\n"
                   "      if(lbEntry === d){\n"
                   "        const ff = fullOf(d);\n"
                   '        document.getElementById(\'lbTitle\').textContent = ff.title || "(未命名)";\n'
                   '        document.getElementById(\'lbPrompt\').textContent = ff.prompt || "(暂无提示词内容)";\n'
                   "      }\n"
                   "    }",
    },
    {  # 复制按钮用 fullOf
        "name": "base.复制按钮→fullOf",
        "marker": "const f = fullOf(d); if(f.prompt == null)",
        "find": '    const copyBtn = document.createElement(\'button\'); copyBtn.className = "act-btn primary"; copyBtn.textContent = "复制提示词"; copyBtn.onclick = (e) => { e.stopPropagation(); copyText(d.prompt || ""); };',
        "replace": '    const copyBtn = document.createElement(\'button\'); copyBtn.className = "act-btn primary"; copyBtn.textContent = "复制提示词"; copyBtn.onclick = (e) => { e.stopPropagation(); const f = fullOf(d); if(f.prompt == null){ ensureFull().then(() => copyText(fullOf(d).prompt || "")); } else { copyText(f.prompt || ""); } };',
    },
    {  # 公共 API 暴露 isPerson/fullOf/ensureFull
        "name": "base.公共API暴露",
        "marker": "isPerson, fullOf, ensureFull,",
        "find": "    getCatStyle, getBatch, imgUrl, getTags, applySort, toggle,",
        "replace": "    getCatStyle, getBatch, imgUrl, getTags, applySort, toggle, isPerson, fullOf, ensureFull,",
    },
]

def person_filter_patch():
    # gallery.js / home.js 共用同一行「全部人像」过滤
    return {
        "name": "isPerson用法",
        "marker": "list = list.filter(App.isPerson);",
        "find": '        list = list.filter(d => ((d.title||"")+(d.prompt||"")).toLowerCase().includes("人像") || (d.category||"").includes("人像") || (d.category||"").includes("头像"));',
        "replace": "        list = list.filter(App.isPerson);",
    }

GALLERY_PATCHES = [
    person_filter_patch(),
    {
        "name": "gallery.__onListGrown钩子",
        "marker": "window.__onListGrown = () =>",
        "find": '    onReady: () => { renderChips(); wireSort(); resetAndRender(); document.addEventListener(\'click\', () => document.querySelectorAll(\'.sort-list\').forEach(s => s.classList.remove(\'show\'))); }',
        "replace": "    onReady: () => {\n"
                   "      renderChips(); wireSort(); resetAndRender();\n"
                   "      document.addEventListener('click', () => document.querySelectorAll('.sort-list').forEach(s => s.classList.remove('show')));\n"
                   "      // 轻量列表 part2/3 后台到达后，刷新 chip 计数与「显示更多」状态（不重建网格，避免打断浏览）\n"
                   '      window.__onListGrown = () => { renderChips(); const list = getGalleryList(); document.getElementById(\'showMore\').style.display = (rendered < list.length) ? "inline-flex" : "none"; };\n'
                   "    }",
    },
]

HOME_PATCHES = [ person_filter_patch() ]

FAVORITES_PATCHES = [
    {
        "name": "favorites.导出await ensureFull",
        "marker": "await App.ensureFull();",
        "find": "    document.getElementById('exportMdBtn').onclick = () => {",
        "replace": "    document.getElementById('exportMdBtn').onclick = async () => {\n      await App.ensureFull();",
    },
    {
        "name": "favorites.导出用fullOf",
        "marker": "(App.fullOf(d).prompt || '')",
        "find": "        md += '\\n```\\n' + (d.prompt || '') + '\\n```\\n\\n';",
        "replace": "        md += '\\n```\\n' + (App.fullOf(d).prompt || '') + '\\n```\\n\\n';",
    },
]

JS_PATCHES = {
    "js/base.js": BASE_PATCHES,
    "js/gallery.js": GALLERY_PATCHES,
    "js/home.js": HOME_PATCHES,
    "js/favorites.js": FAVORITES_PATCHES,
}

# ---------- 工具 ----------
def read_text(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")
def write_text(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
def dump_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def copy_safe(rel):
    src = os.path.join(LOCAL, rel); dst = os.path.join(DEPLOY, rel)
    if not os.path.exists(src):
        warn("本地缺失，跳过: " + rel); return
    if DRY:
        log("  [dry] copy " + rel); return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    log("  copy " + rel)

def copy_and_patch(rel, patches):
    src = os.path.join(LOCAL, rel); dst = os.path.join(DEPLOY, rel)
    if not os.path.exists(src):
        warn("本地缺失，跳过: " + rel); return
    content = read_text(src)
    for p in patches:
        if p.get("marker") and p["marker"] in content:
            log("    skip(已存在): " + p["name"]); continue
        if p["find"] in content:
            content = content.replace(p["find"], p["replace"], 1)
            log("    applied: " + p["name"])
        else:
            warn("补丁锚点找不到，跳过(文件保持本地原样): " + p["name"])
    if DRY:
        log("  [dry] patch " + rel); return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    write_text(dst, content)
    log("  patch+write " + rel)

def split_prompts():
    src = os.path.join(DATA_L, "prompts.json")
    if not os.path.exists(src):
        warn("本地 prompts.json 缺失，跳过数据重新生成"); return
    data = json.load(open(src, encoding="utf-8"))
    n = len(data)
    part = (n + 2) // 3
    chunks = [data[i:i+part] for i in range(0, n, part)][:3]
    if DRY:
        log("  [dry] split prompts.json (%d 条) -> prompts.part1/2/3.json" % n); return
    for i, c in enumerate(chunks, 1):
        dump_json(os.path.join(DATA_D, "prompts.part%d.json" % i), c)
    log("  split prompts.json (%d 条) -> prompts.part1/2/3.json (%d/%d/%d)" %
        (n, len(chunks[0]), len(chunks[1]), len(chunks[2])))

def regen_list():
    if DRY:
        log("  [dry] run build_list.py"); return
    r = subprocess.run([PY, os.path.join(ROOT, "scripts", "build_list.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        warn("build_list.py 失败:\n" + r.stderr); return
    for line in r.stdout.strip().splitlines():
        log("    " + line)

# ---------- 主流程 ----------
def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log("=" * 60)
    log("同步 本地版 -> 部署版" + (" [DRY-RUN]" if DRY else ""))
    log("  本地: " + LOCAL)
    log("  部署: " + DEPLOY)
    log("=" * 60)

    log("\n[1] 安全整文件复制（classify/css/components/分类统计/twitter数据/manifest）")
    for f in SAFE_FILES:
        copy_safe(f)

    log("\n[2] HTML 复制 + 补 R2 preconnect")
    for h in HTML_FILES:
        copy_and_patch_html(h)

    log("\n[3] 受保护 JS：复制本地 + 重新注入部署优化")
    for j in PROTECTED_JS:
        log("  " + j)
        copy_and_patch(j, JS_PATCHES[j])

    if not NO_DATA:
        log("\n[4] 数据重新生成（本地 prompts.json -> part + list）")
        split_prompts()
        regen_list()
    else:
        log("\n[4] 跳过数据重新生成（--no-data）")

    log("\n[5] 保护项确认（不动这些）")
    log("  - images/ 原图：不拷贝（保持 R2 远程）")
    log("  - _headers / README.md：不触碰")
    log("=" * 60)
    log("完成。" + ("（DRY-RUN，未写任何文件）" if DRY else ""))

def copy_and_patch_html(rel):
    src = os.path.join(LOCAL, rel); dst = os.path.join(DEPLOY, rel)
    if not os.path.exists(src):
        warn("本地缺失，跳过: " + rel); return
    content = read_text(src)
    p = HTML_PRECONNECT_PATCH
    if p["marker"] in content:
        log("    skip(已存在 preconnect): " + rel)
    elif p["find"] in content:
        content = content.replace(p["find"], p["replace"], 1)
        log("    applied: preconnect " + rel)
    else:
        warn("HTML 锚点找不到，跳过 preconnect: " + rel)
    if DRY:
        log("  [dry] html " + rel); return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    write_text(dst, content)
    log("  write " + rel)

if __name__ == "__main__":
    main()
