# Handoff: Edgefolio storefront — design export 2026-10-06

| This project | Tool | Repository (branch `_ztool_dev`) |
|---|---|---|
| Edgefolio (trading strategy shop) | **edgefolio** | **Leci37/tuisku_Web_selling** |

**File names:**
- `tools/design_update.py` reads these, all unchanged: `prototype/Storefront v7.dc.html`, `prototype/Strategy Tree.dc.html`, `prototype/support.js`, `prototype/i18n/storefront.ui.json`, `prototype/trees/`, `README.md`, `PR_DESCRIPTION.md`, `docs/IMPLEMENTATION-v7.md` and `docs/catalogue-updates.md`.
- **One layout change:** the earlier versions and sketches moved from `prototype/` to `versions/`. `prototype/` now holds only the current screens.
- `prototype/support.js` loads React, ReactDOM and Babel from `prototype/vendor/` instead of unpkg.com. Copy `prototype/vendor/` together with it.

**Baseline.** The shop on `_ztool_dev` today follows the v7 design exported on 6 Oct 2026, plus the trust row under Checkout. "What changed" below is measured against that.

## Prompt for Claude Code

> Work in `Leci37/tuisku_Web_selling` on branch `_ztool_dev`. Do not create `design/` branches and do not open pull requests.
>
> 1. Save this zip, unchanged, as `docs/handoff/2026-10-06/edgefolio-design-2026-10-06.zip`.
> 2. Run `tools/design_update.py` on it as usual.
> 3. Apply the changes listed below under "What changed since the previous export", screen by screen. `FLUJO_USUARIO.md` gives the expected behaviour and `STATUS.md` says what is final.
> 4. Compare `FLUJO_USUARIO.md` with the app and with the repository's `docs/FLUJO_USUARIO.md`.
> 5. Write `docs/handoff/2026-10-06/CAMBIOS.md` with every difference, each marked **tool** or **core**.
> 6. Keep what the shop has and the design doesn't show. One example is «¿Compraste sin cuenta?» in My strategies: it is not a removal.
> 7. The core (zlecitool-core 0.23.0) draws the top bar (with the word «Edgefolio»), the footer, the account and the welcome tour. The shop's chips go in the bar's two slots.
> 8. `PR_DESCRIPTION.md` and `docs/IMPLEMENTATION-v7.md` still mention `zlecitool_main`, `design/edgefolio-v7` and a pull request. This prompt replaces those lines.

## What changed since the previous export (6 Oct 2026)

Each line is one change, under the number of its screen.

**1 · Lite**
- A "New" badge (`tabNew`) on the cards of strategies released in the last 30 days.
- Adding a bundle or the custom pack removes any other bundle that shares a strategy with it, so no strategy is charged twice.
- The Compare pill sits above the floating cart instead of covering it (screens narrower than about 1100 px).
- Esc closes the pack picker and the compare dialog.

**2 · Pro**
- Cards view: the indicator name opens the indicator's TradingView page (it used to open the symbol page).
- Esc closes the filter dropdowns.
- The Table view label uses the new key `viewTableTab`, with the same text in the 8 languages. The old key `viewTable` repeated one of the core's.

**3 · Strategy page (/s/<id>)**
- "Update available" (`updateAvail`) shows only to buyers who own v1.
- The address follows the page (`#s=<id>` in the prototype), so Back, Forward and reload work. An unknown id goes to the shop.

**4 · How it decides (/s/<id>/tree)**
- "Buy to unlock" only adds the strategy to the cart (it used to remove it when it was already there). On a free strategy, it opens the free-strategy dialog.
- The address keeps `/tree`, and Back returns to the Fact sheet.
- The embedded tree no longer loads its own fonts and icons; it uses the page's. No visible change.

**5 · Cart and checkout**
- "Empty cart" also removes bundles and the custom pack.
- The crossed-out subtotal shows only when there is a discount, in Lite and Pro.
- Pro: "You pay $X with PayPal" (`payNote`) under the total when prices show in local currency.
- Lite: the code box shows its result, "Discount code applied" (`codeOk`) or "Invalid code" (`codeBad`).

**6 · Free strategy for an email**
- An empty or invalid email shows the core's `errEmailRequired` / `errEmailInvalid` under the field, with a red border.
- Enter sends, and Esc closes.
- Asking again for the same strategy restarts its link in My strategies.

**7 · Thank you (/thanks)**
- No change.

**8 · My strategies (/mine)**
- "Get a new link" keeps the purchase date, the order and the version (it used to overwrite the date and hide "Get the update").
- Each row also has `.zip` and the "Fact sheet ↗" / "How it decides ↗" links, as on the thank-you page.

