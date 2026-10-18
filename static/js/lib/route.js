// Pages and their addresses. A strategy has its own address (/s/<id>, /s/<id>/tree) so it opens in
// a new tab; the old #s=<id> links from the first storefront keep working.
export function parseLocation(loc) {
  const path = loc.pathname;
  const m = path.match(/^\/s\/([^/]+)(\/tree)?\/?$/);
  if (m) return { page: 'detail', detail: decodeURIComponent(m[1]), detTab: m[2] ? 'tree' : 'overview' };
  const h = (loc.hash || '').match(/^#s=([^/]+)(?:\/(tree))?/);
  if (h) return { page: 'detail', detail: decodeURIComponent(h[1]), detTab: h[2] ? 'tree' : 'overview' };
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
