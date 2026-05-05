# Snapshot Catalog Audit

Date: 2026-05-05

## Source

The customer-facing catalog is built from `documents/Current_Inventory_Lst with Photos to USe.docx` and the labeled artwork ZIP at `ALL ARTWORK /Merch_Art LeahClark-20260505T183511Z-3-001.zip`. The app serves optimized web images from `prints/current-inventory/`.

## Exported Product Fields

- `name`
- `image`
- `material`
- `size`

`data/product-catalog.json` also includes internal ids for stable app records. `documents/leah-indianapolis-popcon-catalog.csv` contains only the exported product fields above.

## Snapshot Counts

- Inventory rows read from DOCX: 155
- Artwork candidates read from ZIP and fallback catalog: 154
- Customer-visible current-inventory rows: 96
- Rows needing artwork review: 59

## Visibility Rules

Rows appear in the QR catalog when the current inventory row has a safe artwork match, print name, material, and size. Rows without a safe match remain in `documents/leah-current-inventory-artwork-audit.csv` and are not shown to customers.

## Image Access Note

The labeled ZIP contains print-resolution artwork, so the builder generates compressed web catalog images in `prints/current-inventory/` instead of serving the original oversized files.
