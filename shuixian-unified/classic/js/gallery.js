/* ===== Gallery Page ===== */
(function(){
  const state = App.state;
  let rendered = 0;

  /* ---------- 读取 URL 参数：首页跳转入口 ----------
     ?cat=子类  → 进入首页点击的子分类（核心：让首页子分类点击真正筛选）
     ?q=搜索词  → 跨全部分类搜索（首页搜索框 / 热门词跳转）
     两者都缺省时，回落到默认「搞怪」（用户要求：点画廊默认打开搞怪）。 */
  (function parseUrl(){
    const p = new URLSearchParams(window.location.search);
    const cat = (p.get('cat') || '').trim();
    const q = (p.get('q') || '').trim();
    if(cat){
      // 允许「全部」、12 大分类、或任一已知子类；非法值回落默认
      const known = cat === '全部' || App.MAJOR_CAT_LIST.includes(cat) || Object.prototype.hasOwnProperty.call(App.CAT_KEYS, cat);
      if(known) state.cat = cat;
    } else if(q){
      // 仅有搜索词时，搜索应跨全部分类，而非局限默认搞怪
      state.cat = '全部';
    }
    if(q) state.q = q;
  })();

  // 渐进式搜索：优先用已加载的标题即时出结果；若完整数据未就绪，
  // 仅匹配标题（毫秒级），完整数据到达后再补充正文命中项。
  function matchQ(d, q){
    const t = (d.title||"").toLowerCase();
    if(t.includes(q)) return true;
    // 标题未命中且完整数据已加载 → 再查正文
    if(App.isFullLoaded()){
      const f = App.fullOf(d);
      return (f.prompt||"").toLowerCase().includes(q);
    }
    return false;
  }

  function getGalleryList(){
    let list = App.ALL;
    if(state.cat !== "全部"){
      list = list.filter(d => (d.category||"其他综合") === state.cat);
    } else {
      // 「全部」视图不展示「其他/未归类」（无提示词的隔离项），仅在其专属分类中显示
      list = list.filter(d => (d.category||"其他综合") !== "其他/未归类");
    }
    const q = state.q.trim().toLowerCase();
    if(q) list = list.filter(d => matchQ(d, q));
    return App.applySort(list);
  }

  function renderChips(){
    const el = document.getElementById('chips'); el.innerHTML = "";
    // 「全部」置顶（黑色字体，浅色背景）
    const allBtn = document.createElement('button');
    allBtn.className = "chip" + ("全部" === state.cat ? " active" : ""); allBtn.textContent = "全部";
    allBtn.style.color = "全部" === state.cat ? "#fff" : "var(--ink)";
    allBtn.style.background = "全部" === state.cat ? "var(--ink)" : "var(--white)";
    allBtn.style.borderColor = "全部" === state.cat ? "var(--ink)" : "var(--line)";
    allBtn.onclick = () => { state.cat = "全部"; renderChips(); resetAndRender(); };
    el.appendChild(allBtn);
    // 显示全部数据中出现的分类（含所有 79 子类），按首次出现顺序排列
    const majors = new Set(App.MAJOR_CAT_LIST); const seen = new Set(); const subs = [];
    App.ALL.forEach(d => { const c = d.category || "其他/未归类"; if(!seen.has(c)){ seen.add(c); if(c !== "全部") subs.push(c); } });
    subs.forEach(c => {
      const style = App.getCatStyle(c);
      const isActive = c === state.cat;
      const b = document.createElement('button'); b.className = "chip" + (isActive ? " active" : ""); b.textContent = c;
      // 选中态统一：黑底白字（与「全部」一致）；未选中用各自分类色
      if(isActive){
        b.style.background = "var(--ink)";
        b.style.color = "#fff";
        b.style.borderColor = "var(--ink)";
      } else {
        b.style.background = style.bg;
        b.style.color = style.text;
        b.style.borderColor = "transparent";
      }
      // hover 效果通过 CSS transition 自动过渡
      b.onmouseenter = () => {
        if(!isActive){ b.style.background = style.main + "22"; b.style.borderColor = style.main; }
      };
      b.onmouseleave = () => {
        if(!isActive){ b.style.background = style.bg; b.style.color = style.text; b.style.borderColor = "transparent"; }
      };
      b.onclick = () => { state.cat = c; renderChips(); resetAndRender(); };
      el.appendChild(b);
    });
  }

  function resetAndRender(){
    const list = getGalleryList();
    const grid = document.getElementById('grid'); grid.innerHTML = "";
    rendered = 0;
    document.getElementById('loading').style.display = "none";
    const n = App.getBatch();
    list.slice(0, n).forEach(d => grid.appendChild(App.makeCard(d)));
    rendered = list.slice(0, n).length;
    document.getElementById('showMore').style.display = (rendered < list.length) ? "inline-flex" : "none";
    document.getElementById('empty').style.display = (list.length === 0 && rendered === 0) ? "block" : "none";
  }

  function wireSort(){
    const pill = document.getElementById('sortPill'), list = document.getElementById('sortList');
    pill.onclick = (e) => { e.stopPropagation(); list.classList.toggle('show'); };
    list.querySelectorAll('button').forEach(b => {
      b.onclick = (ev) => {
        ev.stopPropagation(); state.sort = b.dataset.sort;
        list.querySelectorAll('button').forEach(x => x.classList.remove('sel')); b.classList.add('sel');
        pill.innerHTML = (state.sort === "hot" ? "最热" : "最新") + ' <span>▾</span>'; list.classList.remove('show');
        resetAndRender();
      };
    });
  }

  document.getElementById('showMore').onclick = () => {
    const list = getGalleryList(); const n = App.getBatch();
    list.slice(rendered, rendered + n).forEach(d => document.getElementById('grid').appendChild(App.makeCard(d)));
    rendered += list.slice(rendered, rendered + n).length;
    document.getElementById('showMore').style.display = (rendered < list.length) ? "inline-flex" : "none";
  };

  // 完整数据到达后自动补全搜索（渐进式：先标题、后正文）
  window.__onFullLoaded = () => {
    if(state.q.trim()){
      resetAndRender();
      const tip = document.getElementById('searchTip');
      if(tip) tip.style.display = "none";
    }
  };

  // 触发完整数据加载（若尚未加载），并显示一行提示，避免"以为卡死"
  function ensureSearchFull(){
    if(!App.isFullLoaded()){
      const tip = document.getElementById('searchTip');
      if(tip) tip.style.display = "block";
      App.ensureFull();
    }
  }

  App.init({
    page: 'gallery',
    onSearch: () => {
      resetAndRender();          // 立即用已加载数据（标题）出结果，不阻塞
      ensureSearchFull();        // 后台异步补正文命中
    },
    onReady: () => {
      renderChips(); wireSort();
      // 若 URL 带搜索词：先立即渲染标题结果，再后台补正文
      if(state.q.trim()){
        resetAndRender();
        ensureSearchFull();
      } else {
        resetAndRender();
      }
      document.addEventListener('click', () => document.querySelectorAll('.sort-list').forEach(s => s.classList.remove('show')));
      // 轻量列表 part2/3 后台到达后，刷新 chip 计数与「显示更多」状态（不重建网格，避免打断浏览）
      window.__onListGrown = () => { renderChips(); const list = getGalleryList(); document.getElementById('showMore').style.display = (rendered < list.length) ? "inline-flex" : "none"; };
    }
  });
})();
