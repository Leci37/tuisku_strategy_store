// Markup and styles ported one to one from docs/design/Strategy Tree.dc.html (the v7 reference design).
// Changed for real data: the forest badge becomes one button per tree for an owner, and the Owner
// switch explains how to sign in or buy when this browser has no purchase to show. Sliders stay
// left-to-right in Arabic, as the coloured zones above them are drawn from the left.
import { html } from '../../lib/html.js';
import { s, T } from '../../lib/tpl.js';

export default function TreeMain(v) {
  return html`
  <section style="max-width:1320px;margin:0 auto;padding:${s(v.mainPad)};display:flex;flex-direction:column;gap:20px">
    ${v.standalone ? html`
      <div style="max-width:820px;display:flex;flex-direction:column;gap:6px">
        <h1 style="margin:0;font-size:30px;font-weight:700;letter-spacing:-.5px">${v.L?.h1}</h1>
        <p style="margin:0;color:#5a6b80;font-size:15px;text-wrap:pretty">${v.L?.intro}</p>
        </div>
      <div style="display:flex;flex-wrap:wrap;gap:10px">
        ${(v.picks || []).map((p, $index) => html`
          <button onClick=${p?.pick} style="font-family:inherit;display:flex;align-items:center;gap:10px;border:1.5px solid ${s(p?.bd)};background:${s(p?.bg)};border-radius:14px;padding:8px 14px 8px 8px;cursor:pointer;text-align:start;color:#16263a">
            <span role="img" aria-hidden="true" style="width:30px;height:30px;border-radius:8px;flex-shrink:0;background-image:url('${s(p?.icon)}');background-size:cover;background-position:center"></span>
            <span style="line-height:1.25"><strong style="display:block;font-size:13.5px;color:${s(p?.color)}">${T(p?.ticker)} · ${T(p?.pattern)}</strong><span style="font-size:11.5px;color:#5a6b80">${T(p?.key)} · 1Day · ${T(p?.status)}</span></span>
            </button>
          `)}
        </div>
      ` : null}
    <div style="display:flex;flex-direction:column;gap:8px">
      <div style="display:flex;flex-wrap:wrap;gap:10px">${(v.steps || []).map((st, $index) => html`<div style="flex:1 1 220px;display:flex;gap:10px;align-items:flex-start;background:#ffffff;border:1px solid #e2e9f0;border-radius:14px;padding:12px 14px"><span style="width:24px;height:24px;border-radius:7px;background:#16263a;color:#ffffff;display:grid;place-items:center;font-size:12px;font-weight:700;flex-shrink:0">${st?.n}</span><span style="font-size:13.5px;text-wrap:pretty">${st?.text}</span></div>`)}</div>
      <span style="font-size:12.5px;color:#5a6b80;text-wrap:pretty">${v.L?.forest}</span>
      </div>
    ${v.loading ? html`<p style="margin:0;color:#8d9cae">${v.L?.loading}</p>` : null}
    ${v.hasErr ? html`<p style="margin:0;color:#c0392b">${T(v.L?.loadErr)} ${T(v.err)}</p>` : null}
    ${v.ready ? html`
      <div style="display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start">
        <aside style="flex:1 1 280px;min-width:0;display:flex;flex-direction:column;gap:16px;position:${s(v.asidePos)};top:16px">
          <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column;gap:12px">
            <span style="font-size:11px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#5a6b80">${v.L?.output}</span>
            <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap"><strong style="font-size:30px;font-weight:700;letter-spacing:-.5px;line-height:1.1;color:${s(v.sigColor)}">${v.sigLabel}</strong><span style="font-size:16px;font-weight:600;font-variant-numeric:tabular-nums;color:${s(v.sigColor)}">${v.sigValue}</span></div>
            <div style="display:flex;flex-direction:column;gap:4px">
              <div style="position:relative;height:8px;border-radius:999px;background:linear-gradient(90deg,#f3c1bb,#e2e9f0 50%,#b7e4c7)">${' '}
                ${v.hasMarker ? html`<span style="position:absolute;top:-4px;left:${s(v.markerLeft)};width:4px;height:16px;margin-left:-2px;border-radius:2px;background:#16263a"></span>` : null}${' '}
                </div>
              <div style="display:flex;justify-content:space-between;font-size:11px;color:#5a6b80"><span>${v.L?.sellEnd}</span><span>0</span><span>${v.L?.buyEnd}</span></div>
              </div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center">
              ${(v.pathChips || []).map((c, $index) => html`<span style="font-size:12px;font-weight:600;background:#e9f0fd;color:#0950e3;border-radius:999px;padding:3px 9px">${c?.text}</span>`)}
              </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <button onClick=${v.buyExample} style="font-family:inherit;border:1px solid #b7e4c7;background:#e8f7ef;color:#15803d;font-weight:700;border-radius:10px;padding:8px 12px;font-size:12.5px;cursor:pointer">${v.L?.buyEx}</button>
              <button onClick=${v.sellExample} style="font-family:inherit;border:1px solid #f3c1bb;background:#fdecea;color:#c0392b;font-weight:700;border-radius:10px;padding:8px 12px;font-size:12.5px;cursor:pointer">${v.L?.sellEx}</button>
              </div>
            <span style="font-size:11.5px;color:#8d9cae;margin-top:-4px">${v.L?.exHelp}</span>
            </div>
          <div style="background:#fff;border:1px solid #e2e9f0;border-radius:18px;padding:16px 18px;display:flex;flex-direction:column;gap:14px">
            <span style="font-size:11px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:#5a6b80">${v.L?.values}</span>
            <div style="display:flex;flex-direction:column;gap:8px;margin-top:-4px">
              <div style="display:flex;gap:10px;align-items:flex-start;background:#f5f8ff;border:1px solid #d6e2fb;border-radius:12px;padding:10px 12px"><i class="fa-solid fa-circle-check" style="color:#0950e3;margin-top:2px"></i><span style="display:flex;flex-direction:column;gap:2px"><strong style="font-size:12.5px">${v.L?.optTitle}</strong><span style="font-size:12px;color:#5a6b80;text-wrap:pretty">${v.L?.optText}</span></span></div>
              <div style="display:flex;flex-wrap:wrap;gap:6px 12px;font-size:11.5px;color:#5a6b80"><span style="display:inline-flex;align-items:center;gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:#15803d"></span>${T(v.L?.zBuy)}</span><span style="display:inline-flex;align-items:center;gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:#c0392b"></span>${T(v.L?.zSell)}</span><span style="display:inline-flex;align-items:center;gap:6px"><span style="width:14px;height:8px;border-radius:2px;background:#9aa7b8"></span>${T(v.L?.zWait)}</span><span style="display:inline-flex;align-items:center;gap:6px"><span style="width:2px;height:12px;border-radius:1px;background:#0950e3"></span>${T(v.L?.zNotch)}</span></div>
              <span style="font-size:11.5px;color:#8d9cae;text-wrap:pretty">${v.L?.zHelp}</span>
              </div>
            ${(v.feats || []).map((f, $index) => html`
              <div style="display:flex;flex-direction:column;gap:3px">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:8px"><span style="display:inline-flex;align-items:center;gap:6px;min-width:0"><button onClick=${f?.onInfo} onMouseEnter=${f?.onEnter} onMouseLeave=${f?.onLeave} style="font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;font-weight:600;color:${s(f?.nameColor)};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;border:none;background:none;padding:0;cursor:help;text-decoration:underline dotted #9aa7b8;text-underline-offset:3px">${f?.name}</button><button onClick=${f?.onInfo} aria-label="What is ${s(f?.full)}?" style="width:18px;height:18px;border-radius:50%;border:1px solid #cfd8e3;background:#ffffff;color:#5a6b80;font-size:11px;font-weight:700;cursor:pointer;display:grid;place-items:center;padding:0;flex-shrink:0;font-family:Georgia,serif;font-style:italic">i</button></span><span style="font-size:13px;font-weight:700;font-variant-numeric:tabular-nums">${f?.valueLabel}</span></div><span style="font-size:11.5px;color:#5a6b80;line-height:1.3">${f?.label}</span>
                ${f?.isNum ? html`
                  <div style="position:relative;height:14px">${' '}
                    <span style="position:absolute;left:8px;right:8px;top:5px;height:4px;border-radius:2px;background:#e2e9f0"></span>${' '}
                    ${(f?.zones || []).map((z, $index) => html`<span style="position:absolute;left:${s(z?.l)};width:${s(z?.w)};top:3px;height:8px;border-radius:2px;background:${s(z?.c)};opacity:${s(z?.op)};box-shadow:${s(z?.ring)}"></span>`)}${' '}
                    ${(f?.ticks || []).map((tk, $index) => html`<span onMouseEnter=${tk?.onEnter} onMouseLeave=${tk?.onLeave} style="position:absolute;left:${s(tk?.left)};top:-3px;width:12px;height:20px;margin-left:-6px;display:flex;justify-content:center;align-items:center;cursor:help"><span style="width:2px;height:${s(tk?.h)};border-radius:1px;background:${s(tk?.bg)}"></span></span>`)}${' '}
                    </div>
                  <input type="range" dir="ltr" min=${f?.min} max=${f?.max} step="any" value=${f?.value ?? ''} onInput=${f?.onChange} aria-label=${f?.full} style="width:100%;margin:0;accent-color:#0950e3;cursor:pointer" />
                  ` : null}
                ${f?.isBool ? html`
                  <div style="display:flex;background:#e9eef4;border-radius:10px;padding:3px;align-self:flex-start">
                    <button onClick=${f?.setNo} style="font-family:inherit;border:none;border-radius:8px;padding:5px 14px;font-size:12.5px;font-weight:700;cursor:pointer;background:${s(f?.noBg)};color:${s(f?.noColor)}">${v.L?.no}</button>
                    <button onClick=${f?.setYes} style="font-family:inherit;border:none;border-radius:8px;padding:5px 14px;font-size:12.5px;font-weight:700;cursor:pointer;background:${s(f?.yesBg)};color:${s(f?.yesColor)}">${v.L?.yes}</button>
                    </div>
                  ` : null}
                </div>
              `)}
            ${v.hasUnused ? html`<p style="margin:0;font-size:12px;color:#8d9cae;text-wrap:pretty">${T(v.L?.unused)} ${T(v.unused)}</p>` : null}
            </div>
          </aside>
        <section data-tree-sec="1" style="flex:999 1 480px;min-width:0;background:#fff;border:1px solid #e2e9f0;border-radius:18px;overflow:hidden;display:flex;flex-direction:column">
          <div style="padding:16px 18px 10px;display:flex;flex-wrap:wrap;gap:10px 16px;align-items:flex-start">
            <div style="flex:1 1 280px;min-width:0;display:flex;flex-direction:column;gap:2px">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><strong dir="auto" style="font-size:18px">${v.title}</strong>${v.hasForest ? (v.forestPicks || []).map(fp => html`<button onClick=${fp?.pick} style="font-family:inherit;border:none;cursor:pointer;font-size:11.5px;font-weight:700;color:${s(fp?.color)};background:${s(fp?.bg)};border-radius:999px;padding:2px 9px">${fp?.text}</button>`) : html`<span style="font-size:11.5px;font-weight:700;color:#0950e3;background:#e9f0fd;border-radius:999px;padding:2px 9px">${v.treeBadge}</span>`}</div>
              <span style="font-size:12.5px;color:#5a6b80">${v.summary}</span>
              <span dir="auto" style="font-size:13px;color:#16263a;text-wrap:pretty;margin-top:4px;max-width:640px">${v.about}</span>
              <span style="font-size:11px;color:#8d9cae;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere">${v.params}</span>
              </div>
            <div role="tablist" style="display:flex;background:#e9eef4;border-radius:10px;padding:3px">
              <button role="tab" onClick=${v.showTree} style="font-family:inherit;border:none;border-radius:8px;padding:6px 14px;font-size:13px;font-weight:600;cursor:pointer;background:${s(v.tBg)};color:${s(v.tColor)};box-shadow:${s(v.tShadow)}">${v.L?.treeTab}</button>
              <button role="tab" onClick=${v.showRules} style="font-family:inherit;border:none;border-radius:8px;padding:6px 14px;font-size:13px;font-weight:600;cursor:pointer;background:${s(v.rBg)};color:${s(v.rColor)};box-shadow:${s(v.rShadow)}">${v.L?.rulesTab}</button>
              </div>
            <div style="display:flex;background:#e9eef4;border-radius:10px;padding:3px"><button onClick=${v.asVisitor} style="font-family:inherit;border:none;border-radius:8px;padding:6px 12px;font-size:13px;font-weight:600;cursor:pointer;background:${s(v.vBg)};color:${s(v.vColor)};box-shadow:${s(v.vShadow)}">${v.L?.visitor}</button><button onClick=${v.asOwner} style="font-family:inherit;border:none;border-radius:8px;padding:6px 12px;font-size:13px;font-weight:600;cursor:pointer;background:${s(v.oBg)};color:${s(v.oColor)};box-shadow:${s(v.oShadow)}">${v.L?.owner}</button></div>
            </div>
          <div style="padding:0 18px 12px;display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12px;color:#5a6b80">
            <span style="display:inline-flex;align-items:center;gap:6px"><span style="width:12px;height:12px;border-radius:3px;background:#e8f7ef;border:1px solid #b7e4c7"></span>${T(v.L?.buy)}</span>
            <span style="display:inline-flex;align-items:center;gap:6px"><span style="width:12px;height:12px;border-radius:3px;background:#fdecea;border:1px solid #f3c1bb"></span>${T(v.L?.sell)}</span>
            <span style="display:inline-flex;align-items:center;gap:6px"><span style="width:12px;height:12px;border-radius:3px;background:#f4f8fb;border:1px solid #cfd8e3"></span>${T(v.L?.none)}</span>
            <span style="display:inline-flex;align-items:center;gap:6px"><span style="width:12px;height:12px;border-radius:3px;background:#f4f8fb;border:1px dashed #b8c4d3"></span>${T(v.L?.paid)}</span>
            <span style="display:inline-flex;align-items:center;gap:6px"><span style="width:16px;height:3px;border-radius:2px;background:#0950e3"></span>${T(v.L?.path)}</span>
            </div>
          ${v.showCta ? html`<div style="margin:0 18px 12px;border:1px solid #c5d6f8;background:#f5f8ff;border-radius:12px;padding:10px 12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px"><i class="fa-solid fa-lock" style="color:#0950e3"></i><span style="flex:1 1 240px;font-size:13px;text-wrap:pretty">${v.ctaText}</span><button onClick=${v.unlock} style="font-family:inherit;border:none;border-radius:10px;padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer;background:#0950e3;color:#ffffff;white-space:nowrap">${v.unlockLabel}</button></div>` : null}
          ${v.isOwner && !v.ownerHas ? html`<div style="margin:0 18px 12px;border:1px solid #c5d6f8;background:#f5f8ff;border-radius:12px;padding:10px 12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px"><i class="fa-solid fa-lock" style="color:#0950e3"></i><span style="flex:1 1 240px;font-size:13px;text-wrap:pretty">${v.ownerText}</span>${v.askSignIn ? html`<a href="/mine" style="font-family:inherit;line-height:normal;border:1.5px solid #0950e3;border-radius:10px;padding:6.5px 14px;font-size:13px;font-weight:700;background:#ffffff;color:#0950e3;white-space:nowrap;text-decoration:none">${v.L?.signIn}</a>` : null}<button onClick=${v.unlock} style="font-family:inherit;border:none;border-radius:10px;padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer;background:#0950e3;color:#ffffff;white-space:nowrap">${v.unlockLabel}</button></div>` : null}
          ${v.isOwner && v.ownerHas ? html`<div style="margin:0 18px 12px;border:1px solid #b7e4c7;background:#e8f7ef;border-radius:12px;padding:10px 12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px"><i class="fa-solid fa-circle-check" style="color:#15803d"></i><span style="flex:1 1 240px;font-size:13px;text-wrap:pretty">${v.ownerText}</span><button onClick=${v.download} style="font-family:inherit;border:none;border-radius:10px;padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer;background:#15803d;color:#ffffff;white-space:nowrap"><i class="fa-solid fa-download"></i> ${T(v.L?.download)}</button></div>` : null}
          ${v.isTree ? html`
            <div ref=${v.treeRef} data-tree-scroll="1" onPointerDown=${v.panDown} onPointerMove=${v.panMove} onPointerUp=${v.panUp} onPointerLeave=${v.panUp} style="cursor:grab;user-select:none;overflow:auto;max-height:72vh;border-top:1px solid #e2e9f0;background:#fbfcfe">
              <div style="position:relative;width:${s(v.cwPx)};height:${s(v.chPx)}">${' '}
                ${(v.heads || []).map((hd, $index) => html`<span style="position:absolute;left:${s(hd?.x)};top:9px;width:${s(v.nW)};text-align:center;font-size:10.5px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#8d9cae">${hd?.text}</span>`)}${' '}
                <svg width=${v.cw} height=${v.ch} style="position:absolute;left:0;top:0;overflow:visible">${' '}
                  ${(v.edges || []).map((e, $index) => html`<path d=${e?.d} style="fill:none;stroke:${s(e?.stroke)};stroke-width:${s(e?.sw)};stroke-linejoin:round;stroke-linecap:round" />`)}${' '}
                  </svg>${' '}
                ${(v.labels || []).map((l, $index) => html`<button onClick=${l?.go} style="position:absolute;left:${s(l?.left)};top:${s(l?.top)};transform:${s(l?.tf)};height:18px;line-height:18px;padding:0 6px;border:none;border-radius:999px;background:${s(l?.bg)};color:${s(l?.color)};font-family:inherit;font-size:10.5px;font-weight:700;white-space:nowrap;cursor:pointer">${l?.text}</button>`)}${' '}
                ${(v.nodes || []).map((n, $index) => html`
                  <button class="tr-hover0" onClick=${n?.onClick} onMouseEnter=${n?.onEnter} onMouseLeave=${n?.onLeave} onFocus=${n?.onEnter} onBlur=${n?.onLeave} aria-label=${n?.title} style="position:absolute;left:${s(n?.x)};top:${s(n?.y)};width:${s(v.nW)};height:${s(v.nH)};border-radius:10px;border:${s(n?.bd)};background:${s(n?.bg)};box-shadow:${s(n?.shadow)};opacity:${s(n?.op)};cursor:pointer;font-family:inherit;padding:0 9px;display:flex;align-items:center;gap:6px;text-align:start;color:#16263a;transition:box-shadow .15s,transform .15s,opacity .15s">
                    ${n?.isDec ? html`<span style="flex:1;display:flex;flex-direction:column;min-width:0"><strong style="font-size:12px;line-height:15px;color:${s(n?.nameC)};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${n?.name}</strong><span style="font-size:11px;line-height:14px;color:#5a6b80;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums">${n?.q}</span></span>` : null}
                    ${n?.isLeaf ? html`<span style="flex:1;display:flex;flex-direction:column;gap:4px;min-width:0"><span style="display:flex;justify-content:space-between;align-items:center;gap:6px"><strong style="font-size:12.5px;line-height:15px;color:${s(n?.c)};display:inline-flex;align-items:center;gap:5px;white-space:nowrap"><i class=${n?.ic} style="font-size:10.5px"></i>${T(n?.verb)}</strong><span style="font-size:11.5px;line-height:15px;font-weight:700;color:${s(n?.c)};font-variant-numeric:tabular-nums">${n?.value}</span></span><span style="height:4px;border-radius:2px;background:#e9eef4;overflow:hidden"><span style="display:block;height:100%;width:${s(n?.str)};border-radius:2px;background:${s(n?.c)}"></span></span></span>` : null}
                    ${n?.isLock ? html`<strong style="font-size:12px;color:#5a6b80;display:inline-flex;align-items:center;gap:6px;white-space:nowrap"><i class="fa-solid fa-lock" style="font-size:10.5px"></i>${T(v.L?.paid)}</strong>` : null}
                    </button>
                  `)}${' '}
                </div>
              </div>
            ` : null}
          ${v.isRules ? html`
            <div data-blk-scroll="1" onPointerDown=${v.panDown} onPointerMove=${v.panMove} onPointerUp=${v.panUp} onPointerLeave=${v.panUp} style="cursor:grab;user-select:none;overflow:auto;max-height:72vh;border-top:1px solid #e2e9f0;background:#fbfcfe;padding:10px 12px">
              <div style="display:flex;width:${s(v.bwPx)}">${(v.heads || []).map((hd, $index) => html`<span style="width:${s(v.bW)};flex-shrink:0;text-align:center;font-size:10.5px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#8d9cae;padding-bottom:8px">${hd?.text}</span>`)}</div>
              <div style="position:relative;width:${s(v.bwPx)};height:${s(v.bhPx)}">${' '}
                ${(v.blocks || []).map((b, $index) => html`<div style="position:absolute;left:${s(b?.x)};top:${s(b?.y)};width:${s(b?.w)};height:${s(b?.h)};padding:2px"><button class="tr-hover1" onClick=${b?.onClick} onMouseEnter=${b?.onEnter} onMouseLeave=${b?.onLeave} style="width:100%;height:100%;font-family:inherit;text-align:start;cursor:pointer;border-radius:9px;background:${s(b?.bg)};border:${s(b?.bd)};padding:3px 8px;display:flex;flex-direction:column;justify-content:flex-start;gap:0;overflow:hidden;opacity:${s(b?.op)}"><span style="flex-shrink:0;max-width:100%;font-size:10.5px;line-height:12px;color:${s(b?.subC)};white-space:${s(b?.ws)};overflow:hidden;text-overflow:ellipsis">${b?.inc}</span><strong style="flex-shrink:0;max-width:100%;font-size:12px;line-height:15px;color:${s(b?.c)};display:flex;gap:6px;align-items:flex-start;overflow:hidden"><i class=${b?.ic} style="font-size:10.5px;flex-shrink:0;margin-top:2.5px"></i><span style="white-space:${s(b?.ws)};overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:${s(b?.lc)};-webkit-box-orient:vertical">${b?.main}</span><span style="font-weight:500;font-size:11px">${b?.val}</span></strong></button></div>`)}${' '}
                </div>
              </div>
            ` : null}
          <div style="border-top:1px solid #e2e9f0;padding:14px 18px 18px;display:flex;flex-direction:column;gap:14px">
            <button class="tr-hover2" onClick=${v.toggleAllRules} style="align-self:flex-start;font-family:inherit;border-radius:999px;padding:9px 16px;font-size:13.5px;font-weight:700;cursor:pointer;display:inline-flex;gap:8px;align-items:center;border:1.5px solid #0950e3;background:#ffffff;color:#0950e3"><i class="fa-solid fa-list-ul"></i>${T(v.allRulesLabel)}</button>
            ${v.allRulesOpen ? html`
              ${(v.groups || []).map((g, $index) => html`
                <div style="display:flex;flex-direction:column;gap:10px">
                  <div style="display:flex;align-items:center;gap:10px"><span style="width:30px;height:30px;border-radius:50%;background:${s(g?.c)};color:#ffffff;display:grid;place-items:center;font-size:13px"><i class=${g?.ic}></i></span><strong style="font-size:17px;color:${s(g?.c)}">${g?.verb}</strong><span style="font-size:13px;color:#5a6b80">${g?.count}</span></div>
                  ${(g?.rules || []).map((r, $index) => html`
                    <button class="tr-hover3" onClick=${r?.jump} style="font-family:inherit;text-align:start;cursor:pointer;color:#16263a;background:#ffffff;border:${s(r?.bd)};border-radius:16px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:${s(r?.sh)}">
                      <span style="display:flex;gap:14px;align-items:center"><span style="width:46px;height:46px;border-radius:50%;background:conic-gradient(${s(r?.c)} ${s(r?.deg)}, #e9eef4 0);display:grid;place-items:center;flex-shrink:0"><span style="width:36px;height:36px;border-radius:50%;background:#ffffff;display:grid;place-items:center;font-size:11px;font-weight:700;color:${s(r?.c)}">${r?.val}</span></span><span style="flex:1;display:flex;flex-direction:column;gap:2px"><span style="font-size:11.5px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:${s(r?.c)}">${r?.str}</span><span style="font-size:14px;text-wrap:pretty">${r?.text}</span></span>${r?.now ? html`<span style="font-size:11.5px;font-weight:700;color:#0950e3;background:#e9f0fd;border-radius:999px;padding:3px 10px;white-space:nowrap">${v.L?.path}</span>` : null}</span>
                      <span style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px 18px">${(r?.bars || []).map((br, $index) => html`<span style="display:flex;flex-direction:column;gap:5px"><span style="display:flex;justify-content:space-between;gap:8px;font-size:12px"><strong>${br?.name}</strong><span style="color:#5a6b80;font-variant-numeric:tabular-nums">${br?.range}</span></span><span style="position:relative;height:8px;border-radius:4px;background:#e9eef4"><span style="position:absolute;top:0;bottom:0;left:${s(br?.l)};width:${s(br?.w)};border-radius:4px;background:${s(r?.c)}"></span></span></span>`)}</span>
                      </button>
                    `)}
                  </div>
                `)}
              ${v.hasLockedNote ? html`<span style="font-size:13px;color:#5a6b80;display:inline-flex;gap:8px;align-items:center"><i class="fa-solid fa-lock"></i>${T(v.lockedNote)}</span>` : null}
              ` : null}
            </div>
          </section>
        </div>
      ` : null}
    ${v.standalone ? html`<p style="margin:0;max-width:820px;font-size:12.5px;color:#8d9cae;text-wrap:pretty">${v.L?.source}</p>` : null}
    </section>
`;
}
