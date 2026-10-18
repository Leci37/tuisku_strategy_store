// Markup and styles ported one to one from docs/design/Strategy Tree.dc.html (the v7 reference design).
import { html } from '../../lib/html.js';
import TreeHeader from './tree_header.js';
import TreeMain from './tree_main.js';
import TreeTip from './tree_tip.js';

export default function TreeRoot(v) {
  return html`<div style="min-height:100vh;font-family:Ubuntu,system-ui,'Segoe UI',sans-serif;color:#16263a;font-size:14px;line-height:1.5">
    ${TreeHeader(v)}
    ${TreeMain(v)}
    ${TreeTip(v)}
  </div>`;
}
