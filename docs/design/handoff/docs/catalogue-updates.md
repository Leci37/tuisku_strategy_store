# Keeping the Edgefolio catalogue up to date

How the shop's 2,834 strategies get refreshed, and how often that is realistic. It is based on `catalogue/publish.py` and the README of `tuisku_Web_selling` (branch `zlecitool_main`).

## What has to change, and where it lives

| What | Where it comes from | Tool today |
|---|---|---|
| Strategies, results, charts | The strategy factory (private repo), which writes an export CSV and `d_result/` | `catalogue/publish.py` |
| Paid `.pine` scripts | The factory's `pine_TW_b/` | Copied by hand to `STRATEGIES_DIR` |
| Prices | `catalogue/catalogue.csv` | Read by the API, never by the browser |
| Discount tiers and codes | `api/settings.py` and environment variables | Restart the server |
| UI texts | `storefront/i18n/storefront.ui.json` (8 languages) | Edit the JSON |

`publish.py` already does the hard part:
- it drops repeated rows;
- it rewrites image paths;
- it removes the location of the paid file;
- it copies only the charts the rows use;
- with `--prune`, it deletes the charts nothing uses.

## Before the first relaunch

The README says the current set should not be sold as it is:
- the strategies were generated on 2024-10-18 and were recommended to expire on 2025-06-18;
- about a third calculate their indicators differently in TradingView than in training;
- the Ichimoku family used future prices.

The first update is therefore a full rebuild in the factory with those problems fixed.

## Monthly: viable

A full refresh is one sequence of steps, and it can be run as a single CI job:

1. Rebuild in the factory, which produces the export CSV and `d_result/`.
2. `python catalogue/publish.py EXPORT.csv --assets d_result --prune`
3. Copy the new paid scripts to `STRATEGIES_DIR` (private storage, never the repo).
4. `pytest`: the 20 tests cover prices, discounts, payment checks, download links and what must stay out of the page.
5. New step: create small WebP thumbnails for the Lite cards and the table, so pages stay light.
6. Deploy, then tell owners about new versions (paid updates) and email the people who opted in through the free downloads.

## Daily: only the light part

Rebuilding 2,834 backtests every day means 5,668 new charts a day. That is heavy and not recommended. What can change daily without a rebuild:

- prices, bundles, the "Hot" order and which strategies are free (a small overrides file, or a table in the database);
- discount codes (environment variables);
- **results since release**, meaning each strategy's real performance after its release date. This needs a new daily job that reads market data and runs the strategy forward. It is the best answer to the overfitting risk and the most valuable daily update.

## Costs and risks

- **Repository size.** The assets are about 570 MB already, and monthly batches of thousands of PNGs will make the git history grow fast. Move the charts to object storage (S3 or R2) behind a CDN, and keep only `catalogue.csv` in the repo, or move it to the database.
- **Versions.** Give every strategy a version and a release date. Buyers keep their old version, and "My strategies" shows when a newer one exists.
- **Translations.** Indicator names and descriptions come from `catalogue/indicators.csv` in English only. New UI texts need all 8 languages.
- **Heavy traffic.** The page should get the catalogue from the API one page at a time (for example 24 rows) and filter on the server. Today the browser loads and parses the whole CSV.

## Verdict

- **Monthly full update:** viable with the tools already in the repo, plus a CI job and object storage for charts.
- **Daily:** viable for prices, ordering, free picks and results since release. Daily full rebuilds are not worth it.
