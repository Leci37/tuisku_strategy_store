# Edgefolio storefront v7: user flow and expected behaviour

This file goes through the shop from the first visit to after the purchase. It lists every screen, every click, tick box and key, and what the application must do in response. The reference is `Storefront v7.dc.html` (with `Strategy Tree.dc.html` inside the "How it decides" tab). `IMPLEMENTATION-v7.md` covers how to build it; this file covers what the user sees and what must happen.

**Conventions**

- **Click → result.** Labels are the English texts, with the i18n key in `code` where it helps.
- **[Mock]** means the prototype only simulates it, and the real build must do it on the server. **[Rule]** is a business rule to keep. **[Decide]** is an open decision.
- **(fixed)** marks behaviour that was broken in the prototype and was corrected in this pass (list in §18).

---

## 0. Sample data and the prototype's starting state

The prototype has 8 strategies. In the real build they come from the catalogue.

| Id | Strategy | Market | Price | Net profit % | Win rate | Closed trades | Grade | Since release [Mock] | New |
|---|---|---|---|---|---|---|---|---|---|
| `amzn-bol` | AMZN · 1BOL Bollinger RSI Double | Stocks · NASDAQ | $79 | +71.06 % | 100 % | 91 | C | +5.2 % | |
| `amzn-t00` | AMZN · 1T00 Triple EMA | Stocks · NASDAQ | $79 | +72.20 % | 100 % | 85 | C | +7.8 % | |
| `adbe-t00` | ADBE · 1T00 Triple EMA | Stocks · NASDAQ | $79 | +78.14 % | 97.25 % | 109 | B | +6.3 % | |
| `aapl-c00` | AAPL · 1C00 Chaikin Money Flow | Stocks · NASDAQ | $79 | +85.80 % | 99.38 % | 160 | B | +9.4 % | |
| `nvda-m00` | NVDA · 1M00 Money Flow Index | Stocks · NASDAQ | $79 | +83.57 % | 97.70 % | 87 | C | +12.1 % | Yes |
| `eth-t00` | ETHUSDT · 1T00 Triple EMA | Crypto | $79 | +43.14 % | 75 % | 36 | C | +18.6 % | Yes |
| `btc-bol` | BTCUSDT · 1BOL Bollinger RSI Double | Crypto | $79 | +1.81 % | 48.28 % | 29 | D | −3.1 % | Yes |
| `nvda-s00` | NVDA · 1S00 Stochastic RSI | Stocks · NASDAQ | Free | +0.49 % | 36.67 % | 499 | A | −1.4 % | |

All of them use the 1Day time frame and were released on 27 Sep 2024. "Today" in the prototype is 5 Oct 2026.

**Starting state of the prototype, for testing only.** In the real build, the cart, pack, favourites and compare list all start empty.

- **Cart:** AMZN 1BOL, AMZN 1T00 and ADBE 1T00, with the code `DEMO20` applied.
- **Custom pack:** AAPL 1C00, NVDA 1M00 and ETHUSDT 1T00 (3 of 5).
- **Favourites:** AMZN 1BOL, with the "New version" and "Price drop" alerts on.
- **My strategies:** NVDA 1S00 (free download on 2 Oct 2026) and ETHUSDT 1T00 (bought on 21 Sep 2026, order EF-48213).
- **Settings:** TradingView chip "Connected"; language English; currency "local".

---

## 1. Arriving at the site

| URL (prototype) | URL (real build) | Opens |
|---|---|---|
| `Storefront v7.dc.html` | `/` | The shop, in the remembered mode (Lite by default) |
| `#s=<id>` | `/s/<id>` | The strategy page, Fact sheet tab |
| `#s=<id>/tree` | `/s/<id>/tree` | The strategy page, How it decides tab |

What happens on load, in order:

1. The remembered settings are read: mode (`tuisku-sf-mode`, default **Lite**), language (`tuisku-sf-lang`), and the Pro view (`tuisku-sf-pview5`, default **Rows**).
2. If the URL names a strategy that exists, its page opens on the tab in the URL, and the welcome tour does not open.
3. If the URL names a strategy that does not exist, the shop opens (fixed). [Real] Answer 404 or redirect to `/`.
4. Otherwise the shop opens. If the welcome tour has never been closed on this device (`edgefolio-tour-v1`), it opens on top (§2).
5. The texts load from `i18n/storefront.ui.json` (tool texts) and the core's `common.json` (shared texts).

**While browsing** (fixed):
- Opening a strategy, or switching its tab, writes `#s=<id>` or `#s=<id>/tree` into the URL.
- The browser's Back and Forward buttons move between the shop, the strategy and its tabs.
- Leaving the strategy page removes `#s=` from the URL.
- Reloading keeps the user where they were.

---

## 2. Welcome tour (first visit)

A centred dialog (max 480px) over a dark backdrop, with 3 steps:

