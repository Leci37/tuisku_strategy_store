// The Pro filters (§12 of the design guide): slider tracks, multi-selects and the query they make.
// Handles keep a fraction of the track (0–1) as the design does; the server gets values. The server's
// `ranges` replace these tracks when it sends them, so the two never drift.
// Esas barras salen del catálogo (su mínimo y su máximo, redondeados hacia fuera): las de aquí, las del
// diseño, sólo valen hasta que llegan (retrack). Las cifras de cada etiqueta (f) van con los valores del
// catálogo: la actividad por vela va de 0,002 a 0,238 (dec3); el factor de beneficio y el beneficio medio
// (%), casi siempre por debajo de 5 (dos decimales hasta 10).
export const RANGES = {
  np: { key: 'fNetProfitUsd', min: 200, max: 6500000, log: true, f: 'money0' },
  price: { key: 'fPrice', min: 0, max: 140, f: 'money0' },
  npp: { key: 'fNetProfitPct', min: 0.1, max: 6500, log: true, f: 'pctAuto' },
  trades: { key: 'fClosedTrades', min: 0, max: 2000, f: 'round' },
  win: { key: 'fWinRate', min: 0, max: 100, f: 'pct0' },
  pf: { key: 'fProfitFactor', min: 1, max: 35000, log: true, f: 'decAuto' },
  months: { key: 'fTrainingMonths', min: 0, max: 400, f: 'round' },
  mlu: { key: 'fMaxLossUsd', min: 0, max: 40000, f: 'money0' },
  mlp: { key: 'fMaxLossPct', min: 0, max: 4, f: 'pct2' },
  avg: { key: 'fAvgProfitUsd', min: 1, max: 2100000, log: true, f: 'money0' },
  avgp: { key: 'fAvgProfitPct', min: 0, max: 5000, f: 'pctAuto' },
  bars: { key: 'fAvgBars', min: 0, max: 8000, f: 'round' },
  act: { key: 'fActivity', min: 0, max: 3, f: 'dec3' },
  candles: { key: 'fCandles', min: 0, max: 500000, f: 'round' },
  prec: { key: 'fPrecision', min: 40, max: 100, f: 'pct0' },
  tree: { key: 'fTreeDepth', min: 1, max: 10, f: 'round' }
};
export const TOP_RANGES = ['np', 'price'];
export const MORE_RANGES = ['npp', 'trades', 'win', 'pf', 'months', 'mlu', 'mlp', 'avg', 'avgp', 'bars', 'act', 'candles', 'prec', 'tree'];
export const SELECTS = { sym: 'fSymbol', tf: 'fTimeframe', ind: 'fIndicators', idx: 'fIndex', rel: 'fReleaseDate' };

// The track of a range, with the server's bounds when it sent them.
export function track(k, served) {
  const s = served && served[k];
  return s ? { ...RANGES[k], min: s.min, max: s.max, log: !!s.log } : RANGES[k];
}

export const val = (dd, fr) => dd.log
  ? Math.pow(10, Math.log10(dd.min) + fr * (Math.log10(dd.max) - Math.log10(dd.min)))
  : dd.min + fr * (dd.max - dd.min);

export function fracOf(dd, v) {
  const f = dd.log
    ? (Math.log10(Math.max(v, dd.min)) - Math.log10(dd.min)) / (Math.log10(dd.max) - Math.log10(dd.min))
    : (v - dd.min) / (dd.max - dd.min);
  return Math.min(1, Math.max(0, f));
}

// A handle within this distance of its end means "no limit" on that side (§12 open ends).
export const isOpenLo = a => a <= 0.001;
export const isOpenHi = b => b >= 0.999;
export const isOn = r => !!r && (!isOpenLo(r[0]) || !isOpenHi(r[1]));

// Las asas guardan una fracción de su barra: cuando llega otra barra (la del catálogo, que en la primera
// respuesta sustituye a la del diseño, o la de un catálogo nuevo), cada asa puesta pasa a la fracción de su
// mismo valor, y una abierta sigue abierta. Si no, «hasta 50 $» escrito antes de esa respuesta pasaba a
// pedir «hasta 29 $». Sin cambios, el mismo objeto.
export function retrack(rg, before, after) {
  let moved = false;
  const out = {};
  Object.keys(rg).forEach(k => {
    const r = rg[k], a = RANGES[k] && track(k, before), b = RANGES[k] && track(k, after);
    if (!r || !a || (a.min === b.min && a.max === b.max && !!a.log === !!b.log)) { out[k] = r; return; }
    const to = (fr, open) => (open ? fr : fracOf(b, snap(a, val(a, fr))));
    out[k] = [to(r[0], isOpenLo(r[0])), to(r[1], isOpenHi(r[1]))];
    moved = true;
  });
  return moved ? out : rg;
}

// Typed values accept the locale's decimal sign and $ or % around them.
export function parseNum(str, decimal) {
  let x = String(str).replace(/−/g, '-').split('').filter(ch => /[0-9-]/.test(ch) || ch === decimal).join('');
  if (decimal !== '.') x = x.replace(decimal, '.');
  const v = parseFloat(x);
  return isNaN(v) ? null : v;
}

// The decimals each label shows (fmt in vals_shop.js): the server gets the number the visitor reads
// on the chip, the label and the min/max boxes, so "4 – 8" on Tree depth includes depth 8.
const DECIMALS = { money0: () => 0, round: () => 0, pct0: () => 0, pct2: () => 2, dec3: () => 3, pctAuto: v => (v < 10 ? 2 : 0), decAuto: v => (v < 10 ? 2 : 0) };

export function snap(dd, v) {
  const m = Math.pow(10, (DECIMALS[dd.f] || (() => 6))(v));
  return Math.round(v * m) / m;
}

// 12 significant digits drop the float noise of the rounding, so 0.07 is sent as 0.07.
const plain = v => String(Number(v.toPrecision(12)));

// Lo más largo que el servidor acepta en q (search.py): con más, contestaba 400 y salía «Algo de esta
// petición no es válido». Las cajas no dejan escribir más (maxlength="100"), y cada consulta lo corta igual.
export const Q_MAX = 100;

export function proQuery(s, served) {
  const p = new URLSearchParams();
  const q = s.q.trim().slice(0, Q_MAX);
  if (q) p.set('q', q);
  if (s.freeOnly) p.set('free', '1');
  p.set('sort', s.sort);
  Object.keys(SELECTS).forEach(k => {
    const cur = s.sel[k];
    if (!cur) return;
    if (!cur.length) p.append(k, '');
    else cur.forEach(v => p.append(k, v));
  });
  Object.keys(RANGES).forEach(k => {
    const r = s.rg[k];
    if (!isOn(r)) return;
    const dd = track(k, served);
    if (!isOpenLo(r[0])) p.set(k + '_min', plain(snap(dd, val(dd, r[0]))));
    if (!isOpenHi(r[1])) p.set(k + '_max', plain(snap(dd, val(dd, r[1]))));
  });
  return p.toString();
}
