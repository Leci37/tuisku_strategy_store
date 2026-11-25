# Los logs de Edgefolio

Ronda de logs de la familia, 15-11-2026, sobre `_ztool_dev` (63de2159) con el núcleo 0.35.0. Qué escribe la tienda en
cada capa, cada `except`/`catch` con su decisión, cada cambio de estado, cada llamada de fuera y cada tarea; lo que se
añade ya y lo que espera a la 0.36 del núcleo.

## La pauta, en corto

- Formato «Qué pasó | clave=valor clave=valor», en español (como los del núcleo: `Cuenta creada | user_id=1`).
- Las personas, por su id (`user_id=`); lo de la tienda, por su referencia: `pedido=<id de PayPal>`, `estrategia=<id>`
  (el de la URL, `AAPL_1Day_1ADX_aaaa1111`), `prueba=<id>`, `lote=<clave>`. **Nunca** un correo, lo tecleado (la búsqueda, un código de descuento), una IP, un
  token de enlace (`/api/download/<token>`, los de confirmar), el contenido de un script.
- Niveles: DEBUG, desarrollo; INFO, lo que pasó; WARNING, algo raro o un servicio de fuera que falla, y se sigue;
  ERROR, falló (con la traza si no se esperaba).
- Un rechazo de la persona (una `Refusal`, `{"error": "errAlgo"}`) va en **una sola línea**, la del manejador de
  `routes.py` (INFO; WARNING si es un 5xx): los módulos no repiten la suya.
- Nada en lo que corre por cada fila o cada petición de una imagen: la carga del catálogo cuenta lo que falta en una
  línea, no en una por estrategia.

## Cómo se miró (F0)

`.env` con `ZLECITOOL_LOG_DIR=C:\Users\leci\Documents\tuisku\logs`, `python app.py` en el puerto 5125 y un recorrido con
un solo Chromium sin ventana: la tienda sin cuenta (Lite, una ficha y su árbol, una búsqueda con «Zelda Logsprueba»), una
gratis a `logs-edgefolio@example.test` con las novedades, un presupuesto con un código que no vale y con `demo20`, un
pedido en el PayPal de prueba y su cobro, descargar el `.pine` y el `.zip`, darse de alta, demostrar el correo, Mis
estrategias, renovar, dos favoritas y quitar una, salir; y rechazos a propósito (`size=abc`, un enlace inventado, un
carrito vacío, Mis estrategias sin cuenta). Después, las tres tareas a mano (`flask --app app zt task run …`; la de
los avisos, dos veces).

Lo que se vio en `edgefolio-2026-11-15.log`:

- sale, con una línea `Arranca | núcleo 0.35.0` por proceso (también los de `flask zt …`);
- las líneas del núcleo (las tareas, el correo, las cuentas: `Cuenta creada | user_id=1`, `Sesión cerrada | user_id=1`)
  y la de cada petición del servidor de desarrollo (`werkzeug`);
- **de la tienda, ninguna**: el recorrido no pasa por ninguna de las 7 líneas que tiene (son de fallos);
- las tareas, sólo `empieza` y `bien en 2.0 s`: ni cuántos cambios trajo `fx_update`, ni qué mandó `send_alerts`, ni qué
  borró `purge`, ni que la segunda vuelta de `send_alerts` no hizo nada;
- ningún logger fuera del slug (`edgefolio.catalogue`, `edgefolio.levels`, `edgefolio.orders` y el de la app);
- la consola del navegador: sólo los «Failed to load resource» de los rechazos buscados; la página no escribe nada
  propio salvo `console.error` en un fallo de la página (`App.fail`), que el recorrido no provocó;
- el correo de la cuenta no sale en el log (el núcleo lo enmascara: `l•••@example.test`); **el nombre sí**, por la
  línea de werkzeug (abajo, «Privacidad»).

## Lo que hay hoy (F1)

| Capa | Líneas | Niveles | Dónde |
|---|---|---|---|
| Frontal | 1 | `console.error` | `static/js/app.js:271` (`App.fail`: un fallo sin código que no es de red) |
| Servidor | 6 | 4 ERROR, 2 WARNING | `catalogue.py:352,358` (un lote fuera), `levels.py:102,113` (`levels.json`), `orders.py:131,165` (PayPal, llamada de fuera) |
| Endpoint | 1 | WARNING | `routes.py:293` (el recibo sin `ZLECITOOL_PUBLIC_URL`); la línea de cada petición es del núcleo (werkzeug o el `accesslog` de gunicorn) |
| Cambio de ventana | 0 | — | — |
| **Total** | **8** (7 en Python) | | |

`except` en Python: 37, de ellos 2 en `paypal.py` (fuera de esta ronda: se van con la migración a los pagos del
núcleo, abajo). De los 35 de esta ronda, 19 vuelven a lanzar o escriben y 16 callan con un valor por defecto.
`catch` en el JavaScript: 37 (26 en `app.js`, 5 en `tree.js`, 3 en `lib/saved.js`, 2 en `lib/api.js`, 1 en
`lib/route.js`).

## Fichero a fichero

«Hoy» es lo que hace el código de `_ztool_dev`; «Decisión», lo que queda después de esta ronda. «Nada» lleva su porqué.

### `app.py`

| Sitio | Hoy | Decisión |
|---|---|---|
| `MissingSecretError` al arrancar | `sys.exit` con el mensaje | se queda: para el proceso y lo dice en la consola (no hay app ni log aún) |

### `edgefolio/tasks.py` — las tres tareas

| Sitio | Hoy | Decisión |
|---|---|---|
| `done(run)`: la vez ya hecha | nada (el núcleo dice «bien en 0.0 s») | INFO `Tarea ya hecha: nada que hacer \| tarea= vez=` |
| `fx_update` | nada propio | lo dice `fx.update` (abajo): INFO con el día y cuántos cambios, o WARNING si el BCE falla |
| `fx_update`: `except fx.FAILURES` | relanza `RuntimeError` (la vez queda «falló» y avisa, §22) | se queda; antes, el WARNING de `fx.update` |
| `send_alerts` | nada propio | lo dice `alerts.run` (abajo) |
| `purge` | nada propio | lo dice `free.purge` (abajo) |
| `public_link` sin `ZLECITOOL_PUBLIC_URL` | `RuntimeError` | se queda: la tarea falla y el núcleo lo apunta |

### `edgefolio/fx.py` — llamada de fuera (frankfurter.app, el BCE)

