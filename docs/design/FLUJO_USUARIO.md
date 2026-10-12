# Edgefolio · Flujo de usuario (exportación 2026-10-06)

> **En esta tienda.** Es el flujo del diseño tal como llegó (exportación del 2026-10-06), y la tienda lo
> sigue con las diferencias que apunta `docs/handoff/2026-10-06/CAMBIOS.md`: las direcciones de verdad
> (`/s/<id>`, `/thanks`, `/mine`), la barra, el idioma, la cuenta y el pie del núcleo, PayPal y los enlaces
> contados de verdad, «¿Compraste sin cuenta?», todas las vistas previas cortadas y el recorrido de
> bienvenida propio, una vez por navegador. La próxima exportación se compara con este fichero.

- **Herramienta:** `edgefolio`. **Repositorio:** `Leci37/tuisku_Web_selling`, rama `_ztool_dev`, sobre el núcleo `zlecitool-core` 0.23.0.
- **Archivos:** `prototype/Storefront v7.dc.html` (pantallas 1–3 y 5–9) y `prototype/Strategy Tree.dc.html` (pantalla 4, incrustada en la ficha).

**Punto de partida.** La tienda de `_ztool_dev` sigue hoy el diseño v7 exportado el 6 oct 2026, más la fila de confianza bajo «Pagar». La marca de cada pantalla compara el diseño con eso:
- **same:** igual que en la tienda;
- **changed: …:** cambia lo que se indica;
- **new:** pantalla nueva;
- **removed:** se quita.

Lo que la tienda tiene y el diseño no muestra se mantiene; no es una baja. Por ejemplo, «¿Compraste sin cuenta?» en Mis estrategias.

**Etiquetas:**
- **[Simulado]:** el prototipo lo imita; la tienda lo hace en el servidor.
- **[Regla]:** regla que hay que mantener.
- **📱:** diferencia en el móvil (390 px) frente al escritorio (1366 px).

Los textos citados son los de español (`texts.json`).

---

## Común a todas las pantallas

**Barra superior.** La pone el núcleo, con la palabra «Edgefolio». Las fichas de la tienda van en sus dos huecos:

| Elemento | Clic → resultado |
|---|---|
| **Lite \| Pro** | Cambia de modo, lo guarda en `tuisku-sf-mode` y va a la tienda desde cualquier pantalla |
| **Mis estrategias** | Abre la pantalla 8 |
| **? Ver tutorial** | Abre el tutorial de bienvenida en el paso 1 (pantalla 1) |
| **TradingView** («● Conectado» / «Conectar TradingView») | Alterna el estado. [Simulado] Solo cambia la etiqueta. |
| **Moneda** (EUR, INR, CNY, SAR o USD) | Alterna entre la moneda local y USD. En inglés no cambia nada. No se guarda. |
| **Idioma** | Abre el menú de los 8 idiomas. Al elegir uno, la interfaz cambia al momento y se guarda; el árabe va de derecha a izquierda. Un clic fuera o **Esc** cierra el menú. |

- **Página:** 1320 px de ancho, con bandas a todo el ancho bajo la barra (la cinta de cotizaciones, la cabecera de Lite y la franja del carrito de Pro).
- **Pie:** el del núcleo (Privacidad · Cookies · Condiciones de uso · Aviso legal · Contacto).
- **Sin anuncios y sin aviso de cookies.**
- **Precios:**
  - PayPal, en USD, sin créditos.
  - El servidor calcula los precios, y ningún código de descuento llega a la página.
  - Cada estrategia cuesta 79 US$; en moneda local se muestra aproximado («≈ 73 €»).
  - [Simulado] El código `DEMO20` viene ya escrito en el prototipo.
- **Direcciones:**

  | Pantalla | Dirección |
  |---|---|
  | Tienda | `/` |
  | Ficha | `/s/<id>` |
  | Cómo decide | `/s/<id>/tree` |
  | Gracias | `/thanks` |
  | Mis estrategias | `/mine` |

  - En el prototipo, la ficha usa `#s=<id>` y `#s=<id>/tree`; Gracias y Mis estrategias no tienen dirección propia.
  - Atrás, Adelante y recargar mantienen la ficha y su pestaña. Un id que no existe lleva a la tienda.
