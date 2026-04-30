# EventPass — Admin Dashboard
> Desktop event management system with barcode scanning, automated email dispatch, and live Google Sheets logging.

---

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Google Sheets Integration Setup](#google-sheets-integration-setup)
- [Building the Executable](#building-the-executable)
- [Distributing the App](#distributing-the-app)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

---

## Overview

EventPass is a standalone Windows desktop application built with Python, Flask, and pywebview. It loads attendee data from a Google Sheet, generates personalized profile cards with barcodes, sends them via email, and logs all scan activity back to a Google Sheet in real time — all from a single `.exe` file.

---

## Features

- **Sheet Import** — Load attendee data directly from a Google Sheets URL (CSV export)
- **Profile Card Generation** — Auto-generates barcode ID cards rendered as PNG images
- **Email Automation** — Sends profile cards via Gmail SMTP on payment confirmation
- **Barcode Scanner** — Scan attendee IDs at the event gate; logs entry in real time
- **Google Sheets Live Logging** — Pushes every scan record directly to a Google Sheet
- **Offline Storage** — All scan data persists locally in browser localStorage
- **Export** — Export full scan logs as `.xlsx` or raw JSON

---

## Requirements

- Windows 10 or later
- Python 3.10
- pip packages (see Installation)

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/eventpass.git
cd eventpass
```

**2. Make sure you are using Python 3.10**
```bash
py -3.10 --version
```

**3. Install all dependencies**
```bash
py -3.10 -m pip install flask flask-cors pillow pywebview pyinstaller gspread google-auth-oauthlib
```

**4. Run the app in development mode**
```bash
py -3.10 app.py
```

---

## Google Sheets Integration Setup

EventPass writes scan logs directly to a Google Sheet using the Google Sheets API with OAuth 2.0. This requires a one-time setup in Google Cloud Console.

### Step 1 — Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **New Project** → name it `EventPass` → click **Create**
3. Make sure the project is selected in the top dropdown

### Step 2 — Enable the Google Sheets API

1. Go to **APIs & Services → Library**
2. Search for **Google Sheets API** → click it → click **Enable**

### Step 3 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. If prompted, configure the OAuth consent screen first:
   - User Type: **External**
   - App name: `EventPass`
   - Fill in required fields → Save
4. Back on Credentials → Create OAuth 2.0 Client ID:
   - Application type: **Desktop app**
   - Name: `EventPass`
   - Click **Create**
5. Click **Download JSON** → rename the file to `google_credentials.json`

### Step 4 — Add a Test User (required while app is unverified)

1. Go to **APIs & Services → OAuth consent screen**
2. Scroll to **Test users** → click **+ Add Users**
3. Enter the Gmail address you will use to log in → click **Save**

### Step 5 — Place the credentials file

Put `google_credentials.json` in the **same folder as `EventPass.exe`** (or next to `app.py` during development).

### Step 6 — Connect your Google Account (one-time per machine)

1. Open the app → go to the **Settings** tab
2. Paste your Google Sheet URL in the input field → click **Save**
3. Click **🔗 Connect Google Account**
4. A browser tab opens → sign in with your Google account → click **Allow**
5. The badge updates to **"● Google account linked"**

From this point on, all scans are pushed to the sheet automatically. No login prompt will appear again on the same machine.

---

## Building the Executable

Run this command from the project folder using CMD (not PowerShell):

```bash
py -3.10 -m PyInstaller --onefile --noconsole --name EventPass --icon=icon.ico --hidden-import=google_auth_oauthlib --hidden-import=google_auth_oauthlib.flow --hidden-import=google.auth.transport.requests --hidden-import=google.oauth2.credentials --hidden-import=gspread app.py
```

The compiled executable will be output to:
```
dist/EventPass.exe
```

---

## Distributing the App

After building, the `dist/` folder must contain **both files** for the app to work:

```
dist/
  EventPass.exe
  google_credentials.json
```

> `google_credentials.json` must always be in the same folder as the exe. The Google OAuth token is saved per-machine at `C:\Users\[username]\.eventpass_token.json` after the first login, so end users only need to log in once.

---

## Usage Guide

### Loading Attendee Data
1. Go to the **Home** tab
2. Open your Google Sheet → click **Share → Anyone with the link can view**
3. Copy the sheet URL and paste it into the Sheet URL input
4. Click **Load Sheet** — attendee rows appear in the Users tab

### Sending Profile Cards
- Cards are auto-sent to all **Paid** attendees on sheet load (if Auto-send is enabled in Settings)
- To send manually, click **Send Card** on any row in the Users tab

### Scanning at the Event
1. Go to the **Scanner** tab
2. Connect a USB barcode scanner (acts as a keyboard)
3. Scan an attendee's barcode — their profile loads instantly
4. Each scan is logged locally and pushed to Google Sheets in real time

### Syncing Logs to Google Sheets
- Every scan auto-pushes to the configured sheet
- To bulk-push all existing logs, go to **Settings → ⬆ Sync All**

---

## Project Structure

```
eventpass/
  app.py                  # Main application (Flask + pywebview + all UI)
  icon.ico                # App icon
  google_credentials.json # OAuth credentials (not committed to git)
  make_icon.py            # Icon generation helper script
  dist/
    EventPass.exe         # Compiled output
    google_credentials.json
```

> Add `google_credentials.json` and `dist/` to your `.gitignore` — never commit credentials to a public repository.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'webview'` | Run with `py -3.10 app.py` — pywebview is installed for Python 3.10 only |
| `No module named 'google_auth_oauthlib'` | Run `py -3.10 -m pip install google-auth-oauthlib gspread` |
| `Access blocked: app has not completed verification` | Add your Gmail to Test Users in Google Cloud Console (see Step 4 above) |
| Browser tab does not open on Connect | Make sure `google_credentials.json` is next to the exe; try running as administrator |
| Logs not appearing in sheet | Check the sheet URL is saved in Settings; click Sync All to force push |
| PyInstaller uses wrong Python version | Use `py -3.10 -m PyInstaller` instead of just `pyinstaller` |

---

## Configuration (inside app.py)

Before building, update these values near the top of `app.py`:

```python
GMAIL_USER     = 'your_gmail@gmail.com'
GMAIL_APP_PASS = 'xxxx xxxx xxxx xxxx'   # Gmail App Password (not your login password)
PORT           = 3000
```

To generate a Gmail App Password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

---

*EventPass v2 — Created by Jan Clyde T. Talosig*
