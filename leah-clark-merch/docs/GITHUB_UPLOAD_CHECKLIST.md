# GitHub Upload Checklist

## Project Path

Use this folder as the GitHub project:

```text
leah-clark-merch/
```

## Print Uploads

The live catalog is driven by the shared Google Sheet export, not hard-coded placeholder images.

```text
leah-clark-merch/data/print-catalog.json
```

Each catalog item should include:

- unique `id`
- display `name`
- inventory `label`
- `size`
- `price`
- `image_url` using a shared Google Drive thumbnail URL
- `source_url`
- `source_tab`
- `active`

The source exports currently kept for audit are:

```text
leah-clark-merch/documents/leah-standard-prints-8_5x11.csv
leah-clark-merch/documents/leah-large-prints-11x17.csv
```

Before committing sheet exports, remove private shipping addresses, customer data, payment details, or API keys. The public app only needs the Drive file links and inventory fields required to build the catalog.

## Document Uploads

Add project, booth, inventory, or workflow documents here:

```text
leah-clark-merch/documents/
```

The current Google Sheet schedule is stored as:

- `documents/leah-current-schedule.csv`
- `data/current-schedule.json`
- `data/print-catalog.json`

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
git commit -m "Use shared Leah print catalog"
git push origin main
```
