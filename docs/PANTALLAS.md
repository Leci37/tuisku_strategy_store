# Edgefolio · Pantallas

- **Qué es:** qué hay en cada pantalla de la tienda, tal como está programada en `_ztool_dev` (12 oct 2026).
- **Repositorio:** `Leci37/tuisku_strategy_store`, rama `_ztool_dev`, núcleo zlecitool-core 0.23.0.
- **Numeración:** las pantallas 1–9 son las mismas en los tres documentos:
  - `PANTALLAS.md` (este): qué contiene cada pantalla;
  - `API_ENDPOINTS.md`: qué manda y qué recibe cada pantalla;
  - `FLUJO_USUARIO.md`: qué hace el usuario, clic a clic, y los estados de cada pantalla.
- `API_ENDPOINTS_referencia.md` es la referencia completa de las 22 llamadas al servidor, en inglés.

## Cuántas hay

- **9 pantallas** numeradas.
- **5 direcciones:** `/` (Lite y Pro), `/s/<id>` (ficha), `/s/<id>/tree` (Cómo decide), `/thanks` (Gracias) y `/mine` (Mis estrategias).
- **5 diálogos:** bienvenida y selector del pack (en la 1), comparar (en la 2), estrategia gratis (la 6) y tutorial de instalación (en la 7).
- **Comunes a todas:** la barra superior, el pie y los avisos flotantes.

| # | Pantalla | Dónde | Tipo | Archivo en el repositorio | Archivo del diseño |
|---|---|---|---|---|---|
| 1 | Lite | `/`, modo Lite (por defecto) | página | `static/js/views/lite.js` | `Storefront v7.dc.html` |
| 2 | Pro | `/`, modo Pro | página | `static/js/views/pro.js` | `Storefront v7.dc.html` |
| 3 | Ficha de la estrategia | `/s/<id>` | página | `static/js/views/detail.js` | `Storefront v7.dc.html` |
| 4 | Cómo decide | `/s/<id>/tree` | pestaña de la ficha | `static/js/tree.js`, `static/js/views/tree/*.js` | `Strategy Tree.dc.html` |
| 5 | Carrito y pago | dentro de la 1 y la 2 | parte de página | `views/lite.js` (carrito flotante), `views/pro.js` (franja), `lib/vals_cart.js` | `Storefront v7.dc.html` |
| 6 | Estrategia gratis por correo | sobre la 1, 2, 3 o 4 | diálogo | `static/js/views/dialogs.js` | `Storefront v7.dc.html` |
| 7 | Gracias | `/thanks` | página | `static/js/views/thanks.js` | `Storefront v7.dc.html` |
| 8 | Mis estrategias | `/mine`, con sesión | página | `static/js/views/mine.js` | `Storefront v7.dc.html` |
| 9 | Móvil (390 px) | todas, por debajo de 640 px | adaptación | `static/js/views/phonebar.js` | `Storefront v7.dc.html` |

Todas usan la misma plantilla, `templates/edgefolio/shop.html`, y el estado de `static/js/app.js`.

---

## Común a todas

**Barra superior** (núcleo):
- la palabra «Edgefolio», el menú de idioma, la cuenta («Entrar» o el correo) y la raya de color de debajo;
- **hueco del principio** (tienda): **Lite | Pro** y **Mis estrategias**;
- **hueco antes del idioma** (tienda): **? Ver tutorial**, **TradingView** y la **moneda** (EUR, INR, CNY, SAR o USD).

**Pie** (núcleo): Privacidad, Cookies, Condiciones de uso, Aviso legal y Contacto.

**Avisos flotantes** (tienda): los rechazos del servidor, un enlace de descarga que ya no vale y la confirmación de las novedades.

No hay anuncios ni aviso de cookies.

---

## 1 · Lite

De arriba abajo:
1. **Cinta de cotizaciones:** 12 estrategias de pago, cada una con su ticker, su clave y su beneficio neto %. Se desliza de lado.
2. **Cabecera:** un gráfico de velas difuminado de fondo, el título «Estrategias para TradingView», el subtítulo y el buscador («Busca una empresa, cripto o indicador»).
3. **Pestañas:** Destacadas, Tasa de acierto, Acciones, Cripto, Gratis y Novedades · N.
4. **Aviso «Riesgo de sobreajuste».**
5. **Packs:**
   - una tarjeta por pack del catálogo: nombre, iconos de sus estrategias, precio de antes tachado, precio, «Ahorra un N %» y **Añadir pack**;
   - la tarjeta del pack propio: 5 huecos (icono o «+»), «Elige N más · 5 por 249 US$» y **Añadir pack**.
