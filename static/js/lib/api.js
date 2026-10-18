// Las llamadas al servidor de la tienda. Un rechazo llega como {"error": "<clave>", ...} (la convención
// de las herramientas): la clave viaja en el ApiError, con el resto de la respuesta (vars, items...), para
// que la página la enseñe traducida. El token CSRF de cada POST, PUT y DELETE lo pone csrf.js del núcleo
// (parchea fetch), igual que la cabecera que dice que esto es un script.
export class ApiError extends Error {
  constructor(status, key, detail) {
    super(key);
    this.status = status;
    this.key = key;
    this.detail = detail || {};
  }
}

export async function api(path, { method = 'GET', body } = {}) {
  const init = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
  if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, init);
  } catch (e) { // ninguna respuesta (sin red, DNS, conexión cortada): el único caso que es un error de red
    const err = new ApiError(0, 'errShopNetwork', {});
    err.network = true;
    throw err;
  }
  let data = null;
  try { data = await res.json(); } catch (e) { data = null; }
  if (!res.ok) {
    const detail = data && typeof data === 'object' && !Array.isArray(data) ? data : {};
    throw new ApiError(res.status, typeof detail.error === 'string' ? detail.error : '', detail);
  }
  return data;
}

export const post = (path, body) => api(path, { method: 'POST', body: body || {} });
