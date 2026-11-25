# Edgefolio · Decisiones del dueño

Lo que ha decidido el dueño de la tienda, con su fecha y dónde se cuenta entero. Hasta el 2026-11-25 estas
decisiones estaban repartidas: las del recorrido de octubre, en `handoff/2026-10-06/CAMBIOS.md` («Las
preguntas abiertas de STATUS.md», que dice cómo se hizo cada una); las de noviembre, en `ESTADO.md` y en
`CLAUDE.md`. Aquí se juntan, sin cambiar ninguna; el detalle sigue donde estaba. Lo que aún no está
decidido, en «Lo que sigue abierto» de ese `CAMBIOS.md` y en «Lo que falta» de `ESTADO.md`.

Lo que vale para toda la familia (los vídeos de las guías, `market/`, el orden de los documentos) es del
núcleo: su `docs/plan/DECISIONES.md`.

## 2026-10-25

- **El primer paso del recorrido de bienvenida en Pro** (`tour1Pro`) dice «…indicadores y 16 más», sin
  la cifra total, para que no se quede vieja; en los 8 idiomas. (`CAMBIOS.md`, pregunta 5.)

## 2026-10-26

Del recorrido de la tienda del 25 y el 26 de octubre (`CAMBIOS.md`, «Y las del dueño»):

- **E1, cómo se listan:** el aviso de sobreajuste de Lite y de Pro dice entre cuántas probadas se eligieron
  (`tried`, de `catalogue/release.json`) y que sus cifras son de datos que los modelos no vieron. Cómo
  elegirlas es del generador.
- **E2, las horarias de acciones, fuera:** las 49 estrategias horarias de acciones salen del catálogo (sus
  cifras no se reproducen con los datos gratis de TradingView); se quedan las 6 de cripto. El catálogo queda
  en 94 (84 de pago y 10 gratis) de 36 tickers, y los lotes, rehechos con la misma regla.
- **E4, las tareas:** `fx_update` y `send_alerts` pasan al reloj del núcleo (`"schedule"` de `tool.json`), sin
  cron; los comandos se quedan para hacerlo a mano.
- **E8, lo que ya es de la cuenta:** suelto no se vuelve a vender (`errAlreadyOwned`); en un lote o en el
  pack, sí. Las fichas dicen «Ya es tuya», **sin el precio**.
- **E9, el árbol del visitante:** se colorea con los niveles de cada script que publica la tienda
  (`catalogue/levels.json`); sin ellos, enseña la puntuación de cada resultado y dice por qué.
- **E10, la nota:** A desde 100 operaciones cerradas, B desde 50, C desde 25; D, menos (`GRADE_CUTOFFS`).
- **E11, «Desde su publicación»:** no sale mientras ninguna estrategia tiene cifra, y vuelve sola con la
  primera.
- **E12, el contenido y las traducciones:** la explicación de cada indicador y los 225 valores del árbol, en
  los 8 idiomas, sin prometer nada; los textos en zh, ar e hi, revisados por la tienda (falta un nativo);
  «Tree depth» en inglés.
- **La versión nueva de una estrategia** es gratis mientras no ha caducado (la «Expiry date» de su
  script); después, no se ofrece. Una gratis se actualiza siempre.
- **El velo oscuro** de los diálogos de la tienda no los cierra al pulsarlo: los cierran Esc y la ×.

## 2026-11-15

- **Un solo Chromium para toda la sesión de pytest**, en todas las herramientas: los minutos de la CI se
  pagan (regla 24 de `CLAUDE.md`).
- **La línea de cada petición:** al subir a la 0.36 del núcleo, `accesslog = "-"` pasa a `accesslog = None`
  en `gunicorn.conf.py`, en el mismo cambio. Hasta entonces no se toca (`ESTADO.md`, «Para el núcleo» 4).

## 2026-11-24

- **Los logs:** ninguna capa por debajo de 30 líneas (cliente, servidor y endpoint), después de pedir un
  25 % más en la segunda vuelta (`ESTADO.md`, «Lo hecho»; regla 25 de `CLAUDE.md`).
- **Los pagos, cuando pasen al núcleo** (`ESTADO.md`, «Lo que falta»): el IVA, incluido en el precio; PayPal
  y Stripe, las dos; un solo recibo, el del núcleo, con el IVA desglosado; y sus pruebas no esperan a nada (la
  pasarela de pruebas del núcleo ya está).
