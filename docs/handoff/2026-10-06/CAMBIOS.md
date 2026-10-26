# Cambios · exportación del diseño del 2026-10-06 (la segunda)

Lo que trajo la exportación `edgefolio-design-2026-10-06` (Claude Design) y lo que hizo la tienda con
ello, cambio por cambio y marcado **herramienta** o **núcleo**. Lo que es del núcleo va al final, en
«Para el núcleo».

## La exportación

- **El zip:** `edgefolio-design-2026-10-06.zip`, aquí al lado, tal como llegó (sha256
  `5d6c94c345fd76f7bba37277666a5371ab050853b05a873ead2aca7792a536d6`, 85 ficheros).
- **Sobre:** `_ztool_dev` en `c0f85b99`, con zlecitool-core 0.23.0.
- **Cómo entró:** `python tools/design_update.py <zip> --apply`. La mezcla a tres dejó 10 conflictos en
  cinco vistas (`lite`, `pro`, `detail`, `dialogs`, `mine`) y 2 en notas (`docs/IMPLEMENTATION-v7.md`,
  `docs/design/PR_DESCRIPTION.md`); el texto nuevo `viewTableTab` entró limpio. El diseño trae un
  elemento nuevo de primer nivel, `cmpFloat` (la píldora de Comparar), que `tools/dc2htm.py` reparte ahora
  a `dialogs`. `support.js` carga React, ReactDOM, Babel y Font Awesome de `vendor/`: se guardan en
  `docs/design/vendor/` y la maqueta abre sin internet.
- **Cada conflicto** se resolvió quedándose con lo que la tienda adaptó (las rutas de verdad, la barra
  del núcleo, el «Pagar» ocupado, los enlaces contados, `dir="auto"`) y tomando el cambio del diseño.
- **Lo que no se usa del zip** (`versions/`, `offline/`, `prototype/brand/`, `docs/img/`, `texts.json`,
  `MANIFEST.md`) se queda dentro del zip archivado.
- **Ojo:** el `prototype/` del zip trae entera una vista previa gratis (NVDA 1Day 1S00, 253 líneas); la
  tienda las corta todas en `static/`. Una prueba (`tests/test_site.py`) comprueba que ningún script de
  pago está entero en un zip archivado. El repositorio es privado.

## Lo que cambió, pantalla por pantalla

Estado: **hecho** (se construyó ahora), **ya estaba** (la tienda ya lo hacía) o **no se hace** (y por qué).
Todo es de la herramienta salvo que se diga.

