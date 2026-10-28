/* 详情页版式：正文列高度不得超过图片列，超出在正文列内滚动（窄屏除外） */
const p = require('puppeteer-core');
const BASE = 'http://127.0.0.1:8140/';
const LONG_ID = 36209;   // 12k 字长提示词，最容易把右列撑高

let pass = 0, fail = 0;
const ok = (c, m, x) => { if (c) { pass++; console.log('  OK   ' + m); } else { fail++; console.log('  FAIL ' + m + (x ? '  → ' + x : '')); } };

(async () => {
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });

  for (const vp of [{ w: 1440, h: 900, name: '1440x900' }, { w: 1024, h: 800, name: '1024x800' }]) {
    const pg = await b.newPage();
    const errs = [];
    pg.on('pageerror', e => errs.push(String(e)));
    await pg.setViewport({ width: vp.w, height: vp.h });
    await pg.goto(BASE + 'detail.html?id=' + LONG_ID, { waitUntil: 'networkidle2', timeout: 60000 });
    await new Promise(r => setTimeout(r, 3500));
    const g = await pg.evaluate(() => {
      const img = document.querySelector('#dImg');
      const body = document.querySelector('.detail-body');
      const panel = document.querySelector('.detail-panel');
      const prompt = document.querySelector('.detail-body > .lb-prompt');
      const acts = document.querySelector('.detail-body > .lb-actions');
      const tip = document.querySelector('.detail-body > p');
      const b = body.getBoundingClientRect(), i = img.getBoundingClientRect();
      const p = prompt.getBoundingClientRect();
      const a = acts.getBoundingClientRect(), t = tip ? tip.getBoundingClientRect() : null;
      return {
        imgH: Math.round(i.height), bodyH: Math.round(b.height),
        imgTop: Math.round(i.top), bodyTop: Math.round(b.top),
        bodyScrollH: body.scrollHeight, bodyClientH: body.clientHeight,
        bodyOverflowY: getComputedStyle(body).overflowY,
        maxHeight: body.style.maxHeight,
        panelH: Math.round(panel.getBoundingClientRect().height),
        promptH: Math.round(p.height), promptTop: Math.round(p.top), promptBottom: Math.round(p.bottom),
        promptScrollH: prompt.scrollHeight, promptClientH: prompt.clientHeight,
        promptOverflowY: getComputedStyle(prompt).overflowY,
        actsTop: Math.round(a.top), actsBottom: Math.round(a.bottom),
        tipBottom: t ? Math.round(t.bottom) : null,
        bodyBottom: Math.round(b.bottom),
      };
    });
    console.log('  [' + vp.name + '] 图片高=' + g.imgH + ' 正文高=' + g.bodyH +
      ' 提示词框高=' + g.promptH + '（内容 ' + g.promptScrollH + ' → 内部滚动）');
    ok(g.bodyH <= g.imgH + 2, `${vp.name}: 正文高度不超过图片（${g.bodyH} ≤ ${g.imgH}）`);
    ok(Math.abs(g.bodyTop - g.imgTop) <= 2, `${vp.name}: 两列顶部对齐`);
    // 外层不再滚：滚动条只出现在提示词框内部
    ok(g.bodyScrollH <= g.bodyClientH + 2, `${vp.name}: 正文列本身不滚动（无外层滚动条）`);
    ok(g.promptOverflowY === 'auto' || g.promptOverflowY === 'scroll', `${vp.name}: 提示词框可滚（overflow-y=${g.promptOverflowY}）`);
    ok(g.promptScrollH > g.promptClientH + 10, `${vp.name}: 长提示词在框内滚动（${g.promptScrollH} > ${g.promptClientH}）`);
    // 输入/按钮区始终完整可见、不被遮挡
    ok(g.actsTop >= g.promptBottom - 1, `${vp.name}: 按钮在提示词框下方，无重叠（${g.actsTop} ≥ ${g.promptBottom}）`);
    ok(g.actsBottom <= g.bodyBottom, `${vp.name}: 按钮完整可见（${g.actsBottom} ≤ ${g.bodyBottom}）`);
    ok(g.tipBottom == null || g.tipBottom <= g.bodyBottom, `${vp.name}: 底部提示完整可见`);
    ok(g.panelH <= g.imgH + 4, `${vp.name}: 整个面板高度≈图片高度（${g.panelH} vs ${g.imgH}）`);
    ok(errs.length === 0, `${vp.name}: 无 JS 报错`, errs.join(' | '));
    await pg.close();
  }

  // 窄屏堆叠：正文不应被限制成图片高度
  const pg = await b.newPage();
  await pg.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true });
  await pg.goto(BASE + 'detail.html?id=' + LONG_ID, { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 3000));
  const m = await pg.evaluate(() => {
    const body = document.querySelector('.detail-body');
    const img = document.querySelector('#dImg');
    return {
      maxHeight: body.style.maxHeight,
      bodyH: Math.round(body.getBoundingClientRect().height),
      imgH: Math.round(img.getBoundingClientRect().height),
      overflowY: getComputedStyle(body).overflowY,
    };
  });
  console.log('  [390x844] 图片高=' + m.imgH + ' 正文高=' + m.bodyH + ' maxHeight=' + m.maxHeight);
  ok(m.maxHeight === '' || m.maxHeight === 'none', '窄屏清除了正文 max-height（按内容自然展开）');
  ok(m.bodyH > m.imgH, '窄屏正文可高于图片（上下堆叠）');
  ok(m.overflowY === 'visible', '窄屏正文不内层滚动（overflow-y=' + m.overflowY + '）');
  await pg.close();

  await b.close();
  console.log('\n结果：' + pass + ' PASS / ' + fail + ' FAIL');
  process.exit(fail ? 1 : 0);
})();
