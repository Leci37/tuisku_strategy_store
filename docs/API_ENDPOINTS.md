# Edgefolio · Llamadas por pantalla

- **Qué es:** lo que cada pantalla manda al servidor y lo que recibe, tal como está programado en `_ztool_dev`: leído del código el 12 oct 2026 y comprobado contra `edgefolio/routes.py` el 26 oct 2026, con los arreglos del recorrido del 25 y el 26 oct.
- **Numeración:**
  - las pantallas 1–9 son las de `PANTALLAS.md` y `FLUJO_USUARIO.md`;
  - las llamadas #1–#22 son las de `API_ENDPOINTS_referencia.md`, que tiene el detalle completo en inglés: todas las reglas del servidor, los límites, la configuración y las tablas.
- **Repositorio:** `Leci37/tuisku_strategy_store`, rama `_ztool_dev`, núcleo zlecitool-core 0.31.1.
  - Las rutas están en `edgefolio/routes.py`.
  - Las llamadas de la página están en `static/js/app.js`, a través de `static/js/lib/api.js`.

## Reglas para todas

- **Sesión:**
  - Las llamadas marcadas «con sesión» la necesitan.
  - Sin sesión, el navegador va a `/login?next=<dirección>`, y un script recibe `401 {"error": "errLoginRequired"}`.
- **CSRF:** el `csrf.js` del núcleo añade el token a cada POST, PUT y DELETE.
- **Cuerpo:** siempre un objeto JSON; si no, `400 errRequest` con `field: "body"`.
- **Errores:**
  - Llegan como `{"error": "<clave>"}`, una clave del diccionario, con extras cuando hacen falta: `field`, `vars`, `items`, `bundles`, `item`, `detail` y `paid`.
  - La página la muestra traducida como aviso flotante, o bajo el campo si es del correo.
  - Sin respuesta (sin red), la página muestra `errShopNetwork`.
- **Dinero:** siempre en USD.
  - Presupuestos y recibos mandan los importes como texto con dos decimales (`"154.05"`).
  - Las filas y los packs los mandan como número.
- **Precios:** la página solo manda ids, claves de packs, el pack propio y el código que escribió el usuario. Nunca calcula un precio y nunca recibe la lista de códigos.
- **Ids:** `TICKER_INTERVALO_CLAVE_HASH`, por ejemplo `SNOW_1Day_1BOL_7abec5de`. También valen la clave del catálogo (`TICKER - INTERVALO - CLAVE - HASH`) y el alias base64 de la tienda antigua.

## La fila de estrategia (ROW)

Las listas, la ficha, los recibos y Mis estrategias mandan cada estrategia con los mismos campos:

| Campo | Qué es |
|---|---|
| `id`, `ticker`, `interval`, `key`, `hash` | Quién es |
| `name`, `ind`, `index`, `market` | Nombre, indicador, índice, y `stocks` o `crypto` |
| `price` | En USD; 0 = gratis |
| `np`, `npp` | Beneficio neto, en $ y % |
| `tr`, `w` | Operaciones cerradas; tasa de acierto (%) |
| `pf` | Factor de beneficio |
| `mdd`, `mddp` | Pérdida máxima, en $ y % |
| `avg`, `avgp` | Beneficio medio, en $ y % |
| `bars` | Velas medias por operación |
| `m`, `cand` | Meses de entrenamiento; número de velas |
| `prc`, `tdep` | Precisión f1 (%); profundidad del árbol |
| `actv` | Operaciones por vela del backtest (la columna `Trade Activity Per Candle` del catálogo); `null` si falta |
| `release`, `version`, `is_new` | Fecha de publicación; versión; publicada en los últimos 30 días |
| `grade` | Nota A–D según las operaciones cerradas (hoy, solo C y D) |
| `live`, `live_as_of` | % desde la publicación y su fecha; `null` hasta que haya cálculo diario |
| `profit`, `candle`, `icon`, `preview` | Gráficos, icono y vista previa cortada, en `/static/assets/` |
| `thumb_profit`, `thumb_candle` | Miniaturas `/thumbs/<nombre>.webp` |
| `tv_symbol`, `file` | Símbolo de TradingView (`NYSE:SNOW`); nombre del script (`Tuisku_<id>`) |
| `ind_text`, `ind_url` | Explicación del indicador (en inglés) y su página (solo en las listas y en la ficha) |