| # | Cambio del diseño | Estado | Dónde |
|---|---|---|---|
| 1 | Insignia «Nuevo» (`tabNew`) en las fichas de Lite publicadas en los últimos 30 días | hecho | `is_new` del servidor (el mismo `NEW_DAYS` que la pestaña); `vals.js` `isNew`; `lite.js`. El catálogo de hoy no tiene ninguna de los últimos 30 días |
| 1 | Añadir un lote o el pack quita los otros lotes que comparten estrategia | ya estaba | `vals_cart.js` `addBundle`; el servidor rechaza un carrito con una estrategia dos veces (`errBundleOverlap`) |
| 1 | La píldora Comparar va encima del carrito flotante, no lo tapa | hecho | `lite.js` (el «dock»), `vals_pages.js` `cmpFloat`, `dockBottom` |
| 1 | Esc cierra el selector del pack y Comparar | hecho | `app.js` `onKey`: una capa por pulsación (Comparar, pack, gratis, desplegable de Pro) |
| 2 | Fichas de Pro: «CLAVE · indicador» abre la página del indicador en TradingView | hecho | las filas de `/api/strategies` llevan `ind_url` e `ind_text` (`catalogue.row`); al pasar por encima, su explicación |
| 2 | Esc cierra los desplegables de los filtros | hecho | `app.js` `onKey` (el menú de idioma es del núcleo y ya se cerraba) |
| 2 | La vista Tabla usa la clave nueva `viewTableTab` | hecho | `vals.js`, `vals_shop.js`; `pviewTable` se quita de `i18n/ui.json` |
| 3 | «Actualización disponible» sólo para quien tiene la v1 | hecho | `vals_pages.js` `detOwnOld`: una compra (no una gratis, que al renovarse ya da la versión nueva) con `update` en `/api/mine`; Mis estrategias se lee en silencio en la ficha |
| 3 | La dirección sigue a la página: Atrás, Adelante y recargar; un id que no existe lleva a la tienda | ya estaba | rutas de verdad `/s/<id>` y `/s/<id>/tree` (`route.js`), con un aviso «no encontramos esa estrategia» |
| 4 | «Comprar para desbloquear» sólo añade; en una gratis, abre el diálogo de la gratis | ya estaba | `vals_pages.js` `treeBuy` |
| 4 | La dirección mantiene `/tree` y Atrás vuelve a la ficha | ya estaba | — |
| 4 | El árbol incrustado no carga sus letras ni sus iconos | ya estaba | la tienda carga `tree.js` como módulo, con la página |
| 5 | «Vaciar el carrito» quita también los lotes y el pack | ya estaba | `vals_cart.js` `emptyCart` |
| 5 | El subtotal tachado sólo con descuento, en Lite y en Pro | hecho | ya con tramos y códigos de porcentaje; ahora también con un código de precio fijo (`total < subtotal`) |
| 5 | Pro: «Pagas X US$ con PayPal» bajo el total en moneda local | hecho | `pro.js` (Lite ya lo tenía) |
| 5 | Lite: el código dice «Código de descuento aplicado» o «Código no válido» | hecho | `lite.js`; y aplicar otra vez el mismo código ya no borra el mensaje (`app.applyCode`); vacío quita el código |
| 6 | Correo vacío o mal escrito: `errEmailRequired` / `errEmailInvalid` del núcleo bajo el campo, borde rojo | hecho | `dialogs.js`, `vals_pages.js` `freeErr*`, `app.sendFree`; el rechazo del servidor a la dirección va también ahí |
| 6 | Intro envía, Esc cierra | hecho | Intro ya estaba (ahora no mientras se compone en zh/hi); Esc nuevo |
| 6 | Pedir otra vez la misma gratis reinicia su enlace en Mis estrategias | ya estaba | `free.claim` da un enlace nuevo; Mis estrategias enseña el último |
| 7 | Gracias: sin cambios | — | — |
| 8 | «Conseguir un enlace nuevo» conserva la fecha, el pedido y la versión | en parte | fecha y pedido, sí; **versión, no**: hay un solo script por estrategia, así que el enlace nuevo da la versión de hoy (pregunta abierta de STATUS: ¿la actualización se paga?) |
| 8 | Cada fila: `.zip` y «Ficha técnica ↗» / «Cómo decide ↗» | hecho | `mine.js` (los `.pine` y `.zip` son los enlaces contados de la tienda) |
| 9 | Móvil: el carrito flotante y la píldora, 76 px arriba, sobre la barra de abajo | hecho | el carrito ya estaba; la píldora va ahora dentro del dock |
| 9 | «Buscar» enfoca el buscador de la tienda | ya estaba | ahora con el atributo del diseño, `data-search`; en Lite, la tienda arriba, como en el diseño; en Pro, el buscador justo bajo la barra (es fija y alta en el móvil) |
| 9 | «Carrito» abre la tienda con el carrito a la vista | hecho | en Lite no mueve la página (ni con el carrito vacío); desde otra página, la tienda arriba; en Pro, la franja del carrito bajo la barra |
| — | Imágenes y textos como recursos (`window.__resources`) | no se hace | es para empaquetar la maqueta; la tienda la sirve Flask |

**Además, de paso** (de comparar `FLUJO_USUARIO.md` con la tienda):

- Los avisos (errores, novedades) se ponen encima del carrito flotante midiendo su alto, no con 84 px fijos
  (tapaban «Pagar» en el móvil).
- «Mis estrategias» sin sesión va a `/mine`, y el núcleo vuelve ahí después de entrar (antes volvía a la
  página de la que se venía).
- La casilla de novedades del diálogo gratis y el interruptor «Sólo GRATIS» de Pro son botones: Tab y
  Espacio llegan a ellos (`USER-FLOW-v7.md` §15).
- Abrir otra vez la página de gracias de un pedido da el enlace más nuevo de cada estrategia, no el que
  caducó (`orders.issue_links`).
- Una dirección `/s/<alias>` (el id de la primera tienda) lleva a `/s/<id>`, y una que no es de ninguna
  estrategia, a la tienda, sin que la página pida nada que conteste 404.

**Y de comprobar cada pantalla contra la maqueta** (cinco revisiones, a 1366, 768 y 390 px, la tienda al
lado de la maqueta nueva; ninguna encontró algo que bloquee, y cada pantalla sale igual que la maqueta,
elemento por elemento, salvo lo de aquí abajo y lo de «a propósito»):

- **Gratis y las búsquedas:** los tickers por turnos dentro de lo que queda (el mejor de cada uno primero,
  por % de beneficio). Con los turnos del catálogo entero, la pestaña Gratis ponía su mejor estrategia en
  el noveno puesto.
