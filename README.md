# Edgefolio (`edgefolio`) · la tienda de estrategias de TradingView

La tienda de tuisku.ai, que se vende como **Edgefolio**: un catálogo de **estrategias de TradingView**
(Pine Script v5; 94 en el de octubre de 2026) con su backtest. Se miran en una vista sencilla,
**Lite**, o se filtran en **Pro**; se ve cómo decide cada una; se compran con PayPal y se descarga el
script. El servidor pone el precio de cada carrito, cobra, y sólo entrega los scripts de pago por
enlaces firmados que caducan.

Es una **herramienta zlecitool**: una app Flask sobre [zlecitool-core](https://github.com/Leci37/zlecitool-core),
como `cv_lin` o `md_pdf`. La barra (con la palabra Edgefolio), el idioma, las cuentas, la seguridad, el
correo, el pie y las páginas legales son del núcleo; aquí sólo está la tienda. Es pública, sin
publicidad, y **vende con PayPal, no con créditos**.

Esta aplicación es **la interfaz gráfica**: enseña, cobra y entrega. Los datos los fabrica su **aplicación
gemela**, [**tuisku_strategy_generator**](https://github.com/Leci37/tuisku_strategy_generator/tree/_ztool_dev) (el generador de
estrategias, rama `_ztool_dev`): baja las velas, entrena los bosques, escribe cada estrategia en Pine Script,
hace su backtest y sus dos gráficos, y deja el catálogo y sus ficheros en **un paquete versionado** (su
`d_result/package/`; los scripts de pago, aparte). Aquí, `flask --app app edgefolio import` lo comprueba
entero y lo publica; lo que trae lo fija `catalogue/contract.json`, el contrato entre las dos: ver
[La aplicación gemela](#la-aplicación-gemela-el-generador-de-estrategias).

<p align="center">
  <img src="docs/img/edgefolio_lite.png" alt="Lite: la cinta de tickers, la búsqueda, las pestañas, el aviso de sobreajuste, tres lotes y Crea tu pack, y las fichas con su curva, su nota y su precio" width="900">
</p>

<table>
<tr>
<td width="50%"><img src="docs/img/edgefolio_pro.png" alt="Pro: la escalera de descuentos con el carrito, el panel de filtros con un histograma en cada deslizador y la lista"></td>
<td width="50%"><img src="docs/img/edgefolio_strategy.png" alt="La página de una estrategia: los gráficos, los 14 resultados del backtest, el indicador y las primeras líneas del script"></td>
</tr>
<tr>
<td><sub><b>Pro.</b> 21 filtros, cada deslizador con su histograma, filtrados y contados en el servidor.</sub></td>
<td><sub><b>La página de una estrategia</b> (<code>/s/&lt;id&gt;</code>): gráficos, resultados, el principio del script y lo que se compra.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_tree.png" alt="Cómo decide: el primer árbol de decisión de la estrategia, caja a caja, con los valores de los indicadores como deslizadores"></td>
<td><img src="docs/img/edgefolio_thanks.png" alt="La página de gracias: el pedido, una fila por estrategia con su .pine y su .zip, y los cinco pasos para instalarla"></td>
</tr>
<tr>
<td><sub><b>Cómo decide</b> (<code>/s/&lt;id&gt;/tree</code>): la parte gratis del árbol, leída de la vista previa pública.</sub></td>
<td><sub><b>Después de pagar:</b> las descargas y el tutorial para ponerla en TradingView.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_mine.png" alt="Mis estrategias: cada compra con su .pine y su .zip, su ficha y cómo decide, lo que dura su enlace, la tarjeta para confirmar un correo y las favoritas"></td>
<td align="center"><img src="docs/img/edgefolio_phone.png" alt="La tienda en un móvil, con la barra de abajo" width="260"></td>
</tr>
<tr>
<td><sub><b>Mis estrategias</b> (<code>/mine</code>, con la cuenta del núcleo): lo comprado con la sesión abierta y lo comprado sin cuenta con un correo que la cuenta ha confirmado.</sub></td>
<td><sub>Cada página funciona desde 390 px, en 8 idiomas, el árabe de derecha a izquierda.</sub></td>
</tr>
</table>

### La tienda funcionando

<table>
<tr>
<td width="50%"><img src="docs/img/edgefolio_pro_filters.png" alt="Pro con dos símbolos y un porcentaje de aciertos del 60 % o más"></td>
<td width="50%"><img src="docs/img/edgefolio_table.png" alt="Los mismos filtros en la vista de tabla"></td>
</tr>
<tr>
<td><sub><b>Filtrar.</b> Cardano y Avalanche (ADAUSDT y AVAXUSDT), aciertos ≥ 60 %: el recuento, las etiquetas, los histogramas y la lista salen del servidor.</sub></td>
<td><sub>El mismo resultado, en una tabla que se ordena.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_install.png" alt="Justo después de pagar: el tutorial de instalación, paso 1 de 5"></td>
<td><img src="docs/img/edgefolio_tour.png" alt="El recorrido de bienvenida, paso 1 de 3, la primera vez"></td>
</tr>
<tr>
<td><sub><b>Después de pagar</b> (PayPal de prueba): el tutorial de 5 pasos para ponerla en TradingView, una vez.</sub></td>
<td><sub><b>La primera visita:</b> el recorrido de bienvenida, de 3 pasos.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_compare.png" alt="Tres estrategias comparadas, con lo mejor de cada fila en verde"></td>
<td><img src="docs/img/edgefolio_pack.png" alt="Crea tu pack: cinco estrategias elegidas de la lista"></td>
</tr>
<tr>
<td><sub><b>Comparar</b> hasta 3; lo mejor de cada fila, en verde.</sub></td>
<td><sub><b>Crea tu pack:</b> 5 estrategias por un precio, buscadas en todo el catálogo de pago.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_free.png" alt="Una estrategia gratis: el correo ha salido"></td>
<td><img src="docs/img/edgefolio_arabic.png" alt="La tienda en árabe, de derecha a izquierda"></td>
</tr>
<tr>
<td><sub><b>Las gratis</b> se mandan por correo (las novedades, en una casilla aparte y sin marcar).</sub></td>
<td><sub><b>En árabe</b>, de derecha a izquierda, con los precios en riales y el cobro en dólares.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_spanish.png" alt="La página de una estrategia en español, con los precios en euros"></td>
<td align="center"><img src="docs/img/edgefolio_phone_tree.png" alt="Cómo decide en un móvil" width="260"></td>
</tr>
<tr>
<td><sub><b>En español</b>, con los precios en euros; 8 idiomas en total, los del menú del núcleo.</sub></td>
<td><sub><b>Cómo decide</b>, en un móvil.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_pro_es.png" alt="Pro en español con dos estrategias en el carrito: el total en euros y lo que se paga en dólares con PayPal"></td>
<td align="center"><img src="docs/img/edgefolio_phone_cart.png" alt="Lite en un móvil con el carrito flotante y la píldora de Comparar encima, sobre la barra de abajo" width="260"></td>
</tr>
<tr>
<td><sub><b>Pro en español:</b> el total en euros y, debajo, «Pagas … US$ con PayPal».</sub></td>
<td><sub><b>El carrito en un móvil,</b> con Comparar encima, los dos sobre la barra de abajo.</sub></td>
</tr>
<tr>
<td><img src="docs/img/edgefolio_free_error.png" alt="El diálogo de una gratis con un correo mal escrito: el aviso bajo el campo y el borde en rojo"></td>
<td></td>
</tr>
<tr>
<td><sub><b>Un correo mal escrito</b> se dice bajo el campo, con los textos del núcleo.</sub></td>
<td></td>
</tr>
</table>

<sub>Las capturas son de `tools/screenshots.py`, que recorre la tienda en un navegador de verdad contra el
servidor local en modo de prueba: un carrito con un código, los filtros, una compra sin cuenta y una
descarga de verdad, el alta en el núcleo y la confirmación del correo con el que se pagó, comparar, el
pack, una gratis, tres idiomas y un móvil; y cada cambio del diseño del 6 de octubre (el resultado del
código, Esc, los errores del correo, la píldora de Comparar, el teclado). Para en el primer paso que no
funciona, y con cualquier error de la consola (también de la CSP).</sub>

## Arrancar

### Con el lanzador de la familia

`arrancar.ps1` es el lanzador de todas las herramientas: **no está en ningún repo**, va en la carpeta
que los tiene todos al lado (`zlecitool-core`, `tuisku_cv_builder`, `tuisku_strategy_store`…). Desde
esa carpeta:

```
pwsh ./arrancar.ps1          # en Windows: powershell -ExecutionPolicy Bypass -File arrancar.ps1
```

Clona o pone al día cada repo, monta **un solo entorno** de Python en el que el
`requirements-dev.txt` de cada herramienta instala el núcleo desde `../zlecitool-core`, escribe **el
mismo `.env`** en todas (el mismo `FLASK_SECRET_KEY`, `ZLECITOOL_DATA_DIR`, `DATABASE_URL`,
`ZLECITOOL_INSECURE_COOKIES=1`, `ZLECITOOL_ADMINS`; a la tienda, además, `PAYPAL_MODE=fake` y
`DISCOUNT_CODES=demo20=0.20`), copia la primera vez los scripts de pago
(`flask --app app edgefolio restore-scripts`) y arranca cada una con `python app.py` en su puerto. **La
tienda queda en http://localhost:5105**. Una sola cuenta vale para todas (en `localhost`, no en
`127.0.0.1`).

El generador (`tuisku_strategy_generator`, rama `_ztool_dev`) va en esa misma
carpeta, al lado de la tienda. No es una web y no se arranca: está ahí para que su prueba del puente
encuentre la tienda y para que, al publicar, el paquete y sus scripts estén al lado.

### A mano

```
git clone https://github.com/Leci37/tuisku_strategy_store     # al lado de zlecitool-core
cd tuisku_strategy_store
python -m venv .venv && . .venv/bin/activate              # Python 3.10 o más (3.11 recomendado)
pip install -r requirements-dev.txt                       # el núcleo, editable, desde ../zlecitool-core
cp .env.example .env                                      # y un FLASK_SECRET_KEY dentro (48 caracteres)
flask --app app edgefolio restore-scripts                 # los scripts de pago, a <datos>/edgefolio/strategies
python app.py                                             # http://localhost:5105
```

`.env.example` trae `PAYPAL_MODE=fake` y `DISCOUNT_CODES=demo20=0.20`: sin PayPal, «Pagar» va directo a la
página de gracias como si se hubiera pagado, y el código `demo20` descuenta un 20 %. Sin
`ZLECITOOL_SMTP_HOST`, **ningún correo sale**: el núcleo deja cada uno en `<datos>/mail/*.eml` (el enlace
de una gratis, el de confirmar un correo, los avisos, el recibo de una compra); se abren con cualquier lector de correo. Sin los
scripts de pago todo funciona, y una descarga contesta que el fichero no está.

## Pruebas

```
pip install -r requirements-dev.txt
python -m playwright install chromium        # las pruebas en un navegador y tools/screenshots.py
pytest
```

Ninguna prueba sale a la red: PayPal es el de prueba y los correos se quedan en
`testing.mail_outbox()`. `tests/test_smoke.py` lleva `testing.check_tool(app, privacy_sample=sample)`, el
contrato del núcleo hecho prueba (desde la 0.30, también «Tus datos»: exporta lo de una cuenta, la borra y
comprueba que no queda nada fuera de los pedidos). Las de los scripts de pago (`test_formats.py`,
`test_cli.py`) los sacan de la historia del repo; en un clon sin ella, se saltan. Las de la página
en un navegador (las de `test_phone_bar.py`, `test_keyboard.py`, `test_listing_page.py`, `test_buying_page.py`,
`test_mine_page.py` y `test_scales.py`, y parte de las de `test_lists_cart.py`, `test_strategy_page.py`,
`test_tree.py` y `test_texts.py`) abren un Chromium (el kit del núcleo, `testing.mobile`); sin él, se saltan y no
prueban nada.

| Fichero | Qué prueba |
|---|---|
| `test_smoke.py` | el contrato del núcleo (con «Tus datos»); la ficha (pública, sin precios en créditos, la palabra Edgefolio); lo público y lo que pide sesión; la página en el idioma de la carcasa |
| `test_privacy.py` | «Tus datos»: lo que sale en «Descargar mis datos» (lo de la cuenta y lo hecho sin ella con un correo demostrado, aquí o en el núcleo; nunca con uno sin demostrar, ni lo de otra cuenta, ni un enlace o un hash); al borrar la cuenta, los pedidos se quedan sin quién los hizo y lo demás se va; el pedido de una cuenta borrada no se cobra; los avisos no le escriben |
| `test_phone_bar.py` | en un Chromium, la barra de abajo del móvil con el gancho del núcleo (`data-zt-bottom`): la página deja lo que tapa, y el pie queda encima; en un ordenador, ni barra ni sitio |
| `test_pricing.py`, `test_bundles.py` | los precios sólo del catálogo; los escalones y el código sumados con el tope del 70 %; los códigos de precio único; los lotes y el pack; una estrategia nunca dos veces; los lotes que se publican, cada uno más barato que sus estrategias sueltas |
| `test_search.py` | los filtros, el orden, las páginas y los histogramas contra el catálogo de verdad; que sean rápidos; la nota según `GRADE_CUTOFFS`; lo que dice `/api/config` (entre cuántas probadas, `tried`); la explicación del indicador en el idioma que pide `ind_lang` |
| `test_orders.py` | pagar y descargar; el importe de PayPal comprobado; los enlaces que caducan y se gastan (también a la vez); el recibo con enlaces sólo para el navegador que compró, la cuenta que compró o la que demostró el correo; lo que ya es de la cuenta (también por sus correos demostrados y sus gratis) no se vende suelto otra vez (`errAlreadyOwned`), nunca por la compra de otra cuenta |
| `test_receipt.py` | el recibo por correo: una vez por pedido, en el idioma de la página, línea a línea; sin dirección pública no sale y el pago sigue |
| `test_publish.py` | el puente con el generador: `contract.json` es lo que lee `publish.py`, y las columnas que faltan o sobran se rechazan (también en el export); el paquete, comprobado entero antes de escribir nada (contrato, sha256, rutas, ficheros fuera del manifiesto, lo que nombran las filas, el script de cada fila, ningún script entero como gráfico) y publicado tal como se comprobó; los logos de la tienda; un fallo a medias deja la tienda como estaba; sin la ruta del script de pago y con las vistas previas cortadas; las intradía de acciones fuera (salvo con `--intraday-stocks`), también en el catálogo publicado; `tried` en `release.json`; el `since_release.csv` de un paquete, comprobado como lo lee la tienda; `publish.py` solo, con pandas |
| `test_release.py` | `flask edgefolio import`: sólo los scripts del manifiesto, con su sha256; sin `--scripts`, ya en `STRATEGIES_DIR`; `--skip-scripts` dice cuántos faltan; si algo falla, nada escrito; las miniaturas vaciadas; los logos que se quedan; los lotes que pierden una estrategia; los niveles de los scripts comprobados, en `catalogue/levels.json`; las intradía de acciones fuera, también con `LIST_INTRADAY_STOCKS`; `tried` y el `since_release.csv` del paquete |
| `test_levels.py` | los niveles de cada script (`edgefolio/levels.py`), sólo del que lleva el nombre de su estrategia; `flask edgefolio levels` los escribe desde `STRATEGIES_DIR` y, sin ningún script de su estrategia, no toca el fichero |
| `test_tasks.py` | las tareas del reloj del núcleo (`"schedule"`): `fx_update` y `send_alerts`, a su hora (`testing.tick`) y una vez aunque se repitan (`testing.run_task` dos veces); los cambios sin una transacción abierta; un fallo deja los cambios de antes; sin dirección pública, los avisos fallan y no mandan nada; a una cuenta borrada, nada |
| `test_free.py` | las gratis por correo; el límite del día (también a la vez); las novedades con doble confirmación; el idioma del correo |
| `test_mine.py` | Mis estrategias: lo de la cuenta y lo de un correo demostrado; renovar; las versiones nuevas, gratis hasta que la estrategia caduca (a las 00:00 UTC de la «Expiry date» de su script; después, `errUpdateExpired`, también en el enlace de antes y en el script del propietario); el script del propietario; las favoritas; el zip de un pedido; lo comprado de una estrategia que salió del catálogo |
| `test_proofs.py` | la prueba de un correo: un uso, en dos pasos, sólo para la cuenta que la pidió, sólo hashes, sin llenar buzones, CSRF, el idioma |
| `test_alerts.py` | los avisos de las favoritas: una vez, en su idioma, sólo a un correo demostrado; sin dirección pública, el comando no manda nada |
| `test_security.py` | los enlaces nunca con la cabecera Host; la cookie de quien compra; correos que un programa leería distinto; los límites por IP; la forma de los rechazos; CSRF |
| `test_formats.py` | los formatos del zip (.md, .py, .js) contra el script; cada script de pago entendido; el .md nombra cada valor como «Cómo decide» |
| `test_texts.py` | los textos en los 8 idiomas: la explicación de cada indicador (fiel a su código, sin promesas, pedida con `ind_lang`), su nombre y su enlace de `indicators.csv`; cada recuento en la forma de su número, en la página y en los correos; los signos y los plurales en árabe; la puntuación del chino y del hindi; «Tree depth»; el tamaño del pack |
| `test_site.py`, `test_media.py`, `test_cli.py`, `test_layout.py` | la página sobre la carcasa; nada privado en `static/`; las vistas previas cortadas, también dentro de un zip del diseño archivado; las miniaturas y los cambios; los comandos; la forma del repo |
| `test_page_code.py` | el código de la página después de mezclar el diseño: ninguna marca de conflicto; cada valor, campo de fila y texto que leen las vistas lo da `static/js`; los textos de la tienda en los 8 idiomas, con las mismas variables y sin repetir una clave del núcleo; los ganchos que busca `app.js` (`data-search`, `data-sf-cart`, `data-sf-bundles`); cada rechazo de un enlace de descarga, explicado |
| `test_keyboard.py` | en un Chromium, el teclado: los diálogos se quedan con el foco y lo devuelven; las × dicen qué quitan; Lite \| Pro con las flechas; una fila de la Tabla y los desplegables de Pro con el teclado |
| `test_lists_cart.py` | en un Chromium, las listas, el carrito y el recorrido: los packs esperan a los lotes; los buscadores no pasan de 100; Intro aplica el código; el árabe; el singular de Pro; la fila desplegada de la Tabla; al llegar, el diccionario, las favoritas y la página de gracias |
| `test_listing_page.py` | en un Chromium, lo que la tienda dice de su catálogo: entre cuántas probadas en el aviso de sobreajuste, los cortes de la nota y «Desde su publicación» sólo con cifras |
| `test_buying_page.py` | en un Chromium, «Ya es tuya» en Lite, Pro y la ficha (sin precio) y el carrito que la pierde con su aviso; la página de gracias, que no rechaza lo que se acaba de pagar; la actualización sólo hasta la caducidad; la gratis en un móvil tumbado; «Hecho» anunciado; el buscador de Pro bajo la barra |
| `test_strategy_page.py`, `test_scales.py` | en un Chromium, la ficha: la temporalidad de TradingView, la explicación del indicador en el idioma de la página, una gratis, «Ya es tuya», el título de la pestaña, «Cómo decide» que se pide otra vez y sigue al carrito; las escalas de Pro y las barras de la ficha, del catálogo |
| `test_tree.py`, `test_mine_page.py` | «Cómo decide»: cada patrón y cada valor de las vistas previas publicadas con su nombre, en los 8 idiomas; en un Chromium, la pestaña como visitante (con los niveles publicados o, sin ellos, con la puntuación de cada resultado; la escala y los signos en árabe) y como propietario, y el móvil. Mis estrategias en un Chromium: la prueba de un correo, las favoritas, el tutorial y una respuesta cortada |
| `test_design_update.py` | aplicar una exportación del diseño: una igual a la anterior no cambia nada; un cambio del diseño llega a la vista adaptada; la forma de las de octubre (`vendor/`, las notas nuevas, `versions/` y `offline/` fuera); `docs/design/serve.py` encuentra el núcleo |

## Cómo funciona

### Una compra

```
navegador                                 servidor (edgefolio/)                       PayPal
  │ POST /api/quote {items, bundles,       precios de catalogue.csv y bundles.json,
  │       pack, code} ───────────────────▶ escalones + código, ≤ 70 %
  │ ◀──────────────── total, descuento ────
  │ POST /api/orders (lo mismo) ──────────▶ el mismo precio ───────────────────────▶ crear el pedido
  │ ◀──────────────────── enlace para aprobar (y la cookie edgefolio_buyer) ───────┘
  │ se paga en PayPal, que vuelve a /thanks?token=<pedido>
  │ POST /api/orders/<id>/capture ────────▶ cobrar ─────────────────────────────────▶ el dinero se mueve
  │                                          ¿importe = total del pedido? ◀─────────┘
  │ ◀──────── recibo + un enlace por fichero (sólo a quien puede verlos)
  │                                          el recibo, por correo a quien pagó
  │ GET /api/download/<token>[?format=zip] ▶ el fichero, de la carpeta privada
```

El navegador sólo manda ids de estrategias, claves de lotes y el código tecleado: no tiene ningún precio
que pueda cambiar, ningún código de descuento ni la ruta de un fichero de pago. Una estrategia nunca se
cobra dos veces: lo que va en un lote o en el pack no se cobra suelto, y dos lotes que comparten una
estrategia se rechazan. Cada POST lleva el token CSRF del núcleo (lo pone `csrf.js` en cada `fetch`).

### Las descargas

Cada estrategia de un pedido pagado tiene su enlace (`/api/download/<token>`): vale `DOWNLOAD_DAYS` días y
`MAX_DOWNLOADS` descargas, que se gastan con un único `UPDATE` condicional antes de mandar nada (dos
peticiones a la vez no se llevan la misma última descarga). `?format=zip` añade las reglas en Markdown y
las versiones beta en Python y JavaScript; `/api/download/all?t=…&t=…` junta los `.pine` de un pedido.
Los scripts completos están en la carpeta privada (`STRATEGIES_DIR`), nunca en `static/`; las vistas
previas públicas van cortadas a 50 líneas de su primer árbol.

**Quién ve los enlaces del recibo:** el navegador que hizo el pedido (su cookie `edgefolio_buyer`,
HttpOnly, 30 días; en la base de datos sólo su hash), la cuenta que compró con la sesión abierta y, si se
compró sin cuenta, una cuenta que ha demostrado el correo de PayPal. Cualquier otro (alguien con el id del
pedido, que va en la dirección de vuelta de PayPal) recibe el recibo sin enlaces.

**El recibo por correo** (la «factura por correo» que promete la fila de confianza bajo «Pagar»): el
primer cobro de un pedido lo manda al correo del pedido (el de la cuenta o, sin cuenta, el de PayPal),
en el idioma de la página: cada línea con lo que costó, el total, cuánto valen los enlaces y la
dirección de Mis estrategias, sin enlaces de descarga (un correo no demuestra nada; ver abajo). Es un
recibo, no una factura con datos fiscales: para eso da `CONTACT_EMAIL`. La misma fila enseña
`DOWNLOAD_DAYS`, `MAX_DOWNLOADS` y `CONTACT_EMAIL` tal como estén configurados.

### Mis estrategias y la prueba de un correo

Las cuentas son **las del núcleo**: entrar en la tienda es haber entrado en todas las herramientas.
`/mine` pide la sesión (el núcleo lleva a `/login?next=/mine`). Pero **el núcleo no comprueba el correo
de quien se da de alta**: si Mis estrategias enseñara los pedidos cuyo correo es el de la cuenta,
cualquiera podría registrarse con el de quien compró y llevarse sus enlaces. Por eso:

- lo comprado o pedido gratis **con la sesión abierta** lleva `user_id`: es de esa cuenta;
- lo hecho **sin cuenta** (se puede comprar sin ella) sólo sale en una cuenta cuando ha **demostrado**
  ese correo. Mis estrategias ofrece «¿Compraste sin cuenta?»: `POST /api/mine/proofs {email}` manda a
  esa dirección un enlace de un solo uso (24 horas, sólo para la cuenta que lo pidió). Abrirlo
  (`/mine?proof=<token>`) sólo pregunta de qué correo es (`/api/mine/proofs/peek`, sin gastar nada: un
  lector de correo que lo abre no confirma nada); el clic de la persona lo confirma
  (`/api/mine/proofs/confirm`) y queda en `edgefolio_email_proof`.

La misma prueba hace falta para los avisos de las favoritas: nadie recibe correos porque otro se
registró con su dirección y marcó unas casillas.

Desde Mis estrategias se pide un enlace nuevo cuando uno caduca o se gasta (o hay una versión nueva; uno
que funciona no se cambia, para que el botón no reinicie el límite), se lee el script entero (la vista de
propietario de «Cómo decide») y se guardan las favoritas con sus avisos.

### Tus datos: descargarlos y borrar la cuenta

«Mis datos» (en la cuenta, del núcleo 0.30) da a cada cuenta **«Descargar mis datos»** y **«Borrar mi
cuenta»** en todas las herramientas. Las páginas, el zip, la cola y la comprobación son del núcleo; lo de
la tienda lo hace `edgefolio/your_data.py`, registrado en `app.py` con `privacy.add_privacy`, en el reloj
de la tienda (sin la petición de nadie):

- **Qué es de la cuenta:** lo hecho con la sesión abierta y lo hecho sin cuenta con un correo demostrado:
  el de la cuenta, si lo demostró el núcleo (al entrar con un enlace por correo), y los que demostró aquí
  («¿Compraste sin cuenta?»). Nunca lo que sólo coincide con un correo sin demostrar.
- **El zip** lleva, en `edgefolio/`: sus pedidos y sus enlaces de descarga, sus gratis, sus favoritas, las
  pruebas de sus correos y, de cada correo demostrado, su alta en las novedades y su fila del buzón. Sin
  los enlaces, ni el hash de la cookie de quien compra, ni el de un enlace de confirmar.
- **Al borrar la cuenta, los pedidos se quedan**: son el registro de una venta, que pide la ley fiscal
  (lo vendido, el importe, la fecha). Pierden quién los hizo: el correo, el de PayPal y el hash de la
  cookie del navegador que compró; los hechos con la sesión abierta siguen apuntando a la cuenta borrada,
  y sus enlaces, que ya no ve nadie, caducan solos. Lo demás se va: sus gratis, sus favoritas, sus pruebas,
  y sus novedades y su fila del buzón. Lo hecho sin cuenta con un correo demostrado se va también si otra
  cuenta demostró el mismo correo (es de quien lo controla).
- Desde el borrado, los avisos de las favoritas no le escriben (también antes de que se sirva la parte de
  la tienda: pasan minutos), y un pedido suyo que vuelve de PayPal no se cobra (409 `errAccountClosed`).

### Las gratis y las novedades

Las 79 estrategias gratis se mandan por correo (`POST /api/free`): el enlace va en el correo, nunca en la
respuesta. Como mucho 10 al día por dirección (contadas con la fila de la dirección bloqueada, así que
diez peticiones a la vez no se cuelan) y 20 por IP a la hora. Las novedades son una casilla aparte, sin
marcar: se apuntan sólo si se marca y sólo cuentan cuando se confirman desde el correo
(`/api/news/confirm`, doble opt-in).

### Idiomas y textos

Los textos de la tienda están en `i18n/ui.json`, en los 8 idiomas del núcleo; la página los lee del
diccionario del núcleo (`/zt/i18n.json`, con los comunes) y sigue el idioma de la carcasa: al cambiarlo
en su menú, se repinta sin recargar (`zt:language`). Los correos salen en el idioma de la petición. Un
rechazo del servidor es una clave (`{"error": "errLinkExpired", "vars": {…}}`) y la página enseña su texto.

## Rutas

| | |
|---|---|
| `/`, `/thanks`, `/s/<id>`, `/s/<id>/tree` | la tienda (una sola plantilla; la página lee la ruta), públicas |
| `/mine` | Mis estrategias, con sesión |
| `GET /api/strategies` | el catálogo filtrado, ordenado y por páginas en el servidor: `q`, `tab` (`hot`, `win`, `stocks`, `crypto`, `new`, `free`), `free=1`, `paid=1`, `sort`, `page`, `size` (≤ 100), los rangos como `<clave>_min` / `<clave>_max`, las listas como `sym`, `tf`, `ind`, `idx`, `rel` repetidos; `facets=1` añade cada histograma y recuento |
| `GET /api/strategies/<id>`, `GET /api/bundles` | una estrategia con su indicador y sus versiones; los lotes y el pack |
| `POST /api/quote`, `POST /api/orders`, `POST /api/orders/<id>/capture` | el precio, el pedido de PayPal, el cobro y el recibo |
| `GET /api/download/<token>`, `GET /api/download/all` | las descargas |
| `POST /api/free`, `GET /api/news/confirm` | una gratis por correo; confirmar las novedades |
| `GET /api/config`, `GET /api/fx`, `GET /api/me`, `GET /thumbs/<raíz>.webp` | lo que la página necesita (nunca un código), los cambios de moneda, quién es, las miniaturas |
| `GET /api/mine`, `POST /api/mine/renew`, `GET /api/mine/<id>/script` | Mis estrategias, un enlace nuevo, el script del propietario (con sesión) |
| `POST /api/mine/proofs`, `/peek`, `/confirm` | la prueba de un correo (con sesión) |
| `PUT` / `DELETE /api/favourites/<id>` | las favoritas y sus avisos (con sesión) |

Sin sesión, un script recibe `401 {"error": "errLoginRequired"}` en lo que la pide. Las cuentas
(`/register`, `/login`, `/cuenta`), el idioma, lo legal (`/legal/…`) y el contacto son del núcleo.

## Comandos

```
flask --app app edgefolio import PAQUETE [--scripts DIR | --skip-scripts] [--prune]
                                                      # un paquete del generador (ver «Publicar un catálogo nuevo»)
flask --app app edgefolio levels                      # los niveles de cada script de STRATEGIES_DIR, para el árbol
flask --app app edgefolio restore-scripts [--force]   # los scripts de pago, de la historia del repo
flask --app app edgefolio fx-update                   # los cambios del día del BCE, a mano (el reloj los trae solo)
flask --app app edgefolio send-alerts                 # los avisos de las favoritas, a mano (el reloj los manda solo)
flask --app app edgefolio subscribers                 # quién confirmó las novedades, en CSV
```

`levels` escribe `catalogue/levels.json`: con qué puntuación compra y con cuál cierra cada script del catálogo
publicado (`buyThreshold` y `sellThreshold`), leídos de `STRATEGIES_DIR`, para que el árbol del visitante diga
comprar, vender o esperar (API #3 los manda; sin ellos enseña la puntuación de cada resultado). Sólo vale el script
que lleva el nombre de su estrategia: si ninguno lo lleva (las copias de prueba de otra máquina), no toca el
fichero. Se ejecuta donde están los scripts de verdad, se sube el `levels.json` que deja y se reinicia la tienda.

Los scripts de pago **no están en el repo**, sólo en su historia (`c3fa796:d_result/pine_TW_b`).
`restore-scripts` los copia a `STRATEGIES_DIR` con `git archive`, **sin tocar la copia de trabajo ni el
índice**, y sólo si la carpeta está vacía (o con `--force`): es lo que hace el lanzador la primera vez.
Traen los del catálogo de ahora; los de un catálogo nuevo llegan con `import --scripts`.
Como siguen en la historia, cualquiera con el repo puede sacarlos: para cerrarlo del todo, publicar la
tienda en un repo nuevo (o reescribir la historia) antes de volver a vender.

`send-alerts` compara el catálogo con la vuelta anterior y manda un correo por persona con lo nuevo de
sus favoritas (versión nueva, bajada de precio, un lote nuevo); la primera vez sólo apunta cómo está.
`fx-update` escribe `<datos>/edgefolio/fx.json`; hasta entonces valen los cambios de ejemplo de
`catalogue/fx.json`. Los dos los hace solos el reloj del núcleo (`"schedule"` de `tool.json`, núcleo 0.25),
una vez entre todos los procesos y servidores: `fx_update` los días laborables a las 17:00 de Madrid
(después de que publique el BCE) y `send_alerts` cada día a las 09:00. Los comandos son para correrlos a
mano (una vez del reloj que falló, otra vez: `flask --app app zt task run fx_update`). Las dos
tareas apuntan cada vez hecha en `edgefolio_task_done`: si se repite, no hace nada. Los enlaces de los avisos
necesitan `ZLECITOOL_PUBLIC_URL`: sin ella, en producción, la vez falla («Sistema» y el aviso de errores)
y no manda nada.

## Configuración

Lo común, con las variables del núcleo (todas en `.env.example`): `FLASK_SECRET_KEY` (el mismo en todas
las herramientas), `ZLECITOOL_DATA_DIR`, `DATABASE_URL`, `ZLECITOOL_PUBLIC_URL` (la dirección pública:
los enlaces de los correos y la vuelta de PayPal se hacen con ella, nunca con la cabecera Host),
`ZLECITOOL_SMTP_*` y `ZLECITOOL_MAIL_FROM` (el correo), `ZLECITOOL_TRUSTED_PROXIES`,
`ZLECITOOL_LEGAL_*`, `ZLECITOOL_ADMINS`… Lo propio de la tienda (`edgefolio/settings.py`):

| Variable | Por defecto | |
|---|---|---|
| `PAYPAL_MODE` | `fake` | `fake`, `sandbox` o `live`. Con `sandbox` o `live` no arranca sin `ZLECITOOL_PUBLIC_URL` |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | | de una app REST del panel de desarrolladores de PayPal; obligatorias fuera de `fake` |
| `DISCOUNT_CODES` | ninguno | pares `código=porcentaje`: `spring20=0.20,partner40=0.40` |
| `FLAT_PRICE_CODES` | ninguno | pares `código=precio` que ponen un precio a cada estrategia suelta |
| `MAX_DISCOUNT` | `0.70` | el tope del escalón más el código, juntos |
| `PACK_SIZE`, `PACK_PRICE` | `5`, `249` | «Arma tu pack»: cuántas estrategias y por cuánto; su tarjeta dice ese tamaño («Elige N más · 5 por …») |
| `DOWNLOAD_DAYS`, `MAX_DOWNLOADS` | `7`, `10` | lo que vale un enlace de descarga |
| `NEW_DAYS` | `30` | lo que una estrategia sale en «Nuevas» |
| `GRADE_CUTOFFS` | `100,50,25` | las operaciones cerradas desde las que una estrategia lleva la nota A, B o C (con menos, D): cuánta prueba respalda su backtest. Su explicación en la página los dice |
| `LIST_INTRADAY_STOCKS` | `0` | con `1`, `edgefolio import` publica también las estrategias intradía de acciones (de minutos u horas), que deja fuera: el plan gratis de TradingView enseña otros datos intradía de las acciones (sólo Cboe BZX), así que allí operan distinto que en su backtest |
| `CONTACT_EMAIL` | `sales@tuisku.ai` | la dirección que la página da para los problemas |
| `STRATEGIES_DIR` | `<datos>/edgefolio/strategies` | los `.pine` de pago |
| `PORT` | `5105` | el de `python app.py` (y `gunicorn.conf.py`) |

Los escalones por importe (más de 160 $: 15 %, 290 $: 20 %, 500 $: 25 %, 1.000 $: 40 %, 2.500 $: 70 %)
están en `edgefolio/settings.py`; la página pinta su escalera con `/api/config`, así que no pueden no
coincidir.

## La base de datos

La de **todas las herramientas** (la del núcleo, `DATABASE_URL`; sin ella, SQLite en
`<ZLECITOOL_DATA_DIR>/zlecitool.db`). Las tablas se crean solas al arrancar (`create_tables`). La tienda
no lee ni escribe ninguna `core_*`: sus filas apuntan a **`core_user.id`** (la cuenta del núcleo) y las
cuentas, la sesión, el idioma elegido y lo demás de la familia los lleva el núcleo en sus tablas.

| Tabla | Columnas | Qué guarda |
|---|---|---|
| `edgefolio_order` | `paypal_id` (clave), `user_id` → `core_user` (vacío sin cuenta), `items` (JSON: las claves), `code`, `total`, `currency`, `status` (`CREATED`, `PAID`, `FAILED`), `payer`, `email`, `lines` (JSON: lo cobrado, línea a línea), `buyer_hash`, `created_at` | un pedido de PayPal; `email` es el de la cuenta o, sin cuenta, el de PayPal (en minúsculas); `buyer_hash`, el SHA-256 de la cookie del navegador que compró |
| `edgefolio_download` | `token` (clave), `paypal_id` → `edgefolio_order`, `item_key`, `expires_at`, `count`, `version`, `created_at` | un enlace de descarga de una estrategia de un pedido pagado (y los que lo renuevan) |
| `edgefolio_free_claim` | `token` (clave), `user_id` → `core_user` (vacío sin cuenta), `email`, `item_key`, `news`, `consent_at`, `expires_at`, `count`, `version`, `lang` | una gratis mandada a un correo, con su enlace y su consentimiento |
| `edgefolio_subscriber` | `email` (clave), `news`, `consent_at`, `source`, `lang`, `token_hash`, `confirmed_at` | quien pidió las novedades; sólo cuenta con `confirmed_at` (doble opt-in) |
| `edgefolio_favourite` | `user_id` → `core_user` y `item_key` (clave), `alerts` (JSON: `nv`, `pd`, `bd`), `email`, `lang`, `created_at` | las favoritas de una cuenta, con sus avisos, y el correo y el idioma a los que van |
| `edgefolio_alert_state` | `item_key` (clave), `version`, `price`, `bundles` (JSON), `updated_at` | cómo era cada estrategia en la última vuelta de los avisos: un cambio se avisa una vez |
| `edgefolio_email_proof` | `id`, `user_id` → `core_user`, `email` (únicos juntos), `token_hash`, `requested_at`, `expires_at`, `verified_at` | que una cuenta ha demostrado un correo (`verified_at`); hasta entonces, el hash del enlace mandado |
| `edgefolio_mailbox` | `email` (clave), `first_seen_at`, `last_seen_at` | una fila por dirección a la que escribe la tienda: se bloquea para contar lo que va por dirección (las gratis del día) de una vez, en SQLite y en Postgres |

Al borrar una cuenta («Tus datos», arriba), `edgefolio_order` se queda sin correo, sin `payer` y sin
`buyer_hash`, y `edgefolio_download` con él; las filas de la cuenta de `edgefolio_free_claim`,
`edgefolio_favourite` y `edgefolio_email_proof` se van, y las de sus correos demostrados en
`edgefolio_free_claim`, `edgefolio_subscriber` y `edgefolio_mailbox`, también. `edgefolio_alert_state` no
guarda nada de nadie.

Los enlaces de un solo uso y la cookie de quien compra se guardan sólo como hash. Fuera de la base de
datos, en `<ZLECITOOL_DATA_DIR>/edgefolio/`: `strategies/` (los scripts de pago), `thumbs/` (las
miniaturas WebP, hechas la primera vez que se piden, y otra vez si su gráfico es más nuevo) y `fx.json`
(los cambios del día). Con `flask --app app zt backup` (del núcleo) se copia la base de datos; la carpeta
de datos, con el resto del servidor.

## La aplicación gemela: el generador de estrategias

| | |
|---|---|
| **Qué es** | [Leci37/tuisku_strategy_generator](https://github.com/Leci37/tuisku_strategy_generator/tree/_ztool_dev), rama `_ztool_dev` (lo estable, en `_ztool_main`): el repo que genera los datos (privado). Su README cuenta los pasos, lo que tarda y lo que se arregló; su `CLAUDE.md`, esta conexión desde su lado |
| **Qué hace** | velas de Alpaca (acciones) y Binance (cripto) → indicadores → bosques de scikit-learn → un script de Pine por bosque → backtest (en TradingView, o en Python con las mismas reglas) con sus dos gráficos → el export y el paquete para la tienda |
| **Esta** | la interfaz: nunca entrena ni hace backtests, sólo publica el paquete del generador |

**El contrato** es `catalogue/contract.json`, de la tienda (versión 1): las columnas del catálogo (y la
opcional, `version`, y la que se quita, `pine_path`), en qué carpeta del paquete está cada fichero que
nombra una fila, a qué carpeta de `static/assets/` va y cómo se llama el script completo de cada
estrategia. `catalogue/publish.py` lo lee de ahí. El generador lleva `CONTRACT_VERSION = 1` junto a
`SHOP_COLUMNS` (`S_04_ladding_file_info_to_see_in_web.py`) y sus pruebas del puente comparan los dos. Un
cambio de columnas o de carpetas sube la versión y entra en los dos repos a la vez; un paquete de otra
versión no se importa.

**El paquete** lo escribe el paso 7 del generador (`python S_04_ladding_file_info_to_see_in_web.py`,
también desde `run_pipeline.py`), después del export, en su `d_result/package/`: fuera de git, vaciado y
escrito de nuevo en cada vuelta, y borrado si no sale ninguna estrategia o si falla al escribirlo. Lleva:

- `manifest.json`: el contrato, cuándo se hizo (UTC), el generador (repo y commit), las filas, el sha256
  de cada fichero del paquete y, en `private`, la carpeta `pine_TW_b` y el sha256 del script completo de
  cada fila;
- `catalogue.csv`: las columnas del contrato, sin `pine_path`;
- `pine_TW_img/`, `icons/`, `pine_TW_hide/`: los gráficos, los logos y las vistas previas que nombran las
  filas (enlaces duros a los de `d_result/`, o copias donde el disco no los deja). Un logo que no está
  en `d_result/icons/` no va: con `SHOP_ICONS_DIR`, es uno que la tienda ya tiene.

Los scripts completos no van en el paquete: se quedan en `d_result/pine_TW_b/`. Y **el paquete nunca se
hace público**: las vistas previas de las gratis son el script entero; la tienda las corta al publicarlas.

Dónde se conectan (lo que escribe el generador → lo que lee la tienda):

| Qué | El generador escribe (su paso) | La tienda lo lee de | Cómo pasa |
|---|---|---|---|
| Las filas del catálogo | `d_result/pine_TW_img_info_6_WEB.csv` (paso 7, `S_04_ladding_file_info_to_see_in_web.py`; sus columnas son `SHOP_COLUMNS`) y, sin `pine_path`, el `catalogue.csv` del paquete | `catalogue/catalogue.csv` | en el paquete; `edgefolio import` comprueba sus columnas contra el contrato y lo escribe |
| Los dos gráficos de cada estrategia | `d_result/pine_TW_img/*_profit.png`, `*_candel.png` (paso 6a o 6b) | `static/assets/charts/` | en el paquete (`pine_TW_img/`), con su sha256; `import` reemplaza los que cambiaron |
| Los logos | `d_result/icons/` | `static/assets/icons/` | en el paquete (`icons/`); `import` añade los que faltan: uno de verdad de la tienda se queda aunque el del paquete sea otro, y uno provisional de la tienda (el círculo gris del generador) deja sitio al del paquete. Con `SHOP_ICONS_DIR=<tienda>/static/assets/icons`, el paso 7 no hace logos que la tienda ya tiene |
| Las vistas previas públicas | `d_result/pine_TW_hide/` | `static/assets/previews/` | en el paquete (`pine_TW_hide/`); `import` las corta a su parte pública |
| Los scripts de pago | `d_result/pine_TW_b/` | `STRATEGIES_DIR` (por defecto `<ZLECITOOL_DATA_DIR>/edgefolio/strategies`) | nunca en el paquete, sólo su sha256 en el manifiesto: `import --scripts <generador>/d_result/pine_TW_b` copia los de la lista, comprobados |
| De qué ejecución es | `manifest.json` del paquete | `catalogue/release.json` | `import` copia el contrato, la fecha y el generador, y apunta las filas que publica, entre cuántas probadas se eligieron (`tried` del manifiesto, si lo trae) y las que deja fuera, con por qué |
| El resultado desde la publicación | aún nada: cuando lo escriba, `since_release.csv` del paquete (`id`, `pct`, `as_of`) | `catalogue/since_release.csv` | `import` lo comprueba y lo copia; con `--prune`, borra uno de antes si el paquete no trae otro |
| La vuelta a la tienda | cada script, al caducar, pide bajar la versión nueva de `SHOP_URL` (`settings.py` del generador, por defecto `tuisku.ai`) | — | el texto del script |

Lo que no pasa: los mosaicos del paso 8 del generador (`d_result/mosaico/`) eran de la página de antes;
esta no los usa.

La prueba que vigila el puente está en los dos lados: `tests/test_publish.py` y `tests/test_release.py`
aquí, y `tests/test_export.py` allí, que comprueba que su contrato es este `contract.json` y publica un
paquete (y un export) de verdad con este `publish.py` cuando `tuisku_strategy_store` está clonado al lado
del generador. Su CI (`.github/workflows/pruebas.yml`, Python 3.11, 3.12 y 3.13) pone al lado la carpeta
`catalogue/` de la tienda y los ficheros de su raíz, sin los assets (es pública: no hace falta ningún secreto), de `_ztool_dev`, o de
`_ztool_main` cuando corre en `_ztool_main` o en un pull request a ella; con `REQUIRE_SHOP=1` esas pruebas
fallan en vez de saltarse. Por eso **importa el orden al subir**: un cambio del contrato llega a la rama de
la tienda antes que el del generador, o a la vez; y lo mismo al fusionar en `_ztool_main`: la tienda,
primero.

## Publicar un catálogo nuevo

Con el paquete del generador (arriba), desde la tienda:

```
flask --app app edgefolio import ruta/al/generador/d_result/package --scripts ruta/al/generador/d_result/pine_TW_b --prune
```

Necesita pandas, que está en `requirements-dev.txt` y no en `requirements.txt`: se importa con el entorno
de desarrollo (el del lanzador), donde el generador está al lado.

- `--scripts DIR`: copia a `STRATEGIES_DIR` los scripts completos del manifiesto (sólo esos, nunca otro
  fichero de la carpeta), con su sha256 comprobado. Sin `--scripts`, tienen que estar ya en
  `STRATEGIES_DIR` con su sha256; si no, no se importa (dice cuántos faltan y cuántos tienen otro
  contenido).
- `--skip-scripts`: publica aunque falten o sean de antes, y dice cuántos: los que faltan no se entregan
  hasta que estén, y los de antes se entregan en su versión de antes. No va con `--scripts`.
- `--prune`: borra los gráficos y las vistas previas que ya no usa ninguna fila, y un
  `catalogue/since_release.csv` de antes si el paquete no trae uno.

Sin `LIST_INTRADAY_STOCKS=1`, deja fuera las estrategias intradía de acciones (de minutos u horas; las de
cripto, no): ni las publica ni pide o copia sus scripts, y dice cuántas y por qué. Por esa regla salieron del
catálogo de 2026-10 sus 49 horarias de acciones (quedan 94, con las 6 horarias de cripto); `catalogue/release.json`
las apunta en `left_out`, con por qué.

Antes de escribir nada lo comprueba todo, y si algo falla dice todo lo que falla y no escribe nada: el
contrato del paquete es el de `catalogue/contract.json` y sus columnas, las del contrato; cada fichero
tiene el sha256 del manifiesto y no hay ninguno fuera de él; cada ruta del manifiesto es segura (dentro del
paquete, en una carpeta del contrato); cada fichero que nombra una fila está en el paquete o ya en
`static/assets/`; la lista privada trae un script por fila, y sólo esos; y ningún gráfico ni logo es un
script completo. Luego comprueba los scripts, como dicen las opciones de arriba.

Después copia los scripts, escribe en `catalogue/levels.json` los niveles de cada uno (de los comprobados con
su sha256; ver `levels` en «Comandos») y publica `catalogue/catalogue.csv` y `static/assets/` como se
comprobaron: una fila por estrategia, rutas relativas, sin `pine_path`, un nombre legible para los que tienen
el código de la bolsa, cada vista previa cortada a su parte pública; los gráficos y las vistas previas que cambiaron se
reemplazan, y los logos que faltan se añaden (ver la tabla de arriba). Apunta en
`catalogue/release.json` de qué ejecución del generador es: su contrato, su fecha y su commit, las filas que
enseña la tienda, entre cuántas estrategias probadas se eligieron (`tried`, si el manifiesto lo dice; si no lo
dice y es la misma ejecución, se queda el que había: las de 2026-10, entre 1.531) y las que dejó fuera, con
por qué. La página dice ese `tried` en el aviso de sobreajuste. Si el paquete trae `since_release.csv` (`id`,
`pct`, `as_of`: lo que lleva cada estrategia desde su publicación; el generador aún no lo escribe), se
comprueba con lo demás y se copia a `catalogue/`; mientras ninguna estrategia tiene cifra, la página no habla
de «Desde su publicación». Todo se escribe primero al lado de su sitio y
se renombra al final: un fallo a medias deja la tienda como estaba (si falla al renombrar, lo último, dice
cuántos ficheros ya estaban en su sitio: se vuelve a importar). Por último vacía las miniaturas WebP,
dice qué lotes de `catalogue/bundles.json` pierden una estrategia (la tienda deja fuera el lote entero:
hay que cambiarlo o quitarlo) y recuerda **reiniciar la tienda**, que lee el catálogo al arrancar.
Después, `pytest`. Lo publicado (`catalogue/`, `static/assets/`) va en el repo; los scripts, en la
carpeta privada de la máquina donde se importa.

Otras dos formas, sin Flask (sólo pandas):

- `python catalogue/publish.py --package DIR [--prune] [--intraday-stocks]`: las mismas comprobaciones del
  paquete y la misma publicación (sin `--intraday-stocks`, también sin las intradía de acciones), pero los
  scripts se copian a mano, no escribe sus niveles (`flask --app app edgefolio levels`, con los scripts ya
  copiados), no vacía las miniaturas (una más vieja que su gráfico se rehace sola) ni avisa de los lotes.
- `python catalogue/publish.py EXPORT.csv [--assets DIR] [--prune] [--intraday-stocks]`, la de antes de los
  paquetes: también comprueba las columnas contra el contrato (y deja fuera las intradía de acciones), pero no
  hay sha256 ni lista privada, deja como están los ficheros que la tienda ya tiene y borra
  `catalogue/release.json`, que ya no diría qué se enseña.

`docs/catalogue-updates.md` cuenta la renovación mensual y la diaria.

## Desplegar

1. **El servidor**: Python 3.10 o más (3.11 recomendado), con HTTPS delante.
2. **El núcleo** es privado: un token de GitHub con lectura de `Leci37/zlecitool-core` para que `pip` lo
   instale en la etiqueta que fija `requirements.txt` (**v0.31.2**).
3. `pip install -r requirements.txt`
4. **El entorno**: el común de la familia (`FLASK_SECRET_KEY` el mismo que las otras, `DATABASE_URL` a
   Postgres, `ZLECITOOL_PUBLIC_URL`, el SMTP, `ZLECITOOL_TRUSTED_PROXIES=1` detrás de nginx, los datos
   legales) y el de la tienda: `PAYPAL_MODE=sandbox` con sus claves de prueba primero; con `live`, la
   primera compra de verdad es la prueba. Los códigos de descuento, en `DISCOUNT_CODES`.
5. **Los scripts de pago**, a `STRATEGIES_DIR` (fuera de lo que se sirve, y que se conserve entre
   despliegues): los de un catálogo nuevo, del `d_result/pine_TW_b/` del generador (`import --scripts`
   los copia, comprobados con el manifiesto del paquete, al `STRATEGIES_DIR` de la máquina donde se
   importa: al servidor se llevan de ahí); los del de ahora, con `flask --app app edgefolio
   restore-scripts` desde un clon con la historia. Con los scripts de verdad en su sitio, `flask --app app
   edgefolio levels` escribe `catalogue/levels.json` (ver «Comandos»): se sube al repo y se reinicia la tienda;
   hasta entonces, el árbol del visitante enseña la puntuación de cada resultado.
6. **Arrancar**: `gunicorn -c gunicorn.conf.py "app:create_app()"` (el `Procfile`), sin `--preload`: el
   reloj del núcleo vive en cada proceso, y con él «Tus datos». Las tablas se crean solas. «Borrar mi
   cuenta» sale sola cuando todas las herramientas de la base de datos van en la 0.30 o más nueva y han
   latido; después de volver a una copia, `flask --app app zt privacy reclose` antes de abrir las puertas.
7. **Los trabajos diarios** los hace el reloj del núcleo (las tareas `fx_update` y `send_alerts` de
   `tool.json`), en los mismos procesos de gunicorn, una vez entre todos. Si el servidor tenía un cron de
   `send-alerts` o `fx-update`, se quita: si no, correrían dos veces. Los avisos necesitan `ZLECITOOL_PUBLIC_URL`
   (paso 4).
8. **Los datos de la versión FastAPI** (`private/shop.db`) no se traen solos: sus pedidos no tienen cuenta
   del núcleo, así que pasarían a ser pedidos sin cuenta (que cada comprador ve al demostrar su correo).
   Si hace falta, se copian a `edgefolio_order` / `edgefolio_download` con un guion de una vez.

## Antes de volver a vender

Las estrategias se generaron el 2024-10-18 y llevan una «caducidad recomendada» del 2025-06-18. Una
revisión del generador encontró que un tercio calcula sus indicadores en TradingView de forma distinta
que el Python que las entrenó, y que la familia Ichimoku usó precios futuros al entrenar. Hay que
regenerar el catálogo con eso corregido antes de relanzarla. La rama `_ztool_dev` del
generador ya lo corrige; su README avisa de que, probadas con datos que no vieron, las estrategias pierden
de media después de costes, y deja al dueño cómo listarlas. Sin hacer, porque necesitan datos o
trabajos que la tienda no tiene: el trabajo diario que mide cada estrategia desde su publicación
(`catalogue/since_release.csv`) y las versiones de pago más allá de la v1.

## Qué cambió desde la versión FastAPI

- **Una herramienta zlecitool**: Flask sobre el núcleo (`app.py` como el de la plantilla, `tool.json`,
  el paquete `edgefolio/`), con `testing.check_tool(app)` en las pruebas. FastAPI y uvicorn ya no están.
- **La carcasa del núcleo**: la barra con la palabra Edgefolio, el menú de idioma, la cuenta («Entrar»),
  la raya de colores, el pie y las páginas legales son los de la familia; lo de la tienda en la barra
  (Lite | Pro, Mis estrategias, Ver tutorial, TradingView, la moneda) va en sus huecos, con el marcado
  del diseño. La página se ve como antes; cambian «Entrar», «Preferencias de cookies» en el pie y el
  aviso de cookies de la familia.
- **Las cuentas del núcleo**: se fue el acceso por enlace de la tienda y su cookie `ef_session`. Lo de
  una compra sin cuenta se ve al demostrar el correo (la tabla `edgefolio_email_proof`).
- **La base de datos común** (SQLAlchemy, tablas `edgefolio_*`) en lugar de `private/shop.db`; los
  ficheros privados, en la carpeta de datos de la herramienta.
- **Los correos del núcleo** (`zlecitool_core.mail.send`): sin SMTP, en `<datos>/mail/`. Se fueron la
  tabla `outbox`, `MAIL_MODE`, `SMTP_*`, `PUBLIC_URL` (ahora `ZLECITOOL_PUBLIC_URL`) y `tools/outbox.py`.
  El núcleo los manda en segundo plano: un fallo de SMTP queda en su log (la descarga gratis ya está
  apuntada y se puede pedir otra vez).
- **Los textos** en `i18n/ui.json` con el diccionario y el idioma del núcleo; las claves que chocaban con
  las suyas, renombradas; cada rechazo, una clave traducida.
- **Los trabajos** son comandos: `restore-scripts`, `fx-update`, `send-alerts`, `subscribers` (antes
  `tools/update_fx.py`, `tools/send_alerts.py`, `tools/outbox.py`).
- **Los límites por dirección** se cuentan con la fila de la dirección bloqueada (también con varios
  procesos y con Postgres); antes, con un candado del proceso.

## El diseño

Las vistas de `static/js/views/` son las plantillas del diseño de Claude Design (`docs/design/`) hechas
vistas de Preact una a una, con lo que la tienda adaptó (las rutas, la barra del núcleo, los enlaces
contados…). Una exportación nueva entra con una mezcla a tres:

```
python tools/design_update.py RUTA/AL/ZIP             # dice qué cambiaría; no escribe nada
python tools/design_update.py RUTA/AL/ZIP --apply     # lo aplica: vistas, textos, docs/design/ y notas
```

Donde la tienda y el diseño tocaron lo mismo queda el conflicto marcado: se resuelve quedándose con lo que
adaptó la tienda y tomando el cambio del diseño; `tests/test_page_code.py` avisa de lo que quede a medias.
Después, `pytest`, `python tools/screenshots.py` y comparar con la maqueta (`python docs/design/serve.py`,
a 1366, 768 y 390 px). El zip se guarda tal cual en `docs/handoff/<fecha>/` con su `CAMBIOS.md`: cada
diferencia, marcada herramienta o núcleo. Lo de la barra, el pie, la cuenta, el idioma o el tutorial del
núcleo va a «Para el núcleo», nunca a un parche aquí.

## Qué hay aquí

```
app.py, tool.json          el arranque y la ficha
edgefolio/                 la tienda: routes.py (las rutas), models.py (las tablas), cli.py (los comandos);
                           catalogue, search, pricing, paypal, orders, downloads, formats, free, mine,
                           proofs, alerts, media, fx, settings, shop, web (el trabajo, sin Flask);
                           your_data (lo de una cuenta en «Tus datos»: exportarlo y borrarlo);
                           release.py (importar un paquete del generador)
templates/edgefolio/       shop.html, la página sobre zt/base.html
static/                    la página tal cual (sin compilar): js/ (Preact + htm, las vistas del diseño),
                           css/ (edgefolio.css y theme.css), vendor/, trees/, img/, assets/ (dos
                           gráficos y una vista previa por estrategia, iconos)
i18n/ui.json               los textos de la tienda, en 8 idiomas
catalogue/                 catalogue.csv, indicators.csv, bundles.json, fx.json; contract.json (el contrato
                           con el generador); release.json (de qué ejecución del generador es el catálogo:
                           lo escribe la importación de un paquete); levels.json (los niveles de cada script,
                           para el árbol: la importación y `levels`); publish.py (el puente con el
                           generador) y previews.py
tests/                     las pruebas (arriba)
tools/screenshots.py       el recorrido en un navegador (las capturas de arriba)
tools/design_update.py     aplicar una exportación nueva del diseño (con dc2htm.py, que hace las vistas)
docs/                      PANTALLAS.md, FLUJO_USUARIO.md, API_ENDPOINTS.md y API_ENDPOINTS_referencia.md (la
                           tienda de hoy, sacada del código); IMPLEMENTATION-v7.md, USER-FLOW-v7.md y
                           catalogue-updates.md (el diseño, al día con cada exportación); design/ (el diseño de referencia y su flujo, con
                           su vendor/: python docs/design/serve.py lo abre), handoff/<fecha>/ (cada
                           exportación tal como llegó y su CAMBIOS.md), img/, notes/
```