| Sitio | Hoy | Decisión |
|---|---|---|
| traer los cambios | `fetch()` sin una línea | `update(out)`, que usan la tarea y el comando: INFO `Cambios del BCE guardados \| dia= cambios=`; con `fx.FAILURES`, WARNING `BCE sin cambios nuevos: <fichero> sigue como estaba \| error=` y relanza |
| la traza de la llamada (`API → / API ←`) | — | **0.36**: `external_call` del núcleo, cuando esté en su CONTRATO |

### `edgefolio/alerts.py` — los avisos de las favoritas

| Sitio | Hoy | Decisión |
|---|---|---|
| la primera vuelta (sólo la foto) | nada | INFO `Avisos de las favoritas: primera vuelta, sólo la foto \| estrategias=` |
| una vuelta | nada (devuelve las cuentas a quien llama) | INFO `Avisos de las favoritas \| cambios= correos= sin_confirmar= cerradas=` |
| cuentas borradas (`privacy.closed`) | se saltan, sin decirlo | se cuentan en `cerradas=` |

### `edgefolio/free.py` — las gratis y las novedades

| Sitio | Hoy | Decisión |
|---|---|---|
| `claim`: la gratis sale | nada | INFO `Gratis mandada \| estrategia= user_id= novedades=pendientes\|confirmadas\|no` |
| `add_claim`: el tope del día | `None` → `errFreeDaily` 429 | la línea del rechazo |
| `request_news` | nada | INFO `Novedades pendientes de confirmar \| origen=` |
| `confirm_news` | nada | INFO `Novedades confirmadas`, o `Novedades sin confirmar: enlace usado, viejo o inventado` |
| `unsubscribe` | nada | INFO `Baja de las novedades`, o `Baja: el enlace no es de nadie` (la respuesta es la misma a propósito) |
| `purge` | nada (devuelve las cuentas) | INFO `Limpieza de lo que ya no se guarda \| altas_sin_confirmar= gratis= buzones=` |

### `edgefolio/orders.py` — comprar y cobrar (PayPal, llamada de fuera)

| Sitio | Hoy | Decisión |
|---|---|---|
| `create`: `except PayPalError` | relanza `errPayPal` 502, sin línea | WARNING `PayPal no creó el pedido \| estrategias= total= moneda= \| <error>`; la línea del rechazo, también (5xx: WARNING) |
| `create`: el pedido | nada | INFO `Pedido creado \| pedido= user_id= estrategias= lotes= pack= total= moneda= codigo=sí\|no` (el código, nunca) |
| `settled`: `except PayPalError` | WARNING `PayPal no dio el pedido \| pedido= \| <error>` | se queda |
| `capture`: `except PayPalError` | pregunta a PayPal; sin respuesta, WARNING `Cobro sin confirmar` y relanza 502 | se queda; si PayPal ya lo había cobrado, INFO `Cobro que PayPal ya había hecho: se toma ese \| pedido= estado=` |
| `capture`: pendiente en PayPal | `PENDING`, 402, sin línea | INFO `Cobro pendiente en PayPal \| pedido=` |
| `capture`: no cuadra (otro importe, otra moneda, otro estado) | `FAILED`, 402, sin línea | WARNING `Cobro que no cuadra: el pedido queda FAILED \| pedido= estado= importe=bien\|distinto` |
| `capture`: pagado | nada | INFO `Pedido cobrado \| pedido= user_id= estrategias= total= moneda=` (sólo el cobro que lo pasó a pagado) |
| `capture`: cuenta borrada, estrategia que salió | `errAccountClosed`, `errStrategyGone` | la línea del rechazo |
| `issue_links`: enlaces nuevos | nada | INFO `Enlaces de descarga \| pedido= nuevos=` (pedir el recibo otra vez no escribe) |
| `email_receipt` sin correo | nada | nada: un pedido sin correo no tiene a quién mandarlo; el correo que sale lo apunta el núcleo |

El texto de `PayPalError` (`paypal.py`) lleva hasta 200 caracteres de la respuesta de PayPal: su error (nombre, motivo,
`debug_id`), no datos de quien compra. Se queda hasta la migración.

### `edgefolio/downloads.py` — los enlaces de descarga

| Sitio | Hoy | Decisión |
|---|---|---|
| `one`: una descarga gastada | nada | INFO `Descarga \| estrategia= tipo=pago\|gratis formato=pine\|zip` (el token, nunca) |
| `all_in_one`: el zip de todo | nada | INFO `Descarga de todo en un zip \| ficheros= rechazados=` |
| `all_in_one`/`usable`: `except Refusal` | se guarda el primero y sigue | se queda: si no sale ninguno, el primer rechazo va a la respuesta (y a su línea); los demás, contados en `rechazados=` |
| `checked`/`spend` | `Refusal` (404, 410, 429, 403) | la línea del rechazo |

### `edgefolio/mine.py` — Mis estrategias y las favoritas

| Sitio | Hoy | Decisión |
|---|---|---|
| `renew`: enlace nuevo de pago | nada | INFO `Enlace renovado \| user_id= estrategia= tipo=pago pedido= version=` (si otra petición ya lo hizo, nada) |
| `renew`: enlace nuevo gratis | nada | INFO `Enlace renovado \| user_id= estrategia= tipo=gratis version=` |
| `set_favourite` | nada | INFO `Favorita guardada \| user_id= estrategia= nueva=sí\|no avisos=nv,pd` |
| `delete_favourite` | nada | INFO `Favorita quitada \| user_id= estrategia= borradas=` |
| `strategy_or_404`, `errNotOwned`, `errUpdateExpired`, `errNoLongerFree` | `Refusal` | la línea del rechazo |

### `edgefolio/proofs.py` — demostrar un correo

| Sitio | Hoy | Decisión |
|---|---|---|
| `request`: enlace nuevo | nada | INFO `Prueba de correo pedida \| user_id= prueba=` |
| `request`: no se manda (ya demostrado, uno hace menos de un minuto, cinco pendientes) | `None`, la misma respuesta (a propósito) | INFO `Prueba de correo sin mandar \| user_id= motivo=demostrado\|reciente\|pendientes`, con la prueba o cuántas: la respuesta no lo dice, el log sí |
| `forget` | nada | INFO `Prueba de correo anulada: no salió \| user_id=` |
| `confirm` | nada | INFO `Correo demostrado \| user_id= prueba=`; un enlace que no vale, la línea del rechazo (`errProofExpired`) |

### `edgefolio/your_data.py` — «Tus datos» (el núcleo los corre en su reloj)

