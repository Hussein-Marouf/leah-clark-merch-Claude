# 🎨 Leah Clark Convention Catalog

A lightweight convention catalog that lets fans scan a QR code and browse the items planned for sale.

## Features

- **QR Code Scanning**: Customers scan a code to browse convention items
- **Simple Catalog Cards**: Each item shows only the image, print name, material, and size
- **Local Image Cache**: Catalog images can be served from `prints/catalog/`
- **Mobile-Friendly**: Works on any phone

---

## 🚀 DEPLOYMENT GUIDE (Step-by-Step)

### Option 1: Deploy to Render.com (FREE - Recommended)

Render offers free hosting perfect for convention use.

#### Step 1: Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in (or create account)
2. Click the **+** icon → **New repository**
3. Name it: `leah-clark-merch`
4. Make it **Public**
5. Click **Create repository**

#### Step 2: Upload Your Files

**Option A: Using GitHub Web Interface (Easiest)**

1. On your new repo page, click **"uploading an existing file"**
2. Drag and drop ALL files from your `leah-clark-merch` folder:
   - `package.json`
   - `server.js`
   - `.gitignore`
   - `public/` folder (with index.html, admin.html, qr.html)
   - `prints/` folder (with all image files)
3. Click **Commit changes**

**Option B: Using Terminal (If you have Git)**

```bash
cd leah-clark-merch
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/leah-clark-merch.git
git push -u origin main
```

#### Step 3: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (use GitHub login)
2. Click **New +** → **Web Service**
3. Connect your GitHub account if prompted
4. Find and select `leah-clark-merch`
5. Configure:
   - **Name**: `leah-clark-merch`
   - **Region**: Choose closest to your convention
   - **Branch**: `main`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Instance Type**: **Free**
6. Click **Create Web Service**
7. Wait 2-3 minutes for deployment
8. Your URL will be: `https://leah-clark-merch.onrender.com`

---

### Option 2: Deploy to Railway (Alternative)

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **New Project** → **Deploy from GitHub repo**
4. Select your repository
5. Railway auto-detects Node.js and deploys
6. Click **Generate Domain** to get your URL

---

### Option 3: Run Locally (For Testing)