**9 · Phone (390 px)**
- The Lite floating cart and the Compare pill sit 76 px up, above the bottom bar (the bar used to cover the cart).
- "Search" focuses the shop's search box (in Pro it focused the code box).
- "Cart" opens the shop with the cart in view (it used to scroll to the footer, even from other pages).

**All screens (nothing visible)**
- Images and texts that the code loads are declared as resources in the page's `<head>` and read through `window.__resources`, so the page can be bundled and published.

**The export itself (no screen)**
- Earlier versions and sketches are in `versions/`.
- `FLUJO_USUARIO.md`, `STATUS.md`, `texts.json`, `MANIFEST.md`, `offline/storefront-offline.html` and `prototype/vendor/` are included.

## Facts about the shop

- **A public tool:** anyone can browse and buy.
- **Top bar:** the core's bar carries the word «Edgefolio», and the shop's chips go in its two slots:
  - the Lite | Pro switch;
  - My strategies;
  - View tutorial;
  - the TradingView chip;
  - the currency chip.

  The design draws its own version of the bar, with the wordmark and "Estrategias de TradingView".
- **Layout:** the page is 1320 px wide, with full-width bands under the bar (ticker strip, Lite hero, Pro cart strip).
- **No ads and no cookie banner.**
- **Payment:** PayPal, in USD. No credits.
  - Prices are computed on the server.
  - No discount code ever reaches the page; the server checks them. The prototype's `DEMO20` (filled in at the start) is only a mock.
- **Languages:** 8 (es, en, pt, fr, de, zh, ar, hi), with Arabic right to left.
- **Previews:** paid previews are cut and free ones are whole. The design shows the free strategy's preview cut too; keep the shop's behaviour (see `STATUS.md`).

## Screens

| # | Screen | File | States | Status |
|---|---|---|---|---|
| 1 | Lite (default): ticker strip, search, tabs, overfitting notice, bundles and «Arma tu pack», cards, floating cart, welcome tour | `prototype/Storefront v7.dc.html` | empty, done; loading and error not designed | final |
| 2 | Pro: ladder strip, 21 filters, chips, Rows / Cards / Table, compare | `prototype/Storefront v7.dc.html` | empty, done; loading and error not designed | final |
| 3 | Strategy page (/s/<id>) | `prototype/Storefront v7.dc.html` | loading (Pine preview), done; error not designed | final |
| 4 | How it decides (/s/<id>/tree) | `prototype/Strategy Tree.dc.html`, embedded in the strategy page | loading, error, done | final |
| 5 | Cart and checkout | `prototype/Storefront v7.dc.html` | empty, error (code), done; PayPal loading, error and cancel not designed | final |
| 6 | Free strategy for an email (dialog) | `prototype/Storefront v7.dc.html` | empty, error (email), done; sending not designed | final |
| 7 | Thank you (/thanks) and install tutorial | `prototype/Storefront v7.dc.html` | done | final |
| 8 | My strategies (/mine) | `prototype/Storefront v7.dc.html` | done, expired link, no favourites; empty list, loading and error not designed; «¿Compraste sin cuenta?» not in the design | in progress |
| 9 | Phone (390 px) with the bottom bar | `prototype/Storefront v7.dc.html` | — | final |

`FLUJO_USUARIO.md` follows the same numbers, click by click. `STATUS.md` has the notes.

## Shared core vs this tool

| Part | Owner | Notes |
|---|---|---|
| Top bar with the word «Edgefolio» and its two slots | **core** | The shop's chips go in the two slots. |
| Footer (Privacy, Cookies, Terms of use, Legal notice, Contact) | **core** | — |
| Language menu, the 8 languages, RTL | **core** | — |
| Shared texts (`common.json`) | **core** | No key in `storefront.ui.json` repeats a core key. |
| Account and sign-in | **core** | My strategies works with an account, or without one through «¿Compraste sin cuenta?» (proving an email). |
| Welcome tour and its steps carousel | **core** | The tool gives the texts and images. The install tutorial uses the same format. |
| Colours and fonts | **core** | `shell.css` tokens; Ubuntu 400 / 500 / 700 |
| Buttons | **core** where the core has them | — |
| Credits | — | Not used: PayPal in USD |
| Ads and cookie banner | — | Not shown |
| Screens 1–9 and their content | tool | — |

## Design tokens in use

These are every value used in `Storefront v7.dc.html` and `Strategy Tree.dc.html`. The counts show how often each appears in the source.

### Colours

**Core tokens** (`shell.css`):

