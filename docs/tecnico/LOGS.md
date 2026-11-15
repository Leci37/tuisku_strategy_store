# Los logs de Edgefolio

Ronda de logs de la familia, 15-11-2026, sobre `_ztool_dev` (63de2159) con el núcleo 0.35.0. Qué escribe la tienda en
cada capa, cada `except`/`catch` con su decisión, cada cambio de estado, cada llamada de fuera y cada tarea; lo que se
añade ya y lo que espera a la 0.36 del núcleo.

## La pauta, en corto

- Formato «Qué pasó | clave=valor clave=valor», en español (como los del núcleo: `Cuenta creada | user_id=1`).
- Las personas, por su id (`user_id=`); lo de la tienda, por su referencia: `pedido=<id de PayPal>`, `estrategia=<clave>`,
  `prueba=<id>`, `lote=<clave>`. **Nunca** un correo, lo tecleado (la búsqueda, un código de descuento), una IP, un
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
| traer los cambios | `fetch()` sin una línea | `update(out)`, que usan la tarea y el comando: INFO `Cambios del BCE guardados \| día= cambios=`; con `fx.FAILURES`, WARNING `BCE sin cambios nuevos \| fichero= error=` y relanza |
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
| `claim`: la gratis sale | nada | INFO `Gratis mandada \| estrategia= user_id= novedades=` |
| `add_claim`: el tope del día | `None` → `errFreeDaily` 429 | la línea del rechazo |
| `request_news` | nada | INFO `Novedades pendientes de confirmar \| origen=` |
| `confirm_news` | nada | INFO `Novedades confirmadas`, o `Novedades sin confirmar: enlace usado, viejo o inventado` |
| `unsubscribe` | nada | INFO `Baja de las novedades`, o `Baja: el enlace no es de nadie` (la respuesta es la misma a propósito) |
| `purge` | nada (devuelve las cuentas) | INFO `Limpieza de lo que ya no se guarda \| altas_sin_confirmar= gratis= buzones=` |

### `edgefolio/orders.py` — comprar y cobrar (PayPal, llamada de fuera)

| Sitio | Hoy | Decisión |
|---|---|---|
| `create`: `except PayPalError` | relanza `errPayPal` 502, sin línea | WARNING `PayPal no creó el pedido \| estrategias= total= \| <error>`; la línea del rechazo, también (5xx: WARNING) |
| `create`: el pedido | nada | INFO `Pedido creado \| pedido= user_id= estrategias= lotes= pack= total= código=sí\|no` (el código, nunca) |
| `settled`: `except PayPalError` | WARNING `PayPal no dio el pedido \| pedido= \| <error>` | se queda |
| `capture`: `except PayPalError` | pregunta a PayPal; sin respuesta, WARNING `Cobro sin confirmar` y relanza 502 | se queda; si PayPal ya lo había cobrado, INFO `Cobro que PayPal ya había hecho \| pedido=` |
| `capture`: pendiente en PayPal | `PENDING`, 402, sin línea | INFO `Cobro pendiente en PayPal \| pedido=` |
| `capture`: no cuadra (otro importe, otra moneda, otro estado) | `FAILED`, 402, sin línea | WARNING `Cobro que no cuadra \| pedido= estado= importe=bien\|distinto` |
| `capture`: pagado | nada | INFO `Pedido cobrado \| pedido= user_id= estrategias= total=` (sólo el cobro que lo pasó a pagado) |
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
| `renew`: enlace nuevo de pago | nada | INFO `Enlace renovado \| user_id= estrategia= tipo=pago versión=` (si otra petición ya lo hizo, nada) |
| `renew`: enlace nuevo gratis | nada | INFO `Enlace renovado \| user_id= estrategia= tipo=gratis versión=` |
| `set_favourite` | nada | INFO `Favorita guardada \| user_id= estrategia= nueva=sí\|no avisos=nv,pd` |
| `delete_favourite` | nada | INFO `Favorita quitada \| user_id= estrategia= borradas=` |
| `strategy_or_404`, `errNotOwned`, `errUpdateExpired`, `errNoLongerFree` | `Refusal` | la línea del rechazo |

### `edgefolio/proofs.py` — demostrar un correo

| Sitio | Hoy | Decisión |
|---|---|---|
| `request`: enlace nuevo | nada | INFO `Prueba de correo pedida \| user_id= prueba=` |
| `request`: no se manda (ya demostrado, uno hace menos de un minuto, cinco pendientes) | `None`, la misma respuesta (a propósito) | INFO `Prueba de correo sin mandar \| user_id= motivo=demostrado\|reciente\|pendientes`: la respuesta no lo dice, el log sí |
| `forget` | nada | INFO `Prueba de correo anulada: no salió \| user_id=` |
| `confirm` | nada | INFO `Correo demostrado \| user_id= prueba=`; un enlace que no vale, la línea del rechazo (`errProofExpired`) |