- **Al llegar:**
  - Se leen el modo, el idioma y la vista de Pro guardados.
  - Si la dirección es una ficha, se abre esa ficha.
  - Si no, se abre la tienda, y en la primera visita también el tutorial de bienvenida.
- **Estados al llegar:**
  - **Cargando:** mientras llegan los textos, las etiquetas salen vacías un instante (no hay pantalla de carga diseñada).
  - **Error:** no diseñado.
  - **Hecho:** la pantalla de destino.

---

## 1 · Lite (por defecto)

**changed:**
- etiqueta «Novedades» en las tarjetas de estrategias publicadas en los últimos 30 días;
- un pack nuevo saca del carrito los packs que comparten alguna estrategia;
- la píldora «Comparar» va encima del carrito flotante;
- Esc cierra el selector del pack y la comparación.

**Pantalla:** `/`, en `Storefront v7.dc.html`, bloque Lite.

### Primera visita: tutorial de bienvenida (núcleo, 3 pasos)

| Paso | Título | Texto |
|---|---|---|
| 1 de 3 | Elige un mercado | En Lite: «Busca una empresa o una cripto, o usa las pestañas…». En Pro: «Acota las 2.834 estrategias…». |
| 2 de 3 | Lee la curva | `tour2Text` |
| 3 de 3 | Compra y cárgala en TradingView | `tour3Text` |

- **Continuar**, **Atrás** y **Empezar** (en el paso 3).
- **×** o **Esc** lo cierran.
- **→ / ←** cambian de paso (al revés en árabe).
- Un clic en la imagen avanza; deslizar más de 40 px cambia de paso.
- Al cerrarlo se guarda `edgefolio-tour-v1` y no vuelve a salir solo.

### Qué ve y qué hace

| Zona | Qué pasa |
|---|---|
| **Cinta de cotizaciones** | Las estrategias de pago por beneficio neto %, por ejemplo «AAPL · 1C00 +85,80 %». Se desliza de lado y no se puede pulsar. |
| **Buscador** «Busca una empresa, cripto o indicador» | Filtra al escribir, por nombre, ticker, indicador o clave. Es el mismo buscador que Pro. |
| **Pestañas** | **Destacadas** (por beneficio neto %), **Tasa de acierto** (por acierto), **Acciones**, **Cripto**, **Gratis** (precio 0) y **Novedades · 3** (últimos 30 días). Se combinan con la búsqueda. |
| **Aviso «Riesgo de sobreajuste»** | Siempre visible; no se cierra |

**Packs:**
- **Top 5 por beneficio:** 249 US$ (antes 395 US$; «Ahorra un 37 %»).
- **Inicio en cripto:** 119 US$ (antes 158 US$; «Ahorra un 25 %»).
- **Pareja Amazon:** 119 US$ (antes 158 US$).
- **Añadir pack** lo mete en el carrito y el botón pasa a «✓ En el carrito»:
  - sus estrategias que estaban sueltas salen del carrito;
  - también salen los packs que comparten alguna estrategia con él.
- Otro clic en «✓ En el carrito» quita el pack.

**Arma tu pack** (5 por 249 US$):
- 5 huecos y el texto «Elige N más · 5 por 249 US$». El botón **Añadir pack** sale gris hasta tener 5.
- Un clic en un hueco, o en el botón sin estar completo, abre el **selector**:
  - las 7 estrategias de pago con casilla, y el contador «N / 5»;
  - una sexta marca se ignora;
  - cualquier cambio saca el pack del carrito;
  - **Hecho** o **Esc** lo cierran.
- Con 5, el botón mete el pack en el carrito («En el carrito»), con las mismas reglas que los packs.

**Tarjetas** (columnas de al menos 270 px):

