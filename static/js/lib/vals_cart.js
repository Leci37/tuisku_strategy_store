// The cart: bundles, "Build your pack", the discount ladder and the totals. Every money figure is
// the server's (POST /api/quote); the browser only knows what is in the cart.
const num = x => (x == null || x === '' ? 0 : Number(x));

// The strategies a chosen bundle key stands for ('custom' is the pack being built).
const idsOf = (st, defs, key) => key === 'custom' ? st.packIds : ((defs.bundles.find(b => b.key === key) || {}).ids || []);
const shares = (a, b) => a.some(id => b.includes(id));

// A strategy is paid once: adding a bundle or the pack drops the loose items, the bundles and the
// pack that share a strategy with it (the server refuses a cart that holds one twice).
function addBundle(st, defs, key) {
  const ids = idsOf(st, defs, key);
  return { bundles: [...st.bundles.filter(b => b !== key && !shares(idsOf(st, defs, b), ids)), key], cart: st.cart.filter(id => !ids.includes(id)) };
}

// The same rule on a cart saved by an older version of the page: the first bundle chosen wins.
export function withoutOverlap(st, defs) {
  const taken = [], bundles = [];
  st.bundles.forEach(b => {
    const ids = idsOf(st, defs, b);
    if (!shares(ids, taken)) { bundles.push(b); taken.push(...ids); }
  });
  const cart = st.cart.filter(id => !taken.includes(id));
  return bundles.length === st.bundles.length && cart.length === st.cart.length ? {} : { bundles, cart };
}