| Step | Image | Title | Text |
|---|---|---|---|
| 1 of 3 | Six strategy icons | Pick a market | **Lite:** "Search a company or a crypto, or use the tabs: Hot, Win rate, Stocks, Crypto and Free." **Pro:** "Narrow the 2,834 strategies with the filter panel: net profit, price, symbol, time frame, indicators and 15 more." |
| 2 of 3 | A profit curve | Read the curve | `tour2Text` (look at the win rate and the trades, keep the overfitting note in mind) |
| 3 of 3 | PayPal → .pine → TradingView | Buy and load it in TradingView | `tour3Text` (pay with PayPal, paste into the Pine Editor, links last 7 days) |

| Action | Result |
|---|---|
| **Continue** (steps 1–2) | Next step |
| **Get started** (step 3) | Closes the tour |
| **Back** (steps 2–3) | Previous step |
| **×** (top corner) or **Esc** | Closes the tour |
| **→ / ←** | Next / previous step. The directions are swapped in Arabic. |
| Click on the image | Next step (does nothing on the last step) |
| Swipe on the image (more than 40px sideways) | Left goes to the next step, right to the previous one. Swapped in Arabic. |
| Dots | Show the current step only; they cannot be clicked |

Closing it in any way stores `edgefolio-tour-v1`, so the tour never opens by itself again. [Real] Store it once per account. The **? View tutorial** chip in the header reopens it at step 1.

---

## 3. Header, footer and phone bar (every page)

**Header** (sticky, white, with a cyan-to-blue line underneath, mirrored in Arabic). The items wrap onto a second line on narrow screens.

| Element | Click → result |
|---|---|
| **Edgefolio \| TradingView strategies** | Goes to the shop in the current mode and scrolls to the top |
| **Lite \| Pro** switch | Switches mode, stores it, and goes to the shop from any page. The active side is solid blue. |
| **My strategies** | Opens My strategies (§11) |
| **? View tutorial** | Opens the welcome tour at step 1 |
| **TradingView chip** ("TradingView ● Connected" / "Connect TradingView") | Switches between connected and not connected; the hover text says "Disconnect" or "Connect TradingView". [Mock] Only the label changes. [Decide] What connecting does in the real build. |
| **Currency chip** (EUR, INR, CNY, SAR or USD) | Switches between local currency and USD (§13). In English, local = USD, so a click shows no change. The choice is not stored. |
| **Language** (flag + name ▾) | Opens a menu with the 8 languages; the current one is highlighted. Choosing one changes the whole interface at once, without reloading, and stores it. Arabic flips the layout to right-to-left. A click outside or **Esc** closes the menu (Esc fixed). |

**Footer:** Privacy · Cookies · Terms of use · Legal notice · Contact, plus the Edgefolio wordmark. [Mock] The links have no target yet. [Real] Use the core's legal pages.

**Phone bottom bar** (under 640px wide; §14): Shop · Search · Cart · Mine.

---

## 4. Lite (default shop)

From top to bottom:

### 4.1 Ticker strip
The paid strategies sorted by net profit %, for example "AAPL · 1C00 +85.80 %". It scrolls sideways, never wraps, and is not clickable.

### 4.2 Hero and search
- A faded candle chart behind; the title "Strategies for TradingView"; the subtitle "Pick a market, look at the curve, download the Pine Script."
- **Search box** ("Search a company, crypto or indicator"). It filters as the user types, matching name, ticker, indicator name and indicator key (for example "nvda", "chaikin" or "1T00"). Lite and Pro share the same search text.

### 4.3 Tabs
One tab is active at a time. The tabs combine with the search, and the choice is not stored.

| Tab | Shows | Order |
|---|---|---|
| **Hot** (default) | Everything | Net profit %, highest first |
| **Win rate** | Everything | Win rate, highest first |
| **Stocks** | Stocks | Net profit % |
| **Crypto** | Crypto | Net profit % |
| **New · 3** | Released in the last 30 days. [Mock] Fixed list: NVDA 1M00, ETHUSDT 1T00, BTCUSDT 1BOL. | Net profit % |
| **Free** | Price = 0 | Net profit % |

### 4.4 Overfitting box
"Risk of overfitting" plus the explanation. It is always visible and cannot be closed.

### 4.5 Bundles row

| Bundle (`key`) | Strategies | Was | Price | Badge |
|---|---|---|---|---|
| Top 5 by profit (`bundleTop`) | AAPL 1C00, NVDA 1M00, ADBE 1T00, AMZN 1T00, AMZN 1BOL | $395.00 | $249.00 | Save 37 % |
| Crypto starter (`bundleCrypto`) | ETHUSDT 1T00, BTCUSDT 1BOL | $158.00 | $119.00 | Save 25 % |
| Amazon pair (`bundleAmzn`) | AMZN 1BOL, AMZN 1T00 | $158.00 | $119.00 | Save 25 % |

Each bundle card shows one icon per ticker, the name, "N strategies · tickers", the old price crossed out, the price, and a button.

| Action | Result |
|---|---|
| **Add bundle** | The bundle goes into the cart and the button changes to "✓ In cart". Any of its strategies that were in the cart on their own are removed, so nothing is paid twice. Any other bundle, or the custom pack, that shares a strategy with it is also removed (fixed; it used to be charged twice). The cards of its strategies show "In cart". |
| **✓ In cart** (on the bundle) | Removes the bundle from the cart |