| Elemento | Clic → resultado |
|---|---|
| Ticker, con la etiqueta «Novedades» si es nueva, o la curva con «⚠ Backtest» | Abre la ficha (pantalla 3) |
| «+85,80 % ?», «Tasa de acierto …?», «… operaciones ?» | Burbuja con la explicación; solo hay una abierta a la vez |
| **Nota** A–D | Al pasar el ratón: «Muestra: N operaciones cerradas…». [Regla] A ≥ 300, B ≥ 100, C ≥ 30 operaciones. |
| «Desde su publicación +9,4 %» | Verde, o rojo si es negativo. [Simulado] |
| ♡ | Favorita, sí o no (pantalla 8) |
| Comparar | Entra o sale de la comparación, hasta 3 (pantalla 2) |
| **Ficha técnica** / **Cómo decide** | Pantallas 3 y 4 |
| **Comprar** | Entra en el carrito → «✓ En el carrito». Otro clic la quita; si está dentro de un pack, quita el pack. |
| **Descargar** (gratis) | Abre la pantalla 6 |

Debajo: «Mostrando N de 2.834» y **Ver más** [Simulado].

**Carrito flotante** (pantalla 5):
- Se queda pegado abajo mientras haya algo en el carrito.
- Si hay estrategias en comparación, la píldora **Comparar · N** va justo encima.

**Estados:**
- **Vacío:** «Ninguna estrategia coincide».
- **Cargando / error:** no diseñados.
- **Hecho:** tarjetas y contador.

---

## 2 · Pro

**changed:**
- en la vista Tarjetas, el nombre del indicador abre su página en TradingView;
- Esc cierra los desplegables de filtros;
- la etiqueta «Tabla» usa la clave `viewTableTab` (mismo texto).

**Pantalla:** `/` en modo Pro, en `Storefront v7.dc.html`, bloque Pro.

- **Franja del carrito y escalera de descuento:** ver la pantalla 5.
- **Panel de filtros:** a la izquierda; 📱 encima de la lista.
  - El contador «N · estrategias mostradas» y **Restablecer filtros**.
  - **Solo GRATIS.**
  - **16 deslizadores de rango**, cada uno con su histograma:
    - Beneficio neto ($) y Precio ($) siempre abiertos;
    - los otros 14, plegados: Beneficio neto (%), Operaciones cerradas, Tasa de acierto (%), Factor de beneficio, Entrenamiento (meses), Pérdida máxima ($), Pérdida máxima (%), Beneficio medio ($), Beneficio medio (%), Velas medias por operación, Actividad por vela, Número de velas, Precisión f1 (%), Profundidad del árbol;
    - las asas se arrastran, y un clic en la pista mueve la más cercana;
    - un asa en el extremo significa «sin límite»;
    - las casillas mín. y máx. se aplican con Intro o al salir;
    - al pasar el ratón por una barra del histograma se ve «N estrategias».
  - **5 desplegables** (Símbolo, Temporalidad, Indicadores, Mercado, Fecha de publicación):
    - buscador, **Seleccionar todo** / **Quitar todo**, y casillas con su recuento;
    - si no hay nada marcado, la lista queda vacía;
    - un clic fuera o **Esc** cierran el desplegable.
  - [Regla] Los filtros se combinan con Y; dentro de un desplegable, las opciones se combinan con O.
- **Encima de la lista:**
  - **Ordenar** (Beneficio neto, Tasa de acierto, Precio, Operaciones cerradas), siempre de mayor a menor.
  - El buscador.
  - **Filas / Tarjetas / Tabla**, que se guarda.
  - Una **etiqueta** por filtro activo con su ×, y **Borrar filtros**.
- **Filas:**
  - el ticker enlaza con TradingView;
  - los botones Ficha técnica y Cómo decide;
  - la curva y 4 cifras;
  - Añadir al carrito o Descargar.
- **Tarjetas:**
  - las dos curvas y 6 cifras;
  - «CLAVE · indicador» abre la página del indicador en TradingView.
- **Tabla:**
  - clic en una cabecera numérica para ordenar;
  - clic en una fila para desplegarla (una cada vez);
  - Comparar y carrito en la fila;
  - 📱 se desplaza de lado.
  - «Filas por página» y los botones de página son [Simulado].