| Sitio | Hoy | Decisión |
|---|---|---|
| `erase` | nada (el núcleo dice «hecha en 0.1 s») | INFO `Tus datos: lo de la tienda, borrado \| user_id= pedidos_anonimos= gratis= favoritas= novedades= buzones= pruebas=` |
| `export` | nada | nada: es una lectura, y el núcleo apunta la exportación (`exportada en …`) |

### `edgefolio/routes.py` — el endpoint

| Sitio | Hoy | Decisión |
|---|---|---|
| `_refused`: cada `Refusal` | la respuesta, sin línea | INFO `Rechazo \| metodo= ruta=<regla> clave= estado= user_id= [campo=]` (WARNING si es 5xx); la regla (`/api/download/<token>`), nunca la ruta con su token |
| `_download`: un rechazo abierto en la pestaña | redirige a la tienda | la misma línea del rechazo, antes de redirigir |
| `link`: sin `ZLECITOOL_PUBLIC_URL` | `errLater` 503 | WARNING `Enlace sin hacer: falta ZLECITOOL_PUBLIC_URL \| destino=`, y la línea del rechazo |
| `_email_receipt` sin dirección pública | WARNING `Recibo sin mandar: falta ZLECITOOL_PUBLIC_URL \| pedido=` | se queda (con el logger del módulo, `edgefolio.routes`) |
| `ask_proof`: tope de la dirección (`proof_to`) | no manda, la misma respuesta | INFO `Prueba de correo sin mandar \| user_id= motivo=tope_de_la_dirección` |
| `ask_proof`: sin dirección pública | `forget` y `errLater` 503 | WARNING `Prueba de correo sin mandar: falta ZLECITOOL_PUBLIC_URL \| user_id=`, y la del rechazo |
| `thumb`: `except KeyError` | 404 | nada: una raíz que no es de un gráfico del catálogo (un enlace viejo, un robot); la respuesta lo dice |
| `thumb`: `except OSError` | 404 | WARNING `Miniatura sin hacer \| grafico= \| <error>`: el gráfico estaba al arrancar y ya no (un `import --prune` con la tienda en marcha) o está roto |
| `client_key`: `except ValueError` | la clave es `remote_addr` tal cual | nada: no es una IP (un socket), y la clave del límite sigue valiendo |
| `_guarded`: un código que no vale | cuenta para el tope | nada: lo dice la respuesta (`code_status`), y pasar el tope es un rechazo con su línea |
| la línea de cada petición (regla, cuenta, resultado, tiempo) | la de werkzeug o gunicorn | **0.36**: el núcleo, con `zlecitool.requests` (`GET /s/<strategy_id> 200 \| ms=12 user=42`, con `error=errAlgo` en un rechazo), sin IP ni consulta; la de werkzeug se va. La tienda no escribe líneas de petición |

### `edgefolio/catalogue.py` y `edgefolio/shop.py` — la carga del catálogo

| Sitio | Hoy | Decisión |
|---|---|---|
| `_bundles`: un lote fuera | 2 × ERROR, con otro formato | ERROR `Lote fuera: nombra estrategias que el catálogo no trae \| lote= ausentes=`, `Lote fuera: no tiene estrategias \| lote=` y `Lote fuera: no cuesta menos que sus estrategias sueltas \| lote= precio= sueltas=` |
| el catálogo, cargado | nada | INFO `Catálogo cargado \| estrategias= lotes= niveles= vistas_previas_ausentes= graficos_ausentes=`, una por carga; WARNING si falta alguno |
| `Shop`: la tienda montada | nada | INFO `Tienda en marcha \| paypal=fake\|sandbox\|live estrategias= lotes=` |
| `number`: `except (TypeError, ValueError)` | `None` | nada: una celda vacía o que no es un número es «sin dato»; corre por cada celda |
| `forest_size`, `script_expiry`, `chart_version`: `except OSError` | 0, `None`, `""` | nada en cada una: lo cuenta la línea de la carga (`vistas_previas_ausentes=`, `graficos_ausentes=`) |
| `script_expiry`: `except ValueError` | `None` | WARNING `Caducidad que no es una fecha \| fichero=` (una cabecera rota; raro) |
| `read_release`: `except (OSError, ValueError)` | `{}` | sin el fichero, nada (un catálogo de antes de los paquetes); roto, WARNING `release.json sin leer \| fichero=` |
| `release_date`: `except ValueError` | `None` | nada: una fila sin fecha de publicación; corre en cada petición |
| `resolve`: `except (binascii.Error, …)` | `None` | nada: un id que no es de nadie; la respuesta (404 o la tienda) lo dice; corre en cada petición |

### `edgefolio/levels.py`

| Sitio | Hoy | Decisión |
|---|---|---|
| `load`: `except (OSError, ValueError)` | ERROR `%s no se lee: %s` | ERROR `Niveles sin leer: el árbol enseña la puntuación \| fichero= \| <error>` |
| entradas que no valen | ERROR | ERROR `Niveles que no valen, fuera \| fichero= entradas=` |
| `number`: `except` | `None` | nada: lectura con valor por defecto |

### `edgefolio/media.py`

| Sitio | Hoy | Decisión |
|---|---|---|
| `except ImportError` (Pillow) | sin miniaturas: el PNG entero | WARNING `Sin Pillow: las miniaturas salen en PNG`, al importar |
| `make_thumb`: `except BaseException` | borra el temporal y relanza | se queda; una miniatura hecha, DEBUG (una por gráfico, no hace falta en producción) |
| `thumb`: `except FileNotFoundError` | la que haya | nada: es la primera vez (aún sin miniatura) |
| `fx`: `except (OSError, ValueError)` | sólo dólares | WARNING `Cambios de moneda sin leer: los precios, sólo en dólares \| fichero=`, una vez por proceso (corre en cada página) |

### `edgefolio/formats.py`

| Sitio | Hoy | Decisión |
|---|---|---|
| `feature_names`: `except (OSError, ValueError)` | `{}` | WARNING `features.json sin leer: el zip sale sin los nombres de los valores \| fichero=` (una vez: `lru_cache`) |

### `edgefolio/release.py` y `edgefolio/cli.py` — los comandos

