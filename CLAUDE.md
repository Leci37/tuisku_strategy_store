# CLAUDE.md — herramienta zlecitool `edgefolio`

Esta es una herramienta **zlecitool**: una app Flask pequeña que sólo contiene
lo suyo. Lo común lo pone el núcleo, `zlecitool-core`, instalado como
dependencia (la versión la fija `requirements.txt`).

Es **pública**: cualquiera mira la tienda sin cuenta y compra sin ella; las
cuentas son las del núcleo (las mismas en todas las herramientas). Lleva la
palabra Edgefolio en la barra y en el pie (`"wordmark"` en `tool.json`), sin
publicidad, y **vende con PayPal, no con créditos** (sin `"prices"`).

Antes de escribir código, lee lo que el núcleo ofrece: su **CONTRATO.md**
(en desarrollo, `../zlecitool-core/CONTRATO.md`; si no está, en GitHub:
`Leci37/zlecitool-core`, en la etiqueta de `requirements.txt`). Y el
README de aquí: la base de datos, las compras, la prueba de un correo.

## Reglas

1. **Lo común no se escribe aquí.** Cuentas, seguridad, estética, idiomas,
   correo, pruebas: vienen del núcleo. Si falta algo, **para y dilo**: se añade
   al núcleo, en otra sesión y en su repo, sale una versión nueva y aquí se
   sube. Nada de parches locales.
2. **Nada copiado** del núcleo ni de otra herramienta.
3. **Del núcleo sólo se importa lo que está en su CONTRATO.md.**
4. **Tablas con prefijo:** `__tablename__ = "edgefolio_algo"`, siempre
   explícito. Las tablas `core_*` son del núcleo: no se leen ni se escriben.
5. **Cada cosa en su sitio:** `app.py` sólo arranca; `edgefolio/routes.py`
   recibe la petición y responde; los módulos de al lado (`search`, `pricing`,
   `orders`, `downloads`, `free`, `mine`, `proofs`, `alerts`…) hacen el
   trabajo, sin Flask, para poder probarlos solos; `edgefolio/models.py` son
   las tablas.
6. **Ficheros sólo dentro de** `current_tool().data_dir` (los scripts de
   pago, las miniaturas, los cambios del día). Lo publicado (catálogo,
   gráficos, vistas previas cortadas) va en el repo.
7. **Pruebas en verde:** `pytest`. `testing.check_tool(app)` es el contrato
   del núcleo: no se quita ni se rodea.
8. **Subir el núcleo** es una decisión: leer su CHANGELOG, cambiar la
   etiqueta en `requirements.txt` y pasar las pruebas.
9. **Idioma:** documentación y comentarios en español; nombres en el código,
   en inglés. Lo que se entrega (los formatos del zip) va en inglés, como el
   script.
10. **Toda ruta pide sesión** sin hacer nada; lo que usa quien entra sin
    cuenta (mirar, comprar, descargar con su enlace, la gratis) se marca con
    `@public`. Nada de `login_required` a mano. Entrar es del núcleo, también
    con un enlace por correo (0.26): nada de `login_user` ni de un «entrar por
    correo» propio (la tienda perdió el suyo al pasar al núcleo); para llevar a
    él, `url_for('zlecitool_accounts.link_request', next=…)`. Lo hecho con la
    sesión abierta lleva `user_id` → `core_user.id`.
11. **Un correo no es una cuenta.** El núcleo no comprueba el correo al darse
    de alta: lo hecho sin cuenta con un correo (un pedido, una gratis) sólo es
    de una cuenta que ha **demostrado** ese correo (`proofs`, tabla
    `edgefolio_email_proof`). Nunca se enseña nada sólo porque el correo de la
    cuenta coincide. Los avisos de las favoritas, tampoco sin demostrarlo.
    Desde la 0.26 el núcleo demuestra el correo de la cuenta al entrar con un
    enlace (`accounts.email_proven()`); Mis estrategias sigue pidiendo la
    prueba de la tienda, y «Tus datos» (regla 23) vale con las dos.
12. **Los precios, sólo en el servidor.** El navegador manda ids, claves de
    lotes y el código tecleado; el servidor pone el precio, el descuento (con
    el tope de `MAX_DISCOUNT`) y el total que se pide a PayPal, y comprueba el
    importe al cobrar. Ningún código de descuento llega al navegador.
13. **Los scripts completos** sólo salen por un enlace que dio la tienda, que
    caduca y tiene descargas contadas (un `UPDATE` condicional, nunca leer y
    después escribir). Las vistas previas públicas van cortadas.