- **El selector del pack** deja marcar también una estrategia que ya está en un lote elegido (dice «En el
  carrito»); al añadir el pack, ese lote sale, como en el diseño. Antes la bloqueaba.
- **Los avisos** se ponen también encima de la píldora de Comparar cuando flota.
- **Un enlace de descarga que ya no vale** (gastado, caducado), abierto en la pestaña (un clic, el enlace
  del correo), vuelve a Mis estrategias (o a la tienda, sin sesión) con el porqué traducido, en vez de una
  página con el JSON; Mis estrategias se lee otra vez y la fila ofrece «Conseguir un enlace nuevo».
- **Mis estrategias:** lo último arriba, también el mismo día; la fecha y el pedido de una fila son los de
  su primera compra (antes, la fecha de una y el pedido de otra si se compró dos veces).
- **Árabe:** los tickers de un lote van en un bloque de izquierda a derecha (se partían con «··»); el
  nombre y la explicación del indicador, y el título y el texto del árbol, con `dir="auto"`.
- **Teclado:** las filas de los filtros de Pro y los 14 tramos plegados son botones (`aria-expanded`), las
  cabeceras de la Tabla llevan un botón (`aria-sort`); el diálogo de la gratis pone el cursor en su campo
  (no en una pantalla táctil) y lo devuelve al botón que lo abrió.
- **Pequeño:** los botones que parecen enlaces («Restablecer filtros», «Seleccionar todo») con el alto de
  línea del diseño; la escalera con el carrito vacío dice 160,01 US$, como cualquier presupuesto; el total
  de la página de gracias se queda al final cuando baja de línea.

## Lo que la tienda hace distinto, a propósito

Se queda como está; el diseño no lo enseña o lo simula:

- **Direcciones de verdad** (`/`, `/s/<id>`, `/s/<id>/tree`, `/thanks`, `/mine`) en vez de `#s=<id>`;
  los enlaces `#s=` de antes siguen abriendo.
- **La carcasa del núcleo:** la barra (con la palabra Edgefolio), el menú de idioma, la cuenta («Entrar»)
  y el pie. La barra ocupa cuatro filas a 390 px, en la tienda y en la maqueta.
- **PayPal de verdad**, con «Pagar» ocupado mientras se crea el pedido; el recibo por correo.
- **Los enlaces de descarga** caducan y se cuentan; en la página de gracias sólo los ve el navegador que
  pagó o la cuenta dueña; los demás van a Mis estrategias.
- **«¿Compraste sin cuenta?»** en Mis estrategias (demostrar un correo); Mis estrategias pide cuenta.
- **El contacto** sólo si `CONTACT_EMAIL` está puesto; las cifras de la fila de confianza, las del servidor.
- **Los precios, los lotes, el pack y los tramos** los pone el servidor; ningún código llega a la página
  (`DEMO20` es una maqueta).
- **El paginador** de Pro funciona; «Ver más» sólo mientras queda algo; el selector del pack busca.
- **Las cifras de ejemplo** del diseño («Desde su publicación», «2.834», la v2, los cambios de moneda)
  son las de verdad o «—» mientras no hay cálculo diario.
- **Toda vista previa pública va cortada**, también las gratis (STATUS y FLUJO dicen lo contrario de la
  tienda: la maqueta, al cortarla, coincide con ella).
- **El recorrido de bienvenida y el tutorial de instalación** son de la tienda, una vez por navegador (el
  del núcleo sólo sale con sesión; ver «Para el núcleo»).
- **`dir="auto"`** en los nombres latinos, para el árabe; los deslizadores del árbol se quedan de izquierda
  a derecha.
- **El carrito** se guarda en este navegador (`edgefolio-cart-v1`).
- **Esc** no cierra el menú de idioma desde la tienda: es del núcleo, y lo cierra él.
- **La escalera** dice «Añade 53,01 US$» donde el diseño dice 53,00: un tramo cuenta por encima de su
  importe (la regla del propio diseño), así que falta un céntimo más. El ejemplo del diseño se queda corto.
- **El árbol** colorea sus resultados con los niveles con que opera el script, no con los comentarios
  `// buy|sell` de la vista previa: el del propietario, con los de su script completo (`buyThreshold` y
  `sellThreshold`, que el generador elige para cada modelo: de 0,4 a 1,0 para comprar, de −1,0 a −0,5 para
  cerrar; `tree.js` los lee como `edgefolio/formats.py`); el del visitante, con 0,55 y −0,9 (los de todos
  los scripts de 2024), porque la vista previa se corta antes de esas líneas. Algunos salen distintos que en
  la maqueta (AMZN 1BOL: −0,78 y −0,90 «Esperar», +0,60 «Comprar»). Para hablarlo con el diseño; publicar
  los niveles de cada script, para que el visitante los vea, es decisión del dueño.
