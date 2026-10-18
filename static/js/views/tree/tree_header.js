// Markup and styles ported one to one from docs/design/Strategy Tree.dc.html (the v7 reference design).
import { html } from '../../lib/html.js';


export default function TreeHeader(v) {
  return html`
  ${v.standalone ? html`<header style="position:relative;background:#fff;border-bottom:1px solid #e2e9f0">
      <div style="max-width:1320px;margin:0 auto;padding:12px 28px;display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <span style="font-weight:700;font-size:21px;letter-spacing:-.5px">Edge<span style="color:#0950e3">folio</span></span>
        <span style="width:1px;height:20px;background:#e2e9f0"></span>
        <span style="font-weight:500;font-size:13px;color:#5a6b80">${v.L?.pageName}</span>
        <span style="margin-inline-start:auto;display:flex;gap:16px;font-size:12.5px;font-weight:600"><a href="/">${v.L?.store}</a></span>
        </div>
      <div style="position:absolute;inset-inline:0;bottom:-1px;height:3px;background:linear-gradient(90deg,#47f9e5,#0950e3)"></div>
      </header>` : null}
`;
}
