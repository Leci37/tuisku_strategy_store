# Edgefolio storefront v7: implementation guide for Claude Code

The design reference is `Storefront v7.dc.html`. This guide lists what to build in the real shop (`Leci37/tuisku_strategy_store`, branch `zlecitool_main`, folder `storefront/` + `api/`), in which order, and what each piece needs from the server.

The mock-up uses 8 sample strategies, and some of its figures are examples (marked below).

The click-by-click behaviour of every screen, with the expected result of each action, is in `docs/USER-FLOW-v7.md`.

> **Status in this repository.** This is the designer's guide, kept as it was handed over; the build
> follows it with these differences:
> - **Built:** §1–§5 and §9–§12; from §6 the paged catalogue with server-side filters and histograms,
>   bundles and the pack priced by the server, the grade (with the cut-offs of §2, still to agree),
>   favourites with alert opt-ins and their daily emails (`flask --app app edgefolio send-alerts`), free
>   download for an email (with double opt-in for news), local currency (`catalogue/fx.json`, refreshed by
>   `flask --app app edgefolio fx-update`), New this month, the previews, the trust row under Checkout
>   (its figures from `DOWNLOAD_DAYS`/`MAX_DOWNLOADS`, its address from `CONTACT_EMAIL`) and the receipt
>   it promises, emailed on payment (a receipt, not a tax invoice); and the changes of the second
>   export of 6 Oct 2026 (`docs/handoff/2026-10-06/CAMBIOS.md`): the New badge, the Compare pill above
>   Lite's cart, the code's result in Lite, "You pay … with PayPal" in Pro, the free dialog's email
>   errors, Esc on dialogs and dropdowns, "Update available" only for an owner of an older version, and
>   the Fact sheet and How it decides links in My strategies.
> - **Different:** the shop is a zlecitool tool (Flask on zlecitool-core, the files of `storefront/` are
>   now `static/`, `templates/edgefolio/shop.html` and `i18n/ui.json`): the bar, the language menu and the
>   footer are the core's shell, and My strategies uses the core's shared accounts; what was bought
>   without an account shows up once the account confirms that email (a one-time emailed link).
>   Thumbnails are made on request, not at publish time; the welcome tour is shown once per browser.
>   "Get a new link" hands over the current version (there is one script file per strategy).
>   The work goes to `_ztool_dev`: no `design/` branch and no pull request, whatever this file says.
> - **Not built (needs data or jobs the shop does not have):** the since-release job, versions beyond
>   v1 and paid updates, translations of the indicator texts.

## 0. Ground rules

- **Brand.** The product name is **Edgefolio**, written as text in Ubuntu 700, with "Edge" in `#16263a` and "folio" in `#0950e3`. There is no "by tuisku" and no tuisku logo in the bar. The line under the bar stays: `linear-gradient(90deg, #47f9e5, #0950e3)`, flipped to 270deg in RTL.
- **Colours.** Use the tokens from `zlecitool_core/ui/static/css/shell.css` only:
  - main: `--pri #0950e3`, `--acc #0e7c98`;
  - surfaces: `--bg #f4f8fb`, `--surface #fff`, `--line #e2e9f0`;
  - text: `--ink #16263a`, `--muted #5a6b80`, `--faint #8d9cae`;
  - status: `--ok #12b76a`, `--warn #f79009`, `--danger #c0392b`.
  - Text greens use `#15803d` on white or on `#e8f7ef`.
  - Aqua `#47f9e5` is decoration only and never carries text.
- **Font.** Ubuntu 400/500/700, self-hosted from the core, never from Google Fonts.
- **Buttons.** Primary: `linear-gradient(135deg,#0950e3,#0e7c98)`, radius 12, white 700 text. Lite "Buy": solid `#0950e3`. Ghost: white with a 1px `#e2e9f0` border. When disabled, use a flat grey background, never opacity.
- **Layout.** Fluid, with `max-width: 1320px`, padding 28px (16px on phones) and flex-wrap or grid with `minmax`. There are no fixed widths on boxes that hold text. Use logical properties everywhere (`inset-inline-*`, `margin-inline-*`, `text-align: start/end`) so Arabic flips cleanly.
- **No inline JS.** The core's CSP forbids it. Move every handler into `static/js`.
- **Images.** Every chart gets `loading="lazy" decoding="async"`. Generate WebP thumbnails, about 640px wide, for cards and tables, and load the full PNG only on the strategy page.

