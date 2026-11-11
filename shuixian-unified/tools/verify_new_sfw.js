/* 新分类「New-SFW」验收：入口 / 计数 / 筛选 / 图片可加载 / 多图 / 详情 */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
const CAT = 'New-SFW';
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  /* ---------- 画廊：入口与计数 ---------- */
  let pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 1440, height: 1000 });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 90000 });
  await new Promise(r => setTimeout(r, 3200));

  const rail = await pg.evaluate(cat => {
    const leaf = document.querySelector(`#filterGroup .maj[data-maj="${cat}"]`);
    const maj = window.App.D.majors.find(m => m.name === cat) || {};
    return {
      exists: !!leaf,
      isLeaf: leaf ? leaf.classList.contains('leaf') : false,
      label: leaf ? leaf.textContent.replace(/\s+/g, ' ').trim() : '',
      count: maj.count || 0,
      total: window.App.ALL.length,
      majors: window.App.D.majors.length,
      color: (window.App.catColor && window.App.catColor(cat)) || null,
    };
  }, CAT);
  ok(rail.exists && rail.isLeaf, `左栏出现大类入口「${CAT}」`, JSON.stringify(rail));
  ok(rail.count === 309, `${CAT} 计数 = 309`, String(rail.count));
  ok(rail.label.includes('309'), '入口标签带数量：' + rail.label);
  ok(rail.total === 6320, '站点总数 = 6,320', String(rail.total));
  ok(rail.majors === 14, '大类共 14 个', String(rail.majors));
  ok(!!rail.color && /^#[0-9A-Fa-f]{6}$/.test(rail.color.main || ''), '分类有独立配色 ' + (rail.color && rail.color.main));

  /* ---------- 筛选 ---------- */
  await pg.click(`#filterGroup .maj[data-maj="${CAT}"] > button`);
  await new Promise(r => setTimeout(r, 2000));
  const filtered = await pg.evaluate(() => ({
    count: (document.querySelector('#resultCount') || {}).textContent || '',
    active: !!document.querySelector('.maj.leaf.active') || !!document.querySelector('.maj[data-maj="New-SFW"] button.active'),
    multi: document.querySelectorAll('#grid .card .multi-badge').length,
    cards: document.querySelectorAll('#grid .card').length,
  }));
  ok(filtered.count.replace(/\D/g, '') === '309', '筛选后 309 条', filtered.count);
  ok(filtered.active, '按钮呈选中态');
  ok(filtered.multi > 0, '分类内有多图角标（' + filtered.multi + ' 个）');

  /* ---------- 图片可用性（懒加载会干扰 naturalWidth，直接验 URL） ---------- */
  await pg.evaluate(() => window.scrollTo(0, 0));
  await new Promise(r => setTimeout(r, 1200));
  const imgs = await pg.evaluate(() => {
    const list = [...document.querySelectorAll('#grid .card img')].slice(0, 8);
    return list.map(i => i.currentSrc || i.src || i.getAttribute('data-src') || '');
  });
  ok(imgs.length > 0 && imgs.every(u => /r2\.qqsrc\.com\/images\/new-sfw\//.test(u)),
     '卡片图片全部指向 R2 的 images/new-sfw/', imgs[0] || '(空)');

  const https = require('https');
  const head = u => new Promise(res => {
    const req = https.request(u, { method: 'HEAD' }, r => { r.resume(); res(r.statusCode); });
    req.on('error', () => res(0)); req.setTimeout(15000, () => { req.destroy(); res(0); }); req.end();
  });
  const codes = [];
  for (const u of imgs.filter(Boolean).slice(0, 6)) codes.push(await head(u));
  ok(codes.length >= 6 && codes.every(c => c === 200), '前 6 张主图 HTTP 200（' + codes.join(',') + '）');

  /* ---------- 详情页 ---------- */
  const multiId = await pg.evaluate(() => {
    const s = window.App.ALL.find(x => x.category === 'New-SFW' && window.App.isMulti(x));
    return s ? s.id : null;
  });
  ok(multiId != null, '分类里有多图条目 id=' + multiId);

  await pg.goto(BASE + 'detail.html?id=' + multiId, { waitUntil: 'networkidle2', timeout: 90000 });
  await new Promise(r => setTimeout(r, 2600));
  const det = await pg.evaluate(() => {
    const img = document.querySelector('#dImg img');
    const tags = [...document.querySelectorAll('.lb-tags .tag')].map(t => t.textContent.trim());
    return {
      title: (document.querySelector('.lb-title') || {}).textContent || '',
      imgOk: img ? img.naturalWidth > 0 : false,
      tags,
      thumbs: document.querySelectorAll('.lb-thumbs img, .lb-thumbs button').length,
      promptLen: ((document.querySelector('#dPrompt') || {}).textContent || '').length,
    };
  });
  ok(det.title.length > 0, '详情页有标题：' + det.title.slice(0, 14));
  ok(det.imgOk, '详情页主图从 R2 正常显示');
  ok(det.tags.some(t => t.includes(CAT)), '分类标签显示 ' + CAT, det.tags.join(','));
  ok(det.thumbs >= 2, '多图缩略条 ≥2 张（' + det.thumbs + '）');
  ok(det.promptLen > 100, '正文完整（' + det.promptLen + ' 字）');
  ok(errs.length === 0, '无 JS 报错', errs.slice(0, 2).join(' | '));
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
