// Numbers, money and dates in the reader's language (Intl), and the texts of the two dictionaries.
// Arabic keeps Latin digits (ar-u-nu-latn), as the design does.
export const LOCALES = { es: 'es-ES', en: 'en-US', pt: 'pt-PT', fr: 'fr-FR', de: 'de-DE', zh: 'zh-CN', ar: 'ar-u-nu-latn', hi: 'hi-IN' };
// The currency each language reads prices in; PayPal always charges USD.
export const LOCAL_CURRENCY = { es: 'EUR', pt: 'EUR', fr: 'EUR', de: 'EUR', hi: 'INR', zh: 'CNY', ar: 'SAR', en: 'USD' };

const DASH = '—';
const bad = n => n == null || (typeof n === 'number' && isNaN(n));

// t(key, vars, count) as the design: tool dictionary first, then the core's. An entry with plural
// forms ({one, other}; Arabic also zero, two, few, many) takes the form the language's rules give for
// count (Intl.PluralRules), else .other: "1 strategy", "2 strategies".
export function translator(dict, common, lang) {
  const plural = new Intl.PluralRules(LOCALES[lang] || 'en-US');
  return (key, vars, count) => {
    const e = dict[key] || common[key];
    let v = e ? (e[lang] ?? e.es ?? e.en ?? '') : '';
    if (v && typeof v === 'object') v = (count != null && v[plural.select(count)]) || v.other || '';
    if (vars) Object.keys(vars).forEach(k => { v = v.split('{' + k + '}').join(vars[k]); });
    return v;
  };
}

export function formatters(lang, { local, rate }) {
  const LOC = LOCALES[lang] || 'en-US';
  const nf = opts => new Intl.NumberFormat(LOC, opts);
  const usd = nf({ style: 'currency', currency: 'USD' });
  const usd0 = nf({ style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  const localCur = LOCAL_CURRENCY[lang] || 'USD';
  const isLocal = !!local && localCur !== 'USD' && rate > 0;
  const loc0 = isLocal ? nf({ style: 'currency', currency: localCur, maximumFractionDigits: 0 }) : null;
  const pct = (n, d = 2) => bad(n) ? DASH : nf({ style: 'percent', minimumFractionDigits: d, maximumFractionDigits: d }).format(n / 100);
  const day = iso => new Date(String(iso).slice(0, 10) + 'T12:00:00');
  return {
    LOC, isLocal, curLabel: isLocal ? localCur : 'USD',
    money: n => bad(n) ? DASH : usd.format(n),
    money0: n => bad(n) ? DASH : usd0.format(n),
    // a price as the reader sees it: "≈ 73 €" in the local currency, else USD
    pmoney: n => bad(n) ? DASH : isLocal ? '≈ ' + loc0.format(n * rate) : usd.format(n),
    pct,
    pct0: n => pct(n, 0),
    pctS: n => bad(n) ? DASH : nf({ style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2, signDisplay: 'exceptZero' }).format(n / 100),
    int: n => bad(n) ? DASH : nf().format(n),
    num: (n, d) => bad(n) ? DASH : nf({ maximumFractionDigits: d }).format(n),
    fmtDate: iso => !iso ? DASH : new Intl.DateTimeFormat(LOC, { dateStyle: 'medium' }).format(day(iso)),
    decimal: (nf().formatToParts(1.5).find(p => p.type === 'decimal') || { value: '.' }).value
  };
}

// TradingView's own names and URL codes for the catalogue's time frames.
const TV_LABEL = { '1Min': '1m', '5Min': '5m', '15Min': '15m', '30Min': '30m', '1Hour': '1h', '4Hour': '4h', '1Day': '1D', '1Week': '1W' };
const TV_CODE = { '1Min': '1', '5Min': '5', '15Min': '15', '30Min': '30', '1Hour': '60', '4Hour': '240', '1Day': 'D', '1Week': 'W' };
export const tvInterval = iv => TV_LABEL[iv] || iv;
export const tvChartUrl = (symbol, iv) => 'https://www.tradingview.com/chart/?symbol=' + encodeURIComponent(symbol || '') + '&interval=' + (TV_CODE[iv] || 'D');
export const tvSymbolUrl = symbol => 'https://www.tradingview.com/symbols/' + String(symbol || '').replace(':', '-') + '/';
