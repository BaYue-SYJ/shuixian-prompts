/* 灯箱边界场景验证：
 * 1. 竖版长图（9:16）在手机端是否把正文挤没
 * 2. .lb-img 的内层 overflow:auto 是否形成嵌套滚动陷阱（滑动图片区应该也能带动正文/不漏内容）
 * 3. 点击背景关闭是否仍然可用（overflow 改动后不要锁死）
 * 4. 键盘 Esc / 方向键翻页未受影响
 */
const os = require('os');
const p = require('puppeteer-core');
const path = require('path');
const fs = require('fs');
const OUT = path.join(os.tmpdir(), 'sx-audit-shots');

let pass = 0, fail = 0; const bad = [];
function ok(c, m) { if (c) pass++; else { fail++; bad.push(m); } }

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await p.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: 'new', args: ['--no-sandbox', '--hide-scrollbars'],
  });
  const pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.setViewport({ width: 390, height: 800, isMobile: true, deviceScaleFactor: 2, hasTouch: true });
  await pg.goto('http://127.0.0.1:8140/index.html', { waitUntil: 'networkidle2', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2200));

  // ---- 1. 打开灯箱，检查图片区与正文区的高度分配 ----
  await pg.evaluate(() => document.querySelector('.card').click());
  await new Promise(r => setTimeout(r, 1400));

  const a = await pg.evaluate(() => {
    const img = document.querySelector('.lb-img'), body = document.querySelector('.lb-body');
    const pan = document.querySelector('.lb-panel');
    const C = e => getComputedStyle(e);
    const r = e => e.getBoundingClientRect();
    return {
      imgH: Math.round(r(img).height), bodyH: Math.round(r(body).height),
      panH: Math.round(r(pan).height),
      imgOverflow: C(img).overflow, imgMinH: C(img).minHeight, imgMaxH: C(img).maxHeight,
      imgScrollH: img.scrollHeight, imgClientH: img.clientHeight,
      bodyH2: Math.round(r(body).height),
    };
  });
  console.log('— 图片区/正文区分配 —');
  console.log(`  img  h=${a.imgH} scrollH=${a.imgScrollH} clientH=${a.imgClientH} overflow=${a.imgOverflow} minH=${a.imgMinH} maxH=${a.imgMaxH}`);
  console.log(`  body h=${a.bodyH}   panel h=${a.panH}`);
  ok(a.imgH + a.bodyH <= a.panH + 2, `图片区+正文区(${a.imgH + a.bodyH}) 超出面板(${a.panH})`);
  ok(a.bodyH >= 120, `正文区被压得只剩 ${a.bodyH}px，太小`);

  // 图片区不应出现内层滚动条(会造成"划不动正文"的错觉)
  // 判据不是 scrollHeight 差值，而是「实际能不能滚」：overflow:hidden 时 scrollTop 恒为 0
  const imgScrollable = await pg.evaluate(() => {
    const img = document.querySelector('.lb-img');
    const ov = getComputedStyle(img).overflow;
    img.scrollTop = 500;
    const after = img.scrollTop;
    img.scrollTop = 0;
    return { ov, after };
  });
  console.log(`  图片区 overflow=${imgScrollable.ov}，强设 scrollTop=500 后实际=${imgScrollable.after}`);
  ok(imgScrollable.after === 0, `图片区自身可滚动（overflow=${imgScrollable.ov}，scrollTop=${imgScrollable.after}），形成嵌套滚动陷阱`);

  // ---- 2. 背景点击关闭 ----
  const closed = await pg.evaluate(async () => {
    const lb = document.querySelector('#sx-lightbox');
    const bd = document.querySelector('.lb-backdrop');
    bd.click();
    await new Promise(r => setTimeout(r, 400));
    return { open: lb.classList.contains('open'), display: getComputedStyle(lb).display };
  });
  console.log(`\n— 点击背景关闭 —  已关闭=${!closed.open}`);
  ok(!closed.open, `点击背景未能关闭灯箱（open=${closed.open} display=${closed.display}）`);

  // ---- 3. Esc 关闭 ----
  await pg.evaluate(() => document.querySelector('.card').click());
  await new Promise(r => setTimeout(r, 900));
  await pg.keyboard.press('Escape');
  await new Promise(r => setTimeout(r, 400));
  const escOk = await pg.evaluate(() => !document.querySelector('#sx-lightbox').classList.contains('open'));
  console.log(`— Esc 关闭 —  ${escOk ? 'OK' : '失败'}`);
  ok(escOk, 'Esc 未能关闭灯箱');

  // ---- 4. 关闭按钮 ----
  await pg.evaluate(() => document.querySelector('.card').click());
  await new Promise(r => setTimeout(r, 900));
  const btnOk = await pg.evaluate(async () => {
    const c = document.querySelector('.lb-close');
    if (!c) return 'no-btn';
    c.click();
    await new Promise(r => setTimeout(r, 400));
    return !document.querySelector('#sx-lightbox').classList.contains('open');
  });
  console.log(`— 关闭按钮 —  ${btnOk === true ? 'OK' : btnOk}`);
  ok(btnOk === true, `关闭按钮无效（${btnOk}）`);

  // ---- 5. 方向键翻页 ----
  await pg.evaluate(() => document.querySelector('.card').click());
  await new Promise(r => setTimeout(r, 1200));
  const before = await pg.evaluate(() => { const t = [...document.querySelectorAll('.lb-tags .tag')].map(x => x.textContent.trim()).find(x => x.indexOf('ID') === 0); return t || ''; });
  await pg.keyboard.press('ArrowRight');
  await new Promise(r => setTimeout(r, 1200));
  const after = await pg.evaluate(() => { const t = [...document.querySelectorAll('.lb-tags .tag')].map(x => x.textContent.trim()).find(x => x.indexOf('ID') === 0); return t || ''; });
  console.log(`\n— 方向键翻页 —  "${before}" → "${after}"`);
  // 比对 ID 而不是标题：数据里存在同名标题，比标题会偶发误报
  ok(before !== after, `方向键未切换提示词（翻页前后 ID 相同：${after}）`);

  // 翻页后正文应回到顶部而不是继承上一条的滚动位置
  const scrollAfterNav = await pg.evaluate(() => {
    const b = document.querySelector('.lb-body');
    return { top: Math.round(b.scrollTop), imgTop: Math.round(document.querySelector('.lb-img').scrollTop) };
  });
  console.log(`  翻页后 body.scrollTop=${scrollAfterNav.top} img.scrollTop=${scrollAfterNav.imgTop}`);
  ok(scrollAfterNav.top <= 4, `翻页后正文未回到顶部（scrollTop=${scrollAfterNav.top}）`);

  // ---- 6. 竖版长图压力测试：注入一张 9:16 假图 ----
  const tall = await pg.evaluate(async () => {
    const img = document.querySelector('.lb-img img');
    if (!img) return { skip: true };
    // 换成一张确定性的竖版 SVG data-uri（9:16）
    img.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1600"><rect width="900" height="1600" fill="#c8d8e0"/></svg>'
    );
    await new Promise(r => { img.complete ? r() : (img.onload = r); setTimeout(r, 1500); });
    await new Promise(r => setTimeout(r, 300));
    const body = document.querySelector('.lb-body'), wrap = document.querySelector('.lb-img');
    const pan = document.querySelector('.lb-panel');
    const R = e => e.getBoundingClientRect();
    return {
      imgBoxH: Math.round(R(img).height),
      wrapH: Math.round(R(wrap).height),
      bodyH: Math.round(R(body).height),
      panH: Math.round(R(pan).height),
      wrapScrollTrap: wrap.scrollHeight - wrap.clientHeight,
      bodyScrollable: body.scrollHeight - body.clientHeight,
    };
  });
  if (!tall.skip) {
    const tallTrap = await pg.evaluate(() => {
      const wrap = document.querySelector('.lb-img');
      const ov = getComputedStyle(wrap).overflow;
      wrap.scrollTop = 500; const after = wrap.scrollTop; wrap.scrollTop = 0;
      return { ov, after };
    });
    console.log(`\n— 竖版长图(9:16)压力测试 —`);
    console.log(`  图片 h=${tall.imgBoxH}  图片容器 h=${tall.wrapH}  正文 h=${tall.bodyH}  面板 h=${tall.panH}`);
    console.log(`  图片容器 overflow=${tallTrap.ov}，强设 scrollTop=500 后实际=${tallTrap.after}；正文可滚 ${tall.bodyScrollable}px`);
    ok(tall.wrapH + tall.bodyH <= tall.panH + 2, `长图下 图片容器+正文(${tall.wrapH + tall.bodyH}) 超出面板(${tall.panH})`);
    ok(tall.bodyH >= 100, `长图下正文被压到 ${tall.bodyH}px`);
    ok(tallTrap.after === 0, `长图下图片容器仍可内层滚动（scrollTop=${tallTrap.after}）`);
    await pg.screenshot({ path: path.join(OUT, 'lb-tall-image.png') });
  }

  ok(errs.length === 0, `页面报错：${errs.join(' | ')}`);
  await b.close();
  console.log(`\n================ 结果 ================`);
  console.log(`通过 ${pass} / 失败 ${fail}`);
  if (bad.length) { console.log('失败项：'); bad.forEach(x => console.log('  ✗ ' + x)); }
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(2); });
