# Documentación de `edgefolio`

Lo que hace falta explicar de la tienda y no se ve leyendo el código, en los cuatro bloques de
`docs/estandar/DOCS.md` del núcleo (§1). Cómo funciona por dentro, la base de datos, las compras y cómo se
despliega: [../README.md](../README.md). Cómo se vende: [../market/](../market/README.md). Lo del núcleo no
se repite aquí: está en `zlecitool-core` (`CONTRATO.md`, `CHANGELOG.md` y su `docs/`, empezando por
`docs/estandar/CICLO.md`, el orden de trabajo).

**Si dos no coinciden**, cada uno manda en lo suyo: lo que enseña una pantalla, `PANTALLAS.md`; cómo se
comporta, los dos flujos; lo que va al servidor, `API_ENDPOINTS.md` y su referencia; lo que se guarda,
`DATOS.md`. Y por encima de todos, el código. `historico/`, `handoff/` y `design/` no mandan nunca:
cuentan de dónde salió cada cosa.

## Producto: qué es

| Fichero | Qué |
|---|---|
| [VISION.md](VISION.md) | Qué es la tienda, para quién (Lite y Pro), sus principios y el glosario |
| [DECISIONES.md](DECISIONES.md) | Lo que ha decidido el dueño, con su fecha y dónde se cuenta entero |
| [COSTES.md](COSTES.md) | Lo que se cobra (con PayPal, en USD) y de dónde sale cada precio |

No hay `REGLAS.md`: las reglas del carrito y de los precios están en el código (`edgefolio/pricing.py`,
`edgefolio/settings.py`) y las cuentan `COSTES.md` y `USER-FLOW-v7.md` §7. Ni `FUTURO.md`: lo que falta está
en `ESTADO.md`, y las ideas para venderla, en `../market/IDEAS.md`.

## Interfaz: cómo se usa

Sacados del código de `_ztool_dev` el 2026-10-12, recorridos en un navegador y corregidos el 2026-10-25 y el
2026-10-26 (núcleo 0.31.2, el catálogo de 94 estrategias). Llevan la misma numeración: las pantallas 1–9 y
las llamadas #1–#22.

| Fichero | Qué |
|---|---|
| [PANTALLAS.md](PANTALLAS.md) | Qué hay en cada pantalla |
| [FLUJO_USUARIO.md](FLUJO_USUARIO.md) | Qué hace quien compra, clic a clic, y los estados de cada pantalla; con lo que es distinto del diseño |
| [FLUJO_ADMINISTRADOR.md](FLUJO_ADMINISTRADOR.md) | Lo de quien administra: el panel del núcleo con la tienda (2026-11-25) |
| [USER-FLOW-v7.md](USER-FLOW-v7.md) | El flujo del diseño v7, con lo esperado de cada acción (en inglés). Es del diseño: lo pone al día `tools/design_update.py` (abajo, «Proceso») |

No hay `GUIA_USO.md`: el manual es el tutorial de instalación de cinco pasos de la página de gracias y de
Mis estrategias (`FLUJO_USUARIO.md`, pantallas 7 y 8). Los vídeos de los dos flujos, en
[../market/videos/VIDEOS.md](../market/videos/VIDEOS.md).

## Técnico: cómo está hecho

| Fichero | Qué |
|---|---|
| [API_ENDPOINTS.md](API_ENDPOINTS.md) | Lo que manda y recibe cada pantalla |
| [API_ENDPOINTS_referencia.md](API_ENDPOINTS_referencia.md) | Las 22 llamadas en detalle, en inglés: reglas, límites, configuración y tablas |
| [DATOS.md](DATOS.md) | Qué se guarda, quién ve qué y cuánto dura; sus «Tablas», generadas con la 0.36 |
| [tecnico/LOGS.md](tecnico/LOGS.md) | Lo que escribe la tienda en el log, capa a capa: cada `except` y `catch` con su decisión, y lo que espera a la 0.36 del núcleo |
| [IMPLEMENTATION-v7.md](IMPLEMENTATION-v7.md) | La guía técnica del diseño v7 (en inglés). Su bloque «Status» es el de la entrega del diseño y se ha quedado atrás: no se corrige aquí, porque `tools/design_update.py` mezcla el fichero con cada exportación. Cómo está la tienda hoy lo dicen los de «Interfaz» |
| [catalogue-updates.md](catalogue-updates.md) | Cómo se mantiene al día el catálogo, y lo que cuesta (en inglés). También lo mezcla `tools/design_update.py` |

## Proceso: de dónde sale

| Fichero | Qué |
|---|---|
| [ESTADO.md](ESTADO.md) | Lo hecho, lo que falta, lo que espera a la 0.36 y lo que se pide al núcleo («Para el núcleo») |
| [design/](design/) | El diseño de referencia (`python docs/design/serve.py` lo abre), sus notas (`HANDOFF.md`, `STATUS.md`, `PR_DESCRIPTION.md`) y su flujo en español (`FLUJO_USUARIO.md`). Es la base de la mezcla a tres de `tools/design_update.py`: se queda aquí, donde la busca |
| `handoff/<fecha>/` | Cada exportación de Claude Design tal como llegó y su `CAMBIOS.md`: lo que la tienda hace distinto a propósito, lo que se pide al núcleo y las preguntas del dueño. Hoy, la del [2026-10-06](handoff/2026-10-06/CAMBIOS.md) |
| `historico/` | Lo que se sustituyó: el índice de antes de este ([README_2026-11-15.md](historico/README_2026-11-15.md)) y las notas de la tienda de antes, de 2024 (`notes_2024-10-29/`: los prompts con los que se hizo su primera página y qué era cada columna de su catálogo) |
| `img/` | Las capturas del README y, en español, las de `FLUJO_USUARIO.md` y `PANTALLAS.md` (`edgefolio_es_*.png`); las hace todas `tools/screenshots.py`. Las de los flujos en `img/flujo/`, con la 0.36 |

No hay `diseno/`: el encargo a Claude Design de la tienda v7 no se guardó; lo que volvió está en `handoff/` y
`design/`. Las rondas de la tienda (las versiones del escaparate) siguen ahí, porque las lee el código; desde
`market/`, se enlazan (`../market/README.md`).

**Por qué `design/`, `IMPLEMENTATION-v7.md`, `USER-FLOW-v7.md` y `catalogue-updates.md` no se mueven:** los
pone al día `tools/design_update.py` con cada exportación de Claude Design (una mezcla a tres, con
`docs/design/` y `docs/design/handoff/` como base) y lo comprueba `tests/test_design_update.py`. El zip de
`handoff/2026-10-06/` lo lee `tests/test_site.py` (ninguna vista previa de pago entera).
