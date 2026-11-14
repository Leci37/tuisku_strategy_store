// Pages and their addresses. A strategy has its own address (/s/<id>, /s/<id>/tree) so it opens in
// a new tab; the old #s=<id> links from the first storefront keep working.
// Un id mal escrito en la dirección (/#s=%E0%A4, un enlace cortado) va tal cual: la ficha dice que no la encuentra.
// Hasta el 14-11-2026, decodeURIComponent lanzaba «URI malformed» y la página se quedaba en blanco.
const decoded = s => { try { return decodeURIComponent(s); } catch (e) { return s; } };

export function parseLocation(loc) {
  const path = loc.pathname;
  const m = path.match(/^\/s\/([^/]+)(\/tree)?\/?$/);
  if (m) return { page: 'detail', detail: decoded(m[1]), detTab: m[2] ? 'tree' : 'overview' };
  const h = (loc.hash || '').match(/^#s=([^/]+)(?:\/(tree))?/);
  if (h) return { page: 'detail', detail: decoded(h[1]), detTab: h[2] ? 'tree' : 'overview' };
  if (/^\/mine\/?$/.test(path)) return { page: 'mine', detail: '', detTab: 'overview' };
  if (/^\/thanks\/?$/.test(path)) return { page: 'thanks', detail: '', detTab: 'overview' };
  return { page: 'shop', detail: '', detTab: 'overview' };
}

export const strategyPath = (id, tree) => '/s/' + encodeURIComponent(id) + (tree ? '/tree' : '');

export function pathOf({ page, detail, detTab }) {
  if (page === 'detail') return strategyPath(detail, detTab === 'tree');
  if (page === 'mine') return '/mine';
  if (page === 'thanks') return '/thanks';
  return '/';
}
