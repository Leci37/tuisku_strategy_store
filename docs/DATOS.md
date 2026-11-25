# Edgefolio · Datos

Qué guarda la tienda, quién ve qué y cuánto dura. Sale, el 2026-11-25, del código y de lo que ya estaba
escrito: los docstrings de `edgefolio/models.py`, `edgefolio/your_data.py` y `edgefolio/tasks.py`, y el
`README.md` de la raíz («La base de datos», «Tus datos», «Las descargas», «Mis estrategias y la prueba de
un correo» y «Las gratis y las novedades», con las columnas de cada tabla). Si no coinciden, manda el
código. Lo de las cuentas (el correo, la contraseña, la sesión, el idioma) es del núcleo: su
`docs/familia/TABLAS.md`.

## Qué se guarda

En la base de datos de todas las herramientas (la del núcleo), nueve tablas `edgefolio_*`; ninguna lee
ni escribe una `core_*`: lo que es de alguien apunta a `core_user.id`.

| Tabla | Qué guarda | De quién |
|---|---|---|
| `edgefolio_order` | un pedido de PayPal: lo comprado, el total que calculó el servidor, cómo acabó, el correo (el de la cuenta o, sin cuenta, el de PayPal), lo que dice PayPal de quien pagó y el hash de la cookie del navegador que compró | de la cuenta que compró con la sesión abierta; sin cuenta, del correo |
| `edgefolio_download` | cada enlace de descarga de una estrategia de un pedido pagado: cuándo caduca y cuántas veces se usó | del pedido |
| `edgefolio_free_claim` | una gratis mandada a un correo, con su enlace, si marcó las novedades, cuándo la pidió y el hash de quién la pidió (la cuenta o la IP) | de la cuenta, si la pidió con la sesión abierta; si no, del correo |
| `edgefolio_subscriber` | quien pidió las novedades, con su consentimiento; sólo cuenta cuando lo confirma desde el correo | del correo |
| `edgefolio_favourite` | las favoritas de una cuenta, con sus avisos, y el correo y el idioma a los que van | de la cuenta |
| `edgefolio_alert_state` | cómo era cada estrategia en la última vuelta de los avisos | de nadie |
| `edgefolio_email_proof` | que una cuenta ha demostrado un correo; hasta entonces, el hash del enlace que se le mandó | de la cuenta |
| `edgefolio_mailbox` | una fila por dirección a la que escribe la tienda, sólo con cuándo (para contar las gratis del día de una vez) | del correo |
| `edgefolio_task_done` | cada vez que una tarea del reloj ya se hizo, con lo que hizo en cifras | de nadie |

Fuera de la base de datos, en la carpeta de datos de la tienda (`<ZLECITOOL_DATA_DIR>/edgefolio/`): los
scripts de pago (`strategies/`), las miniaturas WebP de los gráficos (`thumbs/`) y los cambios de moneda
del día (`fx.json`). Nada de eso es de una persona. El catálogo publicado (`catalogue/`, `static/assets/`)
va en el repo.

**En el navegador** (localStorage, sin cuenta): el modo Lite o Pro, el carrito, el pack, Comparar, las
favoritas de quien no ha entrado, el chip de TradingView y que el recorrido de bienvenida ya se vio
(`docs/FLUJO_USUARIO.md`, «[Navegador]»). Y una cookie propia, `edgefolio_buyer` (HttpOnly, 30 días): un
token que dice qué navegador hizo un pedido; la base de datos guarda sólo su hash.

**Nunca se guardan en claro** los enlaces de un solo uso (confirmar las novedades, demostrar un correo) ni
la cookie de quien compra: sólo su hash. Los logs no llevan correos, nombres, lo tecleado, IP, tokens ni
códigos (`docs/tecnico/LOGS.md`).

## Quién ve qué

- **Un pedido** y sus enlaces de descarga: el navegador que lo hizo (su cookie), la cuenta que compró con
  la sesión abierta y, si se compró sin cuenta, una cuenta que ha demostrado el correo de PayPal. Quien
  sólo tiene el id del pedido (va en la dirección de vuelta de PayPal) ve el recibo sin enlaces.
- **Mis estrategias**: lo hecho con la sesión abierta y lo hecho sin cuenta con un correo demostrado (en
  la tienda, «¿Compraste sin cuenta?», o por el núcleo, al entrar con un enlace por correo). Nunca por un
  correo que sólo coincide con el de la cuenta (regla 11 de `CLAUDE.md`).
- **Los avisos de las favoritas**, sólo a un correo demostrado y nunca a una cuenta borrada.
- **El correo de una gratis** sólo lleva el enlace a esa dirección: la respuesta de la página no lo trae.

## Cuánto dura

| Qué | Cuánto | Dónde se decide |
|---|---|---|
| Un enlace de descarga de un pedido | `DOWNLOAD_DAYS` (7) días y `MAX_DOWNLOADS` (10) descargas, entre el `.pine`, el `.zip` y «Descargar todo»; se renueva desde Mis estrategias | `edgefolio/settings.py` |
| El enlace para demostrar un correo | 24 horas, un uso, sólo para la cuenta que lo pidió | `edgefolio/proofs.py` (`PROOF_HOURS`) |
| La cookie de quien compra | 30 días | `edgefolio/orders.py` (`BUYER_DAYS`) |
| Un alta en las novedades sin confirmar | se borra a los 30 días (la tarea `purge`, cada día a las 04:00) | `edgefolio/free.py` (`UNCONFIRMED_DAYS`), `tool.json` |
| Una gratis caducada | se borra a los 90 días de caducar (la misma tarea) | `edgefolio/free.py` (`EXPIRED_CLAIM_DAYS`) |
| La fila del buzón de una dirección | se borra a los 90 días sin escribirle (la misma tarea) | `edgefolio/free.py` (`MAILBOX_DAYS`) |
| Un pedido | se queda: lo pide la ley fiscal. Al borrar la cuenta, sin correo, sin lo de PayPal y sin el hash de la cookie | `edgefolio/your_data.py` (`KEEP`) |

## Tus datos

«Descargar mis datos» y «Borrar mi cuenta» son del núcleo («Mis datos», en la cuenta); lo de la tienda lo
exporta y lo borra `edgefolio/your_data.py`. El zip lleva sus pedidos y sus enlaces, sus gratis, sus
favoritas, las pruebas de sus correos y, de cada correo demostrado, su alta en las novedades y su fila del
buzón; sin los enlaces ni ningún hash. Al borrar la cuenta, los pedidos se quedan sin quién los hizo y lo
demás se va (README, «Tus datos»). Lo prueba `tests/test_privacy.py`, con `check_tool(app,
privacy_sample=…)`.

## Tablas

Con la 0.36 del núcleo, esta sección la genera `flask --app app zt tables --write docs/DATOS.md` de los
modelos (cada tabla con su para qué, de quién es, qué pasa al borrar una cuenta, sus columnas y su
diagrama), entre las marcas `zt:tablas`. Hasta entonces, las columnas de cada tabla están en el README
(«La base de datos») y su para qué, en el docstring de cada modelo de `edgefolio/models.py` (las nueve lo
tienen).
