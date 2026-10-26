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
| 1 | Insignia «Nuevo» (`tabNew`) en las fichas de Lite publicadas en los últimos 30 días | hecho | `is_new` del servidor (el mismo `NEW_DAYS` que la pestaña); `vals.js` `isNew`; `lite.js`. Con el catálogo de 2026-10, todas: se publicaron el 13 oct 2026 y la llevan hasta el 12 nov 2026 |
| 1 | Añadir un lote o el pack quita los otros lotes que comparten estrategia | ya estaba | `vals_cart.js` `addBundle`; el servidor rechaza un carrito con una estrategia dos veces (`errBundleOverlap`) |
| 1 | La píldora Comparar va encima del carrito flotante, no lo tapa | hecho | `lite.js` (el «dock»), `vals_pages.js` `cmpFloat`, `dockBottom` |
| 1 | Esc cierra el selector del pack y Comparar | hecho | `app.js` `onKey`: una capa por pulsación (Comparar, pack, gratis, desplegable de Pro) |
| 2 | Fichas de Pro: «CLAVE · indicador» abre la página del indicador en TradingView | hecho | las filas de `/api/strategies` llevan `ind_url` e `ind_text` (`catalogue.row`); al pasar por encima, su explicación |
| 2 | Esc cierra los desplegables de los filtros | hecho | `app.js` `onKey` (el menú de idioma es del núcleo y ya se cerraba) |
| 2 | La vista Tabla usa la clave nueva `viewTableTab` | hecho | `vals.js`, `vals_shop.js`; `pviewTable` se quita de `i18n/ui.json` |
| 3 | «Actualización disponible» sólo para quien tiene la v1 | hecho | `vals_pages.js` `detOwnOld`: una compra (no una gratis, que al renovarse ya da la versión nueva) con `update` en `/api/mine`; Mis estrategias se lee en silencio en la ficha |
| 3 | La dirección sigue a la página: Atrás, Adelante y recargar; un id que no existe lleva a la tienda | ya estaba | rutas de verdad `/s/<id>` y `/s/<id>/tree` (`route.js`); un id que no existe, 302 a la tienda sin aviso; con un enlace antiguo `#s=<id>`, el aviso «No encontramos esa estrategia.» |
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
| 8 | «Pedir un enlace nuevo» conserva la fecha, el pedido y la versión | en parte | fecha y pedido, sí; **versión, no**: hay un solo script por estrategia, así que el enlace nuevo da la versión de hoy (pregunta abierta de STATUS: ¿la actualización se paga?) |
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
- La casilla de novedades del diálogo gratis y el interruptor «Solo GRATIS» de Pro son botones: Tab y
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
  página con el JSON; Mis estrategias se lee otra vez y la fila ofrece «Pedir un enlace nuevo».
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
  son las de verdad; «Desde su publicación» no sale mientras ninguna estrategia tiene cifra (abajo).
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
  cerrar; `tree.js` los lee como `edgefolio/formats.py`); el del visitante, con los que publica la tienda
  (`catalogue/levels.json`, leídos de cada script completo; API #3 los manda como `buy_at` y `close_at`),
  porque la vista previa se corta antes de esas líneas. Algunos salen distintos que en la maqueta (AMZN 1BOL:
  −0,78 y −0,90 «Esperar», +0,60 «Comprar»). Para hablarlo con el diseño.
- **Sin los niveles del script** (el visitante, mientras la tienda no los publica para esa estrategia), ningún
  resultado dice Comprar, Vender ni Esperar (`scored` en `tree.js`): cada uno enseña su puntuación («Puntuación
  +0,88», en gris oscuro y con el icono de un medidor, en el árbol, en Bloques, en «Resultado del árbol» y en
  su explicación); la leyenda dice «Puntuación» en vez de Comprar | Vender | Esperar y, debajo, por qué
  (`noLevels`, `data-tree-scored` en `tree_main.js`); los deslizadores no pintan sus zonas de colores ni su
  leyenda (dirían qué haría la estrategia), y su ayuda dice que se ve a qué resultado llega, no qué haría
  (`optTextScore`); la escala de «Resultado del árbol» dice −1 y +1, sin «Venta» ni «Compra», y va en gris, como
  los dos ejemplos (`gaugeBg`, `exBuy*` y `exSell*` en `tree_main.js`); el tercer paso, los dos ejemplos y su
  ayuda y el pie de la explicación de un resultado hablan de la puntuación (`s3Score`, `hiEx`, `loEx`,
  `exHelpScore`, `leafFootScore`), y «Ver todas las reglas» las junta en un grupo, de la puntuación más alta a la
  más baja (`results`, `leadScore1`, `leadScoreN`). El diseño no tiene ese estado: siempre dice comprar, vender o
  esperar.
- **La escala de «Resultado del árbol» va de izquierda a derecha** también en árabe (`dir="ltr"` y el gancho
  `data-tree-gauge` en `tree_main.js`), como su barra y los deslizadores, con cada extremo en su idioma
  (`dir="auto"`): en árabe, «بيع −1» quedaba a la derecha, bajo el extremo verde (el de +1), donde estaba la marca
  de una compra. Y el + de una puntuación lo pone el formato del idioma (`signDisplay` en `tree.js`), como el −:
  en árabe salía «0.89+».
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
  la `d` de WaveTrend no es la %D del RSI estocástico. Cada valor que toman los árboles del catálogo tiene su
  nombre y su descripción, escritos de lo que calcula el código del generador (`TW_pines_script/`): eran 44, y
  181 salían con su código (entre ellos, 140 de los 182 que preguntan las vistas previas). Un nombre que usan dos
  patrones lleva el suyo en la clave (`d@Wave_Trend_Calculation`, `basis@Squeeze_Momentum_Indicator`), que
  `tree.js` mira antes (`keyOf`). Ocho de los 44 no decían lo que calcula el código y se corrigieron
  (`ema12`, `ema13`, `ad_mf`, `MFI_High`, `MFI_Low`, `d_k`, `smoothK_k`, `smoothD_d`).
- **Los idiomas del árbol:** la explicación de los 22 patrones de 2026-10 (15 no tenían), en los 8 idiomas
  (`patterns` de `features.json` en en y es; `pat` de `static/trees/ui.json` en los otros seis). El nombre de
  cada valor, también en los 8 (`feat`), y su descripción, en los 8 la de los 225 (`featDesc` de `ui.json`, con la
  nota de los divididos por el cierre en el idioma de la página; las de los 181 de 2026-10, desde el 2026-10-26).
  Una que faltara saldría en inglés, con `lang="en"` y `dir="ltr"` (`tree_tip.js`; en árabe, sin él, su punto final
  saltaba al principio), como la de un patrón sin traducir (`tree_main.js`). La línea del patrón ya no lleva
  `dir="auto"`, que la tienda le puso cuando era inglesa: va en la dirección de la página, y en árabe «WaveTrend…»,
  «SuperTrend…» y «CM Ultimate MA…» salían de izquierda a derecha.
- **Árbol | Bloques** llevan `aria-selected`, como Ficha técnica | Cómo decide.
- **«CLAVE · indicador»** de 43 estrategias de las 94 (los 17 indicadores combinados: 2BB0, 2BT0…) lleva a la
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
  «N seleccionados» también («1 seleccionado»). En inglés, el rango `fTreeDepth` dice «Tree depth» (decidido el
  2026-10-26, E12d); la columna del CSV sigue siendo «Tree Deep», que es la del contrato con el generador. **Para el
  diseño:** su maqueta dice «Tree Deep»; que diga «Tree depth».
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
- **La explicación del indicador** («Sobre el indicador» y la fila desplegada de la Tabla de Pro, y el `title` de
  «CLAVE · indicador» en Pro) sale en el idioma de la página (2026-10-26, E12a): `catalogue/indicators.csv` la tiene
  en los 8 (`Explanation`, la inglesa, y `Explanation_es`…`_hi`) y API #2 y #3 mandan la del idioma de la petición
  (`ind_text`) con su idioma (`ind_lang`). La `<p>` y el `<span>` llevan el `lang` y el `dir` que dice la fila
  (`exLang`, `exDir` en `detail.js` y `pro.js`): los de la página, y `lang="en"` con `dir="auto"` sólo si una falta
  (nunca `null`: Preact lo dejaría en `lang=""`, «idioma desconocido»). La página pide el catálogo en su idioma
  (`?ind_lang=`; con `?lang=`, el núcleo lo guardaba en la cookie del idioma, y una pestaña en otro idioma cambiaba
  con cada lista el de la próxima visita) y, al cambiarlo, otra vez la ficha a la vista y las páginas de Pro que se
  ven, sin moverse. Cada explicación dice lo que calcula el código del indicador en el generador
  (`TW_pines_script/pines_script/*.py`) y no promete nada (revisión de W2): la de 1TMA hablaba de una media
  triangular con bandas, y las de 1BOL, 1WIL y 1ULT de señales «fiables» y «precisas»; una combinada nombra sólo lo
  que usa (`Key Combination`: 2MM0, 1M00; 2BB0, 1B00).
- **Lo que cuenta un ajuste** (los días y las descargas de un enlace, `DOWNLOAD_DAYS` y `MAX_DOWNLOADS`; las
  estrategias de un pack, `PACK_SIZE`) lleva la forma que pide su número, cada cuenta con su clave (`linkDays`,
  `linkDownloads`): la fila de confianza bajo «Pagar» (`trustLinks`), la nota de los enlaces de Gracias
  (`linksNote`), el aviso de un pack que no vale (`errPackSize`), y los correos del recibo, de la gratis y de los
  avisos (`mailAlertBundle`). En árabe, «يومين» y «تنزيلين» con 2, «11 يومًا» con 11; antes, el texto llevaba escritos
  los 7 días y las 10 descargas de hoy («7 أيام», «10 تنزيلات»). La maqueta los escribe fijos: **para el diseño**.
- **Una respuesta con el cuerpo cortado** (una navegación o la red la cortaron a medias) es «sin conexión», como no
  tener respuesta (`api.js`): antes llegaba `null`, y leerlo era un error en la consola (`m.items`, `r.id`).
- **Las cajas de los resultados del árbol** se llaman (`aria-label`) como lo que enseñan, «Esperar −0,45» o
  «Puntuación +0,89», en el idioma de la página (`tree.js`; el marcado de la vista, igual). En el diseño se llaman con
  su línea de Pine (`ret := 0.452000 // buy`), cuyo comentario es de la fábrica (±0,7) y no de los niveles del
  script: un lector de pantalla oía «buy» donde la caja decía Esperar.
- **Los plurales árabes:** lo que cuenta lleva la forma que pide el número (de 3 a 10, el plural: «9 صفقات»; de 11
  a 99, el singular: «36 صفقة»): la nota de cada estrategia (`gradeTip`), sus operaciones en las fichas de Lite
  (`tradesWord`: la ficha lee `r?.tradesWord`, de cada fila, y no `v.tx?.tradesWord`, uno para todas; `lite.js`),
  entre cuántas se eligieron (`riskTried`, por las probadas), los cortes de la nota (`gradeCuts`, por el de la A) y, en
  el árbol, sus reglas, sus resultados y sus ramas cortadas (`rulesN`, `visible`, `complete`, `paidN`, `ctaN`,
  `fPaidN`, `fCtaN`, elegidas en `tree.js` con `Intl.PluralRules`). En español, alemán, francés y portugués, «1
  operación cerrada». La maqueta pone una sola forma: **para el diseño**.
- **Árabe, los signos:** «بيع −1» y «شراء +1» de la escala del árbol, «من −1 إلى +1» de sus textos, «VI+», «DI−»,
  «%K» y la fórmula de la TEMA llevan una marca de izquierda a derecha (LRM, o aislada con LRI…PDI): sin ella el
  algoritmo bidi pintaba «1−», «+VI», «K%» y partía la fórmula.
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
  factor de beneficio: 1–200). Las del diseño (§12) eran las del catálogo de 2024, y las 94 estrategias
  caían en un rincón de cada barra. Por debajo de 10, el factor de beneficio va con hasta dos decimales y el
  beneficio medio (%) con dos; la actividad por vela, con hasta tres. Hasta la primera respuesta del
  servidor, las cajas de mínimo y máximo salen vacías (no con las cifras del diseño), y lo que se escribe
  antes conserva su valor.
