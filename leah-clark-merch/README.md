# 🎨 Leah Clark Merch Order System

A convention booth ordering system that lets fans pre-select available catalog items while in line, saving time at point of sale.

## Features

- **QR Code Scanning**: Customers scan a code to browse available convention items
- **Pre-Order Selection**: Customers select items while waiting in line
- **Email-Based Orders**: Orders tied to email for easy lookup
- **Real-Time Admin Dashboard**: Sales staff see orders instantly
- **Auto-Refresh**: Dashboard updates every 5 seconds with sound notification for new orders
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
2. **Open** `your-url.com/admin` on your tablet/laptop
3. Keep the admin page open - it auto-refreshes

### Customer Flow

1. Customer scans QR code with their phone
2. Enters their email address
3. Browses and selects prints they want
4. Taps "Save My Order"
5. When they reach the booth, gives their email
6. You search their email in the admin panel
7. Their order appears with all items listed
8. Complete the sale, click "Complete Sale"

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
│   ├── index.html     # Customer ordering page
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

The product catalog is sourced from a read-only snapshot of the shared Google Sheet:

- `documents/leah-standard-prints-8_5x11.csv` keeps a sanitized source export.
- `documents/leah-large-prints-11x17.csv` keeps a sanitized source export.
- `documents/leah-product-catalog-snapshot.csv` keeps the sanitized product snapshot with only quantity, image type, name, image, size, price, and availability.
- `data/product-catalog.json` powers `/api/prints` with the same sanitized snapshot plus internal ids for ordering.

---

## 🔧 Customization

### Updating The Catalog Snapshot

Update the shared Google Sheet first. Then download/export the current workbook snapshot and run:

```bash
python3 scripts/build_catalog_snapshot.py /path/to/convention_inventory_2026.xlsx --output data/product-catalog.json --csv-output documents/leah-product-catalog-snapshot.csv
python3 scripts/download_catalog_images.py --catalog data/product-catalog.json --out-dir prints/catalog --manifest prints/catalog/manifest.json --rewrite-catalog --local-only-availability --csv-output documents/leah-product-catalog-snapshot.csv
```

Rows become orderable only when the snapshot has a positive quantity, a downloaded local image, and a known price. Rows missing a local image or price stay in `data/product-catalog.json` as `needs image` or `needs price` so they can be reviewed without appearing to customers.

### Changing Prices

Edit the price map in `scripts/build_catalog_snapshot.py` after confirming the price convention for that sheet tab, then regenerate `data/product-catalog.json`.

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

**Orders not appearing**
- Refresh the admin page
- Check that the server is running
- On Render free tier, the server may sleep - first request wakes it up

---

## 💡 Tips for Convention Success

1. **Test everything** before the convention
2. **Have a backup** - screenshot orders periodically
3. **Bring a charger** for your display device
4. **Print multiple QR signs** for different line positions
5. **Train staff** on searching by email
6. **Keep the admin page visible** to catch orders immediately

---

Made with ❤️ for Leah Clark
