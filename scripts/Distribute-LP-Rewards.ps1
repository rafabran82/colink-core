function Distribute-LP-Rewards {
    param(
        [Parameter(Mandatory=$true)]
        $TopLPs,

        [Parameter(Mandatory=$true)]
        [double]$RewardPool,

        [switch]$TestMode
    )

    Write-Host "?? Computing LP rewards..." -ForegroundColor Cyan

    if ($TopLPs.Count -eq 0) {
        Write-Host "? No LPs provided to reward function" -ForegroundColor Red
        return @()
    }

    # Weight rewards by APY proportion
    $totalAPY = ($TopLPs | Measure-Object lp_apy -Sum).Sum

    $results = foreach ($lp in $TopLPs) {
        $weight = if ($totalAPY -gt 0) { $lp.lp_apy / $totalAPY } else { 1 / $TopLPs.Count }
        $reward = [math]::Round($RewardPool * $weight, 4)

        [ordered]@{
            lp_address = $lp.lp_address
            lp_apy     = $lp.lp_apy
            reward     = $reward
            testMode   = $TestMode.IsPresent
        }
    }

    Write-Host "? Rewards computed." -ForegroundColor Green
    return $results
}
