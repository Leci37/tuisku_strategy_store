# market/ · Edgefolio

Cómo se vende Edgefolio: a quién, con qué palabras, con qué precio y con qué pruebas, sus ideas y sus
vídeos. Aparte de `docs/`, que cuenta lo que hace. El estándar: `docs/estandar/MARKET.md` del núcleo. Lo de
la familia (tuisku.ai, la oferta, las cifras de todas), en el `market/` del núcleo: aquí se enlaza, no se
repite.

**La tienda es el producto y su propia web comercial.** Edgefolio no tiene portada (`templates/landing.html`):
quien llega a `/` entra directamente en la tienda, y lo que vende está dentro de ella, en Lite (la cabecera,
el aviso de sobreajuste, los packs), en la fila de confianza bajo «Pagar» y en el recorrido de bienvenida
([web/PAGES.md](web/PAGES.md)). Lo aprobado aquí pasa a sus vistas y a `i18n/ui.json`, como cualquier cambio
de la tienda (regla 17 de `CLAUDE.md`: las vistas son las del diseño).

| Documento | Qué |
|---|---|
| [STATUS.md](STATUS.md) | qué está publicado, qué falta y la ronda en curso |
| [PITCH.md](PITCH.md) | para quién es, qué problema resuelve y la promesa |
| [AUDIENCE.md](AUDIENCE.md) | los dos tipos de cliente (Lite y Pro) y lo que objetan |
| [MESSAGES.md](MESSAGES.md) | los textos que venden, con su clave de `i18n/ui.json` |
| [PRICING.md](PRICING.md) | lo que la página enseña de precios y de dónde sale (nunca a mano) |
| [PROOF.md](PROOF.md) | lo que la tienda afirma y su prueba |
| [IDEAS.md](IDEAS.md) | las ideas, con su fecha, de dónde salen y su estado |
| [web/PAGES.md](web/PAGES.md) | la parte de la tienda que vende, sección a sección |
| [videos/VIDEOS.md](videos/VIDEOS.md) | cada vídeo (guía de usuario, de administración y comercial): su guion y su enlace de YouTube |
| [artifacts/BRIEF.md](artifacts/BRIEF.md) | el encargo de una ronda con Artifacts: qué leer y qué reglas cumplir |

No tocan (MARKET.md §1, «cuando tocan»): `OFFER.md` (no se vende a empresas ni on-premise) y `stores/` (no va
a ninguna tienda de apps: su ficha no tiene `"app"`).

## Lo que se enlaza

Se queda donde está, porque lo lee el código o es de `docs/`:

- **La tienda**, `templates/edgefolio/shop.html` (sobre `zt/base.html` del núcleo), con sus vistas
  (`static/js/views/`) y sus textos (`i18n/ui.json`).
- **Sus capturas**, `docs/img/edgefolio_*.png` (las del README y, en español, `edgefolio_es_*.png`), que hace
  `tools/screenshots.py` con la tienda en marcha. `web/img/`, aún vacía: el mismo script podría dejar ahí las
  de la venta (IDEAS.md).
- **Lo que hace la tienda**: `docs/VISION.md`, `docs/PANTALLAS.md`, `docs/FLUJO_USUARIO.md` y `docs/COSTES.md`.
- **Las rondas de diseño de la tienda** (abajo).

## Las rondas de la tienda

MARKET.md §7 del núcleo pide moverlas aquí, a `artifacts/<fecha>/`. **No se mueven**: son la base de la mezcla a
tres con la que entra cada exportación nueva del diseño (`tools/design_update.py`, que comprueba
`tests/test_design_update.py`), y el zip lo lee `tests/test_site.py`. Moverlas sería cambiar el código, y
`docs/estandar/DOCS.md` §4 del núcleo ya dice que `design/` se queda donde está (el informe del ciclo 0.36 lo
lleva a «Para el dueño»). Están aquí:

| Ronda | Qué | Dónde |
|---|---|---|
| Storefront v7 (2026-10-06) | la tienda que hay: Lite, Pro, la ficha, Gracias, Mis estrategias y los diálogos | `docs/design/Storefront v7.dc.html` (`python docs/design/serve.py` la abre), sus notas en `docs/design/` y `docs/design/handoff/` |
| Storefront v2 a v6 y «Storefront Redesign» | las rondas de antes | dentro del zip `docs/handoff/2026-10-06/edgefolio-design-2026-10-06.zip`, en `versions/` |
| «Improvements Lab» | las 10 ideas que se probaron antes de pasar a la tienda | en el mismo zip, `versions/Improvements Lab.dc.html`; su estado, en [IDEAS.md](IDEAS.md) |
| La tienda en un fichero | la maqueta v7 sin servidor | en el mismo zip, `offline/storefront-offline.html` |

Lo que la tienda hace distinto del diseño, a propósito, y lo que se decidió de cada ronda: en
`docs/handoff/2026-10-06/CAMBIOS.md`.

## Antes de escribir aquí

Leer `docs/VISION.md`, `docs/PANTALLAS.md` (nada se promete que no esté ahí), `docs/COSTES.md`, `tool.json` e
`i18n/ui.json`. Y, para cualquier cifra de una estrategia, lo que dice `docs/VISION.md` en «Principios»: son
backtests, y probadas con datos que no vieron pierden de media después de costes.

**Las imágenes, en GitHub; los vídeos, en YouTube**: en el repo sólo va el guion y el enlace de cada vídeo, nunca
el vídeo (el `.gitignore` deja fuera los `.mp4`, `.mov`, `.webm` y `.mkv` de aquí).

**Quién manda:** el código, luego `docs/` (lo que hace), luego `tool.json`, luego esto. Ningún precio se escribe a
mano. `artifacts/<fecha>/` y `archive/` no mandan nunca.

Un cambio sólo de `market/` no gasta CI (`paths-ignore` en `.github/workflows/pruebas.yml`).
