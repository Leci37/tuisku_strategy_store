# PR: Edgefolio storefront v7

> The designer's proposed PR, kept for reference. The work goes to `_ztool_dev` instead (no `design/` branch
> and no pull request: the export's README says so too), and some items of "Not in this PR" were built
> after all (favourites, local-currency rates); see the status note in `../IMPLEMENTATION-v7.md`.

**Base:** `zlecitool_main` · **Branch:** `design/edgefolio-v7`

## Summary

Rebuilds the shop in `storefront/` as Edgefolio, following the v7 reference design (`docs/design/`). Filtering, paging and pricing move to `api/`.

## Changes

1. **Shell:** the Edgefolio bar, the Lite | Pro switch (remembered), and 8 languages with RTL (core `common.json` + `storefront/i18n/storefront.ui.json`).
2. **API:** `GET /api/strategies` with the 21 filters, search, sort, paging (25 per page) and histogram bins (`docs/IMPLEMENTATION-v7.md` §12). The browser no longer downloads the whole CSV.
3. **Lite:** tabs, cards, the overfitting box and the floating cart.
4. **Pro:** the filter panel (sliders with histograms and typed min / max, multi-selects, chips) and the Rows / Cards / Table views.
5. **Strategy page `/s/<id>`:** Overview, and How it decides (compact tree and Blocks views, §9), plus the script preview (§10).
6. **Flows:** free download for an email, the thank-you page with the install tutorial (§11), and My strategies.
7. **Bundles and the custom pack,** priced by the server, plus the welcome tour.
8. **Docs:** `docs/IMPLEMENTATION-v7.md`, `docs/USER-FLOW-v7.md`, `docs/catalogue-updates.md`, and the reference design in `docs/design/`.

## Not in this PR

The since-release results job, versions and update notices, favourite and alert emails, and local-currency rates (§6).

## Checklist

- [ ] `pytest` is green: prices, discounts, payment checks and downloads.
- [ ] Every filter changes the count, the chips, the list and the pager. The slider ends are open, and typed min / max work in es and en number formats.
- [ ] The acceptance checklist in §8.
- [ ] Every flow in `docs/USER-FLOW-v7.md` behaves as described.
- [ ] The full script never reaches the browser, and every price comes from the server.
