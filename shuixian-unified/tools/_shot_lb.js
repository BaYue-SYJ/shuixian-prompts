// 临时：截灯箱（v16 两项交互修复）+ 取关键元素坐标
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

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1080 });
  await page.goto(BASE + '/gallery.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await page.waitForSelector('#grid .m-col', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 500));
  // 点第一张卡开灯箱
  await page.evaluate(() => { const c = document.querySelector('#grid .card'); if (c) c.click(); });
  await page.waitForSelector('.lb-panel', { timeout: 15000 });
  await page.waitForSelector('.lb-img-nav .lb-prev', { timeout: 15000 });
  await new Promise(r => setTimeout(r, 700));
  const out = {
    prev: await rect(page, '.lb-nav.lb-prev'),
    next: await rect(page, '.lb-nav.lb-next'),
    count: await rect(page, '.lb-count'),
    dice: await rect(page, '.dice-btn'),
  };
  await page.screenshot({ path: OUT + '/_shot_lb.png' });
  fs.writeFileSync(OUT + '/_shot_lb.json', JSON.stringify(out, null, 2));
  console.log(JSON.stringify(out, null, 2));
  await browser.close();
})();
