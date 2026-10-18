// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
// La barra fija lleva data-zt-bottom (núcleo 0.28): la carcasa mide lo que tapa (--zt-bottom-h) y deja
// ese sitio debajo del pie; el aviso de cookies y los avisos del núcleo salen encima.
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function PhoneBar(v) {
  return html`
  ${v.isPhone ? html`
    <nav data-zt-bottom style="position:fixed;inset-inline:0;bottom:0;z-index:40;background:#fff;border-top:1px solid #e2e9f0;display:grid;grid-template-columns:repeat(4,1fr);padding:6px 0 10px;box-shadow:0 -8px 24px rgba(22,38,58,.08)">
      ${(v.navItems || []).map((nv, $index) => html`<button onClick=${nv?.go} style="font-family:inherit;border:none;background:none;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:2px;font-size:10.5px;font-weight:600;color:${s(nv?.color)};position:relative;min-height:44px;justify-content:center"><i class=${nv?.icon} style="font-size:17px"></i>${T(nv?.label)}${nv?.hasBadge ? html`<span style="position:absolute;top:2px;inset-inline-start:calc(50% + 6px);background:#0950e3;color:#fff;border-radius:999px;font-size:9.5px;padding:0 5px;line-height:15px">${nv?.badge}</span>` : null}</button>`)}
      </nav>
    ` : null}
`;
}