**Build your pack** card (dashed border):
- The title "Build your pack", a "Save 37 %" badge, and 5 slots showing an icon or "+".
- A hint: "Pick 2 more · 5 for $249.00", or "5 for $249.00" when the pack is full.
- The **Add pack** button stays grey until 5 strategies are chosen.

| Action | Result |
|---|---|
| Click any slot | Opens the pack picker |
| **Add pack** with fewer than 5 chosen | Opens the pack picker |
| **Add pack** with 5 chosen | Adds the pack to the cart, and the button changes to "In cart". The pack's strategies leave the cart as single items, and any bundle that shares a strategy with the pack also leaves (fixed). |
| **In cart** (on the pack) | Removes the pack from the cart |

**Pack picker** (dialog):
- The title and an "N / 5" counter.
- One row for each of the 7 paid strategies: a tick box, the icon, "TICKER · KEY", the indicator and the net profit %. The free strategy is not listed.
- Click a row → it is ticked or unticked. A sixth tick is ignored.
- Any change takes the pack out of the cart, so it must be added again.
- **Done** or **Esc** closes the picker (Esc fixed).
- [Server] The pack price is calculated and checked on the server.

### 4.6 Strategy cards
A grid with columns at least 270px wide. Each card contains:

| Element | Click / hover → result |
|---|---|
| Icon and **ticker**, with a blue **New** badge on strategies released in the last 30 days (fixed: the badge was computed but never shown) | Click the ticker → the strategy page (Fact sheet) |
| Company name | Nothing |
| Green chip "+85.80 % ?" | Opens a dark explanation bubble: "Net profit %: what the strategy gained in the backtest…". × or a second click closes it. Only one bubble is open on the page at a time. |
| Profit curve with a "⚠ Backtest" label | Click → the strategy page (Fact sheet) |
| "Win rate **99.38 %** ?" | Explanation bubble (`expWin`) |
| "**160** trades ?" | Explanation bubble (`expTrades`) |
| "1Day · NASDAQ" | Nothing |
| **Grade** badge A–D (A green, B teal, C grey, D red) | Hover → "Sample: 160 closed trades. Fewer trades, more risk of overfitting." [Rule] A ≥ 300 trades, B ≥ 100, C ≥ 30, D below 30 (to agree). |
| "Since release **+9.4 %**" | Green when ≥ 0, red when negative. [Mock] Example figures. |
| ♡ **Heart** | Adds or removes a favourite (solid red when on). Favourites appear in My strategies (§11). |
| **Compare** icon | Adds the strategy to the compare list or removes it (dark when on). There are at most 3; a fourth is ignored. Adding one shows the Compare pill (§12). |
| **Fact sheet** chip | The strategy page, Fact sheet tab |
| **How it decides** chip | The strategy page, How it decides tab |
| Price ($79.00, ≈ 73 € or Free) | Nothing |
| **Buy** (paid) | Adds the strategy to the cart; the button turns into a light "✓ In cart". Clicking again removes it. If the strategy is in the cart through a bundle or the pack, clicking "In cart" removes that whole bundle or pack. |
| **Download** (free) | Opens the free-download dialog (§10) |

- When nothing matches: "No strategies match".
- Under the grid: "Showing N of 2,834" on Hot and Win rate with no search, otherwise "Showing N of N", and a **Load more** button. [Mock] Load more does nothing. [Real] It loads the next page of 24 from `GET /api/strategies`.

### 4.7 Floating cart
It is shown only when the cart has something in it, and sticks to the bottom of the screen while the shop scrolls. On phones it sits above the bottom bar (fixed: the bar used to cover it).

| Element | Behaviour |
|---|---|
| "Cart · N" | N counts strategies: a bundle counts all of its strategies, and each one is counted once |
| Discount tag "−35 %" | Only shown when a discount applies |
| **Have a code?** | Shows a code box and **Apply**. The result appears next to it: "Discount code applied" in green or "Invalid code, no discount applied" in red (fixed: Lite gave no feedback). [Mock] `DEMO20`, any case, gives 20 %. |
| Totals | The subtotal crossed out (only when there is a discount; fixed), then the total. In local currency, the prices start with "≈" and "You pay $154.05 with PayPal" appears underneath. |
| **Checkout** (PayPal icon) | §8 |
| Trust row | "PayPal: we never see your card" · "Links: 7 days, 10 downloads" · "Invoice by email" · **sales@tuisku.eu** (opens the mail program, and stays left-to-right in Arabic) |

