/* 新分类「New欧美」导入验收：总数 / 分类入口 / 筛选 / 多图计数 / 新图能否从 R2 加载 */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  /* 首页总数 */
  let pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'index.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const home = await pg.evaluate(() => ({
    all: window.App.ALL.length,
    total: window.App.D.total,
    majors: window.App.D.majors.length,
    subs: window.App.D.subCount,
    countTexts: [...document.querySelectorAll('[data-sx-count="total"]')].map(x => x.textContent.trim()),
    lead: (document.querySelector('.hero .lead') || {}).textContent || '',
  }));
  const fmt = n => Number(n).toLocaleString('en-US');
  ok(home.total === home.all && home.total > 0, '数据总数一致=' + home.total + '（App.ALL ' + home.all + '）');
  ok(home.majors > 0 && home.subs > 0, home.majors + ' 大类 / ' + home.subs + ' 小类');
  ok(home.countTexts.every(t => t === fmt(home.total)), '页面总数占位符 = ' + fmt(home.total) + '：' + home.countTexts.join('|'));
  ok(home.lead.indexOf(fmt(home.total)) >= 0 && home.lead.indexOf(home.majors + ' 大分类') >= 0, '首页导语数字与数据一致：' + home.lead.slice(0, 46));
  ok(errs.length === 0, '首页无 JS 报错', errs.join(' | '));
  await pg.close();

  /* 画廊：New欧美 入口 + 多图计数 */
  pg = await b.newPage();
  const errs2 = [];
  pg.on('pageerror', e => errs2.push(String(e)));
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));
  const rail = await pg.evaluate(() => {
    const leaf = document.querySelector('#filterGroup .maj.leaf');
    const multi = document.querySelector('#filterGroup .maj.multi');
    return {
      leafExists: !!leaf,
      leafLabel: leaf ? leaf.textContent.replace(/\s+/g, ' ').trim() : '',
      leafMaj: leaf ? leaf.dataset.maj : '',
      multiLabel: multi ? multi.textContent.replace(/\s+/g, ' ').trim() : '',
      allMajors: [...document.querySelectorAll('#filterGroup .maj:not(.multi)')].length,
      leafCount: (window.App.D.majors.find(m => m.name === 'New欧美') || {}).count || 0,
      multiExpect: window.App.ALL.filter(window.App.isMulti).length,
      multiFmt: Number(window.App.ALL.filter(window.App.isMulti).length).toLocaleString('en-US'),
    };
  });
  ok(rail.leafExists && rail.leafMaj === 'New欧美', '左栏出现大类入口「New欧美」', JSON.stringify(rail));
  ok(rail.leafLabel.indexOf(String(rail.leafCount)) >= 0, '「New欧美」计数 ' + rail.leafCount + '：' + rail.leafLabel);

  await pg.click('#filterGroup .maj.leaf > button');
  await new Promise(r => setTimeout(r, 1500));
  const filtered = await pg.evaluate(() => ({
    count: (document.querySelector('#resultCount') || {}).textContent || '',
    cards: document.querySelectorAll('#grid .card').length,
    active: !!document.querySelector('.maj.leaf > button.active'),
    badges: document.querySelectorAll('#grid .multi-badge').length,
  }));
  ok(filtered.count.replace(/[^0-9]/g, '') === String(rail.leafCount), '点「New欧美」结果数 = ' + rail.leafCount, filtered.count);
  ok(filtered.active, '按钮呈选中态');
  ok(filtered.badges > 0 && filtered.badges <= filtered.cards, '该分类下多图角标 ' + filtered.badges + '/' + filtered.cards);

  // 多图虚拟分类的计数（814 + 203 = 1017）
  const multiLabel = rail.multiLabel;
  ok(multiLabel.indexOf(String(rail.multiExpect)) >= 0, '「多图」入口计数=' + rail.multiExpect + '：' + multiLabel);
  ok(errs2.length === 0, '画廊无 JS 报错', errs2.join(' | '));
  await pg.close();

  /* 新条目详情 + R2 图片是否真的加载 */
  pg = await b.newPage();
  const r2 = {};
  pg.on('response', r => { const u = r.url(); if (u.includes('r2.qqsrc.com/images/shuixian/')) r2[r.status()] = (r2[r.status()] || 0) + 1; });
  await pg.setViewport({ width: 1440, height: 900 });
  // 先拿到一条「New欧美」里的多图条目，别写死 id
  await pg.goto(BASE + 'gallery.html?cat=' + encodeURIComponent('New欧美'), { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const multiId = await pg.evaluate(() => {
    const s = window.App.ALL.find(x => x.category === 'New欧美' && window.App.isMulti(x));
    return s ? s.id : null;
  });
  ok(multiId != null, '「New欧美」里有多图条目，取到 id=' + multiId);
  await pg.goto(BASE + 'detail.html?id=' + multiId, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 4000));
  const det = await pg.evaluate(() => {
    const img = document.querySelector('#dImg img.ph-img');
    const title = (document.querySelector('.lb-title') || {}).textContent || '';
    const tags = [...document.querySelectorAll('.lb-tags .tag')].map(x => x.textContent.trim());
    return {
      title: title.trim(),
      hasImg: !!img,
      loaded: img ? img.naturalWidth > 0 : false,
      src: img ? img.src : '',
      tags,
      thumbs: document.querySelectorAll('#dImg .lb-thumbs .lb-thumb').length,
    };
  });
  ok(det.title.length > 0, '详情页有标题：' + det.title.slice(0, 24));
  ok(det.tags.some(t => t.includes('New欧美')), '分类标签显示 New欧美', det.tags.join(','));
  ok(det.hasImg && det.loaded, '主图从 R2 成功加载', det.src);
  ok(det.thumbs >= 2, '多图条目缩略条 ' + det.thumbs + ' 张');
  ok((r2[200] || 0) > 0 && !r2[403] && !r2[404], 'R2 图片响应正常：' + JSON.stringify(r2));
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
