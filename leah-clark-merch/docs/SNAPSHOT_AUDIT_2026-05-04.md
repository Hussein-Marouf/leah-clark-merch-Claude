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
- Customer-orderable rows with local images: 6
- Downloaded local image files: 37
- Drive image links that redirected to sign-in or failed download: 41
- Rows needing image mapping or accessible image export: 234
- Rows with local image mapping but missing price: 31

## Availability Rules

A product is marked `available` only when it has:

- quantity greater than zero
- a local downloaded image
- a known price

Rows that are missing either a local image or price remain in the snapshot audit but are not shown to customers.

## Price Rules Applied

- Paper print `8.5x11`: `$15`
- Paper print `11x17`: `$25`
- Metal prints, metal trading cards, and holographic prints: `needs price`

## Image Access Note

The downloader saved 37 Google Drive thumbnail images into `prints/catalog/`. The 41 failed Drive image links returned Google sign-in or permission pages, so those rows were changed to `needs image` and are not customer-orderable.
