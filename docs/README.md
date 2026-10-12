# Documentación de `edgefolio`

Lo que hace falta explicar de la tienda y no se ve leyendo el código. Cómo funciona, la base de
datos, las compras y cómo se despliega: [../README.md](../README.md). Lo del núcleo no se repite
aquí: está en `zlecitool-core` (CONTRATO.md, docs/PLAN.md, CHANGELOG.md).

## La tienda de hoy

Sacado del código de `_ztool_dev` el 2026-10-12. Los cuatro llevan la misma numeración: las
pantallas 1–9 y las llamadas #1–#22.

| Fichero | Qué |
|---|---|
| [PANTALLAS.md](PANTALLAS.md) | Qué hay en cada pantalla |
| [FLUJO_USUARIO.md](FLUJO_USUARIO.md) | Qué hace quien compra, clic a clic, y los estados de cada pantalla; con lo que es distinto del diseño |
| [API_ENDPOINTS.md](API_ENDPOINTS.md) | Lo que manda y recibe cada pantalla |
| [API_ENDPOINTS_referencia.md](API_ENDPOINTS_referencia.md) | Las 22 llamadas en detalle, en inglés: reglas, límites, configuración y tablas |

Si no coinciden, cada uno manda en lo suyo: lo que enseña una pantalla, `PANTALLAS.md`; cómo se
comporta, `FLUJO_USUARIO.md`; lo que va al servidor, `API_ENDPOINTS.md` y su referencia. Y por
encima, el código.

## El diseño

Lo pone al día `tools/design_update.py` con cada exportación de Claude Design (mezcla a tres): por
eso estos ficheros se quedan donde los busca.

| Fichero | Qué |
|---|---|
| [IMPLEMENTATION-v7.md](IMPLEMENTATION-v7.md) | La guía técnica del diseño v7 (en inglés) |
| [USER-FLOW-v7.md](USER-FLOW-v7.md) | El flujo del diseño v7, con lo esperado de cada acción (en inglés) |
| [catalogue-updates.md](catalogue-updates.md) | Cómo se mantiene al día el catálogo (en inglés) |
| [design/](design/) | El diseño de referencia (`python docs/design/serve.py` lo abre), sus notas (`HANDOFF.md`, `STATUS.md`, `PR_DESCRIPTION.md`) y su flujo en español (`FLUJO_USUARIO.md`, hasta el 2026-10-12 en `docs/`) |
| `handoff/<fecha>/` | Cada exportación tal como llegó y su `CAMBIOS.md` |

## Lo demás

- `img/`: las capturas del README (`tools/screenshots.py`).
- `notes/`: notas del catálogo (los prompts con los que se escribieron las descripciones y qué es cada columna).
