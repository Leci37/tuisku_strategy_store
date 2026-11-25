# Mensajes · Edgefolio

Los textos de la tienda que venden, con su clave de `i18n/ui.json`: aquí se piensan en español; allí van en los
8 idiomas. Copiados de `i18n/ui.json` el 2026-11-25: si no coinciden, manda `ui.json`. Los del núcleo (la
barra, «Entrar», el pie) no se apuntan. Dónde sale cada uno, en [web/PAGES.md](web/PAGES.md).

| Dónde | Texto | Clave |
|---|---|---|
| Nombre, junto a la palabra Edgefolio | Estrategias de TradingView | `toolName` |
| Ficha para buscadores y la familia | Estrategias de TradingView en Pine Script con su backtest: fíltralas, mira la curva, mira cómo decide cada una y descarga el script. | `description` de `tool.json` |
| Titular de Lite | Estrategias para TradingView | `liteTitle` |
| Subtítulo de Lite | Elige un mercado, mira la curva y descarga el Pine Script. | `liteSub` |
| El buscador | Busca una empresa, cripto o indicador | `searchPh` |
| El aviso de sobreajuste | Riesgo de sobreajuste · Estos resultados son backtests de TradingView sobre precios pasados. Una estrategia ajustada al pasado puede estar sobreajustada y rendir peor con datos nuevos. Los resultados pasados no garantizan rentabilidades futuras. | `riskTitle`, `riskText` |
| Debajo, con su cifra | Estas {n} estrategias se eligieron entre {m} probadas; sus cifras salen de datos que los modelos nunca vieron. | `riskTried` |
| El aviso corto | Backtests sobre precios pasados: los resultados pueden estar sobreajustados y no garantizan rentabilidades futuras. | `riskShort` |
| Los packs | Top 5 por beneficio · Inicio en cripto · Pareja Amazon; «Ahorra un {p}» | `bundleTop`, `bundleCrypto`, `bundleAmzn`, `saveP` |
| Arma tu pack | Arma tu pack · Elige {n} más · {size} por {price} | `packTitle`, `packHint` |
| La nota | Muestra: {n} operaciones cerradas. Menos operaciones, más riesgo de sobreajuste. | `gradeTip` |
| Recorrido de bienvenida, 1 | Elige un mercado · Busca una empresa o una cripto, o usa las pestañas: Destacadas, Tasa de acierto, Acciones, Cripto y Gratis. (En Pro: Acota el catálogo con los filtros del panel…) | `tour1Title`, `tour1Lite`, `tour1Pro` |
| Recorrido de bienvenida, 2 | Lee la curva · Cada curva es el backtest de TradingView de la estrategia. Mira la tasa de acierto y el número de operaciones, y ten presente el aviso de sobreajuste: los resultados pasados no prometen los futuros. | `tour2Title`, `tour2Text` |
| Recorrido de bienvenida, 3 | Compra y cárgala en TradingView · Paga con PayPal y descarga el Pine Script. En TradingView, pégalo en el Pine Editor y pulsa «Add to chart». Los enlaces de descarga valen 7 días. | `tour3Title`, `tour3Text` |
| La fila de confianza, bajo «Pagar» | PayPal: nunca vemos tu tarjeta · Enlaces: {days}, {downloads} · Factura por correo | `trustPaypal`, `trustLinks`, `trustInvoice` |
| Bajo el total | Pagas {amount} con PayPal | `payNote` |
| La gratis | Consíguela gratis · Escribe tu correo y te enviamos el enlace de descarga. · Avísame también de estrategias nuevas (opcional) | `freeTitle`, `freeText`, `newsOpt` |
| Gracias | ¡Gracias! El pago se ha completado. · Tus estrategias están listas para descargar. · Añádela a TradingView | `thanksTitle`, `thanksSub`, `installTitle` |

**Lo que hay que mirar** (al informe del ciclo 0.36, «Para el dueño»; aquí no se cambia nada de la tienda):

- **«Factura por correo»** (`trustInvoice`): lo que llega es un recibo, sin datos fiscales; para una factura, la
  tienda da `CONTACT_EMAIL` (README, «Las descargas»). El diseño decía «By email, with VAT»: tampoco. Con los
  pagos en el núcleo, el recibo será el suyo, con el IVA desglosado (decidido el 2026-11-24).
- **«Los enlaces de descarga valen 7 días»** (`tour3Text`) lleva el 7 escrito; `trustLinks` lo toma de
  `DOWNLOAD_DAYS`. Si cambia la configuración, el recorrido se queda atrás.