- **Comparar** (también desde las tarjetas Lite):
  - la píldora **Comparar · N** abre «Comparar estrategias»;
  - una columna por estrategia, con ×;
  - en cada fila, el mejor valor en verde (en el precio, el más bajo);
  - quitar la última, × o **Esc** cierran.

**Estados:**
- **Vacío:** «Ninguna estrategia coincide».
- **Cargando / error:** no diseñados (en la tienda, `GET /api/strategies`).
- **Hecho:** la lista.

---

## 3 · Ficha de la estrategia (/s/<id>)

**changed:**
- «Actualización disponible» solo sale a quien tiene la v1;
- la dirección sigue a la ficha, y Atrás, Adelante y recargar funcionan.

**Pantalla:** `Storefront v7.dc.html`, bloque de la ficha.

1. **Cabecera:**
   - «Volver a la tienda»;
   - el gráfico de velas difuminado y «Nombre · TICKER»;
   - **Abrir en TradingView** y las etiquetas «1Day», el mercado y la clave;
   - el precio, con **Añadir al carrito** o **Descargar** (si es gratis);
   - «Abrir en otra pestaña» y ♡ Favoritas.
2. **Pestañas Ficha técnica | Cómo decide** (pantalla 4).
3. La tarjeta «Mira cómo decide esta estrategia», que lleva a la pantalla 4.
4. «En TradingView, pon el gráfico en la temporalidad 1Day.»
5. El aviso de sobreajuste.
6. **Backtest frente a resultado real**, con la nota A–D y dos barras. Debajo, «Cifras de ejemplo…» [Simulado].
7. **Versiones:**
   - v2, «Reconstrucción…», con «Actualización disponible» solo para quien tiene la v1;
   - v1 · 27 sep 2024.
8. Los **gráficos** de la estrategia y de velas.
9. Los **14 resultados del backtest**. Un dato que falta sale como «—».
10. **Sobre el indicador**, con «Ver el indicador en TradingView».
11. **Vista previa del Pine Script**, cortada: líneas 5–16 legibles y 17–21 difuminadas, con «El resto del script se entrega tras la compra». [Regla] El script completo nunca llega al navegador.
12. **Formatos:** Pine Script (.pine), Markdown para IA (.md), Python (.py, BETA) y JavaScript (.js, BETA).

**Diferencia que se mantiene:** en la tienda, las vistas previas de pago van cortadas y las gratuitas enteras. El diseño muestra cortada también la gratuita (NVDA 1S00). Se mantiene lo de la tienda.

**Estados:**
- **Cargando:** el editor del Pine Script sale vacío hasta que llega el archivo.
- **Error:** el editor se queda vacío y sin mensaje (no diseñado).
- **Hecho:** la ficha completa.

📱 Las tarjetas van una debajo de otra y el editor se desplaza de lado.

---

## 4 · Cómo decide (/s/<id>/tree)

**changed:**
- «Comprar para desbloquear» solo añade al carrito, y en una estrategia gratis abre la pantalla 6;
- la dirección guarda `/tree`;
- el árbol usa las fuentes de la página (sin cambio visible).

**Pantalla:** `Strategy Tree.dc.html`, dentro de la ficha.

| Control | Qué pasa |
|---|---|
| **Árbol \| Bloques** | Dos formas de dibujar el mismo árbol |
| **Visitante \| Propietario** | [Simulado] Interruptor de demostración; en la tienda depende de la compra |
| Clic en una pregunta o en su **Sí / No** | El camino va hasta ella |
| Resultado (Comprar / Vender / Esperar) | Ratón encima → la regla en una frase. Clic → pone los valores que llegan a ese resultado. |
| Arrastrar | Mueve el árbol |
| **Valores de los indicadores** | Deslizadores coloreados (Compraría, Vendería, Esperaría), y la nota «Umbrales ya optimizados» |
| **Ejemplo de compra / de venta** | Pone los valores del resultado más fuerte |
| **Ver todas las reglas en frases (N)** | Lista las reglas; un clic en una salta a ella |
| Ramas «Parte de pago» + **Comprar para desbloquear** | Añade la estrategia al carrito → «Añadida al carrito». En una gratis, abre la pantalla 6. |
| **Volver a la ficha técnica** | Vuelve a la pantalla 3 |