| Sitio | Hoy | Decisión |
|---|---|---|
| `import_package`: `except pub.ContractError` | relanza `Refused` | se queda; el comando lo apunta |
| `import_package`: `except Exception` | relanza `Refused` con el tipo y el mensaje, sin la traza | ERROR con la traza (`log.exception`) si no es `Refused` ni `ContractError`: falló a medias algo que no se esperaba |
| `import_package`: hecho | lo dice el comando con `click.echo` | INFO `Catálogo importado \| contrato= estrategias= ficheros= scripts= miniaturas_borradas= commit=` |
| `import`: `except release.Refused` | `ClickException` | WARNING `Importación rechazada \| paquete= problemas=`, y la excepción |
| `import`: `except ModuleNotFoundError` | relanza (o `ClickException` sin pandas) | se queda |
| `levels` | `click.echo` | INFO `Niveles publicados \| estrategias= de=`; sin ningún script, nada (lo dice el comando y no cambia nada) |
| `restore-scripts` | `click.echo` | INFO `Scripts de pago restaurados \| n= commit=` |
| `fx-update`: `except fx.FAILURES` | `ClickException` | se queda; lo dice `fx.update` |
| `send-alerts`: `except RuntimeError` | `ClickException` | se queda; lo dice `alerts.run` |
| `subscribers` | el CSV a la salida | INFO `Lista de las novedades sacada \| direcciones=`: saca correos de personas, que quede su rastro |

`catalogue/publish.py` (fuera del paquete: el script que comparten la tienda y el generador) escribe con `print`: es su
salida de comando, no un log.

### `edgefolio/search.py`, `edgefolio/settings.py`

`integer` y `number_param` relanzan un `Refusal` (la línea del rechazo); `_cutoffs` relanza el `ValueError` con su
explicación (la tienda no arranca con `GRADE_CUTOFFS` mal escrito). Se quedan.

### `edgefolio/paypal.py` — fuera de esta ronda

Un cliente de PayPal propio, sin una línea, con 2 `except` (la red, y una respuesta sin la forma de siempre). Choca con
la 0.35 (los pagos son del núcleo, CONTRATO §10, «Pagar: Stripe y PayPal»): **se va con esa migración**, que ya estaba
pendiente, y con él sus logs. No bloquea nada de esta ronda: las líneas de los pedidos y los cobros están en
`orders.py`, que se queda.

## El frontal y los cambios de pantalla (esperan a la 0.36)

El frontal no tiene hoy con qué escribir como pide la pauta. El núcleo 0.36 trae `zt.log` (CONTRATO §27, «Los logs»;
`log.js`, en todas las páginas): `zt.log.debug` y `zt.log.info(qué, datos)`, sólo a la consola; `zt.log.warn`, a la
consola y al servidor (WARNING); `zt.log.error(qué, datos|Error)`, a la consola y al servidor (ERROR), por
`POST /zt/log`, con el logger `zlecitool.front`, en el log de la tienda. `datos`: un objeto plano de ids y referencias (8
claves como mucho, valores cortos), nunca contenido. Y `zt.log.view(tipo, nombre)` para los cambios de ventana. El
núcleo recoge solo `error`, `unhandledrejection` y los `zt.fetchJSON` sin red o con 5xx: eso no se repite aquí. Hasta
que la tienda suba a la 0.36, no se toca (nada de parches locales). Lo que se hará entonces:

**Por qué `App.fail` escribe**: la tienda no pide con `zt.fetchJSON`, sino con su `lib/api.js`, así que el núcleo no
ve sus fallos de red ni sus 5xx. `App.fail` decide: un fallo de la página (sin código, no de red), `zt.log.error`; uno
de red, `zt.log.info` (a la consola: no llegó al servidor, y mandárselo fallaría igual); un 5xx, nada más (el servidor
ya lo apuntó, y su aviso, §22); un rechazo con su clave (4xx), nada (la línea del rechazo y la de la petición, en el
servidor).

### Cada `catch`

| Sitio | Hoy | Con la 0.36 |
|---|---|---|
| `app.js` `App.fail` (el que reciben 18 de los 26 `catch` de `app.js`) | `console.error(e)` si no tiene código ni es de red | arriba: `zt.log.error('Fallo de la página', e)`; de red, `zt.log.info`; 5xx y 4xx, nada |
| `app.js:105, 106, 108, 359, 380, 408, 425, 434, 642` | `this.fail(e)` | por `fail` |
| `app.js:318, 452, 496, 513, 557, 571, 582, 632, 705` | lo esperado (404, 400 de un campo, 401) se trata; lo demás, `fail` | por `fail` |
| `app.js:107` (`/api/fx`) | nada: los precios, en dólares | `zt.log.warn('Cambios de moneda sin cargar', {estado})`, una vez |
| `app.js:109` (`/api/me`) | nada: como sin cuenta | `zt.log.warn('Cuenta sin cargar', {estado})` |
| `app.js:365` (la vista previa del script) | nada: la vista previa, vacía | `zt.log.warn('Vista previa sin cargar', {estrategia: id})` |
| `app.js:541` (`/logout`) | nada: a la tienda igual | nada: salir ya lo apunta el núcleo |
| `app.js:719, 754, 779` (`scrollTo`), `819` (`setPointerCapture`) | nada | nada: el navegador no lo admite y no pasa nada |
| `tree.js:118` (`ui.json` del árbol) | `{}` | `zt.log.warn('Textos del árbol sin cargar')` |
| `tree.js:119` | relanza | se queda |
| `tree.js:137` (`signDisplay`) | `false` | nada: un navegador viejo |
| `tree.js:215` (el árbol no se monta) | el error en la pantalla | `zt.log.error('Árbol sin montar', {estrategia: id})` con el `Error` |
| `tree.js:226` (el bosque del propietario) | «no se pudo» en la pantalla | `zt.log.warn('Bosque del propietario sin cargar', {estrategia: id})` |
| `lib/api.js:23, 29` | relanzan como error de red | se quedan (lo dice `fail`) |
| `lib/route.js:5` | el id tal cual | nada: la ficha dice que no la encuentra |
| `lib/saved.js:7, 16, 23` | el valor por defecto | nada: sin `localStorage` (privado, bloqueado), se sigue sin recordar |

Los que quedan sin atrapar (`error`, `unhandledrejection`) los recoge el núcleo.

### Cada cambio de ventana

Las pantallas de la tienda son una sola página (`/`, `/s/<id>`, `/s/<id>/tree`, `/mine`, `/thanks`, con
`history.pushState`): llegar a ella lo apunta la línea de la petición, y lo demás no recarga. Así que la tienda llama a
`zt.log.view` ella misma, en un solo sitio, `App.componentDidUpdate` (`sync(prevState)`), comparando con el estado de
antes: una vez por cambio, nunca por pintura, y vale para `go()` y para atrás/adelante (`onPop`). Siempre con un nombre
fijo de la tienda, **nunca un dato** (ni la estrategia de la ficha, ni lo buscado):

