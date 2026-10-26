// "How it decides": the decision tree of one strategy, drawn from its Pine script.
// Ported from class Component of docs/design/Strategy Tree.dc.html (v7). The logic stays as close
// to the design as possible because the views in ./views/tree/ were checked against it pixel by
// pixel; renderVals() returns the same names the design's template reads.
// Visitors see the first tree of the public preview (strategy.preview); an owner sees the complete
// forest from GET /api/mine/<id>/script, which needs the session cookie.
import { Component, createRef } from '../vendor/preact.module.js';
import TreeRoot from './views/tree/tree_root.js';

// The base texts live here for en and es as in the design; trees/ui.json adds the newer keys for
// both and every text of the other six languages (a missing key falls back to English).
const TEXT = {
  en: {
    locale: 'en-GB', pageName: 'Strategy tree', store: 'Open the store', h1: 'How a strategy decides',
    intro: 'Each strategy is a random forest, a group of decision trees. This page draws the first tree of each strategy from its free preview. Move the values, or click a result, to see the path.',
    s1: 'Each box checks one indicator from the chart against a fixed value.',
    s2h: 'At or below the value (≤) the path goes up; above it (>) the path goes down.',
    s2v: 'At or below the value (≤) the path goes left; above it (>) the path goes right.',
    s3: 'The path ends in a result: a score from −1 (sell) to +1 (buy).',
    forest: 'The strategy combines many trees like this one, so one tree alone does not decide its signal.',
    loading: 'Loading the tree…', loadErr: 'Could not load the tree:', output: 'Tree output', sellEnd: 'Sell −1', buyEnd: 'Buy +1',
    buyEx: 'Buy example', sellEx: 'Sell example', exHelp: 'Sets the values that reach the strongest buy or sell result of this tree.',
    values: 'Indicator values', lg1: 'A value the tree checks (hover it)', lg2: 'Checked on the current path', lg3: 'Range where the result stays the same',
    unused: 'Not used in the visible part:', no: 'No', yes: 'Yes', visitor: 'Visitor', owner: 'Owner', tree1: 'Tree 1 of the forest',
    treeOf: 'Tree {n} of the forest',
    treeTab: 'Tree', rulesTab: 'Rules', buy: 'Buy', sell: 'Sell', none: 'No signal', paid: 'Paid part', path: 'Current path',
    // a free strategy's hidden branches are in the full script, which is sent by email
    fPaid: 'Full script', fPaid1: '1 branch in the full script', fPaidN: '{n} branches in the full script', fCta1: '1 branch of this tree is in the full script.', fCtaN: '{n} branches of this tree are in the full script.', fCtaRest: ' The strategy is free: ask for it by email to see the complete tree and download the .pine.', fLock: 'This branch is in the full script. The strategy is free: ask for it by email to see the complete tree and download the .pine.', fBtn: 'Get it free',
    unlockBtn: 'Buy to unlock', added: 'Added to the cart', download: 'Download .pine', signIn: 'Sign in',
    source: 'Source: the Pine script of each strategy, its free preview or, for owners, the complete script. Values and scores are exactly as written there.',
    statusPreview: 'preview', statusComplete: 'complete tree', visible: '{n} results visible', paid1: '1 branch in the paid part', paidN: '{n} branches in the paid part',
    complete: 'Complete tree · {n} results', created: 'created {d}', check: 'Check {n}', result: 'Result',
    upB: 'upper branch', dnB: 'lower branch', lB: 'left branch', rB: 'right branch',
    curVal: 'Current value', checksAt: 'The tree checks it at', tickTitle: '{f} checked at {t}',
    tickText: 'One step of the tree compares {name} with {t}. At or below this value it goes one way, above it goes the other.',
    onPath: 'Used on the current path', now: 'Now', stepsTo: 'Checks to get here',
    leafText: 'Score of this result: the average outcome of the training days that ended here, from −1 (sell) to +1 (buy). The script marks strong scores as buy or sell. Click to set the values that lead here.',
    lockText: 'This branch is in the paid script. Buying the strategy shows the complete tree and every tree of its forest, and lets you download the .pine from My strategies.',
    defDesc: 'Value of this indicator as used when the model was trained.',
    cta1: '1 branch of this tree is in the paid part.', ctaN: '{n} branches of this tree are in the paid part.',
    ctaRest: ' Buying the strategy shows the complete tree and every tree of its forest, and lets you download the .pine.',
    ownSignIn: 'Owner view: sign in to My strategies with the email you bought this strategy with to see its complete tree and download the script. Not yours yet? Buy it to unlock everything.',
    ownNotYours: 'Owner view: this strategy is not among the purchases of the email you are signed in with. Buy it to see its complete tree and download the script.',
    // una gratis se pide por correo, no se compra
    fOwnSignIn: 'Owner view: sign in to My strategies with the email you asked for this strategy with to see its complete tree and download the script. Not yours yet? It is free: ask for it by email.',
    fOwnNotYours: 'Owner view: this strategy is not among the ones asked for with the email you are signed in with. It is free: ask for it by email to see its complete tree and download the script.',
    ownFull: 'Owner view: this is the complete tree. Download the script to use it in TradingView.',
    ownFail: 'Owner view: we could not load your complete script. Download it from My strategies or try again later.',
    // la que ya es de la cuenta (la ficha dice «Ya es tuya»): la vista de visitante lleva a la de propietario
    ownedRest: ' Already yours: the complete tree and every tree of its forest are in the owner view.',
    ownedLock: 'Already yours: this branch and the complete tree are in the owner view.', ownedBtn: 'View as owner',
    whatIs: 'What is {f}?',
    relNote: 'As the model sees it: divided by the close of the candle.',
    // sin los niveles del script (scored): cada resultado, con su puntuación y sin comprar, vender ni esperar
    score: 'Score', results: 'Results', s3Score: 'The path ends in a result: its score, from −1 to +1.',
    noLevels: 'The scores at which this script buys and closes are in its full script: here each result shows only its score.',
    leadScore1: 'Gives this score when this condition is met:', leadScoreN: 'Gives this score when these {n} conditions are met at the same time:',
    hiEx: 'Highest score', loEx: 'Lowest score', exHelpScore: 'Sets the values that reach the highest or lowest score of this tree.',
    optTextScore: 'The model chose these values from historical data and they are fixed in the script. Moving a slider does not change the strategy: it simulates a different market reading so you can see which result it reaches.',
    leafFootScore: 'Score from −1 to +1: the average of the training days that ended here. Click to go to this result.'
  },
  es: {
    locale: 'es-ES', pageName: 'Árbol de la estrategia', store: 'Abrir la tienda', h1: 'Cómo decide una estrategia',
    intro: 'Cada estrategia es un bosque aleatorio, un grupo de árboles de decisión. Esta página dibuja el primer árbol de cada estrategia a partir de su vista previa gratuita. Mueve los valores, o haz clic en un resultado, para ver el camino.',
    s1: 'Cada caja compara un indicador del gráfico con un valor fijo.',
    s2h: 'Si es igual o menor (≤), el camino sube; si es mayor (>), baja.',
    s2v: 'Si es igual o menor (≤), el camino va a la izquierda; si es mayor (>), a la derecha.',
    s3: 'El camino termina en un resultado: una puntuación de −1 (venta) a +1 (compra).',
    forest: 'La estrategia combina muchos árboles como este, así que su señal no la decide un solo árbol.',
    loading: 'Cargando el árbol…', loadErr: 'No se pudo cargar el árbol:', output: 'Resultado del árbol', sellEnd: 'Venta −1', buyEnd: 'Compra +1',
    buyEx: 'Ejemplo de compra', sellEx: 'Ejemplo de venta', exHelp: 'Pone los valores que llevan al resultado de compra o venta más fuerte de este árbol.',
    values: 'Valores de los indicadores', lg1: 'Un valor que el árbol comprueba (pasa el ratón)', lg2: 'Comprobado en el camino actual', lg3: 'Rango en el que el resultado no cambia',
    unused: 'No se usan en la parte visible:', no: 'No', yes: 'Sí', visitor: 'Visitante', owner: 'Propietario', tree1: 'Árbol 1 del bosque',
    treeOf: 'Árbol {n} del bosque',
    treeTab: 'Árbol', rulesTab: 'Reglas', buy: 'Compra', sell: 'Venta', none: 'Sin señal', paid: 'Parte de pago', path: 'Camino actual',
    // a free strategy's hidden branches are in the full script, which is sent by email
    fPaid: 'Script completo', fPaid1: '1 rama en el script completo', fPaidN: '{n} ramas en el script completo', fCta1: '1 rama de este árbol está en el script completo.', fCtaN: '{n} ramas de este árbol están en el script completo.', fCtaRest: ' La estrategia es gratis: pídela por email para ver el árbol completo y descargar el .pine.', fLock: 'Esta rama está en el script completo. La estrategia es gratis: pídela por email para ver el árbol completo y descargar el .pine.', fBtn: 'Conseguirla gratis',
    unlockBtn: 'Comprar para desbloquear', added: 'Añadida al carrito', download: 'Descargar .pine', signIn: 'Entrar',
    source: 'Fuente: el script Pine de cada estrategia, su vista previa gratuita o, para quien la ha comprado, el script completo. Los valores y las puntuaciones son exactamente los que aparecen ahí.',
    statusPreview: 'vista previa', statusComplete: 'árbol completo', visible: '{n} resultados visibles', paid1: '1 rama en la parte de pago', paidN: '{n} ramas en la parte de pago',
    complete: 'Árbol completo · {n} resultados', created: 'creado el {d}', check: 'Paso {n}', result: 'Resultado',
    upB: 'rama de arriba', dnB: 'rama de abajo', lB: 'rama izquierda', rB: 'rama derecha',
    curVal: 'Valor actual', checksAt: 'El árbol lo compara con', tickTitle: '{f} comparado con {t}',
    tickText: 'Un paso del árbol compara {name} con {t}. Si es igual o menor va por un lado; si es mayor, por el otro.',
    onPath: 'Usado en el camino actual', now: 'Ahora', stepsTo: 'Pasos hasta aquí',
    leafText: 'Puntuación de este resultado: la media de los días de entrenamiento que acabaron aquí, de −1 (venta) a +1 (compra). El script marca las puntuaciones fuertes como compra o venta. Haz clic para poner los valores que llevan aquí.',
    lockText: 'Esta rama está en el script de pago. Al comprar la estrategia ves el árbol completo y todos los árboles de su bosque, y puedes descargar el .pine desde Mis estrategias.',
    defDesc: 'Valor de este indicador tal como se usó al entrenar el modelo.',
    cta1: '1 rama de este árbol está en la parte de pago.', ctaN: '{n} ramas de este árbol están en la parte de pago.',
    ctaRest: ' Al comprar la estrategia ves el árbol completo y todos los árboles de su bosque, y puedes descargar el .pine.',
    ownSignIn: 'Vista de propietario: entra en Mis estrategias con el email con el que compraste esta estrategia para ver su árbol completo y descargar el script. ¿Aún no es tuya? Cómprala para desbloquearlo todo.',
    ownNotYours: 'Vista de propietario: esta estrategia no está entre las compras del email con el que has entrado. Cómprala para ver su árbol completo y descargar el script.',
    fOwnSignIn: 'Vista de propietario: entra en Mis estrategias con el email con el que pediste esta estrategia para ver su árbol completo y descargar el script. ¿Aún no la tienes? Es gratis: pídela por email.',
    fOwnNotYours: 'Vista de propietario: esta estrategia no está entre las que se pidieron con el email con el que has entrado. Es gratis: pídela por email para ver su árbol completo y descargar el script.',
    ownFull: 'Vista de propietario: este es el árbol completo. Descarga el script para usarlo en TradingView.',
    ownFail: 'Vista de propietario: no pudimos cargar tu script completo. Descárgalo desde Mis estrategias o inténtalo más tarde.',
    ownedRest: ' Ya es tuya: el árbol completo y todos los árboles de su bosque están en la vista de propietario.',
    ownedLock: 'Ya es tuya: esta rama y el árbol completo están en la vista de propietario.', ownedBtn: 'Ver como propietario',
    whatIs: '¿Qué es {f}?',
    relNote: 'Tal como lo ve el modelo: dividido por el cierre de la vela.',
    score: 'Puntuación', results: 'Resultados', s3Score: 'El camino termina en un resultado: su puntuación, de −1 a +1.',
    noLevels: 'Las puntuaciones con las que este script compra y cierra están en su script completo: aquí cada resultado enseña solo su puntuación.',
    leadScore1: 'Da esta puntuación cuando se cumple esta condición:', leadScoreN: 'Da esta puntuación cuando se cumplen estas {n} condiciones a la vez:',
    hiEx: 'Puntuación más alta', loEx: 'Puntuación más baja', exHelpScore: 'Pone los valores que llevan a la puntuación más alta o más baja de este árbol.',
    optTextScore: 'El modelo eligió estos valores con datos históricos y vienen fijados en el script. Mover un deslizador no cambia la estrategia: simula otra lectura del mercado para que veas a qué resultado llega.',
    leafFootScore: 'Puntuación de −1 a +1: la media de los días de entrenamiento que acabaron aquí. Haz clic para ir a este resultado.'
  }
};