| Token | Hex | Use | Count |
|---|---|---|---|
| `--pri` | `#0950e3` | Primary: buttons, links, active states, slider handles | 171 |
| `--acc` | `#0e7c98` | Accent: How it decides, free download, end of the CTA gradient | 45 |
| `--bg` | `#f4f8fb` | Page background, tutorial tiles | 11 |
| `--surface` | `#ffffff` / `#fff` | Cards, panels, dialogs | 206 |
| `--line` | `#e2e9f0` | Borders and dividers | 163 |
| `--ink` | `#16263a` | Text, dark buttons (Compare pill) | 85 |
| `--muted` | `#5a6b80` | Secondary text | 136 |
| `--faint` | `#8d9cae` | Tertiary text, icons | 36 |
| `--ok` | `#12b76a` | "Connected" dot | 1 |
| `--warn` | `#f79009` | Warning icon | 4 |
| `--danger` | `#c0392b` | Sell, negative values, Empty cart, grade D, favourite heart | 17 |

**Tool colours:**
- **Green (gains, buy):** text `#15803d` (20), fill `#e8f7ef` (10), border `#b7e4c7` (5), message text `#15603c` (4).
- **Red (sell):** fill `#fdecea` (3), border `#f3c1bb` (4).
- **Blue tints:**
  - chip fill `#e9f0fd` (26) and chip border `#c5d6f8` (16);
  - selected fill `#f5f8ff` (11) and open table row `#f7faff` (3);
  - dashed or hover border `#9fb8ef` (4);
  - info note fill `#eef3fd` (3) and border `#d6e2fb` (3);
  - illustration bars `#9db9f3` (4).
- **Teal tints:** How it decides chip fill `#e3f4f8` (8) and border `#b5e0ea` (7); free download fill `#eef8fa` (5) and border `#bfe0e8` (5).
- **Greys:**
  - control border and dots `#cfd8e3` (18);
  - checkbox border `#cfd6e6` (8);
  - segmented track `#e9eef4` (9);
  - table header `#fbfcfe` (8);
  - disabled button `#9aa7b8` (8);
  - menu hover `#f4f6fb` (2);
  - trust-row divider `#eef2f6` (1);
  - expired pill `#f1f4f8` (1);
  - illustration surfaces `#eef3f8` and `#f8fafc` (2 each).
- **Warning note:** fill `#fff7ec` (2), border `#f6d9ae` (3). **BETA tag:** text `#9a5b00`, fill `#fff3dd`.
- **Aqua `#47f9e5`** (10): decoration only (gradients, the code tag), never as text on white.
- **Pine code editor:**
  - background `#0f1b2d`, text `#dbe4ef`, line numbers `#4c5d74`;
  - comments `#7f93ad`, strings `#9be3b0`, numbers `#f5b971`, operators `#ff8fa3`, keywords `#7cc4ff`, functions `#47f9e5`;
  - window dots `#ff5f57`, `#febc2e` and `#28c840`.
- **Other:** JavaScript format tile `#b86e00`.
- **Tree viewer details** (one or two uses each): `#f7f9fc`, `#b8c4d3`, `#b8c7da`, `#e3eaf3`, `#d5dde7`, `#eef6f1`, `#f6eeee`, `#3c7a55`, `#9a4b44`, `#9fd8ff`, `#eef3fa`.

**Gradients:**
- CTA: `linear-gradient(135deg,#0950e3,#0e7c98)` (12).
- Brand line and slider fill: `linear-gradient(90deg,#47f9e5,#0950e3)`, flipped to 270deg in RTL (5).
- Chart fade masks: `linear-gradient(90deg, transparent 15–20%, #000 75–80%)`.
- Code fade: `linear-gradient(180deg, rgba(15,27,45,0), #0f1b2d 78%)`.
- Tree slider legend: `linear-gradient(90deg,#f3c1bb,#e2e9f0 50%,#b7e4c7)`.

### Type

- **Families:**
  - `Ubuntu, system-ui, 'Segoe UI', Roboto, Arial, sans-serif`;
  - code: `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` (6 uses);
  - `Georgia, serif` (1 use).
- **Weights:** 700 (169), 600 (72), 500 (6), 400 (1). Body is 14 px with line height 1.5.
- **Font sizes (px), with use counts:**
  - 40 (Lite title): 1
  - 30 (standalone tree title): 2
  - 28 (price on the strategy page): 1
  - 26 (counts, page titles): 4
  - 24 (thank-you title): 1
  - 22: 6
  - 21 (wordmark): 2
  - 20 (dialog titles): 6
  - 18: 6
  - 17: 6
  - 16: 10
  - 15.5: 1
  - 15: 12
  - 14.5: 9
  - 14: 30
  - 13.5: 26
  - 13: 53
  - 12.5: 47
  - 12: 55
  - 11.5: 20
  - 11: 56
  - 10.5: 15
  - 10: 8
  - 9.5: 1
  - 9: 5