## 1. Shell and modes

| Element | Behaviour |
|---|---|
| Lite \| Pro segmented control (top bar) | Defaults to Lite and is remembered in `localStorage['tuisku-sf-mode']`. The active side is solid `#0950e3` with white text. |
| My strategies, View tutorial, TradingView chip, currency chip, language menu | Chips with radius 999, 11px, 600. They wrap onto a second line on narrow screens. |
| Language | The 8 core languages (`_languages` in `common.json`) with live switching and no reload. `dir="rtl"` for `ar`. Numbers, money and dates use `Intl` with the language's locale; Arabic uses Latin digits (`ar-u-nu-latn`). |
| Phone bottom bar (< 640px) | Shop, Search, Cart (with count) and Mine. Fixed to the bottom, at least 44px tall, with 64px of page padding left below the content. Search focuses the current mode's search box; Cart opens the shop with the cart in view. The Lite floating cart and the compare pill sit 76px from the bottom, above the bar. |
| Routing | `/s/<id>` and `/s/<id>/tree` follow in-app navigation, so Back, Forward and reload work. An unknown id goes to the shop. |
| Esc | Closes any open dialog or menu (tours, compare, pack picker, free download, language menu, filter dropdowns). |

## 2. Lite (default)

1. **Ticker strip** of the top strategies with a green % gain. It scrolls sideways and does not wrap.
2. **Header:** a faded candle chart (`opacity .2`, masked with `linear-gradient(90deg, transparent 15%, #000 75%)`), H1 "Strategies for TradingView" (`liteTitle`), one search field, and the tabs Hot · Win rate · Stocks · Crypto · **New · N** · Free.
3. **Overfitting box,** always visible: background `#fff7ec`, border `#f6d9ae`, warning icon in `#f79009`, `riskTitle` and `riskText`.
4. **Bundles row:** three bundles plus a **Build your pack** card (5 slots, fixed price). Slots open a picker of up to 5. The button stays grey until all 5 are chosen.
5. **Cards** (`grid-template-columns: repeat(auto-fill, minmax(270px,1fr))`):
   - ticker and name, plus a green % chip (a button that explains the metric);
   - the profit curve, cropped to the chart (`object-position: 50% 82%`), with a "⚠ Backtest" label;
   - win rate and trades, both explainable;
   - **grade A–D:** A ≥ 300 trades (`#15803d`), B ≥ 100 (`#0e7c98`), C ≥ 30 (`#5a6b80`), D below 30 (`#c0392b`). These cut-offs still need to be agreed;
   - **since release %:** green when positive, red when negative;
   - **favourite** heart and **compare** toggle (up to 3);
   - a **New** badge next to the ticker when the strategy was released in the last 30 days;
   - price and Buy.
6. **Floating cart bar** (sticky bottom):
   - item count and a discount tag (−35%);
   - a "Have a code?" link that opens the code box;
   - the total in the local currency with "You pay $X with PayPal" under it, and Checkout;
   - the crossed-out subtotal only when a discount applies, and the code result (applied / invalid) next to the code box;
7. **Compare** pill at the bottom start (just above the floating cart when that is visible), which opens a table of up to 3 strategies. The best value in each row is marked with green text on `#e8f7ef`.

## 3. Pro

