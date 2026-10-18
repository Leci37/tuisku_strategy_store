// The shop: Lite (ticker strip, tabs, cards, Load more) and Pro (filters with histograms, chips,
// rows / cards / table, pager). Lists, counts, histograms and options come from /api/strategies.
import { RANGES, TOP_RANGES, MORE_RANGES, SELECTS, track, val, snap, fracOf, isOn, parseNum } from './filters.js';

export const PRO_SIZE = 25;

export function shopVals(c) {
  const { app, s, t, tx, f } = c;
  const seg = (items, cur, set) => items.map(([k, label, icon]) => ({
    label, icon, go: () => set(k), pressed: String(cur === k),
    bg: cur === k ? '#ffffff' : 'transparent', color: cur === k ? '#0950e3' : '#5a6b80', shadow: cur === k ? '0 1px 3px rgba(22,38,58,.12)' : 'none'
  }));
  const tab = s.liteTab;
  const lite = s.lite || [];
  const counts = s.counts || {};
  return {
    isPro: s.page === 'shop' && s.mode === 'pro', isLite: s.page === 'shop' && s.mode !== 'pro',
    q: s.q, onQ: e => app.setState({ q: e.target.value }),
    tape: s.tape.map(r => ({ icon: r.icon, ticker: r.ticker + ' · ' + r.key, pct: f.pctS(r.npp) })),
    liteTabs: [['hot', t('tabHot')], ['win', tx.sortWin], ['stocks', t('tabStocks')], ['crypto', t('tabCrypto')], ['new', t('tabNew') + ' · ' + f.int(counts.new || 0)], ['free', t('landingFree')]].map(([k, label]) => ({
      label, sel: String(tab === k), color: tab === k ? '#16263a' : '#5a6b80', line: tab === k ? '#0950e3' : 'transparent', go: () => app.setState({ liteTab: k }) })),
    liteRows: lite.map(c.mk), liteEmpty: !!s.lite && lite.length === 0,
    liteShowing: s.lite ? t('showingN', { n: f.int(lite.length), total: f.int(s.liteTotal) }) : '',
    liteMore: lite.length < s.liteTotal, loadMoreLite: () => app.loadLite(s.litePage + 1),
    ...proVals(c, seg)
  };
}

