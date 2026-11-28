# Estado de Edgefolio

Lo hecho, lo que falta y lo que se pide al núcleo (`docs/estandar/DOCS.md` del núcleo, §1). Empieza el 15-11-2026, con la
ronda de logs; lo de antes está en el README («Qué cambió desde la versión FastAPI» y «Antes de volver a vender»), en
`design/STATUS.md` (el del diseño) y en la historia del repo.

## Lo hecho

### Núcleo 0.35.0 — el remate del ciclo de la 0.36 (25-11-2026)

Lo que contestó la coordinadora del ciclo, por delegación del dueño (`pruebas/2026-11-24_ciclo_036/RESPUESTAS.md`,
«Edgefolio»; regla 1: nada se promete que no sea verdad hoy):

- **La fila de confianza dice «Recibo por correo»** (`trustInvoice`, en los 8 idiomas): decía «Factura por correo», y
  lo que llega es un recibo sin número de factura ni IVA. Vuelve a «Factura» con el recibo con IVA del núcleo (abajo,
  «Lo que falta»). Lo vigila `tests/test_texts.py`.
- **El paso 3 del recorrido de bienvenida** (`tour3Text`) dice los días de `DOWNLOAD_DAYS`, con la forma de su número,
  como la fila de confianza y el «Hecho» de la gratis: llevaba el 7 escrito en los 8 idiomas. Su prueba, en un
  Chromium, en `tests/test_texts.py`.

### Núcleo 0.35.0 — el ciclo de la 0.36 en los documentos (25-11-2026)

Sin tocar el código: `docs/` en los cuatro bloques del núcleo (`README.md` nuevo; `VISION.md`,
`DECISIONES.md`, `COSTES.md`, `DATOS.md` y `FLUJO_ADMINISTRADOR.md`, escritos desde el código y lo que ya
había; el índice de antes y las notas de la tienda de 2024, a `historico/`), los enlaces a las rutas nuevas
del núcleo, `market/` (cómo se vende) y los vídeos de los dos flujos (`market/videos/VIDEOS.md`). Lo que el
código ya pide de la 0.36 sigue esperando: abajo, «Con la 0.36».

### Núcleo 0.35.0 — la ronda de logs (15-11-2026)

- Cada cambio de estado deja su línea (pedidos y cobros, enlaces y descargas, gratis y novedades, pruebas de correo,
  favoritas, «Tus datos»), con los ids y cuántos, nunca un correo, un código ni un token; cada rechazo, una sola, con la
  regla de la ruta; cada tarea dice lo que hizo; el BCE y PayPal que fallan, un WARNING; lo que no se esperaba, con su
  traza. Fichero a fichero, en [tecnico/LOGS.md](tecnico/LOGS.md); las pruebas, en `tests/test_logs.py`.
- La segunda vuelta (16 y 24-11-2026, el dueño pidió un 25 % más y 30 como mínimo por capa): cliente de 1 a 37 líneas,
  servidor de 52 a 71 y endpoint de 5 a 30. El cliente tiene su propio ayudante, `static/js/lib/log.js`: escribe en la
  consola hasta la 0.36 y después usará `zt.log` sin más cambios. En el endpoint va lo que la ruta decide y la línea de
  cada petición no dice. En [tecnico/LOGS.md](tecnico/LOGS.md), «Segunda vuelta».

## Lo que falta

- **Los pagos, del núcleo.** `edgefolio/paypal.py` es un cliente de PayPal propio, y desde la 0.35 los pagos son del
  núcleo (CONTRATO §10, «Pagar: Stripe y PayPal»). Su migración estaba pendiente antes de la ronda de logs, y sus logs
  se van con ella. Las decisiones del dueño para ella (Luis, 24-11-2026):
  1. **El IVA va incluido en el precio.**
  2. **Pasarela: PayPal y Stripe, las dos**; no nos cerramos a una.
  3. **Recibo: uno solo, el del núcleo**, que ya lleva el IVA desglosado; la tienda lo enseña y lo enlaza (deja de
     mandar el suyo, `mailReceiptBody`). Con él, la fila de confianza vuelve a decir «Factura por correo»
     (`trustInvoice`, en los 8 idiomas; hasta entonces, «Recibo por correo»: 2026-11-25).
  4. **Sus pruebas no esperan a nada:** la pasarela de pruebas del núcleo existe desde la 0.35
     (`testing.fake_payments`, `testing.FakeGateway`; CONTRATO).

  El trabajo se definió como WP1, WP2 y WP3 en el chat «trade» de claude.ai, que no está escrito en este repo: hace
  falta traer aquí qué es cada uno antes de empezarlos. Las claves de Alpaca, sólo por el formulario seguro, nunca por
  un chat.
