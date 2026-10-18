// Monta la tienda: el contenido en #app (dentro del .sc-host del diseño) y, en la barra del núcleo, lo
// suyo: Lite | Pro y Mis estrategias al principio, y Ver tutorial, TradingView y la moneda antes del idioma.
import { h, render } from '../vendor/preact.module.js';
import { App } from './app.js';

const bar = where => document.querySelector('[data-ef-bar="' + where + '"]');
const root = document.getElementById('app');
render(h('div', { class: 'sc-host' }, h(App, { barStart: bar('start'), barEnd: bar('end'), signedIn: root.dataset.signedIn === '1' })), root);