6. **Tarjetas** (24 por página), cada una con:
   - icono, ticker y nombre, y la etiqueta «Novedades» si es nueva;
   - beneficio neto % con su «?»;
   - la curva de beneficio con «⚠ Backtest»;
   - tasa de acierto y operaciones, cada una con su «?»;
   - la nota A–D y «Desde su publicación»;
   - ♡ y **Comparar**;
   - **Ficha técnica** y **Cómo decide**;
   - el precio (US$, «≈» en moneda local o «Gratis») y **Comprar** o **Descargar**.
7. «Mostrando N de M» y **Ver más**.
8. Abajo, fijos: el **carrito flotante** (pantalla 5) y la píldora **Comparar · N**.

**Diálogo de bienvenida** (3 pasos, la primera vez):
- imagen, título y texto de cada paso: «Elige un mercado», «Lee la curva» y «Compra y cárgala en TradingView»;
- los puntos de paso, **Atrás**, **Continuar** / **Empezar** y **×**.

**Selector del pack:**
- título, contador «N / 5» y buscador;
- una fila por estrategia de pago: casilla, icono, «TICKER · CLAVE», indicador y beneficio neto %. Las que ya van en un pack del carrito salen marcadas «En el carrito»;
- **Hecho**.

---

## 2 · Pro

De arriba abajo:
1. **Franja del carrito con la escalera de descuento** (pantalla 5).
2. **Panel de filtros** (a la izquierda; en el móvil, encima de la lista):
   - «N · estrategias mostradas» y **Restablecer filtros**;
   - el interruptor **Solo GRATIS**;
   - **16 rangos**, cada uno con su histograma, un deslizador de dos asas y las casillas mín. y máx.:
     - abiertos: Beneficio neto ($) y Precio ($);
     - plegados: Beneficio neto (%), Operaciones cerradas, Tasa de acierto (%), Factor de beneficio, Entrenamiento (meses), Pérdida máxima ($), Pérdida máxima (%), Beneficio medio ($), Beneficio medio (%), Velas medias por operación, Actividad por vela, Número de velas, Precisión f1 (%) y Profundidad del árbol;
   - **5 desplegables:** Símbolo, Temporalidad, Indicadores, Mercado y Fecha de publicación. Cada uno tiene buscador, **Seleccionar todo** / **Quitar todo** y una casilla por opción con su recuento (en Símbolo, también el icono).
3. **Encima de la lista:**
   - el título «Estrategias», **Ordenar** (Beneficio neto, Tasa de acierto, Precio, Operaciones cerradas) y el buscador;
   - **Filas / Tarjetas / Tabla**;
   - una etiqueta por filtro activo con su ×, y **Borrar filtros**;
   - el aviso de sobreajuste, en azul.
4. **La lista**, en una de tres vistas:
   - **Filas:** gráfico de velas de fondo; icono y nombre; ticker (enlace a TradingView), temporalidad y mercado; «CLAVE · indicador»; **Ficha técnica** y **Cómo decide**; la curva y 4 cifras (beneficio neto, tasa de acierto, beneficio neto %, operaciones); el precio y **Añadir al carrito** o **Descargar**.
   - **Tarjetas:** nombre, icono de TradingView, temporalidad, mercado y precio; las dos curvas; 6 cifras (las 4 de Filas, beneficio medio y meses de entrenamiento); «CLAVE · indicador», que enlaza a la página del indicador; **Ficha de la estrategia** y los dos botones; carrito o descarga.
   - **Tabla:**
     - columnas Símbolo (icono, ticker, nota y nombre), Temporalidad, Indicadores, Backtest (minigráfico), Beneficio neto, Beneficio neto %, Tasa de acierto, Operaciones cerradas, Beneficio medio, Meses de entrenamiento, Precio y acciones (Comparar, y carrito o Descargar);
     - una fila desplegada muestra las dos curvas, el indicador con su explicación, **Abrir en TradingView**, **Ficha técnica** y **Cómo decide**;
     - abajo, «Filas por página», «a–b de N» y los botones de página.
