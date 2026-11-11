/* 搜索 + 连续编号回归：
   ① 搜索框与筛选条同行  ② 编号 = 1..N 连续  ③ 卡片链接用编号
   ④ 灯箱标签与底部计数一致  ⑤ 按编号搜索命中  ⑥ 详情页编号/旧 id 都能开  ⑦ 无效编号兜底 */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

async function typeQ(pg, q) {
  await pg.evaluate(q => {
    const i = document.querySelector('#galSearch');
    i.value = q;
    i.dispatchEvent(new Event('input', { bubbles: true }));
  }, q);
  await new Promise(r => setTimeout(r, 1400));
}

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  let pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 1440, height: 1000 });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2800));

  /* ---------- 搜索框位置 ---------- */
  const geo = await pg.evaluate(() => {
    const gs = document.querySelector('#galSearch');
    const fb = document.querySelector('#fxFilterBar');
    if (!gs || !fb) return { missing: !gs ? 'search' : 'filterbar' };
    const a = gs.getBoundingClientRect(), c = fb.getBoundingClientRect();
    return {
      sameRow: Math.abs((a.top + a.height / 2) - (c.top + c.height / 2)) < 22,
      rightOf: a.left > c.left,
      inTools: !!gs.closest('.gallery-tools') && !!fb.closest('.gallery-tools'),
      ph: gs.placeholder,
    };
  });
  ok(!geo.missing, '画廊存在搜索框与筛选条', geo.missing);
  ok(geo.sameRow && geo.rightOf, '搜索框与筛选条同一行、位于右侧', JSON.stringify(geo));
  ok(geo.inTools, '两者同处 .gallery-tools 容器');
  ok(/ID/.test(geo.ph || ''), '占位提示说明可输入编号：' + geo.ph);

  /* ---------- 连续编号 ---------- */
  const seqInfo = await pg.evaluate(() => {
    const all = window.App.ALL.map(s => ({ id: s.id, seq: window.App.seqOf(s) })).sort((a, b) => a.seq - b.seq);
    return { n: all.length, first: all[0], last: all[all.length - 1], uniq: new Set(all.map(x => x.seq)).size };
  });
  ok(seqInfo.first.seq === 1 && seqInfo.last.seq === seqInfo.n && seqInfo.uniq === seqInfo.n,
    `编号 1..${seqInfo.n} 连续且唯一`);

  const links = await pg.evaluate(() => [...document.querySelectorAll('#grid .card a.thumb')].slice(0, 6).map(a => a.getAttribute('href')));
  ok(links.every(h => /^detail\.html\?id=\d{1,4}$/.test(h)), '卡片链接使用对外编号（≤4 位）', links[0]);

  /* ---------- 灯箱：标签与底部计数一致 ---------- */
  await pg.evaluate(() => document.querySelector('#grid .card').click());
  await new Promise(r => setTimeout(r, 1800));
  const lb = await pg.evaluate(() => ({
    tags: [...document.querySelectorAll('.lb-tags .tag')].map(t => t.textContent.trim()),
    count: (document.querySelector('.lb-count') || {}).textContent || '',
  }));
  const idTag = lb.tags.find(t => /^ID #\d+$/.test(t)) || '';
  ok(!!idTag, '灯箱标签显示 ID #连续编号：' + idTag);
  const n1 = (idTag.match(/\d+/) || [])[0];
  const n2 = (lb.count.match(/ID (\d+)/) || [])[1];
  ok(n1 && n1 === n2, '标签编号 = 底部计数（' + n1 + ' / ' + n2 + '）');
  ok(lb.count.trim().endsWith('/ ' + seqInfo.n), '底部显示「ID x / ' + seqInfo.n + '」', lb.count);
  await pg.evaluate(() => document.querySelector('#lb-close') && document.querySelector('#lb-close').click());
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2200));

  /* ---------- 按编号搜索 ---------- */
  const target = seqInfo.first;                       // seq = 1
  const mid = await pg.evaluate(() => {
    const all = window.App.ALL.slice().sort((a, b) => window.App.seqOf(a) - window.App.seqOf(b));
    const s = all[Math.floor(all.length / 2)];
    return { id: s.id, seq: window.App.seqOf(s) };
  });
  for (const t of [target, mid]) {
    for (const q of [String(t.seq), '#' + t.seq]) {
      await typeQ(pg, q);
      const r = await pg.evaluate(() => ({
        ids: [...document.querySelectorAll('#grid .card')].map(c => +c.dataset.id).slice(0, 2),
        legend: ((document.querySelector('#hlLegend') || {}).textContent || '').trim(),
      }));
      ok(r.ids[0] === t.id, `搜索 ${q} → 首条是该条（内部 id ${t.id}）`, JSON.stringify(r.ids));
      ok(/ID/.test(r.legend), `搜索 ${q} 时提示按 ID 匹配：${r.legend.slice(0, 18)}`);
    }
  }

  /* 关键词仍可用 */
  await typeQ(pg, '赛博朋克');
  const kw = await pg.evaluate(() => ({
    n: parseInt(((document.querySelector('#resultCount') || {}).textContent || '0').replace(/\D/g, '')),
    cards: document.querySelectorAll('#grid .card').length,
  }));
  ok(kw.n > 0 && kw.cards > 0, '关键词搜索不受影响（' + kw.n + ' 条）');

  /* 不存在的编号 */
  await typeQ(pg, '9999999');
  const none = await pg.evaluate(() => ({ cards: document.querySelectorAll('#grid .card').length, empty: !!document.querySelector('#grid .empty') }));
  ok(none.cards === 0 && none.empty, '不存在的编号显示空状态', JSON.stringify(none));
  ok(errs.length === 0, '画廊无 JS 报错', errs.join(' | '));
  await pg.close();

  /* ---------- 手机端：搜索框可见 + 分类栏折叠 + 筛选只剩「仅看已收藏」 ---------- */
  pg = await b.newPage();
  const errsM = [];
  pg.on('pageerror', e => errsM.push(String(e)));
  await pg.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2600));
  const mob = await pg.evaluate(() => {
    const rt = document.querySelector('#railToggle');
    const rb = document.querySelector('#railBody');
    const s = document.querySelector('#galSearch').closest('.nav-search');
    return {
      toggleShown: !!rt && getComputedStyle(rt).display !== 'none',
      bodyHidden: rb ? getComputedStyle(rb).display === 'none' : false,
      searchShown: getComputedStyle(s).display !== 'none',
      searchW: Math.round(s.getBoundingClientRect().width),
      switches: [...document.querySelectorAll('#fxFilterBar .switch')].length,
    };
  });
  ok(mob.toggleShown && mob.bodyHidden, '手机端分类栏默认收起，只露标题', JSON.stringify(mob));
  ok(mob.searchShown && mob.searchW > 200, '手机端搜索框可见且占满宽度（' + mob.searchW + 'px）');
  ok(mob.switches === 1, '筛选只剩「仅看已收藏」（' + mob.switches + ' 个开关）');

  await pg.click('#railToggle');
  await new Promise(r => setTimeout(r, 450));
  const opened = await pg.evaluate(() => ({
    shown: getComputedStyle(document.querySelector('#railBody')).display !== 'none',
    expanded: document.querySelector('#railToggle').getAttribute('aria-expanded'),
  }));
  ok(opened.shown && opened.expanded === 'true', '点标题展开分类列表');

  await pg.evaluate(() => { const b2 = document.querySelector('#filterGroup .maj.leaf > button'); if (b2) b2.click(); });
  await new Promise(r => setTimeout(r, 1200));
  const collapsed = await pg.evaluate(() => ({
    hidden: getComputedStyle(document.querySelector('#railBody')).display === 'none',
    count: (document.querySelector('#resultCount') || {}).textContent || '',
  }));
  ok(collapsed.hidden, '选完分类后自动收起（' + collapsed.count + '）');
  ok(errsM.length === 0, '手机端无 JS 报错', errsM.join(' | '));
  await pg.close();

  /* ---------- 详情页：编号 / 旧 id ---------- */
  pg = await b.newPage();
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'detail.html?id=' + mid.seq, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2200));
  const d1 = await pg.evaluate(() => {
    const tags = [...document.querySelectorAll('.lb-tags .tag')].map(t => t.textContent.trim());
    return { title: (document.querySelector('.lb-title') || {}).textContent || '', idTag: tags.find(t => /^ID #/.test(t)) || '' };
  });
  ok(d1.title && !/没有找到/.test(d1.title), '用编号打开详情页正常：' + d1.title.slice(0, 12));
  ok(d1.idTag === 'ID #' + mid.seq, '详情页 ID 标签 = #' + mid.seq, d1.idTag);

  await pg.goto(BASE + 'detail.html?id=' + mid.id, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2000));
  const d2 = await pg.evaluate(() => (document.querySelector('.lb-title') || {}).textContent || '');
  ok(d2 === d1.title, '旧链接（内部 id ' + mid.id + '）仍能打开同一条');

  await pg.goto(BASE + 'detail.html?id=11820', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2000));
  const nf = await pg.evaluate(() => ({
    h1: (document.querySelector('.lb-title') || {}).textContent || '',
    hasBack: !!document.querySelector('#detailMount a[href="gallery.html"].btn'),
  }));
  ok(/没有找到/.test(nf.h1), '无效编号显示「没有找到这条提示词」', nf.h1);
  ok(nf.hasBack, '提供返回画廊按钮');
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