- **Lo de los logs que espera a la 0.36** (abajo, «Para el núcleo»): el frontal, los cambios de pantalla, la traza de
  la llamada al BCE y las comprobaciones de `check_tool()`. Lo que hará la tienda con cada cosa, en
  [tecnico/LOGS.md](tecnico/LOGS.md).
- **Lo que sigue abierto de octubre**, de decidir por el dueño (las condiciones de TradingView para vender scripts,
  lo caducado que se sigue vendiendo, los niveles en el servidor…): en «Lo que sigue abierto» de
  [handoff/2026-10-06/CAMBIOS.md](handoff/2026-10-06/CAMBIOS.md). Lo ya decidido, en [DECISIONES.md](DECISIONES.md).

## Con la 0.36

Cuando el núcleo etiquete la 0.36 y la tienda suba (`docs/estandar/ESTRUCTURA.md` §12 del núcleo), en el mismo
cambio, y nada de ello antes:

- **El pin**, en `requirements.txt`.
- **`docs/DATOS.md`, sus «Tablas»** generadas (`flask --app app zt tables --write docs/DATOS.md`): los docstrings de
  las nueve tablas ya están.
- **`tests/test_flow.py`** con `testing.flow` y `flow.assert_walked` (hoy el recorrido de compra es
  `tests/test_walkthrough.py`); las marcas `<!-- zt:paso … -->` en los dos flujos, sus capturas (`FLOW_SHOTS=1`, en
  `docs/img/flujo/`) y `tests/test_docs.py` con `flow.doc_problems`.
- **`check_tool()` con `logs_check`**, y lo de los logs que ya esperaba: `zt.log` en lugar del ayudante
  `static/js/lib/log.js`, `external_call` para el BCE, la línea de cada petición y `accesslog = None` (abajo,
  «Para el núcleo»; el plan, en [tecnico/LOGS.md](tecnico/LOGS.md)).

## Para el núcleo

1. **El frontal: `zt.log`** (0.36, CONTRATO §27: `debug`/`info` a la consola, `warn`/`error` también al servidor por
   `POST /zt/log`, y `zt.log.view(tipo, nombre)`). Desde la segunda vuelta, la tienda ya escribe en su sitio con su
   ayudante, `static/js/lib/log.js`, con las mismas firmas: en `App.fail` (la tienda pide con su `lib/api.js`, no con
   `zt.fetchJSON`, así que el núcleo no ve sus fallos de red), en los `catch` que callaban y en
   `App.componentDidUpdate` para sus pantallas, pestañas y diálogos (los suyos no son `zt.openDialog`). Hasta la 0.36
   sólo escribe en la consola; al subir, el ayudante usa `zt.log` y `warn` y `error` llegan al servidor, sin tocar nada
   más.
2. **`external_call`** (0.36: `from zlecitool_core.observability.trace import external_call`): la traza de la llamada al
   BCE (`edgefolio/fx.py`). Espera a subir a la 0.36.
3. **Las comprobaciones de `check_tool()`**: sin salidas propias ni `print` en el paquete, y con `privacy_sample`, que
   el correo y el nombre de la cuenta de prueba no salgan en los logs. Espera a la 0.36.
4. **La línea de cada petición.** Con `python app.py`, el núcleo manda al fichero del día la línea de werkzeug, que lleva
   la IP, la ruta con sus credenciales (`/api/download/<token>`, `/api/news/confirm?token=…`, `/api/download/all?t=…`),
   la consulta que tecleó la persona (`GET /api/strategies?q=…`, vista con la cuenta de prueba el 15-11-2026) y, al
   arrancar, el `Debugger PIN` de werkzeug. Con gunicorn, el `accesslog = "-"` de `gunicorn.conf.py`, en su formato por
   defecto (IP, petición con su consulta, referer y agente), lo lleva a la salida estándar. La 0.36 la resuelve: la
   línea de cada petición es suya (`zlecitool.requests`, por la regla, con la cuenta por su id, el resultado, el tiempo
   y `error=errAlgo` en un rechazo; sin IP ni consulta) y la de werkzeug se quita. Y al subir a la 0.36, en el mismo
   cambio, `accesslog = "-"` pasa a `accesslog = None` en `gunicorn.conf.py`, como la plantilla (decidido el
   15-11-2026; el núcleo lo dirá en «Para las herramientas» de su CHANGELOG). Hasta entonces no se toca.
