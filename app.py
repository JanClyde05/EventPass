"""
╔══════════════════════════════════════════════════════════════╗
║               EventPass v2 — Desktop App                     ║
║               Created by Jan Clyde T. Talosig                ║
║                                                              ║
║  pip install flask flask-cors pillow pywebview pyinstaller   ║
║                                                              ║
║  py make_icon.py                                             ║
║  pyinstaller --onefile --noconsole                           ║
║              --name EventPass --icon=icon.ico app.py         ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys, os, threading, base64, time, textwrap
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.image     import MIMEImage

from flask      import Flask, request, jsonify, Response
from flask_cors import CORS
import webview

# ════════════════════════════════════════════════════════════
#  CONFIGURATION  — edit before compiling
# ════════════════════════════════════════════════════════════
GMAIL_USER     = 'janclydettalosig0@gmail.com'
GMAIL_APP_PASS = 'feyy obyg rozs tmej'
PORT           = 3000

# ════════════════════════════════════════════════════════════
#  DASHBOARD HTML  (fully embedded — zero external files)
# ════════════════════════════════════════════════════════════
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>EventPass — Admin Dashboard</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.4.1/papaparse.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.6/JsBarcode.all.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet"/>

<style>
:root {
  --bg:       #0a0c0f;
  --surface:  #111419;
  --panel:    #181c23;
  --border:   #252a35;
  --accent:   #00e5a0;
  --accent2:  #0077ff;
  --warn:     #ff5f3d;
  --muted:    #4a5568;
  --text:     #c8d0de;
  --text-dim: #6b7a90;
  --mono:     'Share Tech Mono', monospace;
  --sans:     'Barlow Condensed', sans-serif;
  --body:     'Barlow', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--body);
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
  overflow-x: hidden;
}

body::before {
  content: '';
  position: fixed; inset: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px,
    rgba(0,229,160,.015) 2px, rgba(0,229,160,.015) 4px);
  pointer-events: none;
  z-index: 9999;
}

/* ── Header ── */
header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 32px; height: 56px;
  background: var(--surface); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.logo {
  font-family: var(--sans); font-weight: 700; font-size: 22px;
  letter-spacing: 4px; text-transform: uppercase;
  color: var(--accent); text-shadow: 0 0 20px rgba(0,229,160,.4);
}
.logo span { color: var(--text-dim); font-weight: 300; }
.status-bar {
  display: flex; align-items: center; gap: 20px;
  font-family: var(--mono); font-size: 11px; color: var(--text-dim);
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); box-shadow: 0 0 6px var(--accent);
  display: inline-block; margin-right: 6px;
  animation: pulse 2s infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .4; } }

/* ── Layout ── */
.shell { display: grid; grid-template-columns: 220px 1fr; min-height: calc(100vh - 56px); }

/* ── Sidebar ── */
.sidebar {
  background: var(--surface); border-right: 1px solid var(--border);
  padding: 24px 0; display: flex; flex-direction: column; gap: 4px;
}
.nav-label {
  padding: 8px 20px 4px;
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 2px; color: var(--muted); text-transform: uppercase;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 20px; cursor: pointer;
  border-left: 3px solid transparent; transition: all .2s;
  color: var(--text-dim); font-family: var(--sans);
  font-size: 15px; font-weight: 600; letter-spacing: .5px; text-transform: uppercase;
}
.nav-item:hover { background: var(--panel); color: var(--text); }
.nav-item.active {
  border-left-color: var(--accent);
  background: rgba(0,229,160,.06); color: var(--accent);
}
.nav-icon { font-size: 16px; }

/* ── Main ── */
main { padding: 32px; overflow-y: auto; }
.section { display: none; }
.section.active { display: block; }
.section-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 24px; }
.section-title {
  font-family: var(--sans); font-size: 28px; font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; color: #fff;
}
.section-sub { font-family: var(--mono); font-size: 11px; color: var(--muted); }

/* ── Cards ── */
.card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 4px; padding: 24px; margin-bottom: 20px;
}
.card-title {
  font-family: var(--mono); font-size: 11px;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--accent); margin-bottom: 16px;
  display: flex; align-items: center; gap: 8px;
}
.card-title::before {
  content: ''; width: 3px; height: 14px;
  background: var(--accent); border-radius: 1px;
}

/* ── Inputs ── */
.input-row { display: flex; gap: 12px; align-items: stretch; }
input[type="text"], input[type="url"] {
  flex: 1; background: var(--bg); border: 1px solid var(--border);
  border-radius: 3px; color: var(--text); font-family: var(--mono);
  font-size: 12px; padding: 10px 14px; outline: none; transition: border-color .2s;
}
input:focus { border-color: var(--accent); }
input::placeholder { color: var(--muted); }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer;
  font-family: var(--sans); font-size: 14px; font-weight: 700;
  letter-spacing: 1px; text-transform: uppercase;
  transition: all .2s; white-space: nowrap;
}
.btn-primary { background: var(--accent); color: #000; }
.btn-primary:hover { background: #00ffb2; box-shadow: 0 0 16px rgba(0,229,160,.4); }
.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn-ghost {
  background: rgba(255,255,255,.06); color: var(--text);
  border: 1px solid var(--border);
}
.btn-ghost:hover { background: rgba(255,255,255,.1); }
.btn-confirm {
  background: rgba(0,119,255,.15); color: var(--accent2);
  border: 1px solid rgba(0,119,255,.3);
}
.btn-confirm:hover { background: rgba(0,119,255,.3); }
.btn-confirm.done {
  background: rgba(0,229,160,.1); color: var(--accent);
  border-color: rgba(0,229,160,.3); cursor: default;
}

/* ── Filter Bar ── */
.filter-bar {
  display: flex; gap: 10px; align-items: center;
  flex-wrap: wrap; margin-bottom: 16px;
  padding-bottom: 16px; border-bottom: 1px solid var(--border);
}
.filter-bar input[type="text"] { flex: 1; min-width: 160px; }
.filter-bar select {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 3px; color: var(--text); font-family: var(--mono);
  font-size: 11px; padding: 10px 12px; outline: none;
  cursor: pointer; transition: border-color .2s; letter-spacing: .5px;
}
.filter-bar select:focus { border-color: var(--accent); }
.filter-bar select option { background: var(--panel); }
.row-count {
  font-family: var(--mono); font-size: 11px;
  color: var(--muted); white-space: nowrap; margin-left: auto;
}

/* ── Table ── */
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead tr { border-bottom: 2px solid var(--border); }
th {
  text-align: left; padding: 10px 14px;
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 2px; color: var(--muted);
  text-transform: uppercase; white-space: nowrap;
}
td { padding: 10px 14px; border-bottom: 1px solid rgba(37,42,53,.7); vertical-align: middle; }
tr:hover td { background: rgba(255,255,255,.02); }

.badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px; border-radius: 20px;
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 1px; text-transform: uppercase;
}
.badge-pending  { background: rgba(255,95,61,.1);  color: var(--warn);    border: 1px solid rgba(255,95,61,.2); }
.badge-paid     { background: rgba(0,229,160,.1);  color: var(--accent);  border: 1px solid rgba(0,229,160,.2); }
.badge-scanned  { background: rgba(0,119,255,.1);  color: var(--accent2); border: 1px solid rgba(0,119,255,.2); }
.badge-not-scan { color: var(--muted); font-family: var(--mono); font-size: 12px; }

/* ── Toast ── */
#toast-container {
  position: fixed; bottom: 28px; right: 28px;
  display: flex; flex-direction: column; gap: 10px; z-index: 9998;
}
.toast {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 4px; padding: 12px 18px;
  font-family: var(--mono); font-size: 12px;
  min-width: 240px; display: flex; align-items: center; gap: 10px;
  animation: slideIn .3s ease; border-left: 3px solid var(--accent);
}
.toast.error { border-left-color: var(--warn); }
.toast.info  { border-left-color: var(--accent2); }
@keyframes slideIn {
  from { transform: translateX(20px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

/* ── Spinner ── */
.spinner {
  width: 16px; height: 16px;
  border: 2px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin .7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Stats ── */
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-box {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 4px; padding: 20px;
  position: relative; overflow: hidden;
}
.stat-box::after {
  content: ''; position: absolute; top: 0; right: 0;
  width: 3px; height: 100%; background: var(--accent); opacity: .3;
}
.stat-val {
  font-family: var(--sans); font-size: 36px; font-weight: 700;
  color: #fff; line-height: 1;
}
.stat-label {
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 2px; color: var(--muted);
  text-transform: uppercase; margin-top: 6px;
}

/* ── Scanner ── */
.scanner-input-wrap { position: relative; margin-bottom: 20px; }
.scanner-icon {
  position: absolute; left: 14px; top: 50%;
  transform: translateY(-50%); font-size: 18px; pointer-events: none;
}
#scanner-input {
  width: 100%; padding-left: 44px; font-size: 15px; height: 48px;
}
#scanner-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0,229,160,.08);
}

.profile-display {
  display: grid; grid-template-columns: auto 1fr;
  gap: 28px; align-items: start;
}
.profile-left { display: flex; flex-direction: column; gap: 14px; }
.profile-barcode-wrap svg {
  background: rgba(0,229,160,.05);
  padding: 10px; border-radius: 4px;
  border: 1px solid rgba(0,229,160,.15); display: block;
}
.profile-card-preview {
  max-width: 220px; border-radius: 4px;
  border: 1px solid var(--border); display: none;
}
.profile-fields { display: grid; gap: 12px; }
.profile-field label {
  font-family: var(--mono); font-size: 10px;
  letter-spacing: 2px; color: var(--muted);
  text-transform: uppercase; display: block; margin-bottom: 3px;
}
.profile-field .val {
  font-family: var(--sans); font-size: 20px; font-weight: 600; color: #fff;
}

.scan-banner {
  padding: 10px 16px; border-radius: 3px;
  font-family: var(--mono); font-size: 12px;
  margin-bottom: 16px; display: none; border-left: 3px solid;
}
.scan-banner.success {
  border-left-color: var(--accent); background: rgba(0,229,160,.07);
  color: var(--accent); display: block;
}
.scan-banner.warning {
  border-left-color: var(--warn); background: rgba(255,95,61,.07);
  color: var(--warn); display: block;
}

/* ── Toggle ── */
.toggle-row {
  display: flex; align-items: center;
  justify-content: space-between; padding: 10px 0;
}
.toggle { position: relative; display: inline-block; width: 44px; height: 22px; flex-shrink: 0; }
.toggle input { display: none; }
.toggle-slider {
  position: absolute; inset: 0;
  background: var(--border); border-radius: 22px;
  transition: .3s; cursor: pointer;
}
.toggle-slider::before {
  content: ''; position: absolute;
  width: 16px; height: 16px; left: 3px; top: 3px;
  background: var(--text-dim); border-radius: 50%; transition: .3s;
}
input:checked + .toggle-slider { background: rgba(0,229,160,.3); }
input:checked + .toggle-slider::before {
  transform: translateX(22px); background: var(--accent);
}

/* ── Misc ── */
#gas-url-input {
  width: 100%; font-size: 12px; padding: 10px 14px;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 3px; color: var(--text); font-family: var(--mono);
  outline: none; transition: border-color .2s; margin-top: 8px;
}
#gas-url-input:focus { border-color: var(--accent); }

.helper {
  font-family: var(--mono); font-size: 10px;
  color: var(--muted); margin-top: 6px; line-height: 1.7;
}
.empty-state {
  text-align: center; padding: 40px;
  color: var(--muted); font-family: var(--mono); font-size: 12px;
}
.empty-icon { font-size: 36px; margin-bottom: 12px; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Hidden card render ── */
#card-render {
  position: fixed; top: -9999px; left: -9999px;
  width: 520px; background: #fff;
  font-family: 'Barlow Condensed', sans-serif;
  border-radius: 8px; overflow: hidden;
}
.card-header-render {
  background: #0a0c0f; color: #00e5a0;
  padding: 24px 28px 20px;
  display: flex; justify-content: space-between; align-items: center;
}
.card-header-render .org {
  font-size: 13px; letter-spacing: 3px; text-transform: uppercase; opacity: .7;
}
.card-header-render .event-name {
  font-size: 22px; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; color: #fff; margin-top: 2px;
}
.card-header-render .badge-render {
  background: rgba(0,229,160,.2); border: 1px solid rgba(0,229,160,.4);
  color: #00e5a0; padding: 6px 14px; border-radius: 20px;
  font-size: 12px; letter-spacing: 2px; text-transform: uppercase;
}
.card-body-render { padding: 24px 28px; background: #fff; }
.card-name-render {
  font-size: 34px; font-weight: 700; color: #0a0c0f;
  letter-spacing: 1px; text-transform: uppercase;
  line-height: 1; margin-bottom: 12px;
}
.card-meta-render { display: flex; gap: 24px; margin-bottom: 20px; }
.card-meta-item .label-r {
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: #8a9ab0; margin-bottom: 2px;
}
.card-meta-item .val-r { font-size: 16px; font-weight: 600; color: #1a1e28; }
.card-divider { border: none; border-top: 1px solid #e8ecf2; margin: 16px 0; }
.card-barcode-render {
  display: flex; flex-direction: column;
  align-items: center; gap: 8px; padding: 12px 0 4px;
}
.card-barcode-label {
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase; color: #8a9ab0;
}
.card-footer-render {
  background: #f5f7fa; padding: 12px 28px;
  display: flex; justify-content: space-between; align-items: center;
  border-top: 1px solid #e8ecf2;
}
.card-footer-render .foot-label {
  font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #8a9ab0;
}
.card-footer-render .foot-val { font-size: 13px; font-weight: 600; color: #1a1e28; }
</style>
</head>
<body>

<header>
  <div class="logo">Event<span>Pass</span> <span style="font-size:13px;letter-spacing:1px;">// ADMIN</span></div>
  <div class="status-bar">
    <span><span class="status-dot"></span>SYSTEM ONLINE</span>
    <span id="clock" style="font-size:12px;"></span>
  </div>
</header>

<div class="shell">
  <nav class="sidebar">
    <div class="nav-label">Navigation</div>
    <div class="nav-item active" data-section="import" onclick="navigate(this)">
      <span class="nav-icon">⬇</span> Import Data
    </div>
    <div class="nav-item" data-section="users" onclick="navigate(this)">
      <span class="nav-icon">◈</span> User Table
    </div>
    <div class="nav-item" data-section="scanner" onclick="navigate(this)">
      <span class="nav-icon">⬡</span> Barcode Scanner
    </div>
    <div class="nav-label" style="margin-top:16px;">Config</div>
    <div class="nav-item" data-section="config" onclick="navigate(this)">
      <span class="nav-icon">⚙</span> Settings
    </div>
  </nav>

  <main>

    <!-- ── IMPORT ── -->
    <section id="import" class="section active">
      <div class="section-header">
        <div class="section-title">Import</div>
        <div class="section-sub">// google sheets → csv pipeline</div>
      </div>

      <div class="card">
        <div class="card-title">Google Sheets URL</div>
        <div class="input-row">
          <input type="url" id="sheet-url"
                 placeholder="https://docs.google.com/spreadsheets/d/.../edit#gid=..."/>
          <button class="btn btn-primary" onclick="loadSheet()">
            <span id="load-btn-text">Load Sheet</span>
            <span id="load-spinner" style="display:none;" class="spinner"></span>
          </button>
        </div>
        <div class="helper">
          ① Paste your Google Sheets share URL above.<br>
          ② Sheet must be set to "Anyone with link can view".<br>
          ③ Expected columns: Timestamp · Email · Name · ID · Department · Number of Attendees · Payment Status
        </div>
      </div>

      <div class="card" id="preview-card" style="display:none;">
        <div class="card-title">Preview</div>
        <div id="preview-content"></div>
      </div>

      <div class="stats" id="stats-row" style="display:none;">
        <div class="stat-box">
          <div class="stat-val" id="stat-total">0</div>
          <div class="stat-label">Total Registrations</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="stat-paid">0</div>
          <div class="stat-label">Paid</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="stat-scanned">0</div>
          <div class="stat-label">Stubs Received</div>
        </div>
        <div class="stat-box">
          <div class="stat-val" id="stat-pending">0</div>
          <div class="stat-label">Awaiting Payment</div>
        </div>
      </div>
    </section>

    <!-- ── USERS ── -->
    <section id="users" class="section">
      <div class="section-header">
        <div class="section-title">Users</div>
        <div class="section-sub">// registration registry</div>
      </div>

      <div class="card">
        <div class="card-title">Registrant Table</div>

        <div class="filter-bar" id="filter-bar" style="display:none;">
          <input type="text" id="filter-search"
                 placeholder="Search name, ID, email…"
                 oninput="applyFilters()"/>
          <select id="filter-dept" onchange="applyFilters()">
            <option value="">All Departments</option>
          </select>
          <select id="filter-payment" onchange="applyFilters()">
            <option value="">All Payment Status</option>
            <option value="paid">Paid</option>
            <option value="unpaid">Unpaid</option>
          </select>
          <select id="filter-scan" onchange="applyFilters()">
            <option value="">All Scan Status</option>
            <option value="scanned">Scanned</option>
            <option value="not_scanned">Not Scanned</option>
          </select>
          <button class="btn btn-sm btn-ghost" onclick="clearFilters()">Clear Filters</button>
          <button class="btn btn-sm btn-primary" onclick="exportXlsx()">⬇ Export XLSX</button>
          <span class="row-count" id="row-count"></span>
        </div>

        <div class="table-wrap">
          <div id="table-container">
            <div class="empty-state">
              <div class="empty-icon">◈</div>
              No data loaded yet. Import a sheet first.
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── SCANNER ── -->
    <section id="scanner" class="section">
      <div class="section-header">
        <div class="section-title">Scanner</div>
        <div class="section-sub">// barcode lookup &amp; stub verification</div>
      </div>

      <div class="card">
        <div class="card-title">Scan or Enter Student ID</div>
        <div class="scanner-input-wrap">
          <span class="scanner-icon">⬡</span>
          <input type="text" id="scanner-input"
                 placeholder="Scan barcode or type student ID then press Enter…"
                 autocomplete="off" autocorrect="off" spellcheck="false"/>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="btn btn-primary btn-sm" onclick="triggerScan()">Scan</button>
          <button class="btn btn-sm btn-ghost" onclick="clearScannerResult()">Clear</button>
        </div>
        <p class="helper" style="margin-top:12px;">
          Connect a USB barcode scanner — it acts as a keyboard and auto-submits on Enter.
          Alternatively type a Student ID and press Enter or click Scan.
        </p>
      </div>

      <div id="profile-result" class="card" style="display:none;">
        <div class="card-title">Profile Found</div>
        <div id="scan-banner" class="scan-banner"></div>
        <div class="profile-display">
          <div class="profile-left">
            <div class="profile-barcode-wrap">
              <svg id="result-barcode"></svg>
            </div>
            <img id="res-card-preview" class="profile-card-preview" alt="Profile Card"/>
          </div>
          <div class="profile-fields">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div class="profile-field">
                <label>Full Name</label>
                <div class="val" id="res-name">—</div>
              </div>
              <div class="profile-field">
                <label>Student ID</label>
                <div class="val" id="res-id">—</div>
              </div>
              <div class="profile-field">
                <label>Department</label>
                <div class="val" id="res-dept" style="font-size:16px;">—</div>
              </div>
              <div class="profile-field">
                <label>Number of Attendees</label>
                <div class="val" id="res-att">—</div>
              </div>
              <div class="profile-field">
                <label>Email</label>
                <div class="val" id="res-email" style="font-size:13px;font-family:var(--mono);">—</div>
              </div>
              <div class="profile-field">
                <label>Payment Status</label>
                <div id="res-payment">—</div>
              </div>
              <div class="profile-field">
                <label>Scan Status</label>
                <div id="res-scan-status">—</div>
              </div>
            </div>
            <div class="profile-field">
              <label>Scan Timestamp</label>
              <div class="val" id="res-scan-ts"
                   style="font-size:14px;font-family:var(--mono);color:var(--text-dim);">—</div>
            </div>
          </div>
        </div>
      </div>

      <div id="profile-not-found" class="card" style="display:none;">
        <div style="text-align:center;padding:20px;color:var(--warn);font-family:var(--mono);font-size:13px;">
          ✕ ID not found in registry. Ensure the sheet is loaded and the ID is correct.
        </div>
      </div>
    </section>

    <!-- ── CONFIG ── -->
    <section id="config" class="section">
      <div class="section-header">
        <div class="section-title">Settings</div>
        <div class="section-sub">// configuration</div>
      </div>

      <div class="card">
        <div class="card-title">Backend Endpoint</div>
        <input type="text" id="gas-url-input"
               placeholder="http://127.0.0.1:3000/send"
               onchange="saveGasUrl()"/>
        <div class="helper" style="margin-top:10px;">
          The Flask backend is embedded in this app. Default:
          <span style="color:var(--accent);">http://127.0.0.1:3000/send</span>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Event Information</div>
        <div style="display:grid;gap:10px;">
          <div>
            <div class="helper" style="margin-bottom:4px;">ORGANIZATION NAME</div>
            <input type="text" id="org-name" placeholder="e.g. AcmeCorp"
                   style="width:100%;" onchange="saveConfig()"/>
          </div>
          <div>
            <div class="helper" style="margin-bottom:4px;">EVENT NAME</div>
            <input type="text" id="event-name" placeholder="e.g. Annual Summit 2025"
                   style="width:100%;" onchange="saveConfig()"/>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Email Automation</div>
        <div class="toggle-row">
          <div>
            <div style="font-weight:500;font-size:15px;">Auto-send on Paid Status</div>
            <div class="helper" style="margin-top:4px;">
              Automatically generate and email profile cards when payment is detected
              in the sheet. Runs silently after sheet load with 500ms between sends.
            </div>
          </div>
          <label class="toggle" style="margin-left:20px;">
            <input type="checkbox" id="auto-send-toggle" checked onchange="saveAutoSend()"/>
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Storage</div>
        <div style="display:flex;gap:12px;">
          <button class="btn btn-primary btn-sm" onclick="exportStorageJSON()">
            Export localStorage
          </button>
          <button class="btn btn-sm"
            style="background:rgba(255,95,61,.15);color:var(--warn);border:1px solid rgba(255,95,61,.3);"
            onclick="clearStorage()">Clear All Data</button>
        </div>
        <div class="helper" style="margin-top:10px;">
          Scan records, sent flags, and confirmed payments persist in browser localStorage.
        </div>
      </div>
    </section>

  </main>
</div>

<div id="toast-container"></div>

<!-- Hidden card for html2canvas -->
<div id="card-render">
  <div class="card-header-render">
    <div>
      <div class="org" id="cr-org">ORGANIZATION</div>
      <div class="event-name" id="cr-event">EVENT NAME</div>
    </div>
    <div class="badge-render">REGISTERED</div>
  </div>
  <div class="card-body-render">
    <div class="card-name-render" id="cr-name">FULL NAME</div>
    <div class="card-meta-render">
      <div class="card-meta-item">
        <div class="label-r">ID Number</div>
        <div class="val-r" id="cr-id">—</div>
      </div>
      <div class="card-meta-item">
        <div class="label-r">Department</div>
        <div class="val-r" id="cr-dept">—</div>
      </div>
      <div class="card-meta-item">
        <div class="label-r">Attendees</div>
        <div class="val-r" id="cr-att">—</div>
      </div>
      <div class="card-meta-item">
        <div class="label-r">Status</div>
        <div class="val-r" style="color:#00b37a;">✓ CONFIRMED</div>
      </div>
    </div>
    <hr class="card-divider"/>
    <div class="card-barcode-render">
      <div class="card-barcode-label">
        ATTENDEE NO. <span id="cr-att-no">—</span> · SCAN TO VERIFY
      </div>
      <svg id="card-barcode-svg"></svg>
    </div>
  </div>
  <div class="card-footer-render">
    <div>
      <div class="foot-label">Email</div>
      <div class="foot-val" id="cr-email">—</div>
    </div>
    <div style="text-align:right;">
      <div class="foot-label">Generated</div>
      <div class="foot-val" id="cr-date">—</div>
    </div>
  </div>
</div>

<script>
// ════════════════════════════════════════════════
//  STATE
// ════════════════════════════════════════════════
let rows         = [];
let filteredRows = [];
let payStatusKey = null;
let scanTimer    = null;


// ════════════════════════════════════════════════
//  FIELD EXTRACTION
// ════════════════════════════════════════════════
function normalizeRow(obj) {
  const out = {};
  for (const k of Object.keys(obj))
    out[k.trim().toLowerCase().replace(/\s+/g, '_')] = obj[k];
  return out;
}

function extractFields(row) {
  const r = normalizeRow(row);
  return {
    email: r.email || r.email_address || '',
    name:  r.name  || r.full_name     || '',
    id:    String(r.id || r.id_number || r.student_id || '').trim(),
    dept:  r.department || r.dept     || '',
    ts:    r.timestamp  || '',
    att:   r.number_of_attendees || r.attendees || '1',
  };
}

// ════════════════════════════════════════════════
//  PAYMENT DETECTION
// ════════════════════════════════════════════════
function detectPayKey(dataRows) {
  if (!dataRows.length) return null;
  return Object.keys(dataRows[0]).find(k => /paid|payment|status/i.test(k)) || null;
}

const PAID_VALUES = ['paid', 'yes', 'confirmed', '✓', 'true', '1'];

function isRowPaid(row) {
  if (payStatusKey && row[payStatusKey] !== undefined) {
    const v = String(row[payStatusKey] || '').trim().toLowerCase();
    if (PAID_VALUES.includes(v)) return true;
  }
  const f    = extractFields(row);
  const conf = getConfirmed();
  return !!(conf[f.email + '_' + f.id] &&
            conf[f.email + '_' + f.id].status === 'confirmed');
}

function getPayLabel(row) {
  if (payStatusKey && row[payStatusKey] !== undefined) {
    return String(row[payStatusKey] || '').trim() || 'Unpaid';
  }
  const f    = extractFields(row);
  const conf = getConfirmed();
  return (conf[f.email + '_' + f.id] &&
          conf[f.email + '_' + f.id].status === 'confirmed')
    ? 'Confirmed' : 'Pending';
}

// ════════════════════════════════════════════════
//  SCAN STATE  (localStorage: scanned_<id>)
// ════════════════════════════════════════════════
function getScanData(id) {
  if (!id) return null;
  try { return JSON.parse(localStorage.getItem('scanned_' + id)); }
  catch { return null; }
}

function setScanData(id, data) {
  if (!id) return;
  localStorage.setItem('scanned_' + id, JSON.stringify(data));
}

// ════════════════════════════════════════════════
//  SENT STATE  (localStorage: sent_<email>_<id>)
// ════════════════════════════════════════════════
function isAlreadySent(email, id) {
  return !!localStorage.getItem('sent_' + email + '_' + id);
}
function markSent(email, id) {
  localStorage.setItem('sent_' + email + '_' + id, 'true');
}

// ════════════════════════════════════════════════
//  CONFIRMED STORAGE  (manual confirm flow)
// ════════════════════════════════════════════════
function getConfirmed() {
  try { return JSON.parse(localStorage.getItem('ep_confirmed') || '{}'); }
  catch { return {}; }
}
function saveConfirmed(obj) {
  localStorage.setItem('ep_confirmed', JSON.stringify(obj));
}

// ════════════════════════════════════════════════
//  INIT
// ════════════════════════════════════════════════
window.addEventListener('DOMContentLoaded', () => {
  loadGasUrl();
  loadConfig();
  loadAutoSendToggle();
  updateClock();
  setInterval(updateClock, 1000);

  const si = document.getElementById('scanner-input');
  si.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); triggerScan(); }
  });
  si.addEventListener('input', e => {
    clearTimeout(scanTimer);
    if (e.target.value.trim().length >= 4) {
      scanTimer = setTimeout(triggerScan, 250);
    }
  });
});

function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toLocaleDateString('en-GB') + ' · ' +
    now.toLocaleTimeString('en-GB', { hour12: false });
}

// ════════════════════════════════════════════════
//  NAVIGATION
// ════════════════════════════════════════════════
function navigate(el) {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  el.classList.add('active');
  const id = el.dataset.section;
  document.getElementById(id).classList.add('active');
  if (id === 'scanner') {
    setTimeout(() => document.getElementById('scanner-input').focus(), 80);
  }
}

// ════════════════════════════════════════════════
//  CONFIG HELPERS
// ════════════════════════════════════════════════
function saveGasUrl() {
  localStorage.setItem('ep_gas_url',
    document.getElementById('gas-url-input').value.trim());
}
function loadGasUrl() {
  document.getElementById('gas-url-input').value =
    localStorage.getItem('ep_gas_url') || 'http://127.0.0.1:3000/send';
}
function saveConfig() {
  localStorage.setItem('ep_org',   document.getElementById('org-name').value.trim());
  localStorage.setItem('ep_event', document.getElementById('event-name').value.trim());
}
function loadConfig() {
  document.getElementById('org-name').value   = localStorage.getItem('ep_org')   || '';
  document.getElementById('event-name').value = localStorage.getItem('ep_event') || '';
}
function getOrg()    { return localStorage.getItem('ep_org')     || 'ORGANIZATION'; }
function getEvent()  { return localStorage.getItem('ep_event')   || 'EVENT'; }
function getGasUrl() { return localStorage.getItem('ep_gas_url') || 'http://127.0.0.1:3000/send'; }

function saveAutoSend() {
  localStorage.setItem('ep_auto_send',
    document.getElementById('auto-send-toggle').checked ? 'true' : 'false');
}
function loadAutoSendToggle() {
  document.getElementById('auto-send-toggle').checked =
    localStorage.getItem('ep_auto_send') !== 'false';
}
function isAutoSendEnabled() {
  return localStorage.getItem('ep_auto_send') !== 'false';
}

// ════════════════════════════════════════════════
//  STORAGE MANAGEMENT
// ════════════════════════════════════════════════
function exportStorageJSON() {
  const data = {};
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    data[k] = localStorage.getItem(k);
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'eventpass_storage.json';
  a.click();
}

function clearStorage() {
  if (!confirm('Clear ALL EventPass data from localStorage? This cannot be undone.')) return;
  const keys = [];
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (k.startsWith('ep_') || k.startsWith('scanned_') ||
        k.startsWith('sent_') || k.startsWith('card_img_')) keys.push(k);
  }
  keys.forEach(k => localStorage.removeItem(k));
  toast('EventPass storage cleared.', 'info');
  applyFilters();
  updateStats();
}

// ════════════════════════════════════════════════
//  SHEET LOADING
// ════════════════════════════════════════════════
function convertSheetUrl(raw) {
  const idMatch  = raw.match(/\/spreadsheets\/d\/([a-zA-Z0-9_-]+)/);
  const gidMatch = raw.match(/[#&?]gid=(\d+)/);
  if (!idMatch) return null;
  return `https://docs.google.com/spreadsheets/d/${idMatch[1]}/export?format=csv&gid=${gidMatch ? gidMatch[1] : '0'}`;
}

async function loadSheet() {
  const raw = document.getElementById('sheet-url').value.trim();
  if (!raw) { toast('Paste a Google Sheets URL first.', 'error'); return; }
  const csvUrl = convertSheetUrl(raw);
  if (!csvUrl) { toast('Could not parse Spreadsheet ID from URL.', 'error'); return; }

  setLoading(true);
  try {
    const res = await fetch(csvUrl);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const text = await res.text();
    const parsed = Papa.parse(text, { header: true, skipEmptyLines: true });
    rows         = parsed.data;
    payStatusKey = detectPayKey(rows);
    filteredRows = [...rows];

    populateDeptFilter();
    applyFilters();
    updateStats();
    showPreview(csvUrl);
    document.getElementById('filter-bar').style.display = 'flex';
    toast('Loaded ' + rows.length + ' rows successfully.');

    navigate(document.querySelector('[data-section="users"]'));

    if (isAutoSendEnabled()) setTimeout(autoSendPaidCards, 800);
  } catch(e) {
    toast('Failed to fetch sheet: ' + e.message, 'error');
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  document.getElementById('load-btn-text').textContent = on ? 'Loading…' : 'Load Sheet';
  document.getElementById('load-spinner').style.display = on ? 'inline-block' : 'none';
}

function showPreview(url) {
  document.getElementById('preview-card').style.display = 'block';
  document.getElementById('stats-row').style.display    = 'grid';
  document.getElementById('preview-content').innerHTML  =
    '<span style="font-family:var(--mono);font-size:11px;color:var(--accent);">CSV endpoint:</span><br>' +
    '<span style="font-family:var(--mono);font-size:11px;color:var(--text-dim);word-break:break-all;">' + url + '</span>';
}

// ════════════════════════════════════════════════
//  AUTO-SEND ON PAID
// ════════════════════════════════════════════════
async function autoSendPaidCards() {
  if (!isAutoSendEnabled() || !rows.length) return;
  const toSend = rows.filter(row => {
    const f = extractFields(row);
    return f.email && f.name && isRowPaid(row) && !isAlreadySent(f.email, f.id);
  });
  if (!toSend.length) return;
  toast('Auto-sending ' + toSend.length + ' pending card(s)…', 'info');

  for (const row of toSend) {
    const f = extractFields(row);
    try {
      const hash       = await sha256(f.name + '|' + f.id + '|' + f.dept);
      const barcodeVal = f.id ? f.id : hash.substring(0, 16).toUpperCase();
      const imageBase64 = await generateCardImage({
        email: f.email, name: f.name, id: f.id,
        department: f.dept, attendees: f.att, hash, barcodeVal
      });
      localStorage.setItem('card_img_' + f.email + '_' + f.id, imageBase64);
      await sendToBackend({ email: f.email, name: f.name, id: f.id, department: f.dept, imageBase64 });
      markSent(f.email, f.id);
      toast('Auto-sent → ' + f.name, 'info');
    } catch(e) {
      toast('Auto-send failed for ' + f.name + ': ' + e.message, 'error');
    }
    await new Promise(r => setTimeout(r, 500));
  }

  applyFilters();
  updateStats();
}

// ════════════════════════════════════════════════
//  FILTERS
// ════════════════════════════════════════════════
function populateDeptFilter() {
  const depts = [...new Set(rows.map(r => extractFields(r).dept).filter(Boolean))].sort();
  const sel   = document.getElementById('filter-dept');
  const cur   = sel.value;
  sel.innerHTML = '<option value="">All Departments</option>' +
    depts.map(d =>
      '<option value="' + esc(d) + '"' + (d === cur ? ' selected' : '') + '>' + esc(d) + '</option>'
    ).join('');
}

function applyFilters() {
  if (!rows.length) { filteredRows = []; renderTable([]); return; }

  const search  = document.getElementById('filter-search').value.trim().toLowerCase();
  const dept    = document.getElementById('filter-dept').value;
  const payment = document.getElementById('filter-payment').value;
  const scan    = document.getElementById('filter-scan').value;

  filteredRows = rows.filter(row => {
    const f = extractFields(row);
    if (search && !(f.name + f.id + f.email).toLowerCase().includes(search)) return false;
    if (dept    && f.dept !== dept) return false;
    if (payment === 'paid'       && !isRowPaid(row)) return false;
    if (payment === 'unpaid'     &&  isRowPaid(row)) return false;
    const sd = getScanData(f.id);
    if (scan === 'scanned'     && !sd) return false;
    if (scan === 'not_scanned' &&  sd) return false;
    return true;
  });

  document.getElementById('row-count').textContent =
    'Showing ' + filteredRows.length + ' of ' + rows.length + ' registrants';
  renderTable(filteredRows);
}

function clearFilters() {
  document.getElementById('filter-search').value  = '';
  document.getElementById('filter-dept').value    = '';
  document.getElementById('filter-payment').value = '';
  document.getElementById('filter-scan').value    = '';
  applyFilters();
}

// ════════════════════════════════════════════════
//  TABLE RENDERING
// ════════════════════════════════════════════════
function renderTable(data) {
  const container = document.getElementById('table-container');
  if (!data || !data.length) {
    container.innerHTML = rows.length
      ? '<div class="empty-state"><div class="empty-icon">◈</div>No rows match the current filters.</div>'
      : '<div class="empty-state"><div class="empty-icon">◈</div>No data loaded yet. Import a sheet first.</div>';
    return;
  }

  const rowsHtml = data.map((row, i) => {
    const f      = extractFields(row);
    const paid   = isRowPaid(row);
    const payLbl = getPayLabel(row);
    const sd     = getScanData(f.id);
    const sent   = isAlreadySent(f.email, f.id);

    const ea = JSON.stringify(f.email), na = JSON.stringify(f.name);
    const ia = JSON.stringify(f.id),   da = JSON.stringify(f.dept);
    const aa = JSON.stringify(f.att);

    return '<tr>' +
      '<td style="color:var(--muted);font-family:var(--mono);font-size:11px;">' + (i + 1) + '</td>' +
      '<td style="font-family:var(--mono);font-size:11px;color:var(--text-dim);">' + esc(f.ts.slice(0, 16)) + '</td>' +
      '<td style="font-weight:500;">' + esc(f.name) + '</td>' +
      '<td style="font-family:var(--mono);font-size:12px;color:var(--text-dim);">' + esc(f.email) + '</td>' +
      '<td style="font-family:var(--mono);font-size:12px;">' + esc(f.id) + '</td>' +
      '<td>' + esc(f.dept) + '</td>' +
      '<td style="text-align:center;">' + esc(f.att) + '</td>' +
      '<td>' + (paid
        ? '<span class="badge badge-paid">✓ ' + esc(payLbl) + '</span>'
        : '<span class="badge badge-pending">● ' + esc(payLbl) + '</span>'
      ) + '</td>' +
      '<td>' + (sd
        ? '<span class="badge badge-scanned">✓ Received</span>'
        : '<span class="badge-not-scan">—</span>'
      ) + '</td>' +
      '<td>' + (sent
        ? '<button class="btn btn-sm btn-confirm done" disabled>Sent ✓</button>'
        : '<button class="btn btn-sm btn-confirm" onclick="confirmPayment(' +
            ea + ',' + na + ',' + ia + ',' + da + ',' + aa + ')">Send Card</button>'
      ) + '</td>' +
      '</tr>';
  }).join('');

  container.innerHTML =
    '<table><thead><tr>' +
    '<th>#</th><th>Timestamp</th><th>Name</th><th>Email</th>' +
    '<th>ID</th><th>Dept</th><th>Att.</th>' +
    '<th>Payment</th><th>Scan Status</th><th>Action</th>' +
    '</tr></thead><tbody>' + rowsHtml + '</tbody></table>';
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ════════════════════════════════════════════════
//  STATS
// ════════════════════════════════════════════════
function updateStats() {
  document.getElementById('stat-total').textContent =
    rows.length;
  document.getElementById('stat-paid').textContent =
    rows.filter(r => isRowPaid(r)).length;
  document.getElementById('stat-scanned').textContent =
    rows.reduce((total, r) => {
        const f = extractFields(r);
        const scanned = getScanData(f.id);
        return total + (scanned ? parseInt(f.att || 1) : 0);
    }, 0);
  document.getElementById('stat-pending').textContent =
    Math.max(0, rows.length - rows.filter(r => isRowPaid(r)).length);
}

// ════════════════════════════════════════════════
//  MANUAL CONFIRM & SEND
// ════════════════════════════════════════════════
async function confirmPayment(email, name, id, dept, att) {
  if (!email) { toast('No email found for this row.', 'error'); return; }

  const hash       = await sha256(name + '|' + id + '|' + dept);
  const barcodeVal = id ? String(id).trim() : hash.substring(0, 16).toUpperCase();

  const confirmed = getConfirmed();
  confirmed[email + '_' + id] = {
    email, name, id, department: dept, attendees: att || '1',
    hash, barcodeVal, status: 'confirmed', ts: Date.now()
  };
  saveConfirmed(confirmed);

  toast('Confirmed ' + name + '. Generating card…', 'info');
  try {
    const imageBase64 = await generateCardImage({
      email, name, id, department: dept, attendees: att || '1', hash, barcodeVal
    });
    localStorage.setItem('card_img_' + email + '_' + id, imageBase64);
    await sendToBackend({ email, name, id, department: dept, imageBase64 });
    markSent(email, id);
    toast('Profile card emailed to ' + email + ' ✓');
  } catch(e) {
    toast('Email failed: ' + e.message, 'error');
  }

  applyFilters();
  updateStats();
}

// ════════════════════════════════════════════════
//  SHA-256
// ════════════════════════════════════════════════
async function sha256(str) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// ════════════════════════════════════════════════
//  CARD GENERATION
// ════════════════════════════════════════════════
async function generateCardImage({ email, name, id, department, attendees, hash, barcodeVal }) {
  document.getElementById('cr-org').textContent    = getOrg();
  document.getElementById('cr-event').textContent  = getEvent();
  document.getElementById('cr-name').textContent   = name.toUpperCase();
  document.getElementById('cr-id').textContent     = id;
  document.getElementById('cr-dept').textContent   = department;
  document.getElementById('cr-email').textContent  = email;
  document.getElementById('cr-date').textContent   = new Date().toLocaleDateString('en-GB');
  document.getElementById('cr-att').textContent    = attendees || '1';
  document.getElementById('cr-att-no').textContent = attendees || '1';

  const codeValue = barcodeVal || (id ? String(id).trim() : hash.substring(0, 16));
  JsBarcode('#card-barcode-svg', codeValue, {
    format: 'CODE128', lineColor: '#0a0c0f', background: 'transparent',
    width: 2, height: 55, displayValue: true, fontSize: 11,
    font: 'monospace', textMargin: 4
  });

  const canvas = await html2canvas(document.getElementById('card-render'),
    { scale: 2, useCORS: true, backgroundColor: '#fff' });
  return canvas.toDataURL('image/png').split(',')[1];
}

// ════════════════════════════════════════════════
//  SEND TO FLASK BACKEND
// ════════════════════════════════════════════════
async function sendToBackend({ email, name, id, department, imageBase64 }) {
  const backendUrl = getGasUrl();
  let res;
  try {
    res = await fetch(backendUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, name, id, department, imageBase64 })
    });
  } catch(e) {
    throw new Error('Cannot reach backend at ' + backendUrl + ': ' + e.message);
  }
  let data;
  try { data = await res.json(); }
  catch { throw new Error('Backend returned non-JSON (HTTP ' + res.status + ').'); }
  if (!res.ok || data.success === false)
    throw new Error(data.message || 'Backend error (HTTP ' + res.status + ').');
  return data;
}

// ════════════════════════════════════════════════
//  BARCODE SCANNER
// ════════════════════════════════════════════════
function triggerScan() {
  const val = document.getElementById('scanner-input').value.trim();
  if (val) finalizeBarcodeScan(val);
}

function finalizeBarcodeScan(scanned) {
  if (!scanned) return;
  document.getElementById('scanner-input').value = '';
  clearTimeout(scanTimer);

  const resultEl   = document.getElementById('profile-result');
  const notFoundEl = document.getElementById('profile-not-found');

  if (!rows.length) {
    toast('No sheet loaded. Import data first.', 'error');
    return;
  }

  const matchRow = rows.find(row => extractFields(row).id === scanned);
  if (!matchRow) {
    resultEl.style.display   = 'none';
    notFoundEl.style.display = 'block';
    toast('ID not found in registry.', 'error');
    return;
  }

  const f      = extractFields(matchRow);
  const sd     = getScanData(f.id);
  const banner = document.getElementById('scan-banner');

  if (sd) {
    banner.className   = 'scan-banner warning';
    banner.textContent = '⚠ Stub already received — ' + sd.timestamp;
    showProfileResult(f, matchRow, sd);
    toast('⚠ Already scanned — ' + sd.timestamp, 'error');
  } else {
    const ts      = new Date().toLocaleString('sv').replace('T', ' ').slice(0, 19);
    const newScan = { scanned: true, timestamp: ts };
    setScanData(f.id, newScan);
    banner.className   = 'scan-banner success';
    banner.textContent = '✓ ' + (f.att || 1) + ' attendee(s) recorded — ' + ts;
    showProfileResult(f, matchRow, newScan);
    toast('✓ Stub received for ' + f.name);
    applyFilters();
    updateStats();
  }

  resultEl.style.display   = 'block';
  notFoundEl.style.display = 'none';
}

function showProfileResult(f, row, scanData) {
  document.getElementById('res-name').textContent  = f.name  || '—';
  document.getElementById('res-id').textContent    = f.id    || '—';
  document.getElementById('res-dept').textContent  = f.dept  || '—';
  document.getElementById('res-att').textContent = f.att || '1';
  document.getElementById('res-email').textContent = f.email || '—';
  document.getElementById('res-scan-ts').textContent =
    scanData ? scanData.timestamp : '—';

  const paid = isRowPaid(row);
  document.getElementById('res-payment').innerHTML = paid
    ? '<span class="badge badge-paid">✓ ' + esc(getPayLabel(row)) + '</span>'
    : '<span class="badge badge-pending">● ' + esc(getPayLabel(row)) + '</span>';

  document.getElementById('res-scan-status').innerHTML = scanData
    ? '<span class="badge badge-scanned">✓ Scanned</span>'
    : '<span class="badge-not-scan">Not Scanned</span>';

  if (f.id) {
    try {
      JsBarcode('#result-barcode', f.id, {
        format: 'CODE128', lineColor: '#00e5a0', background: 'transparent',
        width: 2, height: 55, displayValue: true, fontSize: 11, font: 'monospace'
      });
    } catch(_) {}
  }

  const imgB64 = localStorage.getItem('card_img_' + f.email + '_' + f.id);
  const imgEl  = document.getElementById('res-card-preview');
  if (imgB64) {
    imgEl.src           = 'data:image/png;base64,' + imgB64;
    imgEl.style.display = 'block';
  } else {
    imgEl.style.display = 'none';
  }
}

function clearScannerResult() {
  document.getElementById('scanner-input').value            = '';
  document.getElementById('profile-result').style.display   = 'none';
  document.getElementById('profile-not-found').style.display = 'none';
  document.getElementById('scan-banner').className           = 'scan-banner';
  document.getElementById('scanner-input').focus();
}

// ════════════════════════════════════════════════
//  EXPORT XLSX  (SheetJS, client-side)
// ════════════════════════════════════════════════
function exportXlsx() {
  const toExport = filteredRows.length ? filteredRows : rows;
  if (!toExport.length) { toast('No data to export.', 'error'); return; }

  const dept    = document.getElementById('filter-dept').value || 'All';
  const dateStr = new Date().toISOString().slice(0, 10);
  const fname   = 'EventPass_Export_' + dept + '_' + dateStr + '.xlsx';

  const data = toExport.map(row => {
    const f  = extractFields(row);
    const sd = getScanData(f.id);
    return {
      'Name':           f.name,
      'ID':             f.id,
      'Department':     f.dept,
      'Email':          f.email,
      'Attendees':      f.att,
      'Payment Status': isRowPaid(row) ? 'Paid' : 'Unpaid',
      'Scan Status':    sd ? 'Scanned' : 'Not Scanned',
      'Scan Timestamp': sd ? sd.timestamp : '',
    };
  });

  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'EventPass');
  XLSX.writeFile(wb, fname);
  toast('Exported ' + data.length + ' rows → ' + fname);
}

// ════════════════════════════════════════════════
//  TOAST
// ════════════════════════════════════════════════
function toast(msg, type) {
  type = type || 'success';
  const container = document.getElementById('toast-container');
  const el        = document.createElement('div');
  el.className    = 'toast' + (type === 'error' ? ' error' : type === 'info' ? ' info' : '');
  const icon      = type === 'error' ? '✕' : type === 'info' ? 'ℹ' : '✓';
  el.innerHTML    = '<span>' + icon + '</span><span>' + msg + '</span>';
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity    = '0';
    el.style.transition = 'opacity .4s';
    setTimeout(() => el.remove(), 400);
  }, 4000);
}
</script>
</body>
</html>"""

