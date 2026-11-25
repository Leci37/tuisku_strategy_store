# Precios · Edgefolio

Lo que la tienda enseña de precios y de dónde sale. **Ningún precio se escribe aquí**: el de cada estrategia
está en el catálogo y lo demás, en la configuración; por qué y cómo se calcula, en `docs/COSTES.md`.

| Lo que se ve | Dónde | De dónde sale |
|---|---|---|
| El precio de cada estrategia (o «Gratis») | las tarjetas de Lite, las filas de Pro, la ficha | `Price` de `catalogue/catalogue.csv` (lo publica el generador) |
| El aproximado en tu moneda, «≈ 67 €» | en los 7 idiomas que no son el inglés | los cambios del BCE del día (la tarea `fx_update`); se paga en USD |
| Los packs, con «Ahorra un N %» | Lite, la fila de los packs | `catalogue/bundles.json` |
| «Arma tu pack · 5 por 249 US$» | Lite, la última tarjeta de los packs | `PACK_SIZE`, `PACK_PRICE` |
| La escalera de descuentos por volumen | Pro, arriba; el carrito | `DEFAULT_TIERS` de `edgefolio/settings.py`, que la página pide a `/api/config`: no pueden no coincidir |
| El código de descuento | el carrito | `DISCOUNT_CODES` (nunca llega a la página: sólo si vale y cuánto descuenta) |
| «Pagas X US$ con PayPal» | el carrito | el total que calcula el servidor (`/api/quote`) |

Sin créditos ni tabla de precios del núcleo: la tienda no tiene `"prices"` en `tool.json`. Con los pagos en el
núcleo, el precio incluirá el IVA (decidido el 2026-11-24, `docs/DECISIONES.md`).
