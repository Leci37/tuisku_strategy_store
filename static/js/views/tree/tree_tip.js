// Markup and styles ported one to one from docs/design/Strategy Tree.dc.html (the v7 reference design).
import { html } from '../../lib/html.js';
import { s } from '../../lib/tpl.js';

export default function TreeTip(v) {
  return html`
  ${v.tipOn ? html`
    <div role="tooltip" style="position:fixed;left:${s(v.tipX)};top:${s(v.tipY)};transform:${s(v.tipTf)};z-index:80;width:300px;max-width:calc(100vw - 24px);background:#16263a;color:#ffffff;border-radius:14px;padding:14px 16px;box-shadow:0 18px 40px rgba(22,38,58,.32);display:flex;flex-direction:column;gap:8px;font-size:13px;line-height:1.45;font-family:Ubuntu,system-ui,sans-serif">
      <div style="display:flex;align-items:flex-start;gap:8px"><strong style="flex:1;font-size:14.5px;line-height:1.3">${v.tipTitle}</strong>${v.tipPinned ? html`<button onClick=${v.closeTip} aria-label="Close" style="border:none;background:rgba(255,255,255,.14);color:#ffffff;width:24px;height:24px;border-radius:50%;cursor:pointer;font-size:14px;line-height:1;flex-shrink:0">×</button>` : null}</div>
      ${v.tipHasCode ? html`<span style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:11.5px;color:#9fd8ff;overflow-wrap:anywhere">${v.tipCode}</span>` : null}
      <p style="margin:0;color:#e3eaf3;text-wrap:pretty">${v.tipText}</p>
      ${(v.tipRows || []).map((tw, $index) => html`<div style="display:flex;justify-content:space-between;gap:12px;font-size:12.5px;border-top:1px solid rgba(255,255,255,.12);padding-top:6px"><span style="color:#b8c7da">${tw?.k}</span><strong style="text-align:end;font-variant-numeric:tabular-nums">${tw?.v}</strong></div>`)}
      ${v.tipHasBars ? html`<div style="display:flex;flex-direction:column;gap:8px;border-top:1px solid rgba(255,255,255,.12);padding-top:8px">${(v.tipBars || []).map((tb, $index) => html`<div style="display:flex;flex-direction:column;gap:4px"><span style="display:flex;justify-content:space-between;gap:8px;font-size:12px"><strong>${tb?.name}</strong><span style="color:#b8c7da;font-variant-numeric:tabular-nums">${tb?.range}</span></span><span style="position:relative;height:6px;border-radius:3px;background:rgba(255,255,255,.16)"><span style="position:absolute;top:0;bottom:0;left:${s(tb?.l)};width:${s(tb?.w)};border-radius:3px;background:#47f9e5"></span></span></div>`)}</div>` : null}
      ${v.tipHasFoot ? html`<span style="font-size:11.5px;color:#b8c7da">${v.tipFoot}</span>` : null}
      ${v.tipHasCta ? html`<button onClick=${v.tipCta} style="font-family:inherit;border:none;border-radius:10px;padding:9px 14px;font-size:13px;font-weight:700;cursor:pointer;background:#ffffff;color:#0950e3">${v.tipCtaLabel}</button>` : null}
      </div>
    ` : null}
`;
}
