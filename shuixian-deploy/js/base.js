/* ===== 水仙的 AI 提示词 —— 公共脚本 ===== */

const App = (() => {
  // ---------- 配置 ----------
  const ASSET_VERSION = '6'; // 每次更新静态资源（CSS/JS/组件）时递增，强制刷新 CDN 缓存
  const CATEGORIES = ["全部","真人/写实人物","动漫/二次元人物","字体/排版/标题","Logo/品牌/VI","UI/App/网页/SaaS","产品/电商/包装","海报/广告/社媒","插画/艺术/概念","漫画/分镜/故事板","信息图/教育图解","3D/游戏/像素/等距","建筑/室内/空间","风景/自然","动物/宠物","车辆/机械/科幻","抽象/纹理/背景","其他/未归类"];
  const CAT_KEYS = {
    "全部":"全部","真人/写实人物":"真人写实人物","动漫/二次元人物":"动漫二次元人物","字体/排版/标题":"字体排版标题",
    "Logo/品牌/VI":"Logo品牌VI","UI/App/网页/SaaS":"UIApp网页SaaS","产品/电商/包装":"产品电商包装",
    "海报/广告/社媒":"海报广告社媒","插画/艺术/概念":"插画艺术概念","漫画/分镜/故事板":"漫画分镜故事板",
    "信息图/教育图解":"信息图教育图解","3D/游戏/像素/等距":"3D游戏像素等距","建筑/室内/空间":"建筑室内空间",
    "风景/自然":"风景自然","动物/宠物":"动物宠物","车辆/机械/科幻":"车辆机械科幻",
    "抽象/纹理/背景":"抽象纹理背景","其他/未归类":"其他未归类"
  };
  const THEMES = ["人像","UI","3D","插画","摄影","海报","漫画","字体"];
  const STYLES = ["写实","赛博","水彩","胶片","霓虹","极简","复古","日系"];
  const TAG_RULES = {
    themes: {
      "人像": /人像|头像|少女|女性|女孩|男生|男孩|男人|女人|人物|portrait|face|selfie/i,
      "UI": /UI|界面|网页|app|dashboard|图标|icon|saas/i,
      "3D": /3D|三维|等距|isometric|blender|c4d|产品|电商|包装/i,
      "插画": /插画|illustration|手绘|涂鸦|painting|水彩|油画/i,
      "摄影": /摄影|photography|胶片|写实|photo|街拍|电影感/i,
      "海报": /海报|poster|广告|banner|社媒|电商/i,
      "漫画": /漫画|manga|anime|分镜|storyboard|二次元/i,
      "字体": /字体|typography|标题|文字|logo|品牌|vi/i
    },
    styles: {
      "写实": /写实|photorealistic|realistic|照片|摄影|电影感/i,
      "赛博": /赛博|cyberpunk/i,
      "水彩": /水彩|watercolor/i,
      "胶片": /胶片|film/i,
      "霓虹": /霓虹|neon/i,
      "极简": /极简|minimalist|简约|clean/i,
      "复古": /复古|vintage|怀旧|oldschool/i,
      "日系": /日系|日式|japanese|anime|宫崎骏/i
    }
  };
  const FAV_KEY = 'shuixian_favorites_v1';
  const IMG_BASE = "https://r2.qqsrc.com";
  const PH = "data:image/svg+xml;utf8," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#eaf4f7"/><text x="50%" y="52%" font-size="14" fill="#9AA0A6" text-anchor="middle" font-family="sans-serif">暂无预览</text></svg>');

  // ---------- 状态 ----------
  let ALL = [];
  let state = { q:"", cat:"全部", sort:"hot", themes:[], styles:[], board:"全部" };
  let favData = { boards:[{id:'default',name:'默认收藏'}], items:{} };
  let options = { page:null, onSearch:null, onReady:null };
  let timer = null;

  // 轻量列表模式（部署版）：首屏只加载 list 文件，完整 prompt 后台/按需加载
  let USE_LIST = false;
  let fullLoaded = false;
  let fullPromise = null;
  const DETAIL = {};

  // ---------- 工具 ----------
  function getCatStyle(cat){
    const key = CAT_KEYS[cat] || "其他综合";
    const g = (p) => {
      const v = getComputedStyle(document.documentElement).getPropertyValue('--cat-'+key+'-'+p).trim();
      if(v) return v;
      return p==='main' ? '#8A8A8A' : p==='bg' ? '#E8E8E8' : '#5A5A5A';
    };
    return { bg:g('bg'), text:g('text'), main:g('main') };
  }
  function getBatch(){ const w=window.innerWidth; if(w>=921) return 4*6; if(w>=481) return 3*8; return 2*12; }
  function imgUrl(p){ return IMG_BASE ? IMG_BASE + "/" + p : p; }
  function tagKey(d){ return d.tweet || d.id; }
  const tagCache = new Map();
  function getTags(d){
    const k = tagKey(d);
    if(tagCache.has(k)) return tagCache.get(k);
    let themes, styles;
    if(Array.isArray(d.themes) && Array.isArray(d.styles)){ themes = d.themes; styles = d.styles; }
    else {
      const text = ((d.title||"") + " " + (d.prompt||"")).toLowerCase();
      themes = THEMES.filter(t => TAG_RULES.themes[t].test(text));
      styles = STYLES.filter(s => TAG_RULES.styles[s].test(text));
    }
    const res = { themes, styles };
    tagCache.set(k, res);
    return res;
  }
  function _tweetIdOf(d){
    if(d.tweet && /^\d{15,}$/.test(String(d.tweet))) return String(d.tweet);
    const arr = d.images || (d.image ? [d.image] : []);
    for(const p of arr){ const m = String(p).match(/(\d{15,})\.jpg$/i); if(m) return m[1]; }
    return null;
  }
  function _sortKey(d){ const tid = _tweetIdOf(d); if(tid) return {kind:0, val:tid}; return {kind:1, val:-(d.id||0)}; }
  function _cmpLatest(a,b){ const ka=_sortKey(a), kb=_sortKey(b); if(ka.kind!==kb.kind) return ka.kind-kb.kind; if(ka.kind===0) return ka.val>kb.val ? -1 : (ka.val<kb.val ? 1 : 0); return kb.val-ka.val; }
  function applySort(list){
    if(state.sort === "hot") return list.slice().sort((a,b) => ((b.likes||0) - (a.likes||0)));
    if(state.sort === "latest") return list.slice().sort(_cmpLatest);
    return list;
  }
  function toggle(arr, val){ const i = arr.indexOf(val); if(i>=0) arr.splice(i,1); else arr.push(val); }

  // 是否人物类（真人/动漫）：优先用列表预计算标志，回退到完整规则（兼容本地版）
  function isPerson(d){
    if(typeof d.person === 'boolean') return d.person;
    return ((d.title||"")+(d.prompt||"")).toLowerCase().includes("人像") || (d.category||"").includes("人像") || (d.category||"").includes("头像");
  }
  // ---------- 数据 ----------
  // 兼容两种数据源：部署版优先用轻量 list 文件（首屏快），本地版用完整 prompts.json
  const LIST_PARTS = ["data/list.part1.json","data/list.part2.json","data/list.part3.json"];
  const FULL_PARTS = ["data/prompts.part1.json","data/prompts.part2.json","data/prompts.part3.json"];
  async function loadData(){
    // 1) 轻量列表优先（部署版）：一次性拉齐 list.part1/2/3（共 ~3.2MB，远小于完整 25MB）
    //    注意：必须 await 全部 part，不能把 part2/3 放后台再 ALL=... 赋值——否则后台完成时
    //    会覆盖 twitter 已合并的结果，造成数据丢失（已踩坑：首屏只拿到 ~5166 条）。
    let main = null;
    try {
      const rp = await fetch(LIST_PARTS[0]);
      if(rp.ok){
        USE_LIST = true;
        const parts = await Promise.all(LIST_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));
        main = [].concat(...parts);
      }
    } catch(e){ main = null; }
    if(!main){
      // 回退：本地版完整数据（无 list 文件）
      try { main = await (await fetch('data/prompts.json')).json(); }
      catch(e){ main = []; }
      main.forEach(e => { DETAIL[tagKey(e)] = e; });  // 本地版直接建完整索引
      fullLoaded = true;
    }
    // 2) twitter 列表（优先 list 版，回退完整版）
    const m = await fetch('data/twitter_manifest.json').then(r => r.json()).catch(() => ({ files:["prompts-twitter.json"] }));
    const tws = [];
    for(const f of m.files){
      const listName = 'data/list-' + f.replace(/^prompts-/, '');
      let arr = await fetch(listName).then(r => r.ok ? r.json() : null).catch(() => null);
      if(!arr) arr = await fetch('data/'+f).then(r => r.json()).catch(() => []);
      if(arr && arr.length) tws.push(arr);
    }
    ALL = main.concat(...tws);
    // 注意：完整数据（25MB）不在此自动加载，改为灯箱/复制首次使用时按需加载（ensureFull），
    // 避免占用带宽拖慢图片加载；重复访问时已被浏览器缓存。
  }

  // 按需/后台加载完整数据，填充 DETAIL 索引，供灯箱与复制取完整 prompt
  function ensureFull(){
    if(fullLoaded) return Promise.resolve();
    if(fullPromise) return fullPromise;
    fullPromise = (async () => {
      let full = [];
      try {
        const rp = await fetch(FULL_PARTS[0]);
        if(rp.ok){
          const parts = await Promise.all(FULL_PARTS.map(u => fetch(u).then(x => x.json()).catch(() => [])));
          full = [].concat(...parts);
        } else {
          full = await (await fetch('data/prompts.json')).json();
        }
      } catch(e){ full = []; }
      const m = await fetch('data/twitter_manifest.json').then(r => r.json()).catch(() => ({ files:["prompts-twitter.json"] }));
      const tws = await Promise.all(m.files.map(f => fetch('data/'+f).then(r => r.json()).catch(() => [])));
      full = full.concat(...tws);
      full.forEach(e => { DETAIL[tagKey(e)] = e; });
      fullLoaded = true;
    })();
    return fullPromise;
  }
  // 取完整条目（含 prompt）；列表模式下若尚未加载则退回轻量条目
  function fullOf(d){ return DETAIL[tagKey(d)] || d; }

  // ---------- 组件加载 ----------
  async function injectComponent(url, selector, position='beforeend'){
    const sep = url.includes('?') ? '&' : '?';
    const res = await fetch(url + sep + 'v=' + ASSET_VERSION);
    if(!res.ok) throw new Error('Failed to load ' + url);
    const html = await res.text();
    const el = document.querySelector(selector);
    if(el) el.insertAdjacentHTML(position, html);
  }
  async function loadComponents(){
    await Promise.all([
      injectComponent('components/header.html', 'body', 'afterbegin'),
      injectComponent('components/footer.html', 'main', 'afterend'),
      injectComponent('components/lightbox.html', 'body', 'beforeend'),
      injectComponent('components/modals.html', 'body', 'beforeend')
    ]);
  }
  function highlightNav(){
    const page = options.page;
    document.querySelectorAll('.nav-link').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
    });
  }
  function initMobileNav(){
    const toggle = document.getElementById('navToggle');
    const nav = document.getElementById('mainNav');
    if(!toggle || !nav) return;
    function setOpen(open){
      toggle.classList.toggle('open', open);
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    }
    toggle.addEventListener('click', (e) => { e.stopPropagation(); setOpen(!nav.classList.contains('open')); });
    nav.addEventListener('click', (e) => { const t = e.target.closest('a, button'); if(t) setOpen(false); });
    document.addEventListener('click', (e) => { if(nav.classList.contains('open') && !toggle.contains(e.target) && !nav.contains(e.target)) setOpen(false); });
    window.addEventListener('resize', () => { if(window.innerWidth > 920) setOpen(false); });
  }

  // ---------- 收藏 ----------
  function loadFav(){ try{ const raw = localStorage.getItem(FAV_KEY); if(raw){ const p = JSON.parse(raw); if(p && p.boards && p.items) favData = p; } }catch(e){} }
  function saveFav(){ try{ localStorage.setItem(FAV_KEY, JSON.stringify(favData)); }catch(e){} }
  function isFav(id){ return !!favData.items[id]; }
  function addFav(d, boardId){ favData.items[d.id] = { boardId: boardId || 'default', item: fullOf(d) }; saveFav(); }
  function removeFav(id){ delete favData.items[id]; saveFav(); }
  function getFavItems(boardId){
    const ids = Object.keys(favData.items);
    return boardId === '全部' || !boardId
      ? ids.map(id => favData.items[id].item)
      : ids.filter(id => favData.items[id].boardId === boardId).map(id => favData.items[id].item);
  }
  function getBoards(){ return [{ id:'全部', name:'全部' }].concat(favData.boards); }
  function getBoardName(id){ if(id==='全部') return '全部收藏'; const b = favData.boards.find(x => x.id === id); return b ? b.name : '收藏'; }

  // ---------- 灯箱 ----------
  let lbList = [], lbIndex = 0;
  let lbEntry = null;
  async function openLightbox(d){
    lbEntry = d;
    const f = fullOf(d);
    lbList = (f.images && f.images.length) ? f.images.slice() : [f.image || f.thumb];
    lbIndex = 0;
    renderLb();
    document.getElementById('lbTitle').textContent = f.title || "(未命名)";
    document.getElementById('lbPrompt').textContent = (f.prompt != null) ? f.prompt : "(加载中…)";
    if(f.prompt == null){
      // 列表模式下完整 prompt 尚未加载，等后台加载完再补齐
      await ensureFull();
      if(lbEntry === d){
        const ff = fullOf(d);
        document.getElementById('lbTitle').textContent = ff.title || "(未命名)";
        document.getElementById('lbPrompt').textContent = ff.prompt || "(暂无提示词内容)";
      }
    }
    const mask = document.getElementById('mask');
    mask.classList.add('show'); mask.style.display = 'flex';
    document.body.style.overflow = "hidden";
  }
  function renderLb(){
    const img = document.getElementById('lbImg');
    const loading = document.getElementById('lbLoading');
    const src = lbList[lbIndex] || "";
    const full = src ? imgUrl(src) : "";
    loading.classList.add('show'); img.style.opacity = "0";
    img.onload = function(){ img.style.opacity = "1"; loading.classList.remove('show'); };
    img.onerror = function(){ this.onerror=null; this.style.opacity="1"; this.src=PH; loading.classList.remove('show'); };
    img.src = full || PH;
    const link = document.getElementById('viewLink');
    if(full){ link.href = full; link.style.display = "inline"; } else link.style.display = "none";
    const prev = document.getElementById('lbPrev'), next = document.getElementById('lbNext'), cnt = document.getElementById('lbCount');
    if(lbList.length > 1){ prev.style.display = "flex"; next.style.display = "flex"; cnt.textContent = (lbIndex+1)+" / "+lbList.length; }
    else { prev.style.display = "none"; next.style.display = "none"; cnt.textContent = ""; }
    preloadLb();
  }
  function preloadLb(){
    for(let k=1; k<=3; k++){ const i = lbIndex+k; if(i < lbList.length){ const u = lbList[i] ? imgUrl(lbList[i]) : ""; if(u){ const im = new Image(); im.src = u; } } }
    const p = lbIndex-1; if(p >= 0){ const u = lbList[p] ? imgUrl(lbList[p]) : ""; if(u){ const im = new Image(); im.src = u; } }
  }
  function lbPrev(){ if(lbIndex > 0){ lbIndex--; renderLb(); } }
  function lbNext(){ if(lbIndex < lbList.length-1){ lbIndex++; renderLb(); } }
  function closeLightbox(){ const mask = document.getElementById('mask'); mask.classList.remove('show'); mask.style.display = 'none'; document.body.style.overflow = ""; }

  // ---------- 弹窗 ----------
  function openQr(){ const m = document.getElementById('qrMask'); m.classList.add('show'); m.style.display = 'flex'; document.body.style.overflow = "hidden"; }
  function closeQr(){ const m = document.getElementById('qrMask'); m.classList.remove('show'); m.style.display = 'none'; document.body.style.overflow = ""; }
  function openAbout(){ const m = document.getElementById('aboutMask'); m.classList.add('show'); m.style.display = 'flex'; document.body.style.overflow = "hidden"; }
  function closeAbout(){ const m = document.getElementById('aboutMask'); m.classList.remove('show'); m.style.display = 'none'; document.body.style.overflow = ""; }
  function openReward(){ const m = document.getElementById('rewardMask'); m.classList.add('show'); m.style.display = 'flex'; document.body.style.overflow = "hidden"; }
  function closeReward(){ const m = document.getElementById('rewardMask'); m.classList.remove('show'); m.style.display = 'none'; document.body.style.overflow = ""; }
  function closeBoardModal(){ const m = document.getElementById('boardMask'); m.classList.remove('show'); m.style.display = 'none'; }

  // ---------- Toast & Copy ----------
  const toast = { el:null };
  function showToast(msg){
    if(!toast.el) toast.el = document.getElementById('toast');
    toast.el.textContent = msg; toast.el.classList.add('show');
    setTimeout(() => toast.el.classList.remove('show'), 1600);
  }
  function copyText(txt){
    navigator.clipboard.writeText(txt).then(() => showToast('已复制提示词')).catch(() => {
      const ta = document.createElement('textarea'); ta.value = txt; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta); showToast('已复制提示词');
    });
  }

  // ---------- 公共事件 ----------
  function setupEvents(){
    // 搜索框
    const searchInput = document.getElementById('searchInput');
    if(searchInput){
      searchInput.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
          state.q = searchInput.value;
          if(typeof options.onSearch === 'function') options.onSearch(state.q);
        }, 220);
      });
      // 如果有页面初始搜索词，填入
      if(state.q) searchInput.value = state.q;
    }

    // 灯箱
    document.getElementById('lbClose').onclick = closeLightbox;
    document.getElementById('lbPrev').onclick = (e) => { e.stopPropagation(); lbPrev(); };
    document.getElementById('lbNext').onclick = (e) => { e.stopPropagation(); lbNext(); };
    const mask = document.getElementById('mask');
    mask.addEventListener('click', (e) => { if(e.target === mask) closeLightbox(); });
    document.addEventListener('keydown', (e) => {
      if(e.key === "Escape"){ closeLightbox(); closeQr(); closeAbout(); closeReward(); closeBoardModal(); }
      else if(mask.classList.contains('show')){ if(e.key === "ArrowLeft") lbPrev(); else if(e.key === "ArrowRight") lbNext(); }
    });
    (function(){
      const box = document.getElementById('lbImg'); let x0 = null;
      box.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, {passive:true});
      box.addEventListener('touchend', (e) => { if(x0 === null) return; const dx = e.changedTouches[0].clientX - x0; if(Math.abs(dx) > 40){ if(dx < 0) lbNext(); else lbPrev(); } x0 = null; }, {passive:true});
    })();

    // 弹窗
    document.getElementById('submitBtn').onclick = openQr;
    document.getElementById('qrClose').onclick = closeQr;
    document.getElementById('qrMask').addEventListener('click', (e) => { if(e.target === document.getElementById('qrMask')) closeQr(); });
    document.getElementById('aboutLink').onclick = (e) => { e.preventDefault(); openAbout(); };
    document.getElementById('aboutClose').onclick = closeAbout;
    document.getElementById('aboutMask').addEventListener('click', (e) => { if(e.target === document.getElementById('aboutMask')) closeAbout(); });
    document.getElementById('rewardLink').onclick = (e) => { e.preventDefault(); openReward(); };
    document.getElementById('rewardClose').onclick = closeReward;
    document.getElementById('rewardMask').addEventListener('click', (e) => { if(e.target === document.getElementById('rewardMask')) closeReward(); });
    document.getElementById('copyBtn').onclick = () => copyText(document.getElementById('lbPrompt').textContent);
  }

  // ---------- 卡片渲染（公共） ----------
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if(e.isIntersecting){ const img = e.target; if(img.dataset.src){ img.src = img.dataset.src; img.removeAttribute('data-src'); } io.unobserve(img); }
    });
  }, { rootMargin:"300px" });

  function makeCard(d, extraTags){
    const card = document.createElement('div'); card.className = "card";
    const firstImg = (d.image && d.image.trim()) || (d.images && d.images[0] && d.images[0].trim()) || (d.thumb && d.thumb.trim());
    const wrap = document.createElement('div'); wrap.className = "thumb-wrap";
    if(firstImg){
      const img = document.createElement('img'); img.dataset.src = imgUrl(firstImg); img.alt = d.title || ""; img.loading = "lazy"; img.onerror = function(){ this.onerror=null; this.src=PH; }; io.observe(img); wrap.appendChild(img);
    } else {
      const ph = document.createElement('div'); ph.className = "thumb-ph"; ph.textContent = "暂无预览"; wrap.appendChild(ph);
    }
    const n = (d.images && d.images.length) ? d.images.length : (firstImg ? 1 : 0);
    if(n > 1){
      const badge = document.createElement('div'); badge.className = "badge";
      badge.innerHTML = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="14" height="14" rx="2"/><path d="M21 8v9a2 2 0 0 1-2 2H8"/></svg>' + n;
      wrap.appendChild(badge);
    }
    // 星标
    const star = document.createElement('button'); star.className = "fav-star" + (isFav(d.id) ? " active" : "");
    star.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="' + (isFav(d.id) ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.18L12 21z"/></svg>';
    star.onclick = (e) => { e.stopPropagation(); App.toggleFavFromCard(d, star); };
    wrap.appendChild(star);
    // 悬停操作
    const acts = document.createElement('div'); acts.className = "actions";
    const copyBtn = document.createElement('button'); copyBtn.className = "act-btn primary"; copyBtn.textContent = "复制提示词"; copyBtn.onclick = (e) => { e.stopPropagation(); const f = fullOf(d); if(f.prompt == null){ ensureFull().then(() => copyText(fullOf(d).prompt || "")); } else { copyText(f.prompt || ""); } };
    const favBtn = document.createElement('button'); favBtn.className = "act-btn"; favBtn.textContent = isFav(d.id) ? "已收藏" : "收藏"; favBtn.onclick = (e) => { e.stopPropagation(); App.toggleFavFromCard(d, star); favBtn.textContent = isFav(d.id) ? "已收藏" : "收藏"; };
    const viewBtn = document.createElement('button'); viewBtn.className = "act-btn"; viewBtn.textContent = "看大图"; viewBtn.onclick = (e) => { e.stopPropagation(); openLightbox(d); };
    acts.appendChild(copyBtn); acts.appendChild(favBtn); acts.appendChild(viewBtn); wrap.appendChild(acts);
    card.appendChild(wrap);

    const cap = document.createElement('div'); cap.className = "cap"; cap.textContent = d.title || "(未命名)"; card.appendChild(cap);
    const meta = document.createElement('div'); meta.className = "meta";
    const likes = document.createElement('span'); likes.className = "likes";
    likes.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#C96B87" stroke-width="2"><path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.18L12 21z"/></svg>' + (d.likes || 0);
    meta.appendChild(likes);
    if(d.category){
      const cc = document.createElement('span'); cc.className = "cat-chip"; cc.textContent = d.category;
      const cs = getCatStyle(d.category); cc.style.background = cs.bg; cc.style.color = cs.text;
      meta.appendChild(cc);
    }
    if(extraTags && extraTags.length){
      extraTags.slice(0,3).forEach(t => {
        const tp = document.createElement('span'); tp.className = "tag-pill"; tp.textContent = t; meta.appendChild(tp);
      });
    }
    card.appendChild(meta);
    card.onclick = () => openLightbox(d);
    return card;
  }
  function toggleFavFromCard(d, starEl){
    if(isFav(d.id)){ removeFav(d.id); showToast('已取消收藏'); }
    else { addFav(d, 'default'); showToast('已收藏到默认画板'); }
    if(starEl){
      starEl.classList.toggle('active', isFav(d.id));
      starEl.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="' + (isFav(d.id) ? 'currentColor' : 'none') + '" stroke="currentColor" stroke-width="2"><path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.18L12 21z"/></svg>';
    }
    // 通知收藏页刷新
    if(window.__favChanged) window.__favChanged();
  }

  // ---------- 初始化 ----------
  function init(opts){
    options = Object.assign({ page:null, onSearch:null, onReady:null }, opts);
    loadFav();
    return loadComponents()
      .then(() => { highlightNav(); initMobileNav(); setupEvents(); })
      .then(() => loadData())
      .then(() => { if(typeof options.onReady === 'function') options.onReady(); })
      .catch(err => {
        console.error(err);
        const loading = document.querySelector('.loading');
        if(loading) loading.textContent = "数据加载失败：" + err.message + "（请通过本地服务器打开本页）";
      });
  }

  return {
    init,
    CATEGORIES, CAT_KEYS, THEMES, STYLES, TAG_RULES, PH, IMG_BASE,
    get ALL(){ return ALL; },
    get state(){ return state; }, set state(v){ state = v; },
    get favData(){ return favData; },
    getCatStyle, getBatch, imgUrl, getTags, applySort, toggle, isPerson, fullOf, ensureFull,
    loadFav, saveFav, isFav, addFav, removeFav, getFavItems, getBoards, getBoardName,
    openLightbox, closeLightbox, showToast, copyText,
    openQr, closeQr, openAbout, closeAbout, openReward, closeReward, closeBoardModal,
    makeCard, toggleFavFromCard
  };
})();