1. **Discount ladder strip:** the cart, a progress bar (5 ticks with the % on one line and the amount under it), the code, the totals and Checkout. "Empty cart" also removes bundles and the custom pack. With local currency, "You pay $X with PayPal" goes under the total, and the subtotal is crossed out only when a discount applies.
2. **Left filter panel** (1e). It moves above the list when the width is under about 840px. It has:
   - the count and Reset;
   - Only FREE;
   - **sliders** with draggable handles (pointer events), each with a **histogram above it**. A bin's height is count / max × 40px with a 4px minimum for non-empty bins. Bins below 15% of the tallest are **solid `#0950e3`**, the rest use the gradient. Bins outside the range fade to 25%, and a 1px baseline runs underneath;
   - **multi-select dropdowns** (search, Select all / Deselect all, tick boxes with icon and count) for Symbol, Time frame, Indicators, Index and Release date;
   - 14 more ranges that open in place.
3. **Active filter chips** above the list, each with an ×, plus "Clear all".
4. Views: **Rows** (default; the strategy's candle chart faded behind each row) · **Cards** (the indicator name links to its TradingView page) · **Table** (sortable, a grade badge next to the ticker, a compare toggle, and an expandable row with both charts).
5. **Strategy page** link from every view.

## 4. Strategy page (route `/s/<id>`; it can be opened in a new tab)

It contains, top to bottom:
- **Header:** the faded candle chart, icon, name and ticker, "Open in TradingView", chips (time frame, market, key), price, Buy or Download, New tab, favourite.
- **Time-frame reminder:** "In TradingView, set the chart's time frame to {tf}".
- **Overfitting box.**
- **Backtest vs. since release:** two bars and the grade.
- **Versions:** v2, with "Update available" only for owners of v1, and v1 with its release date.
- **Both charts** at full size, next to all 14 results.
- **About the indicator,** with a link to it on TradingView.
- **Pine Script preview:** the real `pine_path_shadow` preview file, faded out, with "The full script is delivered after purchase".

## 5. Flows

- **Free download:** a dialog asks for an email. Getting news is a separate box, unticked by default (GDPR). The server emails the link. An empty or invalid email shows the core texts `errEmailRequired` / `errEmailInvalid` under the field, and Enter sends. Asking again for the same strategy restarts its link.
- **Trust row under Checkout** (Lite floating cart and Pro cart strip): `trustPaypal` (PayPal: we never see your card), `trustLinks` (Links: 7 days, 10 downloads), `trustInvoice` (Invoice by email) and a `mailto:sales@tuisku.eu` link. 11.5px, `#5a6b80`, icons `#0950e3`; it wraps on phones and the email stays LTR in Arabic. The texts are already in `i18n/storefront.ui.json` for all 8 languages.
- **One payment per strategy.** Adding a bundle or the custom pack removes its strategies from the cart as single items, and also any other bundle that shares a strategy with it. `/api/quote` applies the same rule (to confirm).
- **"Buy to unlock"** in How it decides only adds the strategy to the cart (never removes it); on a free strategy it opens the free download.
- **Checkout → thank-you page:** order number, total and PayPal; "Download all" and one `.pine` per item; a note on how long links last; the 5-step install tutorial (§11).
- **My strategies** (requires an account through the core's shared login):
  - every item bought or downloaded, with how long its link has left;
  - "Get a new link" when a link has expired (it restarts the 7 days and 10 downloads, and keeps the purchase date, order and version), and "Get the update · v2" when a newer version exists;
  - `.pine`, `.zip` and the Fact sheet / How it decides links on every row, as on the thank-you page;
  - **favourites** with alert toggles: new version, price drop, in a bundle.
- **Welcome tour** (core tour, 0.13): 3 steps, once per account, with mode-specific text in step 1. "View tutorial" reopens it.

## 6. Server and data work

| Feature | Needs |
|---|---|
| Paged catalogue | `GET /api/strategies?filters…&sort&page&size=24`, with filtering and sorting on the server and histogram bins in the response. Stop downloading the whole CSV in the browser. |
| Prices, bundles, custom pack | Prices stay on the server: the bundle catalogue and its prices, the custom pack price (5 for $249 in the mock), and a decision on whether tier discounts stack with bundles (the 70% cap still applies). `/api/quote` has to accept bundles. |
| Since release (example figures in the mock) | A daily job that runs each strategy forward on market data from its release date and stores the % result. |
| Grade | Computed from `Total Closed Trades`; agree the cut-offs. |
| Versions and updates | `version`, `released_at` and changelog per strategy. Buyers keep their version, and paid updates can be sold as a yearly plan. |
| Favourites and alerts | Tables tied to the account and an email job. Alerts are opt-in. |
| Free-for-email | An email table with consent timestamp and opt-in; the email with the link; a signed token, as for paid downloads. |
| Local currency (rates are examples) | Daily FX rates on the server. Show prices as "≈ amount", and always charge USD through PayPal. |
| New this month | `released_at` is within the last 30 days. |
| Strategy page preview | Serve the existing `pine_TW_hide` previews. The full script never goes to the browser. |

## 7. Translations

- **Tool texts:** `storefront/i18n/storefront.ui.json`, 160+ keys in es, en, pt, fr, de, zh, ar, hi.
- **Shared texts:** taken from `zlecitool_core/i18n/common.json` and never repeated in the tool file: language, legal links, contact, Free, buy, email, and the tour buttons.
- **Placeholders:** `{n}`, `{p}`, `{amount}`, `{e}`, `{tf}`, `{date}`, `{id}`, `{price}`, `{from}`, `{to}`, `{total}`.
- **Review needed:** native speakers should check zh, ar and hi.
- **Catalogue text:** indicator names and descriptions come from `catalogue/indicators.csv` in English only. Plan translations for them if needed.

## 8. Acceptance checklist

- [ ] The trust row shows under Checkout in Lite and Pro, in all 8 languages.
- [ ] Every flow in `docs/USER-FLOW-v7.md` behaves as described, including the fixes in its §18.
- [ ] Each strategy is paid once: bundles and the pack never overlap in one quote.
- [ ] Back, Forward and reload keep the strategy page and its tab.
- [ ] On a 390px phone the floating cart, the compare pill and the bottom bar don't overlap.
- [ ] Lite is the default, and Pro and the language are remembered across visits.
- [ ] Every page reflows at 390, 768, 1024 and 1366px with no clipped text. The ticker line on cards wraps, it does not cut off.
- [ ] Arabic flips the layout, the gradients, the slider directions and the ladder.
- [ ] Every slider has a histogram with visible low bins, and filters update the count, the chips and the list.
- [ ] Every strategy view links to the strategy page, and the page works in a new tab.
- [ ] The overfitting box is visible in Lite, in Pro and on the strategy page.
- [ ] No console errors and no placeholder text while loading.
- [ ] The full script never reaches the browser, and all prices come from the server.

## 9. "How it decides" (decision tree view)

Reference: the **How it decides** tab of the v7 strategy page (`#s=<id>/tree`), linked from every card, row and table row; `Strategy Tree.dc.html` is the same view on its own. All 8 sample strategies load their real preview file.

- **Data.** Parse each strategy's tree from its preview (`storefront/assets/previews/*.pine`): nested `if( feature <= value )` / `if( feature > value )` blocks ending in `ret := score // buy|sell`. Branches cut by the preview become "Paid part". The mock's `parse()` can run at publish time and write one JSON per strategy.
- **Visitors** see the free part of the first tree, with an unlock note and "Buy to unlock".
- **Owners** get the complete tree and every tree of the forest from an authenticated endpoint (never in the public JSON), plus the .pine download.
- **Explanations.** Every indicator value needs a short label and text (`feat` in `trees/previews.json`), shown when hovering or tapping a step, a slider name or a tick. Check these texts against the factory's indicator code, then translate them.
- **Interaction.** Sliders move the values; the path, the score and the "range where the result stays the same" update live. Clicking a leaf sets values that reach it.

- **Views (v7 update).** Default: the clean tree (each box asks a question about one indicator, branches are Yes / No, results are Buy / Sell / Wait with a strength bar). A switch shows the Blocks view. Hovering a result shows its rule as a sentence with range bars, and "See all rules in plain words" lists every rule under the tree. Indicator codes are shown by name (`trees/features.json`).

- **Navigation.** Clicking any box (or its Yes / No label) moves the path there and the view follows; the tree can also be dragged with the mouse. On touch screens a tap also opens the explanation.
- **Sliders.** Each track is coloured by what the strategy would do if only that value changed (green buy, red sell, grey wait; stronger colour = stronger signal). A note states that the thresholds are already optimised and fixed in the script: moving a slider simulates a market reading, it does not change the strategy.
- **Languages.** `trees/ui.json` holds the tab texts in all 8 languages and the indicator names for pt, fr, de, zh, ar and hi. Indicator descriptions exist only in es/en so far; the other languages fall back to English.
- **Mobile.** Below 640px the boxes and columns shrink; the sliders stack above the tree and the tree scrolls inside its frame.
- **Sizes (compact).** Tree: boxes 34px tall; width = the longest indicator name in that tree (Ubuntu 700, 12px) + 22px, between 132 and 200px (120–172px under 640px); 40px between columns (34px under 640px); rows 40px apart; Yes / No pills 18px tall at 10.5px, right-aligned against the child box. Question boxes have no icon: the name on one line (12px/15px, bold, blue on the current path) and the question under it (11px/14px). Result boxes: icon + verb (12.5px bold), score (11.5px) and a 4px strength bar; the reached result gets a 3px ring. Blocks: rows 42px tall; the column width fits the frame (inner width ÷ number of columns, measured inside the scroll area so the scrollbar counts), capped at 190px and at the longest name + 42px, never under 120px (112px under 640px); labels 10.5px/12px and names 12px/15px.

## 10. Script preview and formats

- **Preview.** The fact sheet shows the real preview file with syntax colours (dark editor, line numbers): lines 5–16 sharp and 17–21 blurred, then "The rest of the script is delivered after purchase".
- **What is sold** is stated under it: the complete Pine script with every tree of the forest.
- **Formats** (download from My strategies after purchase):
  - Pine Script (.pine), the product;
  - Markdown for AI (.md), the rules in plain text, which can be generated from the parsed trees;
  - Python (.py) and JavaScript (.js), both marked **Beta**: they need a converter from the Pine trees and tests that their signals match TradingView before release.


## 11. After purchase: install tutorial and downloads
- **Install tutorial.** Opens automatically the first time the thank-you page appears (`localStorage: edgefolio-install-v1`), and again from "Watch the tutorial", from each of the 5 step tiles, and from "Add it to TradingView" in My strategies. Same modal format as the welcome tour. Steps: download and copy the script → sign in to TradingView (free plan) → open the right symbol and interval (with a direct chart link) → paste in the Pine Editor and Save → Add to chart (Strategy Tester; on phones: Indicators › My scripts).
- **Images.** Steps 3 and 5 use the strategy's own TradingView screenshots (`*_candel.png`, `*_profit.png`) with highlights; steps 1, 2 and 4 are diagrams. Real screenshots of the sign-in page and the Pine Editor can replace the diagrams.
- **Navigation.** Next/Back, the dots, ←/→ and Esc, a click on the image (next) or a swipe on touch screens. Arrow and swipe directions flip in Arabic. The welcome tour now accepts the same clicks, swipes and keys.
- **Download rows.** Each purchased strategy has `.pine`, `.zip` (script, .md rules for AI, Python and JavaScript beta), and "Fact sheet" / "How it decides" links that open the strategy page in a new tab (`#s=<id>` and `#s=<id>/tree`).
- **Translations.** New keys in `i18n/storefront.ui.json` for all 8 languages: `instTourTitle`, `instWatch`, `instDone`, `instOpenTv`, `zipTitle`, `i1T`–`i5X`. TradingView button names stay in English in quotes.

## 12. Filters (Pro): exact behaviour

Filtering, sorting, paging and the histogram counts run on the server against the real catalogue. The browser only sends the query. The mock applies the same rules to its 8 sample rows.

| Filter (i18n key) | Mock field | Scale | Track |
|---|---|---|---|
| Net profit $ (`fNetProfitUsd`) | `np` | log | $200 – $6,500,000 |
| Price $ (`fPrice`) | `p` | linear | $0 – $140 |
| Net profit % (`fNetProfitPct`) | `npp` | log | 0.1 – 6,500 % |
| Closed trades (`fClosedTrades`) | `tr` | linear | 0 – 2,000 |
| Win rate % (`fWinRate`) | `w` | linear | 0 – 100 % |
| Profit factor (`fProfitFactor`) | `pf` | log | 1 – 35,000 |
| Training months (`fTrainingMonths`) | `m` | linear | 0 – 400 |
| Max loss $ (`fMaxLossUsd`) | `mdd` (max drawdown $) | linear | $0 – $40,000 |
| Max loss % (`fMaxLossPct`) | `mddp` | linear | 0 – 4 % |
| Avg profit $ (`fAvgProfitUsd`) | `avg` | log | $1 – $2,100,000 |
| Avg profit % (`fAvgProfitPct`) | `avgp` | linear | 0 – 5,000 % |
| Avg bars in trade (`fAvgBars`) | `bars` | linear | 0 – 8,000 |
| Activity (`fActivity`) | closed trades ÷ months | linear | 0 – 3 |
| Candles (`fCandles`) | bars in the backtest | linear | 0 – 500,000 |
| Precision % (`fPrecision`) | `prc` | linear | 40 – 100 % |
| Tree depth (`fTreeDepth`) | `tdep` | linear | 1 – 10 |
| Symbol (`fSymbol`) | ticker | multi-select | |
| Time frame (`fTimeframe`) | time frame | multi-select | |
| Indicators (`fIndicators`) | indicator key (1C00, 1T00…) | multi-select | |
| Index (`fIndex`) | NASDAQ, NYSE, CRYPTO | multi-select | |
| Release date (`fReleaseDate`) | release date | multi-select | |

Plus **Only FREE** (price = 0) and the **search box** (name, ticker, indicator name and key). Map each mock field to its column in `catalogue/catalogue.csv`.

- **Combining.** Filters combine with AND. Inside a multi-select, ticked options combine with OR. All ticked means no filter; none ticked gives an empty list.
- **Open ends.** A handle at the end of its track means no limit on that side, so values outside the track (for example avg profit above 5,000 %) still pass.
- **Log tracks.** Handle position f (0–1) maps to 10^(log10(min) + f × (log10(max) − log10(min))).
- **Typed min / max.** The two boxes under every slider accept typing. The value applies on Enter or when the box loses focus. It accepts the locale's separators and the $ and % signs, is clamped to the track, and min never passes max.
- **Histograms.** Bins on the same scale as the track: 36 for net profit $ and price, 32 for the others, 10 for tree depth. Bins inside the range are full colour, the rest 25 % opacity, and hovering a bin shows its count. The mock counts every strategy. The server should count the strategies that pass every other filter, so the bins match what the user will get.
- **Feedback.** The count at the top of the panel, one chip per active filter (with ×), Reset filters / Clear all, the list and the pager ("1–N of N", 25 per page) update together.
- **API.** `GET /api/strategies?q=&free=1&sort=np|win|price|trades|npp|avg|months&page=1&size=25`, ranges as `np_min` / `np_max` (omit for an open end), multi-selects as repeated params (`sym=AAPL&sym=NVDA`, or `sym=` for none). Response: `{ total, rows, hist: { np: [...], ... }, options: { sym: [{ v, label, count }], ... } }`.
- **Sample values in the mock.** Profit factor, max loss $ and %, avg profit % and avg bars for AMZN 1T00, ADBE 1T00, AAPL 1C00 and NVDA 1M00 are examples, as are precision and tree depth for all 8. Activity is trades ÷ months, and candles are months × 21 (stocks) or × 30.4 (crypto).
