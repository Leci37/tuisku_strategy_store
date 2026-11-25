# Estado · market/ de Edgefolio

Lo que hay de verdad, el 2026-11-25.

| Qué | Dónde | Estado |
|---|---|---|
| La tienda (su propia web comercial) | `templates/edgefolio/shop.html` y sus vistas; su dirección prevista, `edgefolio.tuisku.ai` (`docs/familia/HERRAMIENTAS.md` del núcleo, «Un servidor para todas») | hecha, en `_ztool_dev`. Si está publicada y vendiendo no lo dice ningún documento del repo; el README pide, antes de volver a vender, regenerar el catálogo («Antes de volver a vender») |
| Sus textos de venta | `i18n/ui.json`, en los 8 idiomas ([MESSAGES.md](MESSAGES.md)) | hechos |
| Sus capturas | `docs/img/edgefolio_*.png`, de `tools/screenshots.py` | hechas; `web/img/`, vacía |
| El SEO (`web/SEO.md`) | lo pone el núcleo con la ficha (`name`, `description` de `tool.json`) | sin escribir |
| La guía de usuario en vídeo | [videos/VIDEOS.md](videos/VIDEOS.md) | grabada, sin voz |
| La guía de administración en vídeo | [videos/VIDEOS.md](videos/VIDEOS.md) | grabada, sin voz |
| El vídeo comercial | — | por escribir y por grabar |
| Las tiendas de apps | — | no va a ninguna |

**Lo que no hace falta todavía** (MARKET.md §1, «cuando tocan»): `OFFER.md` (no se vende a empresas ni
on-premise) y `stores/`.

**La ronda en curso:** ninguna. Las de diseño de la tienda (v2 a v7 y el «Improvements Lab», de Claude
Design, 2026-10-06) están en `docs/design/` y `docs/handoff/`, y las enlaza
[artifacts/README.md](artifacts/README.md). El encargo de la próxima con Artifacts, en [artifacts/BRIEF.md](artifacts/BRIEF.md).

**Lo que frena la venta** (de `docs/handoff/2026-10-06/CAMBIOS.md`, «Lo que sigue abierto», y de
`docs/ESTADO.md`; lo decide el dueño):

- las condiciones de TradingView: desde el 2026-11-01, sus scripts sólo se venden en su Marketplace (su §23),
  y las normas de la UE y de España para vender estrategias;
- el catálogo caduca el 13 jun 2027 (la «Expiry date» de sus scripts) y, sin uno nuevo, después se seguiría
  vendiendo;
- los pagos, que pasan al núcleo (PayPal y Stripe, el IVA incluido, el recibo del núcleo);
- la fila de confianza dice «Factura por correo», y lo que llega es un recibo, sin datos fiscales
  ([MESSAGES.md](MESSAGES.md)).
