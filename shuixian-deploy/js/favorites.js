/* ===== Favorites Page ===== */
(function(){
  const state = App.state;
  state.board = state.board || "全部";

  function renderBoardTabs(){
    const el = document.getElementById('boardTabs'); el.innerHTML = "";
    const allBtn = document.createElement('button');
    allBtn.className = 'board-tab' + (state.board === '全部' ? ' active' : '');
    allBtn.textContent = '全部';
    allBtn.onclick = () => { state.board = '全部'; renderBoardTabs(); renderFavGrid(); };
    el.appendChild(allBtn);
    App.favData.boards.forEach(b => {
      const btn = document.createElement('button');
      btn.className = 'board-tab' + (state.board === b.id ? ' active' : '');
      btn.textContent = b.name;
      btn.onclick = () => { state.board = b.id; renderBoardTabs(); renderFavGrid(); };
      el.appendChild(btn);
    });
  }

  function renderFavGrid(){
    const list = App.getFavItems(state.board);
    const fg = document.getElementById('favGrid'); fg.innerHTML = "";
    list.forEach(d => fg.appendChild(App.makeCard(d)));
    document.getElementById('favEmpty').style.display = list.length ? 'none' : 'block';
  }

  function renderFav(){ renderBoardTabs(); renderFavGrid(); }

  // 当其他页面收藏/取消时通知本页刷新
  window.__favChanged = () => { if(state.board === '全部' || App.favData.items) renderFavGrid(); };

  function bindFavEvents(){
    document.getElementById('newBoardBtn').onclick = () => {
      document.getElementById('boardName').value = '';
      const m = document.getElementById('boardMask'); m.classList.add('show'); m.style.display = 'flex';
      setTimeout(() => document.getElementById('boardName').focus(), 50);
    };

    function closeBoardModal(){ const m = document.getElementById('boardMask'); m.classList.remove('show'); m.style.display = 'none'; }
    document.getElementById('boardClose').onclick = closeBoardModal;
    document.getElementById('boardCancel').onclick = closeBoardModal;
    document.getElementById('boardSave').onclick = () => {
      const name = document.getElementById('boardName').value.trim();
      if(!name){ App.showToast('请输入画板名称'); return; }
      const id = 'b_' + Date.now();
      App.favData.boards.push({ id, name });
      App.saveFav();
      state.board = id;
      renderFav();
      closeBoardModal();
    };

    document.getElementById('exportMdBtn').onclick = async () => {
      await App.ensureFull();
      const list = App.getFavItems(state.board);
      const boardName = App.getBoardName(state.board);
      let md = '# ' + boardName + '\n\n';
      list.forEach((d, i) => {
        md += '## ' + (i + 1) + '. ' + (d.title || '(未命名)') + '\n\n';
        md += '- 分类：' + (d.category || '其他综合') + '\n';
        md += '- 热度：' + (d.likes || 0) + '\n';
        if(d.images && d.images.length) md += '图片：' + d.images.join('\n  - ') + '\n';
        else if(d.image) md += '图片：' + d.image + '\n';
        md += '\n```\n' + (App.fullOf(d).prompt || '') + '\n```\n\n';
      });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([md], { type: 'text/markdown' }));
      a.download = '水仙收藏_' + boardName + '.md';
      a.click();
      URL.revokeObjectURL(a.href);
    };
  }

  App.init({
    page: 'favorites',
    onSearch: () => { renderFavGrid(); },
    onReady: () => { document.getElementById('loading').style.display = "none"; bindFavEvents(); renderFav(); }
  });
})();
