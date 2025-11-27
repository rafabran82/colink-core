# ================================================
# COLINK DASHBOARD AUTO-PATCH (SAFE VERSION)
# From MARK POINT: XRPL-DASHBOARD-BACKEND-LIVE-SUCCESS
# ================================================

Write-Host "🔧 Starting COLINK Dashboard Auto-Patch..." -ForegroundColor Cyan

# --- SAFE ROOT USING CURRENT LOCATION ---
$root = Get-Location

# PATHS
$srcDir    = Join-Path $root "src"
$publicDir = Join-Path $root "public"

# VALIDATE PATHS
if (!(Test-Path $srcDir)) {
    Write-Host "❌ ERROR: src directory not found at $srcDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $publicDir)) {
    Write-Host "❌ ERROR: public directory not found at $publicDir" -ForegroundColor Red
    exit 1
}

# COMPONENT PATH
$componentsDir = Join-Path $srcDir "components"
if (!(Test-Path $componentsDir)) {
    New-Item -ItemType Directory -Force -Path $componentsDir | Out-Null
}

$togglePath = Join-Path $componentsDir "DarkToggle.js"

# Inject toggle component
$toggleCode = @"
import React from 'react';

export default function DarkToggle({ toggleDark }) {
  return (
    <button
      onClick={toggleDark}
      style={{
        padding: '8px 14px',
        borderRadius: '8px',
        cursor: 'pointer',
        backgroundColor: '#222',
        color: 'white',
        border: '1px solid #444',
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999
      }}
    >
      🌙 Dark Mode
    </button>
  );
}
"@

Set-Content -Encoding UTF8 -Path $togglePath -Value $toggleCode
Write-Host "✨ Injected DarkToggle.js" -ForegroundColor Green

# PATCH App.js
$appJs = Join-Path $srcDir "App.js"

$appPatched = @"
import React, { useState, useEffect } from 'react';
import DarkToggle from './components/DarkToggle';
import './index.css';
import './App.css';

function App() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    if (dark) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [dark]);

  const toggleDark = () => setDark(!dark);

  return (
    <>
      <DarkToggle toggleDark={toggleDark} />

      <div className="main-container">
        <h1 className="title">COLINK Dashboard</h1>
        <p className="subtitle">XRPL Testnet Account Integration Live ✓</p>
      </div>
    </>
  );
}

export default App;
"@

Set-Content -Encoding UTF8 -Path $appJs -Value $appPatched
Write-Host "✨ Patched App.js" -ForegroundColor Green

# PATCH index.css
$cssPath = Join-Path $srcDir "index.css"

$cssPatch = @"
body {
  margin: 0;
  padding: 0;
  background: #ffffff;
  color: #000000;
  transition: background 0.3s ease, color 0.3s ease;
  font-family: Arial, sans-serif;
}

body.dark-mode {
  background: #111111;
  color: #dddddd;
}

.main-container {
  padding: 20px;
}

.title {
  font-size: 32px;
  font-weight: bold;
}

.subtitle {
  font-size: 18px;
}
"@

Set-Content -Encoding UTF8 -Path $cssPath -Value $cssPatch
Write-Host "✨ Updated index.css" -ForegroundColor Green

# PATCH App.css
$appCss = Join-Path $srcDir "App.css"
$appCssCode = @"
.dark-mode .card {
  background-color: #222;
  color: #eee;
}

.card {
  background-color: #fafafa;
  padding: 20px;
  border-radius: 14px;
  margin: 10px 0;
  transition: background 0.3s ease, color 0.3s ease;
}
"@

Set-Content -Encoding UTF8 -Path $appCss -Value $appCssCode
Write-Host "✨ Patched App.css" -ForegroundColor Green

# UPDATE public/index.html
$indexHtml = Join-Path $publicDir "index.html"
$html = Get-Content $indexHtml -Raw

if ($html -notmatch "dark-mode") {
    $html = $html -replace "</head>", "  <!-- Dark mode ready -->`n</head>"
    Set-Content -Encoding UTF8 -Path $indexHtml -Value $html
    Write-Host "✨ Updated public/index.html" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================="
Write-Host "🟢 AUTO-PATCH COMPLETE — DASHBOARD IS UPDATED"
Write-Host "============================================="
Write-Host "🚀 You can now run: npm start"
Write-Host "============================================="