| Tipo | Nombre | Cuándo |
|---|---|---|
| `"screen"` | `shop`, `detail`, `mine`, `thanks` | cambia `page` |
| `"tab"` | `overview`, `tree` | cambia `detTab` (la ficha y «Cómo decide») |
| `"tab"` | `lite`, `pro` | cambia `mode` |
| `"tab"` | la clave de la pestaña de Lite (`hot`…) | cambia `liteTab` |
| `"tab"` | `table`, `cards` | cambia `pview` (la vista de Pro) |
| `"dialog"` | `free`, `tour`, `install`, `compare`, `pack` | se abre uno (`freeFor`, el recorrido, `instFor`, `cmpOpen`, `packOpen`) |

Los diálogos de la tienda no son `zt.openDialog` (son las capas del diseño, `lib/modal.js`): el núcleo no los apunta
solo, y por eso van en la tabla. El nombre sale de la clave del estado, no del `aria-label` (que va traducido).

## Privacidad

- **La línea de cada petición** (del núcleo): con `python app.py`, el núcleo manda la de werkzeug al fichero del día, y
  lleva la IP, la ruta con sus credenciales (`/api/download/<token>`, `/api/news/confirm?token=…`,
  `/api/download/all?t=…`, `/thanks?token=<pedido>`) y la consulta tecleada: en este recorrido,
  `GET /api/strategies?q=Zelda%20Logsprueba`. También el `Debugger PIN` de werkzeug al arrancar. Con gunicorn, el
  `accesslog = "-"` de `gunicorn.conf.py` (su formato por defecto: IP, petición con su consulta, referer y agente) lo
  manda a la salida estándar. Es de toda la familia y del núcleo: va a «Para el núcleo» de `ESTADO.md`; aquí no se
  parchea. La 0.36 la cambia por la suya (`zlecitool.requests`, por la regla, sin IP ni consulta) y quita la de
  werkzeug; el `accesslog` de `gunicorn.conf.py` es de la tienda, y al subir a la 0.36 pasa a `accesslog = None`,
  como la plantilla (decidido el 15-11-2026; abajo, «Lo que depende de la 0.36», 5).
- Las líneas de la tienda nombran las cuentas por su id y lo demás por su clave; nunca un correo (las de los pedidos y
  las pruebas sin él), un código de descuento (sólo si se aplicó) ni un token de enlace.

## Lo que depende de la 0.36

Al subir la etiqueta de `requirements.txt` a la 0.36 (CONTRATO §27, «Los logs»):

1. **El frontal**: `zt.log` en `App.fail`, en los 6 `catch` de la tabla y `zt.log.view` en `App.componentDidUpdate`
   (arriba, «El frontal y los cambios de pantalla»). Sus pruebas, en el navegador de la sesión de pytest (un solo
   Chromium): un fallo de la página llega a `POST /zt/log` y queda en el log con `zlecitool.front`; un cambio de pantalla,
   de pestaña y de diálogo, con su nombre fijo.
2. **`external_call`** (`from zlecitool_core.observability.trace import external_call`) alrededor del `httpx.get` de
   `fx.fetch`: las líneas «API → / API ← / API ✗» con su tiempo. El WARNING de `fx.update` se queda (dice qué fichero
   sigue como estaba). La de PayPal se va con la migración de los pagos.
3. **La línea de cada petición es del núcleo** (`zlecitool.requests`, con `error=errAlgo` en un rechazo). La línea
   `Rechazo |` de `routes.py` se queda sólo donde dice lo que la del núcleo no ve: el campo que no valía (`campo=`), el
   rechazo de un enlace abierto en la pestaña (el núcleo ve un 303, no la clave) y los 5xx en WARNING; los demás
   rechazos ya los dice `error=errAlgo`. Las decisiones que no son un rechazo (la dirección pública que falta, el tope
   de una dirección, la miniatura) se quedan.
4. **Las comprobaciones de `check_tool()`** (sin salidas propias ni `print`; con `privacy_sample`, que el correo y el
   nombre de la cuenta de prueba no salgan en los logs): `tests/test_privacy.py` ya pasa `privacy_sample`.
5. **El `accesslog` de gunicorn**: con la línea del núcleo, sobra y lleva la IP y la consulta. En el mismo cambio que
   sube la etiqueta, `accesslog = "-"` pasa a `accesslog = None` en `gunicorn.conf.py`, como la plantilla (decidido el
   15-11-2026; el núcleo lo dirá en «Para las herramientas» de su CHANGELOG). Hasta entonces no se toca.

## Lo añadido (F3, 15-11-2026)

Lo que no depende del núcleo, ya en el código; lo demás, en «Para el núcleo» de [../ESTADO.md](../ESTADO.md).

| Capa | Antes | Después | Qué |
|---|---|---|---|
| Frontal | 1 | 1 | sin tocar: espera al ayudante de la 0.36 (6 `catch` más escribirán, 10 seguirán callando con su porqué) |
| Servidor | 6 | 53 | las tres tareas, los pedidos y los cobros, los enlaces y las descargas, las gratis y las novedades, las pruebas de correo, las favoritas, «Tus datos», la carga del catálogo, los comandos; el BCE (2) y PayPal (4), llamadas de fuera |
| Endpoint | 1 | 6 | una línea por rechazo (por su regla), la dirección pública que falta (3), la miniatura que no sale y el tope de correos de una dirección |
| Cambio de ventana | 0 | 0 | espera a la 0.36 |
| **Total** | **8** | **60** | 59 sitios en Python (`log.…`), en 17 ficheros de `edgefolio/` |

`except` de la ronda: los 35 con su decisión. 28 relanzan o escriben (antes, 19; 3 de ellos, en la línea que resume la
carga del catálogo) y 7 callan con su porqué, escrito al lado (`number`, `release_date`, `resolve`, `levels.number`, la
primera miniatura, `client_key`, una raíz de miniatura que no es de nadie). `catch` del JavaScript: 37, sin tocar.

Por el camino:

- `fx.update(out)`: lo comparten la tarea y el comando `fx-update` (antes, cada uno con su `fetch` y su `write`).
- `downloads.claim_download` da de qué enlace era (`"paid"`, `"free"` o `""`) en vez de `True`/`False`: la línea de la
  descarga lo dice.
- `routes.py` escribe con su logger (`edgefolio.routes`), no con `current_app.logger`.
- `release.py` tiene logger: la importación que falla a medias por algo que no se esperaba deja su traza.