- **«Actividad por vela»** es la columna `Trade Activity Per Candle` del generador (operaciones por vela
  del backtest: 0,002–0,238); la maqueta, que no la tenía, ponía operaciones por mes de entrenamiento.
- **Las barras «Backtest» y «Desde su publicación»** de la ficha miden contra el mejor backtest del
  catálogo (`npp_max` de `/api/config`), no contra el 100 % de la maqueta, dibujado para sus backtests, la
  mayoría del 71–86 % (de 0,49 a 85,80 %): los de 0,03–0,44 % de 2026-10 dejaban la barra vacía.
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
- **Si el código del árbol no llega** (`tree.js`, sin red), pulsar otra vez «Cómo decide» o volver a su pestaña
  lo pide de nuevo, en otra dirección (`tree.js?retry=N`: Chromium recuerda el fallo), nunca solo; cuando
  llega, el aviso de red que dejó el fallo se va (`app.loadTree`, `showHow`). El diseño no tiene ese estado.
- **Las favoritas de Mis estrategias** esperan a API #15: hasta entonces no dice «Pulsa el corazón de una
  estrategia para seguirla.» (`favEmpty`, `vals_pages.js`), como «Packs» espera a los lotes. Un ♥ o una alerta
  cambian al momento y, si el servidor no lo guarda (un 401 tras salir en otra pestaña), vuelven a como los
  tiene la cuenta, la favorita a su sitio, con el aviso (`app.setFav`). El diseño no habla con un servidor.
