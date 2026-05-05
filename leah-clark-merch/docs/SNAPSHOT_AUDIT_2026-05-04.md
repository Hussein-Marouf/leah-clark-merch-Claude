# Snapshot Catalog Audit

Date: 2026-05-05

## Source

The catalog was built from `documents/Current_Inventory_Lst with Photos to USe.docx` and correlated with local images in `prints/catalog/`.

## Exported Product Fields

- `name`
- `image`
- `material`
- `size`

`data/product-catalog.json` also includes internal ids for stable app records. `documents/leah-indianapolis-popcon-catalog.csv` contains only the exported product fields above.

## Snapshot Counts

- Inventory rows read from the DOCX: 155
- Local catalog images read: 37
- Customer-visible matched rows: 12
- Duplicate matched rows skipped: 1
- Inventory rows missing a matched local image: 142

## Visibility Rules

Rows appear in the QR catalog only when the inventory print name has an exact normalized-name or same-word match to a local catalog image name. Rows that are missing a local image match remain in `documents/leah-inventory-image-match-audit.csv` but are not shown to customers.

## Image Access Note

The previous downloader saved 37 Google Drive thumbnail images into `prints/catalog/`. For this build, only 12 non-duplicate inventory rows matched those local images confidently.
