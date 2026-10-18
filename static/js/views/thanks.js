// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Thanks(v) {
  return html`
  ${v.isThanks ? html`
    <section style="flex:1 0 auto;width:100%;max-width:1000px;margin:0 auto;padding:32px 28px 0;display:flex;flex-direction:column;gap:18px">
      <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:24px 26px;display:flex;gap:18px;align-items:center;flex-wrap:wrap">
        <span style="width:52px;height:52px;border-radius:50%;background:#e8f7ef;color:#15803d;display:grid;place-items:center;font-size:22px;flex-shrink:0"><i class="fa-solid fa-check"></i></span>
        <div style="flex:1 1 320px"><h1 style="margin:0;font-size:24px;font-weight:700;letter-spacing:-.3px">${v.tx?.thanksTitle}</h1><p style="margin:2px 0 0;color:#5a6b80">${v.tx?.thanksSub}</p></div>
        <div style="text-align:end;line-height:1.3;margin-inline-start:auto"><div style="font-size:12px;color:#5a6b80">${v.tx?.totalPaid}</div><div style="font-size:26px;font-weight:700;letter-spacing:-.4px">${v.orderTotal}</div><div style="font-size:12px;color:#5a6b80;display:flex;flex-wrap:wrap;gap:2px 6px;align-items:center;justify-content:flex-end"><span style="display:inline-flex;gap:6px;align-items:center;white-space:nowrap"><img src="/static/assets/icons/a_logo_paypal.png" alt="PayPal" style="height:14px" />${T(v.tx?.paidWith)} ·</span><span style="white-space:nowrap">${v.orderLabel}</span></div></div>
        </div>
      ${v.linksHidden ? html`
        <div role="note" style="display:flex;gap:12px;align-items:flex-start;border-radius:12px;padding:12px 14px;background:#eef3fd;border:1px solid #d6e2fb;flex-wrap:wrap">
          <i class="fa-regular fa-folder-open" style="color:#0950e3;font-size:16px;margin-top:2px"></i>
          <div style="flex:1 1 240px;display:flex;flex-direction:column;gap:2px;font-size:13px"><strong style="font-size:13.5px">${v.tx?.linksHiddenTitle}</strong><span style="text-wrap:pretty">${v.tx?.linksHiddenText}</span></div>
          <button onClick=${v.goMine} style="align-self:center;margin-inline-start:auto;font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:9px 16px;font-size:13.5px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;box-shadow:0 8px 20px rgba(9,80,227,.22)"><i class="fa-solid fa-right-to-bracket"></i>${T(v.tx?.signInToDownload)}</button>
          </div>
        ` : null}
      ${v.linksShown ? html`<div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;overflow:hidden">
        <div style="padding:14px 18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;border-bottom:1px solid #e2e9f0"><span style="font-size:13px;color:#5a6b80;flex:1 1 300px">${v.linksNote}</span><a href=${v.downloadAllUrl} style="font-family:inherit;line-height:normal;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:10px 18px;font-size:14px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;text-decoration:none"><i class="fa-solid fa-download"></i>${T(v.tx?.downloadAll)}</a></div>${' '}
        ${(v.orderRows || []).map((o, $index) => html`
          <div style="display:flex;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid #e2e9f0;flex-wrap:wrap">
            <span role="img" aria-hidden="true" style="width:32px;height:32px;border-radius:8px;display:inline-block;flex-shrink:0;background-image:url('${s(o?.icon)}');background-size:cover;background-position:center"></span>
            <div style="flex:1 1 240px;min-width:0;line-height:1.3"><div style="font-weight:700">${T(o?.name)} · ${T(o?.ticker)}</div><div dir="auto" style="font-size:12px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${T(o?.key)} · ${T(o?.ind)} · ${T(o?.interval)}</div></div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
              <a href=${o?.pineUrl} style="font-family:inherit;line-height:normal;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center;text-decoration:none"><i class="fa-solid fa-file-code" style="color:#0950e3"></i><span dir="ltr">.pine</span></a>
              <a href=${o?.zipUrl} title=${v.tyZip} style="font-family:inherit;line-height:normal;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center;text-decoration:none"><i class="fa-solid fa-file-zipper" style="color:#0950e3"></i><span dir="ltr">.zip</span></a>
              <a class="sf-hover8" href=${o?.tabHref} target="_blank" rel="noopener" title=${v.tyNewTab} style="border-radius:999px;padding:6px 11px;font-size:12px;font-weight:700;display:inline-flex;gap:5px;align-items:center;white-space:nowrap;text-decoration:none;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}<i class="fa-solid fa-arrow-up-right-from-square" style="font-size:9px"></i></a>
              <a class="sf-hover9" href=${o?.treeHref} target="_blank" rel="noopener" title=${v.tyNewTab} style="border-radius:999px;padding:6px 11px;font-size:12px;font-weight:700;display:inline-flex;gap:5px;align-items:center;white-space:nowrap;text-decoration:none;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}<i class="fa-solid fa-arrow-up-right-from-square" style="font-size:9px"></i></a>
              </div>
            </div>
          `)}${' '}
        </div>` : null}
      <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:20px 22px;display:flex;flex-direction:column;gap:14px">
        <div style="display:flex;align-items:center;gap:10px 16px;flex-wrap:wrap">
          <h2 style="margin:0;font-size:17px;font-weight:700;display:flex;align-items:center;gap:8px"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:18px;height:18px" />${T(v.tx?.installTitle)}</h2>
          <button onClick=${v.openInst0} style="margin-inline-start:auto;font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:9px 16px;font-size:13.5px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;box-shadow:0 8px 20px rgba(9,80,227,.22)"><i class="fa-solid fa-circle-play"></i>${T(v.instWatch)}</button>
          </div>
        <ol style="margin:0;padding:0;list-style:none;display:grid;grid-template-columns:${s(v.instCols)};gap:10px">
          ${(v.instCards || []).map((st, $index) => html`<li style="display:flex"><button class="sf-hover10" onClick=${st?.go} style="font-family:inherit;flex:1;display:flex;flex-direction:${s(v.instTileDir)};gap:10px;align-items:flex-start;text-align:start;background:#f4f8fb;border:1px solid transparent;border-radius:12px;padding:12px;font-size:13.5px;color:#16263a;cursor:pointer"><span style="width:24px;height:24px;border-radius:50%;background:#0950e3;color:#fff;display:grid;place-items:center;font-size:12px;font-weight:700;flex-shrink:0">${st?.n}</span><span style="text-wrap:pretty;font-weight:600;line-height:1.35">${st?.title}</span></button></li>`)}
          </ol>
        </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap"><button onClick=${v.goMine} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 22px;font-size:14.5px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22)">${v.tx?.goMine}</button><button onClick=${v.goShop} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:11px 20px;font-size:14px;cursor:pointer">${v.tx?.backShop}</button></div>
      ${v.contactOn ? html`<p style="margin:0;font-size:12.5px;color:#5a6b80">${v.tx?.contactProblems}</p>` : null}
      </section>
    ` : null}
`;
}
