# Snapshot Catalog Audit

Date: 2026-05-05

## Source

The customer-facing catalog is built from `documents/leah-product-catalog-snapshot.csv` and local images in `prints/catalog/`. The inventory DOCX match audit is kept separately to review missing or differently named inventory rows.

## Exported Product Fields

- `name`
- `image`
- `material`
- `size`

`data/product-catalog.json` also includes internal ids for stable app records. `documents/leah-indianapolis-popcon-catalog.csv` contains only the exported product fields above.

## Snapshot Counts

- Snapshot rows read from CSV: 271
- Local catalog images available: 37
- Customer-visible image-backed rows: 37
- Inventory rows read from the DOCX audit: 155
- Customer-visible DOCX matched rows before the fuller snapshot rebuild: 12
- Inventory rows missing a matched local image in the DOCX audit: 142

## Visibility Rules

Rows appear in the QR catalog when the snapshot row has a local image, print name, material, and size. Rows without local images remain in the snapshot/audit files and are not shown to customers.

## Image Access Note

The downloader saved 37 Google Drive thumbnail images into `prints/catalog/`. The public QR catalog now shows all 37 image-backed rows instead of only the 12 rows that matched the DOCX inventory names exactly.
