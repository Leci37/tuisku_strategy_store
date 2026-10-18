// renderVals(): the values object the views read, with the names of the prototype's renderVals()
// (Storefront v7.dc.html), computed from the server's data. Split by area: shop (Lite, Pro, filters),
// cart (bundles, pack, quote), pages (strategy page, compare, My strategies, thanks, dialogs).
import { translator, formatters, tvSymbolUrl, LOCAL_CURRENCY } from './fmt.js';
import { strategyPath } from './route.js';
import { shopVals } from './vals_shop.js';
import { cartVals } from './vals_cart.js';
import { pageVals } from './vals_pages.js';

const TX_KEYS = ['toolName', 'tvConnect', 'tvConnected', 'tvDisconnect', 'language', 'cart', 'emptyCart', 'codePh', 'apply', 'checkout', 'shown', 'reset', 'onlyFree', 'strategies', 'sortNp', 'sortWin', 'sortPrice', 'sortTrades', 'npPct', 'avgProfit', 'monthsTrained', 'view', 'viewRows', 'viewCards', 'viewTableTab', 'tabNew', 'addToCart', 'inCartBtn', 'download', 'riskTitle', 'riskText', 'riskShort', 'legalPrivacy', 'legalCookies', 'legalTerms', 'legalNotice', 'contactMenu', 'proView', 'liteTitle', 'liteSub', 'searchPh', 'loadMore', 'haveCode', 'noMatch', 'tradesWord', 'rowsPerPage', 'addFilter', 'colBacktest', 'strategyChart', 'candleChart', 'openTv', 'fSymbol', 'fTimeframe', 'fIndicators', 'any', 'tourOpen', 'tourBack', 'tourClose', 'email', 'bundles', 'freeTitle', 'freeText', 'newsOpt', 'sendLink', 'freeSent', 'myStrategies', 'mineSub', 'newLink', 'backShop', 'thanksTitle', 'thanksSub', 'downloadAll', 'totalPaid', 'paidWith', 'installTitle', 'goMine', 'selAll', 'selNone', 'searchSmall', 'clearAll', 'openPage', 'newTab', 'allResults', 'aboutInd', 'seeInd', 'scriptPreview', 'lockedNote', 'sinceRelease', 'liveVsBacktest', 'demoFigures', 'compare', 'compareTitle', 'compareMax', 'grade', 'packTitle', 'done', 'favourites', 'favEmpty', 'versions', 'v2note', 'v1note', 'updateAvail', 'getUpdate', 'trustPaypal', 'trustLinks', 'trustInvoice', 'currencyLabel', 'howItDecides', 'overviewTab', 'howTeaserTitle', 'howTeaserText', 'toSheet', 'scriptRest', 'buyScriptTitle', 'buyScriptText', 'formatsNote', 'fmtPineDesc', 'fmtMd', 'fmtMdDesc', 'fmtPyDesc', 'fmtJsDesc',
  'liveUnknown', 'signOut', 'errServer', 'linksHiddenTitle', 'linksHiddenText', 'signInToDownload',
  'proofTitle', 'proofText', 'proofSent', 'proofConfirmTitle', 'proofConfirm', 'errProofExpired'];
const GRADE_BG = { A: '#15803d', B: '#0e7c98', C: '#5a6b80', D: '#c0392b' };
const stop = e => { if (e && e.stopPropagation) e.stopPropagation(); };

export function renderVals(app) {
  const s = app.state;
  // el idioma y la dirección, los de la carcasa del núcleo; los textos, su diccionario
  const lang = s.lang;
  const rtl = s.dir === 'rtl';
  const t = translator(s.dict, {}, lang);
  const rates = (s.fx && s.fx.rates) || {};
  const f = formatters(lang, { local: s.cur === 'local', rate: rates[LOCAL_CURRENCY[lang]] || 0 });
  const tx = {};
  TX_KEYS.forEach(k => { tx[k] = t(k); });
  const contact = (s.cfg && s.cfg.contact_email) || '';
  tx.contactProblems = t('contactProblems', { e: contact });
  // the trust row says what the server's settings say, not the design's example figures
  tx.trustLinks = t('trustLinks', { n: f.int((s.cfg && s.cfg.download_days) || 7), m: f.int((s.cfg && s.cfg.max_downloads) || 10) });

  const c = { app, s, t, tx, f, lang, rtl, contact };
  c.mk = r => rowVals(c, r);
  const cart = cartVals(c); // also gives c.inCart and c.toggleCart, which every row uses
  const shop = shopVals(c);
  const pages = pageVals(c);

  return {
    lang, dir: rtl ? 'rtl' : 'ltr', g90: rtl ? '270deg' : '90deg', tickShift: rtl ? 'translateX(100%)' : 'translateX(-100%)',
    tx, barStart: app.props.barStart, barEnd: app.props.barEnd,
    tv: s.tv, tvOff: !s.tv, toggleTv: () => app.toggleTv(), tvTitle: s.tv ? tx.tvDisconnect : tx.tvConnect,
    isLocal: f.isLocal, curLabel: f.curLabel, toggleCur: () => app.setState(st => ({ cur: st.cur === 'local' ? 'usd' : 'local' })),
    isPhone: s.vw < 640,
    goShop: () => app.go({ page: 'shop' }),
    goMine: () => app.goMine(),
    modeTabs: [['lite', 'Lite', 'fa-solid fa-bolt'], ['pro', 'Pro', 'fa-solid fa-chart-line']].map(([k, label, icon]) => {
      const on = (s.mode === 'pro' ? 'pro' : 'lite') === k;
      return { label, icon, on: String(on), bg: on ? '#0950e3' : 'transparent', color: on ? '#ffffff' : '#5a6b80', shadow: on ? '0 4px 12px rgba(9,80,227,.25)' : 'none',
        go: () => app.setMode(k) };
    }),
    ...shop, ...cart, ...pages,
    anyMenu: s.addOpen || !!s.openPill || !!s.openSel,
    closeMenus: () => app.setState({ addOpen: false, openPill: '', openSel: '' })
  };
}

