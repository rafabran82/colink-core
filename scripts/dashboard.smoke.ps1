param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

Write-Host "📊 COLINK dashboard smoke check against $BaseUrl" -ForegroundColor Cyan

# Safe property accessor
function Get-PropSafe {
    param($obj, $prop)
    if ($obj -and $obj.PSObject.Properties[$prop]) {
        return $obj.$prop
    }
    return "[missing]"
}

# Unified endpoint tester
function Test-Endpoint {
    param([string]$Path)

    $url = "$BaseUrl$Path"
    Write-Host "  → GET $url" -ForegroundColor Gray

    try {
        $resp = Invoke-RestMethod -Uri $url -Method GET -ErrorAction Stop
        return [PSCustomObject]@{
            Ok   = $true
            Data = $resp
        }
    }
    catch {
        Write-Host "    ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return [PSCustomObject]@{
            Ok   = $false
            Data = $null
        }
    }
}

$ok = $true

# 1) sim/meta
$r = Test-Endpoint "/api/sim/meta"
if ($r.Ok) {
    $meta = $r.Data
    $status = Get-PropSafe $meta "status"
    $engine = Get-PropSafe $meta "engine"
    $ts     = Get-PropSafe $meta "timestamp"

    Write-Host "    ✅ sim/meta: status=$status engine=$engine ts=$ts" -ForegroundColor Green
} else {
    $ok = $false
}

# 2) pools/state
$r = Test-Endpoint "/api/pools/state"
if ($r.Ok) {
    $pools = $r.Data
    $count = 0

    if ($pools -is [System.Collections.IEnumerable]) {
        $count = ($pools | Measure-Object).Count
    } elseif ($pools.value) {
        $count = ($pools.value | Measure-Object).Count
    }

    Write-Host "    ✅ pools/state: $count pool(s)" -ForegroundColor Green
} else {
    $ok = $false
}

# 3) swaps/recent
$r = Test-Endpoint "/api/swaps/recent"
if ($r.Ok) {
    $swaps = $r.Data
    $count = 0

    if ($swaps -is [System.Collections.IEnumerable]) {
        $count = ($swaps | Measure-Object).Count
    } elseif ($swaps.value) {
        $count = ($swaps.value | Measure-Object).Count
    }

    Write-Host "    ✅ swaps/recent: $count swap(s)" -ForegroundColor Green
} else {
    $ok = $false
}

if ($ok) {
    Write-Host "🎉 Dashboard smoke check PASSED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Dashboard smoke check FAILED" -ForegroundColor Red
    exit 1
}
