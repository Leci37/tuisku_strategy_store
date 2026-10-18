// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Lite(v) {
  return html`
  ${v.isLite ? html`
    <div style="background:#fff;border-bottom:1px solid #e2e9f0;overflow:hidden">
      <div style="max-width:1320px;margin:0 auto;padding:8px 28px;display:flex;gap:24px;white-space:nowrap;font-size:12.5px;overflow-x:auto;scrollbar-width:none">
        ${(v.tape || []).map((tp, $index) => html`<span style="display:inline-flex;align-items:center;gap:6px"><span style="width:16px;height:16px;border-radius:4px;background-image:url('${s(tp?.icon)}');background-size:cover;flex-shrink:0"></span><strong>${tp?.ticker}</strong><span style="color:#15803d;font-weight:600;font-variant-numeric:tabular-nums">${tp?.pct}</span></span>`)}
        </div>
      </div>
    <section style="position:relative;overflow:hidden;background:#fff;border-bottom:1px solid #e2e9f0">${' '}
      <img src="/static/img/hero_candle.png" alt="" decoding="async" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.2;mask-image:linear-gradient(${s(v.g90)},transparent 15%,#000 75%)" />${' '}
      <div style="position:relative;max-width:1320px;margin:0 auto;padding:44px 28px 28px;display:flex;flex-direction:column;gap:14px">
        <h1 style="margin:0;font-size:40px;font-weight:700;letter-spacing:-.6px;line-height:1.1;max-width:640px;text-wrap:balance">${v.tx?.liteTitle}</h1>
        <p style="margin:0;font-size:16px;color:#5a6b80;max-width:540px;text-wrap:pretty">${v.tx?.liteSub}</p>
        <label style="margin-top:8px;max-width:640px;display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e2e9f0;border-radius:14px;padding:12px 16px;box-shadow:0 12px 32px rgba(22,38,58,.08)"><i class="fa-solid fa-magnifying-glass" style="color:#8d9cae"></i><input data-search="lite" value=${v.q ?? ''} onInput=${v.onQ} placeholder=${v.tx?.searchPh} style="flex:1;min-width:0;border:none;outline:none;font-family:inherit;font-size:15px;color:#16263a;background:transparent" /></label>
        </div>
      </section>
    <section style="width:100%;max-width:1320px;margin:0 auto;padding:12px 28px 0;display:flex;flex-direction:column;gap:16px">
      <div role="tablist" style="display:flex;gap:26px;border-bottom:1px solid #e2e9f0;overflow-x:auto;overflow-y:hidden">
        ${(v.liteTabs || []).map((lt, $index) => html`<button role="tab" aria-selected=${lt?.sel} onClick=${lt?.go} style="font-family:inherit;border:none;background:none;padding:12px 0 10px;margin-bottom:-1px;font-size:14.5px;font-weight:600;cursor:pointer;white-space:nowrap;color:${s(lt?.color)};border-bottom:2px solid ${s(lt?.line)}">${lt?.label}</button>`)}
        </div>
      <div role="note" style="display:flex;gap:12px;align-items:flex-start;border-radius:14px;padding:14px 16px;background:#fff7ec;border:1px solid #f6d9ae"><i class="fa-solid fa-triangle-exclamation" style="color:#f79009;font-size:18px;margin-top:1px"></i><div style="display:flex;flex-direction:column;gap:2px;font-size:13.5px;color:#16263a"><strong style="font-size:14.5px">${v.tx?.riskTitle}</strong><span style="text-wrap:pretty">${v.tx?.riskText}</span></div></div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <span style="font-size:12px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#5a6b80">${v.tx?.bundles}</span>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px">
          ${(v.bundles || []).map((bd, $index) => html`
            <div style="background:linear-gradient(135deg,#0950e3,#0e7c98);color:#fff;border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:12px">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:10px">
                <div style="display:flex;padding-inline-start:8px">${(bd?.icons || []).map((ic, $index) => html`<span role="img" aria-hidden="true" style="width:30px;height:30px;border-radius:9px;border:2px solid #fff;background:#fff;margin-inline-start:-8px;display:inline-block;flex-shrink:0;background-image:url('${s(ic?.src)}');background-size:cover;background-position:center"></span>`)}</div>
                <span style="font-size:12px;font-weight:700;background:#fff;color:#0950e3;border-radius:999px;padding:3px 9px;white-space:nowrap">${bd?.save}</span>
                </div>
              <div style="line-height:1.3"><div style="font-weight:700;font-size:17px">${bd?.name}</div><div style="font-size:12.5px">${T(bd?.count)} · <span dir="ltr">${bd?.tickers}</span></div></div>
              <div style="display:flex;align-items:center;gap:10px"><div style="flex:1;line-height:1.15"><div style="font-size:12px;text-decoration:line-through">${bd?.was}</div><div style="font-size:22px;font-weight:700;letter-spacing:-.3px">${bd?.price}</div></div><button onClick=${bd?.go} style="font-family:inherit;border:none;border-radius:10px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;background:#fff;color:#0950e3;display:inline-flex;align-items:center;gap:7px;white-space:nowrap"><i class=${bd?.btnIcon}></i>${T(bd?.label)}</button></div>
              </div>
            `)}
          <div style="background:#fff;border:2px dashed #9fb8ef;border-radius:18px;padding:16px;display:flex;flex-direction:column;gap:12px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px"><strong style="font-size:17px">${v.tx?.packTitle}</strong><span style="font-size:12px;font-weight:700;background:#e9f0fd;color:#0950e3;border-radius:999px;padding:3px 9px;white-space:nowrap">${v.packSave}</span></div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">${(v.packSlots || []).map((ps, $index) => html`<button onClick=${v.openPack} style="width:44px;height:44px;border-radius:12px;border:${s(ps?.border)};background:#fff;display:grid;place-items:center;cursor:pointer;font-size:18px;color:#0950e3;padding:0">${ps?.filled ? html`<span role="img" aria-hidden="true" style="width:28px;height:28px;border-radius:7px;display:inline-block;flex-shrink:0;background-image:url('${s(ps?.icon)}');background-size:cover;background-position:center"></span>` : null}${ps?.empty ? html`+` : null}</button>`)}</div>
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><span style="flex:1;font-size:13px;color:#5a6b80">${v.packHint}</span><button onClick=${v.addPack} style="font-family:inherit;border:none;border-radius:10px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;background:${s(v.packBtnBg)};color:#fff;white-space:nowrap">${v.packBtnLabel}</button></div>
            </div>
          </div>
        </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px">
        ${(v.liteRows || []).map((r, $index) => html`
          <div class="sf-hover2" style="position:relative;background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:14px;display:flex;flex-direction:column;gap:12px">
            <div style="display:flex;align-items:center;gap:10px">
              <span role="img" aria-hidden="true" style="width:36px;height:36px;border-radius:10px;flex-shrink:0;display:inline-block;flex-shrink:0;background-image:url('${s(r?.icon)}');background-size:cover;background-position:center"></span>
              <div style="min-width:0;flex:1;line-height:1.25"><div onClick=${r?.onOpen} style="font-weight:700;font-size:16px;cursor:pointer;display:flex;align-items:center;gap:6px;flex-wrap:wrap">${T(r?.ticker)}${r?.isNew ? html`<span style="font-size:10.5px;font-weight:700;letter-spacing:.3px;color:#0950e3;background:#e9f0fd;border:1px solid #c5d6f8;border-radius:999px;padding:0 7px;line-height:17px">${v.tx?.tabNew}</span>` : null}</div><div dir="auto" style="font-size:12px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r?.name}</div></div>
              <button onClick=${r?.tipNpp} title=${v.tx?.npPct} style="font-family:inherit;border:none;cursor:pointer;font-size:15px;font-weight:700;color:#15803d;background:#e8f7ef;border-radius:8px;padding:4px 8px;white-space:nowrap;font-variant-numeric:tabular-nums;display:inline-flex;align-items:center;gap:5px">${T(r?.nppSigned)}<i class="fa-regular fa-circle-question" style="font-size:11px"></i></button>
              </div>
            <div onClick=${r?.onOpen} title=${v.tx?.openPage} style="position:relative;aspect-ratio:1466/260;border-radius:12px;overflow:hidden;border:1px solid #e2e9f0;background:#fff;cursor:pointer"><span style="position:absolute;top:6px;inset-inline-start:6px;font-size:10.5px;font-weight:700;background:rgba(255,255,255,.94);color:#5a6b80;border:1px solid #e2e9f0;border-radius:6px;padding:1px 6px;display:inline-flex;align-items:center;gap:4px"><i class="fa-solid fa-triangle-exclamation" style="color:#f79009;font-size:9px"></i>${T(v.tx?.colBacktest)}</span><img loading="lazy" decoding="async" src=${r?.profit} alt="" style="width:100%;height:100%;object-fit:cover;object-position:50% 82%;display:block" /></div>
            <div style="display:flex;gap:14px;font-size:12px;color:#5a6b80;flex-wrap:wrap;align-items:center"><button onClick=${r?.tipWin} style="font-family:inherit;border:none;background:none;padding:0;cursor:pointer;color:#5a6b80;font-size:12px;display:inline-flex;align-items:center;gap:4px">${T(v.tx?.sortWin)} <strong style="color:#16263a">${r?.win}</strong><i class="fa-regular fa-circle-question" style="color:#8d9cae"></i></button><button onClick=${r?.tipTrades} style="font-family:inherit;border:none;background:none;padding:0;cursor:pointer;color:#5a6b80;font-size:12px;display:inline-flex;align-items:center;gap:4px"><strong style="color:#16263a">${r?.trades}</strong> ${T(v.tx?.tradesWord)}<i class="fa-regular fa-circle-question" style="color:#8d9cae"></i></button><span>${T(r?.interval)} · ${T(r?.index)}</span></div>
            ${r?.tipOpen ? html`<div role="tooltip" style="position:absolute;inset-inline:14px;top:62px;z-index:5;background:#16263a;color:#fff;border-radius:12px;padding:10px 12px;font-size:12.5px;line-height:1.45;box-shadow:0 12px 30px rgba(22,38,58,.3);display:flex;gap:10px;align-items:flex-start"><span style="flex:1">${r?.tipText}</span><button onClick=${r?.tipClose} aria-label="×" style="border:none;background:none;color:#fff;cursor:pointer;font-size:16px;line-height:1;padding:0">×</button></div>` : null}
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px">
              <span title=${r?.gradeTip} style="width:24px;height:24px;border-radius:7px;display:grid;place-items:center;font-weight:700;font-size:12.5px;color:#fff;background:${s(r?.gradeBg)};cursor:help">${r?.grade}</span>
              <span style="color:#5a6b80">${T(v.tx?.sinceRelease)} <strong style="color:${s(r?.liveColor)}">${r?.live}</strong></span>
              <span style="margin-inline-start:auto;display:flex;gap:6px">
                <button onClick=${r?.onFav} title=${v.tx?.favourites} style="font-family:inherit;width:30px;height:30px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:13px;border:1px solid #e2e9f0;background:#fff;color:${s(r?.favColor)}"><i class=${r?.favIcon}></i></button>
                <button onClick=${r?.onCompare} title=${v.tx?.compare} style="font-family:inherit;width:30px;height:30px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:13px;border:1px solid #e2e9f0;background:${s(r?.cmpBg)};color:${s(r?.cmpColor)}"><i class="fa-solid fa-code-compare"></i></button>
                </span>
              </div>
            <span style="display:inline-flex;flex-wrap:wrap;gap:6px;align-self:flex-start"><button class="sf-hover3" onClick=${r?.onOpen} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}</button><button class="sf-hover4" onClick=${r?.onTree} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</button></span>
            <div style="display:flex;align-items:center;gap:10px">
              <span style="font-size:18px;font-weight:700;flex:1;white-space:nowrap">${r?.priceLabel}</span>
              ${r?.isPaid ? html`<button onClick=${r?.onCart} style="font-family:inherit;border-radius:10px;padding:10px 18px;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:7px;white-space:nowrap;border:1px solid ${s(r?.buyBorder)};background:${s(r?.buyBg)};color:${s(r?.buyColor)}"><i class=${r?.cartIcon}></i>${T(r?.buyLabel)}</button>` : null}
              ${r?.isFree ? html`<button onClick=${r?.onFree} style="font-family:inherit;border-radius:10px;padding:10px 18px;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;align-items:center;gap:7px;border:1px solid #bfe0e8;background:#eef8fa;color:#0e7c98"><i class="fa-solid fa-file-arrow-down"></i>${T(v.tx?.download)}</button>` : null}
              </div>
            </div>
          `)}
        </div>
      ${v.liteEmpty ? html`<p style="margin:0;padding:32px 0;text-align:center;color:#8d9cae">${v.tx?.noMatch}</p>` : null}
      <div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:6px 0"><span style="font-size:12.5px;color:#5a6b80">${v.liteShowing}</span>${v.liteMore ? html`<button onClick=${v.loadMoreLite} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:10px 20px;font-size:13.5px;cursor:pointer">${v.tx?.loadMore}</button>` : null}</div>
      </section>
    ${v.cartHas ? html`
      <div data-sf-cart style="position:sticky;bottom:${s(v.dockBottom)};z-index:10;width:calc(100% - 32px);max-width:780px;margin:24px auto 0;display:flex;flex-direction:column;align-items:flex-start;gap:8px">
        ${v.cmpHas ? html`<button onClick=${v.openCmp} style="font-family:inherit;border:none;border-radius:999px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer;background:#16263a;color:#fff;box-shadow:0 12px 30px rgba(22,38,58,.3);display:inline-flex;gap:8px;align-items:center"><i class="fa-solid fa-code-compare"></i>${T(v.tx?.compare)} · ${T(v.cmpCount)}</button>` : null}
        <div style="align-self:stretch;background:#fff;border:1px solid #e2e9f0;border-radius:16px;box-shadow:0 18px 48px rgba(26,35,56,.2);padding-block:10px;padding-inline:16px 12px;display:flex;align-items:center;gap:12px 14px;flex-wrap:wrap">
          <span style="display:flex;align-items:center;gap:8px;font-weight:700;white-space:nowrap"><span style="width:34px;height:34px;border-radius:10px;background:#e9f0fd;color:#0950e3;display:grid;place-items:center"><i class="fa-solid fa-cart-shopping"></i></span>${T(v.tx?.cart)} · ${T(v.cartCount)}</span>
          ${v.hasDiscount ? html`<span style="font-size:12px;font-weight:700;color:#15603c;background:#e8f7ef;border-radius:999px;padding:3px 9px">${v.liteOff}</span>` : null}
          ${v.codeClosed ? html`<button onClick=${v.openCode} style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;font-weight:600;font-size:12.5px;cursor:pointer">${v.tx?.haveCode}</button>` : null}
          ${v.codeOpen ? html`<span style="display:flex;flex-wrap:wrap;gap:6px;align-items:center"><input value=${v.code ?? ''} onInput=${v.onCode} placeholder=${v.tx?.codePh} style="width:100px;font-family:inherit;font-size:13px;color:#16263a;border:1px solid #e2e9f0;border-radius:10px;padding:6px 9px" /><button onClick=${v.applyCode} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:6px 10px;font-size:12px;cursor:pointer">${v.tx?.apply}</button><span style="font-size:11px;font-weight:600;color:${s(v.codeMsgColor)}">${v.codeMsg}</span></span>` : null}
          <span style="margin-inline-start:auto;text-align:end;line-height:1.15">${v.hasDiscount ? html`<span style="display:block;font-size:11.5px;color:#5a6b80;text-decoration:line-through">${v.subtotal}</span>` : null}<span style="font-size:20px;font-weight:700;letter-spacing:-.3px">${v.total}</span>${v.isLocal ? html`<span style="display:block;font-size:10.5px;color:#5a6b80">${v.payNote}</span>` : null}</span>
          <button onClick=${v.checkout} disabled=${v.paying} aria-busy=${v.paying} style="font-family:inherit;background:${s(v.payBgLite)};border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 20px;font-size:14px;cursor:${s(v.payCursor)};box-shadow:${s(v.payShadow)};display:inline-flex;gap:8px;align-items:center"><i class=${v.payIcon}></i>${T(v.tx?.checkout)}</button>
          <div style="flex:1 1 100%;display:flex;flex-wrap:wrap;gap:6px 16px;padding-top:8px;border-top:1px solid #eef2f6;font-size:11.5px;color:#5a6b80">
            <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-brands fa-paypal" style="color:#0950e3"></i>${T(v.tx?.trustPaypal)}</span>
            <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-solid fa-link" style="color:#0950e3"></i>${T(v.tx?.trustLinks)}</span>
            <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-solid fa-file-invoice" style="color:#0950e3"></i>${T(v.tx?.trustInvoice)}</span>
            ${v.contactOn ? html`<a href=${v.contactUrl} dir="ltr" style="display:inline-flex;gap:6px;align-items:center;color:#5a6b80;text-decoration:none"><i class="fa-regular fa-envelope" style="color:#0950e3"></i>${v.contactEmail}</a>` : null}
            </div>
          </div>
        </div>
      ` : null}
    ` : null}
`;
}
