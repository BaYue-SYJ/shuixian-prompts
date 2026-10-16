/* =========================================================
   水仙 · 提示词花园 — features.js
   在 base.js 之后加载，订阅 App 的 'sx:ready' 事件后自动装配新功能：
     · 变量填空（解析 {argument name="x" default="y"}）→ 填完复制成品
     · 标签分面（媒介 / 风格 / 色调 三类横切标签，从正文自动提取）
     · 智能搜索（模糊子序列 + 拼音首字母 + 关键词高亮）
     · 命令面板 Ctrl/⌘+K、键盘快捷键、随机漫游、深链 #id=
     · 收藏合集（新建/改名/删除/复制/拖拽排序/跨画板移动/导入导出）
     · 导出 JSON · Markdown · CSV，图片下载（单张 / 批量）
     · 个人备注、使用次数、筛选器、LQIP 懒加载、中英切换、PWA
   依赖：window.App（base.js 暴露）
   ========================================================= */
(function () {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => (s == null ? '' : String(s)).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
  const uid = p => (p || 'x') + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

  const LS = {
    notes: 'sx-notes-v1',
    uses: 'sx-uses-v1',
    lang: 'sx-lang',
    prefs: 'sx-prefs-v1',
    boards: 'sx-boards-v2',
    imported: 'sx-imported-v1',
  };

  const store = {
    get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } },
  };

  /* ================= i18n ================= */
  // 这里只保留新功能自身的兜底文案；全站文案在 js/i18n.js（window.SX_I18N），
  // 加载时会合并覆盖（i18n.js 优先）。
  const FALLBACK_UI = {
    zh: {
      nav_home: '首页', nav_gallery: '画廊', nav_categories: '分类', nav_search: '搜索',
      nav_favorites: '收藏', nav_about: '关于', nav_submit: '投稿',
      search_ph: '搜索提示词、标签…', palette: '命令面板', theme: '切换主题', lang: 'English',
      vf_title: '填好变量，一次复制成品', vf_sub: '这条提示词带可替换参数，填完直接复制就是能用的成品。',
      vf_empty: '这条提示词没有可替换变量，可直接复制。', vf_copy_done: '复制成品',
      vf_copy_tpl: '复制模板', vf_reset: '恢复默认', vf_preview: '预览',
      vf_all_default: '（全部留空则等同于原文）',
      palette_ph: '搜索提示词、分类，或输入命令…', palette_cmd: '功能', palette_prompt: '提示词',
      palette_cat: '分类', palette_empty: '没有结果',
      cmd_random: '随机漫游一条提示词', cmd_theme: '切换深浅主题', cmd_lang: '切换语言',
      cmd_export: '导出收藏合集', cmd_help: '键盘快捷键', cmd_gallery: '去画廊', cmd_search: '去搜索',
      cmd_cats: '去分类总览', cmd_fav: '去收藏合集', cmd_about: '去关于', cmd_submit: '去投稿',
      facet_medium: '媒介', facet_style: '风格', facet_tone: '色调', facet_clear: '清除筛选',
      filter_only_img: '只看有图', filter_only_note: '只看有备注', filter_fav: '仅看已收藏',
      filter_used: '仅看用过的', facet_more: '更多',
      col_title: '我的收藏合集', col_new: '＋ 新建合集', col_rename: '重命名', col_dup: '复制合集',
      col_del: '删除合集', col_clear: '清空合集', col_empty: '这个合集还是空的，去画廊点 ❤ 收藏吧。',
      col_export: '导出', col_import: '导入 JSON', col_move: '移动到…', col_remove: '移出合集',
      col_download: '下载图片', col_downloadall: '批量下载图片', col_drag: '拖动可排序',
      col_count: '条', note_title: '我的备注', note_ph: '记下这条提示词的用法、出图参数、改进想法…',
      note_saved: '备注已保存', uses: '使用', times: '次', copied: '已复制', copy_prompt: '复制提示词',
      copy_json: '复制 JSON', copy_md: '复制 Markdown', dl_img: '下载图片', share: '复制链接',
      share_done: '链接已复制', used_mark: '标记已用',
      help_title: '键盘快捷键', help_key: '按键', help_action: '动作',
    },
    en: {
      nav_home: 'Home', nav_gallery: 'Gallery', nav_categories: 'Categories', nav_search: 'Search',
      nav_favorites: 'Collections', nav_about: 'About', nav_submit: 'Submit',
      search_ph: 'Search prompts, tags…', palette: 'Command palette', theme: 'Toggle theme', lang: '中文',
      vf_title: 'Fill the variables, copy a ready-to-use prompt', vf_sub: 'This prompt has replaceable parameters.',
      vf_empty: 'No variables in this prompt — copy it directly.', vf_copy_done: 'Copy result',
      vf_copy_tpl: 'Copy template', vf_reset: 'Reset', vf_preview: 'Preview',
      vf_all_default: '(all empty = original text)',
      palette_ph: 'Search prompts, categories, or type a command…', palette_cmd: 'Actions', palette_prompt: 'Prompts',
      palette_cat: 'Categories', palette_empty: 'No results',
      cmd_random: 'Surprise me — random prompt', cmd_theme: 'Toggle light / dark', cmd_lang: 'Switch language',
      cmd_export: 'Export collections', cmd_help: 'Keyboard shortcuts', cmd_gallery: 'Go to gallery', cmd_search: 'Go to search',
      cmd_cats: 'Browse categories', cmd_fav: 'My collections', cmd_about: 'About', cmd_submit: 'Submit a prompt',
      facet_medium: 'Medium', facet_style: 'Style', facet_tone: 'Tone', facet_clear: 'Clear filters',
      filter_only_img: 'With image', filter_only_note: 'With note', filter_fav: 'Favorited only',
      filter_used: 'Used only', facet_more: 'more',
      col_title: 'My collections', col_new: '＋ New collection', col_rename: 'Rename', col_dup: 'Duplicate',
      col_del: 'Delete', col_clear: 'Clear', col_empty: 'This collection is empty — tap ❤ in the gallery to add prompts.',
      col_export: 'Export', col_import: 'Import JSON', col_move: 'Move to…', col_remove: 'Remove',
      col_download: 'Download image', col_downloadall: 'Download all images', col_drag: 'Drag to reorder',
      col_count: 'items', note_title: 'My notes', note_ph: 'Notes, settings, ideas for this prompt…',
      note_saved: 'Note saved', uses: 'Used', times: '×', copied: 'Copied', copy_prompt: 'Copy prompt',
      copy_json: 'Copy JSON', copy_md: 'Copy Markdown', dl_img: 'Download image', share: 'Copy link',
      share_done: 'Link copied', used_mark: 'Mark as used',
      help_title: 'Keyboard shortcuts', help_key: 'Key', help_action: 'Action',
    },
  };

  // 合并 js/i18n.js 的全站字典（它优先）
  const SX_I18N = window.SX_I18N || {};
  const I18N = {
    zh: Object.assign({}, FALLBACK_UI.zh, (SX_I18N.ui && SX_I18N.ui.zh) || {}),
    en: Object.assign({}, FALLBACK_UI.en, (SX_I18N.ui && SX_I18N.ui.en) || {}),
  };
  const CAT_EN = SX_I18N.cat || {};

  if (!SX_I18N.ui) console.warn('[fx] js/i18n.js 未加载，仅使用内置兜底文案');

  const ENABLE_LANG_SWITCH = true;
  let lang = store.get(LS.lang, 'zh');
  if (lang !== 'en' && lang !== 'zh') lang = 'zh';
  const t = k => (I18N[lang] && I18N[lang][k]) || I18N.zh[k] || k;
  // 带 {n} / {q} / {name} 的文案格式化
  const tf = (k, o) => t(k).replace(/\{(\w+)\}/g, (m, g) => (o && o[g] != null) ? String(o[g]) : m);
  // 分类名显示用（URL 与数据仍用中文原名）
  function catName(name) {
    if (name === '其他/未归类') return '杂项';   // 显示名改「杂项」，数据 key 不变
    if (lang !== 'en') return name;
    return CAT_EN[name] || name;
  }

  /* ================= 标签 / 分面 ================= */
  const TAG_DICT = {
    媒介: {
      '海报': /海报|poster|banner|广告|宣传/i,
      '信息图': /信息图|infographic|图解|可视化图表|图谱|拆解图|爆炸图/i,
      '插画': /插画|illustration|绘本|手绘|绘画|连环画/i,
      '摄影': /摄影|照片|写真|实拍|photo|摄影棚|胶片|人像/i,
      '3D渲染': /3d|渲染|render|立体|建模|c4d|blender/i,
      'UI界面': /ui|界面|网页|app|dashboard|仪表盘|hud|状态屏/i,
      'Logo/图标': /logo|图标|icon|标识|头像|徽标/i,
      '字体排版': /字体|排版|文字|typography|标题设计|书法|字形/i,
      '包装设计': /包装|包装盒|礼盒|瓶身|罐|标签设计|package/i,
      '漫画分镜': /漫画|分镜|漫画格|comic|storyboard|条漫|连环画/i,
      '卡牌': /卡牌|卡面|卡片|tcg|收藏卡|塔罗|运势卡/i,
      '封面': /封面|cover|杂志封面|主视觉|key visual/i,
    },
    风格: {
      '极简': /极简|简约|minimal|留白|克制|性冷淡/i,
      '赛博朋克': /赛博朋克|cyberpunk|霓虹|neon|未来都市/i,
      '复古': /复古|retro|怀旧|vintage|胶片感|老照片|中世纪/i,
      '国风': /国风|中式|东方|中国|水墨|国潮|新中式|古风|敦煌|汉服/i,
      '日系': /日系|日本|和风|japanese|二次元|动漫|anime|吉卜力/i,
      '电影感': /电影感|cinematic|电影质感|戏剧性打光|大片|宽银幕/i,
      '杂志风': /杂志|editorial|edition|排版感|大片风/i,
      '手绘': /手绘|水彩|素描|铅笔|油画|插画风|painterly|笔触/i,
      '像素': /像素|pixel|8bit|16bit|游戏机/i,
      '构成主义': /构成主义|constructivis|包豪斯|bauhaus|agitprop|粗野主义/i,
      '故障艺术': /故障|glitch|失真|错位|故障艺术/i,
      '蒸汽朋克': /蒸汽朋克|steampunk|齿轮|机械美学|废土|赛博/i,
      '哥特': /哥特|gothic|暗黑|黑暗|诡异|恐怖|怪诞/i,
      '可爱': /可爱|kawaii|萌|q版|软萌|chibi|治愈/i,
      '写实': /写实|超写实|真实|photoreal|hyperreal|仿真/i,
      '奇幻': /奇幻|魔幻|fantasy|魔法|神话|史诗|仙侠/i,
    },
    色调: {
      '黑白': /黑白|单色|grayscale|monochrome|黑白灰/i,
      '高饱和': /高饱和|鲜艳|荧光|霓虹色|撞色|vivid/i,
      '低饱和': /低饱和|莫兰迪|柔和色|奶油|低饱和|muted|pastel|马卡龙/i,
      '暖色': /暖色|暖调|米白|象牙|奶油色|焦糖|橘色|琥珀|金色/i,
      '冷色': /冷色|冷调|蓝调|青蓝|冰蓝|灰蓝|薄荷/i,
      '黑金': /黑金|金箔|烫金|哑光金|金色点缀/i,
      '粉紫': /粉紫|粉红|玫瑰|樱花|薰衣草|紫色/i,
      '绿色系': /墨绿|森林绿|鼠尾草|薄荷绿|橄榄绿|青绿/i,
    },
  };

  const _tagCache = new Map();
  function tagsFor(item) {
    if (!item) return {};
    const id = item.id;
    if (_tagCache.has(id)) return _tagCache.get(id);
    const hay = (item.title || '') + ' ' + (item.category || '') + ' ' + (item.prompt || '');
    const out = {};
    for (const facet in TAG_DICT) {
      const hits = [];
      for (const name in TAG_DICT[facet]) if (TAG_DICT[facet][name].test(hay)) hits.push(name);
      out[facet] = hits;
    }
    _tagCache.set(id, out);
    return out;
  }
  function flatTags(item) {
    const g = tagsFor(item), out = [];
    for (const k in g) out.push(...g[k]);
    return out;
  }
  // 正文（prompt）按需加载完成后，标签可能变多 —— 清缓存重算
  function clearTagCache() { _tagCache.clear(); }

  /* ================= 拼音 ================= */
  let PINYIN = null, pinyinPromise = null;
  function loadPinyin() {
    if (PINYIN) return Promise.resolve(PINYIN);
    if (pinyinPromise) return pinyinPromise;
    pinyinPromise = fetch('data/pinyin.json').then(r => r.json())
      .then(j => { PINYIN = (j && j.chars) || {}; return PINYIN; })
      .catch(() => { PINYIN = {}; return PINYIN; });
    return pinyinPromise;
  }
  function initials(str) {
    if (!PINYIN) return '';
    let out = '';
    for (const ch of String(str)) {
      if (PINYIN[ch]) out += PINYIN[ch];
      else if (/[a-z0-9]/i.test(ch)) out += ch.toLowerCase();
    }
    return out;
  }

  /* ================= 智能搜索 ================= */
  function subseq(q, text) {
    // 子序列模糊匹配：返回紧凑度（越高越好），不匹配返回 0
    if (!q || !text) return 0;
    let i = 0, gaps = 0, last = -1;
    for (let j = 0; j < text.length && i < q.length; j++) {
      if (text[j] === q[i]) { if (last >= 0) gaps += (j - last - 1); last = j; i++; }
    }
    if (i < q.length) return 0;
    const span = last + 1;
    return clamp(1 - gaps / (span + 1), 0.15, 1);
  }
  function smartScore(item, q) {
    if (!q) return 1;
    const needle = q.toLowerCase().trim();
    const title = (item.title || '').toLowerCase();
    const cat = (item.category || '').toLowerCase();
    const prompt = (item.prompt || '').toLowerCase();
    let s = 0;
    if (title.includes(needle)) s += 120 - title.indexOf(needle);
    if (cat.includes(needle)) s += 70;
    if (prompt.includes(needle)) s += 26;
    // 逐词 AND（空格分词）
    const toks = needle.split(/\s+/).filter(Boolean);
    if (toks.length > 1) {
      const hay = title + ' ' + cat + ' ' + prompt;
      if (toks.every(x => hay.includes(x))) s += 40;
    }
    if (!s) {
      const fz = subseq(needle, title);
      if (fz > 0.42) s += 58 * fz;
      const pz = PINYIN ? subseq(needle, initials(title)) : 0;
      if (pz > 0.55) s += 62 * pz + (initials(title).startsWith(needle) ? 30 : 0);
      if (PINYIN && initials(cat).includes(needle)) s += 34;
      // 标签命中
      const tg = flatTags(item).join(' ').toLowerCase();
      if (tg.includes(needle)) s += 30;
    }
    return s;
  }
  function smartSearch(list, q) {
    if (!q) return list.slice();
    const scored = [];
    for (const it of list) { const sc = smartScore(it, q); if (sc > 0) scored.push([sc, it]); }
    scored.sort((a, b) => b[0] - a[0]);
    return scored.map(x => x[1]);
  }
  function highlight(text, q) {
    const safe = esc(text);
    if (!q) return safe;
    const toks = String(q).trim().split(/\s+/).filter(x => x.length >= 1)
      .map(x => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    if (!toks.length) return safe;
    try {
      return safe.replace(new RegExp('(' + toks.join('|') + ')', 'gi'), '<mark class="hl">$1</mark>');
    } catch (e) { return safe; }
  }

  /* ================= 变量填空 ================= */
  const VAR_RE = /\{argument\s+name="([^"]+)"(?:\s+default="([^"]*)")?\s*\}/g;
  const VAR_MUSTACHE = /\{\{\s*([A-Za-z0-9_\u4e00-\u9fff\- ]{1,40})\s*\}\}/g;
  const VAR_BRACKET = /\[([A-Z][A-Z0-9_ ]{1,32})\]/g;

  function parseVars(text) {
    const src = text || '', found = new Map();
    let m;
    VAR_RE.lastIndex = 0;
    while ((m = VAR_RE.exec(src))) if (!found.has(m[1])) found.set(m[1], m[2] || '');
    VAR_MUSTACHE.lastIndex = 0;
    while ((m = VAR_MUSTACHE.exec(src))) { const k = m[1].trim(); if (!found.has(k)) found.set(k, ''); }
    VAR_BRACKET.lastIndex = 0;
    while ((m = VAR_BRACKET.exec(src))) { const k = m[1].trim(); if (!found.has(k)) found.set(k, ''); }
    return [...found.entries()].map(([name, def]) => ({ name, def }));
  }
  function resolveVars(text, values) {
    let out = text || '';
    out = out.replace(VAR_RE, (all, name, def) => {
      const v = values && values[name];
      return (v != null && v !== '') ? v : (def != null ? def : all);
    });
    out = out.replace(VAR_MUSTACHE, (all, name) => {
      const v = values && values[name.trim()];
      return (v != null && v !== '') ? v : all;
    });
    out = out.replace(VAR_BRACKET, (all, name) => {
      const v = values && values[name.trim()];
      return (v != null && v !== '') ? v : all;
    });
    return out;
  }
  // 带高亮的预览（空值标红）
  function previewHTML(text, values) {
    let html = esc(text || '');
    html = html.replace(/\{argument\s+name=&quot;([^&]+)&quot;(?:\s+default=&quot;([^&]*)&quot;)?\s*\}/g, (all, name, def) => {
      const v = values && values[name];
      if (v != null && v !== '') return '<span class="fill">' + esc(v) + '</span>';
      if (def != null && def !== '') return '<span class="fill">' + esc(def) + '</span>';
      return '<span class="empty">' + name + '</span>';
    });
    html = html.replace(/\{\{\s*([A-Za-z0-9_\u4e00-\u9fff\- ]{1,40})\s*\}\}/g, (all, name) => {
      const v = values && values[name.trim()];
      return (v != null && v !== '') ? '<span class="fill">' + esc(v) + '</span>' : '<span class="empty">' + name.trim() + '</span>';
    });
    html = html.replace(/\[([A-Z][A-Z0-9_ ]{1,32})\]/g, (all, name) => {
      const v = values && values[name.trim()];
      return (v != null && v !== '') ? '<span class="fill">' + esc(v) + '</span>' : '<span class="empty">' + name.trim() + '</span>';
    });
    return html;
  }

  /* ================= 备注 / 使用次数 ================= */
  function notes() { return store.get(LS.notes, {}); }
  function noteFor(id) { const n = notes()[id]; return n && n.text ? n.text : ''; }
  function setNote(id, text) {
    const n = notes();
    if (text && text.trim()) n[id] = { text: text.trim(), ts: Date.now() };
    else delete n[id];
    store.set(LS.notes, n);
  }
  function uses() { return store.get(LS.uses, {}); }
  function useCount(id) { return uses()[id] || 0; }
  function bumpUse(id) { const u = uses(); u[id] = (u[id] || 0) + 1; store.set(LS.uses, u); }

  /* ================= 合集（画板） ================= */
  function loadBoards() {
    const b = App.getBoards();
    if (!b.boards) b.boards = [];
    if (!b.boards.length) b.boards.push({ id: 'default', name: '我的收藏', items: [] });
    if (!b.active || !b.boards.some(x => x.id === b.active)) b.active = b.boards[0].id;
    return b;
  }
  function saveBoards(B) { App.saveBoards(B); }
  function activeBoard(B) { return B.boards.find(x => x.id === B.active) || B.boards[0]; }

  /* ================= 导出 ================= */
  function downloadBlob(text, filename, mime) {
    const blob = new Blob([text], { type: mime || 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }
  function itemToMD(s) {
    const lines = ['## ' + (s.title || ''), '',
      '- 分类：' + (s.category || '') + ' · ID #' + s.id,
      '- 图片：' + (s.image ? App.imgUrl(s.image) : '—')];
    const nt = noteFor(s.id); if (nt) lines.push('- 备注：' + nt.replace(/\n/g, ' '));
    const tg = flatTags(s); if (tg.length) lines.push('- 标签：' + tg.join(' / '));
    lines.push('', '```', (s.prompt || ''), '```', '');
    return lines.join('\n');
  }
  function boardToMD(B, board) {
    const items = board.items.map(id => App.findSample(id)).filter(Boolean);
    const head = ['# ' + board.name + '（水仙的AI提示词）', '',
      '> 共 ' + items.length + ' 条 · 导出时间 ' + new Date().toLocaleString() + '', ''];
    return head.concat(items.map(itemToMD)).join('\n');
  }
  function csvCell(v) { return '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"'; }
  function boardToCSV(board) {
    const rows = [['id', 'title', 'category', 'tags', 'image', 'note', 'prompt'].map(csvCell).join(',')];
    board.items.map(id => App.findSample(id)).filter(Boolean).forEach(s => {
      rows.push([s.id, s.title || '', s.category || '', flatTags(s).join(' '),
        s.image ? App.imgUrl(s.image) : '', noteFor(s.id), s.prompt || ''].map(csvCell).join(','));
    });
    return '\ufeff' + rows.join('\r\n');
  }
  function boardToJSON(board) {
    const items = board.items.map(id => App.findSample(id)).filter(Boolean).map(s => ({
      id: s.id, title: s.title, category: s.category, image: s.image,
      tags: flatTags(s), note: noteFor(s.id), prompt: s.prompt || '',
    }));
    return JSON.stringify({ app: '水仙的AI提示词', board: board.name, exportedAt: new Date().toISOString(), count: items.length, items }, null, 2);
  }
  function importJSON(text) {
    let j; try { j = JSON.parse(text); } catch (e) { App.toast(t('toast_import_fail')); return; }
    const items = Array.isArray(j) ? j : (j.items || []);
    if (!items.length) { App.toast(t('toast_import_empty')); return; }
    const imported = store.get(LS.imported, {});
    let added = 0;
    items.forEach(it => {
      if (!it || !it.prompt) return;
      const key = 'imp-' + (it.id != null ? it.id : uid('n'));
      if (!imported[key] && !App.findSample(key)) {
        imported[key] = { id: key, title: it.title || '(导入)', category: it.category || '其他/未归类', image: it.image || '', prompt: it.prompt };
      }
      if (it.note) setNote(key, it.note);
      added++;
    });
    store.set(LS.imported, imported);
    App.toast(tf('toast_imported', { n: added, name: j.board || 'JSON' }));
  }

  /* ================= 图片下载 ================= */
  function safeName(s) {
    return String((s && s.title) || s.id || 'prompt').replace(/[\\/:*?"<>|\s]+/g, '_').slice(0, 60);
  }
  async function downloadImage(s, silent) {
    if (!s || !s.image) { App.toast(t('toast_no_img')); return false; }
    const url = App.imgUrl(s.image);
    try {
      const res = await fetch(url, { mode: 'cors' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const blob = await res.blob();
      const ext = (blob.type && blob.type.split('/')[1]) || (s.image.split('.').pop() || 'jpg');
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = safeName(s) + '_' + s.id + '.' + ext;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      if (!silent) App.toast(t('toast_copied_img'));
      return true;
    } catch (e) {
      if (!silent) App.toast(t('toast_cors'));
      window.open(url, '_blank', 'noopener');
      return false;
    }
  }
  async function downloadBoardImages(board, btn) {
    const items = board.items.map(id => App.findSample(id)).filter(s => s && s.image);
    if (!items.length) { App.toast(t('col_dl_none')); return; }
    const total = items.length;
    App.toast(tf('col_dl_start', { n: total }));
    const orig = btn ? btn.textContent : '';
    for (let i = 0; i < items.length; i++) {
      if (btn) btn.textContent = (lang === 'en' ? 'Downloading ' : '下载中 ') + (i + 1) + '/' + total;
      await downloadImage(items[i], true);
      await new Promise(r => setTimeout(r, 420));
    }
    if (btn) btn.textContent = orig || t('col_dl_all');
    App.toast(tf('col_dl_done', { n: total }));
  }

  /* ================= 通用 UI：遮罩 / 菜单 / 提示 ================= */
  function overlay(id, cls, html) {
    let el = document.getElementById(id);
    if (!el) { el = document.createElement('div'); el.id = id; document.body.appendChild(el); }
    el.className = 'fx-overlay ' + (cls || '');
    el.innerHTML = '<div class="fx-backdrop" data-fxclose></div>' + html;
    el.addEventListener('click', e => { if (e.target.hasAttribute('data-fxclose')) closeOverlay(id); });
    return el;
  }
  function openOverlay(id) { const el = document.getElementById(id); if (el) { el.classList.add('open'); document.body.style.overflow = 'hidden'; } }
  function closeOverlay(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('open');
    if (!$('.fx-overlay.open')) document.body.style.overflow = '';
  }

  let openMenuEl = null;
  function closeMenus() { if (openMenuEl) { openMenuEl.classList.remove('open'); openMenuEl = null; } }
  document.addEventListener('click', e => { if (openMenuEl && !openMenuEl.contains(e.target)) closeMenus(); });

  /* ================= 变量填空弹窗 ================= */
  let vfCtx = null;
  function openVarFill(id, opts) {
    const s = App.findSample(id); if (!s) return;
    const vars = parseVars(s.prompt || '');
    opts = opts || {};
    if (!vars.length) {
      App.copyText(s.prompt || ''); bumpUse(id);
      App.toast(t('vf_empty'));
      return;
    }
    vfCtx = { s, vars, values: {} };
    const fields = vars.map(v => `
      <div class="vf-field">
        <label><span class="key">${esc(v.name)}</span>${v.def ? '<span style="color:var(--muted);font-weight:600;font-size:12px">' + esc(t('vf_default')) + ': ' + esc(v.def) + '</span>' : ''}</label>
        <input type="text" data-var="${esc(v.name)}" placeholder="${esc(v.def || t('vf_ph'))}" value="">
      </div>`).join('');
    const html = `<div class="fx-panel">
      <div class="fx-head">
        <div><h3>${esc(t('vf_title'))}</h3><p class="sub">${esc(t('vf_sub'))}</p></div>
        <button class="x" data-fxclose aria-label="关闭">✕</button>
      </div>
      <div class="fx-body">
        <div class="vf-fields">${fields}</div>
        <div class="vf-preview">
          <div class="lbl">${esc(t('vf_preview'))}</div>
          <pre id="vfPreview"></pre>
        </div>
        <p class="fx-note" style="margin-top:12px">${esc(t('vf_all_default'))}</p>
      </div>
      <div class="fx-foot">
        <button class="btn btn-primary" id="vfCopyDone">${esc(t('vf_copy_done'))}</button>
        <button class="btn btn-soft" id="vfCopyTpl">${esc(t('vf_copy_tpl'))}</button>
        <span class="spacer"></span>
        <button class="btn btn-ghost" id="vfReset">${esc(t('vf_reset'))}</button>
      </div>
    </div>`;
    const el = overlay('fxVarFill', '', html);
    const preview = () => {
      const pre = $('#vfPreview', el);
      if (pre) pre.innerHTML = previewHTML(vfCtx.s.prompt || '', collect());
    };
    function collect() {
      const v = {};
      $$('input[data-var]', el).forEach(i => { v[i.dataset.var] = i.value.trim(); });
      return v;
    }
    $$('input[data-var]', el).forEach(i => i.addEventListener('input', preview));
    $('#vfCopyDone', el).addEventListener('click', () => {
      const out = resolveVars(vfCtx.s.prompt || '', collect());
      App.copyText(out); bumpUse(vfCtx.s.id);
      closeOverlay('fxVarFill'); openVarFill._refresh && openVarFill._refresh();
    });
    $('#vfCopyTpl', el).addEventListener('click', () => { App.copyText(vfCtx.s.prompt || ''); });
    $('#vfReset', el).addEventListener('click', () => { $$('input[data-var]', el).forEach(i => i.value = ''); preview(); });
    preview(); openOverlay('fxVarFill');
    const first = $('input[data-var]', el); if (first) setTimeout(() => first.focus(), 60);
  }

  /* ================= 命令面板 ================= */
  const COMMANDS = [
    { id: 'c-random', ico: '🎲', label: () => t('cmd_random'), run: () => randomPrompt() },
    { id: 'c-gallery', ico: '🖼️', label: () => t('cmd_gallery'), run: () => location.href = 'gallery.html' },
    { id: 'c-search', ico: '🔍', label: () => t('cmd_search'), run: () => location.href = 'search.html' },
    { id: 'c-cats', ico: '🗂️', label: () => t('cmd_cats'), run: () => location.href = 'categories.html' },
    { id: 'c-fav', ico: '❤️', label: () => t('cmd_fav'), run: () => location.href = 'favorites.html' },
    { id: 'c-export', ico: '⬇️', label: () => t('cmd_export'), run: () => exportActiveBoard() },
    { id: 'c-theme', ico: '🌗', label: () => t('cmd_theme'), run: () => { const b = $('#themeBtn'); if (b) b.click(); } },
    { id: 'c-lang', ico: '🌐', label: () => t('cmd_lang'), run: () => toggleLang() },
    { id: 'c-help', ico: '⌨️', label: () => t('cmd_help'), run: () => openHelp() },
    { id: 'c-about', ico: 'ℹ️', label: () => t('cmd_about'), run: () => location.href = 'about.html' },
    { id: 'c-submit', ico: '✍️', label: () => t('cmd_submit'), run: () => location.href = 'submit.html' },
  ];
  let palIdx = 0, palItems = [];
  function openPalette() {
    const html = `<div class="fx-panel">
      <div class="cmdk-input">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/><path d="M16 16L21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        <input id="palInput" type="text" placeholder="${esc(t('palette_ph'))}" autocomplete="off">
        <span class="esc">Esc</span>
      </div>
      <div class="cmdk-list" id="palList"></div>
      <div class="cmdk-foot"><span><kbd>↑</kbd><kbd>↓</kbd> ${esc(t('kbd_move'))}</span><span><kbd>Enter</kbd> ${esc(t('kbd_open'))}</span><span><kbd>Esc</kbd> ${esc(t('kbd_close'))}</span></div>
    </div>`;
    const el = overlay('fxPalette', 'cmdk', html);
    const input = $('#palInput', el);
    input.value = '';
    const render = () => {
      const q = input.value.trim();
      let items = [];
      if (!q) {
        items = COMMANDS.map(c => ({ ico: c.ico, t1: c.label(), t2: '', run: c.run, sec: t('palette_cmd') }));
      } else {
        COMMANDS.forEach(c => {
          const lb = c.label();
          if (smartScore({ title: lb }, q) > 0) items.push({ ico: c.ico, t1: lb, t2: '', run: c.run, sec: t('palette_cmd') });
        });
        const cats = [{ name: '全部' }].concat(App.ALL.map(s => ({ name: s.category })))
          .filter((c, i, a) => c.name && a.findIndex(x => x.name === c.name) === i);
        cats.slice(0, 8).forEach(c => {
          if (smartScore({ title: c.name }, q) > 0) {
            items.push({
              ico: '🗂️', t1: c.name, t2: t('palette_cat'), run: () => location.href = 'gallery.html?cat=' + encodeURIComponent(c.name), sec: t('palette_cat')
            });
          }
        });
        smartSearch(App.ALL, q).slice(0, 12).forEach(s => {
          items.push({
            ico: '💡', t1: s.title || ('#' + s.id), t2: s.category + ' · ID #' + s.id,
            run: () => { closeOverlay('fxPalette'); App.openLightbox(s.id); }, sec: t('palette_prompt')
          });
        });
      }
      palItems = items; palIdx = 0;
      const list = $('#palList', el);
      if (!items.length) { list.innerHTML = '<div class="fx-note" style="padding:22px;text-align:center">' + t('palette_empty') + '</div>'; return; }
      let html2 = '', lastSec = '';
      items.forEach((it, i) => {
        if (it.sec !== lastSec) { html2 += '<div class="cmdk-sec">' + esc(it.sec) + '</div>'; lastSec = it.sec; }
        html2 += `<button class="cmdk-item ${i === palIdx ? 'on' : ''}" data-i="${i}">
          <span class="ico">${it.ico}</span>
          <span class="tx"><span class="t1">${esc(it.t1)}</span>${it.t2 ? '<span class="t2">' + esc(it.t2) + '</span>' : ''}</span>
        </button>`;
      });
      list.innerHTML = html2;
      $$('.cmdk-item', list).forEach(b => {
        b.addEventListener('click', () => { const it = palItems[+b.dataset.i]; if (it) { closeOverlay('fxPalette'); it.run(); } });
        b.addEventListener('mousemove', () => { palIdx = +b.dataset.i; paint(); });
      });
      list.scrollTop = 0;
    };
    function paint() {
      const list = $('#palList', el); if (!list) return;
      $$('.cmdk-item', list).forEach(b => b.classList.toggle('on', +b.dataset.i === palIdx));
      const cur = $('.cmdk-item.on', list);
      if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: 'nearest' });
    }
    input.addEventListener('input', render);
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { e.preventDefault(); palIdx = clamp(palIdx + 1, 0, palItems.length - 1); paint(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); palIdx = clamp(palIdx - 1, 0, palItems.length - 1); paint(); }
      else if (e.key === 'Enter') { const it = palItems[palIdx]; if (it) { closeOverlay('fxPalette'); it.run(); } }
    });
    render(); openOverlay('fxPalette');
    setTimeout(() => input.focus(), 50);
  }

  /* ================= 快捷键帮助 ================= */
  function openHelp() {
    const rows = [
      ['Ctrl / ⌘ + K', t('help_palette')], ['/', t('help_focus')], ['R', t('help_random')],
      ['T', t('help_theme')], ['C', t('help_copy')],
      ['← / →', t('help_nav')], ['Esc', t('help_close')], ['?', t('help_help')],
    ];
    const html = `<div class="fx-panel" style="width:min(560px,100%)">
      <div class="fx-head"><div><h3>${esc(t('help_title'))}</h3></div>
        <button class="x" data-fxclose>✕</button></div>
      <div class="fx-body"><div class="kbd-grid">
        ${rows.map(r => `<div class="r"><span>${esc(r[1])}</span><kbd>${esc(r[0])}</kbd></div>`).join('')}
      </div></div></div>`;
    overlay('fxHelp', '', html); openOverlay('fxHelp');
  }

  /* ================= 灯箱增强 ================= */
  let LB = { id: null, list: [] };
  const lastList = { ids: [] };
  function lbOpen(id, list) {
    LB.id = id;
    if (list && list.length) lastList.ids = list.map(x => (typeof x === 'object' ? x.id : x));
    const s = App.findSample(id);
    if (s) { tagsFor(s); }
    decorateLightbox();
  }
  function lbStep(dir) {
    const ids = lastList.ids.length ? lastList.ids : App.ALL.map(s => s.id);
    if (!ids.length) return;
    let i = ids.indexOf(LB.id);
    if (i < 0) i = 0;
    const nid = ids[(i + dir + ids.length) % ids.length];
    App.openLightbox(nid);
  }
  function decorateLightbox() {
    const body = $('#lbBody'); if (!body) return;
    const id = LB.id != null ? LB.id : body.querySelector('[data-id]') && +body.querySelector('[data-id]').dataset.id;
    const s = App.findSample(id); if (!s) return;
    if (body.dataset.decorated === String(id)) return;
    body.dataset.decorated = String(id);
    const tg = flatTags(s);
    const chip = $('.lb-tags', body);
    if (chip && tg.length) {
      tg.slice(0, 8).forEach(x => {
        const b = document.createElement('span'); b.className = 'tag'; b.textContent = x;
        b.style.cursor = 'pointer'; b.title = '按此标签搜索';
        b.addEventListener('click', () => location.href = 'search.html?q=' + encodeURIComponent(x));
        chip.appendChild(b);
      });
    }
    // 使用次数 + 备注
    const uc = useCount(s.id);
    const nt = noteFor(s.id);
    const info = document.createElement('div');
    info.className = 'lb-meta';
    info.innerHTML = `<span>${esc(t('uses'))} <b id="lbUseCount" style="color:var(--garden)">${uc}${esc(t('times'))}</b></span>
      ${nt ? '<span style="color:var(--garden)">📝 ' + esc(t('has_note')) + '</span>' : ''}
      <span style="opacity:.7">${esc(t('lb_navigate'))}</span>`;
    body.insertBefore(info, body.querySelector('.lb-actions'));
    // 动作栏增强
    const acts = body.querySelector('.lb-actions');
    if (acts) {
      const mk = (label, fn, solid, ico) => {
        const b = document.createElement('button');
        b.className = 'mini-btn' + (solid ? ' solid' : '');
        b.innerHTML = (ico || '') + esc(label);
        b.addEventListener('click', fn); return b;
      };
      const vars = parseVars(s.prompt || '');
      const bar = document.createElement('div'); bar.className = 'act-bar'; bar.style.marginTop = '10px';
      bar.appendChild(mk(vars.length ? t('fill_and_copy') : t('copy_prompt'), () => openVarFill(s.id), true, '✍️ '));
      bar.appendChild(mk('换一个', () => randomPrompt(), false, '🎲 '));
      bar.appendChild(mk(t('dl_img'), () => downloadImage(s), false, '⬇️ '));
      bar.appendChild(mk(t('share'), () => { App.copyText(location.origin + location.pathname + '#id=' + s.id); App.toast(t('share_done')); }, false, '🔗 '));
      bar.appendChild(mk(t('used_mark'), () => {
        bumpUse(s.id);
        const el = document.getElementById('lbUseCount');
        if (el) el.textContent = useCount(s.id) + t('times');
        App.toast(t('uses') + ' ' + useCount(s.id) + t('times'));
      }, false, '✅ '));
      bar.appendChild(mk(t('copy_json'), () => App.copyText(JSON.stringify({ id: s.id, title: s.title, category: s.category, tags: tg, prompt: s.prompt || '' }, null, 2)), false, '{} '));
      bar.appendChild(mk(t('copy_md'), () => App.copyText(itemToMD(s)), false, 'M↓ '));
      const wrap = document.createElement('div');
      wrap.style.cssText = 'margin-top:12px;border-top:1px dashed var(--line);padding-top:12px';
      wrap.innerHTML = `<div class="note-box"><div class="nh">📝 ${esc(t('note_title'))}</div>
        <textarea id="lbNote" placeholder="${esc(t('note_ph'))}"></textarea>
        <div class="meta"><span id="lbNoteInfo"></span></div></div>`;
      const ta = $('#lbNote', wrap);
      ta.value = nt;
      ta.addEventListener('input', () => {
        setNote(s.id, ta.value);
        const inf = $('#lbNoteInfo', wrap);
        if (inf) inf.textContent = ta.value.trim() ? t('note_saved') : '';
      });
      body.appendChild(bar); body.appendChild(wrap);
    }
    // 翻页按钮：左右大箭头压在图片两侧，并带位置计数
    const panel = $('.lb-panel');
    if (panel) {
      let nav = $('.lb-img-nav', panel);
      if (!nav) {
        nav = document.createElement('div'); nav.className = 'lb-img-nav';
        const pb = document.createElement('button'); pb.className = 'lb-nav lb-prev'; pb.setAttribute('aria-label', t('lb_prev') || '上一张'); pb.innerHTML = '‹';
        const nb = document.createElement('button'); nb.className = 'lb-nav lb-next'; nb.setAttribute('aria-label', t('lb_next') || '下一张'); nb.innerHTML = '›';
        pb.addEventListener('click', e => { e.stopPropagation(); lbStep(-1); });
        nb.addEventListener('click', e => { e.stopPropagation(); lbStep(1); });
        nav.appendChild(pb); nav.appendChild(nb);
        const cnt = document.createElement('div'); cnt.className = 'lb-count'; nav.appendChild(cnt);
        window.__lbCount = cnt;
        panel.appendChild(nav);
      }
      const cntEl = window.__lbCount;
      if (cntEl) {
        const ids = lastList.ids.length ? lastList.ids : App.ALL.map(x => x.id);
        const i = ids.indexOf(LB.id);
        cntEl.textContent = (i >= 0 ? i + 1 : '?') + ' / ' + ids.length;
      }
    }
  }
  function decorateLightboxReset() {
    const body = $('#lbBody'); if (body) body.dataset.decorated = '';
    decorateLightbox();
  }

  /* ================= 随机漫游 ================= */
  function randomPrompt() {
    const list = App.ALL; if (!list.length) return;
    const pick = list[Math.floor(Math.random() * list.length)];
    lastList.ids = list.map(s => s.id);
    App.openLightbox(pick.id);
  }

  /* ================= 分面 / 筛选 UI ================= */
  const filters = { facets: {}, hasImage: false, hasNote: false, favOnly: false, usedOnly: false };
  const hasFacet = () => Object.keys(filters.facets).some(k => (filters.facets[k] || []).length);
  function toggleFacet(facet, name) {
    const cur = filters.facets[facet] || (filters.facets[facet] = []);
    if (cur.length && cur[0] === name) cur.length = 0;   // 再点已选项 = 取消
    else { cur.length = 0; cur.push(name); }             // 单选：选新项清空同组其他
  }
  function syncFacetGroup(container, facet){
    $$('.facet-chip[data-n]', container).forEach(x => {
      if (x.dataset.f === facet) x.classList.toggle('on', (filters.facets[facet] || []).includes(x.dataset.n));
    });
  }
  function applyFilters(list) {
    let out = list;
    if (hasFacet()) {
      out = out.filter(s => {
        const g = tagsFor(s);
        return Object.keys(filters.facets).every(f => {
          const sel = filters.facets[f] || [];
          if (!sel.length) return true;
          return sel.some(x => (g[f] || []).includes(x));
        });
      });
    }
    if (filters.hasImage) out = out.filter(s => !!s.image);
    if (filters.hasNote) out = out.filter(s => !!noteFor(s.id));
    if (filters.favOnly) out = out.filter(s => App.isFav(s.id));
    if (filters.usedOnly) out = out.filter(s => useCount(s.id) > 0);
    return out;
  }
  function renderFacets(container, pool, onChange) {
    if (!container) return;
    const counts = {};
    pool.forEach(s => { const g = tagsFor(s); for (const f in g) g[f].forEach(n => { (counts[f] = counts[f] || {})[n] = (counts[f][n] || 0) + 1; }); });
    const LABEL = { 媒介: t('facet_medium'), 风格: t('facet_style'), 色调: t('facet_tone') };
    let html = '';
    for (const facet in TAG_DICT) {
      const c = counts[facet]; if (!c) continue;
      const names = Object.keys(c).sort((a, b) => c[b] - c[a]);
      const top = names.slice(0, 10);
      const sel = filters.facets[facet] || [];
      const chips = top.map(n => `<button class="facet-chip ${sel.includes(n) ? 'on' : ''}" data-f="${esc(facet)}" data-n="${esc(n)}">${esc(n)}<span class="n">${c[n]}</span></button>`).join('');
      const more = names.length > 10 ? `<button class="facet-chip more" data-more="${esc(facet)}">+${names.length - 10} ${esc(t('facet_more'))}</button>` : '';
      html += `<div class="frow"><div class="flabel">${esc(LABEL[facet] || facet)}</div><div class="fopts">${chips}${more}</div></div>`;
    }
    html += `<div class="frow" style="justify-content:flex-end"><button class="fclear" id="fxFacetClear">${esc(t('facet_clear'))}</button></div>`;
    container.className = 'facets';
    container.innerHTML = html;
    $$('.facet-chip[data-n]', container).forEach(b => b.addEventListener('click', () => {
      toggleFacet(b.dataset.f, b.dataset.n);
      syncFacetGroup(container, b.dataset.f);   // 单选：刷新同组兄弟高亮
      onChange && onChange();
    }));
    $$('.facet-chip[data-more]', container).forEach(b => b.addEventListener('click', () => {
      const facet = b.dataset.more; const c = counts[facet];
      const names = Object.keys(c).sort((a, bb) => c[bb] - c[a]);
      const sel = filters.facets[facet] || [];
      const row = b.closest('.fopts');
      row.innerHTML = names.map(n => `<button class="facet-chip ${sel.includes(n) ? 'on' : ''}" data-f="${esc(facet)}" data-n="${esc(n)}">${esc(n)}<span class="n">${c[n]}</span></button>`).join('');
      $$('.facet-chip[data-n]', row).forEach(x => x.addEventListener('click', () => {
        toggleFacet(x.dataset.f, x.dataset.n);
        syncFacetGroup(container, x.dataset.f);   // 单选：刷新同组兄弟高亮
        onChange && onChange();
      }));
    }));
    const clr = $('#fxFacetClear', container);
    if (clr) clr.addEventListener('click', () => { filters.facets = {}; renderFacets(container, pool, onChange); onChange && onChange(); });
  }
  function renderFilterBar(container, onChange) {
    if (!container) return;
    const mk = (key, label) => `<button class="switch ${filters[key] ? 'on' : ''}" data-k="${key}"><span class="dot"></span>${esc(label)}</button>`;
    container.className = 'filter-bar';
    container.innerHTML = `<span class="fb-label">筛选</span>` +
      mk('hasImage', t('filter_only_img')) + mk('hasNote', t('filter_only_note')) +
      mk('favOnly', t('filter_fav')) + mk('usedOnly', t('filter_used'));
    $$('.switch', container).forEach(b => b.addEventListener('click', () => {
      filters[b.dataset.k] = !filters[b.dataset.k];
      b.classList.toggle('on', filters[b.dataset.k]);
      onChange && onChange();
    }));
  }

  /* ================= 卡片增强（标签 / 备注点 / 高亮） ================= */
  let lastQuery = '';
  function decorateCards(root, q) {
    if (!root) return;
    $$('.card', root).forEach(card => {
      const id = +card.dataset.id;
      const s = App.findSample(id); if (!s) return;
      const body = $('.body', card); if (!body) return;
      if (!body.dataset.deco) {
        body.dataset.deco = '1';
        const tg = flatTags(s).slice(0, 3);
        if (tg.length) {
          const tl = document.createElement('div'); tl.className = 'tagline';
          tl.innerHTML = tg.map(x => '<span>' + esc(x) + '</span>').join('');
          body.appendChild(tl);
        }
        if (noteFor(s.id)) {
          const dot = document.createElement('span'); dot.className = 'note-dot'; dot.title = t('note_title');
          card.appendChild(dot);
        }
        // 卡片级快捷操作（复制成品 / 下载）
        const thumb = $('.thumb', card);
        if (thumb) {
          const acts = $('.hover-actions', thumb);
          if (acts && !$('[data-fx-dl]', acts)) {
            const dl = document.createElement('button');
            dl.className = 'act'; dl.dataset.fxDl = id; dl.title = t('dl_img');
            dl.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 19h16" stroke-linecap="round" stroke-linejoin="round"/></svg>';
            dl.addEventListener('click', e => { e.preventDefault(); e.stopPropagation(); downloadImage(s); });
            acts.appendChild(dl);
          }
        }
      }
      // 高亮
      if (q) {
        const tt = $('.title', body);
        if (tt) tt.innerHTML = highlight(s.title, q);
      }
    });
  }

  /* ================= 布局注入：分面 / 筛选 ================= */
  let facetsRefresh = null;
  function injectGalleryExtras() {
    const grid = $('#grid'); if (!grid) return;
    let host = $('#fxFacetHost');
    if (!host) {
      host = document.createElement('div'); host.id = 'fxFacetHost';
      const anchor = $('.gallery-layout > section') || grid.parentElement;
      if (anchor && anchor.firstChild) anchor.insertBefore(host, anchor.firstChild);
      else if (anchor) anchor.appendChild(host);
    }
    let fbar = $('#fxFilterBar');
    if (!fbar) {
      fbar = document.createElement('div'); fbar.id = 'fxFilterBar';
      host.parentElement.insertBefore(fbar, host.nextSibling);
    }
    const rebuild = () => {
      lastQuery = $('#galSearch') ? $('#galSearch').value.trim() : '';
      const base = galleryPool();
      renderFacets(host, base, () => { fbar._onChange && fbar._onChange(); });
      renderFilterBar(fbar, () => { fbar._onChange && fbar._onChange(); });
    };
    fbar._onChange = () => { if (typeof window.__fxGalleryRefresh === 'function') window.__fxGalleryRefresh(); };
    window.__fxRebuildFacets = rebuild;
    facetsRefresh = rebuild;
    rebuild();
  }
  function galleryPool() {
    // 画廊页可注入 window.__fxFacetPool 给出「当前分类下」的池子，让标签计数跟随分类变化
    return (typeof window.__fxFacetPool === 'function') ? window.__fxFacetPool() : App.ALL;
  }

  /* ================= 页面装配 ================= */
  function page() { return (document.body && document.body.dataset.page) || ''; }

  // 收起移动端汉堡菜单（点菜单项后立即收起，避免菜单遮住刚打开的弹层）
  function closeMobileMenu() {
    const nl = $('#navLinks'), tg = $('#navToggle');
    if (nl) nl.classList.remove('open');
    if (tg) { tg.classList.remove('open'); tg.setAttribute('aria-expanded', 'false'); }
  }

  function wireHeader() {
    const actions = $('.nav-actions');
    // 命令面板：导航右侧的显式入口（导航搜索框已按需求移除，搜索由命令面板承担）
    if (actions && !$('#openPaletteBtn')) {
      const b = document.createElement('button');
      b.className = 'tool-btn'; b.id = 'openPaletteBtn'; b.type = 'button';
      b.title = t('palette') + '（Ctrl / ⌘ + K）';
      b.setAttribute('aria-label', t('palette'));
      b.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M16 16L21 21" stroke-linecap="round"/></svg>'
        + '<span class="tlabel">' + esc(t('palette')) + '</span><kbd>⌘K</kbd>';
      b.addEventListener('click', openPalette);
      actions.insertBefore(b, actions.firstChild);
    }
    // 语言切换：仅当显式开启时才出现；否则移除任何残留按钮（含历史遗留的）
    if (!ENABLE_LANG_SWITCH) {
      const old = $('#langBtn'); if (old) old.remove();
    } else if (actions && !$('#langBtn')) {
      const b = document.createElement('button');
      b.className = 'tool-btn icon-only lang-btn'; b.id = 'langBtn'; b.title = 'Language';
      b.textContent = lang === 'zh' ? 'EN' : '中';
      b.addEventListener('click', toggleLang);
      const pb = $('#openPaletteBtn');
      actions.insertBefore(b, pb ? pb.nextSibling : actions.firstChild);
    }
    // 移动端（≤1000px 收成汉堡菜单）里的入口：
    // 手机端顶栏只保留「语言 / 版本 / 主题」三个按钮，其余全部收进这里。
    const navLinks = $('#navLinks');
    if (navLinks && !$('#mobilePaletteBtn')) {
      const mb = document.createElement('button');
      mb.id = 'mobilePaletteBtn'; mb.className = 'nav-link only-mobile'; mb.type = 'button';
      mb.textContent = t('palette');
      mb.addEventListener('click', () => {
        closeMobileMenu();
        openPalette();
      });
      navLinks.appendChild(mb);
    }
    // 移动端菜单里的「投稿」——与桌面端同源，只换位置。
    // 注意：「收藏」不再单独添加，导航里本来就有「收藏」链接，重复添加会出现两项。
    if (navLinks && !$('#mobileSubmitLink')) {
      const ms = document.createElement('a');
      ms.id = 'mobileSubmitLink'; ms.className = 'nav-link only-mobile';
      ms.href = 'submit.html';
      ms.textContent = t('nav_submit');
      navLinks.appendChild(ms);
    }
    // 菜单里点击任意链接后收起菜单
    if (navLinks && !navLinks.dataset.fxCloseWired) {
      navLinks.dataset.fxCloseWired = '1';
      navLinks.addEventListener('click', e => {
        if (e.target.closest('a')) closeMobileMenu();
      });
    }
    // 兜底：老页面若还残留导航搜索框，仍保留回车跳搜索
    const ns = $('#navSearchInput');
    if (ns) {
      ns.placeholder = t('search_ph');
      ns.addEventListener('keydown', e => {
        if (e.key === 'Enter' && ns.value.trim()) {
          location.href = 'search.html?q=' + encodeURIComponent(ns.value.trim());
        }
      });
    }
  }
  function applyI18n() {
    document.documentElement.setAttribute('lang', lang === 'en' ? 'en' : 'zh-CN');

    // 1) data-i18n → innerHTML（值由我们编写，可含少量标记）
    $$('[data-i18n]').forEach(el => {
      const k = el.dataset.i18n;
      const raw = (I18N[lang] && I18N[lang][k]) != null ? I18N[lang][k]
        : (I18N.zh[k] != null ? I18N.zh[k] : null);
      if (raw == null) return;
      let v = raw;
      // 带 {占位符} 的文案：从数据里补值
      const prov = PLACEHOLDER_KEYS[k];
      if (prov && typeof raw === 'string' && raw.indexOf('{') >= 0) {
        const vals = prov();
        v = raw.replace(/\{(\w+)\}/g, (m, g) => (vals[g] != null ? String(vals[g]) : m));
      }
      if (el.tagName === 'TITLE') el.textContent = v; else el.innerHTML = v;
    });

    // 2) placeholder / title 属性
    $$('[data-i18n-placeholder]').forEach(el => { const v = t(el.dataset.i18nPlaceholder); if (v) el.placeholder = v; });
    $$('[data-i18n-title]').forEach(el => { const v = t(el.dataset.i18nTitle); if (v) el.title = v; });

    // 3) 文档标题
    const docKey = {
      index: 'doc_index', gallery: 'doc_gallery', categories: 'doc_categories', search: 'doc_search',
      detail: 'doc_detail', favorites: 'doc_favorites', about: 'doc_about', sponsor: 'doc_sponsor',
      submit: 'doc_submit', '404': 'doc_404'
    }[page()];
    if (docKey) document.title = t(docKey);

    // 4) 导航（HTML 里已有 data-i18n 时是二次保险，同时也覆盖动态注入的项）
    const map = {
      index: 'nav_home', gallery: 'nav_gallery', categories: 'nav_categories',
      search: 'nav_search', favorites: 'nav_favorites', about: 'nav_about'
    };
    $$('.nav-link').forEach(a => { const k = map[a.dataset.page]; if (k) a.textContent = t(k); });
    const subBtn = $('.nav-actions .btn-amber'); if (subBtn) subBtn.textContent = t('nav_submit');

    // 5) JS 动态生成的元素（data-i18n 管不到）
    const pb = $('#openPaletteBtn');
    if (pb) {
      pb.title = t('title_palette') + (lang === 'en' ? ' (Ctrl / ⌘ + K)' : '（Ctrl / ⌘ + K）');
      pb.setAttribute('aria-label', t('palette'));
      const lbl = pb.querySelector('.tlabel'); if (lbl) lbl.textContent = t('palette');
    }
    const mb = $('#mobilePaletteBtn'); if (mb) mb.textContent = t('palette');
    const ms = $('#mobileSubmitLink'); if (ms) ms.textContent = t('nav_submit');
    const langBtn = $('#langBtn'); if (langBtn) langBtn.textContent = lang === 'zh' ? 'EN' : '中';
    // 版本切换按钮：base.js 会写文字，这里按它记录的语义纠正语言。
    // 手机端这个按钮收成圆形「⇄」图标（文字被 CSS 藏起），故一并写 title，保证可读。
    const ss = $('#skinSwitch');
    if (ss) {
      const label = ss.dataset.skin
        ? t(ss.dataset.skin === 'classic' ? 'skin_classic' : 'skin_modern')
        : ss.textContent.trim();
      if (ss.dataset.skin) ss.textContent = label;
      ss.title = t('title_skin') + (label ? ' · ' + label : '');
      ss.setAttribute('aria-label', t('title_skin') + (label ? ' · ' + label : ''));
    }
    const th = $('#themeBtn'); if (th) th.title = t('title_theme');
    const favA = $$('.nav-actions > a.icon-btn')[0];
    if (favA) favA.title = t('title_fav');

    // 6) 数据驱动的总数 / 分类数：让硬编码处跟随 meta.json，避免与真实数据脱节
    $$('[data-sx-count]').forEach(el => {
      const k = el.dataset.sxCount;
      const v = k === 'total' ? App.D.total
              : k === 'majors' ? App.D.majors.length
              : k === 'subs' ? App.D.subCount
              : null;
      if (v != null) el.textContent = Number(v).toLocaleString('en-US');
    });
  }

  // 需要从运行数据补值的文案
  const PLACEHOLDER_KEYS = {
    idx_lead: () => ({ total: fmtNum(App.D.total), mj: App.D.majors.length, sb: App.D.subCount }),
    idx_cats_eyebrow: () => ({ mj: App.D.majors.length, sb: App.D.subCount }),
    idx_see_all: () => ({ total: fmtNum(App.D.total) }),
    cat_sub: () => ({ mj: App.D.majors.length, sb: App.D.subCount, total: fmtNum(App.D.total) }),
    sp_p: () => ({ total: fmtNum(App.D.total) })
  };
  const fmtNum = n => Number(n || 0).toLocaleString('en-US');
  function toggleLang() {
    const next = lang === 'zh' ? 'en' : 'zh';
    lang = next;
    store.set(LS.lang, next);
    // 直接重载，而不是就地替换：卡片、分类名、筛选项、合集等都是按语言渲染的，
    // 就地替换必然漏掉动态内容（之前正是因此出现"导航是英文、按钮是中文"的割裂）。
    try { location.reload(); } catch (e) { }
  }

  function wireGallery() {
    // 只负责注入「分面 + 筛选栏」两块 UI；输入框与渲染由 gallery.html 自己驱动
    injectGalleryExtras();
  }

  function wireSearch() {
    const grid = $('#grid');
    const sec = grid ? grid.parentElement : null;
    if (!sec) return;
    let host = $('#fxFacetHost');
    if (!host) { host = document.createElement('div'); host.id = 'fxFacetHost'; sec.insertBefore(host, sec.firstChild); }
    let fbar = $('#fxFilterBar');
    if (!fbar) { fbar = document.createElement('div'); fbar.id = 'fxFilterBar'; sec.insertBefore(fbar, host.nextSibling); }
    const refresh = () => { if (typeof window.__fxSearchRefresh === 'function') window.__fxSearchRefresh(); };
    fbar._onChange = refresh;
    facetsRefresh = () => { renderFacets(host, App.ALL, refresh); renderFilterBar(fbar, refresh); };
    facetsRefresh();
  }

  function wireDetail() {
    const body = $('.detail-body'); if (!body) return;
    const id = +new URLSearchParams(location.search).get('id');
    const s = App.findSample(id); if (!s) return;
    const tg = flatTags(s);
    const tagRow = $('#detailMount .lb-tags');
    if (tagRow && tg.length) {
      tg.slice(0, 8).forEach(x => {
        const b = document.createElement('span'); b.className = 'tag'; b.textContent = x; b.style.cursor = 'pointer';
        b.addEventListener('click', () => location.href = 'search.html?q=' + encodeURIComponent(x));
        tagRow.appendChild(b);
      });
    }
    // 动作增强
    const acts = $('#detailMount .lb-actions');
    if (acts && !$('#fxDetailBar')) {
      const bar = document.createElement('div'); bar.className = 'act-bar'; bar.id = 'fxDetailBar'; bar.style.marginTop = '10px';
      const mk = (label, fn, solid) => { const b = document.createElement('button'); b.className = 'mini-btn' + (solid ? ' solid' : ''); b.textContent = label; b.addEventListener('click', fn); return b; };
      bar.appendChild(mk(t('fill_and_copy'), () => openVarFill(s.id), true));
      bar.appendChild(mk(t('dl_img'), () => downloadImage(s)));
      bar.appendChild(mk(t('share'), () => { App.copyText(location.origin + location.pathname + '#id=' + s.id); App.toast(t('share_done')); }));
      bar.appendChild(mk(t('copy_json'), () => App.copyText(JSON.stringify({ id: s.id, title: s.title, category: s.category, tags: tg, prompt: s.prompt || '' }, null, 2))));
      bar.appendChild(mk(t('copy_md'), () => App.copyText(itemToMD(s))));
      acts.parentElement.insertBefore(bar, acts.nextSibling);
      const nb = document.createElement('div'); nb.className = 'note-box'; nb.style.marginTop = '14px';
      nb.innerHTML = `<div class="nh">📝 ${esc(t('note_title'))}</div>
        <textarea id="fxDetailNote" placeholder="${esc(t('note_ph'))}"></textarea>
        <div class="meta"><span id="fxNoteInfo"></span><span>${esc(t('uses'))} ${useCount(s.id)}${esc(t('times'))}</span></div>`;
      bar.parentElement.insertBefore(nb, bar.nextSibling);
      const ta = $('#fxDetailNote');
      ta.value = noteFor(s.id);
      ta.addEventListener('input', () => { setNote(s.id, ta.value); $('#fxNoteInfo').textContent = ta.value.trim() ? t('note_saved') : ''; });
    }
  }

  function wireCollections() {
    // 收藏页（favorites.html）自带完整合集管理工具条；这里只在页面缺导入入口时补一个
    if (!$('#boardTabs') || $('#colImportBtn')) return;
    // 由 favorites.html 自身的脚本渲染；此处仅把增强操作挂到工具条
    const bar = $('.board-bar'); if (!bar || $('#fxColTools')) return;
    const tools = document.createElement('div');
    tools.className = 'col-tools'; tools.id = 'fxColTools';
    const mk = (label, fn) => { const b = document.createElement('button'); b.className = 'btn btn-soft'; b.textContent = label; b.addEventListener('click', fn); return b; };
    const fileIn = document.createElement('input');
    fileIn.type = 'file'; fileIn.accept = '.json'; fileIn.style.display = 'none';
    fileIn.addEventListener('change', () => {
      const f = fileIn.files && fileIn.files[0]; if (!f) return;
      const rd = new FileReader();
      rd.onload = () => { importJSON(String(rd.result)); if (window.__fxCollectionsReload) window.__fxCollectionsReload(); };
      rd.readAsText(f); fileIn.value = '';
    });
    tools.appendChild(mk(t('col_import'), () => fileIn.click()));
    tools.appendChild(fileIn);
    bar.parentElement.insertBefore(tools, bar.nextSibling);
  }

  /* ================= 深链 ================= */
  function handleHash() {
    const m = (location.hash || '').match(/#(?:id|p)=(\d+)/);
    if (!m) return;
    const id = +m[1];
    if (App.findSample(id)) {
      lastList.ids = App.ALL.map(s => s.id);
      App.openLightbox(id);
    } else {
      App.ensureFull().then(() => { if (App.findSample(id)) App.openLightbox(id); });
    }
  }

  /* ================= LQIP 图片观察 ================= */
  function watchImages() {
    const mark = img => {
      if (img.dataset.lqipReady) return;
      img.dataset.lqipReady = '1';
      img.classList.add('lqip');
      const done = () => img.classList.add('done');
      if (img.complete && img.naturalWidth) { done(); return; }
      img.addEventListener('load', done, { once: true });
      img.addEventListener('error', done, { once: true });
    };
    const scan = root => { $$('img.ph-img', root || document).forEach(mark); };
    scan();
    const mo = new MutationObserver(muts => {
      muts.forEach(m => {
        m.addedNodes && m.addedNodes.forEach(n => {
          if (n.nodeType !== 1) return;
          if (n.tagName === 'IMG' && n.classList.contains('ph-img')) mark(n);
          else if (n.querySelectorAll) $$('img.ph-img', n).forEach(mark);
        });
        if (m.type === 'attributes' && m.target.tagName === 'IMG') mark(m.target);
      });
    });
    mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['src'] });
  }

  /* ================= 键盘快捷键 ================= */
  function wireKeys() {
    document.addEventListener('keydown', e => {
      const tag = (e.target.tagName || '').toLowerCase();
      const typing = tag === 'input' || tag === 'textarea' || e.target.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPalette(); return; }
      if (typing) {
        if (e.key === 'Escape' && e.target.closest('.fx-overlay')) closeOverlay(e.target.closest('.fx-overlay').id);
        return;
      }
      const lbOpen = $('#sx-lightbox') && $('#sx-lightbox').classList.contains('open');
      switch (e.key) {
        case '/': {
          const box = $('#bigSearch') || $('#galSearch') || $('#navSearchInput');
          e.preventDefault();
          if (box) box.focus(); else openPalette();
          break;
        }
        case 'r': case 'R': randomPrompt(); break;
        case 't': case 'T': { const b = $('#themeBtn'); if (b) b.click(); break; }
        case '?': openHelp(); break;
        case 'ArrowLeft': if (lbOpen) lbStep(-1); break;
        case 'ArrowRight': if (lbOpen) lbStep(1); break;
        case 'c': case 'C': if (lbOpen && LB.id != null) { const s = App.findSample(LB.id); if (s) { App.copyText(s.prompt || ''); bumpUse(s.id); } } break;
        case 'Escape': closeMenus(); break;
      }
    });
  }

  /* ================= 浮动骰子 ================= */
  function addDice() {
    if ($('#fxDice')) return;
    const b = document.createElement('button');
    b.id = 'fxDice'; b.className = 'dice-btn'; b.title = t('cmd_random') + ' (R)';
    b.textContent = '🎲';
    b.addEventListener('click', randomPrompt);
    document.body.appendChild(b);
  }

  /* ================= PWA ================= */
  function registerPWA() {
    if (!('serviceWorker' in navigator)) return;
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') return;
    navigator.serviceWorker.register('sw.js').catch(() => { });
  }

  /* ================= 导出入口 ================= */
  function exportActiveBoard() {
    const B = loadBoards(); const board = activeBoard(B);
    if (!board.items.length) { App.toast(t('col_empty_export')); return; }
    closeMenus();
    const menu = document.createElement('div');
    menu.className = 'menu open';
    menu.style.cssText = 'position:fixed;left:50%;bottom:80px;transform:translateX(-50%);z-index:220';
    menu.innerHTML = `<div class="mh">${esc(tf('exp_label', { name: board.name, n: board.items.length }))}</div>
      <button data-x="md">${esc(t('exp_md'))}</button>
      <button data-x="json">${esc(t('exp_json'))}</button>
      <button data-x="csv">${esc(t('exp_csv'))}</button>
      <div class="sep"></div>
      <button data-x="copy">${esc(t('exp_copy'))}</button>`;
    document.body.appendChild(menu); openMenuEl = menu;
    menu.addEventListener('click', e => {
      const b = e.target.closest('[data-x]'); if (!b) return;
      const k = b.dataset.x;
      if (k === 'md') downloadBlob(boardToMD(B, board), board.name + '.md', 'text/markdown;charset=utf-8');
      else if (k === 'json') downloadBlob(boardToJSON(board), board.name + '.json', 'application/json;charset=utf-8');
      else if (k === 'csv') downloadBlob(boardToCSV(board), board.name + '.csv', 'text/csv;charset=utf-8');
      else if (k === 'copy') {
        const txt = board.items.map(id => App.findSample(id)).filter(Boolean).map(s => s.prompt || '').join('\n\n---\n\n');
        App.copyText(txt);
      }
      closeMenus();
    });
  }

  /* ================= 装配 ================= */
  const FX = {
    t, tf, catName, fmtNum, esc,
    lang: () => lang, setLang: l => { lang = l; store.set(LS.lang, l); },
    applyI18n, toggleLang, dict: I18N, catEn: CAT_EN,
    tagsFor, flatTags,
    clearTagCache,
    parseVars, resolveVars, openVarFill,
    smartSearch, smartScore, highlight, initials, loadPinyin,
    noteFor, setNote, useCount, bumpUse,
    loadBoards, saveBoards, activeBoard,
    itemToMD, boardToMD, boardToCSV, boardToJSON, importJSON,
    downloadImage, downloadBoardImages, downloadBlob,
    openPalette, openHelp, randomPrompt,
    filters, applyFilters, renderFacets, renderFilterBar, hasFacet,
    decorateCards, exportActiveBoard, overlay, openOverlay, closeOverlay,
    setQuery: q => { lastQuery = q || ''; },
    refreshFacets: () => { if (facetsRefresh) { try { facetsRefresh(); } catch (e) { } } },
    lastList, lbOpen,
    lang_pack: I18N,
  };
  window.FX = FX;

  // 包装 openLightbox，跟踪上下文
  function wrapLightbox() {
    if (App.__fxWrapped) return;
    const orig = App.openLightbox;
    App.openLightbox = function (id) {
      LB.id = id;
      const cur = window.__fxCurrentList;
      if (cur && cur.length && cur.indexOf(id) >= 0) lastList.ids = cur.slice();
      else if (!lastList.ids.length) lastList.ids = App.ALL.map(x => x.id);
      const r = orig.apply(this, arguments);
      decorateLightbox();
      return r;
    };
    const origRender = App.renderCards;
    App.renderCards = function (list, container) {
      const r = origRender.call(this, list, container);
      window.__fxCurrentList = (list || []).map(x => x.id);
      decorateCards(container, lastQuery);
      return r;
    };
    App.__fxWrapped = true;
  }

  function boot() {
    wrapLightbox();
    wireHeader(); applyI18n();
    const p = page();
    if (p === 'gallery') wireGallery();
    if (p === 'search') wireSearch();
    if (p === 'detail') wireDetail();
    if (p === 'favorites') wireCollections();
    addDice(); wireKeys(); watchImages(); handleHash(); registerPWA();
    loadPinyin().then(() => { if (window.__fxSearchRefresh) window.__fxSearchRefresh(); });
  }

  let booted = false;
  function ready() { if (booted) return; booted = true; try { boot(); } catch (e) { console.error('[fx]', e); } }
  window.addEventListener('sx:ready', ready);
  // 兜底：若事件早于本脚本，轮询等待
  (function poll(n) {
    if (window.App && App.D && App.D.samples && App.D.samples.length) { ready(); return; }
    if (n > 200) return;
    setTimeout(() => poll(n + 1), 60);
  })(0);
})();