- **En una gratis, el árbol** dice «Script completo» y «Conseguirla gratis», no «Parte de pago» y «Comprar
  para desbloquear»; el clic abre el diálogo de la gratis, como en el diseño. Su vista de propietario dice
  con qué correo se pidió y que se pide gratis (`fOwnSignIn`, `fOwnNotYours`), no «compraste» ni «Cómprala».
- **Si el script completo del propietario no llega** (falta en la tienda, o falla la red), el recuadro de
  propietario lo dice en ámbar con «Descargar .pine» (`ownFail`, `tree_main.js`), y el candado de una rama
  ofrece lo mismo; nunca «no está entre las compras…» ni «Comprar para desbloquear». El diseño no tiene ese
  estado.
- **«Vista de propietario: este es el árbol completo»**, sin «primer»: el propietario elige cualquier árbol
  del bosque.
- **«Comprar para desbloquear»** del árbol sigue al carrito de la página (`inCart`, de la ficha): quitada con
  el botón de la cabecera, vuelve a decirlo y a añadirla. El diseño guardaba su propio «Añadida al carrito».
- **Una estrategia que ya es de la cuenta tampoco se vende en el árbol**, como en la ficha («Ya es tuya»): en la
  vista de visitante, su aviso y el candado de una rama dicen «Ya es tuya: … en la vista de propietario»
  (`ownedRest`, `ownedLock`) y su botón, «Ver como propietario» (`ownedBtn`), pasa a esa vista con el foco en
  «Propietario» (`data-tree-owner`); Visitante | Propietario llevan `aria-pressed` (`tree_main.js`). El diseño no
  tiene ese estado: decía «Comprar para desbloquear», que la añadía al carrito (o «Conseguirla gratis», que la
  pedía otra vez).
- **La explicación que abre un toque** (en el móvil, una pregunta; con el ratón, una rama cerrada) se queda
  abierta aunque la página se mueva sola justo después: el marco que sigue el camino y el navegador que deja
  la caja en su sitio cuando cambian los deslizadores de encima. En el diseño se cerraba en el acto.
- **Los valores divididos por el cierre** que usa el generador de 2026 (`macd__close`, `BBlower__close`…)
  llevan el nombre del valor sin `__close`, con una nota en su explicación, y un nombre sólo vale en su
  patrón (el quinto campo de cada valor en `static/trees/features.json`), también el traducido (`feat`):
  la `d` de WaveTrend no es la %D del RSI estocástico. Los que `features.json` no nombra (139 de los 182
  que preguntan las vistas previas) salen con su código, como antes: escribir sus nombres y descripciones es
  contenido del dueño.
- **Los idiomas del árbol:** la explicación de los 22 patrones de 2026-10 (15 no tenían), en los 8 idiomas
  (`patterns` de `features.json` en en y es; `pat` de `static/trees/ui.json` en los otros seis). La
  descripción de cada valor sigue sólo en en y es: en los otros idiomas sale la inglesa, con `lang="en"` y
  `dir="ltr"` (`tree_tip.js`; en árabe, sin él, su punto final saltaba al principio), como la de un patrón sin
  traducir (`tree_main.js`). La línea del patrón ya no lleva `dir="auto"`, que la tienda le puso cuando era
  inglesa: va en la dirección de la página, y en árabe «WaveTrend…», «SuperTrend…» y «CM Ultimate MA…» salían de
  izquierda a derecha.
- **Árbol | Bloques** llevan `aria-selected`, como Ficha técnica | Cómo decide.
- **«CLAVE · indicador»** de 1.402 estrategias (los 17 indicadores combinados: 2BB0, 2BT0…) lleva a la
  lista de scripts de TradingView, la salida del propio diseño para lo que no tiene página:
  `indicators.csv` no les da una dirección. Si se quiere otra, la pone el generador.