// One strategy as every list, card and page shows it (the prototype's mk()).
function rowVals(c, r) {
  const { app, s, t, tx, f } = c;
  const id = r.id, inCart = c.inCart(id), open = s.expanded === id;
  const fav = s.favs.includes(id), cmp = s.compare.includes(id);
  const live = r.live;
  const tipFor = m => () => app.setState(st => ({ tip: st.tip === id + ':' + m ? '' : id + ':' + m }));
  const openAt = tab => e => { stop(e); app.go({ page: 'detail', detail: id, detTab: tab }); };
  return {
    id, ticker: r.ticker, name: r.name, key: r.key, ind: r.ind, ex: r.ind_text || '',
    icon: r.icon, interval: r.interval, index: r.index,
    priceLabel: r.price === 0 ? t('landingFree') : f.pmoney(r.price),
    grade: r.grade, gradeBg: GRADE_BG[r.grade] || '#5a6b80', gradeTip: t('gradeTip', { n: f.int(r.tr) }),
    // since release is measured by a daily job; until it has run there is nothing to show
    live: live == null ? '—' : f.pctS(live), liveColor: live == null ? '#8d9cae' : live >= 0 ? '#15803d' : '#c0392b',
    barBt: Math.max(0, Math.min(100, r.npp || 0)) + '%', barLive: live == null ? '0%' : Math.min(100, Math.abs(live)) + '%',
    releaseLabel: f.fmtDate(r.release),
    // released in the last NEW_DAYS days: the server says so (the same rule as the New tab's count)
    isNew: !!r.is_new,
    favIcon: fav ? 'fa-solid fa-heart' : 'fa-regular fa-heart', favColor: fav ? '#c0392b' : '#5a6b80',
    onFav: e => { stop(e); app.toggleFav(id); },
    cmpBg: cmp ? '#16263a' : '#ffffff', cmpColor: cmp ? '#ffffff' : '#5a6b80',
    onCompare: e => { stop(e); app.toggleCompare(id); },
    isFree: r.price === 0, isPaid: r.price > 0,
    np: f.money(r.np), npp: f.pct(r.npp), nppSigned: f.pctS(r.npp), trades: f.int(r.tr), win: f.pct(r.w), avg: f.money(r.avg), months: f.int(r.m),
    // lists load the 640px WebP; the strategy page swaps in the full PNG
    profit: r.thumb_profit || r.profit, candle: r.thumb_candle || r.candle,
    tvUrl: tvSymbolUrl(r.tv_symbol),
    cartLabel: inCart ? tx.inCartBtn : tx.addToCart, buyLabel: inCart ? tx.inCartBtn : t('buy'),
    cartIcon: inCart ? 'fa-solid fa-check' : 'fa-solid fa-cart-plus',
    cartBg: inCart ? '#e9f0fd' : 'linear-gradient(135deg,#0950e3,#0e7c98)', buyBg: inCart ? '#e9f0fd' : '#0950e3',
    cartColor: inCart ? '#0950e3' : '#ffffff', buyColor: inCart ? '#0950e3' : '#ffffff',
    cartBorder: inCart ? '#c5d6f8' : 'transparent', buyBorder: inCart ? '#c5d6f8' : '#0950e3',
    onCart: e => { stop(e); c.toggleCart(id); },
    isOpen: open, openBg: open ? '#f7faff' : 'transparent',
    onToggle: () => app.setState(st => ({ expanded: st.expanded === id ? '' : id })),
    onOpen: openAt('overview'), onTree: openAt('tree'),
    tabHref: strategyPath(id), treeHref: strategyPath(id, true),
    indUrl: r.ind_url || 'https://www.tradingview.com/scripts/',
    onFree: e => { stop(e); app.openFree(id); },
    tipOpen: s.tip.startsWith(id + ':'),
    tipText: s.tip === id + ':npp' ? t('expNpp') : s.tip === id + ':win' ? t('expWin') : t('expTrades'),
    tipNpp: tipFor('npp'), tipWin: tipFor('win'), tipTrades: tipFor('trades'), tipClose: () => app.setState({ tip: '' })
  };
}
