import io, os, re, sys

ROOT = r'C:\Users\lianxiang\WorkBuddy\2026-07-23-09-09-54\shuixian-unified-0920'
OLD, NEW = '16', '17'
changed = []

# 1) js/base.js  ->  ASSET_VERSION = 'N'
p = os.path.join(ROOT, 'js', 'base.js')
s = io.open(p, encoding='utf-8').read()
pat = re.compile(r"(ASSET_VERSION\s*=\s*')(\d+)(')")
s2 = pat.sub(lambda m: m.group(1) + NEW + m.group(3), s, count=1)
if s2 != s:
    io.open(p, 'w', encoding='utf-8', newline='').write(s2)
    changed.append('js/base.js')

# 2) 根目录 HTML 的 ?v=N
vpat = re.compile(r'\?v=' + OLD + r'(?!\d)')
for f in sorted(os.listdir(ROOT)):
    if not f.endswith('.html'):
        continue
    p = os.path.join(ROOT, f)
    s = io.open(p, encoding='utf-8').read()
    s2 = vpat.sub('?v=' + NEW, s)
    if s2 != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(s2)
        changed.append(f)

# 3) sw.js  ->  VERSION + precache 里的 ?v=
p = os.path.join(ROOT, 'sw.js')
s = io.open(p, encoding='utf-8').read()
s2 = s.replace("VERSION = 'sx-v" + OLD + "'", "VERSION = 'sx-v" + NEW + "'")
s2 = vpat.sub('?v=' + NEW, s2)
if s2 != s:
    io.open(p, 'w', encoding='utf-8', newline='').write(s2)
    changed.append('sw.js')

print('changed:', changed)
print()

# ---- 校验 ----
s = io.open(os.path.join(ROOT, 'js', 'base.js'), encoding='utf-8').read()
print('base.js ASSET_VERSION =', pat.search(s).group(2))
for f in sorted(os.listdir(ROOT)):
    if f.endswith('.html'):
        t = io.open(os.path.join(ROOT, f), encoding='utf-8').read()
        print('  %-18s %s' % (f, sorted(set(re.findall(r'\?v=(\d+)', t)))))
t = io.open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
print('sw.js   ?v=', sorted(set(re.findall(r'\?v=(\d+)', t))),
      ' VERSION =', re.search(r"VERSION\s*=\s*'([^']+)'", t).group(1))