// Every tree shares these two files; one request each per visit, not per strategy.
let shared = null;
const sharedData = () => shared || (shared = Promise.all([
  fetch('/static/trees/features.json').then(r => (r.ok ? r.json() : r.text().then(() => { throw new Error('/static/trees/features.json'); }))),
  fetch('/static/trees/ui.json').then(r => r.json()).catch(() => ({}))
]).catch(e => { shared = null; throw e; }));

// La respuesta de un fallo también se lee: Chromium no da por acabada una no-store que nadie lee (núcleo 0.28).
const text = (url, init) => fetch(url, init).then(r => (r.ok ? r.text() : r.text().then(() => { throw new Error(url + ' (' + r.status + ')'); })));
const rowId = P => (P.strategy && P.strategy.id) || '';

// Lo que hace el script con una puntuación: compra con op_operation >= su nivel de compra y cierra con <= su
// nivel de cierre. Desde el catálogo de 2026-10 cada script tiene los suyos (las entradas buyThreshold y
// sellThreshold, que el generador elige para cada modelo con datos de validación: de 0,4 a 1,0 para comprar,
// de −1,0 a −0,5 para cerrar) y la vista previa pública se corta antes. El propietario colorea con los de su
// script completo (levelsOf); el visitante, con los que publica la tienda (API #3: buy_at y close_at, de
// catalogue/levels.json) y, sin ellos, con ninguno: cada resultado enseña su puntuación, sin decir comprar,
// vender ni esperar, y la pestaña dice por qué (scored). 0,55 y −0,9, los de todos los scripts de 2024, sólo
// valen para un script completo que no dice los suyos. Los comentarios «// buy|sell» de la fábrica marcan ±0,7 y
// no son los niveles.
const BUY_AT = 0.55, CLOSE_AT = -0.9;
const signalOf = (v, lv) => (v >= lv.buy ? 'buy' : v <= lv.close ? 'sell' : 'none');
// Si el navegador pone el signo + del idioma (signDisplay, de Safari 14.1 en adelante): fmtV.
const SIGNS = (() => { try { return new Intl.NumberFormat('en', { signDisplay: 'exceptZero' }).format(1) === '+1'; } catch (e) { return false; } })();
// Los que publica la tienda para una estrategia (API #3), o null; sin el de cierre, ningún resultado cierra.
const published = row => (row && typeof row.buy_at === 'number'
  ? { buy: row.buy_at, close: typeof row.close_at === 'number' ? row.close_at : -Infinity } : null);

// Los niveles de un script completo, leídos como los lee edgefolio/formats.py: las entradas de la plantilla
// de 2026, usadas en `if … op_operation >= buyThreshold` y en un `op_operation <= sellThreshold` que cierra,
// o las cifras de la plantilla de antes (`if( op_operation >= 0.55 )`, y un `if( op_operation <= -0.9 )` que
// cierra). Lo que no aparece se queda en el de 2024.
const NUM_RE = '(-?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?)';
const RE_INPUT = new RegExp('^(buy|sell)Threshold\\s*=\\s*input(?:\\.float)?\\(\\s*' + NUM_RE);
const RE_BUY_AT = new RegExp('^if\\s*\\(\\s*op_operation\\s*>=\\s*' + NUM_RE + '\\s*\\)');
const RE_CLOSE_AT = new RegExp('^if\\s*\\(\\s*op_operation\\s*<=\\s*' + NUM_RE + '\\s*\\)');
const RE_BUY_INPUT = /^if\b.*\bop_operation\s*>=\s*buyThreshold\b/, RE_CLOSE_INPUT = /^if\b.*\bop_operation\s*<=\s*sellThreshold\b/;
export function levelsOf(src) {
  const rows = String(src || '').replace(/\r/g, '').split('\n').map(l => ({ ind: l.match(/^[ \t]*/)[0].replace(/\t/g, '    ').length, text: l.trim() })).filter(r => r.text);
  const closes = i => { for (let k = i + 1; k < rows.length && rows[k].ind > rows[i].ind; k++) if (rows[k].text.includes('strategy.close')) return true; return false; };
  const inputs = {};
  rows.forEach(r => { const m = r.text.match(RE_INPUT); if (m) inputs[m[1]] = +m[2]; });
  let buy = null, close = null;
  rows.forEach((r, i) => {
    let m;
    if (buy == null && (m = r.text.match(RE_BUY_AT))) buy = +m[1];
    if (buy == null && 'buy' in inputs && RE_BUY_INPUT.test(r.text)) buy = inputs.buy;
    if (close == null && 'sell' in inputs && RE_CLOSE_INPUT.test(r.text) && closes(i)) close = inputs.sell;
    if (close == null && (m = r.text.match(RE_CLOSE_AT)) && closes(i)) close = +m[1];
  });
  return { buy: buy == null ? BUY_AT : buy, close: close == null ? CLOSE_AT : close };
}