Las pruebas, en `tests/test_logs.py` (16, sin navegador): un error deja su línea (PayPal que no crea el pedido, un cobro
que no cuadra, `levels.json` roto, el BCE caído), un cambio de estado la suya (el pedido, su cobro y sus enlaces una
vez aunque se cobre dos veces, las descargas, la gratis y las novedades, las pruebas de correo, las favoritas, el
borrado de una cuenta), cada tarea dice lo que hizo (y la repetición, que nada), un rechazo deja una sola línea con la
regla de su ruta, el formato «Qué pasó | clave=valor» se cumple, y ni el correo de la cuenta de prueba, ni lo
tecleado, ni un código, ni un token salen en ninguna línea, de la tienda ni del núcleo.

## Verificado (F4, 15-11-2026)

- `pytest`: 396 pasan y 1 se salta (`test_formats.py`: los scripts de pago de verdad no están en esta máquina); los 16
  de `tests/test_logs.py`, entre ellos.
- El recorrido de F0, otra vez, con una base de datos nueva, y las tres tareas a mano (`send_alerts` dos veces) y
  `flask --app app edgefolio subscribers`, leyendo `edgefolio-2026-11-15.log`. Cada paso deja su línea:
  `Rechazo | método=GET ruta=/api/strategies clave=errRequest estado=400 user_id=- campo=size`, `Gratis mandada |
  estrategia=PYPL_1Day_1MAC_2a2425c6 user_id=- novedades=pendientes`, `Descarga | … tipo=gratis formato=pine`,
  `Novedades confirmadas`, `Pedido creado | pedido=FAKE-… user_id=- estrategias=1 lotes=0 pack=no total=58.40
  moneda=USD código=sí`, `Pedido cobrado`, `Enlaces de descarga | … nuevos=1`, las dos descargas de pago, `Prueba de
  correo pedida | user_id=1 prueba=1`, `Correo demostrado`, los rechazos de Mis estrategias (`errProofExpired`,
  `errNotOwned`), dos `Favorita guardada` y una `Favorita quitada`; y `Cambios del BCE guardados | día=2026-11-13
  cambios=31`, `Avisos de las favoritas: primera vuelta, sólo la foto | estrategias=94`, `Limpieza de lo que ya no se
  guarda | altas_sin_confirmar=0 gratis=0 buzones=0`, `Tarea ya hecha: nada que hacer | tarea=send_alerts vez=…` y
  `Lista de las novedades sacada | direcciones=1`.
- La consola del navegador, como en F0: sólo los «Failed to load resource» de los rechazos buscados.
- En toda la carpeta `C:\Users\leci\Documents\tuisku\logs`, el correo de la cuenta de prueba
  (`logs-edgefolio@example.test`, también con `%40`) no sale ninguna vez. El nombre que tecleó («Zelda Logsprueba», en
  la búsqueda) sale 2 veces en `edgefolio-2026-11-15.log`, las dos en la línea de werkzeug del núcleo
  (`GET /api/strategies?q=Zelda%20Logsprueba`), una por recorrido: es el punto 4 de «Para el núcleo» de
  [../ESTADO.md](../ESTADO.md). En las líneas de la tienda, ninguna.

## Segunda vuelta (+25 %), 16-11-2026

El dueño ve pocas líneas: cada capa sube un 25 %, y ninguna se queda por debajo de 30. Partimos del recuento del
orquestador sobre `_ztool_dev` (e682d91d). En Python cuenta cada `….debug/info/warning/error/exception/critical(`, y va al
endpoint si el fichero es de rutas (aquí, sólo `routes.py`). En JS cuenta cada `console.*(`, `zt.log…(` y
`log.debug/info/warn/error/view(`.

| Capa | Hoy | Objetivo | Previstas |
|---|---|---|---|
| Cliente | 1 | ≥ 30 | 37 |
| Servidor | 52 | ≥ 65 | 71 |
| Endpoint | 5 | ≥ 30 | 17; 30 con la decisión del 24-11-2026 (abajo) |

**Dos líneas que el recuento no veía.** `Catálogo cargado` (`catalogue.py`) y `Rechazo` (`routes.py`) se escriben
con `(log.warning if … else log.info)(…)`, y el recuento no las cuenta. Pasan a un `if` con sus dos llamadas: no son
sucesos nuevos, pero ahora suman (2 en el servidor y 2 en el endpoint).

### Cliente: el ayudante `static/js/lib/log.js`

Hasta la 0.36 no hay `zt.log`, así que la tienda trae un ayudante mínimo, en su propio módulo:
`log = (window.zt && zt.log) || <respaldo>`, mirado en cada llamada. El respaldo escribe sólo en la consola,
«[edgefolio] nivel Qué | k=v k=v», con `debug`, `info`, `warn`, `error` y `view(tipo, nombre)`; nada va al servidor.
Al subir a la 0.36 usará `zt.log` sin cambiar nada más. Sus cuatro `console.*` cuentan (4). En los datos sólo van
ids y referencias (la estrategia, el pedido, un estado HTTP, cuántas): ni un correo, ni lo buscado, ni un código.

