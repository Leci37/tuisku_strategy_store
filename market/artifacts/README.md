# artifacts/ · Edgefolio

Las rondas de diseño de lo que vende la tienda. Con Artifacts, cada una irá aquí, en `<fecha>/`, con su
`CHANGES.md`; el encargo de la próxima, en [BRIEF.md](BRIEF.md). No manda nunca: cuenta de dónde salió cada cosa.

## Las rondas de la tienda, que se quedan en `docs/`

Las de antes son de Claude Design (2026-10-06) y **no se mueven aquí** (MARKET.md §7 del núcleo pedía
moverlas; decidido con la coordinadora del ciclo 0.36 el 2026-11-25): `docs/design/` es la base de la mezcla a
tres con la que entra cada exportación nueva (`tools/design_update.py`, que comprueba
`tests/test_design_update.py`), y el zip de `docs/handoff/2026-10-06/` lo lee `tests/test_site.py` (ninguna
vista previa de pago entera). Tampoco se sacan del zip: duplicarlas en git no aporta nada. Están aquí:

| Ronda | Qué | Dónde |
|---|---|---|
| Storefront v7 (2026-10-06) | la tienda que hay: Lite, Pro, la ficha, Gracias, Mis estrategias y los diálogos | [`docs/design/Storefront v7.dc.html`](../../docs/design/) (`python docs/design/serve.py` la abre), con sus notas en `docs/design/` y `docs/design/handoff/` |
| Storefront v2 a v6 y «Storefront Redesign» | las rondas de antes | dentro del zip [`docs/handoff/2026-10-06/edgefolio-design-2026-10-06.zip`](../../docs/handoff/2026-10-06/), en `versions/` |
| «Improvements Lab» | las 10 ideas que se probaron antes de pasar a la tienda | en el mismo zip, `versions/Improvements Lab.dc.html`; su estado, en [../IDEAS.md](../IDEAS.md) |
| «Tree Styles» | los estilos de «Cómo decide» | en el mismo zip, `versions/Tree Styles.dc.html` |
| La tienda en un fichero | la maqueta v7 sin servidor | en el mismo zip, `offline/storefront-offline.html` |

Lo que la tienda hace distinto del diseño, a propósito, y lo que se decidió de cada ronda: en
[`docs/handoff/2026-10-06/CAMBIOS.md`](../../docs/handoff/2026-10-06/CAMBIOS.md).
