// The review workspace page. It only draws `data` (built in workspace_html.py) and reports clicks with
// setTriggerValue('act', {...}); nothing is decided or stored here.
// the design's serif (Cormorant Garamond) is loaded into the page, not the component, so the component can use it
if (!document.getElementById('clautra-fonts')) {
  const l = document.createElement('link');
  l.id = 'clautra-fonts'; l.rel = 'stylesheet';
  l.href = 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&display=swap';
  document.head.appendChild(l);
}
const ui = { chipsAll: false, gapsOpen: false, ask: null, drafts: {}, findOpen: false, leftTop: 0, docTop: 0, scrollKey: null };

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const BACK = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6"/></svg>`;
const STATE_TAG = { found: 'Found', accepted: 'Accepted', check: 'Nothing found', failed: 'Failed' };

function left(d) {
  if (d.nothingLeft) {
    return `<div class="top"><button class="btn back" data-act="overview">${BACK}Overview</button></div>
      <div class="done"><strong>Nothing left to do.</strong> Every quote the tool found has been accepted or removed. Download the CSV from the sidebar, or switch to All clauses below to look back.</div>${gaps(d)}${modes(d)}`;
  }
  const c = d.current;
  const count = d.mode === 'To do'
    ? `<strong>${d.position.at} of ${d.position.of}</strong> still to do`
    : `<strong>${d.position.at} of ${d.position.of}</strong> passages and clauses`;
  const out = [`
    <div class="top"><button class="btn back" data-act="overview" title="Every contract and clause in one grid">${BACK}Overview</button>
      <span class="btns"><button class="btn" data-act="prev" aria-label="Previous">Previous</button>
      <button class="btn" data-act="next" aria-label="Next">Next</button></span></div>
    <div class="status"><span class="count">${count}</span><span class="bar"><span style="width:${Math.max(2, Math.round(d.progress * 100))}%"></span></span></div>${gaps(d)}
    <div><div class="title">${esc(d.title)}</div>
      <div class="sub">${esc(d.party ? d.party + ' · ' : '')}contract ${d.contractNo} of ${d.contracts}</div></div>
    ${chips(d)}
    <div class="section">
      <div class="head"><span class="name">${esc(c.name)}</span><span class="tag ${c.state}">${esc(STATE_TAG[c.state] || c.status)}</span>
        ${c.reviewed ? '<span class="of">✔ reviewed</span>' : ''}</div>`];
  if (c.failed) out.push(`<div class="qa">Failed to process: ${esc(c.failed)}</div>`);
  d.findings.forEach((f, i) => out.push(finding(f, i === d.findings.findIndex((x) => x.review === 'pending'), { clause: d.current.name, contract: d.title })));
  if (!d.findings.length) {
    out.push(`<div class="hint">Nothing found here. An empty result is not proof the clause is absent, so if this clause matters for the deal, search the contract yourself.</div>
      <button class="btn" data-findtoggle>Search the contract</button>`);
  }
  d.removed.forEach((r) => out.push(`<div class="restore"><div class="quote removed">${esc(r.quote)}</div><button class="btn" data-act="restore" data-id="${r.id}">Restore</button></div>`));
  out.push(`<label class="check"><input type="checkbox" data-reviewed ${c.reviewed ? 'checked' : ''}>${d.findings.length ? 'Mark this clause as reviewed' : 'I searched the contract (optional)'}</label></div>`);
  out.push(`<div class="next"><h4>Up next</h4>${d.upNext.length ? d.upNext.map((u) =>
    `<div class="row"><span>${esc(u.name)} · ${esc(u.clause)}</span><span class="tag ${u.state}">${esc(u.label)}</span></div>`).join('')
    : '<div class="row hint">That is the last one.</div>'}${modes(d)}</div>`);
  return out.join('');
}

// The clause strip shows the clauses that have findings (and the one on screen); the rest fold into one "N not found" chip.
function chips(d) {
  const chip = (k) => `<button class="chip ${k.state}${k.active ? ' active' : ''}" data-clause="${esc(k.name)}"><i></i>${esc(k.label)}</button>`;
  const hasFinding = (k) => k.state === 'found' || k.state === 'accepted';
  const shown = d.clauses.filter((k) => hasFinding(k) || k.active || ui.chipsAll);
  const hidden = d.clauses.length - shown.length;
  const more = ui.chipsAll
    ? '<button class="chip more" data-chipsall>show fewer</button>'
    : hidden ? `<button class="chip more" data-chipsall>${hidden} not found</button>` : '';
  return `<div class="chips">${shown.map(chip).join('')}${more}</div>`;
}

function gaps(d) {
  const open = d.gaps.filter((g) => !g.checked);
  if (!open.length) return '';
  const n = open.length, noun = n === 1 ? 'clause' : 'clauses';
  const list = ui.gapsOpen ? `<div class="gaplist">${d.gaps.map((g) => `<button class="gaprow" data-doc="${g.doc}" data-gapname="${esc(g.name)}"><span>${esc(g.title)} · ${esc(g.clause)}</span><span class="tag ${g.state}">${g.checked ? 'Checked' : STATE_TAG[g.state]}</span></button>`).join('')}</div>` : '';
  return `<div class="gapsum"><button class="linkbtn" data-gaps>${n} ${noun} with nothing found · ${ui.gapsOpen ? 'hide' : 'show'}</button>${list}</div>`;
}

function modes(d) {
  return `<div class="modes"><button data-mode="To do" class="${d.mode === 'To do' ? 'on' : ''}">To do</button><button data-mode="All clauses" class="${d.mode === 'All clauses' ? 'on' : ''}">All clauses</button></div>`;
}