| Fichero, función | Línea | Nivel |
|---|---|---|
| `lib/log.js` (el respaldo) | sus `console.debug/info/warn/error` | — (4) |
| `app.js` `componentDidUpdate` → `views(prev)` | `view('screen', page)`: `shop`, `detail`, `mine`, `thanks` | view |
| ″ | `view('tab', 'detail.overview'\|'detail.tree')`, si la pantalla sigue siendo la ficha | view |
| ″ | `view('tab', 'lite'\|'pro')` (`mode`) | view |
| ″ | `view('tab', 'lite.<pestaña>')` (`liteTab`: `hot`, `new`, `free`…) | view |
| ″ | `view('tab', 'pro.<vista>')` (`pview`: `table`, `rows`, `cards`) | view |
| ″ | `view('dialog', 'free'\|'tour'\|'install'\|'compare'\|'pack')`, al abrirse cada uno (5) | view |
| `app.js` `fail` | un fallo de la página (sin código, no de red), con el `Error` (en lugar del `console.error`) | error |
| ″ | un fallo de red | info |
| ″ | un 5xx (el servidor ya lo apuntó) | info |
| `app.js` `componentDidMount`, `/api/fx` | los cambios de moneda no llegan: precios en dólares | warn |
| ″, `/api/me` | la cuenta no llega: la página sigue como sin cuenta | warn |
| `app.js` `fetchPreview` | la vista previa de un script no llega (con su estado) | warn |
| `app.js` `fetchOne` | una estrategia que ya no está (404): olvidada del carrito, Comparar y las favoritas | info |
| `app.js` `loadQuote` | el servidor ya no vende algo del carrito: fuera (cuántas) | warn |
| `app.js` `dropOwned` | lo que ya es de la cuenta sale del carrito (cuántas) | info |
| `app.js` `checkout` | el pedido está hecho: a PayPal (`pedido`) | info |
| `app.js` `capture` | el recibo, de vuelta de PayPal (`pedido`, `pagado_ahora`, `enlaces`) | info |
| ″ | un cobro sin confirmar o pendiente: la página se queda con su pedido | warn |
| `app.js` `afterSignIn` | las favoritas del navegador pasan a la cuenta (cuántas, cuántas no) | info |
| `app.js` `renew` | un enlace nuevo en Mis estrategias (`estrategia`) | info |
| `app.js` `setFav` | una favorita guardada o quitada en la cuenta (`estrategia`, `on`) | info |
| ″ | el servidor no la guardó: vuelve a como estaba | warn |
| `app.js` `askProof` | la prueba de un correo, pedida (sin el correo) | info |
| `app.js` `peekProof` | el enlace de la prueba ya no vale | info |
| `app.js` `confirmProof` | el correo, demostrado | info |
| `app.js` `sendFree` | la gratis, pedida (`estrategia`) | info |
| `tree.js` `sharedData` | los textos del árbol (`trees/ui.json`) no llegan | warn |
| `tree.js` `load` | el árbol no se monta (`estrategia`, con el `Error`) | error |
| ″ | el bosque del propietario no llega | warn |

Son 37: 4 del respaldo, 10 cambios de ventana, 3 de `fail` (antes, 1) y 20 sucesos. `scrollTo`, `setPointerCapture`,
`localStorage`, `decodeURIComponent` y `signDisplay` siguen sin escribir nada, con el porqué de la primera vuelta.
Nada por pintura: los cambios de ventana sólo cuando cambia su clave; el presupuesto (que corre con cada cambio del
carrito) sólo cuando quita algo.

### Servidor (+17 sucesos y la línea que no se veía)

| Fichero, función | Línea | Nivel |
|---|---|---|
| `catalogue.py` `Catalogue.__init__` | `Catálogo cargado`, en un `if` (ya existía) | info / warning |
| `search.py` `index_of` | `Índice de búsqueda hecho \| estrategias= ms=` (uno por catálogo) | debug |
| `downloads.py` `_tokens` (de `usable` y `all_in_one`) | más de 100 enlaces en una petición: se miran los 100 primeros | warning |
| `downloads.py` `spend` | otra petición a la vez se llevó la última descarga | info |
| `downloads.py` `checked` | el script de pago que no está en `STRATEGIES_DIR` (`errFileMissing`) | warning |
| `free.py` `claim` | el script de una gratis que no está | warning |
| `free.py` `add_claim` | el tope del día: `por=quien_pide\|buzón` (el rechazo no dice cuál) | info |
| ″ | renovar cuando otra petición ya dio uno que sirve (un doble clic) | debug |
| `mine.py` `script_path` | el script del propietario que no está | warning |
| `mine.py` `listing` | lo comprado que ya no está en el catálogo, sin enseñar (cuántas) | debug |
| `orders.py` `capture` | un cobro repetido: el pedido ya estaba pagado | info |
| ″ | un pedido de una cuenta borrada: no se cobra (`user_id` del pedido) | info |
| ″ | una estrategia salió del catálogo mientras se pagaba: no se cobra (cuántas) | warning |
| `your_data.py` `export` | lo de la tienda, exportado (cuántas partes) | info |
| ″ | partes que no caben en el zip, fuera (cuáles) | warning |
| `release.py` `import_package` | `Importación empieza \| paquete= scripts= prune=` | info |
| ″ | `Importación: paquete comprobado \| contrato= filas= scripts= faltan= distintos=` | info |
| `cli.py` `restore-scripts` | la carpeta ya tiene scripts: no se toca | info |

### Endpoint (+10 sucesos y la línea que no se veía)

| Fichero, función | Línea | Nivel |
|---|---|---|
| `routes.py` `_log_refusal` | `Rechazo`, en un `if` (ya existía) | info / warning |
| `routes.py` `confirm_news` | un enlace de confirmar las novedades sin la forma de los nuestros (`free.confirm_news` ni se llama) | info |
| `routes.py` `_strategy_page` | una ficha que no existe: a la tienda (sin el id tecleado) | info |
| ″ | una ficha por su dirección de antes (el base64 de la tienda vieja): a la nueva | info |
| `routes.py` `_guarded` | una red llega al tope de códigos de descuento que no valen (¿alguien probándolos?), una vez por ventana | warning |
| `routes.py` `create_order` | la cookie de quien compra, nueva en este navegador | debug |
| `routes.py` `capture` | el recibo sin enlaces: ni el navegador que compró ni su cuenta | info |
| `routes.py` `_looked_at` | un enlace mirado con HEAD (un escáner de correo), sin gastar | info |
| `routes.py` `my_strategies` | sin lo hecho sin cuenta: el correo de la cuenta no está demostrado | debug |
| `routes.py` `script` | el script completo, enseñado a su dueño (el árbol del propietario) | info |
| `routes.py` `peek_proof` | un enlace de prueba que no vale para esta cuenta (de otra, usado o caducado) | info |

**Por qué el endpoint se quedaba en 17** (el plan del 16-11-2026; el 24-11-2026 el dueño decidió que llegue a 30, en
«Endpoint hasta 30», más abajo). Las rutas de la tienda son finas, a propósito (regla 5 del
`CLAUDE.md`): `routes.py` recibe y responde, y lo que se decide pasa en los módulos de al lado, que el recuento suma al
servidor. Por ejemplo, el permiso de una descarga (`downloads.checked`), el de Mis estrategias (`mine`) o el cobro
(`orders.capture`). Quedan 22 rutas, y la línea de cada petición es del núcleo (0.36: `zlecitool.requests`, con
`error=errAlgo` en un rechazo). Para llegar a 30 habría que escribir una línea por petición o repetir en la ruta lo
que ya dice su módulo, y las dos cosas son relleno. Las 17 son decisiones que la línea del núcleo no ve.

### Lo añadido (segunda vuelta, 16-11-2026)

| Capa | Antes | Después | Objetivo |
|---|---|---|---|
| Cliente | 1 | 37 | ≥ 30 |
| Servidor | 52 | 71 | ≥ 65 |
| Endpoint | 5 | 17 (30 el 24-11-2026: abajo) | ≥ 30 |