function proVals(c, seg) {
  const { app, s, t, tx, f } = c;
  const fmt = {
    money0: f.money0, round: v => f.int(Math.round(v)), pct0: v => f.pct(v, 0), pct2: v => f.pct(v, 2),
    pctAuto: v => f.pct(v, v < 10 ? 2 : 0), dec1: v => f.num(v, 1)
  };
  const rgOf = k => s.rg[k] || [0, 1];
  const slider = k => {
    // labels show the snapped value, the one the query sends (filters.js)
    const dd = track(k, s.ranges), fm = v => fmt[dd.f](snap(dd, v)), [a, b] = rgOf(k), on = isOn(s.rg[k]);
    const cnt = (s.hist && s.hist[k]) || [], hl = cnt.length, mx = Math.max(1, ...cnt), dr = s.draft || {};
    const setD = (i, v) => app.setState(st => ({ draft: { ...(st.draft || {}), [k + i]: v } }));
    const commit = i => app.setState(st => {
      const d = { ...(st.draft || {}) }, raw = d[k + i];
      delete d[k + i];
      const v = raw == null ? null : parseNum(raw, f.decimal);
      if (v == null) return { draft: d };
      const r = (st.rg[k] || [0, 1]).slice(), fr = fracOf(dd, v);
      if (i === 0) r[0] = Math.min(fr, r[1]); else r[1] = Math.max(fr, r[0]);
      return { draft: d, rg: { ...st.rg, [k]: r } };
    });
    return {
      label: t(dd.key), active: on, valColor: on ? '#0950e3' : '#8d9cae',
      loPct: (a * 100).toFixed(2) + '%', hiPct: (b * 100).toFixed(2) + '%', wPct: ((b - a) * 100).toFixed(2) + '%',
      loLabel: fm(val(dd, a)), hiLabel: fm(val(dd, b)), value: on ? fm(val(dd, a)) + ' – ' + fm(val(dd, b)) : tx.any,
      bars: cnt.map((n, i) => {
        const mid = (i + 0.5) / hl, inR = mid >= a && mid <= b, small = n > 0 && n / mx < 0.15;
        return { h: n <= 0 ? '0px' : Math.max(4, Math.round(n / mx * 40)) + 'px', op: inR ? '1' : '.25',
          bg: small ? '#0950e3' : 'linear-gradient(180deg,#47f9e5,#0950e3)', tip: t('nStrategies', { n: f.int(n) }, n) };
      }),
      onDown: e => {
        const el = e.currentTarget, rect = el.getBoundingClientRect();
        const at = x => { let fr = (x - rect.left) / rect.width; if (c.rtl) fr = 1 - fr; return Math.min(1, Math.max(0, fr)); };
        const f0 = at(e.clientX), cur = app.state.rg[k] || [0, 1];
        const which = f0 > cur[1] ? 1 : f0 < cur[0] ? 0 : (Math.abs(f0 - cur[0]) <= Math.abs(f0 - cur[1]) ? 0 : 1);
        const apply = fr => app.setState(st => { const r = (st.rg[k] || [0, 1]).slice(); if (which === 0) r[0] = Math.min(fr, r[1]); else r[1] = Math.max(fr, r[0]); return { rg: { ...st.rg, [k]: r } }; });
        apply(f0);
        const move = ev => apply(at(ev.clientX));
        const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up); };
        window.addEventListener('pointermove', move); window.addEventListener('pointerup', up);
        if (e.preventDefault) e.preventDefault();
      },
      clear: () => app.setState(st => { const n = { ...st.rg }; delete n[k]; return { rg: n }; }),
      loIn: dr[k + 0] != null ? dr[k + 0] : fm(val(dd, a)), hiIn: dr[k + 1] != null ? dr[k + 1] : fm(val(dd, b)),
      loOn: e => setD(0, e.target.value), hiOn: e => setD(1, e.target.value), loDone: () => commit(0), hiDone: () => commit(1),
      onInKey: e => { if (e.key === 'Enter' && e.target && e.target.blur) e.target.blur(); }
    };
  };

  const optLabel = (k, o) => (k === 'rel' ? f.fmtDate(o.v) : o.label);
  const shortList = (k, vals) => vals.map(v => (k === 'rel' ? f.fmtDate(v) : v)).join(', ');
  const selObj = k => {
    const opts = (s.options && s.options[k]) || [], cur = s.sel[k], open = s.openSel === k, qq = (s.selQ || '').toLowerCase();
    const n = cur ? cur.length : opts.length;
    const value = !cur ? (opts.length ? t('selectedN', { n: f.int(opts.length) }) : '') : n === 0 ? '—' : n <= 2 ? shortList(k, cur) : t('selectedN', { n: f.int(n) });
    const setSel = v => app.setState(st => {
      const all = ((st.options && st.options[k]) || []).map(o => o.v);
      const nc = st.sel[k] ? st.sel[k].slice() : all.slice();
      const i = nc.indexOf(v);
      if (i >= 0) nc.splice(i, 1); else nc.push(v);
      const ns = { ...st.sel };
      if (nc.length === all.length) delete ns[k]; else ns[k] = nc;
      return { sel: ns };
    });
    return { label: t(SELECTS[k]), value, open, caret: open ? '▴' : '▾', rowBg: open ? '#f5f8ff' : '#ffffff', valColor: cur ? '#0950e3' : '#5a6b80',
      toggle: () => app.setState(st => ({ openSel: st.openSel === k ? '' : k, selQ: '' })),
      q: s.selQ || '', onQ: e => app.setState({ selQ: e.target.value }),
      all: () => app.setState(st => { const ns = { ...st.sel }; delete ns[k]; return { sel: ns }; }),
      none: () => app.setState(st => ({ sel: { ...st.sel, [k]: [] } })),
      opts: opts.filter(o => !qq || optLabel(k, o).toLowerCase().includes(qq)).map(o => {
        const on = !cur || cur.includes(o.v);
        return { label: optLabel(k, o), icon: o.icon || '', hasIcon: !!o.icon, count: f.int(o.count), check: on ? '✓' : '', bg: on ? '#0950e3' : '#ffffff', bd: on ? '#0950e3' : '#cfd6e6', toggle: () => setSel(o.v) };
      }) };
  };

  const q = s.q.trim();
  const chips = [];
  Object.keys(SELECTS).forEach(k => {
    const cur = s.sel[k];
    if (cur) chips.push({ label: t(SELECTS[k]) + ': ' + (cur.length ? (cur.length <= 2 ? shortList(k, cur) : t('selectedN', { n: f.int(cur.length) })) : '—'),
      clear: () => app.setState(st => { const ns = { ...st.sel }; delete ns[k]; return { sel: ns }; }) });
  });
  Object.keys(RANGES).forEach(k => { if (isOn(s.rg[k])) { const sl = slider(k); chips.push({ label: sl.label + ': ' + sl.loLabel + ' – ' + sl.hiLabel, clear: sl.clear }); } });
  if (s.freeOnly) chips.push({ label: tx.onlyFree, clear: () => app.setState({ freeOnly: false }) });
  if (q) chips.push({ label: '“' + q + '”', clear: () => app.setState({ q: '' }) });

  const rows = s.pro || [];
  const from = rows.length ? (s.proFirst - 1) * PRO_SIZE + 1 : 0, to = rows.length ? from + rows.length - 1 : 0;
  const pageCount = Math.max(1, Math.ceil(s.proTotal / PRO_SIZE)), cur = s.proPage || 1;
  const setPview = v => app.setPview(v);
  const numCols = [['np', tx.sortNp], ['npp', tx.npPct], ['win', tx.sortWin], ['trades', tx.sortTrades], ['avg', tx.avgProfit], ['months', tx.monthsTrained], ['price', tx.sortPrice]]
    .map(([k, label]) => ({ label, arrow: s.sort === k ? '▼' : '', color: s.sort === k ? '#0950e3' : '#5a6b80', cursor: 'pointer', ariaSort: s.sort === k ? 'descending' : null, go: () => app.setState({ sort: k }) }));

  return {
    proRows: rows.map(c.mk), proEmpty: !!s.proLoaded && rows.length === 0,
    shownCount: f.int(s.proTotal),
    rangeLabel2: t('rangeOf', { from: f.int(from), to: f.int(to), total: f.int(s.proTotal) }),
    rangeTop: TOP_RANGES.map(slider),
    selF: Object.keys(SELECTS).map(selObj),
    moreF: MORE_RANGES.map(k => {
      const sl = slider(k), open = s.moreOpen === k;
      return { ...sl, open, caret: open ? '▴' : '▾', weight: sl.active ? '700' : '400', rowBg: open ? '#f5f8ff' : '#ffffff', toggle: () => app.setState(st => ({ moreOpen: st.moreOpen === k ? '' : k })) };
    }),
    activeChips: chips, hasActive: chips.length > 0,
    resetAll: () => app.setState({ sel: {}, rg: {}, draft: {}, freeOnly: false, q: '', openSel: '', moreOpen: '' }),
    toggleFree: () => app.setState(st => ({ freeOnly: !st.freeOnly })), freeOn: String(s.freeOnly),
    freeTrack: s.freeOnly ? '#0950e3' : '#cfd8e3',
    freeKnob: s.freeOnly ? (c.rtl ? 'translateX(-14px)' : 'translateX(14px)') : 'translateX(0px)',
    sortTabs: seg([['np', tx.sortNp], ['win', tx.sortWin], ['price', tx.sortPrice], ['trades', tx.sortTrades]], s.sort, k => app.setState({ sort: k })),
    numCols,
    pages: pager(cur, pageCount).map(p => {
      const on = !p.label && p.n === cur;
      const go = p.n && !on && p.n >= 1 && p.n <= pageCount ? () => app.loadPro(p.n, false) : undefined;
      return { label: p.label || f.int(p.n), go, off: !go,
        bg: on ? '#0950e3' : '#ffffff', color: on ? '#ffffff' : go ? '#16263a' : '#8d9cae', border: on ? '#0950e3' : '#e2e9f0' };
    }),
    proMore: s.proPage * PRO_SIZE < s.proTotal, loadMorePro: () => app.loadPro(s.proPage + 1, true),
    viewTabs: seg([['rows', tx.viewRows, 'fa-solid fa-list'], ['cards', tx.viewCards, 'fa-solid fa-grip'], ['table', tx.viewTableTab, 'fa-solid fa-table']], s.pview, setPview),
    isTable: s.pview === 'table', isRows: s.pview === 'rows', isCards: s.pview === 'cards', proListPager: s.pview !== 'table'
  };
}

// ‹ 1 … 4 5 [6] 7 8 … 113 ›: the current page with two either side, and the ends.
function pager(cur, count) {
  const out = [{ label: '‹', n: cur - 1 }];
  const lo = Math.max(1, cur - 2), hi = Math.min(count, cur + 2);
  if (lo > 1) out.push({ n: 1 });
  if (lo > 2) out.push({ label: '…' });
  for (let i = lo; i <= hi; i++) out.push({ n: i });
  if (hi < count - 1) out.push({ label: '…' });
  if (hi < count) out.push({ n: count });
  out.push({ label: '›', n: cur + 1 });
  return out;
}
