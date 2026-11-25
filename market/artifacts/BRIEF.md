# Encargo · ronda de Artifacts de Edgefolio

**Qué se quiere:** … (una frase; el dueño la da).

**Antes de nada, leer, en este orden:**

1. De `market/`: README.md, PITCH.md, AUDIENCE.md, MESSAGES.md, PRICING.md, PROOF.md, IDEAS.md, web/PAGES.md
   y los guiones de `videos/scripts/` (lo que ya se cuenta en voz alta de la versión de ahora).
2. De la tienda: `docs/VISION.md`; `docs/PANTALLAS.md` y `docs/FLUJO_USUARIO.md` con sus capturas de
   `docs/img/`; `docs/COSTES.md`; `tool.json`; `i18n/ui.json`; y la tienda de ahora,
   `templates/edgefolio/shop.html` con sus vistas (`static/js/views/`) y su diseño de referencia
   (`docs/design/`, `python docs/design/serve.py`).
3. Del núcleo: `docs/familia/MARCA.md`, CONTRATO §17 («Portada y buscadores») y §19 (las cabeceras de
   seguridad) y su `market/`.

**Las reglas**, para que pase a la tienda sin rehacerlo:

- nada de JavaScript en línea ni de fuentes, librerías o imágenes de otro sitio (la CSP del núcleo);
- cada texto, como clave de `i18n/ui.json`, en los 8 idiomas;
- sólo lo que la tienda hace de verdad (`docs/PANTALLAS.md`); ningún precio a mano; **ninguna cifra de una
  estrategia que no sea su backtest**, ni promesas de ganar (PROOF.md);
- sin publicidad;
- primero en el móvil (la barra de abajo es la de la tienda, con el gancho del núcleo).

**Lo que vuelve**, en `artifacts/<fecha>/`: el HTML tal cual y un `CHANGES.md` (qué cambió, qué decidió el
dueño, qué queda). Con el sí del dueño, a la tienda **como cualquier cambio del diseño** (regla 17 de
`CLAUDE.md`): las vistas de `static/js/views/` son las plantillas del diseño, así que el cambio se hace igual en
la vista y en la maqueta de `docs/design/`, con sus textos en `i18n/ui.json` y sus pruebas; y STATUS.md lo
apunta. Si la ronda es una exportación de Claude Design, entra con `tools/design_update.py` y su zip va a
`docs/handoff/<fecha>/`.