5. En Filas y Tarjetas, «a–b de N» y **Ver más**.

**Diálogo Comparar:**
- «Comparar estrategias» y «Hasta 3 estrategias»;
- una columna por estrategia, con «TICKER · CLAVE» y ×;
- filas de Beneficio neto (%), Tasa de acierto (%), Operaciones cerradas, Beneficio medio ($), Desde su publicación y Precio, con el mejor valor de cada fila en verde.

---

## 3 · Ficha de la estrategia

1. **Cabecera:**
   - **Volver a la tienda**;
   - gráfico de velas difuminado, icono y «Nombre · TICKER»;
   - **Abrir en TradingView** y las etiquetas de temporalidad, mercado y clave;
   - el precio y **Añadir al carrito** o **Descargar**;
   - **Abrir en otra pestaña** y ♡.
2. **Pestañas:** Ficha técnica | Cómo decide (pantalla 4).
3. **Ficha técnica**, de arriba abajo:
   1. la tarjeta «Mira cómo decide esta estrategia»;
   2. la temporalidad que hay que poner en TradingView;
   3. el aviso de sobreajuste;
   4. **Backtest frente a resultado real:** la nota A–D y las barras del backtest y de «Desde su publicación»;
   5. **Versiones**, de la actual a la 1, con «Actualización disponible» para quien tiene una anterior;
   6. el **gráfico de la estrategia** y el **gráfico de velas**;
   7. los **14 resultados del backtest:** Beneficio neto ($), Beneficio neto (%), Operaciones cerradas, Tasa de acierto, Factor de beneficio, Pérdida máxima ($), Pérdida máxima (%), Beneficio medio ($), Beneficio medio (%), Velas medias por operación, Fecha de publicación, Entrenamiento (meses), Temporalidad y Mercado;
   8. **Sobre el indicador:** «CLAVE · nombre», la descripción y «Ver el indicador en TradingView»;
   9. la **vista previa del Pine Script:** editor oscuro con el nombre del archivo y «Pine Script v5», unas líneas legibles y otras difuminadas, y el candado «El resto del script se entrega tras la compra»;
   10. **Lo que compras:** los 4 formatos: Pine Script (.pine), Markdown para IA (.md), Python (.py, BETA) y JavaScript (.js, BETA).

---

## 4 · Cómo decide

1. **Controles:** Árbol | Bloques. La vista es de visitante o de propietario según si la estrategia es tuya; no hay interruptor.
2. **El árbol:**
   - cajas de pregunta («¿≤ valor?») con sus ramas Sí y No;
   - cajas de resultado (Comprar, Vender o Esperar) con su fuerza y una barra, y un anillo en el resultado al que se llega;
   - para el visitante, ramas grises «Parte de pago» con **Comprar para desbloquear**.
3. **Valores de los indicadores:**
   - un deslizador por indicador, coloreado según lo que haría la estrategia (Compraría, Vendería, Esperaría), con marcas en los umbrales;
   - la nota «Umbrales ya optimizados»;
   - **Ejemplo de compra** y **Ejemplo de venta**.
4. **Ver todas las reglas en frases (N)** / **Ocultar las reglas**.
5. Según la estrategia:
   - si es tuya: **Descargar .pine**;
   - si es gratis: «Script completo» y **Conseguirla gratis**.
6. **Volver a la ficha técnica**.

---

## 5 · Carrito y pago

**En Lite, el carrito flotante** (abajo, fijo; solo sale con algo dentro):
- «Carrito · N» y la etiqueta «−N %» si hay descuento;
- **¿Tienes un código?**, que abre la casilla «Código», **Aplicar** y el mensaje del código;
- el subtotal tachado (solo con descuento), el total, el «≈» en moneda local y «Pagas X US$ con PayPal»;
- **Pagar**, con el icono de PayPal;
- la fila de confianza.

**En Pro, la franja del carrito** (arriba):
- «Carrito · N» y **Vaciar carrito**;
- el texto de la escalera («15 % de descuento por volumen + 20 % con el código») y el siguiente tramo («Añade X US$ más para llegar al Y %»);
- la barra con 5 marcas: 15 % / 160 US$, 20 % / 290 US$, 25 % / 500 US$, 40 % / 1.000 US$ y 70 % / 2.500 US$;
- la casilla «Código», **Aplicar** y el mensaje;
- el subtotal tachado, el total, «Pagas X US$ con PayPal» y **Pagar**;
- la fila de confianza.