When strategies are being compared, the **Compare · N** pill sits directly above the floating cart instead of on top of it (fixed: it used to cover the cart's left side on screens narrower than about 1100px).

---

## 5. Pro

### 5.1 Cart strip (top of the page, not sticky)

| Element | Behaviour |
|---|---|
| "Cart · N" + **Empty cart** (red) | Removes everything, including bundles and the custom pack (fixed: bundles stayed in the cart) |
| Ladder label | "15 % order discount + 20 % code", or "No order discount yet" |
| Next step | "Add $53.00 more to reach 20 %", or "Top discount reached" |
| Progress bar | Filled up to the current position. It has 5 ticks, each filled once passed, labelled "15 % / $160", "20 % / $290", "25 % / $500", "40 % / $1,000" and "70 % / $2,500". It is mirrored in Arabic. |
| Code box ("Code") + **Apply** | Applies the code, and the message appears underneath (green or red) |
| Totals | The subtotal crossed out (only with a discount; fixed), the total, and "You pay … with PayPal" when showing local currency (fixed: it was missing in Pro) |
| **Checkout** | §8. It is also shown when the cart is empty, but then does nothing. |
| Trust row | The same 4 items as in Lite, aligned to the end of the line |

**[Rule] Discount calculation:**
- The subtotal is the single strategies plus the bundle and pack prices.
- A tier applies when the subtotal is strictly above its threshold.
- The code adds its % on top of the tier.
- The total discount is capped at 70 %.

Example with the starting cart: 3 × $79 = $237, which is above $160, so 15 % + 20 % (DEMO20) = 35 %, and the total is **$154.05**.

[Decide] Whether tier discounts also apply on top of bundle prices. The prototype applies them.

### 5.2 Filter panel
It is on the left on wide screens, and moves above the list when the width is under about 900px.

| Control | Behaviour |
|---|---|
| Count, e.g. "8 · strategies shown" | Updates live |
| **Reset filters** | Clears every filter, the search and "Only FREE", and closes open menus |
| **Show only FREE** (switch) | Shows only strategies with price 0 |
| **Net Profit ($)** and **Price ($)** (always open) | See "Range filter" below |
| **Symbol, Time frame, Indicators, Index, Release date** (dropdowns) | Click the row → a menu opens (one at a time; a click outside or Esc closes it). It has a search box, **Select all** / **Deselect all**, and one tick row per option with its count (Symbol rows also show the icon). The row's value reads "N selected", up to 2 codes ("AAPL, NVDA"), or "—" when nothing is ticked, which gives an empty list. |
| **14 more ranges**, collapsed: Net Profit (%), Closed Trades, Win Rate (%), Profit Factor, Training (Months), Max Loss ($), Max Loss (%), Avg Profit ($), Avg Profit (%), Avg Bars/Trade, Trade Activity Per Candle, Number of Candles, Precision f1 (%), Tree Deep | Click → it opens in place, one at a time; a second click closes it. The label turns bold when the filter is active, and the value reads "any" when it is not. |

**Range filter** (the same for all 16):
- A **histogram** above the track. Hovering a bin shows "N strategies". Bins inside the range are full colour and the rest fade to 25 %. Small bins are solid blue so they stay visible.
- A **slider with two handles**:
  - Drag either handle with the mouse, a finger or a pen.
  - Clicking the track moves the nearest handle there.
  - The direction is reversed in Arabic.
  - A handle at the end of the track means "no limit" on that side.
- **Min and max boxes:**
  - Typing applies the value on **Enter** or when the box loses focus.
  - The boxes accept the language's number separators and the $ and % signs.
  - Values are clamped to the track, and min never passes max.

[Rule] Filters combine with AND; ticked options inside one dropdown combine with OR. The exact field mapping, scales and API are in `IMPLEMENTATION-v7.md` §12.

### 5.3 Above the list
- The title "Strategies".
- **Sort** tabs: Net profit · Win rate · Price · Closed trades. They always sort highest first.
- **Search** box, shared with Lite.
- **View** switch: Rows · Cards · Table. The choice is stored.
- **Active filter chips**, one per filter: "Price ($): $0 – $80 ×", "Show only FREE ×", "“nvda” ×". The × removes that filter. **Clear all** works like Reset filters.
- The overfitting note (blue variant).
- When nothing matches: "No strategies match".

### 5.4 Rows view (default)
Each row has the strategy's candle chart faded behind it. It shows:
- the icon and name;
- the **ticker** as a TradingView link, which opens the symbol page in a new tab, followed by "· 1Day · NASDAQ";
- "KEY · indicator" (hover shows the explanation);
- the **Fact sheet** and **How it decides** chips;
- the profit chart;
- 4 figures: Net profit, Win rate, Net profit %, Closed trades;
- the price and **Add to cart** / "✓ In cart" (same rules as §4.6) or **Download**.

### 5.5 Cards view
Each card shows:
- the name, the TradingView icon with the ticker link, the interval, the index and the price;
- the profit chart and the candle chart;
- 6 figures: Net profit, Win rate, Closed trades, Net profit %, Avg profit, Months trained;
- "KEY · indicator", a link to the **indicator's** TradingView page (fixed: it opened the symbol page);
- a **Strategy page** link and the two chips;
- a full-width cart or download button.

### 5.6 Table view
- **Columns:** Symbol (icon, ticker, grade badge, name) · Time frame · Indicators (key and name; hover shows the explanation) · Backtest (small chart) · Net profit · Net profit % · Win rate · Closed trades · Avg profit · Months trained · Price · actions.
- **Click a number header** to sort by it, highest first. The active header turns blue with ▼.
- **Click a row** to expand or collapse it. Only one row is open at a time (the prototype opens AAPL 1C00 at start). The expanded row shows both charts, "KEY · indicator", the explanation, "Open in TradingView ↗", and the two chips.
- **Row buttons:** Compare (§12), cart (icon only) and Download for the free one. Clicking them does not expand the row.
- **Footer:** "Rows per page 25 ▾", "1–8 of 8" and page buttons. [Mock] The page size and the page buttons do nothing.

In the Rows and Cards views, the footer shows "1–8 of 8" and **Load more** ([Mock]).

---

## 6. Strategy page

It can be opened from:
- the ticker, chart or chips of a Lite card;
- the chips and "Strategy page" link in Pro;
- the favourites list;
- the Fact sheet and How it decides links on the thank-you page and in My strategies (these open a new tab);
- the URL.

### 6.1 Header
- **Back to the shop** → the shop, in the same mode.
- A header card with the faded candle chart, the icon and "Amazon.com · AMZN".
- **Open in TradingView** (the symbol page, new tab) and the chips "1Day", "NASDAQ" and "1BOL".
- The price, then **Add to cart** / "✓ In cart" (same toggle rules as the cards) or **Download** for the free one (§10).
- **Open in a new tab** → the same page in a new tab.
- ♡ **Favourites** → adds or removes the favourite (red when on).
- **Fact sheet | How it decides** tabs. The URL follows the tab, and Back moves between the tabs (fixed).

### 6.2 Fact sheet tab (top to bottom)
1. A teaser card, "See how this strategy decides" → switches to How it decides.
2. A time-frame note: "In TradingView, set the chart's time frame to 1Day."
3. The overfitting box.
4. **Backtest vs. live result:**
   - the grade badge (hover explains it);
   - a Backtest bar (net profit %) and a Since release bar (green, or red when negative);
   - the note "Example figures until the daily job runs." [Mock]
5. **Versions:**
   - v2, "Rebuild: indicators match TradingView; Ichimoku without future prices.", with an **Update available** pill. The pill shows only to buyers who own the older version (fixed: everyone saw it).
   - v1 · 27 Sep 2024, "First release".
6. The **Strategy chart** and the **Candle chart**, at full width.
7. **Backtest results**, 14 rows:
   - Net Profit ($), Net Profit (%) in green, Closed Trades, Win Rate, Profit Factor;
   - Max Loss ($) and Max Loss (%) in red;
   - Avg Profit ($), Avg Profit (%), Avg Bars/Trade, Release Date, Training (Months), Time frame, Index.
   - A missing value shows "—".
8. **About the indicator:** "KEY · name", its description, and "See the indicator on TradingView".
9. **Pine Script preview:**
   - a dark editor with the file name "Tuisku_<file>.pine" and a "Pine Script v5" tag;
   - lines 5–16 readable; lines 17–21 blurred and not selectable;
   - a lock note: "The rest of the script is delivered after purchase".
   - [Rule] The full script never reaches the browser.
10. **What you buy: the complete script**, with 4 format tiles:
    - Pine Script (.pine);
    - Markdown for AI (.md);
    - Python (.py) **BETA**;
    - JavaScript (.js) **BETA**.

    Under them: "Included formats. Download them from My strategies after purchase."

### 6.3 How it decides tab (decision tree)

| Control | Behaviour |
|---|---|
| **Tree \| Blocks** switch | Tree (default) draws questions and Yes/No branches. Blocks draws the same tree as columns sized to the frame. |
| **Visitor \| Owner** switch | [Mock] A demo switch. [Real] Ownership comes from the purchase. |
| Question box ("At or below {value}?") | Click → the path moves there and the view follows. Clicking its **Yes / No** label does the same. |
| Result box (Buy / Sell / Wait, with score and strength bar) | Hover or tap → the rule as a sentence with range bars. Click → sets the values that reach it. The reached result has a ring. |
| Dragging the tree | Pans it |
| **Indicator values** panel | One slider per indicator, coloured by what the strategy would do if only that value changed (green buy, red sell, grey wait; stronger colour means a stronger signal). Ticks mark the thresholds, and hovering a tick or name explains it. The note "Thresholds already optimised" says that moving a slider simulates a market reading and does not change the strategy. |
| **Buy example / Sell example** | Sets the values that reach the strongest buy or sell result |
| **See all rules in plain words (N)** | Lists every rule under the tree; clicking a rule jumps to it. Clicking again hides the list. |
| Grey **Paid part** branches + **Buy to unlock** (also in the bubble) | Adds the strategy to the cart and changes the label to "Added to the cart". It never removes the strategy (fixed: it took it out of the cart when it was already in). On a free strategy it opens the free-download dialog (fixed: it put a $0 item in the cart). |
| Owner: **Download .pine** | [Mock] On the real site it downloads the full script with a signed link. |
| **Back to the fact sheet** | Fact sheet tab, scrolled to the top |

On phones, the sliders stack above the tree, and the tree scrolls inside its frame.

[Real] Visitors see the free part of tree 1. Owners get every tree of the forest from an authenticated endpoint.

---

## 7. Cart rules (summary)

- The cart holds single strategies, ready-made bundles and at most one custom pack.
- **[Rule] Each strategy is paid once** (fixed for overlapping bundles):
  - Adding a bundle or the pack removes its strategies from the cart as singles.
  - It also removes any other bundle or pack that shares a strategy with it.
  - A strategy that is in the cart through a bundle shows "In cart"; clicking it removes that bundle. [Decide] Confirm this rule; `/api/quote` must apply the same one.
- **Count:** strategies, each counted once.
- **Discount:** tier + code, capped at 70 % (§5.1).
- **Prices:** in local currency with "≈" and rounded to whole units; the charge is always in USD (§13).
- [Mock] The cart is not saved, so a reload resets it. [Real] Keep it in the session or account.

---

## 8. Checkout → thank-you page

**Click Checkout** (Lite or Pro):
- With an empty cart, nothing happens.
- **[Mock]** PayPal is skipped. The prototype:
  - creates an order "EF-xxxxx" with the total in USD;
  - adds each strategy to My strategies as bought today;
  - empties the cart and bundles (the code stays);
  - opens the thank-you page at the top;
  - opens the install tutorial if it has never been closed (`edgefolio-install-v1`).
- **[Real]** PayPal (`/api/orders` → approval → `/api/capture`), then the order, then the thank-you page. [Decide] Whether checkout needs an account; My strategies does.

**Thank-you page:**

| Element | Behaviour |
|---|---|
| ✓ "Thank you! Your payment went through." / "Your strategies are ready to download." | |
| Total paid "$154.05", "PayPal · Paid with PayPal · Order EF-xxxxx" | Always in USD |
| "Each link is valid for 7 days and up to 10 downloads. You'll also find them in My strategies." + **Download all** | [Mock] Download all does nothing. [Real] A signed link. |
| One row per strategy: icon, name · ticker, key · indicator · 1Day | |
| **.pine** / **.zip** (hover: "Everything in one .zip: the .pine script, .md rules for AI, Python and JavaScript (beta)") | [Mock] |
| **Fact sheet ↗** / **How it decides ↗** | Open the strategy page in a new tab |
| "Add it to TradingView" card + **Watch the tutorial** | Opens the install tutorial at step 1 |
| 5 step tiles | Open the tutorial at that step. Five columns at 900px or more, stacked below that. |
| **Go to My strategies** / **Back to the shop** | Navigate |
| "Problems? sales@tuisku.eu" | |

---

## 9. Install tutorial (5 steps)

It uses the first strategy of the last order (the prototype default is AMZN 1BOL).

| Step | Title | Image |
|---|---|---|
| 1 | Download and copy the script | The `.pine` button highlighted, then Ctrl+A and Ctrl+C |
| 2 | Sign in to TradingView | The tradingview.com sign-in form, with "Sign in / Create account" highlighted |
| 3 | Open the right chart | The strategy's candle chart, with the symbol search and "AMZN · 1D" highlighted, and an **Open AMZN in TradingView ↗** link to the chart with that symbol and interval (new tab) |
| 4 | Paste it into the Pine Editor | The Pine Editor side panel (1 open it, 2 Ctrl+V, 3 Save) |
| 5 | Add it to the chart | "Add to chart" highlighted and the Strategy Tester panel with the profit chart. On phones: Indicators › My scripts. |

**Controls:**
- **Continue** / **Back**, and **Done** on step 5, which closes the tutorial.
- Clickable **dots**.
- **→ / ←**, swapped in Arabic.
- **Esc** or **×** closes it.
- Clicking the image goes to the next step; swiping moves either way.

Closing stores `edgefolio-install-v1`, so it does not open by itself again. It can be reopened from the thank-you page (the button or the tiles) and from My strategies ("Add it to TradingView").

---

## 10. Free download (email capture)

Opened from **Download** on a free strategy: a Lite card, any Pro view, the strategy page, or "Buy to unlock" in How it decides.

| Element | Behaviour |
|---|---|
| × (top corner) or **Esc** | Closes it (Esc fixed) |
| Strategy icon, "Name · TICKER", "KEY · indicator" | |
| "Get it free" / "Enter your email and we'll send you the download link." | |
| **Email** field (placeholder ana@example.com) | Typing clears any error. **Enter** sends (fixed). |
| ☐ "Also tell me about new strategies (optional)" | **Unticked by default**; a click ticks or unticks it. [Rule] Under GDPR this is separate consent, never pre-ticked. |
| **Send me the link** | Empty field → "Enter your email address." Invalid → "That does not look like an email address." Both show in red under the field, with a red border (fixed: nothing happened). Valid → the success state. |
| Privacy link | [Mock] No target yet |
| Success: "Done. Check your inbox: the link is valid for 7 days." + **Back to the shop** | The button closes the dialog. The strategy appears in My strategies as "Free download {date}", or, if it was already there, its link starts again (fixed). |

[Server] An email table with a consent timestamp and the news opt-in, an email with a signed link (7 days, 10 downloads), and a rate limit.

---

## 11. My strategies

[Real] It requires the core's shared login; a signed-out visitor is asked to sign in first. [Mock] The prototype shows "Signed in as ana@example.com".

**One row per item bought or downloaded,** newest first:

| Element | Behaviour |
|---|---|
| Icon, "Name · TICKER", "KEY · indicator · 1Day" | |
| "Bought 21 Sep 2026" or "Free download 2 Oct 2026", plus "Order EF-48213" | The date is always the purchase date |
| Status pill | "Link valid N more days" (green) or "Link expired" (grey). [Rule] 7 days and 10 downloads from the last link issued. |
| **Get the update · v2** | Shown for paid items bought before v2 that have not been updated yet. Click → marked as updated, and the button disappears. [Mock] [Decide] Whether this is free or a paid yearly plan. |
| **.pine** and **.zip** (only while the link is valid) | [Mock] Downloads. The .zip was missing here (fixed). |
| **Get a new link** (only when expired) | Restarts the 7 days. It keeps the purchase date, order and version (fixed: it overwrote the purchase date and hid "Get the update"). |
| **Fact sheet ↗** / **How it decides ↗** | Open the strategy page in a new tab (fixed: these were only on the thank-you page) |

**Favourites card:**
- Empty → "Tap the heart on a strategy to follow it."
- Each favourite row shows:
  - the icon;
  - "TICKER · KEY", which opens the strategy page;
  - three alert chips, **New version**, **Price drop** and **In a bundle**, each switching on (blue with a solid bell) or off;
  - a ♥ that removes the favourite.
- [Server] The favourites and alerts are tied to the account. An email job sends the alerts, which are opt-in.

**Bottom:** **Add it to TradingView** (opens the install tutorial at step 1) and **Back to the shop**.

---

## 12. Compare (up to 3)

- Strategies are added with the compare icon on Lite cards and Pro table rows. There are at most 3; a fourth is ignored.
- The **Compare · N** pill sits at the bottom-start corner: above the floating cart in Lite (fixed), and 76px up on phones.
- Click the pill → a dialog opens with:
  - the title "Compare strategies" and "Up to 3 strategies";
  - one column per strategy, with the icon, "TICKER · KEY" and **×** to remove it;
  - rows for Net Profit (%), Win Rate (%), Closed Trades, Avg Profit ($), Since release and Price.
- The best value in each row is bold green on light green: the highest, except Price, where the lowest wins. With only one strategy nothing is marked.
- Removing the last strategy closes the dialog. **×** or **Esc** closes it too (Esc fixed).
- [Mock] The selection is not saved.

---

## 13. Languages, right-to-left and currency

- **Languages:** es, en, pt, fr, de, zh, ar, hi.
  - Numbers, money and dates follow the language's locale.
  - Arabic is right-to-left with Latin digits. It mirrors the layout, gradients, sliders, the ladder, and the arrow and swipe directions.
  - "Edgefolio" and the TradingView button names ("Save", "Add to chart") stay untranslated.
- **Currency** follows the language:

  | Language | Currency | Rate [Mock] |
  |---|---|---|
  | en | USD | 1 |
  | es, pt, fr, de | EUR | 0.92 |
  | hi | INR | 83.5 |
  | zh | CNY | 7.2 |
  | ar | SAR | 3.75 |

- Local prices show "≈" and are rounded to whole units ($79 → "≈ 73 €").
- [Rule] PayPal always charges USD. The thank-you total is in USD. The ladder thresholds and "Add $X more" are also in USD.

---

## 14. Phone (under 640px)

The **bottom bar** is fixed at the bottom; each button is at least 44px tall.

| Button | Click → result |
|---|---|
| **Shop** | The shop, scrolled to the top. Blue while on the shop. |
| **Search** | The shop, and focuses the current mode's search box (fixed: in Pro it focused the discount-code box) |
| **Cart** (with count badge) | The shop with the cart in view. In Pro it scrolls to the cart strip at the top. In Lite the floating cart is already on screen (fixed: it scrolled to the footer, even on other pages). |
| **Mine** | My strategies. Blue while there. |

- A 64px space under the footer keeps the content clear of the bar.
- The floating cart and the compare pill sit 76px from the bottom (fixed).
- The header chips wrap. The Pro filter panel moves above the list, and the table scrolls sideways.
- The thank-you tiles stack, and the tree's sliders move above the tree.

---

## 15. Keyboard and screen readers

| Key | Where | Result |
|---|---|---|
| **Esc** | Welcome tour, install tutorial | Closes it and marks it as seen |
| **Esc** | Compare, pack picker, free download, language menu, Pro dropdowns | Closes it (fixed) |
| **→ / ←** | Welcome tour, install tutorial | Next / previous step, swapped in Arabic |
| **Enter** | Min and max boxes | Applies the value |
| **Enter** | Free-download email | Sends (fixed) |

- **Roles in use:**
  - `radiogroup` for Lite | Pro;
  - `tablist` and `tab` for the Lite tabs and the strategy tabs;
  - `dialog` with `aria-modal` for every dialog;
  - `tooltip` for the explanation bubbles;
  - `alert` for the email error;
  - `checkbox` for the news opt-in;
  - `aria-pressed` on the view switch.
- [Real] Use real form controls for the news opt-in and the "Only FREE" switch so they can be reached with Tab. In the prototype they are clickable but not focusable.

---

## 16. Stored on the device (prototype)

| Key | Value | Set when |
|---|---|---|
| `tuisku-sf-mode` | `lite` or `pro` | Switching mode |
| `tuisku-sf-lang` | Language code | Choosing a language |
| `tuisku-sf-pview5` | `rows`, `cards` or `table` | Switching the Pro view |
| `edgefolio-tour-v1` | `1` | Closing the welcome tour |
| `edgefolio-install-v1` | `1` | Closing the install tutorial |

The cart, code, compare list, favourites, alerts, pack and currency choice are not stored in the prototype.

---

## 17. What the prototype simulates

| Feature | Prototype | Real build |
|---|---|---|
| Catalogue, paging, filters, histograms | 8 rows in the browser | `GET /api/strategies` (§12 of the guide) |
| Prices, bundles, pack, discounts | Calculated in the browser | `/api/quote` on the server |
| Payment | Checkout jumps to the thank-you page | PayPal orders and capture |
| Downloads (.pine, .zip, Download all, owner .pine) | Buttons only | Signed links: 7 days, 10 downloads |
| Free download email | Success message only | Email table, consent, email with the link |
| Since release figures | Fixed numbers | A daily forward-test job |
| Versions, "Update available" | v2 released on 1 Oct 2026 | Version data per strategy |
| Favourites, alerts | In memory | Account tables and an email job |
| Exchange rates | Fixed rates | Daily rates on the server |
| New this month | Fixed list of 3 | `released_at` within 30 days |
| Account | "Signed in as ana@example.com" | The core's shared login |
| Tree owner view | Demo switch | Complete forest from an authenticated endpoint |
| TradingView chip | Label only | [Decide] |

---

## 18. Fixes made in this pass (6 Oct 2026)

1. **Phones:** the Lite floating cart was hidden behind the bottom bar. It now sits above it.
2. **Compare pill:** it covered the left side of the Lite floating cart below about 1100px. It now sits above the cart.
3. **Phone "Search":** in Pro it focused the discount-code box. It now focuses the search box.
4. **Phone "Cart":** it scrolled to the footer, also in Pro and on other pages. It now opens the shop with the cart in view.
5. **Pro "Empty cart":** bundles and the custom pack stayed in the cart. It now empties everything.
6. **Overlapping bundles:** they were charged twice (for example Top 5 + Amazon pair). A new bundle or pack now replaces any bundle that shares a strategy with it.
7. **My strategies, "Get a new link":** it overwrote the purchase date, which also hid "Get the update". It now keeps the purchase date and restarts only the link.
8. **My strategies rows:** the .zip and the Fact sheet / How it decides links were missing. They are added, as on the thank-you page.
9. **"New" badge:** it was computed for strategies released in the last 30 days but never shown. It now shows on Lite cards.
10. **Crossed-out subtotal:** it showed even when there was no discount. It now shows only with a discount (Lite and Pro).
11. **Pro cart strip:** "You pay $X with PayPal" was missing when showing local currency. It is added.
12. **Lite code box:** Apply gave no feedback. It now shows "Discount code applied" or "Invalid code".
13. **Free download:** an empty or invalid email did nothing. It now shows an error; Enter sends; asking again restarts the link in My strategies.
14. **"Buy to unlock" in How it decides:** it removed the strategy if it was already in the cart, and added free strategies as $0 items. It now only adds paid strategies, and opens the free-download dialog for free ones.
15. **Strategy page, "Update available":** everyone saw it. It now shows only to owners of the older version.
16. **Pro Cards:** the indicator name opened the symbol page. It now opens the indicator page.
17. **Esc:** it only closed the two tutorials. It now also closes compare, the pack picker, the free download, the language menu and the Pro dropdowns.
18. **URL:** in-app navigation did not update the address. The strategy page now keeps `#s=<id>` (and `/tree`) in the URL, so Back, Forward and reload work, and an unknown id falls back to the shop.

---

## 19. Open points

- The grade cut-offs (A ≥ 300, B ≥ 100, C ≥ 30) still need to be agreed.
- Whether tier discounts apply on top of bundle and pack prices.
- The bundle overlap rule in §7, to confirm and mirror in `/api/quote`.
- Whether checkout needs an account.
- Whether "Get the update" is free or part of a paid yearly plan.
- What "Connect TradingView" does.
- The `tour1Pro` text says "and 15 more", but the panel has 16 more filters after the five it names (Index, Release date and 14 ranges). The text is in 8 languages, so it was left unchanged.
- The grade explanation is a hover text, so touch screens can't read it. A tap bubble, like the metric explanations, would fix that.
- Compare and favourite are not in the Pro Rows and Cards views (the spec only asks for them in the Table).
- The "New this month" strip on top of Lite from the improvements lab (#9) is not built. Only the tab and the badge are.
- The strategy page has no cart summary or Checkout. To pay, the user goes back to the shop.
- Pro shows Checkout even when the cart is empty.
- The ladder thresholds are in USD while the totals can be in local currency.
