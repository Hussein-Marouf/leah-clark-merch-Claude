# GitHub Upload Checklist

## Project Path

Use this folder as the GitHub project:

```text
leah-clark-merch/
```

## Print Uploads

Add updated print image files here:

```text
leah-clark-merch/prints/
```

Add web catalog copies here:

```text
leah-clark-merch/prints/display/
```

After adding images, update the `defaultData.prints` array in `server.js` with:

- unique `id`
- display `name`
- inventory `label`
- `size`
- `price`
- `image_url`
- `active`

Use the smaller `prints/display/` file for `image_url` so the mobile catalog stays fast. Keep the original high-resolution image in `prints/`.

## Document Uploads

Add project, booth, inventory, or workflow documents here:

```text
leah-clark-merch/documents/
```

The current Google Sheet schedule is stored as:

- `documents/leah-current-schedule.csv`
- `data/current-schedule.json`

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
git commit -m "Improve Leah merch app and add upload docs"
git push origin main
```
