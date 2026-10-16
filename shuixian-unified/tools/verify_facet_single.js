// 回归：分面筛选「每组最多选一个」——同组再点别的要清掉前一个；跨组各选一个互不干扰
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.SX_URL || 'http://127.0.0.1:8140';

let pass = 0, fail = 0;
const ok = (n, c, ex) => { if (c) { pass++; console.log('  ✅', n); } else { fail++; console.log('  ❌', n, ex != null ? '→ ' + JSON.stringify(ex) : ''); } };

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(BASE + '/gallery.html?cat=' + encodeURIComponent('城市海报'), { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('#fxFacetHost .facet-chip', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 400));

  // 取第一个分面组（媒介）的两颗 chip
  const firstGroup = await page.evaluate(() => {
    const frow = document.querySelector('#fxFacetHost .frow');
    const chips = [...frow.querySelectorAll('.facet-chip[data-n]')];
    return { facet: chips[0].dataset.f, names: chips.slice(0, 2).map(c => c.dataset.n) };
  });

  // 点第一颗
  await page.evaluate(n => [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')].find(c => c.dataset.n === n).click(), firstGroup.names[0]);
  await new Promise(r => setTimeout(r, 150));
  const afterFirst = await page.evaluate(() => document.querySelectorAll('#fxFacetHost .facet-chip.on').length);

  // 同组点第二颗（应清掉第一颗）
  await page.evaluate(n => [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')].find(c => c.dataset.n === n).click(), firstGroup.names[1]);
  await new Promise(r => setTimeout(r, 150));
  const afterSecond = await page.evaluate((f, n1, n2) => {
    const on = [...document.querySelectorAll('#fxFacetHost .facet-chip.on')];
    const inGroup = [...document.querySelectorAll('#fxFacetHost .facet-chip[data-f="' + f + '"]')];
    return {
      totalOn: on.length,
      groupOnCount: inGroup.filter(c => c.classList.contains('on')).length,
      firstOff: !inGroup.find(c => c.dataset.n === n1).classList.contains('on'),
      secondOn: !!inGroup.find(c => c.dataset.n === n2).classList.contains('on'),
    };
  }, firstGroup.facet, firstGroup.names[0], firstGroup.names[1]);

  // 再点第二颗（取消）
  await page.evaluate(n => [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')].find(c => c.dataset.n === n).click(), firstGroup.names[1]);
  await new Promise(r => setTimeout(r, 150));
  const afterToggleOff = await page.evaluate(() => document.querySelectorAll('#fxFacetHost .facet-chip.on').length);

  // 跨组：再选第一组一颗 + 第二组一颗
  const cross = await page.evaluate(() => {
    const groups = [...document.querySelectorAll('#fxFacetHost .frow')];
    const g0 = groups[0].querySelector('.facet-chip[data-n]').dataset.n;
    const g1 = groups[1].querySelector('.facet-chip[data-n]').dataset.n;
    [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')].find(c => c.dataset.n === g0).click();
    [...document.querySelectorAll('#fxFacetHost .facet-chip[data-n]')].find(c => c.dataset.n === g1).click();
    return { g0, g1 };
  });
  await new Promise(r => setTimeout(r, 150));
  const afterCross = await page.evaluate(() => document.querySelectorAll('#fxFacetHost .facet-chip.on').length);

  console.log('\n断言：');
  ok('点第一颗后 高亮=1', afterFirst === 1, afterFirst);
  ok('同组点第二颗后 总高亮仍=1', afterSecond.totalOn === 1, afterSecond);
  ok('同组仅 1 颗高亮', afterSecond.groupOnCount === 1, afterSecond);
  ok('第一颗已被取消', afterSecond.firstOff, afterSecond);
  ok('第二颗已选中', afterSecond.secondOn, afterSecond);
  ok('再点第二颗=取消（高亮归零）', afterToggleOff === 0, afterToggleOff);
  ok('跨组各选一 高亮=2（互不干扰）', afterCross === 2, afterCross);
  ok('无页面错误', errors.length === 0, errors.slice(0, 3));

  await browser.close();
  console.log('\n结果：%d PASS / %d FAIL', pass, fail);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('ERR', e); process.exit(2); });
