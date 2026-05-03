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
- Added web-optimized display images in `prints/display/` and pointed catalog records to those files.
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

- Original print assets remain in `prints/` for production/reference.
- Mobile catalog assets now use `prints/display/` copies capped at 1200 px, totaling about 1.8 MB.
- Public HTML is not cached, while print and document assets get short cache windows.

## Verification

- `node --check server.js`
- Parsed inline scripts from all public HTML pages with Node VM
- Validated schedule JSON shape and counts
- Verified all catalog `image_url` paths exist
- Ran `git diff --check`
- Ran a headless Chrome smoke test with mocked APIs for customer order flow, admin search/details, QR validation, and schedule rendering

## Remaining Operational Notes

- This local machine does not currently have `npm`, so the Express server cannot be booted locally until Node/npm dependencies are installable.
- GitHub push is still blocked by GitHub HTTPS token authentication in the terminal.
- Admin is intentionally unauthenticated for booth speed; add an optional PIN before public long-term deployment if the URL will be widely shared.