# ════════════════════════════════════════════════════════════
#  SPLASH HTML
# ════════════════════════════════════════════════════════════
SPLASH_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;600;700&family=Share+Tech+Mono&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:#0a0c0f; --accent:#00e5a0; --accent2:#0077ff;
    --text:#c8d0de; --dim:#6b7a90; --muted:#4a5568;
    --border:#252a35; --surface:#111419;
  }
  html, body {
    width:100%; height:100%;
    background:var(--bg); color:var(--text);
    font-family:'Share Tech Mono',monospace;
    overflow:hidden; user-select:none;
  }
  body::before {
    content:''; position:fixed; inset:0;
    background:repeating-linear-gradient(0deg,transparent,transparent 2px,
      rgba(0,229,160,.012) 2px,rgba(0,229,160,.012) 4px);
    pointer-events:none; z-index:999;
  }
  .stripe {
    position:fixed; top:0; left:0; right:0; height:3px;
    background:linear-gradient(90deg,transparent,var(--accent),transparent);
    animation:glow 3s ease-in-out infinite;
  }
  @keyframes glow { 0%,100%{opacity:.5} 50%{opacity:1} }
  .c{position:fixed;width:20px;height:20px;border-color:var(--accent);border-style:solid;opacity:.7;}
  .tl{top:14px;left:14px;border-width:2px 0 0 2px;}
  .tr{top:14px;right:14px;border-width:2px 2px 0 0;}
  .bl{bottom:14px;left:14px;border-width:0 0 2px 2px;}
  .br{bottom:14px;right:14px;border-width:0 2px 2px 0;}
  .card {
    position:fixed; inset:0;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    padding:40px; gap:0;
    animation:fadeIn .5s ease both;
  }
  @keyframes fadeIn { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
  .badge{display:flex;align-items:center;gap:14px;margin-bottom:22px;}
  .brand-wrap{display:flex;flex-direction:column;}
  .brand{
    font-family:'Barlow Condensed',sans-serif;font-weight:700;
    font-size:36px;letter-spacing:6px;text-transform:uppercase;
    color:var(--accent);text-shadow:0 0 24px rgba(0,229,160,.5);line-height:1;
  }
  .brand-sub{
    font-family:'Barlow Condensed',sans-serif;
    font-size:12px;letter-spacing:4px;text-transform:uppercase;
    color:var(--dim);margin-top:4px;
  }
  .icon-wrap{width:52px;height:52px;display:flex;align-items:center;justify-content:center;}
  svg.splash-icon { display:block; }
  hr{width:340px;border:none;border-top:1px solid var(--border);margin:20px 0;}
  .creator-label{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}
  .creator-name{
    font-family:'Barlow Condensed',sans-serif;
    font-size:20px;font-weight:600;letter-spacing:3px;text-transform:uppercase;
  }
  .creator-name span{color:var(--accent);}
  .status-row{display:flex;align-items:center;gap:10px;margin-bottom:12px;width:340px;}
  .dot{
    width:7px;height:7px;border-radius:50%;
    background:var(--accent);box-shadow:0 0 6px var(--accent);
    animation:blink 1.2s ease-in-out infinite;flex-shrink:0;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
  #status{font-size:11px;letter-spacing:1px;color:var(--dim);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .track{width:340px;height:3px;background:var(--surface);border:1px solid var(--border);border-radius:2px;overflow:hidden;}
  #bar{
    height:100%;width:0%;
    background:linear-gradient(90deg,var(--accent),var(--accent2));
    border-radius:2px;transition:width .4s ease;
    box-shadow:0 0 8px rgba(0,229,160,.5);
  }
  .version{position:fixed;bottom:14px;right:18px;font-size:9px;letter-spacing:1px;color:var(--muted);}
</style>
</head>
<body>
<div class="stripe"></div>
<div class="c tl"></div><div class="c tr"></div>
<div class="c bl"></div><div class="c br"></div>
<div class="card">
  <div class="badge">
    <div class="icon-wrap">
      <!-- EventPass icon: flat barcode on dark tile -->
      <svg class="splash-icon" width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="52" height="52" rx="10" fill="#0a0c0f"/>
        <rect x="1" y="1" width="50" height="50" rx="9" stroke="#252a35" stroke-width="1"/>
        <!-- barcode bars -->
        <rect x="10" y="16" width="3"  height="22" fill="#00e5a0"/>
        <rect x="15" y="16" width="2"  height="22" fill="#00e5a0"/>
        <rect x="19" y="16" width="4"  height="22" fill="#00e5a0"/>
        <rect x="25" y="16" width="2"  height="22" fill="#00e5a0"/>
        <rect x="29" y="16" width="3"  height="22" fill="#00e5a0"/>
        <rect x="34" y="16" width="2"  height="22" fill="#00e5a0"/>
        <rect x="38" y="16" width="4"  height="22" fill="#00e5a0"/>
        <!-- scan line -->
        <rect x="8"  y="39" width="36" height="1"  fill="#00e5a0" opacity="0.5"/>
      </svg>
    </div>
    <div class="brand-wrap">
      <div class="brand">EventPass</div>
      <div class="brand-sub">Admin System</div>
    </div>
  </div>
  <hr/>
  <div class="creator-label">Created by</div>
  <div class="creator-name"><span>Jan Clyde T.</span> Talosig</div>
  <hr style="margin:24px 0 20px;"/>
  <div class="status-row">
    <div class="dot"></div>
    <div id="status">Starting server&hellip;</div>
  </div>
  <div class="track"><div id="bar"></div></div>
</div>
<div class="version">v2.0.0</div>
<script>
  function setStatus(msg, pct) {
    document.getElementById('status').textContent = msg;
    if (pct >= 0) document.getElementById('bar').style.width = pct + '%';
  }
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════
#  FLASK SERVER
# ════════════════════════════════════════════════════════════
flask_app = Flask(__name__)
CORS(flask_app, origins='*')


def escape_html(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))


