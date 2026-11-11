// The review workspace page. It only draws `data` (built in workspace_html.py) and reports clicks with
// setTriggerValue('act', {...}); nothing is decided or stored here.
// the design's serif (Cormorant Garamond) is loaded into the page, not the component, so the component can use it
if (!document.getElementById('clautra-fonts')) {
  const l = document.createElement('link');
  l.id = 'clautra-fonts'; l.rel = 'stylesheet';
  l.href = 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&display=swap';
  document.head.appendChild(l);
}
const ui = { ask: null, drafts: {}, findOpen: false, leftTop: 0, docTop: 0, scrollKey: null };

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const BACK = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>`;
const STATE_TAG = { found: 'Found', accepted: 'Accepted', check: 'Nothing found', failed: 'Failed' };

function left(d) {
  if (d.nothingLeft) {
    return `<div class="top"><button class="btn back" data-act="overview">${BACK}Overview</button></div>
      <div class="done"><strong>Nothing left to do.</strong> Every quote the tool found has been accepted or removed. Download the CSV from the sidebar, or go back to the Overview to look at any clause.</div>`;
  }
  const c = d.current, sr = d.role === 'senior', qn = d.questions;
  // the Junior Associate sees passages reviewed (the same numbers as the Overview); the Senior Lawyer sees questions answered
  const count = sr ? `<strong>${qn.total - qn.open} of ${qn.total}</strong> questions answered · ${qn.open} open`
                   : `<strong>${d.decided} of ${d.total}</strong> passages reviewed ·${d.left} left`;
  const prog = sr ? (qn.total ? (qn.total - qn.open) / qn.total : 1) : d.progress;
  const out = [`
    <div class="top"><button class="btn back" data-act="overview" title="${sr ? 'Back to the questions' : 'Every contract and clause in one grid'}">${BACK}${sr ? 'Questions' : 'Overview'}</button>
      <span class="btns"><button class="btn" data-act="prev" aria-label="Previous">Previous</button>
      <button class="btn" data-act="next" aria-label="Next">Next</button></span></div>
    <div class="status"><span class="count">${count}</span><span class="bar"><span style="width:${Math.max(2, Math.round(prog * 100))}%"></span></span></div>
    <div><div class="title">${esc(d.title)}</div>
      <div class="sub">${esc(d.party ? d.party + ' · ' : '')}contract ${d.contractNo} of ${d.contracts}</div></div>
    <div class="section">
      <div class="head"><span class="name">${esc(c.name)}</span><span class="tag ${c.state}">${esc(c.mine ? 'Found by you' : (STATE_TAG[c.state] || c.status))}</span>
        ${c.reviewed ? '<span class="of">✔ reviewed</span>' : ''}</div>`];
  if (c.failed) out.push(`<div class="qa">Failed to process: ${esc(c.failed)}</div>`);
  const about = { clause: d.current.name, contract: d.title, senior: sr };
  d.findings.forEach((f, i) => out.push(finding(f, i === d.findings.findIndex((x) => x.review === 'pending'), about)));
  if (!d.findings.length) out.push(gapPanel(d, about));
  else if (d.gapq) out.push(`<div class="hint">${sr ? 'A question about this clause, asked before a passage was found:' : 'Your question about this clause, asked before a passage was found:'}</div>`, sr ? answerBlock(d.gapq, about) : qaBlock(d.gapq, about, GAP_WORDS, false));
  d.removed.forEach((r) => out.push(`<div class="restore"><div class="quote removed">${esc(r.quote)}</div><button class="btn" data-act="restore" data-id="${r.id}">Restore</button></div>`));
  out.push(`<label class="check"><input type="checkbox" data-reviewed ${c.reviewed ? 'checked' : ''}>${d.findings.length ? 'Mark this clause as reviewed' : 'I searched the contract (optional)'}</label></div>`);
  return out.join('');
}

// The question box and the question/answer panel are the same for a passage and for a clause with nothing found.
// `key` is the passage id, or 'gap' for the clause-level question; `q` holds question, answer, qstate and id.
function askBox(key, q, about, noun, hint) {
  const val = ui.drafts[key] ?? (q ? q.question : '');
  return `<div class="ask"><div class="about">Your question about <strong>${esc(about.clause)}</strong> in ${esc(about.contract)}</div><textarea data-draft="${key}" placeholder="${esc(noun.example)}">${esc(val)}</textarea>
      <div class="hint">${hint}</div>
      <span class="btns"><button class="btn" data-save="${key}">Save question</button><button class="btn" data-cancel>Cancel</button></span></div>`;
}

function qaBlock(q, about, noun, first) {
  if (!q || !q.question) {
    return `<div class="qa quiet"><span class="tag">Senior Lawyer</span><span>${noun.none(about)} Press <strong>Ask senior</strong>${first ? ' (Q)' : ''} to flag it for the Senior Lawyer; the answer shows up here.</span></div>`;
  }
  const st = q.qstate;
  const chip = st === 'answered' ? 'Answered by the Senior Lawyer' : st === 'resolved' ? 'Question resolved' : 'Question open: waiting for the Senior Lawyer';
  let h = `<div class="qa"><span class="tag">${chip}</span><span class="about">About <strong>${esc(about.clause)}</strong> in ${esc(about.contract)}</span><span><strong>You asked:</strong> ${esc(q.question)}</span>`;
  if (q.answer) {
    h += `<span><strong>Senior Lawyer:</strong> ${esc(q.answer)}</span>`;
    h += st === 'resolved' ? `<button class="btn" data-act="resolve" data-on="0" data-id="${q.id}">Reopen</button>`
                           : `<button class="btn" data-act="resolve" data-on="1" data-id="${q.id}">Mark resolved</button>`;
  }
  return h + '</div>';
}

// The Senior Lawyer's side of a question: what the Junior Associate asked, and a box to answer it beside the contract.
function answerBlock(q, about) {
  if (!q || !q.question) {
    return `<div class="qa quiet"><span class="tag">Junior Associate</span><span>No question was asked about ${esc(about.clause)} here. You can still accept or remove the passage.</span></div>`;
  }
  const chip = q.qstate === 'answered' ? 'You answered' : q.qstate === 'resolved' ? 'Resolved by the Junior Associate' : 'Waiting for your answer';
  const val = ui.drafts['a' + q.id] ?? q.answer;
  return `<div class="qa"><span class="tag">${chip}</span><span class="about">About <strong>${esc(about.clause)}</strong> in ${esc(about.contract)}</span>
    <span><strong>Junior Associate asked:</strong> ${esc(q.question)}</span>
    <textarea data-draft="a${q.id}" placeholder="Your answer for the Junior Associate">${esc(val)}</textarea>
    <span class="btns"><button class="btn" data-saveanswer="${q.id}">Save answer</button></span></div>`;
}

const PASSAGE_WORDS = {
  example: 'e.g. Does a transfer to an affiliate count as assignment here?',
  none: (a) => `No question asked about this ${esc(a.clause)} passage.`,
};
const GAP_WORDS = {
  example: 'e.g. I could not find a termination clause. Could it sit under Miscellaneous?',
  none: (a) => `No question asked about ${esc(a.clause)} in this contract.`,
};

// A clause where the tool found nothing: the same buttons and question panel as a passage, plus the way to add the
// passage yourself by selecting it in the contract.
function gapPanel(d, about) {
  const q = d.gapq, asking = ui.ask === 'gap';
  if (about.senior) {
    return `<div class="hint">The tool found nothing here. If you spot the wording in the contract, select it and press <strong>Add passage</strong>.</div>` + answerBlock(q, about);
  }
  let h = `<div class="hint">Nothing found here. An empty result is not proof the clause is absent. Read the contract; if you spot the wording yourself, select it in the contract text and press <strong>Add passage</strong>.</div>
    <div class="acts">
      <button class="act" data-ask="gap">${q ? 'Edit question' : 'Ask senior'} <small>· Q</small></button>
      <button class="act" data-findtoggle>Search the contract</button>
    </div>`;
  if (asking) h += askBox('gap', q, about, GAP_WORDS, 'One question per clause. Saving new text reopens it; saving empty text removes it.');
  return h + qaBlock(q, about, GAP_WORDS, true);
}

// `about` says which clause and which contract the passage belongs to, so a question is never ambiguous
function finding(f, first, about) {
  const status = f.review === 'pending' ? 'Not yet reviewed' : f.review[0].toUpperCase() + f.review.slice(1);
  const accepted = f.review === 'accepted';
  const asking = ui.ask === f.id;
  const meta = [f.mine ? (about.senior ? 'Added by the Junior Associate' : 'Found by you') : '', f.decidedBy === 'senior' ? 'Decided by Senior Lawyer' : '', f.page ? `Page ${f.page}` : '', f.of > 1 ? `Passage ${f.index} of ${f.of}` : '', status].filter(Boolean).join(' · ');
  let h = `<div class="head"><span class="of">${meta}</span></div>
    <div class="quote">${esc(f.quote)}</div>
    <div class="hint">${f.mine ? 'You highlighted this passage yourself, so it counts as accepted. Remove it if you picked the wrong text.' : 'Check the highlighted passage in the contract says the same, word for word.'}</div>
    <div class="acts">
      <button class="act ${accepted ? '' : 'primary'}" data-act="accept" data-id="${f.id}" ${accepted ? 'disabled' : ''}>Accept ${first ? '<small>· A</small>' : ''}</button>
      <button class="act" data-act="remove" data-id="${f.id}">Remove ${first ? '<small>· R</small>' : ''}</button>
      ${about.senior ? '' : `<button class="act" data-ask="${f.id}">${f.question ? 'Edit question' : 'Ask senior'} ${first ? '<small>· Q</small>' : ''}</button>`}
    </div>`;
  if (about.senior) return h + answerBlock(f, about);
  if (asking) h += askBox(f.id, f, about, PASSAGE_WORDS, 'One question per passage. Saving new text reopens it; saving empty text removes it.');
  return h + qaBlock(f, about, PASSAGE_WORDS, first);
}

function right(d) {
  const doc = d.document;
  const head = `<div class="rtop"><div><span class="dt">Contract text</span><span class="file" title="${esc(d.fileFull)}">${esc(d.file)}${doc.pages > 1 ? ' · ' + doc.pages + ' pages' : ''}</span></div>
    <div class="btns"><button class="btn" data-act="pprev">Previous passage</button><button class="btn" data-act="pnext">Next passage</button>
    <button class="btn" data-findtoggle>Find in contract</button></div></div>`;
  const find = (ui.findOpen || doc.query) ? `<div class="find"><input data-find type="text" placeholder="A word or phrase" value="${esc(doc.query || ui.findDraft || '')}">
      <button class="btn" data-dofind>Search</button>${doc.query ? '<button class="btn" data-clearfind>Clear</button>' : ''}</div>` : '';
  let body;
  if (doc.mode === 'search') {
    const note = doc.short ? 'Type at least two characters.' : doc.total ? `${doc.total} match${doc.total === 1 ? '' : 'es'} for “${esc(doc.query)}”${doc.total > doc.snippets.length ? `, showing the first ${doc.snippets.length}` : ''}`
      : 'No match in this contract.';
    body = `<div class="wrap"><div class="doc" data-doc><p class="none">${note}</p>${doc.snippets.map((s) => `<p>${s}</p>`).join('<hr>')}</div></div>`;
  } else {
    body = `<div class="wrap"><div class="doc" data-doc>
      ${doc.hasSpans ? '' : '<p class="none">Nothing was found for this clause, so this is the start of the contract. Use Find in contract, or select the wording here to add it yourself.</p>'}
      ${doc.html}</div>
      <div class="strip" aria-label="Where the findings in this contract sit">${doc.ticks.map((t) => `<span class="${t.now ? 'now' : ''}" title="${esc(t.label)}" style="top:${t.top}%"></span>`).join('')}</div></div>`;
  }
  return head + find + body;
}

export default function (component) {
  const { data, setTriggerValue, parentElement } = component;
  const root = parentElement.querySelector('#ws');
  if (!root) return;
  if (data.empty) { root.innerHTML = '<div style="padding:24px">This review has no contracts.</div>'; return; }

  const prevLeft = root.querySelector('.left'), prevDoc = root.querySelector('[data-doc]');
  if (prevLeft) ui.leftTop = prevLeft.scrollTop;
  if (prevDoc) ui.docTop = prevDoc.scrollTop;
  // a different passage starts at the top of the panel, so the buttons and the count are always where they were
  const passageKey = `${data.docId}|${data.category}|${data.findings[0] ? data.findings[0].id : ''}`;
  if (passageKey !== ui.passageKey) { ui.leftTop = 0; ui.passageKey = passageKey; }
  root.innerHTML = `<div class="left">${left(data)}</div><div class="right">${right(data)}</div>`;
  const leftEl = root.querySelector('.left'), docEl = root.querySelector('[data-doc]');
  leftEl.scrollTop = ui.leftTop;
  paintToast();

  // keep the reader where they were, but bring a newly shown passage into view
  const key = data.document.scrollKey || data.document.query;
  const mark = docEl.querySelector('mark'), changed = key !== ui.scrollKey;
  if (changed && mark) docEl.scrollTop = Math.max(0, mark.offsetTop - docEl.offsetTop - 70);
  else docEl.scrollTop = ui.docTop;
  ui.scrollKey = key;

  const send = (act) => setTriggerValue('act', { ...act, n: Date.now() });
  const ctx = { doc: data.docId, name: data.category };

  // Select text in the contract to add it as a passage the tool missed. The selection is read when the mouse is released;
  // the bar offering "Add passage" is drawn outside the contract text so it does not disturb the selection.
  ui.sel = null;
  const getSel = () => { const r = root.getRootNode(); return r.getSelection ? r.getSelection() : window.getSelection(); };
  function showSelbar() {
    root.querySelector('.selbar')?.remove();
    if (!ui.sel) return;
    const shown = ui.sel.length > 90 ? ui.sel.slice(0, 87) + '…' : ui.sel;
    const bar = document.createElement('div');
    bar.className = 'selbar';
    bar.innerHTML = `<span class="selq">“${esc(shown)}”</span><button class="act primary" data-addsel>Add passage to ${esc(data.current.name)}</button><button class="btn" data-clearsel>Clear</button>`;
    root.querySelector('.right').appendChild(bar);
  }
  root.onmouseup = (e) => {
    if (!e.target.closest?.('[data-doc]')) return;
    setTimeout(() => {
      const s = getSel();
      const txt = s && s.rangeCount ? s.toString().replace(/\s+/g, ' ').trim() : '';
      ui.sel = txt.length >= 12 ? txt : null;
      showSelbar();
    }, 0);
  };
  if (data.notice) paintNotice(data.notice);

  root.onclick = (e) => {
    const t = e.target.closest('button');
    if (!t || t.disabled) return;
    const ds = t.dataset;
    if (t.hasAttribute('data-undo')) {
      const u = ui.undo; ui.undo = null; paintToast();
      if (u) send({ type: 'undo', id: u.id, doc: u.doc, name: u.name });
    }
    else if (ds.act) { if (ds.act === 'accept' || ds.act === 'remove') armUndo(Number(ds.id), ds.act); if (['prev','next','pprev','pnext'].includes(ds.act)) ui.leftTop = 0; send({ type: ds.act, id: ds.id ? Number(ds.id) : undefined, on: ds.on === undefined ? undefined : ds.on === '1' }); }
    else if (ds.clause) { ui.leftTop = 0; send({ type: 'clause', name: ds.clause }); }
    else if (ds.mode) send({ type: 'mode', mode: ds.mode });
    else if (ds.ask) { const k = ds.ask === 'gap' ? 'gap' : Number(ds.ask); ui.ask = ui.ask === k ? null : k; rerender(); }
    else if (ds.save !== undefined) {
      const ta = root.querySelector(`[data-draft="${ds.save}"]`);
      ui.ask = null; delete ui.drafts[ds.save];
      if (ds.save === 'gap') send({ type: 'gapask', text: ta ? ta.value : '', ...ctx });
      else send({ type: 'ask', id: Number(ds.save), text: ta ? ta.value : '' });
      rerender();  // the data may come back unchanged (same text), so close the box here too
    }
    else if (ds.saveanswer !== undefined) {
      const ta = root.querySelector(`[data-draft="a${ds.saveanswer}"]`);
      delete ui.drafts['a' + ds.saveanswer];
      send({ type: 'answer', id: Number(ds.saveanswer), text: ta ? ta.value : '' });
    }
    else if (t.hasAttribute('data-cancel')) { ui.ask = null; rerender(); }
    else if (t.hasAttribute('data-addsel')) {
      const text = ui.sel; ui.sel = null; root.querySelector('.selbar')?.remove();
      if (text) { ui.leftTop = 0; send({ type: 'addpassage', text, ...ctx }); }
    }
    else if (t.hasAttribute('data-clearsel')) { ui.sel = null; root.querySelector('.selbar')?.remove(); getSel()?.removeAllRanges?.(); }
    else if (t.hasAttribute('data-findtoggle')) { ui.findOpen = !ui.findOpen; rerender(); if (ui.findOpen) root.querySelector('[data-find]')?.focus(); }
    else if (t.hasAttribute('data-dofind')) send({ type: 'find', q: root.querySelector('[data-find]').value, doc: data.docId });
    else if (t.hasAttribute('data-clearfind')) { ui.findOpen = false; send({ type: 'find', q: '', doc: data.docId }); }
  };
  root.onchange = (e) => {
    if (e.target.matches('[data-reviewed]')) send({ type: 'reviewed', on: e.target.checked, ...ctx });
  };
  root.oninput = (e) => {
    if (e.target.matches('[data-draft]')) ui.drafts[e.target.dataset.draft] = e.target.value;
    if (e.target.matches('[data-find]')) ui.findDraft = e.target.value;
  };
  root.onkeydown = (e) => {
    if (e.target.matches('[data-find]') && e.key === 'Enter') send({ type: 'find', q: e.target.value, doc: data.docId });
  };

  // draw again from the same data when only local state (the question box, the find box) changed
  function rerender() {
    const l = root.querySelector('.left'), dd = root.querySelector('[data-doc]');
    ui.leftTop = l.scrollTop; ui.docTop = dd.scrollTop; ui.sel = null;
    root.innerHTML = `<div class="left">${left(data)}</div><div class="right">${right(data)}</div>`;
    root.querySelector('.left').scrollTop = ui.leftTop; root.querySelector('[data-doc]').scrollTop = ui.docTop;
    root.querySelector('[data-draft]')?.focus();
    paintToast();
  }

  // a short message, for example when text could not be matched to the contract
  function paintNotice(text) {
    root.querySelector('.notice')?.remove();
    clearTimeout(ui.noticeTimer);
    const el = document.createElement('div');
    el.className = 'toast notice'; el.setAttribute('role', 'status'); el.textContent = text;
    root.appendChild(el);
    ui.noticeTimer = setTimeout(() => el.remove(), 6000);
  }

  // "Accepted · Undo" for a few seconds after Accept or Remove: Undo puts the passage back to not yet reviewed and shows it again
  function armUndo(id, verb) {
    ui.undo = { id, doc: data.docId, name: data.category, text: verb === 'accept' ? 'Accepted' : 'Removed', until: Date.now() + 8000 };
  }
  function paintToast() {
    root.querySelector('.toast')?.remove();
    clearTimeout(ui.undoTimer);
    const u = ui.undo;
    if (!u || Date.now() >= u.until) { ui.undo = null; return; }
    const el = document.createElement('div');
    el.className = 'toast'; el.setAttribute('role', 'status');
    el.innerHTML = `${esc(u.text)} <button class="btn" data-undo>Undo</button>`;
    root.appendChild(el);
    ui.undoTimer = setTimeout(() => { if (ui.undo === u) ui.undo = null; el.remove(); }, u.until - Date.now());
  }

  // keyboard: A accept, R remove, Q ask (the first passage still to review), when not typing
  const onKey = (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || e.target.closest?.('input,textarea,select,[contenteditable]')) return;
    const f = data.findings.find((x) => x.review === 'pending') || data.findings[0];
    const k = e.key.toLowerCase();
    if (data.role === 'senior' && k === 'q') return;  // the Senior Lawyer answers questions, the Junior Associate asks them
    if (!f) { if (k === 'q' && !data.nothingLeft) { e.preventDefault(); ui.ask = 'gap'; rerender(); } return; }  // a clause with nothing found: ask about the clause
    if (k === 'a' && f.review !== 'accepted') { armUndo(f.id, 'accept'); send({ type: 'accept', id: f.id }); }
    else if (k === 'r') { armUndo(f.id, 'remove'); send({ type: 'remove', id: f.id }); }
    else if (k === 'z' && ui.undo) { const u = ui.undo; ui.undo = null; paintToast(); send({ type: 'undo', id: u.id, doc: u.doc, name: u.name }); }
    else if (k === 'q') { e.preventDefault(); ui.ask = f.id; rerender(); }
  };
  document.addEventListener('keydown', onKey);
  return () => document.removeEventListener('keydown', onKey);
}
