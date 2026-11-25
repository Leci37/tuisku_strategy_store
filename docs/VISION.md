# Edgefolio · Visión

Qué es la tienda, para quién y con qué principios. Sale, el 2026-11-25, de lo que ya estaba escrito:
el `README.md` de la raíz (la entrada, «Cómo funciona» y «Antes de volver a vender»), `tool.json`
(`description`), `CLAUDE.md` (las reglas), la guía del diseño (`IMPLEMENTATION-v7.md` §1, los dos
modos) y las decisiones del dueño del 2026-10-26 (`handoff/2026-10-06/CAMBIOS.md`, «Las preguntas
abiertas»). No añade nada que no esté allí. Cómo se vende, en `../market/` (`PITCH.md`).

## Qué es

Edgefolio es la tienda de tuisku.ai de **estrategias de TradingView**: scripts de Pine Script v5, cada
uno con su backtest. Se miran en una vista sencilla, **Lite**, o se filtran en **Pro**; se ve **cómo
decide** cada una (su árbol de decisión); se compran con **PayPal** y se descarga el script, que se
pega en TradingView. Diez son gratis y se mandan por correo.

La tienda es la interfaz: enseña, cobra y entrega. Las estrategias, sus cifras, sus gráficos y sus
scripts los fabrica su aplicación gemela, `tuisku_strategy_generator`, y llegan en un paquete
versionado (README, «La aplicación gemela»).

## Para quién

- **Quien quiere una estrategia hecha** y no conoce los indicadores: Lite, con las destacadas, los
  packs, la nota de cada una y un recorrido de bienvenida de tres pasos.
- **Quien ya opera** y busca por sus cifras: Pro, con 21 filtros (cada deslizador con su histograma),
  tres vistas (filas, fichas y tabla) y Comparar hasta tres.
- En los dos casos, quien usa **TradingView** (el script se pega en su editor de Pine) y paga en
  **USD con PayPal**; la página va en 8 idiomas, el árabe de derecha a izquierda, con los precios
  aproximados en la moneda del idioma.

## Principios

- **Nada se promete.** Las cifras son las del backtest en datos que los modelos no vieron, y el aviso
  de sobreajuste de Lite y de Pro dice entre cuántas probadas se eligieron (decidido el 2026-10-26,
  E1). El generador avisa de que, probadas así, pierden de media después de costes: cómo listarlas es
  del dueño (README, «Antes de volver a vender»). La nota (A, B, C, D) dice cuánta prueba respalda el
  backtest, no lo que va a ganar.
- **Los precios, sólo en el servidor**: el navegador manda ids, claves de lotes y el código tecleado;
  ningún código de descuento llega a la página (regla 12).
- **El script entero, sólo por un enlace que dio la tienda**, que caduca y tiene las descargas
  contadas; las vistas previas públicas van cortadas (regla 13).
- **Un correo no es una cuenta**: lo comprado sin cuenta sólo sale en una cuenta que ha demostrado
  ese correo (regla 11).
- **Se compra sin cuenta**; con ella, lo comprado queda en Mis estrategias. Las cuentas, el idioma, la
  barra, el pie y lo legal son del núcleo: una cuenta vale para todas las herramientas de tuisku.
- **Sin publicidad** (`"ads": false`) y sin créditos: la tienda cobra con PayPal (`tool.json` no tiene
  `"prices"`).

## Glosario

| Palabra | Qué es |
|---|---|
| Estrategia | un script de Pine Script v5 para TradingView, con un símbolo (*ticker*), una temporalidad (1Day, 1Hour) y uno o dos indicadores; su id, `SÍMBOLO_temporalidad_indicador_hash` |
| Backtest | sus resultados en el periodo de prueba: beneficio neto, operaciones cerradas, acierto, factor de beneficio, caída máxima… (los 14 de la ficha) |
| Nota | A, B, C o D: cuánta prueba respalda el backtest, por sus operaciones cerradas (`GRADE_CUTOFFS`: 100, 50 y 25) |
| Cómo decide | el árbol de decisión de la estrategia (su bosque), caja a caja; quien la compró lo ve entero |
| Vista previa | el principio público del script, cortado al final de su primer árbol |
| Lote | un paquete de estrategias con su precio (`catalogue/bundles.json`); «Arma tu pack», el que elige quien compra (`PACK_SIZE` por `PACK_PRICE`) |
| Escalón | el descuento por importe del carrito (de 160 $ a 2.500 $, del 15 % al 70 %), con el código sumado y el tope `MAX_DISCOUNT` |
| Gratis | una de las estrategias de precio 0: su enlace va por correo |
| Mis estrategias | lo comprado y lo pedido gratis de una cuenta, con sus enlaces, sus versiones y sus favoritas (`/mine`) |
| Prueba de un correo | el enlace que demuestra que un correo es de la cuenta: así sale en ella lo comprado sin cuenta |
| Caducidad | la «Expiry date» de la cabecera de cada script: hasta entonces, la versión nueva es gratis para quien la tiene |
| Lite, Pro | los dos modos de la tienda (arriba, «Para quién») |
