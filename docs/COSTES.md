# Edgefolio · Costes

Lo que se cobra y de dónde sale cada precio. Sale, el 2026-11-25, del código (`edgefolio/pricing.py`,
`edgefolio/settings.py`), del catálogo (`catalogue/catalogue.csv`, `catalogue/bundles.json`), del
`README.md` de la raíz («Una compra», «Configuración») y de las decisiones del dueño del 2026-11-24
(`ESTADO.md`, «Los pagos, del núcleo»). Si no coinciden, manda el código. Lo de mantener el catálogo al
día (el tamaño del repo, los lotes mensuales) está en `catalogue-updates.md`, «Costs and risks».

## Lo que se cobra

La tienda **no usa los créditos del núcleo**: `tool.json` no tiene `"prices"`. Se paga en **USD, con
PayPal**; en la moneda del idioma la página sólo enseña un aproximado («≈ 67 €»), con los cambios del BCE
del día (la tarea `fx_update`), y el carrito dice lo que se paga en USD.

| Qué | Precio | De dónde sale |
|---|---|---|
| Una estrategia suelta | el suyo, columna `Price` del catálogo; las gratis, 0 (hoy, 2026-11-25: 10 gratis y 84 de pago, de 48 a 73 US$) | `catalogue/catalogue.csv`, que publica el generador (`flask --app app edgefolio import`) |
| Un lote | el suyo, más barato que sus estrategias sueltas (lo comprueban `tests/test_pricing.py` y `tests/test_bundles.py`) | `catalogue/bundles.json` |
| «Arma tu pack» | `PACK_SIZE` estrategias de pago por `PACK_PRICE` (5 por 249 US$), o por la suma de sus precios si es menor | `edgefolio/settings.py` |
| Los escalones por importe | más de 160 US$, un 15 %; 290, un 20 %; 500, un 25 %; 1.000, un 40 %; 2.500, un 70 % | `DEFAULT_TIERS`, `edgefolio/settings.py` |
| Un código de descuento | el suyo (`DISCOUNT_CODES`), sumado al escalón, con el tope `MAX_DISCOUNT` (70 %) entre los dos; un código de precio fijo (`FLAT_PRICE_CODES`) pone un precio a cada suelta y no se suma | `edgefolio/settings.py`, `edgefolio/pricing.py` |
| Renovar un enlace o bajar la versión nueva | gratis, mientras la estrategia no ha caducado (la «Expiry date» de su script; decidido el 2026-10-26) | `edgefolio/mine.py` |
| Una gratis | 0: el enlace va por correo, hasta 10 al día por dirección | `edgefolio/free.py` |

Cada precio, descuento y total lo calcula el servidor (`POST /api/quote` y `POST /api/orders`), y al cobrar
comprueba que PayPal cobró ese importe. Una estrategia nunca se cobra dos veces en un carrito, y una que ya es
de la cuenta no se vende suelta (`errAlreadyOwned`; en un lote o en el pack, sí: decidido el 2026-10-26).

## El IVA y el recibo

Decidido por el dueño el 2026-11-24, para cuando los pagos pasen al núcleo (`ESTADO.md`, «Lo que falta»):
**el IVA va incluido en el precio**, se paga con **PayPal y Stripe**, y el recibo es **el del núcleo**, con
el IVA desglosado. Hasta entonces, la tienda manda su propio recibo por correo (un recibo, no una factura con
datos fiscales: para eso da `CONTACT_EMAIL`).

## Lo que cuesta

Ni IA ni PDF del servidor: una compra cuesta lo que cobre PayPal por ella, que no está escrito en ningún
documento del repo (va a «Para el dueño» del informe del ciclo 0.36). Fabricar las estrategias cuesta en el
generador, no aquí. Mantener el catálogo (los gráficos en el repo, unos 570 MB; los lotes mensuales), en
`catalogue-updates.md`.