#### Prerequisites
- Node.js 18+ installed ([download here](https://nodejs.org))

#### Steps

1. **Open Terminal/Command Prompt**

2. **Navigate to your project folder**
   ```bash
   cd path/to/leah-clark-merch
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Start the server**
   ```bash
   npm start
   ```

5. **Access the system**
   - Customer Page: http://localhost:3000
   - Admin Dashboard: http://localhost:3000/admin
   - QR Code Page: http://localhost:3000/qr

---

## 📱 Using the System at Conventions

### Before the Convention

1. **Deploy** using one of the methods above
2. Go to `your-url.com/qr`
3. Enter your live URL in the input box
4. Click **Generate QR Code**
5. Click **Print Sign** to print the QR code sign
6. Laminate the sign for durability

### At the Booth

1. **Display** the QR code sign prominently
2. Customers scan the code with their phone
3. The catalog opens with image, print name, material, and size only

### Customer Flow

1. Customer scans QR code with their phone
2. Browses the available convention items
3. Checks the print name, material, and size before visiting the booth

---

## 📂 Project Structure

```
leah-clark-merch/
├── server.js          # Main server file
├── package.json       # Dependencies
├── .gitignore         # Git ignore rules
├── db.json            # Database (auto-created)
├── data/
│   ├── current-schedule.json
│   └── product-catalog.json
├── scripts/
│   └── build_catalog_snapshot.py
├── docs/              # UI/UX audit and upload notes
├── documents/         # Booth/project documents and sheet exports
├── public/
│   ├── index.html     # Customer catalog page
│   ├── admin.html     # Sales dashboard
│   └── qr.html        # QR code display
└── prints/
    └── README.md      # Optional local art storage notes
```

---

## 📄 Documents

Project documents can be added to the `documents/` folder before committing to GitHub. Review any files for customer data, payment details, private addresses, or API keys before pushing to a public repository.

The `docs/` folder contains internal project notes, including the UI/UX audit, white glove audit, and GitHub upload checklist.

The current event schedule is sourced from the shared Google Sheet and saved in two places:

- `documents/leah-current-schedule.csv` keeps the raw sheet export.
- `data/current-schedule.json` powers `/api/schedule` and `/schedule`.

The QR product catalog is sourced from the current inventory document, matched to the labeled artwork ZIP, and served from optimized local images in `prints/current-inventory/`:

- `documents/Current_Inventory_Lst with Photos to USe.docx` is the upcoming-event inventory source.
- `ALL ARTWORK /Merch_Art LeahClark-20260505T183511Z-3-001.zip` is the labeled artwork source used locally to rebuild images.
- `documents/leah-indianapolis-popcon-catalog.csv` is the public catalog export with only name, image, material, and size.
- `documents/leah-current-inventory-artwork-audit.csv` lists matched inventory rows and rows that still need artwork review.
- `data/product-catalog.json` powers `/api/prints` with the same public catalog plus internal ids.
- `prints/current-inventory/` contains web-optimized catalog images generated from the ZIP/fallback artwork.

Legacy sheet exports are still kept for audit:

- `documents/leah-standard-prints-8_5x11.csv` keeps a sanitized source export.
- `documents/leah-large-prints-11x17.csv` keeps a sanitized source export.
- `documents/leah-product-catalog-snapshot.csv` keeps the older sanitized product snapshot.

---

## 🔧 Customization

### Updating The Catalog Snapshot

For the Indianapolis QR catalog, update the inventory document and artwork ZIP:

```text
documents/Current_Inventory_Lst with Photos to USe.docx
ALL ARTWORK /Merch_Art LeahClark-20260505T183511Z-3-001.zip
```

Then rebuild the current-inventory app catalog:

```bash
python3 scripts/build_catalog_from_artwork_zip.py
```

The builder writes:

- `data/product-catalog.json`
- `documents/leah-indianapolis-popcon-catalog.csv`
- `documents/leah-current-inventory-artwork-audit.csv`
- `prints/current-inventory/`

If you manually edit the public CSV instead, rebuild from it with:

```bash
python3 scripts/build_catalog_from_csv.py
```

If you need a fresh legacy workbook export later, download/export the current workbook snapshot and run:

```bash
python3 scripts/build_catalog_snapshot.py /path/to/convention_inventory_2026.xlsx --output data/product-catalog.json --csv-output documents/leah-product-catalog-snapshot.csv
python3 scripts/download_catalog_images.py --catalog data/product-catalog.json --out-dir prints/catalog --manifest prints/catalog/manifest.json --rewrite-catalog --local-only --csv-output documents/leah-product-catalog-snapshot.csv
```

Rows appear in the QR catalog when the current inventory row has a safe artwork match, print name, material, and size. Rows without a safe match stay in the artwork audit and do not appear to customers.

### Resetting Orders

Delete the `db.json` file and restart the server.

---

## 🔒 Security Notes

- The admin panel has no password protection (intentional for convention speed)
- For added security, you can bookmark the admin URL rather than linking it publicly
- Orders are stored in a JSON file - back it up if you need records

---

## ⚠️ Troubleshooting

**Server won't start**
- Make sure Node.js 18+ is installed: `node --version`
- Run `npm install` before starting

**Images not showing**
- Check that each catalog row has a non-empty `image` value in `data/product-catalog.json`
- Check `prints/catalog/manifest.json` for Drive links that redirected to Google sign-in
- Google Drive thumbnail links must be downloadable or replaced with local app images

**QR code shows wrong URL**
- Enter your full live URL in the QR page input
- Include `https://` at the beginning

**Catalog not appearing**
- Refresh the page
- Check that the server is running
- On Render free tier, the server may sleep - first request wakes it up

---

## 💡 Tips for Convention Success

1. **Test everything** before the convention
2. **Have a backup** - keep a printed or saved copy of the catalog
3. **Bring a charger** for your display device
4. **Print multiple QR signs** for different line positions
5. **Check images on mobile** before the doors open
6. **Keep the CSV updated** when items are added or removed

---

Made with ❤️ for Leah Clark
