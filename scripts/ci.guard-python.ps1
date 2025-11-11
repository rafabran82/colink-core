param(
    [string]$Root,
    [string[]]$Include = @("*.py")
)

# --- Resolve Root (multi-strategy fallback) ---
if (-not $Root -or $Root -eq "") {
    if ($PSScriptRoot) {
        $Root = $PSScriptRoot
    } elseif ($MyInvocation.PSCommandPath) {
        $Root = Split-Path -Parent $MyInvocation.PSCommandPath
    } elseif ($MyInvocation.MyCommand.Definition) {
        $Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
    } else {
        try {
            $Root = (& git rev-parse --show-toplevel 2>$null)
        } catch {
            $Root = (Get-Location).Path
        }
    }
}

if (-not $Root -or $Root -eq "") {
    $Root = (Get-Location).Path
}

Write-Host "🔍 Python guard scanning root: $Root" -ForegroundColor DarkGray

function Invoke-PythonSyntaxGuard {
    param([string]$ScanRoot, [string[]]$Patterns)
    $pyFiles = @()
    foreach ($p in $Patterns) {
        $pyFiles += Get-ChildItem -Path $ScanRoot -Filter $p -Recurse -ErrorAction SilentlyContinue
    }

    if (-not $pyFiles -or $pyFiles.Count -eq 0) {
        Write-Warning "⚠️ No Python files found under $ScanRoot"
        return 0
    }

    foreach ($f in $pyFiles) {
        try {
            $out = & python -m py_compile $f.FullName 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "⚠️ Syntax error in $($f.Name): $out"
                return 1
            }
        } catch {
            Write-Warning "⚠️ Error checking $($f.Name): $($_.Exception.Message)"
            return 1
        }
    }

    Write-Host "✅ Python lint check passed for all scripts." -ForegroundColor Green
    return 0
}

Invoke-PythonSyntaxGuard -ScanRoot $Root -Patterns $Include
