# Prints

The live catalog now uses local snapshot images from `prints/catalog/` when Drive links can be downloaded.

Use this folder only for optional local reference art that should be committed intentionally.

Recommended filename format:

```text
character-name-size.jpg
```

After adding a new catalog item, update the shared Google Sheet, export a new workbook snapshot, regenerate `data/product-catalog.json`, and run `scripts/download_catalog_images.py` instead of editing `server.js`.
