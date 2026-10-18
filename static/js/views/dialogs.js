// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
import { html } from '../lib/html.js';
import { s, T } from '../lib/tpl.js';

export default function Dialogs(v) {
  return html`
  ${v.freeOpen ? html`
    <div style="position:fixed;inset:0;z-index:90;background:rgba(22,38,58,.45);display:grid;place-items:center;padding:16px">
      <div role="dialog" aria-modal="true" aria-label=${v.tx?.freeTitle} style="width:100%;max-width:420px;background:#fff;border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.3);padding:22px;display:flex;flex-direction:column;gap:14px;position:relative">
        <button onClick=${v.closeFree} aria-label="×" style="position:absolute;top:12px;inset-inline-end:12px;width:32px;height:32px;border-radius:50%;border:1px solid #e2e9f0;background:#fff;cursor:pointer;font-size:16px;line-height:1;color:#5a6b80">×</button>
        <div style="display:flex;align-items:center;gap:10px">${v.freeRow?.icon ? html`<span role="img" aria-label="" style="width:40px;height:40px;border-radius:10px;background-image:url('${s(v.freeRow?.icon)}');background-size:cover;background-repeat:no-repeat;background-position:center;display:block"></span>` : null}<div style="line-height:1.3"><div style="font-weight:700">${T(v.freeRow?.name)} · ${T(v.freeRow?.ticker)}</div><div style="font-size:12px;color:#5a6b80">${T(v.freeRow?.key)} · ${T(v.freeRow?.ind)}</div></div></div>
        <h2 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-.2px">${v.tx?.freeTitle}</h2>
        ${v.freeNotSent ? html`
          <p style="margin:0;color:#5a6b80;font-size:14px">${v.tx?.freeText}</p>
          <label style="display:flex;flex-direction:column;gap:5px"><span style="font-size:12px;font-weight:600;color:#5a6b80">${v.tx?.email}</span><input type="email" value=${v.freeEmail ?? ''} onInput=${v.onFreeEmail} onKeyDown=${v.freeKey} aria-invalid=${v.freeErrOn} placeholder="ana@example.com" style="font-family:inherit;font-size:14px;color:#16263a;border:1px solid ${s(v.freeBd)};border-radius:10px;padding:10px 12px" />${v.freeErrOn ? html`<span role="alert" style="font-size:12px;font-weight:600;color:#c0392b">${v.freeErr}</span>` : null}</label>
          <button type="button" onClick=${v.toggleNews} role="checkbox" aria-checked=${v.newsOn} style="font-family:inherit;line-height:inherit;color:inherit;background:none;border:0;padding:0;margin:0;width:100%;text-align:start;display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-size:13px"><span style="width:18px;height:18px;border-radius:5px;border:1.5px solid ${s(v.newsBorder)};background:${s(v.newsBg)};display:grid;place-items:center;color:#fff;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px">${v.newsCheck}</span>${T(v.tx?.newsOpt)}</button>
          <button onClick=${v.sendFree} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 22px;font-size:14.5px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22)">${v.tx?.sendLink}</button>
          ${v.legalOn ? html`<a href=${v.legalPrivacyUrl} target="_blank" rel="noopener" style="font-size:12px;color:#5a6b80;cursor:pointer">${v.tx?.legalPrivacy}</a>` : null}
          ` : null}
        ${v.freeSentNow ? html`
          <div style="display:flex;gap:10px;align-items:flex-start;background:#e8f7ef;color:#15603c;border-radius:12px;padding:12px 14px;font-size:13.5px;font-weight:600"><i class="fa-solid fa-circle-check" style="margin-top:2px"></i>${T(v.tx?.freeSent)}</div>
          <button onClick=${v.closeFree} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:11px 20px;font-size:14px;cursor:pointer">${v.tx?.backShop}</button>
          ` : null}
        </div>
      </div>
    ` : null}
  ${v.tourOpen ? html`
    <div style="position:fixed;inset:0;z-index:95;background:rgba(22,38,58,.5);display:grid;place-items:center;padding:16px">
      <div role="dialog" aria-modal="true" aria-label=${v.tx?.tourOpen} style="width:100%;max-width:480px;background:#fff;border-radius:20px;box-shadow:0 30px 80px rgba(0,0,0,.3);overflow:hidden;position:relative">${' '}
        <button onClick=${v.closeTour} title=${v.tx?.tourClose} aria-label=${v.tx?.tourClose} style="position:absolute;top:12px;inset-inline-end:12px;z-index:2;width:32px;height:32px;border-radius:50%;border:1px solid #e2e9f0;background:#fff;cursor:pointer;font-size:16px;line-height:1;color:#5a6b80">×</button>${' '}
        <div onPointerDown=${v.tourPD} onPointerUp=${v.tourPU} style="aspect-ratio:16/10;background:#f4f8fb;border-bottom:1px solid #e2e9f0;display:grid;place-items:center;overflow:hidden;cursor:pointer;touch-action:pan-y;user-select:none">
          ${v.tourS1 ? html`<div style="display:grid;grid-template-columns:repeat(3,64px);gap:14px">
              ${(v.tourIcons || []).map((ti, $index) => html`<div style="width:64px;height:64px;border-radius:16px;background:#fff;border:1px solid #e2e9f0;display:grid;place-items:center;box-shadow:0 6px 16px rgba(22,38,58,.08)"><span role="img" aria-hidden="true" style="width:34px;height:34px;border-radius:8px;display:inline-block;flex-shrink:0;background-image:url('${s(ti?.src)}');background-size:cover;background-position:center"></span></div>`)}
              </div>` : null}
          ${v.tourS2 ? html`<img src="/static/img/tour_profit.png" alt="" style="width:88%;border-radius:12px;border:1px solid #e2e9f0;box-shadow:0 10px 28px rgba(22,38,58,.12);display:block" />` : null}
          ${v.tourS3 ? html`<div style="display:flex;align-items:center;gap:16px">
              <div style="width:88px;height:64px;border-radius:16px;background:#fff;border:1px solid #e2e9f0;display:grid;place-items:center"><img src="/static/assets/icons/a_logo_paypal.png" alt="PayPal" style="max-width:64px;max-height:28px" /></div>
              <i class=${v.arrowFwd} style="color:#8d9cae"></i>
              <div style="width:64px;height:64px;border-radius:16px;background:#fff;border:1px solid #e2e9f0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;color:#0950e3;font-size:11px;font-weight:700"><i class="fa-solid fa-file-code" style="font-size:22px"></i><span dir="ltr">.pine</span></div>
              <i class=${v.arrowFwd} style="color:#8d9cae"></i>
              <div style="width:64px;height:64px;border-radius:16px;background:#fff;border:1px solid #e2e9f0;display:grid;place-items:center"><img src="/static/assets/icons/TW_ICO.svg" alt="TradingView" style="width:32px;height:32px" /></div>
              </div>` : null}
          </div>
        <div style="padding:20px 22px 18px;display:flex;flex-direction:column;gap:8px">
          <span style="font-size:12px;font-weight:700;color:#0950e3">${v.tourStepLabel}</span>
          <h2 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-.2px">${v.tourTitle}</h2>
          <p style="margin:0;font-size:14px;color:#5a6b80;text-wrap:pretty">${v.tourText}</p>
          <div style="display:flex;align-items:center;gap:10px;margin-top:10px">
            <div style="display:flex;gap:6px">${(v.tourDots || []).map((dt, $index) => html`<span style="height:8px;border-radius:999px;width:${s(dt?.w)};background:${s(dt?.bg)};transition:width .3s"></span>`)}</div>
            <div style="margin-inline-start:auto;display:flex;gap:8px">
              ${v.tourHasBack ? html`<button onClick=${v.tourBack} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:10px 16px;font-size:14px;cursor:pointer">${v.tx?.tourBack}</button>` : null}
              <button onClick=${v.tourNext} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:10px 18px;font-size:14px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22)">${v.tourNextLabel}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    ` : null}
  ${v.instOpen ? html`
    <div style="position:fixed;inset:0;z-index:96;background:rgba(22,38,58,.5);display:grid;place-items:center;padding:16px">
      <div role="dialog" aria-modal="true" aria-label=${v.instTourTitle} style="width:100%;max-width:480px;max-height:calc(100vh - 32px);overflow:auto;background:#fff;border-radius:20px;box-shadow:0 30px 80px rgba(0,0,0,.3);position:relative">${' '}
        <button onClick=${v.closeInst} title=${v.tx?.tourClose} aria-label=${v.tx?.tourClose} style="position:absolute;top:12px;inset-inline-end:12px;z-index:2;width:32px;height:32px;border-radius:50%;border:1px solid #e2e9f0;background:#fff;cursor:pointer;font-size:16px;line-height:1;color:#5a6b80">×</button>${' '}
        <div onPointerDown=${v.instPD} onPointerUp=${v.instPU} style="position:relative;aspect-ratio:16/10;background:#f4f8fb;border-bottom:1px solid #e2e9f0;overflow:hidden;container-type:inline-size;cursor:pointer;touch-action:pan-y;user-select:none">${' '}
          ${v.inst1 ? html`<div style="position:absolute;inset:0;padding:6cqw 8cqw;display:flex;flex-direction:column;justify-content:center;gap:5cqw">
              <div style="background:#fff;border:1px solid #e2e9f0;border-radius:2.6cqw;box-shadow:0 1.6cqw 4cqw rgba(22,38,58,.08);padding:2.6cqw 3cqw;display:flex;align-items:center;gap:2.4cqw">
                <span style="width:7cqw;height:7cqw;border-radius:1.6cqw;flex-shrink:0;background-image:url('${s(v.instIcon)}');background-size:cover;background-position:center"></span>
                <span style="flex:1;min-width:0;display:flex;flex-direction:column;gap:1.2cqw"><strong dir="auto" style="font-size:3cqw;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${v.instName}</strong><span style="height:1.4cqw;width:60%;border-radius:1cqw;background:#e2e9f0"></span></span>
                <span style="position:relative;flex-shrink:0;border:1px solid #e2e9f0;background:#fff;border-radius:1.8cqw;padding:1.4cqw 2.4cqw;font-size:2.8cqw;font-weight:700;display:inline-flex;gap:1.2cqw;align-items:center;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)"><i class="fa-solid fa-file-code" style="color:#0950e3"></i><span dir="ltr">.pine</span><i class="fa-solid fa-hand-pointer" style="position:absolute;right:-1.6cqw;bottom:-4.4cqw;font-size:4.4cqw;color:#16263a;text-shadow:0 0 0.6cqw #fff"></i></span>
                <span style="flex-shrink:0;border:1px solid #e2e9f0;background:#fff;border-radius:1.8cqw;padding:1.4cqw 2.4cqw;font-size:2.8cqw;font-weight:700;display:inline-flex;gap:1.2cqw;align-items:center;color:#5a6b80"><i class="fa-solid fa-file-zipper"></i>.zip</span>
                </div>
              <div style="display:flex;gap:3cqw;align-items:center">
                <div style="flex:1;min-width:0;background:#fff;border:1px solid #e2e9f0;border-radius:2.6cqw;box-shadow:0 1.6cqw 4cqw rgba(22,38,58,.08);overflow:hidden">
                  <div style="height:5.4cqw;background:#eef3f8;display:flex;align-items:center;gap:1.2cqw;padding:0 2.4cqw;font-size:2.2cqw;color:#5a6b80;white-space:nowrap;overflow:hidden"><i class="fa-regular fa-file-lines"></i><span dir="ltr" style="overflow:hidden;text-overflow:ellipsis">${v.instFile}</span></div>
                  <div style="padding:2.4cqw 3cqw;display:flex;flex-direction:column;gap:1.4cqw;background:rgba(9,80,227,.08)"><span style="height:1.5cqw;width:50%;border-radius:1cqw;background:#9db9f3"></span><span style="height:1.5cqw;width:80%;border-radius:1cqw;background:#9db9f3"></span><span style="height:1.5cqw;width:66%;border-radius:1cqw;background:#9db9f3"></span><span style="height:1.5cqw;width:38%;border-radius:1cqw;background:#9db9f3"></span></div>
                  </div>
                <div style="flex-shrink:0;display:flex;flex-direction:column;gap:2.4cqw;font-size:2.6cqw;font-weight:700;color:#5a6b80">
                  <span style="display:inline-flex;gap:1cqw;align-items:center;direction:ltr"><kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">Ctrl</kbd>+<kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">A</kbd></span>
                  <span style="display:inline-flex;gap:1cqw;align-items:center;direction:ltr"><kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">Ctrl</kbd>+<kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">C</kbd></span>
                  </div>
                </div>
              </div>` : null}${' '}
          ${v.inst2 ? html`<div style="position:absolute;inset:5cqw 9cqw;background:#fff;border:1px solid #e2e9f0;border-radius:2.6cqw;box-shadow:0 1.6cqw 4cqw rgba(22,38,58,.08);overflow:hidden;display:flex;flex-direction:column">
              <div style="height:6.4cqw;flex-shrink:0;background:#eef3f8;display:flex;align-items:center;gap:1.2cqw;padding:0 2.4cqw">
                <span style="width:1.4cqw;height:1.4cqw;border-radius:50%;background:#cfd8e3"></span><span style="width:1.4cqw;height:1.4cqw;border-radius:50%;background:#cfd8e3"></span><span style="width:1.4cqw;height:1.4cqw;border-radius:50%;background:#cfd8e3"></span>
                <span style="flex:1;height:3.8cqw;border-radius:2cqw;background:#fff;display:flex;align-items:center;gap:1.2cqw;padding:0 2cqw;font-size:2.4cqw;color:#5a6b80;direction:ltr"><i class="fa-solid fa-lock" style="font-size:2cqw;color:#15803d"></i>tradingview.com</span>
                </div>
              <div style="flex:1;display:grid;place-items:center">
                <div style="width:52%;display:flex;flex-direction:column;align-items:center;gap:2.2cqw">
                  <img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:7cqw;height:7cqw;display:block" />
                  <span style="width:100%;height:4.8cqw;border-radius:1.4cqw;border:1px solid #e2e9f0;background:#f8fafc;display:flex;align-items:center;gap:1.4cqw;padding:0 1.8cqw;font-size:2.4cqw;color:#8d9cae"><i class="fa-regular fa-envelope"></i><span style="height:1.2cqw;width:45%;border-radius:1cqw;background:#e2e9f0"></span></span>
                  <span style="width:100%;height:4.8cqw;border-radius:1.4cqw;border:1px solid #e2e9f0;background:#f8fafc;display:flex;align-items:center;gap:1.4cqw;padding:0 1.8cqw;font-size:2.4cqw;color:#8d9cae;letter-spacing:0.4cqw"><i class="fa-solid fa-key" style="letter-spacing:0"></i>••••••</span>
                  <span style="position:relative;width:100%;display:flex;gap:2cqw;border-radius:1.6cqw;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)">
                    <span style="flex:1;height:5.2cqw;border-radius:1.4cqw;background:#16263a;color:#fff;display:grid;place-items:center;font-size:2.8cqw"><i class="fa-solid fa-right-to-bracket"></i></span>
                    <span style="flex:1;height:5.2cqw;border-radius:1.4cqw;border:1px solid #16263a;background:#fff;color:#16263a;display:grid;place-items:center;font-size:2.8cqw"><i class="fa-solid fa-user-plus"></i></span>
                    <i class="fa-solid fa-hand-pointer" style="position:absolute;right:-1.6cqw;bottom:-4.4cqw;font-size:4.4cqw;color:#16263a;text-shadow:0 0 0.6cqw #fff"></i>
                    </span>
                  </div>
                </div>
              </div>` : null}${' '}
          ${v.inst3 ? html`<div style="position:absolute;inset:0;direction:ltr;background-color:#fff;background-image:url('${s(v.instCandle)}');background-size:300% auto;background-position:0 0;background-repeat:no-repeat">${' '}
              <span style="position:absolute;top:0.3cqw;left:0.4cqw;width:62cqw;height:5.6cqw;border-radius:1.4cqw;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)"></span>${' '}
              <span style="position:absolute;top:9.5cqw;left:3cqw;background:#0950e3;color:#fff;font-size:2.8cqw;font-weight:700;border-radius:1.4cqw;padding:1.2cqw 2.2cqw;display:inline-flex;gap:1.4cqw;align-items:center;box-shadow:0 1.2cqw 3cqw rgba(9,80,227,.3)"><i class="fa-solid fa-magnifying-glass"></i>${T(v.instSym)} · ${T(v.instInt)}</span>${' '}
              </div>` : null}${' '}
          ${v.inst4 ? html`<div style="position:absolute;inset:0;display:flex;direction:ltr">
              <div style="flex:1;min-width:0;position:relative;background-color:#fff;background-image:url('${s(v.instCandle)}');background-size:260% auto;background-position:0 40%;background-repeat:no-repeat"><span style="position:absolute;inset:0;background:rgba(244,248,251,.5)"></span></div>
              <div style="width:44cqw;flex-shrink:0;background:#fff;border-left:1px solid #e2e9f0;display:flex;flex-direction:column;box-shadow:-1.6cqw 0 4cqw rgba(22,38,58,.08)">
                <div style="display:flex;align-items:center;gap:1.4cqw;padding:2cqw 2.2cqw;border-bottom:1px solid #e2e9f0">
                  <span style="font-size:2.5cqw;font-weight:700;display:inline-flex;gap:1cqw;align-items:center;white-space:nowrap"><i class="fa-solid fa-code" style="color:#0950e3"></i>Pine Editor</span>
                  <span style="position:relative;margin-left:auto;font-size:2.4cqw;font-weight:700;border-radius:1.2cqw;padding:1cqw 2cqw;background:#0950e3;color:#fff;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)">Save<span style="position:absolute;left:-5.4cqw;top:50%;transform:translateY(-50%);width:3.8cqw;height:3.8cqw;border-radius:50%;background:#16263a;color:#fff;font-size:2.2cqw;font-weight:700;display:grid;place-items:center;font-style:normal">3</span></span>
                  </div>
                <div style="flex:1;display:flex;gap:1.8cqw;padding:2.2cqw;background:rgba(9,80,227,.04);overflow:hidden">
                  <div style="display:flex;flex-direction:column;gap:1.6cqw;font-size:1.9cqw;line-height:1.5cqw;color:#8d9cae;text-align:right"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span></div>
                  <div style="flex:1;display:flex;flex-direction:column;gap:1.6cqw;opacity:.6"><span style="height:1.5cqw;width:38%;border-radius:1cqw;background:#0950e3"></span><span style="height:1.5cqw;width:72%;border-radius:1cqw;background:#9aa7b8"></span><span style="height:1.5cqw;width:56%;border-radius:1cqw;background:#15803d"></span><span style="height:1.5cqw;width:84%;border-radius:1cqw;background:#9aa7b8"></span><span style="height:1.5cqw;width:30%;border-radius:1cqw;background:#c0392b"></span><span style="height:1.5cqw;width:64%;border-radius:1cqw;background:#9aa7b8"></span><span style="height:1.5cqw;width:48%;border-radius:1cqw;background:#0e7c98"></span><span style="height:1.5cqw;width:70%;border-radius:1cqw;background:#9aa7b8"></span></div>
                  </div>
                <div style="padding:1.8cqw 2.2cqw;border-top:1px solid #e2e9f0;display:flex;justify-content:flex-end;align-items:center;gap:1cqw;font-size:2.6cqw;font-weight:700;color:#5a6b80"><span style="position:relative;width:3.8cqw;height:3.8cqw;margin-right:1cqw"><span style="position:absolute;left:0;top:0;width:3.8cqw;height:3.8cqw;border-radius:50%;background:#16263a;color:#fff;font-size:2.2cqw;font-weight:700;display:grid;place-items:center;font-style:normal">2</span></span><kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">Ctrl</kbd>+<kbd style="font-family:inherit;font-size:2.6cqw;font-weight:700;color:#16263a;border:1px solid #cfd8e3;border-bottom-width:0.6cqw;border-radius:1.2cqw;background:#fff;padding:0.6cqw 1.4cqw;line-height:1.2">V</kbd></div>
                </div>
              <div style="width:6cqw;flex-shrink:0;background:#fff;border-left:1px solid #e2e9f0;display:flex;flex-direction:column;align-items:center;gap:3cqw;padding-top:3cqw;font-size:2.6cqw;color:#8d9cae">
                <i class="fa-regular fa-star"></i><i class="fa-regular fa-clock"></i>
                <span style="position:relative;width:4.4cqw;height:4.4cqw;border-radius:1.2cqw;background:#e9f0fd;color:#0950e3;display:grid;place-items:center;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)"><i class="fa-solid fa-code"></i><span style="position:absolute;left:-5.6cqw;top:50%;transform:translateY(-50%);width:3.8cqw;height:3.8cqw;border-radius:50%;background:#16263a;color:#fff;font-size:2.2cqw;font-weight:700;display:grid;place-items:center;font-style:normal">1</span></span>
                <i class="fa-regular fa-bell"></i><i class="fa-regular fa-comment"></i>
                </div>
              </div>` : null}${' '}
          ${v.inst5 ? html`<div style="position:absolute;inset:0;display:flex;flex-direction:column;direction:ltr">
              <div style="flex:1;position:relative;background-color:#fff;background-image:url('${s(v.instCandle)}');background-size:200% auto;background-position:0 30%;background-repeat:no-repeat">${' '}
                <span style="position:absolute;top:2.6cqw;right:3.4cqw;font-size:2.6cqw;font-weight:700;border-radius:1.4cqw;padding:1.2cqw 2.2cqw;background:#fff;color:#16263a;border:1px solid #e2e9f0;display:inline-flex;gap:1.2cqw;align-items:center;box-shadow:0 0 0 0.5cqw #0950e3,0 0 0 1.8cqw rgba(9,80,227,.2)"><i class="fa-solid fa-chart-line" style="color:#0950e3"></i>Add to chart<i class="fa-solid fa-hand-pointer" style="position:absolute;right:-1.6cqw;bottom:-4.4cqw;font-size:4.4cqw;color:#16263a;text-shadow:0 0 0.6cqw #fff"></i></span>${' '}
                </div>
              <div style="height:27cqw;flex-shrink:0;position:relative;border-top:2px solid #16263a;background-color:#fff;background-image:url('${s(v.instProfit)}');background-size:150% auto;background-position:0 0;background-repeat:no-repeat">${' '}
                <span style="position:absolute;bottom:100%;left:3cqw;font-size:2.2cqw;font-weight:700;background:#16263a;color:#fff;border-radius:1cqw 1cqw 0 0;padding:0.8cqw 1.8cqw">Strategy Tester</span>${' '}
                </div>
              </div>` : null}${' '}
          </div>
        <div style="padding:20px 22px 18px;display:flex;flex-direction:column;gap:8px">
          <span style="font-size:12px;font-weight:700;color:#0950e3;display:flex;gap:6px;align-items:center;flex-wrap:wrap"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:14px;height:14px" />${T(v.instTourTitle)} · ${T(v.instStepLabel)}</span>
          <h2 style="margin:0;font-size:20px;font-weight:700;letter-spacing:-.2px">${v.instTitle}</h2>
          <p style="margin:0;font-size:14px;color:#5a6b80;text-wrap:pretty">${v.instText}</p>
          ${v.inst3 ? html`<a class="sf-hover13" href=${v.instChartUrl} target="_blank" rel="noopener" style="align-self:flex-start;display:inline-flex;gap:8px;align-items:center;font-weight:700;font-size:13.5px;border:1px solid #c5d6f8;background:#f5f8ff;border-radius:10px;padding:8px 12px;text-decoration:none"><img src="/static/assets/icons/TW_ICO.svg" alt="" style="width:16px;height:16px" />${T(v.instTvLabel)}<i class="fa-solid fa-arrow-up-right-from-square" style="font-size:11px"></i></a>` : null}
          <div style="display:flex;align-items:center;gap:10px;margin-top:10px">
            <div style="display:flex;gap:2px">${(v.instDots || []).map((dt, $index) => html`<button onClick=${dt?.go} aria-label=${dt?.label} title=${dt?.label} style="border:none;background:none;padding:10px 2px;cursor:pointer;display:block"><span style="display:block;height:8px;border-radius:999px;width:${s(dt?.w)};background:${s(dt?.bg)};transition:width .3s"></span></button>`)}</div>
            <div style="margin-inline-start:auto;display:flex;gap:8px">
              ${v.instHasBack ? html`<button onClick=${v.instBack} style="font-family:inherit;background:#fff;border:1px solid #e2e9f0;color:#16263a;font-weight:600;border-radius:12px;padding:10px 16px;font-size:14px;cursor:pointer">${v.tx?.tourBack}</button>` : null}
              <button onClick=${v.instNext} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:10px 18px;font-size:14px;cursor:pointer;box-shadow:0 8px 20px rgba(9,80,227,.22)">${v.instNextLabel}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    ` : null}
  ${v.cmpFloat ? html`<button onClick=${v.openCmp} style="position:fixed;bottom:${s(v.cmpBottom)};inset-inline-start:16px;z-index:30;font-family:inherit;border:none;border-radius:999px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer;background:#16263a;color:#fff;box-shadow:0 12px 30px rgba(22,38,58,.3);display:inline-flex;gap:8px;align-items:center"><i class="fa-solid fa-code-compare"></i>${T(v.tx?.compare)} · ${T(v.cmpCount)}</button>` : null}
  ${v.cmpOpen ? html`
    <div style="position:fixed;inset:0;z-index:90;background:rgba(22,38,58,.45);display:grid;place-items:center;padding:16px">
      <div role="dialog" aria-modal="true" aria-label=${v.tx?.compareTitle} style="width:100%;max-width:760px;max-height:90vh;overflow:auto;background:#fff;border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.3);padding:20px;display:flex;flex-direction:column;gap:14px;position:relative">
        <button onClick=${v.closeCmp} aria-label="×" style="position:absolute;top:12px;inset-inline-end:12px;width:32px;height:32px;border-radius:50%;border:1px solid #e2e9f0;background:#fff;cursor:pointer;font-size:16px;line-height:1;color:#5a6b80">×</button>
        <div><h2 style="margin:0;font-size:20px;font-weight:700">${v.tx?.compareTitle}</h2><span style="font-size:12.5px;color:#5a6b80">${v.tx?.compareMax}</span></div>
        <div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr><th style="padding:8px 10px;border-bottom:1px solid #e2e9f0"></th>${(v.cmpCols || []).map((cc, $index) => html`<th style="padding:8px 10px;border-bottom:1px solid #e2e9f0;white-space:nowrap"><span style="display:inline-flex;gap:6px;align-items:center"><span role="img" aria-hidden="true" style="width:22px;height:22px;border-radius:6px;display:inline-block;flex-shrink:0;background-image:url('${s(cc?.icon)}');background-size:cover;background-position:center"></span>${T(cc?.ticker)} · ${T(cc?.key)}</span><button onClick=${cc?.remove} aria-label="×" style="margin-inline-start:6px;border:none;background:none;color:#8d9cae;cursor:pointer">×</button></th>`)}</tr>
            ${(v.cmpRows || []).map((cr, $index) => html`<tr><td style="padding:8px 10px;color:#5a6b80;border-bottom:1px solid #e2e9f0;white-space:nowrap">${cr?.label}</td>${(cr?.cells || []).map((ce, $index) => html`<td style="padding:8px 10px;text-align:center;border-bottom:1px solid #e2e9f0;font-variant-numeric:tabular-nums;font-weight:${s(ce?.weight)};color:${s(ce?.color)};background:${s(ce?.bg)}">${ce?.value}</td>`)}</tr>`)}
            </table></div>
        </div>
      </div>
    ` : null}
  ${v.packOpen ? html`
    <div style="position:fixed;inset:0;z-index:90;background:rgba(22,38,58,.45);display:grid;place-items:center;padding:16px">
      <div role="dialog" aria-modal="true" aria-label=${v.tx?.packTitle} style="width:100%;max-width:460px;max-height:90vh;overflow:hidden;background:#fff;border-radius:18px;box-shadow:0 30px 80px rgba(0,0,0,.3);padding:20px;display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:10px"><h2 style="margin:0;font-size:20px;font-weight:700">${v.tx?.packTitle}</h2><span dir="ltr" style="font-size:13px;font-weight:700;color:#0950e3">${T(v.packCount)} / ${T(v.packSize)}</span></div>
        <label style="display:flex;align-items:center;gap:8px;border:1px solid #e2e9f0;border-radius:9px;padding:6px 9px"><i class="fa-solid fa-magnifying-glass" style="color:#8d9cae;font-size:11px"></i><input value=${v.packQ ?? ''} onInput=${v.onPackQ} placeholder=${v.tx?.searchSmall} style="flex:1;min-width:0;border:none;outline:none;font-family:inherit;font-size:13px;color:#16263a;background:transparent" /></label>
        <div style="flex:1 1 auto;min-height:0;overflow:auto;display:flex;flex-direction:column;gap:12px">${(v.packList || []).map((pl, $index) => html`<button onClick=${pl?.toggle} disabled=${pl?.locked} style="display:flex;align-items:center;gap:10px;border:1px solid ${s(pl?.bd)};background:${s(pl?.bg)};border-radius:12px;padding:8px 10px;cursor:${s(pl?.cursor)};font-family:inherit;text-align:start;color:#16263a"><span style="width:18px;height:18px;border-radius:5px;border:1.5px solid ${s(pl?.ck)};background:${s(pl?.ckBg)};display:grid;place-items:center;color:#fff;font-size:11px;font-weight:700;flex-shrink:0">${pl?.check}</span><span role="img" aria-hidden="true" style="width:26px;height:26px;border-radius:7px;display:inline-block;flex-shrink:0;background-image:url('${s(pl?.icon)}');background-size:cover;background-position:center"></span><span style="flex:1;min-width:0"><strong>${T(pl?.ticker)} · ${T(pl?.key)}</strong><span dir="auto" style="display:block;font-size:12px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${pl?.ind}</span></span>${pl?.held ? html`<span style="border-radius:999px;padding:3px 9px;font-size:11.5px;font-weight:700;display:inline-flex;gap:5px;align-items:center;white-space:nowrap;border:1px solid #c5d6f8;background:#e9f0fd;color:#0950e3"><i class="fa-solid fa-check"></i>${T(v.tx?.inCartBtn)}</span>` : html`<span style="font-size:12.5px;font-weight:700;color:#15803d">${pl?.nppSigned}</span>`}</button>`)}</div>
        <button onClick=${v.closePack} style="font-family:inherit;background:linear-gradient(135deg,#0950e3,#0e7c98);border:none;color:#fff;font-weight:700;border-radius:12px;padding:12px 22px;font-size:14.5px;cursor:pointer">${v.tx?.done}</button>
        </div>
      </div>
    ` : null}
  ${v.errOpen ? html`<div role="alert" style="position:fixed;inset-inline:16px;bottom:${s(v.errBottom)};z-index:99;max-width:480px;margin-inline:auto;background:#16263a;color:#fff;border-radius:12px;padding:10px 12px;font-size:12.5px;line-height:1.45;box-shadow:0 12px 30px rgba(22,38,58,.3);display:flex;gap:10px;align-items:flex-start"><i class="fa-solid fa-triangle-exclamation" style="color:#f79009;margin-top:2px"></i><span style="flex:1;display:flex;flex-direction:column;gap:2px"><strong>${v.errTitle}</strong><span>${v.errText}</span></span><button onClick=${v.closeErr} aria-label="×" style="border:none;background:none;color:#fff;cursor:pointer;font-size:16px;line-height:1;padding:0">×</button></div>` : null}
  ${v.noticeOpen ? html`<div role="status" style="position:fixed;inset-inline:16px;bottom:${s(v.noticeBottom)};z-index:98;max-width:480px;margin-inline:auto;background:#16263a;color:#fff;border-radius:12px;padding:10px 12px;font-size:12.5px;line-height:1.45;box-shadow:0 12px 30px rgba(22,38,58,.3);display:flex;gap:10px;align-items:flex-start"><i class=${v.noticeIcon} style="color:${s(v.noticeColor)};margin-top:2px"></i><span style="flex:1;display:flex;flex-direction:column;gap:2px"><strong>${v.noticeTitle}</strong><span>${v.noticeText}</span></span><button onClick=${v.closeNotice} aria-label="×" style="border:none;background:none;color:#fff;cursor:pointer;font-size:16px;line-height:1;padding:0">×</button></div>` : null}
`;
}
