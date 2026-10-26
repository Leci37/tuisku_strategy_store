# Edgefolio · API

What the shop's server receives and answers, read from the code on branch `_ztool_dev` on 12 Oct 2026, and checked again on 26 Oct 2026, after the fixes of the browser walk of 25 and 26 Oct.

- **Repository:** `Leci37/tuisku_strategy_store`. It was renamed from `tuisku_Web_selling`, and the old name still redirects. It runs on zlecitool-core 0.31.1, with the catalogue of 2026-10: 143 strategies (133 paid, 10 free), all released on 13 Oct 2026.
- **Code:**
  - Routes: `edgefolio/routes.py`.
  - The work, in the modules next to it: `search`, `catalogue`, `pricing`, `orders`, `paypal`, `downloads`, `free`, `mine`, `proofs`, `media`, `alerts`.
  - The page's calls: `static/js/app.js`, through `static/js/lib/api.js`.
- The numbers (#1–#22) are the ones `docs/FLUJO_USUARIO.md` and `docs/API_ENDPOINTS.md` use. `docs/API_ENDPOINTS.md` (in Spanish) groups the same calls by screen.

## Rules for every request

- **Session:**
  - Every route needs a session unless it is marked public (`@public`).
  - Without a session, the core sends a browser to `/login?next=<path>`, and answers a script with `401 {"error": "errLoginRequired"}`.
- **CSRF:** the core's `csrf.js` adds the token to every POST, PUT and DELETE the page sends.
- **Bodies:** a body must be a JSON object. Anything else gets `400 {"error": "errRequest", "field": "body"}`.
- **Errors:**
  - A refusal is `{"error": "<key>"}`. The key is a text in the dictionary, so the page can show it translated.
  - It carries extras when needed: `field` (the parameter at fault), `vars` (values for the text), `items`, `bundles`, `item`, `detail` and `paid`.
  - The page shows the text as a toast, or under the field for email errors.
  - With no answer at all (offline), the page shows `errShopNetwork`.
  - If the key isn't in the dictionary, the page picks one by status:

    | Status | Key shown |
    |---|---|
    | 402 | `errPayment` |
    | 404 or 410 | `errLinkNotFound` |
    | 429 | `errTooMany` |
    | 5xx | `errLater` |
    | any other | `errRequest` |
- **Ids:**
  - A strategy id is `TICKER_INTERVAL_KEY_HASH`, for example `SNOW_1Day_1BOL_7abec5de`.
  - Orders and download links store the strategy's key instead: `TICKER - INTERVAL - KEY - HASH`.
  - Every endpoint that takes an id also accepts that key, and the base64 alias the old shop used.
- **Money:**
  - Always in USD.
  - Quotes and receipts send amounts as strings with two decimals (`"154.05"`). Strategy rows and bundles send numbers.
- **Prices come from the server:**
  - The page only sends ids, bundle keys, the pack and the code the user typed; it never computes a price.
  - No valid discount code is ever sent to the page.

## Pages

Every page uses the same template: `templates/edgefolio/shop.html`, inside the core's `zt/base.html`. The page reads the path in the browser and shows the right screen.

| Path | Access | What the server does |
|---|---|---|
| `/` | public | The shop |
| `/s/<id>` | public | Strategy page. An unknown id → `302` to `/`. An alias or a key → `301` to `/s/<id>`. The tab title names the strategy («Snowflake · SNOW · 1BOL · 1Day · Edgefolio»), also in `og:title` for link previews. |
| `/s/<id>/tree` | public | The same, on the "How it decides" tab; the title adds «Cómo decide» (in the page's language) before «Edgefolio» |
| `/thanks` | public | Thank-you page. PayPal returns here with `?token=<order id>`. |
| `/mine` | session | My strategies. Without a session, the core sends the browser to `/login?next=/mine`. |

The page reads these query parameters, then removes them from the address bar:

| Parameter | Comes from | What the page shows |
|---|---|---|
| `/?checkout=cancel` | PayPal, when the user cancels | The shop, with the cart unchanged |
| `?link=<error key>` | A download link opened in the tab that no longer works | The reason, as a toast |
| `/?news=confirmed` or `/?news=expired` | The news confirmation link (#13) | A notice |
| `/mine?proof=<token>` | The link that proves an email (#18), signed in only | The confirm step |

The old `#s=<id>` and `#s=<id>/tree` addresses still open the strategy page. Any other path, and a trailing slash (`/mine/`, `/s/<id>/`), gets the core's 404 page.

## Endpoints

| # | Method and path | Access | What for | Called by the page |
|---|---|---|---|---|
| 1 | `GET /api/config` | public | Settings for prices and limits | On load |
| 2 | `GET /api/strategies` | public | Filtered, sorted, paged list, with optional histograms and counts | Ticker tape (every page), Lite, Pro, pack picker |
| 3 | `GET /api/strategies/<id>` | public | One strategy, full record | Strategy page; any strategy the page names but hasn't loaded |
| 4 | `GET /api/bundles` | public | Bundles and the custom pack offer | On load |
| 5 | `GET /api/fx` | public | Exchange rates for the «≈» prices | On load |
| 6 | `GET /thumbs/<stem>.webp` | public | Chart thumbnails | Card and table images |
| 7 | `POST /api/quote` | public | The price of a cart | Every change to the cart |
| 8 | `POST /api/orders` | public | Create the PayPal order | Checkout |
| 9 | `POST /api/orders/<paypal_id>/capture` | public | Take the payment and get the receipt | `/thanks?token=…` |
| 10 | `GET /api/download/<token>` | public (the token is the key) | One script, as `.pine` or `.zip` | Thank you, My strategies, emails |
| 11 | `GET /api/download/all?t=…` | public | Several `.pine` files in one zip | Thank you, "Download all" |
| 12 | `POST /api/free` | public | A free strategy by email | Free dialog |
| 13 | `GET /api/news/confirm?token=…` | public | Confirm the news opt-in | Link in the email |
| 14 | `GET /api/me` | public | Who is signed in | On load, when the page came with a session |
| 15 | `GET /api/mine` | session | Purchases, free downloads and favourites | My strategies; once, quietly, on a strategy page |
| 16 | `POST /api/mine/renew` | session | A new download link | "Get a new link", "Get the update" |
| 17 | `GET /api/mine/<id>/script` | session | The owner's full script | Owner view of the tree |
| 18 | `POST /api/mine/proofs` | session | Email a link that proves an address | «¿Compraste sin cuenta?» |
| 19 | `POST /api/mine/proofs/peek` | session | Which address a proof link belongs to | Opening `/mine?proof=…` |
| 20 | `POST /api/mine/proofs/confirm` | session | Confirm the address | The confirm button |
| 21 | `PUT /api/favourites/<id>` | session | Add or update a favourite and its alerts | Heart, alert switches, sign-in |
| 22 | `DELETE /api/favourites/<id>` | session | Remove a favourite | Heart |

---

### 1 · GET /api/config

```json
{"mode": "fake", "currency": "USD", "max_discount": "0.70",
 "tiers": [{"over": "2500", "rate": "0.70"}, {"over": "1000", "rate": "0.40"}, {"over": "500", "rate": "0.25"},
           {"over": "290", "rate": "0.20"}, {"over": "160", "rate": "0.15"}],
 "pack": {"size": 5, "price": "249"}, "download_days": 7, "max_downloads": 10,
 "new_days": 30, "contact_email": "sales@tuisku.ai", "strategies": 143, "npp_max": 0.44}
```

- `mode` is `fake`, `sandbox` or `live`.
- `strategies` is the number of strategies in the catalogue.
- `npp_max` is the catalogue's best backtest net profit % (`null` if no strategy has one). The strategy page measures its two bars, «Backtest» and «Desde su publicación», against it (capped at 100 %), not against the design's 100 %: the 2026-10 backtests are 0.03–0.44 %. Without it, the page uses 100.
- The response never contains a secret or a discount code.

### 2 · GET /api/strategies

**Parameters** (all optional):

| Parameter | Values | Meaning |
|---|---|---|
| `q` | Text, up to 100 characters | Searches the name, ticker, indicator name and key. Case and outer spaces don't matter; a partial match counts. The page's search boxes take 100 characters, and every query cuts at 100. |
| `tab` | `hot`, `win`, `stocks`, `crypto`, `new`, `free` | The Lite tabs. `new` means released in the last `NEW_DAYS` days: today all 143 (released 13 Oct 2026), until 12 Nov 2026. |
| `sort` | `np`, `npp`, `win`, `price`, `trades`, `avg`, `months`, `hot` | Always highest first. `hot` sorts by net profit %, with tickers taking turns (each ticker's best first). |
| `free`, `paid` | `1`, `true`, `yes` or `on` (`0`, `false`, `no`, `off` or empty for no) | Only free, or only paid, strategies |
| `<range>_min`, `<range>_max` | A number | A range filter; either end can be left out. The range keys are in the next table. |
| `sym`, `tf`, `ind`, `idx`, `rel` | Repeated, for example `sym=ADBE&sym=AMD` | Symbol, timeframe, indicator key, index and release date |
| `facets` | Flag | Also return the histograms, the bar scales and the option counts |
| `page` | 1 or more (default 1) | — |
| `size` | 1 to 100 (default 25) | — |

**How filters combine:**
- The options ticked within one dropdown combine with OR; separate filters combine with AND.
- A dropdown sent with only empty values (`sym=`) means nothing is ticked, so no rows match.
- Without `sort`, the order is `win` for `tab=win`, `hot` for any other tab, and `np` with no tab.
- Each range bound is widened by one millionth, so a typed «200 $» still keeps a row of 199.9999 $.

**Range keys:**

Each bar runs from its column's minimum to its maximum in the loaded catalogue, rounded outward to a round number (`edgefolio/search.py`, `track()`): on a linear bar, to the power of ten just below the spread; on a log bar, to 1-2-5 values. A bar is logarithmic only where the design asks for log (the «Log» column) and all its values are positive and span more than 100×. The design's bars (§12, made for the 2024 catalogue) are kept only for a column with no values at all, and in `static/js/lib/filters.js` until the page's first answer. The histograms are counted on the served bars.

| Key | Field | Log | Bars | Design's bar (fallback) | Bar with the 2026-10 catalogue |
|---|---|---|---|---|---|
| `np` | Net profit ($) | yes | 36 | 200 – 6,500,000 | 0 – 5,000, linear |
| `price` | Price ($) | no | 36 | 0 – 140 | 0 – 80 |
| `npp` | Net profit (%) | yes | 32 | 0.1 – 6,500 | 0 – 0.5, linear |
| `trades` | Closed trades | no | 32 | 0 – 2,000 | 0 – 70 |
| `win` | Win rate (%) | no | 32 | 0 – 100 | 30 – 100 |
| `pf` | Profit factor | yes | 32 | 1 – 35,000 | 1 – 200, log |
| `months` | Training (months) | no | 32 | 0 – 400 | 10 – 80 |
| `mlu` | Max loss ($) | no | 32 | 0 – 40,000 | 0 – 5,000 |
| `mlp` | Max loss (%) | no | 32 | 0 – 4 | 0 – 0.5 |
| `avg` | Average profit ($) | yes | 32 | 1 – 2,100,000 | 0 – 500, linear |
| `avgp` | Average profit (%) | no | 32 | 0 – 5,000 | 0 – 5 |
| `bars` | Average bars per trade | no | 32 | 0 – 8,000 | 0 – 30 |
| `act` | Trades per candle of the backtest (`Trade Activity Per Candle`) | no | 32 | 0 – 3 | 0 – 0.3 |
| `candles` | Number of candles | no | 32 | 0 – 500,000 | 0 – 50,000 |
| `prec` | Precision f1 (%) | no | 32 | 40 – 100 | 40 – 90 |
| `tree` | Tree depth | no | 10 | 1 – 10 | 5 – 6 |

A strategy with no value in a column (SPOT 1Day 1FIB has no profit factor) never passes an active range on it. The page sends each bound with the decimals its label shows: up to two for the profit factor and average profit (%) under 10, up to three for the activity.

**Response:**

```json
{"total": 143, "page": 1, "size": 25, "rows": [ROW, "…"], "counts": {"all": 143, "new": 143},
 "hist": {"np": [0, 1, 0, 3, "…"]},
 "ranges": {"np": {"min": 0, "max": 5000, "log": false, "bins": 36}},
 "options": {"sym": [{"v": "SNOW", "label": "Snowflake (SNOW)", "count": 2, "icon": "/static/assets/icons/SNOW_big.svg"}]}}
```

- `ROW` is a strategy row (described below).
- `hist`, `ranges` and `options` come only with `facets=1`, with one entry for every range and dropdown key.
- Each histogram and option count applies every filter except its own. The panel therefore shows what the user would get by changing that filter.

**Errors:** `400 errRequest`, with `field` naming the bad parameter: `q`, `tab`, `sort`, `page`, `size`, a flag, a `_min` or `_max` that isn't a finite number, or a dropdown value longer than 200 characters.

**How the page calls it:**
- **Ticker tape:** `paid=1&sort=hot&size=12`.
- **Lite:** `tab=<tab>&q=<search>&size=24&page=<n>`. "Load more" asks for the next page.
- **Pro:** every active filter, plus `size=25&page=<n>`. It adds `facets=1` whenever the filters, the sort or the search change; another page of the same query goes without it.
  - Until the first facets answer, the min/max boxes of open ends are empty; a value typed or dragged before it keeps its value when the served bar arrives.
  - In the Table view, each page replaces the list.
  - In the Rows and Cards views, "Load more" adds the next page.
- **Pack picker:** `paid=1&sort=hot&size=40&q=<search>`.
- The page waits 150 ms after the last change before asking, and uses only the newest answer.
- Pressing the Lite tab that is already marked asks for its first page again (a retry after a failure).

### The strategy row

Lists, the strategy record, receipts and My strategies all use the same row:

| Field | Meaning |
|---|---|
| `id`, `ticker`, `interval`, `key`, `hash` | Who it is |
| `name`, `ind`, `index`, `market` | Company or coin name, indicator name, index, and `stocks` or `crypto` |
| `price` | USD, as a number; 0 means free |
| `np`, `npp` | Net profit, in $ and % |
| `tr`, `w` | Closed trades; win rate (%) |
| `pf` | Profit factor |
| `mdd`, `mddp` | Max loss, in $ and % |
| `avg`, `avgp` | Average profit, in $ and % |
| `bars` | Average bars per trade |
| `m`, `cand` | Months trained; number of candles |
| `prc`, `tdep` | Precision f1 (%); tree depth |
| `actv` | Trades per candle of the backtest: the catalogue's `Trade Activity Per Candle` column (0.002–0.238 in 2026-10); `null` when empty |
| `release` | Release date, `YYYY-MM-DD` |
| `version` | 1 if the catalogue gives none |
| `is_new` | Released in the last `NEW_DAYS` days |
| `grade` | A with 300 trades or more, B with 100 or more, C with 30 or more, otherwise D. With the 2026-10 catalogue (5–63 trades), 35 are C and 108 D; the cut-offs are the owner's to settle |
| `live`, `live_as_of` | Result in % since release, and its date. Both are `null` until a daily file exists. |
| `profit`, `candle` | Chart images (PNG), under `/static/assets/charts/` |
| `icon` | Icon image, under `/static/assets/icons/` |
| `preview` | The cut Pine preview, under `/static/assets/previews/` |
| `thumb_profit`, `thumb_candle` | Thumbnails of the two charts: `/thumbs/<stem>.webp` |
| `tv_symbol` | The TradingView symbol: `NYSE:SNOW`, or `BINANCE:BTCUSDT` for crypto |
| `file` | `Tuisku_<id>`, the script's name in TradingView |
| `ind_text`, `ind_url` | The indicator's explanation (English only, from `catalogue/indicators.csv`; the page marks it `lang="en"`) and its TradingView page. Only in lists and the full record. The 68 strategies with a combined indicator (keys starting with 2) link to `https://www.tradingview.com/scripts/`. |

Any missing number is `null`.

### 3 · GET /api/strategies/<id>

- **Answers:** the row, plus:
  - `ind_author` (the page doesn't show it);
  - `versions`: `[{"v": 1, "date": "2026-10-13", "note": ""}]`, from the current version down to 1. Only the current version has a date, and no version has a note. All 143 strategies are at version 1 today.
- **Errors:** `404 errUnknownStrategy`.
- **When the page asks:**
  - for the strategy page;
  - for any strategy it names but hasn't loaded yet: the cart, the pack, compare, favourites, bundle contents, the free dialog and the install tutorial.
- **What the page does with the answer:**
  - If it asked by alias, it switches to the real id.
  - On a 404, it removes the id from the cart, compare and favourites. On the strategy page it also shows the error and goes to the shop.

### 4 · GET /api/bundles

```json
{"bundles": [{"key": "top5", "name_key": "bundleTop", "ids": ["…"], "price": 249.0, "was": 395.0}],
 "pack": {"size": 5, "price": 249.0, "was": 395.0}}
```

- The bundles come from `catalogue/bundles.json`.
  - A bundle's `was` is the sum of its strategies' prices.
  - A bundle that lost a strategy, or that doesn't cost less than its strategies, is left out entirely and logged.
- The pack's `was` is 5 × the median price of the paid strategies. The custom pack card shows it before any strategy is chosen.

### 5 · GET /api/fx

```json
{"base": "USD", "date": "2026-10-11", "rates": {"USD": 1, "EUR": 0.92, "INR": 83.5, "CNY": 7.2, "SAR": 3.75},
 "source": "ECB via frankfurter.app"}
```

- **Where the rates come from:**
  - today's rates, if `fx-update` has run;
  - otherwise the repository's example rates (`"source": "example"`);
  - if neither can be read, only USD (`"source": "none"`).
- The rates are only for showing «≈» prices; PayPal always charges USD.
- If the call fails, the page shows prices in USD.

### 6 · GET /thumbs/<stem>.webp

- `stem` must name a chart in `static/assets/charts/`. Otherwise: `404 {"error": "errNotFound"}`.
- The first request makes a 640 px WebP (quality 80) in the data folder. It is made again when the chart is newer.
- It is sent with `Cache-Control: public, max-age=31536000, immutable`.
- If Pillow isn't installed: `307` to the PNG.

### 7 · POST /api/quote

**Request:**

```json
{"items": ["UPST_1Day_1ULT_aae26f99", "UBER_1Hour_2MM0_bf5c384c"], "bundles": ["crypto"], "pack": ["id1", "id2", "id3", "id4", "id5"], "code": "demo20"}
```

- **Limits:** up to 500 items, 50 bundles and 50 pack ids; each id up to 200 characters; the code up to 64.
- Every field is optional, but at least one of `items`, `bundles` or `pack` must have something in it.

**Response** (the «Inicio en cripto» bundle at $119 and two strategies at $59, a 20 % code):

```json
{"items": [{"id": "UPST_1Day_1ULT_aae26f99", "price": "38.35"}, {"id": "UBER_1Hour_2MM0_bf5c384c", "price": "38.35"}],
 "bundles": [{"key": "crypto", "price": "77.35"}], "pack": null,
 "subtotal": "237.00", "tier_rate": "0.15", "code_rate": "0.20", "discount_rate": "0.35",
 "discount": "82.95", "total": "154.05", "code_status": "applied",
 "tier_index": 1, "next_tier": {"over": "290", "rate": "0.20", "missing": "53.01"}}
```

- **Line prices:** each line's `price` is what this cart pays for it, after discounts.
- **With a pack:** `pack` is `{"ids", "price", "was", "save"}`.
  - `was` is the price of its strategies bought separately.
  - `save` is what the pack itself saves against them (`"0"` if nothing).
- **`code_status`:**
  - `""`: no code was sent;
  - `"applied"`: the code is valid;
  - `"invalid"`: the code is not valid. There is no discount, but this is not an error.
- **`tier_rate` and `code_rate`:** what each part really takes off after the `MAX_DISCOUNT` cap, the tier first and the code what is left. Below the cap they add up to the configured rates (0.15 + 0.20). At the 70 % tier with a 20 % code, `code_rate` is `"0.00"`; when a lower tier plus the code passes 70 %, it is only the part left. Without a code, or with an invalid one, `"0"`. Their sum is always `discount_rate`.
- **`next_tier`:** `null` when there is no higher tier.

**How the server prices the cart:**
1. Each strategy and each bundle counts once, however many times it is sent.
2. A strategy that is also in a chosen bundle or in the pack isn't charged on its own.
3. The pack:
   - It must be exactly `PACK_SIZE` different paid strategies; otherwise `400 errPackSize`, with `vars.n`.
   - It costs `PACK_PRICE`, or the sum of its strategies' prices if that is lower.
4. Two chosen bundles, or a bundle and the pack, that share a strategy are refused: `400 errBundleOverlap`, with the shared ids in `items`.
   - The server never chooses between them. The page removes the older bundle before asking.
5. The subtotal adds up the single strategies, the bundles and the pack, at their list prices.
6. **Flat-price code** (`FLAT_PRICE_CODES`):
   - Each single strategy is charged that price, or its own price if lower.
   - Bundles and the pack keep their price, and there is no tier discount.
7. **Any other code** adds to the tier discount:
   - The tier is the highest one the subtotal is strictly above. A subtotal of exactly $160 still gets 0 %.
   - The code's rate (`DISCOUNT_CODES`) is added, and the sum is capped at `MAX_DISCOUNT` (70 %). The quote reports each part after the cap (`tier_rate`, `code_rate`).
   - Every line and the total are multiplied by (1 − rate) and rounded half up to the cent, so the total never reaches 0.
8. `next_tier.missing` is what the cart still needs to pass the next tier: the difference plus one cent.
9. Codes are trimmed and compared in lower case.

**Errors (400):**

| Key | When | Extra |
|---|---|---|
| `errRequest` | A field has the wrong type or is too long | `field` |
| `errUnknownItems` | Some ids aren't in the catalogue | `items` |
| `errUnknownBundles` | Some bundle keys don't exist | `bundles` |
| `errPackSize` | The pack isn't exactly 5 different paid strategies | `vars.n` |
| `errBundleOverlap` | Two bundles, or a bundle and the pack, share a strategy | `items` |
| `errCartEmpty` | Nothing in `items`, `bundles` or `pack` | — |

**How the page uses it:**
- It asks 120 ms after any change to the cart, the bundles, the pack or the applied code, and uses only the newest answer.
- It sends the pack only once all 5 strategies are chosen.
- It sends the code only after the user presses «Aplicar» or Enter (not while an input method is composing).
  - `applied` shows «Código de descuento aplicado».
  - `invalid` shows «Código no válido: sin descuento», and the code stops applying (its text stays in the box).
  - Pro's ladder adds «+ N % con el código» only when `code_rate` is above 0.
- On `errUnknownItems` or `errUnknownBundles`, it quietly removes those from the cart; an old cart can have them. Any other refusal is a toast.

### 8 · POST /api/orders

**Request:** the same body as #7.

**What the server does:**
1. Prices the cart again, with the same rules and errors as #7. A total of 0 or less → `400 errNothingToPay`.
2. Creates a PayPal order (Orders v2, `intent: CAPTURE`) for the server's total, in USD.
   - It sets `brand_name: Edgefolio`, `PAY_NOW` and `NO_SHIPPING`.
   - PayPal returns the user to `<public URL>/thanks`, or to `<public URL>/?checkout=cancel` if they cancel.
   - Without `ZLECITOOL_PUBLIC_URL`: `503 errLater`.
   - If PayPal fails: `502 errPayPal`, with `detail`.
3. Saves the order as `CREATED`, with:
   - the strategies' keys;
   - the code, if it applied;
   - the total, currency and lines;
   - the account, if signed in;
   - the hash of the buyer cookie.
4. Sets the cookie `edgefolio_buyer`: a random token, for 30 days, HttpOnly, SameSite=Lax and Secure. A browser keeps the same token for its next orders.

**Response:**

```json
{"id": "5O190127TN364715T", "approve_url": "https://www.paypal.com/checkoutnow?token=…", "…": "the quote"}
```

**How the page uses it:**
- It sends one order at a time, so «Pagar» stays busy and a double click doesn't make two orders.
- It then goes to `approve_url`. Coming back with the browser's Back button frees the button.

**With `PAYPAL_MODE=fake`** (local work and tests), `approve_url` is `<public URL>/thanks?token=FAKE-…&PayerID=FAKE`, and the capture always succeeds.

The server never checks whether a signed-in account already owns a strategy it quotes or orders: it is charged again. The strategy page and the tree say «Ya es tuya» instead of selling it, but Lite's and Pro's cards still add it to the cart (see «Points to check»).

### 9 · POST /api/orders/<paypal_id>/capture

**Request:** no body.

**What the server does:**
1. An unknown order → `404 errUnknownOrder`.
2. An order that is already paid → the same receipt again. Nothing is charged twice.
3. An order placed by an account that has since been deleted (core 0.30, «Mis datos») → `409 errAccountClosed`. Nothing is charged; PayPal lets the approval lapse.
4. Takes the payment in PayPal. If PayPal fails → `502 errPayPal`.
5. If PayPal's status isn't `COMPLETED`, or the amount or currency differ from the order, the order becomes `FAILED` → `402 errPayment`. `paid` says what PayPal reported.
6. Marks the order `PAID`, only once, even if two captures arrive at the same time.
   - For a buyer without an account, it also stores the PayPal payer's email on the order. An account can prove that address later (#18–#20).
7. On that first change to `PAID`, it emails a receipt, in the page's language, to the account's email or the PayPal email. The receipt has:
   - each line with its price;
   - the total;
   - the link to My strategies;
   - the link limits;
   - the contact address.

   Amounts are written `47.45 USD` in every language: the core has no server-side money formatter yet (`CAMBIOS.md`, «Para el núcleo» 8). Without `ZLECITOOL_PUBLIC_URL`, the email is skipped and logged; the payment still stands.
8. Gives every strategy one download link (7 days, 10 downloads) if the order doesn't have one yet. Asking again returns the newest link of each.

**Response:**

```json
{"order_id": "5O190127TN364715T", "status": "PAID", "total": "154.05", "currency": "USD",
 "payer": "a•••@example.com", "valid_days": 7, "max_downloads": 10, "links_hidden": false,
 "download_all": "/api/download/all?t=…&t=…", "paid_now": true,
 "downloads": [{"id": "…", "…": "the rest of ROW", "url": "/api/download/<token>", "zip": "/api/download/<token>?format=zip"}]}
```

- **`paid_now`:** `true` only on the capture that changed the order to `PAID` (the one that emails the receipt). Any later capture, from this browser or another, gives `false`.
- `payer` is the PayPal payer's address, masked; the page doesn't show it.
- `downloads` holds one entry per strategy, the strategies of a bundle or the pack included.

**Who sees the links:**
- the browser that placed the order (its `edgefolio_buyer` cookie);
- the account that placed it while signed in;
- an account that has proven the order's email or the PayPal email.

Anyone else gets `links_hidden: true`, `downloads: []` and `download_all: null`.

**How the page uses it:**
- It takes `token` from `/thanks?token=…`. Without a token, it goes to the shop.
- It empties this browser's cart (strategies, bundles, own pack; the applied code stays) only when `paid_now` is true, so reopening an old thank-you page, or someone else's, leaves the cart alone.
- With the links shown, it opens the install tutorial until it has been closed once (`edgefolio-install-v1`). With the links hidden, there is no install block and no tutorial.
- On an error, it shows a toast and goes back to the shop.

### 10 · GET /api/download/<token>[?format=zip]

**What it sends:**
- Without `format`, or with any value other than `zip`: the full `.pine`, as `text/plain`, named `Tuisku_<id>.pine`.
- With `format=zip`: `Tuisku_<id>.zip`, which holds:
  - the `.pine`;
  - the rules, as `.md`;
  - the `.py` and `.js` beta versions;
  - a `README.txt`.
- Both are sent with `Content-Disposition: attachment` and `Cache-Control: private, no-store`.

**How downloads are counted:**
- Each request uses up one of the link's 10 downloads, before anything is sent. If two requests race for the last download, only one gets it.
- A zip counts as one download.
- The token can be a paid link, whose order must be `PAID`, or a free claim.

**Errors:**

| Status | Key | When |
|---|---|---|
| 404 | `errLinkNotFound` | The token is unknown, or its order isn't paid |
| 410 | `errLinkExpired` | The link is past its date (`vars.e` = the contact email) |
| 429 | `errDownloadLimit` | All 10 downloads are used up |
| 404 | `errStrategyGone` | The strategy has left the catalogue |
| 404 | `errFileMissing` | The script isn't on the server (`item`) |

When the link is opened in a tab (a click, or a link in an email) rather than by a script, a refusal becomes a `303` redirect:
- to `/mine?link=<key>` for a signed-in user;
- otherwise to `/?link=<key>`.

The page then shows the reason, and My strategies offers a new link.

### 11 · GET /api/download/all?t=<token>&t=<token>…

- Takes up to 100 tokens; duplicates are ignored.
- Sends the `.pine` of every valid link in `edgefolio-strategies.zip`. Each file sent uses one download of its link.
- If two links lead to the same script, it is sent, and counted, once.
- Invalid links are skipped, with no notice. If none is valid, the answer is the first refusal, as in #10, with the same redirect when opened in a tab.

### 12 · POST /api/free

**Request:**

```json
{"id": "NVDA_1Day_1S00_…", "email": "ana@example.com", "news": false}
```

**What the server checks, in this order:**
1. The strategy:
   - an unknown strategy → `400 errUnknownStrategy`;
   - a strategy that isn't free → `400 errNotFree`.
2. The email → `400 errEmailInvalid`, with `field: "email"`. The address is trimmed and lowercased, and must:
   - have exactly one `@`;
   - have no spaces, and none of `, ; < > ( ) " [ ] : \`;
   - be 254 characters or fewer;
   - pass the core's rule.
3. `news` must be `true` or `false` → otherwise `400 errRequest`, with `field: "news"`.
4. Per IP address, 20 requests an hour → `429 errTooMany`.
5. The script isn't on the server → `404 errFileMissing`. There's no public URL → `503 errLater`. Nothing is stored in either case.
6. Per email address, 10 free strategies a day → `429 errFreeDaily`.

**What it does next:**
1. Stores the claim with its own link (7 days, 10 downloads). The claim records:
   - the address and the strategy, with its version;
   - whether `news` was ticked, and the time of consent;
   - the language;
   - the account, if signed in.
2. Emails, in the page's language:
   - the `.pine` and `.zip` links;
   - the link to My strategies.
3. If `news` is ticked and the address hasn't confirmed before, the email also has a confirmation link (double opt-in). Until it is confirmed, the address waits as pending.

**Response:** `{"sent": true}`. The link is never in the response, so the address has to be real.

**How the page uses it:**
- It checks the email first, with the core's texts: `errEmailRequired` (empty) and `errEmailInvalid`.
- A server refusal about the email goes under the field; any other refusal is a toast.
- The news box starts unticked every time the dialog opens.
- A refusal about the email goes under the field; the others (`errFreeDaily`, `errTooMany`, `errFileMissing`, `errNotFree`, `errUnknownStrategy`, `errLater`) are toasts over the open dialog.
- A signed-in user sees the strategy in My strategies straight away, and the tree switches to the owner view. Otherwise it shows there only once the account proves that address (#18–#20).

### 13 · GET /api/news/confirm?token=…

- Confirms a pending news opt-in, once, within 30 days of the request.
- Redirects (`303`) to `/?news=confirmed`. A used, old or unknown token goes to `/?news=expired`.
- Only confirmed addresses are on the news list (`flask edgefolio subscribers`).

### 14 · GET /api/me

**Response:** `{"email": "ana@example.com"}`, or `{"email": null}`.

**How the page uses it:**
- It asks only when the page was served with a session.
- Once signed in, it moves the favourites kept in this browser to the account (one #21 each), then loads #15.
- A favourite the catalogue no longer has (404) is dropped from the browser, with no toast. Any other the server refuses stays in the browser for the next sign-in, with one toast.

### 15 · GET /api/mine

```json
{"email": "ana@example.com", "emails": ["ana@example.com"], "proof_needed": false,
 "items": [{"id": "…", "kind": "paid", "date": "2026-09-21", "at": "2026-09-21T10:04:00+00:00",
            "order": "5O190127TN364715T", "expires": "2026-10-15T09:00:00+00:00", "days_left": 3, "valid": true,
            "url": "/api/download/<token>", "zip": "/api/download/<token>?format=zip",
            "version": 1, "update": null, "row": "ROW"}],
 "favourites": [{"id": "…", "alerts": {"nv": true, "pd": false, "bd": false}, "row": "ROW"}]}
```

**What counts as the account's:**
- what it did while signed in;
- what was done without an account using an address the account has proven (`emails`).

Nothing is included just because it matches the account's sign-up email, which the core doesn't verify.

**The items:**
- There is one item per strategy, newest first. Strategies no longer in the catalogue are left out.
- `kind` is `paid` or `free`.
- `date`, `at` and `order` come from the first time the account got the strategy.
- `expires`, `valid`, `url`, `zip` and `version` come from the newest link.
  - `valid` means not expired and fewer than 10 downloads used.
  - `url` and `zip` are `null` when the link isn't valid.
- `update` is the catalogue's version when it is newer than the link's version; otherwise `null`.

**Other fields:** `proof_needed` is true when the account's own email isn't proven yet. `favourites` are in the order they were added.

**How the page uses it:**
- It asks on `/mine`.
- It also asks once, quietly (no toast), on a strategy page: an item for that strategy turns its buy button into «Ya es tuya · Descargar» (its `url`) or «Ya es tuya · Mis estrategias» (no valid link, or an `update`), opens the tree in the owner view, and, on a paid item with `update`, shows «Actualización disponible».
- With no items, My strategies shows no list and no «Añádela a TradingView».
- A `401` sends the user to sign in.

### 16 · POST /api/mine/renew

**Request:** `{"id": "<id>"}`. **Response:** the item, as in #15.

**What the server does:**
- If the newest link still works and there's no newer version, it returns the same item and changes nothing, so a working link's counter can't be reset.
- Otherwise it makes a new link (7 days, 0 of 10 downloads used) with the catalogue's current version:
  - **paid:** the link is added to the same order;
  - **free:** a new claim that keeps the first request's time, so it doesn't count towards the daily limit.

**Errors:** `404 errNotOwned`; `404 errUnknownStrategy`.

**Called by:** «Pedir un enlace nuevo» and «Obtener la actualización · vN».

### 17 · GET /api/mine/<id>/script

- Sends the full script as `text/plain`, with `Cache-Control: private, no-store`.
- Only to an account that owns it, through any of its links, expired or not.
- It doesn't use up a download.
- **Errors:** `404 errUnknownStrategy`, `errNotOwned` or `errFileMissing`.
- **Called by:** the tree's owner view.

### 18 · POST /api/mine/proofs

**Request:** `{"email": "ana@old-address.com"}`. Empty means the account's own email.

**Response:** always `{"sent": true}`, so it never reveals whether anything was bought with that address.

**Errors:**
- an invalid email → `400 errEmailInvalid`;
- per IP address, more than 10 requests in 10 minutes → `429 errTooMany`;
- no public URL → `503 errLater`.

**What it sends:** `<public URL>/mine?proof=<token>`, valid for 24 hours, usable once and only by this account. Nothing is sent when:
- the address is already proven;
- a link went to it less than 60 seconds ago;
- the account already has 5 addresses waiting for confirmation.

**How the page uses it:** it checks the field first, with the core's texts under it (`errEmailRequired`, `errEmailInvalid`), and a server refusal of the address goes there too; other refusals are toasts. It doesn't call #18 for an address already in #15's `emails`: it shows the notice «Ya está confirmado» (`proofProvenTitle`, `proofProvenText`) instead. Enter sends, except while an input method is composing.

### 19 · POST /api/mine/proofs/peek

**Request:** `{"token": "…"}`. **Response:** `{"email": "ana@old-address.com"}`, or `{"email": null}`.

- It doesn't use up the link, because email programs open links too.
- `null` means the link is used, expired or belongs to another account.

### 20 · POST /api/mine/proofs/confirm

**Request:** `{"token": "…"}`. **Response:** `{"email": "ana@old-address.com"}`.

- From then on, #15 includes that address's orders and free downloads.
- **Errors:** `400 errProofExpired` if the link is used, expired or belongs to another account.
- **How the page uses #19 and #20:** opening `/mine?proof=<token>` calls #19 and asks the user to confirm. Their click calls #20 and reloads the list.

### 21 · PUT /api/favourites/<id>

**Request:** `{"alerts": {"nv": true, "pd": false, "bd": false}}`. An empty body means all alerts off.
- `nv`: a new version;
- `pd`: a price drop;
- `bd`: added to a bundle.

**Response:** `{"id": "…", "alerts": {"…": "as sent"}, "row": "ROW"}`.

- It stores the account's email and the page's language, which is where, and in what language, the alerts go.
- The page changes a heart or an alert at once; if the server doesn't save it (a `401` after signing out in another tab, or any failure), it goes back to what the account has and shows the toast.
- **Errors:** `400 errRequest`, with `field` = `alerts` or `alerts.nv` (and so on); `404 errUnknownStrategy`.

### 22 · DELETE /api/favourites/<id>

**Response:** `{"id": "…", "deleted": true}`.

While signed out, the page keeps favourites and alerts in this browser (`edgefolio-favs-v1`) and moves them to the account at sign-in (#14).

---

## What the core provides

- Sign-in (`/login?next=…`): password, a link by email (0.26) and a passkey (0.31, with `ZLECITOOL_PUBLIC_URL` over https or on localhost). Sign-out (`POST /logout`) and the account menu (Mi cuenta, Créditos, Historial de créditos, Contacto, Salir).
- «Mis datos» (0.30): export and delete the account. The shop's part is `edgefolio/your_data.py`; orders are kept for tax law, without the email, the PayPal email or the buyer cookie's hash.
- The room under the page for the shop's phone bar, measured from its `data-zt-bottom` (0.28).
- The dictionary: `zt.i18nReady`, with the shop's texts and the core's.
- The language menu. A change fires `zt:language` and the page repaints; `<html lang dir>` gives the language and the direction.
- `csrf.js`, for every POST, PUT and DELETE.
- The mail sender.
- `external_url`, which builds the links in emails from `ZLECITOOL_PUBLIC_URL`, never from the Host header.

## Static files

- `/static/assets/charts/*.png`, `/static/assets/icons/*` and `/static/assets/previews/*.pine` (cut previews).
- `/static/trees/features.json` and `/static/trees/ui.json`, for the tree.
- `/static/vendor/*`: Preact, htm and Font Awesome.

## What the browser keeps (localStorage)

| Key | What |
|---|---|
| `edgefolio-cart-v1` | The cart: strategies, bundles, pack, the typed code and the applied code |
| `edgefolio-favs-v1` | Favourites and alerts, while signed out |
| `tuisku-sf-mode` | Lite or Pro |
| `tuisku-sf-pview5` | The Pro view: rows, cards or table |
| `edgefolio-tv` | The TradingView chip is on |
| `edgefolio-tour-v1` | The welcome tour has been seen |
| `edgefolio-install-v1` | The install tutorial has been seen |

The language belongs to the core.

## Commands and scheduled jobs

Each command runs as `flask --app app edgefolio <command>`.

| Command | When | What it does |
|---|---|---|
| `send-alerts` | Daily (still a cron job) | Compares each strategy's version, price and bundles with the last run. Each person gets one email listing the changes to the favourites where they have that alert on. Details below the table. |
| `fx-update` | Daily (still a cron job), after the ECB publishes (about 17:00 CET) | Fetches rates from frankfurter.app. SAR is fixed at 3.75. |
| `import <package> --scripts <dir> [--prune]` | Each catalogue release | Checks the whole package from the generator before writing anything, then copies the paid scripts to `STRATEGIES_DIR` |
| `restore-scripts` | Setup | Gets the paid scripts back from the repository's history |
| `subscribers` | As needed | Lists the confirmed news addresses |

Moving `send-alerts` and `fx-update` to the core's clock (`"schedule"` in `tool.json`) is pending, and is done when their cron goes.

**`send-alerts` details:**
- Alerts go only to addresses the account has proven in the shop (#18–#20); signing in with the core's link is not enough. Never to a deleted account (`privacy.closed`).
- The first run only takes a snapshot; it sends nothing.
- Each change is announced once.

## Configuration (environment)

| Variable | Default | What |
|---|---|---|
| `PAYPAL_MODE` | `fake` | `fake`, `sandbox` or `live` |
| `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET` | — | Needed for `sandbox` and `live` |
| `ZLECITOOL_PUBLIC_URL` | — | The shop's address. Needed for `sandbox` and `live`, and for every link in an email. |
| `STRATEGIES_DIR` | `<data>/strategies` | The paid scripts, kept private |
| `DISCOUNT_CODES` | none | `code=rate` pairs, such as `spring20=0.20,partner40=0.40` |
| `FLAT_PRICE_CODES` | none | `code=price` pairs, such as `launch=0.99` |
| `MAX_DISCOUNT` | `0.70` | The cap on the tier and code discounts together |
| `DOWNLOAD_DAYS`, `MAX_DOWNLOADS` | `7`, `10` | Per link |
| `PACK_SIZE`, `PACK_PRICE` | `5`, `249` | The custom pack |
| `NEW_DAYS` | `30` | How long a strategy counts as new |
| `CONTACT_EMAIL` | `sales@tuisku.ai` | The address shown for problems |

The tiers are set in the code (`DEFAULT_TIERS` in `edgefolio/settings.py`):

| Subtotal over | Discount |
|---|---|
| $160 | 15 % |
| $290 | 20 % |
| $500 | 25 % |
| $1,000 | 40 % |
| $2,500 | 70 % |

## Limits

| What | Limit |
|---|---|
| Download link | 7 days, 10 downloads |
| Buyer cookie | 30 days |
| Free strategies per email | 10 a day |
| Free requests per IP address | 20 an hour |
| Proof emails per IP address | 10 every 10 minutes |
| Proofs per account | 5 waiting at a time; 1 per address every 60 seconds; each link lasts 24 hours |
| Request sizes | up to 500 items, 50 bundles, 50 pack ids; ids up to 200 characters, the code up to 64, `q` up to 100; `size` up to 100; up to 100 tokens in `download/all` |

## Tables

All tables have the prefix `edgefolio_`.

| Table | What it holds |
|---|---|
| `order` | Each PayPal order: items, code, total, status, payer, email, lines, buyer cookie hash |
| `download` | Each download link of a paid order: token, expiry, count, version |
| `free_claim` | Each free strategy sent to an email, with its own link |
| `subscriber` | News opt-ins; each counts only once confirmed |
| `favourite` | An account's favourites and alerts, with the email and language for the alerts |
| `alert_state` | Each strategy as it was at the last `send-alerts` run |
| `email_proof` | Addresses an account has proven, or is proving |
| `mailbox` | One row per address the shop writes to, so per-address limits hold with several requests at once |

The buyer cookie and the confirmation links are stored only as SHA-256 hashes. Download tokens are stored as they are, because My strategies has to show them.

## Points to check

These came up while reading the code. Each one may be intended; they are listed for you to decide. The owner's open decisions are listed in «Las preguntas abiertas» of `docs/handoff/2026-10-06/CAMBIOS.md`.

1. **Free previews.** The shop cuts every public preview, the free ones too (`CAMBIOS.md`). The brief for the last export said free previews are whole.
2. **Owner's script.** #17 sends the full script to any owner without using up a download, even after their link has expired.
3. **Updates are free.** There is one script per strategy, and renewing a link (#16) gives the current version. So «Obtener la actualización» costs nothing; whether updates should be paid is still an open question in `STATUS.md`.
4. **Versions.** #3 lists versions with no notes, and with a date only for the current one. The generator doesn't send data per version yet.
5. **Since release.** `live` stays `null`, and the page shows `liveUnknown`, until something writes `catalogue/since_release.csv`. No command in this repository writes it.
6. **Invoice.** The trust row says «Factura por correo», but the server emails a receipt (lines, total and links) with no invoice number and no VAT.
7. **Limits per process.** The per-IP limits are kept in memory by each worker, and start again from zero on restart.
8. **Repository name.** The repository is now `tuisku_strategy_store`, but the export documents still say `tuisku_Web_selling`.
9. **Buying twice.** #7 and #8 don't check whether the signed-in account already owns a strategy, so it can be paid for again. Refusing it (for example with an `errAlreadyOwned`) is a business rule for the owner.

The former point 7, the activity filter computed as closed trades ÷ months trained, is fixed: `act` reads the catalogue's `Trade Activity Per Candle` column.
