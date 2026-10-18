// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Pro(v) {
  return html`
  ${v.isPro ? html`
    <div data-sf-cart style="background:#fff;border-bottom:1px solid #e2e9f0">
      <div style="max-width:1320px;margin:0 auto;padding:12px 28px 10px;display:flex;flex-wrap:wrap;gap:12px 28px;align-items:center">
        <div style="display:flex;align-items:center;gap:10px;flex:0 0 auto"><span style="width:36px;height:36px;border-radius:10px;background:#e9f0fd;color:#0950e3;display:grid;place-items:center"><i class="fa-solid fa-cart-shopping"></i></span><div style="line-height:1.25"><div style="font-weight:700">${T(v.tx?.cart)} · ${T(v.cartCount)}</div><button onClick=${v.emptyCart} style="font-family:inherit;border:none;background:none;padding:0;color:#c0392b;font-weight:600;font-size:12px;cursor:pointer">${v.tx?.emptyCart}</button></div></div>
        <div style="flex:1 1 360px;display:flex;flex-direction:column;gap:7px;min-width:0">
          <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:12.5px"><span style="font-weight:600">${v.tierLabel}</span><span style="color:#0950e3;font-weight:600">${v.nextTierMsg}</span></div>
          <div style="position:relative;height:8px;border-radius:999px;background:#e2e9f0;margin-inline-start:2px">
            <div style="position:absolute;inset-inline-start:0;top:0;bottom:0;width:${s(v.ladderPct)};border-radius:999px;background:linear-gradient(${s(v.g90)},#47f9e5,#0950e3)"></div>${' '}
            ${(v.tiers || []).map((t, $index) => html`<span style="position:absolute;inset-inline-start:${s(t?.pos)};top:50%;width:14px;height:14px;margin-inline-start:-14px;margin-top:-7px;border-radius:50%;background:${s(t?.tickBg)};border:2px solid #0950e3"></span>`)}${' '}
            </div>
          <div style="position:relative;height:28px;font-size:10.5px;color:#5a6b80">${(v.tiers || []).map((t, $index) => html`<span style="position:absolute;inset-inline-start:${s(t?.pos)};transform:${s(v.tickShift)};white-space:nowrap;text-align:end;line-height:1.2"><strong style="display:block;color:#16263a;font-size:11px">${t?.rate}</strong>${T(t?.amt)}</span>`)}</div>
          </div>
        <div class="sf-cartend" style="display:flex;align-items:center;gap:12px;flex:0 0 auto;flex-wrap:wrap">
          <div style="display:flex;flex-direction:column;gap:2px"><div style="display:flex;gap:6px"><input value=${v.code ?? ''} onInput=${v.onCode} placeholder=${v.tx?.codePh} style="width:110px;font-family:inherit;font-size:13px;color:#16263a;border:1px solid #e2e9f0;border-radius:10px;padding:7px 9px" /><button onClick=${v.applyCode} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:7px 10px;font-size:12px;cursor:pointer">${v.tx?.apply}</button></div><span style="font-size:11px;font-weight:600;color:${s(v.codeMsgColor)}">${v.codeMsg}</span></div>
          <div style="text-align:end;line-height:1.15">${v.hasDiscount ? html`<div style="font-size:12px;color:#5a6b80;text-decoration:line-through">${v.subtotal}</div>` : null}<div style="font-size:22px;font-weight:700;letter-spacing:-.3px">${v.total}</div>${v.isLocal ? html`<div style="font-size:10.5px;color:#5a6b80">${v.payNote}</div>` : null}</div>
          <button onClick=${v.checkout} disabled=${v.paying} aria-busy=${v.paying} style="font-family:inherit;background:${s(v.payBgPro)};border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 20px;font-size:14px;cursor:${s(v.payCursor)};box-shadow:${s(v.payShadow)};display:inline-flex;gap:8px;align-items:center"><i class=${v.payIcon}></i>${T(v.tx?.checkout)}</button>
          </div>
        <div style="flex:1 1 100%;display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px 16px;font-size:11.5px;color:#5a6b80;margin-top:-4px">
          <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-brands fa-paypal" style="color:#0950e3"></i>${T(v.tx?.trustPaypal)}</span>
          <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-solid fa-link" style="color:#0950e3"></i>${T(v.tx?.trustLinks)}</span>
          <span style="display:inline-flex;gap:6px;align-items:center"><i class="fa-solid fa-file-invoice" style="color:#0950e3"></i>${T(v.tx?.trustInvoice)}</span>
          ${v.contactOn ? html`<a href=${v.contactUrl} dir="ltr" style="display:inline-flex;gap:6px;align-items:center;color:#5a6b80;text-decoration:none"><i class="fa-regular fa-envelope" style="color:#0950e3"></i>${v.contactEmail}</a>` : null}
          </div>
        </div>
      </div>
    <section style="flex:1 0 auto;width:100%;max-width:1320px;margin:0 auto;padding:24px 28px 0;display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start">
      <aside style="flex:1 1 260px;max-width:100%;background:#fff;border:1px solid #e2e9f0;border-radius:16px;overflow:visible">
        <div style="padding:16px 18px;display:flex;align-items:flex-end;justify-content:space-between;gap:10px;border-bottom:1px solid #e2e9f0"><div style="line-height:1.15"><div style="font-size:26px;font-weight:700;letter-spacing:-.4px">${v.shownCount}</div><div style="font-size:12px;color:#5a6b80">${v.tx?.shown}</div></div><button onClick=${v.resetAll} type="button" class="sf-link" style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;cursor:pointer;font-size:12.5px;font-weight:600">${v.tx?.reset}</button></div>
        <button type="button" onClick=${v.toggleFree} role="switch" aria-checked=${v.freeOn} style="font-family:inherit;font-size:inherit;line-height:inherit;color:inherit;background:none;border:0;margin:0;width:100%;text-align:start;padding:12px 18px;display:flex;align-items:center;justify-content:space-between;gap:10px;cursor:pointer;border-bottom:1px solid #e2e9f0"><span style="font-weight:600;font-size:13.5px;display:flex;gap:8px;align-items:center"><i class="fa-solid fa-file-arrow-down" style="color:#0e7c98"></i>${T(v.tx?.onlyFree)}</span><span style="width:34px;height:20px;border-radius:999px;background:${s(v.freeTrack)};position:relative;flex-shrink:0;transition:background .15s"><span style="position:absolute;top:2px;inset-inline-start:2px;width:16px;height:16px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(22,38,58,.3);transform:${s(v.freeKnob)};transition:transform .15s"></span></span></button>${' '}
        ${(v.rangeTop || []).map((rg, $index) => html`
          <div style="padding:12px 18px;border-bottom:1px solid #e2e9f0;display:flex;flex-direction:column;gap:8px">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:13px"><span style="font-weight:600">${rg?.label}</span><span style="font-size:12px;font-weight:600;color:${s(rg?.valColor)};white-space:nowrap">${rg?.value}</span></div>
            <div style="display:flex;align-items:flex-end;gap:2px;height:40px;border-bottom:1px solid #e2e9f0;margin:0 2px">${(rg?.bars || []).map((b, $index) => html`<span title=${b?.tip} style="flex:1;height:${s(b?.h)};opacity:${s(b?.op)};border-radius:2px 2px 0 0;background:${s(b?.bg)};transition:opacity .15s"></span>`)}</div>
            <div onPointerDown=${rg?.onDown} style="position:relative;height:22px;margin:0 9px;touch-action:none;cursor:pointer">${' '}
              <span style="position:absolute;inset-inline:0;top:9px;height:4px;border-radius:999px;background:#e2e9f0"></span>${' '}
              <span style="position:absolute;top:9px;height:4px;border-radius:999px;background:linear-gradient(${s(v.g90)},#47f9e5,#0950e3);inset-inline-start:${s(rg?.loPct)};width:${s(rg?.wPct)}"></span>${' '}
              <span style="position:absolute;top:2px;inset-inline-start:${s(rg?.loPct)};margin-inline-start:-9px;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid #0950e3;box-shadow:0 2px 6px rgba(9,80,227,.25)"></span>${' '}
              <span style="position:absolute;top:2px;inset-inline-start:${s(rg?.hiPct)};margin-inline-start:-9px;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid #0950e3;box-shadow:0 2px 6px rgba(9,80,227,.25)"></span>${' '}
              </div>
            <div style="display:flex;justify-content:space-between;gap:8px"><input class="sf-focus5" value=${rg?.loIn ?? ''} onInput=${rg?.loOn} onBlur=${rg?.loDone} onKeyDown=${rg?.onInKey} aria-label=${rg?.label} style="width:46%;min-width:0;font-family:inherit;font-size:12.5px;font-weight:600;color:#16263a;border:1px solid #e2e9f0;border-radius:8px;padding:3px 8px;font-variant-numeric:tabular-nums;background:#ffffff;outline:none;text-align:start" /><input class="sf-focus5" value=${rg?.hiIn ?? ''} onInput=${rg?.hiOn} onBlur=${rg?.hiDone} onKeyDown=${rg?.onInKey} aria-label=${rg?.label} style="width:46%;min-width:0;font-family:inherit;font-size:12.5px;font-weight:600;color:#16263a;border:1px solid #e2e9f0;border-radius:8px;padding:3px 8px;font-variant-numeric:tabular-nums;background:#ffffff;outline:none;text-align:end" /></div>
            </div>
          `)}${' '}
        ${(v.selF || []).map((sl, $index) => html`
          <div style="position:relative;border-bottom:1px solid #e2e9f0">
            <button type="button" onClick=${sl?.toggle} aria-expanded=${String(!!sl?.open)} style="font-family:inherit;line-height:inherit;color:inherit;border:0;margin:0;width:100%;text-align:start;padding:11px 18px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:13px;cursor:pointer;background:${s(sl?.rowBg)}"><span style="font-weight:600">${sl?.label}</span><span dir="auto" style="color:${s(sl?.valColor)};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:600">${T(sl?.value)} <span style="font-size:10px;color:#8d9cae">${sl?.caret}</span></span></button>${' '}
            ${sl?.open ? html`
              <div style="position:absolute;inset-inline:10px;top:calc(100% - 2px);z-index:40;background:#fff;border:1px solid #e2e9f0;border-radius:14px;box-shadow:0 18px 48px rgba(26,35,56,.2);padding:8px;display:flex;flex-direction:column;gap:6px">
                <label style="display:flex;align-items:center;gap:8px;border:1px solid #e2e9f0;border-radius:9px;padding:6px 9px"><i class="fa-solid fa-magnifying-glass" style="color:#8d9cae;font-size:11px"></i><input value=${sl?.q ?? ''} onInput=${sl?.onQ} placeholder=${v.tx?.searchSmall} style="flex:1;min-width:0;border:none;outline:none;font-family:inherit;font-size:13px;color:#16263a;background:transparent" /></label>
                <div style="display:flex;justify-content:space-between;font-size:12px;font-weight:600;padding:0 4px"><button onClick=${sl?.all} type="button" class="sf-link" style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;cursor:pointer;font-size:12px;font-weight:600">${v.tx?.selAll}</button><button onClick=${sl?.none} type="button" class="sf-link" style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;cursor:pointer;font-size:12px;font-weight:600">${v.tx?.selNone}</button></div>
                <div style="max-height:230px;overflow:auto;display:flex;flex-direction:column">
                  ${(sl?.opts || []).map((op, $index) => html`<button class="sf-hover1" onClick=${op?.toggle} style="display:flex;align-items:center;gap:9px;border:none;background:none;cursor:pointer;font-family:inherit;padding:7px 8px;border-radius:9px;font-size:13px;color:#16263a;text-align:start"><span style="width:16px;height:16px;border-radius:4px;border:1.5px solid ${s(op?.bd)};background:${s(op?.bg)};display:grid;place-items:center;color:#fff;font-size:10px;font-weight:700;flex-shrink:0">${op?.check}</span>${op?.hasIcon ? html`<span role="img" aria-hidden="true" style="width:18px;height:18px;border-radius:4px;display:inline-block;flex-shrink:0;background-image:url('${s(op?.icon)}');background-size:cover;background-position:center"></span>` : null}<span dir="auto" style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${op?.label}</span><span style="font-size:11.5px;color:#8d9cae">${op?.count}</span></button>`)}
                  </div>
                </div>
              ` : null}${' '}
            </div>
          `)}${' '}
        ${(v.moreF || []).map((mf, $index) => html`
          <div style="border-bottom:1px solid #e2e9f0">
            <button type="button" onClick=${mf?.toggle} aria-expanded=${String(!!mf?.open)} style="font-family:inherit;line-height:inherit;color:inherit;border:0;margin:0;width:100%;text-align:start;padding:9px 18px;display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:13px;cursor:pointer;background:${s(mf?.rowBg)}"><span style="font-weight:${s(mf?.weight)}">${mf?.label}</span><span style="color:${s(mf?.valColor)};font-size:12px;font-weight:600;white-space:nowrap">${T(mf?.value)} <span style="font-size:10px;color:#8d9cae">${mf?.caret}</span></span></button>${' '}
            ${mf?.open ? html`<div style="padding:4px 18px 14px;display:flex;flex-direction:column;gap:8px">
                <div style="display:flex;align-items:flex-end;gap:2px;height:40px;border-bottom:1px solid #e2e9f0;margin:0 2px">${(mf?.bars || []).map((b, $index) => html`<span title=${b?.tip} style="flex:1;height:${s(b?.h)};opacity:${s(b?.op)};border-radius:2px 2px 0 0;background:${s(b?.bg)};transition:opacity .15s"></span>`)}</div>
                <div onPointerDown=${mf?.onDown} style="position:relative;height:22px;margin:0 9px;touch-action:none;cursor:pointer">${' '}
                  <span style="position:absolute;inset-inline:0;top:9px;height:4px;border-radius:999px;background:#e2e9f0"></span>${' '}
                  <span style="position:absolute;top:9px;height:4px;border-radius:999px;background:linear-gradient(${s(v.g90)},#47f9e5,#0950e3);inset-inline-start:${s(mf?.loPct)};width:${s(mf?.wPct)}"></span>${' '}
                  <span style="position:absolute;top:2px;inset-inline-start:${s(mf?.loPct)};margin-inline-start:-9px;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid #0950e3;box-shadow:0 2px 6px rgba(9,80,227,.25)"></span>${' '}
                  <span style="position:absolute;top:2px;inset-inline-start:${s(mf?.hiPct)};margin-inline-start:-9px;width:18px;height:18px;border-radius:50%;background:#fff;border:2px solid #0950e3;box-shadow:0 2px 6px rgba(9,80,227,.25)"></span>${' '}
                  </div>
                <div style="display:flex;justify-content:space-between;gap:8px"><input class="sf-focus5" value=${mf?.loIn ?? ''} onInput=${mf?.loOn} onBlur=${mf?.loDone} onKeyDown=${mf?.onInKey} aria-label=${mf?.label} style="width:46%;min-width:0;font-family:inherit;font-size:12.5px;font-weight:600;color:#16263a;border:1px solid #e2e9f0;border-radius:8px;padding:3px 8px;font-variant-numeric:tabular-nums;background:#ffffff;outline:none;text-align:start" /><input class="sf-focus5" value=${mf?.hiIn ?? ''} onInput=${mf?.hiOn} onBlur=${mf?.hiDone} onKeyDown=${mf?.onInKey} aria-label=${mf?.label} style="width:46%;min-width:0;font-family:inherit;font-size:12.5px;font-weight:600;color:#16263a;border:1px solid #e2e9f0;border-radius:8px;padding:3px 8px;font-variant-numeric:tabular-nums;background:#ffffff;outline:none;text-align:end" /></div>
                </div>` : null}${' '}
            </div>
          `)}${' '}
        </aside>
      <section style="flex:10 1 560px;min-width:0;display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
          <h1 style="margin:0;font-size:22px;font-weight:700;letter-spacing:-.3px">${v.tx?.strategies}</h1>
          <div style="display:flex;background:#e9eef4;border-radius:10px;padding:3px;flex-wrap:wrap">
            ${(v.sortTabs || []).map((st, $index) => html`<button onClick=${st?.go} style="font-family:inherit;border:none;border-radius:8px;padding:5px 10px;font-size:12px;font-weight:600;cursor:pointer;background:${s(st?.bg)};color:${s(st?.color)};box-shadow:${s(st?.shadow)}">${st?.label}</button>`)}
            </div>
          <label style="margin-inline-start:auto;width:240px;max-width:100%;display:flex;align-items:center;gap:8px;background:#fff;border:1px solid #e2e9f0;border-radius:10px;padding:6px 10px"><i class="fa-solid fa-magnifying-glass" style="color:#8d9cae;font-size:12px"></i><input data-search="pro" value=${v.q ?? ''} onInput=${v.onQ} placeholder=${v.tx?.searchSmall} title=${v.tx?.searchPh} style="flex:1;min-width:0;border:none;outline:none;font-family:inherit;font-size:13px;color:#16263a;background:transparent" /></label>
          <div role="group" aria-label=${v.tx?.view} style="display:flex;background:#e9eef4;border-radius:10px;padding:3px">
            ${(v.viewTabs || []).map((vt, $index) => html`<button onClick=${vt?.go} aria-pressed=${vt?.pressed} style="font-family:inherit;border:none;border-radius:8px;padding:5px 11px;font-size:12.5px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:7px;background:${s(vt?.bg)};color:${s(vt?.color)};box-shadow:${s(vt?.shadow)}"><i class=${vt?.icon}></i>${T(vt?.label)}</button>`)}
            </div>
          </div>
        ${v.hasActive ? html`<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
            ${(v.activeChips || []).map((ac, $index) => html`<span style="display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding-block:4px;padding-inline:10px 5px;font-size:12.5px;background:#e9f0fd;color:#0950e3;font-weight:600;white-space:nowrap">${T(ac?.label)}<button onClick=${ac?.clear} aria-label="×" style="border:none;background:#fff;color:#0950e3;width:18px;height:18px;border-radius:50%;cursor:pointer;font-size:12px;line-height:1;padding:0">×</button></span>`)}
            <button onClick=${v.resetAll} type="button" class="sf-link" style="font-family:inherit;border:none;background:none;padding:0;color:#0950e3;cursor:pointer;font-size:12.5px;font-weight:600">${v.tx?.clearAll}</button>
            </div>` : null}
        <div role="note" style="display:flex;gap:12px;align-items:flex-start;border-radius:12px;padding:12px 14px;background:#eef3fd;border:1px solid #d6e2fb">
          <i class="fa-solid fa-triangle-exclamation" style="color:#f79009;font-size:16px;margin-top:2px"></i>
          <div style="display:flex;flex-direction:column;gap:2px;font-size:13px"><strong style="font-size:13.5px">${v.tx?.riskTitle}</strong><span style="text-wrap:pretty">${v.tx?.riskText}</span></div>
          </div>
        ${v.proEmpty ? html`<p style="margin:0;padding:32px 0;text-align:center;color:#8d9cae">${v.tx?.noMatch}</p>` : null}
        ${v.isTable ? html`
          <div style="background:#fff;border:1px solid #e2e9f0;border-radius:14px;overflow:hidden">
            <div style="overflow-x:auto">
              <table style="width:100%;min-width:1100px;border-collapse:collapse;font-size:13px">
                <thead><tr>
                    <th style="text-align:start;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#5a6b80;font-weight:700;padding:10px 14px;border-bottom:1px solid #e2e9f0;background:#fbfcfe;white-space:nowrap">${v.tx?.fSymbol}</th>
                    <th style="text-align:start;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#5a6b80;font-weight:700;padding:10px 12px;border-bottom:1px solid #e2e9f0;background:#fbfcfe;white-space:nowrap">${v.tx?.fTimeframe}</th>
                    <th style="text-align:start;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#5a6b80;font-weight:700;padding:10px 12px;border-bottom:1px solid #e2e9f0;background:#fbfcfe;white-space:nowrap">${v.tx?.fIndicators}</th>
                    <th style="text-align:start;font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#5a6b80;font-weight:700;padding:10px 12px;border-bottom:1px solid #e2e9f0;background:#fbfcfe;white-space:nowrap">${v.tx?.colBacktest}</th>
                    ${(v.numCols || []).map((nc, $index) => html`<th aria-sort=${nc?.ariaSort} style="text-align:end;font-size:11px;text-transform:uppercase;letter-spacing:.4px;font-weight:700;padding:10px 12px;border-bottom:1px solid #e2e9f0;background:#fbfcfe;white-space:nowrap;cursor:${s(nc?.cursor)};color:${s(nc?.color)}"><button type="button" onClick=${nc?.go} style="font:inherit;letter-spacing:inherit;text-transform:inherit;color:inherit;background:none;border:0;padding:0;cursor:inherit">${T(nc?.label)} ${T(nc?.arrow)}</button></th>`)}
                    <th style="padding:10px 14px;border-bottom:1px solid #e2e9f0;background:#fbfcfe"></th>
                    </tr></thead>
                <tbody>
                  ${(v.proRows || []).map((r, $index) => html`
                    <tr class="sf-hover6" onClick=${r?.onToggle} style="cursor:pointer;background:${s(r?.openBg)}">
                      <td style="padding:9px 14px;border-bottom:1px solid #e2e9f0"><div style="display:flex;align-items:center;gap:10px;white-space:nowrap"><span role="img" aria-hidden="true" style="width:24px;height:24px;border-radius:6px;display:inline-block;flex-shrink:0;background-image:url('${s(r?.icon)}');background-size:cover;background-position:center"></span><div style="line-height:1.25"><div style="font-weight:700;display:flex;gap:6px;align-items:center">${T(r?.ticker)}<span title=${r?.gradeTip} style="width:18px;height:18px;border-radius:5px;display:inline-grid;place-items:center;font-size:10.5px;color:#fff;background:${s(r?.gradeBg)}">${r?.grade}</span></div><div style="font-size:11.5px;color:#5a6b80">${r?.name}</div></div></div></td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;white-space:nowrap">${r?.interval}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;max-width:220px"><div dir="auto" title=${r?.ex} style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis"><span style="color:#8d9cae">${r?.key}</span> ${T(r?.ind)}</div></td>
                      <td style="padding:6px 12px;border-bottom:1px solid #e2e9f0"><div style="width:128px;height:34px;border-radius:6px;overflow:hidden;border:1px solid #e2e9f0;background:#fff"><img loading="lazy" decoding="async" src=${r?.profit} alt="" style="width:100%;height:100%;object-fit:cover;object-position:50% 80%;display:block" /></div></td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap">${r?.np}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-weight:600;color:#15803d;font-variant-numeric:tabular-nums;white-space:nowrap">${r?.nppSigned}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-variant-numeric:tabular-nums;white-space:nowrap">${r?.win}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-variant-numeric:tabular-nums">${r?.trades}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-variant-numeric:tabular-nums;white-space:nowrap">${r?.avg}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-variant-numeric:tabular-nums">${r?.months}</td>
                      <td style="padding:9px 12px;border-bottom:1px solid #e2e9f0;text-align:end;font-weight:700;white-space:nowrap">${r?.priceLabel}</td>
                      <td style="padding:9px 14px;border-bottom:1px solid #e2e9f0;text-align:end;white-space:nowrap"><button onClick=${r?.onCompare} title=${v.tx?.compare} style="font-family:inherit;width:30px;height:30px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:13px;border:1px solid #e2e9f0;width:32px;height:32px;margin-inline-end:6px;background:${s(r?.cmpBg)};color:${s(r?.cmpColor)}"><i class="fa-solid fa-code-compare"></i></button>${' '}
                        ${r?.isPaid ? html`<button onClick=${r?.onCart} title=${r?.cartLabel} style="font-family:inherit;width:32px;height:32px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:12.5px;border:1px solid ${s(r?.cartBorder)};background:${s(r?.cartBg)};color:${s(r?.cartColor)}"><i class=${r?.cartIcon}></i></button>` : null}${' '}
                        ${r?.isFree ? html`<button onClick=${r?.onFree} title=${v.tx?.download} style="font-family:inherit;width:32px;height:32px;border-radius:9px;cursor:pointer;display:inline-grid;place-items:center;font-size:12.5px;border:1px solid #bfe0e8;background:#eef8fa;color:#0e7c98"><i class="fa-solid fa-file-arrow-down"></i></button>` : null}${' '}
                        </td>
                      </tr>
                    ${r?.isOpen ? html`
                      <tr><td colSpan="12" style="padding:16px 14px;background:#f7faff;border-bottom:1px solid #e2e9f0">
                          <div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) 260px;gap:16px;align-items:start">
                            <div style="display:flex;flex-direction:column;gap:6px"><span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.strategyChart}</span><img loading="lazy" decoding="async" src=${r?.profit} alt="" style="width:100%;aspect-ratio:1466/438;border-radius:10px;border:1px solid #e2e9f0;background:#fff;display:block" /></div>
                            <div style="display:flex;flex-direction:column;gap:6px"><span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#5a6b80">${v.tx?.candleChart}</span><img loading="lazy" decoding="async" src=${r?.candle} alt="" style="width:100%;aspect-ratio:1424/362;border-radius:10px;border:1px solid #e2e9f0;background:#fff;display:block" /></div>
                            <div style="display:flex;flex-direction:column;gap:10px;font-size:13px">
                              <strong>${T(r?.key)} · ${T(r?.ind)}</strong>
                              <span style="color:#5a6b80;text-wrap:pretty">${r?.ex}</span>
                              <a href=${r?.tvUrl} target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:6px;font-weight:600"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:14px;height:14px" />${T(v.tx?.openTv)} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:10px"></i></a>
                              <span style="display:inline-flex;flex-wrap:wrap;gap:6px;align-self:flex-start"><button class="sf-hover3" onClick=${r?.onOpen} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}</button><button class="sf-hover4" onClick=${r?.onTree} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</button></span>
                              </div>
                            </div>
                          </td></tr>
                      ` : null}
                    `)}
                  </tbody>
                </table>
              </div>
            <div style="display:flex;align-items:center;gap:16px;justify-content:flex-end;padding:10px 14px;border-top:1px solid #e2e9f0;font-size:12.5px;color:#5a6b80;flex-wrap:wrap">
              <span>${T(v.tx?.rowsPerPage)} <strong style="color:#16263a">25 ▾</strong></span>
              <span>${v.rangeLabel2}</span>
              <span style="display:flex;gap:4px;align-items:center">
                ${(v.pages || []).map((pg, $index) => html`<button onClick=${pg?.go} disabled=${pg?.off} style="font-family:inherit;min-width:28px;height:28px;padding:0 6px;border-radius:8px;font-size:12.5px;font-weight:600;cursor:pointer;border:1px solid ${s(pg?.border)};background:${s(pg?.bg)};color:${s(pg?.color)}">${pg?.label}</button>`)}
                </span>
              </div>
            </div>
          ` : null}
        ${v.isRows ? html`
          <div style="display:flex;flex-direction:column;gap:12px">
            ${(v.proRows || []).map((r, $index) => html`
              <div style="position:relative;overflow:hidden;background:#fff;border:1px solid #e2e9f0;border-radius:16px">${' '}
                <img loading="lazy" decoding="async" src=${r?.candle} alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.22;mask-image:linear-gradient(${s(v.g90)},transparent 20%,#000 78%)" />${' '}
                <div style="position:relative;padding:18px 20px;display:flex;flex-wrap:wrap;gap:16px 18px;align-items:center">
                  <div style="flex:1 1 200px;display:flex;flex-direction:column;gap:6px;min-width:0">
                    <div style="display:flex;align-items:center;gap:10px"><span role="img" aria-hidden="true" style="width:40px;height:40px;border-radius:10px;flex-shrink:0;display:inline-block;flex-shrink:0;background-image:url('${s(r?.icon)}');background-size:cover;background-position:center"></span><div style="line-height:1.25;min-width:0"><div dir="auto" style="font-weight:700;font-size:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r?.name}</div><div style="display:flex;flex-wrap:wrap;align-items:center;column-gap:5px;font-size:12.5px;font-weight:600"><a href=${r?.tvUrl} target="_blank" style="display:inline-flex;gap:5px;align-items:center"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:13px;height:13px" />${T(r?.ticker)}</a><span style="color:#5a6b80;font-weight:500;white-space:nowrap">· ${T(r?.interval)} · ${T(r?.index)}</span></div></div></div>
                    <span dir="auto" title=${r?.ex} style="font-size:12.5px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${T(r?.key)} · ${T(r?.ind)}</span>
                    <span style="display:inline-flex;flex-wrap:wrap;gap:6px;align-self:flex-start"><button class="sf-hover3" onClick=${r?.onOpen} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}</button><button class="sf-hover4" onClick=${r?.onTree} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</button></span>
                    </div>
                  <img loading="lazy" decoding="async" src=${r?.profit} alt="" style="flex:1 1 240px;min-width:0;max-width:320px;width:100%;aspect-ratio:1466/438;border-radius:10px;border:1px solid #e2e9f0;background:#fff;display:block;box-shadow:0 6px 16px rgba(22,38,58,.08)" />
                  <div style="flex:1 1 180px;display:grid;grid-template-columns:1fr 1fr;gap:8px 14px">
                    <div style="line-height:1.2"><div style="font-size:11px;color:#5a6b80">${v.tx?.sortNp}</div><div style="font-weight:700;font-size:15px;font-variant-numeric:tabular-nums">${r?.np}</div></div>
                    <div style="line-height:1.2"><div style="font-size:11px;color:#5a6b80">${v.tx?.sortWin}</div><div style="font-weight:700;font-size:15px">${r?.win}</div></div>
                    <div style="line-height:1.2"><div style="font-size:11px;color:#5a6b80">${v.tx?.npPct}</div><div style="font-weight:700;font-size:15px;color:#15803d">${r?.nppSigned}</div></div>
                    <div style="line-height:1.2"><div style="font-size:11px;color:#5a6b80">${v.tx?.sortTrades}</div><div style="font-weight:700;font-size:15px">${r?.trades}</div></div>
                    </div>
                  <div style="flex:0 0 150px;display:flex;flex-direction:column;gap:8px;align-items:stretch">
                    <span style="font-size:22px;font-weight:700;letter-spacing:-.3px;text-align:end">${r?.priceLabel}</span>
                    ${r?.isPaid ? html`<button onClick=${r?.onCart} style="font-family:inherit;border-radius:12px;padding:10px 12px;font-size:13.5px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:7px;border:1px solid ${s(r?.cartBorder)};background:${s(r?.cartBg)};color:${s(r?.cartColor)}"><i class=${r?.cartIcon}></i>${T(r?.cartLabel)}</button>` : null}
                    ${r?.isFree ? html`<button onClick=${r?.onFree} style="font-family:inherit;border-radius:12px;padding:10px 12px;font-size:13.5px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:7px;border:1px solid #bfe0e8;background:#eef8fa;color:#0e7c98"><i class="fa-solid fa-file-arrow-down"></i>${T(v.tx?.download)}</button>` : null}
                    </div>
                  </div>
                </div>
              `)}
            </div>
          ` : null}
        ${v.isCards ? html`
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px">
            ${(v.proRows || []).map((r, $index) => html`
              <div class="sf-hover7" style="background:#fff;border:1px solid #e2e9f0;border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:12px">
                <div style="display:flex;align-items:center;gap:10px">
                  <span role="img" aria-hidden="true" style="width:32px;height:32px;border-radius:8px;flex-shrink:0;display:inline-block;flex-shrink:0;background-image:url('${s(r?.icon)}');background-size:cover;background-position:center"></span>
                  <div style="min-width:0;flex:1;line-height:1.3"><div dir="auto" style="font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r?.name}</div><div style="font-size:12px;color:#5a6b80;display:flex;flex-wrap:wrap;align-items:center;column-gap:5px"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:12px;height:12px" /><a href=${r?.tvUrl} target="_blank" style="font-weight:600">${r?.ticker}</a><span style="white-space:nowrap">· ${T(r?.interval)} · ${T(r?.index)}</span></div></div>
                  <span style="font-size:18px;font-weight:700;white-space:nowrap">${r?.priceLabel}</span>
                  </div>
                <img loading="lazy" decoding="async" src=${r?.profit} alt="" style="width:100%;aspect-ratio:1466/438;border-radius:10px;border:1px solid #e2e9f0;display:block" />
                <img loading="lazy" decoding="async" src=${r?.candle} alt="" style="width:100%;aspect-ratio:1424/362;border-radius:10px;border:1px solid #e2e9f0;display:block" />
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px 10px">
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.sortNp}</div><div style="font-weight:700;font-size:13.5px">${r?.np}</div></div>
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.sortWin}</div><div style="font-weight:700;font-size:13.5px">${r?.win}</div></div>
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.sortTrades}</div><div style="font-weight:700;font-size:13.5px">${r?.trades}</div></div>
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.npPct}</div><div style="font-weight:700;font-size:13.5px;color:#15803d">${r?.nppSigned}</div></div>
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.avgProfit}</div><div style="font-weight:700;font-size:13.5px">${r?.avg}</div></div>
                  <div><div style="font-size:11px;color:#5a6b80">${v.tx?.monthsTrained}</div><div style="font-weight:700;font-size:13.5px">${r?.months}</div></div>
                  </div>
                <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;min-width:0"><a dir="auto" href=${r?.indUrl} target="_blank" rel="noopener" title=${r?.ex} style="font-size:12.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0">${T(r?.key)} · ${T(r?.ind)}</a><button onClick=${r?.onOpen} style="flex-shrink:0;font-family:inherit;border:none;background:none;padding:0;color:#0950e3;font-weight:600;font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;gap:6px"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.openPage)}</button></div>
                <span style="display:inline-flex;flex-wrap:wrap;gap:6px;align-self:flex-start"><button class="sf-hover3" onClick=${r?.onOpen} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-regular fa-file-lines"></i>${T(v.tx?.overviewTab)}</button><button class="sf-hover4" onClick=${r?.onTree} style="font-family:inherit;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:700;cursor:pointer;display:inline-flex;gap:4px;align-items:center;white-space:nowrap;border:1px solid #b5e0ea;background:#e3f4f8;color:#0e7c98"><i class="fa-solid fa-sitemap"></i>${T(v.tx?.howItDecides)}</button></span>
                ${r?.isPaid ? html`<button onClick=${r?.onCart} style="font-family:inherit;width:100%;border-radius:12px;padding:11px 16px;font-size:14px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:8px;border:1px solid ${s(r?.cartBorder)};background:${s(r?.cartBg)};color:${s(r?.cartColor)}"><i class=${r?.cartIcon}></i>${T(r?.cartLabel)}</button>` : null}
                ${r?.isFree ? html`<button onClick=${r?.onFree} style="font-family:inherit;width:100%;border-radius:12px;padding:11px 16px;font-size:14px;font-weight:700;cursor:pointer;display:flex;justify-content:center;align-items:center;gap:8px;border:1px solid #bfe0e8;background:#eef8fa;color:#0e7c98"><i class="fa-solid fa-file-arrow-down"></i>${T(v.tx?.download)}</button>` : null}
                </div>
              `)}
            </div>
          ` : null}
        ${v.proListPager ? html`
          <div style="display:flex;align-items:center;justify-content:center;gap:12px;padding:6px 0;font-size:12.5px;color:#5a6b80"><span>${v.rangeLabel2}</span>${v.proMore ? html`<button onClick=${v.loadMorePro} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:10px;padding:6px 13px;font-size:12px;cursor:pointer">${v.tx?.loadMore}</button>` : null}</div>
          ` : null}
        </section>
      </section>
    ` : null}
`;
}
