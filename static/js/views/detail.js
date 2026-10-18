// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Detail(v) {
  return html`
  ${v.isDetail ? html`
    <section style="flex:1 0 auto;width:100%;max-width:${s(v.detMaxW)};margin:0 auto;padding:22px 28px 0;display:flex;flex-direction:column;gap:16px">
      <button onClick=${v.goShop} style="align-self:flex-start;font-family:inherit;border:none;background:none;padding:0;color:#0950e3;font-weight:600;font-size:13.5px;cursor:pointer">${v.tx?.backShop}</button>
      <section style="position:relative;overflow:hidden;background:#fff;border:1px solid #e2e9f0;border-radius:18px">${' '}
        ${v.det?.candle ? html`<span role="img" aria-label="" style="position:absolute;inset:0;width:100%;height:100%;opacity:.2;mask-image:linear-gradient(${s(v.g90)},transparent 20%,#000 80%);background-image:url('${s(v.det?.candle)}');background-size:cover;background-repeat:no-repeat;background-position:center;display:block"></span>` : null}${' '}
        <div style="position:relative;padding:22px 24px;display:flex;flex-wrap:wrap;gap:16px 24px;align-items:center">
          <span role="img" aria-hidden="true" style="width:56px;height:56px;border-radius:14px;flex-shrink:0;display:inline-block;flex-shrink:0;background-image:url('${s(v.det?.icon)}');background-size:cover;background-position:center"></span>
          <div style="flex:1 1 320px;min-width:0;display:flex;flex-direction:column;gap:6px">
            <h1 style="margin:0;font-size:26px;font-weight:700;letter-spacing:-.4px;line-height:1.15">${T(v.det?.name)} · ${T(v.det?.ticker)}</h1>
            <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12.5px">
              <a href=${v.det?.tvUrl} target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;font-weight:600"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:14px;height:14px" />${T(v.tx?.openTv)}</a>
              <span style="border:1px solid #e2e9f0;border-radius:999px;padding:2px 9px;font-weight:600;color:#5a6b80;background:#fff">${v.det?.interval}</span>
              <span style="border:1px solid #e2e9f0;border-radius:999px;padding:2px 9px;font-weight:600;color:#5a6b80;background:#fff">${v.det?.index}</span>
              <span style="border:1px solid #e2e9f0;border-radius:999px;padding:2px 9px;font-weight:600;color:#5a6b80;background:#fff">${v.det?.key}</span>
              </div>
            </div>
          <div style="display:flex;flex-direction:column;gap:8px;align-items:stretch;min-width:200px">
            <span style="font-size:28px;font-weight:700;letter-spacing:-.4px;text-align:end">${v.det?.priceLabel}</span>
            ${v.det?.isPaid ? html`<button onClick=${v.det?.onCart} style="font-family:inherit;border-radius:12px;padding:12px 18px;font-size:14.5px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:8px;border:1px solid ${s(v.det?.cartBorder)};background:${s(v.det?.cartBg)};color:${s(v.det?.cartColor)}"><i class=${v.det?.cartIcon}></i>${T(v.det?.cartLabel)}</button>` : null}
            ${v.det?.isFree ? html`<button onClick=${v.det?.onFree} style="font-family:inherit;border-radius:12px;padding:12px 18px;font-size:14.5px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:8px;border:1px solid #bfe0e8;background:#eef8fa;color:#0e7c98"><i class="fa-solid fa-file-arrow-down"></i>${T(v.tx?.download)}</button>` : null}
            <a href=${v.det?.tabHref} target="_blank" rel="noopener" style="font-size:12px;font-weight:600;text-align:end;display:inline-flex;gap:6px;align-items:center;justify-content:flex-end"><i class="fa-solid fa-up-right-from-square" style="font-size:10px"></i>${T(v.tx?.newTab)}</a>
            <button onClick=${v.det?.onFav} style="font-family:inherit;border:none;background:none;padding:0;cursor:pointer;font-size:12.5px;font-weight:600;color:${s(v.det?.favColor)};display:inline-flex;gap:6px;align-items:center;justify-content:flex-end"><i class=${v.det?.favIcon}></i>${T(v.tx?.favourites)}</button>
            </div>
          </div>
        </section>
      <div role="tablist" style="display:flex;gap:10px;flex-wrap:wrap">
        <button role="tab" aria-selected=${v.detOverview} onClick=${v.showOverview} style="font-family:inherit;border-radius:999px;padding:9px 18px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;font-size:15px;font-weight:700;background:${s(v.ovBg)};color:${s(v.ovColor)};border:1.5px solid ${s(v.ovLine)}"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}</button>
        <button role="tab" aria-selected=${v.detTreeTab} onClick=${v.showHowTab} style="font-family:inherit;border-radius:999px;padding:9px 18px;cursor:pointer;display:inline-flex;gap:8px;align-items:center;font-size:15px;font-weight:700;background:${s(v.hwBg)};color:${s(v.hwColor)};border:1.5px solid ${s(v.hwLine)}"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</button>
        </div>
      ${v.detOverview ? html`
        <button class="sf-hover11" onClick=${v.showHowTab} style="font-family:inherit;text-align:start;display:flex;align-items:center;gap:14px;flex-wrap:wrap;border:1.5px solid #b5e0ea;background:#e3f4f8;border-radius:16px;padding:14px 16px;cursor:pointer;color:#16263a"><span style="width:40px;height:40px;border-radius:12px;background:#0e7c98;color:#ffffff;display:grid;place-items:center;font-size:17px;flex-shrink:0"><i class="fa-solid fa-sitemap"></i></span><span style="flex:1 1 240px;display:flex;flex-direction:column;gap:2px"><strong style="font-size:15px">${v.tx?.howTeaserTitle}</strong><span style="font-size:13px;color:#5a6b80;text-wrap:pretty">${v.tx?.howTeaserText}</span></span><span style="border-radius:999px;background:#0e7c98;color:#ffffff;font-weight:700;font-size:13.5px;padding:8px 16px;display:inline-flex;gap:7px;align-items:center;white-space:nowrap"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</span></button>
        <div style="display:flex;gap:10px;align-items:center;border-radius:12px;padding:11px 14px;background:#eef3fd;border:1px solid #d6e2fb;font-size:13.5px"><i class="fa-regular fa-clock" style="color:#0950e3"></i><span>${v.detTf}</span></div>
        <div role="note" style="display:flex;gap:12px;align-items:flex-start;border-radius:14px;padding:14px 16px;background:#fff7ec;border:1px solid #f6d9ae"><i class="fa-solid fa-triangle-exclamation" style="color:#f79009;font-size:18px;margin-top:1px"></i><div style="display:flex;flex-direction:column;gap:2px;font-size:13.5px"><strong style="font-size:14.5px">${v.tx?.riskTitle}</strong><span style="text-wrap:pretty">${v.tx?.riskText}</span></div></div>
        <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:stretch">
          <div style="flex:1 1 360px;background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:10px">
            <div style="display:flex;align-items:center;gap:10px"><span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80;flex:1">${v.tx?.liveVsBacktest}</span><span title=${v.det?.gradeTip} style="display:inline-flex;align-items:center;gap:6px;font-size:12px;color:#5a6b80">${T(v.tx?.grade)}<span style="width:24px;height:24px;border-radius:7px;display:grid;place-items:center;font-weight:700;color:#fff;background:${s(v.det?.gradeBg)}">${v.det?.grade}</span></span></div>
            <div style="display:flex;justify-content:space-between;font-size:13px"><span>${v.tx?.colBacktest}</span><strong style="color:#15803d">${v.det?.nppSigned}</strong></div>
            <div style="height:8px;border-radius:999px;background:#e2e9f0;overflow:hidden"><div style="width:${s(v.det?.barBt)};height:100%;background:linear-gradient(${s(v.g90)},#47f9e5,#0950e3)"></div></div>
            <div style="display:flex;justify-content:space-between;font-size:13px"><span>${v.tx?.sinceRelease}</span><strong style="color:${s(v.det?.liveColor)}">${v.det?.live}</strong></div>
            <div style="height:8px;border-radius:999px;background:#e2e9f0;overflow:hidden"><div style="width:${s(v.det?.barLive)};height:100%;background:${s(v.det?.liveColor)}"></div></div>
            ${v.liveNote ? html`<span style="font-size:11.5px;color:#8d9cae">${v.liveNote}</span>` : null}
            </div>
          <div style="flex:1 1 300px;background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:10px">
            <span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.versions}</span>
            ${(v.versions || []).map((vr, $index) => html`<div style="display:flex;gap:10px;align-items:flex-start"><span style="width:10px;height:10px;border-radius:50%;background:${s(vr?.dot)};margin-top:5px;flex-shrink:0"></span><div style="flex:1;font-size:13px"><strong>${vr?.title}</strong>${vr?.note ? html`<div style="color:#5a6b80">${vr?.note}</div>` : null}</div>${vr?.update ? html`<span style="font-size:11px;font-weight:700;color:#0950e3;background:#e9f0fd;border-radius:999px;padding:2px 8px;white-space:nowrap">${v.tx?.updateAvail}</span>` : null}</div>`)}
            </div>
          </div>
        <div style="display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">
          <div style="flex:10 1 520px;min-width:0;display:flex;flex-direction:column;gap:14px">
            <div style="background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:8px"><span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.strategyChart}</span>${v.det?.profit ? html`<span role="img" aria-label="" style="width:100%;aspect-ratio:1466/438;border-radius:10px;border:1px solid #e2e9f0;display:block;background-image:url('${s(v.det?.profit)}');background-size:cover;background-repeat:no-repeat;background-position:center"></span>` : null}</div>
            <div style="background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:8px"><span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.candleChart}</span>${v.det?.candle ? html`<span role="img" aria-label="" style="width:100%;aspect-ratio:1424/362;border-radius:10px;border:1px solid #e2e9f0;display:block;background-image:url('${s(v.det?.candle)}');background-size:cover;background-repeat:no-repeat;background-position:center"></span>` : null}</div>
            </div>
          <div style="flex:1 1 300px;min-width:0;background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:16px 18px">${' '}
            <span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.allResults}</span>${' '}
            ${(v.detMetrics || []).map((dm, $index) => html`<div style="display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid #e2e9f0;font-size:13px"><span style="color:#5a6b80">${dm?.label}</span><strong style="font-variant-numeric:tabular-nums;text-align:end;color:${s(dm?.color)}">${dm?.value}</strong></div>`)}${' '}
            </div>
          </div>
        <div style="background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:6px">
          <span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.aboutInd}</span>
          <strong dir="auto" style="font-size:15px">${T(v.det?.key)} · ${T(v.det?.ind)}</strong>
          <p dir="auto" style="margin:0;color:#5a6b80;font-size:13.5px;text-wrap:pretty">${v.det?.ex}</p>
          <a href=${v.det?.indUrl} target="_blank" rel="noopener" style="font-size:13px;font-weight:600;display:inline-flex;gap:6px;align-items:center"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:14px;height:14px" />${T(v.tx?.seeInd)}</a>
          </div>
        <div style="border-radius:18px;overflow:hidden;border:1px solid #16263a;box-shadow:0 14px 36px rgba(15,27,45,.18)">
          <div style="padding:11px 16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:#16263a">
            <span style="display:flex;gap:6px"><span style="width:10px;height:10px;border-radius:50%;background:#ff5f57"></span><span style="width:10px;height:10px;border-radius:50%;background:#febc2e"></span><span style="width:10px;height:10px;border-radius:50%;background:#28c840"></span></span>
            <span dir="ltr" style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;color:#dbe4ef;overflow-wrap:anywhere">${v.pineFile}</span>
            <span style="margin-inline-start:auto;font-size:11.5px;font-weight:700;color:#47f9e5;border:1px solid rgba(71,249,229,.35);border-radius:999px;padding:2px 10px">Pine Script v5</span>
            </div>
          <div style="position:relative;background:#0f1b2d">
            <div dir="ltr" style="padding:12px 0 18px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px;line-height:1.7;text-align:left;overflow-x:auto">${' '}
              ${(v.pineLines || []).map((ln, $index) => html`<div style="display:flex;filter:${s(ln?.blur)};opacity:${s(ln?.op)};user-select:${s(ln?.sel)}"><span style="width:48px;flex-shrink:0;text-align:right;padding-right:16px;color:#4c5d74;user-select:none">${ln?.no}</span><span style="white-space:pre;tab-size:4;color:#dbe4ef;padding-right:16px">${(ln?.toks || []).map((tk, $index) => html`<span style="color:${s(tk?.c)};font-style:${s(tk?.fs)}">${tk?.t}</span>`)}</span></div>`)}${' '}
              </div>
            <div style="position:absolute;inset-inline:0;bottom:0;height:110px;background:linear-gradient(180deg,rgba(15,27,45,0),#0f1b2d 78%);display:flex;align-items:flex-end;justify-content:center;padding-bottom:14px">
              <span style="display:inline-flex;gap:8px;align-items:center;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#ffffff;border-radius:999px;padding:7px 14px;font-size:13px;font-weight:600"><i class="fa-solid fa-lock"></i>${T(v.tx?.scriptRest)}</span>
              </div>
            </div>
          <div style="background:#ffffff;padding:16px;display:flex;flex-direction:column;gap:12px">
            <div style="display:flex;gap:12px;align-items:flex-start"><span style="width:36px;height:36px;border-radius:10px;background:#e9f0fd;color:#0950e3;display:grid;place-items:center;flex-shrink:0"><i class="fa-solid fa-box-open"></i></span><div style="display:flex;flex-direction:column;gap:2px"><strong style="font-size:15.5px">${v.tx?.buyScriptTitle}</strong><span style="font-size:13px;color:#5a6b80;text-wrap:pretty">${v.tx?.buyScriptText}</span></div></div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px">
              ${(v.formats || []).map((fm, $index) => html`<div style="border:1px solid ${s(fm?.bd)};background:${s(fm?.bg)};border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:6px"><div style="display:flex;align-items:center;gap:8px"><span style="width:32px;height:32px;border-radius:9px;background:${s(fm?.icBg)};color:#ffffff;display:grid;place-items:center;font-size:15px;flex-shrink:0"><i class=${fm?.ic}></i></span><strong style="font-size:14px;flex:1">${fm?.name}</strong>${fm?.beta ? html`<span style="font-size:10.5px;font-weight:700;letter-spacing:.5px;color:#9a5b00;background:#fff3dd;border:1px solid #f6d9ae;border-radius:999px;padding:1px 7px">BETA</span>` : null}</div><span style="font-size:12.5px;color:#5a6b80;text-wrap:pretty">${fm?.desc}</span><span dir="ltr" style="font-size:11.5px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#8d9cae">${fm?.ext}</span></div>`)}
              </div>
            <span style="font-size:12.5px;color:#5a6b80;display:inline-flex;gap:7px;align-items:center"><i class="fa-solid fa-lock" style="color:#8d9cae"></i>${T(v.tx?.formatsNote)}</span>
            </div>
          </div>
        ` : null}
      ${v.detTreeTab ? html`
        ${v.Tree ? html`<div class="sc-host"><${v.Tree} embedded=${true} strategy=${v.treeRow} lang=${v.treeLang} onBuy=${v.treeBuy} owned=${v.treeOwned} signedIn=${v.treeSignedIn} ownerDownload=${v.treeDownload} /></div>` : null}
        <button class="sf-hover12" onClick=${v.backToSheet} style="align-self:flex-start;font-family:inherit;border-radius:999px;padding:9px 18px;font-size:14px;font-weight:700;cursor:pointer;display:inline-flex;gap:8px;align-items:center;border:1.5px solid #0950e3;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.toSheet)}</button>
        ` : null}
      </section>
    ` : null}
`;
}
