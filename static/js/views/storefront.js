// Markup and styles ported one to one from docs/design/Storefront v7.dc.html (the v7 reference design).
// La barra y el pie son los de la carcasa del núcleo: lo de la tienda en la barra va por Portal a sus
// huecos, y el resto de la página, aquí.
import { h } from '../../vendor/preact.module.js';
import { html } from '../lib/html.js';
import { Portal } from '../lib/portal.js';
import MenuScrim, { BarStart, BarEnd } from './header.js';
import Lite from './lite.js';
import Pro from './pro.js';
import Thanks from './thanks.js';
import Mine from './mine.js';
import Detail from './detail.js';
import Dialogs from './dialogs.js';
import PhoneBar from './phonebar.js';

export default function Storefront(v) {
  return html`<div lang=${v.lang} dir=${v.dir} data-screen-label="Edgefolio storefront" style="display:flex;flex-direction:column;background:#f4f8fb;font-family:Ubuntu,system-ui,'Segoe UI',Roboto,Arial,sans-serif;color:#16263a;font-size:14px;line-height:1.5">
    ${h(Portal, { into: v.barStart }, BarStart(v))}
    ${h(Portal, { into: v.barEnd }, BarEnd(v))}
    ${MenuScrim(v)}
    ${Lite(v)}
    ${Pro(v)}
    ${Thanks(v)}
    ${Mine(v)}
    ${Detail(v)}
    ${Dialogs(v)}
    ${PhoneBar(v)}
  </div>`;
}