**Estados:**
- **Cargando:** «Cargando el árbol…».
- **Error:** «No se pudo cargar el árbol: …».
- **Hecho:** el árbol.

📱 Los deslizadores van encima del árbol.

---

## 5 · Carrito y pago

**changed:**
- «Vaciar carrito» quita también los packs;
- el subtotal tachado solo sale si hay descuento;
- «Pagas X US$ con PayPal» también en Pro;
- en Lite, el código muestra si es válido;
- cada estrategia se cobra una sola vez.

**Pantalla:** el carrito flotante de Lite y la franja de Pro, en `Storefront v7.dc.html`.

**Lite, carrito flotante:**
- «Carrito · N» y la etiqueta «−35 %».
- **¿Tienes un código?** abre la casilla «Código» con **Aplicar**. Al lado sale «Código de descuento aplicado» o «Código no válido: sin descuento».
- El subtotal tachado (solo si hay descuento), el total y «Pagas 154,05 US$ con PayPal».
- **Pagar**.

**Pro, franja del carrito:**
- «Carrito · N» y **Vaciar carrito**.
- La escalera: «15 % de descuento por volumen + 20 % con el código» y «Añade 53,00 US$ más para llegar al 20 %». Hay 5 marcas: 160, 290, 500, 1.000 y 2.500 US$, que dan un 15, 20, 25, 40 y 70 %.
- La casilla del código, los totales y **Pagar**.

**Fila de confianza** (bajo «Pagar», en Lite y en Pro): «PayPal: nunca vemos tu tarjeta» · «Enlaces: 7 días, 10 descargas» · «Factura por correo» · sales@tuisku.eu.

**[Regla]:**
- **Tramos:** cada tramo cuenta cuando el subtotal supera su importe (`api/settings.py`). El código suma su %, con un tope total del 70 %.
- **Precios:** el servidor calcula todos los precios, y los códigos se comprueban en el servidor.
- **Packs:** sacan las estrategias sueltas y los otros packs que comparten alguna estrategia.

**Ejemplo:** el carrito de prueba (3 × 79 US$) suma 237 US$; con −35 % queda en **154,05 US$**, o «≈ 142 €».

**Pagar:**
- Con el carrito vacío, no pasa nada.
- Si no, PayPal y luego la pantalla 7. [Simulado] El prototipo salta PayPal.

**Estados:**
- **Vacío:** Lite no muestra el carrito; Pro muestra «Carrito · 0».
- **Error:** código no válido.
- **Cargando / error de PayPal:** no diseñados.
- **Hecho:** pantalla 7.

📱 El carrito flotante va 76 px por encima del borde, sobre la barra inferior.

---

## 6 · Estrategia gratis por correo (diálogo)

**changed:**
- un correo vacío o no válido muestra su error;
- Intro envía y Esc cierra;
- pedir otra vez la misma estrategia renueva su enlace.

**Pantalla:** diálogo de `Storefront v7.dc.html`. Se abre con **Descargar** en una estrategia gratis (pantallas 1–4).

1. Muestra la estrategia, «Consíguela gratis» y «Escribe tu correo y te enviamos el enlace de descarga.».
2. El campo **Correo**: al escribir se borra el error, e **Intro** envía.
3. La casilla ☐ «Avísame también de estrategias nuevas (opcional)», **sin marcar** de entrada. [Regla] RGPD.
4. **Enviarme el enlace:**
   - vacío → «Escribe tu correo electrónico.»;
   - no válido → «Eso no parece un correo electrónico.» (en rojo, con el borde rojo);
   - válido → «Hecho. Mira tu correo: el enlace vale 7 días.» y **Volver a la tienda**.
5. La estrategia aparece en la pantalla 8, o su enlace vuelve a empezar si ya estaba.
6. **×** o **Esc** cierran el diálogo.

**Estados:**
- **Vacío:** el formulario.
- **Error:** el correo.
- **Cargando:** no diseñado.
- **Hecho:** el mensaje verde.

---

## 7 · Gracias (/thanks)

