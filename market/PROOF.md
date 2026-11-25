# Lo que se puede afirmar · Edgefolio

Cada cosa que la tienda afirma, con su prueba (MARKET.md §4 del núcleo). Lo que no esté aquí, no se dice.

| Lo que se afirma | Dónde | La prueba |
|---|---|---|
| Las cifras de cada estrategia (beneficio neto, acierto, operaciones…) son su **backtest** en datos que el modelo no vio | Lite, Pro, la ficha; `riskTried` | las publica el generador con cada paquete (`catalogue/catalogue.csv`, `catalogue/release.json`: la ejecución 2d00ddc); el aviso de sobreajuste lo dice al lado de cada lista |
| «Se eligieron entre 1.531 probadas» (el {m} de `riskTried`) | el aviso de sobreajuste | `tried` de `catalogue/release.json`; lo comprueba `tests/test_listing_page.py` |
| La nota, A a D, dice cuánta prueba respalda el backtest | las tarjetas y la ficha | `GRADE_CUTOFFS` (100, 50 y 25 operaciones), decidido el 2026-10-26; su explicación los dice (`gradeCuts`) |
| «PayPal: nunca vemos tu tarjeta» | la fila de confianza | se paga en PayPal (`edgefolio/paypal.py`); la tienda guarda el pedido y lo que dice PayPal de quien pagó, no la tarjeta (`docs/DATOS.md`) |
| «Enlaces: 7 días, 10 descargas» | la fila de confianza | `DOWNLOAD_DAYS` y `MAX_DOWNLOADS`, tal como estén configurados; las descargas se gastan con un `UPDATE` condicional (`tests/test_orders.py`) |
| El script entero sólo para quien lo compró | la ficha («el resto del script…») | las vistas previas públicas van cortadas (`tests/test_site.py`, `tests/test_media.py`) |
| 8 idiomas, el árabe de derecha a izquierda | toda la página | `i18n/ui.json` en los 8 (`tests/test_texts.py`, `tests/test_page_code.py`) |
| Tus datos: descargarlos y borrar la cuenta | el menú de la cuenta (núcleo) | CONTRATO §5 del núcleo; lo de la tienda, `edgefolio/your_data.py` y `tests/test_privacy.py`; `docs/DATOS.md` |

**Lo que no se puede afirmar:**

- que una estrategia vaya a ganar, ni ninguna cifra «desde su publicación» mientras ninguna estrategia la tenga
  (decidido el 2026-10-26, E11). El generador avisa de que, probadas con datos que no vieron, **pierden de media
  después de costes** (README, «Antes de volver a vender»);
- «Factura por correo» o «con IVA»: hoy es un recibo ([MESSAGES.md](MESSAGES.md));
- cuánta gente a la vez: la tienda no tiene `loadtest/` (el objetivo de la familia, en `docs/plan/PLAN.md` §10
  del núcleo).