**Fila de confianza:** «PayPal: nunca vemos tu tarjeta», «Enlaces: 7 días, 10 descargas», «Factura por correo» y sales@tuisku.ai.

Después de **Pagar** viene PayPal, fuera de la tienda.

---

## 6 · Estrategia gratis por correo (diálogo)

- **×**;
- icono, «Nombre · TICKER» y «CLAVE · indicador»;
- «Consíguela gratis» y «Escribe tu correo y te enviamos el enlace de descarga.»;
- el campo **Correo**, con el error debajo;
- la casilla «Avísame también de estrategias nuevas (opcional)», sin marcar;
- **Enviarme el enlace** y el enlace Privacidad;
- al terminar: «Hecho. Mira tu correo: el enlace vale 7 días.» y **Volver a la tienda**.

---

## 7 · Gracias

1. ✓ «¡Gracias! El pago se ha completado.» y «Tus estrategias están listas para descargar.»
2. El total pagado en USD, el logo de PayPal, «Pagado con PayPal · Pedido <id>» y el correo de quien pagó, recortado.
3. «Cada enlace vale 7 días y hasta 10 descargas…» y **Descargar todo**.
4. Una fila por estrategia: icono, nombre, **.pine**, **.zip**, **Ficha técnica ↗** y **Cómo decide ↗**. Si no eres quien compró, en su lugar salen `linksHiddenTitle`, `linksHiddenText` y `signInToDownload`.
5. «Añádela a TradingView», **Ver el tutorial** y 5 casillas, una por paso.
6. **Ir a Mis estrategias**, **Volver a la tienda** y «¿Problemas? sales@tuisku.ai».

**Tutorial de instalación** (diálogo, 5 pasos):
1. Descarga y copia el script.
2. Entra en TradingView.
3. Abre el gráfico correcto, con el enlace «Abrir TICKER en TradingView».
4. Pégalo en el Pine Editor.
5. Añádela al gráfico.

Cada paso lleva su imagen, título y texto. Debajo, los puntos (se pueden pulsar), **Atrás**, **Continuar** / **Listo** y **×**.

---

## 8 · Mis estrategias

- **Arriba:** el título, «Has entrado como <correo>» y **Salir**.
- **¿Compraste sin cuenta?** (`proofTitle`, `proofText`). Sale solo cuando el correo de la cuenta no está demostrado, o tras un enlace caducado:
  - el campo del correo y el botón para enviar;
  - tras enviar, `proofSent`;
  - al abrir el enlace del correo, `proofConfirmTitle` / `proofAs` y el botón `proofConfirm`.
- **Una fila por compra o descarga gratis:**
  - icono, «Nombre · TICKER» y «CLAVE · indicador · temporalidad»;
  - «Comprada el …» o «Descarga gratuita el …», y el pedido;
  - «Enlace válido N días más» o «El enlace caducó»;
  - **.pine** y **.zip**, o **Pedir un enlace nuevo**;
  - **Obtener la actualización · vN**, si hay una versión nueva;
  - **Ficha técnica ↗** y **Cómo decide ↗**.
- **Favoritas:** icono, «TICKER · CLAVE» (abre la ficha), las alertas **Versión nueva**, **Bajada de precio** y **En un pack**, y ♥. Sin favoritas: «Pulsa el corazón de una estrategia para seguirla.»
- **Abajo:** **Añádela a TradingView** y **Volver a la tienda**.

---

## 9 · Móvil (390 px)

**Barra de abajo** (fija, con botones de al menos 44 px): **Tienda**, **Buscar**, **Carrito** (con el número) y **Mías**.

**Cómo cambian las demás pantallas:**
- la barra del núcleo ocupa cuatro filas;
- las tarjetas van en una columna, y las de la ficha, una debajo de otra;
- el panel de filtros de Pro va encima de la lista, y la Tabla se desplaza de lado;
- el carrito flotante y la píldora Comparar suben a 76 px del borde, y los avisos van encima de ellos;
- los deslizadores de Cómo decide van encima del árbol;
- las 5 casillas de Gracias van una debajo de otra;
- los diálogos ocupan el ancho menos 16 px por lado.
