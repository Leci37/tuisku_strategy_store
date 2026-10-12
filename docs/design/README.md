# Edgefolio v7: the reference design

The design the storefront follows, as it was handed over: a working mock-up of every screen with 8
sample strategies. It is a reference, not production code, and the server never serves it.

| File | What |
|---|---|
| `Storefront v7.dc.html` | the whole store: Lite, Pro, strategy page, thank-you page, My strategies, dialogs |
| `Strategy Tree.dc.html` | the "How it decides" view, embedded in the strategy page |
| `support.js` | the runtime the two files need to open; it loads React 18.3.1, ReactDOM 18.3.1 and Babel 7.29.0 from `vendor/` |
| `vendor/` | local copies of React, ReactDOM, Babel and the mock-up's Font Awesome 6.0.0-beta3 (the templates load its stylesheet from here), so the mock-up opens offline |
| `i18n/`, `trees/`, `zlecitool_core/` | the texts and tree data the mock-up loads (its fonts come from the installed core) |
| `HANDOFF.md`, `PR_DESCRIPTION.md`, `STATUS.md` | the designer's notes (the export's `README.md` is `HANDOFF.md` here) and the status of each screen, merged with the shop's own lines; the full spec is `../IMPLEMENTATION-v7.md`, the user flow `../USER-FLOW-v7.md` (English) and `../FLUJO_USUARIO.md` (Spanish) |
| `handoff/` | those notes exactly as the last export brought them: the base of the next three-way merge |
| `serve.py` | opens the mock-up in a browser (below) |

To open it, from the repository root:

```bash
python docs/design/serve.py
# open http://localhost:8765/Storefront%20v7.dc.html
```

The script serves the charts, icons and previews the mock-up asks for from the repository's `static/`
(the mock-up's `storefront/`), and its fonts from the installed zlecitool-core, so they are not copied
here; `vendor/` is served from this folder, so nothing comes from the internet. It works from the
repository root again: this folder's `zlecitool_core/` (the mock-up's copy of the core's texts) no longer
hides the installed core, so the fonts load. The texts in `i18n/` and `trees/` are the handoff's copies,
frozen: the storefront's own files have grown since (new texts for the parts the mock-up did not have).

## A new export

1. `python tools/design_update.py ZIP` is a dry run: it says what would change (the views, the hover
   styles, the texts, this folder and the notes), which new values the views read that `static/js/` does
   not give yet, and what in the zip is not used. It writes nothing.
2. `python tools/design_update.py ZIP --apply` writes it, with a clean working tree for those paths. It
   merges three ways (the shop, the previous export, the new one) into `static/js/views/`,
   `static/css/edgefolio.css`, `i18n/ui.json` and the notes, and leaves the new export here.
3. Resolve each conflict (`<<<<<<< tienda` … `>>>>>>> diseño nuevo`): keep the shop's adaptation (real
   routes, `data-*` hooks, `dir="auto"`, the busy Checkout, toasts…) and take the design's change.
4. Check it: `pytest`, `python tools/screenshots.py` (with the store running) and
   `python docs/design/serve.py`, to compare screen by screen.

The zip itself goes, unchanged, to `docs/handoff/<date>/`, with its `CAMBIOS.md` (every difference,
marked tool or core). The export's `versions/` (earlier versions and sketches) and `offline/` (the mock-up
in one file) stay only inside that archived zip: nothing here uses them.

## How the real storefront follows it

The views in `static/js/views/` are this mock-up's templates, converted one to one into
[htm](https://github.com/developit/htm) templates for Preact: the same elements and the same inline
styles. With the mock-up's own data they render the same pixels (checked screen by screen at 1366,
768 and 390 px). What changed is where the data comes from: `static/js/app.js` is the mock-up's
logic with the sample rows, prices and purchases replaced by the shop's API.

When the design changes, change the view and the logic the same way here and in the mock-up, so the
two keep matching.