### `edgefolio/your_data.py` — «Tus datos» (el núcleo los corre en su reloj)

| Sitio | Hoy | Decisión |
|---|---|---|
| `erase` | nada (el núcleo dice «hecha en 0.1 s») | INFO `Tus datos: lo de la tienda, borrado \| user_id= pedidos_sin_dueño= gratis= favoritas= novedades= buzones= pruebas=` |
| `export` | nada | nada: es una lectura, y el núcleo apunta la exportación (`exportada en …`) |

### `edgefolio/routes.py` — el endpoint

| Sitio | Hoy | Decisión |
|---|---|---|
| `_refused`: cada `Refusal` | la respuesta, sin línea | INFO `Rechazo \| ruta=<método> <regla> clave= estado= user_id= [campo=]` (WARNING si es 5xx); la regla (`/api/download/<token>`), nunca la ruta con su token |
| `_download`: un rechazo abierto en la pestaña | redirige a la tienda | la misma línea del rechazo, antes de redirigir |
| `link`: sin `ZLECITOOL_PUBLIC_URL` | `errLater` 503 | WARNING `Enlace sin hacer: falta ZLECITOOL_PUBLIC_URL \| destino=`, y la línea del rechazo |
| `_email_receipt` sin dirección pública | WARNING `Recibo sin mandar: falta ZLECITOOL_PUBLIC_URL \| pedido=` | se queda (con el logger del módulo, `edgefolio.routes`) |
| `ask_proof`: tope de la dirección (`proof_to`) | no manda, la misma respuesta | INFO `Prueba de correo sin mandar \| user_id= motivo=tope_de_la_dirección` |
| `ask_proof`: sin dirección pública | `forget` y `errLater` 503 | WARNING `Prueba de correo sin mandar: falta ZLECITOOL_PUBLIC_URL \| user_id=`, y la del rechazo |
| `thumb`: `except KeyError` | 404 | nada: una raíz que no es de un gráfico del catálogo (un enlace viejo, un robot); la respuesta lo dice |
| `thumb`: `except OSError` | 404 | WARNING `Miniatura sin hacer \| gráfico= \| <error>`: el gráfico estaba al arrancar y ya no (un `import --prune` con la tienda en marcha) o está roto |
| `client_key`: `except ValueError` | la clave es `remote_addr` tal cual | nada: no es una IP (un socket), y la clave del límite sigue valiendo |
| `_guarded`: un código que no vale | cuenta para el tope | nada: lo dice la respuesta (`code_status`), y pasar el tope es un rechazo con su línea |
| la línea de cada petición (regla, cuenta, resultado, tiempo) | la de werkzeug o gunicorn | **0.36** (el núcleo) |

### `edgefolio/catalogue.py` y `edgefolio/shop.py` — la carga del catálogo

| Sitio | Hoy | Decisión |
|---|---|---|
| `_bundles`: un lote fuera | 2 × ERROR, con otro formato | ERROR `Lote fuera: … \| lote= ausentes=` / `\| lote= precio= sueltas=` |
| el catálogo, cargado | nada | INFO `Catálogo cargado \| estrategias= lotes= niveles= vistas_previas_ausentes= gráficos_ausentes=`, una por carga; WARNING si falta alguno |
| `Shop`: la tienda montada | nada | INFO `Tienda en marcha \| paypal=fake\|sandbox\|live estrategias= lotes=` |
| `number`: `except (TypeError, ValueError)` | `None` | nada: una celda vacía o que no es un número es «sin dato»; corre por cada celda |
| `forest_size`, `script_expiry`, `chart_version`: `except OSError` | 0, `None`, `""` | nada en cada una: lo cuenta la línea de la carga (`vistas_previas_ausentes=`, `gráficos_ausentes=`) |
| `script_expiry`: `except ValueError` | `None` | WARNING `Caducidad que no es una fecha \| fichero=` (una cabecera rota; raro) |
| `read_release`: `except (OSError, ValueError)` | `{}` | sin el fichero, nada (un catálogo de antes de los paquetes); roto, WARNING `release.json sin leer \| fichero=` |
| `release_date`: `except ValueError` | `None` | nada: una fila sin fecha de publicación; corre en cada petición |
| `resolve`: `except (binascii.Error, …)` | `None` | nada: un id que no es de nadie; la respuesta (404 o la tienda) lo dice; corre en cada petición |

### `edgefolio/levels.py`

| Sitio | Hoy | Decisión |
|---|---|---|
| `load`: `except (OSError, ValueError)` | ERROR `%s no se lee: %s` | ERROR `Niveles sin leer \| fichero= \| <error>` |
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
| `levels` | `click.echo` | INFO `Niveles publicados \| estrategias=`; sin ningún script, nada (lo dice el comando y no cambia nada) |
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

