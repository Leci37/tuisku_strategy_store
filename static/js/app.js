// La tienda de Edgefolio: la lógica del diseño v7 (class Component de Storefront v7.dc.html) sobre la API
// de verdad. El estado, lo que se carga y las acciones viven aquí; lib/vals.js convierte el estado en los
// valores que leen las vistas. Nada de lo que es del servidor se calcula aquí: precios, totales y listas.
// Los textos son los del diccionario del núcleo (/zt/i18n.json: los de la tienda más los comunes) y el
// idioma, el de la carcasa (<html lang>): al cambiarlo en su menú, «zt:language» repinta la página.
import { Component } from '../vendor/preact.module.js';
import Storefront from './views/storefront.js';
import { api, post } from './lib/api.js';
import { read, write, readJSON, writeJSON } from './lib/saved.js';
import { parseLocation, pathOf } from './lib/route.js';
import { proQuery, Q_MAX, retrack } from './lib/filters.js';
import { translator } from './lib/fmt.js';
import { renderVals } from './lib/vals.js';
import { PRO_SIZE } from './lib/vals_shop.js';
import { withoutOverlap } from './lib/vals_cart.js';
import { topDialog, shield, unshield, focusIn, giveBack, keepTab } from './lib/modal.js';

const LITE_SIZE = 24;
const PACK_FIND = 40;
const CART_KEY = 'edgefolio-cart-v1';
const FAVS_KEY = 'edgefolio-favs-v1';
const list = x => (Array.isArray(x) ? x.filter(v => typeof v === 'string') : []);
// what a download link opened in the tab can answer: the server sends the person back here with the key
const LINK_ERRORS = ['errLinkNotFound', 'errLinkExpired', 'errDownloadLimit', 'errStrategyGone', 'errFileMissing'];

