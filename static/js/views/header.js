// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
// Lo de la tienda en la barra del núcleo: la barra, la palabra Edgefolio, el idioma, la cuenta y la raya
// de colores son de la carcasa; aquí, los chips del diseño en sus dos huecos (topbar_start, topbar_end).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export function BarStart(v) {
  return html`
        <div role="radiogroup" aria-label=${v.tx?.view} style="display:flex;background:#e9eef4;border-radius:12px;padding:3px;gap:2px">
          ${(v.modeTabs || []).map((md, $index) => html`<button role="radio" aria-checked=${md?.on} onClick=${md?.go} style="font-family:inherit;border:none;border-radius:10px;padding:8px 18px;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:8px;white-space:nowrap;background:${s(md?.bg)};color:${s(md?.color)};box-shadow:${s(md?.shadow)}"><i class=${md?.icon}></i>${T(md?.label)}</button>`)}
          </div>
        <button class="sf-hover0" onClick=${v.goMine} style="font-family:inherit;border-radius:999px;padding:5px 11px;font-size:11px;font-weight:600;background:#fff;border:1px solid #e2e9f0;display:inline-flex;align-items:center;gap:7px;cursor:pointer;color:#16263a;white-space:nowrap"><i class="fa-regular fa-folder-open" style="color:#0950e3"></i>${T(v.tx?.myStrategies)}</button>
`;
}

export function BarEnd(v) {
  return html`
        <button class="sf-hover0" onClick=${v.openTour} title=${v.tx?.tourOpen} style="font-family:inherit;border-radius:999px;padding:5px 11px;font-size:11px;font-weight:600;background:#fff;border:1px solid #e2e9f0;display:inline-flex;align-items:center;gap:6px;cursor:pointer;color:#0950e3;white-space:nowrap"><span style="width:15px;height:15px;border-radius:50%;display:grid;place-items:center;background:#0950e3;color:#fff;font-size:10px;font-weight:700;line-height:1">?</span>${T(v.tx?.tourOpen)}</button>
        <button class="sf-hover0" onClick=${v.toggleTv} title=${v.tvTitle} style="font-family:inherit;border-radius:999px;padding:5px 11px;font-size:11px;font-weight:600;background:#fff;border:1px solid #e2e9f0;display:inline-flex;align-items:center;gap:7px;cursor:pointer;color:#16263a;white-space:nowrap">
          <img src="/static/assets/icons/TW_ICO.svg" alt="TradingView" style="width:15px;height:15px;display:block" />
          ${v.tv ? html`<span translate=${false}>TradingView</span><span style="width:7px;height:7px;border-radius:50%;background:#12b76a"></span><span style="color:#5a6b80;font-weight:500">${v.tx?.tvConnected}</span>` : null}
          ${v.tvOff ? html`<span style="color:#0950e3">${v.tx?.tvConnect}</span>` : null}
          </button>
        <button onClick=${v.toggleCur} title=${v.tx?.currencyLabel} style="font-family:inherit;border-radius:999px;padding:5px 11px;font-size:11px;font-weight:700;background:#fff;border:1px solid #e2e9f0;cursor:pointer;color:#16263a">${v.curLabel}</button>
`;
}

// La capa que cierra los menús de la tienda (los de los filtros) al pulsar fuera.
export default function MenuScrim(v) {
  return html`${v.anyMenu ? html`<div onClick=${v.closeMenus} style="position:fixed;inset:0;z-index:15"></div>` : null}`;
}
