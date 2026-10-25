// Los diálogos de la tienda (la gratis, el recorrido, el tutorial de instalación, Comparar y el pack) son
// capas del diseño, <div role="dialog" aria-modal="true">, no un <dialog>: lo que showModal() haría solo lo
// hace aquí App.syncModal() después de cada pintura. Lo de detrás, inert: ni Tab, ni el ratón, ni un lector
// de pantalla llegan a la página que tapa el velo. Los avisos (role=alert o status, aria-live) no: se
// pintan por encima y su × se pulsa.
const SKIP = ['SCRIPT', 'STYLE', 'LINK', 'TEMPLATE', 'NOSCRIPT'];
const LIVE = '[role=alert],[role=status],[aria-live]';
const FOCUSABLE = 'a[href],button:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])';

// El diálogo abierto de más arriba (el de más z-index de su velo), o null.
export function topDialog(root) {
  let top = null, z = -Infinity;
  (root || document).querySelectorAll('[role=dialog][aria-modal=true]').forEach(d => {
    const zi = Number(getComputedStyle(d.parentElement).zIndex) || 0;
    if (zi >= z) { z = zi; top = d; }
  });
  return top;
}

// Los hermanos de cada antepasado del velo, hasta <body>, se quedan inert; en `marked`, los que marcó aquí
// (lo que ya era inert, de otro, no se toca). Se repite en cada pintura: lo que salga nuevo detrás, también.
export function shield(dialog, marked) {
  for (let el = dialog.parentElement; el && el.parentElement && el !== document.body; el = el.parentElement) {
    for (const sib of el.parentElement.children) {
      if (sib === el || sib.inert || SKIP.includes(sib.tagName) || sib.matches(LIVE)) continue;
      sib.inert = true;
      marked.push(sib);
    }
  }
}

export function unshield(marked) {
  marked.forEach(el => { el.inert = false; });
  marked.length = 0;
}

// Lo que se enfoca dentro, a la vista y en el orden de Tab.
export function focusables(dialog) {
  return [...dialog.querySelectorAll(FOCUSABLE)].filter(el => el.offsetWidth || el.offsetHeight || el.getClientRects().length);
}

// El foco entra en lo principal del diálogo (data-ef-focus: «Continuar», el buscador, la ×…). En una
// pantalla táctil, en el propio diálogo: un campo abriría el teclado encima, y un botón llevaría el contorno
// del foco sin que nadie use el teclado; el lector de pantalla lee el diálogo igual. El diálogo se puede
// enfocar siempre (tabindex -1): un clic en su fondo deja el foco dentro, no en <body>.
export function focusIn(dialog) {
  if (!dialog.hasAttribute('tabindex')) dialog.setAttribute('tabindex', '-1');
  const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
  (coarse ? dialog : dialog.querySelector('[data-ef-focus]') || dialog).focus();
}

// Al cerrarse, el foco vuelve a quien lo abrió. Si nadie lo abrió (el recorrido de la primera vez, el
// tutorial de /thanks) o ya no está (Comparar se cierra al quitar su última columna, y su píldora se va con
// ella), a <main>, como el diálogo del núcleo (dialog.js): en <body>, el siguiente Tab seguía desde donde
// estaba el diálogo, al final de la página, y saltaba al pie. <main> se enfoca sólo mientras lo tiene (un
// clic en la página no se queda en él) y sin contorno, como el propio diálogo: no es un control, y el
// contorno era una raya azul a lo ancho de la página.
export function giveBack(opener) {
  if (opener && opener !== document.body && opener.isConnected && opener.focus) {
    opener.focus({ preventScroll: true });
    if (document.activeElement === opener) return;
  }
  const main = document.querySelector('main');
  if (!main) return;
  if (!main.hasAttribute('tabindex')) {
    main.setAttribute('tabindex', '-1');
    main.style.outline = 'none';
    main.addEventListener('blur', () => {
      main.removeAttribute('tabindex');
      main.style.removeProperty('outline');
      if (!main.getAttribute('style')) main.removeAttribute('style');
    }, { once: true });
  }
  main.focus({ preventScroll: true });
}

// Tab y Mayús+Tab dan la vuelta dentro del diálogo: del último al primero y al revés.
export function keepTab(dialog, e) {
  const list = focusables(dialog);
  const i = list.indexOf(document.activeElement);
  if (!list.length) { e.preventDefault(); return; }
  if (e.shiftKey ? i <= 0 : i < 0 || i === list.length - 1) {
    e.preventDefault();
    list[e.shiftKey ? list.length - 1 : 0].focus();
  }
}
