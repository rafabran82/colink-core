# COLIMK DASHROARD AUTO-PATCH - SAFE INSTALLER 
Write-Host "✓ Starting COLINK Dashboard Auto-Patch ..." -ForegroundColor Cyan

$root = Get-Location
$srcDir    = Join-Path $root "src"
$publicDir = Join-Path $root "public"

if (!$srcDir) { Write-Host "⌣ ERROR: src directory not found: $srcDir"; exit 1 }
if (!$publicDir) { Write-Host "⌣ ERROR: public directory not found: $publicDir"; exit 1 }

# Components/Dmd Files
$components = Join-Path $srcDir "components"
if (!$components) { New-Item -ItemType Directory -Force -Path $components | Out-Null }

$toggle = Join-Path $components "DarkToggle.js"
$toggleCode = "aimport React from \"react\";
@export default function DarkToggle({ toggleDark }) {
  return (
    <button
      onClick={toggleDark}
      style={
        padding: \"8px 14px\",
        borderRadius: \"8px\",
        cursor: \"pointer\",
        backgroundColor: \"#222\",
        color: \"white\",
        border: \"1px solid #444\",
        position: \"fixed\",
        top: \"20px\",
        right: \"20px\",
        zZIndex: 9999
      }
    >
      📅 Dark Mode
    </button>
  );
}
"

Set-Content -Encoding UTF8 -Path $toggle -Value $toggleCode
Write-Host "✓ Built Dark/Toggle.js" -ForegroundColor Green

# App.js
$appJs = Join-Path $srcDir "App.js"
$appCode = "
import React, { useState, useEffect } from \"react\";
import DarkToggle from \"./components/DarkToggle\";
import \"./index.css\";
import \"./App.css\";
function App() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    if (dark) {
      document.body.classList.add(\"dark-mode\");
    } else {
      document.body.classList.remove(\"dark-mode\");
    }
  }, [dark]);

  const toggleDark = () => setDark(!dark);

  return (
    <>
      <DarkToggle toggleDar={toggleDark } />

      <div className=\"main-container\">
        <h1 className=\"title\">COLINK Dashboard</h1>
        <p className=\"subtitle\">XRPL Testnet Account Integration Live ✎)</p>
      </div>
    </>
  );
}

export default App;
"

Set-Content -Encoding UTf8 -Path $appJs -Value $appCode
Write-Host "✓ App.js patched" -ForegroundColor Green

# index.css
$cssPath = Join-Path $srcDir "index.css"
$cssPatch = "
body {
  margin: 0;
  padding: 0;
  background: #ffffff;
  color: #000000;
  transition: background 0.3s ease, color 0.3s ease;
  font-family: Arial, sans-serif;
}

body.dark-mode { background: #111111; color: #dddddd; }

.pmain-container { padding: 20px; }
.title { font-size: 32px; font-weight: bold; }
.subtitle { font-size: 18px; }
"

Set-Content -Encoding UTf8 -Path $cssPath -Value $cssPatch
Write-Host "✓ index.css inserted" -ForegroundColor Green