El frontal no tiene hoy con qué escribir como pide la pauta: el ayudante del núcleo (`zt.log` o como acabe llamándose,
que además manda los errores del navegador y los cambios de pantalla al log del servidor) llega con la 0.36. Hasta
entonces no se toca (nada de parches locales). Lo que se hará entonces:

### Cada `catch`

| Sitio | Hoy | Con la 0.36 |
|---|---|---|
| `app.js` `App.fail` (el que reciben 18 de los 26 `catch` de `app.js`) | `console.error(e)` si no tiene código ni es de red | `zt.log.error`, que llega al servidor; un fallo de red, a la consola sólo (`warn`); un rechazo con clave, nada: ya lo apunta el servidor |
| `app.js:105, 106, 108, 359, 380, 408, 425, 434, 642` | `this.fail(e)` | por `fail` |
| `app.js:318, 452, 496, 513, 557, 571, 582, 632, 705` | lo esperado (404, 400 de un campo, 401) se trata; lo demás, `fail` | por `fail` |
| `app.js:107` (`/api/fx`) | nada: los precios, en dólares | `zt.log.warn` (una vez) |
| `app.js:109` (`/api/me`) | nada: como sin cuenta | `zt.log.warn` |
| `app.js:365` (la vista previa del script) | nada: la vista previa, vacía | `zt.log.warn` con la estrategia |
| `app.js:541` (`/logout`) | nada: a la tienda igual | nada: salir ya lo apunta el núcleo |
| `app.js:719, 754, 779` (`scrollTo`), `819` (`setPointerCapture`) | nada | nada: el navegador no lo admite y no pasa nada |
| `tree.js:118` (`ui.json` del árbol) | `{}` | `zt.log.warn` |
| `tree.js:119` | relanza | se queda |
| `tree.js:137` (`signDisplay`) | `false` | nada: un navegador viejo |
| `tree.js:215` (el árbol no se monta) | el error en la pantalla | `zt.log.error` con la estrategia |
| `tree.js:226` (el bosque del propietario) | «no se pudo» en la pantalla | `zt.log.warn` |
| `lib/api.js:23, 29` | relanzan como error de red | se quedan (lo dice `fail`) |
| `lib/route.js:5` | el id tal cual | nada: la ficha dice que no la encuentra |
| `lib/saved.js:7, 16, 23` | el valor por defecto | nada: sin `localStorage` (privado, bloqueado), se sigue sin recordar |

Los errores del navegador que nadie atrapa (`window.onerror`, `unhandledrejection`) los recoge el ayudante del núcleo.

### Cada cambio de pantalla

En un solo sitio, `App.componentDidUpdate` (`sync(prevState)`), comparando con el estado de antes, una línea por cambio
(nunca por pintura):

- la pantalla: `page` (`shop`, `detail`, `mine`, `thanks`) y, en la ficha, `detTab` (`overview`, `tree`), con la
  estrategia (`detail`); vale para `go()` y para atrás/adelante (`onPop`);
- Lite o Pro (`mode`), la pestaña de Lite (`liteTab`) y la vista de Pro (`pview`: tabla o tarjetas);
- cada diálogo que se abre o se cierra (`syncModal`): la gratis, el recorrido, el tutorial de instalación, Comparar y el
  pack; y el carrito.

## Privacidad

- **La línea de cada petición** (del núcleo): con `python app.py`, el núcleo manda la de werkzeug al fichero del día, y
  lleva la IP, la ruta con sus credenciales (`/api/download/<token>`, `/api/news/confirm?token=…`,
  `/api/download/all?t=…`, `/thanks?token=<pedido>`) y la consulta tecleada: en este recorrido,
  `GET /api/strategies?q=Zelda%20Logsprueba`. También el `Debugger PIN` de werkzeug al arrancar. Con gunicorn, el
  `accesslog = "-"` de `gunicorn.conf.py` (su formato por defecto: IP, petición con su consulta, referer y agente) lo
  manda a la salida estándar. Es de toda la familia y del núcleo: va a «Para el núcleo» de `ESTADO.md`; aquí no se
  parchea.
- Las líneas de la tienda nombran las cuentas por su id y lo demás por su clave; nunca un correo (las de los pedidos y
  las pruebas sin él), un código de descuento (sólo si se aplicó) ni un token de enlace.

## Lo que depende de la 0.36

1. El ayudante del frontal y la ruta que lleva sus errores y los cambios de pantalla al servidor: todo «El frontal».
2. `external_call` en el CONTRATO: la traza de la llamada al BCE (`fx.py`); la de PayPal se va con la migración.
3. Las comprobaciones de `check_tool()` (sin salidas propias ni `print`; con `privacy_sample`, que el correo y el nombre
   de la cuenta de prueba no salgan en los logs): `tests/test_privacy.py` ya pasa `privacy_sample`.
4. La línea de cada petición por su regla (sin IP, sin credenciales ni consulta).

## Lo añadido

(se completa en F3 y F4)
