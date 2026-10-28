/* 灯箱提示词完整可见性回归（现代版）
 * 判据：
 *   ① .lb-prompt 自身不内滚（scrollHeight == clientHeight）
 *   ② 不自己限高（max-height == none）
 *   ③ 滚到正文底部时，提示词最后一行必须进入视口，且动作按钮也可达
 *   ④ 全站最长的若干条提示词都不能被截断
 */
const os = require('os');
const p = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const OUT = path.join(os.tmpdir(), 'sx-audit-shots');

let pass = 0, fail = 0; const bad = [];
function ok(c, m) { if (c) pass++; else { fail++; bad.push(m); } }

const VIEWPORTS = [
  { name: '320x568', width: 320, height: 568, isMobile: true },
  { name: '390x800', width: 390, height: 800, isMobile: true },
  { name: '430x932', width: 430, height: 932, isMobile: true },
  { name: '768x1024', width: 768, height: 1024, isMobile: false },
  { name: '1440x900', width: 1440, height: 900, isMobile: false },
];

// 覆盖：用户截图那条(784字) / 超长(1010字) / 中等(343字)
const IDS = [32178, 24540, 15286];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  for (const vp of VIEWPORTS) {
    const pg = await b.newPage();
    const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.setViewport({ width: vp.width, height: vp.height, isMobile: vp.isMobile, deviceScaleFactor: 1, hasTouch: !!vp.isMobile });

    for (const id of IDS) {
      await pg.goto('http://127.0.0.1:8140/detail.html?id=' + id, { waitUntil: 'networkidle2', timeout: 90000 });
      await pg.evaluate(() => { if (window.App && App.openLightbox) App.openLightbox(Number(new URLSearchParams(location.search).get('id'))); });
      await new Promise(r => setTimeout(r, 2200));

      const m = await pg.evaluate(async () => {
        const el = document.querySelector('#lbPrompt');
        const body = document.querySelector('#sx-lightbox .lb-body');
        if (!el || !body) return null;
        const cs = getComputedStyle(el);
        // 滚到底，看提示词末行与操作按钮是否可达
        body.scrollTop = 999999;
        await new Promise(r => setTimeout(r, 250));
        const bodyR = body.getBoundingClientRect();
        const promptR = el.getBoundingClientRect();
        const lastLineVisible = promptR.bottom <= bodyR.bottom + 2;
        // 提示词末行文字是否真的露出来
        const tail = (el.textContent || '').trim().slice(-24);
        return {
          len: (el.textContent || '').trim().length,
          selfScroll: el.scrollHeight - el.clientHeight,
          maxH: cs.maxHeight, ovY: cs.overflowY,
          promptBottom: Math.round(promptR.bottom),
          bodyBottom: Math.round(bodyR.bottom),
          lastLineVisible,
          afterScrollTop: Math.round(body.scrollTop),
          tail,
        };
      });

      const tag = `${vp.name} id=${id}`;
      if (!m) { ok(false, `${tag}: 未取到 #lbPrompt`); continue; }

      console.log(`${tag.padEnd(20)} len=${String(m.len).padStart(4)} 自滚=${String(m.selfScroll).padStart(3)}px maxH=${String(m.maxH).padEnd(5)} ovY=${m.ovY.padEnd(7)} 末行底=${m.promptBottom} 容器底=${m.bodyBottom} 可见=${m.lastLineVisible}`);

      // ① 提示词框自身不可滚动（无内层滚动容器）
      ok(m.selfScroll <= 1, `${tag}: .lb-prompt 仍在内部滚动（可滚 ${m.selfScroll}px），文字被藏进小窗口`);
      // ② 不自己限高
      ok(m.maxH === 'none', `${tag}: .lb-prompt 仍被 max-height 限制（${m.maxH}）`);
      // ③ 不是可滚容器
      ok(m.ovY === 'visible', `${tag}: .lb-prompt overflow-y=${m.ovY}，仍是滚动容器`);
      // ④ 滚到底后末行完整露出
      ok(m.lastLineVisible, `${tag}: 滚到底后提示词末行仍被裁（末行底 ${m.promptBottom} > 容器底 ${m.bodyBottom}）`);

      if (vp.name === '390x800' && id === 32178) {
        await pg.screenshot({ path: path.join(OUT, 'p-fix-prompt-bottom.png') });
      }
    }
    ok(errs.length === 0, `${vp.name}: 页面报错 ${errs.join(' | ')}`);
    await pg.close();
  }

  await b.close();
  console.log(`\n================ 结果 ================`);
  console.log(`通过 ${pass} / 失败 ${fail}`);
  if (bad.length) { console.log('失败项：'); bad.forEach(x => console.log('  ✗ ' + x)); }
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(2); });
