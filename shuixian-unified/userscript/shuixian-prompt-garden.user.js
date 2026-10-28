// ==UserScript==
// @name         水仙提示词 · 侧边栏 (Prompt Garden Sidebar)
// @namespace    https://github.com/BaYue-SYJ
// @version      1.0.0
// @description  在 ChatGPT / Claude / Gemini / Midjourney 等页面召唤「水仙的AI提示词」侧边栏：搜索 6,011 条提示词，支持变量填空后一键复制到输入框。
// @author       水仙
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @match        https://claude.ai/*
// @match        https://gemini.google.com/*
// @match        https://aistudio.google.com/*
// @match        https://www.midjourney.com/*
// @match        https://jimeng.jianying.com/*
// @match        https://chat.deepseek.com/*
// @grant        GM_setClipboard
// @run-at       document-idle
// ==/UserScript==

/* ------------------------------------------------------------------
   配置：把下面换成你的画廊线上地址（结尾不要带斜杠）。
   站点已在 _headers 里为 /data/* 放开 CORS，才能跨域读取。
   例：'https://shuixian-unified.pages.dev'
   ------------------------------------------------------------------ */
const SITE = 'https://shuixian-unified.pages.dev';

(function () {
  'use strict';

  const PARTS = [1, 2, 3];
  const HOT = ['赛博朋克', '角色立绘', '电影感', '国风', '极简', '杂志风', '3D渲染', '可爱', '复古', '广告海报'];

  let LIST = null;         // 轻量索引（含 title/category/image，不含 prompt）
  let FULL = null;         // id -> prompt
  let fullLoading = null;
  let api = null;          // shadow root

  /* ---------------- 数据 ---------------- */
  async function loadList() {
    if (LIST) return LIST;
    const parts = await Promise.all(PARTS.map(i =>
      fetch(`${SITE}/data/list.part${i}.json`).then(r => r.json()).catch(() => [])
    ));
    LIST = [].concat(...parts);
    return LIST;
  }
  async function loadFull() {
    if (FULL) return FULL;
    if (fullLoading) return fullLoading;
    fullLoading = (async () => {
      const parts = await Promise.all(PARTS.map(i =>
        fetch(`${SITE}/data/prompts.part${i}.json`).then(r => r.json()).catch(() => [])
      ));
      FULL = {};
      [].concat(...parts).forEach(e => { FULL[e.id] = e.prompt || ''; });
      return FULL;
    })();
    return fullLoading;
  }

  /* ---------------- 工具 ---------------- */
  const esc = s => (s == null ? '' : String(s)).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  async function copy(text) {
    try {
      if (typeof GM_setClipboard === 'function') { GM_setClipboard(text, 'text'); return true; }
      await navigator.clipboard.writeText(text); return true;
    } catch (e) {
      const ta = document.createElement('textarea');
      ta.value = text; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (_) { }
      ta.remove(); return true;
    }
  }

  const VAR_RE = /\{argument\s+name="([^"]+)"(?:\s+default="([^"]*)")?\s*\}/g;
  const VAR_MUST = /\{\{\s*([A-Za-z0-9_\u4e00-\u9fff\- ]{1,40})\s*\}\}/g;
  function parseVars(text) {
    const out = new Map(); let m;
    VAR_RE.lastIndex = 0; while ((m = VAR_RE.exec(text || ''))) if (!out.has(m[1])) out.set(m[1], m[2] || '');
    VAR_MUST.lastIndex = 0; while ((m = VAR_MUST.exec(text || ''))) { const k = m[1].trim(); if (!out.has(k)) out.set(k, ''); }
    return [...out.entries()].map(([name, def]) => ({ name, def }));
  }
  function resolve(text, vals) {
    let o = text || '';
    o = o.replace(VAR_RE, (all, n, d) => (vals[n] != null && vals[n] !== '') ? vals[n] : (d != null ? d : all));
    o = o.replace(VAR_MUST, (all, n) => (vals[n.trim()] != null && vals[n.trim()] !== '') ? vals[n.trim()] : all);
    return o;
  }

  function score(item, q) {
    if (!q) return 1;
    const n = q.toLowerCase();
    const t = (item.title || '').toLowerCase(), c = (item.category || '').toLowerCase();
    let s = 0;
    if (t.includes(n)) s += 100 - Math.min(t.indexOf(n), 60);
    if (c.includes(n)) s += 55;
    if (!s) { // 模糊子序列
      let i = 0; for (const ch of t) { if (ch === n[i]) i++; }
      if (i >= n.length && n.length > 1) s += 30;
    }
    return s;
  }

  /* ---------------- UI ---------------- */
  function build() {
    const host = document.createElement('div');
    host.id = 'sx-pg-host';
    host.style.cssText = 'position:fixed;z-index:2147483000;inset:0;pointer-events:none';
    document.documentElement.appendChild(host);
    const sh = host.attachShadow({ mode: 'open' });
    api = sh;

    sh.innerHTML = `
<style>
  *{box-sizing:border-box}
  .fab{position:fixed;right:22px;bottom:88px;width:50px;height:50px;border-radius:50%;
    background:linear-gradient(135deg,#4FB3C9,#1F6A85);color:#fff;border:none;cursor:pointer;
    box-shadow:0 10px 30px rgba(31,106,133,.38);font-size:22px;pointer-events:auto;
    display:grid;place-items:center;transition:.2s}
  .fab:hover{transform:translateY(-3px) rotate(-8deg)}
  .panel{position:fixed;top:0;right:0;height:100vh;width:392px;max-width:92vw;background:#fff;color:#111;
    border-left:1px solid #EBEBEB;box-shadow:-16px 0 46px rgba(0,0,0,.14);display:flex;flex-direction:column;
    transform:translateX(102%);transition:transform .28s cubic-bezier(.2,.8,.2,1);pointer-events:auto;
    font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif}
  .panel.open{transform:none}
  .hd{display:flex;align-items:center;gap:10px;padding:16px 16px 12px;border-bottom:1px solid #EBEBEB}
  .hd .mk{width:30px;height:30px;border-radius:9px;background:linear-gradient(140deg,#4FB3C9,#2C8CAB);
    display:grid;place-items:center;color:#fff;font-weight:800;font-size:14px;flex:none}
  .hd b{font-size:15px}
  .hd .sm{display:block;font-size:11px;color:#6B6B6B;font-weight:400}
  .hd .cls{margin-left:auto;border:none;background:none;font-size:18px;color:#6B6B6B;cursor:pointer}
  .sb{padding:12px 16px;border-bottom:1px solid #EBEBEB}
  .sb input{width:100%;padding:10px 13px;border-radius:999px;border:1px solid #EBEBEB;outline:none;font-size:13.5px}
  .sb input:focus{border-color:#2C8CAB;box-shadow:0 0 0 4px #E3F4F8}
  .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
  .chip{padding:4px 10px;border-radius:999px;background:#F1F3F4;border:none;font-size:11.5px;color:#4A4A4A;cursor:pointer}
  .chip:hover{background:#E3F4F8;color:#2C8CAB}
  .ls{flex:1;overflow:auto;padding:8px}
  .it{display:flex;gap:10px;padding:10px;border-radius:12px;cursor:pointer;align-items:flex-start}
  .it:hover{background:#E3F4F8}
  .it .th{width:44px;height:58px;border-radius:8px;object-fit:cover;background:#EFF1F2;flex:none}
  .it .tx{min-width:0}
  .it .t1{font-size:13px;font-weight:600;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;
    -webkit-box-orient:vertical;overflow:hidden}
  .it .t2{font-size:11px;color:#6B6B6B;margin-top:3px}
  .ft{padding:10px 16px;border-top:1px solid #EBEBEB;font-size:11px;color:#6B6B6B;display:flex;gap:10px;flex-wrap:wrap}
  .ft kbd{background:#F1F3F4;border-radius:5px;padding:1px 6px;font-size:11px}
  .vf{position:absolute;inset:0;background:#fff;display:flex;flex-direction:column;padding:16px;gap:12px;overflow:auto}
  .vf h4{margin:0;font-size:15px}
  .vf .f{display:flex;flex-direction:column;gap:5px}
  .vf label{font-size:12px;font-weight:700;color:#2C8CAB;font-family:ui-monospace,monospace}
  .vf input{padding:9px 12px;border-radius:10px;border:1px solid #EBEBEB;font-size:13px;outline:none}
  .vf input:focus{border-color:#2C8CAB}
  .vf .row{display:flex;gap:8px;flex-wrap:wrap;margin-top:auto}
  .btn{padding:9px 15px;border-radius:999px;border:none;font-size:13px;font-weight:700;cursor:pointer}
  .pri{background:linear-gradient(135deg,#2C8CAB,#1F6A85);color:#fff}
  .sof{background:#fff;border:1px solid #EBEBEB;color:#111}
  .emp{padding:34px 18px;text-align:center;color:#6B6B6B;font-size:13px}
  .ld{padding:6px 16px;font-size:11px;color:#2C8CAB;background:#E3F4F8}
</style>
  <button class="fab" id="fab" title="水仙提示词 (Ctrl+Shift+K)">🌼</button>
  <div class="panel" id="panel">
    <div class="hd">
      <span class="mk">水</span>
      <div><b>水仙的AI提示词</b><span class="sm">提示词花园 · 侧边栏</span></div>
      <button class="cls" id="cls">✕</button>
    </div>
    <div class="sb">
      <input id="q" type="text" placeholder="搜索提示词…（支持拼音缩写 sbpk）" autocomplete="off">
      <div class="chips" id="chips"></div>
    </div>
    <div class="ld" id="ld" style="display:none"></div>
    <div class="ls" id="ls"></div>
    <div class="ft"><span><kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>K</kbd> 开关</span><span id="cnt"></span></div>
  </div>`;

    sh.getElementById('fab').addEventListener('click', () => toggle(true));
    sh.getElementById('cls').addEventListener('click', () => toggle(false));
    sh.getElementById('q').addEventListener('input', e => render(e.target.value.trim()));
    sh.getElementById('chips').innerHTML = HOT.map(h => `<button class="chip" data-h="${esc(h)}">${esc(h)}</button>`).join('');
    sh.querySelectorAll('[data-h]').forEach(b => b.addEventListener('click', () => {
      sh.getElementById('q').value = b.dataset.h; render(b.dataset.h);
    }));
    document.addEventListener('keydown', e => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'k') { e.preventDefault(); toggle(); }
      if (e.key === 'Escape') toggle(false);
    });

    loadList().then(() => render('')).catch(() => {
      sh.getElementById('ls').innerHTML = `<div class="emp">数据加载失败。<br>请检查脚本顶部的 SITE 是否已改成你的画廊地址，<br>并确认站点 <code>/data/*</code> 已放开 CORS。</div>`;
    });
  }

  function toggle(force) {
    const p = api.getElementById('panel');
    const open = force != null ? force : !p.classList.contains('open');
    p.classList.toggle('open', open);
    if (open) setTimeout(() => api.getElementById('q').focus(), 120);
  }

  function render(q) {
    const ls = api.getElementById('ls');
    if (!LIST) { ls.innerHTML = '<div class="emp">正在加载…</div>'; return; }
    let list;
    if (!q) list = LIST.slice().sort((a, b) => (b.likes || 0) - (a.likes || 0)).slice(0, 40);
    else {
      const scored = [];
      for (const it of LIST) { const s = score(it, q); if (s > 0) scored.push([s, it]); }
      scored.sort((a, b) => b[0] - a[0]);
      list = scored.slice(0, 40).map(x => x[1]);
    }
    api.getElementById('cnt').textContent = q ? `命中 ${list.length} 条` : '热门推荐';
    if (!list.length) { ls.innerHTML = '<div class="emp">没有匹配的提示词</div>'; return; }
    ls.innerHTML = list.map(s => `
      <div class="it" data-id="${s.id}">
        ${s.image ? `<img class="th" loading="lazy" src="${esc(SITE + '/' + s.image)}" alt="">` : '<div class="th"></div>'}
        <div class="tx"><div class="t1">${esc(s.title)}</div><div class="t2">${esc(s.category)}</div></div>
      </div>`).join('');
    ls.querySelectorAll('.it').forEach(el => el.addEventListener('click', () => pick(+el.dataset.id)));
  }

  async function pick(id) {
    const item = LIST.find(x => x.id === id);
    if (!item) return;
    api.getElementById('ld').style.display = 'block';
    api.getElementById('ld').textContent = '正在取回提示词原文…';
    try { await loadFull(); } catch (e) { }
    api.getElementById('ld').style.display = 'none';
    const prompt = (FULL && FULL[id]) || '';
    if (!prompt) { api.getElementById('ld').style.display = 'block'; api.getElementById('ld').textContent = '未取到原文，请在画廊中查看'; setTimeout(() => api.getElementById('ld').style.display = 'none', 2200); return; }
    const vars = parseVars(prompt);
    if (!vars.length) {
      await copy(prompt);
      flash('已复制：' + item.title);
      return;
    }
    showVarFill(item, prompt, vars);
  }

  function flash(msg) {
    const el = api.getElementById('ld');
    el.style.display = 'block'; el.textContent = msg;
    setTimeout(() => { el.style.display = 'none'; }, 1800);
  }

  function showVarFill(item, prompt, vars) {
    const panel = api.getElementById('panel');
    const box = document.createElement('div');
    box.className = 'vf';
    box.innerHTML = `<h4>${esc(item.title)}</h4>
      <div style="font-size:12px;color:#6B6B6B">填好变量后复制，得到可直接使用的成品。</div>
      <div id="flds" style="display:flex;flex-direction:column;gap:11px"></div>
      <div class="row">
        <button class="btn pri" id="ok">复制成品</button>
        <button class="btn sof" id="tpl">复制模板</button>
        <button class="btn sof" id="back">返回</button>
      </div>`;
    panel.appendChild(box);
    const flds = box.querySelector('#flds');
    flds.innerHTML = vars.map(v => `<div class="f"><label>${esc(v.name)}</label>
      <input data-k="${esc(v.name)}" placeholder="${esc(v.def || '填写…')}"></div>`).join('');
    const collect = () => { const o = {}; flds.querySelectorAll('input').forEach(i => o[i.dataset.k] = i.value.trim()); return o; };
    box.querySelector('#ok').addEventListener('click', async () => { await copy(resolve(prompt, collect())); box.remove(); flash('已复制成品'); });
    box.querySelector('#tpl').addEventListener('click', async () => { await copy(prompt); box.remove(); flash('已复制模板'); });
    box.querySelector('#back').addEventListener('click', () => box.remove());
    const first = flds.querySelector('input'); if (first) setTimeout(() => first.focus(), 80);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