// `about` says which clause and which contract the passage belongs to, so a question is never ambiguous
function finding(f, first, about) {
  const status = f.review === 'pending' ? 'Not yet reviewed' : f.review[0].toUpperCase() + f.review.slice(1);
  const accepted = f.review === 'accepted';
  const asking = ui.ask === f.id;
  const st = f.qstate;
  const chip = st === 'answered' ? 'Answered by the Senior Lawyer' : st === 'resolved' ? 'Question resolved' : 'Question open: waiting for the Senior Lawyer';
  const meta = [f.page ? `Page ${f.page}` : '', f.of > 1 ? `Passage ${f.index} of ${f.of}` : '', status].filter(Boolean).join(' · ');
  let h = `<div class="head"><span class="of">${meta}</span></div>
    <div class="quote">${esc(f.quote)}</div>
    <div class="hint">Check the highlighted passage in the contract says the same, word for word.</div>
    <div class="acts">
      <button class="act ${accepted ? '' : 'primary'}" data-act="accept" data-id="${f.id}" ${accepted ? 'disabled' : ''}>Accept ${first ? '<small>· A</small>' : ''}</button>
      <button class="act" data-act="remove" data-id="${f.id}">Remove ${first ? '<small>· R</small>' : ''}</button>
      <button class="act" data-ask="${f.id}">${f.question ? 'Edit question' : 'Ask senior'} ${first ? '<small>· Q</small>' : ''}</button>
    </div>`;
  if (asking) {
    const val = ui.drafts[f.id] ?? f.question;
    h += `<div class="ask"><div class="about">Your question about <strong>${esc(about.clause)}</strong> in ${esc(about.contract)}</div><textarea data-draft="${f.id}" placeholder="e.g. Does a transfer to an affiliate count as assignment here?">${esc(val)}</textarea>
      <div class="hint">One question per passage. Saving new text reopens it; saving empty text removes it.</div>
      <span class="btns"><button class="btn" data-save="${f.id}">Save question</button><button class="btn" data-cancel>Cancel</button></span></div>`;
  }
  if (!f.question) {
    h += `<div class="qa quiet"><span class="tag">Senior Lawyer</span><span>No question asked about this ${esc(about.clause)} passage. Press <strong>Ask senior</strong>${first ? ' (Q)' : ''} to flag it for the Senior Lawyer; the answer shows up here.</span></div>`;
  } else {
    h += `<div class="qa"><span class="tag">${chip}</span><span class="about">About <strong>${esc(about.clause)}</strong> in ${esc(about.contract)}</span><span><strong>You asked:</strong> ${esc(f.question)}</span>`;
    if (f.answer) {
      h += `<span><strong>Senior Lawyer:</strong> ${esc(f.answer)}</span>`;
      h += st === 'resolved' ? `<button class="btn" data-act="resolve" data-on="0" data-id="${f.id}">Reopen</button>`
                             : `<button class="btn" data-act="resolve" data-on="1" data-id="${f.id}">Mark resolved</button>`;
    }
    h += '</div>';
  }
  return h;
}

function right(d) {
  const doc = d.document;
  const head = `<div class="rtop"><div><span class="dt">Contract text</span><span class="file" title="${esc(d.fileFull)}">${esc(d.file)}</span></div>
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
      ${doc.hasSpans ? '' : '<p class="none">Nothing was found for this clause, so this is the start of the contract. Use Find in contract.</p>'}
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
    else if (t.hasAttribute('data-chipsall')) { ui.chipsAll = !ui.chipsAll; rerender(); }
    else if (ds.gapname) { ui.leftTop = 0; ui.gapsOpen = false; send({ type: 'jump', doc: Number(ds.doc), name: ds.gapname }); }
    else if (t.hasAttribute('data-gaps')) { ui.gapsOpen = !ui.gapsOpen; rerender(); }
    else if (ds.mode) send({ type: 'mode', mode: ds.mode });
    else if (ds.ask) { ui.ask = ui.ask === Number(ds.ask) ? null : Number(ds.ask); rerender(); }
    else if (ds.save !== undefined) {
      const ta = root.querySelector(`[data-draft="${ds.save}"]`);
      ui.ask = null; delete ui.drafts[ds.save];
      send({ type: 'ask', id: Number(ds.save), text: ta ? ta.value : '' });
      rerender();  // the data may come back unchanged (same text), so close the box here too
    }
    else if (t.hasAttribute('data-cancel')) { ui.ask = null; rerender(); }
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
    ui.leftTop = l.scrollTop; ui.docTop = dd.scrollTop;
    root.innerHTML = `<div class="left">${left(data)}</div><div class="right">${right(data)}</div>`;
    root.querySelector('.left').scrollTop = ui.leftTop; root.querySelector('[data-doc]').scrollTop = ui.docTop;
    root.querySelector('[data-draft]')?.focus();
    paintToast();
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
    if (!f) return;
    const k = e.key.toLowerCase();
    if (k === 'a' && f.review !== 'accepted') { armUndo(f.id, 'accept'); send({ type: 'accept', id: f.id }); }
    else if (k === 'r') { armUndo(f.id, 'remove'); send({ type: 'remove', id: f.id }); }
    else if (k === 'z' && ui.undo) { const u = ui.undo; ui.undo = null; paintToast(); send({ type: 'undo', id: u.id, doc: u.doc, name: u.name }); }
    else if (k === 'q') { e.preventDefault(); ui.ask = f.id; rerender(); }
  };
  document.addEventListener('keydown', onKey);
  return () => document.removeEventListener('keydown', onKey);
}
