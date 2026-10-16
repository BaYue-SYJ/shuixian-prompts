// 临时：截修复页 + 取关键元素坐标，供 Pillow 标注
const puppeteer = require('puppeteer-core');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = process.env.SX_URL || 'http://127.0.0.1:8140';
const fs = require('fs');
const OUT = 'C:/Users/lianxiang/WorkBuddy/2026-07-23-09-09-54/shuixian-unified-0920/tools';

const rect = (page, sel) => page.evaluate((s) => {
  const el = document.querySelector(s);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
}, sel);

const rectByText = (page, parent, text) => page.evaluate((p, t) => {
  const root = document.querySelector(p);
  if (!root) return null;
  const els = [...root.querySelectorAll('*')];
  const hit = els.find(e => e.children.length === 0 && e.textContent.trim() === t) ||
              els.find(e => e.textContent.includes(t) && e.offsetHeight < 200 && e.offsetWidth < 400);
  if (!hit) return null;
  const r = hit.getBoundingClientRect();
  return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
}, parent, text);

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  const out = { index: {}, gallery: {} };

  // ---------- 首页：Issue 1（杂项卡）----------
  await page.setViewport({ width: 1440, height: 1700 });
  await page.goto(BASE + '/index.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('#catGrid .card, #catGrid a, #catGrid > *', { timeout: 15000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 500));
  out.index.zaCard = await rectByText(page, '#catGrid', '杂项');
  out.index.whole = await rect(page, '#catGrid');
  await page.screenshot({ path: OUT + '/_shot_index.png' });

  // ---------- 画廊：Issue 2/3/4 ----------
  await page.setViewport({ width: 1440, height: 1080 });
  await page.goto(BASE + '/gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('#grid .m-col', { timeout: 15000 });
  await page.waitForSelector('#fxFacetHost .facet-chip[data-n]', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 500));
  // 点第一颗 facet chip 制造 .on 高亮（Issue 3 演示）
  await page.evaluate(() => { const c = document.querySelector('#fxFacetHost .facet-chip[data-n]'); if (c) c.click(); });
  await new Promise(r => setTimeout(r, 300));
  out.gallery.sortSel = await rect(page, '#sortSel');
  out.gallery.facetOn = await rect(page, '#fxFacetHost .facet-chip.on');
  out.gallery.grid = await rect(page, '#grid');
  out.gallery.showMore = await rect(page, '#showMore');
  out.gallery.sortValue = await page.evaluate(() => { const s = document.querySelector('#sortSel'); return s ? s.value : null; });
  out.gallery.cols = await page.evaluate(() => document.querySelectorAll('#grid .m-col').length);
  await page.screenshot({ path: OUT + '/_shot_gallery.png' });

  fs.writeFileSync(OUT + '/_shot_fixes.json', JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  await browser.close();
})();
