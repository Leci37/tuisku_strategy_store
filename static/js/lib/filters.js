// The Pro filters (§12 of the design guide): slider tracks, multi-selects and the query they make.
// Handles keep a fraction of the track (0–1) as the design does; the server gets values. The server's
// `ranges` replace these tracks when it sends them, so the two never drift.
export const RANGES = {
  np: { key: 'fNetProfitUsd', min: 200, max: 6500000, log: true, f: 'money0' },
  price: { key: 'fPrice', min: 0, max: 140, f: 'money0' },
  npp: { key: 'fNetProfitPct', min: 0.1, max: 6500, log: true, f: 'pctAuto' },
  trades: { key: 'fClosedTrades', min: 0, max: 2000, f: 'round' },
  win: { key: 'fWinRate', min: 0, max: 100, f: 'pct0' },
  pf: { key: 'fProfitFactor', min: 1, max: 35000, log: true, f: 'round' },
  months: { key: 'fTrainingMonths', min: 0, max: 400, f: 'round' },
  mlu: { key: 'fMaxLossUsd', min: 0, max: 40000, f: 'money0' },
  mlp: { key: 'fMaxLossPct', min: 0, max: 4, f: 'pct2' },
  avg: { key: 'fAvgProfitUsd', min: 1, max: 2100000, log: true, f: 'money0' },
  avgp: { key: 'fAvgProfitPct', min: 0, max: 5000, f: 'pct0' },
  bars: { key: 'fAvgBars', min: 0, max: 8000, f: 'round' },
  act: { key: 'fActivity', min: 0, max: 3, f: 'dec1' },
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

// Typed values accept the locale's decimal sign and $ or % around them.
export function parseNum(str, decimal) {
  let x = String(str).replace(/−/g, '-').split('').filter(ch => /[0-9-]/.test(ch) || ch === decimal).join('');
  if (decimal !== '.') x = x.replace(decimal, '.');
  const v = parseFloat(x);
  return isNaN(v) ? null : v;
}

// The decimals each label shows (fmt in vals_shop.js): the server gets the number the visitor reads
// on the chip, the label and the min/max boxes, so "4 – 8" on Tree depth includes depth 8.
const DECIMALS = { money0: () => 0, round: () => 0, pct0: () => 0, pct2: () => 2, dec1: () => 1, pctAuto: v => (v < 10 ? 2 : 0) };

export function snap(dd, v) {
  const m = Math.pow(10, (DECIMALS[dd.f] || (() => 6))(v));
  return Math.round(v * m) / m;
}

// 12 significant digits drop the float noise of the rounding, so 0.07 is sent as 0.07.
const plain = v => String(Number(v.toPrecision(12)));

export function proQuery(s, served) {
  const p = new URLSearchParams();
  const q = s.q.trim();
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
