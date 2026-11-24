// El log de la página (la ronda de logs, 16-11-2026; docs/tecnico/LOGS.md). Con el núcleo 0.36, zt.log (CONTRATO
// §27): debug e info a la consola; warn y error, también al servidor (POST /zt/log); view(tipo, nombre), los cambios de
// pantalla, pestaña y diálogo. Hasta entonces, este respaldo, sólo a la consola: «[edgefolio] nivel Qué | k=v k=v».
// Se mira zt.log en cada llamada: al subir a la 0.36 lo usa sin cambiar nada más. Las mismas firmas que zt.log:
// debug/info/warn(qué, datos), error(qué, datos | Error), view(tipo, nombre).
// En los datos, sólo ids y referencias (la estrategia, el pedido, un estado, cuántas): nunca un correo, lo buscado,
// un código de descuento ni nada que haya escrito la persona.
const line = (level, what, data) => {
  const pairs = data && typeof data === 'object' && !(data instanceof Error)
    ? Object.entries(data).filter(([, v]) => v !== undefined && v !== null && v !== '').map(([k, v]) => `${k}=${v}`) : [];
  return `[edgefolio] ${level} ${what}${pairs.length ? ' | ' + pairs.join(' ') : ''}`;
};

const fallback = {
  debug: (what, data) => console.debug(line('debug', what, data)),
  info: (what, data) => console.info(line('info', what, data)),
  warn: (what, data) => console.warn(line('warn', what, data)),
  // un Error, aparte: la consola enseña su traza
  error: (what, data) => console.error(line('error', what, data), ...(data instanceof Error ? [data] : [])),
  view: (type, name) => fallback.info('Vista', { tipo: type, nombre: name }),
};

const target = () => (window.zt && window.zt.log) || fallback;

export const log = {
  debug: (what, data) => target().debug(what, data),
  info: (what, data) => target().info(what, data),
  warn: (what, data) => target().warn(what, data),
  error: (what, data) => target().error(what, data),
  view: (type, name) => target().view(type, name),
};