def build_html_email(name, id_, dept):
    n, i, d = escape_html(name), escape_html(id_ or '—'), escape_html(dept or '—')
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="background:#f0f2f5;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">
<tr><td style="background:#0a0c0f;border-radius:8px 8px 0 0;padding:28px 32px;">
  <p style="margin:0;color:#00e5a0;font-size:11px;letter-spacing:3px;text-transform:uppercase;">
    EventPass System</p>
  <h1 style="margin:6px 0 0;color:#fff;font-size:22px;letter-spacing:2px;text-transform:uppercase;">
    Profile Card Ready</h1>
</td></tr>
<tr><td style="background:#fff;padding:32px;border:1px solid #e8ecf2;border-top:none;">
  <p style="font-size:16px;color:#1a1e28;margin:0 0 16px;">Hello <strong>{n}</strong>,</p>
  <p style="color:#4a5568;line-height:1.7;margin:0 0 24px;">
    Your payment has been confirmed and your event profile card has been generated.
    Please find your card attached.</p>
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f5f7fa;border-radius:6px;border-left:4px solid #00e5a0;
                padding:16px 20px;margin-bottom:24px;">
    <tr>
      <td style="font-size:11px;letter-spacing:2px;text-transform:uppercase;
                 color:#8a9ab0;padding:5px 0;">Name</td>
      <td style="font-weight:600;color:#1a1e28;text-align:right;padding:5px 0;">{n}</td>
    </tr>
    <tr>
      <td style="font-size:11px;letter-spacing:2px;text-transform:uppercase;
                 color:#8a9ab0;padding:5px 0;">ID</td>
      <td style="font-weight:600;color:#1a1e28;text-align:right;padding:5px 0;">{i}</td>
    </tr>
    <tr>
      <td style="font-size:11px;letter-spacing:2px;text-transform:uppercase;
                 color:#8a9ab0;padding:5px 0;">Department</td>
      <td style="font-weight:600;color:#1a1e28;text-align:right;padding:5px 0;">{d}</td>
    </tr>
  </table>
  <p style="color:#8a9ab0;font-size:12px;margin:0;">
    This is an automated message. Please do not reply.</p>