- **«Desde su publicación», sólo con cifras** (decisión del dueño E11, 2026-10-26): mientras ninguna estrategia
  tiene cifra (`since_release` de API #1 a 0: `catalogue/since_release.csv` no está o está vacío), no sale en las
  fichas de Lite (`lite.js`, `liveOn`), en Comparar (su fila, `vals_pages.js`) ni en la ficha, cuya caja es
  entonces la del backtest: «Backtest» de título y «Beneficio neto %» en su barra, sin la segunda barra ni «Aún
  sin medir…» (`detail.js`: `liveHead`, `btLabel`). Con la primera cifra vuelve sola, como en el diseño: «—» y
  «Aún sin medir…» en las que no la tienen. La Tabla de Pro no la tiene. El diseño la enseña siempre, con sus
  cifras de ejemplo.
- **El aviso de sobreajuste de Lite y de Pro** dice, cuando se sabe, entre cuántas estrategias probadas se
  eligieron las del catálogo y de dónde salen sus cifras: «… Estas 94 estrategias se eligieron entre 1531
  probadas; sus cifras salen de datos que los modelos nunca vieron.» (decisión E1; `riskTried`, con `tried` de
  API #1, que sale de `catalogue/release.json`; `lite.js`, `pro.js`). Sin `tried`, el aviso del diseño. El de la
  ficha se queda como el del diseño.
- **La explicación de la nota** (su `title`, en las fichas de Lite, la Tabla de Pro y la ficha) dice desde cuántas
  operaciones es cada letra: «Muestra: 37 operaciones cerradas. Menos operaciones, más riesgo de sobreajuste. A
  desde 100 operaciones, B desde 50, C desde 25; D, menos de 25.» (decisión E10; `gradeCuts`, con los
  `grade_cutoffs` de API #1; `vals.js`). El diseño no los dice.

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
| 1 | Cortes de la nota (A ≥ 300, B ≥ 100, C ≥ 30) | Decidido (2026-10-26): la nota sigue diciendo cuánta prueba respalda el backtest, hecho con datos que el modelo no vio (cerca de año y medio): A desde 100 operaciones cerradas, B desde 50, C desde 25; D, menos. Se cambian con `GRADE_CUTOFFS` (`100,50,25`) y su explicación los dice. Con las 94 del catálogo (5–63 operaciones): 8 B, 22 C y 64 D |
| 2 | ¿Los tramos se suman al precio de un lote? | Sí: tramo y código (con el tope `MAX_DISCOUNT`) también sobre lotes y pack; un código de precio fijo, no |
| 3 | Un lote nuevo sustituye a otro que comparte estrategia | Sí, en la página; el servidor rechaza (nunca elige) un carrito con una estrategia dos veces |
| 4 | ¿Qué hace «Conectar TradingView»? | Abre tradingview.com en otra pestaña y lo recuerda; no hay API a la que conectarse |
| 5 | `tour1Pro` dice «y 15 más» y son 16 | Decidido (2026-10-25): «Acota el catálogo con los filtros del panel: beneficio neto, precio, símbolo, temporalidad, indicadores y 16 más.», sin cifra (no se queda vieja), en los 8 idiomas |
| 6 | La nota se explica al pasar el ratón | Igual (`title`); en el móvil no se ve |
| 7 | ¿Comparar y Favorita en Filas y Fichas de Pro? | Igual que el diseño: sólo en la Tabla |
| 8 | La ficha no tiene resumen del carrito | Igual; en el móvil la barra de abajo cuenta lo que hay |
| 9 | Pro enseña «Pagar» con el carrito vacío | Igual; no hace nada |
| 10 | Los tramos en USD y los totales en moneda local | Igual; se paga en USD («Pagas X US$ con PayPal») |
| 11 | Revisión nativa de zh, ar e hi | Revisados por la tienda (2026-10-26, E12c: gramática, trato, términos de la tienda, números, plurales y signos en árabe, puntuación de cada escritura) los textos de 2026-10: `tour1Pro`, los plurales de `shown` y `selectedN`, `ownedYours`, los cuatro de una gratis en la ficha, `proofProvenTitle` / `proofProvenText`, `removeName`, `riskTried`, `gradeCuts`, `gradeTip`, `tradesWord`, y en el árbol los 22 `pat`, los 225 `feat` y `featDesc` y sus textos nuevos; y la explicación de los 38 indicadores. La revisión de un nativo sigue pendiente |

Y la de la pantalla 8: **¿«Obtener la actualización» se paga?** Hoy no hay versiones más allá de la v1;
renovar un enlace da la versión de hoy. Si se paga, hace falta un script por versión y un pedido.

**Y las del dueño, abiertas** (salieron del recorrido de 2026-10-25 y 2026-10-26; la tienda no las decide):

- **Cómo se listan las estrategias.** La tienda enseña el backtest del periodo de prueba de las estrategias
  que eligió el generador. Probadas con datos que no vieron, pierden de media después de costes (Readme del
  generador, sección 9). Decidido en lo que toca a la tienda (2026-10-26, E1): el aviso de sobreajuste de Lite y
  de Pro dice entre cuántas probadas se eligieron (`tried` de `catalogue/release.json`: 1.531 las de la ejecución
  2d00ddc; el import lo toma del manifiesto cuando el generador lo escriba) y que sus cifras son de datos que los
  modelos no vieron. Cómo elegirlas es del generador.
- **Las 55 estrategias horarias** (49 de acciones): sus cifras salen del backtest en Python, que los datos
  gratis de TradingView no reproducen. Decidido (2026-10-26, E2): fuera del catálogo las 49 de acciones, con sus
  gráficos, sus vistas previas y los logos que ya no usa ninguna fila (GOOG y QCOM); se quedan las 6 de cripto: 94
  estrategias (84 de pago y 10 gratis) de 36 tickers. `catalogue/release.json` dice cuáles y por qué, y el import
  las deja fuera mientras el generador las liste (`LIST_INTRADAY_STOCKS`, apagado). Los lotes, por la misma regla:
  «Top 5 por beneficio», SNOW 1BOL, ADBE 2BV0, META 2BB0, AMD 1M00 y CRWD 1SQU (365 US$ sueltas, por 249 US$);
  «Pareja Amazon», AMZN 1S00 y 2MV0 de 1Day (138 US$, por 119 US$).
- **Las condiciones de TradingView** (§23: desde el 2026-11-01, los scripts solo se venden en su Marketplace)
  y las normas de la UE y de España para vender estrategias.
- **`fx-update` y `send-alerts`** siguen con `cron`, en un solo servidor; pasarlos a `"schedule"` del
  núcleo está pendiente.
- **Una estrategia que ya es de la cuenta se vuelve a vender.** La ficha y el árbol dicen «Ya es tuya», pero
  el presupuesto y el pedido no lo miran: desde las tarjetas de Lite o de Pro se cobra otra vez. Negarlo
  (p. ej. `errAlreadyOwned`) es una regla de negocio.
- **El árbol del visitante** (decidido el 2026-10-26): se colorea con los niveles de cada script que publica la
  tienda, `catalogue/levels.json` (lo escriben `flask --app app edgefolio import … --scripts` y, para el catálogo
  ya publicado, `flask --app app edgefolio levels` desde `STRATEGIES_DIR`; API #3 los manda como `buy_at` y
  `close_at`). Sin ellos, ningún resultado dice Comprar, Vender ni Esperar: enseña su puntuación y la pestaña
  dice por qué. Nunca 0,55 y −0,9. Sólo vale el script que lleva el nombre de su estrategia: los de esta
  máquina son copias de prueba, así que el catálogo de hoy no tiene niveles hasta que se ejecute el comando
  donde están los de verdad (y se suba el `levels.json` que deja).
- **Los cortes de la nota** (pregunta 1): decidido (2026-10-26, E10): A desde 100, B desde 50, C desde 25; D, menos.
- **«Desde su publicación»:** decidido (2026-10-26, E11): no sale mientras ninguna estrategia tiene cifra (ver «a
  propósito») y vuelve sola con la primera. El import copia el `since_release.csv` (`id`, `pct`, `as_of`) de un
  paquete cuando el generador lo escriba, y con `--prune` borra uno de antes si el paquete no trae otro.
- **Un clic en el velo oscuro** de los diálogos de la tienda (el recorrido de bienvenida, el tutorial de
  instalación, el selector del pack, Comparar y el diálogo de la gratis), ¿debería cerrarlos? Hoy no los
  cierra: lo hacen Esc y la × (o «Hecho» en el selector del pack, que no tiene ×).
- **Contenido y traducciones:** la revisión nativa de zh, ar e hi (pregunta 11); si el
  precio sigue encima de «Ya es tuya» en la ficha; y si una actualización se paga (la pregunta de arriba).
  Decidido el 2026-10-26: la explicación de cada indicador, en los 8 idiomas (`catalogue/indicators.csv`, E12a); los
  225 valores del árbol, con su nombre y su descripción en los 8; y «Tree depth» en inglés (E12d; la columna del
  catálogo sigue siendo «Tree Deep»). Revisado el mismo día: cada explicación dice lo que calcula el código del
  generador (la de 1TMA, sus cuatro medias suavizadas, la de 2 velas frente a la de 200 y sus dos patrones de velas)
  y ninguna promete nada. El `indicator_tech_explanation.csv` del generador sigue con los textos de antes, «TMA Overlay
  (Triangular Moving Average)» y la `Key Combination` de 2MM0 y 2BB0 equivocada; de él saca `S_04` el «Full Indicator
  Name» de `catalogue.csv`, así que una estrategia 1TMA publicada saldría con ese nombre.

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
5. **Hecho en el núcleo:** el alto de la barra fija es `--zt-bar-h` / `--zt-sticky-top` (0.24, con su
   `scroll-padding-top`) y la barra de abajo de una herramienta lleva `data-zt-bottom` (0.28), que la tienda
   ya usa (`views/phonebar.js`; su `body.app-shell{padding-bottom:64px}` se quitó con el núcleo 0.30). Queda
   en la tienda: `app.scrollUnderHeader` aún lee `header.app-topbar` en vez de `--zt-sticky-top`.
6. **La barra en dos filas con la sesión abierta.** Con una cuenta, el chip de la cuenta enseña el correo
   entero y, con los chips de la herramienta, la barra sólo cabe en 1320 px con un correo corto: hasta unos
   136 px en español (unos 23 caracteres; «cuenta@example.com» cabe) y unos 145 px en inglés. Con uno más
   largo baja a dos filas (88 px en vez de 59) a 1366, 1440 y 1600, y «Lite | Pro» pasa a la segunda: con él,
   Mis estrategias, que pide cuenta, no se ve como el diseño en un escritorio. Bastaría recortar el correo cuando
   la barra lleva chips (`.app-topbar-actions-tools .app-account-email{max-width:140px;
   overflow:hidden;text-overflow:ellipsis;white-space:nowrap}`) o enseñar sólo el avatar, con el correo
   en el menú.
7. **Hecho en el núcleo (0.28):** `zlecitool_core.testing.mobile` (`serve`, `browser`, `open_page`,
   `sign_in`) da la app servida y una página de Playwright sobre su Chromium, y las pruebas de la tienda en
   un navegador ya lo usan (`test_keyboard.py`, `test_lists_cart.py`, `test_mine_page.py`,
   `test_phone_bar.py`…). Sólo `tools/screenshots.py`, el recorrido de las capturas, sigue sobre un servidor
   en marcha.
8. **Importes con el formato del idioma en el servidor**, para los correos (p. ej.
   `zlecitool_core.i18n.format_money(valor, moneda, idioma)`): el recibo de la tienda dice «47.45 USD» en
   español, donde la página dice «47,45 US$». Con él, `orders.money()` lo usaría con el idioma de
   `email_receipt()`; la tienda no escribe su propio formateador.
9. **«Entrar» y el `from=` de Contacto, al pulsarlos.** La carcasa los escribe en el servidor con la
   dirección de llegada (`back_after_login`, `zt_contact_url`); en una herramienta con rutas en el
   navegador (`pushState`), después de ir a otra ficha sin recargar, «Entrar» vuelve a la primera (o a
   `/`), y Contacto dice que se venía de ella. Bastaría que `shell.js` les pusiera `location.pathname +
   location.search` al pulsarlos.

## Pruebas

- `pytest`, hoy (2026-10-26): 287 pruebas en verde y 1 saltada (`test_formats.py`: los scripts de pago no
  están en la máquina), con Chromium; sin él, las pruebas en un navegador se saltan y no prueban nada. Las
  de los arreglos del recorrido de 2026-10-25: `tests/test_keyboard.py` (los diálogos y el teclado),
  `tests/test_lists_cart.py` (Lite, el carrito, el recorrido y Gracias), `tests/test_scales.py` (las escalas
  de Pro y las barras de la ficha), `tests/test_strategy_page.py`, `tests/test_tree.py`,
  `tests/test_mine_page.py` y lo nuevo de `tests/test_phone_bar.py`, `test_pricing.py`, `test_orders.py` y
  `test_search.py`. Las de las decisiones del dueño del 2026-10-26 sobre el catálogo (E1, E2, E10, E11):
  `tests/test_listing_page.py` (el aviso de sobreajuste, la explicación de la nota y «Desde su publicación», sin
  cifras y con una) y lo nuevo de `test_publish.py`, `test_release.py`, `test_search.py`, `test_bundles.py` y
  `test_mine.py` (lo comprado de una estrategia que salió del catálogo: no se enseña ni se entrega, sin romper nada).
- Con esta exportación eran 228 pruebas en verde (antes 210). Nuevas: `tests/test_page_code.py` (sin marcas de conflicto;
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
- La «insignia Nuevo» no se veía en el catálogo de entonces (nada publicado en los últimos 30 días): se probó
  con datos de prueba. Con el de 2026-10 la llevan las 94, hasta el 12 nov 2026.
