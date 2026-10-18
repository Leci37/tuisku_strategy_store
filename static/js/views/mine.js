// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Mine(v) {
  return html`
  ${v.isMine ? html`
    <section style="flex:1 0 auto;width:100%;max-width:1000px;margin:0 auto;padding:32px 28px 0;display:flex;flex-direction:column;gap:18px">
      <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap">
        <div><h1 style="margin:0;font-size:26px;font-weight:700;letter-spacing:-.3px">${v.tx?.myStrategies}</h1><p style="margin:2px 0 0;color:#5a6b80">${v.tx?.mineSub}</p></div>
        ${v.signedIn ? html`<span style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#5a6b80;flex-wrap:wrap"><span style="width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#0950e3,#0e7c98);color:#fff;display:grid;place-items:center;font-size:11px;font-weight:700">${v.avatar}</span>${T(v.signedAs)}<button type="button" class="sf-link" onClick=${v.signOut} style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;font-weight:600;font-size:12.5px;cursor:pointer">${v.tx?.signOut}</button></span>` : null}
        </div>
      ${v.proofConfirm ? html`
        <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:20px 22px;display:flex;flex-direction:column;gap:14px;max-width:460px">
          <h2 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-.2px">${v.tx?.proofConfirmTitle}</h2>
          <p style="margin:0;color:#5a6b80;font-size:14px">${v.tx?.proofConfirm}</p>
          <button onClick=${v.confirmProof} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 22px;font-size:14.5px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22);overflow-wrap:anywhere">${T(v.proofAsBefore)}<bdi>${v.proofAsEmail}</bdi>${T(v.proofAsAfter)}</button>
          ${v.legalOn ? html`<a href=${v.legalPrivacyUrl} target="_blank" rel="noopener" style="font-size:12px;color:#5a6b80;cursor:pointer">${v.tx?.legalPrivacy}</a>` : null}
          </div>
        ` : null}
      ${v.proofOffer ? html`
        <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:20px 22px;display:flex;flex-direction:column;gap:14px;max-width:460px">
          <h2 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-.2px">${v.tx?.proofTitle}</h2>
          ${v.proofNotSent ? html`
            ${v.proofExpired ? html`<div role="note" style="display:flex;gap:10px;align-items:flex-start;border-radius:12px;padding:12px 14px;background:#fff7ec;border:1px solid #f6d9ae;font-size:13.5px"><i class="fa-solid fa-triangle-exclamation" style="color:#f79009;margin-top:2px"></i>${T(v.tx?.errProofExpired)}</div>` : null}
            <p style="margin:0;color:#5a6b80;font-size:14px">${v.tx?.proofText}</p>
            <label style="display:flex;flex-direction:column;gap:5px"><span style="font-size:12px;font-weight:600;color:#5a6b80">${v.tx?.email}</span><input type="email" value=${v.proofEmail ?? ''} onInput=${v.onProofEmail} onKeyDown=${v.proofKey} placeholder="ana@example.com" style="font-family:inherit;font-size:14px;color:#16263a;border:1px solid #e2e9f0;border-radius:10px;padding:10px 12px" /></label>
            <button onClick=${v.askProof} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 22px;font-size:14.5px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22)">${v.tx?.sendLink}</button>
            ${v.legalOn ? html`<a href=${v.legalPrivacyUrl} target="_blank" rel="noopener" style="font-size:12px;color:#5a6b80;cursor:pointer">${v.tx?.legalPrivacy}</a>` : null}
            ` : null}
          ${v.proofSent ? html`<div style="display:flex;gap:10px;align-items:flex-start;background:#e8f7ef;color:#15603c;border-radius:12px;padding:12px 14px;font-size:13.5px;font-weight:600"><i class="fa-solid fa-circle-check" style="margin-top:2px"></i>${T(v.tx?.proofSent)}</div>` : null}
          </div>
        ` : null}
      ${v.mineHas ? html`<div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;overflow:hidden">${' '}
        ${(v.mineRows || []).map((m, $index) => html`
          <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;border-bottom:1px solid #e2e9f0;flex-wrap:wrap">
            <span role="img" aria-hidden="true" style="width:36px;height:36px;border-radius:9px;display:inline-block;flex-shrink:0;background-image:url('${s(m?.icon)}');background-size:cover;background-position:center"></span>
            <div style="flex:1 1 240px;min-width:0;line-height:1.3"><div style="font-weight:700">${T(m?.name)} · ${T(m?.ticker)}</div><div dir="auto" style="font-size:12px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${T(m?.key)} · ${T(m?.ind)} · ${T(m?.interval)}</div></div>
            <div style="flex:0 1 220px;font-size:12.5px;color:#5a6b80;line-height:1.35"><div>${m?.when}</div><div>${m?.order}</div></div>
            <span style="font-size:12px;font-weight:700;border-radius:999px;padding:4px 10px;white-space:nowrap;background:${s(m?.stBg)};color:${s(m?.stColor)}">${m?.status}</span>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">${m?.hasUpdate ? html`<button onClick=${m?.getUpdate} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center"><i class="fa-solid fa-arrows-rotate"></i>${T(v.tx?.getUpdate)} · ${T(m?.updateLabel)}</button>` : null}
              ${m?.valid ? html`<a href=${m?.pineUrl} style="font-family:inherit;line-height:normal;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center;text-decoration:none"><i class="fa-solid fa-file-code" style="color:#0950e3"></i><span dir="ltr">.pine</span></a><a href=${m?.zipUrl} title=${v.tyZip} style="font-family:inherit;line-height:normal;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center;text-decoration:none"><i class="fa-solid fa-file-zipper" style="color:#0950e3"></i><span dir="ltr">.zip</span></a>` : null}
              ${m?.expired ? html`<button onClick=${m?.renew} style="font-family:inherit;background:#e9f0fd;border:1px solid #c5d6f8;color:#0950e3;font-weight:700;border-radius:10px;padding:8px 14px;font-size:13px;cursor:pointer;display:inline-flex;gap:7px;align-items:center"><i class="fa-solid fa-rotate"></i>${T(v.tx?.newLink)}</button>` : null}<a class="sf-hover8" href=${m?.tabHref} target="_blank" rel="noopener" title=${v.tyNewTab} style="border-radius:999px;padding:6px 11px;font-size:12px;font-weight:700;display:inline-flex;gap:5px;align-items:center;white-space:nowrap;text-decoration:none;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}<i class="fa-solid fa-arrow-up-right-from-square" style="font-size:9px"></i></a><a class="sf-hover9" href=${m?.treeHref} target="_blank" rel="noopener" title=${v.tyNewTab} style="border-radius:999px;padding:6px 11px;font-size:12px;font-weight:700;display:inline-flex;gap:5px;align-items:center;white-space:nowrap;text-decoration:none;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}<i class="fa-solid fa-arrow-up-right-from-square" style="font-size:9px"></i></a></div>
            </div>
          `)}${' '}
        </div>` : null}
      <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column;gap:10px">
        <span style="font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#5a6b80"><i class="fa-solid fa-heart" style="color:#c0392b"></i> ${T(v.tx?.favourites)}</span>
        ${v.favEmpty ? html`<p style="margin:0;color:#8d9cae;font-size:13px">${v.tx?.favEmpty}</p>` : null}
        ${(v.favRows || []).map((f, $index) => html`
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:8px 0;border-top:1px solid #e2e9f0">
            <span role="img" aria-hidden="true" style="width:28px;height:28px;border-radius:7px;display:inline-block;flex-shrink:0;background-image:url('${s(f?.icon)}');background-size:cover;background-position:center"></span>
            <button onClick=${f?.onOpen} style="font-family:inherit;border:none;background:none;padding:0;cursor:pointer;font-weight:700;font-size:13.5px;color:#16263a;flex:1 1 160px;text-align:start">${T(f?.ticker)} · ${T(f?.key)}</button>
            <span style="display:flex;gap:6px;flex-wrap:wrap">${(f?.alerts || []).map((al, $index) => html`<button onClick=${al?.toggle} style="font-family:inherit;border-radius:999px;padding:5px 11px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid ${s(al?.bd)};background:${s(al?.bg)};color:${s(al?.color)};display:inline-flex;gap:6px;align-items:center"><i class=${al?.icon}></i>${T(al?.label)}</button>`)}</span>
            <button onClick=${f?.onFav} title=${v.tx?.favourites} style="font-family:inherit;width:30px;height:30px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:13px;border:1px solid #e2e9f0;background:#fff;color:#c0392b"><i class="fa-solid fa-heart"></i></button>
            </div>
          `)}
        </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center"><button onClick=${v.openInst0} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:11px 18px;font-size:14px;cursor:pointer;display:inline-flex;gap:8px;align-items:center"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:16px;height:16px" />${T(v.tx?.installTitle)}</button><button onClick=${v.goShop} style="font-family:inherit;background:none;border:none;color:#0950e3;font-weight:600;font-size:14px;cursor:pointer">${v.tx?.backShop}</button></div>
      </section>
    ` : null}
`;
}
