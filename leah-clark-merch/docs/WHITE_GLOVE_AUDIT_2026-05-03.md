# White Glove App Audit

Date: 2026-05-03

## Scope

Reviewed the full Leah Clark merch app:

- Express server and JSON data handling
- Customer print ordering page
- Admin sales dashboard
- QR sign generator
- Current schedule page and Google Sheet export
- Print and document asset structure
- GitHub upload readiness

## Issues Fixed

- Customer browsing no longer requires email first; fans can browse immediately and save when ready.
- Added catalog search and size filters to reduce mobile scrolling.
- Changed print art rendering from cropped to contained so customers can inspect the actual artwork.
- Replaced the hard-coded local placeholder catalog with a sanitized product snapshot in `data/product-catalog.json`.
- Added a repeatable snapshot builder that exports only quantity, image type, name, image, size, price, and availability.
- Marked snapshot rows without dependable images or prices as review-only so they do not appear to customers as orderable items.
- Downloaded accessible Drive images into `prints/catalog/` and updated the catalog to use local image paths where available.
- Updated startup normalization so stale Render `db.json` print records are replaced by the current sheet-driven catalog.
- Hardened order validation on the server, including valid email checks, valid active print IDs, item caps, duplicate item merging, and safe quantity limits.
- Added order totals to customer/admin responses for consistent UI math.
- Added proper 404 handling for missing admin orders instead of returning silent success.
- Added QR URL validation on both client and server.
- Improved admin dashboard search so auto-refresh does not wipe active searches.
- Added keyboard access and focus states for admin order cards and customer print cards.
- Added admin status messages for refresh/search/action errors.
- Added schedule summary counts and a source link.
- Added a health endpoint at `/api/health`.
- Updated docs for optimized display images and schedule files.

## Performance Notes

- The customer catalog now loads Drive thumbnail URLs sized for web display instead of shipping local placeholder art in the repo.
- Local `prints/` files are optional reference storage only; they are not the active catalog source.
- Public HTML is not cached, while print and document assets get short cache windows.

## Verification

- `node --check server.js`
- Parsed inline scripts from all public HTML pages with Node VM
- Validated schedule JSON shape and counts
- Validated print catalog JSON shape and required fields
- Verified all Drive thumbnail URLs return HTTP 200
- Ran `git diff --check`
- Ran a headless Chrome smoke test with mocked APIs for customer order flow, admin search/details, QR validation, and schedule rendering

## Remaining Operational Notes

- This local machine does not currently have `npm`, so the Express server cannot be booted locally until Node/npm dependencies are installable.
- Admin is intentionally unauthenticated for booth speed; add an optional PIN before public long-term deployment if the URL will be widely shared.