- **Los avisos** (errores, novedades) son de la tienda: el diseño no los tiene.
- **Los diálogos se quedan con el teclado** (el recorrido, el tutorial de instalación, el pack, Comparar y la
  gratis): son capas del diseño, no un `<dialog>`, y `static/js/lib/modal.js` hace lo que haría
  `showModal()`. Al abrirse, el foco entra en lo marcado con `data-ef-focus` («Continuar», el buscador del
  pack, la × de Comparar, el campo de la gratis; en una pantalla táctil, el propio diálogo); lo de detrás
  queda `inert` y no se desplaza; Tab da la vuelta dentro; al cerrarse, el foco vuelve a quien lo abrió. Si
  se abrió solo (el recorrido de la primera vez, el tutorial de /thanks) o quien lo abrió ya no está (la
  píldora de Comparar, al quitar su última columna), a `<main>`, como el diálogo del núcleo (aquí sin
  contorno, que era una raya azul a lo ancho de la página): en `<body>`, el siguiente Tab saltaba al pie. Si
  lo enfocado desaparece dentro (un paso, «Enviarme el enlace» al mandarlo), va a lo marcado: mandada la
  gratis, «Volver a la tienda». Esc en un desplegable de Pro devuelve el foco a su botón.
- **Las × dicen qué hacen:** «Cerrar» (`dialogClose`, del núcleo) en la gratis, Comparar, los avisos y las
  explicaciones de las tarjetas de Lite; «Quitar …» (`removeName`) en cada columna de Comparar y en cada
  filtro activo de Pro. En el diseño se llaman «×» (los avisos no están en el diseño). La × de las
  explicaciones del árbol, «Close» en el diseño en todos los idiomas, también dice «Cerrar» (se lo pasa la
  ficha: `closeLabel` en `detail.js`, `tipClose` en `tree_tip.js`), y la «i» de cada valor, «¿Qué es …?» en el
  idioma de la página (`whatIs`, `tree_main.js`; en el diseño, «What is …?»).
- **Las filas de la Tabla de Pro** llevan un botón en el ticker (`aria-expanded`): Tab llega a él, e Intro o
  Espacio abren la fila; con el ratón, la fila entera, como en el diseño. El ticker y el nombre van dentro en
  `<span>`, no en `<div>`: un `<button>` sólo admite texto en línea.
- **Lite | Pro** es un grupo de radio de verdad: un solo alto de Tab (el elegido) y las flechas cambian.
- **Los cuatro buscadores** (Lite, Pro, un desplegable de Pro y el pack) enseñan el foco en su caja, con el
  style-focus del diseño (`.sf-focus5`): el diseño le quita el contorno al campo y no pone otro.
- **Las imágenes del recorrido y del tutorial** no se arrastran (`draggable`): con el ratón, un
  deslizamiento que empezaba en la curva o en un logo arrastraba la imagen y no pasaba de paso. Y la zona
  que se desliza captura el puntero (`app.swDown`): uno que acaba fuera de la imagen también cuenta.
- **El chip de la moneda** sólo cambia algo cuando el idioma tiene otra moneda y su cambio llegó
  (`/api/fx`); en inglés, o sin cambios, se queda en USD, con `aria-disabled` y sin la mano del cursor
  (`header.js`, `curFixed`). En el diseño cambia siempre: en inglés, el clic no cambiaba nada que se viera,
  pero la elección pasaba al idioma siguiente (en árabe salía «USD» en vez de «SAR»).
- **«Packs» y «Arma tu pack»** salen cuando llegan los lotes (`/api/bundles`): antes, la tarjeta del pack
  enseñaba los valores de relleno («Ahorra un 0 %», «5 por 0 €») mientras tardaban o si fallaban
  (`lite.js`, `packReady`).
- **Los buscadores** de Lite, de Pro y del pack admiten 100 caracteres (`maxlength`), lo que acepta el
  servidor: con más, contestaba 400 y salía «Algo de esta petición no es válido».
- **Intro en la casilla del código** (Lite y Pro) lo aplica, como «Aplicar» (`codeKey`; no mientras se
  compone en zh/hi). En el diseño, sólo el botón.
- **«N estrategias mostradas»** de Pro va en singular con una («1 estrategia mostrada»; `shownLabel`), y
  «N seleccionados» también («1 seleccionado»). En inglés, el rango `fTreeDepth` sigue diciendo «Tree
  Deep», como el diseño y la columna del CSV: **para el diseño**, ¿«Tree depth»?
- **La fila desplegada de la Tabla se queda en la parte visible:** sus dos gráficos y la explicación del
  indicador, con sus tres acciones, van en una rejilla `sticky` del ancho de la caja que se desliza
  (`container-type:inline-size`, `100cqw`), en una columna en el móvil. En el diseño la rejilla mide lo que
  la tabla (con el catálogo de 2026-10, 1.744 px a 1366): se veía un gráfico y un trozo del otro, y la
  explicación quedaba fuera.
