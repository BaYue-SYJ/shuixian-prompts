/* 灯箱修复在多页面的一致性验证：index / gallery / search / categories / favorites / detail
 * 每个页面在手机视口打开一条提示词，验证「正文可滚 + 图片区不可内层滚」。
 */
const p = require('puppeteer-core');

// categories.html 只是分类入口、点进去就跳 gallery.html（已单独验证），
// 这里换成 detail.html —— 它用 ?id= 直接开灯箱，是灯箱的另一条入口路径。
const PAGES = ['index.html', 'gallery.html', 'search.html', 'detail.html', 'favorites.html'];
let pass = 0, fail = 0; const bad = [];
function ok(c, m) { if (c) pass++; else { fail++; bad.push(m); } }

// 收藏页需要先塞一条收藏记录，否则空页没有卡片可点（上一版因此误报）
// 结构见 js/base.js：{ boards:[{id, name, items:[id...]}], active:'<boardId>' }
const SEED_FAV = async (pg) => {
  await pg.evaluateOnNewDocument(() => {
    try {
      localStorage.setItem('sx-boards-v2', JSON.stringify({
        boards: [{ id: 'b1', name: '默认画板', items: [18850] }],
        active: 'b1',
      }));
    } catch (e) { }
  });
};
// 分类页没有卡片；detail.html 用 ?id= 直接开箱
const gotoFor = (page) => {
  if (page === 'detail.html') return 'detail.html?id=18850';
  return page;
};

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  for (const page of PAGES) {
    const pg = await b.newPage();
    const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.setViewport({ width: 390, height: 800, isMobile: true, deviceScaleFactor: 1, hasTouch: true });
    if (page === 'favorites.html') await SEED_FAV(pg);
    await pg.goto('http://127.0.0.1:8140/' + gotoFor(page), { waitUntil: 'networkidle2', timeout: 60000 });
    await new Promise(r => setTimeout(r, 2500));

    // detail.html 用 ?id= 直接开灯箱；其余页面点第一张卡
    const opened = await pg.evaluate(async () => {
      const lb = document.querySelector('#sx-lightbox');
      if (lb && lb.classList.contains('open')) return 'already';
      const c = document.querySelector('.card, .home-card');
      if (!c) return 'no-card';
      c.click();
      await new Promise(r => setTimeout(r, 1200));
      return document.querySelector('#sx-lightbox') && document.querySelector('#sx-lightbox').classList.contains('open') ? 'ok' : 'not-open';
    }).catch(e => 'eval-err:' + e.message.slice(0, 60));
    await new Promise(r => setTimeout(r, 1200));

    if (opened !== 'ok' && opened !== 'already') {
      ok(false, `${page}: 无法打开灯箱（${opened}）`);
      await pg.close(); continue;
    }

    const m = await pg.evaluate(() => {
      const body = document.querySelector('#sx-lightbox .lb-body');
      const img = document.querySelector('#sx-lightbox .lb-img');
      const pan = document.querySelector('#sx-lightbox .lb-panel');
      if (!body || !img || !pan) return null;
      const ov = getComputedStyle(img).overflow;
      img.scrollTop = 500; const imgAfter = img.scrollTop; img.scrollTop = 0;
      body.scrollTop = 0;
      const maxScroll = body.scrollHeight - body.clientHeight;
      body.scrollTop = 999999; const reached = body.scrollTop; const lim = maxScroll;
      return {
        bodyOverflowY: getComputedStyle(body).overflowY,
        maxScroll, reached,
        imgOverflow: ov, imgAfter,
        panBottom: Math.round(pan.getBoundingClientRect().bottom),
        vh: innerHeight,
      };
    });

    if (!m) { ok(false, `${page}: 灯箱 DOM 缺失`); await pg.close(); continue; }

    console.log(`${page.padEnd(18)} body.overflowY=${m.bodyOverflowY.padEnd(5)} 可滚=${String(m.maxScroll).padStart(4)}px 实达=${String(m.reached).padStart(4)}px  img.overflow=${m.imgOverflow} img强滚=${m.imgAfter}  面板底=${m.panBottom}/视口=${m.vh}`);
    ok(m.bodyOverflowY === 'auto', `${page}: .lb-body overflowY=${m.bodyOverflowY}`);
    ok(m.maxScroll <= 0 || m.reached > 0, `${page}: 正文有内容但滚不动`);
    ok(m.imgAfter === 0, `${page}: 图片区可内层滚动（scrollTop=${m.imgAfter}）`);
    ok(m.panBottom <= m.vh + 1, `${page}: 面板底边 ${m.panBottom} 超出视口 ${m.vh}`);
    ok(errs.length === 0, `${page}: 页面报错 ${errs.join(' | ')}`);
    await pg.close();
  }

  await b.close();
  console.log(`\n================ 结果 ================`);
  console.log(`通过 ${pass} / 失败 ${fail}`);
  if (bad.length) { console.log('失败项：'); bad.forEach(x => console.log('  ✗ ' + x)); }
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(2); });
