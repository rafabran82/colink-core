# --- Python syntax guard (cross-version safe, callable as function) ---
function Invoke-PythonSyntaxGuard {
    param (
        [string]$Root = "scripts",
        [string[]]$Include = @("*.py")
    )

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    $py  = if ($null -ne $cmd) { $cmd.Source } else { $null }

    if (-not $py) {
        Write-Error "❌ Python not found in PATH. Please install Python 3.x."
        return 1
    }

    $pyFiles = Get-ChildItem -Path $Root -Recurse -Include $Include -File -ErrorAction SilentlyContinue
    if (-not $pyFiles) {
        Write-Warning "⚠️ No Python files found under $Root"
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
