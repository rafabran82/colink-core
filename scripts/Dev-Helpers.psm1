function MARK-POINT {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    $statePath = Join-Path $PSScriptRoot "dev_state.json"

    $state = if (Test-Path $statePath) {
        Get-Content $statePath | ConvertFrom-Json
    } else {
        [ordered]@{}
    }

    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

    $state.MarkPoint = [ordered]@{
        Name = $Name
        Timestamp = $timestamp
    }

    $state | ConvertTo-Json | Set-Content -Path $statePath -Encoding utf8

    Write-Host "🟩 [MARK] Marked point '$Name' at $timestamp"
}

function DEV-STAT {
    $statePath = Join-Path $PSScriptRoot "dev_state.json"

    if (-not (Test-Path $statePath)) {
        Write-Host "⚠️ No dev state file found. Use MARK-POINT first."
        return
    }

    $state = Get-Content $statePath | ConvertFrom-Json

    Write-Host "📌 DEV STATUS"
    Write-Host "📂 Current Directory: $(Get-Location)"
    Write-Host "📍 Last Mark: $($state.MarkPoint.Name)"
    Write-Host "⏱️ Timestamp: $($state.MarkPoint.Timestamp)"
}

Export-ModuleMember -Function MARK-POINT, DEV-STAT
