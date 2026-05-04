# Prints

The live catalog now uses snapshot image links from `data/product-catalog.json`.

Use this folder only for optional local reference art that should be committed intentionally.

Recommended filename format:

```text
character-name-size.jpg
```

After adding a new catalog item, update the shared Google Sheet, export a new workbook snapshot, and regenerate `data/product-catalog.json` instead of editing `server.js`.