Un número que falta llega como `null`.

---

## Al cargar, en cualquier pantalla

| Llamada | Manda | Recibe |
|---|---|---|
| #1 `GET /api/config` | — | `mode` (`fake`, `sandbox` o `live`), `currency`, `max_discount`, `tiers` (`[{over, rate}]`), `pack` (`{size, price}`), `download_days`, `max_downloads`, `new_days`, `contact_email`, `strategies` (cuántas hay: 143) y `npp_max` (el mejor % de beneficio neto de los backtests del catálogo, 0,44; `null` si ninguno lo tiene: la escala de las barras de la ficha) |
| #4 `GET /api/bundles` | — | `bundles`: `[{key, name_key, ids, price, was}]`; `pack`: `{size, price, was}` |
| #5 `GET /api/fx` | — | `base`, `date`, `rates` (`USD`, `EUR`, `INR`, `CNY`, `SAR`) y `source`. Si falla, todo sale en USD |
| #2 `GET /api/strategies` (la cinta) | `paid=1&sort=hot&size=12` | Las 12 de la cinta |
| #14 `GET /api/me` (solo si la página llegó con sesión) | — | `{"email": "…"}` o `{"email": null}` |
| #21 `PUT /api/favourites/<id>` (con sesión; una llamada por favorita guardada en el navegador) | `{"alerts": {"nv", "pd", "bd"}}` | `{id, alerts, row}`. Si el servidor rechaza una, se queda en el navegador para la próxima vez; con 404 (ya no está en el catálogo), se borra |
| #3 `GET /api/strategies/<id>` (cada estrategia que la página nombra y no tiene: packs, carrito, pack propio, Comparar, favoritas) | — | La fila. Con un 404, la quita del carrito, del pack propio, de Comparar y de las favoritas, sin aviso |

**Parámetros que llegan en la dirección** (se leen una vez y se borran):

