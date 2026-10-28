// 回归测试：分面筛选 chip 点击高亮 + 计数联动
// 根因：① renderFacets 的 chip 点击只调 toggleFacet + onChange，从不切 .on 类；
//       ② gallery.html 的 __fxGalleryRefresh 只重绘卡片不重建分面 → 高亮永不出现；
//       ③ search.html 缺 __fxFacetPool / __fxGalleryRefresh → 分面点击完全失效。
// 修复：renderFacets 点击时立即切 .on；search.html 补齐两个全局钩子。
// 运行：NODE_PATH=... node verify_facets.js   （依赖 puppeteer-core + 本地 8140 服务）
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.SX_URL || 'http://127.0.0.1:8140';
let fail = 0;

function check(name, cond, extra) { console.log((cond ? 'PASS' : 'FAIL') + ' ' + name + (extra ? '  ' + extra : '')); if (!cond) fail++; }

async function waitFacets(page) {
  await page.waitForSelector('#fxFacetHost .facet-chip[data-n]', { timeout: 30000 });
}
// 真正的「筛选后总数」：用页面内的 FX.applyFilters(__fxFacetPool()) 计算，不依赖展示文案
function totalCount(page) {
  return page.evaluate(() => {
    const pool = (typeof window.__fxFacetPool === 'function') ? window.__fxFacetPool() : (window.App && window.App.ALL) || [];
    return window.FX ? window.FX.applyFilters(pool).length : -1;
  });
}
// 点击计数最小的 chip（最稀有标签），保证筛选后总数必然下降；返回该 chip 的标签数
function clickRarest(page) {
  return page.evaluate(() => {
    const chips = [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')];
    let best = null, bn = Infinity;
    for (const c of chips) { const n = +c.querySelector('.n').textContent; if (n < bn) { bn = n; best = c; } }
    if (best) best.click();
    return best ? bn : -1;
  });
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });

  // ---------- 画廊页：分面块已按需求移除（回归：不得再出现）----------
  {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto(BASE + '/gallery.html?cat=' + encodeURIComponent('城市海报'), { waitUntil: 'networkidle2', timeout: 60000 });
    await page.waitForSelector('#grid .m-col', { timeout: 15000 }).catch(() => {});
    await new Promise(r => setTimeout(r, 800));
    const facetHost = await page.evaluate(() => !!document.querySelector('#fxFacetHost'));
    const filterBar = await page.evaluate(() => !!document.querySelector('#fxFilterBar'));
    check('[gallery] 分面块已移除（无 #fxFacetHost）', facetHost === false);
    check('[gallery] 筛选开关条仍保留（有 #fxFilterBar）', filterBar === true);
    await page.close();
  }

  // ---------- 搜索页 ----------
  {
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    await page.goto(BASE + '/search.html', { waitUntil: 'networkidle2', timeout: 60000 });
    await page.waitForSelector('#bigSearch', { timeout: 30000 });
    await page.type('#bigSearch', '海报');
    await page.click('#goBtn');
    await waitFacets(page);
    await new Promise(r => setTimeout(r, 900));
    const before = await totalCount(page);
    const bn = await clickRarest(page);
    await new Promise(r => setTimeout(r, 350));
    const onAfter = await page.evaluate(() => !!document.querySelector('#fxFacetHost .facet-chip.on'));
    const onCount = await page.evaluate(() => document.querySelectorAll('#fxFacetHost .facet-chip.on').length);
    const after = await totalCount(page);
    check('[search] 点击后 .on 高亮出现', onAfter === true);
    check('[search] 点击后 .on 数量=1', onCount === 1, 'on=' + onCount);
    check('[search] 筛选后总数下降', after < before, 'before=' + before + ' after=' + after + ' chipN=' + bn);
    check('[search] 筛选后总数=被点 chip 计数', after === bn, 'after=' + after + ' chipN=' + bn);
    await page.close();
  }

  await browser.close();
  console.log(fail === 0 ? '\nALL PASS' : '\n' + fail + ' FAILED');
  process.exit(fail === 0 ? 0 : 1);
})().catch(e => { console.error('ERR', e); process.exit(2); });
