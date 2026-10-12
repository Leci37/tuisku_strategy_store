# Keeping the Edgefolio catalogue up to date

How the shop's 2,834 strategies get refreshed, and how often that is realistic. It is based on `catalogue/publish.py`, `edgefolio/release.py` and the README of `tuisku_strategy_store` (branch `_ztool_dev`).

> **Status in this repository.** Written with the v7 handoff. What it plans is built, except the
> daily "results since release" job (the page reads `catalogue/since_release.csv` when it exists) and
> object storage for the charts. Bundles are in `catalogue/bundles.json`.

## What has to change, and where it lives

| What | Where it comes from | Tool today |
|---|---|---|
| Strategies, results, charts | The strategy factory, the twin app that generates the data: [tuisku_strategy_generator](https://github.com/Leci37/tuisku_strategy_generator/tree/_ztool_dev) (private). Its step 7 writes a versioned package, `d_result/package/`, of contract `catalogue/contract.json` | `flask --app app edgefolio import`, into `catalogue/catalogue.csv`, `catalogue/release.json` and `static/assets/` |
| Paid `.pine` scripts | The factory's `d_result/pine_TW_b/` (never in the package: its manifest only has their sha256) | `edgefolio import --scripts`, hash-checked, into `STRATEGIES_DIR` (default `<ZLECITOOL_DATA_DIR>/edgefolio/strategies`) |
| Prices | `catalogue/catalogue.csv` | Read by the API, never by the browser |
| Discount tiers and codes | `edgefolio/settings.py` and environment variables | Restart the server |
| UI texts | `i18n/ui.json` (8 languages; never a key of the core's dictionary) | Edit the JSON |

The import (`edgefolio/release.py`, which uses `catalogue/publish.py`) already does the hard part:
- it checks the whole package before writing anything: the contract version and columns, every sha256, safe paths, no unlisted file, the files every row names, one paid script per row, no full script disguised as a chart or a logo; then the paid scripts' sha256;
- it drops repeated rows;
- it rewrites image paths;
- it removes the location of the paid file;
- it copies only the charts, logos and previews the rows use; it replaces the charts and previews that changed, and a logo only when the shop's is the factory's placeholder;
- it copies only the paid scripts the manifest lists;
- with `--prune`, it deletes the charts and previews nothing uses;
- it writes everything beside its place and renames it at the end, so a failure leaves the shop as it was (one while renaming says how many files are already in place: import again).

## Before the first relaunch

The README says the current set should not be sold as it is:
- the strategies were generated on 2024-10-18 and were recommended to expire on 2025-06-18;
- about a third calculate their indicators differently in TradingView than in training;
- the Ichimoku family used future prices.

The first update is therefore a full rebuild in the factory with those problems fixed. Its branch `_ztool_dev` fixes them, and its README says that, tested on data they never saw, the strategies lose money on average after costs: how to list them is the owner's decision.

## Monthly: viable

A full refresh is one sequence of steps, and it can be run as a single CI job:

1. Rebuild in the factory (`python run_pipeline.py`). Its step 7 writes the export CSV and the package, `d_result/package/`. The package must never be made public: the free strategies' previews in it are whole scripts, which the shop cuts when it publishes them.
2. In the shop, with the development requirements (the import needs pandas, which is in `requirements-dev.txt` only): `flask --app app edgefolio import GENERATOR/d_result/package --scripts GENERATOR/d_result/pine_TW_b --prune`. It copies the listed paid scripts into `STRATEGIES_DIR` (private storage, never the repo), publishes the catalogue and its files, and records the factory run in `catalogue/release.json`. Without `--scripts` the scripts must already be in `STRATEGIES_DIR` with the right sha256; `--skip-scripts` publishes without them and says how many are missing.
3. Fix or remove the bundles the import names: a bundle of `catalogue/bundles.json` that lost a strategy is dropped whole by the shop.
4. `pytest`: the tests cover prices, bundles, filters, payment checks, download links, accounts, the generated formats and what must stay out of the page (including that every public preview is cut).
5. Nothing to do for thumbnails: the server makes the WebP thumbnails of the cards and the table on the first request (`/thumbs/...`) and keeps them in `<ZLECITOOL_DATA_DIR>/edgefolio/thumbs`. The import empties that folder, and a thumbnail older than its chart is made again anyway.
6. Commit `catalogue/` and `static/assets/`, deploy with the new paid scripts in the server's `STRATEGIES_DIR`, and restart the shop: it reads the catalogue when it starts. Then tell owners about new versions (paid updates) and email the people who opted in through the free downloads.

Without Flask, `python catalogue/publish.py --package DIR [--prune]` makes the same checks of the package and the same publish, but the paid scripts are then copied by hand. The form before packages, `python catalogue/publish.py EXPORT.csv [--assets DIR] [--prune]`, still works; it checks the columns, but there are no hashes, and it leaves the files the shop already has as they are.

**When the contract changes** (a column or a folder), its version goes up in both repositories at once: `catalogue/contract.json` here, `CONTRACT_VERSION` and `SHOP_COLUMNS` in the factory. Push the shop's change to its branch before the factory's, or with it, and merge it into `_ztool_main` first too: the factory's CI runs its bridge tests against the shop's `catalogue/` on `_ztool_dev` (on `_ztool_main` for runs on `_ztool_main` and pull requests into it), and a package of another contract version is refused.

## Daily: only the light part

Rebuilding 2,834 backtests every day means 5,668 new charts a day. That is heavy and not recommended. What can change daily without a rebuild:

- prices, bundles, the "Hot" order and which strategies are free (a small overrides file, or a table in the database);
- discount codes (environment variables);
- **results since release**, meaning each strategy's real performance after its release date. This needs a new daily job that reads market data and runs the strategy forward. It is the best answer to the overfitting risk and the most valuable daily update.

## Costs and risks

- **Repository size.** The assets are about 570 MB already, and monthly batches of thousands of PNGs will make the git history grow fast. Move the charts to object storage (S3 or R2) behind a CDN, and keep only `catalogue.csv` in the repo, or move it to the database.
- **Versions.** Give every strategy a version and a release date. Buyers keep their old version, and "My strategies" shows when a newer one exists.
- **Translations.** Indicator names and descriptions come from `catalogue/indicators.csv` in English only. New UI texts need all 8 languages.
- **Heavy traffic.** Done: the page gets the catalogue from the API one page at a time and the server filters, sorts and counts.

## Verdict

- **Monthly full update:** viable with the tools already in the repo, plus a CI job and object storage for charts.
- **Daily:** viable for prices, ordering, free picks and results since release. Daily full rebuilds are not worth it.
