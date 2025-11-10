# =================== Phase-20: Build & Test (Windows-safe) ===================
# Fails fast on PowerShell errors, but we control native exit codes explicitly.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
Set-StrictMode -Version Latest

Write-Host "== Phase-20: Build & Test =="

# --- small helpers ------------------------------------------------------------
function Invoke-External {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter()][string[]]$Args = @(),
        [Parameter()][switch]$IgnoreExitCode
    )
    $cmdLine = @($FilePath) + $Args
    Write-Host ">> $($cmdLine -join ' ')"
    & $FilePath @Args
    $code = $LASTEXITCODE
    if (-not $IgnoreExitCode -and $code -ne 0) {
        throw "Command failed: $FilePath (exit $code)"
    }
    return $code
}

function Reset-LastExitCode {
    # Clear any sticky code from native calls
    $global:LASTEXITCODE = 0
}

# --- sim demo -----------------------------------------------------------------
Write-Host "Running sim demo..."
try {
    # Replace with your real demo once ready; ignore exit code if it's a no-op
    Reset-LastExitCode
    # Example (commented):
    # Invoke-External -FilePath "python" -Args @("-m","colink_core.sim.run","--demo","--display","Agg","--out-prefix",".\.artifacts\demo") -IgnoreExitCode
} catch {
    Write-Warning "sim demo: $_"
}

# --- bridge demo --------------------------------------------------------------
Write-Host "Running bridge demo..."
try {
    Write-Host "Bridge demo placeholder (no-op)."
    Reset-LastExitCode
} catch {
    Write-Warning "bridge demo: $_"
}

# --- pytest -------------------------------------------------------------------
Write-Host "Running pytest -q ..."
$allowNoTests = ($env:ALLOW_PYTEST_NO_TESTS -as [string])
try {
    Reset-LastExitCode
    # Run pytest quietly; do not throw here—interpret exit codes ourselves
    & pytest -q
    $pyCode = $LASTEXITCODE
    Write-Host "pytest exit code: $pyCode"

    switch ($pyCode) {
        0 { Write-Host "pytest: success." }
        5 {
            if ($allowNoTests -and $allowNoTests.ToLower() -in @('1','true','yes','y')){
                Write-Warning "pytest: no tests collected (code 5) — allowed by ALLOW_PYTEST_NO_TESTS."
                Reset-LastExitCode
            } else {
                throw "pytest returned code 5 (no tests) and ALLOW_PYTEST_NO_TESTS is not enabled."
            }
        }
        default {
            throw "pytest failed with exit code $pyCode"
        }
    }
} catch {
    Write-Error $_
    # Ensure runner sees failure:
    exit 1
}

Write-Host "Build & Test done."

# Final defense: ensure a clean exit for the job when we deem success.
Reset-LastExitCode
exit 0
# ============================================================================

