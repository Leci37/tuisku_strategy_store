# STATUS · Edgefolio design (export 2026-10-06)

Tool `edgefolio` · `Leci37/tuisku_Web_selling`, branch `_ztool_dev` · core zlecitool-core 0.23.0.

**Baseline:** the shop follows the v7 export of 6 Oct 2026, plus the trust row.

**Status values:**
- **final:** build it as shown.
- **in progress:** parts are still open.
- **sketch:** an exploration; don't build it.

## Screens

| # | Screen | File | Status | Still open |
|---|---|---|---|---|
| 1 | Lite (default) | `prototype/Storefront v7.dc.html` | final | Loading and error states for the catalogue; "Load more" is a mock; the "New this month" strip from the Improvements Lab was never built |
| 2 | Pro | `prototype/Storefront v7.dc.html` | final | Loading and error states; the pager and "Rows per page" are mocks |
| 3 | Strategy page (/s/<id>) | `prototype/Storefront v7.dc.html` | final | The free strategy's preview is drawn cut, while the shop shows free previews whole (keep the shop's behaviour); no error state for the preview |
| 4 | How it decides (/s/<id>/tree) | `prototype/Strategy Tree.dc.html` | final | The Visitor / Owner switch is a demo; the indicator explanations are es/en only |
| 5 | Cart and checkout | `prototype/Storefront v7.dc.html` | final | The PayPal loading, failure and cancel states are not designed; `DEMO20` is a mock (no code reaches the page) |
| 6 | Free strategy for an email | `prototype/Storefront v7.dc.html` | final | No "sending" state |
| 7 | Thank you (/thanks) and install tutorial | `prototype/Storefront v7.dc.html` | final | Steps 2 and 4 are diagrams; the downloads are mocks |
| 8 | My strategies (/mine) | `prototype/Storefront v7.dc.html` | in progress | «¿Compraste sin cuenta?» is in the shop but not in the design (keep it). The empty list, loading and error states are not designed. Is "Get the update" free or paid? |
| 9 | Phone (390 px) with the bottom bar | `prototype/Storefront v7.dc.html` | final | — |

## Earlier versions and sketches (`versions/`, reference only)

| File | Status |
|---|---|
| `versions/Storefront v2.dc.html` … `Storefront v6.dc.html` | replaced by v7 |
| `versions/Storefront Redesign.dc.html` (directions 1a–1e and "Today") | sketch |
| `versions/Tree Styles.dc.html` (tree options 1a–1c) | sketch |
| `versions/Improvements Lab.dc.html` (10 ideas) | sketch |

## Sample data in the prototype

- **The 8 strategies:**
  - From the catalogue: net profit $ and %, win rate, trades, avg profit $ and months.
  - Examples: profit factor, max loss, avg profit % and avg bars for AMZN 1T00, ADBE 1T00, AAPL 1C00 and NVDA 1M00.
  - Examples for all 8: precision and tree depth.
- **Invented:**
  - the "Since release" figures;
  - the fixed "New" list;
  - the v2 date (1 Oct 2026);
  - the bundle contents and prices, and the 5-for-$249 pack;
  - `DEMO20`;
  - the exchange rates;
  - "2,834" (unknown whether it is the real total);
  - ana@example.com and the orders and purchases;
  - "today" = 5 Oct 2026.
- **Real:** the charts, icons and Pine previews are the repository's files. The discount tiers match `api/settings.py`.

## Open questions

1. The grade cut-offs (A ≥ 300, B ≥ 100, C ≥ 30).
2. Do tier discounts also apply on top of bundle prices?
3. Confirm the bundle overlap rule (a new bundle replaces any bundle that shares a strategy with it) in `/api/quote`.
4. What does "Connect TradingView" do?
5. `tour1Pro` says "and 15 more", but the panel has 16 more filters after the five it names.
6. The grade explanation is a hover text, which touch screens can't show.
7. Should Compare and Favourite also appear in the Pro Rows and Cards views?
8. The strategy page has no cart summary.
9. Pro shows Checkout with an empty cart.
10. The ladder thresholds are in USD while the totals can be in local currency.
11. The zh, ar and hi texts need a native review.
