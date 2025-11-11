param(
    [string]$Root = "scripts",
    [string]$ReportPath = ".artifacts\\ci\\guard-report.txt"
)

Write-Host "🔍 Running full syntax guard on all *.ps1 files under $Root..."

if (!(Test-Path $Root)) { throw "Directory not found: $Root" }

$files = Get-ChildItem -Path $Root -Recurse -Filter "*.ps1" -File
if (-not $files) { throw "No .ps1 files found under $Root" }

$results = @()
$ErrorActionPreference = "Stop"

foreach ($f in $files) {
    $path = $f.FullName
    $name = $f.Name
    $status = "✅ OK"
    $warn = ""
    try {
        $txt = Get-Content -Raw -Path $path -Encoding utf8

        # 1️⃣ Detect risky brace + quote pattern
        if ($txt -match '(?m)^\s*}\s*"') {
            throw "Suspicious pattern: } followed by double quote."
        }

        # 2️⃣ Pre-clean text
        $clean = $txt `
            -replace '\[[a-zA-Z0-9_\.\[\]]+\]', '' `
            -replace '\[[a-zA-Z]+\([^\)]*\)\]', '' `
            -replace '\[ref\]', '' `
            -replace '([a-zA-Z0-9_\]\:]+)\s*\([^()]*\)', ''

        # 3️⃣ Bracket balance
        $stack = @()
        $map = @{ '{' = '}'; '(' = ')'; '[' = ']' }
        $chars = $clean.ToCharArray()
        foreach ($ch in $chars) {
            if ($map.ContainsKey($ch)) { $stack += $ch }
            elseif ($map.Values -contains $ch) {
                if ($stack.Count -gt 0) { $stack = $stack[0..($stack.Count - 2)] }
            }
        }
        if ($stack.Count -gt 0) { $warn = "⚠️ Unclosed brackets ignored" }

        # 4️⃣ Quote balance
        $dq = ($txt -split '"').Count - 1
        $sq = ($txt -split "'").Count - 1
        if ($dq % 2 -ne 0) { throw "Unbalanced double quotes" }
        if ($sq % 2 -ne 0) { throw "Unbalanced single quotes" }

        # 5️⃣ PowerShell syntax validation
        try {
            powershell -NoProfile -Command "[System.Management.Automation.Language.Parser]::ParseInput((Get-Content -Raw '$path'), [ref]$null, [ref]$null)" | Out-Null
        } catch {
            throw "Syntax error: $($_.Exception.Message)"
        }

    } catch {
        $status = "❌ ERROR"
        $warn = $_.Exception.Message
    }

    $results += [PSCustomObject]@{
        File   = $name
        Status = $status
        Note   = $warn
    }
}

# Print summary
Write-Host ""
Write-Host "=== Syntax Guard Summary ==="
$results | ForEach-Object {
    $color = if ($_.Status -eq "✅ OK") { "Green" } elseif ($_.Status -eq "⚠️ WARN") { "Yellow" } else { "Red" }
    Write-Host ("{0,-25} {1,-10} {2}" -f $_.File, $_.Status, $_.Note) -ForegroundColor $color
}

# Ensure artifact dir
$reportDir = Split-Path -Parent $ReportPath
if (!(Test-Path $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }

# Save report
$results | ConvertTo-Json -Depth 3 | Set-Content -Path $ReportPath -Encoding utf8
Write-Host "`n📝 Report saved to $ReportPath"
Write-Host "✅ Syntax guard scan complete."