export function cartVals(c) {
  const { app, s, t, tx, f } = c;
  const defs = s.bundleDefs || { bundles: [], pack: { size: 5, price: 0 } };
  const pack = defs.pack;
  const BUN = {};
  defs.bundles.forEach(b => { BUN[b.key] = b; });
  if (s.bundles.includes('custom') && s.packIds.length === pack.size) BUN.custom = { key: 'custom', name_key: 'packTitle', ids: s.packIds, price: pack.price };
  const inBundle = id => s.bundles.some(b => BUN[b] && BUN[b].ids.includes(id));
  c.inCart = id => s.cart.includes(id) || inBundle(id);
  c.toggleCart = id => app.setState(st => st.bundles.some(b => BUN[b] && BUN[b].ids.includes(id))
    ? { bundles: st.bundles.filter(b => !(BUN[b] && BUN[b].ids.includes(id))) }
    : { cart: st.cart.includes(id) ? st.cart.filter(x => x !== id) : [...st.cart, id] });

  const q = s.quote;
  const bunIds = [...new Set(s.bundles.filter(b => BUN[b]).flatMap(b => BUN[b].ids))];
  const count = s.cart.length + bunIds.length;
  c.cartN = count;
  const sub = q ? num(q.subtotal) : 0, total = q ? num(q.total) : 0;
  const tier = q ? num(q.tier_rate) * 100 : 0, codeRate = q ? num(q.code_rate) * 100 : 0, rate = q ? num(q.discount_rate) * 100 : 0;
  // The ladder is the quote's: how many tiers the cart has passed and what the next one is missing.
  // An empty cart has no quote; it is at the foot of the ladder, the first tier (from /api/config) ahead.
  const tiers = ((s.cfg && s.cfg.tiers) || []).map(x => [num(x.over), num(x.rate) * 100]).sort((a, b) => a[0] - b[0]);
  const steps = Math.max(1, tiers.length);
  const passed = q ? num(q.tier_index) : 0;
  // a tier counts strictly above its amount (the server's rule): an empty cart is a cent more away from it
  const nt = q ? q.next_tier : tiers.length ? { over: tiers[0][0], rate: tiers[0][1] / 100, missing: tiers[0][0] + 0.01 } : null;
  // equal steps between tiers, filled in proportion inside the step the cart is in
  const from = passed > 0 && tiers[passed - 1] ? tiers[passed - 1][0] : 0, to = nt ? num(nt.over) : 0;
  const inStep = nt && to > from ? Math.min(1, Math.max(0, (to - num(nt.missing) - from) / (to - from))) : 0;
  const lp = Math.min(100, (passed + inStep) * 100 / steps);

  const row = id => app.row(id);
  const iconOf = r => (r ? r.icon : '');
  const packRows = s.packIds.map(row);
  // "Save N%" of a bundle, from its price and was (both the server's); the pack's, from the quote once
  // it is in the cart, else from the typical pack /api/bundles describes
  const saveP = r => t('saveP', { p: f.pct0(Math.max(0, Math.round(r * 100))) });
  const ratio = (price, was) => (num(was) > 0 ? 1 - num(price) / num(was) : 0);
  const packSave = q && q.pack ? num(q.pack.save) : ratio(pack.price, pack.was);
  const full = s.packIds.length === pack.size;

  return {
    cartCount: f.int(count), cartHas: s.cart.length + s.bundles.length > 0,
    subtotal: f.pmoney(sub), total: f.pmoney(total),
    tierLabel: (tier ? t('tierOn', { p: f.pct0(tier) }) : t('tierNone')) + (codeRate ? ' ' + t('plusCode', { p: f.pct0(codeRate) }) : ''),
    nextTierMsg: nt ? t('nextTier', { amount: f.money(num(nt.missing)), p: f.pct0(num(nt.rate) * 100) }) : passed >= tiers.length ? t('topTier') : '',
    ladderPct: lp.toFixed(1) + '%',
    tiers: tiers.map(([o, r], i) => ({ label: f.money0(o) + ' · ' + f.pct0(r), rate: f.pct0(r), amt: f.money0(o), pos: ((i + 1) * 100 / steps) + '%', tickBg: i < passed ? '#0950e3' : '#ffffff' })),
    // any discount crosses out the subtotal: a percentage (tier or code) or a flat-price code, whose
    // discount_rate is 0 while its total is lower
    hasDiscount: total < sub, liteOff: '−' + f.pct0(rate > 0 ? rate : sub > 0 ? (1 - total / sub) * 100 : 0),
    payNote: t('payNote', { amount: f.money(total) }),
    code: s.code, onCode: e => app.setState({ code: e.target.value }),
    applyCode: () => app.applyCode(),
    codeMsg: s.codeState === 'ok' ? t('codeOk') : s.codeState === 'bad' ? t('codeBad') : '',
    codeMsgColor: s.codeState === 'bad' ? '#c0392b' : '#15603c',
    codeOpen: s.codeOpen, codeClosed: !s.codeOpen, openCode: () => app.setState({ codeOpen: true }),
    emptyCart: () => app.setState({ cart: [], bundles: [] }),
    checkout: () => app.checkout(),
    // one order at a time: while it is being created the button is the design's disabled grey
    paying: s.paying, payCursor: s.paying ? 'default' : 'pointer', payShadow: s.paying ? 'none' : '0 8px 20px rgba(9,80,227,.22)',
    payBgLite: s.paying ? '#9aa7b8' : '#0950e3', payBgPro: s.paying ? '#9aa7b8' : 'linear-gradient(135deg,#0950e3,#0e7c98)',
    payIcon: s.paying ? 'fa-solid fa-spinner fa-spin' : 'fa-brands fa-paypal',
    bundles: defs.bundles.map(b => {
      const on = s.bundles.includes(b.key), rowsB = b.ids.map(row).filter(Boolean);
      const tick = [...new Set(rowsB.map(r => r.ticker))];
      return { name: t(b.name_key), count: t('nStrategies', { n: f.int(b.ids.length) }, b.ids.length), tickers: tick.join(' · '),
        icons: tick.map(tk => ({ src: iconOf(rowsB.find(r => r.ticker === tk)) })),
        was: f.pmoney(b.was), price: f.pmoney(b.price), save: saveP(ratio(b.price, b.was)),
        label: on ? tx.inCartBtn : t('addBundle'), btnIcon: on ? 'fa-solid fa-check' : 'fa-solid fa-cart-plus',
        go: () => app.setState(st => on ? { bundles: st.bundles.filter(x => x !== b.key) } : addBundle(st, defs, b.key)) };
    }),
    packSlots: Array.from({ length: pack.size }, (_, i) => { const r = packRows[i]; return { filled: !!r, empty: !r, icon: iconOf(r), border: r ? '1px solid #e2e9f0' : '2px dashed #9fb8ef' }; }),
    packSave: saveP(packSave),
    packHint: !full ? t('packHint', { n: f.int(pack.size - s.packIds.length), price: f.pmoney(pack.price) }) : t('packReady', { price: f.pmoney(pack.price) }),
    packBtnLabel: s.bundles.includes('custom') ? tx.inCartBtn : t('addPack'), packBtnBg: full ? '#0950e3' : '#9aa7b8',
    addPack: () => {
      if (!full) { app.setState({ packOpen: true }); return; }
      app.setState(st => st.bundles.includes('custom') ? { bundles: st.bundles.filter(b => b !== 'custom') } : addBundle(st, defs, 'custom'));
    },
    openPack: () => app.setState({ packOpen: true }), closePack: () => app.setState({ packOpen: false }), packOpen: s.packOpen,
    packCount: f.int(s.packIds.length), packSize: f.int(pack.size),
    packQ: s.packQ, onPackQ: e => app.setState({ packQ: e.target.value }),
    packList: packChoices(c, defs)
  };
}

// The picker: what is picked first, then the paid strategies the search found. Any of them can be
// ticked, also one that a chosen bundle holds (it says so: «In cart»): adding the pack then replaces that
// bundle (addBundle), so no strategy is paid twice.
function packChoices(c, defs) {
  const { app, s } = c, size = defs.pack.size;
  const picked = s.packIds.map(id => app.row(id)).filter(Boolean);
  const rest = s.packFound.filter(r => !s.packIds.includes(r.id));
  const inBundle = id => s.bundles.some(b => b !== 'custom' && idsOf(s, defs, b).includes(id));
  return [...picked, ...rest].map(r => {
    const on = s.packIds.includes(r.id), held = inBundle(r.id);
    return { ...c.mk(r), check: on ? '✓' : '', ck: on ? '#0950e3' : '#cfd6e6', ckBg: on ? '#0950e3' : '#ffffff',
      bd: on ? '#c5d6f8' : '#e2e9f0', bg: on ? '#f5f8ff' : '#ffffff', held, locked: false, cursor: 'pointer',
      toggle: () => app.setState(st => {
        if (st.packIds.includes(r.id)) return { packIds: st.packIds.filter(x => x !== r.id), bundles: st.bundles.filter(b => b !== 'custom') };
        if (st.packIds.length >= size) return null;
        return { packIds: [...st.packIds, r.id], bundles: st.bundles.filter(b => b !== 'custom') };
      }) };
  });
}
