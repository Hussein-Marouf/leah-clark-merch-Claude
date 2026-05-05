# GitHub Upload Checklist

## Project Path

Use this folder as the GitHub project:

```text
leah-clark-merch/
```

## Catalog Uploads

The live catalog is driven by the current inventory DOCX matched to local image files, not live Google Drive edits or hard-coded placeholder images.

```text
leah-clark-merch/data/product-catalog.json
```

Customer-facing product rows are limited to:

- `name`
- `image`
- `material`
- `size`

`data/product-catalog.json` also includes internal ids for stable app records and audit rows for products that need image review.

Downloaded catalog images live here:

```text
leah-clark-merch/prints/catalog/
```

The download manifest records which Drive links worked and which returned Google sign-in pages:

```text
leah-clark-merch/prints/catalog/manifest.json
```

The source exports currently kept for audit are:

```text
leah-clark-merch/documents/leah-product-catalog-snapshot.csv
leah-clark-merch/documents/leah-indianapolis-popcon-catalog.csv
leah-clark-merch/documents/leah-inventory-image-match-audit.csv
leah-clark-merch/documents/leah-standard-prints-8_5x11.csv
leah-clark-merch/documents/leah-large-prints-11x17.csv
```

Before committing sheet exports, remove private shipping addresses, customer data, payment details, or API keys. Do not commit the raw workbook unless it has been reviewed and sanitized.

## Document Uploads

Add project, booth, inventory, or workflow documents here:

```text
leah-clark-merch/documents/
```

The current Google Sheet schedule is stored as:

- `documents/leah-current-schedule.csv`
- `data/current-schedule.json`
- `data/product-catalog.json`

Before pushing public documents, check for:

- customer emails
- phone numbers
- private addresses
- API keys
- payment information
- unreleased contract details

## Git Commands

From `/Users/husseinmarouf/Documents/New project`:

```bash
git status
git add .gitignore leah-clark-merch
git commit -m "Use sanitized Leah product snapshot"
git push origin main
```
