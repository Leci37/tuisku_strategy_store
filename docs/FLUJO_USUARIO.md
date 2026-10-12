# Edgefolio · Flujo de usuario (la tienda en `_ztool_dev`)

- **Qué es:** cómo funciona hoy la tienda, paso a paso. Está leído del código de `_ztool_dev` el 12 oct 2026.
- **Documentos hermanos,** con la misma numeración de pantallas (1–9):
  - `docs/PANTALLAS.md`: qué contiene cada pantalla;
  - `docs/API_ENDPOINTS.md`: qué manda y qué recibe cada pantalla.
- **Llamadas al servidor:** cada paso dice cuál hace. El número (API #7) es el de `docs/API_ENDPOINTS_referencia.md` y `docs/API_ENDPOINTS.md`.
- **Repositorio:** `Leci37/tuisku_strategy_store` (antes `tuisku_Web_selling`), rama `_ztool_dev`, núcleo zlecitool-core 0.23.0.
- **Sustituye** al `docs/FLUJO_USUARIO.md` del repositorio, que era el flujo del diseño (exportación del 6 oct).
- **Diferencias con el diseño:** cada pantalla las apunta en «Distinto del diseño». Vienen de `docs/handoff/2026-10-06/CAMBIOS.md` o del código.
- **Textos:** entre comillas, los del diseño en español. Los que solo tiene la tienda, por su clave de `i18n/ui.json`.

**Etiquetas:**
- **[Servidor]:** lo decide el servidor.
- **[Navegador]:** lo guarda este navegador (localStorage).
- **📱:** diferencia en el móvil (390 px) frente al escritorio (1366 px).

---

## Común a todas las pantallas

**Archivos:**
- `templates/edgefolio/shop.html`: una sola plantilla para todas las direcciones, dentro de `zt/base.html` del núcleo.
- `static/js/app.js`: el estado, las llamadas y las acciones.
- `static/js/lib/vals*.js`: pasan el estado a los valores que leen las vistas.
- `static/js/views/*.js`: las vistas, con el marcado del diseño.

**Barra superior.** Es del núcleo: «Edgefolio», el menú de idioma, la cuenta («Entrar» o el correo) y la raya. Lo de la tienda va en sus dos huecos:
- al principio, **Lite | Pro** y **Mis estrategias**;
- antes del idioma, **? Ver tutorial**, **TradingView** y la **moneda**.

| Elemento | Clic → resultado |
|---|---|
| **Lite \| Pro** | Cambia de modo [Navegador `tuisku-sf-mode`] y va a la tienda desde cualquier página |
| **Mis estrategias** | Con sesión, pantalla 8. Sin sesión, va a `/mine`: el núcleo pide entrar y después vuelve a `/mine` |
| **? Ver tutorial** | El recorrido de bienvenida, desde el paso 1 (pantalla 1) |
| **TradingView** | Al encenderlo abre tradingview.com en otra pestaña, y se recuerda [Navegador `edgefolio-tv`]. No conecta nada: TradingView no tiene una API para eso |
| **Moneda** | Alterna entre la moneda local y USD, con los cambios de API #5. Si no llegan, todo sale en USD. No se guarda |
| **Idioma** (núcleo) | Cambia la página al momento (evento `zt:language`); el árabe va de derecha a izquierda. Esc no lo cierra desde la tienda: lo cierra el núcleo |

- **Página:** 1320 px de ancho, con bandas a todo el ancho bajo la barra.
- **Pie (núcleo):** Privacidad, Cookies, Condiciones de uso, Aviso legal y Contacto.
- **Sin anuncios** (`tool.json`: `"ads": false`).
- **Precios** [Servidor]:
  - PayPal, en USD, sin créditos.
  - Cada precio, descuento y total lo calcula el servidor (API #7).
  - Ningún código de descuento llega a la página.

**Direcciones:**

| Pantalla | Dirección | Qué hace el servidor |
|---|---|---|
| Tienda | `/` | — |
| Ficha | `/s/<id>` | Un id que no existe → 302 a `/`. Un alias o una clave → 301 a `/s/<id>` |
| Cómo decide | `/s/<id>/tree` | Igual que la ficha |
| Gracias | `/thanks?token=<pedido>` | — |
| Mis estrategias | `/mine` | Pide sesión |

- Atrás, Adelante y recargar mantienen la página.
- Los enlaces antiguos `#s=<id>` siguen abriendo la ficha.

**Al llegar** (las llamadas van a la vez):
1. Llegan los textos del núcleo (`zt.i18nReady`). **Hasta que llegan, no se pinta nada de la tienda.**
2. Se llaman API #1 (configuración), #4 (packs), #5 (cambios) y #2 (la cinta). Si la página llegó con sesión, también #14.
3. Con sesión, las favoritas guardadas en el navegador pasan a la cuenta (API #21, una llamada por favorita).
4. La dirección decide la pantalla. Estos parámetros valen una vez y se borran de la barra de direcciones:
   - `?checkout=cancel`: se vuelve de PayPal sin pagar, y el carrito sigue igual.
   - `?link=<clave>`: un enlace de descarga que ya no vale. Sale un aviso con el motivo.
   - `?news=confirmed` / `?news=expired`: sale el aviso `newsConfirmed` o `newsExpired`.
   - `/mine?proof=<token>`: lleva a la pantalla 8, a demostrar un correo.

**Avisos:**
- Cada rechazo del servidor sale como un aviso flotante, con su texto traducido. El diseño no tiene avisos.
- En Lite van encima del carrito flotante y de la píldora Comparar; la página mide su alto.

**Estados al llegar:**
- **Cargando:** se ven la barra y el pie del núcleo; el contenido queda en blanco hasta que llegan los textos.
- **Error:** si los textos no llegan, el contenido se queda en blanco. Sin textos, tampoco se puede pintar el aviso.
- **Hecho:** la pantalla de la dirección.

**Distinto del diseño:**
- Direcciones de verdad, en lugar de `#s=`.
- La barra, el idioma, la cuenta y el pie son del núcleo:
  - a 390 px, la barra ocupa cuatro filas;
  - con sesión en el escritorio, baja a dos filas, porque el correo de la cuenta ocupa unos 210 px. Está pedido al núcleo en `CAMBIOS.md`.
- Los avisos flotantes son de la tienda.

---

## 1 · Lite (por defecto)

**Archivos:** `static/js/views/lite.js`, `lib/vals_shop.js` y `lib/vals_cart.js`.

### Recorrido de bienvenida
- Es el de la tienda, no el del núcleo, porque el del núcleo solo sale con sesión.
- Sale en la tienda la primera vez que se entra desde este navegador [Navegador `edgefolio-tour-v1`]. Si se entra por otra dirección, no sale.
- Tiene 3 pasos:
  1. «Elige un mercado», con el texto de Lite o el de Pro;
  2. «Lee la curva»;
  3. «Compra y cárgala en TradingView».
- **Controles:**
  - **Continuar**, **Atrás** y **Empezar**;
  - **×** o **Esc** lo cierran;
  - **→ / ←** cambian de paso (al revés en árabe);
  - un toque en la imagen avanza, y deslizar más de 40 px cambia de paso.

### La lista

| Zona | Qué pasa | Llamada |
|---|---|---|
| **Cinta** | 12 estrategias de pago, en orden `hot`: el mejor % de cada ticker, por turnos. No se pulsa | API #2 `paid=1&sort=hot&size=12` |
| **Buscador** | Busca al escribir en el nombre, el ticker, el indicador y la clave | API #2 `q=…`, 150 ms después de la última tecla |
| **Pestañas** | Destacadas (`hot`), Tasa de acierto (`win`), Acciones, Cripto, Gratis y **Novedades · N** (las publicadas en los últimos 30 días; N = `counts.new`) | API #2 `tab=…` |
| **Lista** | 24 tarjetas. «Mostrando N de M», con el total del servidor | API #2 `size=24&page=1` |
| **Ver más** | Añade las 24 siguientes. Solo sale mientras queda algo | API #2 `page=2…` |
| **Aviso de sobreajuste** | Siempre visible | — |

Solo cuenta la respuesta más nueva: una búsqueda vieja que llega tarde no pisa la nueva.

### Packs
- **Packs del catálogo** (API #4, de `catalogue/bundles.json`):
  - cada uno muestra su nombre, el «antes» (sus estrategias sueltas) y el precio;
  - no sale un pack que perdió una estrategia, ni uno que no es más barato que sus estrategias por separado.
- **Añadir pack:** entra en el carrito [Navegador].
  - Sus estrategias sueltas salen del carrito.
  - También salen los packs que comparten alguna estrategia con él.
  - [Servidor] Un carrito con la misma estrategia en dos packs se rechaza (`errBundleOverlap`).
- **Pack propio** (`packTitle`; «Crea tu pack» en `settings.py`): 5 estrategias por 249 US$ (`PACK_SIZE`, `PACK_PRICE`).
  - Antes de elegir, el «antes» vale 5 × el precio mediano de las estrategias de pago (API #4).
  - El selector busca en todo el catálogo de pago (API #2 `paid=1&sort=hot&size=40&q=…`).
  - Se puede marcar una estrategia que ya va en un pack del carrito, que sale marcada «En el carrito». Al añadir el pack propio, ese otro pack sale del carrito.
  - El pack propio solo va al presupuesto con las 5 elegidas.
  - [Servidor] Cuesta 249 US$, o la suma de sus precios si es menor.

### Tarjetas

| Elemento | Clic → resultado |
|---|---|
| Ticker o curva | La ficha (pantalla 3) |
| «?» de cada cifra | Una burbuja con la explicación |
| **Nota** A–D | [Servidor] Según las operaciones cerradas: A desde 300, B desde 100, C desde 30, D por debajo. Al pasar el ratón, la explicación |
| «Novedades» | Sale si `is_new` [Servidor, `NEW_DAYS`] |
| «Desde su publicación» | El `live` del servidor. Mientras no haya cálculo diario, `liveUnknown` («—») |
| ♡ | Sin sesión, se guarda en el navegador [`edgefolio-favs-v1`]. Con sesión, API #21 / #22 |
| Comparar | Hasta 3 estrategias, solo en el navegador (pantalla 2) |
| **Ficha técnica** / **Cómo decide** | Pantallas 3 y 4 |
| **Comprar** / «✓ En el carrito» | Entra en el carrito o sale de él [Navegador `edgefolio-cart-v1`]. Si va dentro de un pack, quita el pack. Cada cambio pide presupuesto (API #7) |
| **Descargar** (gratis) | Pantalla 6 |

Las imágenes de las tarjetas son miniaturas WebP (API #6).

**El carrito flotante** se explica en la pantalla 5.

**Estados:**
- **Vacío:** «Ninguna estrategia coincide» (`noMatch`).
- **Cargando:**
  - la primera vez, la lista sale vacía, sin indicador;
  - al cambiar la búsqueda o la pestaña, se ve la lista anterior hasta que llega la nueva.
- **Error:** un aviso con el motivo; la lista anterior se queda.
- **Hecho:** las tarjetas y el contador.

**Distinto del diseño:**
- Cifras de verdad:
  - el total de la lista;
  - «Novedades · N», que hoy es 0 porque no hay nada publicado en los últimos 30 días;
  - «Desde su publicación», que sale como «—».
- «Ver más» funciona, y el selector del pack busca en todo el catálogo.
- Los packs son los de `catalogue/bundles.json`, no los del diseño.

---

## 2 · Pro

**Archivos:** `views/pro.js`, `lib/filters.js` (arma la consulta) y `lib/vals_shop.js`.

**Panel de filtros** (📱 encima de la lista). Cada cambio vuelve a pedir la lista (API #2) 150 ms después del último cambio, con `facets=1` cuando cambian los filtros.
- El contador «N · estrategias mostradas» y **Restablecer filtros**.
- **Solo GRATIS** → `free=1`.
- **16 rangos** → `<clave>_min` / `<clave>_max`. Las claves son `np`, `price`, `npp`, `trades`, `win`, `pf`, `months`, `mlu`, `mlp`, `avg`, `avgp`, `bars`, `act`, `candles`, `prec` y `tree`.
  - Los histogramas y la escala de cada barra los da el servidor.
  - Cada histograma cuenta con todos los demás filtros, pero sin el suyo.
  - Un asa en el extremo no manda nada: quiere decir «sin límite».
- **5 desplegables** → `sym`, `tf`, `ind`, `idx` y `rel`, repetidos tantas veces como opciones marcadas.
  - Las opciones, su recuento y los iconos los da el servidor.
  - Con todo quitado, la lista se queda vacía.
- [Servidor] Los filtros se combinan con Y, y las opciones de un mismo desplegable, con O.

**Encima de la lista:**
- **Ordenar** → `sort`, siempre de mayor a menor.
- El buscador → `q`.
- **Filas / Tarjetas / Tabla** [Navegador `tuisku-sf-pview5`].
- Una etiqueta por filtro activo, con su ×, y **Borrar filtros**.

**Vistas:**
- **Filas** y **Tarjetas:** 25 por página; «Ver más» añade la página siguiente.
- **Tabla:**
  - 25 por página, y el paginador cambia de página («a–b de N»);
  - las cabeceras numéricas ordenan, y un clic despliega una fila;
  - Comparar y el carrito van en la fila;
  - 📱 se desplaza de lado.
- «CLAVE · indicador» abre la página del indicador en TradingView (`ind_url`). Al pasar el ratón, sale su explicación (`ind_text`).

**Comparar:**
- Admite hasta 3 estrategias, desde las tarjetas de Lite y desde la Tabla.
- La píldora **Comparar · N** abre la tabla comparativa, con el mejor valor de cada fila en verde. En el precio, gana el más bajo.
- No llama al servidor.

**La franja del carrito y la escalera** se explican en la pantalla 5.

**Estados:**
- **Vacío:** `noMatch`.
- **Cargando:** se ve la lista anterior hasta que llega la nueva.
- **Error:** un aviso; por ejemplo, `errRequest` si un valor no vale.
- **Hecho:** la lista.

**Distinto del diseño:**
- El paginador de la Tabla y «Ver más» funcionan.
- Las filas de los filtros y las cabeceras de la Tabla son botones (`aria-expanded`, `aria-sort`).
- Hay 1.402 estrategias con indicadores combinados (2BB0, 2BT0…) que enlazan a la lista de scripts de TradingView, porque `indicators.csv` no les da página.

---

## 3 · Ficha de la estrategia (/s/<id>)

**Archivos:** `views/detail.js` y `lib/vals_pages.js`.

**Al abrirla se piden:**
- el registro completo (API #3): el indicador, su autor y las versiones;
- la vista previa, de `/static/assets/previews/…pine` (cortada);
- con sesión, Mis estrategias (API #15), una vez y en silencio, para saber si hay que mostrar «Actualización disponible».

**Qué ve y qué hace:**
1. **Cabecera:**
   - **Volver a la tienda**, el nombre y el ticker;
   - **Abrir en TradingView** (`tv_symbol`: `NASDAQ:AAPL`, o `BINANCE:ETHUSDT` en cripto);
   - la temporalidad, el mercado y la clave.
2. **Compra:** el precio, con **Añadir al carrito** / «✓ En el carrito», o **Descargar** si es gratis (pantalla 6).
3. **Abrir en otra pestaña** (`/s/<id>`) y ♡.
4. **Pestañas Ficha técnica | Cómo decide.** La dirección pasa a `/s/<id>/tree`.
5. **Ficha técnica**, de arriba abajo:
   - la tarjeta de «Cómo decide»;
   - la temporalidad que hay que poner en TradingView;
   - el aviso de sobreajuste;
   - el backtest frente a «Desde su publicación», con la nota;
   - **Versiones**;
   - los dos gráficos;
   - los **14 resultados**, con «—» si falta un dato;
   - **Sobre el indicador**;
   - la **vista previa** del Pine Script, cortada;
   - los **formatos**: .pine, .md, .py (beta) y .js (beta).
6. **Versiones** [Servidor]: van de la actual a la 1, sin notas, y solo la actual lleva fecha.
   - «Actualización disponible» sale solo a quien compró una versión anterior (`update` en API #15).
   - Una descarga gratis renovada ya da la versión nueva.

**Estados:**
- **Cargando:** el editor de la vista previa sale vacío hasta que llega.
- **Error:**
  - si la estrategia no existe (404), sale un aviso y se vuelve a la tienda;
  - si la vista previa no llega, el editor se queda vacío, sin mensaje.
- **Hecho:** la ficha completa.

📱 Las tarjetas van una debajo de otra, y el editor se desplaza de lado.

**Distinto del diseño:**
- Toda vista previa pública va cortada, también la de las gratis. El diseño mostraba entera la gratis; está en los puntos a revisar de `API_ENDPOINTS_referencia.md`.
- Las versiones no tienen notas, y «Desde su publicación» sale como «—».

---

## 4 · Cómo decide (/s/<id>/tree)

**Archivos:**
- `static/js/tree.js`, que se carga al abrir la pestaña;
- `views/tree/*.js`;
- `static/trees/features.json` y `static/trees/ui.json`.

**De dónde sale el árbol:**
- **Visitante:** de la vista previa cortada.
- **Propietario** (con sesión y la estrategia comprada): del script entero (API #17), así que el árbol sale completo.

**Controles:** los mismos que en el diseño:
- Árbol | Bloques;
- clic en una pregunta o en su Sí / No;
- los resultados, con su regla;
- arrastrar el árbol;
- los deslizadores de los indicadores;
- los ejemplos de compra y venta;
- «Ver todas las reglas» y «Volver a la ficha técnica».

**Botones de compra y descarga:**
- **Comprar para desbloquear** solo añade al carrito.
- En una estrategia gratis, el árbol dice «Script completo» y «Conseguirla gratis», que abre la pantalla 6.
- **Descargar .pine** (propietario) abre su enlace de descarga o, si no lo tiene, Mis estrategias.

**Estados:**
- **Cargando:** el mensaje de carga del árbol.
- **Error:**
  - si el código del árbol no llega, sale el aviso `errShopNetwork`;
  - si no llegan sus datos, sale el mensaje de error del árbol, con el motivo.
- **Hecho:** el árbol.

📱 Los deslizadores van encima del árbol.

**Distinto del diseño:**
- Los resultados se colorean con los niveles con que opera el script (comprar desde 0,55, cerrar hasta −0,9), no con los comentarios de la vista previa. Algunos salen distintos que en la maqueta; por ejemplo, AMZN 1BOL.
- En árabe, los deslizadores siguen yendo de izquierda a derecha.

---

## 5 · Carrito y pago

**Archivos:** `views/lite.js` (el carrito flotante), `views/pro.js` (la franja) y `lib/vals_cart.js`.

**El carrito** [Navegador `edgefolio-cart-v1`] guarda las estrategias, los packs, el pack propio y el código. Cada cambio pide un presupuesto (API #7) 120 ms después; solo vale la respuesta más nueva.

| Elemento | Comportamiento |
|---|---|
| «Carrito · N» | — |
| ¿Tienes un código? / Código + **Aplicar** | El código va al servidor al pulsar Aplicar. Según `code_status`, sale «Código de descuento aplicado» o «Código no válido»; un código no válido se quita. Aplicar otra vez el mismo no borra el mensaje, y la casilla vacía quita el código |
| Escalera (Pro) | Los tramos vienen de API #1. «Añade X más para llegar al Y %» usa `next_tier.missing` (detalle bajo la tabla) |
| Totales | El subtotal tachado solo si hay descuento, y el total. En moneda local, «≈ …» y «Pagas X US$ con PayPal» |
| Fila de confianza | PayPal; «Enlaces: 7 días, 10 descargas», con las cifras de API #1; «Factura por correo»; el correo de contacto (`CONTACT_EMAIL`) |
| **Vaciar carrito** (Pro) | Quita las estrategias, los packs y el pack propio |

Sobre la escalera: un tramo cuenta solo por encima de su importe. Por eso dice 53,01 US$ donde el diseño dice 53,00, y con el carrito vacío dice 160,01 US$.

**Descuentos** [Servidor]:
- Por tramos: más de 160 US$ → 15 %; más de 290 → 20 %; más de 500 → 25 %; más de 1.000 → 40 %; más de 2.500 → 70 %.
- Un código suma su porcentaje al del tramo. El descuento total tiene un tope del 70 %.
- Un código de precio fijo pone ese precio a cada estrategia suelta, y entonces no se aplica el tramo.

**Pagar:**
1. Con el carrito vacío, no hace nada.
2. API #8 crea el pedido en PayPal por el total del servidor. **Pagar** queda ocupado, así que un doble clic no crea dos pedidos.
3. El navegador va a PayPal (`approve_url`).
4. Si se aprueba, PayPal vuelve a `/thanks?token=<pedido>` (pantalla 7).
5. Si se cancela, vuelve a `/?checkout=cancel`: la tienda, con el carrito intacto. Con el botón Atrás del navegador, **Pagar** se libera.

**Estados:**
- **Vacío:** Lite no muestra el carrito; Pro muestra «Carrito · 0».
- **Cargando:**
  - se ve el presupuesto anterior hasta que llega el nuevo;
  - **Pagar** está ocupado mientras se crea el pedido.
- **Error:**
  - código no válido;
  - un aviso con `errBundleOverlap`, `errPackSize`, `errPayPal` o `errLater`;
  - las estrategias o los packs que ya no se venden salen solos del carrito.
- **Hecho:** PayPal.

📱 El carrito flotante va 76 px por encima del borde, sobre la barra de abajo.

**Distinto del diseño:**
- PayPal de verdad, y las cifras del servidor.
- La escalera dice 53,01 en vez de 53,00.

---

## 6 · Estrategia gratis por correo (diálogo)

**Archivos:** `views/dialogs.js` y `lib/vals_pages.js`.

1. **Se abre** con **Descargar** en una estrategia gratis (pantallas 1–3), o con «Conseguirla gratis» en el árbol.
   - El cursor va al campo del correo, salvo en pantallas táctiles.
   - Al cerrarse, el foco vuelve al botón que lo abrió.
2. **La casilla de novedades** empieza **sin marcar** cada vez que se abre el diálogo.
3. **Enviarme el enlace:**
   - **Correo vacío:** `errEmailRequired`, bajo el campo y con el borde rojo (texto del núcleo).
   - **Correo mal escrito:** `errEmailInvalid`, igual (texto del núcleo).
   - **Correo bien escrito:** se envía (API #12).
     - Si el servidor rechaza el correo, el error sale también bajo el campo.
     - Los demás rechazos salen como aviso: `errFreeDaily` (más de 10 al día con el mismo correo), `errTooMany` (más de 20 por hora desde la misma IP), `errNotFree` o `errLater`.
   - **Hecho:** «Hecho. Mira tu correo: el enlace vale 7 días.» y **Volver a la tienda**.
4. **El correo** lleva el enlace del .pine y el del .zip (7 días, 10 descargas), y el de Mis estrategias. El enlace nunca va en la respuesta del servidor.
5. **Con la casilla marcada,** el correo pide confirmar las novedades (doble opt-in, RGPD).
   - El enlace lleva a `/?news=confirmed` y al aviso `newsConfirmed`.
   - Si caducó (vale 30 días), lleva al aviso `newsExpired`.
6. **Dónde aparece la estrategia:** con sesión, en Mis estrategias en seguida. Sin sesión, cuando la cuenta demuestre ese correo (pantalla 8).
7. **Teclado:**
   - **×** o **Esc** cierran el diálogo.
   - **Intro** envía, salvo mientras se compone texto en chino o en hindi.

**Estados:**
- **Vacío:** el formulario.
- **Cargando:** el botón no envía otra vez mientras espera la respuesta.
- **Error:** bajo el campo, o como aviso.
- **Hecho:** el mensaje verde.

---

## 7 · Gracias (/thanks)

**Archivos:** `views/thanks.js`; el tutorial de instalación está en `views/dialogs.js`.

1. PayPal vuelve a `/thanks?token=<pedido>`. Sin `token`, la página lleva a la tienda.
2. **El cobro** (API #9) cobra el pedido y devuelve el recibo.
   - Repetirlo, por ejemplo al recargar, no cobra otra vez.
   - Con el primer cobro sale el recibo por correo: las líneas, el total y el enlace a Mis estrategias.
3. **El carrito** de este navegador se vacía.
4. **El pedido:** el total en USD y «Pagado con PayPal · Pedido <id de PayPal>», con el correo de quien pagó recortado (a•••@dominio).
5. **Los enlaces:**
   - **Quién los ve:** el navegador que hizo el pedido, la cuenta que lo hizo o la cuenta que demostró su correo. Ven una fila por estrategia con:
     - **.pine** y **.zip** (API #10);
     - **Ficha técnica ↗** y **Cómo decide ↗**.

     Encima, **Descargar todo** (API #11). Cada descarga gasta una de las 10 del enlace.
   - **Cualquier otro** ve `linksHiddenTitle` y `linksHiddenText`, con `signInToDownload`: los enlaces están en Mis estrategias.
6. **El tutorial de instalación** (5 pasos):
   - se abre solo la primera vez [Navegador `edgefolio-install-v1`], y solo si hay un script que instalar;
   - usa la primera estrategia del pedido;
   - se puede reabrir con **Ver el tutorial** o con las casillas de los pasos.
7. **Ir a Mis estrategias** y **Volver a la tienda**.

**Estados:**
- **Cargando:** no hay pedido que mostrar hasta que contesta el cobro.
- **Error:** `errPayment` (PayPal no cobró el importe del pedido), `errPayPal` o `errUnknownOrder`. Sale un aviso y se vuelve a la tienda.
- **Hecho:** el pedido y sus enlaces.

**Distinto del diseño:**
- El número de pedido es el de PayPal, no «EF-xxxxx».
- Los enlaces caducan, se cuentan y solo los ve quien compró.

---

## 8 · Mis estrategias (/mine)

**Archivos:** `views/mine.js` y `lib/vals_pages.js`.

**Entrar:**
- Pide sesión. Sin ella, el núcleo lleva a `/login?next=/mine` y después vuelve aquí.
- Al entrar, las favoritas del navegador pasan a la cuenta (API #21), y luego se lee la lista (API #15).

**Qué es de la cuenta** [Servidor]:
- lo que hizo con la sesión abierta;
- lo que se hizo sin cuenta con un correo que la cuenta ha demostrado.

Nunca entra algo solo porque coincide con el correo de alta.

**Una fila por estrategia**, la más reciente arriba:
- «Comprada el …» o «Descarga gratuita el …», con la fecha de la primera vez, y el pedido.
- «Enlace válido N días más» o «El enlace caducó». También caduca al gastar las 10 descargas.
- **.pine** y **.zip**, mientras el enlace vale.
- **Pedir un enlace nuevo**, cuando el enlace ya no vale (API #16).
  - Da otros 7 días y 10 descargas.
  - La fecha y el pedido se quedan, y el script es el de la versión de hoy.
  - Con un enlace que aún vale, no cambia nada.
- **Obtener la actualización · vN**, si hay una versión más nueva que la del enlace. Hace la misma llamada, sin cobrar.
- **Ficha técnica ↗** y **Cómo decide ↗**.

**¿Compraste sin cuenta?** (`proofTitle`, `proofText`). Sale cuando el correo de la cuenta aún no está demostrado (`proof_needed`), o después de un enlace caducado.
1. Se escribe el correo; por defecto, el de la cuenta. API #18 → `proofSent`. La respuesta es siempre la misma, así que no dice si con ese correo se compró algo.
2. El correo lleva `/mine?proof=<token>`, que vale 24 horas, una vez y solo para esta cuenta.
3. Al abrirlo, la página pregunta de qué correo es (API #19) sin gastarlo, y muestra `proofConfirmTitle` / `proofAs` con el botón `proofConfirm`.
4. El clic confirma (API #20), y la lista se vuelve a leer con los pedidos y las descargas gratis de ese correo.
5. Si el enlace está usado, caducado o es de otra cuenta, sale `errProofExpired`, y el bloque se ofrece otra vez.

**Favoritas:**
- Son las de la cuenta (API #15).
- Las alertas **Versión nueva**, **Bajada de precio** y **En un pack** se guardan al momento (API #21).
- ♥ quita la favorita (API #22).
- [Servidor] Los correos de las alertas los manda el trabajo diario (`send-alerts`), y solo a un correo demostrado.

**Botones:**
- **Añádela a TradingView** abre el tutorial de instalación.
- **Volver a la tienda.**
- **Salir** (`signOut`) cierra la sesión y lleva a la tienda.

**Estados:**
- **Cargando:** hasta que llega API #15.
- **Vacío:**
  - sin compras, la lista sale vacía (no está diseñado);
  - sin favoritas, «Pulsa el corazón de una estrategia para seguirla.».
- **Error:** un aviso. Sin sesión (401), lleva a entrar.
- **Hecho:** las filas y las favoritas.

**Distinto del diseño:**
- Pide cuenta.
- Tiene el bloque «¿Compraste sin cuenta?».
- El enlace nuevo da la versión de hoy, no la de la compra.

---

## 9 · Móvil (390 px) con la barra de abajo

**Archivo:** `views/phonebar.js`. Sale por debajo de 640 px.

| Botón | Qué pasa |
|---|---|
| **Tienda** | La tienda, arriba. Sale en azul si ya estás en ella |
| **Buscar** | La tienda, con el cursor en su buscador (`data-search`). En Lite, la tienda arriba; en Pro, el buscador justo bajo la barra fija |
| **Carrito** (con número) | En Pro, la franja del carrito, bajo la barra. En Lite no se mueve nada, porque el carrito flotante ya está a la vista. Desde otra página, la tienda arriba |
| **Mías** | Pantalla 8, o entrar si no hay sesión. Sale en azul si estás en ella |

**Medidas y colocación:**
- Los botones miden al menos 44 px, y quedan 64 px libres bajo el pie.
- El carrito flotante y la píldora Comparar van a 76 px del borde, y los avisos, encima de ellos.

**Cómo se adapta la página:**
- La barra del núcleo ocupa cuatro filas.
- Las tarjetas van en una columna.
- El panel de Pro va encima de la lista, y la Tabla se desplaza de lado.
- Los diálogos ocupan el ancho menos 16 px por lado.

---

## Teclado

| Tecla | Dónde | Resultado |
|---|---|---|
| **Esc** | Recorrido de bienvenida, tutorial de instalación | Lo cierra y lo marca como visto |
| **Esc** | Comparar, selector del pack, diálogo de la gratis, desplegable de Pro | Cierra uno cada vez, en ese orden |
| **→ / ←** | Los dos tutoriales | Paso siguiente o anterior (al revés en árabe) |
| **Intro** | Casillas mín. y máx. de Pro | Aplica el valor |
| **Intro** | Correo de la gratis | Envía |
| **Tab**, **Espacio** | Casilla de novedades, «Solo GRATIS», filas de los filtros, cabeceras de la Tabla | Llegan a ellos y los activan, porque son botones |
