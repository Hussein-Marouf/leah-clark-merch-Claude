# Snapshot Catalog Audit

Date: 2026-05-04

## Source

The catalog was built from a read-only export of the shared `Convention Inventory 2026` Google Sheet. The raw workbook was not committed because it contains logistics columns.

## Exported Product Fields

- `quantity`
- `image_type`
- `name`
- `image`
- `size`
- `price`
- `availability`

`data/product-catalog.json` also includes internal ids for order handling. `documents/leah-product-catalog-snapshot.csv` contains only the exported product fields above.

## Snapshot Counts

- Total quantity-bearing snapshot rows: 271
- Customer-orderable rows: 17
- Rows needing image mapping: 193
- Rows with image mapping but missing price: 61

## Availability Rules

A product is marked `available` only when it has:

- quantity greater than zero
- a resolved image link from the snapshot
- a known price

Rows that are missing either image or price remain in the snapshot audit but are not shown to customers.

## Price Rules Applied

- Paper print `8.5x11`: `$15`
- Paper print `11x17`: `$25`
- Metal prints, metal trading cards, and holographic prints: `needs price`

## Image Access Note

The snapshot stores Google Drive thumbnail links. A non-signed-in thumbnail check redirected to Google sign-in, so QR users may not see images until the Drive files are publicly viewable or copied into local app assets.
