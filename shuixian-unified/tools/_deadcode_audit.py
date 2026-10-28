# -*- coding: utf-8 -*-
"""死代码扫描器（只读，不改任何文件）
输出：
  A. i18n 孤儿 key（字典里有、页面上没人用）
  B. JS 里定义后从未被引用的函数 / 顶层常量 / App 方法 / window.__ 全局
  C. CSS 里定义了但 HTML/JS 从未出现的 class / id
  D. 文件级：data/ 与 images/ 与根目录里没人引用的文件
用法：python tools/_deadcode_audit.py
"""
import io, os, re, sys, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(p):
    return io.open(p, encoding='utf-8', errors='replace').read()


def walk(subs, exts):
    out = []
    for s in subs:
        p = os.path.join(ROOT, s)
        if os.path.isfile(p):
            out.append(p)
            continue
        for dp, _, fs in os.walk(p):
            for f in fs:
                if any(f.endswith(e) for e in exts):
                    out.append(os.path.join(dp, f))
    return sorted(out)


HTML = walk(['.'], ['.html'])
JS = walk(['js', 'sw.js'], ['.js'])
TOOLS = walk(['tools'], ['.js'])
PRODUCT = {p: read(p) for p in HTML + JS}
TESTS = {p: read(p) for p in TOOLS}


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def count_in_product(tok, exclude=None):
    n = 0
    hits = []
    for p, s in PRODUCT.items():
        if exclude and os.path.abspath(p) == os.path.abspath(exclude):
            continue
        c = s.count(tok)
        if c:
            n += c
            hits.append('%s×%d' % (rel(p), c))
    return n, hits


report = []


def head(t):
    report.append('')
    report.append('=' * 70)
    report.append(t)
    report.append('=' * 70)


# ---------- A. i18n 孤儿 key ----------
head('A. i18n 孤儿 key（字典有、产品代码里一次都没出现）')
i18n_src = read(os.path.join(ROOT, 'js', 'i18n.js'))
# 取 zh 段里的 key（形如  key: "..."）
keys = []
m = re.search(r'zh\s*:\s*\{(.*?)\n\s{4}\}', i18n_src, re.S)
if m:
    keys = re.findall(r'^\s{6}([a-z0-9_]+)\s*:', m.group(1), re.M)
cat_m = re.search(r'cat\s*:\s*\{(.*?)\n\s{4}\}', i18n_src, re.S)
orphans = []
for k in keys:
    n, hits = count_in_product("'%s'" % k)
    n2, hits2 = count_in_product('"%s"' % k)
    n3, hits3 = count_in_product('data-i18n="%s"' % k)
    if n + n2 + n3 == 0:
        orphans.append(k)
report.append('zh 字典 key 共 %d 个，孤儿 %d 个' % (len(keys), len(orphans)))
for k in orphans:
    report.append('  ORPHAN  %s' % k)

# ---------- B. JS 定义但未引用 ----------
head('B. JS 里定义后产品代码从不引用（函数 / 顶层 const / App 方法 / 全局）')
defs = []
for p in [os.path.join(ROOT, 'js', 'base.js'), os.path.join(ROOT, 'js', 'features.js'), os.path.join(ROOT, 'js', 'i18n.js')]:
    s = read(p)
    for mm in re.finditer(r'^\s*function\s+([A-Za-z_$][\w$]*)\s*\(', s, re.M):
        defs.append((rel(p), mm.group(1), 'function'))
    for mm in re.finditer(r'^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=', s, re.M):
        defs.append((rel(p), mm.group(1), 'topconst'))
    for mm in re.finditer(r'^\s*App\.([A-Za-z_$][\w$]*)\s*=', s, re.M):
        defs.append((rel(p), 'App.' + mm.group(1), 'app'))
    for mm in re.finditer(r'window\.(__[A-Za-z_$][\w$]*)\s*=', s):
        defs.append((rel(p), mm.group(1), 'global'))

dead = []
seen = set()
for f, name, kind in defs:
    if (name, kind) in seen:
        continue
    seen.add((name, kind))
    # 定义处本身至少出现 1 次；产品范围内 <=1 视为无人使用
    n, hits = count_in_product(name)
    if n <= 1:
        dead.append((kind, name, f, n, hits))
for kind, name, f, n, hits in sorted(dead, key=lambda x: (x[0], x[1])):
    report.append('  UNUSED  [%s] %-28s def in %-14s product_hits=%d' % (kind, name, f, n))
report.append('  合计 %d 个' % len(dead))

# ---------- C. CSS 未使用选择器 ----------
head('C. CSS 里的 class / id 在产品 HTML+JS 中从未出现')
css_txt = ''
for p in ['css/base.css', 'css/features.css']:
    css_txt += read(os.path.join(ROOT, p))
sel_classes = set()
for mm in re.finditer(r'([^{}]+)\{', css_txt):
    block = mm.group(1)
    if '@' in block or ':' in block.replace('::', ''):
        pass
    for c in re.findall(r'\.([A-Za-z][\w-]*)', block):
        sel_classes.add(c)
sel_ids = set()
for mm in re.finditer(r'([^{}]+)\{', css_txt):
    for c in re.findall(r'#([A-Za-z][\w-]*)', mm.group(1)):
        sel_ids.add(c)

def used_word(word):
    """词边界匹配：.feature 不会被 features.css 这种子串骗到"""
    pat = re.compile(r'(?<![\w-])' + re.escape(word) + r'(?![\w-])')
    return any(pat.search(s) for s in PRODUCT.values())

unused_cls = [c for c in sorted(sel_classes) if not used_word(c)]
unused_ids = [c for c in sorted(sel_ids) if not used_word(c)]
report.append('CSS class 共 %d 个，未被引用 %d 个：' % (len(sel_classes), len(unused_cls)))
report.append('   ' + ', '.join('.%s' % c for c in unused_cls))
report.append('CSS id 共 %d 个，未被引用 %d 个：' % (len(sel_ids), len(unused_ids)))
report.append('   ' + ', '.join('#%s' % c for c in unused_ids))

# ---------- D. 文件级 ----------
head('D. 文件引用情况（data/ images/ 根目录杂项）')
all_txt = '\n'.join(PRODUCT.values())
all_txt += '\n' + '\n'.join(TESTS.values())
for f in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p):
        continue
    if f.endswith(('.html',)) or f in ('sw.js',):
        refs = all_txt.count(f)
        if f not in ('404.html', 'index.html') and refs <= 1:
            report.append('  FILE?   %-34s refs=%d' % (f, refs))
    elif f.endswith(('.txt', '.md', '.py', '.json')):
        refs = all_txt.count(f)
        if refs == 0:
            report.append('  FILE?   %-34s refs=0' % f)
for d in ['data', 'images', 'userscript']:
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p):
        continue
    for f in sorted(os.listdir(p)):
        fp = os.path.join(p, f)
        if not os.path.isfile(fp):
            continue
        refs = all_txt.count(f)
        if refs == 0:
            report.append('  FILE?   %-34s refs=0  (%d bytes)' % (d + '/' + f, os.path.getsize(fp)))

out = '\n'.join(report)
io.open(os.path.join(ROOT, 'tools', '_deadcode_report.txt'), 'w', encoding='utf-8').write(out)
print(out)