</td></tr>
<tr><td style="background:#f5f7fa;border:1px solid #e8ecf2;border-top:none;
               border-radius:0 0 8px 8px;padding:16px 32px;text-align:center;">
  <p style="margin:0;font-size:11px;letter-spacing:1px;color:#8a9ab0;">
    EVENTPASS · AUTOMATED NOTIFICATION</p>
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def build_text_email(name, id_, dept):
    return textwrap.dedent(f"""\
        Hello {name},

        Your payment has been confirmed. Your event profile card is attached.

        Details:
          Name       : {name}
          ID         : {id_ or '—'}
          Department : {dept or '—'}

        Please bring this card (printed or on your phone) to the event.

        — EventPass System
    """)


@flask_app.route('/')
def serve_dashboard():
    return Response(DASHBOARD_HTML, mimetype='text/html')


@flask_app.route('/send', methods=['POST', 'OPTIONS'])
def send_email():
    if request.method == 'OPTIONS':
        return '', 204
    data    = request.get_json(force=True) or {}
    email   = data.get('email', '').strip()
    name    = data.get('name', '').strip()
    id_     = str(data.get('id', '')).strip()
    dept    = data.get('department', '').strip()
    img_b64 = data.get('imageBase64', '').strip()

    if not email or not name or not img_b64:
        return jsonify(success=False, message='Missing required fields.'), 400
    try:
        img_bytes = base64.b64decode(img_b64)
    except Exception as e:
        return jsonify(success=False, message=f'Bad image data: {e}'), 400

    msg            = MIMEMultipart('mixed')
    msg['From']    = f'"EventPass System" <{GMAIL_USER}>'
    msg['To']      = email
    msg['Subject'] = 'Your Event Profile Card 🎟️'
    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText(build_text_email(name, id_, dept), 'plain'))
    alt.attach(MIMEText(build_html_email(name, id_, dept), 'html'))
    msg.attach(alt)

    safe_id = ''.join(c if c.isalnum() or c in '-_' else '_' for c in (id_ or 'card'))
    att = MIMEImage(img_bytes, _subtype='png')
    att.add_header('Content-Disposition', 'attachment',
                   filename=f'profile-card-{safe_id}.png')
    msg.attach(att)

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=ctx) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASS.replace(' ', ''))
            smtp.sendmail(GMAIL_USER, email, msg.as_string())
        print(f'✓  Email sent → {email}')
        return jsonify(success=True)
    except Exception as e:
        print(f'✕  Email failed: {e}')
        return jsonify(success=False, message=f'Email delivery failed: {e}'), 500