Lo de la tabla del plan, con un cambio en el endpoint. La línea de `_start` (PayPal de verdad sin
`ZLECITOOL_PUBLIC_URL`) no hacía falta: `Settings.from_env` ya no deja arrancar así, con su explicación. En su lugar
entra la de `confirm_news`, el enlace de novedades sin la forma de los nuestros, que hasta ahora redirigía sin dejar
rastro.

- **El ayudante**, `static/js/lib/log.js`: `log.debug/info/warn/error/view`, con las firmas de `zt.log`. Mira
  `window.zt.log` en cada llamada; sin él, escribe en la consola «[edgefolio] nivel Qué | k=v». Lo importan `app.js` y
  `tree.js`. `App.fail` ya no usa `console.error`.
- **Las pruebas** (en `tests/test_logs.py`, más una en `tests/test_release.py`):
  - un cobro repetido, y otro desde un navegador sin la cookie de quien compró (el recibo sin enlaces);
  - una estrategia que sale del catálogo mientras se paga (WARNING, no se cobra);
  - un script de pago que falta en el servidor (WARNING);
  - un HEAD que sólo mira, y más de 100 enlaces en una petición;
  - el tope del día de las gratis, que dice cuál de los dos;
  - una ficha por su dirección de antes, y una que no existe, sin lo tecleado;
  - el tope de códigos de descuento que no valen (un solo WARNING, y nunca el código);
  - un enlace de prueba del correo que no es de nadie, Mis estrategias sin el correo demostrado y el script del
    propietario;
  - la exportación de «Tus datos»;
  - los tres pasos de la importación;
  - y, en el Chromium de la sesión, la página: un `/api/fx` que falla da su `warn`, y la pestaña «Cómo decide», la
    vuelta a la tienda y Pro dan sus tres `Vista`, con su nombre fijo y sin la estrategia.

### Endpoint hasta 30 (24-11-2026)

El dueño decide que el endpoint también llegue a 30, aunque las rutas sean finas. Para llegar sin meter lógica en
`routes.py` ni relleno, se escribe lo que la ruta sabe y el servicio no: qué recibió y qué no valía antes de llamarlo,
qué respuesta eligió y por qué, y cuántos resultados, nunca lo buscado. Es lo que la línea de cada petición del núcleo
no dirá (ella dice la regla, el estado, el tiempo y la cuenta), y ninguna la copia.

| Fichero, función | Línea | Nivel |
|---|---|---|
| `routes.py` `limited` | `Tope de peticiones \| limite=free\|proof tope= ventana_s=`: cuál de los topes saltó (el rechazo sólo dice `errTooMany`) | info |
| `routes.py` `text_language` | `ind_lang` que no es de los nuestros: las explicaciones, en el idioma de la petición (sin el valor) | debug |
| `routes.py` `strategies` | `Lista \| resultados= filas= pagina= por_pagina= filtros= busqueda=sí\|no`: cuántos y con cuántos filtros, nunca cuáles ni lo buscado | debug |
| `routes.py` `strategy` | la ficha pedida por su alias de antes (un carrito viejo): se da la de su id | debug |
| `routes.py` `fx` | los cambios de ejemplo del repo, aún sin los del día (una vez por proceso) | info |
| `routes.py` `quote` | `Presupuesto \| estrategias= lotes= pack= codigo=applied\|invalid\|sin total=` (el código, nunca) | debug |
| `routes.py` `capture` | `Recibo con enlaces \| pedido= por=cookie\|cuenta\|correo`: por qué los ve (`orders.link_access`, nueva; `may_see_links` la usa) | info |
| `routes.py` `_email_receipt` | `Recibo por correo \| pedido= idioma=` (sólo si el pedido tiene correo) | info |
| `routes.py` `download` | `?format=` que no es `pine` ni `zip`: se da el `.pine` (sin el valor) | info |
| `routes.py` `free_claim` | una gratis, con la sesión abierta, para otra dirección que la de la cuenta: no sale en Mis estrategias hasta demostrarla | info |
| `routes.py` `my_strategies` | `Mis estrategias \| user_id= estrategias= favoritas= correos_demostrados=` | debug |
| `routes.py` `ask_proof` | la prueba de un correo para otra dirección que la de la cuenta (sin ninguna de las dos) | info |
| `routes.py` `peek_proof` | el enlace de una prueba, abierto y sin confirmar (abrirlo no lo gasta) | info |

Las de `debug` son de lo que la página pide a menudo (cada lista, cada presupuesto, cada visita a Mis estrategias): en
desarrollo, en el fichero del día; en producción, el núcleo deja el paquete en INFO y no salen.

| Capa | Antes | Después | Objetivo |
|---|---|---|---|
| Cliente | 1 | 37 | ≥ 30 |
| Servidor | 52 | 71 | ≥ 65 |
| Endpoint | 5 | 30 | ≥ 30 |

Las pruebas, en `tests/test_logs.py`:

- el recibo dice por qué lleva enlaces y que se mandó por correo, sin el correo;
- una lista dice cuántos sin lo buscado, y lo mismo un idioma que no tenemos y la ficha por su alias;
- el presupuesto, sin el código;
- los cambios de ejemplo, una sola vez;
- el tope de la ruta dice cuál;
- un formato de descarga que no existe da el `.pine`, sin el valor;
- una cuenta que pide una gratis y una prueba para otra dirección, y que abre el enlace, sin ninguna de las dos
  direcciones.

### Claves sin tildes (24-11-2026)

La regla 25 de `CLAUDE.md` (y `docs/estandar/LOGS.md` del núcleo) pide las claves en minúsculas y sin tildes, para buscarlas
sin dudar. Las que las llevaban cambian: `método=` → `metodo=`, `límite=` → `limite=`, `pestaña=` → `pestana=`,
`página=` → `pagina=`, `tamaño=` → `por_pagina=`, `búsqueda=` → `busqueda=`, `código=` → `codigo=`, `día=` →
`dia=`, `gráfico=` → `grafico=`, `gráficos_ausentes=` → `graficos_ausentes=`, `versión=` → `version=` y
`pedidos_sin_dueño=` → `pedidos_anonimos=` (los pedidos que se quedan sin quién los hizo). Las tablas de arriba ya
van con las nuevas; «Verificado (F4)» cuenta lo que se vio el 15-11-2026, con las de entonces. Los valores fijos
(`sí`, `buzón`, `ya_están`) no son claves y se quedan.