**same**

**Pantalla:** `Storefront v7.dc.html`, bloque Gracias, con el tutorial de instalación en un diálogo.

**Página de gracias:**
- «¡Gracias! El pago se ha completado.», con el total pagado en USD y «Pagado con PayPal · Pedido EF-xxxxx».
- «Cada enlace vale 7 días y hasta 10 descargas…» y **Descargar todo** [Simulado].
- Una fila por estrategia, con **.pine**, **.zip**, **Ficha técnica ↗** y **Cómo decide ↗** (en otra pestaña).
- «Añádela a TradingView», con **Ver el tutorial** y 5 casillas de pasos (📱 una debajo de otra).
- **Ir a Mis estrategias** y **Volver a la tienda**.

**Tutorial de instalación** (5 pasos):
1. Descarga y copia el script.
2. Entra en TradingView.
3. Abre el gráfico correcto, con el enlace «Abrir AMZN en TradingView».
4. Pégalo en el Pine Editor.
5. Añádela al gráfico.

- **Continuar**, **Atrás** y **Listo**.
- Los puntos se pueden pulsar.
- **→ / ←**, **Esc** o **×**.
- Un clic en la imagen avanza, y se puede deslizar.
- Sale solo la primera vez (`edgefolio-install-v1`).

**Estados:**
- **Hecho.**
- Sin pedido, el prototipo muestra uno de ejemplo [Simulado].

---

## 8 · Mis estrategias (/mine)

**changed:**
- «Pedir un enlace nuevo» mantiene la fecha de compra, el pedido y la versión;
- cada fila lleva también .zip, «Ficha técnica ↗» y «Cómo decide ↗».

**Pantalla:** `Storefront v7.dc.html`, bloque Mis estrategias.

**Se mantiene de la tienda:** el bloque **«¿Compraste sin cuenta?»**, que pide demostrar un correo. No está en el diseño, pero no es una baja.

**Una fila por compra o descarga:**
- «Comprada el …» o «Descarga gratuita el …», y el pedido.
- El estado: «Enlace válido N días más» o «El enlace caducó». [Regla] 7 días y 10 descargas desde el último enlace.
- **Obtener la actualización · v2:** solo en compras anteriores a la v2. [Simulado]
- **.pine** y **.zip**, mientras el enlace es válido.
- **Pedir un enlace nuevo**, cuando caducó.
- **Ficha técnica ↗** y **Cómo decide ↗**.

**Favoritas:**
- Cada una abre su ficha con un clic, tiene tres alertas (**Versión nueva**, **Bajada de precio**, **En un pack**) y el ♥ la quita.
- Sin favoritas: «Pulsa el corazón de una estrategia para seguirla.»

**Abajo:** **Añádela a TradingView** (abre el tutorial) y **Volver a la tienda**.

**Estados:**
- **Vacío (sin compras):** no diseñado.
- **Favoritas vacías:** con su mensaje.
- **Cargando / error:** no diseñados.
- **Hecho:** las filas.

---

## 9 · Móvil (390 px) con la barra inferior

**changed:**
- el carrito flotante y la píldora «Comparar» van encima de la barra;
- «Buscar» pone el cursor en el buscador;
- «Carrito» lleva al carrito.

**Pantalla:** `Storefront v7.dc.html`, por debajo de 640 px de ancho.

| Botón de la barra inferior | Qué pasa |
|---|---|
| **Tienda** | Tienda, arriba. En azul si estás en ella. |
| **Buscar** | Tienda, con el cursor en su buscador |
| **Carrito** (con número) | Tienda con el carrito a la vista: en Pro sube a la franja; en Lite el carrito flotante ya está en pantalla |
| **Mías** | Pantalla 8. En azul si estás en ella. |

- Los botones miden al menos 44 px, y quedan 64 px libres bajo el pie.
- El carrito flotante y la píldora «Comparar» van a 76 px del borde.
- La cabecera ocupa dos líneas y las tarjetas van en una columna.
- El panel de Pro va encima de la lista, y la tabla se desplaza de lado.
- Los diálogos ocupan el ancho menos 16 px por lado.