// Quita de la barra de direcciones lo que sólo vale una vez (un enlace de confirmación, un aviso).
function dropParams(...keys) {
  const qs = new URLSearchParams(location.search);
  keys.forEach(k => qs.delete(k));
  const rest = qs.toString();
  history.replaceState(history.state, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
}

// El idioma y la dirección de la carcasa del núcleo (los de <html>).
const pageLang = () => (window.zt && zt.uiLang && zt.uiLang()) || document.documentElement.lang || 'es';
const pageDir = () => document.documentElement.dir === 'rtl' ? 'rtl' : 'ltr';
const toLogin = () => window.location.assign('/login?next=' + encodeURIComponent(location.pathname + location.search));

export class App extends Component {
  constructor(props) {
    super(props);
    const route = parseLocation(location);
    const cart = readJSON(CART_KEY, {}), favs = readJSON(FAVS_KEY, {});
    const pview = read('tuisku-sf-pview5');
    this.rows = new Map(); // every strategy row the browser has seen, by id
    this.full = new Set(); // ids whose full record (indicator text, versions) is in this.rows
    this.asked = new Set();
    this.timers = {};
    this.seq = {};
    this.modal = null; // el diálogo abierto de arriba: { el, opener, marked } (syncModal)
    this.favSaved = new Map(); // lo que la cuenta tiene guardado de una favorita con un cambio sin contestar (setFav)
    this.state = {
      dict: null, cfg: null, bundleDefs: null, fx: null,
      lang: pageLang(), dir: pageDir(), mode: read('tuisku-sf-mode') === 'pro' ? 'pro' : 'lite',
      pview: ['table', 'rows', 'cards'].includes(pview) ? pview : 'rows',
      ...route, vw: window.innerWidth,
      addOpen: false, openPill: '', tv: read('edgefolio-tv') === '1', cur: 'local',
      q: '', liteTab: 'hot', lite: null, liteTotal: 0, litePage: 0, counts: {}, tape: [],
      freeOnly: false, sort: 'np', sel: {}, rg: {}, draft: {}, openSel: '', selQ: '', moreOpen: '',
      pro: [], proTotal: 0, proFirst: 1, proPage: 0, proLoaded: false, hist: {}, options: {}, ranges: null,
      expanded: '', tip: '',
      cart: list(cart.cart), bundles: list(cart.bundles), packIds: list(cart.packIds),
      code: cart.code || '', applied: cart.applied || '', codeState: '', codeOpen: !!cart.applied, quote: null,
      favs: list(favs.favs), alerts: favs.alerts && typeof favs.alerts === 'object' ? favs.alerts : {},
      compare: [], cmpOpen: false, packOpen: false, packQ: '', packFound: [],
      freeFor: '', freeEmail: '', freeNews: false, freeSent: false, freeErr: '', dockH: 0, toastH: 0,
      // proofEmail: lo escrito en el campo; null hasta que se escribe algo (sale el de la cuenta), '' si se vació
      me: props.signedIn ? null : { email: null }, mine: null, proofEmail: null, proofErr: '', proofSent: false, proofExpired: false,
      proofToken: '', proofAs: '',
      receipt: null, instStep: -1, instFor: '',
      tourStep: route.page === 'shop' && !read('edgefolio-tour-v1') ? 0 : -1,
      error: '', errorVars: null, notice: '', paying: false, rowsV: 0, Tree: null, pine: {}
    };
  }

  // ---- lifecycle -------------------------------------------------------------------------------

  componentDidMount() {
    this.onResize = () => this.setState({ vw: window.innerWidth });
    this.onKeyDown = e => this.onKey(e);
    this.onPop = () => this.setState({ ...parseLocation(location), tip: '' });
    // el menú de idioma de la carcasa: el diccionario ya está, sólo cambia el idioma
    this.onLang = () => this.setState({ lang: pageLang(), dir: pageDir() });
    this.onShow = e => { if (e.persisted) { this.paying = false; this.setState({ paying: false }); } };
    window.addEventListener('resize', this.onResize);
    window.addEventListener('pageshow', this.onShow);
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('popstate', this.onPop);
    document.addEventListener('zt:language', this.onLang);

    const dictionary = window.zt && zt.i18nReady ? zt.i18nReady : Promise.resolve(null);
    // sin diccionario no se pinta nada (render): el aviso es el que escribió el servidor en la plantilla
    // (zt.i18nReady no falla nunca: sin diccionario, da null)
    dictionary.then(dict => {
      if (dict) { this.setState({ dict }); return; }
      const note = document.querySelector('[data-ef-nodict]');
      if (note) note.hidden = false;
      this.fail({ network: true });
    });
    api('/api/config').then(cfg => this.setState({ cfg })).catch(e => this.fail(e));
    api('/api/bundles').then(bundleDefs => this.setState(st => ({ bundleDefs, ...withoutOverlap(st, bundleDefs) }))).catch(e => this.fail(e));
    api('/api/fx').then(fx => this.setState({ fx })).catch(() => { /* prices then stay in USD */ });
    api(this.inLang('/api/strategies?paid=1&sort=hot&size=12')).then(d => { this.keep(d.rows); this.setState({ tape: d.rows }); }).catch(e => this.fail(e));
    if (this.props.signedIn) api('/api/me').then(me => { this.setState({ me }); if (me.email) this.afterSignIn(); }).catch(() => this.setState({ me: { email: null } }));

    const qs = new URLSearchParams(location.search);
    if (this.state.page === 'thanks') this.capture(qs.get('token'));
    if (qs.get('checkout') === 'cancel') history.replaceState(null, '', '/'); // back from PayPal: the cart is still here
    // el enlace que confirma un correo: /mine?proof=<token> (sólo con la sesión abierta: /mine la pide)
    const proof = this.state.page === 'mine' && this.props.signedIn ? qs.get('proof') : null;
    if (proof) this.peekProof(proof);
    // back from a download link that no longer works (spent, expired): why, and My strategies gives a new one
    const link = qs.get('link');
    if (link) {
      if (LINK_ERRORS.includes(link)) this.setState({ error: link });
      dropParams('link');
    }
    // back from the link that confirms the news opt-in
    const news = qs.get('news');
    if (news) {
      if (news === 'confirmed' || news === 'expired') this.setState({ notice: news === 'confirmed' ? 'newsConfirmed' : 'newsExpired' });
      dropParams('news');
    }
    this.sync(null);
    this.measureDock();
  }

  componentWillUnmount() {
    window.removeEventListener('resize', this.onResize);
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('popstate', this.onPop);
    document.removeEventListener('zt:language', this.onLang);
    window.removeEventListener('pageshow', this.onShow);
    Object.values(this.timers).forEach(clearTimeout);
    if (this.modal) unshield(this.modal.marked);
  }

  componentDidUpdate(prevProps, prevState) {
    this.sync(prevState);
    this.measureDock();
    this.syncModal();
  }

  // Un diálogo abierto se queda con el teclado (lib/modal.js), sea cual sea el camino que lo abre o lo
  // cierra (un botón, Esc, «Hecho», el último paso): al abrirse, el foco entra y lo de detrás queda inert;
  // si lo enfocado desaparece dentro (un paso nuevo, «Enviarme el enlace» al mandarlo), el foco vuelve a
  // lo principal; al cerrarse, vuelve a quien lo abrió (si se abrió solo o ya no está, a <main>). Tab da la
  // vuelta dentro (onKey).
  syncModal() {
    const el = this.base && this.base.querySelectorAll ? topDialog(this.base) : null, cur = this.modal;
    if (cur && cur.el !== el) {
      unshield(cur.marked);
      if (!el) {
        this.modal = null;
        giveBack(cur.opener);
        return;
      }
    }
    if (!el) return;
    if (!cur || cur.el !== el) {
      // un diálogo que se abre encima de otro devuelve el foco adonde lo devolvía el primero
      this.modal = { el, opener: cur ? cur.opener : document.activeElement, marked: [] };
      shield(el, this.modal.marked);
      focusIn(el);
      return;
    }
    shield(el, cur.marked);
    const a = document.activeElement;
    if (!a || a === document.body) focusIn(el);
  }

  // The height of Lite's floating cart (the Compare pill and the cart box): toasts sit above it. It
  // changes with what the page paints (the pill, the code box, the width), so it is read after each paint.
  // También el del aviso que se ve (data-ef-toast): con un diálogo abierto, el diálogo le deja ese sitio arriba.
  measureDock() {
    const s = this.state, el = s.page === 'shop' && s.mode !== 'pro' ? document.querySelector('[data-sf-cart]') : null;
    const h = el ? el.offsetHeight : 0;
    if (h && h !== s.dockH) this.setState({ dockH: h });
    const toast = document.querySelector('[data-ef-toast]'), th = toast ? toast.offsetHeight : 0;
    if (th && th !== s.toastH) this.setState({ toastH: th });
  }

  // Brings the server's data in line with what the state shows: lists, missing rows, the quote.
  sync(prev) {
    const s = this.state;
    const changed = (...keys) => !prev || keys.some(k => prev[k] !== s[k]);
    if (changed('cart', 'bundles', 'packIds', 'code', 'applied')) {
      writeJSON(CART_KEY, { cart: s.cart, bundles: s.bundles, packIds: s.packIds, code: s.code, applied: s.applied });
    }
    if (!(s.me && s.me.email) && changed('favs', 'alerts')) writeJSON(FAVS_KEY, { favs: s.favs, alerts: s.alerts });
    // el título de la pestaña, en el idioma de la carcasa (el servidor ya lo pone al llegar; al moverse por
    // la tienda o cambiar de idioma, aquí)
    if (s.dict && changed('lang', 'dict', 'page', 'detail', 'detTab', 'rowsV')) {
      const title = this.tabTitle();
      if (title && title !== document.title) document.title = title;
    }

    if (s.page === 'shop' && s.mode === 'pro') {
      const key = proQuery(s, s.ranges);
      if (key !== this.proKey) {
        const first = this.proKey == null;
        this.proKey = key;
        this.later('pro', () => this.loadPro(1, false), first ? 0 : 150);
      }
    } else if (s.page === 'shop') {
      const key = new URLSearchParams({ tab: s.liteTab, q: s.q.trim().slice(0, Q_MAX) }).toString();
      if (key !== this.liteKey) {
        const first = this.liteKey == null;
        this.liteKey = key;
        this.later('lite', () => this.loadLite(1), first ? 0 : 150);
      }
    }

    if (prev && prev.lang !== s.lang) this.relang();
    const bundleIds = s.bundleDefs ? s.bundleDefs.bundles.flatMap(b => b.ids) : [];
    this.fetchRows([...s.cart, ...s.packIds, ...s.compare, ...s.favs, ...bundleIds, s.freeFor, s.instFor]);
    if (s.page === 'detail' && s.detail) this.fetchFull(s.detail);
    const d = s.page === 'detail' ? this.rows.get(s.detail) : null;
    if (d && d.preview && s.pine[d.preview] === undefined && !this.asked.has(d.preview)) this.fetchPreview(d.preview);
    // el código del árbol, al abrir su pestaña; si no llegó, otra vez al volver a ella (desde la ficha, otra
    // página o el historial) o al pulsarla (showHow), nunca solo: sin red se pediría sin parar
    if (s.page === 'detail' && s.detTab === 'tree' && !s.Tree && (!this.treeAsked || (this.treeFailed && changed('page', 'detail', 'detTab')))) this.loadTree();

    const body = this.cartBody(), quoteKey = JSON.stringify(body);
    if (quoteKey !== this.quoteKey) {
      this.quoteKey = quoteKey;
      if (body.items.length || body.bundles.length || body.pack.length) this.later('quote', () => this.loadQuote(body, quoteKey), 120);
      else if (s.quote) this.setState({ quote: null });
    }

    // My strategies, on its page; on a strategy page too (what the account owns says whether «Update
    // available» is for it), but quietly and once: there a failure is not worth a toast
    const mineWanted = s.page === 'mine' || (s.page === 'detail' && !this.mineQuietTried);
    if (s.me && s.me.email && mineWanted && !s.mine && !this.mineLoading && !this.uploading) this.loadMine(s.page !== 'mine');
    if (s.packOpen && s.packQ.trim().slice(0, Q_MAX) !== this.packKey) {
      const first = this.packKey == null;
      this.packKey = s.packQ.trim().slice(0, Q_MAX);
      this.later('pack', () => this.loadPack(), first ? 0 : 150);
    }
  }

  later(name, fn, ms) {
    clearTimeout(this.timers[name]);
    this.timers[name] = setTimeout(fn, ms);
  }

  // A newer request of the same kind makes an older answer stale: only the last one is applied.
  ticket(name) {
    const n = (this.seq[name] || 0) + 1;
    this.seq[name] = n;
    return () => this.seq[name] === n;
  }

  // Lo que falló, en el idioma de quien mira: la clave que contestó el servidor ({"error": "errAlgo"}),
  // si el diccionario la tiene; si no, un texto según el tipo de fallo. Sólo una petición sin respuesta
  // es un error de red; cualquier otra cosa sin código es un fallo de la página: a la consola, y a quien
  // mira se le pide que lo intente más tarde.
  fail(e) {
    const st = e && e.status;
    if (!st && !(e && e.network)) console.error(e);
    const own = e && e.key && this.state.dict && this.state.dict[e.key] ? e.key : '';
    const key = own || (e && e.network ? 'errShopNetwork' : !st ? 'errLater' : st === 402 ? 'errPayment' : st === 404 || st === 410 ? 'errLinkNotFound'
      : st === 429 ? 'errTooMany' : st >= 500 ? 'errLater' : 'errRequest');
    this.setState({ error: key, errorVars: own && e.detail && e.detail.vars ? e.detail.vars : null });
  }

  // ---- rows ------------------------------------------------------------------------------------

  keep(rows, full) {
    (rows || []).forEach(r => {
      if (!r || !r.id) return;
      this.rows.set(r.id, { ...(this.rows.get(r.id) || {}), ...r });
      if (full) this.full.add(r.id);
    });
  }

  row(id) {
    return (id && this.rows.get(id)) || null;
  }

  fetchRows(ids) {
    ids.forEach(id => {
      if (!id || this.rows.has(id) || this.asked.has(id)) return;
      this.fetchOne(id);
    });
  }

  fetchFull(id) {
    if (this.full.has(id) || this.asked.has('full:' + id)) return;
    this.asked.add('full:' + id);
    this.fetchOne(id);
  }

  fetchOne(id) {
    this.asked.add(id);
    api(this.inLang('/api/strategies/' + encodeURIComponent(id))).then(r => {
      this.keep([r], true);
      // an old address or a cart saved by the first shop names the strategy by its alias (the base64 of
      // its key), which the server resolves: from now on, by its id
      if (r.id && r.id !== id) {
        const swap = arr => [...new Set(arr.map(x => (x === id ? r.id : x)))];
        this.setState(st => ({ cart: swap(st.cart), packIds: swap(st.packIds), compare: swap(st.compare), favs: swap(st.favs),
          freeFor: st.freeFor === id ? r.id : st.freeFor }));
        if (this.state.page === 'detail' && this.state.detail === id) this.go({ detail: r.id }, { replace: true, scroll: false });
      }
      this.setState(st => ({ rowsV: st.rowsV + 1 }));
    }).catch(e => {
      if (e.status !== 404) { this.fail(e); return; }
      // gone from the catalogue: drop it from what the browser remembers
      const drop = arr => arr.filter(x => x !== id);
      this.setState(st => ({ cart: drop(st.cart), packIds: drop(st.packIds), compare: drop(st.compare), favs: drop(st.favs),
        freeFor: st.freeFor === id ? '' : st.freeFor }));
      if (this.state.page === 'detail' && this.state.detail === id) {
        this.fail(e);
        this.go({ page: 'shop' }, { replace: true });
      }
    });
  }

  // Lo que se pide del catálogo, en el idioma de la página: la explicación del indicador de cada fila llega en él
  // (API #2 y #3). ?lang= manda sobre la cookie y la cuenta, como en la carcasa: una página abierta con ?lang=fr y
  // una cuenta en español no la recibe en español.
  inLang(path) {
    return path + (path.includes('?') ? '&' : '?') + 'lang=' + encodeURIComponent(this.state.lang);
  }

  // Otro idioma: lo que enseña la explicación se pide otra vez, sin moverse de donde está: la ficha a la vista
  // (fetchFull, en este mismo sync) y las páginas de Pro que se ven; Pro, si no se ve, al volver a él. Mientras
  // tanto, la de antes dice su idioma (exLang).
  relang() {
    this.full.clear();
    [...this.asked].forEach(k => { if (k.startsWith('full:')) this.asked.delete(k); });
    const s = this.state;
    if (s.page === 'shop' && s.mode === 'pro' && this.proKey != null && s.proPage > 0) this.reloadPro();
    else this.proKey = null;
  }

  reloadPro() {
    const s = this.state, fresh = this.ticket('pro'), pages = [];
    for (let p = s.proFirst; p <= s.proPage; p++) pages.push(p);
    Promise.all(pages.map(p => api(this.inLang('/api/strategies?' + this.proKey + '&size=' + PRO_SIZE + '&page=' + p))))
      .then(ds => {
        if (!fresh()) return;
        const rows = ds.flatMap(d => d.rows);
        this.keep(rows);
        this.setState({ pro: rows });
      }).catch(e => this.fail(e));
  }

  fetchPreview(url) {
    this.asked.add(url);
    // la respuesta de un fallo también se lee: Chromium no da por acabada una no-store que nadie lee (núcleo 0.28)
    fetch(url).then(r => (r.ok ? r.text() : r.text().then(() => ''))).catch(() => '')
      .then(text => this.setState(st => ({ pine: { ...st.pine, [url]: text } })));
  }

  // Un módulo que no llega es un fallo de red. El navegador recuerda el fallo de su dirección (otro import()
  // falla en el acto, sin pedir nada): cada intento nuevo va a otra (?retry=N). Recuerda también el de una de
  // sus piezas (views/tree/…), que tree.js importa sin ?retry: si falló una de ellas, sólo recargar lo arregla.
  // Si llega en otro intento, el aviso de red que dejó el fallo ya no es verdad: se va (antes se quedaba encima
  // del árbol hasta cerrarlo).
  loadTree() {
    const n = this.treeTries || 0;
    this.treeAsked = true;
    this.treeFailed = false;
    import(n ? './tree.js?retry=' + n : './tree.js')
      .then(m => this.setState(st => ({ Tree: m.StrategyTree, ...(n && st.error === 'errShopNetwork' ? { error: '' } : {}) })))
      .catch(e => { this.treeTries = n + 1; this.treeFailed = true; this.fail({ network: true, cause: e }); });
  }

  // «Cómo decide» (su pestaña y el botón de la ficha): si el código del árbol no llegó, pulsarla lo vuelve a
  // pedir, también con la pestaña ya puesta.
  showHow() {
    if (this.treeFailed) this.treeAsked = false;
    this.go({ detTab: 'tree' }, { scroll: false });
  }

  // El título de la pestaña: el de la tienda o, en la página de una estrategia, cuál es (un ticker tiene hasta
  // 17), como su cabecera y sus etiquetas, y la pestaña de la página; el mismo que pone el servidor
  // (templates/edgefolio/shop.html). Mientras no llega su fila, nada: se queda el que hay.
  tabTitle() {
    const s = this.state, t = translator(s.dict, {}, s.lang);
    if (s.page !== 'detail') return 'Edgefolio · ' + t('toolName');
    const r = this.row(s.detail);
    return r ? [r.name || r.ticker, r.ticker, r.key, r.interval, s.detTab === 'tree' ? t('howItDecides') : '', 'Edgefolio'].filter(Boolean).join(' · ') : '';
  }

  // ---- lists -----------------------------------------------------------------------------------

  loadLite(page) {
    const fresh = this.ticket('lite');
    api(this.inLang('/api/strategies?' + this.liteKey + '&size=' + LITE_SIZE + '&page=' + page)).then(d => {
      if (!fresh()) return;
      this.keep(d.rows);
      this.setState(st => ({ lite: page === 1 ? d.rows : [...(st.lite || []), ...d.rows], liteTotal: d.total, litePage: page, counts: d.counts || st.counts }));
    }).catch(e => this.fail(e));
  }

  // Table pages replace the list; "Load more" (rows, cards) appends the next page.
  loadPro(page, append) {
    const fresh = this.ticket('pro'), key = this.proKey, facets = this.facetsKey !== key;
    api(this.inLang('/api/strategies?' + key + '&size=' + PRO_SIZE + '&page=' + page + (facets ? '&facets=1' : ''))).then(d => {
      if (!fresh()) return;
      this.keep(d.rows);
      const patch = { pro: append ? [...this.state.pro, ...d.rows] : d.rows, proTotal: d.total, proPage: page, proLoaded: true, counts: d.counts || this.state.counts };
      if (!append) patch.proFirst = page;
      if (d.hist) {
        this.facetsKey = key;
        Object.assign(patch, { hist: d.hist, options: d.options || {}, ranges: d.ranges || null,
          rg: retrack(this.state.rg, this.state.ranges, d.ranges || null) });
      }
      this.setState(patch);
    }).catch(e => this.fail(e));
  }

  loadPack() {
    const fresh = this.ticket('pack'), q = this.packKey;
    api(this.inLang('/api/strategies?paid=1&sort=hot&size=' + PACK_FIND + (q ? '&q=' + encodeURIComponent(q) : ''))).then(d => {
      if (!fresh()) return;
      this.keep(d.rows);
      this.setState({ packFound: d.rows });
    }).catch(e => this.fail(e));
  }

  // ---- cart and checkout -----------------------------------------------------------------------

  cartBody() {
    const s = this.state, size = s.bundleDefs ? s.bundleDefs.pack.size : 0;
    const custom = s.bundles.includes('custom') && s.packIds.length === size;
    return { items: s.cart, bundles: s.bundles.filter(b => b !== 'custom'), pack: custom ? s.packIds : [], code: s.applied };
  }

  loadQuote(body, key) {
    post('/api/quote', body).then(q => {
      if (this.quoteKey !== key) return;
      const patch = { quote: q };
      if (body.code && q.code_status === 'applied') patch.codeState = 'ok';
      if (body.code && q.code_status === 'invalid') Object.assign(patch, { codeState: 'bad', applied: '' });
      this.setState(patch);
    }).catch(e => {
      if (this.quoteKey !== key) return;
      // ids o lotes que el servidor ya no vende (un carrito viejo de este navegador): fuera. Cualquier
      // otro rechazo (una estrategia dos veces, un pack que no vale) se enseña, nunca se repite.
      const d = e.detail || {}, gone = d.error === 'errUnknownItems' || d.error === 'errUnknownBundles' ? d.items || d.bundles || [] : [];
      if (e.status === 400 && gone.length) {
        this.setState(st => ({ cart: st.cart.filter(x => !gone.includes(x)), bundles: st.bundles.filter(x => !gone.includes(x)), packIds: st.packIds.filter(x => !gone.includes(x)) }));
      } else this.fail(e);
    });
  }

  // The code is checked by the server's quote (never here). An empty box takes the code off; applying
  // the code that is already applied keeps its «applied» (the quote does not change, so nothing would
  // say it again).
  applyCode() {
    const s = this.state, code = s.code.trim();
    if (!code) { this.setState({ applied: '', codeState: '' }); return; }
    if (code === s.applied && s.codeState === 'ok') return;
    this.setState({ applied: code, codeState: '' });
  }

  // One POST /api/orders at a time: a double click would create two PayPal orders. The button stays
  // busy while the browser leaves for PayPal; coming back with the back button (page cache) frees it.
  checkout() {
    const body = this.cartBody();
    // the flag, not the state: setState lands after the click handler, a second click in the same
    // moment would still see paying: false
    if (this.paying || (!body.items.length && !body.bundles.length && !body.pack.length)) return;
    this.paying = true;
    this.setState({ paying: true });
    post('/api/orders', body).then(o => window.location.assign(o.approve_url))
      .catch(e => { this.paying = false; this.setState({ paying: false }); this.fail(e); });
  }

  // Back from PayPal at /thanks?token=<order>: capturing again is harmless (the server makes it idempotent).
  // El carrito se vacía sólo con el cobro que pagó el pedido (paid_now): abrir otra vez una página de gracias
  // vieja (el historial, un marcador) o la de otro en este navegador vaciaba el carrito que tuviera. El código
  // aplicado se queda.
  capture(token) {
    if (!token) { this.go({ page: 'shop' }, { replace: true }); return; }
    post('/api/orders/' + encodeURIComponent(token) + '/capture').then(rc => {
      this.keep(rc.downloads);
      const first = (rc.downloads || [])[0];
      // another browser than the one that paid gets no links (they are in My strategies): the
      // tutorial waits until there is a script to install
      this.mineQuietTried = false;
      this.setState({ receipt: rc, ...(rc.paid_now ? { cart: [], bundles: [], packIds: [] } : {}), instFor: first ? first.id : '', mine: null,
        instStep: !first || read('edgefolio-install-v1') ? -1 : 0 });
    }).catch(e => { this.fail(e); this.go({ page: 'shop' }, { replace: true }); });
  }

  toggleCompare(id) {
    this.setState(st => ({ compare: st.compare.includes(id) ? st.compare.filter(x => x !== id) : st.compare.length >= 3 ? st.compare : [...st.compare, id] }));
  }

  // ---- la cuenta (la del núcleo), Mis estrategias, favoritas ------------------------------------

  signedIn() {
    return !!(this.state.me && this.state.me.email);
  }

  // Mis estrategias pide la sesión: sin ella, a su dirección, que manda a entrar y vuelve a ella después
  // (/login?next=/mine), no a la página de la que se venía.
  goMine() {
    if (!this.props.signedIn) { window.location.assign('/mine'); return; }
    this.go({ page: 'mine' });
  }

  signOut() {
    post('/logout').catch(() => null).then(() => window.location.assign('/'));
  }

  // Demostrar que un correo es de la cuenta: se manda un enlace a esa dirección. Lo que falla en la dirección
  // sale bajo el campo (los textos del núcleo), como en la gratis: vacía (el campo se puede vaciar) o mal
  // escrita; el rechazo del servidor a la dirección, también; los demás, en un aviso. Una que la cuenta ya
  // demostró (API #15, emails) no se pide: el servidor contestaría lo de siempre sin mandar nada, y lo dice un
  // aviso (quita el de un fallo de antes, que parecería la respuesta).
  askProof() {
    const s = this.state, email = (s.proofEmail ?? ((s.me && s.me.email) || '')).trim();
    if (this.proofBusy) return;
    const err = !email ? 'errEmailRequired' : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? 'errEmailInvalid' : '';
    if (err) { this.setState({ proofErr: err }); return; }
    if (((s.mine && s.mine.emails) || []).includes(email.toLowerCase())) { this.setState({ proofErr: '', error: '', notice: 'proofProven' }); return; }
    this.proofBusy = true;
    post('/api/mine/proofs', { email }).then(() => this.setState({ proofSent: true, proofExpired: false, proofErr: '' }))
      .catch(e => {
        const d = e.detail || {};
        if (e.status === 400 && d.field === 'email' && e.key && this.state.dict && this.state.dict[e.key]) this.setState({ proofErr: e.key });
        else this.fail(e);
      })
      .then(() => { this.proofBusy = false; });
  }

  // El enlace del correo abre /mine?proof=<token>. Abrirlo sólo enseña de qué correo es (los lectores de
  // correo también abren los enlaces); lo gasta el clic de la persona.
  peekProof(token) {
    post('/api/mine/proofs/peek', { token }).then(r => {
      if (!r.email) { this.setState({ proofExpired: true, proofToken: '', proofAs: '' }); dropParams('proof'); return; }
      this.setState({ proofToken: token, proofAs: r.email, proofExpired: false });
    }).catch(e => { if (e.status === 401) toLogin(); else this.fail(e); });
  }

  confirmProof() {
    const token = this.state.proofToken;
    if (!token || this.proofBusy) return;
    this.proofBusy = true;
    post('/api/mine/proofs/confirm', { token }).then(() => {
      dropParams('proof');
      this.mineQuietTried = false;
      this.setState({ proofToken: '', proofAs: '', proofSent: false, proofExpired: false, mine: null });
    }).catch(e => {
      if (e.status === 400) { this.setState({ proofExpired: true, proofToken: '', proofAs: '' }); dropParams('proof'); } else this.fail(e);
    }).then(() => { this.proofBusy = false; });
  }

  // Favourites kept in this browser while signed out move to the account once signed in.
  // Only the ones the server took leave this browser; the others stay for the next sign-in, with one
  // error shown. /api/mine is read once, after the uploads (sync() waits for them).
  // Una que ya no está en el catálogo (404) también se va, sin aviso: no hay nada que guardar (como hace
  // fetchOne con el carrito y Comparar). Antes, si su ficha llegaba después de la subida, salía «No
  // encontramos esa estrategia» y se quedaba en el navegador.
  afterSignIn() {
    const local = readJSON(FAVS_KEY, {}), favs = list(local.favs), alerts = local.alerts || {};
    this.uploading = true;
    Promise.all(favs.map(id => api('/api/favourites/' + encodeURIComponent(id), { method: 'PUT', body: { alerts: alerts[id] || {} } })
      .then(() => null, e => (e.status === 404 ? null : { id, e }))))
      .then(res => {
        const failed = res.filter(Boolean), left = failed.map(x => x.id);
        if (left.length) {
          const keep = {};
          left.forEach(id => { if (alerts[id]) keep[id] = alerts[id]; });
          writeJSON(FAVS_KEY, { favs: left, alerts: keep });
          this.fail(failed[0].e);
        } else write(FAVS_KEY, null);
        this.uploading = false;
        this.loadMine();
      });
  }

  loadMine(quiet = false) {
    this.mineLoading = true;
    if (quiet) this.mineQuietTried = true;
    api('/api/mine').then(m => {
      this.keep(m.items.map(x => x.row));
      this.keep(m.favourites.map(x => x.row));
      const alerts = {};
      m.favourites.forEach(x => { alerts[x.id] = x.alerts || {}; });
      this.setState({ mine: m, favs: m.favourites.map(x => x.id), alerts });
    }).catch(e => {
      if (quiet) return;
      if (e.status === 401) toLogin();
      else this.fail(e);
    }).then(() => { this.mineLoading = false; });
  }

  renew(id) {
    post('/api/mine/renew', { id }).then(entry => this.setState(st => ({
      mine: { ...st.mine, items: st.mine.items.map(x => (x.id === id ? entry : x)) }
    }))).catch(e => this.fail(e));
  }

  // Una favorita y sus alertas cambian en la página al pulsarlas, y después en la cuenta (API #21 y #22). Si el
  // servidor no lo guarda (la sesión se cerró en otra pestaña: 401), vuelven a como las tiene la cuenta, la
  // favorita a su sitio de la lista, y el aviso dice por qué: antes la campana se quedaba encendida y la
  // favorita fuera, sin guardar. De varios cambios seguidos de la misma decide la respuesta del último; lo que
  // tiene la cuenta (favSaved) es lo de antes del primero, o lo último que aceptó el servidor.
  setFav(id, on, alerts) {
    const s = this.state, saved = this.favSaved, signedIn = this.signedIn();
    if (signedIn && !saved.has(id)) saved.set(id, { on: s.favs.includes(id), alerts: s.alerts[id], at: s.favs.indexOf(id) });
    this.setState(st => ({ favs: st.favs.includes(id) === on ? st.favs : on ? [...st.favs, id] : st.favs.filter(x => x !== id),
      alerts: st.alerts[id] === alerts ? st.alerts : { ...st.alerts, [id]: alerts } }));
    if (!signedIn) return;
    const last = this.ticket('fav:' + id), url = '/api/favourites/' + encodeURIComponent(id);
    (on ? api(url, { method: 'PUT', body: { alerts: alerts || {} } }) : api(url, { method: 'DELETE' })).then(() => {
      if (last()) saved.delete(id);
      else if (saved.has(id)) saved.set(id, { ...saved.get(id), on, alerts });
    }, e => {
      const was = last() && saved.get(id);
      if (was) {
        saved.delete(id);
        this.setState(st => {
          const rest = st.favs.filter(x => x !== id), at = was.at < 0 ? rest.length : Math.min(was.at, rest.length);
          return { favs: !was.on ? rest : st.favs.includes(id) ? st.favs : [...rest.slice(0, at), id, ...rest.slice(at)],
            alerts: { ...st.alerts, [id]: was.alerts } };
        });
      }
      this.fail(e);
    });
  }

  toggleFav(id) {
    this.setFav(id, !this.state.favs.includes(id), this.state.alerts[id]);
  }

  toggleAlert(id, k) {
    const cur = this.state.alerts[id] || {};
    this.setFav(id, true, { ...cur, [k]: !cur[k] });
  }

  // Every way into the free-download dialog starts with news unticked (GDPR: consent is asked each time).
  // The focus goes in and back with syncModal(): the cursor in its field (not on a touch screen), and back
  // on the button that opened it when it closes.
  openFree(id) {
    this.setState({ freeFor: id, freeSent: false, freeNews: false, freeErr: '' });
  }

  closeFree() {
    this.setState({ freeFor: '', freeSent: false, freeNews: false, freeErr: '' });
  }

  // What is wrong with the address shows under the field (the core's texts): empty, or not an address.
  // The server checks it again; its refusal of the address goes under the field too, any other one
  // (too many today, not free…) is a toast.
  sendFree() {
    const s = this.state, email = s.freeEmail.trim();
    if (this.freeBusy) return;
    const err = !email ? 'errEmailRequired' : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? 'errEmailInvalid' : '';
    if (err) { this.setState({ freeErr: err }); return; }
    this.freeBusy = true;
    post('/api/free', { id: s.freeFor, email, news: s.freeNews })
      .then(() => { this.mineQuietTried = false; this.setState({ freeSent: true, freeErr: '', mine: null }); })
      .catch(e => {
        const d = e.detail || {};
        if (e.status === 400 && d.field === 'email' && e.key && this.state.dict && this.state.dict[e.key]) this.setState({ freeErr: e.key });
        else this.fail(e);
      })
      .then(() => { this.freeBusy = false; });
  }

  // ---- navigation and preferences --------------------------------------------------------------

  go(patch, { replace = false, scroll = true } = {}) {
    const path = pathOf({ ...this.state, ...patch });
    if (path !== location.pathname || location.search || location.hash) history[replace ? 'replaceState' : 'pushState'](null, '', path);
    this.setState({ ...patch, tip: '' });
    if (scroll) try { window.scrollTo(0, 0); } catch (e) { /* not scrollable */ }
  }

  setMode(mode) {
    write('tuisku-sf-mode', mode);
    this.setState({ mode });
    if (this.state.page !== 'shop') this.go({ page: 'shop' });
  }

  // Un desplegable de los filtros de Pro, uno a la vez. Se recuerda su botón: Esc le devuelve el foco.
  toggleSel(k, button) {
    if (button) this.selButton = button;
    this.setState(st => ({ openSel: st.openSel === k ? '' : k, selQ: '' }));
  }

  setPview(pview) {
    write('tuisku-sf-pview5', pview);
    const s = this.state;
    // "Load more" leaves several pages in the list; the table shows one: the last one loaded, so the
    // pager and "a–b of N" point at it. Its rows are already here; the reload keeps them fresh.
    if (pview === 'table' && s.pro.length > PRO_SIZE && s.proPage > s.proFirst) {
      this.setState({ pview, pro: s.pro.slice((s.proPage - s.proFirst) * PRO_SIZE), proFirst: s.proPage });
      this.loadPro(s.proPage, false);
    } else this.setState({ pview });
  }

  // ---- phone bar ---------------------------------------------------------------------------------

  // Pone un elemento justo debajo de la barra fija (tapa lo de arriba de la página).
  scrollUnderHeader(el) {
    const header = document.querySelector('header.app-topbar');
    const top = el.getBoundingClientRect().top + window.scrollY - (header ? header.offsetHeight : 0) - 12;
    try { window.scrollTo(0, Math.max(0, top)); } catch (e) { /* not scrollable */ }
  }

  // Runs fn once the shop and its list are on screen (the bar's buttons work from every page, and
  // the list's height moves what comes after it); after 3 s it runs anyway.
  onShop(fn) {
    if (this.state.page !== 'shop') this.go({ page: 'shop' });
    let tries = 0;
    const run = () => {
      const s = this.state, ready = s.page === 'shop' && (s.mode === 'pro' ? s.proLoaded : !!s.lite);
      if ((ready || tries >= 59) && fn()) return;
      if (++tries < 60) setTimeout(run, 50);
    };
    setTimeout(run, 0);
  }

  // Search: the strategy search of the list on screen, Lite's or Pro's (never the discount code). Lite's
  // is in the header: the shop at the top, as in the design; Pro's, just under the bar (it is sticky and
  // tall on a phone: a plain focus() could leave the box behind it).
  focusSearch() {
    this.onShop(() => {
      const input = document.querySelector('input[data-search]');
      if (!input) return false;
      input.focus({ preventScroll: true });
      if (this.state.mode === 'pro') this.scrollUnderHeader(input);
      else try { window.scrollTo(0, 0); } catch (e) { /* not scrollable */ }
      return true;
    });
  }

  // Cart: Pro's cart strip, just under the bar. In Lite nothing moves: the floating cart is already on
  // screen above the phone bar (from another page, go() opens the shop at the top), as in the design.
  showCart() {
    this.onShop(() => {
      const cart = document.querySelector('[data-sf-cart]');
      if (cart && this.state.mode === 'pro') this.scrollUnderHeader(cart);
      return true;
    });
  }


  // There is no TradingView API to connect to: the chip opens TradingView and remembers the choice.
  toggleTv() {
    const on = !this.state.tv;
    if (on) window.open('https://www.tradingview.com/', '_blank', 'noopener');
    write('edgefolio-tv', on ? '1' : null);
    this.setState({ tv: on });
  }

  closeTour() {
    write('edgefolio-tour-v1', '1');
    this.setState({ tourStep: -1 });
  }

  closeInst() {
    write('edgefolio-install-v1', '1');
    this.setState({ instStep: -1 });
  }

  // Tour and tutorial: a tap moves on, a swipe moves either way (flipped in Arabic), keys too.
  // El puntero, capturado: con el ratón, un deslizamiento que acaba fuera de la imagen (desde el logo de
  // TradingView, que está en su borde) también cuenta; el dedo ya lo está solo.
  swDown(e) {
    this.sw = { x: e.clientX, y: e.clientY };
    const area = e.currentTarget;
    if (area && area.setPointerCapture) try { area.setPointerCapture(e.pointerId); } catch (err) { /* sin captura, como antes */ }
  }

  swUp(e, which) {
    const p = this.sw;
    this.sw = null;
    if (!p) return;
    const s = this.state, cur = s[which], max = which === 'instStep' ? 4 : 2;
    if (cur < 0) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y, rtl = s.dir === 'rtl';
    let d = 0;
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) d = 1;
    else if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) d = ((dx < 0) !== rtl) ? 1 : -1;
    const n = Math.min(max, Math.max(0, cur + d));
    if (n !== cur) this.setState({ [which]: n });
  }

  onKey(e) {
    const s = this.state, which = s.instStep >= 0 ? 'instStep' : s.tourStep >= 0 ? 'tourStep' : '';
    if (e.key === 'Tab' && this.modal) { keepTab(this.modal.el, e); return; }
    // Esc closes what is open on top, one at a time: compare, the pack picker, the free download, a Pro
    // filter's dropdown (the language menu is the core's, and closes itself)
    if (!which) {
      if (e.key !== 'Escape') return;
      if (s.cmpOpen) this.setState({ cmpOpen: false });
      else if (s.packOpen) this.setState({ packOpen: false });
      else if (s.freeFor) this.closeFree();
      else if (s.openSel) {
        // con el foco dentro del desplegable (su buscador), el foco se caería a <body>: vuelve a su botón
        const button = this.selButton;
        this.setState({ openSel: '', selQ: '' }, () => {
          const a = document.activeElement;
          if (button && button.isConnected && (!a || a === document.body)) button.focus();
        });
      }
      return;
    }
    if (e.key === 'Escape') { if (which === 'instStep') this.closeInst(); else this.closeTour(); return; }
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const max = which === 'instStep' ? 4 : 2, fwd = (e.key === 'ArrowRight') !== (s.dir === 'rtl');
    const n = Math.min(max, Math.max(0, s[which] + (fwd ? 1 : -1)));
    if (n !== s[which]) { e.preventDefault(); this.setState({ [which]: n }); }
  }

  render() {
    const s = this.state;
    // sin textos de relleno: nada se pinta hasta que llega el diccionario
    if (!s.dict) return null;
    return Storefront(renderVals(this));
  }
}
