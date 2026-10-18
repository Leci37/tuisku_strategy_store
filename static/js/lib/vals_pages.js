// The pages beyond the shop lists: the strategy page, compare, My strategies, thanks, the install
// tutorial, the welcome tour, the free-download dialog, the phone bar, the footer and errors.
import { tvInterval, tvChartUrl } from './fmt.js';

// Las páginas legales son las del núcleo, en esta misma web.
const LEGAL = { legalPrivacyUrl: '/legal/privacidad', legalCookiesUrl: '/legal/cookies', legalTermsUrl: '/legal/terminos', legalNoticeUrl: '/legal/aviso-legal' };

export function pageVals(c) {
  const { app, s, t, tx, f } = c;
  const TS = s.tourStep;
  const closeTour = () => app.closeTour();
  // Lite's floating cart (the dock: the Compare pill above the cart box) shows while the cart has something
  const liteDock = s.page === 'shop' && s.mode !== 'pro' && s.cart.length + s.bundles.length > 0;
  const base = s.vw < 640 ? 76 : 16;
  // above the dock when it shows, so the toast never hides the total or Checkout: the dock's measured
  // height (app.measureDock), which grows with the pill, the code box and narrow screens; else above the
  // floating Compare pill (38 px), when it shows
  const pillFloats = s.compare.length > 0 && !liteDock;
  const errBottom = base + (liteDock ? (s.dockH || 84) + 8 : pillFloats ? 38 + 8 : 0);
  return {
    ...detailVals(c), ...compareVals(c, liteDock), ...mineVals(c), ...thanksVals(c), ...installVals(c), ...freeVals(c),
    ...LEGAL, legalOn: true, contactOn: !!c.contact, contactUrl: c.contact ? 'mailto:' + c.contact : '', contactEmail: c.contact,
    errOpen: !!s.error, errTitle: tx.errServer, closeErr: () => app.setState({ error: '' }),
    // the server's vars, or the contact address (a link that expired says where to write)
    errText: t(s.error, s.errorVars || { e: c.contact }) + ((s.error === 'errPayment' || s.error === 'errLater' || s.error === 'errPayPal') && c.contact ? ' ' + t('contactProblems', { e: c.contact }) : ''),
    errBottom: errBottom + 'px',
    cmpBottom: base + 'px',
    // on a phone the bottom bar takes the last 60px: the floating cart sits above it, as the compare pill does
    dockBottom: base + 'px',
    // a short notice (the news opt-in confirmed or its link expired): the toast's look, not an error;
    // it waits while an error toast shows, in the same place
    ...noticeVals(c, errBottom),
    navItems: [
      ['shop', t('navShop'), 'fa-solid fa-house', () => app.go({ page: 'shop' })],
      ['search', t('searchSmall'), 'fa-solid fa-magnifying-glass', () => app.focusSearch()],
      ['cart', tx.cart, 'fa-solid fa-cart-shopping', () => app.showCart()],
      ['mine', t('navMine'), 'fa-regular fa-folder-open', () => app.goMine()]
    ].map(([k, label, icon, go]) => ({ label, icon, go, color: (k === 'shop' && s.page === 'shop') || (k === 'mine' && s.page === 'mine') ? '#0950e3' : '#5a6b80',
      hasBadge: k === 'cart' && c.cartN > 0, badge: f.int(c.cartN) })),
    tourOpen: TS >= 0, tourS1: TS <= 0, tourS2: TS === 1, tourS3: TS === 2, tourHasBack: TS > 0,
    tourStepLabel: t('tourStepOf', { n: f.int(Math.max(0, TS) + 1), total: f.int(3) }),
    tourTitle: t(['tour1Title', 'tour2Title', 'tour3Title'][Math.max(0, TS)]),
    tourText: TS <= 0 ? t(s.mode === 'pro' ? 'tour1Pro' : 'tour1Lite') : TS === 1 ? t('tour2Text') : t('tour3Text'),
    tourNextLabel: TS === 2 ? t('tourStart') : t('tourNext'),
    tourNext: () => { if (TS >= 2) closeTour(); else app.setState({ tourStep: TS + 1 }); },
    tourBack: () => app.setState({ tourStep: Math.max(0, TS - 1) }),
    closeTour, openTour: () => app.setState({ tourStep: 0 }),
    tourDots: [0, 1, 2].map(i => ({ w: i === TS ? '22px' : '8px', bg: i === TS ? '#0950e3' : '#cfd8e3' })),
    // step 3's PayPal → .pine → TradingView reads the other way in Arabic
    arrowFwd: c.rtl ? 'fa-solid fa-arrow-left' : 'fa-solid fa-arrow-right',
    tourIcons: ['AAPL', 'NVDA', 'AMZN', 'ADBE', 'BTC+USDT', 'ETH+USDT'].map(k => ({ src: '/static/assets/icons/' + k + '_big.svg' })),
    tourPD: e => app.swDown(e), tourPU: e => app.swUp(e, 'tourStep')
  };
}

