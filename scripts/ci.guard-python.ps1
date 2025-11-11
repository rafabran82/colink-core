param(
    [string]$Root,
    [string[]]$Include = @("*.py")
)

if (-not $Root -or $Root -eq "") {
    try {
        # Resolve this script's folder robustly for both dot-source and call
        $Root = Split-Path -Parent (Get-Item $MyInvocation.PSCommandPath).FullName
    } catch {
        $Root = (Split-Path -Parent $MyInvocation.MyCommand.Definition)
    }
}

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