- **Con el tope del descuento**, la franja de Pro suma sólo lo que el código quita de verdad: en el tramo
  del 70 %, nada («70 % de descuento por volumen», sin «+ 20 % con el código»). El presupuesto da lo que
  quita cada parte después del tope (`pricing.quote`). La maqueta suma el código sin mirar el tope: un 90 %
  que nadie cobraba.
- **Gracias, con los enlaces escondidos** (otro navegador, sin la cuenta dueña): sin el bloque «Añádela a
  TradingView» ni «Ver el tutorial», que no tenían estrategia que enseñar (`thanks.js`); los enlaces y el
  tutorial están en Mis estrategias. El diseño no tiene ese estado.
- **Mis estrategias, sin nada de la cuenta:** sin «Añádela a TradingView» (`mine.js`, `mineHas`), como Gracias
  con los enlaces escondidos: el tutorial no tenía estrategia que enseñar («strategy.pine», «Busca y elige el
  intervalo , …» y «Abrir en TradingView» sin símbolo) o, llegando desde la tienda, enseñaba la primera de Lite,
  que no es suya. Sale cuando API #15 trae algo. En el diseño, Mis estrategias siempre tiene compras.
- **Árabe:** los importes en USD llevan detrás una marca de izquierda a derecha (salía «$US 172.25») y el
  chip del descuento de Lite va aislado (salía «35%−»): `fmt.js`, `vals_cart.js`. La maqueta pinta lo mismo:
  **para el diseño**.
- **El recorrido de bienvenida** de Pro no lleva cifra («Acota el catálogo con los filtros del panel: … y
  16 más.»; pregunta abierta 5), y los seis logos de su primer paso son de tickers que vende el catálogo
  (MSFT, NVDA, AMZN, ADBE, BTC y SOL): el diseño traía Apple y Ethereum, que el de 2026-10 no tiene.
- **La temporalidad que hay que poner en TradingView** va con el nombre de su menú, «1D» o «1h»
  (`tvInterval`, como el tutorial de instalación): el diseño escribe fijo «1Day», el nombre del catálogo, que
  el menú de TradingView no tiene.
- **La explicación del indicador** («Sobre el indicador» y la fila desplegada de la Tabla de Pro) lleva
  `lang="en"`: `catalogue/indicators.csv` sólo la tiene en inglés, y sale en inglés en los 8 idiomas.
  Traducirla es contenido del dueño.
- **En una gratis, la vista previa y los formatos** no hablan de comprar: «El resto del script te llega
  gratis por correo», «Lo que recibes: el script completo», «Para TradingView. Es lo que te llega por
  correo.» y «Formatos incluidos. Te llegan por correo y están en Mis estrategias.» (`scriptRestFree`,
  `buyScriptTitleFree`, `fmtPineDescFree`, `formatsNoteFree`). El diseño pone los de compra también en ella.