const NOTICES = {
  newsConfirmed: ['fa-solid fa-circle-check', '#12b76a'],
  newsExpired: ['fa-solid fa-circle-info', '#9fb8ef']
};

function noticeVals(c, bottom) {
  const { app, s, t } = c;
  const n = NOTICES[s.notice];
  if (!n || s.error) return { noticeOpen: false };
  return {
    noticeOpen: true, noticeIcon: n[0], noticeColor: n[1],
    noticeTitle: t(s.notice + 'Title'), noticeText: t(s.notice + 'Text'), noticeBottom: bottom + 'px',
    closeNotice: () => app.setState({ notice: '' })
  };
}

const PK = /^(if|else|var|varip|float|int|bool|string|color|and|or|not|true|false|for|to|by|while|switch|import|export|na)$/;
function tokens(line) {
  const out = [], re = /(\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|(\b\d+(?:\.\d+)?(?:e[-+]?\d+)?\b)|(:=|<=|>=|==|!=|=>|[-+*\/<>=?:])|([A-Za-z_][\w.]*)(?=\s*\()|([A-Za-z_][\w.]*)|(\s+)|(.)/g;
  let m;
  while ((m = re.exec(line))) {
    if (m[1]) out.push({ t: m[1], c: '#7f93ad', fs: 'italic' });
    else if (m[2]) out.push({ t: m[2], c: '#9be3b0', fs: 'normal' });
    else if (m[3]) out.push({ t: m[3], c: '#f5b971', fs: 'normal' });
    else if (m[4]) out.push({ t: m[4], c: '#ff8fa3', fs: 'normal' });
    else if (m[5]) out.push({ t: m[5], c: '#47f9e5', fs: 'normal' });
    else if (m[6]) out.push({ t: m[6], c: PK.test(m[6]) ? '#7cc4ff' : '#dbe4ef', fs: 'normal' });
    else out.push({ t: m[7] || m[8], c: '#dbe4ef', fs: 'normal' });
  }
  return out;
}

function detailVals(c) {
  const { app, s, t, tx, f } = c;
  const r = s.page === 'detail' ? app.row(s.detail) : null;
  const tree = s.detTab === 'tree';
  if (!r) return { isDetail: false, det: {}, detOverview: !tree, detTreeTab: tree };
  const det = { ...c.mk(r), profit: r.profit, candle: r.candle };
  const owned = ((s.mine && s.mine.items) || []).find(x => x.id === r.id);
  // «Update available» is for whoever bought an older version (My strategies says which: update), not for
  // every visitor; a free download is renewed with the new version anyway
  const detOwnOld = !!(owned && owned.update && owned.kind === 'paid');
  // lines 5–16 sharp, 17–21 fading out, as the design's preview
  const pine = (s.pine[r.preview] || '').replace(/\r/g, '').split('\n').slice(4, 21);
  const pineLines = s.pine[r.preview] ? pine.map((l, i) => ({ no: String(i + 5), toks: tokens(l || ' '),
    blur: i >= 12 ? 'blur(' + ((i - 11) * 0.8 + 1.4).toFixed(1) + 'px)' : 'none', op: i >= 12 ? String(Math.max(0.35, 1 - (i - 11) * 0.13)) : '1', sel: i >= 12 ? 'none' : 'text' })) : [];
  const versions = (r.versions && r.versions.length ? r.versions : [{ v: r.version || 1, date: r.release, note: '' }]).slice().sort((a, b) => b.v - a.v);
  const dash = '—';
  return {
    isDetail: true, det, detOverview: !tree, detTreeTab: tree, detOwnOld,
    showOverview: () => app.go({ detTab: 'overview' }, { scroll: false }), showHowTab: () => app.go({ detTab: 'tree' }, { scroll: false }),
    ovBg: !tree ? '#0950e3' : '#e9f0fd', ovColor: !tree ? '#ffffff' : '#0950e3', ovLine: '#0950e3',
    hwBg: tree ? '#0e7c98' : '#e3f4f8', hwColor: tree ? '#ffffff' : '#0e7c98', hwLine: '#0e7c98',
    backToSheet: () => app.go({ detTab: 'overview' }),
    detMaxW: tree ? '1320px' : '1120px', treeLang: c.lang,
    Tree: s.Tree, treeRow: r, treeOwned: !!owned, treeSignedIn: !!(s.me && s.me.email), treeDownload: (owned && owned.url) || null, treeBuy: () => { if (r.price === 0) app.openFree(r.id); else if (!c.inCart(r.id)) c.toggleCart(r.id); },
    pineLines, pineFile: (r.file || 'strategy') + '.pine',
    formats: [
      { name: 'Pine Script', desc: tx.fmtPineDesc, ext: '.pine', ic: 'fa-solid fa-chart-line', icBg: '#0950e3', bg: '#f5f8ff', bd: '#c5d6f8', beta: false },
      { name: tx.fmtMd, desc: tx.fmtMdDesc, ext: '.md', ic: 'fa-brands fa-markdown', icBg: '#16263a', bg: '#ffffff', bd: '#e2e9f0', beta: false },
      { name: 'Python', desc: tx.fmtPyDesc, ext: '.py', ic: 'fa-brands fa-python', icBg: '#0e7c98', bg: '#ffffff', bd: '#e2e9f0', beta: true },
      { name: 'JavaScript', desc: tx.fmtJsDesc, ext: '.js', ic: 'fa-brands fa-js', icBg: '#b86e00', bg: '#ffffff', bd: '#e2e9f0', beta: true }
    ],
    detTf: t('tfNote', { tf: r.interval }),
    liveNote: r.live == null ? tx.liveUnknown : r.live_as_of ? t('liveAsOf', { date: f.fmtDate(r.live_as_of) }) : '',
    versions: versions.map((x, i) => ({
      // the date isolated (FSI…PDI): in Arabic "27/09/2024" would otherwise mix with "v1 · "
      title: 'v' + x.v + (x.date ? ' · \u2068' + f.fmtDate(x.date) + '\u2069' : ''), note: x.note || (x.v === 1 ? tx.v1note : ''),
      dot: i === 0 ? '#0950e3' : '#cfd8e3', update: i === 0 && x.v > 1 && detOwnOld
    })),
    detMetrics: [
      [t('fNetProfitUsd'), f.money(r.np)], [t('fNetProfitPct'), f.pctS(r.npp), '#15803d'], [t('fClosedTrades'), f.int(r.tr)], [t('fWinRate'), f.pct(r.w)],
      [t('fProfitFactor'), r.pf ? f.num(r.pf, 3) : dash],
      [t('fMaxLossUsd'), r.mdd ? f.money(r.mdd) : dash, r.mdd ? '#c0392b' : ''], [t('fMaxLossPct'), r.mddp ? f.pct(r.mddp) : dash, r.mddp ? '#c0392b' : ''],
      [t('fAvgProfitUsd'), f.money(r.avg)], [t('fAvgProfitPct'), r.avgp ? f.pct(r.avgp) : dash], [t('fAvgBars'), r.bars ? f.int(r.bars) : dash],
      [t('fReleaseDate'), f.fmtDate(r.release)], [t('fTrainingMonths'), f.int(r.m)], [t('fTimeframe'), r.interval], [t('fIndex'), r.index]
    ].map(([label, value, color]) => ({ label, value, color: color || '#16263a' }))
  };
}

function compareVals(c, liteDock) {
  const { app, s, t, tx, f } = c;
  const rows = s.compare.map(id => app.row(id)).filter(Boolean);
  // the best value of a row is marked; unknown values (no since-release figure yet) never win
  const best = (vals, low) => {
    const known = vals.filter(v => v != null);
    const m = known.length ? (low ? Math.min(...known) : Math.max(...known)) : null;
    return vals.map(v => v != null && v === m && known.length > 1);
  };
  const defs = [
    [t('fNetProfitPct'), r => r.npp, r => f.pctS(r.npp)], [t('fWinRate'), r => r.w, r => f.pct(r.w)], [t('fClosedTrades'), r => r.tr, r => f.int(r.tr)],
    [t('fAvgProfitUsd'), r => r.avg, r => f.money(r.avg)], [tx.sinceRelease, r => r.live, r => f.pctS(r.live)],
    [tx.sortPrice, r => r.price, r => (r.price ? f.pmoney(r.price) : t('landingFree')), true]
  ];
  return {
    // the pill rides in Lite's dock, above the cart, while the dock shows; elsewhere it floats at the
    // bottom-start corner
    cmpHas: s.compare.length > 0, cmpFloat: s.compare.length > 0 && !liteDock, cmpCount: f.int(s.compare.length),
    openCmp: () => app.setState({ cmpOpen: true }), closeCmp: () => app.setState({ cmpOpen: false }), cmpOpen: s.cmpOpen,
    cmpCols: rows.map(r => ({ icon: r.icon, ticker: r.ticker, key: r.key, remove: () => app.setState(st => ({ compare: st.compare.filter(x => x !== r.id), cmpOpen: st.compare.length > 1 })) })),
    cmpRows: defs.map(([label, get, fmt, low]) => {
      const vals = rows.map(get), b = best(vals, low);
      return { label, cells: rows.map((r, i) => ({ value: fmt(r), weight: b[i] ? '700' : '400', color: b[i] ? '#15803d' : '#16263a', bg: b[i] ? '#e8f7ef' : 'transparent' })) };
    })
  };
}

function mineVals(c) {
  const { app, s, t, f } = c;
  const email = (s.me && s.me.email) || '';
  const items = (s.mine && s.mine.items) || [];
  // el enlace de un correo de confirmación, abierto: de qué correo es, y el clic que lo confirma
  const confirm = !!s.proofAs;
  const asText = t('proofAs', { e: '\u0001' }).split('\u0001');
  return {
    isMine: s.page === 'mine', signedIn: !!email,
    proofConfirm: confirm, confirmProof: () => app.confirmProof(),
    proofAsBefore: asText[0], proofAsEmail: s.proofAs, proofAsAfter: asText.slice(1).join(''),
    // ¿compró sin cuenta? Hasta que la cuenta confirma su correo, lo que se hizo con él sin sesión no sale
    proofOffer: !confirm && !!email && (s.proofExpired || !!(s.mine && s.mine.proof_needed)),
    signedAs: t('signedAs', { e: email }), avatar: email.slice(0, 1).toUpperCase(),
    proofEmail: s.proofEmail || email, onProofEmail: e => app.setState({ proofEmail: e.target.value }),
    askProof: () => app.askProof(), proofKey: e => { if (e.key === 'Enter') app.askProof(); },
    proofSent: s.proofSent, proofNotSent: !s.proofSent, proofExpired: s.proofExpired && !s.proofSent,
    signOut: () => app.signOut(),
    mineHas: items.length > 0,
    mineRows: items.map(it => ({ ...c.mk(it.row),
      when: t(it.kind === 'free' ? 'freeOn' : 'boughtOn', { date: f.fmtDate(it.date) }), order: it.order ? t('orderN', { id: it.order }) : '',
      valid: it.valid, expired: !it.valid, pineUrl: it.url, zipUrl: it.zip,
      hasUpdate: !!it.update, updateLabel: 'v' + it.update, getUpdate: () => app.renew(it.id),
      status: it.valid ? t('linkValid', { n: f.int(it.days_left) }, it.days_left) : t('linkExpired'),
      stBg: it.valid ? '#e8f7ef' : '#f1f4f8', stColor: it.valid ? '#15603c' : '#5a6b80',
      renew: () => app.renew(it.id) })),
    favEmpty: s.favs.length === 0,
    favRows: s.favs.map(id => app.row(id)).filter(Boolean).map(r => {
      const al = s.alerts[r.id] || {};
      return { ...c.mk(r),
        alerts: [['nv', t('alertNew')], ['pd', t('alertPrice')], ['bd', t('alertBundle')]].map(([k, label]) => ({
          label, icon: al[k] ? 'fa-solid fa-bell' : 'fa-regular fa-bell', bg: al[k] ? '#e9f0fd' : '#ffffff', color: al[k] ? '#0950e3' : '#5a6b80', bd: al[k] ? '#c5d6f8' : '#e2e9f0',
          toggle: () => app.toggleAlert(r.id, k) })) };
    })
  };
}

function thanksVals(c) {
  const { s, t, f } = c;
  const rc = s.receipt;
  const tips = { tyZip: t('zipTitle'), tyNewTab: t('newTab') };
  if (!rc) return { isThanks: false, orderRows: [], ...tips };
  // links only for the browser that paid or the signed-in owner; anyone else is sent to My strategies
  const shown = (rc.downloads || []).length > 0;
  return { ...tips,
    isThanks: s.page === 'thanks', linksShown: shown, linksHidden: !shown,
    orderRows: (rc.downloads || []).map(d => ({ ...c.mk(d), pineUrl: d.url, zipUrl: d.zip })),
    orderTotal: f.money(Number(rc.total)), orderLabel: t('orderN', { id: rc.order_id }),
    downloadAllUrl: rc.download_all,
    linksNote: t('linksNote', { n: f.int(rc.valid_days), m: f.int(rc.max_downloads) })
  };
}

function installVals(c) {
  const { app, s, t, f } = c;
  const IS = s.instStep;
  const firstOf = list => (list && list[0]) || null;
  const r0 = app.row(s.instFor) || firstOf(s.receipt && s.receipt.downloads) || firstOf(((s.mine && s.mine.items) || []).map(x => x.row)) || firstOf(s.lite) || {};
  const iv = tvInterval(r0.interval || '');
  const go = n => app.setState({ instStep: n });
  const closeInst = () => app.closeInst();
  return {
    instOpen: IS >= 0, inst1: IS <= 0, inst2: IS === 1, inst3: IS === 2, inst4: IS === 3, inst5: IS === 4, instHasBack: IS > 0,
    instTourTitle: t('instTourTitle'), instWatch: t('instWatch'),
    instStepLabel: t('tourStepOf', { n: f.int(Math.max(0, IS) + 1), total: f.int(5) }),
    instTitle: t('i' + (Math.max(0, IS) + 1) + 'T'), instText: t('i' + (Math.max(0, IS) + 1) + 'X', { sym: r0.ticker || '', int: iv }),
    instNextLabel: IS >= 4 ? t('instDone') : t('tourNext'),
    instNext: () => { if (IS >= 4) closeInst(); else go(IS + 1); }, instBack: () => go(Math.max(0, IS - 1)), closeInst,
    openInst0: () => app.setState({ instStep: 0 }),
    instDots: [0, 1, 2, 3, 4].map(i => ({ w: i === IS ? '22px' : '8px', bg: i === IS ? '#0950e3' : '#cfd8e3', go: () => go(i), label: t('tourStepOf', { n: f.int(i + 1), total: f.int(5) }) })),
    instCards: [1, 2, 3, 4, 5].map(i => ({ n: f.int(i), title: t('i' + i + 'T'), go: () => go(i - 1) })),
    instIcon: r0.icon || '', instName: r0.name ? r0.name + ' · ' + r0.ticker : '', instFile: (r0.file || 'strategy') + '.pine',
    instCandle: r0.candle || '', instProfit: r0.profit || '',
    instSym: r0.ticker || '', instInt: iv,
    instChartUrl: tvChartUrl(r0.tv_symbol, r0.interval),
    instTvLabel: t('instOpenTv', { sym: r0.ticker || '' }),
    instPD: e => app.swDown(e), instPU: e => app.swUp(e, 'instStep'),
    instCols: s.vw >= 900 ? 'repeat(5,minmax(0,1fr))' : 'minmax(0,1fr)', instTileDir: s.vw >= 900 ? 'column' : 'row'
  };
}

function freeVals(c) {
  const { app, s, t } = c;
  const r = s.freeFor ? app.row(s.freeFor) : null;
  return {
    freeOpen: !!r, freeRow: r ? c.mk(r) : {}, freeEmail: s.freeEmail, onFreeEmail: e => app.setState({ freeEmail: e.target.value, freeErr: '' }),
    // what is wrong with the address, under the field (the core's errEmailRequired / errEmailInvalid): the
    // key, not the text, so it follows a change of language
    freeErrOn: !!s.freeErr, freeErr: s.freeErr ? t(s.freeErr) : '', freeBd: s.freeErr ? '#c0392b' : '#e2e9f0',
    freeSentNow: s.freeSent, freeNotSent: !s.freeSent, newsOn: String(s.freeNews),
    newsBg: s.freeNews ? '#0950e3' : '#ffffff', newsBorder: s.freeNews ? '#0950e3' : '#cfd6e6', newsCheck: s.freeNews ? '✓' : '',
    toggleNews: () => app.setState(st => ({ freeNews: !st.freeNews })),
    // Enter sends; not while an input method is composing (zh, hi), where Enter picks the characters
    sendFree: () => app.sendFree(), freeKey: e => { if (e.key === 'Enter' && !e.isComposing) app.sendFree(); },
    closeFree: () => app.closeFree()
  };
}
