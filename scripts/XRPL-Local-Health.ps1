param(
    [string]$Rpc1 = "http://localhost:5005",
    [string]$Rpc2 = "http://localhost:51234"
)

Write-Host "======================================="
Write-Host "➡️  COLINK — XRPL LOCAL DEVNET HEALTH"
Write-Host "======================================="

$payload = @{
    method = "server_info"
    params = @(@{})
}

$endpoints = @(
    @{ Name = "LOCAL-5005"; Url = $Rpc1 },
    @{ Name = "LOCAL-51234"; Url = $Rpc2 }
)

$results = @()
$success = $false

foreach ($ep in $endpoints) {
    Write-Host ""
    Write-Host "🔎 Checking $($ep.Name) at $($ep.Url)..."

    try {
        $response = Invoke-RestMethod -Uri $ep.Url -Method Post -Body ($payload | ConvertTo-Json -Depth 5) -ContentType "application/json" -TimeoutSec 5
        if ($response.result -and $response.result.info) {
            $info = $response.result.info

            $serverState   = $info.server_state
            $buildVersion  = $info.build_version
            $pubKeyNode    = $info.pubkey_node
            $completeLedgers = $info.complete_ledgers

            $validated = $null
            if ($info.validated_ledger) {
                $validated = $info.validated_ledger.seq
            }

            Write-Host "   🟩 Connected."
            Write-Host "   • Server state:      $serverState"
            Write-Host "   • Build version:     $buildVersion"
            Write-Host "   • Node public key:   $pubKeyNode"
            Write-Host "   • Complete ledgers:  $completeLedgers"
            if ($validated) {
                Write-Host "   • Validated ledger:  $validated"
            }

            $results += [pscustomobject]@{
                Endpoint        = $ep.Name
                Url             = $ep.Url
                ServerState     = $serverState
                BuildVersion    = $buildVersion
                ValidatedLedger = $validated
            }

            $success = $true
        }
        else {
            Write-Host "   ⚠️  Response did not contain expected info."
        }
    }
    catch {
        Write-Host "   ❌ Failed to connect or parse response:"
        Write-Host "      $($_.Exception.Message)"
    }
}

Write-Host ""
Write-Host "======================================="
Write-Host "       XRPL LOCAL DEVNET SUMMARY"
Write-Host "======================================="

if ($success -and $results.Count -gt 0) {
    foreach ($r in $results) {
        Write-Host ""
        Write-Host "🟢 Endpoint: $($r.Endpoint) — $($r.Url)"
        Write-Host "   • Server state:      $($r.ServerState)"
        Write-Host "   • Build version:     $($r.BuildVersion)"
        if ($r.ValidatedLedger) {
            Write-Host "   • Validated ledger:  $($r.ValidatedLedger)"
        }
    }
    Write-Host ""
    Write-Host "✅ XRPL LOCAL DEVNET IS UP AND RESPONDING 🟢"
}
else {
    Write-Host "❌ No working XRPL local endpoints responded."
    Write-Host "   Check Docker container 'xrpld-local' and port mappings."
}

Write-Host ""
Write-Host "======================================="
Write-Host "          HEALTH CHECK COMPLETE"
Write-Host "======================================="