- **Install tutorial illustrations:** they scale with their frame, in sizes from `1.9cqw` to `4.4cqw`.
- **Line heights:** 1, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.45, 1.5, 1.7 (code), 15px and 17px (tree).
- **Letter spacing (px):** −0.6, −0.5, −0.4, −0.3, −0.2, 0, 0.3, 0.4, 0.5, 0.6, 0.8. Uppercase labels use 0.6–0.8.

### Spacing, radii, shadows, layout

- **Gaps (px):** 2, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 24, 26. The most used are 6, 8 and 10.
- **Paddings:**
  - chips: 3px 9px and 5px 11px;
  - buttons: 8px 14px, 10px 16–18px and 12px 20–22px;
  - cards: 14–16px;
  - panels: 16px 18px and 20px 22px;
  - page sides: 28px.
- **Radii (px):**
  - 999 (pills);
  - 50 % (dots, avatars);
  - 20 (tour and tutorial dialogs);
  - 18 (cards, panels, dialogs);
  - 16, 14, 12 (buttons), 10, 9, 8, 7, 6, 5, 4, 3, 2.
- **Shadows:**
  - CTA: `0 8px 20px rgba(9,80,227,.22)`;
  - card hover: `0 12px 32px rgba(22,38,58,.08–.10)` and `0 14px 36px rgba(22,38,58,.10)`;
  - dropdown or floating cart: `0 18px 48px rgba(26,35,56,.2)`;
  - dialog: `0 30px 80px rgba(0,0,0,.3)`;
  - pill: `0 12px 30px rgba(22,38,58,.3)`;
  - slider handle: `0 2px 6px rgba(9,80,227,.25)`;
  - focus ring: `0 0 0 3px rgba(9,80,227,.15)`.
- **Backdrop:** `rgba(22,38,58,.45)`, or `.5` for the tutorials.
- **Max widths:**
  - shell: 1320;
  - fact sheet: 1120;
  - thank-you and My strategies: 1000;
  - floating cart: 780;
  - compare: 760;
  - Lite hero text: 640 / 540;
  - tour and tutorials: 480;
  - pack picker: 460;
  - free download: 420.
- **Breakpoints:**
  - **640 px:** phone; bottom bar; the tree's small sizes.
  - **840 px:** the tree's side panel becomes sticky.
  - **900 px:** five tutorial tiles per row.
  - **About 900 px:** the Pro filter panel wraps above the list.

## Where everything is

- **`prototype/`:** the current screens, `Storefront v7.dc.html` and `Strategy Tree.dc.html`, with:
  - `support.js`;
  - texts: `i18n/`, `trees/` and `zlecitool_core/i18n/`;
  - images, icons and logos: `storefront/assets/`, `brand/` and `zlecitool_core/ui/static/brand/`;
  - fonts: `zlecitool_core/ui/static/fonts/`;
  - local copies of the outside libraries: `vendor/`.
- **`versions/`:** earlier versions (Storefront v2–v6) and sketches (Storefront Redesign, Tree Styles, Improvements Lab), for reference only. They use the same `support.js` and assets; to open one, copy it into `prototype/`.
- **`offline/storefront-offline.html`:** Storefront v7 in one file. It opens with a double click and no internet.
- **Documents:**
  - `FLUJO_USUARIO.md` (Spanish): the flow per screen 1–9;
  - `STATUS.md`: the status per screen;
  - `texts.json`: every text with its key;
  - `MANIFEST.md`: every file.
- **Specs:**
  - `docs/IMPLEMENTATION-v7.md`: the technical guide;
  - `docs/USER-FLOW-v7.md`: the English flow, with the fixes in §18;
  - `docs/catalogue-updates.md`;
  - `PR_DESCRIPTION.md`: the work steps;
  - `docs/img/`: the README screenshots.

**To open the source:** run `cd prototype && python -m http.server`, then open `http://localhost:8000/Storefront%20v7.dc.html`.

## State and storage (prototype)

- **`localStorage` keys:**
  - `tuisku-sf-mode`: Lite or Pro;
  - `tuisku-sf-lang`: the language;
  - `tuisku-sf-pview5`: the Pro view;
  - `edgefolio-tour-v1`: the welcome tour has been shown;
  - `edgefolio-install-v1`: the install tutorial has been shown.
- **Discount tiers** (as in `api/settings.py`): $160 → 15 %, $290 → 20 %, $500 → 25 %, $1,000 → 40 % and $2,500 → 70 %, with the total capped at 70 %. Codes are checked on the server.

## No outside links

- **Font Awesome 6.0.0-beta3, React 18.3.1, ReactDOM 18.3.1 and Babel 7.29.0** are copied into `prototype/vendor/`; the JavaScript libraries were checked against the runtime's SRI hashes.
- **The only external addresses left** are links the user clicks: TradingView pages, `https://tuisku.eu` (in the versions) and `mailto:sales@tuisku.eu`.