14. **La sesión es de todas las herramientas:** sólo claves `edgefolio.algo`,
    pequeñas. La cookie propia (`edgefolio_buyer`, la de quien compra) sólo
    lleva un token, y la base de datos su hash.
15. **Un rechazo es una clave del diccionario** (`{"error": "errAlgo"}`),
    nunca una frase en el código. Cada POST de la página lleva el token CSRF
    (lo pone `csrf.js` del núcleo en cada `fetch`).
16. **Textos de la interfaz** en `i18n/ui.json`, en los 8 idiomas a la vez;
    ninguna clave puede repetir una del núcleo. La página los lee del
    diccionario del núcleo (`zt.i18nReady`) y se repinta con `zt:language`.
17. **La página extiende `zt/base.html`** (`templates/edgefolio/shop.html`, a
    todo lo ancho): la barra, el idioma, la cuenta, el pie y lo legal son de la
    carcasa; lo de la tienda en la barra va en `topbar_start` y `topbar_end`.
    Las vistas son las del diseño (`docs/design/`), con su marcado y sus
    estilos en línea: se cambian como el diseño, no a ojo. Una exportación
    nueva entra con `tools/design_update.py` (mezcla a tres): en un conflicto,
    lo que adaptó la tienda se queda (rutas, ganchos `data-*`, `dir="auto"`,
    «Pagar» ocupado, avisos) y el cambio del diseño entra. El zip va tal cual
    a `docs/handoff/<fecha>/` con su `CAMBIOS.md` («Para el núcleo»: barra,
    pie, cuenta, idioma, cookies, el tutorial del núcleo). Una pantalla de app
    (en el móvil, con `"app"` en la ficha) extiende `zt/app.html` (barra
    compacta, pestañas de la ficha, sin pie).
18. **Nada de JavaScript en línea** (ni `<script>…</script>` ni `onclick=`):
    va en `static/js/`, con módulos.
19. **Los correos** con `zlecitool_core.mail.send`, en el idioma de la
    petición; sus enlaces, con `http.external_url(…, trusted_host_ok=False)`:
    con `ZLECITOOL_PUBLIC_URL`, nunca con la cabecera Host.
20. **Lo que toca a una hora o cada N minutos** se declara en `"schedule"` de
    `tool.json`, y su función, en `edgefolio/`, se registra con
    `add_task(app, "nombre", función)` en `create_app()`, antes de
    `create_tables(app)` (núcleo 0.25). Nada de hilos con `sleep`, `cron` ni
    APScheduler: con dos procesos o dos servidores correría dos veces. Corre en
    otro hilo, sin la petición de nadie ni `current_user`, y **puede
    repetirse**: se cuenta desde `run.scheduled_for` (cuándo tocaba), nunca
    desde «ahora», y lo hecho se apunta con `run.key` en una columna única de
    su tabla, en la misma transacción. Antes de esperar algo lento que no es
    del núcleo (el BCE o PayPal, con httpx), `db.end_idle_transaction()`. Sus
    enlaces, con `external_url(…, trusted_host_ok=False)`. En sus pruebas,
    `testing.run_task(app, "nombre", at=…)` dos veces y `testing.tick(app, at)`.
    `fx-update` y `send-alerts` son de antes y van aún con `cron`, en un solo
    servidor (README, «Comandos»): pasarlos a `"schedule"` (con sus enlaces de
    `public_base()` a `external_url()`) está pendiente, y se hace a la vez que
    se quita su `cron`.
21. **El móvil es del núcleo** (0.28). La app se pide en la ficha (`"app"`;
    la tienda no la tiene); ni *service worker* ni manifiesto propios; nada de
    nadie en las cachés del navegador (lo que es de alguien, nunca
    `Cache-Control: public`). Las claves nuevas de `localStorage`, con el slug
    (`edgefolio.algo`; las de antes, `tuisku-sf-…` y `edgefolio-…`, se quedan:
    cambiarlas olvidaría lo elegido). La barra de abajo del diseño
    (`views/phonebar.js`) lleva `data-zt-bottom`: la carcasa mide lo que tapa
    y deja su sitio, nunca un `padding-bottom` a mano. Los diálogos y las hojas
    nuevos, con `zt.openDialog`; las pruebas en un navegador, con
    `testing.mobile` (`tests/test_phone_bar.py`).
