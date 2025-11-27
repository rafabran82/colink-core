function Load-Vault {
    param(
        [string]$Path = "wallets.vault.json"
    )

    if (-not (Test-Path $Path)) {
        throw "❌ Vault file not found: $Path"
    }

    try {
        $json = Get-Content $Path -Raw | ConvertFrom-Json
        Write-Host "🔓 Vault loaded" -ForegroundColor Green
        return $json
    }
    catch {
        throw "❌ Failed to load vault JSON: $($_.Exception.Message)"
    }
}

function Save-Vault {
    param(
        [Parameter(Mandatory=$true)]
        [object]$Vault,
        
        [string]$Path = "wallets.vault.json"
    )

    try {
        $pretty = $Vault | ConvertTo-Json -Depth 10
        Set-Content -Path $Path -Value $pretty -Encoding utf8
        Write-Host "💾 Vault saved successfully" -ForegroundColor Green
    }
    catch {
        throw "❌ Failed to save vault: $($_.Exception.Message)"
    }
}

Export-ModuleMember -Function Load-Vault, Save-Vault
