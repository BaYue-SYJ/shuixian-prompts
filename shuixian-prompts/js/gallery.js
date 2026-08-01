/* ===== Gallery Page ===== */
(function(){
  const state = App.state;
  let rendered = 0;

  function getGalleryList(){
    let list = App.ALL;
    if(state.cat !== "全部"){
      list = list.filter(d => (d.category||"其他综合") === state.cat);
    }
    const q = state.q.trim().toLowerCase();
    if(q) list = list.filter(d => ((d.title||"").toLowerCase().includes(q) || (d.prompt||"").toLowerCase().includes(q)));
    return App.applySort(list);
  }

  function renderChips(){
    const el = document.getElementById('chips'); el.innerHTML = "";
    const base = new Set(App.CATEGORIES); const extra = [];
    App.ALL.forEach(d => { const c = d.category || "其他综合"; if(!base.has(c) && !extra.includes(c)) extra.push(c); });
    App.CATEGORIES.concat(extra).forEach(c => {
      const style = App.getCatStyle(c);
      const b = document.createElement('button'); b.className = "chip" + (c === state.cat ? " active" : ""); b.textContent = c;
      b.style.background = c === state.cat ? style.main : style.bg;
      b.style.color = c === state.cat ? "#fff" : style.text;
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

  App.init({
    page: 'gallery',
    onSearch: () => { resetAndRender(); },
    onReady: () => { renderChips(); wireSort(); resetAndRender(); document.addEventListener('click', () => document.querySelectorAll('.sort-list').forEach(s => s.classList.remove('show'))); }
  });
})();