| Parámetro | De dónde viene | Qué muestra |
|---|---|---|
| `/?checkout=cancel` | PayPal, al cancelar | La tienda, con el carrito igual |
| `?link=<clave de error>` | Un enlace de descarga que ya no vale (#10) | El motivo, como aviso |
| `/?news=confirmed` o `/?news=expired` | El enlace de confirmación de novedades (#13) | El aviso |
| `/mine?proof=<token>` | El correo para demostrar una dirección (#18) | La pantalla 8, en el paso de confirmar |

---

## 1 · Lite

| Cuándo | Llamada | Manda | Recibe |
|---|---|---|---|
| Al abrir, al escribir (150 ms después de la última tecla), al cambiar de pestaña y al pulsar la pestaña marcada | #2 `GET /api/strategies` | `tab=<pestaña>&q=<texto>&size=24&page=1`; la pestaña es `hot`, `win`, `stocks`, `crypto`, `new` o `free`; `q`, hasta 100 caracteres | `rows` (24), `total` («Mostrando N de M») y `counts.new` («Novedades · N») |
| **Ver más** | #2 | Lo mismo, con `page=2, 3…` | Las 24 siguientes |
| Al pintar cada tarjeta | #6 `GET /thumbs/<nombre>.webp` | — | La miniatura (WebP de 640 px), o un `307` al PNG |
| Al buscar en el selector del pack | #2 | `paid=1&sort=hot&size=40&q=<texto>` (hasta 100 caracteres) | Las estrategias de pago |
| **Comprar**, **Añadir pack**, pack propio completo | #7 `POST /api/quote` | Ver pantalla 5 | Ver pantalla 5 |
| ♡ con sesión | #21 / #22 | Ver pantalla 8 | Ver pantalla 8 |
| ♡ sin sesión | — | Se guarda en el navegador (`edgefolio-favs-v1`) | — |

Solo cuenta la respuesta más nueva. Si llega `400 errRequest` (con `field`), sale un aviso y la lista anterior se queda.

---

## 2 · Pro

| Cuándo | Llamada | Manda | Recibe |
|---|---|---|---|
| Cada cambio de filtro, orden o búsqueda (150 ms después del último) | #2 `GET /api/strategies` | Los filtros activos, `size=25&page=1` y `facets=1` | `rows` y `total`, y además: `hist` (un histograma por rango), `ranges` (`{min, max, log, bins}`: la barra de cada rango, del mínimo al máximo del catálogo, redondeados hacia fuera; `log` solo si el diseño la quiere y los valores abarcan más de dos órdenes de magnitud) y `options` (por desplegable: `[{v, label, count, icon}]`) |
| Página de la Tabla | #2 | Lo mismo, con `page=n`, sin `facets` | La página, que sustituye a la anterior |
| **Ver más** (Filas y Tarjetas) | #2 | `page=n`, sin `facets` | Se añade a la lista |
| Imágenes | #6 | — | Miniaturas |
| Carrito | #7 | Ver pantalla 5 | Ver pantalla 5 |
| Comparar | — | Solo en el navegador | — |

**Qué manda cada filtro:**

| Filtro | Parámetro |
|---|---|
| Buscador | `q` (hasta 100 caracteres) |
| Ordenar (las pestañas de orden y las cabeceras de la Tabla) | `sort`: `np`, `npp`, `win`, `price`, `trades`, `avg`, `months` o `hot`, siempre de mayor a menor |
| Solo GRATIS | `free=1` |
| 16 rangos | `<clave>_min` y `<clave>_max`, con los decimales que enseña la etiqueta. Las claves son `np`, `price`, `npp`, `trades`, `win`, `pf`, `months`, `mlu`, `mlp`, `avg`, `avgp`, `bars`, `act`, `candles`, `prec` y `tree`. Un asa en el extremo no manda nada |
| 5 desplegables | `sym`, `tf`, `ind`, `idx` y `rel`, repetidos por cada opción marcada (`sym=ADBE&sym=AMD`). Con todo quitado se manda el parámetro vacío (`sym=`), y la lista sale vacía |

Cada histograma y cada recuento cuentan con todos los filtros menos el suyo. Si un parámetro no vale, llega `400 errRequest` con `field` (el parámetro) y sale un aviso.

---

## 3 · Ficha de la estrategia

| Cuándo | Llamada | Manda | Recibe |
|---|---|---|---|
| Al abrir `/s/<id>` (el servidor) | `GET /s/<id>` | — | La página, con el título de la estrategia (también en `og:title`). Un id que no existe → `302` a `/`; un alias o una clave → `301` a `/s/<id>` |
| Al abrir | #3 `GET /api/strategies/<id>` | — | La fila, más `ind_author` (la página no lo enseña) y `versions` (`[{v, date, note}]`, de la actual a la 1). Con `404 errUnknownStrategy` (página ya abierta o enlace `#s=`), sale un aviso y se vuelve a la tienda |
| Al abrir | `GET /static/assets/previews/<archivo>.pine` | — | La vista previa, cortada |
| Al abrir | `GET /static/assets/charts/<archivo>.png` | — | Los dos gráficos |
| Al abrir, con sesión (una vez y sin avisos) | #15 `GET /api/mine` | — | Si la estrategia está en `items`, «Ya es tuya» (con su `url`, o Mis estrategias); si `items[].update` trae una versión nueva de una compra, «Actualización disponible» |
| **Añadir al carrito** | #7 | Ver pantalla 5 | Ver pantalla 5 |
| **Ya es tuya · Descargar** | #10, con su enlace | — | El `.pine` (gasta una descarga) |
| ♡ (con sesión) | #21 / #22 | Ver pantalla 8 | Ver pantalla 8 |
| **Descargar** (gratis) | — | Abre la pantalla 6 | — |

---

## 4 · Cómo decide

| Cuándo | Llamada | Manda | Recibe |
|---|---|---|---|
| Al abrir la pestaña | `GET /static/js/tree.js` (en otro intento, `tree.js?retry=N`), sus piezas `views/tree/*.js`, `/static/trees/features.json` y `/static/trees/ui.json` | — | El código del árbol, los indicadores y sus textos. Si el código no llega, sale `errShopNetwork`, y se pide otra vez al pulsar «Cómo decide» o al volver a la pestaña |
| Visitante | `GET /static/assets/previews/<archivo>.pine` | — | La vista previa cortada, de la que sale el árbol |
| Propietario (con sesión) | #17 `GET /api/mine/<id>/script` | — | El script entero, en texto; no gasta descargas. Errores: `404 errUnknownStrategy`, `errNotOwned` y `errFileMissing` (el recuadro de propietario lo dice en ámbar) |
| **Comprar para desbloquear** | #7 | Ver pantalla 5 | Ver pantalla 5 |
| **Conseguirla gratis** | — | Abre la pantalla 6 | — |
| **Descargar .pine** (propietario) | #10, con su enlace | — | El `.pine`. Sin enlace válido, lleva a la pantalla 8 |

---

## 5 · Carrito y pago

### #7 `POST /api/quote`: el presupuesto

**Cuándo:** 120 ms después de cada cambio en el carrito, los packs, el pack propio o el código aplicado. Solo cuenta la respuesta más nueva.

**Manda:**

```json
{"items": ["UPST_1Day_1ULT_aae26f99", "UBER_1Hour_2MM0_bf5c384c"], "bundles": ["crypto"], "pack": ["id1", "id2", "id3", "id4", "id5"], "code": "demo20"}
```

- `pack`, solo con las 5 elegidas;
- `code`, solo después de pulsar **Aplicar** o Intro;
- hasta 500 ids, 50 packs y 50 ids de pack; el código, hasta 64 caracteres.

**Recibe** (el pack «Inicio en cripto», de 119 US$, y dos estrategias de 59 US$, con un código del 20 %):

```json
{"items": [{"id": "UPST_1Day_1ULT_aae26f99", "price": "38.35"}, {"id": "UBER_1Hour_2MM0_bf5c384c", "price": "38.35"}],
 "bundles": [{"key": "crypto", "price": "77.35"}], "pack": null,
 "subtotal": "237.00", "tier_rate": "0.15", "code_rate": "0.20", "discount_rate": "0.35",
 "discount": "82.95", "total": "154.05", "code_status": "applied",
 "tier_index": 1, "next_tier": {"over": "290", "rate": "0.20", "missing": "53.01"}}
```

| Campo | Dónde se ve |
|---|---|
| `total`, `subtotal`, `discount_rate` | Los totales, el subtotal tachado y la etiqueta «−N %» |
| `code_status` | `applied` → «Código de descuento aplicado»; `invalid` → «Código no válido: sin descuento», y el código deja de aplicarse; `""` → nada |
| `tier_rate`, `code_rate` | Lo que quita cada uno después del tope `MAX_DISCOUNT`, el tramo primero: la escalera de Pro («15 % de descuento por volumen + 20 % con el código»). En el tramo del 70 %, `code_rate` es `"0.00"` y la franja no lo suma; sin código o con uno no válido, `"0"` |
| `tier_index`, `next_tier` | La escalera de Pro y «Añade X más para llegar al Y %» |
| `pack` (`{ids, price, was, save}`) | El pack propio |

**Errores (400):**

| Clave | Cuándo | Qué hace la página |
|---|---|---|
| `errUnknownItems` (`items`) | Hay ids que ya no están en el catálogo | Los quita del carrito, sin aviso |
| `errUnknownBundles` (`bundles`) | Hay packs que ya no existen | Los quita, sin aviso |
| `errBundleOverlap` (`items`) | Dos packs, o un pack y el propio, comparten alguna estrategia | Aviso (la página no lo manda nunca: quita antes el pack repetido) |
| `errPackSize` (`vars.n`) | El pack propio no son 5 estrategias de pago distintas | Aviso |
| `errCartEmpty` | No hay nada | — (la página no pregunta con el carrito vacío) |
| `errRequest` (`field`) | Un campo mal formado o demasiado largo | Aviso |

El servidor no mira si una estrategia ya es de la cuenta: la presupuesta y la cobra otra vez (decisión del dueño, en los puntos a revisar).

### #8 `POST /api/orders`: crear el pedido en PayPal

- **Cuándo:** al pulsar **Pagar**. Solo un pedido cada vez: el botón queda ocupado.
- **Manda:** lo mismo que #7.
- **Recibe:** `{"id": "<id de PayPal>", "approve_url": "https://www.paypal.com/checkoutnow?token=…", …el presupuesto}`. También deja la cookie `edgefolio_buyer` (30 días), que marca este navegador como el que compró.
- **Después:** el navegador va a `approve_url`. PayPal vuelve a `/thanks?token=<id>` (pantalla 7) o, si se cancela, a `/?checkout=cancel`.
- **Errores:** los de #7, y además:
  - `400 errNothingToPay`, si el total es 0 (por ejemplo, un carrito guardado con solo estrategias que ahora son gratis);
  - `502 errPayPal` (`detail`);
  - `503 errLater`, si falta la dirección pública.
- **Con `PAYPAL_MODE=fake`:** `approve_url` lleva directamente a `/thanks?token=FAKE-…&PayerID=FAKE`.

---

## 6 · Estrategia gratis por correo

**Antes de mandar nada,** la página comprueba el correo, con los textos del núcleo:
- vacío → `errEmailRequired`;
- mal escrito → `errEmailInvalid`.

### #12 `POST /api/free`

**Manda:** `{"id": "PYPL_1Day_1MAC_2a2425c6", "email": "ana@example.com", "news": false}`

**Recibe:** `{"sent": true}`. El enlace nunca va en la respuesta: llega por correo.

**Errores:**

| Estado | Clave | Cuándo | Dónde sale |
|---|---|---|---|
| 400 | `errUnknownStrategy` | La estrategia no existe | Aviso |
| 400 | `errNotFree` | No es gratis | Aviso |
| 400 | `errEmailInvalid` (`field: "email"`) | El servidor no acepta el correo | Bajo el campo |
| 400 | `errRequest` (`field: "news"`) | `news` no es `true` ni `false` | Aviso |
| 429 | `errTooMany` | Más de 20 peticiones por hora desde la misma IP | Aviso |
| 404 | `errFileMissing` | El script no está en el servidor | Aviso |
| 503 | `errLater` | Falta la dirección pública | Aviso |
| 429 | `errFreeDaily` | Más de 10 gratis al día con el mismo correo | Aviso |

**Lo que llega por correo:**
- los enlaces del `.pine` y del `.zip` (#10; 7 días, 10 descargas) y el de Mis estrategias;
- con `news: true`, si ese correo aún no confirmó, el enlace para confirmar las novedades: #13 `GET /api/news/confirm?token=…`.
  - Lleva con un `303` a `/?news=confirmed`.
  - Si el enlace está usado, caducado (vale 30 días) o no existe, lleva a `/?news=expired`.

---

## 7 · Gracias

### #9 `POST /api/orders/<id de PayPal>/capture`

- **Cuándo:** al abrir `/thanks?token=<id>`. Sin `token`, la página va a la tienda.
- **Manda:** nada; el id va en la dirección.

**Recibe:**

```json
{"order_id": "5O190127TN364715T", "status": "PAID", "total": "154.05", "currency": "USD",
 "payer": "a•••@example.com", "valid_days": 7, "max_downloads": 10, "links_hidden": false,
 "download_all": "/api/download/all?t=…&t=…", "paid_now": true,
 "downloads": [{"id": "…", "…": "el resto de ROW", "url": "/api/download/<token>", "zip": "/api/download/<token>?format=zip"}]}
```

- Repetirla, por ejemplo al recargar, devuelve el mismo recibo y no cobra otra vez.
- **`paid_now`:** `true` solo en el cobro que pasó el pedido a pagado (el que manda el recibo por correo); cualquier cobro después, de este navegador o de otro, da `false`. La página vacía el carrito solo con `true`.
- **Quién ve los enlaces:** el navegador que compró, la cuenta que lo hizo o una cuenta que demostró el correo. A cualquier otro le llega `links_hidden: true`, con `downloads: []` y `download_all: null`, y la página no enseña el bloque de instalación.
- `payer` llega recortado, pero la página no lo enseña.
- Con el primer cobro, el servidor manda el recibo por correo, a la cuenta o al correo de PayPal.
- La primera vez, con los enlaces a la vista, la página abre el tutorial de instalación.
- **Errores:** `404 errUnknownOrder`, `409 errAccountClosed` (la cuenta que hizo el pedido se borró: no se cobra), `502 errPayPal` y `402 errPayment` (`paid` dice lo que cobró PayPal). Sale un aviso y se vuelve a la tienda.

### #10 `GET /api/download/<token>` y #11 `GET /api/download/all?t=…`

| Botón | Llamada | Recibe |
|---|---|---|
| **.pine** | #10 | `Tuisku_<id>.pine` (texto) |
| **.zip** | #10 con `?format=zip` | `Tuisku_<id>.zip`, con el `.pine`, las reglas en `.md`, el `.py` y el `.js` (beta) y un `README.txt` |
| **Descargar todo** | #11, hasta 100 tokens | `edgefolio-strategies.zip`, con el `.pine` de cada enlace válido (los que no valen se saltan, sin aviso) |

- Cada descarga gasta una de las 10 del enlace; un `.zip` cuenta como una.
- **Errores:** `404 errLinkNotFound`, `410 errLinkExpired` (`vars.e` = el correo de contacto), `429 errDownloadLimit`, `404 errStrategyGone` y `404 errFileMissing`.
- **Abierto en una pestaña,** el error llega como un `303` a `/mine?link=<clave>` (con sesión) o a `/?link=<clave>`.

El tutorial de instalación no llama al servidor; solo enlaza a tradingview.com.

---

## 8 · Mis estrategias

| Cuándo | Llamada | Manda | Recibe |
|---|---|---|---|
| Al abrir `/mine` sin sesión (el servidor) | `GET /mine` | — | El núcleo lleva a `/login?next=/mine` |
| Al abrir | #15 `GET /api/mine` | — | Ver abajo. Con `401`, lleva a entrar |
| **Pedir un enlace nuevo**, **Obtener la actualización · vN** | #16 `POST /api/mine/renew` | `{"id": "<id>"}` | La fila, como en #15. Errores: `404 errNotOwned` y `errUnknownStrategy` |
| **.pine**, **.zip** | #10 | — | Como en la pantalla 7 |
| **¿Compraste sin cuenta?** → enviar (o Intro) | #18 `POST /api/mine/proofs` | `{"email": "…"}`. La página no la hace con un correo vacío o mal escrito (error bajo el campo) ni con uno que ya está en `emails` (aviso «Ya está confirmado») | Siempre `{"sent": true}`. Errores: `400 errEmailInvalid` (`field: "email"`, bajo el campo), `429 errTooMany` y `503 errLater` |
| Al abrir `/mine?proof=<token>` | #19 `POST /api/mine/proofs/peek` | `{"token": "…"}` | `{"email": "…"}`, o `null` si el enlace no vale. No gasta el enlace |
| **Sí, <correo> es mío** | #20 `POST /api/mine/proofs/confirm` | `{"token": "…"}` | `{"email": "…"}`, y después #15 otra vez. Error: `400 errProofExpired` |
| Alertas, y ♡ al añadir | #21 `PUT /api/favourites/<id>` | `{"alerts": {"nv": true, "pd": false, "bd": false}}` | `{id, alerts, row}`. Errores: `400 errRequest` (`field`) y `404 errUnknownStrategy`. Si falla, la página vuelve a lo que tiene la cuenta |
| ♥ al quitar | #22 `DELETE /api/favourites/<id>` | — | `{"id": "…", "deleted": true}`. Si falla, la favorita vuelve a su sitio |
| **Salir** | `POST /logout` (núcleo) | — | Cierra la sesión |

**Lo que recibe #15:**

```json
{"email": "ana@example.com", "emails": ["ana@example.com"], "proof_needed": false,
 "items": [{"id": "…", "kind": "paid", "date": "2026-10-25", "at": "2026-10-25T10:04:00+00:00",
            "order": "5O190127TN364715T", "expires": "2026-11-01T10:04:00+00:00", "days_left": 7, "valid": true,
            "url": "/api/download/<token>", "zip": "/api/download/<token>?format=zip",
            "version": 1, "update": null, "row": "ROW"}],
 "favourites": [{"id": "…", "alerts": {"nv": true, "pd": false, "bd": false}, "row": "ROW"}]}
```

| Campo | Dónde se ve |
|---|---|
| `email` | «Has entrado como …» |
| `emails`, `proof_needed` | Los correos demostrados en la tienda. Con `proof_needed`, sale «¿Compraste sin cuenta?» |
| `kind`, `date`, `order` | «Comprada el …» o «Descarga gratuita el …», y el pedido |
| `valid`, `days_left`, `expires` | «Enlace válido N días más» o «El enlace caducó» |
| `url`, `zip` | Los botones **.pine** y **.zip** (`null` si el enlace no vale) |
| `update` | **Obtener la actualización · vN** (`null` si no hay versión nueva) |
| `items` vacío | Sin lista ni «Añádela a TradingView» |
| `favourites` | Las favoritas, con sus alertas |

---

## 9 · Móvil

No tiene llamadas propias: manda y recibe lo mismo que las pantallas 1–8. La barra de abajo solo navega; **Mías** sin sesión lleva a `/login?next=/mine`.

---

## Resumen: cada llamada y sus pantallas

| # | Llamada | Con sesión | Pantallas |
|---|---|---|---|
| 1 | `GET /api/config` | no | Todas, al cargar |
| 2 | `GET /api/strategies` | no | Todas al cargar (la cinta); 1, 2 |
| 3 | `GET /api/strategies/<id>` | no | 3, y cualquiera que nombre una estrategia que no tiene cargada |
| 4 | `GET /api/bundles` | no | Todas, al cargar (se usa en la 1 y la 5) |
| 5 | `GET /api/fx` | no | Todas, al cargar |
| 6 | `GET /thumbs/<nombre>.webp` | no | 1, 2 |
| 7 | `POST /api/quote` | no | 5 (desde la 1, 2, 3 y 4) |
| 8 | `POST /api/orders` | no | 5 |
| 9 | `POST /api/orders/<id>/capture` | no | 7 |
| 10 | `GET /api/download/<token>` | no (el token es la llave) | 7, 8, 3 y 4 (propietario) y los correos |
| 11 | `GET /api/download/all` | no | 7 |
| 12 | `POST /api/free` | no | 6 |
| 13 | `GET /api/news/confirm` | no | El correo de novedades → 1 |
| 14 | `GET /api/me` | no | Todas, si la página llegó con sesión |
| 15 | `GET /api/mine` | sí | 8, y la 3 en silencio |
| 16 | `POST /api/mine/renew` | sí | 8 |
| 17 | `GET /api/mine/<id>/script` | sí | 4 (propietario) |
| 18 | `POST /api/mine/proofs` | sí | 8 |
| 19 | `POST /api/mine/proofs/peek` | sí | 8 |
| 20 | `POST /api/mine/proofs/confirm` | sí | 8 |
| 21 | `PUT /api/favourites/<id>` | sí | 1, 3, 8, y al entrar |
| 22 | `DELETE /api/favourites/<id>` | sí | 1, 3, 8 |

## Lo que nunca llega a la página

- La lista de códigos de descuento, ni sus porcentajes. Solo llega el resultado del código que escribió el usuario.
- El script completo, salvo al propietario (#17) y por un enlace de descarga.
- El enlace de una descarga gratis, que solo va por correo.
- Las claves de PayPal.

## Puntos a revisar

Salieron al leer el código. Pueden ser intencionados; los dejo apuntados para que decidas. El detalle está al final de `API_ENDPOINTS_referencia.md`, y las decisiones abiertas, en «Las preguntas abiertas» de `docs/handoff/2026-10-06/CAMBIOS.md`.

1. **Vistas previas gratis:** la tienda corta todas, también las gratis. El encargo de la última exportación decía que las gratis van enteras.
2. **Script del propietario (#17):** no gasta descargas, y sigue funcionando con el enlace caducado.
3. **Actualizaciones:** renovar el enlace (#16) da la versión de hoy sin cobrar, así que «Obtener la actualización» es gratis.
4. **Versiones (#3):** no traen notas, y solo la actual trae fecha.
5. **«Desde su publicación»:** `live` es `null` hasta que algo escriba `catalogue/since_release.csv`, y ningún comando del repositorio lo hace.
6. **Factura:** la fila de confianza promete «Factura por correo», pero el servidor manda un recibo sin número de factura ni IVA.
7. **Límites por IP:** cada proceso los guarda en memoria, y vuelven a cero al reiniciar.
8. **Nombre del repositorio:** ahora es `tuisku_strategy_store`, pero los documentos de la exportación aún dicen `tuisku_Web_selling`.
9. **Comprar dos veces (#7, #8):** el presupuesto y el pedido no miran si la estrategia ya es de la cuenta: se cobra otra vez. La ficha y el árbol dicen «Ya es tuya», pero desde las tarjetas de Lite o de Pro entra en el carrito.

(El antiguo punto 7, el filtro de actividad que dividía las operaciones entre los meses, ya está arreglado: `act` es la columna `Trade Activity Per Candle` del catálogo.)
</content>
</invoke>