export class StrategyTree extends Component {
  // Si la estrategia está en el carrito lo dice la página (inCart): con una marca propia, el árbol seguía
  // diciendo «Añadida al carrito» después de quitarla con el botón de la cabecera.
  state = { trees: null, full: null, fullLv: null, fullFail: false, sel: 0, vals: {}, view: 'tree', err: '', vw: 1400, tip: null, owner: false, allRules: false };
  treeRef = createRef();
  T = TEXT;

  watchSec() {
    const host = this.base && this.base.querySelector ? this.base : document;
    const q = sel => host.querySelector(sel);
    const el = q('[data-blk-scroll]') || q('[data-tree-sec]');
    if (!el || el === this._secEl) return;
    if (this._ro) this._ro.disconnect();
    this._secEl = el;
    const inner = el.hasAttribute('data-blk-scroll');
    this._measure = () => { if (!el.isConnected) return; const cs = getComputedStyle(el), w = Math.floor(el.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)) - (inner ? 0 : 40); if (w > 0 && w !== this.state.aw) this.setState({ aw: w }); };
    if (window.ResizeObserver) { this._ro = new ResizeObserver(this._measure); this._ro.observe(el); }
    this._measure();
  }
  textW(list, font) { const c = this._mc || (this._mc = document.createElement('canvas').getContext('2d')); c.font = font; return list.reduce((m, t) => Math.max(m, c.measureText(t).width), 0); }
  componentWillUnmount() { this._tok = null; clearInterval(this._ws); if (this._ro) this._ro.disconnect(); if (document.fonts && this._fl) document.fonts.removeEventListener('loadingdone', this._fl); this._fl = null; window.removeEventListener('resize', this._rs); window.removeEventListener('scroll', this._sc, true); }
  componentDidMount() {
    this._rs = () => { this.setState({ vw: window.innerWidth }); if (this._measure) this._measure(); };
    window.addEventListener('resize', this._rs); this._rs(); this._ws = setInterval(() => { this.watchSec(); if (this._secEl) clearInterval(this._ws); }, 300);
    if (document.fonts) { this._fl = () => this.forceUpdate(); document.fonts.addEventListener('loadingdone', this._fl); document.fonts.ready.then(() => this._fl && this._fl()); }
    // Desplazarse cierra la explicación, pero no lo que se desplaza la página sola justo después del toque o
    // el clic que la deja abierta: en el móvil un toque la abre y mueve el camino, el navegador mantiene la
    // caja tocada en su sitio mientras cambian los deslizadores de encima (scroll anchoring) y el marco se va
    // luego al resultado nuevo (follow). Antes, la explicación de una pregunta no llegaba a verse.
    this._sc = e => {
      const now = Date.now(), own = e && e.target && e.target.closest && e.target.closest('[data-tree-scroll],[data-blk-scroll]');
      if (now - (this._pinAt || 0) < 400 || (own && now - (this._followAt || 0) < 400)) return;
      if (this.state.tip) this.setState({ tip: null });
    };
    window.addEventListener('scroll', this._sc, true);
    this.load();
  }
  componentDidUpdate(pp) { this.watchSec(); if (rowId(pp) !== rowId(this.props) || !!pp.owned !== !!this.props.owned) this.load(); }

  // The trees on screen: the owner's complete forest once it is in, otherwise the public preview.
  list(s = this.state) { return (s.owner && s.full) || s.trees; }

  load() {
    const row = this.props.strategy, owned = !!this.props.owned, tok = this._tok = {};
    this.setState({ trees: null, full: null, fullLv: null, fullFail: false, sel: 0, err: '', vals: {}, tip: null, owner: owned });
    if (!row || !row.preview) { this.setState({ err: String((row && row.id) || '') }); return; }
    sharedData()
      .then(([fx, ui]) => text(row.preview).then(src => { if (tok !== this._tok) return; this._fx = fx; this._ui = ui; this.setState({ trees: this.forest(src, row).slice(0, 1), sel: 0 }, () => this.example('buy')); }))
      .catch(e => { if (tok === this._tok) this.setState({ err: String((e && e.message) || e) }); });
    if (!owned) return;
    // Owners only: the server answers 401 without the session cookie, and then the switch explains how to sign in.
    sharedData()
      .then(() => text('/api/mine/' + encodeURIComponent(row.id) + '/script', { credentials: 'same-origin' }))
      .then(src => {
        if (tok !== this._tok) return;
        const full = this.forest(src, row), fullLv = levelsOf(src);
        if (!full.length) throw new Error('no tree');
        this.setState(st => (st.owner ? { full, fullLv, sel: 0, vals: {}, tip: null } : { full, fullLv }), () => { if (this.state.owner) this.example('buy'); });
      })
      .catch(() => { if (tok === this._tok) this.setState({ fullFail: true }); });
  }

  // Switching between the preview and the forest starts again from the strongest buy of tree 1.
  setOwner(on) {
    if (on === this.state.owner) return;
    const same = this.list() === this.list({ ...this.state, owner: on });
    this.setState(same ? { owner: on } : { owner: on, sel: 0, vals: {}, tip: null }, () => { if (!same) this.example('buy'); });
  }

  // Every decision_tree_N function of the script, with what the page shows about the strategy. Qué hace el script
  // con cada resultado (sig) lo dicen los niveles al pintarlo (renderVals): los del visitante pueden llegar después.
  forest(src, row) {
    src = src.replace(/\r/g, '');
    const lines = src.split('\n').map(l => { const m = l.match(/^(\t*)(.*)$/); return { ind: m[1].length, text: m[2].trim() }; }).filter(l => l.text);
    const bases = ((src.match(/^\/\/ Technical base pattern:(.*)$/m) || [])[1] || '').split(',').map(b => b.trim()).filter(Boolean);
    const meta = {
      ticker: row.ticker, key: row.key, hash: row.hash, interval: row.interval, icon: row.icon, bases,
      pattern: bases.map(b => b.replace(/^L_/, '').replace(/_/g, ' ')).join(' + ') || row.ind || row.key,
      created: (src.match(/Date Creation: (\d{4})\/(\d{2})\/(\d{2})/) || []).slice(1).join('-')
    };
    const out = [];
    for (let at = 0, tr; (tr = this.parse(lines, at)); at = tr.next) out.push({ ...meta, ...tr });
    return out;
  }

  // One tree from lines[from]: nested `if( f <= t )` / `if( f > t )` ending in `ret := score // buy|sell`.
  // Whatever the preview cut (or anything unexpected) becomes a locked "Paid part" stub.
  parse(lines, from) {
    let i = lines.findIndex((l, k) => k >= from && /^decision_tree_\d+_/.test(l.text));
    if (i < 0) return null;
    const sig = lines[i].text.match(/\(([^)]*)\)\s*=>/);
    const params = ((lines[i + 1] && lines[i + 1].text.match(/DecisionTreeRegressor\(([^)]*)\)/)) || [])[1] || '';
    const head = lines[i].ind;
    i++;
    while (i < lines.length && lines[i].ind > head && !/^(if\(|ret :=)/.test(lines[i].text)) i++;
    const base = i < lines.length && lines[i].ind > head ? lines[i].ind : -1;
    const NUM = '(-?\\d+(?:\\.\\d+)?(?:e[-+]?\\d+)?)';
    const reLeaf = new RegExp('^ret := ' + NUM + '\\s*(?://\\s*(buy|sell))?', 'i');
    const reLe = new RegExp('^if\\(\\s*(\\w+)\\s*<=\\s*' + NUM + '\\s*\\)', 'i');
    let id = 0, locked = 0, leaves = 0;
    const stub = d => { locked++; return { id: id++, locked: true, depth: d }; };
    const node = (ind, d) => {
      const L = lines[i];
      if (!L || L.ind !== ind) return stub(d);
      let m = L.text.match(reLeaf);
      if (m) { i++; leaves++; return { id: id++, leaf: true, v: +m[1], mark: (m[2] || '').toLowerCase(), depth: d }; }
      m = L.text.match(reLe);
      if (!m) return stub(d);
      i++;
      const n = { id: id++, f: m[1], t: +m[2], raw: m[2], depth: d };
      n.le = node(ind + 1, d + 1);
      const R = lines[i];
      if (R && R.ind === ind && new RegExp('^if\\(\\s*' + n.f + '\\s*>\\s*').test(R.text)) { i++; n.gt = node(ind + 1, d + 1); }
      else n.gt = stub(d + 1);
      return n;
    };
    const root = node(base, 0);
    while (i < lines.length && lines[i].ind > head) i++;
    return { root, signature: sig ? sig[1].split(',').map(x => x.trim()).filter(Boolean) : [], params, locked, leaves, next: i };
  }

  nodesOf(root) { const out = []; const rec = n => { out.push(n); if (n.le) { rec(n.le); rec(n.gt); } }; rec(root); return out; }

  pathTo(root, target) {
    const rec = (n, acc) => {
      if (n.id === target) return acc;
      if (!n.le) return null;
      return rec(n.le, [...acc, { f: n.f, t: n.t, dir: 'le' }]) || rec(n.gt, [...acc, { f: n.f, t: n.t, dir: 'gt' }]);
    };
    return rec(root, []);
  }

  featInfo(tr) {
    const ts = {}, order = [], q = [tr.root];
    while (q.length) { const n = q.shift(); if (n.f) { if (!ts[n.f]) { ts[n.f] = []; order.push(n.f); } ts[n.f].push(n.t); } if (n.le) q.push(n.le, n.gt); }
    return order.map(f => {
      const list = [...new Set(ts[f])].sort((a, b) => a - b);
      const isBool = /Int$/.test(f) && list.every(t => t > 0 && t < 1);
      const lo = list[0], hi = list[list.length - 1];
      let span = hi - lo; if (!span) span = Math.max(Math.abs(lo) * 0.5, 1);
      return { f, ts: list, isBool, min: isBool ? 0 : lo - span * 0.3, max: isBool ? 1 : hi + span * 0.3 };
    });
  }

  walk(root, vals) {
    const ids = new Set([root.id]), used = [];
    let n = root;
    while (n.le) { const dir = vals[n.f] <= n.t ? 'le' : 'gt'; used.push({ f: n.f, t: n.t, dir }); n = n[dir]; ids.add(n.id); }
    return { ids, used, leaf: n };
  }

  jump(id) {
    const tr = this.list()[this.state.sel], path = this.pathTo(tr.root, id);
    if (!path) return;
    const vals = { ...this.state.vals };
    this.featInfo(tr).forEach(F => {
      const cs = path.filter(c => c.f === F.f);
      if (!cs.length) { if (vals[F.f] == null) vals[F.f] = F.isBool ? 0 : (F.min + F.max) / 2; return; }
      let lo = -Infinity, hi = Infinity;
      cs.forEach(c => { if (c.dir === 'le') hi = Math.min(hi, c.t); else lo = Math.max(lo, c.t); });
      if (F.isBool) { vals[F.f] = hi < Infinity ? 0 : 1; return; }
      vals[F.f] = ((lo === -Infinity ? F.min : lo) + (hi === Infinity ? F.max : hi)) / 2;
    });
    this.setState({ vals });
  }

  example(kind) {
    const tr = this.list()[this.state.sel];
    const leaves = this.nodesOf(tr.root).filter(n => n.leaf);
    // A preview cut before its first result has nothing to reach.
    if (!leaves.length) return;
    const pick = leaves.reduce((a, b) => (kind === 'buy' ? b.v > a.v : b.v < a.v) ? b : a);
    this.jump(pick.id);
  }

  showTip(e, data, pin) {
    if (!pin && this.state.tip && this.state.tip.pin) return;
    const r = e.currentTarget.getBoundingClientRect(), vw = window.innerWidth, vh = window.innerHeight;
    const x = Math.max(12, Math.min(r.left, vw - 312)), below = r.bottom + 240 < vh;
    if (pin) this._pinAt = Date.now();
    this.setState({ tip: { ...data, pin: !!pin, x, y: below ? r.bottom + 8 : r.top - 8, up: !below } });
  }
  hideTip() { if (this.state.tip && !this.state.tip.pin) this.setState({ tip: null }); }

  clickNode(e, id, kind) {
    if (Date.now() - (this._suppress || 0) < 250) return;
    const touch = !!(window.matchMedia && window.matchMedia('(hover: none)').matches);
    if (kind === 'lock' || touch) this.showTip(e, kind === 'lock' ? { kind: 'lock' } : { kind, id }, true);
    this.jump(id);
  }
  panDown(e) { if ((e.pointerType && e.pointerType !== 'mouse') || e.button !== 0) return; const el = e.currentTarget; this._pan = { el, x: e.clientX, y: e.clientY, l: el.scrollLeft, t: el.scrollTop, moved: false }; }
  panMove(e) { const p = this._pan; if (!p) return; const dx = e.clientX - p.x, dy = e.clientY - p.y; if (!p.moved && Math.abs(dx) + Math.abs(dy) < 6) return; p.moved = true; p.el.scrollLeft = p.l - dx; p.el.scrollTop = p.t - dy; }
  panUp() { if (this._pan && this._pan.moved) this._suppress = Date.now(); this._pan = null; }

  follow() {
    const el = (this.treeRef && this.treeRef.current) || document.querySelector('[data-tree-scroll]'), p = this._leafPos;
    if (!el || !p) return;
    // In Arabic the frame scrolls from its right edge (scrollLeft runs from 0 down to minus the overflow),
    // while the boxes are placed from the left: count from the left so the path stays in view there too.
    const off = getComputedStyle(el).direction === 'rtl' ? el.scrollWidth - el.clientWidth : 0;
    const pad = 40, L = el.scrollLeft + off, T = el.scrollTop, vw = el.clientWidth, vh = el.clientHeight;
    let nl = L, nt = T;
    if (p.x < L + pad) nl = Math.max(0, p.x - pad); else if (p.x + p.w > L + vw - pad) nl = p.x + p.w - vw + pad;
    if (p.y < T + pad) nt = Math.max(0, p.y - pad); else if (p.y + p.h > T + vh - pad) nt = p.y + p.h - vh + pad;
    if (nl !== L || nt !== T) this._followAt = Date.now();
    if (nl !== L) el.scrollLeft = nl - off;
    if (nt !== T) el.scrollTop = nt;
  }

  render() { return TreeRoot({ ...this.props, ...this.renderVals() }); }

  renderVals() {
    const s = this.state, P = this.props, trees = this.list();
    const lg = String(P.lang || 'en').slice(0, 2), es = lg === 'es', L = { ...this.T.en, ...(this.T[lg] || {}) };
    Object.assign(L, es ? { buy: 'Comprar', sell: 'Vender', none: 'Esperar', rulesTab: 'Bloques', qNum: '¿≤ {t}?', qBool: '¿Se cumple?', leadBuy: 'Compra cuando', leadSell: 'Vende cuando', leadNone: 'Espera cuando', between: 'entre {a} y {b}', and: 'y', allRules: 'Ver todas las reglas en frases ({n})', hideRules: 'Ocultar las reglas', rulesOne: '{n} regla', rulesN: '{n} reglas', start: 'Inicio', lockedRules: 'Ramas en la parte de pago: {n}', leafFoot: 'Fuerza de −1 a +1: la media de los días de entrenamiento que acabaron aquí. Haz clic para ir a este resultado.', s1: 'Cada caja hace una pregunta sobre un indicador del gráfico.', s2h: 'Si la respuesta es Sí, el camino sube; si es No, baja.', s2v: 'Si la respuesta es Sí, el camino va a la izquierda; si es No, a la derecha.', s3: 'El camino termina en una acción (comprar, vender o esperar) con su fuerza, de −1 a +1.' }
      : { buy: 'Buy', sell: 'Sell', none: 'Wait', rulesTab: 'Blocks', qNum: 'At or below {t}?', qBool: 'Is it true?', leadBuy: 'Buys when', leadSell: 'Sells when', leadNone: 'Waits when', between: 'between {a} and {b}', and: 'and', allRules: 'See all rules in plain words ({n})', hideRules: 'Hide the rules', rulesOne: '{n} rule', rulesN: '{n} rules', start: 'Start', lockedRules: 'Branches in the paid part: {n}', leafFoot: 'Strength from −1 to +1: the average of the training days that ended here. Click to go to this result.', s1: 'Each box asks a question about one indicator from the chart.', s2h: 'If the answer is Yes the path goes up; if No, it goes down.', s2v: 'If the answer is Yes the path goes left; if No, it goes right.', s3: 'The path ends in an action (buy, sell or wait) with its strength, from −1 to +1.' });
    Object.assign(L, (this._ui && this._ui[lg]) || {});
    const rpl = (str, o) => str.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m));
    const dir = P.direction === 'vertical' ? 'vertical' : 'horizontal';
    const curved = P.edgeStyle !== 'elbow', exact = !!P.exactValues;
    const seg = on => on ? ['#ffffff', '#0950e3', '0 1px 3px rgba(22,38,58,.12)'] : ['transparent', '#5a6b80', 'none'];
    const [tBg, tColor, tShadow] = seg(s.view === 'tree'), [rBg, rColor, rShadow] = seg(s.view === 'rules');
    const [vBg, vColor, vShadow] = seg(!s.owner), [oBg, oColor, oShadow] = seg(s.owner);
    const free = !!(P.strategy && P.strategy.price === 0);
    if (free) Object.assign(L, { paid: L.fPaid, paid1: L.fPaid1, paidN: L.fPaidN, cta1: L.fCta1, ctaN: L.fCtaN, ctaRest: L.fCtaRest, lockText: L.fLock, ownSignIn: L.fOwnSignIn, ownNotYours: L.fOwnNotYours });
    // Ya es de la cuenta (la ficha dice «Ya es tuya»): la vista de visitante ni la vende ni la pide otra vez;
    // su aviso y el candado de una rama llevan a la de propietario (unlock), que la enseña entera
    if (P.owned) Object.assign(L, { ctaRest: L.ownedRest, lockText: L.ownedLock });
    // con qué niveles se leen los resultados (signalOf): el bosque del propietario, con los de su script; el árbol del
    // visitante, con los publicados. Sin ellos (scored) nada dice comprar, vender ni esperar: el tercer paso, los dos
    // ejemplos y su ayuda, la escala de «Resultado del árbol» (−1 y +1, sin venta ni compra), la ayuda de los valores
    // (a qué resultado llega, no qué haría) y el pie de la explicación de un resultado hablan de la puntuación, y la
    // pestaña dice por qué (noLevels)
    const lv = s.full && trees === s.full ? s.fullLv : published(P.strategy), scored = !lv;
    if (scored) Object.assign(L, { s3: L.s3Score, buyEx: L.hiEx, sellEx: L.loEx, exHelp: L.exHelpScore, sellEnd: '−1', buyEnd: '+1', optText: L.optTextScore, leafFoot: L.leafFootScore });
    // y sin sus colores: la escala y los dos ejemplos, en gris, sin el rojo de vender ni el verde de comprar
    const ex = scored ? ['#16263a', '#f4f8fb', '#cfd8e3', '#16263a', '#f4f8fb', '#cfd8e3'] : ['#15803d', '#e8f7ef', '#b7e4c7', '#c0392b', '#fdecea', '#f3c1bb'];
    const unlockLabel = P.owned ? L.ownedBtn : free ? L.fBtn : P.inCart ? L.added : L.unlockBtn;
    const base = {
      L, scored, steps: [L.s1, dir === 'vertical' ? L.s2v : L.s2h, L.s3].map((text, i) => ({ n: String(i + 1), text })),
      gaugeBg: scored ? '#e2e9f0' : 'linear-gradient(90deg,#f3c1bb,#e2e9f0 50%,#b7e4c7)',
      exBuyC: ex[0], exBuyBg: ex[1], exBuyBd: ex[2], exSellC: ex[3], exSellBg: ex[4], exSellBd: ex[5],
      loading: !s.trees && !s.err, ready: !!s.trees, hasErr: !!s.err, err: s.err,
      isTree: s.view === 'tree', isRules: s.view === 'rules',
      showTree: () => this.setState({ view: 'tree' }), showRules: () => this.setState({ view: 'rules' }),
      tBg, tColor, tShadow, rBg, rColor, rShadow, treeRef: this.treeRef,
      asidePos: s.vw >= 840 ? 'sticky' : 'static',
      standalone: !P.embedded, mainPad: P.embedded ? '0' : '28px 28px 64px',
      vBg, vColor, vShadow, oBg, oColor, oShadow, asVisitor: () => this.setOwner(false), asOwner: () => this.setOwner(true),
      panDown: e => this.panDown(e), panMove: e => this.panMove(e), panUp: () => this.panUp(),
      // la × de una explicación, en el idioma de la página: la ficha le da el «Cerrar» del núcleo (closeLabel)
      tipOn: false, tipRows: [], heads: [], closeTip: () => this.setState({ tip: null }), tipClose: P.closeLabel || null, unlockLabel,
      buyExample: () => this.example('buy'), sellExample: () => this.example('sell')
    };
    if (!s.trees) return { ...base, picks: [], forestPicks: [], feats: [], nodes: [], edges: [], labels: [], rules: [], pathChips: [], groups: [], blocks: [], tipBars: [] };

    const FX = this._fx || { features: {}, patterns: {} };
    const minus = x => x.replace('-', '−');
    const fmt = x => {
      if (exact) return minus(String(x));
      const a = Math.abs(x);
      return minus(new Intl.NumberFormat(L.locale, { maximumFractionDigits: a >= 1000 ? 0 : a >= 100 ? 1 : a >= 10 ? 2 : 3 }).format(x));
    };
    // el + lo pone el formato del idioma (signDisplay), como el −: en árabe, con su marca de izquierda a derecha, y una
    // puntuación sale «+0.89», no «0.89+» (sólo el − la llevaba); un navegador sin signDisplay, el + de siempre
    const fmtV = v => (SIGNS ? '' : v > 0 ? '+' : '') + minus(new Intl.NumberFormat(L.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' }).format(v));
    const isBoolF = f => /Int$/.test(f);
    const nice = f => f.replace(/Int$/, '');
    // [nombre, descripción, el idioma de la descripción]. Un nombre es el de su patrón (el quinto campo): `d` es la
    // %D del RSI estocástico y una distancia de precio en WaveTrend, así que el de un nombre que usan dos patrones
    // lleva el suyo en la clave (`d@Wave_Trend_Calculation`), que se mira antes. Las entradas del generador de 2026 en
    // unidades de precio van divididas por el cierre (`BBlower__close`): el nombre conocido, con una nota. Nombres y
    // descripciones, en en y es en features.json y en los otros seis idiomas en ui.json (feat y featDesc, con la misma
    // clave); una descripción sin traducir sale en inglés, con su nota en inglés, y lo dice (lang).
    const bases = ((trees[s.sel] || {}).bases) || [];
    const own = x => (x && (!x[4] || !bases.length || bases.includes(x[4])) ? x : null);
    const keyOf = f => {
      for (const g of /__close$/.test(f) ? [f, f.replace(/__close$/, '')] : [f]) {
        const k = [...bases.map(b => g + '@' + b), g].find(c => own(FX.features[c]));
        if (k) return k;
      }
      return '';
    };
    const fdesc = f => {
      const k = keyOf(f), x = k ? FX.features[k] : null;
      // sin k, el código, en todos los idiomas: el nombre traducido (feat) también es el de su patrón
      if (!x) return [nice(f), L.defDesc, lg];
      const noted = (text, note) => (k.split('@')[0] !== f ? text + ' ' + note : text);
      if (es) return [x[2], noted(x[3], L.relNote), 'es'];
      if (lg === 'en') return [x[0], noted(x[1], L.relNote), 'en'];
      const name = (L.feat || {})[k] || x[0], text = (L.featDesc || {})[k];
      return text ? [name, noted(text, L.relNote), lg] : [name, noted(x[1], this.T.en.relNote), 'en'];
    };
    const SIG = {
      buy: [L.buy, '#15803d', '#e8f7ef', '#b7e4c7', 'rgba(21,128,61,.22)'],
      sell: [L.sell, '#c0392b', '#fdecea', '#f3c1bb', 'rgba(192,57,43,.22)'],
      none: [L.none, '#5a6b80', '#f4f8fb', '#cfd8e3', 'rgba(90,107,128,.2)'],
      // sin niveles: la puntuación, sin el color de comprar, vender ni esperar
      score: [L.score, '#16263a', '#f4f8fb', '#cfd8e3', 'rgba(22,38,58,.16)']
    };

    const pickOf = i => () => { if (i !== s.sel) this.setState({ sel: i, vals: {}, tip: null }, () => this.example('buy')); };
    const picks = trees.map((t, i) => {
      const on = i === s.sel;
      return {
        icon: t.icon, ticker: t.ticker, key: t.key, pattern: t.pattern, status: t.locked ? L.statusPreview : L.statusComplete,
        bg: on ? '#f5f8ff' : '#ffffff', bd: on ? '#0950e3' : '#e2e9f0', color: on ? '#0950e3' : '#16263a',
        pick: pickOf(i)
      };
    });
    // An owner's forest with more than one tree: the "Tree 1 of the forest" badge becomes one button per tree.
    const forestPicks = trees.length > 1 ? trees.map((t, i) => {
      const on = i === s.sel;
      return { text: on ? rpl(L.treeOf, { n: i + 1 }) : String(i + 1), bg: on ? '#e9f0fd' : '#f4f8fb', color: on ? '#0950e3' : '#5a6b80', pick: pickOf(i) };
    }) : [];

    const tr = trees[s.sel];
    this.nodesOf(tr.root).forEach(n => { if (n.leaf) n.sig = scored ? 'score' : signalOf(n.v, lv); });
    const fi = this.featInfo(tr), vals = s.vals, w = this.walk(tr.root, vals);

    const sm = s.vw < 640, H = 34, PAD = sm ? 10 : 14, GAP = sm ? 34 : 40;
    const isBoolN = n => isBoolF(n.f) && n.t > 0 && n.t < 1;
    const kidsOf = n => isBoolN(n) ? [n.gt, n.le] : [n.le, n.gt];
    const yesKid = n => isBoolN(n) ? n.gt : n.le;
    const all = []; let row = 0;
    const place = n => { all.push(n); if (n.le) { const [a, b] = kidsOf(n); place(a); place(b); n.u = (a.u + b.u) / 2; n.first = a.first; n.cnt = a.cnt + b.cnt; } else { n.u = row++; n.first = n.u; n.cnt = 1; } };
    place(tr.root);
    const maxD = Math.max(...all.map(n => n.depth));
    const decs = all.filter(n => n.le), mName = this.textW(decs.map(n => fdesc(n.f)[0]), '700 12px Ubuntu, system-ui, sans-serif'), mQ = this.textW(decs.map(n => isBoolN(n) ? L.qBool : rpl(L.qNum, { t: fmt(n.t) })), '400 11px Ubuntu, system-ui, sans-serif');
    const W = Math.max(sm ? 120 : 132, Math.min(sm ? 172 : 200, Math.ceil(Math.max(mName, mQ, 90)) + 22));
    const pos = {}; let cw, ch, heads = [];
    if (dir === 'vertical') {
      const cp = W + 14, rp = H + 56;
      all.forEach(n => { pos[n.id] = { x: PAD + n.u * cp, y: PAD + n.depth * rp }; });
      cw = PAD * 2 + (row - 1) * cp + W; ch = PAD * 2 + maxD * rp + H;
    } else {
      const cp = W + GAP, rp = H + 6, TOP = 28;
      all.forEach(n => { pos[n.id] = { x: PAD + n.depth * cp, y: PAD + TOP + n.u * rp }; });
      cw = PAD * 2 + maxD * cp + W; ch = PAD * 2 + TOP + (row - 1) * rp + H;
    }
    heads = Array.from({ length: maxD + 1 }, (_, d) => ({ x: (PAD + d * (W + GAP)) + 'px', text: d === maxD ? L.result : rpl(L.check, { n: d + 1 }) }));
    if (dir === 'vertical') heads = heads.map(x => ({ ...x, x: '-9999px' }));
    const edges = [], labels = [];
    all.forEach(n => {
      if (!n.le) return;
      [n.le, n.gt].forEach(c => {
        const a = pos[n.id], b = pos[c.id], on = w.ids.has(n.id) && w.ids.has(c.id), yes = c === yesKid(n);
        let path, lx, ly;
        if (dir === 'vertical') {
          const x1 = a.x + W / 2, y1 = a.y + H, x2 = b.x + W / 2, y2 = b.y, ym = y1 + (y2 - y1) * 0.45;
          path = curved ? `M${x1} ${y1} C${x1} ${ym} ${x2} ${ym} ${x2} ${y2}` : `M${x1} ${y1} V${ym} H${x2} V${y2}`;
          lx = x2 - 14; ly = y2 - 26;
        } else {
          const x1 = a.x + W, y1 = a.y + H / 2, x2 = b.x, y2 = b.y + H / 2, xm = x1 + (x2 - x1) * 0.3;
          path = curved ? `M${x1} ${y1} C${x1 + GAP * 0.6} ${y1} ${x2 - GAP * 0.8} ${y2} ${x2} ${y2}` : `M${x1} ${y1} H${xm} V${y2} H${x2}`;
          lx = x2 - 3; ly = y2 - 9;
        }
        edges.push({ d: path, stroke: on ? '#0950e3' : '#d5dde7', sw: on ? 3 : 2, on });
        labels.push({ go: () => { if (Date.now() - (this._suppress || 0) < 250) return; this.jump(c.id); }, text: yes ? L.yes : L.no, left: lx + 'px', top: ly + 'px', tf: dir === 'vertical' ? 'none' : 'translateX(-100%)', bg: on ? '#0950e3' : (yes ? '#eef6f1' : '#f6eeee'), color: on ? '#ffffff' : (yes ? '#3c7a55' : '#9a4b44') });
      });
    });
    edges.sort((a, b) => a.on - b.on);

    const ICO = { buy: 'fa-solid fa-arrow-trend-up', sell: 'fa-solid fa-arrow-trend-down', none: 'fa-solid fa-pause', score: 'fa-solid fa-gauge-simple' };
    const nodes = all.map(n => {
      const p = pos[n.id], on = w.ids.has(n.id), end = on && !n.le;
      const o = { op: on ? 1 : 0.78, x: p.x + 'px', y: p.y + 'px', isDec: !!n.le, isLeaf: !!n.leaf, isLock: !!n.locked, name: '', q: '', verb: '', value: '', str: '0%', c: '#16263a', nameC: '#16263a' };
      if (n.le) return { ...o, nameC: on ? '#0950e3' : '#16263a', name: fdesc(n.f)[0], q: isBoolN(n) ? L.qBool : rpl(L.qNum, { t: fmt(n.t) }), title: `if( ${n.f} <= ${n.raw} )`, ic: 'fa-solid fa-chart-line', icBg: on ? '#0950e3' : '#eef3fa', icC: on ? '#ffffff' : '#5a6b80', bg: on ? '#f5f8ff' : '#ffffff', bd: on ? '1.5px solid #0950e3' : '1px solid #e2e9f0', shadow: on ? '0 6px 18px rgba(9,80,227,.14)' : 'none', onEnter: e => this.showTip(e, { kind: 'node', id: n.id }), onLeave: () => this.hideTip(), onClick: e => this.clickNode(e, n.id, 'node') };
      if (n.leaf) {
        const S = SIG[n.sig];
        return { ...o, verb: S[0], value: fmtV(n.v), str: Math.round(Math.min(1, Math.abs(n.v)) * 100) + '%', c: S[1], ic: ICO[n.sig], icBg: S[1], icC: '#ffffff', title: `ret := ${n.v.toFixed(6)}${n.mark ? ' // ' + n.mark : ''}`, bg: S[2], bd: end ? `2px solid ${S[1]}` : `1px solid ${S[3]}`, shadow: end ? `0 0 0 3px ${S[4]}, 0 6px 16px rgba(22,38,58,.12)` : 'none', onClick: e => this.clickNode(e, n.id, 'leaf'), onEnter: e => this.showTip(e, { kind: 'leaf', id: n.id }), onLeave: () => this.hideTip() };
      }
      return { ...o, ic: 'fa-solid fa-lock', icBg: '#e2e9f0', icC: '#5a6b80', title: L.paid, bg: '#f7f9fc', bd: end ? '2px dashed #5a6b80' : '1px dashed #b8c4d3', shadow: 'none', onEnter: e => this.showTip(e, { kind: 'lock' }), onLeave: () => this.hideTip(), onClick: e => this.clickNode(e, n.id, 'lock') };
    });
    const lp = pos[w.leaf.id];
    this._leafPos = { id: w.leaf.id, x: lp.x, y: lp.y, w: W, h: H, dir };
    const fk = [s.sel, w.leaf.id, dir, s.view, trees === s.full].join(':');
    if (fk !== this._fk) { this._fk = fk; setTimeout(() => this.follow(), 40); }

    const ZC = { buy: '#15803d', sell: '#c0392b', none: '#9aa7b8', lock: '#cfd8e3' };
    // las zonas dicen qué haría la estrategia: sin niveles no se sabe, y no se pintan
    const zonesOf = (F, at, fr) => {
      if (F.isBool || scored) return [];
      const bnd = [F.min, ...F.ts, F.max], segs = [], cur = vals[F.f];
      for (let i = 0; i < bnd.length - 1; i++) { const a = bnd[i], b = bnd[i + 1]; if (!(b > a)) continue; const lf = this.walk(tr.root, { ...vals, [F.f]: (a + b) / 2 }).leaf; const last = segs[segs.length - 1]; if (last && last.id === lf.id) last.b = b; else segs.push({ a, b, id: lf.id, lf }); }
      return segs.map((z, i) => { const sg = z.lf.leaf ? z.lf.sig : 'lock', on = (cur > z.a || i === 0) && cur <= z.b; return { l: at(z.a), w: 'calc((100% - 16px) * ' + (fr(z.b) - fr(z.a)).toFixed(4) + ')', c: ZC[sg], op: z.lf.leaf ? (0.35 + 0.65 * Math.min(1, Math.abs(z.lf.v))).toFixed(2) : '1', ring: on ? '0 0 0 2px #16263a' : 'none' }; });
    };
    const feats = fi.map(F => {
      const v = vals[F.f], used = w.used.filter(c => c.f === F.f);
      let lo = F.min, hi = F.max;
      used.forEach(c => { if (c.dir === 'le') hi = Math.min(hi, c.t); else lo = Math.max(lo, c.t); });
      const fr = x => Math.max(0, Math.min(1, (x - F.min) / (F.max - F.min)));
      const at = x => `calc(8px + (100% - 16px) * ${fr(x).toFixed(4)})`;
      const set = x => () => this.setState(st => ({ vals: { ...st.vals, [F.f]: x } }));
      const yes = v > 0.5;
      return {
        name: nice(F.f), full: F.f, infoLabel: rpl(L.whatIs, { f: F.f }), isBool: F.isBool, isNum: !F.isBool, label: fdesc(F.f)[0],
        onInfo: e => this.showTip(e, { kind: 'feat', f: F.f }, true), onEnter: e => this.showTip(e, { kind: 'feat', f: F.f }), onLeave: () => this.hideTip(),
        nameColor: used.length ? '#0950e3' : '#16263a',
        valueLabel: F.isBool ? (yes ? L.yes : L.no) : (v == null ? '' : fmt(v)),
        min: F.min, max: F.max, value: v == null ? F.min : v,
        onChange: e => { const x = +e.target.value; this.setState(st => ({ vals: { ...st.vals, [F.f]: x } })); },
        zones: zonesOf(F, at, fr), bandL: at(lo), bandW: `calc((100% - 16px) * ${(fr(hi) - fr(lo)).toFixed(4)})`,
        ticks: F.ts.map(t => { const a = used.some(c => c.t === t); return { left: at(t), bg: a ? '#0950e3' : 'rgba(22,38,58,.45)', h: a ? '14px' : '10px', title: fmt(t), onEnter: e => this.showTip(e, { kind: 'tick', f: F.f, t }), onLeave: () => this.hideTip() }; }),
        setNo: set(0), setYes: set(1),
        noBg: yes ? 'transparent' : '#0950e3', noColor: yes ? '#5a6b80' : '#ffffff',
        yesBg: yes ? '#0950e3' : 'transparent', yesColor: yes ? '#ffffff' : '#5a6b80'
      };
    });
    const unusedList = tr.signature.filter(f => !fi.some(F => F.f === f)).map(nice);
    const boolTxt = (f, d) => `${fdesc(f)[0]}: ${d === 'le' ? L.no : L.yes}`;
    const pathChips = w.used.map(c => ({ text: isBoolF(c.f) && c.t > 0 && c.t < 1 ? boolTxt(c.f, c.dir) : `${fdesc(c.f)[0]} ${c.dir === 'le' ? '≤' : '>'} ${fmt(c.t)}` }));
    const LF = w.leaf, LS = LF.leaf ? SIG[LF.sig] : null;

    const FR = {}; fi.forEach(F => { FR[F.f] = F; });
    const constraints = n => { const by = {}, order = []; this.pathTo(tr.root, n.id).forEach(c => { if (!by[c.f]) { by[c.f] = { lo: -Infinity, hi: Infinity }; order.push(c.f); } if (c.dir === 'le') by[c.f].hi = Math.min(by[c.f].hi, c.t); else by[c.f].lo = Math.max(by[c.f].lo, c.t); }); return order.map(f => ({ f, ...by[f] })); };
    const barsOf = cs => cs.map(c => { const F = FR[c.f]; if (!F) return null; const fr = x => Math.max(0, Math.min(100, (x - F.min) / (F.max - F.min) * 100)); const a = c.lo > -Infinity ? fr(c.lo) : 0, b = c.hi < Infinity ? fr(c.hi) : 100; const B = F.isBool; return { name: fdesc(c.f)[0], range: B ? (c.hi < Infinity ? L.no : L.yes) : c.lo > -Infinity && c.hi < Infinity ? rpl(L.between, { a: fmt(c.lo), b: fmt(c.hi) }) : c.hi < Infinity ? rpl(L.orLess, { v: fmt(c.hi) }) : rpl(L.moreThan, { v: fmt(c.lo) }), l: (B ? (c.hi < Infinity ? 0 : 50) : a) + '%', w: (B ? 50 : Math.max(2, b - a)) + '%' }; }).filter(Boolean);
    const strW = v => { const a = Math.abs(v); return a >= 0.9 ? L.strVery : a >= 0.7 ? L.strStrong : a >= 0.4 ? L.strMod : L.strWeak; };
    const strLabel = n => n.sig === 'score' ? '' : n.sig === 'none' ? (n.v > 0.2 ? L.leanBuy : n.v < -0.2 ? L.leanSell : L.neutral) : rpl(L.sigStr || '{s}', { s: strW(n.v) });
    const phraseOf = n => { const cs = constraints(n), k = { buy: 'leadBuy', sell: 'leadSell', none: 'leadNone', score: 'leadScore' }[n.sig]; return { text: rpl(L[k + (cs.length === 1 ? '1' : 'N')] || '', { n: cs.length }), str: strLabel(n), bars: barsOf(cs) }; };
    const leavesAll = all.filter(n => n.leaf);
    // sin niveles, un solo grupo: de la puntuación más alta a la más baja
    const groups = (scored ? ['score'] : ['buy', 'sell', 'none']).map(sig => {
      const S = SIG[sig], list = leavesAll.filter(n => n.sig === sig).sort((a, b) => (scored ? b.v - a.v : Math.abs(b.v) - Math.abs(a.v)));
      return { verb: scored ? L.results : S[0], c: S[1], ic: ICO[sig], has: list.length > 0, count: rpl(list.length === 1 ? L.rulesOne : L.rulesN, { n: list.length }),
        rules: list.map(n => { const ph = phraseOf(n), now = w.leaf.id === n.id; return { text: ph.text, bars: ph.bars, str: ph.str, val: fmtV(n.v), c: S[1], deg: Math.round(Math.min(1, Math.abs(n.v)) * 360) + 'deg', now, bd: now ? '2px solid #0950e3' : '1px solid #e2e9f0', sh: now ? '0 8px 22px rgba(9,80,227,.12)' : 'none', jump: () => this.jump(n.id) }; }) };
    }).filter(g => g.has);
    const BW = Math.max(sm ? 112 : 120, Math.min(sm ? 160 : 190, Math.ceil(mName) + 42, Math.floor((s.aw || 922) / (maxD + 1)))), BU = 42;
    const blocks = all.map(n => {
      const on = w.ids.has(n.id), pr = all.find(x => x.le === n || x.gt === n);
      const inc = !pr ? L.start : isBoolN(pr) ? `${fdesc(pr.f)[0]}: ${pr.gt === n ? L.yes : L.no}` : `${fdesc(pr.f)[0]} ${pr.le === n ? '≤' : '>'} ${fmt(pr.t)}`;
      const base = { x: n.depth * BW + 'px', y: n.first * BU + 'px', w: (n.le ? 1 : (maxD + 1 - n.depth)) * BW + 'px', h: n.cnt * BU + 'px', inc, op: on ? 1 : 0.8, ws: n.cnt > 1 ? 'normal' : 'nowrap', lc: n.cnt > 1 ? 2 : 1 };
      if (n.le) return { ...base, main: fdesc(n.f)[0], val: '', ic: 'fa-solid fa-chart-line', c: on ? '#0950e3' : '#16263a', subC: on ? '#0950e3' : '#8d9cae', bg: on ? '#e9f0fd' : '#f7f9fc', bd: on ? '1.5px solid #0950e3' : '1px solid #e2e9f0', onClick: e => this.clickNode(e, n.id, 'node'), onEnter: e => this.showTip(e, { kind: 'node', id: n.id }), onLeave: () => this.hideTip() };
      if (n.leaf) { const S = SIG[n.sig]; return { ...base, main: S[0], val: fmtV(n.v), ic: ICO[n.sig], c: S[1], subC: '#5a6b80', bg: S[2], bd: on ? '2px solid #0950e3' : '1px solid ' + S[3], onClick: e => this.clickNode(e, n.id, 'leaf'), onEnter: e => this.showTip(e, { kind: 'leaf', id: n.id }), onLeave: () => this.hideTip() }; }
      return { ...base, main: L.paid, val: '', ic: 'fa-solid fa-lock', c: '#5a6b80', subC: '#8d9cae', bg: '#f7f9fc', bd: '1px dashed #b8c4d3', onClick: e => this.clickNode(e, n.id, 'lock'), onEnter: e => this.showTip(e, { kind: 'lock' }), onLeave: () => this.hideTip() };
    });
    const bw = (maxD + 1) * BW, bh = row * BU;

    const TP = s.tip;
    const thrOf = f => ((fi.find(F => F.f === f) || { ts: [] }).ts).map(fmt).join(' · ');
    const curOf = f => { const F = fi.find(x => x.f === f), v = vals[f]; return v == null ? '–' : (F && F.isBool ? (v > 0.5 ? L.yes : L.no) : fmt(v)); };
    const upW = dir === 'vertical' ? L.lB : L.upB, dnW = dir === 'vertical' ? L.rB : L.dnB;
    // El recuadro del propietario: el script completo cuando llega (mientras, que se carga; si no llega,
    // dónde bajarlo, nunca que compre lo que es suyo); sin una compra que este navegador demuestre, cómo
    // entrar o comprarla (o pedirla, si es gratis).
    const ownerHas = !!P.owned && !s.fullFail, ownerFail = !!P.owned && s.fullFail;
    const ownerText = ownerFail ? L.ownFail : !ownerHas ? (P.signedIn ? L.ownNotYours : L.ownSignIn) : s.full ? L.ownFull : L.loading;
    const download = () => window.location.assign(P.ownerDownload || '/mine');
    let tip = null;
    if (TP) {
      const nd = TP.id != null ? all.find(n => n.id === TP.id) : null;
      if (TP.kind === 'feat') { const d = fdesc(TP.f); tip = { title: d[0], code: TP.f, text: d[1], lang: d[2], rows: [[L.curVal, curOf(TP.f)], [L.checksAt, thrOf(TP.f)]] }; }
      else if (TP.kind === 'tick') { const d = fdesc(TP.f); tip = { title: rpl(L.tickTitle, { f: nice(TP.f), t: fmt(TP.t) }), code: 'if( ' + TP.f + ' <= ' + TP.t + ' )', text: rpl(L.tickText, { name: d[0], t: fmt(TP.t) }), rows: [[L.curVal, curOf(TP.f)], [L.onPath, w.used.some(c => c.f === TP.f && c.t === TP.t) ? L.yes : L.no]] }; }
      else if (TP.kind === 'node' && nd) {
        const d = fdesc(nd.f), isB = isBoolF(nd.f) && nd.t > 0 && nd.t < 1, go = (vals[nd.f] <= nd.t) !== isB ? upW : dnW;
        tip = { title: d[0], code: 'if( ' + nd.f + ' <= ' + nd.raw + ' )', text: d[1], lang: d[2], rows: isB ? [[L.yes, upW], [L.no, dnW], [L.now, curOf(nd.f) + ' → ' + go]] : [[L.yes + ' (≤ ' + fmt(nd.t) + ')', upW], [L.no + ' (> ' + fmt(nd.t) + ')', dnW], [L.now, curOf(nd.f) + ' → ' + go]] };
      }
      else if (TP.kind === 'leaf' && nd) { const S = SIG[nd.sig], ph = phraseOf(nd); tip = { title: scored ? S[0] + ' ' + fmtV(nd.v) : S[0] + ' · ' + ph.str + ' (' + fmtV(nd.v) + ')', code: '', text: ph.text, bars: ph.bars, rows: [], foot: L.leafFoot }; }
      else if (TP.kind === 'lock') tip = s.owner && P.owned ? { title: L.paid, code: '', text: ownerText, rows: [], cta: L.download, act: download } : { title: L.paid, code: '', text: L.lockText, rows: [], cta: unlockLabel };
    }
    const unlock = () => {
      // la de la cuenta, a su vista de propietario, con el foco en su botón (el pulsado desaparece), sin llevar la
      // página hasta él: desde el candado de una rama, más abajo, se sigue viendo el árbol
      if (P.owned) {
        this.setOwner(true);
        this.setState({ tip: null }, () => { const b = this.base && this.base.querySelector('[data-tree-owner]'); if (b) b.focus({ preventScroll: true }); });
        return;
      }
      // una gratis abre su diálogo cada vez; una de pago va al carrito mientras no está en él
      this.setState({ tip: null });
      if (P.onBuy && (free || !P.inCart)) P.onBuy({ stopPropagation() {}, preventDefault() {} });
      else if (!P.embedded) window.location.href = '/s/' + encodeURIComponent(rowId(P));
    };
    const tipOut = tip ? { tipOn: true, tipTitle: tip.title, tipCode: tip.code, tipHasCode: !!tip.code, tipText: tip.text, tipLang: tip.lang || lg, tipDir: (tip.lang || lg) !== lg ? 'ltr' : null, tipRows: tip.rows.map(r => ({ k: r[0], v: r[1] })), tipBars: tip.bars || [], tipHasBars: !!(tip.bars && tip.bars.length), tipFoot: tip.foot || '', tipHasFoot: !!tip.foot, tipPinned: !!TP.pin, tipHasCta: !!tip.cta, tipCtaLabel: tip.cta || '', tipCta: tip.act || unlock, tipX: TP.x + 'px', tipY: TP.y + 'px', tipTf: TP.up ? 'translateY(-100%)' : 'none' } : { tipOn: false, tipRows: [], tipBars: [] };

    const params = tr.params.split(',').map(x => x.trim()).filter(x => x && !/^random_state/.test(x)).join(' · ');
    const created = tr.created ? new Intl.DateTimeFormat(L.locale, { dateStyle: 'medium' }).format(new Date(tr.created + 'T12:00:00')) : '';

    return {
      ...base, picks, forestPicks, hasForest: forestPicks.length > 0, treeBadge: L.tree1,
      feats, nodes, edges, labels, pathChips, groups, blocks, bwPx: bw + 'px', bhPx: bh + 'px', nW: W + 'px', nH: H + 'px', bW: BW + 'px',
      allRulesOpen: s.allRules, toggleAllRules: () => this.setState(st => ({ allRules: !st.allRules })), allRulesLabel: s.allRules ? L.hideRules : rpl(L.allRules, { n: leavesAll.length }),
      hasLockedNote: tr.locked > 0, lockedNote: rpl(L.lockedRules, { n: tr.locked }),
      cw, ch, cwPx: cw + 'px', chPx: ch + 'px', heads, ...tipOut, unlock,
      title: `${tr.ticker} · ${tr.pattern}`,
      summary: (tr.locked ? rpl(L.visible, { n: tr.leaves }) + ' · ' + rpl(tr.locked === 1 ? L.paid1 : L.paidN, { n: tr.locked }) : rpl(L.complete, { n: tr.leaves })) + (created ? ' · ' + rpl(L.created, { d: created }) : ''),
      params: `${tr.ticker}_${tr.interval}_${tr.key}_${tr.hash} · ${params}`,
      // qué es cada patrón: en y es, de features.json; los otros idiomas, de `pat` en ui.json; uno sin
      // traducir todavía, en inglés y dicho (lang), para un lector de pantalla, y de izquierda a derecha
      // (dir): en árabe, su punto final saltaba al principio
      abouts: tr.bases.map(b => { const x = FX.patterns[b] || [], t = lg === 'en' ? x[0] : es ? x[1] : (L.pat || {})[b]; return t ? { text: t, lang: lg, dir: null } : x[0] ? { text: x[0], lang: 'en', dir: 'ltr' } : null; }).filter(Boolean),
      sigLabel: LS ? LS[0] : L.paid, sigValue: LS ? fmtV(LF.v) : '', sigColor: LS ? LS[1] : '#8d9cae',
      hasMarker: !!LS, markerLeft: LS ? ((LF.v + 1) / 2 * 100).toFixed(2) + '%' : '0%',
      hasUnused: unusedList.length > 0, unused: unusedList.join(', '),
      isOwner: s.owner, ownerHas, ownerFail, showCta: !s.owner && tr.locked > 0,
      ctaText: rpl(tr.locked === 1 ? L.cta1 : L.ctaN, { n: tr.locked }) + L.ctaRest,
      ownerText, askSignIn: !P.signedIn, download
    };
  }
}
