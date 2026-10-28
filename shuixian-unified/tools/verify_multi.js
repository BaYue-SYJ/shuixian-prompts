/* 多图能力回归：卡片角标 / 画廊「多图」分类 / 详情页与灯箱缩略图 / 动作条与备注已删 */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  /* ---------- 首页：卡片角标 ---------- */
  let pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'index.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const home = await pg.evaluate(() => {
    const cards = [...document.querySelectorAll('#featuredGrid .card')];
    const badges = [...document.querySelectorAll('#featuredGrid .multi-badge')];
    // 逐卡核对：多图必带角标，单图必无角标（首页是随机 12 张，不能假设一定有）
    let mismatch = [];
    cards.forEach(c => {
      const id = +c.dataset.id;
      const s = window.App.findSample(id);
      const want = window.App.isMulti(s);
      const has = !!c.querySelector('.multi-badge');
      if (want !== has) mismatch.push(id + ':' + want + '/' + has);
    });
    const sample = badges[0];
    const rect = sample ? sample.getBoundingClientRect() : null;
    const host = sample ? sample.closest('.thumb').getBoundingClientRect() : null;
    return {
      cards: cards.length, badges: badges.length,
      wantMulti: cards.filter(c => window.App.isMulti(window.App.findSample(+c.dataset.id))).length,
      badgeText: sample ? sample.textContent.trim() : '',
      mismatch,
      leftAligned: rect && host ? (rect.left - host.left) < 20 : null,
      bottomAligned: rect && host ? (host.bottom - rect.bottom) < 20 : null,
    };
  });
  ok(home.cards > 0, '首页卡片渲染 ' + home.cards + ' 张');
  ok(home.mismatch.length === 0, '角标与多图数据一一对应（' + home.wantMulti + ' 张多图 / ' + home.badges + ' 个角标）', home.mismatch.join(','));
  ok(home.badges === 0 || (home.leftAligned === true && home.bottomAligned === true),
    '角标位于图片区左下角' + (home.badges ? '' : '（本轮随机无多图，跳过位置）'), JSON.stringify(home).slice(0, 120));
  ok(errs.length === 0, '首页无 JS 报错', errs.join(' | '));
  await pg.close();

  /* ---------- 画廊：多图分类 + 筛选 ---------- */
  pg = await b.newPage();
  const errs2 = [];
  pg.on('pageerror', e => errs2.push(String(e)));
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));
  const rail = await pg.evaluate(() => {
    const m = document.querySelector('#filterGroup .maj.multi');
    return { exists: !!m, label: m ? m.textContent.replace(/\s+/g, ' ').trim() : '', first: document.querySelector('#filterGroup .maj') === m };
  });
  ok(rail.exists, '左侧分类栏出现「多图」入口', JSON.stringify(rail));
  ok(rail.first === true, '「多图」排在分类列表最前');
  await pg.click('#filterGroup .maj.multi > button');
  await new Promise(r => setTimeout(r, 1200));
  const filtered = await pg.evaluate(() => ({
    count: (document.querySelector('#resultCount') || {}).textContent || '',
    cards: document.querySelectorAll('#grid .card').length,
    active: !!document.querySelector('#filterGroup .maj.multi > button.active'),
    badges: document.querySelectorAll('#grid .multi-badge').length,
    expect: window.App.ALL.filter(window.App.isMulti).length,
  }));
  ok(filtered.count.replace(/[^0-9]/g, '') === String(filtered.expect), '点「多图」后结果数 = ' + filtered.expect, filtered.count);
  ok(filtered.active === true, '「多图」按钮呈选中态');
  ok(filtered.cards > 0, '筛选后仍有卡片 ' + filtered.cards + ' 张');
  ok(filtered.badges === filtered.cards, '「多图」分类下每张卡都带角标（' + filtered.badges + '/' + filtered.cards + '）');
  ok(errs2.length === 0, '画廊无 JS 报错', errs2.join(' | '));
  await pg.close();

  /* ---------- 详情页：多图缩略图切换 ---------- */
  pg = await b.newPage();
  const errs3 = [];
  pg.on('pageerror', e => errs3.push(String(e)));
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'detail.html?id=30001', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3500));
  const lbMulti = await pg.evaluate(() => {
    const wrap = document.querySelector('#dImg');
    const strip = wrap ? wrap.querySelector('.lb-thumbs') : null;
    return {
      thumbs: strip ? strip.querySelectorAll('.lb-thumb').length : 0,
      firstSrc: (wrap.querySelector('img.ph-img') || {}).src || '',
      actBar: !!document.querySelector('.act-bar'),
      noteBox: !!document.querySelector('.note-box'),
      useText: /使用\s*\d+\s*次/.test((document.body || {}).textContent || ''),
    };
  });
  ok(lbMulti.thumbs >= 2, '详情页多图出现缩略图条（' + lbMulti.thumbs + ' 张）', JSON.stringify(lbMulti));
  ok(lbMulti.actBar === false, '详情页无迷你动作条（填变量并复制等）');
  ok(lbMulti.noteBox === false, '详情页无「我的备注」');
  ok(lbMulti.useText === false, '详情页无「使用 N 次」');

  await pg.click('#dImg .lb-thumbs .lb-thumb:nth-child(2)');
  await new Promise(r => setTimeout(r, 1200));
  const switched = await pg.evaluate(() => ({
    src: (document.querySelector('#dImg img.ph-img') || {}).src || '',
    on2: document.querySelectorAll('#dImg .lb-thumbs .lb-thumb')[1].classList.contains('on'),
  }));
  ok(switched.src !== lbMulti.firstSrc && switched.on2, '点第 2 张缩略图主图已切换', JSON.stringify(switched).slice(0, 160));
  ok(errs3.length === 0, '详情页无 JS 报错', errs3.join(' | '));
  await pg.close();

  /* ---------- 画廊灯箱：同样有缩略图条 ---------- */
  pg = await b.newPage();
  await pg.setViewport({ width: 1440, height: 900 });
  await pg.goto(BASE + 'gallery.html?cat=' + encodeURIComponent('多图'), { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));
  await pg.evaluate(() => document.querySelector('#grid .card').click());
  await new Promise(r => setTimeout(r, 3000));
  const lbStrip = await pg.evaluate(() => ({
    open: !!document.querySelector('#sx-lightbox.open'),
    thumbs: document.querySelectorAll('#sx-lightbox .lb-img .lb-thumbs .lb-thumb').length,
    note: !!document.querySelector('#sx-lightbox .note-box'),
  }));
  ok(lbStrip.open === true, '画廊点卡片能打开灯箱');
  ok(lbStrip.thumbs >= 2, '灯箱内出现缩略图条（' + lbStrip.thumbs + ' 张）');
  ok(lbStrip.note === false, '灯箱内无备注框');
  await pg.close();

  /* ---------- 单图：不应有缩略图条 / 角标 ---------- */
  pg = await b.newPage();
  await pg.goto(BASE + 'detail.html?id=14347', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));
  const single = await pg.evaluate(() => ({
    thumbs: document.querySelectorAll('.lb-thumbs').length,
    img: !!document.querySelector('#dImg img.ph-img'),
  }));
  ok(single.thumbs === 0, '单图提示词不显示缩略图条');
  ok(single.img === true, '单图主图正常显示');
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