- **Una estrategia que ya es de la cuenta** (con la sesión abierta, lo dice Mis estrategias, API #15) lleva
  «Ya es tuya · Descargar», el enlace de su .pine, en vez de «Añadir al carrito» o «Descargar»; si el enlace
  caducó, se gastó o hay una versión nueva, «Ya es tuya · Mis estrategias», que lleva allí sin recargar
  (`ownedYours`, `data-ef-owned` en `detail.js`). El diseño no tiene ese estado. El servidor la sigue
  presupuestando: si se puede comprar dos veces lo decide el dueño.
- **El título de la pestaña** dice qué estrategia es («Snowflake · SNOW · 1BOL · 1Day · Edgefolio», con
  «Cómo decide» delante de «Edgefolio» en su pestaña): lo pone el servidor, también para la vista previa de
  un enlace (`og:title`), y la página al moverse por la tienda o cambiar de idioma (`app.tabTitle`). En la
  maqueta no cambia.
- **Las escalas de los rangos de Pro salen del catálogo:** cada barra va del mínimo al máximo de sus
  estrategias, redondeados hacia fuera (con el catálogo de 2026-10, las operaciones 0–70 y el beneficio
  neto 0–0,5 %), y es logarítmica sólo si sus valores abarcan más de dos órdenes de magnitud (hoy, el
  factor de beneficio: 1–200). Las del diseño (§12) eran las del catálogo de 2024, y las 143 estrategias
  caían en un rincón de cada barra. Por debajo de 10, el factor de beneficio va con hasta dos decimales y el
  beneficio medio (%) con dos; la actividad por vela, con hasta tres. Hasta la primera respuesta del
  servidor, las cajas de mínimo y máximo salen vacías (no con las cifras del diseño), y lo que se escribe
  antes conserva su valor.
- **«Actividad por vela»** es la columna `Trade Activity Per Candle` del generador (operaciones por vela
  del backtest: 0,002–0,238); la maqueta, que no la tenía, ponía operaciones por mes de entrenamiento.
- **Las barras «Backtest» y «Desde su publicación»** de la ficha miden contra el mejor backtest del
  catálogo (`npp_max` de `/api/config`), no contra el 100 % de la maqueta, dibujado para backtests de
  71–86 %: los de 0,03–0,44 % de 2026-10 dejaban la barra vacía.
- **«¿Compraste sin cuenta?»** dice bajo el campo lo que falla en el correo, con el borde rojo y
  `aria-invalid`, como la gratis (`mine.js`, `proofErrOn`): vacío o mal escrito (`errEmailRequired`,
  `errEmailInvalid`, del núcleo) y el rechazo del servidor a la dirección. El campo se puede vaciar, Intro no
  manda mientras se compone en zh/hi, «Hecho» se queda también cuando el bloque salió por un enlace usado, y
  un correo que la cuenta ya demostró lo dice el aviso `proofProven`, sin pedir nada. El diseño no tiene el
  bloque.
- **Un aviso nunca tapa un diálogo abierto:** con uno abierto, el aviso va arriba (`errTop`, `noticeTop`) y el
  velo le deja su sitio: su `padding-top` y los `max-height` de Comparar, el pack y el tutorial descuentan
  `toastRoom`, el alto del aviso, que mide `app.measureDock` por `data-ef-toast` (`dialogs.js`). En un móvil,
  encima del carrito flotante, el aviso tapaba «Enviarme el enlace» de la gratis, y el selector del pack (90vh)
  no le dejaba sitio ni arriba ni abajo. Los avisos no están en el diseño.

## Correcciones a la exportación

- El repositorio es `Leci37/tuisku_strategy_store` (antes `tuisku_Web_selling`, el nombre que traen
  README, STATUS, MANIFEST, FLUJO e IMPLEMENTATION).
- La tienda corta todas las vistas previas públicas, también las gratis (fila 3 de STATUS, «Facts» del
  README y FLUJO §3).
- El recorrido de bienvenida no es del núcleo en esta tienda (README, «core vs tool»): `tool.json` no
  tiene `"tour"`, porque el del núcleo no sale sin sesión.
- Los tramos de descuento están en `edgefolio/settings.py` y se sirven en `/api/config`, no en
  `api/settings.py`.
- `storefront/assets/icons/a_logo_tuisku_azulLetras.png` sale en MANIFEST, pero ninguna pantalla lo usa.
- La v2 «sin fecha» sobre la v1 fechada necesita fechas por versión, que el generador no da todavía.

## Las preguntas abiertas de STATUS.md

| # | Pregunta | Lo que hace la tienda hoy |
|---|---|---|
| 1 | Cortes de la nota (A ≥ 300, B ≥ 100, C ≥ 30) | Esos, sobre el número de operaciones; por acordar |
| 2 | ¿Los tramos se suman al precio de un lote? | Sí: tramo y código (con el tope `MAX_DISCOUNT`) también sobre lotes y pack; un código de precio fijo, no |
| 3 | Un lote nuevo sustituye a otro que comparte estrategia | Sí, en la página; el servidor rechaza (nunca elige) un carrito con una estrategia dos veces |
| 4 | ¿Qué hace «Conectar TradingView»? | Abre tradingview.com en otra pestaña y lo recuerda; no hay API a la que conectarse |
| 5 | `tour1Pro` dice «y 15 más» y son 16 | Decidido (2026-10-25): «Acota el catálogo con los filtros del panel: beneficio neto, precio, símbolo, temporalidad, indicadores y 16 más.», sin cifra (no se queda vieja), en los 8 idiomas |
| 6 | La nota se explica al pasar el ratón | Igual (`title`); en el móvil no se ve |
| 7 | ¿Comparar y Favorita en Filas y Fichas de Pro? | Igual que el diseño: sólo en la Tabla |
| 8 | La ficha no tiene resumen del carrito | Igual; en el móvil la barra de abajo cuenta lo que hay |
| 9 | Pro enseña «Pagar» con el carrito vacío | Igual; no hace nada |
| 10 | Los tramos en USD y los totales en moneda local | Igual; se paga en USD («Pagas X US$ con PayPal») |
| 11 | Revisión nativa de zh, ar e hi | Pendiente |

Y la de la pantalla 8: **¿«Conseguir la actualización» se paga?** Hoy no hay versiones más allá de la v1;
renovar un enlace da la versión de hoy. Si se paga, hace falta un script por versión y un pedido.

## Para el núcleo

Nada de esto se parchea en la tienda; si se quiere, entra en una versión del núcleo:

1. **Un tutorial de bienvenida sin cuenta**, en una herramienta pública: hoy `tour.context()` no da nada
   sin sesión y el chip «Ver tutorial» la pide. Haría falta que saliera una vez por navegador (por
   herramienta y versión), que pasara a la cuenta al entrar, y el chip sin sesión. Con eso y lo de abajo,
   la tienda dejaría su recorrido propio.
2. **Pasos del tutorial que la página elige e ilustra:** un texto según una variante
   (`zt.openTour({variant})`, p. ej. Lite o Pro) y un paso con sólo una imagen fija o con un dibujo HTML
   de la herramienta.
3. **Más de un tutorial por herramienta**, abierto por la página en su momento (p. ej. `"tours":
   {"welcome", "install"}` y `zt.openTour(nombre, {step, once})`), con puntos que se pueden pulsar y un
   evento al cerrar con el paso.
4. **Prioridad baja:** un evento cancelable en el enlace de la marca de la barra (p. ej. `zt:home`), para
   que una herramienta con rutas en el navegador vuelva a su portada sin recargar y sin perder lo que
   tiene en memoria (la lista de Comparar, los filtros).
5. **Documentar dos ganchos que la tienda usa sin contrato:** el alto de la barra fija (la tienda lee
   `header.app-topbar` para dejar un elemento justo debajo; serviría una variable `--zt-topbar-height` o
   un `scroll-padding-top` del núcleo) y un sitio para la barra fija de abajo de una herramienta (la
   tienda pone `body.app-shell{padding-bottom:64px}`; `app-shell` no está en CONTRATO.md).
6. **La barra en dos filas con la sesión abierta.** Con una cuenta, el chip de la cuenta enseña el correo
   entero (unos 210 px) y, con los chips de la herramienta, la barra no cabe en 1320 px: baja a dos filas
   (88 px en vez de 59) a 1366, 1440 y 1600, y «Lite | Pro» pasa a la segunda. Como Mis estrategias pide
   cuenta, esa pantalla nunca se ve como el diseño en un escritorio. Bastaría recortar el correo cuando
   la barra lleva chips (`.app-topbar-actions-tools .app-account-email{max-width:140px;
   overflow:hidden;text-overflow:ellipsis;white-space:nowrap}`) o enseñar sólo el avatar, con el correo
   en el menú.
7. **Para las pruebas:** `zlecitool_core.testing` podría dar un servidor en marcha de la app y una página
   de Playwright sobre el Chromium del núcleo (saltando sin Chromium), para que una herramienta pruebe su
   página en un navegador con `pytest` sin montarlo ella. Hoy la tienda lo hace en `tools/screenshots.py`.
8. **Importes con el formato del idioma en el servidor**, para los correos (p. ej.
   `zlecitool_core.i18n.format_money(valor, moneda, idioma)`): el recibo de la tienda dice «47.45 USD» en
   español, donde la página dice «47,45 US$». Con él, `orders.money()` lo usaría con el idioma de
   `email_receipt()`; la tienda no escribe su propio formateador.

## Pruebas

- `pytest`: 228 pruebas en verde (antes 210). Nuevas: `tests/test_page_code.py` (sin marcas de conflicto;
  cada valor, campo y texto que leen las vistas lo da `static/js`; los textos en los 8 idiomas con las
  mismas variables y sin claves del núcleo; los ganchos `data-search` y `data-sf-cart`); en
  `test_design_update.py`, la forma de octubre (`vendor/`, las notas nuevas, `versions/` fuera) y
  `serve.py`; el enlace del indicador en las filas y los turnos de una pestaña o una búsqueda
  (`test_search.py`); el enlace nuevo en una página de gracias reabierta, lo último arriba, la primera
  compra de una fila y un enlace gastado abierto en el navegador (`test_mine.py`); un id que no existe y
  un alias, y ningún script de pago entero en un zip archivado (`test_site.py`).
- `tools/screenshots.py`, el recorrido en un navegador, comprueba cada cambio de esta exportación; pasa
  entero, sobre una base de datos nueva, sin un error en la consola. Las 17 capturas del README, otra vez,
  y tres nuevas: `edgefolio_free_error.png`, `edgefolio_pro_es.png` y `edgefolio_phone_cart.png`.
- La «insignia Nuevo» no se ve en el catálogo de hoy (nada publicado en los últimos 30 días): se probó con
  datos de prueba.