22. **Los avisos y el dispositivo, del núcleo** (0.29). Un aviso de la bandeja
    o del móvil, con `notices.send` (sus tipos en `"notices"` de `tool.json` y
    sus textos en `i18n/ui.json`; en una tarea o un trabajo, con `key`): nada
    de push, campana ni permiso de avisos propios (el permiso, con
    `zt.push.ask()` dentro de un toque). Los correos de la tienda (las
    gratis, los avisos de las favoritas, el recibo) siguen siendo correos
    (regla 19). El movimiento, la cámara, compartir y la pantalla encendida,
    con `zt.motion`, `zt.scan`, `zt.share` y `zt.keepAwake`, con su permiso en
    `"permissions"`; lo leído de un código es de fuera: se comprueba en el
    servidor.
23. **Tus datos, del núcleo** (0.30). «Mis datos» (descargar mis datos y
    borrar la cuenta) es del núcleo; lo de la tienda lo exporta y lo borra
    `edgefolio/your_data.py`, registrado con `privacy.add_privacy(app,
    export=…, erase=…, keep=…)` en `create_app()`, antes de
    `create_tables(app)`. Las dos corren en su reloj, sin `current_user`, y
    **pueden repetirse**; `erase` no confirma. Cada columna con el id de una
    cuenta, con `db.ForeignKey("core_user.id")`. Lo hecho sin cuenta es de una
    cuenta sólo por un correo demostrado: el de la cuenta si lo demostró el
    núcleo (`subject.email`) o uno de sus pruebas (regla 11); nunca por uno sin
    demostrar. **Los pedidos se quedan** (`keep`: los pide la ley fiscal), sin
    correo, sin el de PayPal y sin el hash de la cookie de quien compró; los de
    la cuenta, apuntando a la cuenta borrada. Lo demás de la cuenta se va. Una
    tabla o una columna nueva con algo de una persona entra en `export` y
    `erase` en el mismo cambio. Lo que escribe o manda un correo a cuentas
    fuera de una petición (los avisos de las favoritas) mira antes
    `privacy.closed(ids)`, y el pedido de una cuenta borrada no se cobra. Nada
    de borrar ni exportar por su cuenta. `check_tool(app, privacy_sample=…)` lo
    comprueba (`tests/test_privacy.py`, con `testing.export_account` y
    `testing.close_account`).

## La aplicación gemela

Esta es la interfaz gráfica. Los datos (estrategias, resultados, gráficos, scripts) los genera
[Leci37/tuisku_strategy_generator](https://github.com/Leci37/tuisku_strategy_generator/tree/_ztool_dev) (rama `_ztool_dev`).
Se conectan por **un paquete versionado**: su paso 7 lo deja en su `d_result/package/` y aquí se publica
con `flask --app app edgefolio import <generador>/d_result/package --scripts <generador>/d_result/pine_TW_b
[--prune]` (`edgefolio/release.py`), que lo comprueba entero antes de escribir nada y copia los scripts de
pago a `STRATEGIES_DIR`. El paquete nunca se hace público: las vistas previas de las gratis van enteras.

El contrato es `catalogue/contract.json` (versión 1): columnas, carpetas y nombre de los scripts de pago.
`publish.py` lo lee de ahí; allí, `CONTRACT_VERSION` junto a `SHOP_COLUMNS`. Un cambio de columnas o de
carpetas sube la versión y se hace en los dos repos a la vez: aquí `contract.json`, `tests/test_publish.py`
y `tests/test_release.py`; allí `S_04_ladding_file_info_to_see_in_web.py` y `tests/test_export.py`. Se sube
primero aquí (o a la vez), también al fusionar en `_ztool_main`: el CI del generador prueba contra el
`catalogue/` de nuestra `_ztool_dev` (o `_ztool_main`). El README («La aplicación gemela») lo cuenta
entero, y el `CLAUDE.md` del generador lo mismo desde su lado. Sus ramas son las mismas: `_ztool_dev` y
`_ztool_main`.

## Ramas

Se trabaja en `_ztool_dev`; `_ztool_main` sólo para lo estable (se fusiona
desde `_ztool_dev` al publicar). Los mismos nombres en el núcleo y en todas
las herramientas. `main` es la tienda de antes, y `main_2025-07-29` su copia tal
como quedó en su último cambio, para el histórico (`main_original_2025-07-29` es
el mismo commit): no se tocan.

## Comandos

```
pip install -r requirements-dev.txt
playwright install chromium
flask --app app edgefolio restore-scripts     # los scripts de pago, de la historia del repo
python app.py                                 # http://localhost:5105
pytest
python tools/screenshots.py                   # el recorrido en un navegador (con el servidor en marcha)
python tools/design_update.py ZIP [--apply]   # una exportación nueva del diseño (sin --apply, sólo lo dice)
python docs/design/serve.py                   # la maqueta del diseño, para comparar
```