@flask_app.route('/health')
def health():
    return jsonify(status='ok', service='EventPass v2', port=PORT)


def run_flask():
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    flask_app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


# ════════════════════════════════════════════════════════════
#  LAUNCH SEQUENCE
# ════════════════════════════════════════════════════════════
def launch_sequence(window):
    def status(msg, pct):
        try:
            window.evaluate_js(f"setStatus({repr(msg)}, {pct});")
        except Exception:
            pass

    status('Starting Flask server…', 20)
    time.sleep(0.8)
    status('Initializing dashboard…', 55)
    time.sleep(0.4)
    status('Loading EventPass v2…', 80)
    time.sleep(0.3)
    status('Ready!', 100)
    time.sleep(0.3)
    window.load_url(f'http://127.0.0.1:{PORT}/')


# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(0.3)

    window = webview.create_window(
        title            = 'EventPass — Admin Dashboard',
        html             = SPLASH_HTML,
        width            = 1340,
        height           = 820,
        min_size         = (960, 640),
        resizable        = True,
        background_color = '#0a0c0f',
    )

    def on_shown():
        t = threading.Thread(target=launch_sequence, args=(window,), daemon=True)
        t.start()

    webview.start(on_shown)
    os._exit(0)


if __name__ == '__main__':
    main()
