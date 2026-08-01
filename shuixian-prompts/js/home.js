/* ===== Home Page ===== */
(function(){
  const state = App.state;
  let rendered = 0;

  function getHomeList(){
    let list = App.ALL;
    if(state.cat !== "全部"){
      list = list.filter(d => (d.category||"其他综合") === state.cat);
    }
    const q = state.q.trim().toLowerCase();
    if(q) list = list.filter(d => ((d.title||"").toLowerCase().includes(q) || (d.prompt||"").toLowerCase().includes(q)));
    return App.applySort(list);
  }

  function renderHomeChips(){
    const el = document.getElementById('heroChips'); el.innerHTML = "";
    const base = new Set(App.CATEGORIES); const extra = [];
    App.ALL.forEach(d => { const c = d.category || "其他综合"; if(!base.has(c) && !extra.includes(c)) extra.push(c); });
    App.CATEGORIES.concat(extra).forEach(c => {
      const b = document.createElement('button');
      b.className = "chip" + (c === state.cat ? " active" : ""); b.textContent = c;
      b.onclick = () => { state.cat = c; renderHomeChips(); resetAndRenderHome(); };
      el.appendChild(b);
    });
  }

  function renderHomeStats(list){
    const total = list.length;
    const withImg = list.reduce((s,d) => s + ((d.images && d.images.length) ? d.images.length : (d.image && d.image.trim() ? 1 : 0)), 0);
    const coverage = total ? Math.round(withImg / total * 100) + "%" : "0%";
    const el = document.getElementById('heroStats'); el.innerHTML = "";
    [["提示词", total.toLocaleString()], ["原图", withImg.toLocaleString()], ["覆盖率", coverage]].forEach(([label, val]) => {
      const box = document.createElement('div');
      const n = document.createElement('div'); n.className = "stat-num num"; n.textContent = val;
      const l = document.createElement('div'); l.className = "stat-label"; l.textContent = label;
      box.appendChild(n); box.appendChild(l); el.appendChild(box);
    });
  }

  let timer = null;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if(e.isIntersecting){ const img = e.target; if(img.dataset.src){ img.src = img.dataset.src; img.removeAttribute('data-src'); } io.unobserve(img); }
    });
  }, { rootMargin: "300px" });

  function makeHomeCard(d){
    const card = document.createElement('div'); card.className = "home-card";
    const firstImg = (d.image && d.image.trim()) || (d.images && d.images[0] && d.images[0].trim()) || (d.thumb && d.thumb.trim());
    const wrap = document.createElement('div'); wrap.className = "thumb-wrap";
    if(firstImg){
      const img = document.createElement('img'); img.className = "thumb";
      img.dataset.src = App.imgUrl(firstImg); img.alt = d.title || ""; img.loading = "lazy";
      img.onerror = function(){ this.onerror = null; this.src = App.PH; };
      io.observe(img);
      wrap.appendChild(img);
    } else {
      const ph = document.createElement('div'); ph.className = "thumb-ph"; ph.textContent = "暂无预览"; wrap.appendChild(ph);
    }
    const n = (d.images && d.images.length) ? d.images.length : (firstImg ? 1 : 0);
    if(n > 1){
      const badge = document.createElement('div'); badge.className = "badge";
      badge.innerHTML = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="14" height="14" rx="2"/><path d="M21 8v9a2 2 0 0 1-2 2H8"/></svg>' + n;
      wrap.appendChild(badge);
    }
    const cap = document.createElement('div'); cap.className = "cap"; cap.textContent = d.title || "(未命名)";
    const meta = document.createElement('div'); meta.className = "meta";
    const likes = document.createElement('span'); likes.className = "likes";
    likes.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#C96B87" stroke-width="2"><path d="M12 21l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.18L12 21z"/></svg>' + (d.likes || 0);
    meta.appendChild(likes);
    if(d.category){
      const cc = document.createElement('span'); cc.className = "cat-chip"; cc.textContent = d.category;
      const cs = App.getCatStyle(d.category); cc.style.background = cs.bg; cc.style.color = cs.text;
      meta.appendChild(cc);
    }
    card.appendChild(wrap); card.appendChild(cap); card.appendChild(meta);
    card.onclick = () => App.openLightbox(d);
    return card;
  }

  function resetAndRenderHome(){
    const list = getHomeList();
    renderHomeStats(list);
    document.getElementById('homeCount').textContent = "(" + list.length.toLocaleString() + ")";
    const grid = document.getElementById('homeGrid'); grid.innerHTML = "";
    rendered = 0;
    document.getElementById('loading').style.display = "none";
    const n = App.getBatch();
    list.slice(0, n).forEach(d => grid.appendChild(makeHomeCard(d)));
    rendered = list.slice(0, n).length;
    document.getElementById('homeShowMore').style.display = (rendered < list.length) ? "inline-flex" : "none";
    document.getElementById('homeEmpty').style.display = (list.length === 0 && rendered === 0) ? "block" : "none";
  }

  function wireHomeSort(){
    const pill = document.getElementById('homeSortPill'), list = document.getElementById('homeSortList');
    pill.onclick = (e) => { e.stopPropagation(); list.classList.toggle('show'); };
    list.querySelectorAll('button').forEach(b => {
      b.onclick = (ev) => {
        ev.stopPropagation(); state.sort = b.dataset.sort;
        list.querySelectorAll('button').forEach(x => x.classList.remove('sel')); b.classList.add('sel');
        pill.innerHTML = '排序 · ' + (state.sort === "hot" ? "最热" : "最新") + ' <span>▾</span>'; list.classList.remove('show');
        resetAndRenderHome();
      };
    });
  }

  document.getElementById('homeShowMore').onclick = () => {
    const list = getHomeList(); const n = App.getBatch();
    list.slice(rendered, rendered + n).forEach(d => document.getElementById('homeGrid').appendChild(makeHomeCard(d)));
    rendered += list.slice(rendered, rendered + n).length;
    document.getElementById('homeShowMore').style.display = (rendered < list.length) ? "inline-flex" : "none";
  };

  const heroSearch = document.getElementById('heroSearch');
  heroSearch.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => { state.q = heroSearch.value; resetAndRenderHome(); }, 220); });
  document.getElementById('heroSearchBtn').onclick = () => { state.q = heroSearch.value; resetAndRenderHome(); };

  App.init({
    page: 'index',
    onSearch: (q) => { heroSearch.value = q; state.q = q; resetAndRenderHome(); },
    onReady: () => { renderHomeChips(); wireHomeSort(); resetAndRenderHome(); document.addEventListener('click', () => document.querySelectorAll('.sort-list').forEach(s => s.classList.remove('show'))); }
  });
})();
